"""Criptografia simétrica autenticada (Fernet / AES-256-GCM via biblioteca cryptography) para proteção de observações pedagógicas restritas (BE-045)."""

import base64
from functools import lru_cache
import hashlib
import os
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

ENCRYPTION_ENVELOPE_PREFIX: Final[str] = "ENC::FERNET+AES256GCM::"
LEGACY_FERNET_PREFIX: Final[str] = "ENC::FERNET::"
_AES256_NONCE_BYTES: Final[int] = 12


class PedagogicalNoteCipher:
    """Serviço de criptografia em dupla camada (AES-256-GCM + Fernet) para anotações pedagógicas sensíveis (LGPD / BE-045).

    Combina:
    1. AES-256-GCM (chave de 256 bits derivada via SHA-256) com nonce aleatório de 96 bits para confidencialidade AES-256.
    2. Fernet (AES-128-CBC + HMAC-SHA256 com timestamp assinado) sobre o envelope binário para compatibilidade nativa com tokens Fernet.
    """

    def __init__(self, secret_key: str) -> None:
        if not isinstance(secret_key, str) or len(secret_key.strip()) < 16:
            raise ValueError(
                "A chave de criptografia (secret_key) deve ter pelo menos 16 caracteres."
            )
        raw_secret = secret_key.strip().encode("utf-8")
        # Chave de 32 bytes (256 bits) para AES-256-GCM e base64 urlsafe para Fernet
        aes256_key = hashlib.sha256(b"nexa-aes256-gcm::" + raw_secret).digest()
        fernet_raw_key = hashlib.sha256(b"nexa-fernet::" + raw_secret).digest()
        fernet_key = base64.urlsafe_b64encode(fernet_raw_key)

        self._aesgcm = AESGCM(aes256_key)
        self._fernet = Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> str:
        """Criptografa o conteúdo textual da observação pedagógica com AES-256-GCM encapsulado em token Fernet."""
        if not isinstance(plaintext, str) or not plaintext.strip():
            raise ValueError(
                "O conteúdo da observação pedagógica para criptografia não pode ser vazio."
            )
        if self.is_encrypted(plaintext):
            return plaintext

        nonce = os.urandom(_AES256_NONCE_BYTES)
        aes256_ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            b"pedagogical_notes",
        )
        fernet_token = self._fernet.encrypt(nonce + aes256_ciphertext).decode("ascii")
        return f"{ENCRYPTION_ENVELOPE_PREFIX}{fernet_token}"

    def decrypt(self, stored_value: str) -> str:
        """Descriptografa o conteúdo armazenado em pedagogical_notes (suportando registros legados em texto claro do seed SQL)."""
        if not isinstance(stored_value, str):
            raise ValueError("O valor armazenado para descriptografia deve ser uma string.")

        if stored_value.startswith(ENCRYPTION_ENVELOPE_PREFIX):
            token_str = stored_value[len(ENCRYPTION_ENVELOPE_PREFIX) :]
            try:
                inner_blob = self._fernet.decrypt(token_str.encode("ascii"))
                if len(inner_blob) <= _AES256_NONCE_BYTES:
                    raise ValueError("Payload criptografado corrompido ou truncado.")
                nonce = inner_blob[:_AES256_NONCE_BYTES]
                ciphertext = inner_blob[_AES256_NONCE_BYTES:]
                plain_bytes = self._aesgcm.decrypt(
                    nonce,
                    ciphertext,
                    b"pedagogical_notes",
                )
                return plain_bytes.decode("utf-8")
            except (InvalidToken, InvalidTag, ValueError) as exc:
                raise ValueError(
                    "Falha ao descriptografar observação pedagógica restrita: token ou chave inválida."
                ) from exc

        if stored_value.startswith(LEGACY_FERNET_PREFIX):
            token_str = stored_value[len(LEGACY_FERNET_PREFIX) :]
            try:
                return self._fernet.decrypt(token_str.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                raise ValueError(
                    "Falha ao descriptografar token Fernet da observação pedagógica."
                ) from exc

        # Caso o registro tenha vindo de seed SQL direto não prefixado, tenta Fernet puro ou retorna o texto
        if stored_value.startswith("gAAAA"):
            try:
                inner_blob = self._fernet.decrypt(stored_value.encode("ascii"))
                nonce = inner_blob[:_AES256_NONCE_BYTES]
                ciphertext = inner_blob[_AES256_NONCE_BYTES:]
                return self._aesgcm.decrypt(
                    nonce,
                    ciphertext,
                    b"pedagogical_notes",
                ).decode("utf-8")
            except Exception:
                try:
                    return self._fernet.decrypt(stored_value.encode("ascii")).decode(
                        "utf-8"
                    )
                except Exception:
                    return stored_value

        return stored_value

    @staticmethod
    def is_encrypted(value: str) -> bool:
        """Indica se a string já se encontra cifrada pelo PedagogicalNoteCipher."""
        return isinstance(value, str) and (
            value.startswith(ENCRYPTION_ENVELOPE_PREFIX)
            or value.startswith(LEGACY_FERNET_PREFIX)
        )


@lru_cache
def get_pedagogical_note_cipher() -> PedagogicalNoteCipher:
    """Retorna instância em cache do serviço de criptografia de observações pedagógicas."""
    settings = get_settings()
    return PedagogicalNoteCipher(
        secret_key=settings.PEDAGOGICAL_NOTE_ENCRYPTION_KEY
    )


__all__ = [
    "ENCRYPTION_ENVELOPE_PREFIX",
    "LEGACY_FERNET_PREFIX",
    "PedagogicalNoteCipher",
    "get_pedagogical_note_cipher",
]
