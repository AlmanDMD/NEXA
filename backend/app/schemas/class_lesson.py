"""Schemas Pydantic v2 para Diário de Classe e Registro de Aulas Ministradas (BE-021)."""

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.academic_class import ISODate, validate_iso_date_pt
from app.schemas.base import BaseResponseSchema, StrictRequestSchema, UUIDResponseMixin
from app.schemas.enums import AttendanceStatus, EnrollmentStatus, RiskLevel
from app.schemas.validators import sanitize_optional_text, sanitize_text

_INT_PATTERN: re.Pattern[str] = re.compile(r"^[+-]?\d+$")
_DECIMAL_QUANTIZER = Decimal("0.01")


def validate_lesson_workload_hours_pt(value: Any) -> int:
    """Garante que a carga horária da aula seja um número inteiro entre 1 e 8 horas."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "lesson_workload_invalid",
            "A carga horária da aula (workload_hours) deve ser um número inteiro entre 1 e 8 horas.",
        )

    if isinstance(value, int):
        if 1 <= value <= 8:
            return value
        raise PydanticCustomError(
            "lesson_workload_invalid",
            "A carga horária da aula (workload_hours) deve ser um número inteiro entre 1 e 8 horas.",
        )

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if 1 <= parsed <= 8:
                return parsed

    raise PydanticCustomError(
        "lesson_workload_invalid",
        "A carga horária da aula (workload_hours) deve ser um número inteiro entre 1 e 8 horas.",
    )


def validate_topic_summary_pt(value: Any) -> str:
    """Sanitiza e valida o resumo do conteúdo ministrado na aula."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "topic_summary_too_short",
            "O resumo do conteúdo (topic_summary) deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 2000:
        raise PydanticCustomError(
            "topic_summary_too_long",
            "O resumo do conteúdo (topic_summary) deve ter no máximo 2000 caracteres.",
        )
    return cleaned


def validate_lab_environment_pt(value: Any) -> str | None:
    """Sanitiza e valida o ambiente ou oficina prática opcional da aula."""
    cleaned = sanitize_optional_text(value, collapse_spaces=True)
    if cleaned is None:
        return None
    if len(cleaned) > 100:
        raise PydanticCustomError(
            "lab_environment_too_long",
            "O ambiente/oficina (lab_environment) deve ter no máximo 100 caracteres.",
        )
    return cleaned


type LessonWorkloadHoursInt = Annotated[
    int,
    BeforeValidator(validate_lesson_workload_hours_pt),
    Field(
        description="Carga horária ministrada na aula em horas (1 a 8 horas)",
        examples=[4],
    ),
]

type LessonTopicSummaryStr = Annotated[
    str,
    BeforeValidator(validate_topic_summary_pt),
    Field(
        description="Resumo técnico do conteúdo teórico ou prático abordado na aula (3 a 2000 caracteres)",
        examples=["Torneamento cilíndrico externo e faceamento com controle no micrômetro."],
    ),
]

type OptionalLabEnvironmentStr = Annotated[
    str | None,
    BeforeValidator(validate_lab_environment_pt),
    Field(
        description="Identificação opcional da oficina ou laboratório prático utilizado",
        examples=["Oficina de Tornearia 02"],
    ),
]


class ClassLessonCreateSchema(StrictRequestSchema):
    """Schema de entrada para criação de aula no diário de classe (POST /api/v1/lessons)."""

    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica lecionada",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático abordado na aula",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    )
    teacher_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do docente responsável (quando omitido, utiliza o docente autenticado)",
    )
    lesson_date: ISODate
    workload_hours: LessonWorkloadHoursInt = Field(
        default=4,
        description="Carga horária ministrada na aula (inteiro de 1 a 8 horas, padrão 4)",
        examples=[4],
    )
    topic_summary: LessonTopicSummaryStr
    lab_environment: OptionalLabEnvironmentStr = None


class LessonTeacherSummarySchema(BaseResponseSchema):
    """Resumo do docente responsável embutido na resposta da aula."""

    id: UUID = Field(description="Identificador UUID do docente")
    email: str = Field(description="E-mail institucional do docente")
    full_name: str | None = Field(default=None, description="Nome completo do docente")
    registration_number: str | None = Field(
        default=None,
        description="Matrícula funcional SENAI do docente",
    )


