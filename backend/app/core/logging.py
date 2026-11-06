"""Configuração centralizada de logs estruturados em JSON com Loguru."""

from __future__ import annotations

from datetime import timezone
import logging
import sys
import traceback
from typing import TYPE_CHECKING, Any

from loguru import logger
import orjson

if TYPE_CHECKING:
    from loguru import Message, Record

    from app.core.config import Settings


class InterceptHandler(logging.Handler):
    """Intercepta logs da biblioteca padrão (logging) e redireciona para o Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def format_json_log(record: Record) -> str:
    """Serializa um registro do Loguru em uma linha JSON estruturada."""
    log_entry: dict[str, Any] = {
        "timestamp": record["time"].astimezone(timezone.utc).isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    if record["extra"]:
        log_entry["extra"] = record["extra"]

    if record["exception"] is not None:
        exc_type, exc_value, exc_tb = record["exception"]
        log_entry["exception"] = {
            "type": exc_type.__name__ if exc_type else None,
            "value": str(exc_value) if exc_value else None,
            "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            if exc_tb
            else None,
        }

    return orjson.dumps(log_entry, default=str).decode("utf-8") + "\n"


def _json_sink(message: Message) -> None:
    """Sink de saída padrão (stdout) para logs em formato JSON."""
    sys.stdout.write(format_json_log(message.record))
    sys.stdout.flush()


def setup_logging(settings: Settings) -> None:
    """Configura o Loguru e intercepta os loggers do Uvicorn, FastAPI e SQLAlchemy."""
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()

    if settings.LOG_JSON:
        logger.add(
            _json_sink,
            level=log_level,
            backtrace=True,
            diagnose=False,
            enqueue=False,
        )
    else:
        logger.add(
            sys.stdout,
            level=log_level,
            backtrace=True,
            diagnose=settings.DEBUG,
            enqueue=False,
        )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
    ):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [intercept_handler]
        std_logger.propagate = False


__all__ = ["InterceptHandler", "format_json_log", "logger", "setup_logging"]

