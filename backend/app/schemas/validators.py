"""Validadores customizados e funções de sanitização com mensagens em português para Pydantic v2."""

import re
from typing import Annotated, Any

from pydantic import BeforeValidator, EmailStr, Field, TypeAdapter, ValidationError
from pydantic_core import PydanticCustomError

_EMAIL_ADAPTER: TypeAdapter[EmailStr] = TypeAdapter(EmailStr)

_DANGEROUS_HTML_PATTERN: re.Pattern[str] = re.compile(
    r"(<\s*/?\s*(script|iframe|object|embed|svg|style|link|meta)\b|javascript\s*:|on\w+\s*=|<[^>]+>)",
    re.IGNORECASE,
)
_CONTROL_CHARS_PATTERN: re.Pattern[str] = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTIPLE_SPACES_PATTERN: re.Pattern[str] = re.compile(r"\s+")
_REGISTRATION_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z0-9._-]+$")
_PHONE_ALLOWED_PATTERN: re.Pattern[str] = re.compile(r"^[0-9+\-() ]+$")
_SPECIAL_CHAR_PATTERN: re.Pattern[str] = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")


def sanitize_text(value: Any, *, collapse_spaces: bool = False) -> str:
    """Remove espaços nas extremidades, rejeita bytes nulos e bloqueia tags HTML/XSS."""
    if not isinstance(value, str):
        raise PydanticCustomError(
            "string_type",
            "O valor deve ser um texto válido.",
        )

    if "\x00" in value or _CONTROL_CHARS_PATTERN.search(value):
        raise PydanticCustomError(
            "invalid_control_chars",
            "O campo contém caracteres de controle não permitidos.",
        )

    cleaned = value.strip()

    if _DANGEROUS_HTML_PATTERN.search(cleaned):
        raise PydanticCustomError(
            "unsafe_html_content",
            "O campo contém marcações HTML ou scripts não permitidos.",
        )

    if collapse_spaces:
        cleaned = _MULTIPLE_SPACES_PATTERN.sub(" ", cleaned)

    return cleaned


def sanitize_optional_text(value: Any, *, collapse_spaces: bool = False) -> str | None:
    """Sanitiza texto opcional convertendo strings vazias em None."""
    if value is None:
        return None
    cleaned = sanitize_text(value, collapse_spaces=collapse_spaces)
    return cleaned if cleaned else None


def validate_email_pt(value: Any) -> str:
    """Normaliza (lowercase + trim) e valida formato de e-mail com mensagem em português."""
    if not isinstance(value, str):
        raise PydanticCustomError(
            "email_type",
            "O endereço de e-mail deve ser um texto válido.",
        )

    cleaned = sanitize_text(value).lower()
    if not cleaned:
        raise PydanticCustomError(
            "email_empty",
            "O endereço de e-mail é obrigatório.",
        )

    if len(cleaned) > 255:
        raise PydanticCustomError(
            "email_too_long",
            "O endereço de e-mail deve ter no máximo 255 caracteres.",
        )

    try:
        validated = _EMAIL_ADAPTER.validate_python(cleaned)
        return str(validated).lower()
    except ValidationError as exc:
        raise PydanticCustomError(
            "email_invalid",
            "Endereço de e-mail inválido.",
        ) from exc


def validate_strong_password_pt(
    value: Any,
    *,
    min_length: int = 8,
    max_length: int = 128,
) -> str:
    """Valida força de senha segundo políticas de segurança com mensagens em português."""
    if not isinstance(value, str):
        raise PydanticCustomError(
            "password_type",
            "A senha deve ser um texto válido.",
        )

    if "\x00" in value or _CONTROL_CHARS_PATTERN.search(value):
        raise PydanticCustomError(
            "password_invalid_chars",
            "A senha contém caracteres de controle não permitidos.",
        )

    if len(value) < min_length:
        raise PydanticCustomError(
            "password_too_short",
            f"A senha deve ter pelo menos {min_length} caracteres.",
        )

    if len(value) > max_length:
        raise PydanticCustomError(
            "password_too_long",
            f"A senha deve ter no máximo {max_length} caracteres.",
        )

    if not any(ch.isupper() for ch in value):
        raise PydanticCustomError(
            "password_missing_uppercase",
            "A senha deve conter pelo menos uma letra maiúscula.",
        )

    if not any(ch.islower() for ch in value):
        raise PydanticCustomError(
            "password_missing_lowercase",
            "A senha deve conter pelo menos uma letra minúscula.",
        )

    if not any(ch.isdigit() for ch in value):
        raise PydanticCustomError(
            "password_missing_digit",
            "A senha deve conter pelo menos um número.",
        )

    if not _SPECIAL_CHAR_PATTERN.search(value):
        raise PydanticCustomError(
            "password_missing_special",
            "A senha deve conter pelo menos um caractere especial.",
        )

    return value


