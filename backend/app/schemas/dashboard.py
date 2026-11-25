"""Schemas Pydantic v2 para Dashboard Híbrido do Professor e Visão 360° do Aluno (BE-031)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import Field, field_validator

from app.schemas.academic_assessment import StudentSubjectAverageSchema
from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import ModuleAttendanceRiskItemSchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import (
    AcademicStandingStatus,
    AlertCategory,
    AlertStatus,
    CompetencyCategory,
    EnrollmentStatus,
    RiskLevel,
)
from app.schemas.practical_task import StudentPendingTaskItemSchema

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
    created_at: datetime = Field(description="Data/hora de geração do alerta")


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


__all__ = [
    "DashboardStudent360SummaryItemSchema",
    "DashboardStudentProfileSchema",
    "ModuleDashboardPerformanceSchema",
    "Student360OverviewResponseSchema",
    "Student360ParamsDep",
    "Student360QueryParams",
    "StudentActiveAlertItemSchema",
    "StudentCompetencyRadarItemSchema",
    "TeacherClassDashboardParamsDep",
    "TeacherClassDashboardQueryParams",
    "TeacherClassDashboardResponseSchema",
    "TeacherDashboardKpisSchema",
]
