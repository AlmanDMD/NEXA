"""Modelo ORM SQLAlchemy 2.0 para a tabela de turmas acadêmicas (classes - DB-012)."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.schemas.enums import ClassStatus, Shift

if TYPE_CHECKING:
    from app.models.academic_assessment import AcademicAssessment
    from app.models.class_lesson import ClassLesson
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.practical_task import PracticalTask
    from app.models.teacher_assignment import TeacherAssignment


class AcademicClass(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de turma acadêmica vinculada a um curso técnico e período letivo (tabela 'classes')."""

    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("code", "period", name="uq_classes_code_period"),
        CheckConstraint(
            "max_students > 0 AND max_students <= 100",
            name="chk_classes_max_students",
        ),
        CheckConstraint(
            "start_date < end_date",
            name="chk_classes_date_range",
        ),
        Index("idx_classes_course_period", "course_id", "period"),
        Index("idx_classes_period", "period"),
        Index("idx_classes_shift", "shift"),
        Index("idx_classes_status", "status"),
    )

    course_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    shift: Mapped[Shift] = mapped_column(
        SAEnum(Shift, name="shift_enum", native_enum=True),
        nullable=False,
    )
    max_students: Mapped[int] = mapped_column(
        Integer,
        default=40,
        nullable=False,
    )
    status: Mapped[ClassStatus] = mapped_column(
        SAEnum(ClassStatus, name="class_status_enum", native_enum=True),
        default=ClassStatus.PLANNING,
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="classes",
        lazy="joined",
        innerjoin=True,
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="academic_class",
        passive_deletes=True,
    )
    teacher_assignments: Mapped[list["TeacherAssignment"]] = relationship(
        "TeacherAssignment",
        back_populates="academic_class",
        passive_deletes=True,
    )
    lessons: Mapped[list["ClassLesson"]] = relationship(
        "ClassLesson",
        back_populates="academic_class",
        passive_deletes=True,
    )
    practical_tasks: Mapped[list["PracticalTask"]] = relationship(
        "PracticalTask",
        back_populates="academic_class",
        passive_deletes=True,
    )
    academic_assessments: Mapped[list["AcademicAssessment"]] = relationship(
        "AcademicAssessment",
        back_populates="academic_class",
        passive_deletes=True,
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        """Normaliza o código da turma em maiúsculas sem espaços laterais e valida comprimento."""
        if not isinstance(value, str):
            raise ValueError("O código da turma deve ser um texto válido.")
        normalized = value.strip().upper()
        if not (3 <= len(normalized) <= 40):
            raise ValueError("O código da turma deve ter entre 3 e 40 caracteres.")
        return normalized

    @validates("period")
    def _validate_period(self, _key: str, value: str) -> str:
        """Normaliza o período letivo em maiúsculas sem espaços laterais e valida comprimento."""
        if not isinstance(value, str):
            raise ValueError("O período letivo deve ser um texto válido.")
        normalized = value.strip().upper()
        if not (3 <= len(normalized) <= 20):
            raise ValueError("O período letivo deve ter entre 3 e 20 caracteres.")
        return normalized

    @validates("max_students")
    def _validate_max_students(self, _key: str, value: int) -> int:
        """Garante que a capacidade máxima de alunos seja um inteiro entre 1 e 100."""
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 100):
            raise ValueError("A capacidade máxima de alunos deve ser um inteiro entre 1 e 100.")
        return value

    @validates("start_date", "end_date")
    def _validate_dates(self, _key: str, value: date) -> date:
        """Garante que start_date e end_date sejam instâncias puras de date (sem datetime)."""
        if isinstance(value, datetime) or not isinstance(value, date):
            raise ValueError("As datas da turma devem ser objetos date válidos.")
        return value


__all__ = ["AcademicClass"]
