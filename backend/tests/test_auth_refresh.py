"""Testes unitários e de integração para Renovação de Sessão e Rotação de Refresh Token (BE-006)."""

from collections.abc import AsyncIterator, Generator
from datetime import datetime, timedelta, timezone
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
    decode_access_token,
    decode_refresh_token,
    get_db,
    get_password_hasher,
    get_settings,
    hash_refresh_token,
)
from app.main import create_app
from app.models import AuthSession, Base, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequestSchema
from app.schemas.enums import UserRole
from app.schemas.user import UserCreateSchema
from app.services.auth_service import (
    AuthService,
    REFRESH_TOKEN_EXPIRED_MESSAGE,
    REFRESH_TOKEN_INVALID_MESSAGE,
    REFRESH_TOKEN_MISSING_MESSAGE,
    REFRESH_TOKEN_REVOKED_REUSE_MESSAGE,
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
    email: str = "docente.refresh@senai.br",
    password: str = "Senai@2026!Password",
    role: str = "TEACHER",
    user_agent: str = "NEXA-Client/1.0",
    forwarded_for: str = "198.51.100.10",
) -> tuple[dict, str, str]:
    """Helper para registrar (se ainda não existir) e autenticar um usuário, retornando user, access e refresh."""
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


async def test_refresh_token_rotation_success_issues_new_tokens_and_invalidates_previous_session(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Testa POST /api/v1/auth/refresh com rotação de tokens, novo cookie HttpOnly e invalidação do token anterior."""
    user_data, initial_access_token, initial_refresh_token = await _register_and_login(
        auth_client,
        email="professor.rotacao@senai.br",
    )
    user_id = UUID(user_data["id"])
    initial_refresh_hash = hash_refresh_token(initial_refresh_token)

    auth_client.cookies.clear()
    refresh_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={initial_refresh_token}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) NEXA-Refreshed/2.0",
            "X-Forwarded-For": "203.0.113.77, 10.0.0.2",
        },
    )

    assert refresh_res.status_code == status.HTTP_200_OK
    refresh_body = refresh_res.json()
    assert refresh_body["token_type"] == "bearer"
    assert isinstance(refresh_body["access_token"], str) and len(refresh_body["access_token"]) > 20
    assert refresh_body["access_token"] != initial_access_token

    decoded_initial_access = decode_access_token(initial_access_token)
    decoded_new_access = decode_access_token(refresh_body["access_token"])
    assert decoded_new_access["sub"] == str(user_id)
    assert decoded_new_access["email"] == "professor.rotacao@senai.br"
    assert decoded_new_access["role"] == "TEACHER"
    assert decoded_new_access["type"] == "access"
    assert decoded_new_access["jti"] != decoded_initial_access["jti"]
    assert decoded_new_access["exp"] - decoded_new_access["iat"] == 15 * 60

    set_cookie_header = refresh_res.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "Secure" in set_cookie_header
    assert "SameSite=lax" in set_cookie_header
    assert f"Max-Age={7 * 24 * 60 * 60}" in set_cookie_header

    new_refresh_token = refresh_res.cookies.get("refresh_token")
    assert new_refresh_token is not None
    assert new_refresh_token != initial_refresh_token

    decoded_initial_refresh = decode_refresh_token(initial_refresh_token)
    decoded_new_refresh = decode_refresh_token(new_refresh_token)
    assert decoded_new_refresh["sub"] == str(user_id)
    assert decoded_new_refresh["type"] == "refresh"
    assert decoded_new_refresh["jti"] != decoded_initial_refresh["jti"]
    assert decoded_new_refresh["exp"] - decoded_new_refresh["iat"] == 7 * 24 * 60 * 60

    new_refresh_hash = hashlib.sha256(new_refresh_token.encode("utf-8")).hexdigest()
    with db_session_factory() as session:
        old_db_session = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == initial_refresh_hash)
        )
        new_db_session = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == new_refresh_hash)
        )
        assert old_db_session is not None
        assert old_db_session.is_revoked is True

        assert new_db_session is not None
        assert new_db_session.is_revoked is False
        assert new_db_session.user_id == user_id
        assert new_db_session.user_agent == "Mozilla/5.0 (X11; Linux x86_64) NEXA-Refreshed/2.0"
        assert new_db_session.ip_address == "203.0.113.77"
        assert new_db_session.expires_at > new_db_session.created_at

    auth_client.cookies.clear()
    second_refresh_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={new_refresh_token}"},
    )
    assert second_refresh_res.status_code == status.HTTP_200_OK
    third_refresh_token = second_refresh_res.cookies.get("refresh_token")
    assert third_refresh_token is not None
    assert third_refresh_token != new_refresh_token


async def test_refresh_token_reuse_detection_triggers_chain_revocation_of_all_active_sessions(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Garante que o reúso de um refresh token já revogado revoga em cadeia todas as sessões ativas do usuário."""
    user_data, _, device_a_token_1 = await _register_and_login(
        auth_client,
        email="aluno.seguranca@senai.br",
        role="STUDENT",
        user_agent="Device-A-Notebook",
        forwarded_for="198.51.100.1",
    )
    user_id = UUID(user_data["id"])

    _, _, device_b_token_1 = await _register_and_login(
        auth_client,
        email="aluno.seguranca@senai.br",
        role="STUDENT",
        user_agent="Device-B-Tablet-Oficina",
        forwarded_for="198.51.100.2",
    )

    auth_client.cookies.clear()
    rotate_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={device_a_token_1}"},
    )
    assert rotate_res.status_code == status.HTTP_200_OK
    device_a_token_2 = rotate_res.cookies.get("refresh_token")
    assert device_a_token_2 is not None

    auth_client.cookies.clear()
    reuse_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={device_a_token_1}",
            "X-Forwarded-For": "203.0.113.250",
        },
    )
    assert reuse_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert reuse_res.json() == {
        "success": False,
        "status_code": 401,
        "error": "UNAUTHORIZED",
        "message": REFRESH_TOKEN_REVOKED_REUSE_MESSAGE,
    }

    with db_session_factory() as session:
        user_sessions = session.scalars(
            select(AuthSession).where(AuthSession.user_id == user_id)
        ).all()
        assert len(user_sessions) == 3
        assert all(s.is_revoked is True for s in user_sessions)

    auth_client.cookies.clear()
    subsequent_a_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={device_a_token_2}"},
    )
    assert subsequent_a_res.status_code == status.HTTP_401_UNAUTHORIZED

    auth_client.cookies.clear()
    subsequent_b_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={device_b_token_1}"},
    )
    assert subsequent_b_res.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_returns_401_for_missing_empty_malformed_or_unregistered_token(
    auth_client: AsyncClient,
) -> None:
    """Garante retorno HTTP 401 para cookie ausente, vazio, JWT malformado, tipo incorreto ou sessão inexistente."""
    auth_client.cookies.clear()
    missing_res = await auth_client.post("/api/v1/auth/refresh")
    assert missing_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert missing_res.json() == {
        "success": False,
        "status_code": 401,
        "error": "UNAUTHORIZED",
        "message": REFRESH_TOKEN_MISSING_MESSAGE,
    }

    empty_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": "refresh_token=   "},
    )
    assert empty_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert empty_res.json()["message"] == REFRESH_TOKEN_MISSING_MESSAGE

    malformed_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": "refresh_token=token.malformado.invalido"},
    )
    assert malformed_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert malformed_res.json()["message"] == REFRESH_TOKEN_INVALID_MESSAGE

    access_instead_of_refresh = create_access_token(subject=uuid4())
    wrong_type_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={access_instead_of_refresh}"},
    )
    assert wrong_type_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert wrong_type_res.json()["message"] == REFRESH_TOKEN_INVALID_MESSAGE

    unregistered_refresh = create_refresh_token(subject=uuid4())
    unregistered_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={unregistered_refresh}"},
    )
    assert unregistered_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert unregistered_res.json()["message"] == REFRESH_TOKEN_INVALID_MESSAGE


