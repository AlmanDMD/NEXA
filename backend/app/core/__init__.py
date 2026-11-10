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
from app.core.security import (
    DEFAULT_BCRYPT_ROUNDS,
    MAX_BCRYPT_PASSWORD_BYTES,
    MAX_BCRYPT_ROUNDS,
    MIN_BCRYPT_ROUNDS,
    PasswordHasher,
    PasswordHasherDep,
    bearer_scheme,
    get_password_hash,
    get_password_hasher,
    hash_password,
    needs_rehash,
    password_hasher,
    verify_password,
)

__all__ = [
    "AppException",
    "BadRequestException",
    "ConflictException",
    "DEFAULT_BCRYPT_ROUNDS",
    "ForbiddenException",
    "InternalServerException",
    "MAX_BCRYPT_PASSWORD_BYTES",
    "MAX_BCRYPT_ROUNDS",
    "MIN_BCRYPT_ROUNDS",
    "NotFoundException",
    "PasswordHasher",
    "PasswordHasherDep",
    "Settings",
    "SettingsDep",
    "UnauthorizedException",
    "UnprocessableEntityException",
    "bearer_scheme",
    "get_password_hash",
    "get_password_hasher",
    "get_settings",
    "hash_password",
    "logger",
    "needs_rehash",
    "password_hasher",
    "register_exception_handlers",
    "setup_logging",
    "verify_password",
]
