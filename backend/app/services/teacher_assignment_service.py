"""Serviço de domínio para alocação de docentes em disciplinas e turmas SENAI (BE-018)."""

from typing import Annotated, Final

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.teacher_assignment import TeacherAssignment
from app.repositories.teacher_assignment_repository import (
    TeacherAssignmentRepository,
    TeacherAssignmentRepositoryDep,
)
from app.schemas.enums import UserRole
from app.schemas.teacher_assignment import (
    TeacherAssignmentClassSummarySchema,
    TeacherAssignmentCreateSchema,
    TeacherAssignmentResponseSchema,
    TeacherAssignmentSubjectSummarySchema,
    TeacherAssignmentTeacherSummarySchema,
)

TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE: Final[str] = (
    "O usuário indicado não é um professor cadastrado (role TEACHER)."
)
TEACHER_ASSIGNMENT_INACTIVE_TEACHER_MESSAGE: Final[str] = (
    "Não é possível alocar um professor com conta inativa."
)
TEACHER_ASSIGNMENT_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
TEACHER_ASSIGNMENT_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina técnica não encontrada."
TEACHER_ASSIGNMENT_INACTIVE_SUBJECT_MESSAGE: Final[str] = (
    "Não é possível alocar docente em uma disciplina técnica inativa."
)
TEACHER_ASSIGNMENT_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "A disciplina informada não pertence ao curso técnico da turma selecionada."
)
TEACHER_ASSIGNMENT_CONFLICT_MESSAGE: Final[str] = (
    "O professor já está atribuído a esta disciplina nesta turma."
)


class TeacherAssignmentService:
    """Serviço responsável pelas regras de negócio de alocação de docentes em oficinas e turmas."""

    def __init__(self, repository: TeacherAssignmentRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_response(assignment: TeacherAssignment) -> TeacherAssignmentResponseSchema:
        """Converte a entidade TeacherAssignment no schema detalhado da atribuição docente."""
        teacher = assignment.teacher
        profile = teacher.profile
        return TeacherAssignmentResponseSchema(
            id=assignment.id,
            teacher_id=assignment.teacher_id,
            class_id=assignment.class_id,
            subject_id=assignment.subject_id,
            is_main_teacher=assignment.is_main_teacher,
            assigned_at=assignment.assigned_at,
            teacher=TeacherAssignmentTeacherSummarySchema(
                id=teacher.id,
                email=teacher.email,
                role=teacher.role,
                is_active=teacher.is_active,
                full_name=profile.full_name if profile is not None else None,
                registration_number=(
                    profile.registration_number if profile is not None else None
                ),
            ),
            academic_class=TeacherAssignmentClassSummarySchema.model_validate(
                assignment.academic_class
            ),
            subject=TeacherAssignmentSubjectSummarySchema.model_validate(
                assignment.subject
            ),
        )

    def create_assignment(
        self,
        payload: TeacherAssignmentCreateSchema,
    ) -> TeacherAssignmentResponseSchema:
        """Aloca um professor (role TEACHER) a uma disciplina e turma, permitindo co-docência."""
        teacher = self._repository.get_user_by_id(payload.teacher_id)
        if teacher is None or teacher.role != UserRole.TEACHER:
            raise BadRequestException(message=TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE)

        if not teacher.is_active:
            raise BadRequestException(message=TEACHER_ASSIGNMENT_INACTIVE_TEACHER_MESSAGE)

        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=TEACHER_ASSIGNMENT_CLASS_NOT_FOUND_MESSAGE)

        subject = self._repository.get_subject_by_id(payload.subject_id)
        if subject is None:
            raise NotFoundException(message=TEACHER_ASSIGNMENT_SUBJECT_NOT_FOUND_MESSAGE)

        if not subject.is_active:
            raise UnprocessableEntityException(
                message=TEACHER_ASSIGNMENT_INACTIVE_SUBJECT_MESSAGE
            )

        if subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(
                message=TEACHER_ASSIGNMENT_COURSE_MISMATCH_MESSAGE
            )

        existing = self._repository.get_by_composite_key(
            teacher_id=teacher.id,
            class_id=academic_class.id,
            subject_id=subject.id,
        )
        if existing is not None:
            raise ConflictException(message=TEACHER_ASSIGNMENT_CONFLICT_MESSAGE)

        try:
            created = self._repository.create(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
                is_main_teacher=payload.is_main_teacher,
            )
        except IntegrityError as exc:
            self._repository.rollback()
            raise ConflictException(message=TEACHER_ASSIGNMENT_CONFLICT_MESSAGE) from exc

        logger.bind(
            assignment_id=str(created.id),
            teacher_id=str(created.teacher_id),
            class_id=str(created.class_id),
            subject_id=str(created.subject_id),
            is_main_teacher=created.is_main_teacher,
        ).info("Docente alocado na disciplina e turma acadêmica com sucesso.")
        return self._to_response(created)


def get_teacher_assignment_service(
    repository: TeacherAssignmentRepositoryDep,
) -> TeacherAssignmentService:
    """Provedor de injeção de dependência para TeacherAssignmentService."""
    return TeacherAssignmentService(repository=repository)


TeacherAssignmentServiceDep = Annotated[
    TeacherAssignmentService,
    Depends(get_teacher_assignment_service),
]

__all__ = [
    "TEACHER_ASSIGNMENT_CLASS_NOT_FOUND_MESSAGE",
    "TEACHER_ASSIGNMENT_CONFLICT_MESSAGE",
    "TEACHER_ASSIGNMENT_COURSE_MISMATCH_MESSAGE",
    "TEACHER_ASSIGNMENT_INACTIVE_SUBJECT_MESSAGE",
    "TEACHER_ASSIGNMENT_INACTIVE_TEACHER_MESSAGE",
    "TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE",
    "TEACHER_ASSIGNMENT_SUBJECT_NOT_FOUND_MESSAGE",
    "TeacherAssignmentService",
    "TeacherAssignmentServiceDep",
    "get_teacher_assignment_service",
]
