"""Schemas base Pydantic v2 e utilitários de paginação e injeção de parâmetros para FastAPI."""

from collections.abc import Sequence
from datetime import datetime
import math
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from fastapi import Path, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.validators import sanitize_optional_text


class BaseSchema(BaseModel):
    """Schema base central do projeto NEXA configurado para Pydantic v2 e SQLAlchemy 2.0."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
        ser_json_timedelta="iso8601",
    )


class StrictRequestSchema(BaseSchema):
    """Schema base para payloads de entrada (Body e Query), proibindo campos extras ('extra=forbid')."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


BaseRequestSchema = StrictRequestSchema


class BaseResponseSchema(BaseSchema):
    """Schema base para respostas da API e serialização segura de entidades SQLAlchemy 2.0."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class UUIDResponseMixin(BaseModel):
    """Mixin com identificador universal UUID v4."""

    id: UUID = Field(
        description="Identificador único universal (UUID v4) do registro",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class TimestampResponseMixin(BaseModel):
    """Mixin com carimbos de tempo de criação e última atualização em UTC."""

    created_at: datetime = Field(
        description="Data e hora de criação do registro (UTC ISO 8601)",
    )
    updated_at: datetime = Field(
        description="Data e hora da última atualização do registro (UTC ISO 8601)",
    )


class EntityResponseSchema(BaseResponseSchema, UUIDResponseMixin, TimestampResponseMixin):
    """Schema base de saída para entidades persistidas com id, created_at e updated_at."""


class PaginationQueryParams(StrictRequestSchema):
    """Schema de validação estrita para parâmetros de consulta (Query Params) de listagens paginadas."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
        examples=[1],
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de registros por página (1 a 100)",
        examples=[20],
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual opcional (sanitizado)",
        examples=["Tornearia"],
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="asc",
        description="Direção da ordenação ('asc' ou 'desc')",
        examples=["asc"],
    )

    @field_validator("search", mode="before")
    @classmethod
    def sanitize_search_term(cls, value: Any) -> str | None:
        cleaned = sanitize_optional_text(value, collapse_spaces=True)
        if cleaned is not None and len(cleaned) > 100:
            raise PydanticCustomError(
                "search_too_long",
                "O termo de busca deve ter no máximo 100 caracteres.",
            )
        return cleaned

    @property
    def offset(self) -> int:
        """Retorna o deslocamento (OFFSET) calculado para consultas SQLAlchemy."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Retorna o limite (LIMIT) para consultas SQLAlchemy."""
        return self.page_size


class PaginatedResponse[T](BaseResponseSchema):
    """Envelope genérico padronizado para respostas paginadas da API."""

    items: list[T] = Field(
        default_factory=list,
        description="Lista de registros da página atual",
    )
    total: int = Field(
        ge=0,
        description="Total geral de registros encontrados",
        examples=[42],
    )
    page: int = Field(
        ge=1,
        description="Página atual",
        examples=[1],
    )
    page_size: int = Field(
        ge=1,
        le=100,
        description="Quantidade de itens por página",
        examples=[20],
    )
    total_pages: int = Field(
        ge=0,
        description="Quantidade total de páginas disponíveis",
        examples=[3],
    )

    @classmethod
    def create(
        cls,
        *,
        items: Sequence[T],
        total: int,
        params: PaginationQueryParams | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Self:
        """Constrói uma resposta paginada calculando automaticamente total_pages."""
        resolved_page = params.page if params is not None else page
        resolved_page_size = params.page_size if params is not None else page_size
        total_pages = math.ceil(total / resolved_page_size) if total > 0 else 0
        return cls(
            items=list(items),
            total=total,
            page=resolved_page,
            page_size=resolved_page_size,
            total_pages=total_pages,
        )


class MessageResponseSchema(BaseResponseSchema):
    """Schema padrão para respostas simples de confirmação de operação."""

    success: bool = Field(default=True, description="Indica sucesso na operação", examples=[True])
    message: str = Field(
        description="Mensagem informativa em português sobre a operação realizada",
        examples=["Operação realizada com sucesso."],
    )


type PaginationParamsDep = Annotated[PaginationQueryParams, Query()]

type UUIDPathParam = Annotated[
    UUID,
    Path(
        description="Identificador único universal (UUID v4) do recurso na rota",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
]

type PositiveIntPathParam = Annotated[
    int,
    Path(
        ge=1,
        description="Identificador numérico inteiro positivo do recurso na rota",
        examples=[1],
    ),
]

__all__ = [
    "BaseRequestSchema",
    "BaseResponseSchema",
    "BaseSchema",
    "EntityResponseSchema",
    "MessageResponseSchema",
    "PaginatedResponse",
    "PaginationParamsDep",
    "PaginationQueryParams",
    "PositiveIntPathParam",
    "StrictRequestSchema",
    "TimestampResponseMixin",
    "UUIDPathParam",
    "UUIDResponseMixin",
]
