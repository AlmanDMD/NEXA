"""Router para Diário de Classe e Registro de Aulas Ministradas (EPIC-03 / BE-021)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.models.user import User
from app.schemas.base import UUIDPathParam
from app.schemas.class_lesson import (
    BatchAttendanceRequestSchema,
    BatchAttendanceResponseSchema,
    ClassLessonCreateSchema,
    ClassLessonListParamsDep,
    ClassLessonPaginatedResponseSchema,
    ClassLessonResponseSchema,
    StudentAttendanceQueryParamsDep,
    StudentConsolidatedAttendanceResponseSchema,
)
from app.schemas.enums import UserRole
from app.services.class_lesson_service import ClassLessonServiceDep

router = APIRouter(
    prefix="/api/v1",
    tags=["Lessons"],
)


@router.post(
    "/lessons",
    response_model=ClassLessonResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar aula ministrada no diário de classe e pré-inicializar chamada",
)
async def create_lesson(
    payload: ClassLessonCreateSchema,
    lesson_service: ClassLessonServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassLessonResponseSchema:
    """Registra conteúdo e oficina da aula ministrada e inicializa lista de chamada dos ativos."""
    return lesson_service.create_lesson(payload, current_user=current_user)


@router.get(
    "/classes/{class_id}/lessons",
    response_model=ClassLessonPaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar diário de bordo de aulas ministradas de uma turma",
)
async def list_class_lessons(
    class_id: UUIDPathParam,
    params: ClassLessonListParamsDep,
    lesson_service: ClassLessonServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> ClassLessonPaginatedResponseSchema:
    """Lista aulas ministradas da turma ordenadas cronologicamente com filtros por disciplina/módulo/período."""
    return lesson_service.list_class_lessons(
        class_id,
        params,
        current_user=current_user,
    )


@router.post(
    "/lessons/{lesson_id}/attendance",
    response_model=BatchAttendanceResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Registrar chamada rápida em lote e recalcular frequência na matrícula",
)
async def record_batch_attendance(
    lesson_id: UUIDPathParam,
    payload: BatchAttendanceRequestSchema,
    lesson_service: ClassLessonServiceDep,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR, UserRole.TEACHER)),
    ],
) -> BatchAttendanceResponseSchema:
    """Executa upsert transacional da chamada da aula e recalcula attendance_rate no servidor."""
    return lesson_service.record_batch_attendance(
        lesson_id,
        payload,
        current_user=current_user,
    )


@router.get(
    "/students/{student_id}/attendance",
    response_model=StudentConsolidatedAttendanceResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar extrato consolidado de frequência do estudante por disciplina e módulo prático",
)
async def get_student_consolidated_attendance(
    student_id: UUIDPathParam,
    params: StudentAttendanceQueryParamsDep,
    lesson_service: ClassLessonServiceDep,
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
) -> StudentConsolidatedAttendanceResponseSchema:
    """Retorna presenças, faltas, margem até o limite de 75% e alerta (<78%) via vw_module_attendance_risk."""
    return lesson_service.get_student_consolidated_attendance(
        student_id,
        params,
        current_user=current_user,
    )


__all__ = ["router"]
