"""Serviço de domínio para matrícula atômica de estudantes em turmas com validação de vagas (BE-016)."""

import asyncio
import threading
from typing import Annotated, Final
from uuid import UUID
from weakref import WeakKeyDictionary

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.enrollment import Enrollment, _utc_today
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.enrollment_repository import (
    EnrollmentRepository,
    EnrollmentRepositoryDep,
)
from app.schemas.enrollment import (
    EnrollmentClassSummarySchema,
    EnrollmentCreateSchema,
    EnrollmentResponseSchema,
    EnrollmentStatusUpdateSchema,
    EnrollmentStudentSummarySchema,
)
from app.schemas.enums import ClassStatus, EnrollmentStatus, UserRole
from app.services.audit_service import AuditService, AuditServiceDep

ENROLLMENT_NOT_FOUND_MESSAGE: Final[str] = "Matrícula não encontrada."
ENROLLMENT_REACTIVATION_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível reativar matrícula em uma turma que não está ativa."
)
ENROLLMENT_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
ENROLLMENT_STUDENT_NOT_FOUND_MESSAGE: Final[str] = "Estudante não encontrado."
ENROLLMENT_INVALID_STUDENT_ROLE_MESSAGE: Final[str] = (
    "Apenas usuários com perfil de estudante (STUDENT) podem ser matriculados em turmas."
)
ENROLLMENT_INACTIVE_STUDENT_MESSAGE: Final[str] = (
    "Não é possível matricular um estudante com conta inativa."
)
ENROLLMENT_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível realizar matrícula em uma turma que não está ativa."
)
ENROLLMENT_INACTIVE_COURSE_MESSAGE: Final[str] = (
    "Não é possível realizar matrícula em turma vinculada a um curso técnico inativo."
)
ENROLLMENT_ALREADY_EXISTS_MESSAGE: Final[str] = (
    "O estudante já está matriculado nesta turma acadêmica."
)
ENROLLMENT_CLASS_FULL_MESSAGE: Final[str] = (
    "Não foi possível realizar a matrícula: a turma atingiu o limite máximo de vagas."
)

_LOOP_CLASS_LOCKS: WeakKeyDictionary[asyncio.AbstractEventLoop, dict[UUID, asyncio.Lock]] = (
    WeakKeyDictionary()
)
_THREAD_LOCK = threading.RLock()


def _get_async_class_lock(class_id: UUID) -> asyncio.Lock:
    """Retorna um lock assíncrono isolado por event loop e turma para evitar overbooking."""
    loop = asyncio.get_running_loop()
    with _THREAD_LOCK:
        locks_for_loop = _LOOP_CLASS_LOCKS.setdefault(loop, {})
        lock = locks_for_loop.get(class_id)
        if lock is None:
            lock = asyncio.Lock()
            locks_for_loop[class_id] = lock
        return lock


