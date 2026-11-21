"""Modelo ORM SQLAlchemy 2.0 para alocação de docentes em disciplinas/turmas (teacher_assignments - DB-018)."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.subject import Subject
    from app.models.user import User


class TeacherAssignment(Base, UUIDPrimaryKeyMixin):
    """Entidade de vínculo docente a turma e disciplina SENAI (tabela 'teacher_assignments')."""

    __tablename__ = "teacher_assignments"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "class_id",
            "subject_id",
            name="uq_teacher_assignments_composite",
        ),
        Index("idx_teacher_assignments_teacher_class", "teacher_id", "class_id"),
        Index("idx_teacher_assignments_class_subject", "class_id", "subject_id"),
        Index("idx_teacher_assignments_subject", "subject_id"),
    )

    teacher_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )
    is_main_teacher: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )

    teacher: Mapped["User"] = relationship(
        "User",
        back_populates="teacher_assignments",
        lazy="joined",
        innerjoin=True,
    )
    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        back_populates="teacher_assignments",
        lazy="joined",
        innerjoin=True,
    )
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="teacher_assignments",
        lazy="joined",
        innerjoin=True,
    )

    @validates("is_main_teacher")
    def _validate_is_main_teacher(self, _key: str, value: bool) -> bool:
        """Garante que is_main_teacher seja estritamente booleano."""
        if not isinstance(value, bool):
            raise ValueError("O campo is_main_teacher deve ser um booleano válido.")
        return value


__all__ = ["TeacherAssignment"]
