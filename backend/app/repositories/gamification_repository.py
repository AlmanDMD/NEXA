"""Repositório SQLAlchemy 2.0 para Catálogo de Conquistas (gamification_badges - DB-045) e Conquistas de Estudantes (student_achievements - DB-046)."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.enrollment import Enrollment
from app.models.gamification import GamificationBadge, StudentAchievement
from app.models.practical_task import SkillEvidence
from app.models.self_assessment import ExplainableDiagnostic, StudentSelfAssessment
from app.schemas.enums import DiagnosticType, EnrollmentStatus

DEFAULT_SENAI_BADGES_CATALOG: tuple[dict[str, object], ...] = (
    {
        "code": "BADGE-METROLOGIA-100",
        "title": "Mestre do Micrômetro",
        "description": "Excelência em medição centesimal com micrômetro externo e interno sem desvios de tolerância.",
        "criteria_explanation": "Atingir nível verificado >= 4.50 nas atividades práticas de Metrologia Dimensional avaliadas pelo docente na oficina.",
        "icon_name": "micrometer-star",
        "xp_reward": 150,
    },
    {
        "code": "BADGE-PAQUIMETRO-PRO",
        "title": "Olho de Precisão H7",
        "description": "Domínio consistente na inspeção dimensional de eixos e buchas com paquímetro universal.",
        "criteria_explanation": "Concluir ao menos 1 entrega prática de controle dimensional com nota >= 9.00 ou nível de rubrica >= 4.",
        "icon_name": "caliper-check",
        "xp_reward": 120,
    },
    {
        "code": "BADGE-TORNEARIA-EXACT",
        "title": "Especialista em Tornearia Cilíndrica",
        "description": "Execução precisa de faceamento, cilindramento e escalonamento em torno mecânico convencional.",
        "criteria_explanation": "Obter avaliação docente nível 5 (Excelente) nos critérios de acabamento superficial e tolerância dimensional em Tornearia.",
        "icon_name": "lathe-award",
        "xp_reward": 200,
    },
    {
        "code": "BADGE-SEGURANCA-NR12",
        "title": "Guardião NR-12 & 5S",
        "description": "Compromisso exemplar com normas de segurança operacional em máquinas rotativas, uso de EPIs e organização de bancada.",
        "criteria_explanation": "Manter nível verificado >= 4.00 em competências da categoria SAFETY (Segurança NR-12 e EPIs) sem ocorrências críticas.",
        "icon_name": "shield-check",
        "xp_reward": 180,
    },
    {
        "code": "BADGE-ASSIDUIDADE-100",
        "title": "Presença de Aço 100%",
        "description": "Assiduidade integral em aulas teóricas e oficinas práticas durante todo o módulo.",
        "criteria_explanation": "Registrar 100% de presença efetiva (zero faltas não justificadas) em todas as aulas ministradas do ciclo.",
        "icon_name": "calendar-medal",
        "xp_reward": 100,
    },
    {
        "code": "BADGE-AUTOCONHECIMENTO-360",
        "title": "Calibração Metacognitiva",
        "description": "Alinhamento consistente entre autoavaliação discente e evidências práticas verificadas.",
        "criteria_explanation": "Responder aos formulários de autoavaliação dentro do prazo com diagnóstico ALIGNED frente à avaliação docente.",
        "icon_name": "compass-aligned",
        "xp_reward": 130,
    },
)


class GamificationRepository:
    """Repositório responsável pelas consultas de gamification_badges, student_achievements e métricas individuais de progresso."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def ensure_default_catalog_if_empty(self) -> None:
        """Popula o catálogo padrão de 6 insígnias técnicas SENAI (DB-045) caso a tabela esteja vazia."""
        count = int(
            self._session.scalar(select(func.count(GamificationBadge.id))) or 0
        )
        if count > 0:
            return

        for item in DEFAULT_SENAI_BADGES_CATALOG:
            self._session.add(
                GamificationBadge(
                    code=str(item["code"]),
                    title=str(item["title"]),
                    description=str(item["description"]),
                    criteria_explanation=str(item["criteria_explanation"]),
                    icon_name=str(item["icon_name"]),
                    xp_reward=int(item["xp_reward"]),  # type: ignore[arg-type]
                    competency_id=None,
                    is_active=True,
                )
            )
        self._session.commit()

    def list_active_badges(
        self,
        *,
        competency_id: UUID | None = None,
    ) -> list[GamificationBadge]:
        """Retorna todas as conquistas ativas do catálogo ordenadas por xp_reward ASC e code ASC."""
        stmt = (
            select(GamificationBadge)
            .options(joinedload(GamificationBadge.competency))
            .where(GamificationBadge.is_active.is_(True))
        )
        if competency_id is not None:
            stmt = stmt.where(GamificationBadge.competency_id == competency_id)

        stmt = stmt.order_by(
            GamificationBadge.xp_reward.asc(),
            GamificationBadge.code.asc(),
        )
        return list(self._session.scalars(stmt).unique().all())

    def list_student_achievements(
        self,
        student_id: UUID,
    ) -> list[StudentAchievement]:
        """Retorna todas as conquistas desbloqueadas pelo estudante ordenadas por unlocked_at DESC (DB-046)."""
        stmt = (
            select(StudentAchievement)
            .options(
                joinedload(StudentAchievement.badge).joinedload(
                    GamificationBadge.competency
                )
            )
            .where(StudentAchievement.student_id == student_id)
            .order_by(
                StudentAchievement.unlocked_at.desc(),
                StudentAchievement.id.asc(),
            )
        )
        return list(self._session.scalars(stmt).unique().all())

    def get_student_competency_verified_averages(
        self,
        student_id: UUID,
    ) -> dict[UUID, Decimal]:
        """Calcula a média de verified_level por competency_id a partir de skill_evidences do estudante."""
        stmt = (
            select(
                SkillEvidence.competency_id,
                func.avg(SkillEvidence.verified_level),
            )
            .where(SkillEvidence.student_id == student_id)
            .group_by(SkillEvidence.competency_id)
        )
        result: dict[UUID, Decimal] = {}
        for comp_id, avg_val in self._session.execute(stmt).all():
            if comp_id is not None and avg_val is not None:
                result[comp_id] = Decimal(str(avg_val)).quantize(Decimal("0.01"))
        return result

    def get_student_overall_verified_average_and_count(
        self,
        student_id: UUID,
    ) -> tuple[Decimal, int]:
        """Retorna a média geral e quantidade de evidências práticas (skill_evidences) do estudante."""
        stmt = select(
            func.avg(SkillEvidence.verified_level),
            func.count(SkillEvidence.id),
        ).where(SkillEvidence.student_id == student_id)
        row = self._session.execute(stmt).one()
        avg_val = (
            Decimal(str(row[0])).quantize(Decimal("0.01"))
            if row[0] is not None
            else Decimal("0.00")
        )
        total_count = int(row[1] or 0)
        return avg_val, total_count

    def get_student_best_attendance_rate(self, student_id: UUID) -> Decimal:
        """Retorna a maior taxa de presença (attendance_rate) dentre as matrículas ativas/concluídas do estudante."""
        stmt = select(func.max(Enrollment.attendance_rate)).where(
            Enrollment.student_id == student_id,
            Enrollment.status.in_(
                [EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED]
            ),
        )
        val = self._session.scalar(stmt)
        if val is None:
            return Decimal("0.00")
        return Decimal(str(val)).quantize(Decimal("0.01"))

    def get_student_self_assessment_progress_stats(
        self,
        student_id: UUID,
    ) -> tuple[int, int]:
        """Retorna (quantidade de respostas de autoavaliação, quantidade de diagnósticos ALIGNED) do estudante."""
        answers_count = int(
            self._session.scalar(
                select(func.count(StudentSelfAssessment.id)).where(
                    StudentSelfAssessment.student_id == student_id
                )
            )
            or 0
        )
        aligned_count = int(
            self._session.scalar(
                select(func.count(ExplainableDiagnostic.id)).where(
                    ExplainableDiagnostic.student_id == student_id,
                    ExplainableDiagnostic.diagnostic_type == DiagnosticType.ALIGNED,
                )
            )
            or 0
        )
        return answers_count, aligned_count


def get_gamification_repository(
    session: DbSessionDep,
) -> GamificationRepository:
    """Provedor de injeção de dependência para GamificationRepository."""
    return GamificationRepository(session=session)


GamificationRepositoryDep = Annotated[
    GamificationRepository,
    Depends(get_gamification_repository),
]

__all__ = [
    "DEFAULT_SENAI_BADGES_CATALOG",
    "GamificationRepository",
    "GamificationRepositoryDep",
    "get_gamification_repository",
]
