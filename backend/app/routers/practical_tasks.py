"""Router para Atividades Práticas de Oficina e Critérios de Tolerância (EPIC-04 / BE-024)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.enums import UserRole
from app.schemas.practical_task import (
    PracticalTaskCreateSchema,
    PracticalTaskListParamsDep,
    PracticalTaskPaginatedResponseSchema,
    PracticalTaskResponseSchema,
    StudentPendingTasksQueryParamsDep,
    StudentPendingTasksResponseSchema,
    TaskEvaluationRequestSchema,
    TaskEvaluationResponseSchema,
)
from app.services.practical_task_service import PracticalTaskServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Practical Tasks"],
)


@router.post(
    "/practical-tasks",
    response_model=PracticalTaskResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar atividade prática de oficina com rubricas e gerar entregas pendentes",
)
async def create_practical_task(
    payload: PracticalTaskCreateSchema,
    task_service: PracticalTaskServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> PracticalTaskResponseSchema:
    """Cria tarefa prática validando competências e gera registros PENDING em task_submissions."""
    return task_service.create_practical_task(payload, current_user=current_user)


@router.get(
    "/modules/{module_id}/practical-tasks",
    response_model=PracticalTaskPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar atividades práticas e rubricas vinculadas a um módulo prático",
)
async def list_module_practical_tasks(
    module_id: UUIDPathParam,
    params: PracticalTaskListParamsDep,
    task_service: PracticalTaskServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> PracticalTaskPaginatedResponseSchema:
    """Lista atividades práticas do módulo ordenadas por prazo de entrega com progresso da turma."""
    return task_service.list_module_practical_tasks(
        module_id,
        params,
        current_user=current_user,
    )


@router.post(
    "/tasks/{task_id}/evaluations",
    response_model=TaskEvaluationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Registrar conclusão e avaliação por rubricas de atividade prática pelo docente",
)
@router.post(
    "/practical-tasks/{task_id}/evaluations",
    response_model=TaskEvaluationResponseSchema,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def evaluate_practical_task(
    task_id: UUIDPathParam,
    payload: TaskEvaluationRequestSchema,
    task_service: PracticalTaskServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> TaskEvaluationResponseSchema:
    """Calcula a nota ponderada a partir das rubricas, atualiza task_submissions e grava skill_evidences."""
    return task_service.evaluate_practical_task(
        task_id,
        payload,
        current_user=current_user,
    )


@router.get(
    "/students/{student_id}/pending-tasks",
    response_model=StudentPendingTasksResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar tarefas práticas pendentes, em atraso e concluídas de um estudante",
)
async def list_student_pending_tasks(
    student_id: UUIDPathParam,
    params: StudentPendingTasksQueryParamsDep,
    task_service: PracticalTaskServiceDep,
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
) -> StudentPendingTasksResponseSchema:
    """Consulta submissões práticas do aluno marcando dinamicamente LATE quando due_date expirou."""
    return task_service.list_student_pending_tasks(
        student_id,
        params,
        current_user=current_user,
    )


__all__ = ["router"]
