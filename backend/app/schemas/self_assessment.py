"""Schemas Pydantic v2 para Questionários e Ciclos de Autoavaliação de Competências (BE-035)."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import (
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import CompetencyCategory
from app.schemas.validators import sanitize_optional_text, sanitize_text

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")


def validate_self_assessment_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título do questionário de autoavaliação (3 a 150 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "self_assessment_title_too_short",
            "O título do questionário de autoavaliação deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "self_assessment_title_too_long",
            "O título do questionário de autoavaliação deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_self_assessment_instructions_pt(value: Any) -> str | None:
    """Sanitiza instruções opcionais do questionário de autoavaliação (até 2000 caracteres)."""
    cleaned = sanitize_optional_text(value, collapse_spaces=False)
    if cleaned is None:
        return None
    if len(cleaned) > 2000:
        raise PydanticCustomError(
            "self_assessment_instructions_too_long",
            "As instruções do questionário (instructions) devem ter no máximo 2000 caracteres.",
        )
    return cleaned


def _parse_iso_datetime_pt(
    value: Any,
    *,
    field_name: str,
    end_of_day_for_date: bool = False,
) -> datetime:
    """Converte e valida data/hora ISO-8601 normalizando para UTC."""
    error_message = (
        f"Data/hora ({field_name}) inválida. Informe um valor no formato ISO-8601."
    )
    error_code = f"self_assessment_{field_name}_invalid"

    if isinstance(value, bool):
        raise PydanticCustomError(error_code, error_message)

    if isinstance(value, datetime):
        parsed_dt = value
    elif isinstance(value, date):
        default_time = (
            time(23, 59, 59) if end_of_day_for_date else time(0, 0, 0)
        )
        parsed_dt = datetime.combine(value, default_time, tzinfo=timezone.utc)
    elif isinstance(value, str):
        cleaned = sanitize_text(value, collapse_spaces=False)
        if not cleaned:
            raise PydanticCustomError(error_code, error_message)
        normalized_iso = (
            cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
        )
        try:
            if "T" in normalized_iso or " " in normalized_iso:
                parsed_dt = datetime.fromisoformat(normalized_iso)
            else:
                parsed_date = date.fromisoformat(normalized_iso)
                default_time = (
                    time(23, 59, 59) if end_of_day_for_date else time(0, 0, 0)
                )
                parsed_dt = datetime.combine(
                    parsed_date,
                    default_time,
                    tzinfo=timezone.utc,
                )
        except ValueError as exc:
            raise PydanticCustomError(error_code, error_message) from exc
    else:
        raise PydanticCustomError(error_code, error_message)

    if parsed_dt.tzinfo is None:
        return parsed_dt.replace(tzinfo=timezone.utc)
    return parsed_dt.astimezone(timezone.utc)


def validate_self_assessment_opens_at_pt(value: Any) -> datetime:
    """Valida a data/hora de abertura do questionário de autoavaliação (opens_at)."""
    return _parse_iso_datetime_pt(
        value,
        field_name="opens_at",
        end_of_day_for_date=False,
    )


def validate_self_assessment_closes_at_pt(value: Any) -> datetime:
    """Valida a data/hora de fechamento do questionário de autoavaliação (closes_at)."""
    return _parse_iso_datetime_pt(
        value,
        field_name="closes_at",
        end_of_day_for_date=True,
    )


type SelfAssessmentTitleStr = Annotated[
    str,
    BeforeValidator(validate_self_assessment_title_pt),
    Field(
        description="Título do ciclo/questionário de autoavaliação (3 a 150 caracteres)",
        examples=["Autoavaliação de Competências — Módulo 1: Metrologia Dimensional"],
    ),
]

type OptionalSelfAssessmentInstructionsStr = Annotated[
    str | None,
    BeforeValidator(validate_self_assessment_instructions_pt),
    Field(
        description="Instruções pedagógicas opcionais exibidas ao estudante antes de responder (até 2000 caracteres)",
        examples=[
            "Avalie com sinceridade seu nível de domínio prático (1 a 5) e seu grau de segurança em cada competência do módulo."
        ],
    ),
]

type SelfAssessmentOpensAtDatetime = Annotated[
    datetime,
    BeforeValidator(validate_self_assessment_opens_at_pt),
    Field(
        description="Data e hora de início para submissão do questionário (ISO-8601 UTC)",
        examples=["2026-04-01T08:00:00Z"],
    ),
]

type SelfAssessmentClosesAtDatetime = Annotated[
    datetime,
    BeforeValidator(validate_self_assessment_closes_at_pt),
    Field(
        description="Data e hora limite para encerramento do questionário (ISO-8601 UTC, estritamente posterior a opens_at)",
        examples=["2026-04-15T23:59:59Z"],
    ),
]


class SelfAssessmentScaleLevelDescriptorSchema(BaseResponseSchema):
    """Descritor de um nível da escala pedagógica SENAI de 1 a 5 exibida no formulário de autoavaliação."""

    level: int = Field(
        ge=1,
        le=5,
        description="Valor numérico inteiro da escala (1 a 5)",
    )
    label: str = Field(
        description="Rótulo resumido do nível de proficiência ou confiança",
    )
    description: str = Field(
        description="Explicação didática do nível para orientar a autoavaliação do estudante",
    )


class SelfAssessmentScaleDefinitionSchema(BaseResponseSchema):
    """Definição estruturada da escala de 1 a 5 para nível percebido e confiança (FE-041 / BE-035)."""

    min_level: int = Field(
        default=1,
        description="Valor mínimo permitido na escala de autoavaliação (1)",
    )
    max_level: int = Field(
        default=5,
        description="Valor máximo permitido na escala de autoavaliação (5)",
    )
    options: list[int] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5],
        description="Valores inteiros selecionáveis no componente de escala (1 a 5)",
    )
    levels: list[SelfAssessmentScaleLevelDescriptorSchema] = Field(
        default_factory=list,
        description="Descritores detalhados de cada nível de 1 a 5 na taxonomia prática SENAI",
    )


DEFAULT_SELF_ASSESSMENT_SCALE: SelfAssessmentScaleDefinitionSchema = (
    SelfAssessmentScaleDefinitionSchema(
        min_level=1,
        max_level=5,
        options=[1, 2, 3, 4, 5],
        levels=[
            SelfAssessmentScaleLevelDescriptorSchema(
                level=1,
                label="Iniciante / Dependentes de Apoio",
                description="Reconhece os conceitos básicos, mas precisa de auxílio constante na bancada ou oficina.",
            ),
            SelfAssessmentScaleLevelDescriptorSchema(
                level=2,
                label="Em Desenvolvimento",
                description="Executa etapas simples com supervisão frequente e consulta constante à folha de processo.",
            ),
            SelfAssessmentScaleLevelDescriptorSchema(
                level=3,
                label="Proficiente / Autonomia Padrão SENAI",
                description="Realiza a operação dentro das tolerâncias e normas de segurança com autonomia esperada para o módulo.",
            ),
            SelfAssessmentScaleLevelDescriptorSchema(
                level=4,
                label="Avançado",
                description="Domina a técnica com precisão, identifica desvios rapidamente e mantém alto padrão de qualidade.",
            ),
            SelfAssessmentScaleLevelDescriptorSchema(
                level=5,
                label="Domínio Pleno / Referência na Oficina",
                description="Executa com excelência técnica, solucionando imprevistos complexos e podendo apoiar colegas.",
            ),
        ],
    )
)


class SelfAssessmentCompetencyItemSchema(BaseResponseSchema):
    """Competência técnica vinculada ao módulo retornada no formulário de autoavaliação (module_competencies)."""

    id: UUID = Field(description="Identificador UUID da competência técnica (competencies.id)")
    competency_id: UUID = Field(
        description="Identificador UUID da competência técnica vinculada ao módulo",
    )
    module_id: UUID = Field(
        description="Identificador UUID do módulo de aprendizagem prática",
    )
    code: str = Field(
        description="Código institucional da competência na matriz SENAI",
        examples=["COMP-MET-01"],
    )
    title: str = Field(
        description="Título da competência ou habilidade técnica",
        examples=["Medição com Paquímetro e Tolerância H7"],
    )
    description: str | None = Field(
        default=None,
        description="Descrição técnica detalhada da competência para leitura no formulário",
    )
    category: CompetencyCategory = Field(
        description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)",
    )
    weight: Decimal = Field(
        description="Peso ponderado da competência no módulo prático",
    )
    required_level: int = Field(
        ge=1,
        le=5,
        description="Nível esperado de proficiência no módulo (1 a 5)",
    )
    min_level: int = Field(
        default=1,
        description="Limite inferior da escala de resposta (1)",
    )
    max_level: int = Field(
        default=5,
        description="Limite superior da escala de resposta (5)",
    )
    scale_options: list[int] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5],
        description="Opções numéricas da escala de 1 a 5 para autoavaliação desta competência",
    )
    is_answered: bool | None = Field(
        default=None,
        description="Quando consultado por um estudante, indica se esta competência já foi respondida no formulário",
    )
    student_perceived_level: int | None = Field(
        default=None,
        description="Quando consultado pelo próprio estudante, nível percebido já submetido (1 a 5)",
    )
    student_confidence_score: int | None = Field(
        default=None,
        description="Quando consultado pelo próprio estudante, grau de confiança já submetido (1 a 5)",
    )
    student_difficulty_notes: str | None = Field(
        default=None,
        description="Quando consultado pelo próprio estudante, relato opcional de dificuldade já submetido",
    )

    @field_validator("weight", mode="after")
    @classmethod
    def quantize_weight(cls, value: Decimal) -> Decimal:
        """Padroniza weight com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class SelfAssessmentFormCreateSchema(StrictRequestSchema):
    """Payload de criação ou reabertura de questionário de autoavaliação (POST /api/v1/self-assessments/forms)."""

    module_id: UUID = Field(
        description="Identificador UUID do módulo de aprendizagem prática (learning_modules)",
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica (classes)",
    )
    title: SelfAssessmentTitleStr
    instructions: OptionalSelfAssessmentInstructionsStr = None
    opens_at: SelfAssessmentOpensAtDatetime
    closes_at: SelfAssessmentClosesAtDatetime
    is_active: bool = Field(
        default=True,
        description="Indica se o ciclo de autoavaliação está ativo para a turma",
    )
    reopen_if_exists: bool = Field(
        default=False,
        description="Quando True, caso já exista formulário para o mesmo módulo e turma, reabre/atualiza seu prazo e status",
    )

    @model_validator(mode="after")
    def validate_window_order(self) -> Self:
        """Valida que a janela de abertura seja estritamente anterior ao fechamento (opens_at < closes_at)."""
        if self.opens_at >= self.closes_at:
            raise PydanticCustomError(
                "self_assessment_invalid_date_window",
                "A janela do questionário é inválida: a data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at).",
            )
        return self


