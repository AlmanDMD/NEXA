"""Repositório SQLAlchemy 2.0 para o Motor de Cruzamento Diagnóstico Explicável (BE-037)."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.academic_alert import AcademicAlert
from app.models.academic_class import AcademicClass
from app.models.base import _utc_now
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.practical_task import SkillEvidence, TaskSubmission
from app.models.self_assessment import (
    ExplainableDiagnostic,
    VW_SELF_EVAL_DISCREPANCY_CREATE_SQL,
    VW_SELF_EVAL_DISCREPANCY_NAME,
    vw_self_eval_discrepancy_table,
)
from app.models.teacher_assignment import TeacherAssignment
from app.schemas.enums import (
    AlertCategory,
    AlertStatus,
    DiagnosticType,
    EnrollmentStatus,
    RiskLevel,
)


class DiagnosticRepository:
    """Repositório responsável por consultar vw_self_eval_discrepancy (DB-038), skill_evidences (DB-033), explainable_diagnostics (DB-035) e academic_alerts (DB-034)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def ensure_discrepancy_view(self) -> None:
        """Garante que a view analítica vw_self_eval_discrepancy (DB-038) esteja criada na conexão atual."""
        bind = self._session.get_bind()
        view_names = {name.lower() for name in inspect(bind).get_view_names()}
        if VW_SELF_EVAL_DISCREPANCY_NAME.lower() not in view_names:
            self._session.execute(text(VW_SELF_EVAL_DISCREPANCY_CREATE_SQL))
            self._session.commit()

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_module_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo prático pelo UUID carregando a disciplina associada."""
        stmt = (
            select(LearningModule)
            .options(joinedload(LearningModule.subject))
            .where(LearningModule.id == module_id)
        )
        return self._session.scalar(stmt)

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> bool:
        """Verifica se o docente possui atribuição ativa na turma informada."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def query_discrepancy_view(
        self,
        *,
        class_id: UUID | None = None,
        module_id: UUID | None = None,
        form_id: UUID | None = None,
        student_id: UUID | None = None,
        competency_ids: Sequence[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Consulta linhas consolidadas na view vw_self_eval_discrepancy (DB-038) com filtros opcionais."""
        self.ensure_discrepancy_view()
        vw = vw_self_eval_discrepancy_table
        stmt = select(vw)

        if class_id is not None:
            stmt = stmt.where(vw.c.class_id == class_id)
        if module_id is not None:
            stmt = stmt.where(vw.c.module_id == module_id)
        if form_id is not None:
            stmt = stmt.where(vw.c.form_id == form_id)
        if student_id is not None:
            stmt = stmt.where(vw.c.student_id == student_id)
        if competency_ids is not None:
            target_comps = list(dict.fromkeys(competency_ids))
            if not target_comps:
                return []
            stmt = stmt.where(vw.c.competency_id.in_(target_comps))

        stmt = stmt.order_by(
            vw.c.student_name.asc(),
            vw.c.competency_code.asc(),
            vw.c.submitted_at.desc(),
        )
        rows = self._session.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def list_skill_evidences_for_students_and_competencies(
        self,
        *,
        student_ids: Sequence[UUID],
        competency_ids: Sequence[UUID],
    ) -> dict[tuple[UUID, UUID], list[SkillEvidence]]:
        """Retorna mapa {(student_id, competency_id): [SkillEvidence, ...]} com submissão e tarefa prática carregadas."""
        unique_students = list(dict.fromkeys(student_ids))
        unique_comps = list(dict.fromkeys(competency_ids))
        if not unique_students or not unique_comps:
            return {}

        stmt = (
            select(SkillEvidence)
            .options(
                joinedload(SkillEvidence.source_submission).joinedload(
                    TaskSubmission.task
                ),
            )
            .where(
                SkillEvidence.student_id.in_(unique_students),
                SkillEvidence.competency_id.in_(unique_comps),
            )
            .order_by(
                SkillEvidence.recorded_at.asc(),
                SkillEvidence.id.asc(),
            )
        )
        evidences = list(self._session.scalars(stmt).all())
        grouped: dict[tuple[UUID, UUID], list[SkillEvidence]] = {}
        for ev in evidences:
            grouped.setdefault((ev.student_id, ev.competency_id), []).append(ev)
        return grouped

    def list_active_enrollments_by_class_and_students(
        self,
        *,
        class_ids: Sequence[UUID],
        student_ids: Sequence[UUID],
    ) -> dict[tuple[UUID, UUID], Enrollment]:
        """Retorna mapa {(class_id, student_id): Enrollment} para matrículas ativas."""
        unique_classes = list(dict.fromkeys(class_ids))
        unique_students = list(dict.fromkeys(student_ids))
        if not unique_classes or not unique_students:
            return {}

        stmt = select(Enrollment).where(
            Enrollment.class_id.in_(unique_classes),
            Enrollment.student_id.in_(unique_students),
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        records = list(self._session.scalars(stmt).all())
        return {(enr.class_id, enr.student_id): enr for enr in records}

    def upsert_explainable_diagnostic(
        self,
        *,
        student_id: UUID,
        class_id: UUID,
        module_id: UUID,
        competency_id: UUID,
        self_perceived_level: Decimal,
        teacher_verified_level: Decimal,
        discrepancy_gap: Decimal,
        diagnostic_type: DiagnosticType,
        explanation_text: str,
        limitations_note: str,
        recommended_action: str,
        generated_at: datetime | None = None,
    ) -> ExplainableDiagnostic:
        """Grava ou atualiza diagnóstico explicável em explainable_diagnostics (DB-035) sem efetuar commit imediato."""
        now = generated_at if generated_at is not None else _utc_now()
        stmt = (
            select(ExplainableDiagnostic)
            .where(
                ExplainableDiagnostic.student_id == student_id,
                ExplainableDiagnostic.class_id == class_id,
                ExplainableDiagnostic.module_id == module_id,
                ExplainableDiagnostic.competency_id == competency_id,
            )
            .order_by(ExplainableDiagnostic.generated_at.desc())
            .limit(1)
        )
        existing = self._session.scalar(stmt)
        if existing is None:
            entity = ExplainableDiagnostic(
                student_id=student_id,
                class_id=class_id,
                module_id=module_id,
                competency_id=competency_id,
                self_perceived_level=self_perceived_level,
                teacher_verified_level=teacher_verified_level,
                discrepancy_gap=discrepancy_gap,
                diagnostic_type=diagnostic_type,
                explanation_text=explanation_text,
                limitations_note=limitations_note,
                recommended_action=recommended_action,
                generated_at=now,
            )
            self._session.add(entity)
            self._session.flush()
            return entity

        existing.self_perceived_level = self_perceived_level
        existing.teacher_verified_level = teacher_verified_level
        existing.discrepancy_gap = discrepancy_gap
        existing.diagnostic_type = diagnostic_type
        existing.explanation_text = explanation_text
        existing.limitations_note = limitations_note
        existing.recommended_action = recommended_action
        existing.generated_at = now
        self._session.add(existing)
        self._session.flush()
        return existing

    def list_open_self_eval_gap_alerts(
        self,
        *,
        enrollment_id: UUID,
        module_id: UUID,
    ) -> list[AcademicAlert]:
        """Lista alertas abertos (ACTIVE ou ACKNOWLEDGED) da categoria SELF_EVAL_GAP para a matrícula e módulo."""
        stmt = (
            select(AcademicAlert)
            .where(
                AcademicAlert.enrollment_id == enrollment_id,
                AcademicAlert.module_id == module_id,
                AcademicAlert.alert_category == AlertCategory.SELF_EVAL_GAP,
                AcademicAlert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
            )
            .order_by(AcademicAlert.created_at.asc())
        )
        return list(self._session.scalars(stmt).all())

    def sync_self_eval_gap_alert_for_competency(
        self,
        *,
        student_id: UUID,
        enrollment_id: UUID,
        class_id: UUID,
        module_id: UUID,
        competency_id: UUID,
        should_trigger: bool,
        risk_level: RiskLevel,
        explainable_reason: str,
        metric_snapshot: dict[str, Any],
    ) -> AcademicAlert | None:
        """Cria, atualiza ou resolve automaticamente alerta SELF_EVAL_GAP para uma competência específica sem duplicidade."""
        open_alerts = self.list_open_self_eval_gap_alerts(
            enrollment_id=enrollment_id,
            module_id=module_id,
        )
        comp_id_str = str(competency_id)
        matching_alerts = [
            alert
            for alert in open_alerts
            if isinstance(alert.metric_snapshot, dict)
            and str(alert.metric_snapshot.get("competency_id")) == comp_id_str
        ]

        if should_trigger:
            encoded_snapshot: dict[str, Any] = jsonable_encoder(metric_snapshot)
            if matching_alerts:
                primary = matching_alerts[0]
                primary.risk_level = risk_level
                primary.explainable_reason = explainable_reason
                primary.metric_snapshot = encoded_snapshot
                self._session.add(primary)
                for dup in matching_alerts[1:]:
                    dup.status = AlertStatus.RESOLVED
                    dup.resolution_notes = (
                        "Alerta de discrepância de autoavaliação consolidado automaticamente."
                    )
                    self._session.add(dup)
                self._session.flush()
                return primary

            created = AcademicAlert(
                student_id=student_id,
                enrollment_id=enrollment_id,
                class_id=class_id,
                module_id=module_id,
                risk_level=risk_level,
                alert_category=AlertCategory.SELF_EVAL_GAP,
                explainable_reason=explainable_reason,
                metric_snapshot=encoded_snapshot,
                status=AlertStatus.ACTIVE,
            )
            self._session.add(created)
            self._session.flush()
            return created

        for stale in matching_alerts:
            stale.status = AlertStatus.RESOLVED
            stale.resolution_notes = (
                "Discrepância crítica entre autoavaliação e evidência prática normalizada após nova avaliação."
            )
            self._session.add(stale)
        if matching_alerts:
            self._session.flush()
        return None

    def commit(self) -> None:
        """Efetiva a transação no banco de dados."""
        self._session.commit()


def get_diagnostic_repository(session: DbSessionDep) -> DiagnosticRepository:
    """Provedor de injeção de dependência para DiagnosticRepository."""
    return DiagnosticRepository(session=session)


DiagnosticRepositoryDep = Annotated[
    DiagnosticRepository,
    Depends(get_diagnostic_repository),
]

__all__ = [
    "DiagnosticRepository",
    "DiagnosticRepositoryDep",
    "get_diagnostic_repository",
]