async def test_refresh_token_returns_401_when_jwt_or_database_session_is_expired(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Garante retorno HTTP 401 quando o JWT expirou ou quando expires_at no banco já foi ultrapassado."""
    user_data, _, valid_refresh_token = await _register_and_login(
        auth_client,
        email="coordenador.expirado@senai.br",
        role="COORDINATOR",
    )
    user_id = UUID(user_data["id"])
    auth_client.cookies.clear()

    expired_jwt_refresh = create_refresh_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-30),
    )
    expired_jwt_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={expired_jwt_refresh}"},
    )
    assert expired_jwt_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert expired_jwt_res.json() == {
        "success": False,
        "status_code": 401,
        "error": "UNAUTHORIZED",
        "message": REFRESH_TOKEN_EXPIRED_MESSAGE,
    }

    token_hash = hash_refresh_token(valid_refresh_token)
    with db_session_factory() as session:
        db_session = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        )
        assert db_session is not None
        past_created = datetime.now(timezone.utc) - timedelta(days=8)
        past_expires = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.created_at = past_created
        db_session.expires_at = past_expires
        session.commit()

    expired_db_res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={valid_refresh_token}"},
    )
    assert expired_db_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert expired_db_res.json()["message"] == REFRESH_TOKEN_EXPIRED_MESSAGE


async def test_refresh_token_returns_401_and_revokes_session_when_user_is_deactivated(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Garante que um usuário desativado após o login não consegue renovar a sessão e tem a sessão revogada."""
    user_data, _, refresh_token = await _register_and_login(
        auth_client,
        email="usuario.desativado@senai.br",
        role="STUDENT",
    )
    user_id = UUID(user_data["id"])
    token_hash = hash_refresh_token(refresh_token)
    auth_client.cookies.clear()

    with db_session_factory() as session:
        db_user = session.scalar(select(User).where(User.id == user_id))
        assert db_user is not None
        db_user.is_active = False
        session.commit()

    res = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["message"] == REFRESH_TOKEN_INVALID_MESSAGE

    with db_session_factory() as session:
        db_session = session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        )
        assert db_session is not None
        assert db_session.is_revoked is True


