"""Router para Abertura, Atendimento, Mensagens e Encerramento de Solicitações de Apoio Confidenciais (EPIC-08 / BE-043 / BE-044)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.help_request import (
    HelpRequestCreateSchema,
    HelpRequestListParamsDep,
    HelpRequestMessageCreateSchema,
    HelpRequestPaginatedResponseSchema,
    HelpRequestResponseSchema,
    HelpRequestUpdateSchema,
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


@router.get(
    "/{id}",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Visualizar chamado confidencial de apoio e confirmar leitura das mensagens",
)
async def get_help_request_detail(
    id: UUIDPathParam,
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
) -> HelpRequestResponseSchema:
    """Retorna os detalhes e o histórico de mensagens do chamado, marcando automaticamente is_read=True e read_at para o destinatário (BE-044)."""
    return help_request_service.get_help_request_detail(
        id,
        current_user=current_user,
    )


@router.post(
    "/{id}/messages",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensagem interna no chamado de apoio com atualização de leitura",
)
async def send_help_request_message(
    id: UUIDPathParam,
    payload: HelpRequestMessageCreateSchema,
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
) -> HelpRequestResponseSchema:
    """Envia nova mensagem em chat_messages dentro da solicitação de apoio e confirma leitura das mensagens anteriores da outra parte (BE-044)."""
    return help_request_service.send_message(
        id,
        payload,
        current_user=current_user,
    )


@router.patch(
    "/{id}",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Atualizar status de atendimento ou encerrar solicitação de apoio com resumo de resolução",
)
async def update_help_request_status(
    id: UUIDPathParam,
    payload: HelpRequestUpdateSchema,
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
) -> HelpRequestResponseSchema:
    """Realiza transição de status (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED), grava resolution_summary e registra closed_at ao encerrar (BE-044)."""
    return help_request_service.update_help_request(
        id,
        payload,
        current_user=current_user,
    )


__all__ = ["router"]
