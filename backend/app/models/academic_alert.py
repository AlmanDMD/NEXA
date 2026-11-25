"""Modelo ORM para Alertas Acadêmicos (DB-034) e View Analítica 360° (vw_student_360_performance - DB-036)."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Final
from uuid import UUID

from sqlalchemy import (
    JSON,
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
    Uuid,
    column,
    event,
    func,
    inspect,
    table,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base, UUIDPrimaryKeyMixin, _utc_now
from app.schemas.enums import AlertCategory, AlertStatus, RiskLevel

if TYPE_CHECKING:
    from app.models.academic_class import AcademicClass
    from app.models.enrollment import Enrollment
    from app.models.learning_module import LearningModule
    from app.models.user import User


class AcademicAlert(Base, UUIDPrimaryKeyMixin):
    """Entidade de alerta precoce e explicável de risco acadêmico (tabela 'academic_alerts' - DB-034)."""

    __tablename__ = "academic_alerts"
    __table_args__ = (
        CheckConstraint(
            "length(trim(explainable_reason)) >= 5",
            name="chk_academic_alerts_reason_not_empty",
        ),
        Index(
            "idx_academic_alerts_class_status_risk",
            "class_id",
            "status",
            "risk_level",
        ),
        Index("idx_academic_alerts_enrollment_status", "enrollment_id", "status"),
        Index("idx_academic_alerts_student_status", "student_id", "status"),
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
    class_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    module_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum", native_enum=True),
        nullable=False,
    )
    alert_category: Mapped[AlertCategory] = mapped_column(
        SAEnum(AlertCategory, name="alert_category_enum", native_enum=True),
        nullable=False,
    )
    explainable_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    metric_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, name="alert_status_enum", native_enum=True),
        default=AlertStatus.ACTIVE,
        server_default=AlertStatus.ACTIVE.value,
        nullable=False,
    )
    resolved_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    enrollment: Mapped["Enrollment"] = relationship("Enrollment")
    academic_class: Mapped["AcademicClass"] = relationship("AcademicClass")
    module: Mapped["LearningModule | None"] = relationship("LearningModule")
    resolver: Mapped["User | None"] = relationship("User", foreign_keys=[resolved_by])

    @validates("explainable_reason")
    def _validate_explainable_reason(self, _key: str, value: str) -> str:
        """Exige justificativa transparente e legível com ao menos 5 caracteres."""
        if not isinstance(value, str):
            raise ValueError("O motivo explicável (explainable_reason) deve ser um texto válido.")
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "O motivo explicável (explainable_reason) deve ter ao menos 5 caracteres."
            )
        return normalized

    @validates("resolution_notes")
    def _validate_resolution_notes(self, _key: str, value: str | None) -> str | None:
        """Normaliza notas opcionais de resolução."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("As notas de resolução (resolution_notes) devem ser um texto válido.")
        normalized = value.strip()
        return normalized or None


VW_STUDENT_360_PERFORMANCE_NAME: Final[str] = "vw_student_360_performance"

VW_STUDENT_360_PERFORMANCE_DROP_SQL: Final[str] = (
    f"DROP VIEW IF EXISTS {VW_STUDENT_360_PERFORMANCE_NAME}"
)

