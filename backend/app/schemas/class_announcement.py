"""Schemas Pydantic v2 para Publicação, Edição e Fixação de Avisos no Mural da Turma (BE-041)."""

from datetime import date, datetime, time, timezone
from typing import Annotated, Any, Self
from uuid import UUID

from fastapi import Query
from pydantic import BeforeValidator, Field, model_validator
from pydantic_core import PydanticCustomError

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import AnnouncementPriority, UserRole
from app.schemas.validators import sanitize_text


def validate_announcement_title_pt(value: Any) -> str:
    """Sanitiza espaços e valida o título do comunicado oficial (3 a 150 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "announcement_title_too_short",
            "O título do aviso (title) deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "announcement_title_too_long",
            "O título do aviso (title) deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_announcement_content_pt(value: Any) -> str:
    """Sanitiza e valida o corpo completo do comunicado oficial (5 a 5000 caracteres)."""
    cleaned = sanitize_text(value, collapse_spaces=False)
    if len(cleaned) < 5:
        raise PydanticCustomError(
            "announcement_content_too_short",
            "O conteúdo do aviso (content) deve ter pelo menos 5 caracteres.",
        )
    if len(cleaned) > 5000:
        raise PydanticCustomError(
            "announcement_content_too_long",
            "O conteúdo do aviso (content) deve ter no máximo 5000 caracteres.",
        )
    return cleaned


def validate_announcement_priority_pt(value: Any) -> AnnouncementPriority:
    """Valida e normaliza a prioridade do aviso (NORMAL, IMPORTANT ou URGENT)."""
    if isinstance(value, AnnouncementPriority):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return AnnouncementPriority(normalized)
        except ValueError as exc:
            raise PydanticCustomError(
                "announcement_priority_invalid",
                "A prioridade do aviso (priority) deve ser 'NORMAL', 'IMPORTANT' ou 'URGENT'.",
            ) from exc
    raise PydanticCustomError(
        "announcement_priority_invalid",
        "A prioridade do aviso (priority) deve ser 'NORMAL', 'IMPORTANT' ou 'URGENT'.",
    )


def validate_optional_announcement_priority_pt(
    value: Any,
) -> AnnouncementPriority | None:
    """Valida filtro opcional de prioridade do aviso tratando string vazia como None."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_announcement_priority_pt(value)


def validate_announcement_expires_at_pt(value: Any) -> datetime | None:
    """Valida e normaliza a data/hora opcional de expiração do aviso para UTC."""
    if value is None:
        return None
    error_message = (
        "Data/hora de expiração (expires_at) inválida. Informe um valor no formato ISO-8601."
    )
    if isinstance(value, bool):
        raise PydanticCustomError("announcement_expires_at_invalid", error_message)

    if isinstance(value, datetime):
        parsed_dt = value
    elif isinstance(value, date):
        parsed_dt = datetime.combine(value, time(23, 59, 59), tzinfo=timezone.utc)
    elif isinstance(value, str):
        cleaned = sanitize_text(value, collapse_spaces=False)
        if not cleaned:
            return None
        normalized_iso = (
            cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
        )
        try:
            if "T" in normalized_iso or " " in normalized_iso:
                parsed_dt = datetime.fromisoformat(normalized_iso)
            else:
                parsed_date = date.fromisoformat(normalized_iso)
                parsed_dt = datetime.combine(
                    parsed_date,
                    time(23, 59, 59),
                    tzinfo=timezone.utc,
                )
        except ValueError as exc:
            raise PydanticCustomError(
                "announcement_expires_at_invalid",
                error_message,
            ) from exc
    else:
        raise PydanticCustomError("announcement_expires_at_invalid", error_message)

    if parsed_dt.tzinfo is None:
        return parsed_dt.replace(tzinfo=timezone.utc)
    return parsed_dt.astimezone(timezone.utc)


