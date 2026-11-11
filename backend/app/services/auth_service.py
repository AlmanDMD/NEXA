"""Serviço de domínio para Registro e Login com JWT (PyJWT) e Sessões (BE-005)."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Final

from fastapi import Depends

from app.core.config import Settings, SettingsDep
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.logging import logger
from app.core.security import (
    PasswordHasher,
    PasswordHasherDep,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from app.repositories.auth_repository import AuthRepository, AuthRepositoryDep
from app.schemas.auth import LoginRequestSchema, TokenResponseSchema
from app.schemas.user import UserCreateSchema, UserResponseSchema

INVALID_CREDENTIALS_MESSAGE: Final[str] = "Credenciais inválidas"


class AuthService:
    """Serviço responsável pelo registro de usuários, autenticação e emissão de tokens JWT."""

    def __init__(
        self,
        repository: AuthRepository,
        password_hasher: PasswordHasher,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._settings = settings

    def register_user(self, payload: UserCreateSchema) -> UserResponseSchema:
        """Registra um novo usuário com senha criptografada via Bcrypt e perfil opcional."""
        normalized_email = str(payload.email).strip().lower()
        existing_user = self._repository.get_user_by_email(normalized_email)
        if existing_user is not None:
            raise ConflictException(
                message="Já existe um usuário cadastrado com este endereço de e-mail."
            )

        if payload.profile is not None:
            existing_profile = self._repository.get_profile_by_registration_number(
                payload.profile.registration_number
            )
            if existing_profile is not None:
                raise ConflictException(
                    message="Já existe um perfil cadastrado com este número de matrícula."
                )

        hashed_password = self._password_hasher.hash_password(payload.password)
        created_user = self._repository.create_user(
            email=normalized_email,
            password_hash=hashed_password,
            role=payload.role,
            is_active=payload.is_active,
            profile_data=payload.profile,
        )

        logger.bind(
            user_id=str(created_user.id),
            role=str(created_user.role),
        ).info("Novo usuário registrado com sucesso.")

        return UserResponseSchema.model_validate(created_user)

    def authenticate_user(
        self,
        credentials: LoginRequestSchema,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenResponseSchema, str]:
        """Autentica credenciais em tempo constante e emite Access Token (15m) e Refresh Token (7d).

        Em caso de e-mail inexistente, senha incorreta ou conta inativa, retorna sempre
        a mensagem genérica 'Credenciais inválidas' (HTTP 401) para prevenir enumeração de contas.
        """
        normalized_email = str(credentials.email).strip().lower()
        db_user = self._repository.get_user_by_email(normalized_email)

        target_hash = (
            db_user.password_hash
            if db_user is not None
            else self._password_hasher.dummy_hash
        )
        is_password_valid = self._password_hasher.verify_password(
            credentials.password,
            target_hash,
        )

        if db_user is None or not is_password_valid or not db_user.is_active:
            logger.bind(ip_address=ip_address).warning(
                "Tentativa de autenticação recusada por credenciais inválidas ou conta inativa."
            )
            raise UnauthorizedException(message=INVALID_CREDENTIALS_MESSAGE)

        access_delta = timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_delta = timedelta(days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            subject=db_user.id,
            email=db_user.email,
            role=db_user.role,
            expires_delta=access_delta,
        )
        refresh_token = create_refresh_token(
            subject=db_user.id,
            expires_delta=refresh_delta,
        )

        refresh_token_hash = hash_refresh_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + refresh_delta

        self._repository.create_auth_session(
            user_id=db_user.id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        logger.bind(
            user_id=str(db_user.id),
            role=str(db_user.role),
            ip_address=ip_address,
        ).info("Login realizado com sucesso e sessão registrada.")

        token_response = TokenResponseSchema(
            user=UserResponseSchema.model_validate(db_user),
            access_token=access_token,
            token_type="bearer",
        )
        return token_response, refresh_token


def get_auth_service(
    repository: AuthRepositoryDep,
    password_hasher: PasswordHasherDep,
    settings: SettingsDep,
) -> AuthService:
    """Provedor de injeção de dependência para AuthService."""
    return AuthService(
        repository=repository,
        password_hasher=password_hasher,
        settings=settings,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

__all__ = [
    "AuthService",
    "AuthServiceDep",
    "INVALID_CREDENTIALS_MESSAGE",
    "get_auth_service",
]

