"""Repositório SQLAlchemy 2.0 para Observações Pedagógicas Restritas (pedagogical_notes - DB-043 / BE-045)."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.pedagogical_note import PedagogicalNote
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import (
    ClassStatus,
    EnrollmentStatus,
    NoteCategory,
    NoteVisibilityScope,
    UserRole,
)


class PedagogicalNoteRepository:
    """Repositório responsável pela persistência e consultas filtradas por visibility_scope em pedagogical_notes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(
        self,
        note_id: UUID,
        *,
        populate_existing: bool = False,
    ) -> PedagogicalNote | None:
        """Busca uma observação pedagógica pelo UUID carregando estudante, matrícula/turma e autor."""
        stmt = (
            select(PedagogicalNote)
            .options(
                joinedload(PedagogicalNote.student).selectinload(User.profile),
                joinedload(PedagogicalNote.enrollment).joinedload(
                    Enrollment.academic_class
                ),
                joinedload(PedagogicalNote.author).selectinload(User.profile),
            )
            .where(PedagogicalNote.id == note_id)
        )
        if populate_existing:
            stmt = stmt.execution_options(populate_existing=True)
        return self._session.scalar(stmt)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo UUID carregando seu perfil."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def get_enrollment_by_id(self, enrollment_id: UUID) -> Enrollment | None:
        """Busca uma matrícula pelo UUID carregando a turma acadêmica."""
        stmt = (
            select(Enrollment)
            .options(joinedload(Enrollment.academic_class))
            .where(Enrollment.id == enrollment_id)
        )
        return self._session.scalar(stmt)

    def resolve_student_enrollment(
        self,
        *,
        student_id: UUID,
        class_id: UUID | None = None,
        teacher_class_ids: set[UUID] | None = None,
    ) -> Enrollment | None:
        """Localiza a matrícula do estudante priorizando matrícula ativa e turmas permitidas."""
        stmt = (
            select(Enrollment)
            .join(AcademicClass, Enrollment.class_id == AcademicClass.id)
            .options(joinedload(Enrollment.academic_class))
            .where(Enrollment.student_id == student_id)
        )
        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)
        elif teacher_class_ids:
            stmt = stmt.where(Enrollment.class_id.in_(list(teacher_class_ids)))

        stmt = stmt.order_by(
            (Enrollment.status == EnrollmentStatus.ACTIVE).desc(),
            (AcademicClass.status == ClassStatus.ACTIVE).desc(),
            Enrollment.enrollment_date.desc(),
            Enrollment.created_at.desc(),
        ).limit(1)
        return self._session.scalar(stmt)

    def list_student_class_ids(self, student_id: UUID) -> set[UUID]:
        """Retorna os UUIDs das turmas em que o estudante possui matrícula."""
        stmt = select(Enrollment.class_id).where(Enrollment.student_id == student_id)
        return set(self._session.scalars(stmt).all())

    def list_teacher_assigned_class_ids(self, teacher_id: UUID) -> set[UUID]:
        """Retorna os UUIDs das turmas em que o professor possui alocação ativa."""
        stmt = select(TeacherAssignment.class_id).where(
            TeacherAssignment.teacher_id == teacher_id
        )
        return set(self._session.scalars(stmt).all())

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

    def create_in_transaction(
        self,
        *,
        student_id: UUID,
        enrollment_id: UUID,
        author_id: UUID,
        visibility_scope: NoteVisibilityScope,
        category: NoteCategory,
        encrypted_note_content: str,
        requires_followup: bool,
        followup_date: date | None,
    ) -> PedagogicalNote:
        """Adiciona uma nova observação pedagógica cifrada à sessão e realiza flush para obter o UUID."""
        entity = PedagogicalNote(
            student_id=student_id,
            enrollment_id=enrollment_id,
            author_id=author_id,
            visibility_scope=visibility_scope,
            category=category,
            note_content=encrypted_note_content,
            requires_followup=requires_followup,
            followup_date=followup_date,
        )
        self._session.add(entity)
        self._session.flush()
        return entity

    def commit_and_get(self, note_id: UUID) -> PedagogicalNote | None:
        """Comita a transação ativa e retorna a observação pedagógica completa."""
        self._session.commit()
        return self.get_by_id(note_id, populate_existing=True)

    def list_student_notes_for_viewer(
        self,
        *,
        student_id: UUID,
        viewer_id: UUID,
        viewer_role: UserRole,
        page: int,
        limit: int,
        class_id: UUID | None = None,
        enrollment_id: UUID | None = None,
        visibility_scope: NoteVisibilityScope | None = None,
        category: NoteCategory | None = None,
        requires_followup: bool | None = None,
    ) -> tuple[list[PedagogicalNote], int]:
        """Consulta observações pedagógicas de um estudante aplicando rigorosamente o visibility_scope (DB-043 / BE-045).

        Regras de escopo:
        - PRIVATE_AUTHOR: somente o próprio autor (author_id == viewer_id) ou ADMIN.
        - TEACHERS_AND_COORD: TEACHER (da turma do aluno), COORDINATOR e ADMIN.
        - COORDINATION_ONLY: somente COORDINATOR, ADMIN (ou o próprio autor caso tenha registrado).
        """
        stmt = (
            select(PedagogicalNote)
            .join(Enrollment, PedagogicalNote.enrollment_id == Enrollment.id)
            .where(PedagogicalNote.student_id == student_id)
        )

        if viewer_role == UserRole.TEACHER:
            stmt = stmt.where(
                or_(
                    PedagogicalNote.visibility_scope
                    == NoteVisibilityScope.TEACHERS_AND_COORD,
                    PedagogicalNote.author_id == viewer_id,
                )
            )
        elif viewer_role == UserRole.COORDINATOR:
            stmt = stmt.where(
                or_(
                    PedagogicalNote.visibility_scope.in_(
                        [
                            NoteVisibilityScope.TEACHERS_AND_COORD,
                            NoteVisibilityScope.COORDINATION_ONLY,
                        ]
                    ),
                    PedagogicalNote.author_id == viewer_id,
                )
            )
        elif viewer_role != UserRole.ADMIN:
            return [], 0

        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)

        if enrollment_id is not None:
            stmt = stmt.where(PedagogicalNote.enrollment_id == enrollment_id)

        if visibility_scope is not None:
            stmt = stmt.where(PedagogicalNote.visibility_scope == visibility_scope)

        if category is not None:
            stmt = stmt.where(PedagogicalNote.category == category)

        if requires_followup is not None:
            stmt = stmt.where(PedagogicalNote.requires_followup.is_(requires_followup))

        total = int(
            self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(
                joinedload(PedagogicalNote.student).selectinload(User.profile),
                joinedload(PedagogicalNote.enrollment).joinedload(
                    Enrollment.academic_class
                ),
                joinedload(PedagogicalNote.author).selectinload(User.profile),
            )
            .order_by(
                PedagogicalNote.created_at.desc(),
                PedagogicalNote.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total


def get_pedagogical_note_repository(
    session: DbSessionDep,
) -> PedagogicalNoteRepository:
    """Provedor de injeção de dependência para PedagogicalNoteRepository."""
    return PedagogicalNoteRepository(session=session)


PedagogicalNoteRepositoryDep = Annotated[
    PedagogicalNoteRepository,
    Depends(get_pedagogical_note_repository),
]

__all__ = [
    "PedagogicalNoteRepository",
    "PedagogicalNoteRepositoryDep",
    "get_pedagogical_note_repository",
]
