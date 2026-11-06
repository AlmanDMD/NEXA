"""Handlers globais de exceções para padronização de respostas de erro na API FastAPI."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.exceptions import AppException
from app.core.logging import logger

HTTP_STATUS_ERROR_CODES: dict[int, tuple[str, str]] = {
    status.HTTP_400_BAD_REQUEST: (
        "BAD_REQUEST",
        "Requisição inválida.",
    ),
    status.HTTP_401_UNAUTHORIZED: (
        "UNAUTHORIZED",
        "Não autenticado ou credenciais inválidas.",
    ),
    status.HTTP_403_FORBIDDEN: (
        "FORBIDDEN",
        "Acesso não autorizado para seu perfil.",
    ),
    status.HTTP_404_NOT_FOUND: (
        "NOT_FOUND",
        "Recurso não encontrado.",
    ),
    status.HTTP_405_METHOD_NOT_ALLOWED: (
        "METHOD_NOT_ALLOWED",
        "Método HTTP não permitido para esta rota.",
    ),
    status.HTTP_409_CONFLICT: (
        "CONFLICT",
        "Conflito com o estado atual do recurso.",
    ),
    status.HTTP_422_UNPROCESSABLE_CONTENT: (
        "UNPROCESSABLE_ENTITY",
        "Não foi possível processar os dados enviados.",
    ),
    status.HTTP_429_TOO_MANY_REQUESTS: (
        "TOO_MANY_REQUESTS",
        "Limite de requisições excedido. Tente novamente em instantes.",
    ),
    status.HTTP_500_INTERNAL_SERVER_ERROR: (
        "INTERNAL_SERVER_ERROR",
        "Erro interno inesperado no servidor. Tente novamente mais tarde.",
    ),
}

DEFAULT_ENGLISH_HTTP_DETAILS: set[str] = {
    "Bad Request",
    "Unauthorized",
    "Forbidden",
    "Not Found",
    "Method Not Allowed",
    "Conflict",
    "Unprocessable Entity",
    "Too Many Requests",
    "Internal Server Error",
}


def build_error_response(
    *,
    status_code: int,
    error: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Constrói uma resposta JSON padronizada de erro."""
    content: dict[str, Any] = {
        "success": False,
        "status_code": status_code,
        "error": error,
        "message": message,
    }
    if details is not None:
        content["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )


def _format_field_location(loc: tuple[int | str, ...]) -> str:
    """Converte a tupla 'loc' do Pydantic em um caminho de campo legível."""
    location_prefixes = {"body", "query", "path", "header", "cookie"}
    filtered = [str(part) for i, part in enumerate(loc) if not (i == 0 and part in location_prefixes)]
    if not filtered:
        return ".".join(str(part) for part in loc) or "body"
    return ".".join(filtered)


def _translate_pydantic_error_message(err: dict[str, Any]) -> str:
    """Traduz mensagens padrão do Pydantic v2 para português amigável ao usuário."""
    err_type: str = str(err.get("type", ""))
    ctx: dict[str, Any] = err.get("ctx") or {}
    raw_msg: str = str(err.get("msg", "Valor inválido."))

    if err_type == "missing":
        return "Campo obrigatório."
    if err_type in ("string_type", "string_unicode"):
        return "O valor deve ser um texto válido."
    if err_type in ("int_parsing", "int_type", "int_from_float"):
        return "O valor deve ser um número inteiro válido."
    if err_type in ("float_parsing", "float_type", "decimal_parsing", "decimal_type"):
        return "O valor deve ser um número válido."
    if err_type in ("bool_parsing", "bool_type"):
        return "O valor deve ser booleano (verdadeiro ou falso)."
    if err_type == "string_too_short":
        min_length = ctx.get("min_length")
        if min_length is not None:
            return f"O texto deve ter pelo menos {min_length} caracteres."
        return "O texto informado é muito curto."
    if err_type == "string_too_long":
        max_length = ctx.get("max_length")
        if max_length is not None:
            return f"O texto deve ter no máximo {max_length} caracteres."
        return "O texto informado excede o tamanho máximo permitido."
    if err_type == "greater_than":
        gt = ctx.get("gt")
        return f"O valor deve ser maior que {gt}." if gt is not None else "Valor abaixo do mínimo."
    if err_type == "greater_than_equal":
        ge = ctx.get("ge")
        return (
            f"O valor deve ser maior ou igual a {ge}."
            if ge is not None
            else "Valor abaixo do mínimo permitido."
        )
    if err_type == "less_than":
        lt = ctx.get("lt")
        return f"O valor deve ser menor que {lt}." if lt is not None else "Valor acima do máximo."
    if err_type == "less_than_equal":
        le = ctx.get("le")
        return (
            f"O valor deve ser menor ou igual a {le}."
            if le is not None
            else "Valor acima do máximo permitido."
        )
    if err_type == "extra_forbidden":
        return "Campo adicional não permitido."
    if err_type == "json_invalid":
        return "Formato JSON inválido no corpo da requisição."
    if err_type.startswith("enum") or err_type == "literal_error":
        expected = ctx.get("expected")
        if expected:
            return f"Valor inválido. Opções permitidas: {expected}."
        return "Valor fora das opções permitidas."
    if err_type == "value_error" and raw_msg.startswith("Value error, "):
        return raw_msg.removeprefix("Value error, ")

    return raw_msg


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Trata exceções de domínio derivadas de AppException."""
    log = logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        error=exc.error,
    )
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        log.error(f"AppException: {exc.message}")
    else:
        log.warning(f"AppException: {exc.message}")

    return build_error_response(
        status_code=exc.status_code,
        error=exc.error,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Trata HTTPExceptions do FastAPI e Starlette (como 401, 403, 404, 405)."""
    default_code, default_message = HTTP_STATUS_ERROR_CODES.get(
        exc.status_code,
        ("HTTP_ERROR", "Erro ao processar a requisição."),
    )

    details: list[dict[str, Any]] | None = None
    if isinstance(exc.detail, str) and exc.detail and exc.detail not in DEFAULT_ENGLISH_HTTP_DETAILS:
        message = exc.detail
    elif isinstance(exc.detail, list):
        message = default_message
        details = [
            item if isinstance(item, dict) else {"message": str(item)} for item in exc.detail
        ]
    elif isinstance(exc.detail, dict):
        message = str(exc.detail.get("message", default_message))
        error_override = exc.detail.get("error")
        if isinstance(error_override, str):
            default_code = error_override
        raw_details = exc.detail.get("details")
        if isinstance(raw_details, list):
            details = raw_details
    else:
        message = default_message

    logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        error=default_code,
    ).warning(f"HTTPException: {message}")

    headers = dict(exc.headers) if exc.headers else None
    return build_error_response(
        status_code=exc.status_code,
        error=default_code,
        message=message,
        details=details,
        headers=headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError | ValidationError,
) -> JSONResponse:
    """Trata erros de validação do Pydantic retornando HTTP 400 com lista amigável de campos."""
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        loc = tuple(err.get("loc", ()))
        details.append(
            {
                "field": _format_field_location(loc),
                "message": _translate_pydantic_error_message(dict(err)),
                "type": str(err.get("type", "validation_error")),
            }
        )

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    message = "Erro de validação nos dados enviados. Verifique os campos informados."

    logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        error=error_code,
        invalid_fields=[item["field"] for item in details],
    ).warning(message)

    return build_error_response(
        status_code=status_code,
        error=error_code,
        message=message,
        details=details,
    )