class LessonSubjectSummarySchema(BaseResponseSchema):
    """Resumo da disciplina técnica embutido na resposta da aula."""

    id: UUID = Field(description="Identificador UUID da disciplina")
    code: str = Field(description="Código identificador da disciplina")
    name: str = Field(description="Nome oficial da disciplina")
    workload_hours: int = Field(description="Carga horária total da disciplina em horas")


class LessonModuleSummarySchema(BaseResponseSchema):
    """Resumo do módulo de aprendizagem prática embutido na resposta da aula."""

    id: UUID = Field(description="Identificador UUID do módulo prático")
    title: str = Field(description="Título do módulo prático")
    order_index: int = Field(ge=1, description="Ordem didática do módulo")
    practical_hours: int = Field(ge=0, description="Carga horária prática do módulo em horas")


class ClassLessonResponseSchema(UUIDResponseMixin, BaseResponseSchema):
    """Schema de saída detalhado de aula ministrada e lista de chamada pré-inicializada."""

    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo prático vinculado",
    )
    teacher_id: UUID = Field(description="Identificador UUID do docente que ministrou a aula")
    lesson_date: date = Field(description="Data da aula ministrada (AAAA-MM-DD)")
    workload_hours: int = Field(
        ge=1,
        le=8,
        description="Carga horária ministrada na aula em horas (1 a 8h)",
    )
    topic_summary: str = Field(description="Resumo do conteúdo ministrado")
    lab_environment: str | None = Field(
        default=None,
        description="Ambiente ou oficina prática utilizada",
    )
    initialized_attendance_count: int = Field(
        ge=0,
        description="Quantidade de registros de chamada pré-inicializados para alunos ativos da turma",
    )
    teacher: LessonTeacherSummarySchema = Field(description="Resumo do docente responsável")
    subject: LessonSubjectSummarySchema = Field(description="Resumo da disciplina")
    module: LessonModuleSummarySchema | None = Field(
        default=None,
        description="Resumo do módulo prático associado",
    )
    created_at: datetime = Field(description="Data e hora de registro da aula (UTC ISO 8601)")


class ClassLessonListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada para listagem de aulas de uma turma."""

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
        description="Quantidade máxima de aulas por página (1 a 100)",
        examples=[20],
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da disciplina técnica",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do módulo prático",
    )
    start_date: date | None = Field(
        default=None,
        description="Filtro opcional de data inicial (AAAA-MM-DD)",
        examples=["2026-02-01"],
    )
    end_date: date | None = Field(
        default=None,
        description="Filtro opcional de data final (AAAA-MM-DD)",
        examples=["2026-06-30"],
    )

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_optional_date(cls, value: Any) -> date | None:
        if value is None:
            return None
        return validate_iso_date_pt(value)

    @model_validator(mode="after")
    def validate_date_filter_range(self) -> Self:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise PydanticCustomError(
                "invalid_date_range",
                "A data inicial (start_date) não pode ser posterior à data final (end_date).",
            )
        return self

    @property
    def offset(self) -> int:
        """Retorna o deslocamento (OFFSET) calculado para consultas SQLAlchemy."""
        return (self.page - 1) * self.limit


class ClassLessonPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de aulas da turma."""

    data: list[ClassLessonResponseSchema] = Field(
        default_factory=list,
        description="Lista de aulas registradas na turma ordenadas da mais recente para a mais antiga",
    )
    total: int = Field(ge=0, description="Total geral de aulas encontradas")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite máximo de registros por página")


type ClassLessonListParamsDep = Annotated[ClassLessonListQueryParams, Query()]


