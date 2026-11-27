"""Dependência FastAPI de bloqueio de mutações em turmas com período letivo encerrado (BE-029 / DB-029)."""

from collections.abc import Awaitable, Callable
import json
from typing import Final, Literal
from uuid import UUID

from fastapi import Request
from sqlalchemy import select

from app.core.database import DbSessionDep
from app.core.exceptions import UnprocessableEntityException
from app.core.logging import logger
from app.core.security import CurrentUserDep
from app.models.academic_assessment import AcademicAssessment
from app.models.academic_class import AcademicClass
from app.models.class_lesson import ClassLesson
from app.models.practical_task import PracticalTask
from app.models.self_assessment import SelfAssessmentForm
from app.models.teacher_assignment import TeacherAssignment
from app.schemas.enums import ClassStatus, UserRole

CLASS_PERIOD_CLOSED_ERROR_CODE: Final[str] = "CLASS_PERIOD_CLOSED"
CLASS_PERIOD_CLOSED_MESSAGE: Final[str] = "Período letivo encerrado para esta turma."
CLOSED_CLASS_STATUSES: Final[frozenset[ClassStatus]] = frozenset(
    {ClassStatus.COMPLETED, ClassStatus.ARCHIVED}
)
MUTATION_HTTP_METHODS: Final[frozenset[str]] = frozenset(
    {"POST", "PUT", "PATCH", "DELETE"}
)

ClassResolutionSource = Literal[
    "class_id",
    "lesson_id",
    "task_id",
    "assessment_id",
    "form_id",
    "body_class_id",
]


def _parse_uuid_safe(raw_value: object) -> UUID | None:
    """Tenta converter valor arbitrário em UUID sem lançar erro (delegando 400 ao Pydantic)."""
    if isinstance(raw_value, UUID):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return UUID(raw_value.strip())
        except ValueError:
            return None
    return None


def raise_if_class_period_closed(academic_class: AcademicClass) -> None:
    """Lança HTTP 422 com código CLASS_PERIOD_CLOSED quando a turma está COMPLETED ou ARCHIVED."""
    if academic_class.status in CLOSED_CLASS_STATUSES:
        raise UnprocessableEntityException(
            message=CLASS_PERIOD_CLOSED_MESSAGE,
            error=CLASS_PERIOD_CLOSED_ERROR_CODE,
        )


def check_class_is_active(
    source: ClassResolutionSource = "class_id",
) -> Callable[..., Awaitable[AcademicClass | None]]:
    """Factory de dependência FastAPI que bloqueia mutações (POST/PUT/PATCH/DELETE) em turmas encerradas (BE-029)."""

    async def _verify_class_is_active(
        request: Request,
        db: DbSessionDep,
        current_user: CurrentUserDep,
    ) -> AcademicClass | None:
        if request.method.upper() not in MUTATION_HTTP_METHODS:
            return None

        resolved_class_id: UUID | None = None

        if source == "class_id":
            resolved_class_id = _parse_uuid_safe(request.path_params.get("class_id"))
        elif source == "lesson_id":
            lesson_id = _parse_uuid_safe(request.path_params.get("lesson_id"))
            if lesson_id is not None:
                resolved_class_id = db.scalar(
                    select(ClassLesson.class_id).where(ClassLesson.id == lesson_id)
                )
        elif source == "task_id":
            task_id = _parse_uuid_safe(request.path_params.get("task_id"))
            if task_id is not None:
                resolved_class_id = db.scalar(
                    select(PracticalTask.class_id).where(PracticalTask.id == task_id)
                )
        elif source == "assessment_id":
            assessment_id = _parse_uuid_safe(request.path_params.get("assessment_id"))
            if assessment_id is not None:
                resolved_class_id = db.scalar(
                    select(AcademicAssessment.class_id).where(
                        AcademicAssessment.id == assessment_id
                    )
                )
        elif source == "form_id":
            form_id = _parse_uuid_safe(request.path_params.get("form_id"))
            if form_id is not None:
                resolved_class_id = db.scalar(
                    select(SelfAssessmentForm.class_id).where(
                        SelfAssessmentForm.id == form_id
                    )
                )
        elif source == "body_class_id":
            raw_body = await request.body()
            if raw_body:
                try:
                    parsed_body = json.loads(raw_body)
                    if isinstance(parsed_body, dict):
                        resolved_class_id = _parse_uuid_safe(parsed_body.get("class_id"))
                except (ValueError, TypeError):
                    resolved_class_id = None

        if resolved_class_id is None:
            return None

        academic_class = db.scalar(
            select(AcademicClass).where(AcademicClass.id == resolved_class_id)
        )
        if academic_class is None:
            return None

        # Preserva precedência de autorização contextual (403) para docente não alocado na turma
        if current_user.role == UserRole.TEACHER:
            is_assigned = (
                db.scalar(
                    select(TeacherAssignment.id)
                    .where(
                        TeacherAssignment.teacher_id == current_user.id,
                        TeacherAssignment.class_id == academic_class.id,
                    )
                    .limit(1)
                )
                is not None
            )
            if not is_assigned:
                return None

        if academic_class.status in CLOSED_CLASS_STATUSES:
            logger.bind(
                method=request.method,
                path=request.url.path,
                class_id=str(academic_class.id),
                class_code=academic_class.code,
                class_status=academic_class.status.value,
                actor_id=str(current_user.id),
                actor_role=current_user.role.value,
                error=CLASS_PERIOD_CLOSED_ERROR_CODE,
            ).warning(
                "Bloqueio de mutação em turma com período letivo encerrado (BE-029)."
            )
            raise_if_class_period_closed(academic_class)

        return academic_class

    return _verify_class_is_active


__all__ = [
    "CLASS_PERIOD_CLOSED_ERROR_CODE",
    "CLASS_PERIOD_CLOSED_MESSAGE",
    "CLOSED_CLASS_STATUSES",
    "ClassResolutionSource",
    "MUTATION_HTTP_METHODS",
    "check_class_is_active",
    "raise_if_class_period_closed",
]
