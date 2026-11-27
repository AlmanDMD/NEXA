"""Schemas Pydantic v2 para Registro e Consulta de Observações Pedagógicas com Acesso Restrito e Criptografia (BE-045)."""

from datetime import date, datetime
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import NoteCategory, NoteVisibilityScope, UserRole
from app.schemas.validators import sanitize_text


def validate_pedagogical_note_content_pt(value: Any) -> str:
    """Sanitiza e valida o conteúdo da observação pedagógica restrita (5 a 5000 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=False)
    if len(cleaned) < 5:
        raise PydanticCustomError(
            "pedagogical_note_content_too_short",
            "O conteúdo da observação pedagógica (note_content) deve ter pelo menos 5 caracteres.",
        )
    if len(cleaned) > 5000:
        raise PydanticCustomError(
            "pedagogical_note_content_too_long",
            "O conteúdo da observação pedagógica (note_content) deve ter no máximo 5000 caracteres.",
        )
    return cleaned


def validate_note_visibility_scope_pt(value: Any) -> NoteVisibilityScope:
    """Valida e normaliza o escopo de visibilidade da observação pedagógica."""
    if isinstance(value, NoteVisibilityScope):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return NoteVisibilityScope(normalized)
        except ValueError as exc:
            raise PydanticCustomError(
                "note_visibility_scope_invalid",
                "O escopo de visibilidade (visibility_scope) deve ser 'PRIVATE_AUTHOR', 'TEACHERS_AND_COORD' ou 'COORDINATION_ONLY'.",
            ) from exc
    raise PydanticCustomError(
        "note_visibility_scope_invalid",
        "O escopo de visibilidade (visibility_scope) deve ser 'PRIVATE_AUTHOR', 'TEACHERS_AND_COORD' ou 'COORDINATION_ONLY'.",
    )


def validate_optional_note_visibility_scope_pt(
    value: Any,
) -> NoteVisibilityScope | None:
    """Valida filtro opcional de visibility_scope tratando string vazia como None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_note_visibility_scope_pt(value)


def validate_note_category_pt(value: Any) -> NoteCategory:
    """Valida e normaliza a categoria da observação pedagógica."""
    if isinstance(value, NoteCategory):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return NoteCategory(normalized)
        except ValueError as exc:
            raise PydanticCustomError(
                "note_category_invalid",
                "A categoria da observação (category) deve ser 'INTERVENTION', 'MENTORING', 'BEHAVIORAL' ou 'ACCOMMODATION'.",
            ) from exc
    raise PydanticCustomError(
        "note_category_invalid",
        "A categoria da observação (category) deve ser 'INTERVENTION', 'MENTORING', 'BEHAVIORAL' ou 'ACCOMMODATION'.",
    )


