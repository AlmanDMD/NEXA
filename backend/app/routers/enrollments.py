"""Router administrativo para Matrículas de Estudantes em Turmas (EPIC-02 / BE-016 e BE-019)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enrollment import (
    EnrollmentCreateSchema,
    EnrollmentResponseSchema,
    EnrollmentStatusUpdateSchema,
)
from app.schemas.enums import UserRole
from app.services.enrollment_service import EnrollmentServiceDep

router = APIRouter(
    prefix="/api/v1/enrollments",
    tags=["Enrollments"],
)


@router.post(
    "",
    response_model=EnrollmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Matricular estudante em turma acadêmica com validação atômica de vagas",
)
async def create_enrollment(
    payload: EnrollmentCreateSchema,
    enrollment_service: EnrollmentServiceDep,
) -> EnrollmentResponseSchema:
    """Processa matrícula validando turma ativa, capacidade max_students e não duplicidade."""
    return await enrollment_service.create_enrollment(payload)


@router.patch(
    "/{enrollment_id}/status",
    response_model=EnrollmentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Alterar status da matrícula do estudante com registro em log de auditoria",
)
async def update_enrollment_status(
    enrollment_id: UUIDPathParam,
    payload: EnrollmentStatusUpdateSchema,
    request: Request,
    enrollment_service: EnrollmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR)),
    ],
) -> EnrollmentResponseSchema:
    """Atualiza o status da matrícula (ACTIVE, DROPPED, COMPLETED, SUSPENDED) e grava auditoria."""
    client_ip = request.client.host if request.client is not None else None
    return await enrollment_service.update_enrollment_status(
        enrollment_id,
        payload,
        current_user=current_user,
        ip_address=client_ip,
    )


__all__ = ["router"]