def validate_absent_hours_pt(value: Any) -> int:
    """Garante que as horas ausentes em chamada sejam um inteiro entre 0 e 8."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "attendance_absent_hours_invalid",
            "A quantidade de horas ausentes (absent_hours) deve ser um número inteiro entre 0 e 8.",
        )

    if isinstance(value, int):
        if 0 <= value <= 8:
            return value
        raise PydanticCustomError(
            "attendance_absent_hours_invalid",
            "A quantidade de horas ausentes (absent_hours) deve ser um número inteiro entre 0 e 8.",
        )

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if 0 <= parsed <= 8:
                return parsed

    raise PydanticCustomError(
        "attendance_absent_hours_invalid",
        "A quantidade de horas ausentes (absent_hours) deve ser um número inteiro entre 0 e 8.",
    )


def validate_justification_note_pt(value: Any) -> str | None:
    """Sanitiza a justificativa opcional de ausência/atraso limitando a 500 caracteres."""
    cleaned = sanitize_optional_text(value, collapse_spaces=True)
    if cleaned is None:
        return None
    if len(cleaned) > 500:
        raise PydanticCustomError(
            "justification_note_too_long",
            "A justificativa da frequência (justification_note) deve ter no máximo 500 caracteres.",
        )
    return cleaned


type AbsentHoursInt = Annotated[
    int,
    BeforeValidator(validate_absent_hours_pt),
    Field(
        ge=0,
        le=8,
        description="Quantidade de horas ausentes registradas para a aula (0 a 8h)",
        examples=[0],
    ),
]

type OptionalJustificationNoteStr = Annotated[
    str | None,
    BeforeValidator(validate_justification_note_pt),
    Field(
        description="Observação ou justificativa opcional para falta ou atraso (até 500 caracteres)",
        examples=["Atestado médico entregue à secretaria."],
    ),
]


class AttendanceRecordItemInputSchema(StrictRequestSchema):
    """Item individual da chamada em lote de uma aula (POST /api/v1/lessons/{id}/attendance)."""

    student_id: UUID = Field(
        description="Identificador UUID do estudante matriculado na turma da aula",
    )
    status: AttendanceStatus = Field(
        description="Situação de frequência na aula (PRESENT, ABSENT, LATE, JUSTIFIED)",
        examples=[AttendanceStatus.PRESENT],
    )
    absent_hours: AbsentHoursInt | None = Field(
        default=None,
        description="Horas ausentes na aula (0 a carga horária da aula; padrão derivado do status quando omitido)",
        examples=[0],
    )
    justification_note: OptionalJustificationNoteStr = None


class BatchAttendanceRequestSchema(StrictRequestSchema):
    """Payload da chamada rápida em lote contendo todos os registros da aula."""

    records: list[AttendanceRecordItemInputSchema] = Field(
        min_length=1,
        max_length=200,
        description="Lista de registros individuais de presença/falta da turma",
    )

    @model_validator(mode="after")
    def validate_unique_students(self) -> Self:
        """Impede envio duplicado do mesmo student_id dentro do mesmo lote de chamada."""
        seen: set[UUID] = set()
        for item in self.records:
            if item.student_id in seen:
                raise PydanticCustomError(
                    "duplicate_attendance_student",
                    "A lista de chamada contém student_id duplicado no mesmo lote.",
                )
            seen.add(item.student_id)
        return self


class UpdatedEnrollmentAttendanceSchema(BaseResponseSchema):
    """Resumo atualizado da matrícula após recálculo de frequência no servidor."""

    enrollment_id: UUID = Field(description="Identificador UUID da matrícula atualizada")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    status: AttendanceStatus = Field(description="Status gravado para a aula")
    absent_hours: int = Field(ge=0, le=8, description="Horas ausentes computadas na aula")
    attendance_rate: Decimal = Field(
        description="Taxa de frequência recalculada no servidor (0.00 a 100.00%)",
        examples=["95.00"],
    )
    is_attendance_critical: bool = Field(
        description="Indica se a frequência atualizada caiu abaixo de 78% (< 78.00%)",
    )
    risk_level: RiskLevel = Field(
        description="Nível de risco avaliado pelo motor de regras de frequência",
    )

    @field_validator("attendance_rate", mode="after")
    @classmethod
    def quantize_attendance_rate(cls, value: Decimal) -> Decimal:
        """Padroniza attendance_rate com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class BatchAttendanceResponseSchema(BaseResponseSchema):
    """Resumo consolidado do processamento em lote da chamada da aula."""

    lesson_id: UUID = Field(description="Identificador UUID da aula processada")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    total_processed: int = Field(ge=0, description="Total de registros processados no lote")
    present_count: int = Field(
        ge=0,
        description="Quantidade de alunos com presença contabilizada (PRESENT, LATE, JUSTIFIED)",
    )
    absent_count: int = Field(
        ge=0,
        description="Quantidade de alunos registrados com falta integral (ABSENT)",
    )
    at_risk_students_count: int = Field(
        ge=0,
        description="Quantidade de alunos com frequência abaixo de 78% após o recálculo",
    )
    updated_enrollments: list[UpdatedEnrollmentAttendanceSchema] = Field(
        default_factory=list,
        description="Lista das matrículas recalculadas no servidor",
    )


