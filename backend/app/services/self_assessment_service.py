"""Serviço de domínio para Cadastro, Reabertura e Consulta de Questionários de Autoavaliação de Competências (BE-035)."""

from datetime import datetime, timezone
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.base import _utc_now
from app.models.module_competency import ModuleCompetency
from app.models.self_assessment import SelfAssessmentForm, StudentSelfAssessment
from app.models.user import User
from app.repositories.self_assessment_repository import (
    SelfAssessmentRepository,
    SelfAssessmentRepositoryDep,
)
from app.schemas.class_lesson import (
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import ClassStatus, EnrollmentStatus, UserRole
from app.schemas.self_assessment import (
    ClassSelfAssessmentFormsListResponseSchema,
    ClassSelfAssessmentFormsQueryParams,
    DEFAULT_SELF_ASSESSMENT_SCALE,
    SelfAssessmentCompetencyItemSchema,
    SelfAssessmentFormCreateSchema,
    SelfAssessmentFormResponseSchema,
    SelfAssessmentFormUpdateWindowSchema,
)

SELF_ASSESSMENT_FORM_NOT_FOUND_MESSAGE: Final[str] = (
    "Questionário de autoavaliação não encontrado."
)
SELF_ASSESSMENT_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
SELF_ASSESSMENT_CLASS_NOT_FOUND_MESSAGE: Final[str] = (
    "Turma acadêmica não encontrada."
)
SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE: Final[str] = (
    "Não é possível criar questionário de autoavaliação: o módulo prático informado não possui competências cadastradas (module_competencies)."
)
SELF_ASSESSMENT_INVALID_WINDOW_MESSAGE: Final[str] = (
    "A janela do questionário é inválida: a data/hora de abertura (opens_at) deve ser estritamente anterior ao fechamento (closes_at)."
)
SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa para esta turma e disciplina."
)
SELF_ASSESSMENT_CLASS_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE: Final[str] = (
    "Acesso negado: estudante não possui matrícula ativa nesta turma para consultar questionários de autoavaliação."
)
SELF_ASSESSMENT_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível criar ou reabrir questionário de autoavaliação em uma turma que não está ativa."
)
SELF_ASSESSMENT_INACTIVE_SUBJECT_MESSAGE: Final[str] = (
    "Não é possível criar questionário de autoavaliação em uma disciplina inativa."
)
SELF_ASSESSMENT_MODULE_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence ao curso técnico da turma selecionada."
)


