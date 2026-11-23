"""Testes unitários e de integração para Registro e Login com JWT (PyJWT) e HttpOnly Cookie (BE-005)."""

from collections.abc import AsyncIterator, Generator
from datetime import datetime, timedelta, timezone
import hashlib
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
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
from app.models import AuthSession, Base, User, UserProfile
from app.schemas import UserRole
from app.services.auth_service import INVALID_CREDENTIALS_MESSAGE


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


def test_jwt_access_and_refresh_tokens_lifecycle() -> None:
    """Valida emissão, claims, tempo de expiração (15m / 7d) e decodificação via PyJWT."""
    settings = get_settings()
    user_id = uuid4()

    assert ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    access_token = create_access_token(
        subject=user_id,
        email="docente@senai.br",
        role=UserRole.TEACHER,
        extra_claims={"unit": "SENAI-SP"},
    )
    decoded_access = decode_access_token(access_token)

    assert decoded_access["sub"] == str(user_id)
    assert decoded_access["email"] == "docente@senai.br"
    assert decoded_access["role"] == "TEACHER"
    assert decoded_access["type"] == "access"
    assert decoded_access["unit"] == "SENAI-SP"
    assert "jti" in decoded_access
    assert decoded_access["exp"] - decoded_access["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    refresh_token = create_refresh_token(
        subject=user_id,
        extra_claims={"device": "workshop-tablet"},
    )
    decoded_refresh = decode_refresh_token(refresh_token)

    assert decoded_refresh["sub"] == str(user_id)
    assert decoded_refresh["type"] == "refresh"
    assert decoded_refresh["device"] == "workshop-tablet"
    assert "jti" in decoded_refresh
    assert (
        decoded_refresh["exp"] - decoded_refresh["iat"]
        == settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )


def test_jwt_validation_rejects_expired_tampered_or_wrong_token_type() -> None:
    """Garante que tokens expirados, adulterados ou de tipo trocado lançam UnauthorizedException (401)."""
    user_id = uuid4()

    expired_access = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(UnauthorizedException, match="Token de acesso expirado"):
        decode_access_token(expired_access)

    expired_refresh = create_refresh_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(UnauthorizedException, match="Refresh token expirado"):
        decode_refresh_token(expired_refresh)

    valid_access = create_access_token(subject=user_id)
    valid_refresh = create_refresh_token(subject=user_id)

    with pytest.raises(UnauthorizedException, match="Token de acesso inválido"):
        decode_access_token("token.malformado.invalido")

    with pytest.raises(UnauthorizedException, match="Refresh token inválido"):
        decode_refresh_token("token.malformado.invalido")

    with pytest.raises(UnauthorizedException, match="Token de acesso inválido"):
        decode_access_token(valid_refresh)

    with pytest.raises(UnauthorizedException, match="Refresh token inválido"):
        decode_refresh_token(valid_access)

    settings = get_settings()
    forged_access_with_refresh_type = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        settings.JWT_ACCESS_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedException, match="Token de acesso inválido"):
        decode_access_token(forged_access_with_refresh_type)

    forged_refresh_with_access_type = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        },
        settings.JWT_REFRESH_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedException, match="Refresh token inválido"):
        decode_refresh_token(forged_refresh_with_access_type)


