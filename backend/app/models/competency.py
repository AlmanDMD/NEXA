"""Modelo ORM SQLAlchemy 2.0 para a tabela de competências técnicas (competencies - DB-015)."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SAEnum,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.schemas.enums import CompetencyCategory

if TYPE_CHECKING:
    from app.models.module_competency import ModuleCompetency


class Competency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de competência ou habilidade técnica da taxonomia SENAI (tabela 'competencies')."""

    __tablename__ = "competencies"
    __table_args__ = (
        UniqueConstraint("code", name="uq_competencies_code"),
        Index("idx_competencies_code", "code"),
        Index("idx_competencies_category", "category"),
        Index("idx_competencies_title", "title"),
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    category: Mapped[CompetencyCategory] = mapped_column(
        SAEnum(CompetencyCategory, name="competency_category_enum", native_enum=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    module_competencies: Mapped[list["ModuleCompetency"]] = relationship(
        "ModuleCompetency",
        back_populates="competency",
        passive_deletes=True,
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        """Normaliza o código da competência em maiúsculas sem espaços laterais e valida comprimento."""
        if not isinstance(value, str):
            raise ValueError("O código da competência deve ser um texto válido.")
        normalized = value.strip().upper()
        if not (3 <= len(normalized) <= 50):
            raise ValueError("O código da competência deve ter entre 3 e 50 caracteres.")
        return normalized

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e valida comprimento do título da competência."""
        if not isinstance(value, str):
            raise ValueError("O título da competência deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError("O título da competência deve ter entre 3 e 150 caracteres.")
        return normalized

    @validates("description")
    def _validate_description(self, _key: str, value: str | None) -> str | None:
        """Normaliza a descrição opcional da competência convertendo texto vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("A descrição da competência deve ser um texto válido.")
        normalized = value.strip()
        return normalized or None


__all__ = ["Competency"]