class StudentAttendanceQueryParams(StrictRequestSchema):
    """Filtros opcionais para consulta de frequência consolidada do estudante (BE-023)."""

    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da disciplina técnica",
    )


type StudentAttendanceQueryParamsDep = Annotated[StudentAttendanceQueryParams, Query()]


class StudentAttendanceSummaryStudentSchema(BaseResponseSchema):
    """Identificação resumida do estudante no extrato consolidado de frequência."""

    id: UUID = Field(description="Identificador UUID do estudante")
    email: str = Field(description="E-mail institucional do estudante")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do estudante",
    )
    registration_number: str | None = Field(
        default=None,
        description="Matrícula acadêmica SENAI do estudante",
    )


class ModuleAttendanceRiskItemSchema(BaseResponseSchema):
    """Indicadores consolidados de frequência e margem de 75% por módulo prático (vw_module_attendance_risk)."""

    enrollment_id: UUID = Field(description="Identificador UUID da matrícula na turma")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    class_code: str = Field(description="Código da turma (ex: USI-2026-1M)")
    class_period: str = Field(description="Período letivo da turma (ex: 2026.1)")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    subject_code: str = Field(description="Código da disciplina técnica")
    subject_name: str = Field(description="Nome da disciplina técnica")
    module_id: UUID = Field(description="Identificador UUID do módulo de aprendizagem prática")
    module_title: str = Field(description="Título do módulo prático (ex: Tornearia, Metrologia)")
    order_index: int = Field(ge=1, description="Ordem didática do módulo na disciplina")
    planned_hours: int = Field(
        ge=0,
        description="Carga horária prática prevista para o módulo",
    )
    total_hours: int = Field(
        ge=0,
        description="Total de horas-aula ministradas no módulo até o momento",
    )
    attended_hours: int = Field(
        ge=0,
        description="Total de horas com presença computada para o estudante no módulo",
    )
    absent_hours: int = Field(
        ge=0,
        description="Total de horas de faltas não justificadas no módulo",
    )
    justified_absent_hours: int = Field(
        ge=0,
        description="Total de horas de ausências justificadas (JUSTIFIED) no módulo",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual exato de presença no módulo (0.00 a 100.00%)",
        examples=["85.00"],
    )
    is_critical: bool = Field(
        description="Alerta preventivo quando o percentual de presença é inferior a 78% (< 78.00%)",
    )
    is_attendance_critical: bool = Field(
        description="Flag booleana da view vw_module_attendance_risk (< 78.00%)",
    )
    risk_level: RiskLevel = Field(
        description="Nível de risco avaliado pelo motor preventivo (LOW, HIGH <78%, CRITICAL <75%)",
    )
    min_required_percentage: Decimal = Field(
        description="Percentual mínimo legal exigido para aprovação por frequência (75.00%)",
        examples=["75.00"],
    )
    max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) proporcional às horas já ministradas",
        examples=["5.00"],
    )
    remaining_absent_hours_margin: Decimal = Field(
        description="Margem restante de horas de falta sobre as aulas ministradas antes do limite de 75%",
        examples=["1.00"],
    )
    planned_max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) sobre a carga horária prevista do módulo",
        examples=["10.00"],
    )
    planned_remaining_absent_hours_margin: Decimal = Field(
        description="Saldo restante de horas que o aluno ainda pode faltar no módulo antes do limite de 75%",
        examples=["6.00"],
    )
    percentage_margin_to_limit: Decimal = Field(
        description="Margem percentual atual em relação ao limite mínimo de 75.00% (attendance_percentage - 75.00)",
        examples=["10.00"],
    )

    @field_validator(
        "attendance_percentage",
        "min_required_percentage",
        "max_allowed_absent_hours",
        "remaining_absent_hours_margin",
        "planned_max_allowed_absent_hours",
        "planned_remaining_absent_hours_margin",
        "percentage_margin_to_limit",
        mode="after",
    )
    @classmethod
    def quantize_decimal_metrics(cls, value: Decimal) -> Decimal:
        """Padroniza os indicadores decimais com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class SubjectConsolidatedAttendanceSchema(BaseResponseSchema):
    """Histórico consolidado de frequência do estudante agrupado por disciplina e seus módulos práticos."""

    enrollment_id: UUID = Field(description="Identificador UUID da matrícula na turma")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    class_code: str = Field(description="Código da turma acadêmica")
    class_period: str = Field(description="Período letivo da turma")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    subject_code: str = Field(description="Código da disciplina técnica")
    subject_name: str = Field(description="Nome da disciplina técnica")
    planned_hours: int = Field(ge=0, description="Carga horária prevista da disciplina")
    total_hours: int = Field(ge=0, description="Total de horas ministradas na disciplina")
    attended_hours: int = Field(ge=0, description="Total de horas com presença na disciplina")
    absent_hours: int = Field(ge=0, description="Total de horas de falta não justificada na disciplina")
    justified_absent_hours: int = Field(
        ge=0,
        description="Total de horas de falta justificada na disciplina",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual consolidado de presença na disciplina (0.00 a 100.00%)",
    )
    is_critical: bool = Field(
        description="Indica se a frequência da disciplina está abaixo de 78% (< 78.00%)",
    )
    is_attendance_critical: bool = Field(
        description="Indica se a frequência da disciplina está abaixo do limiar preventivo de 78%",
    )
    risk_level: RiskLevel = Field(
        description="Nível de risco de frequência na disciplina (LOW, HIGH, CRITICAL)",
    )
    min_required_percentage: Decimal = Field(
        description="Limite mínimo legal de frequência (75.00%)",
    )
    max_allowed_absent_hours: Decimal = Field(
        description="Teto de 25% de faltas sobre as horas ministradas na disciplina",
    )
    remaining_absent_hours_margin: Decimal = Field(
        description="Margem restante de horas de falta sobre as horas ministradas na disciplina",
    )
    planned_max_allowed_absent_hours: Decimal = Field(
        description="Teto de 25% de faltas sobre a carga horária prevista da disciplina",
    )
    planned_remaining_absent_hours_margin: Decimal = Field(
        description="Saldo restante de horas que o aluno pode faltar na disciplina antes do limite de 75%",
    )
    percentage_margin_to_limit: Decimal = Field(
        description="Margem percentual até o limite de 75.00% na disciplina",
    )
    modules: list[ModuleAttendanceRiskItemSchema] = Field(
        default_factory=list,
        description="Lista de módulos práticos da disciplina ordenados por order_index",
    )

    @field_validator(
        "attendance_percentage",
        "min_required_percentage",
        "max_allowed_absent_hours",
        "remaining_absent_hours_margin",
        "planned_max_allowed_absent_hours",
        "planned_remaining_absent_hours_margin",
        "percentage_margin_to_limit",
        mode="after",
    )
    @classmethod
    def quantize_decimal_metrics(cls, value: Decimal) -> Decimal:
        """Padroniza os indicadores decimais com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class StudentLessonAbsenceRecordSchema(BaseResponseSchema):
    """Registro individual de falta, atraso ou justificativa por data de aula para o extrato do aluno."""

    attendance_record_id: UUID = Field(description="Identificador UUID do registro de chamada")
    lesson_id: UUID = Field(description="Identificador UUID da aula ministrada")
    class_id: UUID = Field(description="Identificador UUID da turma")
    subject_id: UUID = Field(description="Identificador UUID da disciplina")
    subject_code: str = Field(description="Código da disciplina")
    subject_name: str = Field(description="Nome da disciplina")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo prático (quando vinculado)",
    )
    module_title: str | None = Field(
        default=None,
        description="Título do módulo prático (quando vinculado)",
    )
    lesson_date: date = Field(description="Data da aula em que ocorreu a ausência/atraso")
    workload_hours: int = Field(ge=1, le=8, description="Carga horária total da aula")
    status: AttendanceStatus = Field(
        description="Situação registrada na chamada (ABSENT, LATE, JUSTIFIED)",
    )
    absent_hours: int = Field(ge=0, le=8, description="Horas de ausência registradas na aula")
    justification_note: str | None = Field(
        default=None,
        description="Justificativa ou observação registrada pelo docente",
    )
    recorded_at: datetime = Field(description="Data/hora da gravação na chamada")


