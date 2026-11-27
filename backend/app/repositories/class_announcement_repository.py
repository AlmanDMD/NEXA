"""Repositório SQLAlchemy 2.0 para Publicação, Edição e Remoção de Avisos no Mural da Turma (BE-041)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.class_announcement import ClassAnnouncement
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import AnnouncementPriority


class ClassAnnouncementRepository:
    """Repositório responsável pela persistência e consultas auxiliares de comunicados em class_announcements."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, announcement_id: UUID) -> ClassAnnouncement | None:
        """Busca um comunicado oficial pelo UUID carregando turma, disciplina e autor com perfil."""
        stmt = (
            select(ClassAnnouncement)
            .options(
                joinedload(ClassAnnouncement.academic_class),
                joinedload(ClassAnnouncement.subject),
                joinedload(ClassAnnouncement.author).selectinload(User.profile),
            )
            .where(ClassAnnouncement.id == announcement_id)
        )
        return self._session.scalar(stmt)

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        return self._session.scalar(
            select(AcademicClass).where(AcademicClass.id == class_id)
        )

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        return self._session.scalar(select(Subject).where(Subject.id == subject_id))

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> bool:
        """Verifica se o docente possui atribuição ativa na turma informada."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def is_teacher_assigned_to_class_and_subject(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
    ) -> bool:
        """Verifica se o docente possui atribuição ativa na turma e disciplina informadas."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.subject_id == subject_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def create(
        self,
        *,
        class_id: UUID,
        subject_id: UUID | None,
        author_id: UUID,
        title: str,
        content: str,
        priority: AnnouncementPriority,
        is_pinned: bool,
        published_at: datetime,
        expires_at: datetime | None,
    ) -> ClassAnnouncement:
        """Cria e persiste um novo comunicado oficial em class_announcements."""
        entity = ClassAnnouncement(
            class_id=class_id,
            subject_id=subject_id,
            author_id=author_id,
            title=title,
            content=content,
            priority=priority,
            is_pinned=is_pinned,
            published_at=published_at,
            expires_at=expires_at,
        )
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return self.get_by_id(entity.id) or entity

    def update(
        self,
        announcement: ClassAnnouncement,
        *,
        subject_id: UUID | None = None,
        update_subject: bool = False,
        title: str | None = None,
        content: str | None = None,
        priority: AnnouncementPriority | None = None,
        is_pinned: bool | None = None,
        expires_at: datetime | None = None,
        update_expires_at: bool = False,
    ) -> ClassAnnouncement:
        """Atualiza campos de um comunicado existente em class_announcements."""
        if update_subject:
            announcement.subject_id = subject_id
        if title is not None:
            announcement.title = title
        if content is not None:
            announcement.content = content
        if priority is not None:
            announcement.priority = priority
        if is_pinned is not None:
            announcement.is_pinned = is_pinned
        if update_expires_at:
            announcement.expires_at = expires_at

        self._session.add(announcement)
        self._session.commit()
        self._session.refresh(announcement)
        return self.get_by_id(announcement.id) or announcement

    def delete(self, announcement: ClassAnnouncement) -> None:
        """Remove definitivamente um comunicado do mural da turma."""
        self._session.delete(announcement)
        self._session.commit()


def get_class_announcement_repository(
    session: DbSessionDep,
) -> ClassAnnouncementRepository:
    """Provedor de injeção de dependência para ClassAnnouncementRepository."""
    return ClassAnnouncementRepository(session=session)


ClassAnnouncementRepositoryDep = Annotated[
    ClassAnnouncementRepository,
    Depends(get_class_announcement_repository),
]

__all__ = [
    "ClassAnnouncementRepository",
    "ClassAnnouncementRepositoryDep",
    "get_class_announcement_repository",
]
