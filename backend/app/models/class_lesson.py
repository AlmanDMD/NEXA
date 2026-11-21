"""Modelos ORM SQLAlchemy 2.0 para Diário de Classe (class_lessons - DB-021) e Chamada (attendance_records - DB-022)."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Final
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
from app.schemas.enums import AttendanceStatus

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.subject import Subject
    from app.models.user import User


class ClassLesson(Base, UUIDPrimaryKeyMixin):
    """Entidade de aula ministrada e diário de bordo por turma, disciplina e módulo (tabela 'class_lessons')."""

    __tablename__ = "class_lessons"
    __table_args__ = (
        CheckConstraint(
            "workload_hours >= 1 AND workload_hours <= 8",
            name="chk_class_lessons_workload",
        ),
        Index(
            "idx_class_lessons_class_subject_date",
            "class_id",
            "subject_id",
            "lesson_date",
        ),
        Index("idx_class_lessons_module", "module_id"),
        Index("idx_class_lessons_teacher", "teacher_id"),
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
        ForeignKey("learning_modules.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    teacher_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    lesson_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    workload_hours: Mapped[int] = mapped_column(
        Integer,
        default=4,
        server_default=text("4"),
        nullable=False,
    )
    topic_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    lab_environment: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    academic_class: Mapped["AcademicClass"] = relationship(
        "AcademicClass",
        back_populates="lessons",
        lazy="joined",
        innerjoin=True,
    )
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="lessons",
        lazy="joined",
        innerjoin=True,
    )
    module: Mapped["LearningModule | None"] = relationship(
        "LearningModule",
        back_populates="lessons",
        lazy="joined",
    )
    teacher: Mapped["User"] = relationship(
        "User",
        back_populates="lessons_taught",
        lazy="joined",
        innerjoin=True,
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @validates("lesson_date")
    def _validate_lesson_date(self, _key: str, value: date) -> date:
        """Garante que lesson_date seja uma instância pura de date (sem datetime)."""
        if isinstance(value, datetime) or not isinstance(value, date):
            raise ValueError("A data da aula (lesson_date) deve ser um objeto date válido.")
        return value

    @validates("workload_hours")
    def _validate_workload_hours(self, _key: str, value: int) -> int:
        """Garante que a carga horária da aula seja um inteiro entre 1 e 8 horas."""
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 8):
            raise ValueError(
                "A carga horária da aula (workload_hours) deve ser um inteiro entre 1 e 8."
            )
        return value

    @validates("topic_summary")
    def _validate_topic_summary(self, _key: str, value: str) -> str:
        """Remove espaços extras das extremidades e exige conteúdo resumido não vazio."""
        if not isinstance(value, str):
            raise ValueError("O resumo do conteúdo (topic_summary) deve ser um texto válido.")
        normalized = value.strip()
        if not (3 <= len(normalized) <= 2000):
            raise ValueError(
                "O resumo do conteúdo (topic_summary) deve ter entre 3 e 2000 caracteres."
            )
        return normalized

    @validates("lab_environment")
    def _validate_lab_environment(self, _key: str, value: str | None) -> str | None:
        """Normaliza o ambiente/oficina opcional convertendo texto vazio em None."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("O ambiente/oficina (lab_environment) deve ser um texto válido.")
        normalized = value.strip()
        if len(normalized) > 100:
            raise ValueError(
                "O ambiente/oficina (lab_environment) deve ter no máximo 100 caracteres."
            )
        return normalized or None


