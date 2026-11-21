"""Repositório SQLAlchemy 2.0 para persistência e consultas de Alocação Docente (BE-018)."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User


class TeacherAssignmentRepository:
    """Repositório SQLAlchemy 2.0 para criação e verificação de vínculos docentes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, assignment_id: UUID) -> TeacherAssignment | None:
        """Busca uma alocação docente pelo UUID carregando docente, perfil, turma e disciplina."""
        stmt = (
            select(TeacherAssignment)
            .options(
                joinedload(TeacherAssignment.teacher).selectinload(User.profile),
                joinedload(TeacherAssignment.academic_class).joinedload(AcademicClass.course),
                joinedload(TeacherAssignment.subject),
            )
            .where(TeacherAssignment.id == assignment_id)
        )
        return self._session.scalar(stmt)

    def get_by_composite_key(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
    ) -> TeacherAssignment | None:
        """Busca atribuição existente pela tripla única (teacher_id, class_id, subject_id)."""
        stmt = select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.class_id == class_id,
            TeacherAssignment.subject_id == subject_id,
        )
        return self._session.scalar(stmt)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário e seu perfil institucional pelo UUID."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID com curso vinculado."""
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

    def create(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        is_main_teacher: bool = True,
    ) -> TeacherAssignment:
        """Persiste uma nova alocação docente no banco e retorna o registro hidratado."""
        assignment = TeacherAssignment(
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            is_main_teacher=is_main_teacher,
        )
        self._session.add(assignment)
        self._session.flush()
        self._session.commit()
        self._session.refresh(assignment)
        return self.get_by_id(assignment.id) or assignment

    def rollback(self) -> None:
        """Reverte a transação ativa em caso de conflito ou falha de integridade."""
        self._session.rollback()


def get_teacher_assignment_repository(
    session: DbSessionDep,
) -> TeacherAssignmentRepository:
    """Provedor de injeção de dependência para TeacherAssignmentRepository."""
    return TeacherAssignmentRepository(session=session)


TeacherAssignmentRepositoryDep = Annotated[
    TeacherAssignmentRepository,
    Depends(get_teacher_assignment_repository),
]

__all__ = [
    "TeacherAssignmentRepository",
    "TeacherAssignmentRepositoryDep",
    "get_teacher_assignment_repository",
]
