"""Camada de repositories (acesso e persistência de dados)."""

from app.repositories.auth_repository import (
    AuthRepository,
    AuthRepositoryDep,
    get_auth_repository,
)

__all__ = [
    "AuthRepository",
    "AuthRepositoryDep",
    "get_auth_repository",
]
