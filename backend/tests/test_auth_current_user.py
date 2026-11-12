"""Testes unitários e de integração para Dependência de Autenticação JWT e Extração de Usuário (BE-008)."""

from collections.abc import AsyncIterator, Generator
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, status
from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    CurrentUserDep,
    PasswordHasher,
    UnauthorizedException,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_db,
    get_password_hasher,
    get_settings,
    oauth2_scheme,
)
from app.main import create_app
from app.models import Base, User, UserProfile
from app.repositories.auth_repository import AuthRepository
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
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes de integração."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def app_with_protected_routes(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância da aplicação FastAPI com rotas protegidas de exemplo e injeção de dependências."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher

    example_router = APIRouter(prefix="/api/v1/example", tags=["Example"])

    @example_router.get("/me")
    async def example_me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
        """Rota de exemplo que declara explicitamente current_user: User = Depends(get_current_user)."""
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "full_name": current_user.profile.full_name if current_user.profile else None,
            "registration_number": (
                current_user.profile.registration_number
                if current_user.profile
                else None
            ),
        }

    @example_router.get("/annotated-me")
    async def example_annotated_me(current_user: CurrentUserDep) -> dict[str, Any]:
        """Rota de exemplo que utiliza a anotação simplificada CurrentUserDep."""
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role.value,
        }

    application.include_router(example_router)
    return application


@pytest.fixture
async def client(app_with_protected_routes: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono para testar as rotas protegidas."""
    transport = ASGITransport(app=app_with_protected_routes)
    async with AsyncClient(transport=transport, base_url="https://testserver") as test_client:
        yield test_client


def _create_db_user(
    session: Session,
    hasher: PasswordHasher,
    *,
    email: str = "aluno.nexa@senai.br",
    role: UserRole = UserRole.STUDENT,
    is_active: bool = True,
    full_name: str = "Aluno Nexa SENAI",
    registration_number: str = "SENAI-2026-ALU-01",
) -> User:
    """Helper para criar usuário e perfil persistidos no banco de testes."""
    repo = AuthRepository(session=session)
    profile_data = UserProfileCreateSchema(
        full_name=full_name,
        registration_number=registration_number,
        phone="(11) 99999-0000",
    )
    return repo.create_user(
        email=email,
        password_hash=hasher.hash_password("Senai@2026!Secret"),
        role=role,
        is_active=is_active,
        profile_data=profile_data,
    )


def test_oauth2_password_bearer_openapi_documentation(
    app_with_protected_routes: FastAPI,
) -> None:
    """Valida se o OpenAPI documenta o esquema OAuth2PasswordBearer com tokenUrl correto para Swagger UI."""
    schema = app_with_protected_routes.openapi()

    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "OAuth2PasswordBearer" in schema["components"]["securitySchemes"]

    security_scheme = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]
    assert security_scheme["type"] == "oauth2"
    assert "flows" in security_scheme
    assert "password" in security_scheme["flows"]
    assert security_scheme["flows"]["password"]["tokenUrl"] == "/api/v1/auth/login"

    # Confirma que a rota protegida declara o requisito de segurança
    path_item = schema["paths"]["/api/v1/example/me"]["get"]
    assert "security" in path_item
    assert any("OAuth2PasswordBearer" in req for req in path_item["security"])


async def test_get_current_user_injects_typed_user_with_depends(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que current_user: User = Depends(get_current_user) injeta o usuário autenticado com perfil."""
    with db_session_factory() as session:
        user = _create_db_user(
            session,
            fast_hasher,
            email="docente.metrologia@senai.br",
            role=UserRole.TEACHER,
            full_name="Prof. Carlos Eduardo",
            registration_number="SENAI-PROF-007",
        )
        user_id = user.id

    access_token = create_access_token(
        subject=user_id,
        email="docente.metrologia@senai.br",
        role=UserRole.TEACHER,
    )

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == str(user_id)
    assert body["email"] == "docente.metrologia@senai.br"
    assert body["role"] == "TEACHER"
    assert body["is_active"] is True
    assert body["full_name"] == "Prof. Carlos Eduardo"
    assert body["registration_number"] == "SENAI-PROF-007"


async def test_get_current_user_injects_typed_user_with_annotated_dep(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que CurrentUserDep (Annotated[User, Depends(get_current_user)]) funciona identicamente."""
    with db_session_factory() as session:
        user = _create_db_user(
            session,
            fast_hasher,
            email="coordenador@senai.br",
            role=UserRole.COORDINATOR,
        )
        user_id = user.id

    access_token = create_access_token(
        subject=user_id,
        email="coordenador@senai.br",
        role=UserRole.COORDINATOR,
    )

    response = await client.get(
        "/api/v1/example/annotated-me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == str(user_id)
    assert body["email"] == "coordenador@senai.br"
    assert body["role"] == "COORDINATOR"


async def test_get_current_user_blocks_missing_authorization_header(
    client: AsyncClient,
) -> None:
    """Critério 1: Bloqueia requisições sem header Authorization retornando HTTP 401 Unauthorized."""
    response = await client.get("/api/v1/example/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Bearer" in response.headers.get("www-authenticate", "")
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert body["message"] == "Não autenticado ou credenciais inválidas."


async def test_get_current_user_blocks_non_bearer_scheme(
    client: AsyncClient,
) -> None:
    """Critério 1: Bloqueia requisições cujo schema não seja Bearer com HTTP 401."""
    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ="},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Bearer" in response.headers.get("www-authenticate", "")
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"


async def test_get_current_user_blocks_empty_or_whitespace_bearer_token(
    client: AsyncClient,
) -> None:
    """Critério 1: Bloqueia requisições com Authorization Bearer vazio retornando HTTP 401."""
    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": "Bearer   "},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Bearer" in response.headers.get("www-authenticate", "")
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"


async def test_get_current_user_blocks_expired_access_token(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 2: Bloqueia tokens com tempo de expiração expirado retornando HTTP 401."""
    with db_session_factory() as session:
        user = _create_db_user(session, fast_hasher)
        user_id = user.id

    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-30),
    )

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Bearer" in response.headers.get("www-authenticate", "")
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert "expirado" in body["message"].lower()