class StudentConsolidatedAttendanceResponseSchema(BaseResponseSchema):
    """Resposta consolidada do extrato de frequência do estudante por disciplina e módulo (BE-023)."""

    student_id: UUID = Field(description="Identificador UUID do estudante consultado")
    student: StudentAttendanceSummaryStudentSchema = Field(
        description="Dados cadastrais resumidos do estudante",
    )
    enrollment_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da matrícula principal/filtrada do estudante",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da turma principal/filtrada do estudante",
    )
    enrollment_status: EnrollmentStatus | None = Field(
        default=None,
        description="Status da matrícula principal/filtrada do estudante",
    )
    planned_hours: int = Field(
        ge=0,
        description="Carga horária total prevista nas disciplinas/módulos consultados",
    )
    total_hours: int = Field(
        ge=0,
        description="Total consolidado de horas-aula ministradas para o estudante",
    )
    attended_hours: int = Field(
        ge=0,
        description="Total consolidado de horas com presença do estudante",
    )
    absent_hours: int = Field(
        ge=0,
        description="Total consolidado de horas de faltas não justificadas",
    )
    justified_absent_hours: int = Field(
        ge=0,
        description="Total consolidado de horas de faltas justificadas (JUSTIFIED)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual consolidado de presença do estudante (0.00 a 100.00%)",
        examples=["85.00"],
    )
    is_critical: bool = Field(
        description="Flag de risco preventivo indicando frequência abaixo de 78% (< 78.00%)",
    )
    is_attendance_critical: bool = Field(
        description="Alias compatível com vw_module_attendance_risk para frequência < 78.00%",
    )
    risk_level: RiskLevel = Field(
        description="Nível de risco consolidado de frequência (LOW, HIGH <78%, CRITICAL <75%)",
    )
    min_required_percentage: Decimal = Field(
        description="Limite mínimo legal de presença exigido (75.00%)",
        examples=["75.00"],
    )
    max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) sobre as horas já ministradas",
    )
    remaining_absent_hours_margin: Decimal = Field(
        description="Margem restante em horas sobre as aulas ministradas até o limite de 75%",
    )
    planned_max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) sobre a carga horária prevista",
    )
    planned_remaining_absent_hours_margin: Decimal = Field(
        description="Saldo restante em horas que o aluno ainda pode faltar na carga prevista antes de 75%",
    )
    percentage_margin_to_limit: Decimal = Field(
        description="Margem percentual atual até o limite mínimo de 75.00%",
    )
    critical_modules_count: int = Field(
        ge=0,
        description="Quantidade de módulos práticos com frequência crítica (< 78.00%)",
    )
    subjects: list[SubjectConsolidatedAttendanceSchema] = Field(
        default_factory=list,
        description="Extrato de frequência agrupado por disciplina técnica e seus módulos práticos",
    )
    modules: list[ModuleAttendanceRiskItemSchema] = Field(
        default_factory=list,
        description="Lista consolidada de módulos práticos consultados da view vw_module_attendance_risk",
    )
    absence_records: list[StudentLessonAbsenceRecordSchema] = Field(
        default_factory=list,
        description="Histórico cronológico de faltas, atrasos e ausências justificadas por data de aula",
    )

    @field_validator(
        "attendance_percentage",
        "min_required_percentage",
        "max_allowed_absent_hours",
        "remaining_absent_hours_margin",
        "planned_max_allowed_absent_hours",
        "planned_remaining_absent_hours_margin",
        "percentage_margin_to_limit",
        mode="after",
    )
    @classmethod
    def quantize_decimal_metrics(cls, value: Decimal) -> Decimal:
        """Padroniza os indicadores decimais com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


__all__ = [
    "AbsentHoursInt",
    "AttendanceRecordItemInputSchema",
    "BatchAttendanceRequestSchema",
    "BatchAttendanceResponseSchema",
    "ClassLessonCreateSchema",
    "ClassLessonListParamsDep",
    "ClassLessonListQueryParams",
    "ClassLessonPaginatedResponseSchema",
    "ClassLessonResponseSchema",
    "LessonModuleSummarySchema",
    "LessonSubjectSummarySchema",
    "LessonTeacherSummarySchema",
    "LessonTopicSummaryStr",
    "LessonWorkloadHoursInt",
    "ModuleAttendanceRiskItemSchema",
    "OptionalJustificationNoteStr",
    "OptionalLabEnvironmentStr",
    "StudentAttendanceQueryParams",
    "StudentAttendanceQueryParamsDep",
    "StudentAttendanceSummaryStudentSchema",
    "StudentConsolidatedAttendanceResponseSchema",
    "StudentLessonAbsenceRecordSchema",
    "SubjectConsolidatedAttendanceSchema",
    "UpdatedEnrollmentAttendanceSchema",
    "validate_absent_hours_pt",
    "validate_justification_note_pt",
    "validate_lab_environment_pt",
    "validate_lesson_workload_hours_pt",
    "validate_topic_summary_pt",
]
