"""Testes unitários e de integração para o endpoint GET /api/v1/auth/me (BE-010)."""

from collections.abc import AsyncIterator, Generator
from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    create_access_token,
    create_refresh_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import Base, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import UserMeResponse
from app.schemas.enums import UserRole
from app.schemas.user import UserProfileCreateSchema


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Cria um banco SQLite em memória isolado com todas as tabelas ORM para cada teste."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield testing_session_factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def test_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância da aplicação FastAPI com dependências de banco e hasher sobrescritas."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher
    return application


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono para chamadas de integração contra o FastAPI."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def _create_user(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    *,
    email: str = "maria.oliveira@senai.br",
    role: UserRole = UserRole.STUDENT,
    is_active: bool = True,
    with_profile: bool = True,
    registration_number: str = "senai-2026-0042",
) -> User:
    """Cria um usuário de teste persistido no banco em memória."""
    with db_session_factory() as db:
        repo = AuthRepository(db)
        profile_data = (
            UserProfileCreateSchema(
                full_name="Maria Fernanda Oliveira",
                registration_number=registration_number,
                phone="(11) 98765-4321",
                avatar_url="https://cdn.senai.br/avatars/maria.png",
                bio="Estudante de Desenvolvimento de Sistemas.",
            )
            if with_profile
            else None
        )
        return repo.create_user(
            email=email,
            password_hash=fast_hasher.hash_password("Senai@2026"),
            role=role,
            is_active=is_active,
            profile_data=profile_data,
        )


class TestAuthMeEndpoint:
    """Suite de testes para GET /api/v1/auth/me."""

    async def test_me_returns_200_with_full_profile_and_no_store_header(
        self,
        async_client: AsyncClient,
        db_session_factory: sessionmaker[Session],
        fast_hasher: PasswordHasher,
    ) -> None:
        """Retorna HTTP 200, UserMeResponse completo com matrícula SENAI formatada e Cache-Control: no-store."""
        user = _create_user(db_session_factory, fast_hasher)
        token = create_access_token(subject=user.id, role=user.role.value)

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("cache-control") == "no-store"

        payload: dict[str, Any] = response.json()
        parsed = UserMeResponse.model_validate(payload)

        assert parsed.id == user.id
        assert parsed.email == "maria.oliveira@senai.br"
        assert parsed.role == UserRole.STUDENT
        assert parsed.is_active is True
        assert parsed.profile is not None
        assert parsed.profile.full_name == "Maria Fernanda Oliveira"
        assert parsed.profile.registration_number == "SENAI-2026-0042"
        assert parsed.profile.avatar_url == "https://cdn.senai.br/avatars/maria.png"
        assert parsed.profile.phone == "(11) 98765-4321"

        assert "password_hash" not in payload
        assert "password" not in payload
        assert "access_token" not in payload
        assert "refresh_token" not in payload

    async def test_me_returns_200_when_user_has_no_profile(
        self,
        async_client: AsyncClient,
        db_session_factory: sessionmaker[Session],
        fast_hasher: PasswordHasher,
    ) -> None:
        """Retorna HTTP 200 com profile=None quando o usuário autenticado não possui perfil cadastrado."""
        user = _create_user(
            db_session_factory,
            fast_hasher,
            email="admin.sem.perfil@senai.br",
            role=UserRole.ADMIN,
            with_profile=False,
        )
        token = create_access_token(subject=user.id, role=user.role.value)

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("cache-control") == "no-store"

        payload = response.json()
        assert UUID(payload["id"]) == user.id
        assert payload["email"] == "admin.sem.perfil@senai.br"
        assert payload["role"] == "ADMIN"
        assert payload["profile"] is None
        assert "password_hash" not in payload

    async def test_me_without_authentication_returns_401(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Retorna HTTP 401 quando a requisição não envia cabeçalho Authorization Bearer."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_me_with_invalid_or_expired_token_returns_401(
        self,
        async_client: AsyncClient,
        db_session_factory: sessionmaker[Session],
        fast_hasher: PasswordHasher,
    ) -> None:
        """Retorna HTTP 401 para token expirado, malformado ou refresh token usado como Bearer."""
        user = _create_user(db_session_factory, fast_hasher)

        expired_token = create_access_token(
            subject=user.id,
            role=user.role.value,
            expires_delta=timedelta(seconds=-10),
        )
        refresh_token = create_refresh_token(subject=user.id)

        for bad_token in ("token-invalido", expired_token, refresh_token):
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {bad_token}"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_me_for_inactive_user_returns_401(
        self,
        async_client: AsyncClient,
        db_session_factory: sessionmaker[Session],
        fast_hasher: PasswordHasher,
    ) -> None:
        """Retorna HTTP 401 quando o usuário autenticado está inativo no banco."""
        user = _create_user(
            db_session_factory,
            fast_hasher,
            email="inativo@senai.br",
            is_active=False,
        )
        token = create_access_token(subject=user.id, role=user.role.value)

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
