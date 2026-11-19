"""Schemas Pydantic v2 para validação e serialização de Cursos Técnicos SENAI (BE-011)."""

import re
from typing import Annotated, Any, Self
from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.validators import sanitize_optional_text, sanitize_text

_COURSE_CODE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._-]+$")

_NON_NULLABLE_UPDATE_FIELD_MESSAGES: dict[str, str] = {
    "code": "O código do curso não pode ser nulo.",
    "name": "O nome do curso não pode ser nulo.",
    "total_hours": "A carga horária total não pode ser nula.",
    "is_active": "O status de ativação do curso não pode ser nulo.",
}


def validate_course_code_pt(value: Any) -> str:
    """Normaliza (UPPER + TRIM) e valida o código identificador do curso técnico SENAI."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "course_code_too_short",
            "O código do curso deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 30:
        raise PydanticCustomError(
            "course_code_too_long",
            "O código do curso deve ter no máximo 30 caracteres.",
        )
    if not _COURSE_CODE_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "course_code_invalid_format",
            "O código do curso deve conter apenas letras, números, pontos, underscores ou hífens.",
        )
    return cleaned


def validate_course_name_pt(value: Any) -> str:
    """Sanitiza espaços e valida o nome do curso técnico SENAI."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "course_name_too_short",
            "O nome do curso deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "course_name_too_long",
            "O nome do curso deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_course_hours_pt(value: Any) -> int:
    """Garante que a carga horária total seja um inteiro estritamente maior que zero."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "course_hours_invalid",
            "A carga horária total deve ser um número inteiro maior que zero.",
        )

    if isinstance(value, int):
        if value <= 0:
            raise PydanticCustomError(
                "course_hours_invalid",
                "A carga horária total deve ser um número inteiro maior que zero.",
            )
        return value

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lstrip("+-").isdigit():
            parsed = int(cleaned)
            if parsed > 0:
                return parsed

    raise PydanticCustomError(
        "course_hours_invalid",
        "A carga horária total deve ser um número inteiro maior que zero.",
    )


type CourseCodeStr = Annotated[
    str,
    BeforeValidator(validate_course_code_pt),
    Field(
        description="Código único SENAI do curso (3 a 30 caracteres, normalizado em maiúsculas)",
        examples=["TEC-MEC-01"],
    ),
]

type CourseNameStr = Annotated[
    str,
    BeforeValidator(validate_course_name_pt),
    Field(
        description="Nome oficial do curso técnico (3 a 150 caracteres)",
        examples=["Técnico em Mecânica"],
    ),
]

type PositiveHoursInt = Annotated[
    int,
    BeforeValidator(validate_course_hours_pt),
    Field(
        description="Carga horária total do curso em horas (inteiro maior que zero)",
        examples=[1200],
    ),
]


class CourseCreateSchema(StrictRequestSchema):
    """Schema de entrada para cadastro administrativo de curso técnico (POST /api/v1/courses)."""

    code: CourseCodeStr
    name: CourseNameStr
    description: str | None = Field(
        default=None,
        description="Descrição pedagógica opcional do curso técnico",
        examples=["Formação técnica em processos de usinagem, metrologia e manutenção mecânica."],
    )
    total_hours: PositiveHoursInt
    is_active: bool = Field(
        default=True,
        description="Indica se o curso está ativo na oferta formativa",
        examples=[True],
    )

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)


class CourseUpdateSchema(StrictRequestSchema):
    """Schema de entrada para atualização de curso técnico (PUT /api/v1/courses/{id})."""

    code: str | None = Field(
        default=None,
        description="Novo código único SENAI do curso (3 a 30 caracteres)",
        examples=["TEC-MEC-02"],
    )
    name: str | None = Field(
        default=None,
        description="Novo nome oficial do curso técnico (3 a 150 caracteres)",
        examples=["Técnico em Mecânica Industrial"],
    )
    description: str | None = Field(
        default=None,
        description="Descrição pedagógica atualizada (envie null para limpar)",
    )
    total_hours: int | None = Field(
        default=None,
        description="Nova carga horária total em horas (inteiro maior que zero)",
        examples=[1400],
    )
    is_active: bool | None = Field(
        default=None,
        description="Novo status de ativação do curso na oferta formativa",
    )

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_course_code_pt(value)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_course_name_pt(value)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)

    @field_validator("total_hours", mode="before")
    @classmethod
    def validate_total_hours(cls, value: Any) -> int | None:
        if value is None:
            return None
        return validate_course_hours_pt(value)

    @model_validator(mode="after")
    def validate_update_payload(self) -> Self:
        """Exige ao menos um campo informado e impede valores nulos em campos obrigatórios."""
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização do curso.")

        for field_name, error_message in _NON_NULLABLE_UPDATE_FIELD_MESSAGES.items():
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(error_message)

        return self


class CourseResponseSchema(EntityResponseSchema):
    """Schema de saída para serialização de Course do SQLAlchemy."""

    code: str = Field(
        description="Código único SENAI do curso técnico",
        examples=["TEC-MEC-01"],
    )
    name: str = Field(
        description="Nome oficial do curso técnico",
        examples=["Técnico em Mecânica"],
    )
    description: str | None = Field(
        default=None,
        description="Descrição pedagógica do curso",
    )
    total_hours: int = Field(
        description="Carga horária total do curso em horas",
        examples=[1200],
    )
    is_active: bool = Field(
        description="Indica se o curso está ativo na oferta formativa",
        examples=[True],
    )


class CourseListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada e busca para listagem de cursos (GET /api/v1/courses)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
        examples=[1],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de cursos por página (1 a 100)",
        examples=[20],
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual por código, nome ou descrição",
        examples=["Mecânica"],
    )
    is_active: bool | None = Field(
        default=None,
        description="Filtro opcional de status ativo/inativo",
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
        return (self.page - 1) * self.limit


class CoursePaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de cursos técnicos."""

    data: list[CourseResponseSchema] = Field(
        default_factory=list,
        description="Lista de cursos da página atual",
    )
    total: int = Field(
        ge=0,
        description="Total geral de cursos encontrados",
        examples=[12],
    )
    page: int = Field(
        ge=1,
        description="Página atual",
        examples=[1],
    )
    limit: int = Field(
        ge=1,
        le=100,
        description="Quantidade máxima de registros por página",
        examples=[20],
    )


type CourseListParamsDep = Annotated[CourseListQueryParams, Query()]

__all__ = [
    "CourseCodeStr",
    "CourseCreateSchema",
    "CourseListParamsDep",
    "CourseListQueryParams",
    "CourseNameStr",
    "CoursePaginatedResponseSchema",
    "CourseResponseSchema",
    "CourseUpdateSchema",
    "PositiveHoursInt",
    "validate_course_code_pt",
    "validate_course_hours_pt",
    "validate_course_name_pt",
]
