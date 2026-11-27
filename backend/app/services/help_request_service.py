"""Serviço de domínio para Abertura, Atendimento, Mensagens e Encerramento de Solicitações de Apoio Confidenciais (BE-043 / BE-044)."""

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
from app.models.help_request import ChatMessage, HelpRequest
from app.models.user import User
from app.repositories.help_request_repository import (
    HelpRequestRepository,
    HelpRequestRepositoryDep,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import HelpRequestStatus, UserRole
from app.schemas.help_request import (
    HelpRequestChatMessageResponseSchema,
    HelpRequestCreateSchema,
    HelpRequestListQueryParams,
    HelpRequestMessageCreateSchema,
    HelpRequestModuleSummarySchema,
    HelpRequestPaginatedResponseSchema,
    HelpRequestResponseSchema,
    HelpRequestStudentSummarySchema,
    HelpRequestSubjectSummarySchema,
    HelpRequestTeacherSummarySchema,
    HelpRequestUpdateSchema,
)

HELP_REQUEST_NOT_FOUND_MESSAGE: Final[str] = (
    "Solicitação de apoio pedagógico não encontrada."
)
HELP_REQUEST_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = (
    "Disciplina técnica não encontrada."
)
HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
HELP_REQUEST_MODULE_SUBJECT_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence à disciplina selecionada."
)
HELP_REQUEST_STUDENT_NO_ACTIVE_ENROLLMENT_MESSAGE: Final[str] = (
    "Acesso não autorizado: estudante não possui matrícula ativa em nenhuma turma."
)
HELP_REQUEST_STUDENT_NOT_ENROLLED_IN_SUBJECT_COURSE_MESSAGE: Final[str] = (
    "Acesso não autorizado: estudante não possui matrícula ativa em turma vinculada ao curso desta disciplina."
)
HELP_REQUEST_ONLY_STUDENTS_CAN_CREATE_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas estudantes podem abrir solicitações confidenciais de apoio pedagógico."
)
HELP_REQUEST_TEACHER_SUBJECT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona a disciplina informada."
)
HELP_REQUEST_TEACHER_CLASS_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
HELP_REQUEST_STUDENT_PARTICIPANT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas o estudante autor da solicitação pode consultar ou enviar mensagens neste chamado."
)
HELP_REQUEST_TEACHER_PARTICIPANT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas o professor responsável pela disciplina ou a coordenação pode atender ou enviar mensagens neste chamado."
)
HELP_REQUEST_STATUS_UPDATE_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: apenas o professor responsável ou a coordenação pode alterar o status ou encerrar a solicitação de apoio."
)
HELP_REQUEST_ALREADY_CLOSED_MESSAGE: Final[str] = (
    "Esta solicitação de apoio já foi encerrada (CLOSED) e não aceita novas mensagens ou alterações de status."
)
HELP_REQUEST_INVALID_STATUS_TRANSITION_MESSAGE: Final[str] = (
    "Transição de status inválida: uma solicitação já resolvida (RESOLVED) não pode retornar ao status aberto (OPEN)."
)
HELP_REQUEST_INVALID_ASSIGNED_TEACHER_MESSAGE: Final[str] = (
    "O responsável atribuído ao atendimento deve ser um usuário ativo com perfil TEACHER, COORDINATOR ou ADMIN."
)


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um datetime esteja normalizado em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class HelpRequestService:
    """Serviço responsável pelas regras de negócio, roteamento ao docente titular e sigilo de help_requests (BE-043)."""

    def __init__(self, repository: HelpRequestRepository) -> None:
        self._repository = repository

    @staticmethod
    def _serialize_message(
        message: ChatMessage,
    ) -> HelpRequestChatMessageResponseSchema:
        """Serializa entidade ChatMessage no contrato da API."""
        sender = message.sender
        sender_profile = sender.profile
        return HelpRequestChatMessageResponseSchema(
            id=message.id,
            help_request_id=message.help_request_id,
            sender_id=message.sender_id,
            sender_role=sender.role,
            sender_name=(
                sender_profile.full_name if sender_profile is not None else None
            ),
            message_body=message.message_body,
            is_read=message.is_read,
            read_at=(
                _ensure_utc(message.read_at) if message.read_at is not None else None
            ),
            sent_at=_ensure_utc(message.sent_at),
        )

    @classmethod
    def _to_response(
        cls,
        help_request: HelpRequest,
        *,
        viewer_id: UUID,
    ) -> HelpRequestResponseSchema:
        """Serializa entidade HelpRequest no contrato completo da API com contagem de mensagens não lidas."""
        student = help_request.student
        student_profile = student.profile
        enrollment = help_request.enrollment
        subject = help_request.subject
        module = help_request.module
        assigned_teacher = help_request.assigned_teacher
        teacher_profile = (
            assigned_teacher.profile if assigned_teacher is not None else None
        )
        messages = list(help_request.messages or [])
        unread_count = sum(
            1
            for msg in messages
            if not msg.is_read and msg.sender_id != viewer_id
        )

        return HelpRequestResponseSchema(
            id=help_request.id,
            student_id=help_request.student_id,
            enrollment_id=help_request.enrollment_id,
            class_id=enrollment.class_id,
            subject_id=help_request.subject_id,
            module_id=help_request.module_id,
            assigned_teacher_id=help_request.assigned_teacher_id,
            category=help_request.category,
            subject_title=help_request.subject_title,
            description=help_request.description,
            is_confidential=help_request.is_confidential,
            status=help_request.status,
            resolution_summary=help_request.resolution_summary,
            created_at=_ensure_utc(help_request.created_at),
            updated_at=_ensure_utc(help_request.updated_at),
            closed_at=(
                _ensure_utc(help_request.closed_at)
                if help_request.closed_at is not None
                else None
            ),
            student=HelpRequestStudentSummarySchema(
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
            subject=HelpRequestSubjectSummarySchema(
                id=subject.id,
                code=subject.code,
                name=subject.name,
            ),
            module=(
                HelpRequestModuleSummarySchema(
                    id=module.id,
                    title=module.title,
                    order_index=module.order_index,
                )
                if module is not None
                else None
            ),
            assigned_teacher=(
                HelpRequestTeacherSummarySchema(
                    id=assigned_teacher.id,
                    email=assigned_teacher.email,
                    role=assigned_teacher.role,
                    full_name=(
                        teacher_profile.full_name
                        if teacher_profile is not None
                        else None
                    ),
                )
                if assigned_teacher is not None
                else None
            ),
            unread_messages_count=unread_count,
            messages=[cls._serialize_message(msg) for msg in messages],
        )

    def create_help_request(
        self,
        payload: HelpRequestCreateSchema,
        *,
        current_user: User,
    ) -> HelpRequestResponseSchema:
        """Abre uma solicitação confidencial de apoio pelo aluno e direciona automaticamente ao professor titular (BE-043)."""
        if current_user.role != UserRole.STUDENT:
            raise ForbiddenException(
                message=HELP_REQUEST_ONLY_STUDENTS_CAN_CREATE_MESSAGE
            )

        subject = self._repository.get_subject_by_id(payload.subject_id)
        if subject is None:
            raise NotFoundException(message=HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE)

        if payload.module_id is not None:
            module = self._repository.get_module_by_id(payload.module_id)
            if module is None:
                raise NotFoundException(message=HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE)
            if module.subject_id != subject.id:
                raise UnprocessableEntityException(
                    message=HELP_REQUEST_MODULE_SUBJECT_MISMATCH_MESSAGE
                )

        enrollment = self._repository.get_student_active_enrollment_for_course(
            student_id=current_user.id,
            course_id=subject.course_id,
        )
        if enrollment is None:
            if not self._repository.has_any_active_enrollment(current_user.id):
                raise ForbiddenException(
                    message=HELP_REQUEST_STUDENT_NO_ACTIVE_ENROLLMENT_MESSAGE
                )
            raise ForbiddenException(
                message=HELP_REQUEST_STUDENT_NOT_ENROLLED_IN_SUBJECT_COURSE_MESSAGE
            )

        assigned_teacher_id = (
            self._repository.resolve_main_teacher_id_for_class_and_subject(
                class_id=enrollment.class_id,
                subject_id=subject.id,
            )
        )

        created = self._repository.create(
            student_id=current_user.id,
            enrollment_id=enrollment.id,
            subject_id=subject.id,
            module_id=payload.module_id,
            assigned_teacher_id=assigned_teacher_id,
            category=payload.category,
            subject_title=payload.subject_title,
            description=payload.description,
            is_confidential=payload.is_confidential,
        )

        logger.bind(
            help_request_id=str(created.id),
            student_id=str(current_user.id),
            enrollment_id=str(enrollment.id),
            class_id=str(enrollment.class_id),
            subject_id=str(subject.id),
            module_id=str(payload.module_id) if payload.module_id else None,
            assigned_teacher_id=(
                str(assigned_teacher_id) if assigned_teacher_id else None
            ),
            category=created.category.value,
            is_confidential=created.is_confidential,
        ).info(
            "Solicitação confidencial de apoio pedagógico aberta pelo estudante (BE-043)."
        )

        return self._to_response(created, viewer_id=current_user.id)

    def list_help_requests(
        self,
        params: HelpRequestListQueryParams,
        *,
        current_user: User,
    ) -> HelpRequestPaginatedResponseSchema:
        """Lista solicitações de apoio com proteção anti-exposição entre alunos e filtro contextual para docentes (BE-043)."""
        if params.class_id is not None:
            if self._repository.get_class_by_id(params.class_id) is None:
                raise NotFoundException(message=HELP_REQUEST_CLASS_NOT_FOUND_MESSAGE)

        if params.subject_id is not None:
            if self._repository.get_subject_by_id(params.subject_id) is None:
                raise NotFoundException(message=HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE)

        if params.module_id is not None:
            if self._repository.get_module_by_id(params.module_id) is None:
                raise NotFoundException(message=HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE)

        student_id_scope: UUID | None = None
        teacher_scope_id: UUID | None = None
        teacher_pairs: list[tuple[UUID, UUID]] | None = None

        if current_user.role == UserRole.STUDENT:
            # Proteção anti-exposição crítica: estudante vê estritamente os próprios pedidos
            student_id_scope = current_user.id

        elif current_user.role == UserRole.TEACHER:
            teacher_scope_id = current_user.id
            teacher_pairs = self._repository.list_teacher_assignments_pairs(
                current_user.id
            )
            assigned_class_ids = {cls_id for cls_id, _ in teacher_pairs}
            assigned_subject_ids = {subj_id for _, subj_id in teacher_pairs}

            if (
                params.class_id is not None
                and params.class_id not in assigned_class_ids
            ):
                raise ForbiddenException(
                    message=HELP_REQUEST_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )

            if (
                params.subject_id is not None
                and params.subject_id not in assigned_subject_ids
            ):
                raise ForbiddenException(
                    message=HELP_REQUEST_TEACHER_SUBJECT_FORBIDDEN_MESSAGE
                )

        items, total = self._repository.list_help_requests(
            page=params.page,
            limit=params.limit,
            student_id_scope=student_id_scope,
            teacher_scope_id=teacher_scope_id,
            teacher_class_subject_pairs=teacher_pairs,
            class_id=params.class_id,
            subject_id=params.subject_id,
            module_id=params.module_id,
            category=params.category,
            status=params.status,
        )
        total_pages = math.ceil(total / params.limit) if total > 0 else 0

        return HelpRequestPaginatedResponseSchema(
            data=[
                self._to_response(item, viewer_id=current_user.id) for item in items
            ],
            total=total,
            page=params.page,
            limit=params.limit,
            total_pages=total_pages,
        )

    def _get_authorized_help_request(
        self,
        help_request_id: UUID,
        *,
        current_user: User,
    ) -> HelpRequest:
        """Valida que apenas o aluno autor do pedido, o professor responsável ou a coordenação/admin acessam o chamado (BE-044)."""
        help_request = self._repository.get_by_id(help_request_id)
        if help_request is None:
            raise NotFoundException(message=HELP_REQUEST_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.STUDENT:
            if help_request.student_id != current_user.id:
                raise ForbiddenException(
                    message=HELP_REQUEST_STUDENT_PARTICIPANT_FORBIDDEN_MESSAGE
                )
            return help_request

        if current_user.role == UserRole.TEACHER:
            is_assigned_owner = help_request.assigned_teacher_id == current_user.id
            is_subject_teacher = (
                self._repository.is_teacher_assigned_to_class_and_subject(
                    teacher_id=current_user.id,
                    class_id=help_request.enrollment.class_id,
                    subject_id=help_request.subject_id,
                )
            )
            if not (is_assigned_owner or is_subject_teacher):
                raise ForbiddenException(
                    message=HELP_REQUEST_TEACHER_PARTICIPANT_FORBIDDEN_MESSAGE
                )

        return help_request

    def get_help_request_detail(
        self,
        help_request_id: UUID,
        *,
        current_user: User,
    ) -> HelpRequestResponseSchema:
        """Consulta um pedido de ajuda confidencial e atualiza is_read=True e read_at nas mensagens visualizadas pelo destinatário (BE-044)."""
        help_request = self._get_authorized_help_request(
            help_request_id,
            current_user=current_user,
        )
        self._repository.mark_recipient_messages_as_read(
            help_request,
            viewer_id=current_user.id,
        )
        refreshed = (
            self._repository.get_by_id(help_request.id, populate_existing=True)
            or help_request
        )
        return self._to_response(refreshed, viewer_id=current_user.id)

    def send_message(
        self,
        help_request_id: UUID,
        payload: HelpRequestMessageCreateSchema,
        *,
        current_user: User,
    ) -> HelpRequestResponseSchema:
        """Envia mensagem interna em chat_messages atualizando is_read/read_at das mensagens anteriores do outro participante (BE-044)."""
        help_request = self._get_authorized_help_request(
            help_request_id,
            current_user=current_user,
        )

        if help_request.status == HelpRequestStatus.CLOSED:
            raise UnprocessableEntityException(
                message=HELP_REQUEST_ALREADY_CLOSED_MESSAGE
            )

        now_utc = _utc_now()
        is_staff = current_user.role in {
            UserRole.TEACHER,
            UserRole.COORDINATOR,
            UserRole.ADMIN,
        }
        auto_assign_teacher_id = (
            current_user.id
            if is_staff and help_request.assigned_teacher_id is None
            else None
        )

        updated = self._repository.create_message_and_mark_read(
            help_request,
            sender_id=current_user.id,
            message_body=payload.message_body,
            sent_at=now_utc,
            auto_assign_teacher_id=auto_assign_teacher_id,
            auto_transition_to_in_progress=is_staff,
        )

        logger.bind(
            help_request_id=str(updated.id),
            sender_id=str(current_user.id),
            sender_role=current_user.role.value,
            status=updated.status.value,
        ).info(
            "Mensagem enviada na solicitação confidencial de apoio pedagógico (BE-044)."
        )

        return self._to_response(updated, viewer_id=current_user.id)

    def update_help_request(
        self,
        help_request_id: UUID,
        payload: HelpRequestUpdateSchema,
        *,
        current_user: User,
    ) -> HelpRequestResponseSchema:
        """Atualiza status de atendimento (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED), resumo de resolução e closed_at (BE-044)."""
        if current_user.role == UserRole.STUDENT:
            raise ForbiddenException(
                message=HELP_REQUEST_STATUS_UPDATE_FORBIDDEN_MESSAGE
            )

        help_request = self._get_authorized_help_request(
            help_request_id,
            current_user=current_user,
        )

        fields_set = payload.model_fields_set
        update_resolution = "resolution_summary" in fields_set
        update_assigned_teacher = "assigned_teacher_id" in fields_set
        target_status = payload.status

        if (
            help_request.status == HelpRequestStatus.CLOSED
            and target_status is not None
            and target_status != HelpRequestStatus.CLOSED
        ):
            raise UnprocessableEntityException(
                message=HELP_REQUEST_ALREADY_CLOSED_MESSAGE
            )

        if (
            help_request.status == HelpRequestStatus.RESOLVED
            and target_status == HelpRequestStatus.OPEN
        ):
            raise UnprocessableEntityException(
                message=HELP_REQUEST_INVALID_STATUS_TRANSITION_MESSAGE
            )

        assigned_teacher_id = payload.assigned_teacher_id
        if update_assigned_teacher and assigned_teacher_id is not None:
            assignee = self._repository.get_user_by_id(assigned_teacher_id)
            if (
                assignee is None
                or not assignee.is_active
                or assignee.role
                not in {UserRole.TEACHER, UserRole.COORDINATOR, UserRole.ADMIN}
            ):
                raise UnprocessableEntityException(
                    message=HELP_REQUEST_INVALID_ASSIGNED_TEACHER_MESSAGE
                )
        elif (
            not update_assigned_teacher
            and help_request.assigned_teacher_id is None
            and current_user.role
            in {UserRole.TEACHER, UserRole.COORDINATOR, UserRole.ADMIN}
        ):
            update_assigned_teacher = True
            assigned_teacher_id = current_user.id

        now_utc = _utc_now()
        updated = self._repository.update_help_request(
            help_request,
            viewer_id=current_user.id,
            now_utc=now_utc,
            status=target_status,
            resolution_summary=payload.resolution_summary,
            update_resolution_summary=update_resolution,
            assigned_teacher_id=assigned_teacher_id,
            update_assigned_teacher=update_assigned_teacher,
        )

        logger.bind(
            help_request_id=str(updated.id),
            actor_id=str(current_user.id),
            actor_role=current_user.role.value,
            status=updated.status.value,
            closed_at=updated.closed_at.isoformat() if updated.closed_at else None,
        ).info(
            "Status/resolução da solicitação confidencial de apoio atualizado (BE-044)."
        )

        return self._to_response(updated, viewer_id=current_user.id)


def get_help_request_service(
    repository: HelpRequestRepositoryDep,
) -> HelpRequestService:
    """Provedor de injeção de dependência para HelpRequestService."""
    return HelpRequestService(repository=repository)


HelpRequestServiceDep = Annotated[
    HelpRequestService,
    Depends(get_help_request_service),
]

__all__ = [
    "HELP_REQUEST_ALREADY_CLOSED_MESSAGE",
    "HELP_REQUEST_CLASS_NOT_FOUND_MESSAGE",
    "HELP_REQUEST_INVALID_ASSIGNED_TEACHER_MESSAGE",
    "HELP_REQUEST_INVALID_STATUS_TRANSITION_MESSAGE",
    "HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE",
    "HELP_REQUEST_MODULE_SUBJECT_MISMATCH_MESSAGE",
    "HELP_REQUEST_NOT_FOUND_MESSAGE",
    "HELP_REQUEST_ONLY_STUDENTS_CAN_CREATE_MESSAGE",
    "HELP_REQUEST_STATUS_UPDATE_FORBIDDEN_MESSAGE",
    "HELP_REQUEST_STUDENT_NOT_ENROLLED_IN_SUBJECT_COURSE_MESSAGE",
    "HELP_REQUEST_STUDENT_NO_ACTIVE_ENROLLMENT_MESSAGE",
    "HELP_REQUEST_STUDENT_PARTICIPANT_FORBIDDEN_MESSAGE",
    "HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE",
    "HELP_REQUEST_TEACHER_CLASS_FORBIDDEN_MESSAGE",
    "HELP_REQUEST_TEACHER_PARTICIPANT_FORBIDDEN_MESSAGE",
    "HELP_REQUEST_TEACHER_SUBJECT_FORBIDDEN_MESSAGE",
    "HelpRequestService",
    "HelpRequestServiceDep",
    "get_help_request_service",
]
