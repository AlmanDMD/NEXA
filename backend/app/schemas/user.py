"""Schemas Pydantic v2 para validação e serialização de Usuários e Perfis (EPIC-01)."""

from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from pydantic import EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import EntityResponseSchema, StrictRequestSchema
from app.schemas.enums import UserRole
from app.schemas.validators import (
    sanitize_optional_text,
    validate_email_pt,
    validate_full_name_pt,
    validate_phone_pt,
    validate_registration_number_pt,
    validate_strong_password_pt,
)


def _validate_avatar_url(value: Any) -> str | None:
    """Sanitiza e valida URL opcional de avatar exigindo esquema http ou https."""
    cleaned = sanitize_optional_text(value, collapse_spaces=False)
    if cleaned is None:
        return None

    if len(cleaned) > 500:
        raise PydanticCustomError(
            "avatar_url_too_long",
            "A URL do avatar deve ter no máximo 500 caracteres.",
        )

    parsed = urlparse(cleaned)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise PydanticCustomError(
            "avatar_url_invalid",
            "A URL do avatar deve ser um endereço válido iniciando com http:// ou https://.",
        )
    return cleaned


def _validate_bio(value: Any) -> str | None:
    """Sanitiza e valida biografia opcional do perfil de usuário."""
    cleaned = sanitize_optional_text(value, collapse_spaces=True)
    if cleaned is None:
        return None

    if len(cleaned) > 1000:
        raise PydanticCustomError(
            "bio_too_long",
            "A biografia deve ter no máximo 1000 caracteres.",
        )
    return cleaned


class UserProfileCreateSchema(StrictRequestSchema):
    """Schema de entrada para criação de perfil de usuário (user_profiles)."""

    full_name: str = Field(
        description="Nome completo do usuário (mínimo de 2 e máximo de 150 caracteres)",
        examples=["Maria Fernanda Oliveira"],
    )
    registration_number: str = Field(
        description="Matrícula acadêmica ou registro funcional SENAI (normalizado em maiúsculas)",
        examples=["SENAI-2026-0001"],
    )
    phone: str | None = Field(
        default=None,
        description="Telefone de contato opcional",
        examples=["(11) 98765-4321"],
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL pública opcional da foto de perfil",
        examples=["https://cdn.senai.br/avatars/maria.png"],
    )
    bio: str | None = Field(
        default=None,
        description="Resumo biográfico ou observação institucional opcional",
        examples=["Estudante do Curso Técnico em Mecânica de Precisão."],
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, value: Any) -> str:
        return validate_full_name_pt(value)

    @field_validator("registration_number", mode="before")
    @classmethod
    def validate_registration_number(cls, value: Any) -> str:
        return validate_registration_number_pt(value)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> str | None:
        return validate_phone_pt(value)

    @field_validator("avatar_url", mode="before")
    @classmethod
    def validate_avatar_url(cls, value: Any) -> str | None:
        return _validate_avatar_url(value)

    @field_validator("bio", mode="before")
    @classmethod
    def validate_bio(cls, value: Any) -> str | None:
        return _validate_bio(value)


