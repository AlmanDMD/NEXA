"""Router para CRUD de Turmas Acadêmicas e Períodos Letivos (EPIC-02 / BE-012)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.academic_class import (
    AcademicClassCreateSchema,
    AcademicClassListParamsDep,
    AcademicClassPaginatedResponseSchema,
    AcademicClassResponseSchema,
    AcademicClassStatusUpdateSchema,
    ClassStudentsListParamsDep,
    ClassStudentsResponseSchema,
)
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.services.academic_class_service import AcademicClassServiceDep

router = APIRouter(
    prefix="/api/v1/classes",
    tags=["Classes"],
)


@router.get(
    "",
    response_model=AcademicClassPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar turmas acadêmicas com filtros por curso, período letivo e turno",
)
async def list_classes(
    params: AcademicClassListParamsDep,
    class_service: AcademicClassServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> AcademicClassPaginatedResponseSchema:
    """Retorna lista paginada { data, total, page, limit } de turmas conforme o papel do usuário."""
    return class_service.list_classes(params, current_user=current_user)


@router.post(
    "",
    response_model=AcademicClassResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Criar nova turma acadêmica vinculada a curso técnico",
)
async def create_class(
    payload: AcademicClassCreateSchema,
    class_service: AcademicClassServiceDep,
) -> AcademicClassResponseSchema:
    """Cadastra uma nova turma acadêmica validando curso existente, datas e capacidade máxima."""
    return class_service.create_class(payload)


@router.get(
    "/{class_id}",
    response_model=AcademicClassResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalhes de turma acadêmica com curso e contagem de matriculados",
)
async def get_class(
    class_id: UUIDPathParam,
    class_service: AcademicClassServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> AcademicClassResponseSchema:
    """Retorna os detalhes da turma, resumo do curso e ocupação de vagas (matriculados vs max_students)."""
    return class_service.get_class(class_id, current_user=current_user)


@router.get(
    "/{class_id}/students",
    response_model=ClassStudentsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar lista de estudantes matriculados na turma ordenada alfabeticamente",
)
async def list_class_students(
    class_id: UUIDPathParam,
    params: ClassStudentsListParamsDep,
    class_service: AcademicClassServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassStudentsResponseSchema:
    """Retorna a pauta de estudantes matriculados na turma (ordem alfabética) e metadados da turma."""
    return class_service.list_class_students(
        class_id,
        params=params,
        current_user=current_user,
    )


@router.patch(
    "/{class_id}/status",
    response_model=AcademicClassResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Atualizar status do ciclo de vida da turma acadêmica",
)
async def update_class_status(
    class_id: UUIDPathParam,
    payload: AcademicClassStatusUpdateSchema,
    class_service: AcademicClassServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR)),
    ],
) -> AcademicClassResponseSchema:
    """Atualiza o status da turma (PLANNING, ACTIVE, COMPLETED, ARCHIVED) com governança de transição."""
    return class_service.update_class_status(class_id, payload, current_user=current_user)


__all__ = ["router"]