def test_auth_service_and_repository_refresh_rotation_and_reuse_unit(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida unitariamente AuthService.refresh_session e AuthRepository (rotação e revogação em cadeia)."""
    settings = get_settings()
    with db_session_factory() as session:
        repository = AuthRepository(session=session)
        service = AuthService(
            repository=repository,
            password_hasher=fast_hasher,
            settings=settings,
        )

        created_user = service.register_user(
            UserCreateSchema(
                email="unitario.refresh@senai.br",
                password="Senai@2026!Password",
                role=UserRole.TEACHER,
            )
        )

        _, refresh_1 = service.authenticate_user(
            LoginRequestSchema(
                email="unitario.refresh@senai.br",
                password="Senai@2026!Password",
            ),
            user_agent="Unit-Agent/1.0",
            ip_address="10.0.0.10",
        )

        refresh_schema, refresh_2 = service.refresh_session(
            refresh_1,
            user_agent="Unit-Agent/1.1",
            ip_address="10.0.0.11",
        )
        assert refresh_schema.token_type == "bearer"
        assert decode_access_token(refresh_schema.access_token)["sub"] == str(created_user.id)
        assert refresh_2 != refresh_1

        s1 = repository.get_auth_session_by_token_hash(hash_refresh_token(refresh_1))
        s2 = repository.get_auth_session_by_token_hash(hash_refresh_token(refresh_2))
        assert s1 is not None and s1.is_revoked is True
        assert s2 is not None and s2.is_revoked is False

        with pytest.raises(UnauthorizedException, match=REFRESH_TOKEN_REVOKED_REUSE_MESSAGE):
            service.refresh_session(refresh_1)

        session.expire_all()
        s2_after_reuse = repository.get_auth_session_by_token_hash(hash_refresh_token(refresh_2))
        assert s2_after_reuse is not None and s2_after_reuse.is_revoked is True

