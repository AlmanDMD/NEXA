"""Configuração de engine, sessões e injeção de dependência do SQLAlchemy 2.0."""

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _normalize_database_url(database_url: str) -> str:
    """Remove parâmetros específicos do Prisma (ex: ?schema=public) incompatíveis com drivers Python."""
    if "?schema=" in database_url:
        base_url, _, query = database_url.partition("?")
        remaining = [p for p in query.split("&") if not p.startswith("schema=")]
        return f"{base_url}?{'&'.join(remaining)}" if remaining else base_url
    return database_url


@lru_cache
def get_engine(database_url: str | None = None) -> Engine:
    """Cria e armazena em cache a instância do Engine SQLAlchemy."""
    raw_url = database_url or get_settings().DATABASE_URL
    normalized_url = _normalize_database_url(raw_url)
    connect_args: dict[str, Any] = {}
    if normalized_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        normalized_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Retorna a fábrica de sessões (sessionmaker) vinculada ao Engine."""
    engine = get_engine(database_url)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """Provedor de dependência FastAPI para sessão transacional do banco de dados."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


DbSessionDep = Annotated[Session, Depends(get_db)]

__all__ = [
    "DbSessionDep",
    "get_db",
    "get_engine",
    "get_session_factory",
]

