"""Schemas Pydantic v2 para validação e serialização de Competências Técnicas e Vínculos com Módulos (BE-015)."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.enums import CompetencyCategory
from app.schemas.validators import sanitize_optional_text, sanitize_text

_COMPETENCY_CODE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._-]+$")
_INT_PATTERN: re.Pattern[str] = re.compile(r"^[+-]?\d+$")
_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")
_MIN_WEIGHT: Decimal = Decimal("0.00")
_MAX_WEIGHT: Decimal = Decimal("9.99")
_MIN_REQUIRED_LEVEL: int = 1
_MAX_REQUIRED_LEVEL: int = 5


def validate_competency_code_pt(value: Any) -> str:
    """Normaliza (UPPER + TRIM) e valida o código identificador único da competência técnica."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "competency_code_too_short",
            "O código da competência deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 50:
        raise PydanticCustomError(
            "competency_code_too_long",
            "O código da competência deve ter no máximo 50 caracteres.",
        )
    if not _COMPETENCY_CODE_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "competency_code_invalid_format",
            "O código da competência deve conter apenas letras, números, pontos, underscores ou hífens.",
        )
    return cleaned


def validate_competency_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título da competência técnica SENAI."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "competency_title_too_short",
            "O título da competência deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "competency_title_too_long",
            "O título da competência deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_competency_weight_pt(value: Any) -> Decimal:
    """Valida o peso da competência no módulo (> 0.00 e <= 9.99) com até 2 casas decimais."""
    error_message = "O peso da competência (weight) deve ser maior que 0.00 e no máximo 9.99."
    if isinstance(value, bool):
        raise PydanticCustomError("competency_weight_invalid", error_message)

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, float):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise PydanticCustomError("competency_weight_invalid", error_message)
        try:
            parsed = Decimal(cleaned)
        except InvalidOperation as exc:
            raise PydanticCustomError("competency_weight_invalid", error_message) from exc
    else:
        raise PydanticCustomError("competency_weight_invalid", error_message)

    if not parsed.is_finite():
        raise PydanticCustomError("competency_weight_invalid", error_message)

    exponent = parsed.normalize().as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise PydanticCustomError(
            "competency_weight_precision",
            f"{error_message} Informe no máximo 2 casas decimais.",
        )

    quantized = parsed.quantize(_DECIMAL_QUANTIZER)
    if not (_MIN_WEIGHT < quantized <= _MAX_WEIGHT):
        raise PydanticCustomError("competency_weight_out_of_range", error_message)

    return quantized


def validate_required_level_pt(value: Any) -> int:
    """Valida que o nível requerido de proficiência seja um inteiro entre 1 e 5."""
    error_message = "O nível requerido (required_level) deve ser um número inteiro entre 1 e 5."
    if isinstance(value, bool):
        raise PydanticCustomError("required_level_invalid", error_message)

    if isinstance(value, int):
        if _MIN_REQUIRED_LEVEL <= value <= _MAX_REQUIRED_LEVEL:
            return value
        raise PydanticCustomError("required_level_invalid", error_message)

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if _MIN_REQUIRED_LEVEL <= parsed <= _MAX_REQUIRED_LEVEL:
                return parsed

    raise PydanticCustomError("required_level_invalid", error_message)


type CompetencyCodeStr = Annotated[
    str,
    BeforeValidator(validate_competency_code_pt),
    Field(
        description="Código único institucional da competência (3 a 50 caracteres, normalizado em maiúsculas)",
        examples=["COMP-MET-01"],
    ),
]

type CompetencyTitleStr = Annotated[
    str,
    BeforeValidator(validate_competency_title_pt),
    Field(
        description="Título legível da competência técnica (3 a 150 caracteres)",
        examples=["Medição com Paquímetro e Tolerância H7"],
    ),
]

type CompetencyWeightDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_competency_weight_pt),
    Field(
        description="Peso ponderado da competência no módulo (> 0.00 e <= 9.99, padrão 1.00)",
        examples=["1.00"],
    ),
]

type RequiredLevelInt = Annotated[
    int,
    BeforeValidator(validate_required_level_pt),
    Field(
        description="Nível requerido de proficiência da competência no módulo (1 a 5, padrão 3)",
        examples=[3],
    ),
]


class CompetencyCreateSchema(StrictRequestSchema):
    """Schema de entrada para cadastro de competência técnica (POST /api/v1/competencies)."""

    code: CompetencyCodeStr
    title: CompetencyTitleStr
    category: CompetencyCategory = Field(
        description="Categoria da competência técnica (TECHNICAL, SAFETY, PROCEDURAL)",
        examples=[CompetencyCategory.TECHNICAL],
    )
    description: str | None = Field(
        default=None,
        description="Descrição detalhada dos critérios técnicos, tolerâncias ou normas associadas",
        examples=["Interpretar leituras milimétricas e verificar tolerâncias IT/H7 com paquímetro."],
    )

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)


class CompetencyResponseSchema(EntityResponseSchema):
    """Schema de saída para serialização de Competency do SQLAlchemy."""

    code: str = Field(
        description="Código único institucional da competência",
        examples=["COMP-MET-01"],
    )
    title: str = Field(
        description="Título da competência técnica",
        examples=["Medição com Paquímetro e Tolerância H7"],
    )
    category: CompetencyCategory = Field(
        description="Categoria da competência na taxonomia SENAI",
        examples=[CompetencyCategory.TECHNICAL],
    )
    description: str | None = Field(
        default=None,
        description="Descrição técnica detalhada da competência",
    )


class CompetencyListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada para listagem de competências (GET /api/v1/competencies)."""

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
        description="Quantidade máxima de competências por página (1 a 100)",
        examples=[20],
    )
    category: CompetencyCategory | None = Field(
        default=None,
        description="Filtro opcional por categoria (TECHNICAL, SAFETY, PROCEDURAL)",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual por código, título ou descrição da competência",
        examples=["Paquímetro"],
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


class CompetencyPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de competências."""

    data: list[CompetencyResponseSchema] = Field(
        default_factory=list,
        description="Lista de competências da página atual",
    )
    total: int = Field(
        ge=0,
        description="Total geral de competências encontradas",
        examples=[15],
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


class ModuleCompetencyCreateSchema(StrictRequestSchema):
    """Schema de entrada para associação módulo-competência (POST /api/v1/modules/{id}/competencies)."""

    competency_id: UUID = Field(
        description="Identificador UUID da competência técnica a vincular ao módulo",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    weight: CompetencyWeightDecimal = Field(
        default=Decimal("1.00"),
        description="Peso ponderado da competência na nota do módulo (> 0.00 e <= 9.99, padrão 1.00)",
        examples=["1.50"],
    )
    required_level: RequiredLevelInt = Field(
        default=3,
        description="Nível requerido de proficiência entre 1 (Básico) e 5 (Avançado), padrão 3",
        examples=[4],
    )


class ModuleCompetencyResponseSchema(BaseResponseSchema):
    """Schema de saída para vínculo ModuleCompetency com metadados completos da competência."""

    module_id: UUID = Field(
        description="Identificador UUID do módulo prático",
    )
    competency_id: UUID = Field(
        description="Identificador UUID da competência técnica",
    )
    weight: Decimal = Field(
        description="Peso ponderado da competência no módulo",
        examples=["1.50"],
    )
    required_level: int = Field(
        ge=1,
        le=5,
        description="Nível requerido de proficiência (1 a 5)",
        examples=[4],
    )
    competency: CompetencyResponseSchema = Field(
        description="Detalhes da competência técnica vinculada",
    )
    created_at: datetime = Field(
        description="Data e hora de criação do vínculo (UTC ISO 8601)",
    )
    updated_at: datetime = Field(
        description="Data e hora da última atualização do vínculo (UTC ISO 8601)",
    )

    @field_validator("weight", mode="after")
    @classmethod
    def quantize_weight(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)


class LearningModuleSummarySchema(BaseResponseSchema):
    """Resumo do módulo de aprendizagem prática na consulta agregada de competências."""

    id: UUID = Field(description="Identificador UUID do módulo prático")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica vinculada")
    title: str = Field(description="Título do módulo de aprendizagem prática")
    order_index: int = Field(ge=1, description="Posição didática do módulo na disciplina")
    practical_hours: int = Field(ge=0, description="Carga horária prática do módulo em horas")
    passing_score: Decimal = Field(description="Nota de corte do módulo (0.00 a 10.00)")

    @field_validator("passing_score", mode="after")
    @classmethod
    def quantize_passing_score(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)


class ModuleCompetenciesAggregatedResponseSchema(BaseResponseSchema):
    """Resposta agregada de competências por módulo prático para renderização de gráfico radar."""

    module: LearningModuleSummarySchema = Field(
        description="Resumo do módulo de aprendizagem prática consultado",
    )
    total_competencies: int = Field(
        ge=0,
        description="Quantidade total de competências vinculadas ao módulo",
        examples=[4],
    )
    total_weight: Decimal = Field(
        description="Soma dos pesos das competências vinculadas ao módulo",
        examples=["5.50"],
    )
    categories_summary: dict[str, int] = Field(
        description="Contagem de competências por categoria (TECHNICAL, SAFETY, PROCEDURAL)",
        examples=[{"TECHNICAL": 2, "SAFETY": 1, "PROCEDURAL": 1}],
    )
    data: list[ModuleCompetencyResponseSchema] = Field(
        default_factory=list,
        description="Lista detalhada de competências associadas ao módulo",
    )

    @field_validator("total_weight", mode="after")
    @classmethod
    def quantize_total_weight(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)


type CompetencyListParamsDep = Annotated[CompetencyListQueryParams, Query()]

__all__ = [
    "CompetencyCodeStr",
    "CompetencyCreateSchema",
    "CompetencyListParamsDep",
    "CompetencyListQueryParams",
    "CompetencyPaginatedResponseSchema",
    "CompetencyResponseSchema",
    "CompetencyTitleStr",
    "CompetencyWeightDecimal",
    "LearningModuleSummarySchema",
    "ModuleCompetenciesAggregatedResponseSchema",
    "ModuleCompetencyCreateSchema",
    "ModuleCompetencyResponseSchema",
    "RequiredLevelInt",
    "validate_competency_code_pt",
    "validate_competency_title_pt",
    "validate_competency_weight_pt",
    "validate_required_level_pt",
]
