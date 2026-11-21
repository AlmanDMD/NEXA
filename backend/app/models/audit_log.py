"""Modelo ORM SQLAlchemy 2.0 para a tabela de auditoria imutável (audit_logs - DB-009)."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Entidade de registro imutável de auditoria e rastreabilidade JSON (tabela 'audit_logs')."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "length(trim(action)) >= 2",
            name="chk_audit_logs_action_not_empty",
        ),
        CheckConstraint(
            "length(trim(entity)) >= 2",
            name="chk_audit_logs_entity_not_empty",
        ),
        CheckConstraint(
            "length(trim(entity_id)) >= 1",
            name="chk_audit_logs_entity_id_not_empty",
        ),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_entity_reference", "entity", "entity_id"),
        Index("idx_audit_logs_user_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    old_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    new_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="selectin",
    )

    @validates("action", "entity", "entity_id")
    def _validate_non_empty_metadata(self, key: str, value: str) -> str:
        """Garante que action/entity tenham ao menos 2 caracteres e entity_id ao menos 1."""
        if not isinstance(value, str):
            raise ValueError(f"O campo '{key}' do log de auditoria deve ser um texto válido.")
        cleaned = value.strip()
        min_len = 1 if key == "entity_id" else 2
        if len(cleaned) < min_len:
            raise ValueError(
                f"O campo '{key}' do log de auditoria deve ter ao menos {min_len} caractere(s)."
            )
        if len(cleaned) > 100:
            raise ValueError(
                f"O campo '{key}' do log de auditoria deve ter no máximo 100 caracteres."
            )
        return cleaned


__all__ = ["AuditLog"]
