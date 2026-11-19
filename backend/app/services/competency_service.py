"""Serviço de domínio para gestão de Competências Técnicas e Vínculos com Módulos (BE-015)."""

from decimal import Decimal
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.logging import logger
from app.models.learning_module import LearningModule
from app.models.user import User
from app.repositories.competency_repository import (
    CompetencyRepository,
    CompetencyRepositoryDep,
)
from app.repositories.learning_module_repository import (
    LearningModuleRepository,
    LearningModuleRepositoryDep,
)
from app.schemas.competency import (
    CompetencyCreateSchema,
    CompetencyListQueryParams,
    CompetencyPaginatedResponseSchema,
    CompetencyResponseSchema,
    LearningModuleSummarySchema,
    ModuleCompetenciesAggregatedResponseSchema,
    ModuleCompetencyCreateSchema,
    ModuleCompetencyResponseSchema,
)
from app.schemas.enums import CompetencyCategory, UserRole

COMPETENCY_NOT_FOUND_MESSAGE: Final[str] = "Competência técnica não encontrada."
COMPETENCY_CODE_CONFLICT_MESSAGE: Final[str] = (
    "Já existe uma competência cadastrada com este código."
)
MODULE_NOT_FOUND_MESSAGE: Final[str] = "Módulo de aprendizagem prática não encontrado."
MODULE_COMPETENCY_CONFLICT_MESSAGE: Final[str] = (
    "Esta competência já está vinculada a este módulo prático."
)
MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado na disciplina deste módulo."
)


class CompetencyService:
    """Serviço responsável pelo catálogo de competências e sua associação com módulos práticos."""

    def __init__(
        self,
        repository: CompetencyRepository,
        learning_module_repository: LearningModuleRepository,
    ) -> None:
        self._repository = repository
        self._learning_module_repository = learning_module_repository

    def _ensure_module_access(self, module_id: UUID, *, current_user: User) -> LearningModule:
        """Valida existência do módulo prático e autorização contextual para docentes alocados."""
        module = self._learning_module_repository.get_by_id(module_id)
        if module is None:
            raise NotFoundException(message=MODULE_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._learning_module_repository.is_teacher_assigned_to_subject(
                teacher_id=current_user.id,
                subject_id=module.subject_id,
            )
        ):
            raise ForbiddenException(message=MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE)

        return module

    def list_competencies(
        self,
        params: CompetencyListQueryParams,
    ) -> CompetencyPaginatedResponseSchema:
        """Lista competências técnicas paginadas com filtro por categoria e busca textual."""
        items, total = self._repository.list_competencies(
            page=params.page,
            limit=params.limit,
            category=params.category,
            search=params.search,
        )
        return CompetencyPaginatedResponseSchema(
            data=[CompetencyResponseSchema.model_validate(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def create_competency(self, payload: CompetencyCreateSchema) -> CompetencyResponseSchema:
        """Cadastra uma nova competência técnica garantindo unicidade do código."""
        existing = self._repository.get_by_code(payload.code)
        if existing is not None:
            raise ConflictException(message=COMPETENCY_CODE_CONFLICT_MESSAGE)

        created = self._repository.create(
            code=payload.code,
            title=payload.title,
            category=payload.category,
            description=payload.description,
        )
        logger.bind(
            competency_id=str(created.id),
            code=created.code,
            category=created.category.value,
        ).info("Nova competência técnica cadastrada com sucesso.")
        return CompetencyResponseSchema.model_validate(created)

    def link_competency_to_module(
        self,
        module_id: UUID,
        payload: ModuleCompetencyCreateSchema,
        *,
        current_user: User,
    ) -> ModuleCompetencyResponseSchema:
        """Associa uma competência técnica a um módulo prático com peso e nível requerido (1..5)."""
        module = self._ensure_module_access(module_id, current_user=current_user)

        competency = self._repository.get_by_id(payload.competency_id)
        if competency is None:
            raise NotFoundException(message=COMPETENCY_NOT_FOUND_MESSAGE)

        existing = self._repository.get_module_competency(
            module_id=module.id,
            competency_id=competency.id,
        )
        if existing is not None:
            raise ConflictException(message=MODULE_COMPETENCY_CONFLICT_MESSAGE)

        link = self._repository.link_to_module(
            module_id=module.id,
            competency_id=competency.id,
            weight=payload.weight,
            required_level=payload.required_level,
        )
        logger.bind(
            module_id=str(module.id),
            competency_id=str(competency.id),
            competency_code=competency.code,
            weight=str(link.weight),
            required_level=link.required_level,
            actor_id=str(current_user.id),
        ).info("Competência técnica associada ao módulo prático com sucesso.")
        return ModuleCompetencyResponseSchema.model_validate(link)

    def list_module_competencies(
        self,
        module_id: UUID,
        *,
        current_user: User,
    ) -> ModuleCompetenciesAggregatedResponseSchema:
        """Consulta competências agregadas por módulo prático para suporte a gráfico radar."""
        module = self._ensure_module_access(module_id, current_user=current_user)
        links = self._repository.list_by_module(module_id=module.id)

        total_competencies = len(links)
        total_weight = sum((item.weight for item in links), Decimal("0.00")).quantize(
            Decimal("0.01")
        )
        categories_summary: dict[str, int] = {cat.value: 0 for cat in CompetencyCategory}
        for item in links:
            category_key = item.competency.category.value
            categories_summary[category_key] = categories_summary.get(category_key, 0) + 1

        return ModuleCompetenciesAggregatedResponseSchema(
            module=LearningModuleSummarySchema.model_validate(module),
            total_competencies=total_competencies,
            total_weight=total_weight,
            categories_summary=categories_summary,
            data=[ModuleCompetencyResponseSchema.model_validate(item) for item in links],
        )


def get_competency_service(
    repository: CompetencyRepositoryDep,
    learning_module_repository: LearningModuleRepositoryDep,
) -> CompetencyService:
    """Provedor de injeção de dependência para CompetencyService."""
    return CompetencyService(
        repository=repository,
        learning_module_repository=learning_module_repository,
    )


CompetencyServiceDep = Annotated[
    CompetencyService,
    Depends(get_competency_service),
]

__all__ = [
    "COMPETENCY_CODE_CONFLICT_MESSAGE",
    "COMPETENCY_NOT_FOUND_MESSAGE",
    "CompetencyService",
    "CompetencyServiceDep",
    "MODULE_COMPETENCY_CONFLICT_MESSAGE",
    "MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE",
    "MODULE_NOT_FOUND_MESSAGE",
    "get_competency_service",
]
