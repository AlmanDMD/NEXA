"""Camada de repositories (acesso e persistência de dados)."""

from app.repositories.academic_class_repository import (
    AcademicClassRepository,
    AcademicClassRepositoryDep,
    get_academic_class_repository,
)
from app.repositories.auth_repository import (
    AuthRepository,
    AuthRepositoryDep,
    get_auth_repository,
)
from app.repositories.course_repository import (
    CourseRepository,
    CourseRepositoryDep,
    get_course_repository,
)

__all__ = [
    "AcademicClassRepository",
    "AcademicClassRepositoryDep",
    "AuthRepository",
    "AuthRepositoryDep",
    "CourseRepository",
    "CourseRepositoryDep",
    "get_academic_class_repository",
    "get_auth_repository",
    "get_course_repository",
]
