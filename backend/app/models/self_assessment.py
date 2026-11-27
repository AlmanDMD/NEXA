"""Modelos ORM SQLAlchemy 2.0 para Formulários de Autoavaliação (DB-031), Respostas do Estudante (DB-032), Diagnósticos Explicáveis (DB-035) e View de Discrepância (vw_self_eval_discrepancy - DB-038)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Final
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
    column,
    event,
    func,
    inspect,
    table,
    text,
)
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now
from app.models.learning_module import _coerce_orm_decimal
from app.schemas.enums import DiagnosticType

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.competency import Competency
    from app.models.learning_module import LearningModule
    from app.models.user import User


def _normalize_utc_datetime(value: datetime, *, field_label: str) -> datetime:
    """Garante que o valor seja um datetime válido normalizado em UTC."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field_label} deve ser um objeto datetime válido.")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SelfAssessmentForm(Base, UUIDPrimaryKeyMixin):
    """Entidade de ciclo/questionário de autoavaliação de competências práticas por módulo e turma (tabela 'self_assessment_forms' - DB-031)."""

    __tablename__ = "self_assessment_forms"
    __table_args__ = (
        CheckConstraint(
            "opens_at < closes_at",
            name="chk_self_assessment_forms_dates",
        ),
        CheckConstraint(
            "length(trim(title)) >= 3",
            name="chk_self_assessment_forms_title_not_blank",
        ),
        Index(
            "idx_self_assessment_forms_class_active",
            "class_id",
            "is_active",
        ),
        Index(
            "idx_self_assessment_forms_window",
            "class_id",
            "is_active",
            "opens_at",
            "closes_at",
        ),
        Index("idx_self_assessment_forms_module", "module_id"),
        Index("idx_self_assessment_forms_creator", "created_by"),
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
    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    opens_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    closes_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    created_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    module: Mapped["LearningModule"] = relationship(
        "LearningModule",
        lazy="joined",
        innerjoin=True,
    )
    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        lazy="joined",
        innerjoin=True,
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="joined",
        innerjoin=True,
    )
    responses: Mapped[list["StudentSelfAssessment"]] = relationship(
        "StudentSelfAssessment",
        back_populates="form",
        passive_deletes=True,
        lazy="selectin",
    )

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        """Remove espaços extras e valida que o título tenha entre 3 e 150 caracteres."""
        if not isinstance(value, str):
            raise ValueError(
                "O título do questionário de autoavaliação deve ser um texto válido."
            )
        normalized = value.strip()
        if not (3 <= len(normalized) <= 150):
            raise ValueError(
                "O título do questionário de autoavaliação deve ter entre 3 e 150 caracteres."
            )
        return normalized

    @validates("instructions")
    def _validate_instructions(self, _key: str, value: str | None) -> str | None:
        """Normaliza as instruções opcionais do questionário convertendo vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(
                "As instruções do questionário (instructions) devem ser um texto válido."
            )
        normalized = value.strip()
        return normalized or None

    @validates("opens_at", "closes_at")
    def _validate_window_dates(self, key: str, value: datetime) -> datetime:
        """Valida que opens_at seja estritamente anterior a closes_at."""
        label = (
            "A data/hora de abertura (opens_at)"
            if key == "opens_at"
            else "A data/hora de fechamento (closes_at)"
        )
        normalized = _normalize_utc_datetime(value, field_label=label)
        if key == "opens_at" and getattr(self, "closes_at", None) is not None:
            closes_utc = _normalize_utc_datetime(
                self.closes_at,
                field_label="A data/hora de fechamento (closes_at)",
            )
            if normalized >= closes_utc:
                raise ValueError(
                    "A data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at)."
                )
        elif key == "closes_at" and getattr(self, "opens_at", None) is not None:
            opens_utc = _normalize_utc_datetime(
                self.opens_at,
                field_label="A data/hora de abertura (opens_at)",
            )
            if opens_utc >= normalized:
                raise ValueError(
                    "A data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at)."
                )
        return normalized


class StudentSelfAssessment(Base, UUIDPrimaryKeyMixin):
    """Resposta individual de autoavaliação de domínio (1..5) e confiança (1..5) declarada pelo estudante por competência (tabela 'student_self_assessments' - DB-032)."""

    __tablename__ = "student_self_assessments"
    __table_args__ = (
        UniqueConstraint(
            "form_id",
            "student_id",
            "competency_id",
            name="uq_student_self_assessments_composite",
        ),
        CheckConstraint(
            "perceived_level >= 1 AND perceived_level <= 5",
            name="chk_self_assessments_perceived",
        ),
        CheckConstraint(
            "confidence_score >= 1 AND confidence_score <= 5",
            name="chk_self_assessments_confidence",
        ),
        Index(
            "idx_student_self_assessments_student_competency",
            "student_id",
            "competency_id",
        ),
        Index(
            "idx_student_self_assessments_form_student",
            "form_id",
            "student_id",
        ),
        Index("idx_student_self_assessments_competency", "competency_id"),
    )

    form_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("self_assessment_forms.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    perceived_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    confidence_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    difficulty_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    form: Mapped["SelfAssessmentForm"] = relationship(
        "SelfAssessmentForm",
        back_populates="responses",
    )
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        lazy="joined",
        innerjoin=True,
    )
    competency: Mapped["Competency"] = relationship(
        "Competency",
        lazy="joined",
        innerjoin=True,
    )

    @validates("perceived_level", "confidence_score")
    def _validate_scale_level(self, key: str, value: int) -> int:
        """Garante que perceived_level e confidence_score sejam inteiros entre 1 e 5."""
        label = (
            "O nível percebido (perceived_level)"
            if key == "perceived_level"
            else "O grau de confiança (confidence_score)"
        )
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
            raise ValueError(f"{label} deve ser um número inteiro entre 1 e 5.")
        return value

    @validates("difficulty_notes")
    def _validate_difficulty_notes(self, _key: str, value: str | None) -> str | None:
        """Normaliza relato opcional de dificuldades convertendo string vazia em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(
                "As observações de dificuldade (difficulty_notes) devem ser um texto válido."
            )
        normalized = value.strip()
        return normalized or None