def _ensure_utc(value: datetime) -> datetime:
    """Garante que um objeto datetime esteja em UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_form_window_open(
    form: SelfAssessmentForm,
    *,
    reference_now: datetime,
) -> bool:
    """Verifica se o questionário está ativo e dentro da janela [opens_at, closes_at]."""
    if not form.is_active:
        return False
    now_utc = _ensure_utc(reference_now)
    opens_utc = _ensure_utc(form.opens_at)
    closes_utc = _ensure_utc(form.closes_at)
    return opens_utc <= now_utc <= closes_utc


class SelfAssessmentService:
    """Serviço responsável pelo cadastro, reabertura de prazo e listagem de formulários de autoavaliação (BE-035)."""

    def __init__(self, repository: SelfAssessmentRepository) -> None:
        self._repository = repository

    @staticmethod
    def _sort_module_competencies(
        module_competencies: list[ModuleCompetency],
    ) -> list[ModuleCompetency]:
        """Ordena vínculos módulo-competência de forma determinística por código e título da competência."""
        return sorted(
            module_competencies,
            key=lambda mc: (
                mc.competency.code.upper(),
                mc.competency.title.lower(),
                str(mc.competency_id),
            ),
        )

    @classmethod
    def _to_form_response(
        cls,
        form: SelfAssessmentForm,
        *,
        reference_now: datetime,
        student_responses_by_comp: dict[UUID, StudentSelfAssessment] | None = None,
    ) -> SelfAssessmentFormResponseSchema:
        """Converte SelfAssessmentForm ORM em SelfAssessmentFormResponseSchema com competências do módulo e escala 1..5."""
        ordered_links = cls._sort_module_competencies(
            list(form.module.module_competencies)
        )
        competency_items: list[SelfAssessmentCompetencyItemSchema] = []
        answered_count = 0

        for link in ordered_links:
            comp = link.competency
            student_resp = (
                student_responses_by_comp.get(comp.id)
                if student_responses_by_comp is not None
                else None
            )
            is_answered: bool | None = None
            perceived_level: int | None = None
            confidence_score: int | None = None
            difficulty_notes: str | None = None

            if student_responses_by_comp is not None:
                is_answered = student_resp is not None
                if student_resp is not None:
                    answered_count += 1
                    perceived_level = student_resp.perceived_level
                    confidence_score = student_resp.confidence_score
                    difficulty_notes = student_resp.difficulty_notes

            competency_items.append(
                SelfAssessmentCompetencyItemSchema(
                    id=comp.id,
                    competency_id=comp.id,
                    module_id=form.module_id,
                    code=comp.code,
                    title=comp.title,
                    description=comp.description,
                    category=comp.category,
                    weight=link.weight,
                    required_level=link.required_level,
                    min_level=1,
                    max_level=5,
                    scale_options=[1, 2, 3, 4, 5],
                    is_answered=is_answered,
                    student_perceived_level=perceived_level,
                    student_confidence_score=confidence_score,
                    student_difficulty_notes=difficulty_notes,
                )
            )

        total_competencies = len(competency_items)
        window_open = is_form_window_open(form, reference_now=reference_now)

        answered_competencies_count: int | None = None
        is_pending_for_student: bool | None = None
        is_completed_by_student: bool | None = None

        if student_responses_by_comp is not None:
            answered_competencies_count = answered_count
            is_completed_by_student = (
                total_competencies > 0 and answered_count >= total_competencies
            )
            is_pending_for_student = window_open and not is_completed_by_student

        return SelfAssessmentFormResponseSchema(
            id=form.id,
            module_id=form.module_id,
            class_id=form.class_id,
            subject_id=form.module.subject_id,
            title=form.title,
            instructions=form.instructions,
            opens_at=_ensure_utc(form.opens_at),
            closes_at=_ensure_utc(form.closes_at),
            is_active=form.is_active,
            is_open=window_open,
            created_by=form.created_by,
            created_at=_ensure_utc(form.created_at),
            total_competencies=max(1, total_competencies),
            answered_competencies_count=answered_competencies_count,
            is_pending_for_current_student=is_pending_for_student,
            is_completed_by_current_student=is_completed_by_student,
            scale=DEFAULT_SELF_ASSESSMENT_SCALE,
            module=LessonModuleSummarySchema.model_validate(form.module),
            subject=LessonSubjectSummarySchema.model_validate(form.module.subject),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                form.academic_class
            ),
            competencies=competency_items,
            module_competencies=competency_items,
        )

    def create_self_assessment_form(
        self,
        payload: SelfAssessmentFormCreateSchema,
        *,
        current_user: User,
    ) -> SelfAssessmentFormResponseSchema:
        """Cria (ou reabre quando solicitado) um questionário de autoavaliação validando competências do módulo e janela temporal."""
        if _ensure_utc(payload.opens_at) >= _ensure_utc(payload.closes_at):
            raise BadRequestException(message=SELF_ASSESSMENT_INVALID_WINDOW_MESSAGE)

        module = self._repository.get_module_with_competencies(payload.module_id)
        if module is None:
            raise NotFoundException(message=SELF_ASSESSMENT_MODULE_NOT_FOUND_MESSAGE)

        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=SELF_ASSESSMENT_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=academic_class.id,
                subject_id=module.subject_id,
            )
        ):
            raise ForbiddenException(message=SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)

        if academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_INACTIVE_CLASS_MESSAGE
            )

        if not module.subject.is_active:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_INACTIVE_SUBJECT_MESSAGE
            )

        if module.subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_MODULE_COURSE_MISMATCH_MESSAGE
            )

        if not module.module_competencies:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE
            )

        now = _utc_now()
        if payload.reopen_if_exists:
            existing_form = self._repository.get_latest_form_by_class_and_module(
                class_id=academic_class.id,
                module_id=module.id,
            )
            if existing_form is not None:
                updated_form = self._repository.update_form(
                    existing_form,
                    title=payload.title,
                    instructions=payload.instructions,
                    update_instructions=True,
                    opens_at=payload.opens_at,
                    closes_at=payload.closes_at,
                    is_active=payload.is_active,
                )
                logger.bind(
                    form_id=str(updated_form.id),
                    module_id=str(updated_form.module_id),
                    class_id=str(updated_form.class_id),
                    actor_id=str(current_user.id),
                    opens_at=updated_form.opens_at.isoformat(),
                    closes_at=updated_form.closes_at.isoformat(),
                    is_active=updated_form.is_active,
                ).info("Questionário de autoavaliação existente reaberto/atualizado pelo professor.")
                return self._to_form_response(updated_form, reference_now=now)

        created = self._repository.create_form(
            module_id=module.id,
            class_id=academic_class.id,
            title=payload.title,
            instructions=payload.instructions,
            opens_at=payload.opens_at,
            closes_at=payload.closes_at,
            is_active=payload.is_active,
            created_by=current_user.id,
        )
        logger.bind(
            form_id=str(created.id),
            module_id=str(created.module_id),
            class_id=str(created.class_id),
            actor_id=str(current_user.id),
            competencies_count=len(created.module.module_competencies),
            opens_at=created.opens_at.isoformat(),
            closes_at=created.closes_at.isoformat(),
        ).info("Questionário de autoavaliação de competências criado com sucesso.")
        return self._to_form_response(created, reference_now=now)

    def update_or_reopen_self_assessment_form(
        self,
        form_id: UUID,
        payload: SelfAssessmentFormUpdateWindowSchema,
        *,
        current_user: User,
    ) -> SelfAssessmentFormResponseSchema:
        """Atualiza ou reabre o prazo (opens_at, closes_at, is_active) de um questionário de autoavaliação."""
        form = self._repository.get_form_by_id(form_id)
        if form is None:
            raise NotFoundException(message=SELF_ASSESSMENT_FORM_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=form.class_id,
                subject_id=form.module.subject_id,
            )
        ):
            raise ForbiddenException(message=SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)

        if form.academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_INACTIVE_CLASS_MESSAGE
            )

        if not form.module.module_competencies:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE
            )

        target_opens_at = (
            _ensure_utc(payload.opens_at)
            if payload.opens_at is not None
            else _ensure_utc(form.opens_at)
        )
        target_closes_at = (
            _ensure_utc(payload.closes_at)
            if payload.closes_at is not None
            else _ensure_utc(form.closes_at)
        )
        if target_opens_at >= target_closes_at:
            raise BadRequestException(message=SELF_ASSESSMENT_INVALID_WINDOW_MESSAGE)

        updated = self._repository.update_form(
            form,
            title=payload.title,
            instructions=payload.instructions,
            update_instructions=("instructions" in payload.model_fields_set),
            opens_at=target_opens_at,
            closes_at=target_closes_at,
            is_active=payload.is_active,
        )
        logger.bind(
            form_id=str(updated.id),
            module_id=str(updated.module_id),
            class_id=str(updated.class_id),
            actor_id=str(current_user.id),
            opens_at=updated.opens_at.isoformat(),
            closes_at=updated.closes_at.isoformat(),
            is_active=updated.is_active,
        ).info("Prazo/configuração do questionário de autoavaliação atualizado com sucesso.")
        return self._to_form_response(updated, reference_now=_utc_now())

    def list_class_self_assessment_forms(
        self,
        class_id: UUID,
        params: ClassSelfAssessmentFormsQueryParams | None = None,
        *,
        current_user: User,
    ) -> ClassSelfAssessmentFormsListResponseSchema:
        """Lista formulários de autoavaliação da turma com suas competências e filtra pendentes para o aluno logado."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=SELF_ASSESSMENT_CLASS_NOT_FOUND_MESSAGE)

        requested_module_id = params.module_id if params is not None else None
        requested_is_active = params.is_active if params is not None else None
        requested_pending_only = params.pending_only if params is not None else None
        include_completed = params.include_completed if params is not None else False

        if requested_module_id is not None:
            module = self._repository.get_module_with_competencies(requested_module_id)
            if module is None:
                raise NotFoundException(message=SELF_ASSESSMENT_MODULE_NOT_FOUND_MESSAGE)

        allowed_subject_ids: list[UUID] | None = None

        if current_user.role == UserRole.STUDENT:
            enrollment = self._repository.get_enrollment_by_class_and_student(
                class_id=academic_class.id,
                student_id=current_user.id,
            )
            if enrollment is None or enrollment.status != EnrollmentStatus.ACTIVE:
                raise ForbiddenException(
                    message=SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE
                )
        elif current_user.role == UserRole.TEACHER:
            assigned_subject_ids = (
                self._repository.get_teacher_assigned_subject_ids_for_class(
                    teacher_id=current_user.id,
                    class_id=academic_class.id,
                )
            )
            if not assigned_subject_ids:
                raise ForbiddenException(
                    message=SELF_ASSESSMENT_CLASS_TEACHER_FORBIDDEN_MESSAGE
                )
            allowed_subject_ids = list(assigned_subject_ids)

        forms = self._repository.list_forms_by_class(
            academic_class.id,
            module_id=requested_module_id,
            is_active=(
                True
                if (
                    current_user.role == UserRole.STUDENT
                    and requested_is_active is None
                )
                else requested_is_active
            ),
            allowed_subject_ids=allowed_subject_ids,
        )

        now = _utc_now()

        if current_user.role == UserRole.STUDENT:
            responses_map = self._repository.list_student_responses_for_forms(
                student_id=current_user.id,
                form_ids=[f.id for f in forms],
            )
            all_student_forms: list[SelfAssessmentFormResponseSchema] = []
            pending_count = 0

            for form in forms:
                if not form.module.module_competencies:
                    continue
                comp_responses: dict[UUID, StudentSelfAssessment] = {
                    mc.competency_id: responses_map[(form.id, mc.competency_id)]
                    for mc in form.module.module_competencies
                    if (form.id, mc.competency_id) in responses_map
                }
                schema_item = self._to_form_response(
                    form,
                    reference_now=now,
                    student_responses_by_comp=comp_responses,
                )
                if schema_item.is_pending_for_current_student:
                    pending_count += 1
                all_student_forms.append(schema_item)

            # Para estudante logado, por padrão lista os formulários pendentes de resposta (Critério de Aceitação 3)
            filter_pending = (
                True
                if (requested_pending_only is None and not include_completed)
                else bool(requested_pending_only)
            )
            if filter_pending:
                filtered_forms = [
                    item
                    for item in all_student_forms
                    if item.is_pending_for_current_student
                ]
            else:
                filtered_forms = all_student_forms

            return ClassSelfAssessmentFormsListResponseSchema(
                class_id=academic_class.id,
                academic_class=EnrollmentClassSummarySchema.model_validate(
                    academic_class
                ),
                total=len(filtered_forms),
                pending_count=pending_count,
                scale=DEFAULT_SELF_ASSESSMENT_SCALE,
                forms=filtered_forms,
                data=filtered_forms,
            )

        # Visão Docente / Coordenação / Admin
        staff_forms: list[SelfAssessmentFormResponseSchema] = []
        open_forms_count = 0
        for form in forms:
            if not form.module.module_competencies:
                continue
            schema_item = self._to_form_response(
                form,
                reference_now=now,
                student_responses_by_comp=None,
            )
            if schema_item.is_open:
                open_forms_count += 1
            staff_forms.append(schema_item)

        if requested_pending_only:
            staff_forms = [item for item in staff_forms if item.is_open]

        return ClassSelfAssessmentFormsListResponseSchema(
            class_id=academic_class.id,
            academic_class=EnrollmentClassSummarySchema.model_validate(academic_class),
            total=len(staff_forms),
            pending_count=open_forms_count,
            scale=DEFAULT_SELF_ASSESSMENT_SCALE,
            forms=staff_forms,
            data=staff_forms,
        )


