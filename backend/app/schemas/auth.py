"""Schemas Pydantic v2 para fluxos de Autenticação e Sessão (EPIC-01)."""

from typing import Any, Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.user import UserResponseSchema
from app.schemas.validators import validate_email_pt, validate_login_password_pt


class LoginRequestSchema(StrictRequestSchema):
    """Schema de entrada para credenciais de autenticação (POST /api/v1/auth/login)."""

    email: EmailStr = Field(
        description="Endereço de e-mail institucional do usuário",
        examples=["maria.oliveira@senai.br"],
    )
    password: str = Field(
        description="Senha de acesso (mínimo de 8 caracteres)",
        examples=["Senai@2026"],
    )

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any) -> str:
        return validate_email_pt(value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: Any) -> str:
        return validate_login_password_pt(value)


class TokenResponseSchema(BaseResponseSchema):
    """Schema de resposta de autenticação bem-sucedida com token JWT e dados do usuário."""

    user: UserResponseSchema = Field(
        description="Dados públicos do usuário autenticado e seu perfil",
    )
    access_token: str = Field(
        min_length=1,
        description="Token JWT de acesso de curta duração",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="Tipo do token de autenticação OAuth2",
        examples=["bearer"],
    )


class RefreshTokenResponseSchema(BaseResponseSchema):
    """Schema de resposta para renovação de Access Token via Refresh Token."""

    access_token: str = Field(
        min_length=1,
        description="Novo token JWT de acesso emitido",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="Tipo do token de autenticação OAuth2",
        examples=["bearer"],
    )


class LogoutResponseSchema(BaseResponseSchema):
    """Schema de resposta para encerramento de sessão."""

    message: str = Field(
        default="Sessão encerrada com sucesso",
        description="Mensagem de confirmação do encerramento da sessão",
        examples=["Sessão encerrada com sucesso"],
    )


class UserMeResponse(UserResponseSchema):
    """Schema de resposta para consulta do usuário autenticado atual (GET /api/v1/auth/me)."""


__all__ = [
    "LoginRequestSchema",
    "LogoutResponseSchema",
    "RefreshTokenResponseSchema",
    "TokenResponseSchema",
    "UserMeResponse",
]
