"""Router para Dashboard Híbrido do Professor e Visão 360° do Aluno (EPIC-05 / BE-031)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.dashboard import (
    Student360OverviewResponseSchema,
    Student360ParamsDep,
    TeacherClassDashboardParamsDep,
    TeacherClassDashboardResponseSchema,
)
from app.schemas.enums import UserRole
from app.schemas.risk_engine import ClassRiskEvaluationResponseSchema
from app.services.dashboard_service import DashboardServiceDep
from app.services.risk_engine_service import RiskEngineServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Dashboard"],
)


@router.get(
    "/dashboard/teacher/classes/{class_id}",
    response_model=TeacherClassDashboardResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar Dashboard Híbrido do Professor com KPIs, evolução modular e lista da turma",
)
async def get_teacher_class_dashboard(
    class_id: UUIDPathParam,
    params: TeacherClassDashboardParamsDep,
    dashboard_service: DashboardServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> TeacherClassDashboardResponseSchema:
    """Agrega KPIs globais, distribuição por módulo e estudantes via vw_student_360_performance."""
    return dashboard_service.get_teacher_class_dashboard(
        class_id,
        params,
        current_user=current_user,
    )


@router.get(
    "/students/{student_id}/360",
    response_model=Student360OverviewResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar Ficha 360° completa do estudante (notas, faltas, oficinas, competências e alertas)",
)
async def get_student_360_overview(
    student_id: UUIDPathParam,
    params: Student360ParamsDep,
    dashboard_service: DashboardServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> Student360OverviewResponseSchema:
    """Retorna a visão multidisciplinar 360° de um estudante para docentes e coordenação."""
    return dashboard_service.get_student_360_overview(
        student_id,
        params,
        current_user=current_user,
    )


@router.post(
    "/dashboard/teacher/classes/{class_id}/evaluate-risk",
    response_model=ClassRiskEvaluationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Executar Motor Explicável de Identificação Precoce de Risco Acadêmico na turma",
)
async def evaluate_class_academic_risk(
    class_id: UUIDPathParam,
    risk_engine_service: RiskEngineServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassRiskEvaluationResponseSchema:
    """Analisa frequência, entregas práticas e médias da turma gravando/atualizando academic_alerts sem duplicidade."""
    return risk_engine_service.evaluate_class_risk(
        class_id,
        current_user=current_user,
    )


__all__ = ["router"]
