"""Repositório SQLAlchemy 2.0 para Questionários e Ciclos de Autoavaliação de Competências (BE-035)."""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.competency import Competency
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.module_competency import ModuleCompetency
from app.models.self_assessment import SelfAssessmentForm, StudentSelfAssessment
from app.models.teacher_assignment import TeacherAssignment


class SelfAssessmentRepository:
    """Repositório SQLAlchemy 2.0 para persistência e consulta de formulários de autoavaliação."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_form_by_id(self, form_id: UUID) -> SelfAssessmentForm | None:
        """Busca um questionário de autoavaliação pelo UUID carregando módulo, competências, turma e respostas."""
        stmt = (
            select(SelfAssessmentForm)
            .options(
                joinedload(SelfAssessmentForm.module).joinedload(LearningModule.subject),
                joinedload(SelfAssessmentForm.module)
                .selectinload(LearningModule.module_competencies)
                .joinedload(ModuleCompetency.competency),
                joinedload(SelfAssessmentForm.academic_class),
                joinedload(SelfAssessmentForm.creator),
                selectinload(SelfAssessmentForm.responses),
            )
            .where(SelfAssessmentForm.id == form_id)
        )
        return self._session.scalar(stmt)

    def get_latest_form_by_class_and_module(
        self,
        *,
        class_id: UUID,
        module_id: UUID,
    ) -> SelfAssessmentForm | None:
        """Busca o formulário mais recente cadastrado para uma turma e módulo prático."""
        stmt = (
            select(SelfAssessmentForm)
            .options(
                joinedload(SelfAssessmentForm.module).joinedload(LearningModule.subject),
                joinedload(SelfAssessmentForm.module)
                .selectinload(LearningModule.module_competencies)
                .joinedload(ModuleCompetency.competency),
                joinedload(SelfAssessmentForm.academic_class),
                joinedload(SelfAssessmentForm.creator),
                selectinload(SelfAssessmentForm.responses),
            )
            .where(
                SelfAssessmentForm.class_id == class_id,
                SelfAssessmentForm.module_id == module_id,
            )
            .order_by(
                SelfAssessmentForm.created_at.desc(),
                SelfAssessmentForm.id.desc(),
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def get_module_with_competencies(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo prático pelo UUID carregando disciplina e competências associadas (module_competencies)."""
        stmt = (
            select(LearningModule)
            .options(
                joinedload(LearningModule.subject),
                selectinload(LearningModule.module_competencies).joinedload(
                    ModuleCompetency.competency
                ),
            )
            .where(LearningModule.id == module_id)
        )
        return self._session.scalar(stmt)

    def list_module_competencies(self, module_id: UUID) -> list[ModuleCompetency]:
        """Lista as competências associadas ao módulo ordenadas por código da competência."""
        stmt = (
            select(ModuleCompetency)
            .join(Competency, Competency.id == ModuleCompetency.competency_id)
            .options(joinedload(ModuleCompetency.competency))
            .where(ModuleCompetency.module_id == module_id)
            .order_by(
                Competency.code.asc(),
                Competency.title.asc(),
            )
        )
        return list(self._session.scalars(stmt).all())

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

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

    def get_teacher_assigned_subject_ids_for_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> set[UUID]:
        """Retorna os UUIDs das disciplinas em que o docente está alocado na turma informada."""
        stmt = select(TeacherAssignment.subject_id).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.class_id == class_id,
        )
        return set(self._session.scalars(stmt).all())

    def create_form(
        self,
        *,
        module_id: UUID,
        class_id: UUID,
        title: str,
        instructions: str | None,
        opens_at: datetime,
        closes_at: datetime,
        is_active: bool,
        created_by: UUID,
    ) -> SelfAssessmentForm:
        """Cria e persiste um novo questionário de autoavaliação em self_assessment_forms."""
        form = SelfAssessmentForm(
            module_id=module_id,
            class_id=class_id,
            title=title,
            instructions=instructions,
            opens_at=opens_at,
            closes_at=closes_at,
            is_active=is_active,
            created_by=created_by,
        )
        self._session.add(form)
        self._session.commit()
        self._session.refresh(form)
        return self.get_form_by_id(form.id) or form

    def update_form(
        self,
        form: SelfAssessmentForm,
        *,
        title: str | None = None,
        instructions: str | None = None,
        update_instructions: bool = False,
        opens_at: datetime | None = None,
        closes_at: datetime | None = None,
        is_active: bool | None = None,
    ) -> SelfAssessmentForm:
        """Atualiza janela temporal (reabertura de prazo), título, instruções ou status ativo do formulário."""
        if title is not None:
            form.title = title
        if update_instructions:
            form.instructions = instructions

        target_opens_at = opens_at if opens_at is not None else form.opens_at
        target_closes_at = closes_at if closes_at is not None else form.closes_at
        # Evita violar o validator intermediário quando opens_at e closes_at são deslocados juntos
        if target_opens_at >= target_closes_at:
            raise ValueError(
                "A data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at)."
            )

        # Limpa temporariamente para evitar erro de ordem quando novo opens_at >= antigo closes_at
        form.__dict__.pop("opens_at", None)
        form.__dict__.pop("closes_at", None)
        form.opens_at = target_opens_at
        form.closes_at = target_closes_at

        if is_active is not None:
            form.is_active = is_active

        self._session.add(form)
        self._session.commit()
        self._session.refresh(form)
        return self.get_form_by_id(form.id) or form

    def list_forms_by_class(
        self,
        class_id: UUID,
        *,
        module_id: UUID | None = None,
        is_active: bool | None = None,
        allowed_subject_ids: Sequence[UUID] | None = None,
    ) -> list[SelfAssessmentForm]:
        """Lista formulários de autoavaliação da turma carregando módulo, competências e respostas."""
        stmt = (
            select(SelfAssessmentForm)
            .join(LearningModule, LearningModule.id == SelfAssessmentForm.module_id)
            .options(
                joinedload(SelfAssessmentForm.module).joinedload(LearningModule.subject),
                joinedload(SelfAssessmentForm.module)
                .selectinload(LearningModule.module_competencies)
                .joinedload(ModuleCompetency.competency),
                joinedload(SelfAssessmentForm.academic_class),
                joinedload(SelfAssessmentForm.creator),
                selectinload(SelfAssessmentForm.responses),
            )
            .where(SelfAssessmentForm.class_id == class_id)
        )

        if module_id is not None:
            stmt = stmt.where(SelfAssessmentForm.module_id == module_id)

        if is_active is not None:
            stmt = stmt.where(SelfAssessmentForm.is_active == is_active)

        if allowed_subject_ids is not None:
            subject_ids_list = list(dict.fromkeys(allowed_subject_ids))
            if not subject_ids_list:
                return []
            stmt = stmt.where(LearningModule.subject_id.in_(subject_ids_list))

        stmt = stmt.order_by(
            SelfAssessmentForm.opens_at.asc(),
            SelfAssessmentForm.closes_at.asc(),
            LearningModule.order_index.asc(),
            SelfAssessmentForm.created_at.desc(),
            SelfAssessmentForm.id.asc(),
        )
        return list(self._session.scalars(stmt).unique().all())

    def list_student_responses_for_forms(
        self,
        *,
        student_id: UUID,
        form_ids: Sequence[UUID],
    ) -> dict[tuple[UUID, UUID], StudentSelfAssessment]:
        """Retorna mapa {(form_id, competency_id): StudentSelfAssessment} para o estudante e formulários informados."""
        unique_form_ids = list(dict.fromkeys(form_ids))
        if not unique_form_ids:
            return {}
        stmt = select(StudentSelfAssessment).where(
            StudentSelfAssessment.student_id == student_id,
            StudentSelfAssessment.form_id.in_(unique_form_ids),
        )
        records = list(self._session.scalars(stmt).all())
        return {(item.form_id, item.competency_id): item for item in records}


def get_self_assessment_repository(
    session: DbSessionDep,
) -> SelfAssessmentRepository:
    """Provedor de injeção de dependência para SelfAssessmentRepository."""
    return SelfAssessmentRepository(session=session)


SelfAssessmentRepositoryDep = Annotated[
    SelfAssessmentRepository,
    Depends(get_self_assessment_repository),
]

__all__ = [
    "SelfAssessmentRepository",
    "SelfAssessmentRepositoryDep",
    "get_self_assessment_repository",
]
