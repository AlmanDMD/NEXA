"""Repositório SQLAlchemy 2.0 para registro imutável de logs de auditoria (BE-019 / DB-009)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.database import DbSessionDep
from app.models.audit_log import AuditLog


class AuditRepository:
    """Repositório SQLAlchemy 2.0 responsável por persistir eventos na tabela audit_logs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    @staticmethod
    def _encode_json_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
        """Serializa tipos Python (UUID, Decimal, date, Enum) em dicionário JSON compatível."""
        if payload is None:
            return None
        encoded: dict[str, Any] = jsonable_encoder(payload)
        return encoded

    def create_log(
        self,
        *,
        user_id: UUID | None,
        action: str,
        entity: str,
        entity_id: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        commit: bool = False,
    ) -> AuditLog:
        """Registra um evento de auditoria com opção de flush na transação corrente ou commit direto."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_values=self._encode_json_payload(old_values),
            new_values=self._encode_json_payload(new_values),
            ip_address=ip_address,
        )
        self._session.add(audit_entry)
        self._session.flush()
        if commit:
            self._session.commit()
            self._session.refresh(audit_entry)
        return audit_entry


def get_audit_repository(session: DbSessionDep) -> AuditRepository:
    """Provedor de injeção de dependência para AuditRepository."""
    return AuditRepository(session=session)


AuditRepositoryDep = Annotated[AuditRepository, Depends(get_audit_repository)]

__all__ = [
    "AuditRepository",
    "AuditRepositoryDep",
    "get_audit_repository",
]
