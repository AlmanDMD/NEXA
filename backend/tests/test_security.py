"""Testes unitários e de integração para o serviço de Hash de Senhas e Segurança (BE-004)."""

from datetime import datetime, timezone
import hmac
from unittest.mock import patch
from uuid import uuid4

import bcrypt
from fastapi import Depends, FastAPI, status
from fastapi.routing import APIRoute
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    DEFAULT_BCRYPT_ROUNDS,
    MAX_BCRYPT_PASSWORD_BYTES,
    MAX_BCRYPT_ROUNDS,
    MIN_BCRYPT_ROUNDS,
    PasswordHasher,
    PasswordHasherDep,
    UnauthorizedException,
    get_password_hash,
    get_password_hasher,
    hash_password,
    needs_rehash,
    password_hasher,
    verify_password,
)
from app.main import create_app
from app.models import Base, User, UserProfile
from app.schemas import (
    LoginRequestSchema,
    TokenResponseSchema,
    UserCreateSchema,
    UserResponseSchema,
)


def test_password_hasher_default_and_custom_rounds() -> None:
    """Verifica configuração padrão (rounds=12) e customizada do fator de custo Bcrypt."""
    default_hasher = PasswordHasher()
    assert default_hasher.rounds == DEFAULT_BCRYPT_ROUNDS == 12
    assert default_hasher.dummy_hash.startswith("$2b$12$")
    assert len(default_hasher.dummy_hash) == 60

    fast_hasher = PasswordHasher(rounds=4)
    assert fast_hasher.rounds == 4
    assert fast_hasher.dummy_hash.startswith("$2b$04$")


@pytest.mark.parametrize(
    "invalid_rounds",
    [
        MIN_BCRYPT_ROUNDS - 1,
        0,
        -5,
        MAX_BCRYPT_ROUNDS + 1,
        True,
        False,
        "12",  # type: ignore[list-item]
        None,  # type: ignore[list-item]
    ],
)
def test_password_hasher_rejects_invalid_rounds(invalid_rounds: int) -> None:
    """Garante que fatores de custo fora do intervalo [4, 31] ou tipos inválidos levantam ValueError."""
    with pytest.raises(ValueError, match="O fator de custo \\(rounds\\) do Bcrypt deve ser um inteiro"):
        PasswordHasher(rounds=invalid_rounds)


def test_hash_password_generates_unique_salted_bcrypt_hashes() -> None:
    """Garante geração de hashes Bcrypt válidos ($2b$12$) com salt aleatório a cada execução."""
    secret = "Senai@2026!Seguranca"
    hash_1 = hash_password(secret)
    hash_2 = get_password_hash(secret)
    hash_3 = password_hasher.hash(secret)

    for generated_hash in (hash_1, hash_2, hash_3):
        assert isinstance(generated_hash, str)
        assert len(generated_hash) == 60
        assert generated_hash.startswith("$2b$12$")
        assert secret not in generated_hash
        assert generated_hash != secret

    assert hash_1 != hash_2
    assert hash_2 != hash_3

    assert verify_password(secret, hash_1) is True
    assert verify_password(secret, hash_2) is True
    assert password_hasher.verify(secret, hash_3) is True


def test_verify_password_with_correct_and_incorrect_passwords() -> None:
    """Valida verificação positiva para senha exata e negativa para variações incorretas."""
    hasher = PasswordHasher(rounds=4)
    correct_password = "Senai# Mecânica 2026!"
    hashed = hasher.hash_password(correct_password)

    assert hasher.verify_password(correct_password, hashed) is True

    assert hasher.verify_password("senai# mecânica 2026!", hashed) is False
    assert hasher.verify_password("Senai# Mecânica 2026", hashed) is False
    assert hasher.verify_password("Senai# Mecânica 2026! ", hashed) is False
    assert hasher.verify_password(" OutraSenhaQualquer@123", hashed) is False


