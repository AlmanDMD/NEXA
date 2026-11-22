"""Modelos ORM SQLAlchemy 2.0 para Avaliações Formativas (DB-027) e Notas de Estudantes (DB-028)."""

from datetime import date, datetime
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
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.learning_module import _coerce_orm_decimal
from app.schemas.enums import AssessmentType

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.subject import Subject
    from app.models.user import User


class AcademicAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de avaliação formativa, microavaliação ou prova aplicada em turma e disciplina (tabela 'academic_assessments' - DB-027)."""

    __tablename__ = "academic_assessments"
    __table_args__ = (
        CheckConstraint(
            "weight > 0 AND weight <= 9.99",
            name="chk_academic_assessments_weight",
        ),
        CheckConstraint(
            "max_grade >= 1.00 AND max_grade <= 10.00",
            name="chk_academic_assessments_max_grade",
        ),
        Index(
            "idx_academic_assessments_class_subject_date",
            "class_id",
            "subject_id",
            "application_date",
        ),
        Index("idx_academic_assessments_module", "module_id"),
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
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    assessment_type: Mapped[AssessmentType] = mapped_column(
        SAEnum(AssessmentType, name="assessment_type_enum", native_enum=True),
        default=AssessmentType.EXAM,
        server_default=AssessmentType.EXAM.value,
        nullable=False,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        default=Decimal("1.00"),
        server_default=text("1.00"),
        nullable=False,
    )
    application_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    max_grade: Mapped[Decimal] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        default=Decimal("10.00"),
        server_default=text("10.00"),
        nullable=False,
    )

    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        back_populates="academic_assessments",
        lazy="joined",
        innerjoin=True,
    )
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="academic_assessments",
        lazy="joined",
        innerjoin=True,
    )
    module: Mapped["LearningModule | None"] = relationship(
        "LearningModule",
        back_populates="academic_assessments",
        lazy="joined",
    )
    grades: Mapped[list["StudentGrade"]] = relationship(
        "StudentGrade",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras e valida comprimento do título da avaliação (3 a 150 caracteres)."""
        if not isinstance(value, str):
            raise ValueError("O título da avaliação deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError("O título da avaliação deve ter entre 3 e 150 caracteres.")
        return normalized

    @validates("weight")
    def _validate_weight(self, _key: str, value: Any) -> Decimal:
        """Valida que o peso da avaliação seja maior que 0.00 e no máximo 9.99."""
        parsed = _coerce_orm_decimal(value, field_label="O peso da avaliação (weight)")
        if not (Decimal("0.00") < parsed <= Decimal("9.99")):
            raise ValueError(
                "O peso da avaliação (weight) deve ser maior que 0.00 e no máximo 9.99."
            )
        return parsed

    @validates("application_date")
    def _validate_application_date(self, _key: str, value: date) -> date:
        """Garante que application_date seja uma instância pura de date."""
        if isinstance(value, datetime) or not isinstance(value, date):
            raise ValueError(
                "A data de aplicação (application_date) deve ser um objeto date válido."
            )
        return value

    @validates("max_grade")
    def _validate_max_grade(self, _key: str, value: Any) -> Decimal:
        """Valida que a nota máxima da avaliação esteja entre 1.00 e 10.00."""
        parsed = _coerce_orm_decimal(
            value,
            field_label="A nota máxima da avaliação (max_grade)",
        )
        if not (Decimal("1.00") <= parsed <= Decimal("10.00")):
            raise ValueError(
                "A nota máxima da avaliação (max_grade) deve estar entre 1.00 e 10.00."
            )
        return parsed


class StudentGrade(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Nota e menção de recuperação obtidas por estudante em avaliação formativa (tabela 'student_grades' - DB-028)."""

    __tablename__ = "student_grades"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "student_id",
            name="uq_student_grades_assessment_student",
        ),
        UniqueConstraint(
            "assessment_id",
            "enrollment_id",
            name="uq_student_grades_assessment_enrollment",
        ),
        CheckConstraint(
            "grade_value >= 0.00 AND grade_value <= 10.00",
            name="chk_student_grades_grade_value",
        ),
        CheckConstraint(
            "recovery_grade IS NULL OR (recovery_grade >= 0.00 AND recovery_grade <= 10.00)",
            name="chk_student_grades_recovery_grade",
        ),
        Index("idx_student_grades_assessment", "assessment_id"),
        Index("idx_student_grades_student", "student_id"),
        Index("idx_student_grades_enrollment", "enrollment_id"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_assessments.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    recorded_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    grade_value: Mapped[Decimal] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        nullable=False,
    )
    recovery_grade: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        nullable=True,
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessment: Mapped["AcademicAssessment"] = relationship(
        "AcademicAssessment",
        back_populates="grades",
    )
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        lazy="joined",
        innerjoin=True,
    )
    recorder: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recorded_by],
        lazy="joined",
        innerjoin=True,
    )

    @property
    def effective_grade(self) -> Decimal:
        """Retorna a maior nota entre grade_value e recovery_grade conforme regra pedagógica SENAI."""
        if self.recovery_grade is not None and self.recovery_grade > self.grade_value:
            return self.recovery_grade
        return self.grade_value

    @validates("grade_value")
    def _validate_grade_value(self, _key: str, value: Any) -> Decimal:
        """Valida que a nota da avaliação esteja entre 0.00 e 10.00."""
        parsed = _coerce_orm_decimal(value, field_label="A nota (grade_value)")
        if not (Decimal("0.00") <= parsed <= Decimal("10.00")):
            raise ValueError("A nota (grade_value) deve estar entre 0.00 e 10.00.")
        return parsed

    @validates("recovery_grade")
    def _validate_recovery_grade(self, _key: str, value: Any) -> Decimal | None:
        """Valida que a nota de recuperação opcional esteja entre 0.00 e 10.00."""
        if value is None:
            return None
        parsed = _coerce_orm_decimal(
            value,
            field_label="A nota de recuperação (recovery_grade)",
        )
        if not (Decimal("0.00") <= parsed <= Decimal("10.00")):
            raise ValueError(
                "A nota de recuperação (recovery_grade) deve estar entre 0.00 e 10.00."
            )
        return parsed

    @validates("comments")
    def _validate_comments(self, _key: str, value: str | None) -> str | None:
        """Normaliza comentários opcionais convertendo string vazia em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("As observações da nota (comments) devem ser um texto válido.")
        normalized = value.strip()
        if len(normalized) > 1000:
            raise ValueError(
                "As observações da nota (comments) devem ter no máximo 1000 caracteres."
            )
        return normalized or None


__all__ = [
    "AcademicAssessment",
    "StudentGrade",
]
