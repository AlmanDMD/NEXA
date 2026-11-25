"""Repositório SQLAlchemy 2.0 para o Motor de Identificação Precoce de Risco Acadêmico (BE-032)."""

from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.academic_alert import (
    AcademicAlert,
    VW_STUDENT_360_PERFORMANCE_CREATE_SQL,
    VW_STUDENT_360_PERFORMANCE_NAME,
    vw_student_360_performance_table,
)
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.schemas.enums import AlertCategory, AlertStatus, EnrollmentStatus, RiskLevel


class RiskEngineRepository:
    """Repositório responsável pela leitura de métricas 360° e upsert sem duplicidade em academic_alerts."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def ensure_student_360_view(self) -> None:
        """Garante que a view vw_student_360_performance (DB-036) esteja criada na conexão atual."""
        bind = self._session.get_bind()
        view_names = {name.lower() for name in inspect(bind).get_view_names()}
        if VW_STUDENT_360_PERFORMANCE_NAME.lower() not in view_names:
            self._session.execute(text(VW_STUDENT_360_PERFORMANCE_CREATE_SQL))
            self._session.commit()

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_enrollment_by_id(self, enrollment_id: UUID) -> Enrollment | None:
        """Busca matrícula pelo UUID com turma e curso carregados."""
        stmt = (
            select(Enrollment)
            .options(
                joinedload(Enrollment.academic_class).joinedload(AcademicClass.course)
            )
            .where(Enrollment.id == enrollment_id)
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

    def get_course_average_passing_score(self, course_id: UUID) -> list[LearningModule]:
        """Lista os módulos práticos do curso para cálculo da nota de corte de referência."""
        stmt = (
            select(LearningModule)
            .join(Subject, Subject.id == LearningModule.subject_id)
            .where(Subject.course_id == course_id)
        )
        return list(self._session.scalars(stmt).all())

    def query_student_360_metrics(
        self,
        *,
        class_id: UUID,
        student_ids: Sequence[UUID] | None = None,
        enrollment_ids: Sequence[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Consulta métricas consolidadas de matrículas ativas em vw_student_360_performance."""
        self.ensure_student_360_view()
        vw = vw_student_360_performance_table
        stmt = select(vw).where(
            vw.c.class_id == class_id,
            vw.c.enrollment_status == EnrollmentStatus.ACTIVE.value,
        )
        if student_ids is not None:
            target_students = list(dict.fromkeys(student_ids))
            if not target_students:
                return []
            stmt = stmt.where(vw.c.student_id.in_(target_students))
        if enrollment_ids is not None:
            target_enrollments = list(dict.fromkeys(enrollment_ids))
            if not target_enrollments:
                return []
            stmt = stmt.where(vw.c.enrollment_id.in_(target_enrollments))

        stmt = stmt.order_by(vw.c.student_full_name.asc(), vw.c.student_email.asc())
        rows = self._session.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def list_open_alerts_by_enrollments(
        self,
        enrollment_ids: Sequence[UUID],
    ) -> list[AcademicAlert]:
        """Lista alertas não resolvidos (ACTIVE ou ACKNOWLEDGED) das matrículas informadas."""
        target_ids = list(dict.fromkeys(enrollment_ids))
        if not target_ids:
            return []
        stmt = (
            select(AcademicAlert)
            .where(
                AcademicAlert.enrollment_id.in_(target_ids),
                AcademicAlert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
            )
            .order_by(AcademicAlert.created_at.asc())
        )
        return list(self._session.scalars(stmt).all())

    def create_alert(
        self,
        *,
        student_id: UUID,
        enrollment_id: UUID,
        class_id: UUID,
        module_id: UUID | None,
        risk_level: RiskLevel,
        alert_category: AlertCategory,
        explainable_reason: str,
        metric_snapshot: dict[str, Any],
    ) -> AcademicAlert:
        """Cria um novo alerta explicável em academic_alerts sem efetuar commit imediato."""
        encoded_snapshot: dict[str, Any] = jsonable_encoder(metric_snapshot)
        alert = AcademicAlert(
            student_id=student_id,
            enrollment_id=enrollment_id,
            class_id=class_id,
            module_id=module_id,
            risk_level=risk_level,
            alert_category=alert_category,
            explainable_reason=explainable_reason,
            metric_snapshot=encoded_snapshot,
            status=AlertStatus.ACTIVE,
        )
        self._session.add(alert)
        self._session.flush()
        return alert

    def update_open_alert(
        self,
        alert: AcademicAlert,
        *,
        risk_level: RiskLevel,
        explainable_reason: str,
        metric_snapshot: dict[str, Any],
    ) -> AcademicAlert:
        """Atualiza alerta aberto existente evitando criação de alertas duplicados."""
        encoded_snapshot: dict[str, Any] = jsonable_encoder(metric_snapshot)
        alert.risk_level = risk_level
        alert.explainable_reason = explainable_reason
        alert.metric_snapshot = encoded_snapshot
        self._session.add(alert)
        self._session.flush()
        return alert

    def auto_resolve_alert(
        self,
        alert: AcademicAlert,
        *,
        resolution_notes: str,
    ) -> AcademicAlert:
        """Encerra automaticamente um alerta cuja condição geradora deixou de existir."""
        alert.status = AlertStatus.RESOLVED
        alert.resolution_notes = resolution_notes
        self._session.add(alert)
        self._session.flush()
        return alert

    def commit(self) -> None:
        """Efetiva a transação no banco de dados."""
        self._session.commit()


def get_risk_engine_repository(session: DbSessionDep) -> RiskEngineRepository:
    """Provedor de injeção de dependência para RiskEngineRepository."""
    return RiskEngineRepository(session=session)


RiskEngineRepositoryDep = Annotated[
    RiskEngineRepository,
    Depends(get_risk_engine_repository),
]

__all__ = [
    "RiskEngineRepository",
    "RiskEngineRepositoryDep",
    "get_risk_engine_repository",
]
