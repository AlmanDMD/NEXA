"""Testes unitários e de integração para Schemas Pydantic v2, Sanitização e SQLAlchemy 2.0 (BE-003)."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from pydantic import EmailStr, ValidationError
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Base, User, UserProfile
from app.schemas import (
    BaseResponseSchema,
    LoginRequestSchema,
    MessageResponseSchema,
    NormalizedEmailStr,
    PaginatedResponse,
    PaginationParamsDep,
    PaginationQueryParams,
    PositiveIntPathParam,
    StrictRequestSchema,
    StrongPasswordStr,
    TokenResponseSchema,
    UUIDPathParam,
    UserCreateSchema,
    UserProfileCreateSchema,
    UserProfileResponseSchema,
    UserProfileUpdateSchema,
    UserResponseSchema,
    UserRole,
    UserUpdateSchema,
)


def test_strict_request_schema_forbids_extra_fields() -> None:
    """Garante que StrictRequestSchema rejeita propriedades extras (extra='forbid')."""

    class SampleInput(StrictRequestSchema):
        name: str

    valid = SampleInput(name="  Oficina de Tornearia  ")
    assert valid.name == "Oficina de Tornearia"

    with pytest.raises(ValidationError) as exc_info:
        SampleInput(name="Valido", intruso="malicioso")  # type: ignore[call-arg]

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "extra_forbidden"
    assert errors[0]["loc"] == ("intruso",)


def test_user_create_schema_sanitization_and_normalization() -> None:
    """Verifica sanitização de strings, normalização de e-mail (lowercase) e matrícula (uppercase)."""
    payload = UserCreateSchema(
        email="  Maria.Oliveira@SENAI.BR  ",
        password="Senai@2026!Password",
        role=UserRole.TEACHER,
        profile=UserProfileCreateSchema(
            full_name="  Maria    Fernanda   Oliveira  ",
            registration_number="  senai-doc-2026  ",
            phone="  (11) 98765-4321  ",
            avatar_url="  https://cdn.senai.br/avatars/maria.png  ",
            bio="  Docente   de   Metrologia  ",
        ),
    )

    assert payload.email == "maria.oliveira@senai.br"
    assert payload.role == UserRole.TEACHER
    assert payload.profile is not None
    assert payload.profile.full_name == "Maria Fernanda Oliveira"
    assert payload.profile.registration_number == "SENAI-DOC-2026"
    assert payload.profile.phone == "(11) 98765-4321"
    assert payload.profile.avatar_url == "https://cdn.senai.br/avatars/maria.png"
    assert payload.profile.bio == "Docente de Metrologia"


@pytest.mark.parametrize(
    ("invalid_email", "expected_message"),
    [
        ("email-sem-arroba.com", "Endereço de e-mail inválido."),
        ("usuario@dominio", "Endereço de e-mail inválido."),
        ("@senai.br", "Endereço de e-mail inválido."),
        ("   ", "O endereço de e-mail é obrigatório."),
    ],
)
def test_email_validation_messages_in_portuguese(
    invalid_email: str,
    expected_message: str,
) -> None:
    """E-mails inválidos devem falhar com mensagem clara em português."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreateSchema(
            email=invalid_email,
            password="Senai@2026!Password",
        )

    messages = [err["msg"] for err in exc_info.value.errors()]
    assert any(expected_message in msg for msg in messages)