VW_STUDENT_360_PERFORMANCE_CREATE_SQL: Final[str] = f"""
CREATE VIEW {VW_STUDENT_360_PERFORMANCE_NAME} AS
SELECT
    e.id AS enrollment_id,
    e.student_id AS student_id,
    u.email AS student_email,
    up.full_name AS student_full_name,
    up.registration_number AS registration_number,
    up.avatar_url AS avatar_url,
    e.class_id AS class_id,
    c.code AS class_code,
    c.period AS class_period,
    c.shift AS class_shift,
    c.status AS class_status,
    co.id AS course_id,
    co.code AS course_code,
    co.name AS course_name,
    e.status AS enrollment_status,
    e.enrollment_date AS enrollment_date,
    e.final_grade AS stored_final_grade,
    COALESCE(
        e.final_grade,
        CASE
            WHEN (COALESCE(g_agg.grade_weight_sum, 0) + COALESCE(t_agg.evaluated_score_count, 0)) <= 0
            THEN NULL
            ELSE ROUND(
                (
                    CAST(COALESCE(g_agg.weighted_grade_sum, 0) AS NUMERIC)
                    + CAST(COALESCE(t_agg.evaluated_score_sum, 0) AS NUMERIC)
                )
                / (
                    CAST(COALESCE(g_agg.grade_weight_sum, 0) AS NUMERIC)
                    + CAST(COALESCE(t_agg.evaluated_score_count, 0) AS NUMERIC)
                ),
                2
            )
        END
    ) AS overall_average,
    COALESCE(att_agg.total_lesson_hours, 0) AS total_lesson_hours,
    COALESCE(att_agg.attended_hours, 0) AS attended_hours,
    COALESCE(att_agg.absent_hours, 0) AS absent_hours,
    COALESCE(
        e.attendance_rate,
        CASE
            WHEN COALESCE(att_agg.total_lesson_hours, 0) <= 0
            THEN 100.00
            ELSE ROUND(
                (CAST(COALESCE(att_agg.attended_hours, 0) AS NUMERIC) * 100.0)
                / CAST(att_agg.total_lesson_hours AS NUMERIC),
                2
            )
        END
    ) AS attendance_percentage,
    COALESCE(t_agg.total_tasks_count, 0) AS total_tasks_count,
    COALESCE(t_agg.pending_tasks_count, 0) AS pending_tasks_count,
    COALESCE(t_agg.late_tasks_count, 0) AS late_tasks_count,
    COALESCE(t_agg.submitted_tasks_count, 0) AS submitted_tasks_count,
    COALESCE(t_agg.evaluated_tasks_count, 0) AS evaluated_tasks_count,
    COALESCE(t_agg.completed_tasks_count, 0) AS completed_tasks_count,
    COALESCE(t_agg.on_time_completed_tasks_count, 0) AS on_time_completed_tasks_count,
    COALESCE(al_agg.active_alerts_count, 0) AS active_alerts_count,
    CASE
        WHEN COALESCE(al_agg.max_alert_rank, 0) = 4 THEN 'CRITICAL'
        WHEN COALESCE(
            e.attendance_rate,
            CASE
                WHEN COALESCE(att_agg.total_lesson_hours, 0) <= 0 THEN 100.00
                ELSE (CAST(COALESCE(att_agg.attended_hours, 0) AS NUMERIC) * 100.0)
                     / CAST(att_agg.total_lesson_hours AS NUMERIC)
            END
        ) < 75.00 THEN 'CRITICAL'
        WHEN COALESCE(al_agg.max_alert_rank, 0) = 3 THEN 'HIGH'
        WHEN COALESCE(
            e.attendance_rate,
            CASE
                WHEN COALESCE(att_agg.total_lesson_hours, 0) <= 0 THEN 100.00
                ELSE (CAST(COALESCE(att_agg.attended_hours, 0) AS NUMERIC) * 100.0)
                     / CAST(att_agg.total_lesson_hours AS NUMERIC)
            END
        ) < 78.00 THEN 'HIGH'
        WHEN COALESCE(
            e.final_grade,
            CASE
                WHEN (COALESCE(g_agg.grade_weight_sum, 0) + COALESCE(t_agg.evaluated_score_count, 0)) <= 0
                THEN NULL
                ELSE (
                    CAST(COALESCE(g_agg.weighted_grade_sum, 0) AS NUMERIC)
                    + CAST(COALESCE(t_agg.evaluated_score_sum, 0) AS NUMERIC)
                ) / (
                    CAST(COALESCE(g_agg.grade_weight_sum, 0) AS NUMERIC)
                    + CAST(COALESCE(t_agg.evaluated_score_count, 0) AS NUMERIC)
                )
            END
        ) < 6.00 THEN 'HIGH'
        WHEN COALESCE(al_agg.max_alert_rank, 0) = 2 THEN 'MODERATE'
        WHEN COALESCE(t_agg.late_tasks_count, 0) >= 2 THEN 'MODERATE'
        ELSE 'LOW'
    END AS risk_level
FROM enrollments e
JOIN users u ON u.id = e.student_id
LEFT JOIN user_profiles up ON up.user_id = u.id
JOIN classes c ON c.id = e.class_id
JOIN courses co ON co.id = c.course_id
LEFT JOIN (
    SELECT
        ar.enrollment_id AS enrollment_id,
        SUM(cl.workload_hours) AS total_lesson_hours,
        SUM(
            CASE
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
        ) AS attended_hours,
        SUM(
            CASE
                WHEN ar.status IN ('PRESENT', 'JUSTIFIED') THEN 0
                WHEN ar.absent_hours < 0 THEN 0
                WHEN ar.absent_hours > cl.workload_hours THEN cl.workload_hours
                ELSE ar.absent_hours
            END
        ) AS absent_hours
    FROM attendance_records ar
    JOIN class_lessons cl ON cl.id = ar.lesson_id
    GROUP BY ar.enrollment_id
) att_agg ON att_agg.enrollment_id = e.id
LEFT JOIN (
    SELECT
        ts.enrollment_id AS enrollment_id,
        COUNT(ts.id) AS total_tasks_count,
        SUM(
            CASE
                WHEN ts.status = 'PENDING' AND pt.due_date >= CURRENT_TIMESTAMP THEN 1
                ELSE 0
            END
        ) AS pending_tasks_count,
        SUM(
            CASE
                WHEN ts.status = 'LATE' OR (ts.status = 'PENDING' AND pt.due_date < CURRENT_TIMESTAMP) THEN 1
                ELSE 0
            END
        ) AS late_tasks_count,
        SUM(CASE WHEN ts.status = 'SUBMITTED' THEN 1 ELSE 0 END) AS submitted_tasks_count,
        SUM(CASE WHEN ts.status = 'EVALUATED' THEN 1 ELSE 0 END) AS evaluated_tasks_count,
        SUM(
            CASE
                WHEN ts.status IN ('SUBMITTED', 'EVALUATED') THEN 1
                ELSE 0
            END
        ) AS completed_tasks_count,
        SUM(
            CASE
                WHEN ts.status IN ('SUBMITTED', 'EVALUATED')
                     AND (ts.completed_at IS NULL OR ts.completed_at <= pt.due_date)
                THEN 1
                ELSE 0
            END
        ) AS on_time_completed_tasks_count,
        SUM(CASE WHEN ts.final_task_score IS NOT NULL THEN ts.final_task_score ELSE 0 END) AS evaluated_score_sum,
        SUM(CASE WHEN ts.final_task_score IS NOT NULL THEN 1 ELSE 0 END) AS evaluated_score_count
    FROM task_submissions ts
    JOIN practical_tasks pt ON pt.id = ts.task_id
    GROUP BY ts.enrollment_id
) t_agg ON t_agg.enrollment_id = e.id
LEFT JOIN (
    SELECT
        sg.enrollment_id AS enrollment_id,
        SUM(
            (
                CASE
                    WHEN sg.recovery_grade IS NOT NULL AND sg.recovery_grade > sg.grade_value
                    THEN sg.recovery_grade
                    ELSE sg.grade_value
                END
            ) * aa.weight
        ) AS weighted_grade_sum,
        SUM(aa.weight) AS grade_weight_sum
    FROM student_grades sg
    JOIN academic_assessments aa ON aa.id = sg.assessment_id
    GROUP BY sg.enrollment_id
) g_agg ON g_agg.enrollment_id = e.id
LEFT JOIN (
    SELECT
        al.enrollment_id AS enrollment_id,
        COUNT(al.id) AS active_alerts_count,
        MAX(
            CASE
                WHEN al.risk_level = 'CRITICAL' THEN 4
                WHEN al.risk_level = 'HIGH' THEN 3
                WHEN al.risk_level = 'MODERATE' THEN 2
                ELSE 1
            END
        ) AS max_alert_rank
    FROM academic_alerts al
    WHERE al.status = 'ACTIVE'
    GROUP BY al.enrollment_id
) al_agg ON al_agg.enrollment_id = e.id
"""

