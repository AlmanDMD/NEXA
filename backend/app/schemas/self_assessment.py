"""Schemas Pydantic v2 para Questionários e Ciclos de Autoavaliação de Competências (BE-035)."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import AliasChoices, BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import (
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
)
from app.schemas.competency import validate_required_level_pt
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import CompetencyCategory, DiagnosticType
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


def validate_self_assessment_scale_level_pt(value: Any, *, field_label: str) -> int:
    """Valida que um nível de autoavaliação (perceived_level ou confidence_score) seja um inteiro entre 1 e 5."""
    try:
        return validate_required_level_pt(value)
    except PydanticCustomError as exc:
        raise PydanticCustomError(
            "self_assessment_level_invalid",
            f"{field_label} deve ser um número inteiro entre 1 e 5.",
        ) from exc


def validate_perceived_level_pt(value: Any) -> int:
    """Valida que perceived_level seja um número inteiro entre 1 e 5."""
    return validate_self_assessment_scale_level_pt(
        value,
        field_label="O nível percebido de domínio (perceived_level)",
    )


def validate_confidence_score_pt(value: Any) -> int:
    """Valida que confidence_score seja um número inteiro entre 1 e 5."""
    return validate_self_assessment_scale_level_pt(
        value,
        field_label="O grau de confiança (confidence_score)",
    )


def validate_difficulty_notes_pt(value: Any) -> str | None:
    """Sanitiza o relato opcional de dificuldades práticas encontradas pelo estudante (até 1000 caracteres)."""
    cleaned = sanitize_optional_text(value, collapse_spaces=False)
    if cleaned is None:
        return None
    if len(cleaned) > 1000:
        raise PydanticCustomError(
            "difficulty_notes_too_long",
            "O relato de dificuldades (difficulty_notes) deve ter no máximo 1000 caracteres.",
        )
    return cleaned


type PerceivedLevelInt = Annotated[
    int,
    BeforeValidator(validate_perceived_level_pt),
    Field(
        description="Nível percebido de domínio prático declarado pelo estudante (escala inteira de 1 a 5)",
        examples=[4],
    ),
]

type ConfidenceScoreInt = Annotated[
    int,
    BeforeValidator(validate_confidence_score_pt),
    Field(
        description="Grau de segurança/confiança na execução da competência (escala inteira de 1 a 5)",
        examples=[3],
    ),
]

type OptionalDifficultyNotesStr = Annotated[
    str | None,
    BeforeValidator(validate_difficulty_notes_pt),
    Field(
        description="Relato opcional de dificuldades técnicas ou operacionais encontradas nas máquinas/bancada (até 1000 caracteres)",
        examples=["Dificuldade em compensar a folga do anel graduado no passe de acabamento."],
    ),
]


class StudentSelfAssessmentAnswerInputSchema(StrictRequestSchema):
    """Item individual de resposta de autoavaliação por competência (BE-036)."""

    competency_id: UUID = Field(
        description="Identificador UUID da competência técnica vinculada ao módulo (module_competencies)",
    )
    perceived_level: PerceivedLevelInt
    confidence_score: ConfidenceScoreInt
    difficulty_notes: OptionalDifficultyNotesStr = None


class StudentSelfAssessmentSubmitRequestSchema(StrictRequestSchema):
    """Payload de submissão de respostas de autoavaliação pelo estudante autenticado (POST /api/v1/self-assessments/submit)."""

    form_id: UUID = Field(
        description="Identificador UUID do questionário de autoavaliação ativo (self_assessment_forms.id)",
    )
    student_id: UUID | None = Field(
        default=None,
        description="Campo opcional validado estritamente contra current_user.id para impedir submissão em nome de outro aluno",
    )
    responses: list[StudentSelfAssessmentAnswerInputSchema] = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("responses", "answers", "items"),
        description="Lista de respostas de autoavaliação para cada competência do módulo",
    )

    @model_validator(mode="after")
    def validate_unique_competencies(self) -> Self:
        """Impede o envio de competency_id duplicado na mesma submissão."""
        seen: set[UUID] = set()
        for item in self.responses:
            if item.competency_id in seen:
                raise PydanticCustomError(
                    "duplicate_self_assessment_competency",
                    "A submissão contém respostas duplicadas para a mesma competência (competency_id).",
                )
            seen.add(item.competency_id)
        return self


class StudentSelfAssessmentAnswerResponseSchema(BaseResponseSchema):
    """Resposta individual persistida em student_self_assessments (DB-032 / BE-036)."""

    id: UUID = Field(description="Identificador UUID do registro em student_self_assessments")
    form_id: UUID = Field(description="Identificador UUID do formulário de autoavaliação")
    student_id: UUID = Field(description="Identificador UUID do estudante autenticado")
    competency_id: UUID = Field(description="Identificador UUID da competência técnica")
    competency_code: str = Field(description="Código institucional da competência")
    competency_title: str = Field(description="Título da competência técnica")
    competency_category: CompetencyCategory = Field(
        description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)",
    )
    perceived_level: int = Field(
        ge=1,
        le=5,
        description="Nível percebido de domínio prático (1 a 5)",
    )
    confidence_score: int = Field(
        ge=1,
        le=5,
        description="Grau de confiança declarado pelo estudante (1 a 5)",
    )
    difficulty_notes: str | None = Field(
        default=None,
        description="Relato opcional de dificuldades práticas",
    )
    is_high_difficulty: bool = Field(
        description="Indica se o estudante relatou dificuldade alta nesta competência (perceived_level <= 2)",
    )
    submitted_at: datetime = Field(description="Data/hora da submissão da resposta (UTC)")


class HelpRequestSuggestionCompetencySchema(BaseResponseSchema):
    """Resumo de competência em que o estudante relatou dificuldade alta (perceived_level <= 2)."""

    competency_id: UUID = Field(description="Identificador UUID da competência")
    competency_code: str = Field(description="Código institucional da competência")
    competency_title: str = Field(description="Título da competência técnica")
    perceived_level: int = Field(ge=1, le=2, description="Nível percebido declarado (<= 2)")
    confidence_score: int = Field(ge=1, le=5, description="Grau de confiança declarado")
    difficulty_notes: str | None = Field(
        default=None,
        description="Relato de dificuldade enviado pelo estudante",
    )


class HelpRequestSuggestionSchema(BaseResponseSchema):
    """Sugestão opcional de abertura de pedido de ajuda confidencial quando há perceived_level <= 2 (Regra BE-036)."""

    should_suggest_help_request: bool = Field(
        description="Indica se o sistema sugere a abertura opcional de um pedido de apoio pedagógico (perceived_level <= 2)",
    )
    high_difficulty_count: int = Field(
        ge=0,
        description="Quantidade de competências com dificuldade alta relatada (perceived_level <= 2)",
    )
    suggested_category: str = Field(
        default="PRACTICAL_DIFFICULTY",
        description="Categoria sugerida para abertura do pedido de ajuda (PRACTICAL_DIFFICULTY)",
    )
    suggested_endpoint: str = Field(
        default="/api/v1/help-requests",
        description="Rota de destino para abertura opcional da solicitação confidencial de apoio",
    )
    subject_id: UUID = Field(description="Identificador UUID da disciplina para o pedido de ajuda")
    module_id: UUID = Field(description="Identificador UUID do módulo prático para o pedido de ajuda")
    message: str | None = Field(
        default=None,
        description="Mensagem acolhedora exibida na interface sugerindo solicitar apoio ao professor",
    )
    flagged_competencies: list[HelpRequestSuggestionCompetencySchema] = Field(
        default_factory=list,
        description="Lista de competências em que o aluno indicou nível percebido <= 2",
    )


class DiagnosticEvidenceSummarySchema(BaseResponseSchema):
    """Evidência prática individual (skill_evidences - DB-033) utilizada na geração do diagnóstico explicável (BE-037)."""

    evidence_id: UUID = Field(description="Identificador UUID da evidência em skill_evidences")
    competency_id: UUID = Field(description="Identificador UUID da competência técnica")
    source_submission_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da entrega prática (task_submissions) que originou a evidência",
    )
    task_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da atividade prática de oficina (practical_tasks)",
    )
    task_title: str | None = Field(
        default=None,
        description="Título da atividade prática avaliada pelo docente",
    )
    verified_level: Decimal = Field(
        description="Nível técnico verificado pelo docente na escala de 1.00 a 5.00",
    )
    verified_by: UUID = Field(description="Identificador UUID do docente avaliador")
    recorded_at: datetime = Field(description="Data/hora do registro da evidência prática")

    @field_validator("verified_level", mode="after")
    @classmethod
    def quantize_verified_level(cls, value: Decimal) -> Decimal:
        """Padroniza verified_level com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class ExplainableDiagnosticItemResponseSchema(BaseResponseSchema):
    """Diagnóstico explicável gerado pelo algoritmo de cruzamento Autoavaliação vs. Evidência Docente (DB-035 / BE-036 / BE-037)."""

    id: UUID = Field(description="Identificador UUID do diagnóstico em explainable_diagnostics")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    student_name: str | None = Field(
        default=None,
        description="Nome completo do estudante analisado",
    )
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    module_title: str | None = Field(
        default=None,
        description="Título do módulo prático analisado",
    )
    competency_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da competência analisada",
    )
    competency_code: str | None = Field(
        default=None,
        description="Código institucional da competência analisada",
    )
    competency_title: str | None = Field(
        default=None,
        description="Título da competência analisada",
    )
    competency_category: CompetencyCategory | None = Field(
        default=None,
        description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)",
    )
    self_perceived_level: Decimal = Field(
        description="Nível percebido pelo estudante (1.00 a 5.00)",
    )
    teacher_verified_level: Decimal = Field(
        description="Média das evidências práticas verificadas pelo docente em skill_evidences (1.00 a 5.00)",
    )
    discrepancy_gap: Decimal = Field(
        description="Diferença calculada (self_perceived_level - teacher_verified_level)",
    )
    confidence_score: int | None = Field(
        default=None,
        description="Grau de confiança declarado pelo estudante na autoavaliação (1 a 5)",
    )
    evidence_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de evidências práticas (skill_evidences) consideradas no cruzamento",
    )
    evidences_used: list[DiagnosticEvidenceSummarySchema] = Field(
        default_factory=list,
        description="Lista explícita de evidências práticas (skill_evidences) utilizadas no cálculo do diagnóstico (BE-037)",
    )
    diagnostic_type: DiagnosticType = Field(
        description="Classificação diagnóstica (ALIGNED, OVERCONFIDENCE_RISK, UNDERCONFIDENCE_SUPPORT, INSUFFICIENT_EVIDENCE)",
    )
    explanation_text: str = Field(
        description="Texto explicativo detalhando os critérios e valores comparados",
    )
    limitations_note: str = Field(
        description="Nota de transparência explicitando as limitações da análise diagnóstica",
    )
    recommended_action: str = Field(
        description="Ação pedagógica recomendada ao professor e ao estudante",
    )
    pedagogical_alert_triggered: bool = Field(
        default=False,
        description="Indica se a divergência gerou/atualizou alerta pedagógico (SELF_EVAL_GAP) para competência de segurança ou precisão",
    )
    pedagogical_alert_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do alerta pedagógico (academic_alerts) quando acionado",
    )
    generated_at: datetime = Field(description="Data/hora de geração do diagnóstico explicável")

    @field_validator(
        "self_perceived_level",
        "teacher_verified_level",
        "discrepancy_gap",
        mode="after",
    )
    @classmethod
    def quantize_diagnostic_decimals(cls, value: Decimal) -> Decimal:
        """Padroniza níveis e gap com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class DiagnosticEngineEvaluationResponseSchema(BaseResponseSchema):
    """Resultado consolidado da execução do Motor de Cruzamento Diagnóstico Explicável (BE-037)."""

    class_id: UUID = Field(description="Identificador UUID da turma avaliada")
    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional de módulo prático avaliado",
    )
    student_id: UUID | None = Field(
        default=None,
        description="Filtro opcional de estudante avaliado",
    )
    evaluated_at: datetime = Field(description="Data/hora da execução do cruzamento diagnóstico")
    total_diagnostics_generated: int = Field(
        ge=0,
        description="Total de diagnósticos por competência processados a partir de vw_self_eval_discrepancy",
    )
    aligned_count: int = Field(
        ge=0,
        description="Quantidade de competências classificadas como ALIGNED",
    )
    overconfidence_risk_count: int = Field(
        ge=0,
        description="Quantidade de competências classificadas como OVERCONFIDENCE_RISK",
    )
    underconfidence_support_count: int = Field(
        ge=0,
        description="Quantidade de competências classificadas como UNDERCONFIDENCE_SUPPORT",
    )
    insufficient_evidence_count: int = Field(
        ge=0,
        description="Quantidade de competências classificadas como INSUFFICIENT_EVIDENCE",
    )
    pedagogical_alerts_triggered_count: int = Field(
        ge=0,
        description="Quantidade de alertas pedagógicos (SELF_EVAL_GAP) gerados/atualizados em competências de segurança ou precisão",
    )
    ethical_disclaimer: str = Field(
        description="Nota ética e metodológica garantindo que a autoavaliação nunca é tratada como prova definitiva de competência",
    )
    diagnostics: list[ExplainableDiagnosticItemResponseSchema] = Field(
        default_factory=list,
        description="Lista detalhada dos diagnósticos explicáveis gravados em explainable_diagnostics",
    )


class StudentSelfAssessmentSubmitResponseSchema(BaseResponseSchema):
    """Resposta consolidada da submissão de autoavaliação pelo estudante com diagnóstico e sugestão de apoio (BE-036)."""

    form_id: UUID = Field(description="Identificador UUID do questionário respondido")
    student_id: UUID = Field(description="Identificador UUID do estudante autenticado")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    total_submitted: int = Field(
        ge=1,
        description="Total de respostas de competências processadas na submissão",
    )
    created_count: int = Field(
        ge=0,
        description="Quantidade de novas respostas criadas em student_self_assessments",
    )
    updated_count: int = Field(
        ge=0,
        description="Quantidade de respostas atualizadas dentro da janela aberta do formulário",
    )
    is_form_completed: bool = Field(
        description="Indica se todas as competências do módulo foram respondidas pelo estudante",
    )
    suggest_help_request: bool = Field(
        description="Atalho booleano indicando se há sugestão de pedido de ajuda (perceived_level <= 2)",
    )
    help_request_suggestion: HelpRequestSuggestionSchema = Field(
        description="Detalhes da sugestão opcional de pedido de ajuda quando perceived_level <= 2",
    )
    diagnostic_triggered: bool = Field(
        default=True,
        description="Indica que o algoritmo de cruzamento diagnóstico (BE-037) foi disparado após a submissão",
    )
    diagnostics: list[ExplainableDiagnosticItemResponseSchema] = Field(
        default_factory=list,
        description="Diagnósticos explicáveis gerados a partir do cruzamento com skill_evidences",
    )
    responses: list[StudentSelfAssessmentAnswerResponseSchema] = Field(
        default_factory=list,
        description="Lista das respostas de autoavaliação gravadas em student_self_assessments",
    )
    submitted_at: datetime = Field(description="Timestamp UTC da submissão")


__all__ = [
    "ClassSelfAssessmentFormsListResponseSchema",
    "ClassSelfAssessmentFormsParamsDep",
    "ClassSelfAssessmentFormsQueryParams",
    "ConfidenceScoreInt",
    "DEFAULT_SELF_ASSESSMENT_SCALE",
    "DiagnosticEngineEvaluationResponseSchema",
    "DiagnosticEvidenceSummarySchema",
    "ExplainableDiagnosticItemResponseSchema",
    "HelpRequestSuggestionCompetencySchema",
    "HelpRequestSuggestionSchema",
    "OptionalDifficultyNotesStr",
    "OptionalSelfAssessmentInstructionsStr",
    "PerceivedLevelInt",
    "SelfAssessmentClosesAtDatetime",
    "SelfAssessmentCompetencyItemSchema",
    "SelfAssessmentFormCreateSchema",
    "SelfAssessmentFormResponseSchema",
    "SelfAssessmentFormUpdateWindowSchema",
    "SelfAssessmentOpensAtDatetime",
    "SelfAssessmentScaleDefinitionSchema",
    "SelfAssessmentScaleLevelDescriptorSchema",
    "SelfAssessmentTitleStr",
    "StudentSelfAssessmentAnswerInputSchema",
    "StudentSelfAssessmentAnswerResponseSchema",
    "StudentSelfAssessmentSubmitRequestSchema",
    "StudentSelfAssessmentSubmitResponseSchema",
    "validate_confidence_score_pt",
    "validate_difficulty_notes_pt",
    "validate_perceived_level_pt",
    "validate_self_assessment_closes_at_pt",
    "validate_self_assessment_instructions_pt",
    "validate_self_assessment_opens_at_pt",
    "validate_self_assessment_title_pt",
]
