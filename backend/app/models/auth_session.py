"""Modelo ORM SQLAlchemy 2.0 para a tabela auth_sessions (DB-008)."""

from datetime import datetime
import re
from typing import TYPE_CHECKING, Final
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now

if TYPE_CHECKING:
    from app.models.user import User

_SHA256_HEX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-f0-9]{64}$")


class AuthSession(Base, UUIDPrimaryKeyMixin):
    """Entidade de controle de sessões autenticadas e Refresh Tokens (tabela 'auth_sessions')."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint("refresh_token_hash", name="uq_auth_sessions_token_hash"),
        CheckConstraint("expires_at > created_at", name="chk_auth_sessions_expiration"),
        Index("idx_auth_sessions_refresh_token_hash", "refresh_token_hash"),
        Index("idx_auth_sessions_is_revoked", "is_revoked"),
        Index("idx_auth_sessions_user_revoked_expires", "user_id", "is_revoked", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="auth_sessions",
    )

    @validates("refresh_token_hash")
    def _validate_refresh_token_hash(self, _key: str, value: str) -> str:
        """Garante que apenas um digest SHA-256 hexadecimal (64 chars) seja persistido."""
        if not isinstance(value, str):
            raise ValueError("O hash do refresh token deve ser uma string hexadecimal SHA-256.")
        normalized = value.strip().lower()
        if not _SHA256_HEX_PATTERN.match(normalized):
            raise ValueError(
                "O refresh_token_hash deve ser um hash SHA-256 hexadecimal de 64 caracteres."
            )
        return normalized


__all__ = ["AuthSession"]

