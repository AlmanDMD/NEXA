"""Repositório SQLAlchemy 2.0 para persistência e consultas de Competências e Vínculos (BE-015)."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.competency import Competency
from app.models.module_competency import ModuleCompetency
from app.schemas.enums import CompetencyCategory


class CompetencyRepository:
    """Repositório SQLAlchemy 2.0 para operações de catálogo de competências e vínculo com módulos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, competency_id: UUID) -> Competency | None:
        """Busca uma competência técnica pelo seu identificador UUID."""
        stmt = select(Competency).where(Competency.id == competency_id)
        return self._session.scalar(stmt)

    def get_by_code(self, code: str) -> Competency | None:
        """Busca uma competência técnica pelo código institucional (comparação case-insensitive)."""
        normalized_code = code.strip().upper()
        stmt = select(Competency).where(func.upper(Competency.code) == normalized_code)
        return self._session.scalar(stmt)

    def list_competencies(
        self,
        *,
        page: int,
        limit: int,
        category: CompetencyCategory | None = None,
        search: str | None = None,
    ) -> tuple[list[Competency], int]:
        """Lista competências paginadas com suporte a filtro por categoria e busca textual."""
        stmt = select(Competency)

        if category is not None:
            stmt = stmt.where(Competency.category == category)

        if search:
            escaped = (
                search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            stmt = stmt.where(
                or_(
                    Competency.code.ilike(pattern, escape="\\"),
                    Competency.title.ilike(pattern, escape="\\"),
                    Competency.description.ilike(pattern, escape="\\"),
                )
            )

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.order_by(Competency.code.asc(), Competency.title.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).all())
        return items, total

    def create(
        self,
        *,
        code: str,
        title: str,
        category: CompetencyCategory,
        description: str | None = None,
    ) -> Competency:
        """Persiste uma nova competência técnica no catálogo."""
        competency = Competency(
            code=code,
            title=title,
            category=category,
            description=description,
        )
        self._session.add(competency)
        self._session.commit()
        self._session.refresh(competency)
        return competency

    def get_module_competency(
        self,
        *,
        module_id: UUID,
        competency_id: UUID,
    ) -> ModuleCompetency | None:
        """Busca um vínculo módulo-competência pela chave primária composta."""
        stmt = (
            select(ModuleCompetency)
            .options(joinedload(ModuleCompetency.competency))
            .where(
                ModuleCompetency.module_id == module_id,
                ModuleCompetency.competency_id == competency_id,
            )
        )
        return self._session.scalar(stmt)

    def link_to_module(
        self,
        *,
        module_id: UUID,
        competency_id: UUID,
        weight: Decimal = Decimal("1.00"),
        required_level: int = 3,
    ) -> ModuleCompetency:
        """Persiste uma associação N:M entre módulo prático e competência com peso e nível."""
        link = ModuleCompetency(
            module_id=module_id,
            competency_id=competency_id,
            weight=weight,
            required_level=required_level,
        )
        self._session.add(link)
        self._session.commit()
        self._session.refresh(link)
        return (
            self.get_module_competency(module_id=module_id, competency_id=competency_id)
            or link
        )

    def list_by_module(self, *, module_id: UUID) -> list[ModuleCompetency]:
        """Lista todas as competências associadas a um módulo prático ordenadas por código."""
        stmt = (
            select(ModuleCompetency)
            .join(ModuleCompetency.competency)
            .options(joinedload(ModuleCompetency.competency))
            .where(ModuleCompetency.module_id == module_id)
            .order_by(Competency.code.asc())
        )
        return list(self._session.scalars(stmt).unique().all())


def get_competency_repository(session: DbSessionDep) -> CompetencyRepository:
    """Provedor de injeção de dependência para CompetencyRepository."""
    return CompetencyRepository(session=session)


CompetencyRepositoryDep = Annotated[
    CompetencyRepository,
    Depends(get_competency_repository),
]

__all__ = [
    "CompetencyRepository",
    "CompetencyRepositoryDep",
    "get_competency_repository",
]
