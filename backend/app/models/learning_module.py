"""Modelo ORM SQLAlchemy 2.0 para a tabela de módulos de aprendizagem prática (learning_modules - DB-014)."""

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.module_competency import ModuleCompetency
    from app.models.subject import Subject

_DECIMAL_QUANTIZER = Decimal("0.01")


def _coerce_orm_decimal(value: Any, *, field_label: str) -> Decimal:
    """Converte Decimal/int/float finito/str para Decimal com 2 casas decimais no ORM."""
    if isinstance(value, bool):
        raise ValueError(f"{field_label} deve ser um número decimal válido.")

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, float):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field_label} deve ser um número decimal válido.")
        try:
            parsed = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"{field_label} deve ser um número decimal válido.") from exc
    else:
        raise ValueError(f"{field_label} deve ser um número decimal válido.")

    if not parsed.is_finite():
        raise ValueError(f"{field_label} deve ser um número decimal finito válido.")

    return parsed.quantize(_DECIMAL_QUANTIZER)


class LearningModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de módulo de aprendizagem prática SENAI vinculado a uma disciplina (tabela 'learning_modules')."""

    __tablename__ = "learning_modules"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "order_index",
            name="uq_learning_modules_subject_order",
        ),
        CheckConstraint("order_index > 0", name="chk_learning_modules_order_positive"),
        CheckConstraint(
            "practical_hours >= 0",
            name="chk_learning_modules_hours_non_negative",
        ),
        CheckConstraint("module_weight > 0", name="chk_learning_modules_weight_positive"),
        CheckConstraint(
            "passing_score >= 0 AND passing_score <= 10",
            name="chk_learning_modules_passing_score",
        ),
        Index("idx_learning_modules_subject_order", "subject_id", "order_index"),
        Index("idx_learning_modules_title", "title"),
    )

    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    practical_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    module_weight: Mapped[Decimal] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        default=Decimal("1.00"),
        nullable=False,
    )
    passing_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        default=Decimal("6.00"),
        nullable=False,
    )

    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="learning_modules",
        lazy="joined",
        innerjoin=True,
    )
    module_competencies: Mapped[list["ModuleCompetency"]] = relationship(
        "ModuleCompetency",
        back_populates="module",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e valida comprimento do título do módulo."""
        if not isinstance(value, str):
            raise ValueError("O título do módulo prático deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 120):
            raise ValueError("O título do módulo prático deve ter entre 3 e 120 caracteres.")
        return normalized

    @validates("order_index")
    def _validate_order_index(self, _key: str, value: int) -> int:
        """Garante que o índice de ordenação didática seja um inteiro estritamente positivo."""
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(
                "O índice de ordenação (order_index) deve ser um inteiro maior que zero."
            )
        return value

    @validates("practical_hours")
    def _validate_practical_hours(self, _key: str, value: int) -> int:
        """Garante que a carga horária prática seja um inteiro maior ou igual a zero."""
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(
                "A carga horária prática (practical_hours) deve ser um inteiro maior ou igual a zero."
            )
        return value

    @validates("description")
    def _validate_description(self, _key: str, value: str | None) -> str | None:
        """Normaliza a descrição opcional do módulo convertendo texto vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("A descrição do módulo prático deve ser um texto válido.")
        normalized = value.strip()
        return normalized or None

    @validates("passing_score")
    def _validate_passing_score(self, _key: str, value: Any) -> Decimal:
        """Valida que a nota de corte esteja entre 0.00 e 10.00."""
        parsed = _coerce_orm_decimal(value, field_label="A nota de corte (passing_score)")
        if not (Decimal("0.00") <= parsed <= Decimal("10.00")):
            raise ValueError("A nota de corte (passing_score) deve estar entre 0.00 e 10.00.")
        return parsed

    @validates("module_weight")
    def _validate_module_weight(self, _key: str, value: Any) -> Decimal:
        """Valida que o peso do módulo seja maior que 0.00 e no máximo 99.99."""
        parsed = _coerce_orm_decimal(value, field_label="O peso do módulo (module_weight)")
        if not (Decimal("0.00") < parsed <= Decimal("99.99")):
            raise ValueError(
                "O peso do módulo (module_weight) deve ser maior que 0.00 e no máximo 99.99."
            )
        return parsed


__all__ = ["LearningModule"]
