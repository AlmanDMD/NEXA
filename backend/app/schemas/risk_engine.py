"""Schemas Pydantic v2 para o Motor Explicável de Identificação Precoce de Risco Acadêmico (BE-032)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.dashboard import (
    AlertInterventionAuditItemSchema,
    DashboardStudentProfileSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import AlertCategory, AlertStatus, RiskLevel, UserRole
from app.schemas.validators import sanitize_optional_text, sanitize_text

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")

ETHICAL_PEDAGOGICAL_DISCLAIMER: str = (
    "Indicador transparente de atenção e apoio pedagógico preventivo; "
    "nunca constitui reprovação ou rótulo automático ao estudante."
)


def validate_alert_resolution_status_pt(value: Any) -> AlertStatus:
    """Valida que o status informado para resolução do alerta é 'ACKNOWLEDGED' ou 'RESOLVED'."""
    if isinstance(value, AlertStatus):
        resolved = value
    elif isinstance(value, str):
        normalized = value.strip().upper()
        if normalized == "ACKNOWLEDGE":
            resolved = AlertStatus.ACKNOWLEDGED
        elif normalized == "RESOLVE":
            resolved = AlertStatus.RESOLVED
        else:
            try:
                resolved = AlertStatus(normalized)
            except ValueError as exc:
                raise PydanticCustomError(
                    "invalid_alert_resolution_status",
                    "O status de resolução do alerta deve ser 'ACKNOWLEDGED' ou 'RESOLVED'.",
                ) from exc
    else:
        raise PydanticCustomError(
            "invalid_alert_resolution_status",
            "O status de resolução do alerta deve ser 'ACKNOWLEDGED' ou 'RESOLVED'.",
        )

    if resolved not in (AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED):
        raise PydanticCustomError(
            "invalid_alert_resolution_status",
            "O status de resolução do alerta deve ser 'ACKNOWLEDGED' ou 'RESOLVED'.",
        )
    return resolved


def validate_alert_resolution_notes_pt(value: Any) -> str:
    """Sanitiza e valida as notas obrigatórias de intervenção pedagógica (mínimo 10 caracteres)."""
    if not isinstance(value, str):
        raise PydanticCustomError(
            "alert_resolution_notes_invalid",
            "As notas de resolução (resolution_notes) devem ser um texto válido.",
        )
    cleaned = sanitize_text(value, collapse_spaces=False)
    if len(cleaned) < 10:
        raise PydanticCustomError(
            "alert_resolution_notes_too_short",
            "As notas de resolução (resolution_notes) são obrigatórias e devem ter pelo menos 10 caracteres.",
        )
    if len(cleaned) > 2000:
        raise PydanticCustomError(
            "alert_resolution_notes_too_long",
            "As notas de resolução (resolution_notes) devem ter no máximo 2000 caracteres.",
        )
    return cleaned


class RiskRuleEvaluationItemSchema(BaseResponseSchema):
    """Resultado determinístico e auditável de uma regra individual disparada pelo motor de risco."""

    rule_code: str = Field(
        description="Código determinístico da regra acionada (ex: ATTENDANCE_CRITICAL_BELOW_75)",
    )
    alert_category: AlertCategory = Field(
        description="Categoria do indicador de atenção (ATTENDANCE, PENDING_TASKS, GRADE_DROP, SELF_EVAL_GAP)",
    )
    risk_level: RiskLevel = Field(
        description="Grau de atenção pedagógica atribuído pela regra (MODERATE, HIGH, CRITICAL)",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo específico associado ao alerta",
    )
    explainable_reason: str = Field(
        description="Explicação textual clara e legível detalhando os dados e o limiar atingido",
    )
    recommended_action: str = Field(
        description="Sugestão de ação pedagógica preventiva para docente ou coordenação",
    )
    metric_snapshot: dict[str, Any] = Field(
        description="Fotografia auditável em JSON com as métricas exatas consideradas na avaliação",
    )


class AcademicAlertResponseSchema(BaseResponseSchema):
    """Representação serializada de um alerta persistido em academic_alerts (DB-034 / BE-032)."""

    id: UUID = Field(description="Identificador UUID do alerta acadêmico")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    enrollment_id: UUID = Field(description="Identificador UUID da matrícula na turma")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático",
    )
    risk_level: RiskLevel = Field(
        description="Nível de atenção pedagógica (LOW, MODERATE, HIGH, CRITICAL)",
    )
    alert_category: AlertCategory = Field(
        description="Categoria do alerta (ATTENDANCE, GRADE_DROP, PENDING_TASKS, SELF_EVAL_GAP)",
    )
    explainable_reason: str = Field(
        description="Justificativa transparente e explicável da regra disparada",
    )
    metric_snapshot: dict[str, Any] | None = Field(
        default=None,
        description="Snapshot auditável em JSON das métricas acadêmicas avaliadas",
    )
    status: AlertStatus = Field(
        description="Status do ciclo do alerta (ACTIVE, ACKNOWLEDGED, RESOLVED)",
    )
    resolved_by: UUID | None = Field(
        default=None,
        description="Identificador UUID do docente ou coordenador responsável pela intervenção",
    )
    resolution_notes: str | None = Field(
        default=None,
        description="Descrição da intervenção pedagógica registrada",
    )
    ethical_disclaimer: str = Field(
        default=ETHICAL_PEDAGOGICAL_DISCLAIMER,
        description="Nota ética obrigatória reforçando caráter preventivo e não punitivo",
    )
    created_at: datetime = Field(description="Data/hora UTC de criação do alerta")


class StudentRiskEvaluationResultSchema(BaseResponseSchema):
    """Resultado consolidado da análise do motor de risco para um estudante na turma."""

    enrollment_id: UUID = Field(description="Identificador UUID da matrícula avaliada")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    class_id: UUID = Field(description="Identificador UUID da turma")
    overall_risk_level: RiskLevel = Field(
        description="Grau consolidado de risco/atenção (LOW, MODERATE, HIGH, CRITICAL)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual atual de presença considerado na análise",
    )
    overall_average: Decimal | None = Field(
        default=None,
        description="Média parcial/final ponderada considerada na análise",
    )
    passing_score: Decimal = Field(
        description="Nota de corte de referência considerada na análise",
    )
    late_tasks_count: int = Field(
        ge=0,
        description="Quantidade de tarefas práticas em atraso (LATE) consideradas",
    )
    created_alerts_count: int = Field(
        ge=0,
        description="Quantidade de novos alertas abertos nesta execução",
    )
    updated_alerts_count: int = Field(
        ge=0,
        description="Quantidade de alertas existentes atualizados sem duplicação",
    )
    auto_resolved_alerts_count: int = Field(
        ge=0,
        description="Quantidade de alertas encerrados automaticamente por recuperação das métricas",
    )
    ethical_disclaimer: str = Field(
        default=ETHICAL_PEDAGOGICAL_DISCLAIMER,
        description="Diretriz ética de apoio pedagógico preventivo",
    )
    active_alerts: list[AcademicAlertResponseSchema] = Field(
        default_factory=list,
        description="Alertas ativos resultantes após deduplicação e atualização",
    )

    @field_validator("attendance_percentage", "passing_score", mode="after")
    @classmethod
    def quantize_required_decimals(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("overall_average", mode="after")
    @classmethod
    def quantize_optional_average(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class ClassRiskEvaluationResponseSchema(BaseResponseSchema):
    """Resumo consolidado da execução do Motor de Risco para toda uma turma (BE-032)."""

    class_id: UUID = Field(description="Identificador UUID da turma avaliada")
    evaluated_at: datetime = Field(description="Timestamp UTC da avaliação de risco")
    total_students_evaluated: int = Field(
        ge=0,
        description="Total de estudantes ativos avaliados na turma",
    )
    at_risk_students_count: int = Field(
        ge=0,
        description="Quantidade de estudantes classificados em MODERATE, HIGH ou CRITICAL",
    )
    low_risk_count: int = Field(ge=0, description="Estudantes em situação regular (LOW)")
    moderate_risk_count: int = Field(
        ge=0,
        description="Estudantes em atenção moderada (MODERATE)",
    )
    high_risk_count: int = Field(ge=0, description="Estudantes em atenção alta (HIGH)")
    critical_risk_count: int = Field(
        ge=0,
        description="Estudantes em atenção crítica (CRITICAL)",
    )
    created_alerts_count: int = Field(
        ge=0,
        description="Total de novos alertas criados em academic_alerts",
    )
    updated_alerts_count: int = Field(
        ge=0,
        description="Total de alertas já abertos atualizados sem duplicidade",
    )
    auto_resolved_alerts_count: int = Field(
        ge=0,
        description="Total de alertas resolvidos automaticamente por melhoria dos indicadores",
    )
    ethical_disclaimer: str = Field(
        default=ETHICAL_PEDAGOGICAL_DISCLAIMER,
        description="Nota ética institucional (regras transparentes e não rotuladoras)",
    )
    results: list[StudentRiskEvaluationResultSchema] = Field(
        default_factory=list,
        description="Detalhamento individual por estudante avaliado",
    )


class AtRiskStudentsQueryParams(StrictRequestSchema):
    """Parâmetros de paginação e filtros para GET /api/v1/dashboard/teacher/at-risk (BE-033)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de alertas por página (1 a 100)",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do módulo prático",
    )
    risk_level: RiskLevel | None = Field(
        default=None,
        description="Filtro opcional pelo grau de severidade (CRITICAL, HIGH, MODERATE, LOW)",
    )
    alert_category: AlertCategory | None = Field(
        default=None,
        description="Filtro opcional pela categoria do alerta (ATTENDANCE, GRADE_DROP, PENDING_TASKS, SELF_EVAL_GAP)",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Busca textual opcional por nome, matrícula ou e-mail do estudante",
    )

    @field_validator("search", mode="before")
    @classmethod
    def sanitize_search(cls, value: Any) -> str | None:
        cleaned = sanitize_optional_text(value, collapse_spaces=True)
        if cleaned is not None and len(cleaned) > 100:
            raise PydanticCustomError(
                "search_too_long",
                "O termo de busca deve ter no máximo 100 caracteres.",
            )
        return cleaned


