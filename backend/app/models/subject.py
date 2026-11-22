"""Modelo ORM SQLAlchemy 2.0 para a tabela de disciplinas teórico-práticas (subjects - DB-013)."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.academic_assessment import AcademicAssessment
    from app.models.class_lesson import ClassLesson
    from app.models.course import Course
    from app.models.learning_module import LearningModule
    from app.models.teacher_assignment import TeacherAssignment


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de disciplina teórico-prática (unidade curricular) vinculada a um curso (tabela 'subjects')."""

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("course_id", "code", name="uq_subjects_course_code"),
        CheckConstraint("workload_hours > 0", name="chk_subjects_workload_positive"),
        Index("idx_subjects_name", "name"),
        Index("idx_subjects_course_active", "course_id", "is_active"),
    )

    course_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    workload_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    syllabus: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="subjects",
        lazy="joined",
        innerjoin=True,
    )
    learning_modules: Mapped[list["LearningModule"]] = relationship(
        "LearningModule",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    teacher_assignments: Mapped[list["TeacherAssignment"]] = relationship(
        "TeacherAssignment",
        back_populates="subject",
        passive_deletes=True,
    )
    lessons: Mapped[list["ClassLesson"]] = relationship(
        "ClassLesson",
        back_populates="subject",
        passive_deletes=True,
    )
    academic_assessments: Mapped[list["AcademicAssessment"]] = relationship(
        "AcademicAssessment",
        back_populates="subject",
        passive_deletes=True,
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        """Normaliza o código da disciplina em maiúsculas sem espaços laterais e valida comprimento."""
        if not isinstance(value, str):
            raise ValueError("O código da disciplina deve ser um texto válido.")
        normalized = value.strip().upper()
        if not (2 <= len(normalized) <= 50):
            raise ValueError("O código da disciplina deve ter entre 2 e 50 caracteres.")
        return normalized

    @validates("name")
    def _validate_name(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e valida comprimento do nome da disciplina."""
        if not isinstance(value, str):
            raise ValueError("O nome da disciplina deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError("O nome da disciplina deve ter entre 3 e 150 caracteres.")
        return normalized

    @validates("workload_hours")
    def _validate_workload_hours(self, _key: str, value: int) -> int:
        """Garante que a carga horária da disciplina seja um inteiro estritamente positivo."""
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("A carga horária da disciplina deve ser um inteiro maior que zero.")
        return value

    @validates("syllabus")
    def _validate_syllabus(self, _key: str, value: str | None) -> str | None:
        """Normaliza a ementa técnica opcional convertendo texto vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("A ementa técnica da disciplina deve ser um texto válido.")
        normalized = value.strip()
        return normalized or None


__all__ = ["Subject"]
