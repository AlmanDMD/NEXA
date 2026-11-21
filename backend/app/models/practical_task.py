"""Modelos ORM SQLAlchemy 2.0 para Atividades Práticas (DB-023), Rubricas (DB-024) e Submissões (DB-025)."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
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
from app.schemas.enums import SubmissionStatus

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.competency import Competency
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.user import User


def _validate_optional_http_url(value: str | None, *, field_label: str) -> str | None:
    """Valida e normaliza URL opcional exigindo esquema http:// ou https:// com até 500 caracteres."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_label} deve ser um texto válido.")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > 500:
        raise ValueError(f"{field_label} deve ter no máximo 500 caracteres.")
    parsed = urlparse(normalized)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"{field_label} deve ser um endereço válido iniciando com http:// ou https://."
        )
    return normalized


class PracticalTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Entidade de atividade prática de oficina vinculada a módulo e turma (tabela 'practical_tasks' - DB-023)."""

    __tablename__ = "practical_tasks"
    __table_args__ = (
        CheckConstraint(
            "max_score >= 1.00 AND max_score <= 10.00",
            name="chk_practical_tasks_max_score",
        ),
        Index("idx_practical_tasks_class_due_date", "class_id", "due_date"),
        Index("idx_practical_tasks_module", "module_id"),
    )

    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT", onupdate="CASCADE"),
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
    blueprint_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        default=Decimal("10.00"),
        server_default=text("10.00"),
        nullable=False,
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )

    module: Mapped["LearningModule"] = relationship(
        "LearningModule",
        back_populates="practical_tasks",
        lazy="joined",
        innerjoin=True,
    )
    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        back_populates="practical_tasks",
        lazy="joined",
        innerjoin=True,
    )
    criteria: Mapped[list["TaskCriterion"]] = relationship(
        "TaskCriterion",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    submissions: Mapped[list["TaskSubmission"]] = relationship(
        "TaskSubmission",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e valida comprimento do título da tarefa prática."""
        if not isinstance(value, str):
            raise ValueError("O título da atividade prática deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError("O título da atividade prática deve ter entre 3 e 150 caracteres.")
        return normalized

    @validates("description")
    def _validate_description(self, _key: str, value: str | None) -> str | None:
        """Normaliza a descrição opcional convertendo string vazia em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("A descrição da atividade prática deve ser um texto válido.")
        normalized = value.strip()
        return normalized or None

    @validates("blueprint_url")
    def _validate_blueprint_url(self, _key: str, value: str | None) -> str | None:
        """Valida URL opcional do desenho técnico / folha de processo."""
        return _validate_optional_http_url(
            value,
            field_label="A URL do desenho técnico (blueprint_url)",
        )

    @validates("due_date")
    def _validate_due_date(self, _key: str, value: datetime) -> datetime:
        """Garante que due_date seja uma instância válida de datetime."""
        if not isinstance(value, datetime):
            raise ValueError("O prazo de entrega (due_date) deve ser um objeto datetime válido.")
        return value

    @validates("max_score")
    def _validate_max_score(self, _key: str, value: Any) -> Decimal:
        """Valida que a pontuação máxima esteja entre 1.00 e 10.00."""
        parsed = _coerce_orm_decimal(value, field_label="A pontuação máxima (max_score)")
        if not (Decimal("1.00") <= parsed <= Decimal("10.00")):
            raise ValueError("A pontuação máxima (max_score) deve estar entre 1.00 e 10.00.")
        return parsed

    @validates("is_mandatory")
    def _validate_is_mandatory(self, _key: str, value: bool) -> bool:
        """Garante que is_mandatory seja um booleano estrito."""
        if not isinstance(value, bool):
            raise ValueError("O indicador de obrigatoriedade (is_mandatory) deve ser booleano.")
        return value


class TaskCriterion(Base, UUIDPrimaryKeyMixin):
    """Critério técnico / rubrica de avaliação prática vinculada a uma competência (tabela 'task_criteria' - DB-024)."""

    __tablename__ = "task_criteria"
    __table_args__ = (
        CheckConstraint(
            "weight > 0 AND weight <= 9.99",
            name="chk_task_criteria_weight",
        ),
        CheckConstraint(
            "min_acceptable_level >= 1 AND min_acceptable_level <= 5",
            name="chk_task_criteria_min_level",
        ),
        Index("idx_task_criteria_task", "task_id"),
        Index("idx_task_criteria_competency", "competency_id"),
    )

    task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practical_tasks.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    criterion_name: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        default=Decimal("1.00"),
        server_default=text("1.00"),
        nullable=False,
    )
    min_acceptable_level: Mapped[int] = mapped_column(
        Integer,
        default=3,
        server_default=text("3"),
        nullable=False,
    )

    task: Mapped["PracticalTask"] = relationship(
        "PracticalTask",
        back_populates="criteria",
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        lazy="joined",
        innerjoin=True,
    )

    @validates("criterion_name")
    def _validate_criterion_name(self, _key: str, value: str) -> str:
        """Valida o nome do critério técnico / rubrica (3 a 180 caracteres)."""
        if not isinstance(value, str):
            raise ValueError("O nome do critério técnico (criterion_name) deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 180):
            raise ValueError(
                "O nome do critério técnico (criterion_name) deve ter entre 3 e 180 caracteres."
            )
        return normalized

    @validates("weight")
    def _validate_weight(self, _key: str, value: Any) -> Decimal:
        """Valida que o peso do critério seja maior que 0.00 e no máximo 9.99."""
        parsed = _coerce_orm_decimal(value, field_label="O peso do critério (weight)")
        if not (Decimal("0.00") < parsed <= Decimal("9.99")):
            raise ValueError("O peso do critério (weight) deve ser maior que 0.00 e no máximo 9.99.")
        return parsed

    @validates("min_acceptable_level")
    def _validate_min_acceptable_level(self, _key: str, value: int) -> int:
        """Garante que o nível mínimo aceitável seja um inteiro entre 1 e 5."""
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
            raise ValueError(
                "O nível mínimo aceitável (min_acceptable_level) deve ser um inteiro entre 1 e 5."
            )
        return value


class TaskSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Submissão e estado de execução de atividade prática por estudante (tabela 'task_submissions' - DB-025)."""

    __tablename__ = "task_submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uq_task_submissions_task_student"),
        UniqueConstraint("task_id", "enrollment_id", name="uq_task_submissions_task_enrollment"),
        CheckConstraint(
            "final_task_score IS NULL OR (final_task_score >= 0 AND final_task_score <= 10)",
            name="chk_task_submissions_final_score",
        ),
        Index("idx_task_submissions_student_status", "student_id", "status"),
        Index("idx_task_submissions_task_status", "task_id", "status"),
    )

    task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practical_tasks.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
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
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus, name="submission_status_enum", native_enum=True),
        default=SubmissionStatus.PENDING,
        server_default=SubmissionStatus.PENDING.value,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    evidence_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    student_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    final_task_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2, asdecimal=True),
        nullable=True,
    )

    task: Mapped["PracticalTask"] = relationship(
        "PracticalTask",
        back_populates="submissions",
    )
    student: Mapped["User"] = relationship("User")
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")

    @validates("evidence_url")
    def _validate_evidence_url(self, _key: str, value: str | None) -> str | None:
        """Valida URL opcional de evidência da entrega prática."""
        return _validate_optional_http_url(
            value,
            field_label="A URL de evidência (evidence_url)",
        )

    @validates("student_notes")
    def _validate_student_notes(self, _key: str, value: str | None) -> str | None:
        """Normaliza observações opcionais do estudante."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("As observações do estudante (student_notes) devem ser um texto válido.")
        normalized = value.strip()
        return normalized or None

    @validates("final_task_score")
    def _validate_final_task_score(self, _key: str, value: Any) -> Decimal | None:
        """Valida que a nota final da tarefa prática esteja entre 0.00 e 10.00 quando informada."""
        if value is None:
            return None
        parsed = _coerce_orm_decimal(value, field_label="A nota final da tarefa (final_task_score)")
        if not (Decimal("0.00") <= parsed <= Decimal("10.00")):
            raise ValueError(
                "A nota final da tarefa (final_task_score) deve estar entre 0.00 e 10.00."
            )
        return parsed


__all__ = ["PracticalTask", "TaskCriterion", "TaskSubmission"]
