"""Motor determinístico, transparente e explicável para Identificação Precoce de Risco Acadêmico (BE-032)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import logger
from app.models.academic_alert import AcademicAlert
from app.models.base import _utc_now
from app.models.user import User
from app.repositories.risk_engine_repository import (
    RiskEngineRepository,
    RiskEngineRepositoryDep,
)
from app.schemas.enums import AlertCategory, RiskLevel, UserRole
from app.schemas.risk_engine import (
    AcademicAlertResponseSchema,
    ClassRiskEvaluationResponseSchema,
    ETHICAL_PEDAGOGICAL_DISCLAIMER,
    RiskRuleEvaluationItemSchema,
    StudentRiskEvaluationResultSchema,
)

RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)

ATTENDANCE_CRITICAL_LIMIT: Final[Decimal] = Decimal("75.00")
ATTENDANCE_PREVENTIVE_LIMIT: Final[Decimal] = Decimal("78.00")
LATE_TASKS_MODERATE_THRESHOLD: Final[int] = 2
LATE_TASKS_HIGH_THRESHOLD: Final[int] = 3
DEFAULT_PASSING_SCORE: Final[Decimal] = Decimal("6.00")
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")

_RISK_SEVERITY_RANK: Final[dict[RiskLevel, int]] = {
    RiskLevel.LOW: 1,
    RiskLevel.MODERATE: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

_MANAGED_RULE_CATEGORIES: Final[frozenset[AlertCategory]] = frozenset(
    {
        AlertCategory.ATTENDANCE,
        AlertCategory.PENDING_TASKS,
        AlertCategory.GRADE_DROP,
    }
)


def _q2(value: Decimal) -> Decimal:
    """Padroniza valor Decimal com duas casas decimais usando ROUND_HALF_UP."""
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _to_dec_or_none(raw: Any) -> Decimal | None:
    """Converte valor arbitrário vindo de SQL view em Decimal(0.01) ou None."""
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return _q2(raw)
    return _q2(Decimal(str(raw)))


@dataclass(frozen=True, slots=True)
class StudentRiskMetricsInput:
    """Conjunto auditável de métricas de entrada para avaliação pura do Motor de Regras (BE-032)."""

    attendance_percentage: Decimal
    total_lesson_hours: int = 0
    attended_hours: int = 0
    absent_hours: int = 0
    late_tasks_count: int = 0
    pending_tasks_count: int = 0
    completed_tasks_count: int = 0
    total_tasks_count: int = 0
    overall_average: Decimal | None = None
    passing_score: Decimal = DEFAULT_PASSING_SCORE
    module_id: UUID | None = None


def evaluate_student_risk_rules(
    metrics: StudentRiskMetricsInput,
    *,
    evaluated_at: datetime | None = None,
) -> tuple[RiskLevel, list[RiskRuleEvaluationItemSchema]]:
    """Executa regras determinísticas e explicáveis sobre frequência, tarefas práticas e médias (zero caixa-preta).

    Regras auditáveis (BE-032):
    1. Presença < 75.00% -> CRITICAL; Presença entre 75.00% e 77.99% (< 78.00%) -> HIGH.
    2. >= 2 tarefas práticas atrasadas (LATE): 2 tarefas -> MODERATE; >= 3 tarefas -> HIGH.
    3. Média parcial/final abaixo de passing_score -> HIGH.
    4. Caso nenhuma regra seja acionada -> LOW (nenhum alerta aberto).
    """
    ref_time = evaluated_at or _utc_now()
    att_pct = _q2(Decimal(metrics.attendance_percentage))
    passing = _q2(Decimal(metrics.passing_score))
    avg_grade = (
        _q2(Decimal(metrics.overall_average))
        if metrics.overall_average is not None
        else None
    )

    base_snapshot: dict[str, Any] = {
        "attendance_percentage": str(att_pct),
        "total_lesson_hours": int(metrics.total_lesson_hours),
        "attended_hours": int(metrics.attended_hours),
        "absent_hours": int(metrics.absent_hours),
        "late_tasks_count": int(metrics.late_tasks_count),
        "pending_tasks_count": int(metrics.pending_tasks_count),
        "completed_tasks_count": int(metrics.completed_tasks_count),
        "total_tasks_count": int(metrics.total_tasks_count),
        "overall_average": str(avg_grade) if avg_grade is not None else None,
        "passing_score": str(passing),
        "ethical_disclaimer": ETHICAL_PEDAGOGICAL_DISCLAIMER,
        "evaluated_at": ref_time.isoformat(),
    }

    triggered_rules: list[RiskRuleEvaluationItemSchema] = []

    # Regra 1: Assiduidade (< 75% CRITICAL; 75% <= presença < 78% HIGH)
    if att_pct < ATTENDANCE_CRITICAL_LIMIT:
        rule_code = "ATTENDANCE_CRITICAL_BELOW_75"
        reason = (
            "Indicador de atenção pedagógica (não constitui reprovação automática): "
            f"frequência acumulada em {att_pct}% (abaixo do limiar mínimo legal de "
            f"{ATTENDANCE_CRITICAL_LIMIT}%, com {metrics.absent_hours}h de ausência em "
            f"{metrics.total_lesson_hours}h ministradas)."
        )
        action = (
            "Convocar estudante para acolhimento pedagógico imediato e verificar possíveis "
            "justificativas ou dificuldades de deslocamento/permanência."
        )
        triggered_rules.append(
            RiskRuleEvaluationItemSchema(
                rule_code=rule_code,
                alert_category=AlertCategory.ATTENDANCE,
                risk_level=RiskLevel.CRITICAL,
                module_id=metrics.module_id,
                explainable_reason=reason,
                recommended_action=action,
                metric_snapshot={
                    **base_snapshot,
                    "rule_code": rule_code,
                    "threshold": str(ATTENDANCE_CRITICAL_LIMIT),
                    "recommended_action": action,
                },
            )
        )
    elif att_pct < ATTENDANCE_PREVENTIVE_LIMIT:
        rule_code = "ATTENDANCE_PREVENTIVE_75_TO_78"
        reason = (
            "Indicador preventivo de atenção pedagógica (não constitui reprovação automática): "
            f"frequência acumulada em {att_pct}% (na faixa preventiva entre "
            f"{ATTENDANCE_CRITICAL_LIMIT}% e {ATTENDANCE_PREVENTIVE_LIMIT}%, próxima ao limite de faltas)."
        )
        action = (
            "Orientar preventivamente o estudante sobre o saldo restante de horas antes "
            "de atingir o limite legal de 25% de faltas."
        )
        triggered_rules.append(
            RiskRuleEvaluationItemSchema(
                rule_code=rule_code,
                alert_category=AlertCategory.ATTENDANCE,
                risk_level=RiskLevel.HIGH,
                module_id=metrics.module_id,
                explainable_reason=reason,
                recommended_action=action,
                metric_snapshot={
                    **base_snapshot,
                    "rule_code": rule_code,
                    "threshold": str(ATTENDANCE_PREVENTIVE_LIMIT),
                    "recommended_action": action,
                },
            )
        )

    # Regra 2: Tarefas Práticas de Oficina em Atraso (>= 2 LATE -> MODERATE / >= 3 LATE -> HIGH)
    if metrics.late_tasks_count >= LATE_TASKS_MODERATE_THRESHOLD:
        is_high_backlog = metrics.late_tasks_count >= LATE_TASKS_HIGH_THRESHOLD
        task_risk = RiskLevel.HIGH if is_high_backlog else RiskLevel.MODERATE
        rule_code = (
            "PRACTICAL_TASKS_LATE_HIGH"
            if is_high_backlog
            else "PRACTICAL_TASKS_LATE_MODERATE"
        )
        reason = (
            "Indicador de atenção pedagógica (não constitui reprovação automática): "
            f"estudante acumula {metrics.late_tasks_count} atividades práticas de oficina "
            f"em atraso (LATE) de um total de {metrics.total_tasks_count} atribuídas."
        )
        action = (
            "Agendar horário de apoio prático em bancada/oficina para regularização "
            "das entregas pendentes."
        )
        triggered_rules.append(
            RiskRuleEvaluationItemSchema(
                rule_code=rule_code,
                alert_category=AlertCategory.PENDING_TASKS,
                risk_level=task_risk,
                module_id=metrics.module_id,
                explainable_reason=reason,
                recommended_action=action,
                metric_snapshot={
                    **base_snapshot,
                    "rule_code": rule_code,
                    "threshold": LATE_TASKS_HIGH_THRESHOLD
                    if is_high_backlog
                    else LATE_TASKS_MODERATE_THRESHOLD,
                    "recommended_action": action,
                },
            )
        )

    # Regra 3: Média Parcial / Consolidada abaixo da Nota de Corte (passing_score) -> HIGH
    if avg_grade is not None and avg_grade < passing:
        rule_code = "PARTIAL_AVERAGE_BELOW_PASSING_SCORE"
        deficit = _q2(passing - avg_grade)
        reason = (
            "Indicador de atenção pedagógica (não constitui reprovação automática): "
            f"média parcial consolidada em {avg_grade}, abaixo da nota de corte de "
            f"referência ({passing}, diferença de -{deficit} ponto(s))."
        )
        action = (
            "Oferecer recuperação paralela e mentoria focada nos critérios técnicos "
            "com menor pontuação."
        )
        triggered_rules.append(
            RiskRuleEvaluationItemSchema(
                rule_code=rule_code,
                alert_category=AlertCategory.GRADE_DROP,
                risk_level=RiskLevel.HIGH,
                module_id=metrics.module_id,
                explainable_reason=reason,
                recommended_action=action,
                metric_snapshot={
                    **base_snapshot,
                    "rule_code": rule_code,
                    "threshold": str(passing),
                    "grade_deficit": str(deficit),
                    "recommended_action": action,
                },
            )
        )

    if not triggered_rules:
        return RiskLevel.LOW, []

    overall_risk = max(
        (rule.risk_level for rule in triggered_rules),
        key=lambda lvl: _RISK_SEVERITY_RANK[lvl],
    )
    return overall_risk, triggered_rules


class RiskEngineService:
    """Serviço transparente e explicável de identificação precoce de risco acadêmico (BE-032)."""

    def __init__(self, repository: RiskEngineRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_alert_response(alert: AcademicAlert) -> AcademicAlertResponseSchema:
        """Serializa entidade AcademicAlert no contrato explicável de resposta."""
        return AcademicAlertResponseSchema(
            id=alert.id,
            student_id=alert.student_id,
            enrollment_id=alert.enrollment_id,
            class_id=alert.class_id,
            module_id=alert.module_id,
            risk_level=alert.risk_level,
            alert_category=alert.alert_category,
            explainable_reason=alert.explainable_reason,
            metric_snapshot=alert.metric_snapshot,
            status=alert.status,
            ethical_disclaimer=ETHICAL_PEDAGOGICAL_DISCLAIMER,
            created_at=alert.created_at,
        )

    def _resolve_course_passing_score(self, course_id: UUID) -> Decimal:
        """Calcula a nota de corte de referência do curso a partir dos seus módulos práticos."""
        modules = self._repository.get_course_average_passing_score(course_id)
        if not modules:
            return DEFAULT_PASSING_SCORE
        total = sum((Decimal(m.passing_score) for m in modules), Decimal("0.00"))
        return _q2(total / Decimal(len(modules)))

    def _evaluate_and_sync_rows(
        self,
        *,
        class_id: UUID,
        passing_score: Decimal,
        view_rows: list[dict[str, Any]],
        evaluated_at: datetime,
    ) -> list[StudentRiskEvaluationResultSchema]:
        """Executa regras determinísticas e sincroniza academic_alerts sem duplicar alertas abertos."""
        if not view_rows:
            return []

        enrollment_ids = [UUID(str(r["enrollment_id"])) for r in view_rows]
        open_alerts = self._repository.list_open_alerts_by_enrollments(enrollment_ids)

        # Agrupa alertas abertos por (enrollment_id, alert_category)
        open_by_enr_cat: dict[tuple[UUID, AlertCategory], list[AcademicAlert]] = {}
        for alert in open_alerts:
            open_by_enr_cat.setdefault(
                (alert.enrollment_id, alert.alert_category),
                [],
            ).append(alert)

        results: list[StudentRiskEvaluationResultSchema] = []

        for row in view_rows:
            enr_id = UUID(str(row["enrollment_id"]))
            stu_id = UUID(str(row["student_id"]))
            parsed_att = _to_dec_or_none(row.get("attendance_percentage"))
            att_pct = parsed_att if parsed_att is not None else Decimal("100.00")
            overall_avg = _to_dec_or_none(row.get("overall_average"))
            total_h = int(row.get("total_lesson_hours") or 0)
            attended_h = int(row.get("attended_hours") or 0)
            absent_h = int(row.get("absent_hours") or 0)
            late_tasks = int(row.get("late_tasks_count") or 0)
            pending_tasks = int(row.get("pending_tasks_count") or 0)
            completed_tasks = int(row.get("completed_tasks_count") or 0)
            total_tasks = int(row.get("total_tasks_count") or 0)

            metrics_input = StudentRiskMetricsInput(
                attendance_percentage=att_pct,
                total_lesson_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                late_tasks_count=late_tasks,
                pending_tasks_count=pending_tasks,
                completed_tasks_count=completed_tasks,
                total_tasks_count=total_tasks,
                overall_average=overall_avg,
                passing_score=passing_score,
            )
            overall_risk, triggered_rules = evaluate_student_risk_rules(
                metrics_input,
                evaluated_at=evaluated_at,
            )
            triggered_by_cat = {rule.alert_category: rule for rule in triggered_rules}

            created_count = 0
            updated_count = 0
            resolved_count = 0
            student_active_alerts: list[AcademicAlert] = []

            for category in _MANAGED_RULE_CATEGORIES:
                existing_list = open_by_enr_cat.get((enr_id, category), [])
                rule = triggered_by_cat.get(category)

                if rule is not None:
                    if existing_list:
                        primary = existing_list[0]
                        self._repository.update_open_alert(
                            primary,
                            risk_level=rule.risk_level,
                            explainable_reason=rule.explainable_reason,
                            metric_snapshot=rule.metric_snapshot,
                        )
                        updated_count += 1
                        student_active_alerts.append(primary)
                        # Caso existam duplicatas legadas para a mesma categoria, encerra o excedente
                        for extra_dup in existing_list[1:]:
                            self._repository.auto_resolve_alert(
                                extra_dup,
                                resolution_notes="Alerta consolidado automaticamente para evitar duplicidade.",
                            )
                            resolved_count += 1
                    else:
                        created_alert = self._repository.create_alert(
                            student_id=stu_id,
                            enrollment_id=enr_id,
                            class_id=class_id,
                            module_id=rule.module_id,
                            risk_level=rule.risk_level,
                            alert_category=rule.alert_category,
                            explainable_reason=rule.explainable_reason,
                            metric_snapshot=rule.metric_snapshot,
                        )
                        created_count += 1
                        student_active_alerts.append(created_alert)
                else:
                    for stale_alert in existing_list:
                        self._repository.auto_resolve_alert(
                            stale_alert,
                            resolution_notes=(
                                "Indicador normalizado automaticamente após recuperação das métricas acadêmicas."
                            ),
                        )
                        resolved_count += 1

            # Preserva alertas abertos de categorias externas (ex: SELF_EVAL_GAP - BE-037)
            for (e_id, cat), extra_alerts in open_by_enr_cat.items():
                if e_id == enr_id and cat not in _MANAGED_RULE_CATEGORIES:
                    student_active_alerts.extend(extra_alerts)
                    for ext in extra_alerts:
                        if (
                            _RISK_SEVERITY_RANK[ext.risk_level]
                            > _RISK_SEVERITY_RANK[overall_risk]
                        ):
                            overall_risk = ext.risk_level

            student_active_alerts.sort(
                key=lambda a: (-_RISK_SEVERITY_RANK[a.risk_level], str(a.id))
            )

            results.append(
                StudentRiskEvaluationResultSchema(
                    enrollment_id=enr_id,
                    student_id=stu_id,
                    class_id=class_id,
                    overall_risk_level=overall_risk,
                    attendance_percentage=att_pct,
                    overall_average=overall_avg,
                    passing_score=passing_score,
                    late_tasks_count=late_tasks,
                    created_alerts_count=created_count,
                    updated_alerts_count=updated_count,
                    auto_resolved_alerts_count=resolved_count,
                    ethical_disclaimer=ETHICAL_PEDAGOGICAL_DISCLAIMER,
                    active_alerts=[
                        self._to_alert_response(a) for a in student_active_alerts
                    ],
                )
            )

        self._repository.commit()
        return results

    def evaluate_class_students_risk(
        self,
        *,
        class_id: UUID,
        student_ids: Sequence[UUID] | None = None,
    ) -> list[StudentRiskEvaluationResultSchema]:
        """Executa o motor de risco internamente para alunos específicos ou todos os ativos da turma."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            return []
        passing_score = self._resolve_course_passing_score(academic_class.course_id)
        now = _utc_now()
        rows = self._repository.query_student_360_metrics(
            class_id=academic_class.id,
            student_ids=student_ids,
        )
        return self._evaluate_and_sync_rows(
            class_id=academic_class.id,
            passing_score=passing_score,
            view_rows=rows,
            evaluated_at=now,
        )

    def evaluate_student_enrollment_risk(
        self,
        *,
        enrollment_id: UUID,
    ) -> StudentRiskEvaluationResultSchema | None:
        """Executa o motor de risco para uma matrícula específica após mutação acadêmica."""
        enrollment = self._repository.get_enrollment_by_id(enrollment_id)
        if enrollment is None:
            return None
        passing_score = self._resolve_course_passing_score(
            enrollment.academic_class.course_id
        )
        now = _utc_now()
        rows = self._repository.query_student_360_metrics(
            class_id=enrollment.class_id,
            enrollment_ids=[enrollment.id],
        )
        results = self._evaluate_and_sync_rows(
            class_id=enrollment.class_id,
            passing_score=passing_score,
            view_rows=rows,
            evaluated_at=now,
        )
        return results[0] if results else None

    def evaluate_class_risk(
        self,
        class_id: UUID,
        *,
        current_user: User | None = None,
    ) -> ClassRiskEvaluationResponseSchema:
        """Avalia toda a turma com RBAC contextual, atualiza academic_alerts e retorna resumo auditável (BE-032)."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user is not None
            and current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
        ):
            raise ForbiddenException(message=RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE)

        passing_score = self._resolve_course_passing_score(academic_class.course_id)
        now = _utc_now()
        rows = self._repository.query_student_360_metrics(class_id=academic_class.id)
        results = self._evaluate_and_sync_rows(
            class_id=academic_class.id,
            passing_score=passing_score,
            view_rows=rows,
            evaluated_at=now,
        )

        low_count = sum(
            1 for r in results if r.overall_risk_level == RiskLevel.LOW
        )
        mod_count = sum(
            1 for r in results if r.overall_risk_level == RiskLevel.MODERATE
        )
        high_count = sum(
            1 for r in results if r.overall_risk_level == RiskLevel.HIGH
        )
        crit_count = sum(
            1 for r in results if r.overall_risk_level == RiskLevel.CRITICAL
        )
        created_sum = sum(r.created_alerts_count for r in results)
        updated_sum = sum(r.updated_alerts_count for r in results)
        resolved_sum = sum(r.auto_resolved_alerts_count for r in results)

        logger.bind(
            class_id=str(academic_class.id),
            actor_id=str(current_user.id) if current_user is not None else None,
            total_students_evaluated=len(results),
            low_risk_count=low_count,
            moderate_risk_count=mod_count,
            high_risk_count=high_count,
            critical_risk_count=crit_count,
            created_alerts_count=created_sum,
            updated_alerts_count=updated_sum,
            auto_resolved_alerts_count=resolved_sum,
        ).info("Motor explicável de risco acadêmico executado para a turma.")

        return ClassRiskEvaluationResponseSchema(
            class_id=academic_class.id,
            evaluated_at=now,
            total_students_evaluated=len(results),
            at_risk_students_count=mod_count + high_count + crit_count,
            low_risk_count=low_count,
            moderate_risk_count=mod_count,
            high_risk_count=high_count,
            critical_risk_count=crit_count,
            created_alerts_count=created_sum,
            updated_alerts_count=updated_sum,
            auto_resolved_alerts_count=resolved_sum,
            ethical_disclaimer=ETHICAL_PEDAGOGICAL_DISCLAIMER,
            results=results,
        )


def get_risk_engine_service(
    repository: RiskEngineRepositoryDep,
) -> RiskEngineService:
    """Provedor de injeção de dependência para RiskEngineService."""
    return RiskEngineService(repository=repository)


RiskEngineServiceDep = Annotated[
    RiskEngineService,
    Depends(get_risk_engine_service),
]

__all__ = [
    "ATTENDANCE_CRITICAL_LIMIT",
    "ATTENDANCE_PREVENTIVE_LIMIT",
    "DEFAULT_PASSING_SCORE",
    "LATE_TASKS_HIGH_THRESHOLD",
    "LATE_TASKS_MODERATE_THRESHOLD",
    "RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE",
    "RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE",
    "RiskEngineService",
    "RiskEngineServiceDep",
    "StudentRiskMetricsInput",
    "evaluate_student_risk_rules",
    "get_risk_engine_service",
]