class AttendanceRecord(Base, UUIDPrimaryKeyMixin):
    """Registro atômico de presença/falta de um estudante em uma aula ministrada (tabela 'attendance_records')."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("lesson_id", "student_id", name="uq_attendance_lesson_student"),
        UniqueConstraint(
            "lesson_id",
            "enrollment_id",
            name="uq_attendance_lesson_enrollment",
        ),
        CheckConstraint(
            "absent_hours >= 0 AND absent_hours <= 8",
            name="chk_attendance_absent_hours",
        ),
        Index("idx_attendance_student_status", "student_id", "status"),
        Index("idx_attendance_lesson", "lesson_id"),
    )

    lesson_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("class_lessons.id", ondelete="RESTRICT", onupdate="CASCADE"),
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
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status_enum", native_enum=True),
        default=AttendanceStatus.PRESENT,
        server_default=AttendanceStatus.PRESENT.value,
        nullable=False,
    )
    absent_hours: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    justification_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    lesson: Mapped["ClassLesson"] = relationship(
        "ClassLesson",
        back_populates="attendance_records",
    )
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")
    student: Mapped["User"] = relationship("User")

    @validates("absent_hours")
    def _validate_absent_hours(self, _key: str, value: int) -> int:
        """Garante que as horas de ausência sejam um inteiro entre 0 e 8."""
        if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 8):
            raise ValueError(
                "A quantidade de horas ausentes (absent_hours) deve ser um inteiro entre 0 e 8."
            )
        return value


VW_MODULE_ATTENDANCE_RISK_NAME: Final[str] = "vw_module_attendance_risk"

VW_MODULE_ATTENDANCE_RISK_DROP_SQL: Final[str] = (
    f"DROP VIEW IF EXISTS {VW_MODULE_ATTENDANCE_RISK_NAME}"
)

VW_MODULE_ATTENDANCE_RISK_CREATE_SQL: Final[str] = f"""
CREATE VIEW {VW_MODULE_ATTENDANCE_RISK_NAME} AS
SELECT
    e.id AS enrollment_id,
    e.student_id AS student_id,
    e.class_id AS class_id,
    c.code AS class_code,
    c.period AS class_period,
    e.status AS enrollment_status,
    s.id AS subject_id,
    s.code AS subject_code,
    s.name AS subject_name,
    s.workload_hours AS subject_planned_hours,
    lm.id AS module_id,
    lm.title AS module_title,
    lm.order_index AS module_order_index,
    lm.practical_hours AS module_planned_hours,
    COALESCE(
        SUM(CASE WHEN ar.id IS NOT NULL THEN cl.workload_hours ELSE 0 END),
        0
    ) AS total_hours,
    COALESCE(
        SUM(
            CASE
                WHEN ar.id IS NULL THEN 0
                WHEN ar.status IN ('PRESENT', 'JUSTIFIED') THEN cl.workload_hours
                ELSE CASE
                    WHEN cl.workload_hours - CASE
                        WHEN ar.absent_hours < 0 THEN 0
                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                        ELSE ar.absent_hours
                    END > 0
                    THEN cl.workload_hours - CASE
                        WHEN ar.absent_hours < 0 THEN 0
                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                        ELSE ar.absent_hours
                    END
                    ELSE 0
                END
            END
        ),
        0
    ) AS attended_hours,
    COALESCE(
        SUM(
            CASE
                WHEN ar.id IS NULL THEN 0
                WHEN ar.status IN ('PRESENT', 'JUSTIFIED') THEN 0
                WHEN ar.absent_hours < 0 THEN 0
                WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                ELSE ar.absent_hours
            END
        ),
        0
    ) AS absent_hours,
    COALESCE(
        SUM(
            CASE
                WHEN ar.id IS NULL THEN 0
                WHEN ar.status = 'JUSTIFIED' THEN CASE
                    WHEN ar.absent_hours < 0 THEN 0
                    WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                    ELSE ar.absent_hours
                END
                ELSE 0
            END
        ),
        0
    ) AS justified_absent_hours,
    CASE
        WHEN COALESCE(SUM(CASE WHEN ar.id IS NOT NULL THEN cl.workload_hours ELSE 0 END), 0) <= 0
        THEN 100.00
        ELSE ROUND(
            (
                CAST(
                    COALESCE(
                        SUM(
                            CASE
                                WHEN ar.id IS NULL THEN 0
                                WHEN ar.status IN ('PRESENT', 'JUSTIFIED') THEN cl.workload_hours
                                ELSE CASE
                                    WHEN cl.workload_hours - CASE
                                        WHEN ar.absent_hours < 0 THEN 0
                                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                                        ELSE ar.absent_hours
                                    END > 0
                                    THEN cl.workload_hours - CASE
                                        WHEN ar.absent_hours < 0 THEN 0
                                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                                        ELSE ar.absent_hours
                                    END
                                    ELSE 0
                                END
                            END
                        ),
                        0
                    ) AS NUMERIC
                ) * 100.0
            ) / CAST(
                SUM(CASE WHEN ar.id IS NOT NULL THEN cl.workload_hours ELSE 0 END) AS NUMERIC
            ),
            2
        )
    END AS attendance_percentage,
    CASE
        WHEN COALESCE(SUM(CASE WHEN ar.id IS NOT NULL THEN cl.workload_hours ELSE 0 END), 0) <= 0
        THEN 0
        WHEN (
            (
                CAST(
                    COALESCE(
                        SUM(
                            CASE
                                WHEN ar.id IS NULL THEN 0
                                WHEN ar.status IN ('PRESENT', 'JUSTIFIED') THEN cl.workload_hours
                                ELSE CASE
                                    WHEN cl.workload_hours - CASE
                                        WHEN ar.absent_hours < 0 THEN 0
                                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                                        ELSE ar.absent_hours
                                    END > 0
                                    THEN cl.workload_hours - CASE
                                        WHEN ar.absent_hours < 0 THEN 0
                                        WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                                        ELSE ar.absent_hours
                                    END
                                    ELSE 0
                                END
                            END
                        ),
                        0
                    ) AS NUMERIC
                ) * 100.0
            ) / CAST(
                SUM(CASE WHEN ar.id IS NOT NULL THEN cl.workload_hours ELSE 0 END) AS NUMERIC
            )
        ) < 78.00
        THEN 1
        ELSE 0
    END AS is_attendance_critical
