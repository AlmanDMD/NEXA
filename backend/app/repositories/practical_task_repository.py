"""Repositório SQLAlchemy 2.0 para Atividades Práticas, Rubricas e Submissões Iniciais (BE-024)."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.base import _utc_now
from app.models.competency import Competency
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
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import EnrollmentStatus, SubmissionStatus


def _build_ilike_pattern(term: str) -> str:
    """Escapa caracteres curinga (% e _) para busca parcial segura."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class PracticalTaskRepository:
    """Repositório SQLAlchemy 2.0 para cadastro e listagem de tarefas práticas de oficina."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, task_id: UUID) -> PracticalTask | None:
        """Busca uma atividade prática pelo UUID carregando módulo, turma, critérios e submissões."""
        stmt = (
            select(PracticalTask)
            .options(
                joinedload(PracticalTask.module).joinedload(LearningModule.subject),
                joinedload(PracticalTask.academic_class),
                selectinload(PracticalTask.criteria).joinedload(TaskCriterion.competency),
                selectinload(PracticalTask.submissions),
            )
            .where(PracticalTask.id == task_id)
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

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_competencies_by_ids(self, competency_ids: Sequence[UUID]) -> dict[UUID, Competency]:
        """Retorna mapa {competency_id: Competency} para os UUIDs informados."""
        unique_ids = list(dict.fromkeys(competency_ids))
        if not unique_ids:
            return {}
        stmt = select(Competency).where(Competency.id.in_(unique_ids))
        items = list(self._session.scalars(stmt).all())
        return {item.id: item for item in items}

    def is_teacher_assigned_to_class_and_subject(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
    ) -> bool:
        """Verifica se o docente possui atribuição ativa para a turma e disciplina."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.subject_id == subject_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def get_teacher_assigned_class_ids_for_subject(
        self,
        *,
        teacher_id: UUID,
        subject_id: UUID,
    ) -> set[UUID]:
        """Retorna os UUIDs das turmas em que o docente leciona a disciplina informada."""
        stmt = select(TeacherAssignment.class_id).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.subject_id == subject_id,
        )
        return set(self._session.scalars(stmt).all())

    def create_task_with_criteria_and_pending_submissions(
        self,
        *,
        module_id: UUID,
        class_id: UUID,
        title: str,
        description: str | None,
        blueprint_url: str | None,
        due_date: datetime,
        max_score: Decimal,
        is_mandatory: bool,
        criteria_items: Sequence[tuple[UUID, str, Decimal, int]],
    ) -> PracticalTask:
        """Cria tarefa prática, critérios (task_criteria) e entregas PENDING em transação única."""
        task = PracticalTask(
            module_id=module_id,
            class_id=class_id,
            title=title,
            description=description,
            blueprint_url=blueprint_url,
            due_date=due_date,
            max_score=max_score,
            is_mandatory=is_mandatory,
        )
        self._session.add(task)
        self._session.flush()

        existing_module_comp_ids = set(
            self._session.scalars(
                select(ModuleCompetency.competency_id).where(
                    ModuleCompetency.module_id == module_id
                )
            ).all()
        )
        new_module_links: list[ModuleCompetency] = []
        criteria_entities: list[TaskCriterion] = []

        for competency_id, criterion_name, weight, min_acceptable_level in criteria_items:
            criteria_entities.append(
                TaskCriterion(
                    task_id=task.id,
                    competency_id=competency_id,
                    criterion_name=criterion_name,
                    weight=weight,
                    min_acceptable_level=min_acceptable_level,
                )
            )
            if competency_id not in existing_module_comp_ids:
                new_module_links.append(
                    ModuleCompetency(
                        module_id=module_id,
                        competency_id=competency_id,
                        weight=weight,
                        required_level=min_acceptable_level,
                    )
                )
                existing_module_comp_ids.add(competency_id)

        if new_module_links:
            self._session.add_all(new_module_links)
        if criteria_entities:
            self._session.add_all(criteria_entities)

        active_enrollments = list(
            self._session.scalars(
                select(Enrollment).where(
                    Enrollment.class_id == class_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            ).all()
        )
        if active_enrollments:
            pending_submissions = [
                TaskSubmission(
                    task_id=task.id,
                    student_id=enrollment.student_id,
                    enrollment_id=enrollment.id,
                    status=SubmissionStatus.PENDING,
                )
                for enrollment in active_enrollments
            ]
            self._session.add_all(pending_submissions)

        self._session.commit()
        self._session.refresh(task)
        return self.get_by_id(task.id) or task

    def list_by_module(
        self,
        module_id: UUID,
        *,
        page: int,
        limit: int,
        class_id: UUID | None = None,
        allowed_class_ids: Sequence[UUID] | None = None,
        is_mandatory: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[PracticalTask], int]:
        """Lista atividades práticas do módulo ordenadas por due_date ascendente com filtros."""
        stmt = select(PracticalTask).where(PracticalTask.module_id == module_id)

        if class_id is not None:
            stmt = stmt.where(PracticalTask.class_id == class_id)

        if allowed_class_ids is not None:
            allowed_list = list(dict.fromkeys(allowed_class_ids))
            if not allowed_list:
                return [], 0
            stmt = stmt.where(PracticalTask.class_id.in_(allowed_list))

        if is_mandatory is not None:
            stmt = stmt.where(PracticalTask.is_mandatory == is_mandatory)

        if search:
            pattern = _build_ilike_pattern(search)
            stmt = stmt.where(
                or_(
                    PracticalTask.title.ilike(pattern, escape="\\"),
                    PracticalTask.description.ilike(pattern, escape="\\"),
                )
            )

        total = int(
            self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(
                joinedload(PracticalTask.module).joinedload(LearningModule.subject),
                joinedload(PracticalTask.academic_class),
                selectinload(PracticalTask.criteria).joinedload(TaskCriterion.competency),
                selectinload(PracticalTask.submissions),
            )
            .order_by(
                PracticalTask.due_date.asc(),
                PracticalTask.created_at.desc(),
                PracticalTask.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total

    def get_enrollment_by_class_and_student(
        self,
        *,
        class_id: UUID,
        student_id: UUID,
    ) -> Enrollment | None:
        """Busca a matrícula do estudante na turma informada."""
        stmt = select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == student_id,
        )
        return self._session.scalar(stmt)

    def get_submission_by_task_and_student(
        self,
        *,
        task_id: UUID,
        student_id: UUID,
    ) -> TaskSubmission | None:
        """Busca a submissão prática existente para a tarefa e estudante com avaliações e evidências."""
        stmt = (
            select(TaskSubmission)
            .options(
                selectinload(TaskSubmission.evaluations).joinedload(
                    SubmissionEvaluation.criterion
                ).joinedload(TaskCriterion.competency),
                selectinload(TaskSubmission.skill_evidences).joinedload(
                    SkillEvidence.competency
                ),
            )
            .where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.student_id == student_id,
            )
        )
        return self._session.scalar(stmt)

    def evaluate_task_submission_with_evidences(
        self,
        *,
        task: PracticalTask,
        enrollment: Enrollment,
        evaluator_id: UUID,
        final_task_score: Decimal,
        criterion_evaluations: Sequence[tuple[TaskCriterion, int, Decimal, str | None]],
        competency_verified_levels: Sequence[tuple[UUID, Decimal]],
        evidence_url: str | None = None,
        student_notes: str | None = None,
    ) -> TaskSubmission:
        """Executa upsert transacional de task_submissions, submission_evaluations e skill_evidences."""
        now = _utc_now()
        submission = self.get_submission_by_task_and_student(
            task_id=task.id,
            student_id=enrollment.student_id,
        )
        if submission is None:
            submission = TaskSubmission(
                task_id=task.id,
                student_id=enrollment.student_id,
                enrollment_id=enrollment.id,
                status=SubmissionStatus.EVALUATED,
                completed_at=now,
                evidence_url=evidence_url,
                student_notes=student_notes,
                final_task_score=final_task_score,
            )
            self._session.add(submission)
            self._session.flush()
            existing_evals_by_criterion: dict[UUID, SubmissionEvaluation] = {}
            existing_evidences_by_comp: dict[UUID, SkillEvidence] = {}
        else:
            submission.status = SubmissionStatus.EVALUATED
            submission.final_task_score = final_task_score
            if submission.completed_at is None:
                submission.completed_at = now
            if evidence_url is not None:
                submission.evidence_url = evidence_url
            if student_notes is not None:
                submission.student_notes = student_notes
            submission.updated_at = now
            self._session.add(submission)
            self._session.flush()
            existing_evals_by_criterion = {
                ev.criterion_id: ev for ev in submission.evaluations
            }
            existing_evidences_by_comp = {
                se.competency_id: se for se in submission.skill_evidences
            }

        for criterion, achieved_level, score_awarded, technical_feedback in criterion_evaluations:
            existing_eval = existing_evals_by_criterion.get(criterion.id)
            if existing_eval is not None:
                existing_eval.evaluator_id = evaluator_id
                existing_eval.achieved_level = achieved_level
                existing_eval.score_awarded = score_awarded
                existing_eval.technical_feedback = technical_feedback
                existing_eval.evaluated_at = now
                self._session.add(existing_eval)
            else:
                new_eval = SubmissionEvaluation(
                    submission_id=submission.id,
                    criterion_id=criterion.id,
                    evaluator_id=evaluator_id,
                    achieved_level=achieved_level,
                    score_awarded=score_awarded,
                    technical_feedback=technical_feedback,
                    evaluated_at=now,
                )
                self._session.add(new_eval)

        for competency_id, verified_level in competency_verified_levels:
            existing_evidence = existing_evidences_by_comp.get(competency_id)
            if existing_evidence is not None:
                existing_evidence.verified_level = verified_level
                existing_evidence.verified_by = evaluator_id
                existing_evidence.recorded_at = now
                self._session.add(existing_evidence)
            else:
                new_evidence = SkillEvidence(
                    student_id=enrollment.student_id,
                    competency_id=competency_id,
                    source_submission_id=submission.id,
                    verified_level=verified_level,
                    verified_by=evaluator_id,
                    recorded_at=now,
                )
                self._session.add(new_evidence)

        self._session.commit()
        self._session.refresh(submission)
        return (
            self.get_submission_by_task_and_student(
                task_id=task.id,
                student_id=enrollment.student_id,
            )
            or submission
        )

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo UUID com seu perfil carregado."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        stmt = select(Subject).where(Subject.id == subject_id)
        return self._session.scalar(stmt)

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> bool:
        """Verifica se o docente leciona ao menos uma disciplina na turma informada."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

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
        """Lista matrículas do estudante na(s) turma(s)."""
        stmt = (
            select(Enrollment)
            .options(joinedload(Enrollment.academic_class).joinedload(AcademicClass.course))
            .where(Enrollment.student_id == student_id)
        )
        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)
        stmt = stmt.order_by(
            Enrollment.enrollment_date.desc(),
            Enrollment.created_at.desc(),
            Enrollment.id.asc(),
        )
        return list(self._session.scalars(stmt).all())

    def list_student_task_submissions(
        self,
        student_id: UUID,
        *,
        allowed_class_ids: Sequence[UUID] | None = None,
        class_id: UUID | None = None,
        module_id: UUID | None = None,
        subject_id: UUID | None = None,
        is_mandatory: bool | None = None,
        search: str | None = None,
    ) -> list[TaskSubmission]:
        """Lista submissões práticas de um estudante cruzando com practical_tasks e learning_modules ordenadas por due_date."""
        stmt = (
            select(TaskSubmission)
            .join(PracticalTask, PracticalTask.id == TaskSubmission.task_id)
            .join(LearningModule, LearningModule.id == PracticalTask.module_id)
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
            .where(TaskSubmission.student_id == student_id)
        )

        if allowed_class_ids is not None:
            allowed_list = list(dict.fromkeys(allowed_class_ids))
            if not allowed_list:
                return []
            stmt = stmt.where(PracticalTask.class_id.in_(allowed_list))

        if class_id is not None:
            stmt = stmt.where(PracticalTask.class_id == class_id)

        if module_id is not None:
            stmt = stmt.where(PracticalTask.module_id == module_id)

        if subject_id is not None:
            stmt = stmt.where(LearningModule.subject_id == subject_id)

        if is_mandatory is not None:
            stmt = stmt.where(PracticalTask.is_mandatory == is_mandatory)

        if search:
            pattern = _build_ilike_pattern(search)
            stmt = stmt.where(
                or_(
                    PracticalTask.title.ilike(pattern, escape="\\"),
                    PracticalTask.description.ilike(pattern, escape="\\"),
                )
            )

        stmt = stmt.order_by(
            PracticalTask.due_date.asc(),
            PracticalTask.created_at.asc(),
            TaskSubmission.id.asc(),
        )
        return list(self._session.scalars(stmt).unique().all())


def get_practical_task_repository(session: DbSessionDep) -> PracticalTaskRepository:
    """Provedor de injeção de dependência para PracticalTaskRepository."""
    return PracticalTaskRepository(session=session)


PracticalTaskRepositoryDep = Annotated[
    PracticalTaskRepository,
    Depends(get_practical_task_repository),
]

__all__ = [
    "PracticalTaskRepository",
    "PracticalTaskRepositoryDep",
    "get_practical_task_repository",
]
