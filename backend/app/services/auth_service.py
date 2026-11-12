"""Serviço de domínio para Registro, Login e Renovação de Sessão com JWT (PyJWT) (BE-005 / BE-006)."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.config import Settings, SettingsDep
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.logging import logger
from app.core.security import (
    PasswordHasher,
    PasswordHasherDep,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
)
from app.repositories.auth_repository import AuthRepository, AuthRepositoryDep
from app.schemas.auth import (
    LoginRequestSchema,
    RefreshTokenResponseSchema,
    TokenResponseSchema,
)
from app.schemas.user import UserCreateSchema, UserResponseSchema

INVALID_CREDENTIALS_MESSAGE: Final[str] = "Credenciais inválidas"
REFRESH_TOKEN_MISSING_MESSAGE: Final[str] = "Refresh token não informado."
REFRESH_TOKEN_INVALID_MESSAGE: Final[str] = "Refresh token inválido."
REFRESH_TOKEN_EXPIRED_MESSAGE: Final[str] = "Refresh token expirado."
REFRESH_TOKEN_REVOKED_REUSE_MESSAGE: Final[str] = (
    "Refresh token revogado. Por segurança, todas as sessões ativas foram encerradas."
)


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

    def refresh_session(
        self,
        refresh_token: str | None,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[RefreshTokenResponseSchema, str]:
        """Valida o Refresh Token, detecta reúso com revogação em cadeia e realiza Token Rotation (BE-006)."""
        if not refresh_token or not isinstance(refresh_token, str) or not refresh_token.strip():
            logger.bind(ip_address=ip_address).warning(
                "Tentativa de renovação de sessão sem cookie refresh_token."
            )
            raise UnauthorizedException(message=REFRESH_TOKEN_MISSING_MESSAGE)

        clean_token = refresh_token.strip()
        token_hash = hash_refresh_token(clean_token)
        stored_session = self._repository.get_auth_session_by_token_hash(token_hash)

        if stored_session is not None and stored_session.is_revoked:
            revoked_count = self._repository.revoke_all_user_sessions(stored_session.user_id)
            logger.bind(
                user_id=str(stored_session.user_id),
                session_id=str(stored_session.id),
                revoked_sessions_count=revoked_count,
                ip_address=ip_address,
            ).warning(
                "Reúso de refresh token revogado detectado. Revogação em cadeia executada."
            )
            raise UnauthorizedException(message=REFRESH_TOKEN_REVOKED_REUSE_MESSAGE)

        payload = decode_refresh_token(clean_token)

        if stored_session is None:
            logger.bind(ip_address=ip_address).warning(
                "Tentativa de renovação com refresh token não encontrado na tabela auth_sessions."
            )
            raise UnauthorizedException(message=REFRESH_TOKEN_INVALID_MESSAGE)

        now = datetime.now(timezone.utc)
        session_expires_at = (
            stored_session.expires_at
            if stored_session.expires_at.tzinfo is not None
            else stored_session.expires_at.replace(tzinfo=timezone.utc)
        )
        if session_expires_at <= now:
            logger.bind(
                user_id=str(stored_session.user_id),
                session_id=str(stored_session.id),
                ip_address=ip_address,
            ).warning("Tentativa de renovação com sessão expirada no banco de dados.")
            raise UnauthorizedException(message=REFRESH_TOKEN_EXPIRED_MESSAGE)

        try:
            token_user_id = UUID(str(payload.get("sub")))
        except (ValueError, TypeError) as exc:
            raise UnauthorizedException(message=REFRESH_TOKEN_INVALID_MESSAGE) from exc

        if token_user_id != stored_session.user_id:
            self._repository.revoke_all_user_sessions(stored_session.user_id)
            logger.bind(
                user_id=str(stored_session.user_id),
                token_sub=str(token_user_id),
                ip_address=ip_address,
            ).warning("Divergência entre sub do token e user_id da sessão. Sessões revogadas.")
            raise UnauthorizedException(message=REFRESH_TOKEN_INVALID_MESSAGE)

        db_user = self._repository.get_user_by_id(stored_session.user_id)
        if db_user is None or not db_user.is_active:
            self._repository.revoke_auth_session(stored_session)
            logger.bind(
                user_id=str(stored_session.user_id),
                ip_address=ip_address,
            ).warning("Tentativa de renovação de sessão para usuário inexistente ou inativo.")
            raise UnauthorizedException(message=REFRESH_TOKEN_INVALID_MESSAGE)

        access_delta = timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_delta = timedelta(days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_access_token = create_access_token(
            subject=db_user.id,
            email=db_user.email,
            role=db_user.role,
            expires_delta=access_delta,
        )
        new_refresh_token = create_refresh_token(
            subject=db_user.id,
            expires_delta=refresh_delta,
        )
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)
        new_expires_at = now + refresh_delta

        rotated_session = self._repository.rotate_auth_session(
            previous_session=stored_session,
            new_refresh_token_hash=new_refresh_token_hash,
            expires_at=new_expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        logger.bind(
            user_id=str(db_user.id),
            previous_session_id=str(stored_session.id),
            new_session_id=str(rotated_session.id),
            ip_address=ip_address,
        ).info("Sessão renovada com sucesso via Refresh Token Rotation.")

        refresh_response = RefreshTokenResponseSchema(
            access_token=new_access_token,
            token_type="bearer",
        )
        return refresh_response, new_refresh_token


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
    "REFRESH_TOKEN_EXPIRED_MESSAGE",
    "REFRESH_TOKEN_INVALID_MESSAGE",
    "REFRESH_TOKEN_MISSING_MESSAGE",
    "REFRESH_TOKEN_REVOKED_REUSE_MESSAGE",
    "get_auth_service",
]

