"""Router administrativo para Matrículas de Estudantes em Turmas (EPIC-02 / BE-016)."""

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.schemas.enrollment import EnrollmentCreateSchema, EnrollmentResponseSchema
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


__all__ = ["router"]
