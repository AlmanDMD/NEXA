"""Serviço de domínio para Cadastro, Reabertura, Submissão e Cruzamento Diagnóstico de Autoavaliação de Competências (BE-035 / BE-036)."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
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
from app.models.competency import Competency
from app.models.module_competency import ModuleCompetency
from app.models.self_assessment import (
    ExplainableDiagnostic,
    SelfAssessmentForm,
    StudentSelfAssessment,
)
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
from app.schemas.enums import (
    ClassStatus,
    DiagnosticType,
    EnrollmentStatus,
    UserRole,
)
from app.schemas.self_assessment import (
    ClassSelfAssessmentFormsListResponseSchema,
    ClassSelfAssessmentFormsQueryParams,
    DEFAULT_SELF_ASSESSMENT_SCALE,
    ExplainableDiagnosticItemResponseSchema,
    HelpRequestSuggestionCompetencySchema,
    HelpRequestSuggestionSchema,
    SelfAssessmentCompetencyItemSchema,
    SelfAssessmentFormCreateSchema,
    SelfAssessmentFormResponseSchema,
    SelfAssessmentFormUpdateWindowSchema,
    StudentSelfAssessmentAnswerResponseSchema,
    StudentSelfAssessmentSubmitRequestSchema,
    StudentSelfAssessmentSubmitResponseSchema,
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
SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso negado: não é permitido submeter respostas de autoavaliação em nome de outro estudante."
)
SELF_ASSESSMENT_SUBMIT_ROLE_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso negado: apenas usuários com perfil de estudante (STUDENT) podem submeter respostas de autoavaliação."
)
SELF_ASSESSMENT_SUBMIT_INACTIVE_FORM_MESSAGE: Final[str] = (
    "Não é possível enviar respostas: o questionário de autoavaliação está inativo."
)
SELF_ASSESSMENT_SUBMIT_NOT_OPEN_YET_MESSAGE: Final[str] = (
    "Não é possível enviar respostas: o questionário de autoavaliação ainda não foi aberto para submissões."
)
SELF_ASSESSMENT_SUBMIT_DEADLINE_EXPIRED_MESSAGE: Final[str] = (
    "Não é possível enviar respostas: o prazo do questionário de autoavaliação já foi encerrado."
)
SELF_ASSESSMENT_SUBMIT_INVALID_COMPETENCY_MESSAGE: Final[str] = (
    "Uma ou mais competências informadas na submissão não pertencem ao módulo prático deste questionário."
)
HIGH_DIFFICULTY_LEVEL_THRESHOLD: Final[int] = 2
DISCREPANCY_GAP_THRESHOLD: Final[Decimal] = Decimal("1.50")
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")


def _quantize_level(value: Decimal) -> Decimal:
    """Arredonda nível numérico para duas casas decimais."""
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def compute_competency_explainable_diagnostic(
    *,
    competency: Competency,
    module_title: str,
    perceived_level: int,
    confidence_score: int,
    difficulty_notes: str | None,
    avg_verified_level: Decimal | None,
    evidence_count: int,
) -> tuple[Decimal, Decimal, Decimal, DiagnosticType, str, str, str]:
    """Executa o cruzamento diagnóstico explicável entre autoavaliação discente e evidências práticas do docente (BE-036 / BE-037)."""
    self_level = _quantize_level(Decimal(perceived_level))

    if evidence_count <= 0 or avg_verified_level is None:
        teacher_level = self_level
        gap = Decimal("0.00")
        diag_type = DiagnosticType.INSUFFICIENT_EVIDENCE
        explanation_text = (
            f"Na competência '{competency.code} — {competency.title}' do módulo '{module_title}', "
            f"o estudante declarou nível percebido {self_level:.2f}/5.00 (confiança {confidence_score}/5), "
            "porém ainda não há evidências práticas avaliadas pelo docente (skill_evidences = 0) para comparação objetiva."
        )
        limitations_note = (
            "Análise preliminar baseada exclusivamente na autopercepção discente (0 evidências práticas registradas). "
            "A autoavaliação tem caráter formativo e não substitui a verificação técnica em bancada pelo professor."
        )
        if perceived_level <= HIGH_DIFFICULTY_LEVEL_THRESHOLD:
            recommended_action = (
                "Priorizar acompanhamento preventivo em bancada na próxima aula prática e considerar abertura de pedido de apoio pedagógico."
            )
        else:
            recommended_action = (
                "Aguardar a avaliação da próxima entrega prática com rubricas (BE-025) para consolidar o cruzamento diagnóstico."
            )
        return (
            self_level,
            teacher_level,
            gap,
            diag_type,
            explanation_text,
            limitations_note,
            recommended_action,
        )

    teacher_level = min(
        Decimal("5.00"),
        max(Decimal("1.00"), _quantize_level(avg_verified_level)),
    )
    gap = _quantize_level(self_level - teacher_level)

    if gap >= DISCREPANCY_GAP_THRESHOLD:
        diag_type = DiagnosticType.OVERCONFIDENCE_RISK
        explanation_text = (
            f"Divergência positiva (superestimação) identificada em '{competency.code} — {competency.title}': "
            f"nível autopercebido de {self_level:.2f}/5.00 (confiança {confidence_score}/5) frente à média verificada "
            f"pelo docente de {teacher_level:.2f}/5.00 em {evidence_count} evidência(s) prática(s) (gap de +{gap:.2f})."
        )
        recommended_action = (
            "Realizar calibração de critérios técnicos e revisão de normas de segurança/tolerância na oficina com feedback individualizado."
        )
    elif gap <= -DISCREPANCY_GAP_THRESHOLD:
        diag_type = DiagnosticType.UNDERCONFIDENCE_SUPPORT
        explanation_text = (
            f"Divergência negativa (subestimação/insegurança) identificada em '{competency.code} — {competency.title}': "
            f"o estudante declarou nível percebido de {self_level:.2f}/5.00 (confiança {confidence_score}/5), mas demonstrou "
            f"desempenho prático superior de {teacher_level:.2f}/5.00 em {evidence_count} evidência(s) verificada(s) (gap de {gap:.2f})."
        )
        recommended_action = (
            "Reforçar feedback positivo sobre o desempenho real em bancada para fortalecer a autonomia e a segurança técnica do estudante."
        )
    else:
        diag_type = DiagnosticType.ALIGNED
        explanation_text = (
            f"Percepção alinhada na competência '{competency.code} — {competency.title}': "
            f"nível autopercebido de {self_level:.2f}/5.00 (confiança {confidence_score}/5) convergente com a média "
            f"verificada pelo docente de {teacher_level:.2f}/5.00 em {evidence_count} evidência(s) (gap de {gap:+.2f})."
        )
        if perceived_level <= HIGH_DIFFICULTY_LEVEL_THRESHOLD:
            recommended_action = (
                "Estudante e docente reconhecem dificuldade técnica atual (nível <= 2): recomendar prática assistida ou mentoria direcionada."
            )
        else:
            recommended_action = (
                "Manter progressão prática nas atividades de oficina do módulo com monitoramento contínuo das rubricas."
            )

    difficulty_excerpt = (
        f" Relato do estudante: '{difficulty_notes}'."
        if difficulty_notes
        else ""
    )
    limitations_note = (
        f"Diagnóstico explicável baseado em {evidence_count} evidência(s) prática(s) registrada(s) até o momento e na autoavaliação reflexiva "
        f"(limiar de discrepância |gap| >= {DISCREPANCY_GAP_THRESHOLD:.2f}). Indicador pedagógico de apoio à decisão docente, não punitivo.{difficulty_excerpt}"
    )

    return (
        self_level,
        teacher_level,
        gap,
        diag_type,
        explanation_text,
        limitations_note,
        recommended_action,
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

    def submit_student_self_assessment(
        self,
        payload: StudentSelfAssessmentSubmitRequestSchema,
        *,
        current_user: User,
    ) -> StudentSelfAssessmentSubmitResponseSchema:
        """Recebe e persiste as respostas de autoavaliação do estudante logado, sugere pedido de ajuda se perceived_level <= 2 e dispara o cruzamento diagnóstico (BE-036)."""
        if current_user.role != UserRole.STUDENT:
            raise ForbiddenException(
                message=SELF_ASSESSMENT_SUBMIT_ROLE_FORBIDDEN_MESSAGE
            )

        if payload.student_id is not None and payload.student_id != current_user.id:
            raise ForbiddenException(
                message=SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE
            )

        form = self._repository.get_form_by_id(payload.form_id)
        if form is None:
            raise NotFoundException(message=SELF_ASSESSMENT_FORM_NOT_FOUND_MESSAGE)

        if form.academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_INACTIVE_CLASS_MESSAGE
            )

        enrollment = self._repository.get_enrollment_by_class_and_student(
            class_id=form.class_id,
            student_id=current_user.id,
        )
        if enrollment is None or enrollment.status != EnrollmentStatus.ACTIVE:
            raise ForbiddenException(
                message=SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE
            )

        now = _utc_now()
        if not form.is_active:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_SUBMIT_INACTIVE_FORM_MESSAGE
            )

        opens_utc = _ensure_utc(form.opens_at)
        closes_utc = _ensure_utc(form.closes_at)
        now_utc = _ensure_utc(now)

        if now_utc < opens_utc:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_SUBMIT_NOT_OPEN_YET_MESSAGE
            )
        if now_utc > closes_utc:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_SUBMIT_DEADLINE_EXPIRED_MESSAGE
            )

        module_competencies_by_id: dict[UUID, Competency] = {
            mc.competency_id: mc.competency
            for mc in form.module.module_competencies
        }
        if not module_competencies_by_id:
            raise UnprocessableEntityException(
                message=SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE
            )

        for item in payload.responses:
            if item.competency_id not in module_competencies_by_id:
                raise BadRequestException(
                    message=SELF_ASSESSMENT_SUBMIT_INVALID_COMPETENCY_MESSAGE
                )

        answer_tuples = [
            (
                item.competency_id,
                item.perceived_level,
                item.confidence_score,
                item.difficulty_notes,
            )
            for item in payload.responses
        ]
        persisted_answers, created_count, updated_count = (
            self._repository.upsert_student_self_assessment_responses(
                form_id=form.id,
                student_id=current_user.id,
                answers=answer_tuples,
                submitted_at=now_utc,
            )
        )

        # Dispara o algoritmo de cruzamento diagnóstico (BE-037) para as competências respondidas
        submitted_comp_ids = [item.competency_id for item in payload.responses]
        evidence_stats_by_comp = self._repository.get_student_skill_evidence_stats(
            student_id=current_user.id,
            competency_ids=submitted_comp_ids,
        )

        diagnostic_tuples: list[
            tuple[
                UUID,
                Decimal,
                Decimal,
                Decimal,
                DiagnosticType,
                str,
                str,
                str,
            ]
        ] = []
        for item in payload.responses:
            comp = module_competencies_by_id[item.competency_id]
            avg_verified, evidence_count = evidence_stats_by_comp.get(
                item.competency_id,
                (None, 0),
            )
            (
                self_lvl,
                teacher_lvl,
                gap,
                diag_type,
                explanation_text,
                limitations_note,
                recommended_action,
            ) = compute_competency_explainable_diagnostic(
                competency=comp,
                module_title=form.module.title,
                perceived_level=item.perceived_level,
                confidence_score=item.confidence_score,
                difficulty_notes=item.difficulty_notes,
                avg_verified_level=avg_verified,
                evidence_count=evidence_count,
            )
            diagnostic_tuples.append(
                (
                    item.competency_id,
                    self_lvl,
                    teacher_lvl,
                    gap,
                    diag_type,
                    explanation_text,
                    limitations_note,
                    recommended_action,
                )
            )

        persisted_diagnostics = self._repository.upsert_explainable_diagnostics(
            student_id=current_user.id,
            class_id=form.class_id,
            module_id=form.module_id,
            diagnostic_items=diagnostic_tuples,
            generated_at=now_utc,
        )

        all_student_responses = self._repository.list_student_responses_for_form(
            form_id=form.id,
            student_id=current_user.id,
        )
        answered_comp_ids = {
            resp.competency_id
            for resp in all_student_responses
            if resp.competency_id in module_competencies_by_id
        }
        is_form_completed = len(answered_comp_ids) >= len(module_competencies_by_id)

        responses_schemas: list[StudentSelfAssessmentAnswerResponseSchema] = []
        flagged_for_help: list[HelpRequestSuggestionCompetencySchema] = []

        for ans in persisted_answers:
            comp = module_competencies_by_id[ans.competency_id]
            is_high_diff = ans.perceived_level <= HIGH_DIFFICULTY_LEVEL_THRESHOLD
            if is_high_diff:
                flagged_for_help.append(
                    HelpRequestSuggestionCompetencySchema(
                        competency_id=comp.id,
                        competency_code=comp.code,
                        competency_title=comp.title,
                        perceived_level=ans.perceived_level,
                        confidence_score=ans.confidence_score,
                        difficulty_notes=ans.difficulty_notes,
                    )
                )
            responses_schemas.append(
                StudentSelfAssessmentAnswerResponseSchema(
                    id=ans.id,
                    form_id=ans.form_id,
                    student_id=ans.student_id,
                    competency_id=ans.competency_id,
                    competency_code=comp.code,
                    competency_title=comp.title,
                    competency_category=comp.category,
                    perceived_level=ans.perceived_level,
                    confidence_score=ans.confidence_score,
                    difficulty_notes=ans.difficulty_notes,
                    is_high_difficulty=is_high_diff,
                    submitted_at=_ensure_utc(ans.submitted_at),
                )
            )

        should_suggest_help = len(flagged_for_help) > 0
        help_message = (
            "Identificamos que você relatou dificuldade mais alta (nível 1 ou 2) em uma ou mais competências práticas deste módulo. "
            "Caso deseje, você pode abrir um pedido confidencial de apoio pedagógico para receber orientação individual do professor na oficina."
            if should_suggest_help
            else None
        )
        help_suggestion = HelpRequestSuggestionSchema(
            should_suggest_help_request=should_suggest_help,
            high_difficulty_count=len(flagged_for_help),
            suggested_category="PRACTICAL_DIFFICULTY",
            suggested_endpoint="/api/v1/help-requests",
            subject_id=form.module.subject_id,
            module_id=form.module_id,
            message=help_message,
            flagged_competencies=flagged_for_help,
        )

        diagnostics_schemas: list[ExplainableDiagnosticItemResponseSchema] = []
        for diag in persisted_diagnostics:
            comp = (
                module_competencies_by_id.get(diag.competency_id)
                if diag.competency_id is not None
                else None
            )
            _, ev_count = (
                evidence_stats_by_comp.get(diag.competency_id, (None, 0))
                if diag.competency_id is not None
                else (None, 0)
            )
            diagnostics_schemas.append(
                ExplainableDiagnosticItemResponseSchema(
                    id=diag.id,
                    student_id=diag.student_id,
                    class_id=diag.class_id,
                    module_id=diag.module_id,
                    competency_id=diag.competency_id,
                    competency_code=comp.code if comp is not None else None,
                    competency_title=comp.title if comp is not None else None,
                    self_perceived_level=diag.self_perceived_level,
                    teacher_verified_level=diag.teacher_verified_level,
                    discrepancy_gap=diag.discrepancy_gap,
                    evidence_count=ev_count,
                    diagnostic_type=diag.diagnostic_type,
                    explanation_text=diag.explanation_text,
                    limitations_note=diag.limitations_note,
                    recommended_action=diag.recommended_action,
                    generated_at=_ensure_utc(diag.generated_at),
                )
            )

        logger.bind(
            form_id=str(form.id),
            student_id=str(current_user.id),
            class_id=str(form.class_id),
            module_id=str(form.module_id),
            total_submitted=len(responses_schemas),
            created_count=created_count,
            updated_count=updated_count,
            suggest_help_request=should_suggest_help,
            diagnostics_count=len(diagnostics_schemas),
        ).info("Autoavaliação de competências submetida pelo estudante com cruzamento diagnóstico.")

        return StudentSelfAssessmentSubmitResponseSchema(
            form_id=form.id,
            student_id=current_user.id,
            class_id=form.class_id,
            module_id=form.module_id,
            subject_id=form.module.subject_id,
            total_submitted=len(responses_schemas),
            created_count=created_count,
            updated_count=updated_count,
            is_form_completed=is_form_completed,
            suggest_help_request=should_suggest_help,
            help_request_suggestion=help_suggestion,
            diagnostic_triggered=True,
            diagnostics=diagnostics_schemas,
            responses=responses_schemas,
            submitted_at=now_utc,
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
    "DISCREPANCY_GAP_THRESHOLD",
    "HIGH_DIFFICULTY_LEVEL_THRESHOLD",
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
    "SELF_ASSESSMENT_SUBMIT_DEADLINE_EXPIRED_MESSAGE",
    "SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE",
    "SELF_ASSESSMENT_SUBMIT_INACTIVE_FORM_MESSAGE",
    "SELF_ASSESSMENT_SUBMIT_INVALID_COMPETENCY_MESSAGE",
    "SELF_ASSESSMENT_SUBMIT_NOT_OPEN_YET_MESSAGE",
    "SELF_ASSESSMENT_SUBMIT_ROLE_FORBIDDEN_MESSAGE",
    "SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE",
    "SelfAssessmentService",
    "SelfAssessmentServiceDep",
    "compute_competency_explainable_diagnostic",
    "get_self_assessment_service",
    "is_form_window_open",
]