class ExplainableDiagnostic(Base, UUIDPrimaryKeyMixin):
    """Diagnóstico pedagógico explicável comparando autoavaliação discente e evidência docente (tabela 'explainable_diagnostics' - DB-035)."""

    __tablename__ = "explainable_diagnostics"
    __table_args__ = (
        CheckConstraint(
            "self_perceived_level >= 1.00 AND self_perceived_level <= 5.00",
            name="chk_diagnostics_self_level",
        ),
        CheckConstraint(
            "teacher_verified_level >= 1.00 AND teacher_verified_level <= 5.00",
            name="chk_diagnostics_teacher_level",
        ),
        CheckConstraint(
            "discrepancy_gap >= -4.00 AND discrepancy_gap <= 4.00",
            name="chk_diagnostics_gap_range",
        ),
        CheckConstraint(
            "length(trim(explanation_text)) >= 10",
            name="chk_diagnostics_explanation_not_empty",
        ),
        CheckConstraint(
            "length(trim(limitations_note)) >= 10",
            name="chk_diagnostics_limitations_not_empty",
        ),
        CheckConstraint(
            "length(trim(recommended_action)) >= 5",
            name="chk_diagnostics_action_not_empty",
        ),
        Index(
            "idx_explainable_diagnostics_class_type",
            "class_id",
            "diagnostic_type",
        ),
        Index(
            "idx_explainable_diagnostics_student_module",
            "student_id",
            "module_id",
            "generated_at",
        ),
        Index("idx_explainable_diagnostics_competency", "competency_id"),
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
    module_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competencies.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    self_perceived_level: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        nullable=False,
    )
    teacher_verified_level: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        nullable=False,
    )
    discrepancy_gap: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True),
        nullable=False,
    )
    diagnostic_type: Mapped[DiagnosticType] = mapped_column(
        SAEnum(DiagnosticType, name="diagnostic_type_enum", native_enum=True),
        nullable=False,
    )
    explanation_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    limitations_note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    recommended_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        lazy="joined",
        innerjoin=True,
    )
    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        lazy="joined",
        innerjoin=True,
    )
    module: Mapped["LearningModule"] = relationship(
        "LearningModule",
        lazy="joined",
        innerjoin=True,
    )
    competency: Mapped["Competency | None"] = relationship(
        "Competency",
        lazy="joined",
    )

    @validates("self_perceived_level", "teacher_verified_level")
    def _validate_diagnostic_levels(self, key: str, value: Any) -> Decimal:
        """Valida que os níveis percebido e verificado estejam entre 1.00 e 5.00."""
        label = (
            "O nível autopercebido (self_perceived_level)"
            if key == "self_perceived_level"
            else "O nível verificado pelo docente (teacher_verified_level)"
        )
        parsed = _coerce_orm_decimal(value, field_label=label)
        if not (Decimal("1.00") <= parsed <= Decimal("5.00")):
            raise ValueError(f"{label} deve estar entre 1.00 e 5.00.")
        return parsed

    @validates("discrepancy_gap")
    def _validate_discrepancy_gap(self, _key: str, value: Any) -> Decimal:
        """Valida que a amplitude da discrepância esteja entre -4.00 e 4.00."""
        parsed = _coerce_orm_decimal(
            value,
            field_label="O gap de discrepância (discrepancy_gap)",
        )
        if not (Decimal("-4.00") <= parsed <= Decimal("4.00")):
            raise ValueError(
                "O gap de discrepância (discrepancy_gap) deve estar entre -4.00 e 4.00."
            )
        return parsed

    @validates("explanation_text", "limitations_note", "recommended_action")
    def _validate_required_texts(self, key: str, value: str) -> str:
        """Remove espaços extras e valida comprimento mínimo dos campos de inteligência explicável."""
        min_len = 5 if key == "recommended_action" else 10
        if not isinstance(value, str):
            raise ValueError(f"O campo {key} deve ser um texto válido.")
        normalized = value.strip()
        if len(normalized) < min_len:
            raise ValueError(
                f"O campo {key} deve ter pelo menos {min_len} caracteres."
            )
        return normalized


