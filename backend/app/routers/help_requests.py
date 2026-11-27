"""Router para Abertura e Consulta de Solicitações de Apoio Confidenciais pelo Aluno (EPIC-08 / BE-043)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.enums import UserRole
from app.schemas.help_request import (
    HelpRequestCreateSchema,
    HelpRequestListParamsDep,
    HelpRequestPaginatedResponseSchema,
    HelpRequestResponseSchema,
)
from app.services.help_request_service import HelpRequestServiceDep

router = APIRouter(
    prefix="/api/v1/help-requests",
    tags=["Communication"],
)


@router.post(
    "",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir solicitação confidencial de apoio pedagógico ou mentoria pelo estudante",
)
async def create_help_request(
    payload: HelpRequestCreateSchema,
    help_request_service: HelpRequestServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.STUDENT)),
    ],
) -> HelpRequestResponseSchema:
    """Abre um pedido de ajuda confidencial direcionado automaticamente ao professor titular da disciplina na turma do aluno (BE-043)."""
    return help_request_service.create_help_request(
        payload,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=HelpRequestPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar solicitações de apoio com proteção estrita de confidencialidade",
)
async def list_help_requests(
    params: HelpRequestListParamsDep,
    help_request_service: HelpRequestServiceDep,
    current_user: Annotated[
        User,
        Depends(
            require_role(
                UserRole.ADMIN,
                UserRole.COORDINATOR,
                UserRole.TEACHER,
                UserRole.STUDENT,
            )
        ),
    ],
) -> HelpRequestPaginatedResponseSchema:
    """Retorna exclusivamente os próprios pedidos para estudantes ou os pedidos das disciplinas/turmas atribuídas para docentes (BE-043)."""
    return help_request_service.list_help_requests(
        params,
        current_user=current_user,
    )


__all__ = ["router"]
