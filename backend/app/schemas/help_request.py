"""Schemas Pydantic v2 para Abertura e Consulta de Solicitações de Apoio Confidenciais (BE-043)."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import (
    HelpRequestCategory,
    HelpRequestStatus,
    UserRole,
)
from app.schemas.validators import sanitize_text


def validate_help_request_subject_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o assunto da solicitação de apoio (3 a 150 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "help_request_title_too_short",
            "O assunto da solicitação (subject_title) deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "help_request_title_too_long",
            "O assunto da solicitação (subject_title) deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_help_request_description_pt(value: Any) -> str:
    """Sanitiza e valida a descrição detalhada da dificuldade relatada pelo aluno (10 a 5000 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=False)
    if len(cleaned) < 10:
        raise PydanticCustomError(
            "help_request_description_too_short",
            "A descrição da solicitação (description) deve ter pelo menos 10 caracteres.",
        )
    if len(cleaned) > 5000:
        raise PydanticCustomError(
            "help_request_description_too_long",
            "A descrição da solicitação (description) deve ter no máximo 5000 caracteres.",
        )
    return cleaned


def validate_help_request_category_pt(value: Any) -> HelpRequestCategory:
    """Valida e normaliza a categoria da solicitação de apoio."""
    if isinstance(value, HelpRequestCategory):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return HelpRequestCategory(normalized)
        except ValueError as exc:
            raise PydanticCustomError(
                "help_request_category_invalid",
                "A categoria da solicitação (category) deve ser 'TECHNICAL_DOUBT', 'PRACTICAL_DIFFICULTY' ou 'PERSONAL_PEDAGOGICAL'.",
            ) from exc
    raise PydanticCustomError(
        "help_request_category_invalid",
        "A categoria da solicitação (category) deve ser 'TECHNICAL_DOUBT', 'PRACTICAL_DIFFICULTY' ou 'PERSONAL_PEDAGOGICAL'.",
    )


def validate_optional_help_request_category_pt(
    value: Any,
) -> HelpRequestCategory | None:
    """Valida filtro opcional de categoria tratando string vazia como None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_help_request_category_pt(value)


def validate_help_request_status_pt(value: Any) -> HelpRequestStatus:
    """Valida e normaliza o status da solicitação de apoio."""
    if isinstance(value, HelpRequestStatus):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return HelpRequestStatus(normalized)
        except ValueError as exc:
            raise PydanticCustomError(
                "help_request_status_invalid",
                "O status da solicitação (status) deve ser 'OPEN', 'IN_PROGRESS', 'RESOLVED' ou 'CLOSED'.",
            ) from exc
    raise PydanticCustomError(
        "help_request_status_invalid",
        "O status da solicitação (status) deve ser 'OPEN', 'IN_PROGRESS', 'RESOLVED' ou 'CLOSED'.",
    )


def validate_optional_help_request_status_pt(
    value: Any,
) -> HelpRequestStatus | None:
    """Valida filtro opcional de status tratando string vazia como None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_help_request_status_pt(value)


type HelpRequestSubjectTitleStr = Annotated[
    str,
    BeforeValidator(validate_help_request_subject_title_pt),
    Field(
        description="Assunto resumido da solicitação de apoio (3 a 150 caracteres)",
        examples=["Dificuldade no ajuste de tolerância H7 com micrômetro externo"],
    ),
]

type HelpRequestDescriptionStr = Annotated[
    str,
    BeforeValidator(validate_help_request_description_pt),
    Field(
        description="Relato detalhado e confidencial da dúvida ou dificuldade prática (10 a 5000 caracteres)",
        examples=[
            "Estou com dificuldade para zerar o nônio do micrômetro centesimal antes de medir o eixo escalonado na bancada 03."
        ],
    ),
]

