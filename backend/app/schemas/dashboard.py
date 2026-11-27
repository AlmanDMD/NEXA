"""Schemas Pydantic v2 para Dashboard Híbrido do Professor e Visão 360° do Aluno (BE-031)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import Field, field_validator

from app.schemas.academic_assessment import StudentSubjectAverageSchema
from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import (
    ModuleAttendanceRiskItemSchema,
    SubjectConsolidatedAttendanceSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import (
    AcademicStandingStatus,
    AlertCategory,
    AlertStatus,
    CompetencyCategory,
    EnrollmentStatus,
    MilestoneType,
    RiskLevel,
    UserRole,
)
from app.schemas.practical_task import (
    StudentPendingTaskItemSchema,
    StudentTaskCountsSummarySchema,
)

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")


class TeacherClassDashboardQueryParams(StrictRequestSchema):
    """Filtros opcionais para o Dashboard do Professor (GET /api/v1/dashboard/teacher/classes/{id})."""

    subject_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da disciplina técnica",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do módulo de aprendizagem prática",
    )


type TeacherClassDashboardParamsDep = Annotated[
    TeacherClassDashboardQueryParams,
    Query(),
]


class Student360QueryParams(StrictRequestSchema):
    """Filtros opcionais para a Ficha 360° do Aluno (GET /api/v1/students/{id}/360)."""

    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )


type Student360ParamsDep = Annotated[Student360QueryParams, Query()]


class StudentPortalDashboardQueryParams(StrictRequestSchema):
    """Filtros opcionais para o Portal do Aluno (GET /api/v1/dashboard/student/me - BE-034)."""

    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica do estudante",
    )


type StudentPortalDashboardParamsDep = Annotated[
    StudentPortalDashboardQueryParams,
    Query(),
]


class DashboardStudentProfileSchema(BaseResponseSchema):
    """Dados cadastrais resumidos do estudante para o Dashboard e Ficha 360°."""

    id: UUID = Field(description="Identificador UUID do estudante")
    email: str = Field(description="E-mail institucional do estudante")
    full_name: str | None = Field(default=None, description="Nome completo do estudante")
    registration_number: str | None = Field(
        default=None,
        description="Matrícula acadêmica SENAI do estudante",
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL opcional do avatar do estudante",
    )


class DashboardStudent360SummaryItemSchema(BaseResponseSchema):
    """Indicadores pré-agregados por estudante a partir da view vw_student_360_performance (DB-036)."""

    enrollment_id: UUID = Field(description="Identificador UUID da matrícula na turma")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    student_email: str = Field(description="E-mail institucional do estudante")
    student_full_name: str | None = Field(
        default=None,
        description="Nome completo do estudante",
    )
    registration_number: str | None = Field(
        default=None,
        description="Matrícula SENAI do estudante",
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL opcional da foto de perfil do estudante",
    )
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    class_code: str = Field(description="Código da turma acadêmica")
    class_period: str = Field(description="Período letivo da turma")
    enrollment_status: EnrollmentStatus = Field(
        description="Status da matrícula do estudante",
    )
    enrollment_date: date = Field(description="Data de matrícula do estudante")
    overall_average: Decimal | None = Field(
        default=None,
        description="Média geral ponderada do estudante na turma (0.00 a 10.00)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual atualizado de presença do estudante (0.00 a 100.00%)",
    )
    total_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas atribuídas ao estudante",
    )
    pending_tasks_count: int = Field(
        ge=0,
        description="Quantidade de atividades práticas pendentes dentro do prazo",
    )
    late_tasks_count: int = Field(
        ge=0,
        description="Quantidade de atividades práticas em atraso (LATE)",
    )
    submitted_tasks_count: int = Field(
        ge=0,
        description="Quantidade de atividades práticas entregues aguardando avaliação",
    )
    evaluated_tasks_count: int = Field(
        ge=0,
        description="Quantidade de atividades práticas avaliadas pelo docente",
    )
    completed_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas concluídas (SUBMITTED + EVALUATED)",
    )
    on_time_completed_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas concluídas dentro do prazo",
    )
    on_time_tasks_percentage: Decimal = Field(
        description="Percentual de entregas práticas concluídas no prazo pelo estudante",
    )
    active_alerts_count: int = Field(
        ge=0,
        description="Quantidade de alertas acadêmicos ativos para o estudante",
    )
    standing_status: AcademicStandingStatus = Field(
        description="Situação acadêmica consolidada (APPROVED, IN_RECOVERY, AT_RISK)",
    )
    risk_level: RiskLevel = Field(
        description="Nível de atenção/risco acadêmico atual (LOW, MODERATE, HIGH, CRITICAL)",
    )
    is_at_risk: bool = Field(
        description="Indica se o estudante requer atenção pedagógica preventiva (risk_level != LOW)",
    )

    @field_validator("attendance_percentage", "on_time_tasks_percentage", mode="after")
    @classmethod
    def quantize_percentages(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("overall_average", mode="after")
    @classmethod
    def quantize_optional_average(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class TeacherDashboardKpisSchema(BaseResponseSchema):
    """KPIs globais consolidados da turma para os cards de topo do Dashboard do Professor (FE-031)."""

    total_students: int = Field(
        ge=0,
        description="Total de estudantes considerados na turma (excluindo trancados)",
    )
    class_average_grade: Decimal | None = Field(
        default=None,
        description="Média geral de notas da turma (0.00 a 10.00)",
    )
    average_attendance_rate: Decimal = Field(
        description="Taxa média de presença da turma (0.00 a 100.00%)",
    )
    on_time_tasks_percentage: Decimal = Field(
        description="Percentual de entregas práticas realizadas dentro do prazo na turma",
    )
    completed_tasks_percentage: Decimal = Field(
        description="Percentual total de entregas práticas concluídas/avaliadas na turma",
    )
    at_risk_students_count: int = Field(
        ge=0,
        description="Quantidade de estudantes em atenção pedagógica/risco (MODERATE, HIGH ou CRITICAL)",
    )
    critical_students_count: int = Field(
        ge=0,
        description="Quantidade de estudantes em risco crítico (CRITICAL)",
    )
    active_alerts_count: int = Field(
        ge=0,
        description="Total de alertas acadêmicos ativos na turma",
    )

    @field_validator(
        "average_attendance_rate",
        "on_time_tasks_percentage",
        "completed_tasks_percentage",
        mode="after",
    )
    @classmethod
    def quantize_required_rates(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("class_average_grade", mode="after")
    @classmethod
    def quantize_optional_class_avg(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class ModuleDashboardPerformanceSchema(BaseResponseSchema):
    """Indicadores de evolução, notas, presença e entregas por módulo prático da turma (FE-031 / FE-033)."""

    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    subject_code: str = Field(description="Código identificador da disciplina")
    subject_name: str = Field(description="Nome oficial da disciplina")
    module_title: str = Field(
        description="Título do módulo prático (ex: Desenho Técnico, Metrologia, Tornearia)",
    )
    order_index: int = Field(ge=1, description="Ordem didática do módulo na disciplina")
    practical_hours: int = Field(ge=0, description="Carga horária prática prevista do módulo")
    passing_score: Decimal = Field(description="Nota de corte do módulo prático")
    average_grade: Decimal | None = Field(
        default=None,
        description="Média das notas dos estudantes avaliados neste módulo",
    )
    median_grade: Decimal | None = Field(
        default=None,
        description="Mediana das notas dos estudantes avaliados neste módulo",
    )
    average_attendance_rate: Decimal = Field(
        description="Taxa média de presença da turma neste módulo via vw_module_attendance_risk",
    )
    completion_rate: Decimal = Field(
        description="Taxa percentual de conclusão das atividades práticas do módulo",
    )
    on_time_completion_rate: Decimal = Field(
        description="Taxa percentual de entregas práticas concluídas no prazo no módulo",
    )
    total_tasks_assigned: int = Field(
        ge=0,
        description="Total de submissões esperadas no módulo",
    )
    completed_tasks_count: int = Field(
        ge=0,
        description="Total de submissões concluídas/avaliadas no módulo",
    )
    late_tasks_count: int = Field(
        ge=0,
        description="Total de submissões em atraso no módulo",
    )
    average_skill_level: Decimal | None = Field(
        default=None,
        description="Nível médio de domínio técnico verificado nas competências do módulo (1.00 a 5.00)",
    )
    at_risk_students_count: int = Field(
        ge=0,
        description="Quantidade de estudantes abaixo da nota de corte ou com frequência crítica (<78%) no módulo",
    )

    @field_validator(
        "passing_score",
        "average_attendance_rate",
        "completion_rate",
        "on_time_completion_rate",
        mode="after",
    )
    @classmethod
    def quantize_required_metrics(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("average_grade", "median_grade", "average_skill_level", mode="after")
    @classmethod
    def quantize_optional_metrics(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class TeacherClassDashboardResponseSchema(BaseResponseSchema):
    """Resposta consolidada do Dashboard Híbrido do Professor para uma turma (GET /api/v1/dashboard/teacher/classes/{id})."""

    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Dados resumidos da turma acadêmica",
    )
    course_code: str = Field(description="Código do curso técnico da turma")
    course_name: str = Field(description="Nome oficial do curso técnico da turma")
    generated_at: datetime = Field(description="Data/hora UTC de geração dos indicadores")
    kpis: TeacherDashboardKpisSchema = Field(
        description="KPIs globais da turma (média, assiduidade, entregas no prazo e alunos em risco)",
    )
    modules_distribution: list[ModuleDashboardPerformanceSchema] = Field(
        default_factory=list,
        description="Distribuição e evolução de desempenho por módulo prático",
    )
    students: list[DashboardStudent360SummaryItemSchema] = Field(
        default_factory=list,
        description="Lista de estudantes da turma com indicadores pré-agregados via vw_student_360_performance",
    )


class StudentCompetencyRadarItemSchema(BaseResponseSchema):
    """Indicador de proficiência por competência técnica para o Gráfico Radar da Ficha 360° (FE-034 / FE-038)."""

    competency_id: UUID = Field(description="Identificador UUID da competência técnica")
    code: str = Field(description="Código institucional da competência")
    title: str = Field(description="Título da competência técnica")
    category: CompetencyCategory = Field(
        description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)",
    )
    required_level: int = Field(
        ge=1,
        le=5,
        description="Nível meta exigido no plano de ensino modular (1 a 5)",
    )
    verified_level: Decimal | None = Field(
        default=None,
        description="Nível médio verificado pelo docente em evidências práticas (1.00 a 5.00)",
    )
    evidences_count: int = Field(
        ge=0,
        description="Quantidade de evidências práticas registradas para esta competência",
    )
    is_proficient: bool = Field(
        description="Indica se verified_level atingiu ou superou required_level",
    )

    @field_validator("verified_level", mode="after")
    @classmethod
    def quantize_verified(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class AlertInterventionAuditItemSchema(BaseResponseSchema):
    """Registro auditável de intervenção pedagógica realizada sobre um alerta acadêmico (audit_logs - BE-039)."""

    audit_id: UUID = Field(description="Identificador UUID do log em audit_logs")
    action: str = Field(
        description="Ação registrada na auditoria (ACADEMIC_ALERT_ACKNOWLEDGED ou ACADEMIC_ALERT_RESOLVED)",
    )
    previous_status: AlertStatus | None = Field(
        default=None,
        description="Status do alerta antes da intervenção",
    )
    new_status: AlertStatus = Field(
        description="Novo status aplicado na intervenção (ACKNOWLEDGED ou RESOLVED)",
    )
    resolution_notes: str = Field(
        description="Notas descrevendo a ação pedagógica realizada",
    )
    actor_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do docente ou coordenador autor da intervenção",
    )
    actor_name: str | None = Field(
        default=None,
        description="Nome completo do responsável pela intervenção",
    )
    actor_role: UserRole | None = Field(
        default=None,
        description="Papel institucional do responsável pela intervenção",
    )
    ip_address: str | None = Field(
        default=None,
        description="Endereço IP de origem da operação registrada na auditoria",
    )
    recorded_at: datetime = Field(
        description="Timestamp UTC do registro da intervenção na trilha imutável",
    )


class StudentActiveAlertItemSchema(BaseResponseSchema):
    """Resumo de alerta acadêmico explicável ativo na Ficha 360° do Aluno."""

    id: UUID = Field(description="Identificador UUID do alerta em academic_alerts")
    class_id: UUID = Field(description="Identificador UUID da turma")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo relacionado (quando aplicável)",
    )
    risk_level: RiskLevel = Field(description="Nível de severidade do alerta")
    alert_category: AlertCategory = Field(description="Categoria do alerta acadêmico")
    explainable_reason: str = Field(
        description="Explicação transparente dos dados e da regra que originou o alerta",
    )
    metric_snapshot: dict[str, Any] | None = Field(
        default=None,
        description="Fotografia JSON das métricas no momento da geração do alerta",
    )
    status: AlertStatus = Field(description="Status atual do alerta")
    resolved_by: UUID | None = Field(
        default=None,
        description="Identificador UUID do docente ou coordenador que assumiu/encerrou o alerta",
    )
    resolved_by_name: str | None = Field(
        default=None,
        description="Nome completo do responsável pela última intervenção no alerta",
    )
    resolution_notes: str | None = Field(
        default=None,
        description="Notas da última intervenção pedagógica registrada no alerta",
    )
    created_at: datetime = Field(description="Data/hora de geração do alerta")


class StudentAlertHistoryItemSchema(StudentActiveAlertItemSchema):
    """Item completo do histórico de alertas e intervenções pedagógicas na Ficha 360° (BE-039)."""

    interventions: list[AlertInterventionAuditItemSchema] = Field(
        default_factory=list,
        description="Histórico auditável de intervenções pedagógicas realizadas no alerta",
    )


class Student360OverviewResponseSchema(BaseResponseSchema):
    """Ficha 360° multidisciplinar completa do estudante para docentes e coordenação (GET /api/v1/students/{id}/360)."""

    student_id: UUID = Field(description="Identificador UUID do estudante")
    student: DashboardStudentProfileSchema = Field(
        description="Dados cadastrais do estudante",
    )
    enrollment_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da matrícula ativa/selecionada",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da turma ativa/selecionada",
    )
    enrollment_status: EnrollmentStatus | None = Field(
        default=None,
        description="Status da matrícula selecionada",
    )
    academic_class: EnrollmentClassSummarySchema | None = Field(
        default=None,
        description="Resumo da turma acadêmica selecionada",
    )
    generated_at: datetime = Field(description="Data/hora UTC da consulta 360°")
    overview: DashboardStudent360SummaryItemSchema | None = Field(
        default=None,
        description="Indicadores globais consolidados a partir da view vw_student_360_performance",
    )
    subjects: list[StudentSubjectAverageSchema] = Field(
        default_factory=list,
        description="Desempenho multidisciplinar por disciplina e seus módulos práticos",
    )
    attendance_by_module: list[ModuleAttendanceRiskItemSchema] = Field(
        default_factory=list,
        description="Indicadores de frequência e margem de 75% por módulo via vw_module_attendance_risk",
    )
    competencies: list[StudentCompetencyRadarItemSchema] = Field(
        default_factory=list,
        description="Mapa de proficiência por competência técnica para gráfico radar",
    )
    practical_submissions: list[StudentPendingTaskItemSchema] = Field(
        default_factory=list,
        description="Histórico completo de entregas práticas e avaliações por rubrica",
    )
    active_alerts: list[StudentActiveAlertItemSchema] = Field(
        default_factory=list,
        description="Alertas acadêmicos ativos e explicáveis do estudante",
    )
    alerts_history: list[StudentAlertHistoryItemSchema] = Field(
        default_factory=list,
        description="Histórico completo de alertas e intervenções pedagógicas do estudante (ACTIVE, ACKNOWLEDGED, RESOLVED)",
    )


class StudentPortalAttendanceSummarySchema(BaseResponseSchema):
    """Resumo consolidado de frequência do estudante para o Portal de Autonomia (BE-034 / FE-035 / FE-037)."""

    planned_hours: int = Field(
        ge=0,
        description="Carga horária total prevista nas disciplinas/módulos da turma",
    )
    total_hours: int = Field(
        ge=0,
        description="Total de horas-aula ministradas até o momento",
    )
    attended_hours: int = Field(
        ge=0,
        description="Total de horas com presença registrada para o estudante",
    )
    absent_hours: int = Field(
        ge=0,
        description="Total de horas de faltas não justificadas",
    )
    justified_absent_hours: int = Field(
        ge=0,
        description="Total de horas de ausências justificadas (JUSTIFIED)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual consolidado de presença do estudante (0.00 a 100.00%)",
    )
    min_required_percentage: Decimal = Field(
        description="Percentual mínimo legal exigido para aprovação por frequência (75.00%)",
    )
    max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) sobre as aulas ministradas",
    )
    remaining_absent_hours_margin: Decimal = Field(
        description="Margem restante em horas sobre as aulas ministradas até o limite de 75%",
    )
    planned_max_allowed_absent_hours: Decimal = Field(
        description="Limite máximo de horas de falta (25%) sobre a carga horária prevista",
    )
    planned_remaining_absent_hours_margin: Decimal = Field(
        description="Saldo restante em horas que o estudante ainda pode faltar na carga prevista antes de 75%",
    )
    percentage_margin_to_limit: Decimal = Field(
        description="Margem percentual atual até o limite mínimo de 75.00%",
    )
    is_critical: bool = Field(
        description="Indica se a frequência consolidada está abaixo do limiar preventivo (< 78.00%)",
    )
    is_attendance_critical: bool = Field(
        description="Alias compatível com vw_module_attendance_risk para frequência < 78.00%",
    )
    risk_level: RiskLevel = Field(
        description="Nível de atenção preventiva de frequência (LOW, HIGH, CRITICAL)",
    )
    critical_modules_count: int = Field(
        ge=0,
        description="Quantidade de módulos práticos com frequência abaixo de 78%",
    )
    by_subject: list[SubjectConsolidatedAttendanceSchema] = Field(
        default_factory=list,
        description="Resumo de frequência agrupado por disciplina técnica e seus módulos",
    )
    by_module: list[ModuleAttendanceRiskItemSchema] = Field(
        default_factory=list,
        description="Indicadores de frequência e margem de 75% por módulo prático",
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
        return value.quantize(_DECIMAL_QUANTIZER)


class StudentModuleProgressItemSchema(BaseResponseSchema):
    """Progresso percentual e indicadores do estudante em cada módulo prático (BE-034 / FE-035)."""

    module_id: UUID = Field(description="Identificador UUID do módulo prático")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    subject_code: str = Field(description="Código identificador da disciplina")
    subject_name: str = Field(description="Nome oficial da disciplina")
    module_title: str = Field(description="Título do módulo prático")
    order_index: int = Field(ge=1, description="Ordem didática do módulo na disciplina")
    practical_hours: int = Field(
        ge=0,
        description="Carga horária prática prevista para o módulo",
    )
    module_weight: Decimal = Field(
        description="Peso ponderado do módulo na disciplina",
    )
    passing_score: Decimal = Field(
        description="Nota mínima de corte do módulo prático",
    )
    total_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas atribuídas ao estudante no módulo",
    )
    completed_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas concluídas/avaliadas no módulo",
    )
    pending_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas pendentes dentro do prazo no módulo",
    )
    late_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas em atraso no módulo",
    )
    submitted_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas entregues aguardando avaliação no módulo",
    )
    evaluated_tasks_count: int = Field(
        ge=0,
        description="Total de atividades práticas já avaliadas pelo docente no módulo",
    )
    progress_percentage: Decimal = Field(
        description="Progresso percentual de conclusão do estudante no módulo prático (0.00 a 100.00%)",
    )
    completion_percentage: Decimal = Field(
        description="Taxa percentual de atividades práticas concluídas no módulo (0.00 a 100.00%)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual de presença do estudante no módulo prático (0.00 a 100.00%)",
    )
    assessments_count: int = Field(
        ge=0,
        description="Quantidade de avaliações formativas com nota lançada no módulo",
    )
    assessments_average: Decimal | None = Field(
        default=None,
        description="Média ponderada das avaliações formativas do módulo",
    )
    practical_tasks_average: Decimal | None = Field(
        default=None,
        description="Média das atividades práticas avaliadas no módulo",
    )
    module_average: Decimal | None = Field(
        default=None,
        description="Média consolidada do módulo combinando avaliações e práticas",
    )
    is_below_passing_score: bool = Field(
        description="Indica se a média do módulo está abaixo da nota de corte",
    )
    is_completed: bool = Field(
        description="Indica se o módulo prático teve todas as atividades concluídas (100%)",
    )
    status: AcademicStandingStatus = Field(
        description="Situação acadêmica no módulo (APPROVED, IN_RECOVERY, AT_RISK)",
    )

    @field_validator(
        "module_weight",
        "passing_score",
        "progress_percentage",
        "completion_percentage",
        "attendance_percentage",
        mode="after",
    )
    @classmethod
    def quantize_required_decimals(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator(
        "assessments_average",
        "practical_tasks_average",
        "module_average",
        mode="after",
    )
    @classmethod
    def quantize_optional_decimals(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class StudentMilestoneTimelineItemSchema(BaseResponseSchema):
    """Marco acadêmico da linha do tempo de evolução do estudante (student_milestone_history - DB-039 / FE-039)."""

    id: UUID = Field(description="Identificador UUID do marco em student_milestone_history")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    enrollment_id: UUID = Field(description="Identificador UUID da matrícula")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo prático associado (quando aplicável)",
    )
    module_title: str | None = Field(
        default=None,
        description="Título do módulo prático associado (quando aplicável)",
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da disciplina associada ao módulo (quando aplicável)",
    )
    subject_code: str | None = Field(
        default=None,
        description="Código da disciplina associada ao módulo (quando aplicável)",
    )
    subject_name: str | None = Field(
        default=None,
        description="Nome da disciplina associada ao módulo (quando aplicável)",
    )
    milestone_type: MilestoneType = Field(
        description="Tipo do marco acadêmico (MODULE_COMPLETED, SKILL_LEVEL_UP, PERFECT_ATTENDANCE, RECOVERY_ACHIEVED)",
    )
    title: str = Field(description="Título descritivo e motivador do marco conquistado")
    description: str | None = Field(
        default=None,
        description="Descrição detalhada do marco acadêmico",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Metadados estruturados JSONB do marco conquistado",
    )
    achieved_at: datetime = Field(
        description="Data e hora UTC em que o marco foi conquistado",
    )


class StudentPortalDashboardResponseSchema(BaseResponseSchema):
    """Resposta privada consolidada do Portal do Aluno (GET /api/v1/dashboard/student/me - BE-034).

    Cumpre os requisitos de privacidade e autonomia do estudante (seção 4.2):
    extrai exclusivamente os dados de current_user.id e jamais inclui observações
    pedagógicas restritas de professores.
    """

    student_id: UUID = Field(description="Identificador UUID do próprio estudante autenticado")
    student: DashboardStudentProfileSchema = Field(
        description="Dados cadastrais do estudante autenticado",
    )
    enrollment_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da matrícula ativa/selecionada do estudante",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Identificador UUID da turma ativa/selecionada do estudante",
    )
    enrollment_status: EnrollmentStatus | None = Field(
        default=None,
        description="Status da matrícula ativa/selecionada",
    )
    academic_class: EnrollmentClassSummarySchema | None = Field(
        default=None,
        description="Resumo da turma acadêmica do estudante",
    )
    course_code: str | None = Field(
        default=None,
        description="Código do curso técnico SENAI",
    )
    course_name: str | None = Field(
        default=None,
        description="Nome oficial do curso técnico SENAI",
    )
    generated_at: datetime = Field(
        description="Data e hora UTC da consulta ao Portal do Aluno",
    )
    overall_average: Decimal | None = Field(
        default=None,
        description="Média geral ponderada do estudante na turma (0.00 a 10.00)",
    )
    overall_progress_percentage: Decimal = Field(
        default=Decimal("0.00"),
        description="Progresso percentual global do estudante nos módulos práticos (0.00 a 100.00%)",
    )
    attendance_percentage: Decimal = Field(
        default=Decimal("100.00"),
        description="Percentual consolidado de presença do estudante (0.00 a 100.00%)",
    )
    standing_status: AcademicStandingStatus = Field(
        default=AcademicStandingStatus.APPROVED,
        description="Situação acadêmica consolidada (APPROVED, IN_RECOVERY, AT_RISK)",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Nível de atenção acadêmica (LOW, MODERATE, HIGH, CRITICAL)",
    )
    overview: DashboardStudent360SummaryItemSchema | None = Field(
        default=None,
        description="Indicadores globais consolidados via vw_student_360_performance (DB-036)",
    )
    attendance_summary: StudentPortalAttendanceSummarySchema = Field(
        description="Resumo de frequência global, por disciplina e por módulo prático",
    )
    subjects: list[StudentSubjectAverageSchema] = Field(
        default_factory=list,
        description="Médias ponderadas por disciplina técnica e seus módulos práticos (FE-037)",
    )
    attendance_by_module: list[ModuleAttendanceRiskItemSchema] = Field(
        default_factory=list,
        description="Frequência detalhada e margem de 75% por módulo prático (FE-037)",
    )
    modules_progress: list[StudentModuleProgressItemSchema] = Field(
        default_factory=list,
        description="Progresso percentual e situação em cada módulo prático (FE-035)",
    )
    competencies: list[StudentCompetencyRadarItemSchema] = Field(
        default_factory=list,
        description="Evolução de nível por competência técnica para o Gráfico Radar (FE-038)",
    )
    competencies_radar: list[StudentCompetencyRadarItemSchema] = Field(
        default_factory=list,
        description="Alias compatível com FE-038 para evolução de nível por competência técnica",
    )
    task_counts: StudentTaskCountsSummarySchema = Field(
        description="Contadores de atividades práticas pendentes, atrasadas, entregues e avaliadas",
    )
    activity_counters: StudentTaskCountsSummarySchema = Field(
        description="Alias semântico para contadores de atividades práticas do estudante",
    )
    upcoming_tasks: list[StudentPendingTaskItemSchema] = Field(
        default_factory=list,
        description="Atividades práticas pendentes ou em atraso para alerta amigável no portal (FE-035 / FE-036)",
    )
    practical_submissions: list[StudentPendingTaskItemSchema] = Field(
        default_factory=list,
        description="Lista completa de atividades práticas do estudante com feedback das rubricas",
    )
    timeline: list[StudentMilestoneTimelineItemSchema] = Field(
        default_factory=list,
        description="Linha do tempo cronológica de marcos e conquistas acadêmicas (student_milestone_history - FE-039)",
    )
    milestone_history: list[StudentMilestoneTimelineItemSchema] = Field(
        default_factory=list,
        description="Alias direto da tabela student_milestone_history (DB-039) para a linha do tempo",
    )

    @field_validator(
        "overall_progress_percentage",
        "attendance_percentage",
        mode="after",
    )
    @classmethod
    def quantize_required_percentages(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("overall_average", mode="after")
    @classmethod
    def quantize_optional_overall_average(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


__all__ = [
    "AlertInterventionAuditItemSchema",
    "DashboardStudent360SummaryItemSchema",
    "DashboardStudentProfileSchema",
    "ModuleDashboardPerformanceSchema",
    "Student360OverviewResponseSchema",
    "Student360ParamsDep",
    "Student360QueryParams",
    "StudentActiveAlertItemSchema",
    "StudentAlertHistoryItemSchema",
    "StudentCompetencyRadarItemSchema",
    "StudentMilestoneTimelineItemSchema",
    "StudentModuleProgressItemSchema",
    "StudentPortalAttendanceSummarySchema",
    "StudentPortalDashboardParamsDep",
    "StudentPortalDashboardQueryParams",
    "StudentPortalDashboardResponseSchema",
    "TeacherClassDashboardParamsDep",
    "TeacherClassDashboardQueryParams",
    "TeacherClassDashboardResponseSchema",
    "TeacherDashboardKpisSchema",
]