type AtRiskStudentsParamsDep = Annotated[AtRiskStudentsQueryParams, Query()]


class AtRiskAlertModuleSummarySchema(BaseResponseSchema):
    """Resumo do módulo prático associado a um alerta acadêmico."""

    id: UUID = Field(description="Identificador UUID do módulo prático")
    title: str = Field(description="Título do módulo prático (ex: Metrologia, Tornearia)")
    order_index: int = Field(ge=1, description="Ordem didática do módulo")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    subject_code: str = Field(description="Código identificador da disciplina")
    subject_name: str = Field(description="Nome oficial da disciplina")


class AtRiskStudentCurrentMetricsSchema(BaseResponseSchema):
    """Métricas acadêmicas atuais do estudante consolidadas via vw_student_360_performance."""

    overall_average: Decimal | None = Field(
        default=None,
        description="Média parcial/final atual do estudante (0.00 a 10.00)",
    )
    attendance_percentage: Decimal = Field(
        description="Percentual atual de presença do estudante (0.00 a 100.00%)",
    )
    pending_tasks_count: int = Field(
        ge=0,
        description="Quantidade atual de tarefas práticas pendentes dentro do prazo",
    )
    late_tasks_count: int = Field(
        ge=0,
        description="Quantidade atual de tarefas práticas em atraso (LATE)",
    )
    completed_tasks_count: int = Field(
        ge=0,
        description="Quantidade atual de tarefas práticas concluídas/avaliadas",
    )
    active_alerts_count: int = Field(
        ge=0,
        description="Total de alertas ativos abertos para esta matrícula",
    )

    @field_validator("attendance_percentage", mode="after")
    @classmethod
    def quantize_attendance(cls, value: Decimal) -> Decimal:
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("overall_average", mode="after")
    @classmethod
    def quantize_optional_avg(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class AtRiskStudentAlertItemSchema(BaseResponseSchema):
    """Item detalhado de aluno em situação de risco com justificativa explicável e ação sugerida (BE-033 / FE-032)."""

    id: UUID = Field(description="Identificador UUID do alerta em academic_alerts")
    alert_id: UUID = Field(description="Alias explícito do identificador UUID do alerta")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    enrollment_id: UUID = Field(description="Identificador UUID da matrícula na turma")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático relacionado",
    )
    risk_level: RiskLevel = Field(
        description="Nível de severidade do alerta (CRITICAL, HIGH, MODERATE, LOW)",
    )
    alert_category: AlertCategory = Field(
        description="Categoria da regra que gerou o alerta (ATTENDANCE, GRADE_DROP, PENDING_TASKS, SELF_EVAL_GAP)",
    )
    status: AlertStatus = Field(
        description="Status atual do alerta (ACTIVE, ACKNOWLEDGED, RESOLVED)",
    )
    resolved_by: UUID | None = Field(
        default=None,
        description="Identificador UUID do docente ou coordenador responsável pela intervenção",
    )
    resolution_notes: str | None = Field(
        default=None,
        description="Descrição da intervenção pedagógica registrada",
    )
    explainable_reason: str = Field(
        description="Justificativa transparente detalhando a regra e as evidências numéricas",
    )
    recommended_action: str = Field(
        description="Sugestão contextual de intervenção pedagógica para o professor",
    )
    suggested_pedagogical_action: str = Field(
        description="Sugestão de ação pedagógica rápida (ex: 'Agendar mentoria prática no módulo de Metrologia')",
    )
    ethical_disclaimer: str = Field(
        default=ETHICAL_PEDAGOGICAL_DISCLAIMER,
        description="Nota ética obrigatória: indicador de apoio pedagógico, não decisão automática",
    )
    metric_snapshot: dict[str, Any] | None = Field(
        default=None,
        description="Snapshot auditável em JSON das métricas do momento da geração do alerta",
    )
    current_metrics: AtRiskStudentCurrentMetricsSchema = Field(
        description="Métricas acadêmicas atuais do estudante em tempo real",
    )
    student: DashboardStudentProfileSchema = Field(
        description="Dados cadastrais do estudante",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Dados resumidos da turma acadêmica",
    )
    module: AtRiskAlertModuleSummarySchema | None = Field(
        default=None,
        description="Dados resumidos do módulo prático quando o alerta é específico de um módulo",
    )
    created_at: datetime = Field(description="Data/hora UTC de criação do alerta")


