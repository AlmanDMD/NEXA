"""Camada de models (entidades de domínio / persistência SQLAlchemy 2.0)."""

from app.models.auth_session import AuthSession
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User, UserProfile

__all__ = [
    "AuthSession",
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "UserProfile",
]