def validate_login_password_pt(
    value: Any,
    *,
    min_length: int = 8,
    max_length: int = 128,
) -> str:
    """Valida senha recebida no login garantindo tamanho mínimo e máximo em português."""
    if not isinstance(value, str):
        raise PydanticCustomError(
            "password_type",
            "A senha deve ser um texto válido.",
        )

    if "\x00" in value or _CONTROL_CHARS_PATTERN.search(value):
        raise PydanticCustomError(
            "password_invalid_chars",
            "A senha contém caracteres de controle não permitidos.",
        )

    if len(value) < min_length:
        raise PydanticCustomError(
            "password_too_short",
            f"A senha deve ter pelo menos {min_length} caracteres.",
        )

    if len(value) > max_length:
        raise PydanticCustomError(
            "password_too_long",
            f"A senha deve ter no máximo {max_length} caracteres.",
        )

    return value


def validate_full_name_pt(value: Any) -> str:
    """Sanitiza, colapsa espaços múltiplos e valida nome completo do usuário."""
    cleaned = sanitize_text(value, collapse_spaces=True)
    if len(cleaned) < 2:
        raise PydanticCustomError(
            "full_name_too_short",
            "O nome completo deve ter pelo menos 2 caracteres.",
        )
    if len(cleaned) > 150:
        raise PydanticCustomError(
            "full_name_too_long",
            "O nome completo deve ter no máximo 150 caracteres.",
        )
    return cleaned


def validate_registration_number_pt(value: Any) -> str:
    """Normaliza em maiúsculas (UPPER + TRIM) e valida matrícula/registro funcional SENAI."""
    cleaned = sanitize_text(value, collapse_spaces=False).upper()
    if len(cleaned) < 3:
        raise PydanticCustomError(
            "registration_too_short",
            "O número de matrícula deve ter pelo menos 3 caracteres.",
        )
    if len(cleaned) > 50:
        raise PydanticCustomError(
            "registration_too_long",
            "O número de matrícula deve ter no máximo 50 caracteres.",
        )
    if not _REGISTRATION_PATTERN.match(cleaned):
        raise PydanticCustomError(
            "registration_invalid_format",
            "O número de matrícula deve conter apenas letras, números, pontos, underscores ou hífens.",
        )
    return cleaned


def validate_phone_pt(value: Any) -> str | None:
    """Sanitiza e valida telefone opcional no formato nacional ou internacional."""
    cleaned = sanitize_optional_text(value, collapse_spaces=True)
    if cleaned is None:
        return None

    if len(cleaned) > 25:
        raise PydanticCustomError(
            "phone_too_long",
            "O telefone deve ter no máximo 25 caracteres.",
        )

    digits = [ch for ch in cleaned if ch.isdigit()]
    if not _PHONE_ALLOWED_PATTERN.match(cleaned) or len(digits) < 8 or len(digits) > 15:
        raise PydanticCustomError(
            "phone_invalid_format",
            "Número de telefone inválido. Informe entre 8 e 15 dígitos numéricos.",
        )

    return cleaned


type SanitizedStr = Annotated[
    str,
    BeforeValidator(lambda v: sanitize_text(v, collapse_spaces=True)),
]

type NormalizedEmailStr = Annotated[
    EmailStr,
    BeforeValidator(validate_email_pt),
    Field(
        description="Endereço de e-mail válido e normalizado em letras minúsculas",
        examples=["aluno.teste@senai.br"],
    ),
]

type StrongPasswordStr = Annotated[
    str,
    BeforeValidator(validate_strong_password_pt),
    Field(
        description="Senha forte com mínimo de 8 caracteres, maiúscula, minúscula, número e especial",
        examples=["Senai@2026"],
    ),
]

type LoginPasswordStr = Annotated[
    str,
    BeforeValidator(validate_login_password_pt),
    Field(
        description="Senha de autenticação com no mínimo 8 caracteres",
        examples=["Senai@2026"],
    ),
]

type FullNameStr = Annotated[
    str,
    BeforeValidator(validate_full_name_pt),
    Field(
        description="Nome completo do usuário sanitizado",
        examples=["Maria Fernanda Oliveira"],
    ),
]

type RegistrationNumberStr = Annotated[
    str,
    BeforeValidator(validate_registration_number_pt),
    Field(
        description="Matrícula acadêmica ou registro funcional SENAI normalizado em maiúsculas",
        examples=["SENAI-2026-0001"],
    ),
]

type OptionalPhoneStr = Annotated[
    str | None,
    BeforeValidator(validate_phone_pt),
    Field(
        default=None,
        description="Telefone de contato opcional",
        examples=["(11) 98765-4321"],
    ),
]

__all__ = [
    "FullNameStr",
    "LoginPasswordStr",
    "NormalizedEmailStr",
    "OptionalPhoneStr",
    "RegistrationNumberStr",
    "SanitizedStr",
    "StrongPasswordStr",
    "sanitize_optional_text",
    "sanitize_text",
    "validate_email_pt",
    "validate_full_name_pt",
    "validate_login_password_pt",
    "validate_phone_pt",
    "validate_registration_number_pt",
    "validate_strong_password_pt",
]
