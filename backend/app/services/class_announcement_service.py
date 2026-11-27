"""Serviço de domínio para Publicação, Edição, Fixação, Consulta e Exclusão de Avisos no Mural da Turma (BE-041 / BE-042)."""

from datetime import datetime, timezone
import math
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.base import _utc_now
from app.models.class_announcement import ClassAnnouncement
from app.models.user import User
from app.repositories.class_announcement_repository import (
    ClassAnnouncementRepository,
    ClassAnnouncementRepositoryDep,
)
from app.schemas.class_announcement import (
    AnnouncementAuthorSummarySchema,
    AnnouncementSubjectSummarySchema,
    ClassAnnouncementCreateSchema,
    ClassAnnouncementListQueryParams,
    ClassAnnouncementPaginatedResponseSchema,
    ClassAnnouncementResponseSchema,
    ClassAnnouncementUpdateSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import UserRole

ANNOUNCEMENT_NOT_FOUND_MESSAGE: Final[str] = "Aviso acadêmico não encontrado."
ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = (
    "Disciplina técnica não encontrada."
)
ANNOUNCEMENT_SUBJECT_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "A disciplina informada não pertence ao curso da turma selecionada."
)
ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
ANNOUNCEMENT_TEACHER_SUBJECT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona a disciplina informada nesta turma."
)
ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas o professor autor do aviso ou a coordenação pode editá-lo ou removê-lo."
)
ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE: Final[str] = (
    "A data/hora de expiração (expires_at) deve ser estritamente posterior à data de publicação."
)
ANNOUNCEMENT_STUDENT_CLASS_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: estudante não possui matrícula ativa nesta turma."
)


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um datetime esteja normalizado em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ClassAnnouncementService:
    """Serviço responsável pelas regras de negócio e autorização do Mural Oficial de Avisos (BE-041)."""

    def __init__(self, repository: ClassAnnouncementRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_response(
        announcement: ClassAnnouncement,
    ) -> ClassAnnouncementResponseSchema:
        """Serializa entidade ClassAnnouncement no contrato completo da API."""
        author = announcement.author
        author_profile = author.profile
        subject = announcement.subject

        return ClassAnnouncementResponseSchema(
            id=announcement.id,
            class_id=announcement.class_id,
            subject_id=announcement.subject_id,
            author_id=announcement.author_id,
            title=announcement.title,
            content=announcement.content,
            priority=announcement.priority,
            is_pinned=announcement.is_pinned,
            published_at=_ensure_utc(announcement.published_at),
            expires_at=(
                _ensure_utc(announcement.expires_at)
                if announcement.expires_at is not None
                else None
            ),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                announcement.academic_class
            ),
            subject=(
                AnnouncementSubjectSummarySchema(
                    id=subject.id,
                    code=subject.code,
                    name=subject.name,
                )
                if subject is not None
                else None
            ),
            author=AnnouncementAuthorSummarySchema(
                id=author.id,
                email=author.email,
                role=author.role,
                full_name=(
                    author_profile.full_name if author_profile is not None else None
                ),
            ),
        )

    def _validate_subject_for_class(
        self,
        *,
        subject_id: UUID,
        course_id: UUID,
        class_id: UUID,
        current_user: User,
    ) -> None:
        """Valida existência da disciplina, pertencimento ao curso da turma e atribuição docente."""
        subject = self._repository.get_subject_by_id(subject_id)
        if subject is None:
            raise NotFoundException(message=ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE)

        if subject.course_id != course_id:
            raise UnprocessableEntityException(
                message=ANNOUNCEMENT_SUBJECT_COURSE_MISMATCH_MESSAGE
            )

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=class_id,
                subject_id=subject.id,
            )
        ):
            raise ForbiddenException(
                message=ANNOUNCEMENT_TEACHER_SUBJECT_FORBIDDEN_MESSAGE
            )

    def _get_authorized_announcement(
        self,
        announcement_id: UUID,
        *,
        current_user: User,
    ) -> ClassAnnouncement:
        """Busca comunicado validando existência (404) e autorização contextual de edição/exclusão (403)."""
        announcement = self._repository.get_by_id(announcement_id)
        if announcement is None:
            raise NotFoundException(message=ANNOUNCEMENT_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER:
            if not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=announcement.class_id,
            ):
                raise ForbiddenException(
                    message=ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )
            if announcement.author_id != current_user.id:
                raise ForbiddenException(
                    message=ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE
                )

        return announcement

    def create_announcement(
        self,
        payload: ClassAnnouncementCreateSchema,
        *,
        current_user: User,
    ) -> ClassAnnouncementResponseSchema:
        """Publica um novo aviso oficial no mural da turma validando atribuição docente/coordenação (BE-041)."""
        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
        ):
            raise ForbiddenException(
                message=ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE
            )

        if payload.subject_id is not None:
            self._validate_subject_for_class(
                subject_id=payload.subject_id,
                course_id=academic_class.course_id,
                class_id=academic_class.id,
                current_user=current_user,
            )

        published_at = _utc_now()
        if payload.expires_at is not None and payload.expires_at <= published_at:
            raise UnprocessableEntityException(
                message=ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE
            )

        created = self._repository.create(
            class_id=academic_class.id,
            subject_id=payload.subject_id,
            author_id=current_user.id,
            title=payload.title,
            content=payload.content,
            priority=payload.priority,
            is_pinned=payload.is_pinned,
            published_at=published_at,
            expires_at=payload.expires_at,
        )

        logger.bind(
            announcement_id=str(created.id),
            class_id=str(created.class_id),
            subject_id=str(created.subject_id) if created.subject_id else None,
            author_id=str(current_user.id),
            author_role=current_user.role.value,
            priority=created.priority.value,
            is_pinned=created.is_pinned,
        ).info("Aviso oficial publicado no mural da turma (BE-041).")

        return self._to_response(created)

    def update_announcement(
        self,
        announcement_id: UUID,
        payload: ClassAnnouncementUpdateSchema,
        *,
        current_user: User,
    ) -> ClassAnnouncementResponseSchema:
        """Edita conteúdo, prioridade, disciplina, expiração ou fixação (is_pinned) de um aviso do mural."""
        announcement = self._get_authorized_announcement(
            announcement_id,
            current_user=current_user,
        )

        fields_set = payload.model_fields_set
        update_subject = "subject_id" in fields_set
        update_expires_at = "expires_at" in fields_set

        if update_subject and payload.subject_id is not None:
            self._validate_subject_for_class(
                subject_id=payload.subject_id,
                course_id=announcement.academic_class.course_id,
                class_id=announcement.class_id,
                current_user=current_user,
            )

        if update_expires_at and payload.expires_at is not None:
            published_utc = _ensure_utc(announcement.published_at)
            if payload.expires_at <= published_utc:
                raise UnprocessableEntityException(
                    message=ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE
                )

        updated = self._repository.update(
            announcement,
            subject_id=payload.subject_id,
            update_subject=update_subject,
            title=payload.title,
            content=payload.content,
            priority=payload.priority,
            is_pinned=payload.is_pinned,
            expires_at=payload.expires_at,
            update_expires_at=update_expires_at,
        )

        logger.bind(
            announcement_id=str(updated.id),
            class_id=str(updated.class_id),
            actor_id=str(current_user.id),
            actor_role=current_user.role.value,
            priority=updated.priority.value,
            is_pinned=updated.is_pinned,
            updated_fields=sorted(fields_set),
        ).info("Aviso oficial atualizado no mural da turma (BE-041).")

        return self._to_response(updated)

    def delete_announcement(
        self,
        announcement_id: UUID,
        *,
        current_user: User,
    ) -> None:
        """Remove um aviso oficial do mural da turma respeitando a alçada do autor/coordenação."""
        announcement = self._get_authorized_announcement(
            announcement_id,
            current_user=current_user,
        )
        deleted_id = str(announcement.id)
        class_id = str(announcement.class_id)

        self._repository.delete(announcement)

        logger.bind(
            announcement_id=deleted_id,
            class_id=class_id,
            actor_id=str(current_user.id),
            actor_role=current_user.role.value,
        ).info("Aviso oficial removido do mural da turma (BE-041).")

    def list_announcements(
        self,
        params: ClassAnnouncementListQueryParams,
        *,
        current_user: User,
    ) -> ClassAnnouncementPaginatedResponseSchema:
        """Consulta comunicados ativos do mural ordenados por is_pinned DESC e published_at DESC com isolamento por turma (BE-042)."""
        if params.class_id is not None:
            if self._repository.get_class_by_id(params.class_id) is None:
                raise NotFoundException(message=ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE)

        if params.subject_id is not None:
            if self._repository.get_subject_by_id(params.subject_id) is None:
                raise NotFoundException(message=ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE)

        allowed_class_ids: list[UUID] | None = None
        if current_user.role == UserRole.STUDENT:
            enrolled_class_ids = self._repository.list_student_enrolled_class_ids(
                current_user.id
            )
            if (
                params.class_id is not None
                and params.class_id not in enrolled_class_ids
            ):
                raise ForbiddenException(
                    message=ANNOUNCEMENT_STUDENT_CLASS_FORBIDDEN_MESSAGE
                )
            if not enrolled_class_ids:
                return ClassAnnouncementPaginatedResponseSchema(
                    data=[],
                    total=0,
                    page=params.page,
                    limit=params.limit,
                    total_pages=0,
                )
            allowed_class_ids = list(enrolled_class_ids)

        elif current_user.role == UserRole.TEACHER:
            assigned_class_ids = self._repository.list_teacher_assigned_class_ids(
                current_user.id
            )
            if (
                params.class_id is not None
                and params.class_id not in assigned_class_ids
            ):
                raise ForbiddenException(
                    message=ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )
            if not assigned_class_ids:
                return ClassAnnouncementPaginatedResponseSchema(
                    data=[],
                    total=0,
                    page=params.page,
                    limit=params.limit,
                    total_pages=0,
                )
            allowed_class_ids = list(assigned_class_ids)

        items, total = self._repository.list_active_announcements(
            now_utc=_utc_now(),
            page=params.page,
            limit=params.limit,
            class_id=params.class_id,
            allowed_class_ids=allowed_class_ids,
            subject_id=params.subject_id,
            priority=params.priority,
        )
        total_pages = math.ceil(total / params.limit) if total > 0 else 0

        return ClassAnnouncementPaginatedResponseSchema(
            data=[self._to_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
        )


def get_class_announcement_service(
    repository: ClassAnnouncementRepositoryDep,
) -> ClassAnnouncementService:
    """Provedor de injeção de dependência para ClassAnnouncementService."""
    return ClassAnnouncementService(repository=repository)


ClassAnnouncementServiceDep = Annotated[
    ClassAnnouncementService,
    Depends(get_class_announcement_service),
]

__all__ = [
    "ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE",
    "ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE",
    "ANNOUNCEMENT_NOT_FOUND_MESSAGE",
    "ANNOUNCEMENT_STUDENT_CLASS_FORBIDDEN_MESSAGE",
    "ANNOUNCEMENT_SUBJECT_COURSE_MISMATCH_MESSAGE",
    "ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE",
    "ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE",
    "ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE",
    "ANNOUNCEMENT_TEACHER_SUBJECT_FORBIDDEN_MESSAGE",
    "ClassAnnouncementService",
    "ClassAnnouncementServiceDep",
    "get_class_announcement_service",
]
