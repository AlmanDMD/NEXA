"""Serviço de hash de senhas e verificação criptográfica com Bcrypt (BE-004)."""

import hmac
import re
from functools import lru_cache
from typing import Annotated, Final

import bcrypt
from fastapi import Depends
from fastapi.security import HTTPBearer

from app.core.config import get_settings

DEFAULT_BCRYPT_ROUNDS: Final[int] = 12
MIN_BCRYPT_ROUNDS: Final[int] = 4
MAX_BCRYPT_ROUNDS: Final[int] = 31
MAX_BCRYPT_PASSWORD_BYTES: Final[int] = 72

_BCRYPT_HASH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\$2[aby]\$(\d{2})\$[./A-Za-z0-9]{53}$"
)

bearer_scheme = HTTPBearer(auto_error=False)


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


__all__ = [
    "DEFAULT_BCRYPT_ROUNDS",
    "MAX_BCRYPT_PASSWORD_BYTES",
    "MAX_BCRYPT_ROUNDS",
    "MIN_BCRYPT_ROUNDS",
    "PasswordHasher",
    "PasswordHasherDep",
    "bearer_scheme",
    "get_password_hash",
    "get_password_hasher",
    "hash_password",
    "needs_rehash",
    "password_hasher",
    "verify_password",
]
