"""Schemas Pydantic v2 para validação e serialização de Disciplinas do Currículo Técnico (BE-013)."""

import re
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.academic_class import CourseSummarySchema
from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.validators import sanitize_optional_text, sanitize_text

_SUBJECT_CODE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._-]+$")
_INT_PATTERN: re.Pattern[str] = re.compile(r"^[+-]?\d+$")

_NON_NULLABLE_UPDATE_FIELD_MESSAGES: dict[str, str] = {
    "course_id": "O curso técnico vinculado não pode ser nulo.",
    "code": "O código da disciplina não pode ser nulo.",
    "name": "O nome da disciplina não pode ser nulo.",
    "workload_hours": "A carga horária da disciplina não pode ser nula.",
    "is_active": "O status de ativação da disciplina não pode ser nulo.",
}


def validate_subject_code_pt(value: Any) -> str:
    """Normaliza (UPPER + TRIM) e valida o código identificador da disciplina técnica."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 2:
        raise PydanticCustomError(
            "subject_code_too_short",
            "O código da disciplina deve ter pelo menos 2 caracteres.",
        )
    if len(cleaned) > 50:
        raise PydanticCustomError(
            "subject_code_too_long",
            "O código da disciplina deve ter no máximo 50 caracteres.",
        )
    if not _SUBJECT_CODE_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "subject_code_invalid_format",
            "O código da disciplina deve conter apenas letras, números, pontos, underscores ou hífens.",
        )
    return cleaned


def validate_subject_name_pt(value: Any) -> str:
    """Sanitiza espaços e valida o nome da disciplina do currículo técnico."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "subject_name_too_short",
            "O nome da disciplina deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "subject_name_too_long",
            "O nome da disciplina deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_subject_workload_hours_pt(value: Any) -> int:
    """Garante que a carga horária da disciplina seja um inteiro estritamente maior que zero."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "subject_workload_hours_invalid",
            "A carga horária da disciplina deve ser um número inteiro maior que zero.",
        )

    if isinstance(value, int):
        if value <= 0:
            raise PydanticCustomError(
                "subject_workload_hours_invalid",
                "A carga horária da disciplina deve ser um número inteiro maior que zero.",
            )
        return value

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if parsed > 0:
                return parsed

    raise PydanticCustomError(
        "subject_workload_hours_invalid",
        "A carga horária da disciplina deve ser um número inteiro maior que zero.",
    )


type SubjectCodeStr = Annotated[
    str,
    BeforeValidator(validate_subject_code_pt),
    Field(
        description="Código único da disciplina no curso (2 a 50 caracteres, normalizado em maiúsculas)",
        examples=["MET-DIM-01"],
    ),
]

type SubjectNameStr = Annotated[
    str,
    BeforeValidator(validate_subject_name_pt),
    Field(
        description="Nome oficial da disciplina técnica (3 a 150 caracteres)",
        examples=["Metrologia Dimensional"],
    ),
]

type PositiveWorkloadHoursInt = Annotated[
    int,
    BeforeValidator(validate_subject_workload_hours_pt),
    Field(
        description="Carga horária da disciplina em horas (inteiro maior que zero)",
        examples=[80],
    ),
]


class SubjectCreateSchema(StrictRequestSchema):
    """Schema de entrada para cadastro de disciplina técnica (POST /api/v1/subjects)."""

    course_id: UUID = Field(
        description="Identificador UUID do curso técnico ao qual a disciplina pertence",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    code: SubjectCodeStr
    name: SubjectNameStr
    workload_hours: PositiveWorkloadHoursInt
    syllabus: str | None = Field(
        default=None,
        description="Ementa técnica opcional da unidade curricular",
        examples=["Leitura e interpretação com paquímetro, micrômetro e tolerâncias dimensionais."],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se a disciplina está ativa na matriz curricular",
        examples=[True],
    )

    @field_validator("syllabus", mode="before")
    @classmethod
    def sanitize_syllabus(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)


class SubjectUpdateSchema(StrictRequestSchema):
    """Schema de entrada para atualização de disciplina técnica (PUT /api/v1/subjects/{id})."""

    course_id: UUID | None = Field(
        default=None,
        description="Novo identificador UUID do curso técnico vinculado à disciplina",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    code: str | None = Field(
        default=None,
        description="Novo código identificador da disciplina no curso (2 a 50 caracteres)",
        examples=["MET-DIM-02"],
    )
    name: str | None = Field(
        default=None,
        description="Novo nome oficial da disciplina técnica (3 a 150 caracteres)",
        examples=["Metrologia Dimensional Aplicada"],
    )
    workload_hours: int | None = Field(
        default=None,
        description="Nova carga horária da disciplina em horas (inteiro maior que zero)",
        examples=[100],
    )
    syllabus: str | None = Field(
        default=None,
        description="Ementa técnica atualizada da disciplina (envie null para limpar)",
    )
    is_active: bool | None = Field(
        default=None,
        description="Novo status de ativação da disciplina na matriz curricular",
    )

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_subject_code_pt(value)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        return validate_subject_name_pt(value)

    @field_validator("syllabus", mode="before")
    @classmethod
    def sanitize_syllabus(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)

    @field_validator("workload_hours", mode="before")
    @classmethod
    def validate_workload_hours(cls, value: Any) -> int | None:
        if value is None:
            return None
        return validate_subject_workload_hours_pt(value)

    @model_validator(mode="after")
    def validate_update_payload(self) -> Self:
        """Exige ao menos um campo informado e impede valores nulos em campos obrigatórios."""
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização da disciplina.")

        for field_name, error_message in _NON_NULLABLE_UPDATE_FIELD_MESSAGES.items():
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(error_message)

        return self


class SubjectResponseSchema(EntityResponseSchema):
    """Schema de saída para serialização de Subject do SQLAlchemy."""

    course_id: UUID = Field(
        description="Identificador UUID do curso técnico vinculado",
    )
    code: str = Field(
        description="Código identificador da disciplina técnica no curso",
        examples=["MET-DIM-01"],
    )
    name: str = Field(
        description="Nome oficial da disciplina técnica",
        examples=["Metrologia Dimensional"],
    )
    workload_hours: int = Field(
        ge=1,
        description="Carga horária total da disciplina em horas",
        examples=[80],
    )
    syllabus: str | None = Field(
        default=None,
        description="Ementa técnica da unidade curricular",
    )
    is_active: bool = Field(
        description="Indica se a disciplina está ativa na matriz curricular",
        examples=[True],
    )
    course: CourseSummarySchema = Field(
        description="Resumo do curso técnico ao qual a disciplina está vinculada",
    )


class SubjectListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada e filtros para listagem de disciplinas (GET /api/v1/subjects)."""

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
        description="Quantidade máxima de disciplinas por página (1 a 100)",
        examples=[20],
    )
    course_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do curso técnico",
    )
    is_active: bool | None = Field(
        default=None,
        description="Filtro opcional por status ativo/inativo (use true para apenas disciplinas ativas)",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual por código, nome ou ementa técnica",
        examples=["Metrologia"],
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


class SubjectPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de disciplinas."""

    data: list[SubjectResponseSchema] = Field(
        default_factory=list,
        description="Lista de disciplinas da página atual",
    )
    total: int = Field(
        ge=0,
        description="Total geral de disciplinas encontradas",
        examples=[8],
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


type SubjectListParamsDep = Annotated[SubjectListQueryParams, Query()]

__all__ = [
    "PositiveWorkloadHoursInt",
    "SubjectCodeStr",
    "SubjectCreateSchema",
    "SubjectListParamsDep",
    "SubjectListQueryParams",
    "SubjectNameStr",
    "SubjectPaginatedResponseSchema",
    "SubjectResponseSchema",
    "SubjectUpdateSchema",
    "validate_subject_code_pt",
    "validate_subject_name_pt",
    "validate_subject_workload_hours_pt",
]