class EnrollmentService:
    """Serviço responsável pelo processamento atômico de matrículas, controle de vagas e auditoria."""

    def __init__(
        self,
        repository: EnrollmentRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repository = repository
        self._audit_service = (
            audit_service
            if audit_service is not None
            else AuditService(repository=AuditRepository(session=repository.session))
        )

    @staticmethod
    def _to_response(enrollment: Enrollment) -> EnrollmentResponseSchema:
        """Converte a entidade Enrollment no schema detalhado com dados do estudante e da turma."""
        student = enrollment.student
        profile = student.profile
        return EnrollmentResponseSchema(
            id=enrollment.id,
            student_id=enrollment.student_id,
            class_id=enrollment.class_id,
            enrollment_date=enrollment.enrollment_date,
            status=enrollment.status,
            final_grade=enrollment.final_grade,
            attendance_rate=enrollment.attendance_rate,
            student=EnrollmentStudentSummarySchema(
                id=student.id,
                email=student.email,
                role=student.role,
                is_active=student.is_active,
                full_name=profile.full_name if profile is not None else None,
                registration_number=(
                    profile.registration_number if profile is not None else None
                ),
            ),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                enrollment.academic_class
            ),
            created_at=enrollment.created_at,
            updated_at=enrollment.updated_at,
        )

    async def create_enrollment(
        self,
        payload: EnrollmentCreateSchema,
    ) -> EnrollmentResponseSchema:
        """Matricula um estudante em turma ativa garantindo isolamento contra overbooking."""
        async with _get_async_class_lock(payload.class_id):
            with _THREAD_LOCK:
                academic_class = self._repository.get_class_for_update(payload.class_id)
                if academic_class is None:
                    raise NotFoundException(message=ENROLLMENT_CLASS_NOT_FOUND_MESSAGE)

                if academic_class.status != ClassStatus.ACTIVE:
                    raise UnprocessableEntityException(
                        message=ENROLLMENT_INACTIVE_CLASS_MESSAGE
                    )

                if not academic_class.course.is_active:
                    raise UnprocessableEntityException(
                        message=ENROLLMENT_INACTIVE_COURSE_MESSAGE
                    )

                student = self._repository.get_user_by_id(payload.student_id)
                if student is None:
                    raise NotFoundException(message=ENROLLMENT_STUDENT_NOT_FOUND_MESSAGE)

                if student.role != UserRole.STUDENT:
                    raise UnprocessableEntityException(
                        message=ENROLLMENT_INVALID_STUDENT_ROLE_MESSAGE
                    )

                if not student.is_active:
                    raise UnprocessableEntityException(
                        message=ENROLLMENT_INACTIVE_STUDENT_MESSAGE
                    )

                existing = self._repository.get_by_student_and_class(
                    student_id=student.id,
                    class_id=academic_class.id,
                )
                if existing is not None:
                    raise ConflictException(message=ENROLLMENT_ALREADY_EXISTS_MESSAGE)

                active_count = self._repository.count_active_enrollments_in_class(
                    academic_class.id
                )
                if active_count >= academic_class.max_students:
                    raise UnprocessableEntityException(
                        message=ENROLLMENT_CLASS_FULL_MESSAGE
                    )

                resolved_date = payload.enrollment_date or _utc_today()
                try:
                    created = self._repository.create_in_transaction(
                        student_id=student.id,
                        class_id=academic_class.id,
                        enrollment_date=resolved_date,
                        status=EnrollmentStatus.ACTIVE,
                    )
                except IntegrityError as exc:
                    self._repository.rollback()
                    error_text = str(exc).lower()
                    if "chk_enrollments_class_capacity" in error_text:
                        raise UnprocessableEntityException(
                            message=ENROLLMENT_CLASS_FULL_MESSAGE
                        ) from exc
                    raise ConflictException(
                        message=ENROLLMENT_ALREADY_EXISTS_MESSAGE
                    ) from exc

                logger.bind(
                    enrollment_id=str(created.id),
                    student_id=str(created.student_id),
                    class_id=str(created.class_id),
                    status=created.status.value,
                    active_enrollments=active_count + 1,
                    max_students=academic_class.max_students,
                ).info("Estudante matriculado na turma acadêmica com sucesso.")
                return self._to_response(created)

    async def update_enrollment_status(
        self,
        enrollment_id: UUID,
        payload: EnrollmentStatusUpdateSchema,
        *,
        current_user: User,
        ip_address: str | None = None,
    ) -> EnrollmentResponseSchema:
        """Altera o status da matrícula e grava trilha de auditoria JSON em audit_logs."""
        initial_enrollment = self._repository.get_by_id(enrollment_id)
        if initial_enrollment is None:
            raise NotFoundException(message=ENROLLMENT_NOT_FOUND_MESSAGE)

        async with _get_async_class_lock(initial_enrollment.class_id):
            with _THREAD_LOCK:
                enrollment = self._repository.get_by_id(enrollment_id)
                if enrollment is None:
                    raise NotFoundException(message=ENROLLMENT_NOT_FOUND_MESSAGE)

                academic_class = self._repository.get_class_for_update(enrollment.class_id)
                if academic_class is None:
                    raise NotFoundException(message=ENROLLMENT_CLASS_NOT_FOUND_MESSAGE)

                previous_status = enrollment.status
                is_reactivation = (
                    previous_status != EnrollmentStatus.ACTIVE
                    and payload.status == EnrollmentStatus.ACTIVE
                )
                if is_reactivation:
                    if academic_class.status != ClassStatus.ACTIVE:
                        raise UnprocessableEntityException(
                            message=ENROLLMENT_REACTIVATION_INACTIVE_CLASS_MESSAGE
                        )
                    active_count = self._repository.count_active_enrollments_in_class(
                        academic_class.id
                    )
                    if active_count >= academic_class.max_students:
                        raise UnprocessableEntityException(
                            message=ENROLLMENT_CLASS_FULL_MESSAGE
                        )

                old_values = {
                    "status": previous_status.value,
                    "student_id": str(enrollment.student_id),
                    "class_id": str(enrollment.class_id),
                }
                new_values = {
                    "status": payload.status.value,
                    "student_id": str(enrollment.student_id),
                    "class_id": str(enrollment.class_id),
                    "justification": payload.justification,
                }

                try:
                    self._repository.update_status(
                        enrollment,
                        new_status=payload.status,
                    )
                    self._audit_service.log_action(
                        user_id=current_user.id,
                        action="ENROLLMENT_STATUS_UPDATED",
                        entity="enrollments",
                        entity_id=str(enrollment.id),
                        old_values=old_values,
                        new_values=new_values,
                        ip_address=ip_address,
                        commit=False,
                    )
                    updated = self._repository.commit_and_refresh(enrollment)
                except IntegrityError as exc:
                    self._repository.rollback()
                    error_text = str(exc).lower()
                    if "chk_enrollments_class_capacity" in error_text:
                        raise UnprocessableEntityException(
                            message=ENROLLMENT_CLASS_FULL_MESSAGE
                        ) from exc
                    raise

                logger.bind(
                    enrollment_id=str(updated.id),
                    student_id=str(updated.student_id),
                    class_id=str(updated.class_id),
                    previous_status=previous_status.value,
                    new_status=updated.status.value,
                    actor_id=str(current_user.id),
                ).info("Status da matrícula atualizado com auditoria registrada.")
                return self._to_response(updated)