@pytest.mark.parametrize(
    ("weak_password", "expected_message"),
    [
        ("Curta1!", "A senha deve ter pelo menos 8 caracteres."),
        ("tudo_minusculo1!", "A senha deve conter pelo menos uma letra maiúscula."),
        ("TUDO_MAIUSCULO1!", "A senha deve conter pelo menos uma letra minúscula."),
        ("SemNumerosAqui!", "A senha deve conter pelo menos um número."),
        ("SemEspecial2026", "A senha deve conter pelo menos um caractere especial."),
    ],
)
def test_password_strength_validation_messages_in_portuguese(
    weak_password: str,
    expected_message: str,
) -> None:
    """Senhas fracas ou curtas devem falhar com mensagens específicas em português."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreateSchema(
            email="aluno@senai.br",
            password=weak_password,
        )

    messages = [err["msg"] for err in exc_info.value.errors()]
    assert expected_message in messages


def test_xss_and_control_character_sanitization_rejection() -> None:
    """Payloads maliciosos com tags HTML/XSS ou bytes nulos devem ser rejeitados antes do banco."""
    with pytest.raises(ValidationError) as exc_info_xss:
        UserProfileCreateSchema(
            full_name="<script>alert('xss')</script>João Silva",
            registration_number="SENAI-2026-001",
        )
    assert any(
        "marcações HTML ou scripts não permitidos" in err["msg"]
        for err in exc_info_xss.value.errors()
    )

    with pytest.raises(ValidationError) as exc_info_null:
        UserProfileCreateSchema(
            full_name="João\x00Silva",
            registration_number="SENAI-2026-001",
        )
    assert any(
        "caracteres de controle não permitidos" in err["msg"]
        for err in exc_info_null.value.errors()
    )


def test_profile_fields_validation_errors_in_portuguese() -> None:
    """Valida regras de tamanho e formato dos campos do perfil de usuário em português."""
    with pytest.raises(ValidationError) as exc_info:
        UserProfileCreateSchema(
            full_name="A",
            registration_number="AB",
            phone="telefone-invalido",
            avatar_url="ftp://servidor.invalido/foto.png",
        )

    error_map = {err["loc"][0]: err["msg"] for err in exc_info.value.errors()}
    assert error_map["full_name"] == "O nome completo deve ter pelo menos 2 caracteres."
    assert error_map["registration_number"] == "O número de matrícula deve ter pelo menos 3 caracteres."
    assert "Número de telefone inválido" in error_map["phone"]
    assert "iniciando com http:// ou https://" in error_map["avatar_url"]


def test_sqlalchemy_orm_serialization_with_from_attributes() -> None:
    """Valida integração entre modelos SQLAlchemy 2.0 e schemas Pydantic v2 (from_attributes=True)."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    user_id = uuid4()
    profile_id = uuid4()
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        db_user = User(
            id=user_id,
            email="professor.tornearia@senai.br",
            password_hash="$2b$12$abcdefghijklmnopqrstuv1234567890abcdefghijklmnopqrstu",
            role=UserRole.TEACHER,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db_profile = UserProfile(
            id=profile_id,
            user_id=user_id,
            full_name="Roberto Carlos Almeida",
            registration_number="SENAI-PROF-0099",
            phone="(11) 99999-8888",
            avatar_url="https://cdn.senai.br/avatars/roberto.jpg",
            bio="Instrutor de Usinagem CNC",
            created_at=now,
            updated_at=now,
        )
        db_user.profile = db_profile
        session.add(db_user)
        session.commit()

        loaded_user = session.scalar(select(User).where(User.id == user_id))
        assert loaded_user is not None

        serialized = UserResponseSchema.model_validate(loaded_user)
        dumped = serialized.model_dump(mode="json")

        assert serialized.id == user_id
        assert serialized.email == "professor.tornearia@senai.br"
        assert serialized.role == UserRole.TEACHER
        assert serialized.is_active is True
        assert serialized.profile is not None
        assert serialized.profile.id == profile_id
        assert serialized.profile.full_name == "Roberto Carlos Almeida"
        assert serialized.profile.registration_number == "SENAI-PROF-0099"
        assert "password_hash" not in dumped


def test_paginated_response_and_query_params_calculation() -> None:
    """Verifica cálculo de offset, limit e total_pages em PaginationQueryParams e PaginatedResponse."""
    params = PaginationQueryParams(page=3, page_size=15, search="  Metrologia   Industrial  ")
    assert params.offset == 30
    assert params.limit == 15
    assert params.search == "Metrologia Industrial"

    paginated = PaginatedResponse[str].create(
        items=["Item 1", "Item 2"],
        total=35,
        params=params,
    )
    assert paginated.page == 3
    assert paginated.page_size == 15
    assert paginated.total == 35
    assert paginated.total_pages == 3
    assert paginated.items == ["Item 1", "Item 2"]


@pytest.fixture
def schema_test_app() -> FastAPI:
    """Cria uma aplicação FastAPI com rotas de teste para injeção automática de Body, Query e Path."""
    app = create_app()

    @app.post(
        "/test/users",
        response_model=UserResponseSchema,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_user_endpoint(payload: UserCreateSchema) -> User:
        now = datetime.now(timezone.utc)
        user_id = uuid4()
        orm_user = User(
            id=user_id,
            email=str(payload.email),
            password_hash="$2b$12$hashed_secret_never_exposed_in_response_123456789012",
            role=payload.role,
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
        )
        if payload.profile is not None:
            orm_user.profile = UserProfile(
                id=uuid4(),
                user_id=user_id,
                full_name=payload.profile.full_name,
                registration_number=payload.profile.registration_number,
                phone=payload.profile.phone,
                avatar_url=payload.profile.avatar_url,
                bio=payload.profile.bio,
                created_at=now,
                updated_at=now,
            )
        return orm_user

    @app.get(
        "/test/users/{user_id}",
        response_model=UserResponseSchema,
    )
    async def get_user_by_id_endpoint(
        user_id: UUIDPathParam,
        pagination: PaginationParamsDep,
    ) -> User:
        now = datetime.now(timezone.utc)
        return User(
            id=user_id,
            email="consulta@senai.br",
            password_hash="$2b$12$hashed_secret_never_exposed_in_response_123456789012",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @app.post(
        "/test/auth/login",
        response_model=TokenResponseSchema,
    )
    async def login_endpoint(credentials: LoginRequestSchema) -> TokenResponseSchema:
        now = datetime.now(timezone.utc)
        orm_user = User(
            id=uuid4(),
            email=str(credentials.email),
            password_hash="$2b$12$hashed_secret_never_exposed_in_response_123456789012",
            role=UserRole.COORDINATOR,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return TokenResponseSchema(
            user=UserResponseSchema.model_validate(orm_user),
            access_token="jwt-token-simulado",
        )

    return app


@pytest.fixture
async def schema_client(schema_test_app: FastAPI) -> AsyncClient:
    """Cliente HTTP assíncrono para testar rotas FastAPI integradas aos schemas Pydantic v2."""
    transport = ASGITransport(app=schema_test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def test_fastapi_endpoint_validates_and_serializes_sqlalchemy_model(
    schema_client: AsyncClient,
) -> None:
    """Testa injeção de UserCreateSchema no FastAPI e serialização automática de User ORM."""
    response = await schema_client.post(
        "/test/users",
        json={
            "email": "  Novo.Aluno@SENAI.br ",
            "password": "Senai@2026!Password",
            "role": "STUDENT",
            "profile": {
                "full_name": "  Lucas   Gabriel   Pereira ",
                "registration_number": " senai-2026-999 ",
                "phone": "(11) 91234-5678",
            },
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["email"] == "novo.aluno@senai.br"
    assert body["role"] == "STUDENT"
    assert body["is_active"] is True
    assert "password_hash" not in body
    assert "password" not in body
    assert body["profile"]["full_name"] == "Lucas Gabriel Pereira"
    assert body["profile"]["registration_number"] == "SENAI-2026-999"
    assert UUID(body["id"])


async def test_fastapi_endpoint_rejects_extra_fields_and_invalid_inputs_in_portuguese(
    schema_client: AsyncClient,
) -> None:
    """Testa rejeição HTTP 400 em português para payloads com campos extras, e-mail inválido e senha curta."""
    response = await schema_client.post(
        "/test/users",
        json={
            "email": "email-invalido",
            "password": "123",
            "propriedade_maliciosa": "injetada",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 400
    assert body["error"] == "VALIDATION_ERROR"

    details_by_field = {item["field"]: item["message"] for item in body["details"]}
    assert details_by_field["email"] == "Endereço de e-mail inválido."
    assert details_by_field["password"] == "A senha deve ter pelo menos 8 caracteres."
    assert details_by_field["propriedade_maliciosa"] == "Campo adicional não permitido."


async def test_fastapi_path_and_query_params_validation_in_portuguese(
    schema_client: AsyncClient,
) -> None:
    """Testa validação estrita de Path Params (UUID) e Query Params (PaginationParamsDep com extra='forbid')."""
    invalid_uuid_res = await schema_client.get("/test/users/id-nao-uuid?page=0&intruso=1")
    assert invalid_uuid_res.status_code == status.HTTP_400_BAD_REQUEST
    body = invalid_uuid_res.json()

    details_by_field = {item["field"]: item["message"] for item in body["details"]}
    assert details_by_field["user_id"] == "O valor deve ser um identificador UUID válido."
    assert "maior ou igual a 1" in details_by_field["page"]
    assert details_by_field["intruso"] == "Campo adicional não permitido."

    valid_uuid = uuid4()
    valid_res = await schema_client.get(f"/test/users/{valid_uuid}?page=2&page_size=10&search=Tornearia")
    assert valid_res.status_code == status.HTTP_200_OK
    assert valid_res.json()["id"] == str(valid_uuid)


async def test_login_and_update_schemas_validation(schema_client: AsyncClient) -> None:
    """Verifica LoginRequestSchema, TokenResponseSchema, UserUpdateSchema e MessageResponseSchema."""
    bad_login = await schema_client.post(
        "/test/auth/login",
        json={"email": "invalido", "password": "curta"},
    )
    assert bad_login.status_code == status.HTTP_400_BAD_REQUEST
    details = {item["field"]: item["message"] for item in bad_login.json()["details"]}
    assert details["email"] == "Endereço de e-mail inválido."
    assert details["password"] == "A senha deve ter pelo menos 8 caracteres."

    ok_login = await schema_client.post(
        "/test/auth/login",
        json={"email": "Coord@SENAI.br", "password": "SenhaValida123!"},
    )
    assert ok_login.status_code == status.HTTP_200_OK
    token_data = ok_login.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == "coord@senai.br"

    update_schema = UserUpdateSchema(
        email="  Atualizado@SENAI.br ",
        profile=UserProfileUpdateSchema(full_name="  Nome   Atualizado  "),
    )
    assert update_schema.email == "atualizado@senai.br"
    assert update_schema.profile is not None
    assert update_schema.profile.full_name == "Nome Atualizado"

    msg = MessageResponseSchema(message="Perfil atualizado com sucesso.")
    assert msg.success is True
