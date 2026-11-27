"""Repositório SQLAlchemy 2.0 de alta performance para Dashboard do Professor e Visão 360° (BE-031)."""

from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import case, inspect, select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_alert import (
    AcademicAlert,
    VW_STUDENT_360_PERFORMANCE_CREATE_SQL,
    VW_STUDENT_360_PERFORMANCE_NAME,
    vw_student_360_performance_table,
)
from app.models.academic_assessment import AcademicAssessment
from app.models.academic_class import AcademicClass
from app.models.audit_log import AuditLog
from app.models.class_lesson import (
    VW_MODULE_ATTENDANCE_RISK_CREATE_SQL,
    VW_MODULE_ATTENDANCE_RISK_NAME,
    vw_module_attendance_risk_table,
)
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.module_competency import ModuleCompetency
from app.models.practical_task import (
    PracticalTask,
    SkillEvidence,
    SubmissionEvaluation,
    TaskCriterion,
    TaskSubmission,
)
from app.models.student_milestone_history import StudentMilestoneHistory
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import AlertStatus, EnrollmentStatus


class DashboardRepository:
    """Repositório otimizado que consulta vw_student_360_performance (DB-036) e vw_module_attendance_risk (DB-037)."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._views_verified: bool = False

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def ensure_analytical_views(self) -> None:
        """Garante que as views vw_student_360_performance e vw_module_attendance_risk existam na conexão atual."""
        if self._views_verified:
            return
        bind = self._session.get_bind()
        if getattr(bind, "_nexa_analytical_views_ready", False):
            self._views_verified = True
            return
        view_names = {name.lower() for name in inspect(bind).get_view_names()}
        created_any = False
        if VW_MODULE_ATTENDANCE_RISK_NAME.lower() not in view_names:
            self._session.execute(text(VW_MODULE_ATTENDANCE_RISK_CREATE_SQL))
            created_any = True
        if VW_STUDENT_360_PERFORMANCE_NAME.lower() not in view_names:
            self._session.execute(text(VW_STUDENT_360_PERFORMANCE_CREATE_SQL))
            created_any = True
        if created_any:
            self._session.commit()
        try:
            setattr(bind, "_nexa_analytical_views_ready", True)
        except Exception:
            pass
        self._views_verified = True

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID carregando o curso associado."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        return self._session.scalar(select(Subject).where(Subject.id == subject_id))

    def get_module_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo prático pelo UUID."""
        return self._session.scalar(
            select(LearningModule).where(LearningModule.id == module_id)
        )

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo UUID com seu perfil carregado."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def get_teacher_assigned_subject_ids_for_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> set[UUID]:
        """Retorna os UUIDs das disciplinas que o docente leciona na turma informada."""
        stmt = select(TeacherAssignment.subject_id).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.class_id == class_id,
        )
        return set(self._session.scalars(stmt).all())

    def get_teacher_assigned_class_ids(
        self,
        teacher_id: UUID,
        *,
        class_ids: Sequence[UUID] | None = None,
    ) -> set[UUID]:
        """Retorna os UUIDs das turmas em que o docente possui atribuição ativa."""
        stmt = select(TeacherAssignment.class_id).where(
            TeacherAssignment.teacher_id == teacher_id
        )
        if class_ids is not None:
            target_ids = list(dict.fromkeys(class_ids))
            if not target_ids:
                return set()
            stmt = stmt.where(TeacherAssignment.class_id.in_(target_ids))
        return set(self._session.scalars(stmt).all())

    def list_student_enrollments(
        self,
        student_id: UUID,
        *,
        class_id: UUID | None = None,
    ) -> list[Enrollment]:
        """Lista matrículas do estudante priorizando status ACTIVE e matrícula mais recente."""
        stmt = (
            select(Enrollment)
            .options(
                joinedload(Enrollment.academic_class).joinedload(AcademicClass.course)
            )
            .where(Enrollment.student_id == student_id)
        )
        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)

        active_priority = case(
            (Enrollment.status == EnrollmentStatus.ACTIVE, 0),
            else_=1,
        )
        stmt = stmt.order_by(
            active_priority.asc(),
            Enrollment.enrollment_date.desc(),
            Enrollment.created_at.desc(),
            Enrollment.id.asc(),
        )
        return list(self._session.scalars(stmt).all())

    def query_class_student_360_view(
        self,
        class_id: UUID,
        *,
        exclude_dropped: bool = True,
    ) -> list[dict[str, Any]]:
        """Consulta a view vw_student_360_performance (DB-036) para todos os alunos da turma."""
        self.ensure_analytical_views()
        vw = vw_student_360_performance_table
        stmt = select(vw).where(vw.c.class_id == class_id)
        if exclude_dropped:
            stmt = stmt.where(vw.c.enrollment_status != EnrollmentStatus.DROPPED.value)
        stmt = stmt.order_by(vw.c.student_full_name.asc(), vw.c.student_email.asc())
        rows = self._session.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def query_student_360_view_by_enrollment(
        self,
        enrollment_id: UUID,
    ) -> dict[str, Any] | None:
        """Consulta a view vw_student_360_performance (DB-036) para uma matrícula específica."""
        self.ensure_analytical_views()
        vw = vw_student_360_performance_table
        stmt = select(vw).where(vw.c.enrollment_id == enrollment_id).limit(1)
        row = self._session.execute(stmt).mappings().first()
        return dict(row) if row is not None else None

    def query_class_module_attendance_view(
        self,
        class_id: UUID,
        *,
        subject_id: UUID | None = None,
        module_id: UUID | None = None,
        student_id: UUID | None = None,
        exclude_dropped: bool = True,
    ) -> list[dict[str, Any]]:
        """Consulta a view vw_module_attendance_risk (DB-037) para agregação modular rápida."""
        self.ensure_analytical_views()
        vw = vw_module_attendance_risk_table
        stmt = select(vw).where(vw.c.class_id == class_id)
        if exclude_dropped:
            stmt = stmt.where(vw.c.enrollment_status != EnrollmentStatus.DROPPED.value)
        if subject_id is not None:
            stmt = stmt.where(vw.c.subject_id == subject_id)
        if module_id is not None:
            stmt = stmt.where(vw.c.module_id == module_id)
        if student_id is not None:
            stmt = stmt.where(vw.c.student_id == student_id)
        stmt = stmt.order_by(
            vw.c.subject_code.asc(),
            vw.c.module_order_index.asc(),
            vw.c.module_title.asc(),
        )
        rows = self._session.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def list_course_subjects_with_modules_and_competencies(
        self,
        course_id: UUID,
        *,
        subject_id: UUID | None = None,
        allowed_subject_ids: Sequence[UUID] | None = None,
    ) -> list[Subject]:
        """Carrega disciplinas do curso com módulos e competências vinculadas em query única."""
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.learning_modules)
                .selectinload(LearningModule.module_competencies)
                .joinedload(ModuleCompetency.competency)
            )
            .where(Subject.course_id == course_id)
        )
        if subject_id is not None:
            stmt = stmt.where(Subject.id == subject_id)
        if allowed_subject_ids is not None:
            allowed_list = list(dict.fromkeys(allowed_subject_ids))
            if not allowed_list:
                return []
            stmt = stmt.where(Subject.id.in_(allowed_list))
        stmt = stmt.order_by(Subject.code.asc(), Subject.name.asc(), Subject.id.asc())
        return list(self._session.scalars(stmt).unique().all())

    def list_class_assessments_with_grades(
        self,
        class_id: UUID,
        *,
        subject_id: UUID | None = None,
        module_id: UUID | None = None,
    ) -> list[AcademicAssessment]:
        """Carrega avaliações formativas e notas da turma."""
        stmt = (
            select(AcademicAssessment)
            .options(selectinload(AcademicAssessment.grades))
            .where(AcademicAssessment.class_id == class_id)
        )
        if subject_id is not None:
            stmt = stmt.where(AcademicAssessment.subject_id == subject_id)
        if module_id is not None:
            stmt = stmt.where(AcademicAssessment.module_id == module_id)
        return list(self._session.scalars(stmt).unique().all())

    def list_class_practical_tasks_with_submissions(
        self,
        class_id: UUID,
        *,
        module_id: UUID | None = None,
    ) -> list[PracticalTask]:
        """Carrega tarefas práticas e submissões da turma."""
        stmt = (
            select(PracticalTask)
            .options(selectinload(PracticalTask.submissions))
            .where(PracticalTask.class_id == class_id)
        )
        if module_id is not None:
            stmt = stmt.where(PracticalTask.module_id == module_id)
        return list(self._session.scalars(stmt).unique().all())

    def list_skill_evidences_for_students(
        self,
        student_ids: Sequence[UUID],
    ) -> list[SkillEvidence]:
        """Carrega evidências práticas verificadas dos estudantes informados."""
        target_ids = list(dict.fromkeys(student_ids))
        if not target_ids:
            return []
        stmt = (
            select(SkillEvidence)
            .options(joinedload(SkillEvidence.competency))
            .where(SkillEvidence.student_id.in_(target_ids))
        )
        return list(self._session.scalars(stmt).all())

    def list_student_detailed_submissions(
        self,
        student_id: UUID,
        *,
        class_id: UUID,
    ) -> list[TaskSubmission]:
        """Carrega entregas práticas detalhadas do estudante na turma ordenadas por due_date."""
        stmt = (
            select(TaskSubmission)
            .join(PracticalTask, PracticalTask.id == TaskSubmission.task_id)
            .options(
                joinedload(TaskSubmission.task)
                .joinedload(PracticalTask.module)
                .joinedload(LearningModule.subject),
                joinedload(TaskSubmission.task).joinedload(PracticalTask.academic_class),
                joinedload(TaskSubmission.task)
                .selectinload(PracticalTask.criteria)
                .joinedload(TaskCriterion.competency),
                selectinload(TaskSubmission.evaluations)
                .joinedload(SubmissionEvaluation.criterion)
                .joinedload(TaskCriterion.competency),
            )
            .where(
                TaskSubmission.student_id == student_id,
                PracticalTask.class_id == class_id,
            )
            .order_by(PracticalTask.due_date.asc(), TaskSubmission.id.asc())
        )
        return list(self._session.scalars(stmt).unique().all())

    def list_student_active_alerts(
        self,
        student_id: UUID,
        *,
        class_id: UUID | None = None,
    ) -> list[AcademicAlert]:
        """Lista alertas acadêmicos ativos de um estudante ordenados por severidade e data."""
        stmt = (
            select(AcademicAlert)
            .options(joinedload(AcademicAlert.resolver).selectinload(User.profile))
            .where(
                AcademicAlert.student_id == student_id,
                AcademicAlert.status == AlertStatus.ACTIVE,
            )
        )
        if class_id is not None:
            stmt = stmt.where(AcademicAlert.class_id == class_id)

        severity_order = case(
            (AcademicAlert.risk_level == "CRITICAL", 1),
            (AcademicAlert.risk_level == "HIGH", 2),
            (AcademicAlert.risk_level == "MODERATE", 3),
            else_=4,
        )
        stmt = stmt.order_by(severity_order.asc(), AcademicAlert.created_at.desc())
        return list(self._session.scalars(stmt).unique().all())

    def list_student_alerts_history(
        self,
        student_id: UUID,
        *,
        class_id: UUID | None = None,
    ) -> list[AcademicAlert]:
        """Lista o histórico completo de alertas (ACTIVE, ACKNOWLEDGED e RESOLVED) do estudante para a Ficha 360° (BE-039)."""
        stmt = (
            select(AcademicAlert)
            .options(joinedload(AcademicAlert.resolver).selectinload(User.profile))
            .where(AcademicAlert.student_id == student_id)
        )
        if class_id is not None:
            stmt = stmt.where(AcademicAlert.class_id == class_id)
        stmt = stmt.order_by(AcademicAlert.created_at.desc(), AcademicAlert.id.asc())
        return list(self._session.scalars(stmt).unique().all())

    def list_audit_logs_for_alerts(
        self,
        alert_ids: Sequence[UUID],
    ) -> dict[UUID, list[AuditLog]]:
        """Busca em lote os logs de auditoria de intervenções pedagógicas para uma coleção de alertas (BE-039)."""
        unique_ids = [str(aid) for aid in dict.fromkeys(alert_ids)]
        if not unique_ids:
            return {}
        stmt = (
            select(AuditLog)
            .options(joinedload(AuditLog.user).selectinload(User.profile))
            .where(
                AuditLog.entity == "academic_alerts",
                AuditLog.entity_id.in_(unique_ids),
            )
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        )
        logs = list(self._session.scalars(stmt).unique().all())
        grouped: dict[UUID, list[AuditLog]] = {}
        for entry in logs:
            try:
                aid = UUID(entry.entity_id)
            except ValueError:
                continue
            grouped.setdefault(aid, []).append(entry)
        return grouped

    def list_student_milestones(
        self,
        student_id: UUID,
        *,
        enrollment_id: UUID | None = None,
    ) -> list[StudentMilestoneHistory]:
        """Lista a linha do tempo de marcos acadêmicos do estudante (student_milestone_history - DB-039)."""
        stmt = (
            select(StudentMilestoneHistory)
            .options(
                joinedload(StudentMilestoneHistory.module).joinedload(
                    LearningModule.subject
                )
            )
            .where(StudentMilestoneHistory.student_id == student_id)
        )
        if enrollment_id is not None:
            stmt = stmt.where(StudentMilestoneHistory.enrollment_id == enrollment_id)
        stmt = stmt.order_by(
            StudentMilestoneHistory.achieved_at.desc(),
            StudentMilestoneHistory.id.asc(),
        )
        return list(self._session.scalars(stmt).all())


def get_dashboard_repository(session: DbSessionDep) -> DashboardRepository:
    """Provedor de injeção de dependência para DashboardRepository."""
    return DashboardRepository(session=session)


DashboardRepositoryDep = Annotated[
    DashboardRepository,
    Depends(get_dashboard_repository),
]

__all__ = [
    "DashboardRepository",
    "DashboardRepositoryDep",
    "get_dashboard_repository",
]