def get_enrollment_service(
    repository: EnrollmentRepositoryDep,
    audit_service: AuditServiceDep,
) -> EnrollmentService:
    """Provedor de injeção de dependência para EnrollmentService."""
    return EnrollmentService(
        repository=repository,
        audit_service=audit_service,
    )


EnrollmentServiceDep = Annotated[
    EnrollmentService,
    Depends(get_enrollment_service),
]

__all__ = [
    "ENROLLMENT_ALREADY_EXISTS_MESSAGE",
    "ENROLLMENT_CLASS_FULL_MESSAGE",
    "ENROLLMENT_CLASS_NOT_FOUND_MESSAGE",
    "ENROLLMENT_INACTIVE_CLASS_MESSAGE",
    "ENROLLMENT_INACTIVE_COURSE_MESSAGE",
    "ENROLLMENT_INACTIVE_STUDENT_MESSAGE",
    "ENROLLMENT_INVALID_STUDENT_ROLE_MESSAGE",
    "ENROLLMENT_NOT_FOUND_MESSAGE",
    "ENROLLMENT_REACTIVATION_INACTIVE_CLASS_MESSAGE",
    "ENROLLMENT_STUDENT_NOT_FOUND_MESSAGE",
    "EnrollmentService",
    "EnrollmentServiceDep",
    "get_enrollment_service",
]
