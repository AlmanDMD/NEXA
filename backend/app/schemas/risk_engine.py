"""Schemas Pydantic v2 para o Motor Explicável de Identificação Precoce de Risco Acadêmico (BE-032)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseResponseSchema
from app.schemas.enums import AlertCategory, AlertStatus, RiskLevel

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")

ETHICAL_PEDAGOGICAL_DISCLAIMER: str = (
    "Indicador transparente de atenção e apoio pedagógico preventivo; "
    "nunca constitui reprovação ou rótulo automático ao estudante."
)


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


__all__ = [
    "AcademicAlertResponseSchema",
    "ClassRiskEvaluationResponseSchema",
    "ETHICAL_PEDAGOGICAL_DISCLAIMER",
    "RiskRuleEvaluationItemSchema",
    "StudentRiskEvaluationResultSchema",
]