vw_student_360_performance_table = table(
    VW_STUDENT_360_PERFORMANCE_NAME,
    column("enrollment_id", Uuid(as_uuid=True)),
    column("student_id", Uuid(as_uuid=True)),
    column("student_email", String),
    column("student_full_name", String),
    column("registration_number", String),
    column("avatar_url", String),
    column("class_id", Uuid(as_uuid=True)),
    column("class_code", String),
    column("class_period", String),
    column("class_shift", String),
    column("class_status", String),
    column("course_id", Uuid(as_uuid=True)),
    column("course_code", String),
    column("course_name", String),
    column("enrollment_status", String),
    column("enrollment_date", Date),
    column("stored_final_grade", Numeric(4, 2)),
    column("overall_average", Numeric(4, 2)),
    column("total_lesson_hours", Integer),
    column("attended_hours", Integer),
    column("absent_hours", Integer),
    column("attendance_percentage", Numeric(5, 2)),
    column("total_tasks_count", Integer),
    column("pending_tasks_count", Integer),
    column("late_tasks_count", Integer),
    column("submitted_tasks_count", Integer),
    column("evaluated_tasks_count", Integer),
    column("completed_tasks_count", Integer),
    column("on_time_completed_tasks_count", Integer),
    column("active_alerts_count", Integer),
    column("risk_level", String),
)

_VW_360_REQUIRED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "enrollments",
        "users",
        "user_profiles",
        "classes",
        "courses",
        "class_lessons",
        "attendance_records",
        "practical_tasks",
        "task_submissions",
        "academic_assessments",
        "student_grades",
        "academic_alerts",
    }
)


@event.listens_for(Base.metadata, "after_create")
def _create_vw_student_360_performance(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Cria a view analítica vw_student_360_performance (DB-036) após a criação das tabelas base."""
    existing_tables = set(inspect(connection).get_table_names())
    if _VW_360_REQUIRED_TABLES.issubset(existing_tables):
        connection.execute(text(VW_STUDENT_360_PERFORMANCE_DROP_SQL))
        connection.execute(text(VW_STUDENT_360_PERFORMANCE_CREATE_SQL))


@event.listens_for(Base.metadata, "before_drop")
def _drop_vw_student_360_performance(
    _target: Any,
    connection: Connection,
    **_kw: Any,
) -> None:
    """Remove a view vw_student_360_performance antes do drop das tabelas base."""
    connection.execute(text(VW_STUDENT_360_PERFORMANCE_DROP_SQL))


__all__ = [
    "AcademicAlert",
    "VW_STUDENT_360_PERFORMANCE_CREATE_SQL",
    "VW_STUDENT_360_PERFORMANCE_DROP_SQL",
    "VW_STUDENT_360_PERFORMANCE_NAME",
    "vw_student_360_performance_table",
]
