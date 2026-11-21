"""Schemas Pydantic v2 para validação e serialização de Turmas Acadêmicas (BE-012)."""

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift
from app.schemas.validators import sanitize_optional_text, sanitize_text

_CLASS_CODE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._-]+$")
_ACADEMIC_PERIOD_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._/-]+$")
_ISO_DATE_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_PATTERN: re.Pattern[str] = re.compile(r"^[+-]?\d+$")
_DECIMAL_QUANTIZER = Decimal("0.01")


def validate_class_code_pt(value: Any) -> str:
    """Normaliza (UPPER + TRIM) e valida o código identificador da turma acadêmica."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "class_code_too_short",
            "O código da turma deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 40:
        raise PydanticCustomError(
            "class_code_too_long",
            "O código da turma deve ter no máximo 40 caracteres.",
        )
    if not _CLASS_CODE_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "class_code_invalid_format",
            "O código da turma deve conter apenas letras, números, pontos, underscores ou hífens.",
        )
    return cleaned


def validate_academic_period_pt(value: Any) -> str:
    """Normaliza (UPPER + TRIM) e valida o período letivo (ex: '2026.1', '2026/1')."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "class_period_too_short",
            "O período letivo deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 20:
        raise PydanticCustomError(
            "class_period_too_long",
            "O período letivo deve ter no máximo 20 caracteres.",
        )
    if not _ACADEMIC_PERIOD_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "class_period_invalid_format",
            "O período letivo deve conter apenas letras, números, pontos, barras, underscores ou hífens.",
        )
    return cleaned


def validate_max_students_pt(value: Any) -> int:
    """Garante que a capacidade máxima de alunos seja um inteiro entre 1 e 100."""
    if isinstance(value, bool):
        raise PydanticCustomError(
            "class_max_students_invalid",
            "A capacidade máxima de alunos deve ser um número inteiro entre 1 e 100.",
        )

    if isinstance(value, int):
        if 1 <= value <= 100:
            return value
        raise PydanticCustomError(
            "class_max_students_invalid",
            "A capacidade máxima de alunos deve ser um número inteiro entre 1 e 100.",
        )

    if isinstance(value, str):
        cleaned = value.strip()
        if _INT_PATTERN.fullmatch(cleaned):
            parsed = int(cleaned)
            if 1 <= parsed <= 100:
                return parsed

    raise PydanticCustomError(
        "class_max_students_invalid",
        "A capacidade máxima de alunos deve ser um número inteiro entre 1 e 100.",
    )


def validate_iso_date_pt(value: Any) -> date:
    """Valida data pura (sem datetime/int/bool/float) aceitando apenas date ou string AAAA-MM-DD."""
    if isinstance(value, datetime):
        raise PydanticCustomError(
            "invalid_date_format",
            "O valor deve ser uma data válida no formato AAAA-MM-DD.",
        )

    if isinstance(value, date):
        return value

    if isinstance(value, (bool, int, float)):
        raise PydanticCustomError(
            "invalid_date_format",
            "O valor deve ser uma data válida no formato AAAA-MM-DD.",
        )

    if isinstance(value, str):
        cleaned = sanitize_text(value, collapse_spaces=False)
        if _ISO_DATE_PATTERN.fullmatch(cleaned):
            try:
                return date.fromisoformat(cleaned)
            except ValueError as exc:
                raise PydanticCustomError(
                    "invalid_date_format",
                    "O valor deve ser uma data válida no formato AAAA-MM-DD.",
                ) from exc

    raise PydanticCustomError(
        "invalid_date_format",
        "O valor deve ser uma data válida no formato AAAA-MM-DD.",
    )


type ClassCodeStr = Annotated[
    str,
    BeforeValidator(validate_class_code_pt),
    Field(
        description="Código identificador da turma acadêmica (3 a 40 caracteres, único por período)",
        examples=["MEC-2026-1T"],
    ),
]

type AcademicPeriodStr = Annotated[
    str,
    BeforeValidator(validate_academic_period_pt),
    Field(
        description="Identificador do período letivo da turma (3 a 20 caracteres)",
        examples=["2026.1"],
    ),
]

type MaxStudentsInt = Annotated[
    int,
    BeforeValidator(validate_max_students_pt),
    Field(
        description="Capacidade máxima de estudantes matriculados na turma (1 a 100)",
        examples=[40],
    ),
]

type ISODate = Annotated[
    date,
    BeforeValidator(validate_iso_date_pt),
    Field(
        description="Data no formato ISO AAAA-MM-DD",
        examples=["2026-02-02"],
    ),
]