FROM enrollments e
JOIN classes c ON c.id = e.class_id
JOIN subjects s ON s.course_id = c.course_id
JOIN learning_modules lm ON lm.subject_id = s.id
LEFT JOIN class_lessons cl
    ON cl.class_id = e.class_id
    AND cl.subject_id = s.id
    AND cl.module_id = lm.id
LEFT JOIN attendance_records ar
    ON ar.lesson_id = cl.id
    AND ar.student_id = e.student_id
GROUP BY
    e.id,
    e.student_id,
    e.class_id,
    c.code,
    c.period,
    e.status,
    s.id,
    s.code,
    s.name,
    s.workload_hours,
    lm.id,
    lm.title,
    lm.order_index,
    lm.practical_hours
"""

vw_module_attendance_risk_table = table(
    VW_MODULE_ATTENDANCE_RISK_NAME,
    column("enrollment_id", Uuid(as_uuid=True)),
    column("student_id", Uuid(as_uuid=True)),
    column("class_id", Uuid(as_uuid=True)),
    column("class_code", String),
    column("class_period", String),
    column("enrollment_status", String),
    column("subject_id", Uuid(as_uuid=True)),
    column("subject_code", String),
    column("subject_name", String),
    column("subject_planned_hours", Integer),
    column("module_id", Uuid(as_uuid=True)),
    column("module_title", String),
    column("module_order_index", Integer),
    column("module_planned_hours", Integer),
    column("total_hours", Integer),
    column("attended_hours", Integer),
    column("absent_hours", Integer),
    column("justified_absent_hours", Integer),
    column("attendance_percentage", Numeric(5, 2)),
    column("is_attendance_critical", Boolean),
)

_VW_REQUIRED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "enrollments",
        "classes",
        "subjects",
        "learning_modules",
        "class_lessons",
        "attendance_records",
    }
)


@event.listens_for(Base.metadata, "after_create")
def _create_vw_module_attendance_risk(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Cria a view analítica vw_module_attendance_risk (DB-037) após a criação das tabelas base."""
    existing_tables = set(inspect(connection).get_table_names())
    if _VW_REQUIRED_TABLES.issubset(existing_tables):
        connection.execute(text(VW_MODULE_ATTENDANCE_RISK_DROP_SQL))
        connection.execute(text(VW_MODULE_ATTENDANCE_RISK_CREATE_SQL))


@event.listens_for(Base.metadata, "before_drop")
def _drop_vw_module_attendance_risk(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Remove a view vw_module_attendance_risk antes do drop das tabelas base."""
    connection.execute(text(VW_MODULE_ATTENDANCE_RISK_DROP_SQL))


__all__ = [
    "AttendanceRecord",
    "ClassLesson",
    "VW_MODULE_ATTENDANCE_RISK_CREATE_SQL",
    "VW_MODULE_ATTENDANCE_RISK_DROP_SQL",
    "VW_MODULE_ATTENDANCE_RISK_NAME",
    "vw_module_attendance_risk_table",
]
