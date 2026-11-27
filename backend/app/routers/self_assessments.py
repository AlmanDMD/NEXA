"""Router para Cadastro, Reabertura, Consulta, Submissão de Autoavaliação, Motor de Cruzamento e Discrepâncias Diagnósticas (EPIC-07 / BE-035 / BE-036 / BE-037 / BE-038)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.class_period_guard import check_class_is_active
from app.core.security import CurrentUserDep, require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.self_assessment import (
    ClassSelfAssessmentFormsListResponseSchema,
    ClassSelfAssessmentFormsParamsDep,
    DiagnosticDiscrepanciesListResponseSchema,
    DiagnosticDiscrepanciesParamsDep,
    DiagnosticEngineEvaluationResponseSchema,
    SelfAssessmentFormCreateSchema,
    SelfAssessmentFormResponseSchema,
    SelfAssessmentFormUpdateWindowSchema,
    StudentSelfAssessmentSubmitRequestSchema,
    StudentSelfAssessmentSubmitResponseSchema,
)
from app.services.diagnostic_service import DiagnosticServiceDep
from app.services.self_assessment_service import SelfAssessmentServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Self Assessments"],
)


@router.post(
    "/self-assessments/forms",
    response_model=SelfAssessmentFormResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar e ativar questionário de autoavaliação de competências de um módulo prático",
)
async def create_self_assessment_form(
    payload: SelfAssessmentFormCreateSchema,
    self_assessment_service: SelfAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
    _class_guard: Annotated[object, Depends(check_class_is_active("body_class_id"))] = None,
) -> SelfAssessmentFormResponseSchema:
    """Cria ciclo de autoavaliação validando competências do módulo (module_competencies) e janela opens_at < closes_at."""
    return self_assessment_service.create_self_assessment_form(
        payload,
        current_user=current_user,
    )


@router.patch(
    "/self-assessments/forms/{form_id}",
    response_model=SelfAssessmentFormResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Reabrir prazo ou atualizar janela e status de questionário de autoavaliação",
)
@router.put(
    "/self-assessments/forms/{form_id}",
    response_model=SelfAssessmentFormResponseSchema,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_self_assessment_form_window(
    form_id: UUIDPathParam,
    payload: SelfAssessmentFormUpdateWindowSchema,
    self_assessment_service: SelfAssessmentServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
    _class_guard: Annotated[object, Depends(check_class_is_active("form_id"))] = None,
) -> SelfAssessmentFormResponseSchema:
    """Permite ao docente/gestor reabrir ou prorrogar o prazo (opens_at < closes_at) de um ciclo de autoavaliação."""
    return self_assessment_service.update_or_reopen_self_assessment_form(
        form_id,
        payload,
        current_user=current_user,
    )


@router.get(
    "/classes/{class_id}/self-assessments/forms",
    response_model=ClassSelfAssessmentFormsListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar questionários de autoavaliação da turma com competências do módulo e escala de 1 a 5",
)
async def list_class_self_assessment_forms(
    class_id: UUIDPathParam,
    params: ClassSelfAssessmentFormsParamsDep,
    self_assessment_service: SelfAssessmentServiceDep,
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
) -> ClassSelfAssessmentFormsListResponseSchema:
    """Retorna formulários de autoavaliação da turma (filtrando os pendentes de resposta para o aluno logado)."""
    return self_assessment_service.list_class_self_assessment_forms(
        class_id,
        params,
        current_user=current_user,
    )


@router.post(
    "/self-assessments/submit",
    response_model=StudentSelfAssessmentSubmitResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submeter respostas de autoavaliação de habilidades práticas pelo estudante autenticado",
)
async def submit_student_self_assessment(
    payload: StudentSelfAssessmentSubmitRequestSchema,
    self_assessment_service: SelfAssessmentServiceDep,
    current_user: CurrentUserDep,
    _class_guard: Annotated[object, Depends(check_class_is_active("body_form_id"))] = None,
) -> StudentSelfAssessmentSubmitResponseSchema:
    """Grava as respostas do estudante logado em student_self_assessments, sugere pedido de ajuda quando perceived_level <= 2 e dispara o cruzamento diagnóstico."""
    return self_assessment_service.submit_student_self_assessment(
        payload,
        current_user=current_user,
    )


@router.post(
    "/classes/{class_id}/diagnostics/evaluate",
    response_model=DiagnosticEngineEvaluationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Executar motor de cruzamento diagnóstico (Autoavaliação vs. Avaliação Prática do Docente) para a turma",
)
@router.post(
    "/self-assessments/diagnostics/evaluate/{class_id}",
    response_model=DiagnosticEngineEvaluationResponseSchema,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def evaluate_class_explainable_diagnostics(
    class_id: UUIDPathParam,
    diagnostic_service: DiagnosticServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
    module_id: Annotated[
        UUID | None,
        Query(description="Filtro opcional pelo UUID do módulo prático"),
    ] = None,
    student_id: Annotated[
        UUID | None,
        Query(description="Filtro opcional pelo UUID do estudante"),
    ] = None,
) -> DiagnosticEngineEvaluationResponseSchema:
    """Consulta vw_self_eval_discrepancy, grava explainable_diagnostics com critérios, evidências e limitações explícitas e gera alertas pedagógicos (BE-037)."""
    return diagnostic_service.evaluate_class_diagnostics(
        class_id,
        module_id=module_id,
        student_id=student_id,
        current_user=current_user,
    )


@router.get(
    "/diagnostics/discrepancies",
    response_model=DiagnosticDiscrepanciesListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar mapa comparativo de discrepâncias entre autoavaliação e avaliações práticas (BE-038)",
)
async def get_diagnostic_discrepancies(
    params: DiagnosticDiscrepanciesParamsDep,
    diagnostic_service: DiagnosticServiceDep,
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
) -> DiagnosticDiscrepanciesListResponseSchema:
    """Disponibiliza visualização comparativa entre autoavaliação e evidências práticas de aprendizagem (BE-038).

    - Estudante: visualiza apenas o próprio comparativo com linguagem pedagógica construtiva.
    - Professor: visualiza o mapa de divergências de toda a turma com filtros por módulo, competência e tipo diagnóstico.
    - Coordenação / Admin: visão multidisciplinar irrestrita para apoio pedagógico.
    """
    return diagnostic_service.get_discrepancies(
        params,
        current_user=current_user,
    )


__all__ = ["router"]
