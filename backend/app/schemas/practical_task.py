"""Schemas Pydantic v2 para Atividades Práticas de Oficina e Critérios de Tolerância (BE-024)."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Annotated, Any, Self
from urllib.parse import urlparse
from uuid import UUID

from fastapi import Query
from pydantic import AliasChoices, BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import LessonModuleSummarySchema
from app.schemas.competency import (
    CompetencyWeightDecimal,
    RequiredLevelInt,
    validate_competency_weight_pt,
    validate_required_level_pt,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import CompetencyCategory
from app.schemas.learning_module import _parse_decimal_two_places
from app.schemas.validators import sanitize_optional_text, sanitize_text

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")
_MIN_MAX_SCORE: Decimal = Decimal("1.00")
_MAX_MAX_SCORE: Decimal = Decimal("10.00")


def validate_practical_task_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título da atividade prática de oficina (3 a 150 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "practical_task_title_too_short",
            "O título da atividade prática deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "practical_task_title_too_long",
            "O título da atividade prática deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_task_criterion_name_pt(value: Any) -> str:
    """Sanitiza espaços e valida o nome do critério técnico/rubrica (3 a 180 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "task_criterion_name_too_short",
            "O nome do critério técnico (criterion_name) deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 180:
        raise PydanticCustomError(
            "task_criterion_name_too_long",
            "O nome do critério técnico (criterion_name) deve ter no máximo 180 caracteres.",
        )
    return cleaned


def validate_blueprint_url_pt(value: Any) -> str | None:
    """Sanitiza e valida a URL opcional do desenho técnico ou folha de processo (http/https, <= 500 chars)."""
    cleaned = sanitize_optional_text(value, collapse_spaces=False)
    if cleaned is None:
        return None
    if len(cleaned) > 500:
        raise PydanticCustomError(
            "blueprint_url_too_long",
            "A URL do desenho técnico (blueprint_url) deve ter no máximo 500 caracteres.",
        )
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise PydanticCustomError(
            "blueprint_url_invalid",
            "A URL do desenho técnico (blueprint_url) deve ser um endereço válido iniciando com http:// ou https://.",
        )
    return cleaned


def validate_practical_task_max_score_pt(value: Any) -> Decimal:
    """Valida a pontuação máxima (max_score) da atividade prática entre 1.00 e 10.00."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="practical_task_max_score_invalid",
        error_message="A pontuação máxima (max_score) deve estar entre 1.00 e 10.00.",
    )
    if not (_MIN_MAX_SCORE <= parsed <= _MAX_MAX_SCORE):
        raise PydanticCustomError(
            "practical_task_max_score_out_of_range",
            "A pontuação máxima (max_score) deve estar entre 1.00 e 10.00.",
        )
    return parsed


def validate_practical_task_due_date_pt(value: Any) -> datetime:
    """Converte e valida o prazo de entrega (due_date) aceitando ISO-8601 datetime ou date."""
    error_message = (
        "Prazo de entrega (due_date) inválido. Informe data/hora no formato ISO-8601."
    )
    if isinstance(value, bool):
        raise PydanticCustomError("practical_task_due_date_invalid", error_message)

    if isinstance(value, datetime):
        parsed_dt = value
    elif isinstance(value, date):
        parsed_dt = datetime.combine(value, time(23, 59, 59), tzinfo=timezone.utc)
    elif isinstance(value, str):
        cleaned = sanitize_text(value, collapse_spaces=False)
        if not cleaned:
            raise PydanticCustomError("practical_task_due_date_invalid", error_message)
        normalized_iso = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
        try:
            if "T" in normalized_iso or " " in normalized_iso:
                parsed_dt = datetime.fromisoformat(normalized_iso)
            else:
                parsed_date = date.fromisoformat(normalized_iso)
                parsed_dt = datetime.combine(
                    parsed_date,
                    time(23, 59, 59),
                    tzinfo=timezone.utc,
                )
        except ValueError as exc:
            raise PydanticCustomError("practical_task_due_date_invalid", error_message) from exc
    else:
        raise PydanticCustomError("practical_task_due_date_invalid", error_message)

    if parsed_dt.tzinfo is None:
        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
    return parsed_dt


type PracticalTaskTitleStr = Annotated[
    str,
    BeforeValidator(validate_practical_task_title_pt),
    Field(
        description="Título da atividade prática de oficina (3 a 150 caracteres)",
        examples=["Usinagem de Eixo Escalonado Ø25mm H7"],
    ),
]

type TaskCriterionNameStr = Annotated[
    str,
    BeforeValidator(validate_task_criterion_name_pt),
    Field(
        description="Descrição objetiva do critério técnico ou tolerância de bancada (3 a 180 caracteres)",
        examples=["Tolerância Dimensional ±0,02mm no Micrômetro"],
    ),
]

type OptionalBlueprintUrlStr = Annotated[
    str | None,
    BeforeValidator(validate_blueprint_url_pt),
    Field(
        description="Link HTTP/HTTPS opcional para o desenho técnico ou folha de processo (até 500 caracteres)",
        examples=["https://cdn.senai.br/blueprints/eixo-escalonado-h7.pdf"],
    ),
]

type PracticalTaskMaxScoreDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_practical_task_max_score_pt),
    Field(
        description="Pontuação máxima da atividade prática entre 1.00 e 10.00 (padrão 10.00)",
        examples=["10.00"],
    ),
]

type PracticalTaskDueDate = Annotated[
    datetime,
    BeforeValidator(validate_practical_task_due_date_pt),
    Field(
        description="Data e hora limite para conclusão/entrega da atividade prática (ISO-8601)",
        examples=["2026-04-20T23:59:59Z"],
    ),
]


class TaskCriterionCreateItemSchema(StrictRequestSchema):
    """Item de rubrica/critério técnico vinculado a uma competência na criação da atividade prática."""

    competency_id: UUID = Field(
        description="Identificador UUID da competência técnica avaliada neste critério",
    )
    criterion_name: TaskCriterionNameStr
    weight: CompetencyWeightDecimal = Field(
        default=Decimal("1.00"),
        description="Peso relativo do critério no cálculo da nota da peça (> 0.00 e <= 9.99)",
        examples=["1.00"],
    )
    min_acceptable_level: RequiredLevelInt = Field(
        default=3,
        description="Nível mínimo aceitável de domínio técnico na escala SENAI de 1 a 5 (padrão 3)",
        examples=[3],
    )

    @field_validator("weight", mode="before")
    @classmethod
    def validate_weight(cls, value: Any) -> Decimal:
        return validate_competency_weight_pt(value)

    @field_validator("min_acceptable_level", mode="before")
    @classmethod
    def validate_min_level(cls, value: Any) -> int:
        return validate_required_level_pt(value)


class PracticalTaskCreateSchema(StrictRequestSchema):
    """Payload de criação de atividade prática com critérios de tolerância (POST /api/v1/practical-tasks)."""

    module_id: UUID = Field(
        description="Identificador UUID do módulo prático de aprendizagem (learning_modules)",
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica (classes)",
    )
    title: PracticalTaskTitleStr
    description: str | None = Field(
        default=None,
        description="Instruções detalhadas de usinagem, bancada, instrumentos e segurança",
    )
    blueprint_url: OptionalBlueprintUrlStr = None
    due_date: PracticalTaskDueDate
    max_score: PracticalTaskMaxScoreDecimal = Field(
        default=Decimal("10.00"),
        description="Pontuação máxima da atividade prática (1.00 a 10.00, padrão 10.00)",
        examples=["10.00"],
    )
    is_mandatory: bool = Field(
        default=True,
        description="Indica se a entrega da atividade prática é obrigatória para o módulo",
    )
    criteria: list[TaskCriterionCreateItemSchema] = Field(
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("criteria", "task_criteria"),
        description="Lista de critérios técnicos / rubricas de tolerância vinculadas a competências",
    )

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Any) -> str | None:
        return sanitize_optional_text(value, collapse_spaces=False)

    @model_validator(mode="after")
    def validate_unique_criterion_names(self) -> Self:
        """Evita critérios duplicados com o mesmo nome na mesma atividade prática."""
        seen: set[str] = set()
        for item in self.criteria:
            normalized_key = item.criterion_name.lower()
            if normalized_key in seen:
                raise PydanticCustomError(
                    "duplicate_task_criterion_name",
                    "A atividade prática não pode conter critérios (rubricas) com nomes duplicados.",
                )
            seen.add(normalized_key)
        return self


class TaskCriterionCompetencySummarySchema(BaseResponseSchema):
    """Resumo da competência técnica associada a um critério de avaliação prática."""

    id: UUID = Field(description="Identificador UUID da competência técnica")
    code: str = Field(description="Código institucional da competência")
    title: str = Field(description="Título da competência técnica")
    category: CompetencyCategory = Field(description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)")


class TaskCriterionResponseSchema(BaseResponseSchema):
    """Schema de saída para critério de avaliação prática / rubrica (task_criteria)."""

    id: UUID = Field(description="Identificador UUID do critério técnico")
    task_id: UUID = Field(description="Identificador UUID da atividade prática")
    competency_id: UUID = Field(description="Identificador UUID da competência técnica vinculada")
    criterion_name: str = Field(description="Nome/descrição do critério de tolerância ou operação")
    weight: Decimal = Field(description="Peso do critério na atividade prática")
    min_acceptable_level: int = Field(
        ge=1,
        le=5,
        description="Nível mínimo aceitável de domínio (1 a 5)",
    )
    competency: TaskCriterionCompetencySummarySchema = Field(
        description="Resumo da competência técnica vinculada à rubrica",
    )

    @field_validator("weight", mode="after")
    @classmethod
    def quantize_weight(cls, value: Decimal) -> Decimal:
        """Padroniza weight com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class PracticalTaskResponseSchema(EntityResponseSchema):
    """Schema de saída detalhado de atividade prática com rubricas e contadores de submissão."""

    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    title: str = Field(description="Título da atividade prática")
    description: str | None = Field(default=None, description="Descrição técnica da atividade")
    blueprint_url: str | None = Field(
        default=None,
        description="URL do desenho técnico / folha de processo",
    )
    due_date: datetime = Field(description="Prazo de entrega da atividade prática")
    max_score: Decimal = Field(description="Pontuação máxima (1.00 a 10.00)")
    is_mandatory: bool = Field(description="Indica se a atividade prática é obrigatória")
    initialized_submissions_count: int = Field(
        ge=0,
        description="Total de entregas inicializadas automaticamente para os alunos ativos da turma",
    )
    total_submissions_count: int = Field(
        ge=0,
        description="Total de registros em task_submissions vinculados à tarefa",
    )
    pending_submissions_count: int = Field(
        ge=0,
        description="Quantidade de alunos com entrega ainda pendente (PENDING ou LATE)",
    )
    completed_submissions_count: int = Field(
        ge=0,
        description="Quantidade de alunos com entrega concluída ou avaliada (SUBMITTED ou EVALUATED)",
    )
    module: LessonModuleSummarySchema = Field(
        description="Resumo do módulo de aprendizagem prática",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica",
    )
    criteria: list[TaskCriterionResponseSchema] = Field(
        default_factory=list,
        description="Lista de critérios técnicos / rubricas de avaliação da tarefa",
    )
    task_criteria: list[TaskCriterionResponseSchema] = Field(
        default_factory=list,
        description="Alias compatível com DB-024/BE-024 para a lista de rubricas da tarefa",
    )

    @field_validator("max_score", mode="after")
    @classmethod
    def quantize_max_score(cls, value: Decimal) -> Decimal:
        """Padroniza max_score com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class PracticalTaskListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada para GET /api/v1/modules/{module_id}/practical-tasks."""

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
        description="Quantidade máxima de atividades práticas por página (1 a 100)",
        examples=[20],
    )
    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    is_mandatory: bool | None = Field(
        default=None,
        description="Filtro opcional por obrigatoriedade da atividade prática",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Busca textual opcional por título ou descrição da atividade prática",
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


class PracticalTaskPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de atividades práticas do módulo."""

    data: list[PracticalTaskResponseSchema] = Field(
        default_factory=list,
        description="Lista de atividades práticas do módulo ordenadas por prazo de entrega",
    )
    total: int = Field(ge=0, description="Total de atividades práticas encontradas")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite de registros por página")


type PracticalTaskListParamsDep = Annotated[PracticalTaskListQueryParams, Query()]


__all__ = [
    "OptionalBlueprintUrlStr",
    "PracticalTaskCreateSchema",
    "PracticalTaskDueDate",
    "PracticalTaskListParamsDep",
    "PracticalTaskListQueryParams",
    "PracticalTaskMaxScoreDecimal",
    "PracticalTaskPaginatedResponseSchema",
    "PracticalTaskResponseSchema",
    "PracticalTaskTitleStr",
    "TaskCriterionCompetencySummarySchema",
    "TaskCriterionCreateItemSchema",
    "TaskCriterionNameStr",
    "TaskCriterionResponseSchema",
    "validate_blueprint_url_pt",
    "validate_practical_task_due_date_pt",
    "validate_practical_task_max_score_pt",
    "validate_practical_task_title_pt",
    "validate_task_criterion_name_pt",
]