async def test_get_current_user_blocks_invalid_signature_and_tampered_token(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 2: Bloqueia tokens com assinatura forjada/adulterada retornando HTTP 401."""
    with db_session_factory() as session:
        user = _create_db_user(session, fast_hasher)
        user_id = user.id

    # Token assinado com chave secreta diferente
    forged_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "jti": str(uuid4()),
        },
        "wrong-secret-key-that-does-not-match-configuration",
        algorithm="HS256",
    )

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert "inválido" in body["message"].lower()


async def test_get_current_user_blocks_malformed_token_string(
    client: AsyncClient,
) -> None:
    """Critério 2: Bloqueia tokens malformados que não são JWT válidos com HTTP 401."""
    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.string"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert "inválido" in body["message"].lower()


async def test_get_current_user_blocks_refresh_token_used_as_access_token(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que um Refresh Token não seja aceito como Bearer Access Token (type != 'access')."""
    with db_session_factory() as session:
        user = _create_db_user(session, fast_hasher)
        user_id = user.id

    refresh_token = create_refresh_token(subject=user_id)

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"


async def test_get_current_user_blocks_nonexistent_user_id_in_database(
    client: AsyncClient,
) -> None:
    """Garante retorno HTTP 401 caso o usuário do token tenha sido removido do banco."""
    nonexistent_id = uuid4()
    access_token = create_access_token(subject=nonexistent_id)

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert "não encontrado" in body["message"].lower()


async def test_get_current_user_blocks_inactive_user(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante retorno HTTP 401 quando a conta do usuário estiver inativa (is_active=False)."""
    with db_session_factory() as session:
        user = _create_db_user(
            session,
            fast_hasher,
            email="inativo@senai.br",
            is_active=False,
        )
        user_id = user.id

    access_token = create_access_token(subject=user_id)

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"
    assert "inativo" in body["message"].lower()


async def test_get_current_user_blocks_invalid_sub_format(
    client: AsyncClient,
) -> None:
    """Garante retorno HTTP 401 quando a claim 'sub' contiver valor que não seja UUID válido."""
    settings = get_settings()
    forged_token = jwt.encode(
        {
            "sub": "not-a-valid-uuid-string",
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "jti": str(uuid4()),
        },
        settings.JWT_ACCESS_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/api/v1/example/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 401
    assert body["error"] == "UNAUTHORIZED"


def test_get_current_user_unit_direct_invocation(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Testa invocação direta da função get_current_user sem passar pela camada HTTP."""
    with db_session_factory() as session:
        repo = AuthRepository(session=session)
        user = _create_db_user(session, fast_hasher, email="unit.test@senai.br")

        valid_token = create_access_token(subject=user.id)
        retrieved_user = get_current_user(token=valid_token, repository=repo)

        assert retrieved_user.id == user.id
        assert retrieved_user.email == "unit.test@senai.br"
        assert retrieved_user.role == UserRole.STUDENT

        with pytest.raises(UnauthorizedException, match="Token de acesso ausente ou inválido"):
            get_current_user(token="", repository=repo)

        with pytest.raises(UnauthorizedException, match="Token de acesso ausente ou inválido"):
            get_current_user(token="   ", repository=repo)

        with pytest.raises(UnauthorizedException, match="Token de acesso inválido"):
            get_current_user(token="token.invalido", repository=repo)

        nonexistent_token = create_access_token(subject=uuid4())
        with pytest.raises(UnauthorizedException, match="Usuário não encontrado ou inativo"):
            get_current_user(token=nonexistent_token, repository=repo)