type AnnouncementTitleStr = Annotated[
    str,
    BeforeValidator(validate_announcement_title_pt),
    Field(
        description="Título do comunicado oficial no mural da turma (3 a 150 caracteres)",
        examples=["Uso obrigatório de óculos de proteção na aula prática de Torno"],
    ),
]

type AnnouncementContentStr = Annotated[
    str,
    BeforeValidator(validate_announcement_content_pt),
    Field(
        description="Conteúdo detalhado do comunicado oficial (5 a 5000 caracteres)",
        examples=[
            "Amanhã iniciaremos a usinagem prática no Laboratório 02. Todos os estudantes devem trazer jaleco e óculos de segurança."
        ],
    ),
]

type AnnouncementPriorityField = Annotated[
    AnnouncementPriority,
    BeforeValidator(validate_announcement_priority_pt),
    Field(
        description="Prioridade visual do aviso (NORMAL, IMPORTANT, URGENT)",
        examples=[AnnouncementPriority.IMPORTANT],
    ),
]

type OptionalAnnouncementExpiresAtDatetime = Annotated[
    datetime | None,
    BeforeValidator(validate_announcement_expires_at_pt),
    Field(
        description="Data/hora opcional de expiração do comunicado no mural (ISO-8601 UTC)",
        examples=["2026-06-30T23:59:59Z"],
    ),
]


class ClassAnnouncementCreateSchema(StrictRequestSchema):
    """Payload de entrada para criação de aviso oficial no mural da turma (POST /api/v1/announcements)."""

    class_id: UUID = Field(
        description="Identificador UUID da turma acadêmica destinatária do aviso",
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional da disciplina vinculada ao aviso (deve pertencer ao curso da turma)",
    )
    title: AnnouncementTitleStr
    content: AnnouncementContentStr
    priority: AnnouncementPriorityField = AnnouncementPriority.NORMAL
    is_pinned: bool = Field(
        default=False,
        description="Quando True, fixa o aviso no topo do mural da turma",
    )
    expires_at: OptionalAnnouncementExpiresAtDatetime = None


class ClassAnnouncementUpdateSchema(StrictRequestSchema):
    """Payload de entrada para edição ou fixação de aviso oficial no mural (PATCH /api/v1/announcements/{id})."""

    subject_id: UUID | None = Field(
        default=None,
        description="Permite vincular ou remover (null) a disciplina associada ao aviso",
    )
    title: AnnouncementTitleStr | None = None
    content: AnnouncementContentStr | None = None
    priority: AnnouncementPriorityField | None = None
    is_pinned: bool | None = Field(
        default=None,
        description="Permite fixar (True) ou desfixar (False) o aviso no topo do mural",
    )
    expires_at: OptionalAnnouncementExpiresAtDatetime = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> Self:
        """Garante que ao menos um campo editável tenha sido enviado no payload de atualização."""
        updatable = {
            "subject_id",
            "title",
            "content",
            "priority",
            "is_pinned",
            "expires_at",
        }
        if not (self.model_fields_set & updatable):
            raise PydanticCustomError(
                "empty_announcement_update",
                "Informe ao menos um campo para atualizar o aviso do mural.",
            )
        for non_nullable_field in ("title", "content", "priority", "is_pinned"):
            if (
                non_nullable_field in self.model_fields_set
                and getattr(self, non_nullable_field) is None
            ):
                raise PydanticCustomError(
                    "null_announcement_field",
                    f"O campo '{non_nullable_field}' não pode ser nulo na atualização do aviso.",
                )
        return self


class AnnouncementAuthorSummarySchema(BaseResponseSchema):
    """Resumo cadastral do docente, coordenador ou administrador autor do comunicado."""

    id: UUID = Field(description="Identificador UUID do autor do aviso")
    email: str = Field(description="E-mail institucional do autor")
    role: UserRole = Field(description="Papel institucional do autor")
    full_name: str | None = Field(
        default=None,
        description="Nome completo do autor do comunicado",
    )


