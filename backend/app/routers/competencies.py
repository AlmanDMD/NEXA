"""Router para Gestão de Competências Técnicas e Associação com Módulos Práticos (EPIC-04 / BE-015)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.competency import (
    CompetencyCreateSchema,
    CompetencyListParamsDep,
    CompetencyPaginatedResponseSchema,
    CompetencyResponseSchema,
    ModuleCompetenciesAggregatedResponseSchema,
    ModuleCompetencyCreateSchema,
    ModuleCompetencyResponseSchema,
)
from app.schemas.enums import UserRole
from app.services.competency_service import CompetencyServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Competencies"],
)


@router.get(
    "/competencies",
    response_model=CompetencyPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER))],
    summary="Listar catálogo de competências técnicas com busca e filtro por categoria",
)
async def list_competencies(
    params: CompetencyListParamsDep,
    competency_service: CompetencyServiceDep,
) -> CompetencyPaginatedResponseSchema:
    """Retorna lista paginada { data, total, page, limit } do catálogo de competências."""
    return competency_service.list_competencies(params)


@router.post(
    "/competencies",
    response_model=CompetencyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Cadastrar nova competência ou habilidade técnica no catálogo SENAI",
)
async def create_competency(
    payload: CompetencyCreateSchema,
    competency_service: CompetencyServiceDep,
) -> CompetencyResponseSchema:
    """Cadastra uma competência garantindo unicidade do código institucional."""
    return competency_service.create_competency(payload)


@router.post(
    "/modules/{module_id}/competencies",
    response_model=ModuleCompetencyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular competência técnica a módulo prático com peso e nível requerido",
)
async def link_competency_to_module(
    module_id: UUIDPathParam,
    payload: ModuleCompetencyCreateSchema,
    competency_service: CompetencyServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ModuleCompetencyResponseSchema:
    """Associa competência ao módulo prático validando nível requerido entre 1 e 5."""
    return competency_service.link_competency_to_module(
        module_id,
        payload,
        current_user=current_user,
    )


@router.get(
    "/modules/{module_id}/competencies",
    response_model=ModuleCompetenciesAggregatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalhes agregados de competências associadas a um módulo prático",
)
async def list_module_competencies(
    module_id: UUIDPathParam,
    competency_service: CompetencyServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ModuleCompetenciesAggregatedResponseSchema:
    """Retorna competências associadas ao módulo com peso total e sumário por categoria (radar)."""
    return competency_service.list_module_competencies(
        module_id,
        current_user=current_user,
    )


__all__ = ["router"]
