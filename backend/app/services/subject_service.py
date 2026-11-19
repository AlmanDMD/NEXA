"""Serviço de domínio para gestão de Disciplinas do Currículo Técnico (BE-013)."""

from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.repositories.course_repository import CourseRepository, CourseRepositoryDep
from app.repositories.subject_repository import SubjectRepository, SubjectRepositoryDep
from app.schemas.subject import (
    SubjectCreateSchema,
    SubjectListQueryParams,
    SubjectPaginatedResponseSchema,
    SubjectResponseSchema,
    SubjectUpdateSchema,
)

SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina não encontrada."
SUBJECT_COURSE_NOT_FOUND_MESSAGE: Final[str] = "Curso técnico não encontrado."
SUBJECT_INACTIVE_COURSE_MESSAGE: Final[str] = (
    "Não é possível vincular disciplina a um curso técnico inativo."
)
SUBJECT_ACTIVATION_INACTIVE_COURSE_MESSAGE: Final[str] = (
    "Não é possível ativar uma disciplina vinculada a um curso técnico inativo."
)
SUBJECT_CODE_COURSE_CONFLICT_MESSAGE: Final[str] = (
    "Já existe uma disciplina cadastrada com este código neste curso técnico."
)


class SubjectService:
    """Serviço responsável pelas regras de negócio do CRUD de disciplinas técnicas."""

    def __init__(
        self,
        repository: SubjectRepository,
        course_repository: CourseRepository,
    ) -> None:
        self._repository = repository
        self._course_repository = course_repository

    def list_subjects(
        self,
        params: SubjectListQueryParams,
    ) -> SubjectPaginatedResponseSchema:
        """Lista disciplinas paginadas com filtros por curso, status ativo e busca textual."""
        items, total = self._repository.list_subjects(
            page=params.page,
            limit=params.limit,
            course_id=params.course_id,
            is_active=params.is_active,
            search=params.search,
        )
        return SubjectPaginatedResponseSchema(
            data=[SubjectResponseSchema.model_validate(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def get_subject(self, subject_id: UUID) -> SubjectResponseSchema:
        """Obtém os detalhes de uma disciplina técnica pelo UUID."""
        subject = self._repository.get_by_id(subject_id)
        if subject is None:
            raise NotFoundException(message=SUBJECT_NOT_FOUND_MESSAGE)
        return SubjectResponseSchema.model_validate(subject)

    def create_subject(self, payload: SubjectCreateSchema) -> SubjectResponseSchema:
        """Cadastra uma nova disciplina vinculada a curso ativo garantindo unicidade de código no curso."""
        course = self._course_repository.get_by_id(payload.course_id)
        if course is None:
            raise NotFoundException(message=SUBJECT_COURSE_NOT_FOUND_MESSAGE)

        if not course.is_active:
            raise UnprocessableEntityException(message=SUBJECT_INACTIVE_COURSE_MESSAGE)

        existing = self._repository.get_by_course_and_code(payload.course_id, payload.code)
        if existing is not None:
            raise ConflictException(message=SUBJECT_CODE_COURSE_CONFLICT_MESSAGE)

        created = self._repository.create(
            course_id=payload.course_id,
            code=payload.code,
            name=payload.name,
            workload_hours=payload.workload_hours,
            syllabus=payload.syllabus,
            is_active=payload.is_active,
        )
        logger.bind(
            subject_id=str(created.id),
            course_id=str(created.course_id),
            code=created.code,
            workload_hours=created.workload_hours,
        ).info("Nova disciplina técnica cadastrada com sucesso.")
        return SubjectResponseSchema.model_validate(created)

    def update_subject(
        self,
        subject_id: UUID,
        payload: SubjectUpdateSchema,
    ) -> SubjectResponseSchema:
        """Atualiza uma disciplina validando curso destino, unicidade de código e status ativo."""
        subject = self._repository.get_by_id(subject_id)
        if subject is None:
            raise NotFoundException(message=SUBJECT_NOT_FOUND_MESSAGE)

        updates = {field: getattr(payload, field) for field in payload.model_fields_set}

        target_course = subject.course
        target_course_id = updates.get("course_id", subject.course_id)
        if "course_id" in updates and updates["course_id"] != subject.course_id:
            target_course = self._course_repository.get_by_id(target_course_id)
            if target_course is None:
                raise NotFoundException(message=SUBJECT_COURSE_NOT_FOUND_MESSAGE)
            if not target_course.is_active:
                raise UnprocessableEntityException(message=SUBJECT_INACTIVE_COURSE_MESSAGE)

        if "course_id" in updates or "code" in updates:
            target_code = updates.get("code", subject.code)
            existing = self._repository.get_by_course_and_code(target_course_id, target_code)
            if existing is not None and existing.id != subject.id:
                raise ConflictException(message=SUBJECT_CODE_COURSE_CONFLICT_MESSAGE)

        if (
            updates.get("is_active") is True
            and not subject.is_active
            and not target_course.is_active
        ):
            raise UnprocessableEntityException(message=SUBJECT_ACTIVATION_INACTIVE_COURSE_MESSAGE)

        updated = self._repository.update(subject, updates=updates)
        logger.bind(
            subject_id=str(updated.id),
            course_id=str(updated.course_id),
            code=updated.code,
            updated_fields=sorted(updates.keys()),
        ).info("Disciplina técnica atualizada com sucesso.")
        return SubjectResponseSchema.model_validate(updated)


def get_subject_service(
    repository: SubjectRepositoryDep,
    course_repository: CourseRepositoryDep,
) -> SubjectService:
    """Provedor de injeção de dependência para SubjectService."""
    return SubjectService(
        repository=repository,
        course_repository=course_repository,
    )


SubjectServiceDep = Annotated[SubjectService, Depends(get_subject_service)]

__all__ = [
    "SUBJECT_ACTIVATION_INACTIVE_COURSE_MESSAGE",
    "SUBJECT_CODE_COURSE_CONFLICT_MESSAGE",
    "SUBJECT_COURSE_NOT_FOUND_MESSAGE",
    "SUBJECT_INACTIVE_COURSE_MESSAGE",
    "SUBJECT_NOT_FOUND_MESSAGE",
    "SubjectService",
    "SubjectServiceDep",
    "get_subject_service",
]
