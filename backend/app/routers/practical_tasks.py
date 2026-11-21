"""Router para Atividades Práticas de Oficina e Critérios de Tolerância (EPIC-04 / BE-024)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.practical_task import (
    PracticalTaskCreateSchema,
    PracticalTaskListParamsDep,
    PracticalTaskPaginatedResponseSchema,
    PracticalTaskResponseSchema,
)
from app.services.practical_task_service import PracticalTaskServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Practical Tasks"],
)


@router.post(
    "/practical-tasks",
    response_model=PracticalTaskResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar atividade prática de oficina com rubricas e gerar entregas pendentes",
)
async def create_practical_task(
    payload: PracticalTaskCreateSchema,
    task_service: PracticalTaskServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> PracticalTaskResponseSchema:
    """Cria tarefa prática validando competências e gera registros PENDING em task_submissions."""
    return task_service.create_practical_task(payload, current_user=current_user)


@router.get(
    "/modules/{module_id}/practical-tasks",
    response_model=PracticalTaskPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar atividades práticas e rubricas vinculadas a um módulo prático",
)
async def list_module_practical_tasks(
    module_id: UUIDPathParam,
    params: PracticalTaskListParamsDep,
    task_service: PracticalTaskServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> PracticalTaskPaginatedResponseSchema:
    """Lista atividades práticas do módulo ordenadas por prazo de entrega com progresso da turma."""
    return task_service.list_module_practical_tasks(
        module_id,
        params,
        current_user=current_user,
    )


__all__ = ["router"]
