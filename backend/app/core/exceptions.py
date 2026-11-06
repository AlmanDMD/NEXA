"""Hierarquia de exceções customizadas de domínio e aplicação da API NEXA."""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Classe base para todas as exceções tratadas de domínio e aplicação."""

    def __init__(
        self,
        message: str = "Erro ao processar a requisição.",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error: str = "APP_ERROR",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error
        self.details = details
        self.headers = headers


class BadRequestException(AppException):
    """Exceção para requisições malformadas ou inválidas (HTTP 400)."""

    def __init__(
        self,
        message: str = "Requisição inválida.",
        error: str = "BAD_REQUEST",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error=error,
            details=details,
            headers=headers,
        )


class UnauthorizedException(AppException):
    """Exceção para falha de autenticação ou credenciais ausentes/inválidas (HTTP 401)."""

    def __init__(
        self,
        message: str = "Não autenticado ou credenciais inválidas.",
        error: str = "UNAUTHORIZED",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error=error,
            details=details,
            headers=headers,
        )


class ForbiddenException(AppException):
    """Exceção para falta de permissão de acesso ao recurso (HTTP 403)."""

    def __init__(
        self,
        message: str = "Acesso não autorizado para seu perfil.",
        error: str = "FORBIDDEN",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error=error,
            details=details,
            headers=headers,
        )


class NotFoundException(AppException):
    """Exceção para recurso não encontrado (HTTP 404)."""

    def __init__(
        self,
        message: str = "Recurso não encontrado.",
        error: str = "NOT_FOUND",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error=error,
            details=details,
            headers=headers,
        )


class ConflictException(AppException):
    """Exceção para conflitos de estado ou duplicidade de registro (HTTP 409)."""

    def __init__(
        self,
        message: str = "Conflito com o estado atual do recurso.",
        error: str = "CONFLICT",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error=error,
            details=details,
            headers=headers,
        )


class UnprocessableEntityException(AppException):
    """Exceção para violação de regra de negócio semântica (HTTP 422)."""

    def __init__(
        self,
        message: str = "Não foi possível processar as instruções da requisição.",
        error: str = "UNPROCESSABLE_ENTITY",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error=error,
            details=details,
            headers=headers,
        )


class InternalServerException(AppException):
    """Exceção para falhas internas controladas do servidor (HTTP 500)."""

    def __init__(
        self,
        message: str = "Erro interno inesperado no servidor. Tente novamente mais tarde.",
        error: str = "INTERNAL_SERVER_ERROR",
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=error,
            details=details,
            headers=headers,
        )


__all__ = [
    "AppException",
    "BadRequestException",
    "ConflictException",
    "ForbiddenException",
    "InternalServerException",
    "NotFoundException",
    "UnauthorizedException",
    "UnprocessableEntityException",
]

