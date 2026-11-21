"""Repositório SQLAlchemy 2.0 para persistência e validação transacional de Matrículas (BE-016)."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enums import EnrollmentStatus


class EnrollmentRepository:
    """Repositório SQLAlchemy 2.0 para operações transacionais de matrícula em turmas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, enrollment_id: UUID) -> Enrollment | None:
        """Busca uma matrícula pelo UUID com carregamento imediato de estudante, perfil e turma."""
        stmt = (
            select(Enrollment)
            .options(
                joinedload(Enrollment.student).selectinload(User.profile),
                joinedload(Enrollment.academic_class).joinedload(AcademicClass.course),
            )
            .where(Enrollment.id == enrollment_id)
        )
        return self._session.scalar(stmt)

    def get_by_student_and_class(
        self,
        *,
        student_id: UUID,
        class_id: UUID,
    ) -> Enrollment | None:
        """Busca matrícula existente pelo par único (student_id, class_id)."""
        stmt = select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.class_id == class_id,
        )
        return self._session.scalar(stmt)

    def get_class_for_update(self, class_id: UUID) -> AcademicClass | None:
        """Carrega a turma aplicando bloqueio pessimista (SELECT FOR UPDATE) na transação."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
            .with_for_update()
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

    def count_active_enrollments_in_class(self, class_id: UUID) -> int:
        """Conta quantas matrículas com status ACTIVE existem na turma informada."""
        stmt = (
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        return int(self._session.scalar(stmt) or 0)

    def create_in_transaction(
        self,
        *,
        student_id: UUID,
        class_id: UUID,
        enrollment_date: date,
        status: EnrollmentStatus = EnrollmentStatus.ACTIVE,
    ) -> Enrollment:
        """Persiste uma nova matrícula dentro da transação ativa e efetua commit."""
        enrollment = Enrollment(
            student_id=student_id,
            class_id=class_id,
            enrollment_date=enrollment_date,
            status=status,
        )
        self._session.add(enrollment)
        self._session.flush()
        self._session.commit()
        self._session.refresh(enrollment)
        return self.get_by_id(enrollment.id) or enrollment

    def rollback(self) -> None:
        """Reverte a transação ativa em caso de conflito ou falha de integridade."""
        self._session.rollback()


def get_enrollment_repository(session: DbSessionDep) -> EnrollmentRepository:
    """Provedor de injeção de dependência para EnrollmentRepository."""
    return EnrollmentRepository(session=session)


EnrollmentRepositoryDep = Annotated[
    EnrollmentRepository,
    Depends(get_enrollment_repository),
]

__all__ = [
    "EnrollmentRepository",
    "EnrollmentRepositoryDep",
    "get_enrollment_repository",
]