def validate_optional_note_category_pt(value: Any) -> NoteCategory | None:
    """Valida filtro opcional de category tratando string vazia como None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_note_category_pt(value)


def validate_optional_followup_date_pt(value: Any) -> date | None:
    """Valida e converte followup_date opcional para date ISO-8601 (YYYY-MM-DD)."""
    if value is None:
        return None
    error_message = (
        "Data de acompanhamento (followup_date) inválida. Informe uma data no formato YYYY-MM-DD."
    )
    if isinstance(value, bool):
        raise PydanticCustomError("note_followup_date_invalid", error_message)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        cleaned = sanitize_text(value, collapse_spaces=False)
        if not cleaned:
            return None
        try:
            if "T" in cleaned:
                normalized = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
                return datetime.fromisoformat(normalized).date()
            return date.fromisoformat(cleaned)
        except ValueError as exc:
            raise PydanticCustomError(
                "note_followup_date_invalid",
                error_message,
            ) from exc
    raise PydanticCustomError("note_followup_date_invalid", error_message)


type PedagogicalNoteContentStr = Annotated[
    str,
    BeforeValidator(validate_pedagogical_note_content_pt),
    Field(
        description="Conteúdo sigiloso da observação pedagógica (5 a 5000 caracteres — armazenado criptografado com Fernet/AES-256)",
        examples=[
            "Realizada conversa individual e mentoria de bancada com o estudante sobre calibração do micrômetro externo."
        ],
    ),
]

type NoteVisibilityScopeField = Annotated[
    NoteVisibilityScope,
    BeforeValidator(validate_note_visibility_scope_pt),
    Field(
        description="Escopo estrito de visibilidade (PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY)",
        examples=[NoteVisibilityScope.TEACHERS_AND_COORD],
    ),
]

type NoteCategoryField = Annotated[
    NoteCategory,
    BeforeValidator(validate_note_category_pt),
    Field(
        description="Categoria do acompanhamento pedagógico (INTERVENTION, MENTORING, BEHAVIORAL, ACCOMMODATION)",
        examples=[NoteCategory.INTERVENTION],
    ),
]

type OptionalFollowupDateField = Annotated[
    date | None,
    BeforeValidator(validate_optional_followup_date_pt),
    Field(
        description="Data prevista para retorno ou acompanhamento pedagógico (YYYY-MM-DD)",
        examples=["2026-06-15"],
    ),
]


class PedagogicalNoteCreateSchema(StrictRequestSchema):
    """Payload de entrada para registro de observação pedagógica restrita e criptografada (POST /api/v1/pedagogical-notes - BE-045)."""

    student_id: UUID = Field(
        description="Identificador UUID do estudante acompanhado",
    )
    enrollment_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional da matrícula do estudante (resolvido automaticamente quando omitido)",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional da turma para resolver a matrícula do estudante",
    )
    visibility_scope: NoteVisibilityScopeField = NoteVisibilityScope.PRIVATE_AUTHOR
    category: NoteCategoryField
    note_content: PedagogicalNoteContentStr
    requires_followup: bool = Field(
        default=False,
        description="Indica se a observação exige acompanhamento/retorno agendado",
    )
    followup_date: OptionalFollowupDateField = None

    @model_validator(mode="after")
    def validate_followup_consistency(self) -> Self:
        """Sincroniza e valida consistência entre requires_followup e followup_date."""
        if self.followup_date is not None and not self.requires_followup:
            if "requires_followup" in self.model_fields_set:
                raise PydanticCustomError(
                    "pedagogical_note_followup_inconsistent",
                    "Quando 'followup_date' é informada, 'requires_followup' deve ser True.",
                )
            self.requires_followup = True
        return self


class PedagogicalNoteStudentSummarySchema(BaseResponseSchema):
    """Resumo cadastral do estudante vinculado à observação pedagógica."""

    id: UUID = Field(description="Identificador UUID do estudante")
    email: str = Field(description="E-mail institucional do estudante")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do estudante",
    )
    registration_number: str | None = Field(
        default=None,
        description="Matrícula acadêmica SENAI do estudante",
    )


class PedagogicalNoteAuthorSummarySchema(BaseResponseSchema):
    """Resumo cadastral do docente, coordenador ou administrador autor da observação."""

    id: UUID = Field(description="Identificador UUID do autor")
    email: str = Field(description="E-mail institucional do autor")
    role: UserRole = Field(description="Papel institucional do autor")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do autor",
    )


class PedagogicalNoteResponseSchema(BaseResponseSchema):
    """Contrato de saída de uma observação pedagógica restrita após descriptografia autorizada (BE-045)."""

    id: UUID = Field(description="Identificador UUID da observação em pedagogical_notes")
    student_id: UUID = Field(description="Identificador UUID do estudante acompanhado")
    enrollment_id: UUID = Field(
        description="Identificador UUID da matrícula vinculada ao estudante",
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica da matrícula",
    )
    author_id: UUID = Field(
        description="Identificador UUID do professor ou coordenador autor",
    )
    visibility_scope: NoteVisibilityScope = Field(
        description="Escopo estrito de visibilidade (PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY)",
    )
    category: NoteCategory = Field(
        description="Categoria do acompanhamento (INTERVENTION, MENTORING, BEHAVIORAL, ACCOMMODATION)",
    )
    note_content: str = Field(
        description="Conteúdo descriptografado em memória exclusivamente para usuário autorizado pelo visibility_scope",
    )
    is_encrypted_at_rest: bool = Field(
        default=True,
        description="Confirma que o conteúdo está armazenado criptografado com Fernet/AES-256 no banco de dados",
    )
    requires_followup: bool = Field(
        description="Indica necessidade de retorno ou acompanhamento agendado",
    )
    followup_date: date | None = Field(
        default=None,
        description="Data prevista para o retorno/acompanhamento pedagógico",
    )
    created_at: datetime = Field(description="Data/hora UTC de registro da observação")
    updated_at: datetime = Field(
        description="Data/hora UTC da última atualização da observação",
    )
    student: PedagogicalNoteStudentSummarySchema = Field(
        description="Dados resumidos do estudante acompanhado",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Dados resumidos da turma acadêmica da matrícula",
    )
    author: PedagogicalNoteAuthorSummarySchema = Field(
        description="Dados resumidos do autor da observação",
    )


class PedagogicalNoteListQueryParams(StrictRequestSchema):
    """Parâmetros de paginação e filtros para GET /api/v1/students/{id}/pedagogical-notes (BE-045)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de observações por página (1 a 100)",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    enrollment_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da matrícula do estudante",
    )
    visibility_scope: Annotated[
        NoteVisibilityScope | None,
        BeforeValidator(validate_optional_note_visibility_scope_pt),
        Field(
            default=None,
            description="Filtro opcional pelo escopo de visibilidade",
        ),
    ] = None
    category: Annotated[
        NoteCategory | None,
        BeforeValidator(validate_optional_note_category_pt),
        Field(
            default=None,
            description="Filtro opcional pela categoria da observação",
        ),
    ] = None
    requires_followup: bool | None = Field(
        default=None,
        description="Filtro opcional por observações com acompanhamento agendado",
    )


type PedagogicalNoteListParamsDep = Annotated[
    PedagogicalNoteListQueryParams,
    Query(),
]


class PedagogicalNotePaginatedResponseSchema(BaseResponseSchema):
    """Lista paginada de observações pedagógicas restritas filtradas estritamente por visibility_scope (BE-045)."""

    data: list[PedagogicalNoteResponseSchema] = Field(
        default_factory=list,
        description="Observações pedagógicas autorizadas para o perfil e escopo do usuário autenticado",
    )
    total: int = Field(
        ge=0,
        description="Total de observações visíveis para o usuário autenticado",
    )
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite máximo de itens por página")
    total_pages: int = Field(
        ge=0,
        description="Quantidade total de páginas disponíveis",
    )


__all__ = [
    "NoteCategoryField",
    "NoteVisibilityScopeField",
    "OptionalFollowupDateField",
    "PedagogicalNoteAuthorSummarySchema",
    "PedagogicalNoteContentStr",
    "PedagogicalNoteCreateSchema",
    "PedagogicalNoteListParamsDep",
    "PedagogicalNoteListQueryParams",
    "PedagogicalNotePaginatedResponseSchema",
    "PedagogicalNoteResponseSchema",
    "PedagogicalNoteStudentSummarySchema",
    "validate_note_category_pt",
    "validate_note_visibility_scope_pt",
    "validate_optional_followup_date_pt",
    "validate_optional_note_category_pt",
    "validate_optional_note_visibility_scope_pt",
    "validate_pedagogical_note_content_pt",
]
