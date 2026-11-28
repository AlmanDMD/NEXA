"""Modelos ORM SQLAlchemy 2.0 para Catálogo de Conquistas (gamification_badges - DB-045) e Conquistas dos Estudantes (student_achievements - DB-046)."""

from datetime import datetime, timezone
import re
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now

if TYPE_CHECKING:
    from app.models.competency import Competency
    from app.models.enrollment import Enrollment
    from app.models.user import User

_BADGE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,59}$")


def _normalize_utc_datetime(value: datetime, *, field_label: str) -> datetime:
    """Garante que o valor seja um datetime válido normalizado em UTC."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field_label} deve ser um objeto datetime válido.")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class GamificationBadge(Base, UUIDPrimaryKeyMixin):
    """Entidade de conquista/insígnia técnica com critérios transparentes de pontuação (tabela 'gamification_badges' - DB-045)."""

    __tablename__ = "gamification_badges"
    __table_args__ = (
        UniqueConstraint("code", name="uq_gamification_badges_code"),
        CheckConstraint(
            "length(trim(title)) >= 3",
            name="chk_gamification_badges_title_not_empty",
        ),
        CheckConstraint(
            "length(trim(description)) >= 10",
            name="chk_gamification_badges_description_not_empty",
        ),
        CheckConstraint(
            "length(trim(criteria_explanation)) >= 15",
            name="chk_gamification_badges_criteria_not_empty",
        ),
        CheckConstraint(
            "length(trim(icon_name)) >= 2",
            name="chk_gamification_badges_icon_not_empty",
        ),
        CheckConstraint(
            "xp_reward > 0 AND xp_reward <= 5000",
            name="chk_gamification_badges_xp_positive",
        ),
        Index(
            "idx_gamification_badges_active_competency",
            "is_active",
            "competency_id",
        ),
        Index("idx_gamification_badges_xp", "xp_reward"),
    )

    code: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    criteria_explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    icon_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=50,
        server_default=text("50"),
        nullable=False,
    )
    competency_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    competency: Mapped["Competency | None"] = relationship(
        "Competency",
        lazy="joined",
    )
    achievements: Mapped[list["StudentAchievement"]] = relationship(
        "StudentAchievement",
        back_populates="badge",
        passive_deletes=True,
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        """Normaliza o código da conquista em maiúsculas e valida o formato."""
        if not isinstance(value, str):
            raise ValueError("O código da conquista (code) deve ser um texto válido.")
        normalized = value.strip().upper()
        if not _BADGE_CODE_PATTERN.match(normalized):
            raise ValueError(
                "O código da conquista (code) deve ter entre 3 e 60 caracteres alfanuméricos, hífen ou underscore."
            )
        return normalized

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Valida que o título da conquista tenha entre 3 e 120 caracteres."""
        if not isinstance(value, str):
            raise ValueError("O título da conquista (title) deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 120):
            raise ValueError(
                "O título da conquista (title) deve ter entre 3 e 120 caracteres."
            )
        return normalized

    @validates("description")
    def _validate_description(self, _key: str, value: str) -> str:
        """Valida que a descrição da conquista tenha pelo menos 10 caracteres."""
        if not isinstance(value, str):
            raise ValueError(
                "A descrição da conquista (description) deve ser um texto válido."
            )
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError(
                "A descrição da conquista (description) deve ter pelo menos 10 caracteres."
            )
        return normalized

    @validates("criteria_explanation")
    def _validate_criteria_explanation(self, _key: str, value: str) -> str:
        """Garante preenchimento obrigatório de criteria_explanation (>= 15 caracteres - DB-045 / BE-046)."""
        if not isinstance(value, str):
            raise ValueError(
                "A explicação dos critérios (criteria_explanation) deve ser um texto válido."
            )
        normalized = value.strip()
        if len(normalized) < 15:
            raise ValueError(
                "A explicação dos critérios (criteria_explanation) deve ter pelo menos 15 caracteres."
            )
        return normalized

    @validates("icon_name")
    def _validate_icon_name(self, _key: str, value: str) -> str:
        """Valida que o identificador do ícone tenha entre 2 e 80 caracteres."""
        if not isinstance(value, str):
            raise ValueError("O nome do ícone (icon_name) deve ser um texto válido.")
        normalized = value.strip()
        if not (2 <= len(normalized) <= 80):
            raise ValueError(
                "O nome do ícone (icon_name) deve ter entre 2 e 80 caracteres."
            )
        return normalized

    @validates("xp_reward")
    def _validate_xp_reward(self, _key: str, value: int) -> int:
        """Garante que xp_reward seja um inteiro positivo entre 1 e 5000."""
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not (1 <= value <= 5000)
        ):
            raise ValueError(
                "A recompensa de XP (xp_reward) deve ser um inteiro positivo entre 1 e 5000."
            )
        return value


class StudentAchievement(Base, UUIDPrimaryKeyMixin):
    """Entidade de conquista desbloqueada por um estudante (tabela 'student_achievements' - DB-046)."""

    __tablename__ = "student_achievements"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "badge_id",
            name="uq_student_achievements_composite",
        ),
        CheckConstraint(
            "length(trim(origin_reference)) >= 3",
            name="chk_student_achievements_origin_not_empty",
        ),
        Index(
            "idx_student_achievements_student_unlocked",
            "student_id",
            "unlocked_at",
        ),
        Index("idx_student_achievements_enrollment", "enrollment_id"),
        Index("idx_student_achievements_badge", "badge_id"),
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
    badge_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("gamification_badges.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )
    origin_reference: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
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
    badge: Mapped["GamificationBadge"] = relationship(
        "GamificationBadge",
        back_populates="achievements",
        lazy="joined",
        innerjoin=True,
    )

    @validates("origin_reference")
    def _validate_origin_reference(self, _key: str, value: str) -> str:
        """Valida que origin_reference tenha entre 3 e 150 caracteres."""
        if not isinstance(value, str):
            raise ValueError(
                "A referência de origem (origin_reference) deve ser um texto válido."
            )
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError(
                "A referência de origem (origin_reference) deve ter entre 3 e 150 caracteres."
            )
        return normalized

    @validates("unlocked_at")
    def _validate_unlocked_at(self, _key: str, value: datetime) -> datetime:
        """Normaliza unlocked_at em UTC."""
        return _normalize_utc_datetime(
            value,
            field_label="A data/hora de desbloqueio (unlocked_at)",
        )


__all__ = ["GamificationBadge", "StudentAchievement"]
