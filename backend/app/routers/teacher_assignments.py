"""Router administrativo para Alocação de Docentes em Disciplinas/Turmas (EPIC-02 / BE-018)."""

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.schemas.enums import UserRole
from app.schemas.teacher_assignment import (
    TeacherAssignmentCreateSchema,
    TeacherAssignmentResponseSchema,
)
from app.services.teacher_assignment_service import TeacherAssignmentServiceDep

router = APIRouter(
    prefix="/api/v1/teacher-assignments",
    tags=["Teacher Assignments"],
)


@router.post(
    "",
    response_model=TeacherAssignmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
    summary="Alocar docente em disciplina técnica e turma acadêmica",
)
async def create_teacher_assignment(
    payload: TeacherAssignmentCreateSchema,
    assignment_service: TeacherAssignmentServiceDep,
) -> TeacherAssignmentResponseSchema:
    """Vincula um usuário TEACHER a uma disciplina e turma, suportando múltiplos instrutores por oficina."""
    return assignment_service.create_assignment(payload)


__all__ = ["router"]
