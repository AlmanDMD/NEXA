"""Serviço de auditoria centralizada (AuditService) para registro de operações sensíveis (BE-019)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository, AuditRepositoryDep


class AuditService:
    """Serviço de aplicação para registro estruturado de trilha de auditoria em audit_logs."""

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def log_action(
        self,
        *,
        user_id: UUID | None,
        action: str,
        entity: str,
        entity_id: str | UUID,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        commit: bool = False,
    ) -> AuditLog:
        """Grava registro imutável de auditoria contendo estado anterior e novo em JSON."""
        audit_entry = self._repository.create_log(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            commit=commit,
        )
        logger.bind(
            audit_id=str(audit_entry.id),
            actor_id=str(user_id) if user_id is not None else None,
            action=audit_entry.action,
            entity=audit_entry.entity,
            entity_id=audit_entry.entity_id,
        ).info("Evento de auditoria registrado em audit_logs.")
        return audit_entry


def get_audit_service(repository: AuditRepositoryDep) -> AuditService:
    """Provedor de injeção de dependência para AuditService."""
    return AuditService(repository=repository)


AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]

__all__ = [
    "AuditService",
    "AuditServiceDep",
    "get_audit_service",
]
