"""Enumerações de domínio sincronizadas com os tipos ENUM nativos do PostgreSQL 16 (DB-005)."""

from enum import StrEnum


class UserRole(StrEnum):
    """Papéis de controle de acesso baseado em função (RBAC) — 'user_role_enum'."""

    ADMIN = "ADMIN"
    COORDINATOR = "COORDINATOR"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class EnrollmentStatus(StrEnum):
    """Status de matrícula acadêmica — 'enrollment_status_enum'."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    SUSPENDED = "SUSPENDED"


class RiskLevel(StrEnum):
    """Nível de risco acadêmico — 'risk_level_enum'."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Shift(StrEnum):
    """Turno de oferta de turma — 'shift_enum'."""

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    NIGHT = "NIGHT"


class ClassStatus(StrEnum):
    """Status do ciclo de vida da turma — 'class_status_enum'."""

    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CompetencyCategory(StrEnum):
    """Categorias da taxonomia de competências técnicas SENAI — 'competency_category_enum'."""

    TECHNICAL = "TECHNICAL"
    SAFETY = "SAFETY"
    PROCEDURAL = "PROCEDURAL"


class AttendanceStatus(StrEnum):
    """Status de registro de presença em aula — 'attendance_status_enum'."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    JUSTIFIED = "JUSTIFIED"


class SubmissionStatus(StrEnum):
    """Status de entrega e avaliação de tarefa prática — 'submission_status_enum' (DB-025)."""

    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    LATE = "LATE"


class AssessmentType(StrEnum):
    """Tipos de avaliação formativa, prova teórica/prática ou projeto — 'assessment_type_enum' (DB-027)."""

    EXAM = "EXAM"
    MICRO_EVALUATION = "MICRO_EVALUATION"
    PROJECT = "PROJECT"


class AcademicStandingStatus(StrEnum):
    """Situação acadêmica consolidada por módulo, disciplina ou turma (BE-028)."""

    APPROVED = "APPROVED"
    IN_RECOVERY = "IN_RECOVERY"
    AT_RISK = "AT_RISK"


class AlertCategory(StrEnum):
    """Categorias de alertas precoces de risco acadêmico — 'alert_category_enum' (DB-034)."""

    ATTENDANCE = "ATTENDANCE"
    GRADE_DROP = "GRADE_DROP"
    PENDING_TASKS = "PENDING_TASKS"
    SELF_EVAL_GAP = "SELF_EVAL_GAP"


class AlertStatus(StrEnum):
    """Status do ciclo de acompanhamento de alertas acadêmicos — 'alert_status_enum' (DB-034)."""

    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class MilestoneType(StrEnum):
    """Tipos de marcos da linha do tempo acadêmica do estudante — 'milestone_type_enum' (DB-039)."""

    MODULE_COMPLETED = "MODULE_COMPLETED"
    SKILL_LEVEL_UP = "SKILL_LEVEL_UP"
    PERFECT_ATTENDANCE = "PERFECT_ATTENDANCE"
    RECOVERY_ACHIEVED = "RECOVERY_ACHIEVED"


class DiagnosticType(StrEnum):
    """Classificação do cruzamento diagnóstico entre autoavaliação e evidência docente — 'diagnostic_type_enum' (DB-035)."""

    ALIGNED = "ALIGNED"
    OVERCONFIDENCE_RISK = "OVERCONFIDENCE_RISK"
    UNDERCONFIDENCE_SUPPORT = "UNDERCONFIDENCE_SUPPORT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


__all__ = [
    "AcademicStandingStatus",
    "AlertCategory",
    "AlertStatus",
    "AssessmentType",
    "AttendanceStatus",
    "ClassStatus",
    "CompetencyCategory",
    "DiagnosticType",
    "EnrollmentStatus",
    "MilestoneType",
    "RiskLevel",
    "Shift",
    "SubmissionStatus",
    "UserRole",
]
