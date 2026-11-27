"""Serviço de domínio para Registro e Consulta de Observações Pedagógicas com Acesso Restrito, Criptografia e Auditoria (BE-045)."""

from datetime import datetime, timezone
import math
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.encryption import (
    PedagogicalNoteCipher,
    get_pedagogical_note_cipher,
)
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.pedagogical_note import PedagogicalNote
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.pedagogical_note_repository import (
    PedagogicalNoteRepository,
    PedagogicalNoteRepositoryDep,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import NoteVisibilityScope, UserRole
from app.schemas.pedagogical_note import (
    PedagogicalNoteAuthorSummarySchema,
    PedagogicalNoteCreateSchema,
    PedagogicalNoteListQueryParams,
    PedagogicalNotePaginatedResponseSchema,
    PedagogicalNoteResponseSchema,
    PedagogicalNoteStudentSummarySchema,
)
from app.services.audit_service import AuditService, AuditServiceDep

PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso terminantemente proibido: estudantes não possuem permissão para registrar ou consultar observações pedagógicas restritas."
)
PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE: Final[str] = (
    "Estudante não encontrado."
)
PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE: Final[str] = (
    "A observação pedagógica deve referenciar um usuário com perfil de estudante (STUDENT)."
)
PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE: Final[str] = (
    "Matrícula acadêmica não encontrada para o estudante informado."
)
PEDAGOGICAL_NOTE_ENROLLMENT_STUDENT_MISMATCH_MESSAGE: Final[str] = (
    "A matrícula informada não pertence ao estudante selecionado."
)
PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa na turma deste estudante."
)
PEDAGOGICAL_NOTE_TEACHER_COORD_SCOPE_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas coordenadores ou administradores podem criar observações com escopo COORDINATION_ONLY."
)
PEDAGOGICAL_NOTE_FOLLOWUP_INCONSISTENT_MESSAGE: Final[str] = (
    "Quando 'followup_date' é informada, 'requires_followup' deve ser True."
)


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um datetime esteja normalizado em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class PedagogicalNoteService:
    """Serviço responsável pelo controle de acesso, criptografia Fernet/AES-256 e auditoria de pedagogical_notes (BE-045)."""

    def __init__(
        self,
        repository: PedagogicalNoteRepository,
        audit_service: AuditService | None = None,
        cipher: PedagogicalNoteCipher | None = None,
    ) -> None:
        self._repository = repository
        self._audit_service = (
            audit_service
            if audit_service is not None
            else AuditService(repository=AuditRepository(session=repository.session))
        )
        self._cipher = cipher if cipher is not None else get_pedagogical_note_cipher()

    def _to_response(
        self,
        note: PedagogicalNote,
    ) -> PedagogicalNoteResponseSchema:
        """Descriptografa note_content em memória e serializa PedagogicalNote no contrato de saída."""
        student = note.student
        student_profile = student.profile
        author = note.author
        author_profile = author.profile
        enrollment = note.enrollment
        decrypted_content = self._cipher.decrypt(note.note_content)

        return PedagogicalNoteResponseSchema(
            id=note.id,
            student_id=note.student_id,
            enrollment_id=note.enrollment_id,
            class_id=enrollment.class_id,
            author_id=note.author_id,
            visibility_scope=note.visibility_scope,
            category=note.category,
            note_content=decrypted_content,
            is_encrypted_at_rest=self._cipher.is_encrypted(note.note_content),
            requires_followup=note.requires_followup,
            followup_date=note.followup_date,
            created_at=_ensure_utc(note.created_at),
            updated_at=_ensure_utc(note.updated_at),
            student=PedagogicalNoteStudentSummarySchema(
                id=student.id,
                email=student.email,
                full_name=(
                    student_profile.full_name if student_profile is not None else None
                ),
                registration_number=(
                    student_profile.registration_number
                    if student_profile is not None
                    else None
                ),
            ),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                enrollment.academic_class
            ),
            author=PedagogicalNoteAuthorSummarySchema(
                id=author.id,
                email=author.email,
                role=author.role,
                full_name=(
                    author_profile.full_name if author_profile is not None else None
                ),
            ),
        )

    def _block_and_audit_if_student(
        self,
        *,
        current_user: User,
        attempted_operation: str,
        target_student_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Bloqueia terminantemente acesso por perfil STUDENT com HTTP 403 Forbidden e grava alerta em audit_logs (Critério 1 BE-045)."""
        if current_user.role == UserRole.STUDENT:
            entity_ref = (
                str(target_student_id)
                if target_student_id is not None
                else str(current_user.id)
            )
            self._audit_service.log_action(
                user_id=current_user.id,
                action="PEDAGOGICAL_NOTE_FORBIDDEN_STUDENT_ACCESS",
                entity="pedagogical_notes",
                entity_id=entity_ref,
                new_values={
                    "security_alert": "UNAUTHORIZED_STUDENT_ACCESS_ATTEMPT",
                    "attempted_operation": attempted_operation,
                    "actor_id": str(current_user.id),
                    "actor_role": current_user.role.value,
                    "target_student_id": (
                        str(target_student_id)
                        if target_student_id is not None
                        else None
                    ),
                },
                ip_address=ip_address,
                commit=True,
            )
            logger.bind(
                actor_id=str(current_user.id),
                actor_role=current_user.role.value,
                attempted_operation=attempted_operation,
                target_student_id=(
                    str(target_student_id) if target_student_id is not None else None
                ),
                ip_address=ip_address,
            ).warning(
                "Tentativa bloqueada de acesso a observações pedagógicas restritas por perfil STUDENT (BE-045)."
            )
            raise ForbiddenException(
                message=PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE
            )

    def create_pedagogical_note(
        self,
        payload: PedagogicalNoteCreateSchema,
        *,
        current_user: User,
        ip_address: str | None = None,
    ) -> PedagogicalNoteResponseSchema:
        """Registra observação pedagógica criptografada (Fernet/AES-256) e grava rastro em audit_logs (BE-045)."""
        self._block_and_audit_if_student(
            current_user=current_user,
            attempted_operation="CREATE_PEDAGOGICAL_NOTE",
            target_student_id=payload.student_id,
            ip_address=ip_address,
        )

        if payload.followup_date is not None and not payload.requires_followup:
            raise UnprocessableEntityException(
                message=PEDAGOGICAL_NOTE_FOLLOWUP_INCONSISTENT_MESSAGE
            )

        if (
            current_user.role == UserRole.TEACHER
            and payload.visibility_scope == NoteVisibilityScope.COORDINATION_ONLY
        ):
            raise ForbiddenException(
                message=PEDAGOGICAL_NOTE_TEACHER_COORD_SCOPE_FORBIDDEN_MESSAGE
            )

        student = self._repository.get_user_by_id(payload.student_id)
        if student is None:
            raise NotFoundException(
                message=PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE
            )
        if student.role != UserRole.STUDENT:
            raise UnprocessableEntityException(
                message=PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE
            )

        teacher_class_ids: set[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            teacher_class_ids = self._repository.list_teacher_assigned_class_ids(
                current_user.id
            )

        if payload.enrollment_id is not None:
            enrollment = self._repository.get_enrollment_by_id(payload.enrollment_id)
            if enrollment is None:
                raise NotFoundException(
                    message=PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE
                )
            if enrollment.student_id != student.id:
                raise UnprocessableEntityException(
                    message=PEDAGOGICAL_NOTE_ENROLLMENT_STUDENT_MISMATCH_MESSAGE
                )
            if (
                current_user.role == UserRole.TEACHER
                and enrollment.class_id not in (teacher_class_ids or set())
            ):
                raise ForbiddenException(
                    message=PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )
        else:
            if current_user.role == UserRole.TEACHER:
                student_classes = self._repository.list_student_class_ids(student.id)
                if not student_classes:
                    raise NotFoundException(
                        message=PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE
                    )
                if not (student_classes & (teacher_class_ids or set())):
                    raise ForbiddenException(
                        message=PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE
                    )

            enrollment = self._repository.resolve_student_enrollment(
                student_id=student.id,
                class_id=payload.class_id,
                teacher_class_ids=teacher_class_ids,
            )
            if enrollment is None:
                raise NotFoundException(
                    message=PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE
                )

        encrypted_content = self._cipher.encrypt(payload.note_content)

        created_entity = self._repository.create_in_transaction(
            student_id=student.id,
            enrollment_id=enrollment.id,
            author_id=current_user.id,
            visibility_scope=payload.visibility_scope,
            category=payload.category,
            encrypted_note_content=encrypted_content,
            requires_followup=payload.requires_followup,
            followup_date=payload.followup_date,
        )

        # Auditoria obrigatória em audit_logs (sem jamais expor note_content em texto claro no log)
        self._audit_service.log_action(
            user_id=current_user.id,
            action="PEDAGOGICAL_NOTE_CREATE",
            entity="pedagogical_notes",
            entity_id=str(created_entity.id),
            new_values={
                "student_id": str(student.id),
                "enrollment_id": str(enrollment.id),
                "class_id": str(enrollment.class_id),
                "author_id": str(current_user.id),
                "author_role": current_user.role.value,
                "visibility_scope": payload.visibility_scope.value,
                "category": payload.category.value,
                "requires_followup": payload.requires_followup,
                "followup_date": (
                    payload.followup_date.isoformat()
                    if payload.followup_date is not None
                    else None
                ),
                "encrypted_at_rest": True,
            },
            ip_address=ip_address,
            commit=False,
        )

        persisted = (
            self._repository.commit_and_get(created_entity.id) or created_entity
        )

        logger.bind(
            pedagogical_note_id=str(persisted.id),
            student_id=str(persisted.student_id),
            enrollment_id=str(persisted.enrollment_id),
            author_id=str(current_user.id),
            author_role=current_user.role.value,
            visibility_scope=persisted.visibility_scope.value,
            category=persisted.category.value,
            requires_followup=persisted.requires_followup,
        ).info(
            "Observação pedagógica restrita criptografada registrada com auditoria (BE-045)."
        )

        return self._to_response(persisted)

    def list_student_pedagogical_notes(
        self,
        student_id: UUID,
        params: PedagogicalNoteListQueryParams,
        *,
        current_user: User,
        ip_address: str | None = None,
    ) -> PedagogicalNotePaginatedResponseSchema:
        """Lista e descriptografa observações pedagógicas do estudante respeitando visibility_scope e auditando a leitura (BE-045)."""
        self._block_and_audit_if_student(
            current_user=current_user,
            attempted_operation="READ_STUDENT_PEDAGOGICAL_NOTES",
            target_student_id=student_id,
            ip_address=ip_address,
        )

        student = self._repository.get_user_by_id(student_id)
        if student is None:
            raise NotFoundException(
                message=PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE
            )
        if student.role != UserRole.STUDENT:
            raise UnprocessableEntityException(
                message=PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE
            )

        if current_user.role == UserRole.TEACHER:
            teacher_class_ids = self._repository.list_teacher_assigned_class_ids(
                current_user.id
            )
            student_class_ids = self._repository.list_student_class_ids(student.id)
            if not (teacher_class_ids & student_class_ids):
                raise ForbiddenException(
                    message=PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )
            if (
                params.class_id is not None
                and params.class_id not in teacher_class_ids
            ):
                raise ForbiddenException(
                    message=PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )

        items, total = self._repository.list_student_notes_for_viewer(
            student_id=student.id,
            viewer_id=current_user.id,
            viewer_role=current_user.role,
            page=params.page,
            limit=params.limit,
            class_id=params.class_id,
            enrollment_id=params.enrollment_id,
            visibility_scope=params.visibility_scope,
            category=params.category,
            requires_followup=params.requires_followup,
        )

        # Rastro obrigatório de leitura em audit_logs (DB-043 / BE-045)
        self._audit_service.log_action(
            user_id=current_user.id,
            action="PEDAGOGICAL_NOTE_READ",
            entity="pedagogical_notes",
            entity_id=str(student.id),
            new_values={
                "student_id": str(student.id),
                "reader_id": str(current_user.id),
                "reader_role": current_user.role.value,
                "returned_count": len(items),
                "total_visible": total,
            },
            ip_address=ip_address,
            commit=True,
        )

        total_pages = math.ceil(total / params.limit) if total > 0 else 0
        return PedagogicalNotePaginatedResponseSchema(
            data=[self._to_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
        )


def get_pedagogical_note_service(
    repository: PedagogicalNoteRepositoryDep,
    audit_service: AuditServiceDep,
) -> PedagogicalNoteService:
    """Provedor de injeção de dependência para PedagogicalNoteService."""
    return PedagogicalNoteService(
        repository=repository,
        audit_service=audit_service,
    )


PedagogicalNoteServiceDep = Annotated[
    PedagogicalNoteService,
    Depends(get_pedagogical_note_service),
]

__all__ = [
    "PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE",
    "PEDAGOGICAL_NOTE_ENROLLMENT_STUDENT_MISMATCH_MESSAGE",
    "PEDAGOGICAL_NOTE_FOLLOWUP_INCONSISTENT_MESSAGE",
    "PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE",
    "PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE",
    "PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE",
    "PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE",
    "PEDAGOGICAL_NOTE_TEACHER_COORD_SCOPE_FORBIDDEN_MESSAGE",
    "PedagogicalNoteService",
    "PedagogicalNoteServiceDep",
    "get_pedagogical_note_service",
]