def _classify_integrity_error(exc: IntegrityError) -> tuple[int, str, str]:
    """Classifica erros de integridade do banco de dados sem expor SQL ou detalhes internos."""
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    orig_text = str(orig).lower() if orig is not None else str(exc).lower()

    if pgcode == "23505" or "unique" in orig_text or "duplicate" in orig_text:
        return (
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Conflito de integridade: já existe um registro com os dados informados.",
        )
    if pgcode == "23503" or "foreign key" in orig_text:
        return (
            status.HTTP_409_CONFLICT,
            "FOREIGN_KEY_VIOLATION",
            "Operação não permitida: o registro possui vínculo com outros dados do sistema.",
        )
    if pgcode == "23502" or "not null" in orig_text or "null value" in orig_text:
        return (
            status.HTTP_400_BAD_REQUEST,
            "INTEGRITY_ERROR",
            "Violação de integridade: um campo obrigatório do registro não foi preenchido.",
        )
    if pgcode == "23514" or "check constraint" in orig_text:
        return (
            status.HTTP_400_BAD_REQUEST,
            "CHECK_VIOLATION",
            "Violação de regra de integridade nos dados informados.",
        )

    return (
        status.HTTP_409_CONFLICT,
        "INTEGRITY_ERROR",
        "Violação de integridade de dados ao processar a operação.",
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Trata erros do SQLAlchemy (constraints/integridade e falhas de banco) sem vazar SQL."""
    if isinstance(exc, IntegrityError):
        status_code, error_code, message = _classify_integrity_error(exc)
        logger.bind(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            error=error_code,
            db_exception_type=type(exc).__name__,
        ).warning("Violação de integridade no banco de dados.")
        return build_error_response(
            status_code=status_code,
            error=error_code,
            message=message,
        )

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "DATABASE_ERROR"
    message = "Erro interno ao processar operação no banco de dados."

    logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        error=error_code,
        db_exception_type=type(exc).__name__,
    ).opt(exception=exc).error("Falha de banco de dados durante o processamento da requisição.")

    return build_error_response(
        status_code=status_code,
        error=error_code,
        message=message,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Trata exceções inesperadas (500), logando o traceback e retornando resposta segura."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "INTERNAL_SERVER_ERROR"
    message = "Erro interno inesperado no servidor. Tente novamente mais tarde."

    logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        error=error_code,
        exception_type=type(exc).__name__,
    ).opt(exception=exc).error("Exceção não tratada capturada pelo handler global.")

    return build_error_response(
        status_code=status_code,
        error=error_code,
        message=message,
    )


class GlobalExceptionMiddleware:
    """Middleware ASGI que garante resposta JSON padronizada em exceções 500 mesmo com DEBUG=True."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Any) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as exc:
            if response_started:
                raise exc
            request = Request(scope, receive=receive)
            response = await unhandled_exception_handler(request, exc)
            await response(scope, receive, send)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos os exception handlers globais na instância FastAPI."""
    app.add_middleware(GlobalExceptionMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    "GlobalExceptionMiddleware",
    "app_exception_handler",
    "build_error_response",
    "http_exception_handler",
    "register_exception_handlers",
    "sqlalchemy_exception_handler",
    "unhandled_exception_handler",
    "validation_exception_handler",
]

