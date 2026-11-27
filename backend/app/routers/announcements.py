"""Router para Publicação, Edição, Fixação, Consulta e Exclusão de Avisos no Mural da Turma (EPIC-08 / BE-041 / BE-042)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.class_announcement import (
    ClassAnnouncementCreateSchema,
    ClassAnnouncementListParamsDep,
    ClassAnnouncementPaginatedResponseSchema,
    ClassAnnouncementResponseSchema,
    ClassAnnouncementUpdateSchema,
)
from app.schemas.enums import UserRole
from app.services.class_announcement_service import ClassAnnouncementServiceDep

router = APIRouter(
    prefix="/api/v1/announcements",
    tags=["Communication"],
)


@router.get(
    "",
    response_model=ClassAnnouncementPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar mural de avisos das turmas com filtros e paginação",
)
async def list_class_announcements(
    params: ClassAnnouncementListParamsDep,
    announcement_service: ClassAnnouncementServiceDep,
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
) -> ClassAnnouncementPaginatedResponseSchema:
    """Retorna avisos não expirados das turmas permitidas ordenados por is_pinned DESC e published_at DESC (BE-042)."""
    return announcement_service.list_announcements(
        params,
        current_user=current_user,
    )


@router.post(
    "",
    response_model=ClassAnnouncementResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar aviso oficial no mural da turma ou disciplina",
)
async def create_class_announcement(
    payload: ClassAnnouncementCreateSchema,
    announcement_service: ClassAnnouncementServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassAnnouncementResponseSchema:
    """Publica um comunicado oficial no mural da turma com prioridade (NORMAL, IMPORTANT, URGENT) e fixação opcional."""
    return announcement_service.create_announcement(
        payload,
        current_user=current_user,
    )


@router.patch(
    "/{id}",
    response_model=ClassAnnouncementResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Editar conteúdo, prioridade ou fixação de aviso oficial no mural",
)
async def update_class_announcement(
    id: UUIDPathParam,
    payload: ClassAnnouncementUpdateSchema,
    announcement_service: ClassAnnouncementServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassAnnouncementResponseSchema:
    """Atualiza texto, prioridade, disciplina, expiração ou fixação (is_pinned) de um aviso do mural."""
    return announcement_service.update_announcement(
        id,
        payload,
        current_user=current_user,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Remover aviso oficial do mural da turma",
)
async def delete_class_announcement(
    id: UUIDPathParam,
    announcement_service: ClassAnnouncementServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> Response:
    """Remove um comunicado oficial do mural da turma (apenas autor ou coordenação/admin)."""
    announcement_service.delete_announcement(
        id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
