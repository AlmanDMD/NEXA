"""Modelos ORM SQLAlchemy 2.0 para Solicitações de Apoio Confidenciais (help_requests - DB-042) e Mensagens Internas (chat_messages - DB-044)."""

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

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, _utc_now
from app.schemas.enums import HelpRequestCategory, HelpRequestStatus

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.subject import Subject
    from app.models.user import User


def _normalize_utc_datetime(value: datetime, *, field_label: str) -> datetime:
    """Garante que o valor seja um datetime válido normalizado em UTC."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field_label} deve ser um objeto datetime válido.")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class HelpRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de solicitação confidencial de apoio pedagógico e mentoria (tabela 'help_requests' - DB-042)."""

    __tablename__ = "help_requests"
    __table_args__ = (
        CheckConstraint(
            "length(trim(subject_title)) >= 3",
            name="chk_help_requests_title_not_empty",
        ),
        CheckConstraint(
            "length(trim(description)) >= 10",
            name="chk_help_requests_desc_not_empty",
        ),
        CheckConstraint(
            "(status = 'CLOSED' AND closed_at IS NOT NULL) OR (status <> 'CLOSED' AND closed_at IS NULL)",
            name="chk_help_requests_closed_at_consistency",
        ),
        Index(
            "idx_help_requests_teacher_status",
            "assigned_teacher_id",
            "status",
        ),
        Index(
            "idx_help_requests_student_status",
            "student_id",
            "status",
        ),
        Index(
            "idx_help_requests_enrollment_status",
            "enrollment_id",
            "status",
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
    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    assigned_teacher_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    category: Mapped[HelpRequestCategory] = mapped_column(
        SAEnum(
            HelpRequestCategory,
            name="help_request_category_enum",
            native_enum=True,
        ),
        nullable=False,
    )
    subject_title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_confidential: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    status: Mapped[HelpRequestStatus] = mapped_column(
        SAEnum(
            HelpRequestStatus,
            name="help_request_status_enum",
            native_enum=True,
        ),
        default=HelpRequestStatus.OPEN,
        server_default=HelpRequestStatus.OPEN.value,
        nullable=False,
    )
    resolution_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
    subject: Mapped["Subject"] = relationship(
        "Subject",
        lazy="joined",
        innerjoin=True,
    )
    module: Mapped["LearningModule | None"] = relationship(
        "LearningModule",
        lazy="joined",
    )
    assigned_teacher: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_teacher_id],
        lazy="joined",
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="help_request",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.sent_at.asc()",
    )

    @validates("subject_title")
    def _validate_subject_title(self, _key: str, value: str) -> str:
        """Remove espaços laterais e garante que subject_title tenha entre 3 e 150 caracteres."""
        if not isinstance(value, str):
            raise ValueError(
                "O assunto da solicitação (subject_title) deve ser um texto válido."
            )
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError(
                "O assunto da solicitação (subject_title) deve ter entre 3 e 150 caracteres."
            )
        return normalized

    @validates("description")
    def _validate_description(self, _key: str, value: str) -> str:
        """Valida que a descrição da dificuldade tenha pelo menos 10 caracteres úteis."""
        if not isinstance(value, str):
            raise ValueError(
                "A descrição da solicitação (description) deve ser um texto válido."
            )
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError(
                "A descrição da solicitação (description) deve ter pelo menos 10 caracteres."
            )
        return normalized

    @validates("is_confidential")
    def _validate_is_confidential(self, _key: str, value: bool) -> bool:
        """Garante que is_confidential seja estritamente booleano."""
        if not isinstance(value, bool):
            raise ValueError("O campo is_confidential deve ser um booleano válido.")
        return value

    @validates("resolution_summary")
    def _validate_resolution_summary(
        self,
        _key: str,
        value: str | None,
    ) -> str | None:
        """Normaliza o resumo de resolução opcional convertendo texto vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(
                "O resumo da resolução (resolution_summary) deve ser um texto válido."
            )
        normalized = value.strip()
        return normalized or None

    @validates("closed_at")
    def _validate_closed_at(
        self,
        _key: str,
        value: datetime | None,
    ) -> datetime | None:
        """Normaliza closed_at opcional para UTC."""
        if value is None:
            return None
        return _normalize_utc_datetime(
            value,
            field_label="A data/hora de encerramento (closed_at)",
        )


class ChatMessage(Base, UUIDPrimaryKeyMixin):
    """Entidade de mensagem interna em solicitação confidencial de apoio (tabela 'chat_messages' - DB-044)."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(
            "length(trim(message_body)) >= 1",
            name="chk_chat_messages_body_not_empty",
        ),
        CheckConstraint(
            "(is_read = false AND read_at IS NULL) OR (is_read = true AND read_at IS NOT NULL)",
            name="chk_chat_messages_read_consistency",
        ),
        CheckConstraint(
            "read_at IS NULL OR read_at >= sent_at",
            name="chk_chat_messages_read_after_sent",
        ),
        Index(
            "idx_chat_messages_request_sent",
            "help_request_id",
            "sent_at",
        ),
        Index(
            "idx_chat_messages_unread",
            "help_request_id",
            "sender_id",
        ),
    )

    help_request_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("help_requests.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    message_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    help_request: Mapped["HelpRequest"] = relationship(
        "HelpRequest",
        back_populates="messages",
    )
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        lazy="joined",
        innerjoin=True,
    )

    @validates("message_body")
    def _validate_message_body(self, _key: str, value: str) -> str:
        """Valida que o corpo da mensagem não seja vazio."""
        if not isinstance(value, str):
            raise ValueError(
                "O conteúdo da mensagem (message_body) deve ser um texto válido."
            )
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "O conteúdo da mensagem (message_body) não pode ser vazio."
            )
        return normalized

    @validates("sent_at")
    def _validate_sent_at(self, _key: str, value: datetime) -> datetime:
        """Normaliza sent_at para UTC."""
        return _normalize_utc_datetime(
            value,
            field_label="A data/hora de envio (sent_at)",
        )

    @validates("read_at")
    def _validate_read_at(
        self,
        _key: str,
        value: datetime | None,
    ) -> datetime | None:
        """Normaliza read_at opcional para UTC."""
        if value is None:
            return None
        return _normalize_utc_datetime(
            value,
            field_label="A data/hora de leitura (read_at)",
        )


__all__ = ["ChatMessage", "HelpRequest"]