VW_SELF_EVAL_DISCREPANCY_NAME: Final[str] = "vw_self_eval_discrepancy"

VW_SELF_EVAL_DISCREPANCY_DROP_SQL: Final[str] = (
    f"DROP VIEW IF EXISTS {VW_SELF_EVAL_DISCREPANCY_NAME}"
)

VW_SELF_EVAL_DISCREPANCY_CREATE_SQL: Final[str] = f"""
CREATE VIEW {VW_SELF_EVAL_DISCREPANCY_NAME} AS
SELECT
    ssa.id AS self_assessment_id,
    ssa.form_id AS form_id,
    saf.class_id AS class_id,
    saf.module_id AS module_id,
    lm.title AS module_title,
    ssa.student_id AS student_id,
    up.full_name AS student_name,
    ssa.competency_id AS competency_id,
    cp.code AS competency_code,
    cp.title AS competency_title,
    cp.category AS competency_category,
    ROUND(CAST(ssa.perceived_level AS NUMERIC), 2) AS perceived_level,
    ssa.confidence_score AS confidence_score,
    ea.avg_verified_level AS avg_verified_level,
    COALESCE(ea.evidence_count, 0) AS evidence_count,
    CASE
        WHEN COALESCE(ea.evidence_count, 0) = 0 THEN NULL
        ELSE ROUND(CAST(ssa.perceived_level AS NUMERIC) - ea.avg_verified_level, 2)
    END AS discrepancy_delta,
    CASE
        WHEN COALESCE(ea.evidence_count, 0) = 0 THEN 'INSUFFICIENT_EVIDENCE'
        WHEN (CAST(ssa.perceived_level AS NUMERIC) - ea.avg_verified_level) >= 1.50 THEN 'OVERCONFIDENCE_RISK'
        WHEN (CAST(ssa.perceived_level AS NUMERIC) - ea.avg_verified_level) <= -1.50 THEN 'UNDERCONFIDENCE_SUPPORT'
        ELSE 'ALIGNED'
    END AS diagnostic_classification,
    CASE
        WHEN COALESCE(ea.evidence_count, 0) = 0
             OR ABS(CAST(ssa.perceived_level AS NUMERIC) - ea.avg_verified_level) >= 1.50
        THEN 1
        ELSE 0
    END AS requires_pedagogical_review,
    ssa.difficulty_notes AS difficulty_notes,
    ssa.submitted_at AS submitted_at,
    ea.last_evidence_at AS last_evidence_at
FROM student_self_assessments ssa
INNER JOIN self_assessment_forms saf ON saf.id = ssa.form_id
INNER JOIN learning_modules lm ON lm.id = saf.module_id
INNER JOIN competencies cp ON cp.id = ssa.competency_id
LEFT JOIN user_profiles up ON up.user_id = ssa.student_id
LEFT JOIN (
    SELECT
        se.student_id AS student_id,
        se.competency_id AS competency_id,
        ROUND(AVG(CAST(se.verified_level AS NUMERIC)), 2) AS avg_verified_level,
        COUNT(se.id) AS evidence_count,
        MAX(se.recorded_at) AS last_evidence_at
    FROM skill_evidences se
    GROUP BY se.student_id, se.competency_id
) ea
    ON ea.student_id = ssa.student_id
   AND ea.competency_id = ssa.competency_id
"""

