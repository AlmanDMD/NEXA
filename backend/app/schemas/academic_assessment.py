"""Schemas Pydantic v2 para Avaliações Formativas e Lançamento de Notas em Lote (BE-027)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import AliasChoices, BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.academic_class import ISODate
from app.schemas.base import BaseResponseSchema, EntityResponseSchema, StrictRequestSchema
from app.schemas.class_lesson import LessonModuleSummarySchema, LessonSubjectSummarySchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import AssessmentType
from app.schemas.learning_module import _parse_decimal_two_places
from app.schemas.validators import sanitize_optional_text, sanitize_text

_DECIMAL_QUANTIZER: Decimal = Decimal("0.01")
_MIN_ASSESSMENT_WEIGHT: Decimal = Decimal("0.01")
_MAX_ASSESSMENT_WEIGHT: Decimal = Decimal("9.99")
_MIN_MAX_GRADE: Decimal = Decimal("1.00")
_MAX_MAX_GRADE: Decimal = Decimal("10.00")
_MIN_STUDENT_GRADE: Decimal = Decimal("0.00")
_MAX_STUDENT_GRADE: Decimal = Decimal("10.00")


def validate_assessment_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título da avaliação formativa ou prova (3 a 150 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "assessment_title_too_short",
            "O título da avaliação deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "assessment_title_too_long",
            "O título da avaliação deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_assessment_weight_pt(value: Any) -> Decimal:
    """Valida o peso da avaliação (weight) exigindo valor > 0.00 e <= 9.99."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="assessment_weight_invalid",
        error_message="O peso da avaliação (weight) deve ser maior que 0.00 e no máximo 9.99.",
    )
    if not (_MIN_ASSESSMENT_WEIGHT <= parsed <= _MAX_ASSESSMENT_WEIGHT):
        raise PydanticCustomError(
            "assessment_weight_out_of_range",
            "O peso da avaliação (weight) deve ser maior que 0.00 e no máximo 9.99.",
        )
    return parsed


def validate_assessment_max_grade_pt(value: Any) -> Decimal:
    """Valida a nota máxima da avaliação (max_grade) entre 1.00 e 10.00."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="assessment_max_grade_invalid",
        error_message="A nota máxima da avaliação (max_grade) deve estar entre 1.00 e 10.00.",
    )
    if not (_MIN_MAX_GRADE <= parsed <= _MAX_MAX_GRADE):
        raise PydanticCustomError(
            "assessment_max_grade_out_of_range",
            "A nota máxima da avaliação (max_grade) deve estar entre 1.00 e 10.00.",
        )
    return parsed


def validate_student_grade_value_pt(value: Any) -> Decimal:
    """Valida que a nota do estudante esteja estritamente entre 0.00 e 10.00."""
    parsed = _parse_decimal_two_places(
        value,
        error_code="student_grade_invalid",
        error_message="A nota da avaliação deve ser um número válido entre 0.00 e 10.00.",
    )
    if not (_MIN_STUDENT_GRADE <= parsed <= _MAX_STUDENT_GRADE):
        raise PydanticCustomError(
            "student_grade_out_of_range",
            "A nota da avaliação não pode ser menor que 0.00 nem maior que 10.00.",
        )
    return parsed


def validate_optional_recovery_grade_pt(value: Any) -> Decimal | None:
    """Valida a nota de recuperação opcional do estudante entre 0.00 e 10.00."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    parsed = _parse_decimal_two_places(
        value,
        error_code="recovery_grade_invalid",
        error_message="A nota de recuperação (recovery_grade) deve ser um número válido entre 0.00 e 10.00.",
    )
    if not (_MIN_STUDENT_GRADE <= parsed <= _MAX_STUDENT_GRADE):
        raise PydanticCustomError(
            "recovery_grade_out_of_range",
            "A nota de recuperação (recovery_grade) não pode ser menor que 0.00 nem maior que 10.00.",
        )
    return parsed


def validate_grade_comments_pt(value: Any) -> str | None:
    """Sanitiza observações opcionais da nota limitando a 1000 caracteres."""
    cleaned = sanitize_optional_text(value, collapse_spaces=True)
    if cleaned is None:
        return None
    if len(cleaned) > 1000:
        raise PydanticCustomError(
            "grade_comments_too_long",
            "As observações da nota (comments) devem ter no máximo 1000 caracteres.",
        )
    return cleaned


type AssessmentTitleStr = Annotated[
    str,
    BeforeValidator(validate_assessment_title_pt),
    Field(
        description="Título da prova, microavaliação ou projeto técnico (3 a 150 caracteres)",
        examples=["Prova Teórica de Leitura de Paquímetro e Micrômetro"],
    ),
]

type AssessmentWeightDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_assessment_weight_pt),
    Field(
        description="Peso ponderado da avaliação na composição da média (> 0.00 e <= 9.99)",
        examples=["2.00"],
    ),
]

type AssessmentMaxGradeDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_assessment_max_grade_pt),
    Field(
        description="Nota máxima da avaliação formativa entre 1.00 e 10.00 (padrão 10.00)",
        examples=["10.00"],
    ),
]

type StudentGradeValueDecimal = Annotated[
    Decimal,
    BeforeValidator(validate_student_grade_value_pt),
    Field(
        description="Nota obtida pelo estudante na avaliação (0.00 a 10.00)",
        examples=["7.50"],
    ),
]

type OptionalRecoveryGradeDecimal = Annotated[
    Decimal | None,
    BeforeValidator(validate_optional_recovery_grade_pt),
    Field(
        description="Nota de recuperação opcional obtida pelo estudante (0.00 a 10.00)",
        examples=["8.50"],
    ),
]

type OptionalGradeCommentsStr = Annotated[
    str | None,
    BeforeValidator(validate_grade_comments_pt),
    Field(
        description="Observações pedagógicas opcionais sobre a avaliação do estudante (até 1000 caracteres)",
        examples=["Recuperação realizada após revisão prática de leitura milesimal."],
    ),
]


class AcademicAssessmentCreateSchema(StrictRequestSchema):
    """Payload de criação de avaliação formativa, microavaliação ou prova (POST /api/v1/assessments)."""

    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica (classes)",
    )
    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica (subjects)",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático de aprendizagem (learning_modules)",
    )
    title: AssessmentTitleStr
    assessment_type: AssessmentType = Field(
        default=AssessmentType.EXAM,
        description="Tipo de avaliação formativa (EXAM, MICRO_EVALUATION, PROJECT)",
        examples=[AssessmentType.EXAM],
    )
    weight: AssessmentWeightDecimal = Field(
        default=Decimal("1.00"),
        description="Peso ponderado da avaliação (> 0.00 e <= 9.99, padrão 1.00)",
        examples=["1.00"],
    )
    application_date: ISODate = Field(
        description="Data de aplicação da avaliação (AAAA-MM-DD)",
        examples=["2026-04-15"],
    )
    max_grade: AssessmentMaxGradeDecimal = Field(
        default=Decimal("10.00"),
        description="Nota máxima da avaliação (1.00 a 10.00, padrão 10.00)",
        examples=["10.00"],
    )


class AcademicAssessmentResponseSchema(EntityResponseSchema):
    """Schema de saída detalhado de avaliação formativa com metadados de turma, disciplina e módulo."""

    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo prático vinculado (quando informado)",
    )
    title: str = Field(description="Título da avaliação formativa ou prova")
    assessment_type: AssessmentType = Field(
        description="Tipo da avaliação (EXAM, MICRO_EVALUATION, PROJECT)",
    )
    weight: Decimal = Field(description="Peso ponderado da avaliação")
    application_date: date = Field(description="Data de aplicação da avaliação")
    max_grade: Decimal = Field(description="Nota máxima da avaliação (1.00 a 10.00)")
    graded_students_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de alunos da turma com nota já lançada nesta avaliação",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica",
    )
    subject: LessonSubjectSummarySchema = Field(
        description="Resumo da disciplina técnica",
    )
    module: LessonModuleSummarySchema | None = Field(
        default=None,
        description="Resumo do módulo de aprendizagem prática (quando vinculado)",
    )

    @field_validator("weight", "max_grade", mode="after")
    @classmethod
    def quantize_decimals(cls, value: Decimal) -> Decimal:
        """Padroniza weight e max_grade com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


class AcademicAssessmentListQueryParams(StrictRequestSchema):
    """Filtros opcionais para listagem de avaliações formativas (GET /api/v1/assessments)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de avaliações por página (1 a 100)",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da disciplina técnica",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID do módulo prático",
    )
    assessment_type: AssessmentType | None = Field(
        default=None,
        description="Filtro opcional pelo tipo de avaliação (EXAM, MICRO_EVALUATION, PROJECT)",
    )


type AcademicAssessmentListParamsDep = Annotated[
    AcademicAssessmentListQueryParams,
    Query(),
]


class AcademicAssessmentPaginatedResponseSchema(BaseResponseSchema):
    """Envelope paginado { data, total, page, limit } para listagem de avaliações formativas."""

    data: list[AcademicAssessmentResponseSchema] = Field(
        default_factory=list,
        description="Lista de avaliações formativas ordenadas por application_date",
    )
    total: int = Field(ge=0, description="Total de avaliações encontradas")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite de registros por página")


class StudentGradeItemInputSchema(StrictRequestSchema):
    """Item individual de lançamento de nota e recuperação de um aluno na avaliação (BE-027)."""

    student_id: UUID = Field(
        description="Identificador UUID do estudante matriculado na turma da avaliação",
    )
    grade_value: StudentGradeValueDecimal
    recovery_grade: OptionalRecoveryGradeDecimal = None
    comments: OptionalGradeCommentsStr = None

    @field_validator("grade_value", mode="before")
    @classmethod
    def validate_grade_value(cls, value: Any) -> Decimal:
        return validate_student_grade_value_pt(value)

    @field_validator("recovery_grade", mode="before")
    @classmethod
    def validate_recovery_grade(cls, value: Any) -> Decimal | None:
        return validate_optional_recovery_grade_pt(value)