class SelfAssessmentFormUpdateWindowSchema(StrictRequestSchema):
    """Payload para reabertura de prazo ou atualização de questionário pelo professor (PATCH /api/v1/self-assessments/forms/{form_id})."""

    title: SelfAssessmentTitleStr | None = None
    instructions: OptionalSelfAssessmentInstructionsStr = None
    opens_at: SelfAssessmentOpensAtDatetime | None = None
    closes_at: SelfAssessmentClosesAtDatetime | None = None
    is_active: bool | None = Field(
        default=None,
        description="Permite ativar/reabrir (True) ou desativar (False) o questionário",
    )

    @model_validator(mode="after")
    def validate_non_empty_and_window(self) -> Self:
        """Garante que ao menos um campo foi enviado e que opens_at < closes_at quando ambos informados."""
        if (
            self.title is None
            and "instructions" not in self.model_fields_set
            and self.opens_at is None
            and self.closes_at is None
            and self.is_active is None
        ):
            raise PydanticCustomError(
                "empty_self_assessment_update",
                "Informe ao menos um campo para atualizar ou reabrir o questionário de autoavaliação.",
            )
        if (
            self.opens_at is not None
            and self.closes_at is not None
            and self.opens_at >= self.closes_at
        ):
            raise PydanticCustomError(
                "self_assessment_invalid_date_window",
                "A janela do questionário é inválida: a data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at).",
            )
        return self


