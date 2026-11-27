"""Motor em Python de Cruzamento Explicável: Autoavaliação Discente vs. Avaliação Prática do Docente (BE-037)."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import logger
from app.models.base import _utc_now
from app.models.practical_task import SkillEvidence
from app.models.user import User
from app.repositories.diagnostic_repository import (
    DiagnosticRepository,
    DiagnosticRepositoryDep,
)
from app.schemas.enums import (
    AlertCategory,
    CompetencyCategory,
    DiagnosticType,
    RiskLevel,
    UserRole,
)
from app.schemas.self_assessment import (
    DiagnosticDiscrepanciesFiltersAppliedSchema,
    DiagnosticDiscrepanciesListResponseSchema,
    DiagnosticDiscrepanciesQueryParams,
    DiagnosticDiscrepanciesSummarySchema,
    DiagnosticEngineEvaluationResponseSchema,
    DiagnosticEvidenceSummarySchema,
    ExplainableDiagnosticItemResponseSchema,
)

DIAGNOSTIC_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso restrito: estudantes só possuem permissão para visualizar seu próprio comparativo de aprendizagem."
)
DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE: Final[str] = (
    "Acesso não autorizado: estudante não possui matrícula ativa nesta turma."
)
DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: estudante não pertence às turmas ativas do professor."
)

# Limiares oficiais do Algoritmo de Cruzamento Diagnóstico (BE-037 / DB-038 / Seção 4.3)
ALIGNED_STRICT_THRESHOLD: Final[Decimal] = Decimal("0.80")
DISCREPANCY_CRITICAL_THRESHOLD: Final[Decimal] = Decimal("1.50")
HIGH_DIFFICULTY_LEVEL_THRESHOLD: Final[int] = 2
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")

SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER: Final[str] = (
    "A autoavaliação discente possui caráter estritamente formativo e reflexivo, "
    "jamais sendo tratada como prova definitiva de competência técnica. "
    "Este diagnóstico explicável cruza percepção e evidências práticas de oficina para apoiar "
    "a mentoria docente sem aplicar rótulos determinísticos ou punitivos ao estudante."
)


def _q2(value: Decimal) -> Decimal:
    """Padroniza valor Decimal com duas casas decimais usando ROUND_HALF_UP."""
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um objeto datetime esteja em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_dec_or_none(raw: Any) -> Decimal | None:
    """Converte valor arbitrário vindo de SQL view em Decimal(0.01) ou None."""
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return _q2(raw)
    return _q2(Decimal(str(raw)))


@dataclass(frozen=True, slots=True)
class CompetencyDiagnosticInput:
    """Conjunto auditável de dados de entrada por competência para o algoritmo de cruzamento (BE-037)."""

    competency_id: UUID
    competency_code: str
    competency_title: str
    competency_category: CompetencyCategory
    module_title: str
    perceived_level: Decimal | int
    confidence_score: int = 3
    avg_verified_level: Decimal | None = None
    evidence_count: int = 0
    difficulty_notes: str | None = None
    evidences_used: Sequence[DiagnosticEvidenceSummarySchema] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class CompetencyDiagnosticEvaluationResult:
    """Resultado puro e explicável do algoritmo de cruzamento por competência (BE-037)."""

    self_perceived_level: Decimal
    teacher_verified_level: Decimal
    discrepancy_gap: Decimal
    abs_discrepancy: Decimal
    evidence_count: int
    diagnostic_type: DiagnosticType
    is_strictly_aligned: bool
    explanation_text: str
    limitations_note: str
    recommended_action: str
    should_trigger_pedagogical_alert: bool
    alert_risk_level: RiskLevel | None
    alert_explainable_reason: str | None


def is_safety_or_precision_competency(
    *,
    category: CompetencyCategory,
    code: str = "",
    title: str = "",
) -> bool:
    """Identifica se a competência envolve segurança operacional (SAFETY) ou precisão técnica/procedimental crítica (TECHNICAL/PROCEDURAL)."""
    if category in (
        CompetencyCategory.SAFETY,
        CompetencyCategory.TECHNICAL,
        CompetencyCategory.PROCEDURAL,
    ):
        return True
    combined = f"{code} {title}".lower()
    keywords = (
        "segurança",
        "nr-12",
        "epi",
        "precisão",
        "tolerância",
        "metrologia",
        "paquímetro",
        "micrômetro",
    )
    return any(kw in combined for kw in keywords)


def evaluate_competency_discrepancy(
    data: CompetencyDiagnosticInput,
) -> CompetencyDiagnosticEvaluationResult:
    """Executa o algoritmo determinístico e explicável de cruzamento Autoavaliação vs. Avaliação Prática (BE-037).

    Regras de classificação por competência:
    1. Sem entregas práticas avaliadas (evidence_count == 0 ou avg_verified_level is None) -> INSUFFICIENT_EVIDENCE.
    2. Se perceived - verified >= 1.50 -> OVERCONFIDENCE_RISK (percepção acima da evidência prática/tolerância).
    3. Se verified - perceived >= 1.50 (gap <= -1.50) -> UNDERCONFIDENCE_SUPPORT (domínio prático comprovado, mas estudante inseguro).
    4. Se |perceived - verified| <= 0.80 -> ALIGNED (alinhamento estrito) e faixa intermediária (0.80 < |gap| < 1.50) -> ALIGNED com observação preventiva.
    """
    self_level = _q2(Decimal(data.perceived_level))
    ev_count = max(0, int(data.evidence_count))

    evidences_summary_parts: list[str] = []
    for ev in data.evidences_used:
        task_label = f" ({ev.task_title})" if ev.task_title else ""
        evidences_summary_parts.append(
            f"evidência {str(ev.evidence_id)[:8]}{task_label}: nível {ev.verified_level:.2f}/5.00"
        )
    evidences_detail_text = (
        f" Evidências práticas utilizadas ({ev_count}): " + "; ".join(evidences_summary_parts) + "."
        if evidences_summary_parts
        else f" Total de evidências práticas em skill_evidences consideradas: {ev_count}."
    )

    # Cenário 4: Sem entregas práticas avaliadas -> INSUFFICIENT_EVIDENCE
    if ev_count == 0 or data.avg_verified_level is None:
        teacher_level = self_level
        gap = Decimal("0.00")
        abs_gap = Decimal("0.00")
        diag_type = DiagnosticType.INSUFFICIENT_EVIDENCE
        explanation_text = (
            f"Critério INSUFFICIENT_EVIDENCE (sem entregas práticas avaliadas): na competência "
            f"'{data.competency_code} — {data.competency_title}' ({data.competency_category.value}) do módulo "
            f"'{data.module_title}', o estudante declarou nível percebido {self_level:.2f}/5.00 "
            f"(confiança {data.confidence_score}/5), mas ainda não existem evidências práticas verificadas "
            f"pelo docente em skill_evidences (evidence_count = 0) para cruzamento objetivo."
        )
        limitations_note = (
            f"Limitação explícita: diagnóstico preliminar com 0 evidências práticas registradas pelo professor. "
            f"{SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER}"
        )
        if self_level <= Decimal(HIGH_DIFFICULTY_LEVEL_THRESHOLD):
            recommended_action = (
                "Priorizar acompanhamento preventivo em bancada na próxima aula prática e verificar necessidade de apoio pedagógico."
            )
        else:
            recommended_action = (
                "Aguardar o registro e avaliação de atividade prática com rubricas (BE-025) para consolidar o comparativo docente."
            )
        return CompetencyDiagnosticEvaluationResult(
            self_perceived_level=self_level,
            teacher_verified_level=teacher_level,
            discrepancy_gap=gap,
            abs_discrepancy=abs_gap,
            evidence_count=0,
            diagnostic_type=diag_type,
            is_strictly_aligned=False,
            explanation_text=explanation_text,
            limitations_note=limitations_note,
            recommended_action=recommended_action,
            should_trigger_pedagogical_alert=False,
            alert_risk_level=None,
            alert_explainable_reason=None,
        )

    teacher_level = min(
        Decimal("5.00"),
        max(Decimal("1.00"), _q2(Decimal(data.avg_verified_level))),
    )
    gap = _q2(self_level - teacher_level)
    abs_gap = abs(gap)
    is_strictly_aligned = abs_gap <= ALIGNED_STRICT_THRESHOLD

    should_alert = False
    alert_risk: RiskLevel | None = None
    alert_reason: str | None = None

    # Cenário 2: perceived - verified >= 1.50 -> OVERCONFIDENCE_RISK
    if gap >= DISCREPANCY_CRITICAL_THRESHOLD:
        diag_type = DiagnosticType.OVERCONFIDENCE_RISK
        explanation_text = (
            f"Critério OVERCONFIDENCE_RISK (perceived - verified >= {DISCREPANCY_CRITICAL_THRESHOLD:.2f}): "
            f"na competência '{data.competency_code} — {data.competency_title}' ({data.competency_category.value}) "
            f"do módulo '{data.module_title}', o estudante declarou nível percebido {self_level:.2f}/5.00 "
            f"(confiança {data.confidence_score}/5), enquanto a média das evidências práticas verificadas pelo "
            f"docente é {teacher_level:.2f}/5.00 (gap de +{gap:.2f} ponto(s)).{evidences_detail_text}"
        )
        recommended_action = (
            "Realizar mentoria técnica e calibração prática em bancada para alinhar a percepção do estudante às tolerâncias dimensionais e normas operacionais."
        )

        # Critério de Aceitação 3: Gera alerta pedagógico quando houver divergência crítica em competência de segurança ou precisão
        if is_safety_or_precision_competency(
            category=data.competency_category,
            code=data.competency_code,
            title=data.competency_title,
        ):
            should_alert = True
            if (
                data.competency_category == CompetencyCategory.SAFETY
                or gap >= Decimal("2.00")
            ):
                alert_risk = RiskLevel.CRITICAL
            else:
                alert_risk = RiskLevel.HIGH
            category_focus = (
                "segurança operacional"
                if data.competency_category == CompetencyCategory.SAFETY
                else "precisão técnica e tolerância"
            )
            alert_reason = (
                f"Indicador pedagógico de discrepância crítica em competência de {category_focus} "
                f"('{data.competency_code} — {data.competency_title}' no módulo '{data.module_title}'): "
                f"autoavaliação em {self_level:.2f}/5.00 vs. evidência prática verificada pelo docente em "
                f"{teacher_level:.2f}/5.00 (gap de +{gap:.2f} em {ev_count} evidência(s)). "
                "Requer orientação em oficina para prevenção de erros operacionais ou desvios de tolerância."
            )

    # Cenário 3: verified - perceived >= 1.50 (gap <= -1.50) -> UNDERCONFIDENCE_SUPPORT
    elif gap <= -DISCREPANCY_CRITICAL_THRESHOLD:
        diag_type = DiagnosticType.UNDERCONFIDENCE_SUPPORT
        inverse_diff = _q2(teacher_level - self_level)
        explanation_text = (
            f"Critério UNDERCONFIDENCE_SUPPORT (verified - perceived >= {DISCREPANCY_CRITICAL_THRESHOLD:.2f}): "
            f"na competência '{data.competency_code} — {data.competency_title}' ({data.competency_category.value}) "
            f"do módulo '{data.module_title}', o estudante declarou nível percebido {self_level:.2f}/5.00 "
            f"(confiança {data.confidence_score}/5), porém atingiu média prática superior de {teacher_level:.2f}/5.00 "
            f"verificada pelo docente (diferença de +{inverse_diff:.2f} a favor da prática; gap {gap:.2f}).{evidences_detail_text}"
        )
        recommended_action = (
            "Realizar devolutiva de reforço positivo evidenciando os resultados práticos alcançados na oficina para fortalecer a autoconfiança técnica do estudante."
        )

    # Cenário 1: |perceived - verified| <= 0.80 (e faixa moderada < 1.50) -> ALIGNED
    else:
        diag_type = DiagnosticType.ALIGNED
        band_description = (
            f"|perceived - verified| <= {ALIGNED_STRICT_THRESHOLD:.2f} (convergência estrita)"
            if is_strictly_aligned
            else f"{ALIGNED_STRICT_THRESHOLD:.2f} < |perceived - verified| < {DISCREPANCY_CRITICAL_THRESHOLD:.2f} (convergência moderada dentro da margem aceitável)"
        )
        explanation_text = (
            f"Critério ALIGNED ({band_description}): na competência '{data.competency_code} — {data.competency_title}' "
            f"({data.competency_category.value}) do módulo '{data.module_title}', o nível autopercebido de "
            f"{self_level:.2f}/5.00 (confiança {data.confidence_score}/5) está alinhado à média prática de "
            f"{teacher_level:.2f}/5.00 verificada pelo docente (gap de {gap:+.2f}).{evidences_detail_text}"
        )
        if self_level <= Decimal(HIGH_DIFFICULTY_LEVEL_THRESHOLD):
            recommended_action = (
                "Percepção e avaliação docente convergem em nível inicial (<= 2.00): oferecer prática assistida focalizada para evolução gradual no módulo."
            )
        elif not is_strictly_aligned:
            recommended_action = (
                "Acompanhar evolução nas próximas tarefas práticas para manter a calibração entre autopercepção e rubricas de bancada."
            )
        else:
            recommended_action = (
                "Manter progressão prática nas atividades do módulo com acompanhamento regular das rubricas técnicas."
            )

    difficulty_excerpt = (
        f" Relato textual registrado pelo estudante: '{data.difficulty_notes}'."
        if data.difficulty_notes
        else ""
    )
    limitations_note = (
        f"Limitações e transparência do diagnóstico: análise calculada sobre {ev_count} evidência(s) prática(s) "
        f"(skill_evidences) e autoavaliação declarada pelo estudante (limiares: alinhamento estrito <= {ALIGNED_STRICT_THRESHOLD:.2f}; "
        f"divergência crítica >= {DISCREPANCY_CRITICAL_THRESHOLD:.2f}). {SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER}{difficulty_excerpt}"
    )

    return CompetencyDiagnosticEvaluationResult(
        self_perceived_level=self_level,
        teacher_verified_level=teacher_level,
        discrepancy_gap=gap,
        abs_discrepancy=abs_gap,
        evidence_count=ev_count,
        diagnostic_type=diag_type,
        is_strictly_aligned=is_strictly_aligned,
        explanation_text=explanation_text,
        limitations_note=limitations_note,
        recommended_action=recommended_action,
        should_trigger_pedagogical_alert=should_alert,
        alert_risk_level=alert_risk,
        alert_explainable_reason=alert_reason,
    )


class DiagnosticService:
    """Serviço de domínio que consulta vw_self_eval_discrepancy (DB-038), grava explainable_diagnostics (DB-035) e sincroniza alertas pedagógicos (BE-037)."""

    def __init__(self, repository: DiagnosticRepository) -> None:
        self._repository = repository

    @staticmethod
    def _build_evidence_summaries(
        evidences: Sequence[SkillEvidence],
    ) -> list[DiagnosticEvidenceSummarySchema]:
        """Converte entidades SkillEvidence em resumos auditáveis das evidências utilizadas no diagnóstico."""
        items: list[DiagnosticEvidenceSummarySchema] = []
        for ev in evidences:
            sub = ev.source_submission
            task = sub.task if sub is not None else None
            items.append(
                DiagnosticEvidenceSummarySchema(
                    evidence_id=ev.id,
                    competency_id=ev.competency_id,
                    source_submission_id=ev.source_submission_id,
                    task_id=task.id if task is not None else None,
                    task_title=task.title if task is not None else None,
                    verified_level=_q2(Decimal(ev.verified_level)),
                    verified_by=ev.verified_by,
                    recorded_at=_ensure_utc(ev.recorded_at),
                )
            )
        return items

    def run_diagnostic_crossover(
        self,
        *,
        class_id: UUID | None = None,
        module_id: UUID | None = None,
        form_id: UUID | None = None,
        student_id: UUID | None = None,
        competency_ids: Sequence[UUID] | None = None,
    ) -> list[ExplainableDiagnosticItemResponseSchema]:
        """Consulta vw_self_eval_discrepancy, executa o algoritmo dos 4 cenários, grava explainable_diagnostics e gera alertas pedagógicos."""
        view_rows = self._repository.query_discrepancy_view(
            class_id=class_id,
            module_id=module_id,
            form_id=form_id,
            student_id=student_id,
            competency_ids=competency_ids,
        )
        if not view_rows:
            return []

        student_ids = [UUID(str(row["student_id"])) for row in view_rows]
        comp_ids = [UUID(str(row["competency_id"])) for row in view_rows]
        class_ids = [UUID(str(row["class_id"])) for row in view_rows]

        evidences_map = (
            self._repository.list_skill_evidences_for_students_and_competencies(
                student_ids=student_ids,
                competency_ids=comp_ids,
            )
        )
        enrollments_map = (
            self._repository.list_active_enrollments_by_class_and_students(
                class_ids=class_ids,
                student_ids=student_ids,
            )
        )

        # Deduplica por (student_id, class_id, module_id, competency_id) preservando a submissão mais recente
        seen_keys: set[tuple[UUID, UUID, UUID, UUID]] = set()
        now = _utc_now()
        results: list[ExplainableDiagnosticItemResponseSchema] = []

        for row in view_rows:
            stu_id = UUID(str(row["student_id"]))
            cls_id = UUID(str(row["class_id"]))
            mod_id = UUID(str(row["module_id"]))
            comp_id = UUID(str(row["competency_id"]))
            dedup_key = (stu_id, cls_id, mod_id, comp_id)
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            raw_cat = row.get("competency_category")
            comp_category = (
                raw_cat
                if isinstance(raw_cat, CompetencyCategory)
                else CompetencyCategory(str(raw_cat))
            )
            perceived_dec = (
                _to_dec_or_none(row.get("perceived_level")) or Decimal("1.00")
            )
            avg_verified_dec = _to_dec_or_none(row.get("avg_verified_level"))
            ev_count = int(row.get("evidence_count") or 0)
            conf_score = int(row.get("confidence_score") or 3)
            comp_code = str(row.get("competency_code") or "")
            comp_title = str(row.get("competency_title") or "")
            mod_title = str(row.get("module_title") or "")
            stu_name = (
                str(row["student_name"])
                if row.get("student_name") is not None
                else None
            )
            diff_notes = (
                str(row["difficulty_notes"])
                if row.get("difficulty_notes") is not None
                else None
            )

            raw_evidences = evidences_map.get((stu_id, comp_id), [])
            evidence_summaries = self._build_evidence_summaries(raw_evidences)

            eval_input = CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code=comp_code,
                competency_title=comp_title,
                competency_category=comp_category,
                module_title=mod_title,
                perceived_level=perceived_dec,
                confidence_score=conf_score,
                avg_verified_level=avg_verified_dec,
                evidence_count=ev_count,
                difficulty_notes=diff_notes,
                evidences_used=evidence_summaries,
            )
            eval_result = evaluate_competency_discrepancy(eval_input)

            persisted_diag = self._repository.upsert_explainable_diagnostic(
                student_id=stu_id,
                class_id=cls_id,
                module_id=mod_id,
                competency_id=comp_id,
                self_perceived_level=eval_result.self_perceived_level,
                teacher_verified_level=eval_result.teacher_verified_level,
                discrepancy_gap=eval_result.discrepancy_gap,
                diagnostic_type=eval_result.diagnostic_type,
                explanation_text=eval_result.explanation_text,
                limitations_note=eval_result.limitations_note,
                recommended_action=eval_result.recommended_action,
                generated_at=now,
            )

            enrollment = enrollments_map.get((cls_id, stu_id))
            triggered_alert_id: UUID | None = None
            alert_triggered = False

            if enrollment is not None:
                snapshot = {
                    "rule_code": "SELF_EVAL_CRITICAL_OVERCONFIDENCE_GAP",
                    "diagnostic_id": str(persisted_diag.id),
                    "diagnostic_type": eval_result.diagnostic_type.value,
                    "competency_id": str(comp_id),
                    "competency_code": comp_code,
                    "competency_title": comp_title,
                    "competency_category": comp_category.value,
                    "module_id": str(mod_id),
                    "module_title": mod_title,
                    "self_perceived_level": str(eval_result.self_perceived_level),
                    "teacher_verified_level": str(eval_result.teacher_verified_level),
                    "discrepancy_gap": str(eval_result.discrepancy_gap),
                    "evidence_count": eval_result.evidence_count,
                    "evidences_used": [
                        {
                            "evidence_id": str(ev.evidence_id),
                            "task_id": str(ev.task_id) if ev.task_id else None,
                            "task_title": ev.task_title,
                            "verified_level": str(ev.verified_level),
                            "recorded_at": ev.recorded_at.isoformat(),
                        }
                        for ev in evidence_summaries
                    ],
                    "recommended_action": eval_result.recommended_action,
                    "limitations_note": eval_result.limitations_note,
                    "ethical_disclaimer": SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
                }
                synced_alert = (
                    self._repository.sync_self_eval_gap_alert_for_competency(
                        student_id=stu_id,
                        enrollment_id=enrollment.id,
                        class_id=cls_id,
                        module_id=mod_id,
                        competency_id=comp_id,
                        should_trigger=eval_result.should_trigger_pedagogical_alert,
                        risk_level=eval_result.alert_risk_level or RiskLevel.HIGH,
                        explainable_reason=(
                            eval_result.alert_explainable_reason
                            or eval_result.explanation_text
                        ),
                        metric_snapshot=snapshot,
                    )
                )
                if synced_alert is not None:
                    alert_triggered = True
                    triggered_alert_id = synced_alert.id

            results.append(
                ExplainableDiagnosticItemResponseSchema(
                    id=persisted_diag.id,
                    student_id=stu_id,
                    student_name=stu_name,
                    class_id=cls_id,
                    module_id=mod_id,
                    module_title=mod_title,
                    competency_id=comp_id,
                    competency_code=comp_code,
                    competency_title=comp_title,
                    competency_category=comp_category,
                    self_perceived_level=eval_result.self_perceived_level,
                    teacher_verified_level=eval_result.teacher_verified_level,
                    discrepancy_gap=eval_result.discrepancy_gap,
                    confidence_score=conf_score,
                    evidence_count=eval_result.evidence_count,
                    evidences_used=evidence_summaries,
                    diagnostic_type=eval_result.diagnostic_type,
                    explanation_text=eval_result.explanation_text,
                    limitations_note=eval_result.limitations_note,
                    recommended_action=eval_result.recommended_action,
                    pedagogical_alert_triggered=alert_triggered,
                    pedagogical_alert_id=triggered_alert_id,
                    generated_at=_ensure_utc(persisted_diag.generated_at),
                )
            )

        self._repository.commit()
        return results

    def evaluate_class_diagnostics(
        self,
        class_id: UUID,
        *,
        module_id: UUID | None = None,
        student_id: UUID | None = None,
        current_user: User | None = None,
    ) -> DiagnosticEngineEvaluationResponseSchema:
        """Executa o motor de cruzamento diagnóstico para uma turma (com filtros opcionais de módulo/estudante) e retorna sumário explicável (BE-037)."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=DIAGNOSTIC_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user is not None
            and current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
        ):
            raise ForbiddenException(message=DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE)

        if module_id is not None:
            if self._repository.get_module_by_id(module_id) is None:
                raise NotFoundException(message=DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE)

        now = _utc_now()
        diagnostics = self.run_diagnostic_crossover(
            class_id=academic_class.id,
            module_id=module_id,
            student_id=student_id,
        )

        aligned_count = sum(
            1 for d in diagnostics if d.diagnostic_type == DiagnosticType.ALIGNED
        )
        overconf_count = sum(
            1
            for d in diagnostics
            if d.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
        )
        underconf_count = sum(
            1
            for d in diagnostics
            if d.diagnostic_type == DiagnosticType.UNDERCONFIDENCE_SUPPORT
        )
        insufficient_count = sum(
            1
            for d in diagnostics
            if d.diagnostic_type == DiagnosticType.INSUFFICIENT_EVIDENCE
        )
        alerts_count = sum(
            1 for d in diagnostics if d.pedagogical_alert_triggered
        )

        logger.bind(
            class_id=str(academic_class.id),
            module_id=str(module_id) if module_id else None,
            student_id=str(student_id) if student_id else None,
            actor_id=str(current_user.id) if current_user is not None else None,
            total_diagnostics=len(diagnostics),
            aligned_count=aligned_count,
            overconfidence_risk_count=overconf_count,
            underconfidence_support_count=underconf_count,
            insufficient_evidence_count=insufficient_count,
            pedagogical_alerts_triggered_count=alerts_count,
        ).info("Motor de cruzamento diagnóstico explicável (BE-037) executado com sucesso.")

        return DiagnosticEngineEvaluationResponseSchema(
            class_id=academic_class.id,
            module_id=module_id,
            student_id=student_id,
            evaluated_at=now,
            total_diagnostics_generated=len(diagnostics),
            aligned_count=aligned_count,
            overconfidence_risk_count=overconf_count,
            underconfidence_support_count=underconf_count,
            insufficient_evidence_count=insufficient_count,
            pedagogical_alerts_triggered_count=alerts_count,
            ethical_disclaimer=SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
            diagnostics=diagnostics,
        )

    def get_discrepancies(
        self,
        params: DiagnosticDiscrepanciesQueryParams,
        *,
        current_user: User,
    ) -> DiagnosticDiscrepanciesListResponseSchema:
        """Consulta comparativa de discrepâncias de aprendizagem entre autoavaliação e evidências práticas (GET /api/v1/diagnostics/discrepancies - BE-038).

        Critérios de Aceitação e Regras de Negócio:
        - Estudante visualiza apenas o próprio comparativo com linguagem pedagógica construtiva.
        - Professor visualiza o mapa de divergências das suas turmas com filtros.
        - Coordenação e Admin possuem visão geral irrestrita.
        """
        target_class_id: UUID | None = None
        target_class_ids: list[UUID] | None = None
        effective_student_id: UUID | None = None

        if current_user.role == UserRole.STUDENT:
            if params.student_id is not None and params.student_id != current_user.id:
                raise ForbiddenException(message=DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE)
            effective_student_id = current_user.id

            if params.class_id is not None:
                if not self._repository.is_student_enrolled_in_class(
                    student_id=current_user.id,
                    class_id=params.class_id,
                ):
                    raise ForbiddenException(
                        message=DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE
                    )
                target_class_id = params.class_id

        elif current_user.role == UserRole.TEACHER:
            if params.class_id is not None:
                if not self._repository.is_teacher_assigned_to_class(
                    teacher_id=current_user.id,
                    class_id=params.class_id,
                ):
                    raise ForbiddenException(
                        message=DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE
                    )
                target_class_id = params.class_id
            else:
                teacher_classes = self._repository.get_teacher_assigned_class_ids(
                    current_user.id
                )
                if not teacher_classes:
                    return DiagnosticDiscrepanciesListResponseSchema(
                        total=0,
                        page=params.page,
                        page_size=params.page_size,
                        total_pages=0,
                        summary=DiagnosticDiscrepanciesSummarySchema(
                            total_discrepancies=0,
                            aligned_count=0,
                            overconfidence_risk_count=0,
                            underconfidence_support_count=0,
                            insufficient_evidence_count=0,
                            critical_alerts_count=0,
                        ),
                        filters=DiagnosticDiscrepanciesFiltersAppliedSchema(
                            class_id=None,
                            module_id=params.module_id,
                            student_id=params.student_id,
                            competency_id=params.competency_id,
                            diagnostic_type=params.diagnostic_type,
                        ),
                        discrepancies=[],
                        ethical_disclaimer=SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
                    )
                target_class_ids = teacher_classes

            if params.student_id is not None:
                if target_class_id is not None:
                    if not self._repository.is_student_enrolled_in_class(
                        student_id=params.student_id,
                        class_id=target_class_id,
                    ):
                        raise ForbiddenException(
                            message=DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE
                        )
                else:
                    if not self._repository.is_student_in_teacher_classes(
                        teacher_id=current_user.id,
                        student_id=params.student_id,
                    ):
                        raise ForbiddenException(
                            message=DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE
                        )
                effective_student_id = params.student_id
        else:
            target_class_id = params.class_id
            effective_student_id = params.student_id

        if params.module_id is not None:
            if self._repository.get_module_by_id(params.module_id) is None:
                raise NotFoundException(message=DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE)

        # 1. Consulta inicial na tabela explainable_diagnostics
        all_matching, total_count = self._repository.query_explainable_diagnostics(
            class_id=target_class_id,
            class_ids=target_class_ids,
            module_id=params.module_id,
            student_id=effective_student_id,
            competency_id=params.competency_id,
            diagnostic_type=params.diagnostic_type,
            limit=10000,
            offset=0,
        )

        # 2. Se nenhum diagnóstico foi encontrado, verifica se há dados na view vw_self_eval_discrepancy para auto-sincronização
        if total_count == 0:
            discrepancy_rows = self._repository.query_discrepancy_view(
                class_id=target_class_id,
                module_id=params.module_id,
                student_id=effective_student_id,
                competency_ids=[params.competency_id] if params.competency_id else None,
            )
            if discrepancy_rows:
                if target_class_id is not None:
                    self.run_diagnostic_crossover(
                        class_id=target_class_id,
                        module_id=params.module_id,
                        student_id=effective_student_id,
                    )
                else:
                    distinct_cids = list(
                        dict.fromkeys(
                            r["class_id"]
                            for r in discrepancy_rows
                            if r.get("class_id") is not None
                        )
                    )
                    for cid in distinct_cids:
                        if target_class_ids is None or cid in target_class_ids:
                            self.run_diagnostic_crossover(
                                class_id=cid,
                                module_id=params.module_id,
                                student_id=effective_student_id,
                            )

                all_matching, total_count = (
                    self._repository.query_explainable_diagnostics(
                        class_id=target_class_id,
                        class_ids=target_class_ids,
                        module_id=params.module_id,
                        student_id=effective_student_id,
                        competency_id=params.competency_id,
                        diagnostic_type=params.diagnostic_type,
                        limit=10000,
                        offset=0,
                    )
                )

        # 3. Busca evidências práticas e alertas pedagógicos para enriquecer os diagnósticos
        stu_ids = list(dict.fromkeys(d.student_id for d in all_matching))
        comp_ids = list(
            dict.fromkeys(
                d.competency_id for d in all_matching if d.competency_id is not None
            )
        )
        mod_ids = list(dict.fromkeys(d.module_id for d in all_matching))

        evidences_map = (
            self._repository.list_skill_evidences_for_students_and_competencies(
                student_ids=stu_ids,
                competency_ids=comp_ids,
            )
        )
        alerts_map = (
            self._repository.map_active_self_eval_gap_alerts_for_students_and_modules(
                student_ids=stu_ids,
                module_ids=mod_ids,
            )
        )

        aligned_count = sum(
            1 for d in all_matching if d.diagnostic_type == DiagnosticType.ALIGNED
        )
        overconf_count = sum(
            1
            for d in all_matching
            if d.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
        )
        underconf_count = sum(
            1
            for d in all_matching
            if d.diagnostic_type == DiagnosticType.UNDERCONFIDENCE_SUPPORT
        )
        insufficient_count = sum(
            1
            for d in all_matching
            if d.diagnostic_type == DiagnosticType.INSUFFICIENT_EVIDENCE
        )
        critical_alerts_count = sum(
            1
            for d in all_matching
            if (d.student_id, d.module_id, d.competency_id) in alerts_map
        )

        # 4. Paginação dos resultados
        offset = (params.page - 1) * params.page_size
        paginated_raw = all_matching[offset : offset + params.page_size]

        formatted_items: list[ExplainableDiagnosticItemResponseSchema] = []
        for diag in paginated_raw:
            raw_evidences = (
                evidences_map.get((diag.student_id, diag.competency_id), [])
                if diag.competency_id is not None
                else []
            )
            evidence_summaries = [
                DiagnosticEvidenceSummarySchema(
                    evidence_id=ev.id,
                    competency_id=ev.competency_id,
                    source_submission_id=ev.source_submission_id,
                    task_id=ev.source_submission.task_id
                    if ev.source_submission is not None
                    else None,
                    task_title=ev.source_submission.task.title
                    if (
                        ev.source_submission is not None
                        and ev.source_submission.task is not None
                    )
                    else None,
                    verified_level=_q2(ev.verified_level),
                    verified_by=ev.verified_by,
                    recorded_at=_ensure_utc(ev.recorded_at),
                )
                for ev in raw_evidences
            ]

            active_alert = (
                alerts_map.get((diag.student_id, diag.module_id, diag.competency_id))
                if diag.competency_id is not None
                else None
            )

            student_name: str | None = None
            if diag.student is not None:
                student_name = (
                    diag.student.profile.full_name
                    if diag.student.profile is not None
                    else diag.student.email
                )

            module_title: str | None = (
                diag.module.title if diag.module is not None else None
            )
            competency_code: str | None = (
                diag.competency.code if diag.competency is not None else None
            )
            competency_title: str | None = (
                diag.competency.title if diag.competency is not None else None
            )
            competency_category = (
                diag.competency.category if diag.competency is not None else None
            )

            formatted_items.append(
                ExplainableDiagnosticItemResponseSchema(
                    id=diag.id,
                    student_id=diag.student_id,
                    student_name=student_name,
                    class_id=diag.class_id,
                    module_id=diag.module_id,
                    module_title=module_title,
                    competency_id=diag.competency_id,
                    competency_code=competency_code,
                    competency_title=competency_title,
                    competency_category=competency_category,
                    self_perceived_level=_q2(diag.self_perceived_level),
                    teacher_verified_level=_q2(diag.teacher_verified_level),
                    discrepancy_gap=_q2(diag.discrepancy_gap),
                    confidence_score=None,
                    evidence_count=len(evidence_summaries),
                    evidences_used=evidence_summaries,
                    diagnostic_type=diag.diagnostic_type,
                    explanation_text=diag.explanation_text,
                    limitations_note=diag.limitations_note,
                    recommended_action=diag.recommended_action,
                    pedagogical_alert_triggered=active_alert is not None,
                    pedagogical_alert_id=active_alert.id
                    if active_alert is not None
                    else None,
                    generated_at=_ensure_utc(diag.generated_at),
                )
            )

        total_pages = (
            (total_count + params.page_size - 1) // params.page_size
            if total_count > 0
            else 0
        )

        logger.bind(
            actor_id=str(current_user.id),
            actor_role=current_user.role.value,
            total_discrepancies=total_count,
            page=params.page,
            page_size=params.page_size,
        ).info("Discrepâncias de aprendizagem consultadas com sucesso (BE-038).")

        return DiagnosticDiscrepanciesListResponseSchema(
            total=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            summary=DiagnosticDiscrepanciesSummarySchema(
                total_discrepancies=total_count,
                aligned_count=aligned_count,
                overconfidence_risk_count=overconf_count,
                underconfidence_support_count=underconf_count,
                insufficient_evidence_count=insufficient_count,
                critical_alerts_count=critical_alerts_count,
            ),
            filters=DiagnosticDiscrepanciesFiltersAppliedSchema(
                class_id=target_class_id,
                module_id=params.module_id,
                student_id=effective_student_id,
                competency_id=params.competency_id,
                diagnostic_type=params.diagnostic_type,
            ),
            discrepancies=formatted_items,
            ethical_disclaimer=SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
        )


def get_diagnostic_service(
    repository: DiagnosticRepositoryDep,
) -> DiagnosticService:
    """Provedor de injeção de dependência para DiagnosticService."""
    return DiagnosticService(repository=repository)


DiagnosticServiceDep = Annotated[
    DiagnosticService,
    Depends(get_diagnostic_service),
]

__all__ = [
    "ALIGNED_STRICT_THRESHOLD",
    "CompetencyDiagnosticEvaluationResult",
    "CompetencyDiagnosticInput",
    "DIAGNOSTIC_CLASS_NOT_FOUND_MESSAGE",
    "DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE",
    "DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE",
    "DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE",
    "DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE",
    "DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE",
    "DISCREPANCY_CRITICAL_THRESHOLD",
    "DiagnosticService",
    "DiagnosticServiceDep",
    "SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER",
    "evaluate_competency_discrepancy",
    "get_diagnostic_service",
    "is_safety_or_precision_competency",
]