class AtRiskStudentsPaginatedResponseSchema(BaseResponseSchema):
    """Lista paginada de alertas ativos ordenada por severidade (CRITICAL -> HIGH -> MODERATE -> LOW) (BE-033)."""

    data: list[AtRiskStudentAlertItemSchema] = Field(
        default_factory=list,
        description="Lista de alertas ativos ordenados por prioridade de severidade",
    )
    total: int = Field(ge=0, description="Total de alertas ativos encontrados para os filtros")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite máximo de itens por página")
    critical_count: int = Field(
        default=0,
        ge=0,
        description="Total de alertas ativos com severidade CRITICAL no escopo filtrado",
    )
    high_count: int = Field(
        default=0,
        ge=0,
        description="Total de alertas ativos com severidade HIGH no escopo filtrado",
    )
    moderate_count: int = Field(
        default=0,
        ge=0,
        description="Total de alertas ativos com severidade MODERATE no escopo filtrado",
    )
    low_count: int = Field(
        default=0,
        ge=0,
        description="Total de alertas ativos com severidade LOW no escopo filtrado",
    )
    ethical_disclaimer: str = Field(
        default=ETHICAL_PEDAGOGICAL_DISCLAIMER,
        description="Diretriz ética institucional do motor explicável",
    )


class AcademicAlertResolveRequestSchema(StrictRequestSchema):
    """Payload de entrada para assumir acompanhamento (ACKNOWLEDGED) ou encerrar (RESOLVED) um alerta (BE-039)."""

    status: Annotated[
        AlertStatus,
        BeforeValidator(validate_alert_resolution_status_pt),
        Field(description="Novo status do alerta ('ACKNOWLEDGED' ou 'RESOLVED')"),
    ]
    resolution_notes: Annotated[
        str,
        BeforeValidator(validate_alert_resolution_notes_pt),
        Field(
            description="Descrição obrigatória da ação/intervenção pedagógica tomada (mínimo 10 caracteres)",
            examples=[
                "Realizada mentoria individual em bancada e plano de reposição de faltas com o estudante."
            ],
        ),
    ]


