"""Modelo ORM SQLAlchemy 2.0 para a tabela de cursos técnicos SENAI (courses - DB-011)."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.subject import Subject


class Course(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de curso técnico ofertado pela unidade SENAI (tabela 'courses')."""

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("code", name="uq_courses_code"),
        CheckConstraint("total_hours > 0", name="chk_courses_total_hours_positive"),
        Index("idx_courses_code", "code"),
        Index("idx_courses_name", "name"),
        Index("idx_courses_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    total_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    classes: Mapped[list["AcademicClass"]] = relationship(
        "AcademicClass",
        back_populates="course",
        passive_deletes=True,
    )
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject",
        back_populates="course",
        passive_deletes=True,
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        """Normaliza o código SENAI em maiúsculas sem espaços laterais e valida comprimento."""
        if not isinstance(value, str):
            raise ValueError("O código do curso deve ser um texto válido.")
        normalized = value.strip().upper()
        if not (3 <= len(normalized) <= 30):
            raise ValueError("O código do curso deve ter entre 3 e 30 caracteres.")
        return normalized

    @validates("name")
    def _validate_name(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e valida comprimento do nome do curso."""
        if not isinstance(value, str):
            raise ValueError("O nome do curso deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError("O nome do curso deve ter entre 3 e 150 caracteres.")
        return normalized

    @validates("total_hours")
    def _validate_total_hours(self, _key: str, value: int) -> int:
        """Garante que a carga horária total seja um número inteiro estritamente positivo."""
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("A carga horária total deve ser um inteiro maior que zero.")
        return value


__all__ = ["Course"]
