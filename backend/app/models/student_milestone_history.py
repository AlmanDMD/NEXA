"""Modelo ORM SQLAlchemy 2.0 para Histórico e Linha do Tempo Acadêmica do Estudante (student_milestone_history - DB-039)."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now
from app.schemas.enums import MilestoneType

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.user import User


class StudentMilestoneHistory(Base, UUIDPrimaryKeyMixin):
    """Entidade de marco da linha do tempo acadêmica do estudante (tabela 'student_milestone_history' - DB-039)."""

    __tablename__ = "student_milestone_history"
    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) >= 3",
            name="chk_milestone_history_title_not_empty",
        ),
        Index(
            "idx_milestone_history_student_achieved",
            "student_id",
            "achieved_at",
        ),
        Index(
            "idx_milestone_history_enrollment_achieved",
            "enrollment_id",
            "achieved_at",
        ),
        Index("idx_milestone_history_module", "module_id"),
        Index("idx_milestone_history_type", "milestone_type"),
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
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    milestone_type: Mapped[MilestoneType] = mapped_column(
        SAEnum(MilestoneType, name="milestone_type_enum", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    milestone_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped["User"] = relationship("User")
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")
    module: Mapped["LearningModule | None"] = relationship("LearningModule")

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras e valida que o título do marco tenha entre 3 e 150 caracteres."""
        if not isinstance(value, str):
            raise ValueError("O título do marco acadêmico (title) deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError(
                "O título do marco acadêmico (title) deve ter entre 3 e 150 caracteres."
            )
        return normalized

    @validates("description")
    def _validate_description(self, _key: str, value: str | None) -> str | None:
        """Normaliza a descrição opcional do marco acadêmico."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(
                "A descrição do marco acadêmico (description) deve ser um texto válido."
            )
        normalized = value.strip()
        return normalized or None

    @validates("milestone_metadata")
    def _validate_milestone_metadata(
        self,
        _key: str,
        value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Garante que o campo metadata JSONB opcional seja um dicionário/objeto JSON."""
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError(
                "Os metadados do marco acadêmico (metadata) devem ser um objeto JSON válido."
            )
        return value


__all__ = ["StudentMilestoneHistory"]
