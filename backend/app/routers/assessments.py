"""Router para Avaliações Formativas e Lançamento de Notas em Lote (EPIC-03 / BE-027)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.academic_assessment import (
    AcademicAssessmentCreateSchema,
    AcademicAssessmentListParamsDep,
    AcademicAssessmentPaginatedResponseSchema,
    AcademicAssessmentResponseSchema,
    BatchStudentGradesRequestSchema,
    BatchStudentGradesResponseSchema,
    ClassGradesSummaryParamsDep,
    ClassGradesSummaryResponseSchema,
)
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.services.academic_assessment_service import AcademicAssessmentServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Assessments"],
)


@router.post(
    "/assessments",
    response_model=AcademicAssessmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar prova, microavaliação formativa ou projeto na turma e disciplina",
)
async def create_assessment(
    payload: AcademicAssessmentCreateSchema,
    assessment_service: AcademicAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> AcademicAssessmentResponseSchema:
    """Cadastra avaliação formativa validando turma ativa, disciplina, módulo e alocação docente."""
    return assessment_service.create_assessment(
        payload,
        current_user=current_user,
    )


@router.get(
    "/assessments",
    response_model=AcademicAssessmentPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar avaliações formativas e provas ordenadas por data de aplicação",
)
async def list_assessments(
    params: AcademicAssessmentListParamsDep,
    assessment_service: AcademicAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> AcademicAssessmentPaginatedResponseSchema:
    """Lista avaliações formativas com filtros opcionais por turma, disciplina, módulo e tipo."""
    return assessment_service.list_assessments(
        params,
        current_user=current_user,
    )


@router.post(
    "/assessments/{assessment_id}/grades",
    response_model=BatchStudentGradesResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Lançar notas e recuperações de avaliação formativa em lote com auditoria de retificações",
)
async def record_batch_grades(
    assessment_id: UUIDPathParam,
    payload: BatchStudentGradesRequestSchema,
    request: Request,
    assessment_service: AcademicAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> BatchStudentGradesResponseSchema:
    """Lança notas (0.00 a 10.00) e recuperações em lote na turma e grava retificações em audit_logs."""
    client_ip = request.client.host if request.client is not None else None
    return assessment_service.record_batch_grades(
        assessment_id,
        payload,
        current_user=current_user,
        ip_address=client_ip,
    )


@router.post(
    "/classes/{class_id}/calculate-averages",
    response_model=ClassGradesSummaryResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Calcular e consolidar médias ponderadas da turma atualizando final_grade em enrollments",
)
async def calculate_class_averages(
    class_id: UUIDPathParam,
    assessment_service: AcademicAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassGradesSummaryResponseSchema:
    """Calcula médias ponderadas por módulo/disciplina (student_grades + task_submissions) e atualiza enrollments."""
    return assessment_service.calculate_class_averages(
        class_id,
        current_user=current_user,
    )


@router.get(
    "/classes/{class_id}/grades-summary",
    response_model=ClassGradesSummaryResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar boletim consolidado de médias por aluno, disciplina e módulo da turma",
)
async def get_class_grades_summary(
    class_id: UUIDPathParam,
    params: ClassGradesSummaryParamsDep,
    assessment_service: AcademicAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassGradesSummaryResponseSchema:
    """Retorna o boletim consolidado da turma com situação (APPROVED, IN_RECOVERY, AT_RISK) sem mutar matrículas."""
    return assessment_service.get_class_grades_summary(
        class_id,
        params,
        current_user=current_user,
    )


__all__ = ["router"]