def test_hash_refresh_token_and_auth_session_sha256_validation() -> None:
    """Garante que refresh_token_hash armazena exclusivamente SHA-256 (64 hex chars) e rejeita JWT puro."""
    sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
    digest = hash_refresh_token(sample_jwt)

    assert len(digest) == 64
    assert digest == hashlib.sha256(sample_jwt.encode("utf-8")).hexdigest()

    with pytest.raises(ValueError, match="O refresh token deve ser um texto não vazio"):
        hash_refresh_token("   ")

    with pytest.raises(ValueError, match="O refresh_token_hash deve ser um hash SHA-256"):
        AuthSession(
            user_id=uuid4(),
            refresh_token_hash=sample_jwt,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

    with pytest.raises(ValueError, match="O hash do refresh token deve ser uma string"):
        AuthSession(
            user_id=uuid4(),
            refresh_token_hash=12345,  # type: ignore[arg-type]
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )


async def test_register_and_login_success_emits_jwt_and_secure_httponly_cookie(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    """Testa fluxo completo: registro de usuário e login POST /api/v1/auth/login com JWT e cookie HttpOnly."""
    register_payload = {
        "email": "  Maria.Oliveira@SENAI.br  ",
        "password": "Senai@2026!Password",
        "role": "TEACHER",
        "profile": {
            "full_name": "  Maria   Fernanda   Oliveira  ",
            "registration_number": "  senai-prof-2026  ",
            "phone": "(11) 98765-4321",
            "avatar_url": "https://cdn.senai.br/avatars/maria.png",
            "bio": "Docente de Usinagem e Metrologia",
        },
    }

    reg_response = await auth_client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == status.HTTP_201_CREATED
    reg_body = reg_response.json()
    assert reg_body["email"] == "maria.oliveira@senai.br"
    assert reg_body["role"] == "TEACHER"
    assert reg_body["is_active"] is True
    assert reg_body["profile"]["full_name"] == "Maria Fernanda Oliveira"
    assert reg_body["profile"]["registration_number"] == "SENAI-PROF-2026"
    assert "password" not in reg_body
    assert "password_hash" not in reg_body

    login_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "  MARIA.OLIVEIRA@senai.br ",
            "password": "Senai@2026!Password",
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEXA-Test/1.0",
            "X-Forwarded-For": "203.0.113.42, 10.0.0.1",
        },
    )

    assert login_response.status_code == status.HTTP_200_OK
    login_body = login_response.json()

    assert login_body["token_type"] == "bearer"
    assert isinstance(login_body["access_token"], str) and len(login_body["access_token"]) > 20
    assert login_body["user"]["id"] == reg_body["id"]
    assert login_body["user"]["email"] == "maria.oliveira@senai.br"
    assert login_body["user"]["role"] == "TEACHER"
    assert login_body["user"]["profile"]["full_name"] == "Maria Fernanda Oliveira"
    assert login_body["user"]["profile"]["registration_number"] == "SENAI-PROF-2026"
    assert "password_hash" not in login_body["user"]

    decoded_access = decode_access_token(login_body["access_token"])
    assert decoded_access["sub"] == reg_body["id"]
    assert decoded_access["email"] == "maria.oliveira@senai.br"
    assert decoded_access["role"] == "TEACHER"
    assert decoded_access["type"] == "access"
    assert decoded_access["exp"] - decoded_access["iat"] == 15 * 60

    set_cookie_header = login_response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "Secure" in set_cookie_header
    assert "SameSite=lax" in set_cookie_header
    assert f"Max-Age={7 * 24 * 60 * 60}" in set_cookie_header

    refresh_token_cookie = login_response.cookies.get("refresh_token")
    assert refresh_token_cookie is not None
    decoded_refresh = decode_refresh_token(refresh_token_cookie)
    assert decoded_refresh["sub"] == reg_body["id"]
    assert decoded_refresh["type"] == "refresh"
    assert decoded_refresh["exp"] - decoded_refresh["iat"] == 7 * 24 * 60 * 60

    expected_token_hash = hashlib.sha256(refresh_token_cookie.encode("utf-8")).hexdigest()
    with db_session_factory() as session:
        stored_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == UUID(reg_body["id"]))
        )
        assert stored_session is not None
        assert stored_session.refresh_token_hash == expected_token_hash
        assert stored_session.refresh_token_hash != refresh_token_cookie
        assert len(stored_session.refresh_token_hash) == 64
        assert stored_session.is_revoked is False
        assert stored_session.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEXA-Test/1.0"
        assert stored_session.ip_address == "203.0.113.42"
        assert stored_session.expires_at > stored_session.created_at


