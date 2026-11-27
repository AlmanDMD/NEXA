"""Modelo ORM SQLAlchemy 2.0 para Mural Oficial de Avisos da Turma (class_announcements - DB-041)."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now
from app.schemas.enums import AnnouncementPriority

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.subject import Subject
    from app.models.user import User


def _normalize_utc_datetime(value: datetime, *, field_label: str) -> datetime:
    """Garante que o valor seja um datetime válido normalizado em UTC."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field_label} deve ser um objeto datetime válido.")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ClassAnnouncement(Base, UUIDPrimaryKeyMixin):
    """Entidade de comunicado oficial publicado no mural da turma (tabela 'class_announcements' - DB-041)."""

    __tablename__ = "class_announcements"
    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) >= 3",
            name="chk_announcements_title_not_empty",
        ),
        CheckConstraint(
            "length(trim(content)) >= 5",
            name="chk_announcements_content_not_empty",
        ),
        CheckConstraint(
            "expires_at IS NULL OR expires_at > published_at",
            name="chk_announcements_expiration",
        ),
        Index(
            "idx_class_announcements_feed",
            "class_id",
            "is_pinned",
            "published_at",
        ),
        Index(
            "idx_class_announcements_priority",
            "class_id",
            "priority",
            "published_at",
        ),
        Index("idx_class_announcements_author", "author_id"),
    )

    class_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    priority: Mapped[AnnouncementPriority] = mapped_column(
        SAEnum(
            AnnouncementPriority,
            name="announcement_priority_enum",
            native_enum=True,
        ),
        default=AnnouncementPriority.NORMAL,
        server_default=AnnouncementPriority.NORMAL.value,
        nullable=False,
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        lazy="joined",
        innerjoin=True,
    )
    subject: Mapped["Subject | None"] = relationship(
        "Subject",
        lazy="joined",
    )
    author: Mapped["User"] = relationship(
        "User",
        foreign_keys=[author_id],
        lazy="joined",
        innerjoin=True,
    )

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras e valida que o título do aviso tenha entre 3 e 150 caracteres."""
        if not isinstance(value, str):
            raise ValueError("O título do aviso (title) deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError(
                "O título do aviso (title) deve ter entre 3 e 150 caracteres."
            )
        return normalized

    @validates("content")
    def _validate_content(self, _key: str, value: str) -> str:
        """Valida que o conteúdo do aviso tenha pelo menos 5 caracteres não vazios."""
        if not isinstance(value, str):
            raise ValueError("O conteúdo do aviso (content) deve ser um texto válido.")
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "O conteúdo do aviso (content) deve ter pelo menos 5 caracteres."
            )
        return normalized

    @validates("published_at")
    def _validate_published_at(self, _key: str, value: datetime) -> datetime:
        """Normaliza published_at em UTC e garante coerência com expires_at quando já definido."""
        normalized = _normalize_utc_datetime(
            value,
            field_label="A data/hora de publicação (published_at)",
        )
        current_expires = getattr(self, "expires_at", None)
        if current_expires is not None:
            expires_utc = _normalize_utc_datetime(
                current_expires,
                field_label="A data/hora de expiração (expires_at)",
            )
            if expires_utc <= normalized:
                raise ValueError(
                    "A data/hora de expiração (expires_at) deve ser posterior à publicação (published_at)."
                )
        return normalized

    @validates("expires_at")
    def _validate_expires_at(
        self,
        _key: str,
        value: datetime | None,
    ) -> datetime | None:
        """Normaliza expires_at opcional em UTC e garante que seja posterior a published_at."""
        if value is None:
            return None
        normalized = _normalize_utc_datetime(
            value,
            field_label="A data/hora de expiração (expires_at)",
        )
        current_published = getattr(self, "published_at", None)
        if current_published is not None:
            published_utc = _normalize_utc_datetime(
                current_published,
                field_label="A data/hora de publicação (published_at)",
            )
            if normalized <= published_utc:
                raise ValueError(
                    "A data/hora de expiração (expires_at) deve ser posterior à publicação (published_at)."
                )
        return normalized


__all__ = ["ClassAnnouncement"]
