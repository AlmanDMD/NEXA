"""Router para Conquistas, Níveis de Habilidade e Badges Desbloqueadas pelo Estudante (EPIC-09 / BE-046)."""

from fastapi import APIRouter, status

from app.core.security import CurrentUserDep
from app.schemas.gamification import (
    GamificationBadgesParamsDep,
    StudentGamificationOverviewResponseSchema,
)
from app.services.gamification_service import GamificationServiceDep

router = APIRouter(
    prefix="/api/v1/gamification",
    tags=["Gamification"],
)


@router.get(
    "/badges",
    response_model=StudentGamificationOverviewResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar insígnias conquistadas, próximas conquistas, nível atual de habilidade e critérios transparentes de XP",
)
async def list_student_gamification_badges(
    params: GamificationBadgesParamsDep,
    gamification_service: GamificationServiceDep,
    current_user: CurrentUserDep,
) -> StudentGamificationOverviewResponseSchema:
    """Retorna o catálogo de gamification_badges cruzado com student_achievements do estudante autenticado, sem rankings punitivos (BE-046)."""
    return gamification_service.get_student_badges_overview(
        params,
        current_user=current_user,
    )


__all__ = ["router"]
