"""Repositório SQLAlchemy 2.0 para Solicitações de Apoio Confidenciais (help_requests - DB-042 / BE-043)."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.help_request import ChatMessage, HelpRequest
from app.models.learning_module import LearningModule
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import (
    ClassStatus,
    EnrollmentStatus,
    HelpRequestCategory,
    HelpRequestStatus,
)


class HelpRequestRepository:
    """Repositório responsável pela persistência e consultas isoladas em help_requests e chat_messages."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, help_request_id: UUID) -> HelpRequest | None:
        """Busca uma solicitação de apoio pelo UUID carregando aluno, matrícula/turma, disciplina, módulo, docente e mensagens."""
        stmt = (
            select(HelpRequest)
            .options(
                joinedload(HelpRequest.student).selectinload(User.profile),
                joinedload(HelpRequest.enrollment).joinedload(
                    Enrollment.academic_class
                ),
                joinedload(HelpRequest.subject),
                joinedload(HelpRequest.module),
                joinedload(HelpRequest.assigned_teacher).selectinload(User.profile),
                selectinload(HelpRequest.messages)
                .joinedload(ChatMessage.sender)
                .selectinload(User.profile),
            )
            .where(HelpRequest.id == help_request_id)
        )
        return self._session.scalar(stmt)

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        return self._session.scalar(
            select(AcademicClass).where(AcademicClass.id == class_id)
        )

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        return self._session.scalar(select(Subject).where(Subject.id == subject_id))

    def get_module_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo de aprendizagem prática pelo UUID."""
        return self._session.scalar(
            select(LearningModule).where(LearningModule.id == module_id)
        )

    def get_student_active_enrollment_for_course(
        self,
        *,
        student_id: UUID,
        course_id: UUID,
    ) -> Enrollment | None:
        """Localiza a matrícula ativa do estudante em uma turma do curso da disciplina informada."""
        stmt = (
            select(Enrollment)
            .join(AcademicClass, Enrollment.class_id == AcademicClass.id)
            .options(joinedload(Enrollment.academic_class))
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
                AcademicClass.course_id == course_id,
            )
            .order_by(
                (AcademicClass.status == ClassStatus.ACTIVE).desc(),
                Enrollment.enrollment_date.desc(),
                Enrollment.created_at.desc(),
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def has_any_active_enrollment(self, student_id: UUID) -> bool:
        """Verifica se o estudante possui ao menos uma matrícula ativa em qualquer turma."""
        stmt = (
            select(Enrollment.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def resolve_main_teacher_id_for_class_and_subject(
        self,
        *,
        class_id: UUID,
        subject_id: UUID,
    ) -> UUID | None:
        """Localiza o professor titular (is_main_teacher=True preferencialmente) da disciplina na turma do aluno."""
        stmt = (
            select(TeacherAssignment.teacher_id)
            .join(User, TeacherAssignment.teacher_id == User.id)
            .where(
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.subject_id == subject_id,
                User.is_active.is_(True),
            )
            .order_by(
                TeacherAssignment.is_main_teacher.desc(),
                TeacherAssignment.assigned_at.asc(),
                TeacherAssignment.id.asc(),
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def list_teacher_assignments_pairs(
        self,
        teacher_id: UUID,
    ) -> list[tuple[UUID, UUID]]:
        """Retorna os pares (class_id, subject_id) atribuídos ao professor."""
        stmt = select(
            TeacherAssignment.class_id,
            TeacherAssignment.subject_id,
        ).where(TeacherAssignment.teacher_id == teacher_id)
        return [(row[0], row[1]) for row in self._session.execute(stmt).all()]

    def create(
        self,
        *,
        student_id: UUID,
        enrollment_id: UUID,
        subject_id: UUID,
        module_id: UUID | None,
        assigned_teacher_id: UUID | None,
        category: HelpRequestCategory,
        subject_title: str,
        description: str,
        is_confidential: bool,
    ) -> HelpRequest:
        """Cria e persiste uma nova solicitação confidencial de apoio em help_requests."""
        entity = HelpRequest(
            student_id=student_id,
            enrollment_id=enrollment_id,
            subject_id=subject_id,
            module_id=module_id,
            assigned_teacher_id=assigned_teacher_id,
            category=category,
            subject_title=subject_title,
            description=description,
            is_confidential=is_confidential,
            status=HelpRequestStatus.OPEN,
        )
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return self.get_by_id(entity.id) or entity

    def list_help_requests(
        self,
        *,
        page: int,
        limit: int,
        student_id_scope: UUID | None = None,
        teacher_scope_id: UUID | None = None,
        teacher_class_subject_pairs: list[tuple[UUID, UUID]] | None = None,
        class_id: UUID | None = None,
        subject_id: UUID | None = None,
        module_id: UUID | None = None,
        category: HelpRequestCategory | None = None,
        status: HelpRequestStatus | None = None,
    ) -> tuple[list[HelpRequest], int]:
        """Lista solicitações de apoio aplicando isolamento estrito por papel e filtros opcionais (BE-043)."""
        stmt = select(HelpRequest).join(
            Enrollment, HelpRequest.enrollment_id == Enrollment.id
        )

        # Proteção anti-exposição para STUDENT: filtra estritamente pelo próprio student_id
        if student_id_scope is not None:
            stmt = stmt.where(HelpRequest.student_id == student_id_scope)

        # Escopo para TEACHER: solicitações direcionadas a ele OU das disciplinas que leciona nas suas turmas
        if teacher_scope_id is not None:
            pair_clauses = [
                and_(
                    Enrollment.class_id == cls_id,
                    HelpRequest.subject_id == subj_id,
                )
                for cls_id, subj_id in (teacher_class_subject_pairs or [])
            ]
            stmt = stmt.where(
                or_(
                    HelpRequest.assigned_teacher_id == teacher_scope_id,
                    *pair_clauses,
                )
            )

        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)

        if subject_id is not None:
            stmt = stmt.where(HelpRequest.subject_id == subject_id)

        if module_id is not None:
            stmt = stmt.where(HelpRequest.module_id == module_id)

        if category is not None:
            stmt = stmt.where(HelpRequest.category == category)

        if status is not None:
            stmt = stmt.where(HelpRequest.status == status)

        total = int(
            self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(
                joinedload(HelpRequest.student).selectinload(User.profile),
                joinedload(HelpRequest.enrollment).joinedload(
                    Enrollment.academic_class
                ),
                joinedload(HelpRequest.subject),
                joinedload(HelpRequest.module),
                joinedload(HelpRequest.assigned_teacher).selectinload(User.profile),
                selectinload(HelpRequest.messages)
                .joinedload(ChatMessage.sender)
                .selectinload(User.profile),
            )
            .order_by(
                HelpRequest.created_at.desc(),
                HelpRequest.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total


def get_help_request_repository(
    session: DbSessionDep,
) -> HelpRequestRepository:
    """Provedor de injeção de dependência para HelpRequestRepository."""
    return HelpRequestRepository(session=session)


HelpRequestRepositoryDep = Annotated[
    HelpRequestRepository,
    Depends(get_help_request_repository),
]

__all__ = [
    "HelpRequestRepository",
    "HelpRequestRepositoryDep",
    "get_help_request_repository",
]
