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


__all__ = [
    "ClassStatus",
    "EnrollmentStatus",
    "RiskLevel",
    "Shift",
    "UserRole",
]