class BatchStudentGradesRequestSchema(StrictRequestSchema):
    """Payload de lançamento de notas e recuperações em lote (POST /api/v1/assessments/{id}/grades)."""

    grades: list[StudentGradeItemInputSchema] = Field(
        min_length=1,
        max_length=200,
        validation_alias=AliasChoices("grades", "records", "items"),
        description="Lista de notas individuais e de recuperação dos alunos da turma",
    )

    @model_validator(mode="after")
    def validate_unique_students(self) -> Self:
        """Impede envio duplicado do mesmo student_id dentro do mesmo lote de notas."""
        seen: set[UUID] = set()
        for item in self.grades:
            if item.student_id in seen:
                raise PydanticCustomError(
                    "duplicate_grade_student",
                    "O lançamento em lote contém student_id duplicado.",
                )
            seen.add(item.student_id)
        return self


class StudentGradeItemResponseSchema(EntityResponseSchema):
    """Registro de nota persistido em student_grades com cálculo da nota efetiva SENAI."""

    assessment_id: UUID = Field(description="Identificador UUID da avaliação formativa")
    enrollment_id: UUID = Field(description="Identificador UUID da matrícula do estudante")
    student_id: UUID = Field(description="Identificador UUID do estudante")
    recorded_by: UUID = Field(description="Identificador UUID do docente que lançou a nota")
    grade_value: Decimal = Field(
        description="Nota original obtida na avaliação (0.00 a 10.00)",
    )
    recovery_grade: Decimal | None = Field(
        default=None,
        description="Nota de recuperação opcional (0.00 a 10.00)",
    )
    effective_grade: Decimal = Field(
        description="Maior nota entre grade_value e recovery_grade conforme regra pedagógica SENAI",
    )
    is_recovery_applied: bool = Field(
        description="Indica se a nota de recuperação superou a nota original e foi adotada como effective_grade",
    )
    was_rectified: bool = Field(
        default=False,
        description="Indica se este lançamento retificou uma nota já existente (auditado em audit_logs)",
    )
    comments: str | None = Field(
        default=None,
        description="Observações pedagógicas opcionais sobre a nota",
    )

    @field_validator("grade_value", "effective_grade", mode="after")
    @classmethod
    def quantize_required_grades(cls, value: Decimal) -> Decimal:
        """Padroniza notas obrigatórias com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)

    @field_validator("recovery_grade", mode="after")
    @classmethod
    def quantize_optional_recovery(cls, value: Decimal | None) -> Decimal | None:
        """Padroniza recovery_grade com duas casas decimais quando presente."""
        if value is None:
            return None
        return value.quantize(_DECIMAL_QUANTIZER)


class BatchStudentGradesResponseSchema(BaseResponseSchema):
    """Resumo consolidado do lançamento em lote de notas de uma avaliação formativa (BE-027)."""

    assessment_id: UUID = Field(description="Identificador UUID da avaliação processada")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do módulo prático (quando vinculado)",
    )
    max_grade: Decimal = Field(description="Nota máxima configurada na avaliação")
    total_processed: int = Field(
        ge=0,
        description="Total de notas processadas no lote",
    )
    created_count: int = Field(
        ge=0,
        description="Quantidade de novos lançamentos de notas criados",
    )
    rectified_count: int = Field(
        ge=0,
        description="Quantidade de notas já existentes que sofreram retificação (registradas em audit_logs)",
    )
    grades: list[StudentGradeItemResponseSchema] = Field(
        default_factory=list,
        description="Lista das notas gravadas com effective_grade calculada pela regra SENAI",
    )

    @field_validator("max_grade", mode="after")
    @classmethod
    def quantize_max_grade(cls, value: Decimal) -> Decimal:
        """Padroniza max_grade com duas casas decimais."""
        return value.quantize(_DECIMAL_QUANTIZER)


__all__ = [
    "AcademicAssessmentCreateSchema",
    "AcademicAssessmentListParamsDep",
    "AcademicAssessmentListQueryParams",
    "AcademicAssessmentPaginatedResponseSchema",
    "AcademicAssessmentResponseSchema",
    "AssessmentMaxGradeDecimal",
    "AssessmentTitleStr",
    "AssessmentWeightDecimal",
    "BatchStudentGradesRequestSchema",
    "BatchStudentGradesResponseSchema",
    "OptionalGradeCommentsStr",
    "OptionalRecoveryGradeDecimal",
    "StudentGradeItemInputSchema",
    "StudentGradeItemResponseSchema",
    "StudentGradeValueDecimal",
    "validate_assessment_max_grade_pt",
    "validate_assessment_title_pt",
    "validate_assessment_weight_pt",
    "validate_grade_comments_pt",
    "validate_optional_recovery_grade_pt",
    "validate_student_grade_value_pt",
]
