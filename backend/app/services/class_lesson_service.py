"""Serviço de domínio para Diário de Classe e Registro de Aulas Ministradas (BE-021)."""

from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.class_lesson import ClassLesson
from app.models.user import User
from app.repositories.class_lesson_repository import (
    ClassLessonRepository,
    ClassLessonRepositoryDep,
)
from app.schemas.class_lesson import (
    ClassLessonCreateSchema,
    ClassLessonListQueryParams,
    ClassLessonPaginatedResponseSchema,
    ClassLessonResponseSchema,
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
    LessonTeacherSummarySchema,
)
from app.schemas.enums import ClassStatus, UserRole

LESSON_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
LESSON_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina técnica não encontrada."
LESSON_MODULE_NOT_FOUND_MESSAGE: Final[str] = "Módulo de aprendizagem prática não encontrado."
LESSON_TEACHER_NOT_FOUND_MESSAGE: Final[str] = "Docente não encontrado."
LESSON_INVALID_TEACHER_ROLE_MESSAGE: Final[str] = (
    "O usuário indicado como docente não possui perfil TEACHER cadastrado."
)
LESSON_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa para esta turma e disciplina."
)
LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado nesta turma."
)
LESSON_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível registrar aula em uma turma que não está ativa."
)
LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "A disciplina informada não pertence ao curso técnico da turma."
)
LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence à disciplina selecionada."
)


class ClassLessonService:
    """Serviço responsável pelo registro diário de aulas, RBAC docente e chamada inicial."""

    def __init__(self, repository: ClassLessonRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_response(lesson: ClassLesson) -> ClassLessonResponseSchema:
        """Converte ClassLesson ORM no schema detalhado com contagem de chamada inicializada."""
        teacher = lesson.teacher
        profile = teacher.profile
        return ClassLessonResponseSchema(
            id=lesson.id,
            class_id=lesson.class_id,
            subject_id=lesson.subject_id,
            module_id=lesson.module_id,
            teacher_id=lesson.teacher_id,
            lesson_date=lesson.lesson_date,
            workload_hours=lesson.workload_hours,
            topic_summary=lesson.topic_summary,
            lab_environment=lesson.lab_environment,
            initialized_attendance_count=len(lesson.attendance_records),
            teacher=LessonTeacherSummarySchema(
                id=teacher.id,
                email=teacher.email,
                full_name=profile.full_name if profile is not None else None,
                registration_number=(
                    profile.registration_number if profile is not None else None
                ),
            ),
            subject=LessonSubjectSummarySchema.model_validate(lesson.subject),
            module=(
                LessonModuleSummarySchema.model_validate(lesson.module)
                if lesson.module is not None
                else None
            ),
            created_at=lesson.created_at,
        )

    def create_lesson(
        self,
        payload: ClassLessonCreateSchema,
        *,
        current_user: User,
    ) -> ClassLessonResponseSchema:
        """Registra aula ministrada validando alocação docente, turma ativa e módulo vinculado."""
        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=LESSON_CLASS_NOT_FOUND_MESSAGE)

        subject = self._repository.get_subject_by_id(payload.subject_id)
        if subject is None:
            raise NotFoundException(message=LESSON_SUBJECT_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER:
            if (
                payload.teacher_id is not None and payload.teacher_id != current_user.id
            ) or not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            ):
                raise ForbiddenException(message=LESSON_TEACHER_FORBIDDEN_MESSAGE)
            resolved_teacher_id = current_user.id
        else:
            if payload.teacher_id is not None:
                assigned_teacher = self._repository.get_user_by_id(payload.teacher_id)
                if assigned_teacher is None:
                    raise NotFoundException(message=LESSON_TEACHER_NOT_FOUND_MESSAGE)
                if assigned_teacher.role != UserRole.TEACHER:
                    raise BadRequestException(message=LESSON_INVALID_TEACHER_ROLE_MESSAGE)
                resolved_teacher_id = assigned_teacher.id
            else:
                resolved_teacher_id = current_user.id

        if academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=LESSON_INACTIVE_CLASS_MESSAGE)

        if subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(message=LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE)

        if payload.module_id is not None:
            module = self._repository.get_module_by_id(payload.module_id)
            if module is None:
                raise NotFoundException(message=LESSON_MODULE_NOT_FOUND_MESSAGE)
            if module.subject_id != subject.id:
                raise UnprocessableEntityException(
                    message=LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE
                )

        created = self._repository.create_lesson_with_initial_attendance(
            class_id=academic_class.id,
            subject_id=subject.id,
            module_id=payload.module_id,
            teacher_id=resolved_teacher_id,
            lesson_date=payload.lesson_date,
            workload_hours=payload.workload_hours,
            topic_summary=payload.topic_summary,
            lab_environment=payload.lab_environment,
        )
        logger.bind(
            lesson_id=str(created.id),
            class_id=str(created.class_id),
            subject_id=str(created.subject_id),
            module_id=str(created.module_id) if created.module_id else None,
            teacher_id=str(created.teacher_id),
            lesson_date=created.lesson_date.isoformat(),
            workload_hours=created.workload_hours,
            initialized_attendance_count=len(created.attendance_records),
        ).info("Aula ministrada registrada com chamada em lote pré-inicializada.")
        return self._to_response(created)

    def list_class_lessons(
        self,
        class_id: UUID,
        params: ClassLessonListQueryParams,
        *,
        current_user: User,
    ) -> ClassLessonPaginatedResponseSchema:
        """Lista aulas do diário de classe de uma turma com filtros e RBAC docente contextual."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=LESSON_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
        ):
            raise ForbiddenException(message=LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE)

        items, total = self._repository.list_by_class(
            academic_class.id,
            page=params.page,
            limit=params.limit,
            subject_id=params.subject_id,
            module_id=params.module_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return ClassLessonPaginatedResponseSchema(
            data=[self._to_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )


def get_class_lesson_service(
    repository: ClassLessonRepositoryDep,
) -> ClassLessonService:
    """Provedor de injeção de dependência para ClassLessonService."""
    return ClassLessonService(repository=repository)


ClassLessonServiceDep = Annotated[
    ClassLessonService,
    Depends(get_class_lesson_service),
]

__all__ = [
    "ClassLessonService",
    "ClassLessonServiceDep",
    "LESSON_CLASS_NOT_FOUND_MESSAGE",
    "LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE",
    "LESSON_INACTIVE_CLASS_MESSAGE",
    "LESSON_INVALID_TEACHER_ROLE_MESSAGE",
    "LESSON_MODULE_NOT_FOUND_MESSAGE",
    "LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE",
    "LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE",
    "LESSON_SUBJECT_NOT_FOUND_MESSAGE",
    "LESSON_TEACHER_FORBIDDEN_MESSAGE",
    "LESSON_TEACHER_NOT_FOUND_MESSAGE",
    "get_class_lesson_service",
]