vw_self_eval_discrepancy_table = table(
    VW_SELF_EVAL_DISCREPANCY_NAME,
    column("self_assessment_id", Uuid(as_uuid=True)),
    column("form_id", Uuid(as_uuid=True)),
    column("class_id", Uuid(as_uuid=True)),
    column("module_id", Uuid(as_uuid=True)),
    column("module_title", String),
    column("student_id", Uuid(as_uuid=True)),
    column("student_name", String),
    column("competency_id", Uuid(as_uuid=True)),
    column("competency_code", String),
    column("competency_title", String),
    column("competency_category", String),
    column("perceived_level", Numeric(3, 2)),
    column("confidence_score", Integer),
    column("avg_verified_level", Numeric(3, 2)),
    column("evidence_count", Integer),
    column("discrepancy_delta", Numeric(3, 2)),
    column("diagnostic_classification", String),
    column("requires_pedagogical_review", Boolean),
    column("difficulty_notes", Text),
    column("submitted_at", DateTime(timezone=True)),
    column("last_evidence_at", DateTime(timezone=True)),
)

_VW_DISCREPANCY_REQUIRED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "student_self_assessments",
        "self_assessment_forms",
        "learning_modules",
        "competencies",
        "user_profiles",
        "skill_evidences",
    }
)


@event.listens_for(Base.metadata, "after_create")
def _create_vw_self_eval_discrepancy(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Cria a view analítica vw_self_eval_discrepancy (DB-038) após a criação das tabelas base."""
    existing_tables = set(inspect(connection).get_table_names())
    if _VW_DISCREPANCY_REQUIRED_TABLES.issubset(existing_tables):
        connection.execute(text(VW_SELF_EVAL_DISCREPANCY_DROP_SQL))
        connection.execute(text(VW_SELF_EVAL_DISCREPANCY_CREATE_SQL))


@event.listens_for(Base.metadata, "before_drop")
def _drop_vw_self_eval_discrepancy(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Remove a view vw_self_eval_discrepancy antes do drop das tabelas base."""
    connection.execute(text(VW_SELF_EVAL_DISCREPANCY_DROP_SQL))


__all__ = [
    "ExplainableDiagnostic",
    "SelfAssessmentForm",
    "StudentSelfAssessment",
    "VW_SELF_EVAL_DISCREPANCY_CREATE_SQL",
    "VW_SELF_EVAL_DISCREPANCY_DROP_SQL",
    "VW_SELF_EVAL_DISCREPANCY_NAME",
    "vw_self_eval_discrepancy_table",
]
