"""Serviço de domínio para gestão de Módulos de Aprendizagem Prática SENAI (BE-014)."""

from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.subject import Subject
from app.models.user import User
from app.repositories.learning_module_repository import (
    LearningModuleRepository,
    LearningModuleRepositoryDep,
)
from app.repositories.subject_repository import SubjectRepository, SubjectRepositoryDep
from app.schemas.enums import UserRole
from app.schemas.learning_module import (
    LearningModuleCreateSchema,
    LearningModuleListQueryParams,
    LearningModulePaginatedResponseSchema,
    LearningModuleResponseSchema,
)

LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina não encontrada."
LEARNING_MODULE_INACTIVE_SUBJECT_MESSAGE: Final[str] = (
    "Não é possível cadastrar módulo prático em uma disciplina inativa."
)
LEARNING_MODULE_ORDER_CONFLICT_MESSAGE: Final[str] = (
    "Já existe um módulo prático cadastrado nesta disciplina com este índice de ordenação."
)
LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado nesta disciplina."
)


class LearningModuleService:
    """Serviço responsável pelas regras de negócio e autorização contextual de módulos práticos."""

    def __init__(
        self,
        repository: LearningModuleRepository,
        subject_repository: SubjectRepository,
    ) -> None:
        self._repository = repository
        self._subject_repository = subject_repository

    def _ensure_subject_access(self, subject_id: UUID, *, current_user: User) -> Subject:
        """Valida existência da disciplina e permissão contextual para docentes alocados."""
        subject = self._subject_repository.get_by_id(subject_id)
        if subject is None:
            raise NotFoundException(message=LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_subject(
                teacher_id=current_user.id,
                subject_id=subject.id,
            )
        ):
            raise ForbiddenException(message=LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE)

        return subject

    def list_subject_modules(
        self,
        subject_id: UUID,
        params: LearningModuleListQueryParams,
        *,
        current_user: User,
    ) -> LearningModulePaginatedResponseSchema:
        """Lista módulos práticos de uma disciplina ordenados por order_index ascendente."""
        self._ensure_subject_access(subject_id, current_user=current_user)
        items, total = self._repository.list_by_subject(
            subject_id=subject_id,
            page=params.page,
            limit=params.limit,
            search=params.search,
        )
        return LearningModulePaginatedResponseSchema(
            data=[LearningModuleResponseSchema.model_validate(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def create_module(
        self,
        payload: LearningModuleCreateSchema,
        *,
        current_user: User,
    ) -> LearningModuleResponseSchema:
        """Cadastra um novo módulo prático validando disciplina ativa, permissão e order_index único."""
        subject = self._ensure_subject_access(payload.subject_id, current_user=current_user)

        if not subject.is_active:
            raise UnprocessableEntityException(message=LEARNING_MODULE_INACTIVE_SUBJECT_MESSAGE)

        if payload.order_index is not None:
            existing = self._repository.get_by_subject_and_order_index(
                payload.subject_id,
                payload.order_index,
            )
            if existing is not None:
                raise ConflictException(message=LEARNING_MODULE_ORDER_CONFLICT_MESSAGE)
            resolved_order_index = payload.order_index
        else:
            resolved_order_index = self._repository.get_next_order_index(payload.subject_id)

        created = self._repository.create(
            subject_id=payload.subject_id,
            title=payload.title,
            order_index=resolved_order_index,
            practical_hours=payload.practical_hours,
            description=payload.description,
            module_weight=payload.module_weight,
            passing_score=payload.passing_score,
        )
        logger.bind(
            module_id=str(created.id),
            subject_id=str(created.subject_id),
            order_index=created.order_index,
            practical_hours=created.practical_hours,
            passing_score=str(created.passing_score),
            actor_id=str(current_user.id),
        ).info("Novo módulo de aprendizagem prática cadastrado com sucesso.")
        return LearningModuleResponseSchema.model_validate(created)


def get_learning_module_service(
    repository: LearningModuleRepositoryDep,
    subject_repository: SubjectRepositoryDep,
) -> LearningModuleService:
    """Provedor de injeção de dependência para LearningModuleService."""
    return LearningModuleService(
        repository=repository,
        subject_repository=subject_repository,
    )


LearningModuleServiceDep = Annotated[
    LearningModuleService,
    Depends(get_learning_module_service),
]

__all__ = [
    "LEARNING_MODULE_INACTIVE_SUBJECT_MESSAGE",
    "LEARNING_MODULE_ORDER_CONFLICT_MESSAGE",
    "LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE",
    "LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE",
    "LearningModuleService",
    "LearningModuleServiceDep",
    "get_learning_module_service",
]
