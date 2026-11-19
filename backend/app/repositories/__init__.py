"""Camada de repositories (acesso e persistência de dados)."""

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
    "AuthRepository",
    "AuthRepositoryDep",
    "CourseRepository",
    "CourseRepositoryDep",
    "get_auth_repository",
    "get_course_repository",
]
