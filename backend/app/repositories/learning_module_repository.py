"""Repositório SQLAlchemy 2.0 para persistência e consultas de Módulos de Aprendizagem Prática (BE-014)."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import (
    Uuid,
    column,
    func,
    inspect,
    literal,
    or_,
    select,
    table,
)
from sqlalchemy.orm import Session, joinedload

from app.core.database import DbSessionDep
from app.models.learning_module import LearningModule


class LearningModuleRepository:
    """Repositório SQLAlchemy 2.0 para operações de criação e listagem ordenada de módulos práticos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo prático pelo seu UUID com carregamento da disciplina vinculada."""
        stmt = (
            select(LearningModule)
            .options(joinedload(LearningModule.subject))
            .where(LearningModule.id == module_id)
        )
        return self._session.scalar(stmt)

    def get_by_subject_and_order_index(
        self,
        subject_id: UUID,
        order_index: int,
    ) -> LearningModule | None:
        """Busca um módulo prático pelo par único (subject_id, order_index)."""
        stmt = (
            select(LearningModule)
            .options(joinedload(LearningModule.subject))
            .where(
                LearningModule.subject_id == subject_id,
                LearningModule.order_index == order_index,
            )
        )
        return self._session.scalar(stmt)

    def get_next_order_index(self, subject_id: UUID) -> int:
        """Calcula o próximo índice de ordenação didática sequencial para a disciplina."""
        stmt = select(func.coalesce(func.max(LearningModule.order_index), 0) + 1).where(
            LearningModule.subject_id == subject_id
        )
        return int(self._session.scalar(stmt) or 1)

    def list_by_subject(
        self,
        *,
        subject_id: UUID,
        page: int,
        limit: int,
        search: str | None = None,
    ) -> tuple[list[LearningModule], int]:
        """Lista módulos práticos de uma disciplina ordenados por order_index ascendente."""
        stmt = select(LearningModule).where(LearningModule.subject_id == subject_id)

        if search:
            escaped = (
                search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            stmt = stmt.where(
                or_(
                    LearningModule.title.ilike(pattern, escape="\\"),
                    LearningModule.description.ilike(pattern, escape="\\"),
                )
            )

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(joinedload(LearningModule.subject))
            .order_by(LearningModule.order_index.asc(), LearningModule.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total

    def create(
        self,
        *,
        subject_id: UUID,
        title: str,
        order_index: int,
        practical_hours: int,
        description: str | None = None,
        module_weight: Decimal = Decimal("1.00"),
        passing_score: Decimal = Decimal("6.00"),
    ) -> LearningModule:
        """Persiste um novo módulo de aprendizagem prática vinculado a uma disciplina."""
        module = LearningModule(
            subject_id=subject_id,
            title=title,
            order_index=order_index,
            description=description,
            practical_hours=practical_hours,
            module_weight=module_weight,
            passing_score=passing_score,
        )
        self._session.add(module)
        self._session.commit()
        self._session.refresh(module)
        return self.get_by_id(module.id) or module

    def is_teacher_assigned_to_subject(
        self,
        *,
        teacher_id: UUID,
        subject_id: UUID,
    ) -> bool:
        """Verifica se o docente possui alocação registrada para a disciplina em teacher_assignments."""
        bind = self._session.get_bind()
        if not inspect(bind).has_table("teacher_assignments"):
            return False

        ta_tbl = table(
            "teacher_assignments",
            column("teacher_id", Uuid(as_uuid=True)),
            column("subject_id", Uuid(as_uuid=True)),
        )
        stmt = (
            select(literal(1))
            .select_from(ta_tbl)
            .where(
                ta_tbl.c.teacher_id == teacher_id,
                ta_tbl.c.subject_id == subject_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None


def get_learning_module_repository(session: DbSessionDep) -> LearningModuleRepository:
    """Provedor de injeção de dependência para LearningModuleRepository."""
    return LearningModuleRepository(session=session)


LearningModuleRepositoryDep = Annotated[
    LearningModuleRepository,
    Depends(get_learning_module_repository),
]

__all__ = [
    "LearningModuleRepository",
    "LearningModuleRepositoryDep",
    "get_learning_module_repository",
]