class UserProfileUpdateSchema(StrictRequestSchema):
    """Schema de entrada para atualização parcial de perfil de usuário."""

    full_name: str | None = Field(
        default=None,
        description="Nome completo atualizado do usuário",
        examples=["Maria Fernanda Oliveira Santos"],
    )
    registration_number: str | None = Field(
        default=None,
        description="Matrícula acadêmica ou registro funcional atualizado",
        examples=["SENAI-2026-0001"],
    )
    phone: str | None = Field(
        default=None,
        description="Telefone de contato atualizado",
        examples=["(11) 98765-4321"],
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL pública da foto de perfil",
        examples=["https://cdn.senai.br/avatars/maria.png"],
    )
    bio: str | None = Field(
        default=None,
        description="Resumo biográfico atualizado",
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_full_name_pt(value)

    @field_validator("registration_number", mode="before")
    @classmethod
    def validate_registration_number(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_registration_number_pt(value)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> str | None:
        return validate_phone_pt(value)

    @field_validator("avatar_url", mode="before")
    @classmethod
    def validate_avatar_url(cls, value: Any) -> str | None:
        return _validate_avatar_url(value)

    @field_validator("bio", mode="before")
    @classmethod
    def validate_bio(cls, value: Any) -> str | None:
        return _validate_bio(value)


class UserProfileResponseSchema(EntityResponseSchema):
    """Schema de saída para serialização de UserProfile a partir do SQLAlchemy (from_attributes=True)."""

    user_id: UUID = Field(
        description="Identificador UUID do usuário proprietário do perfil",
    )
    full_name: str = Field(
        description="Nome completo do usuário",
        examples=["Maria Fernanda Oliveira"],
    )
    registration_number: str = Field(
        description="Matrícula acadêmica ou registro funcional SENAI",
        examples=["SENAI-2026-0001"],
    )
    phone: str | None = Field(
        default=None,
        description="Telefone de contato",
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL da foto de perfil",
    )
    bio: str | None = Field(
        default=None,
        description="Biografia ou descrição institucional",
    )


class UserCreateSchema(StrictRequestSchema):
    """Schema de entrada para criação de usuário com validação estrita e sanitização."""

    email: EmailStr = Field(
        description="Endereço de e-mail institucional do usuário (normalizado em minúsculas)",
        examples=["maria.oliveira@senai.br"],
    )
    password: str = Field(
        description="Senha de acesso atendendo aos critérios de complexidade",
        examples=["Senai@2026"],
    )
    role: UserRole = Field(
        default=UserRole.STUDENT,
        description="Papel institucional RBAC do usuário",
        examples=[UserRole.STUDENT],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se a conta do usuário está ativa",
        examples=[True],
    )
    profile: UserProfileCreateSchema | None = Field(
        default=None,
        description="Dados cadastrais opcionais do perfil 1:1 do usuário",
    )

    @field_validator("email", mode="before")
    @classmethod
    def validate_and_normalize_email(cls, value: Any) -> str:
        return validate_email_pt(value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: Any) -> str:
        return validate_strong_password_pt(value)


class UserUpdateSchema(StrictRequestSchema):
    """Schema de entrada para atualização parcial de usuário."""

    email: EmailStr | None = Field(
        default=None,
        description="Novo endereço de e-mail institucional",
        examples=["maria.oliveira@senai.br"],
    )
    password: str | None = Field(
        default=None,
        description="Nova senha de acesso atendendo aos critérios de complexidade",
    )
    role: UserRole | None = Field(
        default=None,
        description="Novo papel institucional RBAC",
    )
    is_active: bool | None = Field(
        default=None,
        description="Status de ativação da conta",
    )
    profile: UserProfileUpdateSchema | None = Field(
        default=None,
        description="Dados de atualização do perfil do usuário",
    )

    @field_validator("email", mode="before")
    @classmethod
    def validate_and_normalize_email(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_email_pt(value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_strong_password_pt(value)


class UserResponseSchema(EntityResponseSchema):
    """Schema de saída para serialização segura de User do SQLAlchemy (nunca expõe password_hash)."""

    email: EmailStr = Field(
        description="Endereço de e-mail institucional do usuário",
        examples=["maria.oliveira@senai.br"],
    )
    role: UserRole = Field(
        description="Papel institucional RBAC do usuário",
        examples=[UserRole.STUDENT],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se o usuário está ativo no sistema",
        examples=[True],
    )
    profile: UserProfileResponseSchema | None = Field(
        default=None,
        description="Perfil cadastral 1:1 vinculado ao usuário",
    )


__all__ = [
    "UserCreateSchema",
    "UserProfileCreateSchema",
    "UserProfileResponseSchema",
    "UserProfileUpdateSchema",
    "UserResponseSchema",
    "UserUpdateSchema",
]
