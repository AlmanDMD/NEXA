"""Repositório SQLAlchemy 2.0 para persistência e consultas de Turmas Acadêmicas (BE-012)."""

from collections.abc import Sequence
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import (
    String,
    Uuid,
    cast,
    column,
    exists,
    func,
    inspect,
    literal,
    or_,
    select,
    table,
)
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.base import _utc_now
from app.models.course import Course
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift


class AcademicClassRepository:
    """Repositório SQLAlchemy 2.0 para operações de criação, consulta e status de turmas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID com carregamento imediato do curso vinculado."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_by_code_and_period(self, code: str, period: str) -> AcademicClass | None:
        """Busca uma turma pelo par único (code, period) com comparação case-insensitive."""
        normalized_code = code.strip().upper()
        normalized_period = period.strip().upper()
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(
                func.upper(AcademicClass.code) == normalized_code,
                func.upper(AcademicClass.period) == normalized_period,
            )
        )
        return self._session.scalar(stmt)

    def list_classes(
        self,
        *,
        page: int,
        limit: int,
        course_id: UUID | None = None,
        period: str | None = None,
        shift: Shift | None = None,
        status: ClassStatus | None = None,
        search: str | None = None,
        teacher_id: UUID | None = None,
    ) -> tuple[list[AcademicClass], int]:
        """Lista turmas acadêmicas paginadas com filtros de curso, período, turno, status e busca."""
        stmt = select(AcademicClass)

        if teacher_id is not None:
            bind = self._session.get_bind()
            if not inspect(bind).has_table("teacher_assignments"):
                return [], 0

            ta_tbl = table(
                "teacher_assignments",
                column("class_id", Uuid(as_uuid=True)),
                column("teacher_id", Uuid(as_uuid=True)),
            )
            stmt = stmt.where(
                exists(
                    select(literal(1))
                    .select_from(ta_tbl)
                    .where(
                        ta_tbl.c.class_id == AcademicClass.id,
                        ta_tbl.c.teacher_id == teacher_id,
                    )
                )
            )

        if course_id is not None:
            stmt = stmt.where(AcademicClass.course_id == course_id)

        if period:
            stmt = stmt.where(func.upper(AcademicClass.period) == period.strip().upper())

        if shift is not None:
            stmt = stmt.where(AcademicClass.shift == shift)

        if status is not None:
            stmt = stmt.where(AcademicClass.status == status)

        if search:
            stmt = stmt.join(AcademicClass.course)
            escaped = (
                search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            stmt = stmt.where(
                or_(
                    AcademicClass.code.ilike(pattern, escape="\\"),
                    AcademicClass.period.ilike(pattern, escape="\\"),
                    Course.code.ilike(pattern, escape="\\"),
                    Course.name.ilike(pattern, escape="\\"),
                )
            )

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(joinedload(AcademicClass.course))
            .order_by(AcademicClass.period.desc(), AcademicClass.code.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total

    def create(
        self,
        *,
        course_id: UUID,
        code: str,
        period: str,
        shift: Shift,
        max_students: int,
        status: ClassStatus,
        start_date: date,
        end_date: date,
    ) -> AcademicClass:
        """Persiste uma nova turma acadêmica no banco de dados."""
        academic_class = AcademicClass(
            course_id=course_id,
            code=code,
            period=period,
            shift=shift,
            max_students=max_students,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
        self._session.add(academic_class)
        self._session.commit()
        self._session.refresh(academic_class)
        return self.get_by_id(academic_class.id) or academic_class

    def update_status(
        self,
        academic_class: AcademicClass,
        *,
        status: ClassStatus,
    ) -> AcademicClass:
        """Atualiza o status da turma acadêmica e registra timestamp updated_at."""
        academic_class.status = status
        academic_class.updated_at = _utc_now()
        self._session.add(academic_class)
        self._session.commit()
        self._session.refresh(academic_class)
        return self.get_by_id(academic_class.id) or academic_class

    def count_active_enrollments(self, class_id: UUID) -> int:
        """Conta quantos alunos possuem matrícula ACTIVE na turma informada."""
        bind = self._session.get_bind()
        if not inspect(bind).has_table("enrollments"):
            return 0

        enrollments_tbl = table(
            "enrollments",
            column("class_id", Uuid(as_uuid=True)),
            column("status", String),
        )
        stmt = (
            select(func.count())
            .select_from(enrollments_tbl)
            .where(
                enrollments_tbl.c.class_id == class_id,
                cast(enrollments_tbl.c.status, String) == EnrollmentStatus.ACTIVE.value,
            )
        )
        return int(self._session.scalar(stmt) or 0)

    def count_active_enrollments_by_class_ids(
        self,
        class_ids: Sequence[UUID],
    ) -> dict[UUID, int]:
        """Agrega em lote a contagem de matrículas ACTIVE por turma para evitar queries N+1."""
        if not class_ids:
            return {}

        bind = self._session.get_bind()
        if not inspect(bind).has_table("enrollments"):
            return {}

        enrollments_tbl = table(
            "enrollments",
            column("class_id", Uuid(as_uuid=True)),
            column("status", String),
        )
        stmt = (
            select(enrollments_tbl.c.class_id, func.count())
            .select_from(enrollments_tbl)
            .where(
                enrollments_tbl.c.class_id.in_(list(class_ids)),
                cast(enrollments_tbl.c.status, String) == EnrollmentStatus.ACTIVE.value,
            )
            .group_by(enrollments_tbl.c.class_id)
        )
        rows = self._session.execute(stmt).all()
        return {row[0]: int(row[1]) for row in rows}

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> bool:
        """Verifica se o docente possui alocação registrada para a turma em teacher_assignments."""
        bind = self._session.get_bind()
        if not inspect(bind).has_table("teacher_assignments"):
            return False

        ta_tbl = table(
            "teacher_assignments",
            column("teacher_id", Uuid(as_uuid=True)),
            column("class_id", Uuid(as_uuid=True)),
        )
        stmt = (
            select(literal(1))
            .select_from(ta_tbl)
            .where(
                ta_tbl.c.teacher_id == teacher_id,
                ta_tbl.c.class_id == class_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None


def get_academic_class_repository(session: DbSessionDep) -> AcademicClassRepository:
    """Provedor de injeção de dependência para AcademicClassRepository."""
    return AcademicClassRepository(session=session)


AcademicClassRepositoryDep = Annotated[
    AcademicClassRepository,
    Depends(get_academic_class_repository),
]

__all__ = [
    "AcademicClassRepository",
    "AcademicClassRepositoryDep",
    "get_academic_class_repository",
]
