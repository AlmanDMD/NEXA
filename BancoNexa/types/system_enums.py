"""
ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate` — CARD [DB-005]
Enumerações Globais de Sistema sincronizadas com os tipos ENUM nativos do PostgreSQL 16.
Compatíveis com FastAPI, Pydantic v2 e SQLAlchemy 2.0 (BE-005, BE-009).
"""

from enum import StrEnum

class Role(StrEnum):
    """Mapeado no PostgreSQL 16 como 'user_role_enum'."""
    ADMIN = "ADMIN"
    COORDINATOR = "COORDINATOR"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class EnrollmentStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'enrollment_status_enum'."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    SUSPENDED = "SUSPENDED"


class RiskLevel(StrEnum):
    """Mapeado no PostgreSQL 16 como 'risk_level_enum'."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SubmissionStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'submission_status_enum'."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    LATE = "LATE"


class HelpRequestStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'help_request_status_enum'."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Shift(StrEnum):
    """Mapeado no PostgreSQL 16 como 'shift_enum'."""
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    NIGHT = "NIGHT"


class ClassStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'class_status_enum'."""
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CompetencyCategory(StrEnum):
    """Mapeado no PostgreSQL 16 como 'competency_category_enum'."""
    TECHNICAL = "TECHNICAL"
    SAFETY = "SAFETY"
    PROCEDURAL = "PROCEDURAL"


class AttendanceStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'attendance_status_enum'."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    JUSTIFIED = "JUSTIFIED"


class AssessmentType(StrEnum):
    """Mapeado no PostgreSQL 16 como 'assessment_type_enum'."""
    EXAM = "EXAM"
    MICRO_EVALUATION = "MICRO_EVALUATION"
    PROJECT = "PROJECT"


class AlertCategory(StrEnum):
    """Mapeado no PostgreSQL 16 como 'alert_category_enum'."""
    ATTENDANCE = "ATTENDANCE"
    GRADE_DROP = "GRADE_DROP"
    PENDING_TASKS = "PENDING_TASKS"
    SELF_EVAL_GAP = "SELF_EVAL_GAP"


class AlertStatus(StrEnum):
    """Mapeado no PostgreSQL 16 como 'alert_status_enum'."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class DiagnosticType(StrEnum):
    """Mapeado no PostgreSQL 16 como 'diagnostic_type_enum'."""
    ALIGNED = "ALIGNED"
    OVERCONFIDENCE_RISK = "OVERCONFIDENCE_RISK"
    UNDERCONFIDENCE_SUPPORT = "UNDERCONFIDENCE_SUPPORT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class MilestoneType(StrEnum):
    """Mapeado no PostgreSQL 16 como 'milestone_type_enum'."""
    MODULE_COMPLETED = "MODULE_COMPLETED"
    SKILL_LEVEL_UP = "SKILL_LEVEL_UP"
    PERFECT_ATTENDANCE = "PERFECT_ATTENDANCE"
    RECOVERY_ACHIEVED = "RECOVERY_ACHIEVED"


class AnnouncementPriority(StrEnum):
    """Mapeado no PostgreSQL 16 como 'announcement_priority_enum'."""
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"


class HelpRequestCategory(StrEnum):
    """Mapeado no PostgreSQL 16 como 'help_request_category_enum'."""
    TECHNICAL_DOUBT = "TECHNICAL_DOUBT"
    PRACTICAL_DIFFICULTY = "PRACTICAL_DIFFICULTY"
    PERSONAL_PEDAGOGICAL = "PERSONAL_PEDAGOGICAL"


class NoteVisibilityScope(StrEnum):
    """Mapeado no PostgreSQL 16 como 'note_visibility_scope_enum'."""
    PRIVATE_AUTHOR = "PRIVATE_AUTHOR"
    TEACHERS_AND_COORD = "TEACHERS_AND_COORD"
    COORDINATION_ONLY = "COORDINATION_ONLY"


class NoteCategory(StrEnum):
    """Mapeado no PostgreSQL 16 como 'note_category_enum'."""
    INTERVENTION = "INTERVENTION"
    MENTORING = "MENTORING"
    BEHAVIORAL = "BEHAVIORAL"
    ACCOMMODATION = "ACCOMMODATION"

