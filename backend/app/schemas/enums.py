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


__all__ = [
    "AssessmentType",
    "AttendanceStatus",
    "ClassStatus",
    "CompetencyCategory",
    "EnrollmentStatus",
    "RiskLevel",
    "Shift",
    "SubmissionStatus",
    "UserRole",
]