class AcademicClassCreateSchema(StrictRequestSchema):
    """Schema de entrada para criação de turma acadêmica (POST /api/v1/classes)."""

    course_id: UUID = Field(
        description="Identificador UUID do curso técnico ao qual a turma pertence",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    code: ClassCodeStr
    period: AcademicPeriodStr
    shift: Shift = Field(
        description="Turno de oferta da turma (MORNING, AFTERNOON, NIGHT)",
        examples=[Shift.MORNING],
    )
    max_students: MaxStudentsInt = Field(
        default=40,
        description="Capacidade máxima de alunos da turma (1 a 100, padrão 40)",
        examples=[40],
    )
    status: ClassStatus = Field(
        default=ClassStatus.PLANNING,
        description="Status inicial da turma no ciclo letivo (padrão PLANNING)",
        examples=[ClassStatus.PLANNING],
    )
    start_date: ISODate
    end_date: ISODate

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """Garante que a data de início letivo seja estritamente anterior à data de término."""
        if self.start_date >= self.end_date:
            raise PydanticCustomError(
                "invalid_date_range",
                "A data de início (start_date) deve ser anterior à data de término (end_date).",
            )
        return self


class AcademicClassStatusUpdateSchema(StrictRequestSchema):
    """Schema de entrada para atualização de status da turma (PATCH /api/v1/classes/{id}/status)."""

    status: ClassStatus = Field(
        description="Novo status da turma (PLANNING, ACTIVE, COMPLETED, ARCHIVED)",
        examples=[ClassStatus.ACTIVE],
    )


class CourseSummarySchema(BaseResponseSchema):
    """Resumo dos dados do curso técnico embutido na resposta da turma acadêmica."""

    id: UUID = Field(
        description="Identificador UUID do curso técnico",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    code: str = Field(
        description="Código único SENAI do curso técnico",
        examples=["TEC-MEC-01"],
    )
    name: str = Field(
        description="Nome oficial do curso técnico",
        examples=["Técnico em Mecânica"],
    )
    total_hours: int = Field(
        description="Carga horária total do curso em horas",
        examples=[1200],
    )
    is_active: bool = Field(
        description="Indica se o curso técnico está ativo",
        examples=[True],
    )


class AcademicClassResponseSchema(EntityResponseSchema):
    """Schema de saída detalhado de turma acadêmica com curso e ocupação de vagas."""

    course_id: UUID = Field(
        description="Identificador UUID do curso técnico vinculado",
    )
    code: str = Field(
        description="Código identificador da turma acadêmica",
        examples=["MEC-2026-1T"],
    )
    period: str = Field(
        description="Período letivo da turma",
        examples=["2026.1"],
    )
    shift: Shift = Field(
        description="Turno de oferta da turma",
        examples=[Shift.MORNING],
    )
    max_students: int = Field(
        ge=1,
        le=100,
        description="Capacidade máxima de estudantes na turma",
        examples=[40],
    )
    enrolled_students_count: int = Field(
        ge=0,
        description="Quantidade atual de estudantes com matrícula ativa na turma",
        examples=[28],
    )
    available_slots: int = Field(
        ge=0,
        description="Quantidade de vagas disponíveis (max_students - enrolled_students_count)",
        examples=[12],
    )
    status: ClassStatus = Field(
        description="Status atual do ciclo de vida da turma",
        examples=[ClassStatus.ACTIVE],
    )
    start_date: date = Field(
        description="Data de início do período letivo (AAAA-MM-DD)",
        examples=["2026-02-02"],
    )
    end_date: date = Field(
        description="Data de término do período letivo (AAAA-MM-DD)",
        examples=["2026-06-30"],
    )
    course: CourseSummarySchema = Field(
        description="Resumo do curso técnico vinculado à turma",
    )


class AcademicClassListQueryParams(StrictRequestSchema):
    """Parâmetros de consulta paginada e filtros para listagem de turmas (GET /api/v1/classes)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
        examples=[1],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de turmas por página (1 a 100)",
        examples=[20],
    )
    course_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do curso técnico",
    )
    period: str | None = Field(
        default=None,
        max_length=20,
        description="Filtro opcional pelo período letivo (ex: 2026.1)",
        examples=["2026.1"],
    )
    shift: Shift | None = Field(
        default=None,
        description="Filtro opcional pelo turno da turma (MORNING, AFTERNOON, NIGHT)",
    )
    status: ClassStatus | None = Field(
        default=None,
        description="Filtro opcional pelo status da turma (PLANNING, ACTIVE, COMPLETED, ARCHIVED)",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Termo de busca textual por código da turma, período ou código/nome do curso",
        examples=["MEC-2026"],
    )

    @field_validator("period", mode="before")
    @classmethod
    def sanitize_period_filter(cls, value: Any) -> str | None:
        cleaned = sanitize_optional_text(value, collapse_spaces=False)
        if cleaned is None:
            return None
        normalized = cleaned.upper()
        if len(normalized) > 20:
            raise PydanticCustomError(
                "class_period_too_long",
                "O período letivo deve ter no máximo 20 caracteres.",
            )
        return normalized

    @field_validator("search", mode="before")
    @classmethod
    def sanitize_search_term(cls, value: Any) -> str | None:
        cleaned = sanitize_optional_text(value, collapse_spaces=True)
        if cleaned is not None and len(cleaned) > 100:
            raise PydanticCustomError(
                "search_too_long",
                "O termo de busca deve ter no máximo 100 caracteres.",
            )
        return cleaned

    @property
    def offset(self) -> int:
        """Retorna o deslocamento (OFFSET) calculado para consultas SQLAlchemy."""
        return (self.page - 1) * self.limit


class AcademicClassPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de turmas acadêmicas."""

    data: list[AcademicClassResponseSchema] = Field(
        default_factory=list,
        description="Lista de turmas acadêmicas da página atual",
    )
    total: int = Field(
        ge=0,
        description="Total geral de turmas encontradas",
        examples=[6],
    )
    page: int = Field(
        ge=1,
        description="Página atual",
        examples=[1],
    )
    limit: int = Field(
        ge=1,
        le=100,
        description="Quantidade máxima de registros por página",
        examples=[20],
    )


type AcademicClassListParamsDep = Annotated[AcademicClassListQueryParams, Query()]


class ClassEnrolledStudentItemSchema(BaseResponseSchema):
    """Item da pauta de estudantes matriculados em uma turma (GET /api/v1/classes/{id}/students)."""

    id: UUID = Field(
        description="Identificador UUID do estudante (usuário)",
    )
    student_id: UUID = Field(
        description="Identificador UUID do estudante (alias explícito)",
    )
    enrollment_id: UUID = Field(
        description="Identificador UUID do registro de matrícula na turma",
    )
    full_name: str = Field(
        description="Nome completo do estudante cadastrado em user_profiles",
        examples=["Ana Clara Souza"],
    )
    email: str = Field(
        description="E-mail institucional do estudante",
        examples=["ana.souza@senai.br"],
    )
    registration_number: str | None = Field(
        default=None,
        description="Número de matrícula SENAI do estudante",
        examples=["SENAI-2026-0001"],
    )
    enrollment_date: date = Field(
        description="Data formal da matrícula (AAAA-MM-DD)",
        examples=["2026-02-02"],
    )
    status: EnrollmentStatus = Field(
        description="Status atual da matrícula (ACTIVE, COMPLETED, DROPPED, SUSPENDED)",
        examples=[EnrollmentStatus.ACTIVE],
    )
    attendance_rate: Decimal | None = Field(
        default=None,
        description="Frequência acumulada do estudante na turma (0.00 a 100.00%)",
        examples=["95.50"],
    )
    final_grade: Decimal | None = Field(
        default=None,
        description="Nota parcial ou final consolidada do estudante na turma (0.00 a 10.00)",
        examples=["8.75"],
    )

    @field_validator("attendance_rate", "final_grade", mode="after")
    @classmethod
    def quantize_optional_decimals(cls, value: Decimal | None) -> Decimal | None:
        """Padroniza valores decimais opcionais com 2 casas decimais."""
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class ClassStudentsListQueryParams(StrictRequestSchema):
    """Parâmetros opcionais de filtro para consulta da pauta de alunos da turma."""

    status: EnrollmentStatus | None = Field(
        default=None,
        description="Filtro opcional pelo status da matrícula (ACTIVE, COMPLETED, DROPPED, SUSPENDED)",
    )
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Filtro textual opcional por nome completo, matrícula SENAI ou e-mail do estudante",
        examples=["Ana"],
    )

    @field_validator("search", mode="before")
    @classmethod
    def sanitize_search_term(cls, value: Any) -> str | None:
        """Normaliza o termo de busca textual e limita a 100 caracteres."""
        cleaned = sanitize_optional_text(value, collapse_spaces=True)
        if cleaned is not None and len(cleaned) > 100:
            raise PydanticCustomError(
                "search_too_long",
                "O termo de busca deve ter no máximo 100 caracteres.",
            )
        return cleaned


class ClassStudentsResponseSchema(BaseResponseSchema):
    """Resposta da pauta de estudantes matriculados com metadados completos da turma."""

    academic_class: AcademicClassResponseSchema = Field(
        description="Metadados da turma acadêmica consultada com curso e vagas",
    )
    total: int = Field(
        ge=0,
        description="Quantidade total de estudantes retornados na pauta",
        examples=[28],
    )
    data: list[ClassEnrolledStudentItemSchema] = Field(
        default_factory=list,
        description="Lista de estudantes matriculados na turma ordenados alfabeticamente",
    )


type ClassStudentsListParamsDep = Annotated[ClassStudentsListQueryParams, Query()]

__all__ = [
    "AcademicClassCreateSchema",
    "AcademicClassListParamsDep",
    "AcademicClassListQueryParams",
    "AcademicClassPaginatedResponseSchema",
    "AcademicClassResponseSchema",
    "AcademicClassStatusUpdateSchema",
    "AcademicPeriodStr",
    "ClassCodeStr",
    "ClassEnrolledStudentItemSchema",
    "ClassStudentsListParamsDep",
    "ClassStudentsListQueryParams",
    "ClassStudentsResponseSchema",
    "CourseSummarySchema",
    "ISODate",
    "MaxStudentsInt",
    "validate_academic_period_pt",
    "validate_class_code_pt",
    "validate_iso_date_pt",
    "validate_max_students_pt",
]
