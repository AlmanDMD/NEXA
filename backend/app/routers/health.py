from fastapi import APIRouter, status

from app.schemas.health import HealthResponse
from app.services.health_service import HealthServiceDep

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
)
async def health_check(health_service: HealthServiceDep) -> HealthResponse:
    """Retorna o status da aplicação e o timestamp atual em UTC."""
    return await health_service.check_health()

