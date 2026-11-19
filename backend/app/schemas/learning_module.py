"""Schemas Pydantic v2 para validação e serialização de Módulos de Aprendizagem Prática (BE-014)."""

from decimal import Decimal, InvalidOperation
import re
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.validators import sanitize_optional_text, sanitize_text

_INT_PATTERN: re.Pattern[str] = re.compile(r"^[+-]?\d+$")
_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")
_MIN_PASSING_SCORE: Decimal = Decimal("0.00")
_MAX_PASSING_SCORE: Decimal = Decimal("10.00")
_MIN_MODULE_WEIGHT: Decimal = Decimal("0.00")
_MAX_MODULE_WEIGHT: Decimal = Decimal("99.99")


def _parse_decimal_two_places(
    value: Any,
    *,
    error_code: str,
    error_message: str,
) -> Decimal:
    """Converte entrada numérica/texto para Decimal validando finitude e até 2 casas decimais."""
    if isinstance(value, bool):
        raise PydanticCustomError(error_code, error_message)

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, float):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise PydanticCustomError(error_code, error_message)
        try:
            parsed = Decimal(cleaned)
        except InvalidOperation as exc:
            raise PydanticCustomError(error_code, error_message) from exc
    else:
        raise PydanticCustomError(error_code, error_message)

    if not parsed.is_finite():
        raise PydanticCustomError(error_code, error_message)

    exponent = parsed.normalize().as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise PydanticCustomError(
            f"{error_code}_precision",
            f"{error_message} Informe no máximo 2 casas decimais.",
        )

    return parsed.quantize(_DECIMAL_QUANTIZER)


def validate_learning_module_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título do módulo prático de aprendizagem."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "learning_module_title_too_short",
            "O título do módulo prático deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 120:
        raise PydanticCustomError(
            "learning_module_title_too_long",
            "O título do módulo prático deve ter no máximo 120 caracteres.",
        )
    return cleaned


def validate_module_order_index_pt(value: Any) -> int:
    """Garante que o índice de ordenação didática seja um inteiro estritamente maior que zero."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "learning_module_order_index_invalid",
            "O índice de ordenação (order_index) deve ser um número inteiro maior que zero.",
        )

    if isinstance(value, int):
        if value > 0:
            return value
        raise PydanticCustomError(
            "learning_module_order_index_invalid",
            "O índice de ordenação (order_index) deve ser um número inteiro maior que zero.",
        )

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if parsed > 0:
                return parsed

    raise PydanticCustomError(
        "learning_module_order_index_invalid",
        "O índice de ordenação (order_index) deve ser um número inteiro maior que zero.",
    )


def validate_practical_hours_pt(value: Any) -> int:
    """Garante que a carga horária prática seja um inteiro maior ou igual a zero."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "learning_module_practical_hours_invalid",
            "A carga horária prática (practical_hours) deve ser um inteiro maior ou igual a zero.",
        )

    if isinstance(value, int):
        if value >= 0:
            return value
        raise PydanticCustomError(
            "learning_module_practical_hours_invalid",
            "A carga horária prática (practical_hours) deve ser um inteiro maior ou igual a zero.",
        )

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if parsed >= 0:
                return parsed

    raise PydanticCustomError(
        "learning_module_practical_hours_invalid",
        "A carga horária prática (practical_hours) deve ser um inteiro maior ou igual a zero.",
    )


def validate_passing_score_pt(value: Any) -> Decimal:
    """Valida a nota de corte (passing_score) entre 0.00 e 10.00 com até 2 casas decimais."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="passing_score_invalid",
        error_message="A nota de corte (passing_score) deve estar entre 0.00 e 10.00.",
    )
    if not (_MIN_PASSING_SCORE <= parsed <= _MAX_PASSING_SCORE):
        raise PydanticCustomError(
            "passing_score_out_of_range",
            "A nota de corte (passing_score) deve estar entre 0.00 e 10.00.",
        )
    return parsed


def validate_module_weight_pt(value: Any) -> Decimal:
    """Valida o peso ponderado do módulo (> 0.00 e <= 99.99) com até 2 casas decimais."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="module_weight_invalid",
        error_message="O peso do módulo (module_weight) deve ser maior que 0.00 e no máximo 99.99.",
    )
    if not (_MIN_MODULE_WEIGHT < parsed <= _MAX_MODULE_WEIGHT):
        raise PydanticCustomError(
            "module_weight_invalid",
            "O peso do módulo (module_weight) deve ser maior que 0.00 e no máximo 99.99.",
        )
    return parsed


type LearningModuleTitleStr = Annotated[
    str,
    BeforeValidator(validate_learning_module_title_pt),
    Field(
        description="Título do módulo de aprendizagem prática (3 a 120 caracteres)",
        examples=["Módulo de Tornearia Cilíndrica"],
    ),
]

type PositiveOrderIndexInt = Annotated[
    int,
    BeforeValidator(validate_module_order_index_pt),
    Field(
        description="Ordem didática sequencial do módulo na disciplina (inteiro >= 1)",
        examples=[1],
    ),
]

type NonNegativePracticalHoursInt = Annotated[
    int,
    BeforeValidator(validate_practical_hours_pt),
    Field(
        description="Carga horária prática de oficina em horas (inteiro >= 0)",
        examples=[40],
    ),
]

type PassingScoreDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_passing_score_pt),
    Field(
        description="Nota mínima de aprovação (passing_score) entre 0.00 e 10.00 (padrão 6.00)",
        examples=["6.00"],
    ),
]

type ModuleWeightDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_module_weight_pt),
    Field(
        description="Peso ponderado do módulo na composição final da disciplina (> 0.00 e <= 99.99)",
        examples=["1.00"],
    ),
]


class LearningModuleCreateSchema(StrictRequestSchema):
    """Schema de entrada para criação de módulo prático (POST /api/v1/modules)."""

    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica à qual o módulo pertence",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: LearningModuleTitleStr
    order_index: int | None = Field(
        default=None,
        description="Ordem didática sequencial na disciplina (>= 1; se omitido, atribuído automaticamente ao final)",
        examples=[1],
    )
    description: str | None = Field(
        default=None,
        description="Descrição do escopo prático, bancadas e equipamentos utilizados",
        examples=["Operação segura do torno mecânico convencional, faceamento e torneamento cilíndrico externo."],
    )
    practical_hours: NonNegativePracticalHoursInt
    module_weight: ModuleWeightDecimal = Field(
        default=Decimal("1.00"),
        description="Peso ponderado do módulo na composição final da disciplina (padrão 1.00)",
        examples=["1.00"],
    )
    passing_score: PassingScoreDecimal = Field(
        default=Decimal("6.00"),
        description="Nota de corte do módulo entre 0.00 e 10.00 (padrão 6.00)",
        examples=["6.00"],
    )

    @field_validator("order_index", mode="before")
    @classmethod
    def validate_order_index(cls, value: Any) -> int | None:
        if value is None:
            return None
        return validate_module_order_index_pt(value)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)


class SubjectSummarySchema(BaseResponseSchema):
    """Resumo dos dados da disciplina técnica embutido na resposta do módulo prático."""

    id: UUID = Field(
        description="Identificador UUID da disciplina técnica",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    course_id: UUID = Field(
        description="Identificador UUID do curso técnico vinculado à disciplina",
    )
    code: str = Field(
        description="Código identificador da disciplina técnica",
        examples=["MET-DIM-01"],
    )
    name: str = Field(
        description="Nome oficial da disciplina técnica",
        examples=["Metrologia Dimensional"],
    )
    workload_hours: int = Field(
        description="Carga horária total da disciplina em horas",
        examples=[80],
    )
    is_active: bool = Field(
        description="Indica se a disciplina está ativa na matriz curricular",
        examples=[True],
    )


class LearningModuleResponseSchema(EntityResponseSchema):
    """Schema de saída detalhado para serialização de LearningModule do SQLAlchemy."""

    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica vinculada",
    )
    title: str = Field(
        description="Título do módulo de aprendizagem prática",
        examples=["Módulo de Tornearia Cilíndrica"],
    )
    order_index: int = Field(
        ge=1,
        description="Posição na sequência didática recomendada da disciplina",
        examples=[1],
    )
    description: str | None = Field(
        default=None,
        description="Descrição do escopo prático, bancadas e equipamentos",
    )
    practical_hours: int = Field(
        ge=0,
        description="Carga horária prática do módulo em horas de oficina",
        examples=[40],
    )
    module_weight: Decimal = Field(
        description="Peso ponderado do módulo na composição final da disciplina",
        examples=["1.00"],
    )
    passing_score: Decimal = Field(
        description="Nota mínima de aprovação do módulo (0.00 a 10.00)",
        examples=["6.00"],
    )
    subject: SubjectSummarySchema = Field(
        description="Resumo da disciplina técnica vinculada ao módulo prático",
    )

    @field_validator("module_weight", "passing_score", mode="after")
    @classmethod
    def quantize_decimal_fields(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)


class LearningModuleListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada para listagem ordenada de módulos (GET /api/v1/subjects/{subject_id}/modules)."""

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
        description="Quantidade máxima de módulos por página (1 a 100)",
        examples=[20],
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual por título ou descrição do módulo prático",
        examples=["Tornearia"],
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


class LearningModulePaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de módulos práticos."""

    data: list[LearningModuleResponseSchema] = Field(
        default_factory=list,
        description="Lista de módulos práticos ordenados por order_index ascendente",
    )
    total: int = Field(
        ge=0,
        description="Total geral de módulos práticos encontrados",
        examples=[4],
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


type LearningModuleListParamsDep = Annotated[LearningModuleListQueryParams, Query()]

__all__ = [
    "LearningModuleCreateSchema",
    "LearningModuleListParamsDep",
    "LearningModuleListQueryParams",
    "LearningModulePaginatedResponseSchema",
    "LearningModuleResponseSchema",
    "LearningModuleTitleStr",
    "ModuleWeightDecimal",
    "NonNegativePracticalHoursInt",
    "PassingScoreDecimal",
    "PositiveOrderIndexInt",
    "SubjectSummarySchema",
    "validate_learning_module_title_pt",
    "validate_module_order_index_pt",
    "validate_module_weight_pt",
    "validate_passing_score_pt",
    "validate_practical_hours_pt",
]
