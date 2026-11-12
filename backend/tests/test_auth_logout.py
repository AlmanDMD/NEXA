"""Testes unitários e de integração para Logout e Invalidação de Sessão no Banco (BE-007)."""

from collections.abc import AsyncIterator, Generator
from datetime import datetime, timezone
import hashlib
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    UnauthorizedException,
    create_access_token,
    create_refresh_token,
    get_db,
    get_password_hasher,
    get_settings,
    hash_refresh_token,
)
from app.main import create_app
from app.models import AuthSession, Base, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LogoutResponseSchema
from app.schemas.enums import UserRole
from app.services.auth_service import (
    LOGOUT_SUCCESS_MESSAGE,
    REFRESH_TOKEN_REVOKED_REUSE_MESSAGE,
    AuthService,
)


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
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes de integração."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def auth_app(
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
async def auth_client(auth_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono (httpx.AsyncClient) acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str = "docente.logout@senai.br",
    password: str = "Senai@2026!Password",
    role: str = "TEACHER",
    user_agent: str = "NEXA-Client/1.0",
    forwarded_for: str = "198.51.100.10",
) -> tuple[dict, str, str]:
    """Helper para registrar e autenticar um usuário, retornando user, access e refresh."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role,
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={
            "User-Agent": user_agent,
            "X-Forwarded-For": forwarded_for,
        },
    )
    assert login_res.status_code == status.HTTP_200_OK
    login_body = login_res.json()
    refresh_cookie = login_res.cookies.get("refresh_token")
    assert refresh_cookie is not None
    return login_body["user"], login_body["access_token"], refresh_cookie


async def test_logout_success_with_cookie_revokes_session_and_clears_cookie(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Valida POST /api/v1/auth/logout com cookie HttpOnly, marcando is_revoked=True no banco e deletando o cookie."""
    user_data, _, refresh_token = await _register_and_login(
        auth_client,
        email="professor.oficina@senai.br",
    )
    user_id = UUID(user_data["id"])
    token_hash = hash_refresh_token(refresh_token)

    # Verifica sessão ativa no banco antes do logout
    with db_session_factory() as session:
        stored_before = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        )
        assert stored_before is not None
        assert stored_before.user_id == user_id
        assert stored_before.is_revoked is False

    # Executa logout enviando o cookie refresh_token
    logout_res = await auth_client.post(
        "/api/v1/auth/logout",
        headers={
            "Cookie": f"refresh_token={refresh_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Oficina-SENAI/1.0",
            "X-Forwarded-For": "203.0.113.88",
        },
    )

    # Critérios de Aceitação
    assert logout_res.status_code == status.HTTP_200_OK
    assert logout_res.json() == {"message": "Sessão encerrada com sucesso"}

    # Verifica exclusão do cookie no header set-cookie
    set_cookie_header = logout_res.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header

    # Verifica se a sessão foi marcada como revogada no banco
    with db_session_factory() as session:
        stored_after = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        )
        assert stored_after is not None
        assert stored_after.is_revoked is True


async def test_refresh_token_rejected_after_logout(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """DoD: Garante que o refresh token anterior é rejeitado após o encerramento da sessão via logout."""
    user_data, _, refresh_token = await _register_and_login(
        auth_client,
        email="aluno.oficina@senai.br",
    )
    user_id = UUID(user_data["id"])

    # Executa logout
    logout_res = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    assert logout_res.status_code == status.HTTP_200_OK

    # Tenta renovar sessão com o token já revogado
    refresh_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )

    assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
    refresh_body = refresh_res.json()
    assert refresh_body["error"] == "UNAUTHORIZED"
    assert refresh_body["message"] == REFRESH_TOKEN_REVOKED_REUSE_MESSAGE

    # Confirma que a mitigação de reúso (revogação de todas as sessões) ocorreu
    with db_session_factory() as session:
        active_sessions = session.scalars(
            select(AuthSession).where(
                AuthSession.user_id == user_id,
                AuthSession.is_revoked.is_(False),
            )
        ).all()
        assert len(active_sessions) == 0


async def test_logout_with_json_body_refresh_token(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Testa logout passando o refresh token diretamente no corpo JSON quando não houver cookie."""
    user_data, _, refresh_token = await _register_and_login(
        auth_client,
        email="coordenador.laboratorio@senai.br",
    )
    token_hash = hash_refresh_token(refresh_token)

    auth_client.cookies.clear()
    logout_res = await auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_res.status_code == status.HTTP_200_OK
    assert logout_res.json() == {"message": "Sessão encerrada com sucesso"}

    set_cookie_header = logout_res.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header

    with db_session_factory() as session:
        stored_session = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        )
        assert stored_session is not None
        assert stored_session.is_revoked is True


async def test_logout_idempotence_and_multiple_invocations(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Garante que chamadas repetidas de logout para a mesma sessão sejam idempotentes e retornem 200."""
    _, _, refresh_token = await _register_and_login(
        auth_client,
        email="tecnico.manutencao@senai.br",
    )

    first_logout = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    assert first_logout.status_code == status.HTTP_200_OK
    assert first_logout.json() == {"message": "Sessão encerrada com sucesso"}

    second_logout = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    assert second_logout.status_code == status.HTTP_200_OK
    assert second_logout.json() == {"message": "Sessão encerrada com sucesso"}


async def test_logout_without_cookie_or_token_returns_200_and_clears_cookie(
    auth_client: AsyncClient,
) -> None:
    """Garante que uma chamada sem cookie retorne 200 e continue enviando cabeçalho de exclusão do cookie."""
    auth_client.cookies.clear()
    res = await auth_client.post("/api/v1/auth/logout")

    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"message": "Sessão encerrada com sucesso"}
    set_cookie_header = res.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header


async def test_logout_with_unregistered_or_malformed_token_returns_200(
    auth_client: AsyncClient,
) -> None:
    """Garante resiliência caso o token enviado não exista no banco ou seja inválido."""
    res = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": "refresh_token=token_inexistente_no_banco"},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"message": "Sessão encerrada com sucesso"}
    assert "refresh_token=" in res.headers.get("set-cookie", "")


def test_auth_service_logout_unit_logic(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Teste unitário do método AuthService.logout com sessão persistida."""
    settings = get_settings()
    with db_session_factory() as session:
        repo = AuthRepository(session)
        service = AuthService(
            repository=repo,
            password_hasher=fast_hasher,
            settings=settings,
        )

        user = repo.create_user(
            email="unit.logout@senai.br",
            password_hash="hash",
            role=UserRole.STUDENT,
        )
        refresh_token = create_refresh_token(subject=user.id)
        token_hash = hash_refresh_token(refresh_token)
        auth_session = repo.create_auth_session(
            user_id=user.id,
            refresh_token_hash=token_hash,
            expires_at=datetime.now(timezone.utc),
        )
        assert auth_session.is_revoked is False

        # Chamada direta do serviço
        result = service.logout(refresh_token, ip_address="127.0.0.1")
        assert isinstance(result, LogoutResponseSchema)
        assert result.message == LOGOUT_SUCCESS_MESSAGE

        # Verifica banco
        session.refresh(auth_session)
        assert auth_session.is_revoked is True
