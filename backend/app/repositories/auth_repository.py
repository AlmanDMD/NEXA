"""Repositório de persistência para Usuários, Perfis e Sessões de Autenticação (BE-005)."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import DbSessionDep
from app.models.auth_session import AuthSession
from app.models.user import User, UserProfile
from app.schemas.enums import UserRole
from app.schemas.user import UserProfileCreateSchema


class AuthRepository:
    """Repositório SQLAlchemy 2.0 para operações de autenticação e registro."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_user_by_email(self, email: str) -> User | None:
        """Busca um usuário pelo e-mail normalizado carregando o perfil 1:1."""
        normalized_email = email.strip().lower()
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == normalized_email)
        )
        return self._session.scalar(stmt)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo UUID carregando o perfil 1:1."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def get_profile_by_registration_number(
        self,
        registration_number: str,
    ) -> UserProfile | None:
        """Busca um perfil de usuário pelo número de matrícula SENAI."""
        normalized_reg = registration_number.strip().upper()
        stmt = select(UserProfile).where(
            UserProfile.registration_number == normalized_reg
        )
        return self._session.scalar(stmt)

    def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.STUDENT,
        is_active: bool = True,
        profile_data: UserProfileCreateSchema | None = None,
    ) -> User:
        """Cria e persiste um novo usuário e seu perfil opcional de forma transacional."""
        now = datetime.now(timezone.utc)
        user_id = uuid4()
        db_user = User(
            id=user_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )

        if profile_data is not None:
            db_user.profile = UserProfile(
                id=uuid4(),
                user_id=user_id,
                full_name=profile_data.full_name,
                registration_number=profile_data.registration_number,
                phone=profile_data.phone,
                avatar_url=profile_data.avatar_url,
                bio=profile_data.bio,
                created_at=now,
                updated_at=now,
            )

        self._session.add(db_user)
        self._session.commit()
        self._session.refresh(db_user)
        return db_user

    def create_auth_session(
        self,
        *,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthSession:
        """Registra uma nova sessão autenticada na tabela auth_sessions com hash SHA-256."""
        now = datetime.now(timezone.utc)
        effective_expires_at = (
            expires_at
            if expires_at > now
            else datetime.fromtimestamp(now.timestamp() + 1, tz=timezone.utc)
        )
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address[:45] if ip_address else None,
            expires_at=effective_expires_at,
            is_revoked=False,
            created_at=now,
        )
        self._session.add(auth_session)
        self._session.commit()
        self._session.refresh(auth_session)
        return auth_session

    def get_auth_session_by_token_hash(
        self,
        refresh_token_hash: str,
    ) -> AuthSession | None:
        """Busca uma sessão pelo hash SHA-256 do Refresh Token."""
        normalized_hash = refresh_token_hash.strip().lower()
        stmt = select(AuthSession).where(
            AuthSession.refresh_token_hash == normalized_hash
        )
        return self._session.scalar(stmt)


def get_auth_repository(session: DbSessionDep) -> AuthRepository:
    """Provedor de injeção de dependência para AuthRepository."""
    return AuthRepository(session=session)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repository)]

__all__ = [
    "AuthRepository",
    "AuthRepositoryDep",
    "get_auth_repository",
]