def test_password_boundary_72_bytes_and_never_leaks_plaintext_in_errors() -> None:
    """Valida limite de 72 bytes UTF-8 do Bcrypt e garante que erros nunca exponham a senha."""
    hasher = PasswordHasher(rounds=4)

    exact_72_ascii = "A" * 70 + "1!"
    assert len(exact_72_ascii.encode("utf-8")) == MAX_BCRYPT_PASSWORD_BYTES
    hashed_72 = hasher.hash_password(exact_72_ascii)
    assert hasher.verify_password(exact_72_ascii, hashed_72) is True

    over_72_secret = "SenhaSuperSecretaQueNaoPodeVazarNoErro_" + ("X" * 40)
    assert len(over_72_secret.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES

    with pytest.raises(ValueError) as exc_info:
        hasher.hash_password(over_72_secret)

    error_message = str(exc_info.value)
    assert "excede o limite criptográfico de 72 bytes" in error_message
    assert over_72_secret not in error_message


@pytest.mark.parametrize(
    ("invalid_password", "expected_msg"),
    [
        (None, "A senha deve ser um texto válido."),
        (12345678, "A senha deve ser um texto válido."),
        ("", "A senha não pode ser vazia."),
        ("     ", "A senha não pode ser vazia."),
        ("SenhaCom\x00ByteNulo", "A senha contém caracteres nulos não permitidos."),
    ],
)
def test_hash_password_rejects_invalid_inputs_without_leaking_value(
    invalid_password: object,
    expected_msg: str,
) -> None:
    """Entradas nulas, vazias ou com byte nulo devem levantar ValueError seguro em português."""
    hasher = PasswordHasher(rounds=4)
    with pytest.raises(ValueError, match=expected_msg) as exc_info:
        hasher.hash_password(invalid_password)  # type: ignore[arg-type]

    if isinstance(invalid_password, str) and invalid_password.strip():
        assert invalid_password not in str(exc_info.value)


def test_verify_password_constant_time_execution_and_edge_cases() -> None:
    """Garante execução em tempo constante (hmac.compare_digest + bcrypt.hashpw) em todos os fluxos."""
    hasher = PasswordHasher(rounds=4)
    valid_hash = hasher.hash_password("Senai@2026")

    with (
        patch("app.core.security.hmac.compare_digest", wraps=hmac.compare_digest) as spy_compare,
        patch("app.core.security.bcrypt.hashpw", wraps=bcrypt.hashpw) as spy_hashpw,
    ):
        assert hasher.verify_password("Senai@2026", valid_hash) is True
        assert hasher.verify_password("SenhaErrada@2026", valid_hash) is False
        assert hasher.verify_password(None, valid_hash) is False  # type: ignore[arg-type]
        assert hasher.verify_password("Senai@2026", None) is False  # type: ignore[arg-type]
        assert hasher.verify_password("", valid_hash) is False
        assert hasher.verify_password("   ", valid_hash) is False
        assert hasher.verify_password("Senha\x00Nula", valid_hash) is False
        assert hasher.verify_password("Senai@2026", "") is False
        assert hasher.verify_password("Senai@2026", "hash\x00invalido") is False
        assert hasher.verify_password("B" * 73, valid_hash) is False
        assert hasher.verify_password("Senai@2026", "hash-malformado-nao-bcrypt") is False

        assert spy_compare.call_count == 11
        assert spy_hashpw.call_count == 12


def test_needs_rehash_detects_cost_factor_and_prefix_changes() -> None:
    """Verifica detecção de hashes que precisam ser recalculados por mudança de rounds ou versão."""
    hasher_4 = PasswordHasher(rounds=4)
    hasher_5 = PasswordHasher(rounds=5)

    hash_r4 = hasher_4.hash_password("Senai@2026")
    assert hasher_4.needs_rehash(hash_r4) is False
    assert hasher_5.needs_rehash(hash_r4) is True

    legacy_2a_hash = "$2a$" + hash_r4[4:]
    assert hasher_4.needs_rehash(legacy_2a_hash) is True

    assert hasher_4.needs_rehash("hash-invalido") is True
    assert hasher_4.needs_rehash(None) is True  # type: ignore[arg-type]

    current_default_hash = hash_password("Senai@2026")
    assert needs_rehash(current_default_hash) is False
    assert needs_rehash(hash_r4) is True


def test_fastapi_and_sqlalchemy_integration_with_password_hasher() -> None:
    """Valida integração completa do PasswordHasher com modelos SQLAlchemy 2.0, Schemas e rotas FastAPI."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    fast_hasher = PasswordHasher(rounds=4)
    app: FastAPI = create_app()

    def get_db() -> Session:
        return TestingSessionLocal()

    @app.post(
        "/test/auth/register",
        response_model=UserResponseSchema,
        status_code=status.HTTP_201_CREATED,
    )
    def register_user(
        payload: UserCreateSchema,
        hasher: PasswordHasherDep,
        session: Session = Depends(get_db),
    ) -> UserResponseSchema:
        now = datetime.now(timezone.utc)
        user_id = uuid4()
        hashed_pw = hasher.hash_password(payload.password)
        db_user = User(
            id=user_id,
            email=str(payload.email),
            password_hash=hashed_pw,
            role=payload.role,
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
        )
        if payload.profile is not None:
            db_user.profile = UserProfile(
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
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserResponseSchema.model_validate(db_user)

    @app.post(
        "/test/auth/login",
        response_model=TokenResponseSchema,
    )
    def login_user(
        credentials: LoginRequestSchema,
        hasher: PasswordHasherDep,
        session: Session = Depends(get_db),
    ) -> TokenResponseSchema:
        db_user = session.scalar(select(User).where(User.email == str(credentials.email)))
        target_hash = db_user.password_hash if db_user is not None else hasher.dummy_hash
        is_valid = hasher.verify_password(credentials.password, target_hash)

        if db_user is None or not is_valid or not db_user.is_active:
            raise UnauthorizedException(message="E-mail ou senha inválidos.")

        return TokenResponseSchema(
            user=UserResponseSchema.model_validate(db_user),
            access_token="simulated-jwt-access-token",
        )

    registered_paths = {
        route.path for route in app.routes if isinstance(route, APIRoute)
    }
    assert "/test/auth/register" in registered_paths
    assert "/test/auth/login" in registered_paths
    db_dep = get_db()
    db_dep.close()

    plain_secret = "Senai@2026!Forte"
    with TestingSessionLocal() as session:
        create_payload = UserCreateSchema.model_validate(
            {
                "email": "Maria.Oliveira@SENAI.br",
                "password": plain_secret,
                "role": "TEACHER",
                "profile": {
                    "full_name": "Maria Fernanda Oliveira",
                    "registration_number": "SENAI-DOC-2026",
                },
            }
        )
        created_response = register_user(
            payload=create_payload,
            hasher=fast_hasher,
            session=session,
        )
        reg_body = created_response.model_dump(mode="json")
        assert reg_body["email"] == "maria.oliveira@senai.br"
        assert "password" not in reg_body
        assert "password_hash" not in reg_body
        assert plain_secret not in str(reg_body)

        stored_user = session.scalar(
            select(User).where(User.email == "maria.oliveira@senai.br")
        )
        assert stored_user is not None
        assert stored_user.password_hash != plain_secret
        assert stored_user.password_hash.startswith("$2b$04$")
        assert fast_hasher.verify_password(plain_secret, stored_user.password_hash) is True

        token_response = login_user(
            credentials=LoginRequestSchema(
                email="maria.oliveira@senai.br",
                password=plain_secret,
            ),
            hasher=fast_hasher,
            session=session,
        )
        assert token_response.access_token == "simulated-jwt-access-token"
        assert token_response.user.email == "maria.oliveira@senai.br"

        with pytest.raises(UnauthorizedException) as exc_wrong_pw:
            login_user(
                credentials=LoginRequestSchema(
                    email="maria.oliveira@senai.br",
                    password="SenhaIncorreta@2026",
                ),
                hasher=fast_hasher,
                session=session,
            )
        assert exc_wrong_pw.value.status_code == status.HTTP_401_UNAUTHORIZED

        with pytest.raises(UnauthorizedException) as exc_unknown_email:
            login_user(
                credentials=LoginRequestSchema(
                    email="inexistente@senai.br",
                    password=plain_secret,
                ),
                hasher=fast_hasher,
                session=session,
            )
        assert exc_unknown_email.value.status_code == status.HTTP_401_UNAUTHORIZED
