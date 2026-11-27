"""Router para Registro e Consulta de Observações Pedagógicas com Acesso Restrito e Criptografia (EPIC-08 / BE-045)."""

from fastapi import APIRouter, Request, status

from app.core.security import CurrentUserDep
from app.schemas.base import UUIDPathParam
from app.schemas.pedagogical_note import (
    PedagogicalNoteCreateSchema,
    PedagogicalNoteListParamsDep,
    PedagogicalNotePaginatedResponseSchema,
    PedagogicalNoteResponseSchema,
)
from app.services.pedagogical_note_service import PedagogicalNoteServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Communication"],
)


@router.post(
    "/pedagogical-notes",
    response_model=PedagogicalNoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar observação pedagógica restrita e criptografada (Fernet / AES-256)",
)
async def create_pedagogical_note(
    payload: PedagogicalNoteCreateSchema,
    request: Request,
    pedagogical_note_service: PedagogicalNoteServiceDep,
    current_user: CurrentUserDep,
) -> PedagogicalNoteResponseSchema:
    """Registra anotação pedagógica de acompanhamento criptografada com controle de visibility_scope e auditoria em audit_logs (BE-045)."""
    client_ip = request.client.host if request.client is not None else None
    return pedagogical_note_service.create_pedagogical_note(
        payload,
        current_user=current_user,
        ip_address=client_ip,
    )


@router.get(
    "/students/{id}/pedagogical-notes",
    response_model=PedagogicalNotePaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar observações pedagógicas restritas de um estudante filtradas por visibility_scope",
)
async def list_student_pedagogical_notes(
    id: UUIDPathParam,
    params: PedagogicalNoteListParamsDep,
    request: Request,
    pedagogical_note_service: PedagogicalNoteServiceDep,
    current_user: CurrentUserDep,
) -> PedagogicalNotePaginatedResponseSchema:
    """Retorna observações pedagógicas do estudante filtradas por visibility_scope; bloqueia e audita qualquer tentativa por perfil STUDENT (BE-045)."""
    client_ip = request.client.host if request.client is not None else None
    return pedagogical_note_service.list_student_pedagogical_notes(
        id,
        params,
        current_user=current_user,
        ip_address=client_ip,
    )


__all__ = ["router"]
