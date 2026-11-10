"""Configuração declarativa base do SQLAlchemy 2.0 com suporte a tipagem estrita."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utc_now() -> datetime:
    """Retorna o timestamp atual em UTC."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Classe base declarativa para todos os modelos ORM SQLAlchemy 2.0 do projeto NEXA."""


class TimestampMixin:
    """Mixin com colunas de auditoria temporal (created_at e updated_at)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        server_default=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Mixin com chave primária UUID v4."""

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


__all__ = ["Base", "TimestampMixin", "UUIDPrimaryKeyMixin"]
