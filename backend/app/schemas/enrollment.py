"""Schemas Pydantic v2 para validação e serialização de Matrículas de Estudantes (BE-016)."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.academic_class import validate_iso_date_pt
from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift, UserRole
from app.schemas.validators import sanitize_optional_text

_DECIMAL_QUANTIZER = Decimal("0.01")


class EnrollmentCreateSchema(StrictRequestSchema):
    """Schema de entrada para matrícula de estudante em turma (POST /api/v1/enrollments)."""

    student_id: UUID = Field(
        description="Identificador UUID do estudante (usuário com role STUDENT)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica ativa",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )
    enrollment_date: date | None = Field(
        default=None,
        description="Data de matrícula opcional no formato AAAA-MM-DD (padrão: data atual)",
        examples=["2026-02-02"],
    )

    @field_validator("enrollment_date", mode="before")
    @classmethod
    def validate_enrollment_date(cls, value: Any) -> date | None:
        if value is None:
            return None
        return validate_iso_date_pt(value)


class EnrollmentStudentSummarySchema(BaseResponseSchema):
    """Resumo dos dados do estudante matriculado embutido na resposta da matrícula."""

    id: UUID = Field(description="Identificador UUID do estudante")
    email: str = Field(description="E-mail institucional do estudante")
    role: UserRole = Field(description="Papel institucional do usuário")
    is_active: bool = Field(description="Indica se a conta do estudante está ativa")
    full_name: str | None = Field(default=None, description="Nome completo do estudante")
    registration_number: str | None = Field(
        default=None,
        description="Número de matrícula SENAI do estudante",
    )


class EnrollmentClassSummarySchema(BaseResponseSchema):
    """Resumo da turma acadêmica embutido na resposta da matrícula."""

    id: UUID = Field(description="Identificador UUID da turma acadêmica")
    course_id: UUID = Field(description="Identificador UUID do curso técnico vinculado")
    code: str = Field(description="Código identificador da turma", examples=["MEC-2026-1T"])
    period: str = Field(description="Período letivo da turma", examples=["2026.1"])
    shift: Shift = Field(description="Turno de oferta da turma", examples=[Shift.MORNING])
    max_students: int = Field(description="Capacidade máxima de estudantes da turma")
    status: ClassStatus = Field(description="Status atual da turma", examples=[ClassStatus.ACTIVE])
    start_date: date = Field(description="Data de início do período letivo")
    end_date: date = Field(description="Data de término do período letivo")


class EnrollmentResponseSchema(EntityResponseSchema):
    """Schema de saída detalhado para serialização de Enrollment do SQLAlchemy."""

    student_id: UUID = Field(description="Identificador UUID do estudante matriculado")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    enrollment_date: date = Field(description="Data formal da matrícula (AAAA-MM-DD)")
    status: EnrollmentStatus = Field(
        description="Status atual da matrícula",
        examples=[EnrollmentStatus.ACTIVE],
    )
    final_grade: Decimal | None = Field(
        default=None,
        description="Nota final consolidada (0.00 a 10.00)",
    )
    attendance_rate: Decimal | None = Field(
        default=None,
        description="Taxa de frequência consolidada (0.00 a 100.00%)",
    )
    student: EnrollmentStudentSummarySchema = Field(
        description="Resumo do estudante matriculado",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica vinculada",
    )

    @field_validator("final_grade", "attendance_rate", mode="after")
    @classmethod
    def quantize_optional_decimals(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class EnrollmentStatusUpdateSchema(StrictRequestSchema):
    """Schema de entrada para alteração de status de matrícula (PATCH /api/v1/enrollments/{id}/status)."""

    status: EnrollmentStatus = Field(
        description="Novo status da matrícula (ACTIVE, COMPLETED, DROPPED, SUSPENDED)",
        examples=[EnrollmentStatus.DROPPED],
    )
    justification: str | None = Field(
        default=None,
        max_length=500,
        description="Justificativa opcional para a alteração de status da matrícula",
        examples=["Solicitação formal de trancamento protocolada na secretaria."],
    )

    @field_validator("justification", mode="before")
    @classmethod
    def validate_justification_pt(cls, value: Any) -> str | None:
        """Sanitiza a justificativa opcional e valida comprimento/conteúdo seguro."""
        cleaned = sanitize_optional_text(value, collapse_spaces=True)
        if cleaned is None:
            return None
        if "<" in cleaned or ">" in cleaned:
            raise PydanticCustomError(
                "justification_invalid_chars",
                "A justificativa contém caracteres não permitidos.",
            )
        if len(cleaned) > 500:
            raise PydanticCustomError(
                "justification_too_long",
                "A justificativa deve ter no máximo 500 caracteres.",
            )
        return cleaned


__all__ = [
    "EnrollmentClassSummarySchema",
    "EnrollmentCreateSchema",
    "EnrollmentResponseSchema",
    "EnrollmentStatusUpdateSchema",
    "EnrollmentStudentSummarySchema",
]