type HelpRequestCategoryField = Annotated[
    HelpRequestCategory,
    BeforeValidator(validate_help_request_category_pt),
    Field(
        description="Categoria do pedido de apoio (TECHNICAL_DOUBT, PRACTICAL_DIFFICULTY, PERSONAL_PEDAGOGICAL)",
        examples=[HelpRequestCategory.PRACTICAL_DIFFICULTY],
    ),
]


class HelpRequestCreateSchema(StrictRequestSchema):
    """Payload de entrada para abertura de solicitação confidencial de apoio pelo aluno (POST /api/v1/help-requests)."""

    subject_id: UUID = Field(
        description="Identificador UUID da disciplina técnica vinculada à solicitação",
    )
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático da disciplina",
    )
    category: HelpRequestCategoryField
    subject_title: HelpRequestSubjectTitleStr
    description: HelpRequestDescriptionStr
    is_confidential: bool = Field(
        default=True,
        description="Garante confidencialidade estrita perante outros estudantes (True por padrão)",
    )


class HelpRequestStudentSummarySchema(BaseResponseSchema):
    """Resumo cadastral do estudante solicitante do pedido de apoio."""

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


class HelpRequestTeacherSummarySchema(BaseResponseSchema):
    """Resumo cadastral do professor titular ou responsável alocado à solicitação."""

    id: UUID = Field(description="Identificador UUID do docente responsável")
    email: str = Field(description="E-mail institucional do docente")
    role: UserRole = Field(description="Papel institucional do responsável")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do docente responsável",
    )


class HelpRequestSubjectSummarySchema(BaseResponseSchema):
    """Resumo da disciplina técnica vinculada à solicitação de apoio."""

    id: UUID = Field(description="Identificador UUID da disciplina")
    code: str = Field(description="Código identificador da disciplina")
    name: str = Field(description="Nome oficial da disciplina")


class HelpRequestModuleSummarySchema(BaseResponseSchema):
    """Resumo do módulo de aprendizagem prática vinculado opcionalmente à solicitação."""

    id: UUID = Field(description="Identificador UUID do módulo prático")
    title: str = Field(description="Título do módulo de aprendizagem")
    order_index: int = Field(description="Ordem didática do módulo na disciplina")


class HelpRequestChatMessageResponseSchema(BaseResponseSchema):
    """Contrato de saída de mensagem contextualizada na solicitação de apoio (chat_messages - DB-044)."""

    id: UUID = Field(description="Identificador UUID da mensagem")
    help_request_id: UUID = Field(description="Identificador UUID da solicitação de apoio")
    sender_id: UUID = Field(description="Identificador UUID do usuário remetente")
    sender_role: UserRole = Field(description="Papel institucional do remetente")
    sender_name: str | None = Field(
        default=None,
        description="Nome completo do remetente",
    )
    message_body: str = Field(description="Conteúdo textual da mensagem")
    is_read: bool = Field(description="Indica se a mensagem já foi lida pelo destinatário")
    read_at: datetime | None = Field(
        default=None,
        description="Data/hora UTC de leitura da mensagem",
    )
    sent_at: datetime = Field(description="Data/hora UTC de envio da mensagem")


