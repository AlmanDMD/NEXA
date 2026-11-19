"""Repositório SQLAlchemy 2.0 para persistência e consultas de Disciplinas Técnicas (BE-013)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.base import _utc_now
from app.models.subject import Subject


class SubjectRepository:
    """Repositório SQLAlchemy 2.0 para operações CRUD e consulta de disciplinas técnicas."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina pelo seu identificador UUID com carregamento do curso vinculado."""
        stmt = (
            select(Subject)
            .options(joinedload(Subject.course))
            .where(Subject.id == subject_id)
        )
        return self._session.scalar(stmt)

    def get_by_course_and_code(self, course_id: UUID, code: str) -> Subject | None:
        """Busca uma disciplina pelo par único (course_id, code) com comparação case-insensitive."""
        normalized_code = code.strip().upper()
        stmt = (
            select(Subject)
            .options(joinedload(Subject.course))
            .where(
                Subject.course_id == course_id,
                func.upper(Subject.code) == normalized_code,
            )
        )
        return self._session.scalar(stmt)

    def list_subjects(
        self,
        *,
        page: int,
        limit: int,
        course_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Subject], int]:
        """Lista disciplinas paginadas com filtros por curso, status ativo e busca textual."""
        stmt = select(Subject)

        if course_id is not None:
            stmt = stmt.where(Subject.course_id == course_id)

        if is_active is not None:
            stmt = stmt.where(Subject.is_active.is_(is_active))

        if search:
            escaped = (
                search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            stmt = stmt.where(
                or_(
                    Subject.code.ilike(pattern, escape="\\"),
                    Subject.name.ilike(pattern, escape="\\"),
                    Subject.syllabus.ilike(pattern, escape="\\"),
                )
            )

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(joinedload(Subject.course))
            .order_by(Subject.name.asc(), Subject.code.asc())
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
        name: str,
        workload_hours: int,
        syllabus: str | None = None,
        is_active: bool = True,
    ) -> Subject:
        """Persiste uma nova disciplina técnica vinculada a um curso no banco de dados."""
        subject = Subject(
            course_id=course_id,
            code=code,
            name=name,
            workload_hours=workload_hours,
            syllabus=syllabus,
            is_active=is_active,
        )
        self._session.add(subject)
        self._session.commit()
        self._session.refresh(subject)
        return self.get_by_id(subject.id) or subject

    def update(self, subject: Subject, *, updates: dict[str, Any]) -> Subject:
        """Atualiza atributos de uma disciplina existente, atualiza updated_at e recarrega curso."""
        for field, value in updates.items():
            setattr(subject, field, value)
        subject.updated_at = _utc_now()
        self._session.add(subject)
        self._session.commit()
        self._session.refresh(subject)
        self._session.expire(subject, ["course"])
        stmt = (
            select(Subject)
            .options(joinedload(Subject.course))
            .execution_options(populate_existing=True)
            .where(Subject.id == subject.id)
        )
        return self._session.scalar(stmt) or subject


def get_subject_repository(session: DbSessionDep) -> SubjectRepository:
    """Provedor de injeção de dependência para SubjectRepository."""
    return SubjectRepository(session=session)


SubjectRepositoryDep = Annotated[SubjectRepository, Depends(get_subject_repository)]

__all__ = [
    "SubjectRepository",
    "SubjectRepositoryDep",
    "get_subject_repository",
]
