"""Router administrativo para CRUD de Cursos Técnicos SENAI (EPIC-02 / BE-011)."""

from fastapi import APIRouter, Depends, status

from app.core.security import require_role
from app.schemas.base import UUIDPathParam
from app.schemas.course import (
    CourseCreateSchema,
    CourseListParamsDep,
    CoursePaginatedResponseSchema,
    CourseResponseSchema,
    CourseUpdateSchema,
)
from app.schemas.enums import UserRole
from app.services.course_service import CourseServiceDep

router = APIRouter(
    prefix="/api/v1/courses",
    tags=["Courses"],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.COORDINATOR))],
)


@router.get(
    "",
    response_model=CoursePaginatedResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar cursos técnicos com paginação e busca",
)
async def list_courses(
    params: CourseListParamsDep,
    course_service: CourseServiceDep,
) -> CoursePaginatedResponseSchema:
    """Retorna lista paginada { data, total, page, limit } de cursos técnicos."""
    return course_service.list_courses(params)


@router.post(
    "",
    response_model=CourseResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo curso técnico SENAI",
)
async def create_course(
    payload: CourseCreateSchema,
    course_service: CourseServiceDep,
) -> CourseResponseSchema:
    """Cadastra um novo curso técnico validando código único e carga horária positiva."""
    return course_service.create_course(payload)


@router.get(
    "/{course_id}",
    response_model=CourseResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalhes de curso técnico por ID",
)
async def get_course(
    course_id: UUIDPathParam,
    course_service: CourseServiceDep,
) -> CourseResponseSchema:
    """Retorna os dados detalhados de um curso técnico pelo UUID."""
    return course_service.get_course(course_id)


@router.put(
    "/{course_id}",
    response_model=CourseResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados de curso técnico",
)
async def update_course(
    course_id: UUIDPathParam,
    payload: CourseUpdateSchema,
    course_service: CourseServiceDep,
) -> CourseResponseSchema:
    """Atualiza informações do curso técnico e impede desativação caso haja turmas ativas."""
    return course_service.update_course(course_id, payload)


@router.delete(
    "/{course_id}",
    response_model=CourseResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desativar logicamente curso técnico (soft delete)",
)
async def deactivate_course(
    course_id: UUIDPathParam,
    course_service: CourseServiceDep,
) -> CourseResponseSchema:
    """Desativa o curso logicamente (is_active=False) caso não existam turmas ativas vinculadas."""
    return course_service.deactivate_course(course_id)


__all__ = ["router"]
