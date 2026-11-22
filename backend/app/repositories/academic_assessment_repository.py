"""Repositório SQLAlchemy 2.0 para Avaliações Formativas (DB-027) e Lançamento de Notas (DB-028)."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_assessment import AcademicAssessment, StudentGrade
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.practical_task import PracticalTask, TaskSubmission
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import AssessmentType, EnrollmentStatus


class AcademicAssessmentRepository:
    """Repositório SQLAlchemy 2.0 para cadastro de avaliações formativas e lançamento de notas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, assessment_id: UUID) -> AcademicAssessment | None:
        """Busca uma avaliação formativa pelo UUID carregando turma, disciplina, módulo e notas."""
        stmt = (
            select(AcademicAssessment)
            .options(
                joinedload(AcademicAssessment.academic_class),
                joinedload(AcademicAssessment.subject),
                joinedload(AcademicAssessment.module),
                selectinload(AcademicAssessment.grades),
            )
            .where(AcademicAssessment.id == assessment_id)
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

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        stmt = select(Subject).where(Subject.id == subject_id)
        return self._session.scalar(stmt)

    def get_module_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo prático pelo UUID."""
        stmt = select(LearningModule).where(LearningModule.id == module_id)
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

    def get_teacher_assigned_class_subject_pairs(
        self,
        teacher_id: UUID,
    ) -> set[tuple[UUID, UUID]]:
        """Retorna pares (class_id, subject_id) nos quais o docente possui atribuição."""
        stmt = select(
            TeacherAssignment.class_id,
            TeacherAssignment.subject_id,
        ).where(TeacherAssignment.teacher_id == teacher_id)
        rows = self._session.execute(stmt).all()
        return {(row[0], row[1]) for row in rows}

    def create_assessment(
        self,
        *,
        class_id: UUID,
        subject_id: UUID,
        module_id: UUID | None,
        title: str,
        assessment_type: AssessmentType,
        weight: Decimal,
        application_date: date,
        max_grade: Decimal,
    ) -> AcademicAssessment:
        """Persiste uma nova avaliação formativa ou prova em academic_assessments."""
        assessment = AcademicAssessment(
            class_id=class_id,
            subject_id=subject_id,
            module_id=module_id,
            title=title,
            assessment_type=assessment_type,
            weight=weight,
            application_date=application_date,
            max_grade=max_grade,
        )
        self._session.add(assessment)
        self._session.commit()
        self._session.refresh(assessment)
        return self.get_by_id(assessment.id) or assessment

    def list_assessments(
        self,
        *,
        page: int,
        limit: int,
        class_id: UUID | None = None,
        subject_id: UUID | None = None,
        module_id: UUID | None = None,
        assessment_type: AssessmentType | None = None,
        allowed_class_ids: Sequence[UUID] | None = None,
    ) -> tuple[list[AcademicAssessment], int]:
        """Lista avaliações formativas ordenadas por application_date."""
        stmt = select(AcademicAssessment)

        if class_id is not None:
            stmt = stmt.where(AcademicAssessment.class_id == class_id)

        if subject_id is not None:
            stmt = stmt.where(AcademicAssessment.subject_id == subject_id)

        if module_id is not None:
            stmt = stmt.where(AcademicAssessment.module_id == module_id)

        if assessment_type is not None:
            stmt = stmt.where(AcademicAssessment.assessment_type == assessment_type)

        if allowed_class_ids is not None:
            allowed_list = list(dict.fromkeys(allowed_class_ids))
            if not allowed_list:
                return [], 0
            stmt = stmt.where(AcademicAssessment.class_id.in_(allowed_list))

        total = int(
            self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(
                joinedload(AcademicAssessment.academic_class),
                joinedload(AcademicAssessment.subject),
                joinedload(AcademicAssessment.module),
                selectinload(AcademicAssessment.grades),
            )
            .order_by(
                AcademicAssessment.application_date.asc(),
                AcademicAssessment.created_at.desc(),
                AcademicAssessment.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total

    def get_enrollments_by_class(self, class_id: UUID) -> dict[UUID, Enrollment]:
        """Retorna mapa {student_id: Enrollment} de todas as matrículas vinculadas à turma."""
        stmt = select(Enrollment).where(Enrollment.class_id == class_id)
        enrollments = list(self._session.scalars(stmt).all())
        return {enr.student_id: enr for enr in enrollments}

    def get_existing_grades_by_assessment(
        self,
        assessment_id: UUID,
    ) -> dict[UUID, StudentGrade]:
        """Retorna mapa {student_id: StudentGrade} das notas já lançadas para a avaliação."""
        stmt = select(StudentGrade).where(StudentGrade.assessment_id == assessment_id)
        grades = list(self._session.scalars(stmt).all())
        return {grade.student_id: grade for grade in grades}

    def list_grades_by_assessment(
        self,
        assessment_id: UUID,
    ) -> list[StudentGrade]:
        """Lista todas as notas lançadas para uma avaliação ordenadas por created_at."""
        stmt = (
            select(StudentGrade)
            .where(StudentGrade.assessment_id == assessment_id)
            .order_by(StudentGrade.created_at.asc(), StudentGrade.id.asc())
        )
        return list(self._session.scalars(stmt).all())

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

    def list_class_enrollments_with_students(
        self,
        class_id: UUID,
        *,
        student_id: UUID | None = None,
        exclude_dropped: bool = True,
    ) -> list[Enrollment]:
        """Lista matrículas da turma com dados do estudante e perfil carregados."""
        stmt = (
            select(Enrollment)
            .options(joinedload(Enrollment.student).selectinload(User.profile))
            .where(Enrollment.class_id == class_id)
        )
        if exclude_dropped:
            stmt = stmt.where(Enrollment.status != EnrollmentStatus.DROPPED)
        if student_id is not None:
            stmt = stmt.where(Enrollment.student_id == student_id)
        return list(self._session.scalars(stmt).unique().all())

    def list_course_subjects_with_modules(
        self,
        course_id: UUID,
        *,
        subject_id: UUID | None = None,
        allowed_subject_ids: Sequence[UUID] | None = None,
    ) -> list[Subject]:
        """Lista disciplinas do curso com seus módulos práticos carregados."""
        stmt = (
            select(Subject)
            .options(selectinload(Subject.learning_modules))
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
        """Lista todas as avaliações formativas da turma com suas notas (student_grades)."""
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
        """Lista todas as atividades práticas da turma com suas submissões (task_submissions)."""
        stmt = (
            select(PracticalTask)
            .options(selectinload(PracticalTask.submissions))
            .where(PracticalTask.class_id == class_id)
        )
        if module_id is not None:
            stmt = stmt.where(PracticalTask.module_id == module_id)
        return list(self._session.scalars(stmt).unique().all())


def get_academic_assessment_repository(
    session: DbSessionDep,
) -> AcademicAssessmentRepository:
    """Provedor de injeção de dependência para AcademicAssessmentRepository."""
    return AcademicAssessmentRepository(session=session)


AcademicAssessmentRepositoryDep = Annotated[
    AcademicAssessmentRepository,
    Depends(get_academic_assessment_repository),
]

__all__ = [
    "AcademicAssessmentRepository",
    "AcademicAssessmentRepositoryDep",
    "get_academic_assessment_repository",
]
