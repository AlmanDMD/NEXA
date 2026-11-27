"""Modelo ORM SQLAlchemy 2.0 para Observações Pedagógicas Restritas (pedagogical_notes - DB-043 / BE-045)."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.schemas.enums import NoteCategory, NoteVisibilityScope

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment
    from app.models.user import User


class PedagogicalNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de observação pedagógica de acesso restrito e conteúdo criptografado (tabela 'pedagogical_notes' - DB-043)."""

    __tablename__ = "pedagogical_notes"
    __table_args__ = (
        CheckConstraint(
            "length(trim(note_content)) >= 5",
            name="chk_pedagogical_notes_content_not_empty",
        ),
        CheckConstraint(
            "followup_date IS NULL OR requires_followup = true",
            name="chk_pedagogical_notes_followup_consistency",
        ),
        Index(
            "idx_pedagogical_notes_student_created",
            "student_id",
            "created_at",
        ),
        Index(
            "idx_pedagogical_notes_enrollment_scope",
            "enrollment_id",
            "visibility_scope",
        ),
        Index(
            "idx_pedagogical_notes_author_followup",
            "author_id",
            "requires_followup",
            "followup_date",
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    visibility_scope: Mapped[NoteVisibilityScope] = mapped_column(
        SAEnum(
            NoteVisibilityScope,
            name="note_visibility_scope_enum",
            native_enum=True,
        ),
        default=NoteVisibilityScope.PRIVATE_AUTHOR,
        server_default=NoteVisibilityScope.PRIVATE_AUTHOR.value,
        nullable=False,
    )
    category: Mapped[NoteCategory] = mapped_column(
        SAEnum(
            NoteCategory,
            name="note_category_enum",
            native_enum=True,
        ),
        nullable=False,
    )
    note_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    requires_followup: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    followup_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        lazy="joined",
        innerjoin=True,
    )
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        lazy="joined",
        innerjoin=True,
    )
    author: Mapped["User"] = relationship(
        "User",
        foreign_keys=[author_id],
        lazy="joined",
        innerjoin=True,
    )

    @validates("note_content")
    def _validate_note_content(self, _key: str, value: str) -> str:
        """Garante que o conteúdo (em texto ou cifrado) tenha pelo menos 5 caracteres não vazios."""
        if not isinstance(value, str):
            raise ValueError(
                "O conteúdo da observação pedagógica (note_content) deve ser um texto válido."
            )
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "O conteúdo da observação pedagógica (note_content) deve ter pelo menos 5 caracteres."
            )
        return normalized

    @validates("requires_followup")
    def _validate_requires_followup(self, _key: str, value: bool) -> bool:
        """Valida que requires_followup seja estritamente booleano."""
        if not isinstance(value, bool):
            raise ValueError(
                "O campo requires_followup deve ser um booleano válido."
            )
        return value

    @validates("followup_date")
    def _validate_followup_date(
        self,
        _key: str,
        value: date | None,
    ) -> date | None:
        """Garante que followup_date seja uma instância pura de date quando informado."""
        if value is None:
            return None
        if isinstance(value, datetime) or not isinstance(value, date):
            raise ValueError(
                "A data de acompanhamento (followup_date) deve ser um objeto date válido."
            )
        return value


__all__ = ["PedagogicalNote"]
