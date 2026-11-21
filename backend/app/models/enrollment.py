"""Modelo ORM SQLAlchemy 2.0 para a tabela de matrículas de estudantes (enrollments - DB-017 / DB-019)."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.learning_module import _coerce_orm_decimal
from app.schemas.enums import EnrollmentStatus

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.user import User


def _utc_today() -> date:
    """Retorna a data atual em UTC."""
    return datetime.now(timezone.utc).date()


class Enrollment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de matrícula de estudante em uma turma acadêmica SENAI (tabela 'enrollments')."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", name="uq_enrollments_student_class"),
        CheckConstraint(
            "final_grade IS NULL OR (final_grade >= 0 AND final_grade <= 10)",
            name="chk_enrollments_final_grade",
        ),
        CheckConstraint(
            "attendance_rate IS NULL OR (attendance_rate >= 0 AND attendance_rate <= 100)",
            name="chk_enrollments_attendance_rate",
        ),
        Index("idx_enrollments_attendance_rate", "attendance_rate"),
        Index(
            "idx_enrollments_class_status_attendance",
            "class_id",
            "status",
            "attendance_rate",
        ),
        Index("idx_enrollments_class_status", "class_id", "status"),
        Index("idx_enrollments_student_status", "student_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    enrollment_date: Mapped[date] = mapped_column(
        Date,
        default=_utc_today,
        server_default=func.current_date(),
        nullable=False,
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, name="enrollment_status_enum", native_enum=True),
        default=EnrollmentStatus.ACTIVE,
        server_default=EnrollmentStatus.ACTIVE.value,
        nullable=False,
    )
    final_grade: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        nullable=True,
    )
    attendance_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2, asdecimal=True),
        nullable=True,
    )

    student: Mapped["User"] = relationship(
        "User",
        back_populates="enrollments",
        lazy="joined",
        innerjoin=True,
    )
    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        back_populates="enrollments",
        lazy="joined",
        innerjoin=True,
    )

    @validates("enrollment_date")
    def _validate_enrollment_date(self, _key: str, value: date) -> date:
        """Garante que enrollment_date seja uma instância pura de date (sem datetime)."""
        if isinstance(value, datetime) or not isinstance(value, date):
            raise ValueError("A data de matrícula deve ser um objeto date válido.")
        return value

    @validates("final_grade")
    def _validate_final_grade(self, _key: str, value: Any) -> Decimal | None:
        """Valida que a nota final opcional esteja entre 0.00 e 10.00."""
        if value is None:
            return None
        parsed = _coerce_orm_decimal(value, field_label="A nota final (final_grade)")
        if not (Decimal("0.00") <= parsed <= Decimal("10.00")):
            raise ValueError("A nota final (final_grade) deve estar entre 0.00 e 10.00.")
        return parsed

    @validates("attendance_rate")
    def _validate_attendance_rate(self, _key: str, value: Any) -> Decimal | None:
        """Valida que a taxa de frequência percentual opcional esteja entre 0.00 e 100.00."""
        if value is None:
            return None
        parsed = _coerce_orm_decimal(value, field_label="A taxa de frequência (attendance_rate)")
        if not (Decimal("0.00") <= parsed <= Decimal("100.00")):
            raise ValueError("A taxa de frequência (attendance_rate) deve estar entre 0.00 e 100.00.")
        return parsed


__all__ = ["Enrollment"]
