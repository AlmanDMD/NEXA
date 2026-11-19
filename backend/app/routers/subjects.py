"""Router para CRUD de Disciplinas do Currículo Técnico SENAI (EPIC-02 / BE-013)."""

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.subject import (
    SubjectCreateSchema,
    SubjectListParamsDep,
    SubjectPaginatedResponseSchema,
    SubjectResponseSchema,
    SubjectUpdateSchema,
)
from app.services.subject_service import SubjectServiceDep

router = APIRouter(
    prefix="/api/v1/subjects",
    tags=["Subjects"],
)


@router.get(
    "",
    response_model=SubjectPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER))],
    summary="Listar disciplinas técnicas com filtro por curso e status ativo",
)
async def list_subjects(
    params: SubjectListParamsDep,
    subject_service: SubjectServiceDep,
) -> SubjectPaginatedResponseSchema:
    """Retorna lista paginada { data, total, page, limit } de disciplinas técnicas."""
    return subject_service.list_subjects(params)


@router.post(
    "",
    response_model=SubjectResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Cadastrar nova disciplina do currículo técnico",
)
async def create_subject(
    payload: SubjectCreateSchema,
    subject_service: SubjectServiceDep,
) -> SubjectResponseSchema:
    """Cadastra uma nova disciplina vinculada a curso ativo validando carga horária positiva."""
    return subject_service.create_subject(payload)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER))],
    summary="Consultar detalhes de disciplina técnica por ID",
)
async def get_subject(
    subject_id: UUIDPathParam,
    subject_service: SubjectServiceDep,
) -> SubjectResponseSchema:
    """Retorna os dados detalhados de uma disciplina técnica pelo UUID."""
    return subject_service.get_subject(subject_id)


@router.put(
    "/{subject_id}",
    response_model=SubjectResponseSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Atualizar dados de disciplina técnica",
)
async def update_subject(
    subject_id: UUIDPathParam,
    payload: SubjectUpdateSchema,
    subject_service: SubjectServiceDep,
) -> SubjectResponseSchema:
    """Atualiza informações da disciplina técnica, ementa, carga horária, curso ou status ativo."""
    return subject_service.update_subject(subject_id, payload)


__all__ = ["router"]