class AnnouncementSubjectSummarySchema(BaseResponseSchema):
    """Resumo da disciplina técnica vinculada opcionalmente ao comunicado."""

    id: UUID = Field(description="Identificador UUID da disciplina")
    code: str = Field(description="Código identificador da disciplina")
    name: str = Field(description="Nome oficial da disciplina")


class ClassAnnouncementResponseSchema(BaseResponseSchema):
    """Contrato completo de saída de um comunicado oficial no mural da turma (BE-041)."""

    id: UUID = Field(description="Identificador UUID do comunicado em class_announcements")
    class_id: UUID = Field(description="Identificador UUID da turma acadêmica")
    subject_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional da disciplina técnica",
    )
    author_id: UUID = Field(description="Identificador UUID do autor do comunicado")
    title: str = Field(description="Título do comunicado")
    content: str = Field(description="Corpo completo do comunicado")
    priority: AnnouncementPriority = Field(
        description="Prioridade visual do comunicado (NORMAL, IMPORTANT, URGENT)",
    )
    is_pinned: bool = Field(
        description="Indica se o comunicado está fixado no topo do mural",
    )
    published_at: datetime = Field(description="Data/hora UTC de publicação do comunicado")
    expires_at: datetime | None = Field(
        default=None,
        description="Data/hora UTC opcional de expiração do comunicado",
    )
    academic_class: EnrollmentClassSummarySchema = Field(
        description="Resumo da turma acadêmica destinatária",
    )
    subject: AnnouncementSubjectSummarySchema | None = Field(
        default=None,
        description="Resumo da disciplina vinculada, quando aplicável",
    )
    author: AnnouncementAuthorSummarySchema = Field(
        description="Dados resumidos do autor do comunicado",
    )


class ClassAnnouncementListQueryParams(StrictRequestSchema):
    """Parâmetros de paginação e filtros para GET /api/v1/announcements (BE-042)."""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (iniciando em 1)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Quantidade máxima de avisos por página (1 a 100)",
    )
    class_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da turma acadêmica",
    )
    subject_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID da disciplina técnica",
    )
    priority: Annotated[
        AnnouncementPriority | None,
        BeforeValidator(validate_optional_announcement_priority_pt),
        Field(
            default=None,
            description="Filtro opcional pela prioridade visual do aviso (NORMAL, IMPORTANT, URGENT)",
        ),
    ] = None


type ClassAnnouncementListParamsDep = Annotated[
    ClassAnnouncementListQueryParams,
    Query(),
]


class ClassAnnouncementPaginatedResponseSchema(BaseResponseSchema):
    """Lista paginada de avisos do mural ordenada por is_pinned DESC e published_at DESC (BE-042)."""

    data: list[ClassAnnouncementResponseSchema] = Field(
        default_factory=list,
        description="Lista de comunicados ativos ordenados por fixação e data de publicação",
    )
    total: int = Field(ge=0, description="Total de comunicados encontrados para os filtros")
    page: int = Field(ge=1, description="Página atual")
    limit: int = Field(ge=1, le=100, description="Limite máximo de itens por página")
    total_pages: int = Field(ge=0, description="Quantidade total de páginas disponíveis")


__all__ = [
    "AnnouncementAuthorSummarySchema",
    "AnnouncementContentStr",
    "AnnouncementPriorityField",
    "AnnouncementSubjectSummarySchema",
    "AnnouncementTitleStr",
    "ClassAnnouncementCreateSchema",
    "ClassAnnouncementListParamsDep",
    "ClassAnnouncementListQueryParams",
    "ClassAnnouncementPaginatedResponseSchema",
    "ClassAnnouncementResponseSchema",
    "ClassAnnouncementUpdateSchema",
    "OptionalAnnouncementExpiresAtDatetime",
    "validate_announcement_content_pt",
    "validate_announcement_expires_at_pt",
    "validate_announcement_priority_pt",
    "validate_announcement_title_pt",
    "validate_optional_announcement_priority_pt",
]
