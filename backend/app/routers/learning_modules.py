"""Router para Módulos de Aprendizagem Prática SENAI (EPIC-02 / BE-014)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.learning_module import (
    LearningModuleCreateSchema,
    LearningModuleListParamsDep,
    LearningModulePaginatedResponseSchema,
    LearningModuleResponseSchema,
)
from app.services.learning_module_service import LearningModuleServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Learning Modules"],
)


@router.get(
    "/subjects/{subject_id}/modules",
    response_model=LearningModulePaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar módulos práticos de uma disciplina em ordem didática",
)
async def list_subject_modules(
    subject_id: UUIDPathParam,
    params: LearningModuleListParamsDep,
    module_service: LearningModuleServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> LearningModulePaginatedResponseSchema:
    """Retorna módulos práticos da disciplina ordenados por order_index ascendente."""
    return module_service.list_subject_modules(
        subject_id,
        params,
        current_user=current_user,
    )


@router.post(
    "/modules",
    response_model=LearningModuleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo módulo de aprendizagem prática vinculado a disciplina",
)
async def create_learning_module(
    payload: LearningModuleCreateSchema,
    module_service: LearningModuleServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> LearningModuleResponseSchema:
    """Cadastra módulo prático com horas de oficina e nota de corte validada entre 0.00 e 10.00."""
    return module_service.create_module(payload, current_user=current_user)


__all__ = ["router"]
