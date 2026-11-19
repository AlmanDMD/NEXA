"""Serviço de domínio para gestão administrativa de Cursos Técnicos SENAI (BE-011)."""

from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import logger
from app.repositories.course_repository import CourseRepository, CourseRepositoryDep
from app.schemas.course import (
    CourseCreateSchema,
    CourseListQueryParams,
    CoursePaginatedResponseSchema,
    CourseResponseSchema,
    CourseUpdateSchema,
)

COURSE_NOT_FOUND_MESSAGE: Final[str] = "Curso técnico não encontrado."
COURSE_CODE_CONFLICT_MESSAGE: Final[str] = (
    "Já existe um curso técnico cadastrado com este código."
)
COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE: Final[str] = (
    "Não é possível desativar o curso pois existem turmas ativas vinculadas."
)


class CourseService:
    """Serviço responsável pelas regras de negócio do CRUD de cursos técnicos."""

    def __init__(self, repository: CourseRepository) -> None:
        self._repository = repository

    def list_courses(
        self,
        params: CourseListQueryParams,
    ) -> CoursePaginatedResponseSchema:
        """Lista cursos técnicos paginados com suporte a busca e filtro de status."""
        items, total = self._repository.list_courses(
            page=params.page,
            limit=params.limit,
            search=params.search,
            is_active=params.is_active,
        )
        return CoursePaginatedResponseSchema(
            data=[CourseResponseSchema.model_validate(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def get_course(self, course_id: UUID) -> CourseResponseSchema:
        """Obtém os detalhes de um curso técnico pelo UUID."""
        course = self._repository.get_by_id(course_id)
        if course is None:
            raise NotFoundException(message=COURSE_NOT_FOUND_MESSAGE)
        return CourseResponseSchema.model_validate(course)

    def create_course(self, payload: CourseCreateSchema) -> CourseResponseSchema:
        """Cadastra um novo curso técnico garantindo unicidade do código SENAI."""
        existing = self._repository.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(message=COURSE_CODE_CONFLICT_MESSAGE)

        course = self._repository.create(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            total_hours=payload.total_hours,
            is_active=payload.is_active,
        )
        logger.bind(
            course_id=str(course.id),
            code=course.code,
        ).info("Novo curso técnico cadastrado com sucesso.")
        return CourseResponseSchema.model_validate(course)

    def update_course(
        self,
        course_id: UUID,
        payload: CourseUpdateSchema,
    ) -> CourseResponseSchema:
        """Atualiza um curso técnico validando unicidade de código e regras de desativação."""
        course = self._repository.get_by_id(course_id)
        if course is None:
            raise NotFoundException(message=COURSE_NOT_FOUND_MESSAGE)

        updates = {field: getattr(payload, field) for field in payload.model_fields_set}

        if "code" in updates:
            existing = self._repository.get_by_code(updates["code"])
            if existing is not None and existing.id != course.id:
                raise ConflictException(message=COURSE_CODE_CONFLICT_MESSAGE)

        if updates.get("is_active") is False and self._repository.has_active_classes(course.id):
            raise ConflictException(message=COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE)

        updated = self._repository.update(course, updates=updates)
        logger.bind(
            course_id=str(updated.id),
            code=updated.code,
            updated_fields=sorted(updates.keys()),
        ).info("Curso técnico atualizado com sucesso.")
        return CourseResponseSchema.model_validate(updated)

    def deactivate_course(self, course_id: UUID) -> CourseResponseSchema:
        """Desativa logicamente um curso (soft delete via is_active=False) sem turmas ativas."""
        course = self._repository.get_by_id(course_id)
        if course is None:
            raise NotFoundException(message=COURSE_NOT_FOUND_MESSAGE)

        if self._repository.has_active_classes(course.id):
            raise ConflictException(message=COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE)

        if not course.is_active:
            return CourseResponseSchema.model_validate(course)

        deactivated = self._repository.deactivate(course)
        logger.bind(
            course_id=str(deactivated.id),
            code=deactivated.code,
        ).info("Curso técnico desativado logicamente com sucesso.")
        return CourseResponseSchema.model_validate(deactivated)


def get_course_service(repository: CourseRepositoryDep) -> CourseService:
    """Provedor de injeção de dependência para CourseService."""
    return CourseService(repository=repository)


CourseServiceDep = Annotated[CourseService, Depends(get_course_service)]

__all__ = [
    "COURSE_CODE_CONFLICT_MESSAGE",
    "COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE",
    "COURSE_NOT_FOUND_MESSAGE",
    "CourseService",
    "CourseServiceDep",
    "get_course_service",
]
