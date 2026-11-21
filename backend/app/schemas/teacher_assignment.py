"""Schemas Pydantic v2 para validação e serialização de Alocações Docentes (BE-018)."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema, UUIDResponseMixin
from app.schemas.enums import ClassStatus, Shift, UserRole


class TeacherAssignmentCreateSchema(StrictRequestSchema):
    """Schema de entrada para alocação de docente em turma e disciplina (POST /api/v1/teacher-assignments)."""

    teacher_id: UUID = Field(
        description="Identificador UUID do docente (usuário cadastrado com role TEACHER)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica de destino",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )
    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica vinculada ao curso da turma",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    )
    is_main_teacher: bool = Field(
        default=True,
        description="Indica se o docente é o professor titular (True) ou instrutor/apoio de oficina (False)",
        examples=[True],
    )

    @field_validator("is_main_teacher", mode="before")
    @classmethod
    def validate_strict_boolean(cls, value: Any) -> bool:
        """Exige valor estritamente booleano sem coerção implícita de inteiros ou strings."""
        if not isinstance(value, bool):
            raise PydanticCustomError(
                "invalid_is_main_teacher",
                "O campo is_main_teacher deve ser um booleano válido (true ou false).",
            )
        return value


class TeacherAssignmentTeacherSummarySchema(BaseResponseSchema):
    """Resumo dos dados do docente alocado embutido na resposta da atribuição."""

    id: UUID = Field(description="Identificador UUID do docente")
    email: str = Field(description="E-mail institucional do docente")
    role: UserRole = Field(description="Papel institucional do usuário")
    is_active: bool = Field(description="Indica se a conta do docente está ativa")
    full_name: str | None = Field(default=None, description="Nome completo do docente")
    registration_number: str | None = Field(
        default=None,
        description="Matrícula/registro funcional SENAI do docente",
    )


class TeacherAssignmentClassSummarySchema(BaseResponseSchema):
    """Resumo da turma acadêmica embutido na resposta da alocação docente."""

    id: UUID = Field(description="Identificador UUID da turma acadêmica")
    course_id: UUID = Field(description="Identificador UUID do curso técnico vinculado")
    code: str = Field(description="Código identificador da turma", examples=["MEC-2026-1T"])
    period: str = Field(description="Período letivo da turma", examples=["2026.1"])
    shift: Shift = Field(description="Turno de oferta da turma", examples=[Shift.MORNING])
    max_students: int = Field(description="Capacidade máxima de estudantes da turma")
    status: ClassStatus = Field(description="Status atual da turma", examples=[ClassStatus.ACTIVE])
    start_date: date = Field(description="Data de início do período letivo")
    end_date: date = Field(description="Data de término do período letivo")


class TeacherAssignmentSubjectSummarySchema(BaseResponseSchema):
    """Resumo da disciplina técnica embutido na resposta da alocação docente."""

    id: UUID = Field(description="Identificador UUID da disciplina técnica")
    course_id: UUID = Field(description="Identificador UUID do curso técnico vinculado")
    code: str = Field(description="Código único da disciplina no curso", examples=["USN-TOR-01"])
    name: str = Field(description="Nome oficial da disciplina", examples=["Usinagem e Tornearia"])
    workload_hours: int = Field(description="Carga horária total da disciplina em horas")
    is_active: bool = Field(description="Indica se a disciplina está ativa")


class TeacherAssignmentResponseSchema(UUIDResponseMixin, BaseResponseSchema):
    """Schema de saída detalhado para serialização de TeacherAssignment do SQLAlchemy."""

    teacher_id: UUID = Field(description="Identificador UUID do docente alocado")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    is_main_teacher: bool = Field(
        description="Indica se o docente atua como professor titular na oficina/disciplina",
    )
    assigned_at: datetime = Field(
        description="Data e hora da alocação docente (UTC ISO 8601)",
    )
    teacher: TeacherAssignmentTeacherSummarySchema = Field(
        description="Resumo do docente alocado",
    )
    academic_class: TeacherAssignmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica vinculada",
    )
    subject: TeacherAssignmentSubjectSummarySchema = Field(
        description="Resumo da disciplina técnica vinculada",
    )


__all__ = [
    "TeacherAssignmentClassSummarySchema",
    "TeacherAssignmentCreateSchema",
    "TeacherAssignmentResponseSchema",
    "TeacherAssignmentSubjectSummarySchema",
    "TeacherAssignmentTeacherSummarySchema",
]
