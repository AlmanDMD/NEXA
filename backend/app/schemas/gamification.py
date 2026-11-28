"""Schemas Pydantic v2 para Catálogo de Conquistas, Níveis de Habilidade e Badges Desbloqueadas pelo Estudante (BE-046)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Final
from uuid import UUID

from fastapi import Query
from pydantic import Field

from app.schemas.base import BaseResponseSchema, StrictRequestSchema
from app.schemas.enums import CompetencyCategory, SkillLevel

GAMIFICATION_SCORING_RULE_EXPLANATION: Final[str] = (
    "Cada insígnia técnica (badge) concede XP positivo de experiência prática ao ser "
    "desbloqueada por evidências verificadas em oficina, assiduidade ou alinhamento "
    "diagnóstico. O XP total acumulado determina o nível de habilidade do estudante: "
    "Nível 1 — Iniciante (0 a 149 XP), Nível 2 — Praticante (150 a 299 XP), "
    "Nível 3 — Proficiente (300 a 499 XP) e Nível 4 — Especialista (500+ XP). "
    "A gamificação do Sistema NEXA é estritamente individual, formativa e transparente, "
    "sem rankings comparativos ou exposição de estudantes."
)

GAMIFICATION_ETHICAL_PRIVACY_NOTE: Final[str] = (
    "Seus pontos de experiência (XP) e conquistas refletem exclusivamente a sua "
    "evolução pessoal nas oficinas práticas SENAI. Nenhum ranking comparativo entre "
    "colegas é calculado ou exibido."
)


class GamificationSkillLevelTierSchema(BaseResponseSchema):
    """Faixa transparente da tabela de níveis de habilidade baseados em XP acumulado."""

    level_number: int = Field(
        ge=1,
        le=4,
        description="Número sequencial do nível de habilidade (1 a 4)",
    )
    level_key: SkillLevel = Field(
        description="Identificador técnico do nível (BEGINNER, PRACTITIONER, PROFICIENT, SPECIALIST)",
    )
    level_title: str = Field(
        description="Título pedagógico do nível (Iniciante, Praticante, Proficiente, Especialista)",
    )
    min_xp: int = Field(
        ge=0,
        description="Pontuação mínima de XP para ingressar neste nível",
    )
    max_xp: int | None = Field(
        default=None,
        description="Pontuação máxima de XP deste nível (None no nível máximo Especialista)",
    )
    description: str = Field(
        description="Explicação pedagógica do que representa este nível de habilidade técnica",
    )


class GamificationCompetencySummarySchema(BaseResponseSchema):
    """Resumo da competência técnica SENAI associada opcionalmente a uma conquista."""

    id: UUID = Field(description="Identificador UUID da competência")
    code: str = Field(description="Código único da competência técnica")
    title: str = Field(description="Título da competência técnica")
    category: CompetencyCategory = Field(
        description="Categoria da competência (TECHNICAL, SAFETY, PROCEDURAL)",
    )


class StudentBadgeProgressItemSchema(BaseResponseSchema):
    """Item do catálogo de conquistas cruzado com o progresso individual do estudante (BE-046)."""

    badge_id: UUID = Field(
        description="Identificador UUID da conquista em gamification_badges",
    )
    code: str = Field(
        description="Código único da conquista (ex.: BADGE-METROLOGIA-100)",
    )
    title: str = Field(description="Título da conquista (ex.: Mestre do Micrômetro)")
    description: str = Field(description="Descrição pedagógica da conquista")
    criteria_explanation: str = Field(
        description="Explicação clara e transparente da regra para desbloquear a conquista",
    )
    icon_name: str = Field(description="Identificador do ícone visual da conquista")
    xp_reward: int = Field(
        gt=0,
        description="Recompensa de XP concedida ao desbloquear a conquista",
    )
    competency_id: UUID | None = Field(
        default=None,
        description="Identificador UUID opcional da competência técnica vinculada",
    )
    competency: GamificationCompetencySummarySchema | None = Field(
        default=None,
        description="Dados resumidos da competência técnica vinculada, quando aplicável",
    )
    unlocked: bool = Field(
        description="Alias booleano direto para consumo no front-end indicando se a conquista foi desbloqueada",
    )
    is_unlocked: bool = Field(
        description="Indica se o estudante autenticado já desbloqueou esta conquista",
    )
    progress_percentage: Decimal = Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Percentual de progresso individual (0.00 a 100.00) rumo à conquista",
    )
    status_label: str = Field(
        description="Rótulo amigável do estado atual da conquista para o estudante",
    )
    unlocked_at: datetime | None = Field(
        default=None,
        description="Data/hora UTC em que o estudante desbloqueou a conquista",
    )
    origin_reference: str | None = Field(
        default=None,
        description="Módulo, tarefa prática ou marco acadêmico que concedeu a conquista",
    )


class StudentGamificationOverviewResponseSchema(BaseResponseSchema):
    """Contrato completo de saída de GET /api/v1/gamification/badges (BE-046)."""

    student_id: UUID = Field(
        description="Identificador UUID do estudante titular das conquistas",
    )
    total_xp: int = Field(
        ge=0,
        description="XP total acumulado pelo estudante com as conquistas desbloqueadas",
    )
    current_level_number: int = Field(
        ge=1,
        le=4,
        description="Número do nível atual de habilidade do estudante (1 a 4)",
    )
    current_level: SkillLevel = Field(
        description="Chave do nível atual de habilidade (BEGINNER, PRACTITIONER, PROFICIENT, SPECIALIST)",
    )
    current_level_title: str = Field(
        description="Título do nível atual (ex.: 'Nível 2 — Praticante')",
    )
    next_level: SkillLevel | None = Field(
        default=None,
        description="Chave do próximo nível de habilidade (None quando já em SPECIALIST)",
    )
    next_level_title: str | None = Field(
        default=None,
        description="Título do próximo nível de habilidade",
    )
    next_level_xp_threshold: int | None = Field(
        default=None,
        description="Meta de XP total necessária para atingir o próximo nível",
    )
    xp_to_next_level: int = Field(
        ge=0,
        description="Quantidade de XP restante para subir ao próximo nível de habilidade",
    )
    level_progress_percentage: Decimal = Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Percentual de progresso dentro da faixa do nível atual rumo ao próximo nível",
    )
    unlocked_count: int = Field(
        ge=0,
        description="Total de insígnias desbloqueadas pelo estudante",
    )
    locked_count: int = Field(
        ge=0,
        description="Total de próximas insígnias disponíveis para conquistar",
    )
    total_badges: int = Field(
        ge=0,
        description="Total de insígnias ativas no catálogo pedagógico",
    )
    completion_percentage: Decimal = Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        description="Percentual global de conclusão do catálogo de insígnias",
    )
    scoring_rule_explanation: str = Field(
        default=GAMIFICATION_SCORING_RULE_EXPLANATION,
        description="Explicação clara e transparente da regra de pontuação e níveis de habilidade",
    )
    ethical_privacy_note: str = Field(
        default=GAMIFICATION_ETHICAL_PRIVACY_NOTE,
        description="Garantia explícita de gamificação individual sem ranking punitivo ou exposição",
    )
    level_tiers: list[GamificationSkillLevelTierSchema] = Field(
        default_factory=list,
        description="Tabela transparente com os 4 níveis de habilidade e seus intervalos de XP",
    )
    badges: list[StudentBadgeProgressItemSchema] = Field(
        default_factory=list,
        description="Catálogo completo de insígnias cruzado com o progresso do estudante",
    )
    unlocked_badges: list[StudentBadgeProgressItemSchema] = Field(
        default_factory=list,
        description="Lista filtrada apenas com as insígnias já conquistadas pelo estudante",
    )
    upcoming_badges: list[StudentBadgeProgressItemSchema] = Field(
        default_factory=list,
        description="Lista ordenada das próximas conquistas mais próximas de desbloqueio",
    )


class GamificationBadgesQueryParams(StrictRequestSchema):
    """Parâmetros opcionais de consulta para GET /api/v1/gamification/badges (BE-046)."""

    competency_id: UUID | None = Field(
        default=None,
        description="Filtro opcional pelo UUID de uma competência técnica específica",
    )
    unlocked_only: bool = Field(
        default=False,
        description="Quando True, retorna na lista principal apenas as insígnias já desbloqueadas",
    )


type GamificationBadgesParamsDep = Annotated[
    GamificationBadgesQueryParams,
    Query(),
]

__all__ = [
    "GAMIFICATION_ETHICAL_PRIVACY_NOTE",
    "GAMIFICATION_SCORING_RULE_EXPLANATION",
    "GamificationBadgesParamsDep",
    "GamificationBadgesQueryParams",
    "GamificationCompetencySummarySchema",
    "GamificationSkillLevelTierSchema",
    "StudentBadgeProgressItemSchema",
    "StudentGamificationOverviewResponseSchema",
]
