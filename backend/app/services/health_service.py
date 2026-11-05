from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends

from app.schemas.health import HealthResponse


class HealthService:
    """Serviço responsável pela verificação de integridade da aplicação."""

    async def check_health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            timestamp=datetime.now(timezone.utc),
        )


def get_health_service() -> HealthService:
    """Provedor de injeção de dependência para HealthService."""
    return HealthService()


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]