class SelfAssessmentFormResponseSchema(BaseResponseSchema):
    """Schema de saída detalhado de questionário de autoavaliação com competências do módulo e escala 1..5."""

    id: UUID = Field(description="Identificador UUID do questionário (self_assessment_forms.id)")
    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica do módulo")
    title: str = Field(description="Título do questionário de autoavaliação")
    instructions: str | None = Field(
        default=None,
        description="Instruções pedagógicas para preenchimento",
    )
    opens_at: datetime = Field(description="Data/hora de abertura do questionário (UTC)")
    closes_at: datetime = Field(description="Data/hora de fechamento do questionário (UTC)")
    is_active: bool = Field(description="Indica se o questionário está ativo")
    is_open: bool = Field(
        description="Indica se o questionário está ativo e dentro da janela [opens_at, closes_at] no momento da consulta",
    )
    created_by: UUID = Field(description="Identificador UUID do docente/gestor criador")
    created_at: datetime = Field(description="Data/hora de criação do questionário")
    total_competencies: int = Field(
        ge=1,
        description="Total de competências do módulo que compõem o formulário",
    )
    answered_competencies_count: int | None = Field(
        default=None,
        description="Quando consultado por um estudante, quantidade de competências já respondidas por ele neste formulário",
    )
    is_pending_for_current_student: bool | None = Field(
        default=None,
        description="Quando consultado por um estudante, indica se o formulário ainda está pendente de resposta completa",
    )
    is_completed_by_current_student: bool | None = Field(
        default=None,
        description="Quando consultado por um estudante, indica se todas as competências do módulo já foram respondidas",
    )
    scale: SelfAssessmentScaleDefinitionSchema = Field(
        default=DEFAULT_SELF_ASSESSMENT_SCALE,
        description="Escala padronizada de 1 a 5 para nível percebido e grau de confiança",
    )
    module: LessonModuleSummarySchema = Field(
        description="Resumo do módulo de aprendizagem prática",
    )
    subject: LessonSubjectSummarySchema = Field(
        description="Resumo da disciplina técnica vinculada ao módulo",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica",
    )
    competencies: list[SelfAssessmentCompetencyItemSchema] = Field(
        default_factory=list,
        description="Lista de competências associadas ao módulo (module_competencies) com descrições e escala 1 a 5",
    )
    module_competencies: list[SelfAssessmentCompetencyItemSchema] = Field(
        default_factory=list,
        description="Alias compatível com DB-016/BE-035 para a lista de competências do módulo no formulário",
    )