def get_self_assessment_service(
    repository: SelfAssessmentRepositoryDep,
) -> SelfAssessmentService:
    """Provedor de injeção de dependência para SelfAssessmentService."""
    return SelfAssessmentService(repository=repository)


SelfAssessmentServiceDep = Annotated[
    SelfAssessmentService,
    Depends(get_self_assessment_service),
]

__all__ = [
    "SELF_ASSESSMENT_CLASS_NOT_FOUND_MESSAGE",
    "SELF_ASSESSMENT_CLASS_TEACHER_FORBIDDEN_MESSAGE",
    "SELF_ASSESSMENT_FORM_NOT_FOUND_MESSAGE",
    "SELF_ASSESSMENT_INACTIVE_CLASS_MESSAGE",
    "SELF_ASSESSMENT_INACTIVE_SUBJECT_MESSAGE",
    "SELF_ASSESSMENT_INVALID_WINDOW_MESSAGE",
    "SELF_ASSESSMENT_MODULE_COURSE_MISMATCH_MESSAGE",
    "SELF_ASSESSMENT_MODULE_NOT_FOUND_MESSAGE",
    "SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE",
    "SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE",
    "SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE",
    "SelfAssessmentService",
    "SelfAssessmentServiceDep",
    "get_self_assessment_service",
    "is_form_window_open",
]