class HelpRequestResponseSchema(BaseResponseSchema):
    """Contrato completo de saída de uma solicitação confidencial de apoio pedagógico (BE-043)."""

    id: UUID = Field(description="Identificador UUID da solicitação em help_requests")
    student_id: UUID = Field(description="Identificador UUID do estudante solicitante")
    enrollment_id: UUID = Field(
        description="Identificador UUID da matrícula ativa do estudante na turma",
    )
    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica da matrícula",
    )
    subject_id: UUID = Field(description="Identificador UUID da disciplina técnica")
    module_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional do módulo prático",
    )
    assigned_teacher_id: UUID | None = Field(
        default=None,
        description="Identificador UUID do professor titular direcionado automaticamente",
    )
    category: HelpRequestCategory = Field(
        description="Categoria do pedido de apoio (TECHNICAL_DOUBT, PRACTICAL_DIFFICULTY, PERSONAL_PEDAGOGICAL)",
    )
    subject_title: str = Field(description="Assunto resumido da solicitação")
    description: str = Field(description="Relato detalhado da dificuldade")
    is_confidential: bool = Field(
        description="Indica proteção de confidencialidade perante outros estudantes",
    )
    status: HelpRequestStatus = Field(
        description="Status atual do chamado (OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
    )
    resolution_summary: str | None = Field(
        default=None,
        description="Resumo da orientação pedagógica registrada no encerramento",
    )
    created_at: datetime = Field(description="Data/hora UTC de abertura do chamado")
    updated_at: datetime = Field(description="Data/hora UTC da última atualização")
    closed_at: datetime | None = Field(
        default=None,
        description="Data/hora UTC de encerramento do chamado",
    )
    student: HelpRequestStudentSummarySchema = Field(
        description="Dados resumidos do estudante solicitante",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Dados resumidos da turma acadêmica do estudante",
    )
    subject: HelpRequestSubjectSummarySchema = Field(
        description="Dados resumidos da disciplina técnica",
    )
    module: HelpRequestModuleSummarySchema | None = Field(
        default=None,
        description="Dados resumidos do módulo prático, quando informado",
    )
    assigned_teacher: HelpRequestTeacherSummarySchema | None = Field(
        default=None,
        description="Dados resumidos do professor titular direcionado automaticamente",
    )
    unread_messages_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de mensagens não lidas enviadas pela outra parte na thread",
    )
    messages: list[HelpRequestChatMessageResponseSchema] = Field(
        default_factory=list,
        description="Histórico cronológico de mensagens internas da solicitação (chat_messages)",
    )


class HelpRequestListQueryParams(StrictRequestSchema):
    """Parâmetros de paginação e filtros para GET /api/v1/help-requests (BE-043)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de solicitações por página (1 a 100)",
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
        description="Filtro opcional pelo UUID do módulo de aprendizagem prática",
    )
    category: Annotated[
        HelpRequestCategory | None,
        BeforeValidator(validate_optional_help_request_category_pt),
        Field(
            default=None,
            description="Filtro opcional pela categoria do pedido",
        ),
    ] = None
    status: Annotated[
        HelpRequestStatus | None,
        BeforeValidator(validate_optional_help_request_status_pt),
        Field(
            default=None,
            description="Filtro opcional pelo status do chamado (OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
        ),
    ] = None


type HelpRequestListParamsDep = Annotated[
    HelpRequestListQueryParams,
    Query(),
]


class HelpRequestPaginatedResponseSchema(BaseResponseSchema):
    """Lista paginada de solicitações de apoio confidenciais com proteção anti-exposição (BE-043)."""

    data: list[HelpRequestResponseSchema] = Field(
        default_factory=list,
        description="Lista de solicitações de apoio visíveis estritamente ao usuário autenticado",
    )
    total: int = Field(
        ge=0,
        description="Total de solicitações encontradas para os filtros e escopo do usuário",
    )
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite máximo de itens por página")
    total_pages: int = Field(
        ge=0,
        description="Quantidade total de páginas disponíveis",
    )


__all__ = [
    "HelpRequestCategoryField",
    "HelpRequestChatMessageResponseSchema",
    "HelpRequestCreateSchema",
    "HelpRequestDescriptionStr",
    "HelpRequestListParamsDep",
    "HelpRequestListQueryParams",
    "HelpRequestModuleSummarySchema",
    "HelpRequestPaginatedResponseSchema",
    "HelpRequestResponseSchema",
    "HelpRequestStudentSummarySchema",
    "HelpRequestSubjectSummarySchema",
    "HelpRequestSubjectTitleStr",
    "HelpRequestTeacherSummarySchema",
    "validate_help_request_category_pt",
    "validate_help_request_description_pt",
    "validate_help_request_status_pt",
    "validate_help_request_subject_title_pt",
    "validate_optional_help_request_category_pt",
    "validate_optional_help_request_status_pt",
]