class AlertResolverSummarySchema(BaseResponseSchema):
    """Resumo cadastral do docente ou coordenador responsável pela intervenção no alerta."""

    id: UUID = Field(description="Identificador UUID do usuário responsável pela intervenção")
    email: str = Field(description="E-mail institucional do responsável")
    role: UserRole = Field(description="Papel institucional do responsável")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do responsável pela intervenção",
    )


class AcademicAlertResolutionResponseSchema(AcademicAlertResponseSchema):
    """Resposta da atualização/resolução de alerta acadêmico com trilha de auditoria e histórico (BE-039)."""

    alert_id: UUID = Field(description="Alias explícito do identificador UUID do alerta")
    previous_status: AlertStatus = Field(
        description="Status anterior do alerta antes da intervenção registrada",
    )
    resolved_by: UUID = Field(
        description="Identificador UUID do professor/coordenador que assumiu ou encerrou o alerta",
    )
    resolution_notes: str = Field(
        description="Descrição registrada da ação pedagógica tomada",
    )
    resolver: AlertResolverSummarySchema | None = Field(
        default=None,
        description="Dados cadastrais do responsável pela intervenção",
    )
    audit_log_id: UUID = Field(
        description="Identificador UUID do registro gerado em audit_logs",
    )
    updated_at: datetime = Field(
        description="Data/hora UTC da atualização do alerta e gravação na auditoria",
    )
    intervention_history: list[AlertInterventionAuditItemSchema] = Field(
        default_factory=list,
        description="Histórico cronológico completo de intervenções registradas em audit_logs para este alerta",
    )


__all__ = [
    "AcademicAlertResolutionResponseSchema",
    "AcademicAlertResolveRequestSchema",
    "AcademicAlertResponseSchema",
    "AlertInterventionAuditItemSchema",
    "AlertResolverSummarySchema",
    "AtRiskAlertModuleSummarySchema",
    "AtRiskStudentAlertItemSchema",
    "AtRiskStudentCurrentMetricsSchema",
    "AtRiskStudentsPaginatedResponseSchema",
    "AtRiskStudentsParamsDep",
    "AtRiskStudentsQueryParams",
    "ClassRiskEvaluationResponseSchema",
    "ETHICAL_PEDAGOGICAL_DISCLAIMER",
    "RiskRuleEvaluationItemSchema",
    "StudentRiskEvaluationResultSchema",
    "validate_alert_resolution_notes_pt",
    "validate_alert_resolution_status_pt",
]
