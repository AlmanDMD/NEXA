"""Módulo core com configurações globais, logging, exceções e segurança."""

from app.core.config import Settings, SettingsDep, get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
    UnprocessableEntityException,
)
from app.core.logging import logger, setup_logging

__all__ = [
    "AppException",
    "BadRequestException",
    "ConflictException",
    "ForbiddenException",
    "InternalServerException",
    "NotFoundException",
    "Settings",
    "SettingsDep",
    "UnauthorizedException",
    "UnprocessableEntityException",
    "get_settings",
    "logger",
    "register_exception_handlers",
    "setup_logging",
]
