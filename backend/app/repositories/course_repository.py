"""Repositório SQLAlchemy 2.0 para persistência e consultas de Cursos Técnicos (BE-011)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import (
    String,
    Uuid,
    cast,
    column,
    func,
    inspect,
    literal,
    or_,
    select,
    table,
)
from sqlalchemy.orm import Session

from app.core.database import DbSessionDep
from app.models.base import _utc_now
from app.models.course import Course
from app.schemas.enums import ClassStatus


class CourseRepository:
    """Repositório SQLAlchemy 2.0 para operações CRUD e consulta de cursos técnicos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, course_id: UUID) -> Course | None:
        """Busca um curso técnico pelo seu identificador UUID."""
        stmt = select(Course).where(Course.id == course_id)
        return self._session.scalar(stmt)

    def get_by_code(self, code: str) -> Course | None:
        """Busca um curso técnico pelo código SENAI (comparação case-insensitive)."""
        normalized_code = code.strip().upper()
        stmt = select(Course).where(func.upper(Course.code) == normalized_code)
        return self._session.scalar(stmt)

    def list_courses(
        self,
        *,
        page: int,
        limit: int,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Course], int]:
        """Lista cursos técnicos com paginação, busca textual e filtro por status ativo."""
        stmt = select(Course)

        if is_active is not None:
            stmt = stmt.where(Course.is_active.is_(is_active))

        if search:
            escaped = (
                search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            stmt = stmt.where(
                or_(
                    Course.code.ilike(pattern, escape="\\"),
                    Course.name.ilike(pattern, escape="\\"),
                    Course.description.ilike(pattern, escape="\\"),
                )
            )

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.order_by(Course.name.asc(), Course.code.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).all())
        return items, total

    def create(
        self,
        *,
        code: str,
        name: str,
        description: str | None,
        total_hours: int,
        is_active: bool = True,
    ) -> Course:
        """Persiste um novo curso técnico no banco de dados."""
        course = Course(
            code=code,
            name=name,
            description=description,
            total_hours=total_hours,
            is_active=is_active,
        )
        self._session.add(course)
        self._session.commit()
        self._session.refresh(course)
        return course

    def update(self, course: Course, *, updates: dict[str, Any]) -> Course:
        """Atualiza atributos de um curso técnico existente e registra updated_at."""
        for field, value in updates.items():
            setattr(course, field, value)
        course.updated_at = _utc_now()
        self._session.add(course)
        self._session.commit()
        self._session.refresh(course)
        return course

    def deactivate(self, course: Course) -> Course:
        """Realiza a desativação lógica (soft delete) definindo is_active=False."""
        course.is_active = False
        course.updated_at = _utc_now()
        self._session.add(course)
        self._session.commit()
        self._session.refresh(course)
        return course

    def has_active_classes(self, course_id: UUID) -> bool:
        """Verifica se existem turmas ativas vinculadas ao curso na tabela 'classes'."""
        bind = self._session.get_bind()
        if not inspect(bind).has_table("classes"):
            return False

        classes_tbl = table(
            "classes",
            column("course_id", Uuid(as_uuid=True)),
            column("status", String),
        )
        stmt = (
            select(literal(1))
            .select_from(classes_tbl)
            .where(
                classes_tbl.c.course_id == course_id,
                cast(classes_tbl.c.status, String) == ClassStatus.ACTIVE.value,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None


def get_course_repository(session: DbSessionDep) -> CourseRepository:
    """Provedor de injeção de dependência para CourseRepository."""
    return CourseRepository(session=session)


CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]

__all__ = [
    "CourseRepository",
    "CourseRepositoryDep",
    "get_course_repository",
]
