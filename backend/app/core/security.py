"""Serviço de hash de senhas (Bcrypt - BE-004) e tokens JWT com PyJWT (BE-005)."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import hmac
import re
from typing import Annotated, Any, Final
from uuid import UUID, uuid4

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
import jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.repositories.auth_repository import AuthRepositoryDep
from app.schemas.enums import UserRole

DEFAULT_BCRYPT_ROUNDS: Final[int] = 12
MIN_BCRYPT_ROUNDS: Final[int] = 4
MAX_BCRYPT_ROUNDS: Final[int] = 31
MAX_BCRYPT_PASSWORD_BYTES: Final[int] = 72

ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 15
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7
DEFAULT_JWT_ALGORITHM: Final[str] = "HS256"

_BCRYPT_HASH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\$2[aby]\$(\d{2})\$[./A-Za-z0-9]{53}$"
)

bearer_scheme = HTTPBearer(auto_error=False)

oauth2_scheme: Final[OAuth2PasswordBearer] = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    description="Autenticação OAuth2 com Bearer Token JWT para rotas protegidas.",
    auto_error=True,
)


class PasswordHasher:
    """Serviço criptográfico para geração e verificação de hashes de senha com Bcrypt.

    Implementa derivação de chave com salt criptograficamente aleatório por senha,
    fator de custo calibrado segundo recomendações da OWASP (rounds=12 por padrão)
    e verificação em tempo constante contra ataques de temporização (timing attacks).
    """

    def __init__(self, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> None:
        if (
            not isinstance(rounds, int)
            or isinstance(rounds, bool)
            or not (MIN_BCRYPT_ROUNDS <= rounds <= MAX_BCRYPT_ROUNDS)
        ):
            raise ValueError(
                f"O fator de custo (rounds) do Bcrypt deve ser um inteiro entre "
                f"{MIN_BCRYPT_ROUNDS} e {MAX_BCRYPT_ROUNDS}."
            )

        self._rounds: int = rounds
        self._dummy_hash: bytes = bcrypt.hashpw(
            b"nexa-constant-time-dummy-secret",
            bcrypt.gensalt(rounds=self._rounds),
        )

    @property
    def rounds(self) -> int:
        """Retorna o fator de custo (cost rounds) configurado para o Bcrypt."""
        return self._rounds

    @property
    def dummy_hash(self) -> str:
        """Retorna um hash Bcrypt válido para mitigação de enumeração de usuários por timing."""
        return self._dummy_hash.decode("utf-8")

    @staticmethod
    def _encode_and_validate_password(plain_password: str) -> bytes:
        """Valida e codifica a senha em bytes UTF-8 sem nunca expor o valor em texto puro."""
        if not isinstance(plain_password, str):
            raise ValueError("A senha deve ser um texto válido.")

        if not plain_password or not plain_password.strip():
            raise ValueError("A senha não pode ser vazia.")

        if "\x00" in plain_password:
            raise ValueError("A senha contém caracteres nulos não permitidos.")

        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError(
                f"A senha excede o limite criptográfico de {MAX_BCRYPT_PASSWORD_BYTES} bytes do Bcrypt."
            )

        return password_bytes

    def hash_password(self, plain_password: str) -> str:
        """Gera um hash Bcrypt seguro com salt aleatório para a senha fornecida."""
        password_bytes = self._encode_and_validate_password(plain_password)
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode("utf-8")

    def hash(self, plain_password: str) -> str:
        """Alias para hash_password mantendo compatibilidade com interfaces de hasher."""
        return self.hash_password(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha em texto puro corresponde ao hash Bcrypt em tempo constante.

        Utiliza comparação criptográfica em tempo constante (hmac.compare_digest) e executa
        derivação contra um hash dummy quando entradas são inválidas ou malformadas para
        mitigar ataques de canal lateral por temporização (timing attacks).
        """
        if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
            bcrypt.hashpw(b"nexa-invalid-type-timing-guard", self._dummy_hash)
            hmac.compare_digest(self._dummy_hash, self._dummy_hash)
            return False

        if (
            not plain_password
            or not plain_password.strip()
            or "\x00" in plain_password
            or not hashed_password
            or "\x00" in hashed_password
        ):
            bcrypt.hashpw(b"nexa-empty-input-timing-guard", self._dummy_hash)
            hmac.compare_digest(self._dummy_hash, self._dummy_hash)
            return False

        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
            bcrypt.hashpw(password_bytes[:MAX_BCRYPT_PASSWORD_BYTES], self._dummy_hash)
            hmac.compare_digest(self._dummy_hash, self._dummy_hash)
            return False

        hashed_bytes = hashed_password.encode("utf-8")
        try:
            computed_hash = bcrypt.hashpw(password_bytes, hashed_bytes)
        except ValueError:
            bcrypt.hashpw(password_bytes, self._dummy_hash)
            hmac.compare_digest(self._dummy_hash, self._dummy_hash)
            return False

        return hmac.compare_digest(computed_hash, hashed_bytes)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Alias para verify_password mantendo compatibilidade com interfaces de hasher."""
        return self.verify_password(plain_password, hashed_password)

    def needs_rehash(self, hashed_password: str) -> bool:
        """Indica se o hash armazenado precisa ser atualizado para o prefixo ou rounds atuais."""
        if not isinstance(hashed_password, str):
            return True

        match = _BCRYPT_HASH_PATTERN.match(hashed_password)
        if not match:
            return True

        hash_rounds = int(match.group(1))
        return not hashed_password.startswith("$2b$") or hash_rounds != self._rounds


@lru_cache
def get_password_hasher() -> PasswordHasher:
    """Provedor de dependência com cache para o serviço PasswordHasher."""
    settings = get_settings()
    return PasswordHasher(rounds=settings.BCRYPT_ROUNDS)


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]

password_hasher: Final[PasswordHasher] = get_password_hasher()


def hash_password(plain_password: str) -> str:
    """Gera hash Bcrypt utilizando a instância configurada do PasswordHasher."""
    return get_password_hasher().hash_password(plain_password)


def get_password_hash(plain_password: str) -> str:
    """Alias utilitário padrão FastAPI para geração de hash de senha."""
    return get_password_hasher().hash_password(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha em tempo constante utilizando a instância configurada do PasswordHasher."""
    return get_password_hasher().verify_password(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Verifica se um hash Bcrypt requer recálculo segundo a configuração atual."""
    return get_password_hasher().needs_rehash(hashed_password)


def hash_refresh_token(refresh_token: str) -> str:
    """Calcula o digest SHA-256 hexadecimal (64 chars minúsculos) de um Refresh Token."""
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise ValueError("O refresh token deve ser um texto não vazio.")
    return hashlib.sha256(refresh_token.strip().encode("utf-8")).hexdigest()


def create_access_token(
    subject: str | UUID,
    *,
    email: str | None = None,
    role: Any | None = None,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Gera um Access Token JWT assinado via PyJWT (vida útil padrão de 15 minutos)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire = now + delta

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
    }
    if email is not None:
        payload["email"] = email
    if role is not None:
        payload["role"] = str(role.value if hasattr(role, "value") else role)
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_ACCESS_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str | UUID,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Gera um Refresh Token JWT assinado via PyJWT (vida útil padrão de 7 dias)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    expire = now + delta

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_REFRESH_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida um Access Token JWT, lançando UnauthorizedException se inválido."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException(
            message="Token de acesso expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException(
            message="Token de acesso inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise UnauthorizedException(
            message="Token de acesso inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decodifica e valida um Refresh Token JWT, lançando UnauthorizedException se inválido."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException(message="Refresh token expirado.") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException(message="Refresh token inválido.") from exc

    if payload.get("type") != "refresh" or not payload.get("sub"):
        raise UnauthorizedException(message="Refresh token inválido.")

    return payload


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    repository: AuthRepositoryDep,
) -> User:
    """Valida o Bearer Token JWT e injeta a entidade User autenticada no contexto da requisição.

    - Bloqueia requisições sem Authorization Bearer retornando HTTP 401 Unauthorized.
    - Bloqueia tokens com assinatura inválida, expirados ou de tipo incorreto com HTTP 401.
    - Bloqueia usuários inexistentes ou inativos (is_active=False) com HTTP 401.
    - Carrega e retorna a instância do modelo SQLAlchemy User com id, email e role tipados.
    """
    if not token or not token.strip():
        raise UnauthorizedException(
            message="Token de acesso ausente ou inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    user_id_raw = payload.get("sub")
    try:
        user_id = UUID(str(user_id_raw))
    except (ValueError, TypeError) as exc:
        raise UnauthorizedException(
            message="Token de acesso inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = repository.get_user_by_id(user_id)
    if user is None:
        raise UnauthorizedException(
            message="Usuário não encontrado ou inativo.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise UnauthorizedException(
            message="Usuário inativo ou desativado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: str | UserRole) -> Callable[[User], User]:
    """Factory de dependência FastAPI para controle de acesso baseado em papéis (RBAC).

    Valida se o usuário autenticado (injetado via get_current_user) possui pelo menos
    um dos papéis permitidos para o endpoint.

    Args:
        *allowed_roles: Papéis institucionais autorizados (ex: 'ADMIN', 'COORDINATOR',
            UserRole.TEACHER, UserRole.STUDENT). Suporta tanto instâncias de UserRole
            quanto strings equivalentes.

    Returns:
        Callable de dependência FastAPI que recebe o usuário autenticado e o retorna
        caso autorizado, permitindo uso tanto em `dependencies=[Depends(require_role(...))]`
        quanto em injeção direta de parâmetro `current_user: User = Depends(require_role(...))`.

    Raises:
        ValueError: Caso nenhum papel seja especificado na chamada da factory.
        HTTPException: HTTP 403 Forbidden com detail 'Acesso não autorizado para seu perfil'
            caso o papel do usuário não esteja na lista permitida.
    """
    if not allowed_roles:
        raise ValueError("Pelo menos um papel deve ser informado para require_role.")

    normalized_roles: set[str] = set()
    for role in allowed_roles:
        if isinstance(role, UserRole):
            normalized_roles.add(role.value.upper())
        elif hasattr(role, "value"):
            normalized_roles.add(str(role.value).upper())
        elif isinstance(role, str):
            normalized_roles.add(role.strip().upper())
        else:
            normalized_roles.add(str(role).upper())

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        ).upper()

        if user_role_str not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado para seu perfil",
            )
        return current_user

    return role_checker


__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "CurrentUserDep",
    "DEFAULT_BCRYPT_ROUNDS",
    "DEFAULT_JWT_ALGORITHM",
    "MAX_BCRYPT_PASSWORD_BYTES",
    "MAX_BCRYPT_ROUNDS",
    "MIN_BCRYPT_ROUNDS",
    "PasswordHasher",
    "PasswordHasherDep",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "bearer_scheme",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "get_current_user",
    "get_password_hash",
    "get_password_hasher",
    "hash_password",
    "hash_refresh_token",
    "needs_rehash",
    "oauth2_scheme",
    "password_hasher",
    "require_role",
    "verify_password",
]