async def test_login_returns_generic_401_for_unknown_email_wrong_password_or_inactive_user(
    auth_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante retorno HTTP 401 genérico 'Credenciais inválidas' sem enumerar e-mail ou senha."""
    await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "aluno.ativo@senai.br",
            "password": "Senai@2026!Password",
            "role": "STUDENT",
        },
    )
    await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "aluno.inativo@senai.br",
            "password": "Senai@2026!Password",
            "role": "STUDENT",
            "is_active": False,
        },
    )

    with patch.object(
        fast_hasher,
        "verify_password",
        wraps=fast_hasher.verify_password,
    ) as spy_verify:
        unknown_email_res = await auth_client.post(
            "/api/v1/auth/login",
            json={
                "email": "inexistente@senai.br",
                "password": "Senai@2026!Password",
            },
        )
        assert spy_verify.call_count == 1
        assert spy_verify.call_args.args[1] == fast_hasher.dummy_hash

    assert unknown_email_res.status_code == status.HTTP_401_UNAUTHORIZED
    unknown_body = unknown_email_res.json()
    assert unknown_body == {
        "success": False,
        "status_code": 401,
        "error": "UNAUTHORIZED",
        "message": INVALID_CREDENTIALS_MESSAGE,
    }
    assert "refresh_token" not in unknown_email_res.cookies

    wrong_password_res = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "aluno.ativo@senai.br",
            "password": "SenhaIncorreta@2026",
        },
    )
    assert wrong_password_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert wrong_password_res.json() == unknown_body
    assert "refresh_token" not in wrong_password_res.cookies

    inactive_user_res = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "aluno.inativo@senai.br",
            "password": "Senai@2026!Password",
        },
    )
    assert inactive_user_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert inactive_user_res.json() == unknown_body
    assert "refresh_token" not in inactive_user_res.cookies

    with db_session_factory() as session:
        sessions_count = session.scalars(select(AuthSession)).all()
        assert len(sessions_count) == 0


async def test_login_and_register_pydantic_validation_and_conflict_handling(
    auth_client: AsyncClient,
) -> None:
    """Valida erros HTTP 400 (Pydantic v2) no login e conflitos HTTP 409 no registro duplicado."""
    invalid_login_res = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "email-malformado",
            "password": "123",
            "campo_extra": "bloqueado",
        },
    )
    assert invalid_login_res.status_code == status.HTTP_400_BAD_REQUEST
    error_body = invalid_login_res.json()
    assert error_body["error"] == "VALIDATION_ERROR"
    fields = {item["field"]: item["message"] for item in error_body["details"]}
    assert fields["email"] == "Endereço de e-mail inválido."
    assert fields["password"] == "A senha deve ter pelo menos 8 caracteres."
    assert fields["campo_extra"] == "Campo adicional não permitido."

    first_reg = await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "coordenador@senai.br",
            "password": "Senai@2026!Password",
            "role": "COORDINATOR",
            "profile": {
                "full_name": "Carlos Eduardo Souza",
                "registration_number": "SENAI-COORD-01",
            },
        },
    )
    assert first_reg.status_code == status.HTTP_201_CREATED

    duplicate_email_reg = await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "COORDENADOR@senai.br",
            "password": "Senai@2026!Password",
            "role": "COORDINATOR",
        },
    )
    assert duplicate_email_reg.status_code == status.HTTP_409_CONFLICT
    assert duplicate_email_reg.json()["error"] == "CONFLICT"

    duplicate_registration_reg = await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "outro.coordenador@senai.br",
            "password": "Senai@2026!Password",
            "role": "COORDINATOR",
            "profile": {
                "full_name": "Outro Coordenador",
                "registration_number": "senai-coord-01",
            },
        },
    )
    assert duplicate_registration_reg.status_code == status.HTTP_409_CONFLICT
    assert duplicate_registration_reg.json()["error"] == "CONFLICT"

