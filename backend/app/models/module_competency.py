"""Modelo ORM SQLAlchemy 2.0 para a tabela associativa módulo-competência (module_competencies - DB-016)."""

from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin
from app.models.learning_module import _coerce_orm_decimal

if TYPE_CHECKING:
    from app.models.competency import Competency
    from app.models.learning_module import LearningModule


class ModuleCompetency(Base, TimestampMixin):
    """Entidade associativa N:M entre módulos práticos e competências técnicas (tabela 'module_competencies')."""

    __tablename__ = "module_competencies"
    __table_args__ = (
        CheckConstraint(
            "weight > 0 AND weight <= 9.99",
            name="chk_module_competencies_weight",
        ),
        CheckConstraint(
            "required_level >= 1 AND required_level <= 5",
            name="chk_module_competencies_level",
        ),
        Index("idx_module_competencies_competency", "competency_id"),
        Index("idx_module_competencies_module_level", "module_id", "required_level"),
    )

    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        default=Decimal("1.00"),
        nullable=False,
    )
    required_level: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    module: Mapped["LearningModule"] = relationship(
        "LearningModule",
        back_populates="module_competencies",
        lazy="joined",
        innerjoin=True,
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="module_competencies",
        lazy="joined",
        innerjoin=True,
    )

    @validates("weight")
    def _validate_weight(self, _key: str, value: Any) -> Decimal:
        """Valida que o peso da competência no módulo seja maior que 0.00 e no máximo 9.99."""
        parsed = _coerce_orm_decimal(value, field_label="O peso da competência (weight)")
        if not (Decimal("0.00") < parsed <= Decimal("9.99")):
            raise ValueError(
                "O peso da competência (weight) deve ser maior que 0.00 e no máximo 9.99."
            )
        return parsed

    @validates("required_level")
    def _validate_required_level(self, _key: str, value: int) -> int:
        """Garante que o nível requerido de proficiência seja um inteiro entre 1 e 5."""
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
            raise ValueError("O nível requerido (required_level) deve ser um inteiro entre 1 e 5.")
        return value


__all__ = ["ModuleCompetency"]
