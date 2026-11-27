"""Router para Cadastro, Reabertura, Consulta e Submissão de Questionários de Autoavaliação de Competências (EPIC-07 / BE-035 / BE-036)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.class_period_guard import check_class_is_active
from app.core.security import CurrentUserDep, require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.self_assessment import (
    ClassSelfAssessmentFormsListResponseSchema,
    ClassSelfAssessmentFormsParamsDep,
    SelfAssessmentFormCreateSchema,
    SelfAssessmentFormResponseSchema,
    SelfAssessmentFormUpdateWindowSchema,
    StudentSelfAssessmentSubmitRequestSchema,
    StudentSelfAssessmentSubmitResponseSchema,
)
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


__all__ = ["router"]
