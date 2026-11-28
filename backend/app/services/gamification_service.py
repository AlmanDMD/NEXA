"""Serviço de domínio para Conquistas, Níveis de Habilidade e Badges Desbloqueadas pelo Estudante (BE-046)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.models.gamification import GamificationBadge, StudentAchievement
from app.models.user import User
from app.repositories.gamification_repository import (
    GamificationRepository,
    GamificationRepositoryDep,
)
from app.schemas.enums import SkillLevel
from app.schemas.gamification import (
    GAMIFICATION_ETHICAL_PRIVACY_NOTE,
    GAMIFICATION_SCORING_RULE_EXPLANATION,
    GamificationBadgesQueryParams,
    GamificationCompetencySummarySchema,
    GamificationSkillLevelTierSchema,
    StudentBadgeProgressItemSchema,
    StudentGamificationOverviewResponseSchema,
)

SKILL_LEVEL_TIERS: Final[tuple[GamificationSkillLevelTierSchema, ...]] = (
    GamificationSkillLevelTierSchema(
        level_number=1,
        level_key=SkillLevel.BEGINNER,
        level_title="Nível 1 — Iniciante",
        min_xp=0,
        max_xp=149,
        description="Início da jornada prática nas oficinas SENAI, familiarizando-se com instrumentos de medição, leitura técnica e normas de segurança.",
    ),
    GamificationSkillLevelTierSchema(
        level_number=2,
        level_key=SkillLevel.PRACTITIONER,
        level_title="Nível 2 — Praticante",
        min_xp=150,
        max_xp=299,
        description="Execução autônoma de atividades de bancada com controle dimensional consistente e cumprimento rigoroso das normas NR-12.",
    ),
    GamificationSkillLevelTierSchema(
        level_number=3,
        level_key=SkillLevel.PROFICIENT,
        level_title="Nível 3 — Proficiente",
        min_xp=300,
        max_xp=499,
        description="Domínio técnico comprovado em múltiplos módulos práticos, alta precisão nas tolerâncias mecânicas e assiduidade exemplar.",
    ),
    GamificationSkillLevelTierSchema(
        level_number=4,
        level_key=SkillLevel.SPECIALIST,
        level_title="Nível 4 — Especialista",
        min_xp=500,
        max_xp=None,
        description="Excelência integral nas competências técnicas, procedimentais e de segurança industrial do curso técnico SENAI.",
    ),
)

_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100.00")
_QUANT = Decimal("0.01")


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um datetime esteja normalizado em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def compute_skill_level_from_xp(
    total_xp: int,
) -> tuple[
    GamificationSkillLevelTierSchema,
    GamificationSkillLevelTierSchema | None,
    int,
    Decimal,
]:
    """Determina de forma transparente o nível atual de habilidade, o próximo nível, XP faltante e percentual na faixa (BE-046 / BE-047)."""
    safe_xp = max(0, int(total_xp))
    current_tier = SKILL_LEVEL_TIERS[0]
    next_tier: GamificationSkillLevelTierSchema | None = None

    for idx, tier in enumerate(SKILL_LEVEL_TIERS):
        if tier.max_xp is None or safe_xp <= tier.max_xp:
            current_tier = tier
            next_tier = (
                SKILL_LEVEL_TIERS[idx + 1]
                if idx + 1 < len(SKILL_LEVEL_TIERS)
                else None
            )
            break

    if next_tier is None:
        return current_tier, None, 0, _HUNDRED

    xp_to_next = max(0, next_tier.min_xp - safe_xp)
    tier_span = max(1, next_tier.min_xp - current_tier.min_xp)
    earned_in_tier = max(0, safe_xp - current_tier.min_xp)
    progress_pct = min(
        _HUNDRED,
        (Decimal(earned_in_tier) * _HUNDRED / Decimal(tier_span)).quantize(_QUANT),
    )
    return current_tier, next_tier, xp_to_next, progress_pct


class GamificationService:
    """Serviço responsável pelo cruzamento de gamification_badges e student_achievements sem rankings punitivos (BE-046)."""

    def __init__(self, repository: GamificationRepository) -> None:
        self._repository = repository

    @staticmethod
    def _estimate_locked_badge_progress(
        badge: GamificationBadge,
        *,
        competency_averages: dict[UUID, Decimal],
        overall_verified_avg: Decimal,
        evidences_count: int,
        best_attendance_rate: Decimal,
        self_eval_answers_count: int,
        aligned_diagnostics_count: int,
    ) -> tuple[Decimal, str]:
        """Calcula o percentual de progresso individual (0.00 a 95.00) para uma conquista ainda não desbloqueada."""
        code_upper = badge.code.upper()

        if badge.competency_id is not None and badge.competency_id in competency_averages:
            avg_lvl = competency_averages[badge.competency_id]
            pct = min(
                Decimal("95.00"),
                (avg_lvl * _HUNDRED / Decimal("4.50")).quantize(_QUANT),
            )
            return (
                pct,
                f"Em progresso ({pct}%): nível prático médio atual {avg_lvl}/5.00 na competência vinculada.",
            )

        if "ASSIDUIDADE" in code_upper or "ATTENDANCE" in code_upper:
            pct = min(Decimal("95.00"), max(_ZERO, best_attendance_rate))
            if pct > _ZERO:
                return (
                    pct,
                    f"Em progresso ({pct}%): taxa de presença atual em {best_attendance_rate}%.",
                )
            return _ZERO, "Aguardando registro de presença nas aulas do módulo."

        if "AUTOCONHECIMENTO" in code_upper or "SELF" in code_upper:
            if aligned_diagnostics_count > 0:
                return (
                    Decimal("90.00"),
                    "Quase lá (90.00%): diagnóstico alinhado identificado, aguardando fechamento do ciclo.",
                )
            if self_eval_answers_count > 0:
                return (
                    Decimal("50.00"),
                    "Em progresso (50.00%): autoavaliação enviada, aguardando cruzamento com avaliação docente.",
                )
            return (
                _ZERO,
                "Responda ao questionário de autoavaliação do módulo para iniciar o progresso.",
            )

        if evidences_count > 0 and overall_verified_avg > _ZERO:
            pct = min(
                Decimal("90.00"),
                (overall_verified_avg * _HUNDRED / Decimal("5.00")).quantize(_QUANT),
            )
            return (
                pct,
                f"Em progresso ({pct}%): baseado em {evidences_count} avaliação(ões) prática(s) de oficina.",
            )

        return (
            _ZERO,
            "Conquista disponível: realize as atividades práticas da oficina para progredir.",
        )

    def get_student_badges_overview(
        self,
        params: GamificationBadgesQueryParams,
        *,
        current_user: User,
    ) -> StudentGamificationOverviewResponseSchema:
        """Retorna catálogo de badges cruzado com conquistas do estudante logado, XP, nível atual e regras transparentes (BE-046)."""
        self._repository.ensure_default_catalog_if_empty()

        all_active_badges = self._repository.list_active_badges(
            competency_id=params.competency_id,
        )
        achievements = self._repository.list_student_achievements(current_user.id)
        achievement_by_badge_id: dict[UUID, StudentAchievement] = {
            ach.badge_id: ach for ach in achievements
        }

        # O XP total do estudante considera todas as conquistas desbloqueadas por ele
        total_xp = sum(
            ach.badge.xp_reward
            for ach in achievements
            if ach.badge is not None and ach.badge.is_active
        )
        current_tier, next_tier, xp_to_next, level_progress_pct = (
            compute_skill_level_from_xp(total_xp)
        )

        comp_averages = self._repository.get_student_competency_verified_averages(
            current_user.id
        )
        overall_avg, evidences_count = (
            self._repository.get_student_overall_verified_average_and_count(
                current_user.id
            )
        )
        best_attendance = self._repository.get_student_best_attendance_rate(
            current_user.id
        )
        self_eval_count, aligned_count = (
            self._repository.get_student_self_assessment_progress_stats(
                current_user.id
            )
        )

        badge_items: list[StudentBadgeProgressItemSchema] = []
        unlocked_items: list[StudentBadgeProgressItemSchema] = []
        upcoming_items: list[StudentBadgeProgressItemSchema] = []

        for badge in all_active_badges:
            ach = achievement_by_badge_id.get(badge.id)
            is_unlocked = ach is not None
            comp = badge.competency

            if is_unlocked and ach is not None:
                progress_pct = _HUNDRED
                status_label = f"Conquista desbloqueada (+{badge.xp_reward} XP)"
                unlocked_at_utc = _ensure_utc(ach.unlocked_at)
                origin_ref = ach.origin_reference
            else:
                progress_pct, status_label = self._estimate_locked_badge_progress(
                    badge,
                    competency_averages=comp_averages,
                    overall_verified_avg=overall_avg,
                    evidences_count=evidences_count,
                    best_attendance_rate=best_attendance,
                    self_eval_answers_count=self_eval_count,
                    aligned_diagnostics_count=aligned_count,
                )
                unlocked_at_utc = None
                origin_ref = None

            item = StudentBadgeProgressItemSchema(
                badge_id=badge.id,
                code=badge.code,
                title=badge.title,
                description=badge.description,
                criteria_explanation=badge.criteria_explanation,
                icon_name=badge.icon_name,
                xp_reward=badge.xp_reward,
                competency_id=badge.competency_id,
                competency=(
                    GamificationCompetencySummarySchema(
                        id=comp.id,
                        code=comp.code,
                        title=comp.title,
                        category=comp.category,
                    )
                    if comp is not None
                    else None
                ),
                unlocked=is_unlocked,
                is_unlocked=is_unlocked,
                progress_percentage=progress_pct,
                status_label=status_label,
                unlocked_at=unlocked_at_utc,
                origin_reference=origin_ref,
            )

            if is_unlocked:
                unlocked_items.append(item)
            else:
                upcoming_items.append(item)

            if not params.unlocked_only or is_unlocked:
                badge_items.append(item)

        # Ordena próximas conquistas pelas mais próximas de serem desbloqueadas (maior progress_percentage primeiro)
        upcoming_items.sort(
            key=lambda b: (-b.progress_percentage, b.xp_reward, b.code)
        )

        total_catalog = len(all_active_badges)
        unlocked_count = len(unlocked_items)
        locked_count = len(upcoming_items)
        completion_pct = (
            (Decimal(unlocked_count) * _HUNDRED / Decimal(total_catalog)).quantize(
                _QUANT
            )
            if total_catalog > 0
            else _ZERO
        )

        return StudentGamificationOverviewResponseSchema(
            student_id=current_user.id,
            total_xp=total_xp,
            current_level_number=current_tier.level_number,
            current_level=current_tier.level_key,
            current_level_title=current_tier.level_title,
            next_level=next_tier.level_key if next_tier is not None else None,
            next_level_title=(
                next_tier.level_title if next_tier is not None else None
            ),
            next_level_xp_threshold=(
                next_tier.min_xp if next_tier is not None else None
            ),
            xp_to_next_level=xp_to_next,
            level_progress_percentage=level_progress_pct,
            unlocked_count=unlocked_count,
            locked_count=locked_count,
            total_badges=total_catalog,
            completion_percentage=completion_pct,
            scoring_rule_explanation=GAMIFICATION_SCORING_RULE_EXPLANATION,
            ethical_privacy_note=GAMIFICATION_ETHICAL_PRIVACY_NOTE,
            level_tiers=list(SKILL_LEVEL_TIERS),
            badges=badge_items,
            unlocked_badges=unlocked_items,
            upcoming_badges=upcoming_items,
        )


def get_gamification_service(
    repository: GamificationRepositoryDep,
) -> GamificationService:
    """Provedor de injeção de dependência para GamificationService."""
    return GamificationService(repository=repository)


GamificationServiceDep = Annotated[
    GamificationService,
    Depends(get_gamification_service),
]

__all__ = [
    "GamificationService",
    "GamificationServiceDep",
    "SKILL_LEVEL_TIERS",
    "compute_skill_level_from_xp",
    "get_gamification_service",
]