class ClassSelfAssessmentFormsQueryParams(StrictRequestSchema):
    """Filtros opcionais para listagem de formulários de autoavaliação da turma (GET /api/v1/classes/{class_id}/self-assessments/forms)."""

    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do módulo de aprendizagem prática",
    )
    is_active: bool | None = Field(
        default=None,
        description="Filtro opcional por status ativo/inativo do formulário",
    )
    pending_only: bool | None = Field(
        default=None,
        description="Quando True (padrão automático para perfil STUDENT), retorna apenas formulários ativos, abertos e pendentes de resposta",
    )
    include_completed: bool = Field(
        default=False,
        description="Para perfil STUDENT, quando True inclui também formulários já respondidos pelo aluno logado",
    )


type ClassSelfAssessmentFormsParamsDep = Annotated[
    ClassSelfAssessmentFormsQueryParams,
    Query(),
]


class ClassSelfAssessmentFormsListResponseSchema(BaseResponseSchema):
    """Resposta estruturada de listagem de formulários de autoavaliação de uma turma (GET /api/v1/classes/{class_id}/self-assessments/forms)."""

    class_id: UUID = Field(description="Identificador UUID da turma consultada")
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica",
    )
    total: int = Field(
        ge=0,
        description="Total de formulários retornados na consulta",
    )
    pending_count: int = Field(
        ge=0,
        description="Total de formulários abertos e pendentes de resposta (para o aluno logado) ou ativos na janela (para docente/gestão)",
    )
    scale: SelfAssessmentScaleDefinitionSchema = Field(
        default=DEFAULT_SELF_ASSESSMENT_SCALE,
        description="Definição da escala de 1 a 5 utilizada nos questionários",
    )
    forms: list[SelfAssessmentFormResponseSchema] = Field(
        default_factory=list,
        description="Lista de formulários de autoavaliação com competências do módulo",
    )
    data: list[SelfAssessmentFormResponseSchema] = Field(
        default_factory=list,
        description="Envelope padrão de dados contendo a lista de formulários de autoavaliação",
    )


__all__ = [
    "ClassSelfAssessmentFormsListResponseSchema",
    "ClassSelfAssessmentFormsParamsDep",
    "ClassSelfAssessmentFormsQueryParams",
    "DEFAULT_SELF_ASSESSMENT_SCALE",
    "OptionalSelfAssessmentInstructionsStr",
    "SelfAssessmentClosesAtDatetime",
    "SelfAssessmentCompetencyItemSchema",
    "SelfAssessmentFormCreateSchema",
    "SelfAssessmentFormResponseSchema",
    "SelfAssessmentFormUpdateWindowSchema",
    "SelfAssessmentOpensAtDatetime",
    "SelfAssessmentScaleDefinitionSchema",
    "SelfAssessmentScaleLevelDescriptorSchema",
    "SelfAssessmentTitleStr",
    "validate_self_assessment_closes_at_pt",
    "validate_self_assessment_instructions_pt",
    "validate_self_assessment_opens_at_pt",
    "validate_self_assessment_title_pt",
]
