"""Serviço de domínio para Atividades Práticas de Oficina e Critérios de Tolerância (BE-024)."""

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
from app.models.practical_task import PracticalTask, TaskCriterion, TaskSubmission
from app.models.user import User
from app.repositories.practical_task_repository import (
    PracticalTaskRepository,
    PracticalTaskRepositoryDep,
)
from app.repositories.risk_engine_repository import RiskEngineRepository
from app.services.risk_engine_service import RiskEngineService
from app.schemas.class_lesson import (
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
    StudentAttendanceSummaryStudentSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import ClassStatus, EnrollmentStatus, SubmissionStatus, UserRole
from app.schemas.practical_task import (
    PracticalTaskCreateSchema,
    PracticalTaskListQueryParams,
    PracticalTaskPaginatedResponseSchema,
    PracticalTaskResponseSchema,
    SkillEvidenceResponseSchema,
    StudentPendingTaskItemSchema,
    StudentPendingTasksQueryParams,
    StudentPendingTasksResponseSchema,
    StudentTaskCountsSummarySchema,
    SubmissionCriterionEvaluationResponseSchema,
    TaskCriterionCompetencySummarySchema,
    TaskCriterionResponseSchema,
    TaskEvaluationRequestSchema,
    TaskEvaluationResponseSchema,
)

PRACTICAL_TASK_NOT_FOUND_MESSAGE: Final[str] = "Atividade prática não encontrada."
PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
PRACTICAL_TASK_COMPETENCY_NOT_FOUND_MESSAGE: Final[str] = (
    "Uma ou mais competências técnicas referenciadas nas rubricas não existem no banco de dados."
)
PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa para esta turma e disciplina."
)
PRACTICAL_TASK_MODULE_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado na disciplina deste módulo prático."
)
PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível criar atividade prática em uma turma que não está ativa."
)
PRACTICAL_TASK_INACTIVE_SUBJECT_MESSAGE: Final[str] = (
    "Não é possível criar atividade prática em uma disciplina inativa."
)
PRACTICAL_TASK_MODULE_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence ao curso técnico da turma selecionada."
)
TASK_EVALUATION_STUDENT_NOT_ENROLLED_MESSAGE: Final[str] = (
    "Estudante informado não está matriculado na turma desta atividade prática."
)
TASK_EVALUATION_INACTIVE_ENROLLMENT_MESSAGE: Final[str] = (
    "Não é possível registrar avaliação prática para matrícula inativa ou trancada (DROPPED)."
)
TASK_EVALUATION_INVALID_CRITERION_MESSAGE: Final[str] = (
    "Um ou mais critérios informados não pertencem a esta atividade prática."
)
TASK_EVALUATION_INCOMPLETE_CRITERIA_MESSAGE: Final[str] = (
    "Todos os critérios técnicos (rubricas) da atividade prática devem ser avaliados."
)
STUDENT_TASKS_NOT_FOUND_MESSAGE: Final[str] = "Estudante não encontrado."
STUDENT_TASKS_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = (
    "Disciplina técnica não encontrada."
)
STUDENT_TASKS_ENROLLMENT_NOT_FOUND_MESSAGE: Final[str] = (
    "Matrícula do estudante não encontrada para a turma informada."
)
STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso negado: estudantes só podem consultar suas próprias atividades práticas pendentes."
)
STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona em nenhuma turma em que o estudante está matriculado."
)
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")
_MAX_RUBRIC_LEVEL: Final[Decimal] = Decimal("5")


class PracticalTaskService:
    """Serviço responsável pelo cadastro e listagem de tarefas práticas com geração de entregas PENDING."""

    def __init__(self, repository: PracticalTaskRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_response(task: PracticalTask) -> PracticalTaskResponseSchema:
        """Converte PracticalTask ORM em PracticalTaskResponseSchema com contadores de submissão."""
        criteria_schemas = [
            TaskCriterionResponseSchema(
                id=criterion.id,
                task_id=criterion.task_id,
                competency_id=criterion.competency_id,
                criterion_name=criterion.criterion_name,
                weight=criterion.weight,
                min_acceptable_level=criterion.min_acceptable_level,
                competency=TaskCriterionCompetencySummarySchema(
                    id=criterion.competency.id,
                    code=criterion.competency.code,
                    title=criterion.competency.title,
                    category=criterion.competency.category,
                ),
            )
            for criterion in task.criteria
        ]

        total_submissions = len(task.submissions)
        completed_submissions = sum(
            1
            for sub in task.submissions
            if sub.status in (SubmissionStatus.SUBMITTED, SubmissionStatus.EVALUATED)
        )
        pending_submissions = total_submissions - completed_submissions

        return PracticalTaskResponseSchema(
            id=task.id,
            module_id=task.module_id,
            class_id=task.class_id,
            title=task.title,
            description=task.description,
            blueprint_url=task.blueprint_url,
            due_date=task.due_date,
            max_score=task.max_score,
            is_mandatory=task.is_mandatory,
            initialized_submissions_count=total_submissions,
            total_submissions_count=total_submissions,
            pending_submissions_count=pending_submissions,
            completed_submissions_count=completed_submissions,
            module=LessonModuleSummarySchema.model_validate(task.module),
            academic_class=EnrollmentClassSummarySchema.model_validate(task.academic_class),
            criteria=criteria_schemas,
            task_criteria=criteria_schemas,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def create_practical_task(
        self,
        payload: PracticalTaskCreateSchema,
        *,
        current_user: User,
    ) -> PracticalTaskResponseSchema:
        """Cadastra atividade prática com rubricas e inicializa entregas PENDING para alunos ativos."""
        module = self._repository.get_module_by_id(payload.module_id)
        if module is None:
            raise NotFoundException(message=PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE)

        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=academic_class.id,
                subject_id=module.subject_id,
            )
        ):
            raise ForbiddenException(message=PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE)

        if academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE)

        if not module.subject.is_active:
            raise UnprocessableEntityException(message=PRACTICAL_TASK_INACTIVE_SUBJECT_MESSAGE)

        if module.subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(
                message=PRACTICAL_TASK_MODULE_COURSE_MISMATCH_MESSAGE
            )

        referenced_comp_ids = [item.competency_id for item in payload.criteria]
        existing_competencies = self._repository.get_competencies_by_ids(referenced_comp_ids)
        missing_comp_ids = [
            comp_id for comp_id in referenced_comp_ids if comp_id not in existing_competencies
        ]
        if missing_comp_ids:
            raise NotFoundException(message=PRACTICAL_TASK_COMPETENCY_NOT_FOUND_MESSAGE)

        criteria_items = [
            (
                item.competency_id,
                item.criterion_name,
                item.weight,
                item.min_acceptable_level,
            )
            for item in payload.criteria
        ]
        created = self._repository.create_task_with_criteria_and_pending_submissions(
            module_id=module.id,
            class_id=academic_class.id,
            title=payload.title,
            description=payload.description,
            blueprint_url=payload.blueprint_url,
            due_date=payload.due_date,
            max_score=payload.max_score,
            is_mandatory=payload.is_mandatory,
            criteria_items=criteria_items,
        )
        logger.bind(
            task_id=str(created.id),
            module_id=str(created.module_id),
            class_id=str(created.class_id),
            actor_id=str(current_user.id),
            criteria_count=len(created.criteria),
            initialized_submissions_count=len(created.submissions),
        ).info("Atividade prática criada com rubricas e entregas PENDING inicializadas.")
        return self._to_response(created)

    def list_module_practical_tasks(
        self,
        module_id: UUID,
        params: PracticalTaskListQueryParams,
        *,
        current_user: User,
    ) -> PracticalTaskPaginatedResponseSchema:
        """Lista atividades práticas de um módulo com suas rubricas e contadores de progresso da turma."""
        module = self._repository.get_module_by_id(module_id)
        if module is None:
            raise NotFoundException(message=PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE)

        allowed_class_ids: list[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            assigned_classes = self._repository.get_teacher_assigned_class_ids_for_subject(
                teacher_id=current_user.id,
                subject_id=module.subject_id,
            )
            if not assigned_classes:
                raise ForbiddenException(
                    message=PRACTICAL_TASK_MODULE_TEACHER_FORBIDDEN_MESSAGE
                )
            if params.class_id is not None and params.class_id not in assigned_classes:
                raise ForbiddenException(message=PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE)
            allowed_class_ids = list(assigned_classes)

        items, total = self._repository.list_by_module(
            module.id,
            page=params.page,
            limit=params.limit,
            class_id=params.class_id,
            allowed_class_ids=allowed_class_ids,
            is_mandatory=params.is_mandatory,
            search=params.search,
        )
        return PracticalTaskPaginatedResponseSchema(
            data=[self._to_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def evaluate_practical_task(
        self,
        task_id: UUID,
        payload: TaskEvaluationRequestSchema,
        *,
        current_user: User,
    ) -> TaskEvaluationResponseSchema:
        """Avalia entrega prática por rubricas no servidor, atualiza task_submissions e grava skill_evidences (BE-025)."""
        task = self._repository.get_by_id(task_id)
        if task is None:
            raise NotFoundException(message=PRACTICAL_TASK_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=task.class_id,
                subject_id=task.module.subject_id,
            )
        ):
            raise ForbiddenException(message=PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE)

        if task.academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE)

        enrollment = self._repository.get_enrollment_by_class_and_student(
            class_id=task.class_id,
            student_id=payload.student_id,
        )
        if enrollment is None:
            raise BadRequestException(message=TASK_EVALUATION_STUDENT_NOT_ENROLLED_MESSAGE)

        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise BadRequestException(message=TASK_EVALUATION_INACTIVE_ENROLLMENT_MESSAGE)

        task_criteria_by_id: dict[UUID, TaskCriterion] = {
            criterion.id: criterion for criterion in task.criteria
        }
        for item in payload.evaluations:
            if item.criterion_id not in task_criteria_by_id:
                raise BadRequestException(message=TASK_EVALUATION_INVALID_CRITERION_MESSAGE)

        if len(payload.evaluations) != len(task_criteria_by_id):
            raise BadRequestException(message=TASK_EVALUATION_INCOMPLETE_CRITERIA_MESSAGE)

        criterion_evaluations: list[tuple[TaskCriterion, int, Decimal, str | None]] = []
        weighted_level_sum = Decimal("0.00")
        total_weight_sum = Decimal("0.00")
        competency_weighted_sums: dict[UUID, list[Decimal]] = {}

        for item in payload.evaluations:
            criterion = task_criteria_by_id[item.criterion_id]
            level_dec = Decimal(item.achieved_level)
            weight_dec = Decimal(criterion.weight)
            score_awarded = (
                (level_dec / _MAX_RUBRIC_LEVEL) * Decimal(task.max_score)
            ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

            weighted_level_sum += level_dec * weight_dec
            total_weight_sum += weight_dec

            comp_bucket = competency_weighted_sums.setdefault(
                criterion.competency_id,
                [Decimal("0.00"), Decimal("0.00")],
            )
            comp_bucket[0] += level_dec * weight_dec
            comp_bucket[1] += weight_dec

            criterion_evaluations.append(
                (
                    criterion,
                    item.achieved_level,
                    score_awarded,
                    item.technical_feedback,
                )
            )

        if total_weight_sum <= Decimal("0.00"):
            final_task_score = Decimal("0.00")
        else:
            final_task_score = (
                (weighted_level_sum / (_MAX_RUBRIC_LEVEL * total_weight_sum))
                * Decimal(task.max_score)
            ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

        competency_verified_levels: list[tuple[UUID, Decimal]] = []
        for comp_id, (comp_weighted_level, comp_weight_total) in competency_weighted_sums.items():
            verified_level = (comp_weighted_level / comp_weight_total).quantize(
                _DECIMAL_QUANTIZER,
                rounding=ROUND_HALF_UP,
            )
            verified_level = min(
                Decimal("5.00"),
                max(Decimal("1.00"), verified_level),
            )
            competency_verified_levels.append((comp_id, verified_level))

        submission = self._repository.evaluate_task_submission_with_evidences(
            task=task,
            enrollment=enrollment,
            evaluator_id=current_user.id,
            final_task_score=final_task_score,
            criterion_evaluations=criterion_evaluations,
            competency_verified_levels=competency_verified_levels,
            evidence_url=payload.evidence_url,
            student_notes=payload.student_notes,
        )
        RiskEngineService(
            repository=RiskEngineRepository(session=self._repository.session)
        ).evaluate_student_enrollment_risk(enrollment_id=enrollment.id)

        evaluations_response = [
            SubmissionCriterionEvaluationResponseSchema(
                id=ev.id,
                submission_id=ev.submission_id,
                criterion_id=ev.criterion_id,
                criterion_name=ev.criterion.criterion_name,
                competency_id=ev.criterion.competency_id,
                competency_code=ev.criterion.competency.code,
                competency_title=ev.criterion.competency.title,
                weight=ev.criterion.weight,
                min_acceptable_level=ev.criterion.min_acceptable_level,
                achieved_level=ev.achieved_level,
                meets_min_acceptable_level=(
                    ev.achieved_level >= ev.criterion.min_acceptable_level
                ),
                score_awarded=ev.score_awarded,
                technical_feedback=ev.technical_feedback,
                evaluated_at=ev.evaluated_at,
            )
            for ev in submission.evaluations
        ]

        evidences_response = [
            SkillEvidenceResponseSchema(
                id=se.id,
                student_id=se.student_id,
                competency_id=se.competency_id,
                competency_code=se.competency.code,
                competency_title=se.competency.title,
                source_submission_id=se.source_submission_id,
                verified_level=se.verified_level,
                verified_by=se.verified_by,
                recorded_at=se.recorded_at,
            )
            for se in submission.skill_evidences
        ]

        evaluated_at = (
            evaluations_response[0].evaluated_at
            if evaluations_response
            else submission.updated_at
        )
        passing_score = Decimal(task.module.passing_score).quantize(_DECIMAL_QUANTIZER)
        is_approved = final_task_score >= passing_score

        logger.bind(
            task_id=str(task.id),
            submission_id=str(submission.id),
            student_id=str(enrollment.student_id),
            evaluator_id=str(current_user.id),
            final_task_score=str(final_task_score),
            is_approved=is_approved,
            evidences_count=len(evidences_response),
        ).info("Avaliação prática por rubricas registrada com nota ponderada e evidências de habilidade.")

        return TaskEvaluationResponseSchema(
            submission_id=submission.id,
            task_id=task.id,
            module_id=task.module_id,
            class_id=task.class_id,
            student_id=enrollment.student_id,
            enrollment_id=enrollment.id,
            evaluator_id=current_user.id,
            status=submission.status,
            max_score=task.max_score,
            final_task_score=final_task_score,
            passing_score=passing_score,
            is_approved=is_approved,
            evidence_url=submission.evidence_url,
            student_notes=submission.student_notes,
            completed_at=submission.completed_at or evaluated_at,
            evaluated_at=evaluated_at,
            evaluations=evaluations_response,
            skill_evidences=evidences_response,
        )

    @staticmethod
    def resolve_effective_submission_status(
        submission: TaskSubmission,
        *,
        due_date: datetime,
        reference_now: datetime,
    ) -> SubmissionStatus:
        """Marca dinamicamente como LATE tarefas com status PENDING cujo due_date expirou (BE-026)."""
        normalized_due = (
            due_date.replace(tzinfo=timezone.utc)
            if due_date.tzinfo is None
            else due_date.astimezone(timezone.utc)
        )
        normalized_now = (
            reference_now.replace(tzinfo=timezone.utc)
            if reference_now.tzinfo is None
            else reference_now.astimezone(timezone.utc)
        )
        if submission.status == SubmissionStatus.PENDING and normalized_due < normalized_now:
            return SubmissionStatus.LATE
        return submission.status

    @classmethod
    def _to_student_pending_task_item(
        cls,
        submission: TaskSubmission,
        *,
        effective_status: SubmissionStatus,
    ) -> StudentPendingTaskItemSchema:
        """Converte TaskSubmission + PracticalTask em StudentPendingTaskItemSchema."""
        task = submission.task
        module = task.module
        subject = module.subject
        passing_score = Decimal(module.passing_score).quantize(_DECIMAL_QUANTIZER)
        final_score = (
            Decimal(submission.final_task_score).quantize(_DECIMAL_QUANTIZER)
            if submission.final_task_score is not None
            else None
        )
        is_approved = (
            final_score >= passing_score if final_score is not None else None
        )

        criteria_schemas = [
            TaskCriterionResponseSchema(
                id=criterion.id,
                task_id=criterion.task_id,
                competency_id=criterion.competency_id,
                criterion_name=criterion.criterion_name,
                weight=criterion.weight,
                min_acceptable_level=criterion.min_acceptable_level,
                competency=TaskCriterionCompetencySummarySchema(
                    id=criterion.competency.id,
                    code=criterion.competency.code,
                    title=criterion.competency.title,
                    category=criterion.competency.category,
                ),
            )
            for criterion in task.criteria
        ]

        evaluations_schemas = [
            SubmissionCriterionEvaluationResponseSchema(
                id=ev.id,
                submission_id=ev.submission_id,
                criterion_id=ev.criterion_id,
                criterion_name=ev.criterion.criterion_name,
                competency_id=ev.criterion.competency_id,
                competency_code=ev.criterion.competency.code,
                competency_title=ev.criterion.competency.title,
                weight=ev.criterion.weight,
                min_acceptable_level=ev.criterion.min_acceptable_level,
                achieved_level=ev.achieved_level,
                meets_min_acceptable_level=(
                    ev.achieved_level >= ev.criterion.min_acceptable_level
                ),
                score_awarded=ev.score_awarded,
                technical_feedback=ev.technical_feedback,
                evaluated_at=ev.evaluated_at,
            )
            for ev in submission.evaluations
        ]

        return StudentPendingTaskItemSchema(
            id=submission.id,
            submission_id=submission.id,
            task_id=task.id,
            student_id=submission.student_id,
            enrollment_id=submission.enrollment_id,
            class_id=task.class_id,
            module_id=task.module_id,
            subject_id=module.subject_id,
            title=task.title,
            description=task.description,
            blueprint_url=task.blueprint_url,
            due_date=task.due_date,
            max_score=task.max_score,
            passing_score=passing_score,
            is_mandatory=task.is_mandatory,
            status=effective_status,
            persisted_status=submission.status,
            is_late=(effective_status == SubmissionStatus.LATE),
            is_completed=effective_status
            in (SubmissionStatus.SUBMITTED, SubmissionStatus.EVALUATED),
            final_task_score=final_score,
            is_approved=is_approved,
            evidence_url=submission.evidence_url,
            student_notes=submission.student_notes,
            completed_at=submission.completed_at,
            module=LessonModuleSummarySchema.model_validate(module),
            subject=LessonSubjectSummarySchema.model_validate(subject),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                task.academic_class
            ),
            criteria=criteria_schemas,
            evaluations=evaluations_schemas,
        )

    def list_student_pending_tasks(
        self,
        student_id: UUID,
        params: StudentPendingTasksQueryParams | None = None,
        *,
        current_user: User,
    ) -> StudentPendingTasksResponseSchema:
        """Lista tarefas práticas do aluno marcando dinamicamente LATE quando PENDING expirou e retornando contadores (BE-026)."""
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise ForbiddenException(message=STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE)

        student = self._repository.get_user_by_id(student_id)
        if student is None or student.role != UserRole.STUDENT:
            raise NotFoundException(message=STUDENT_TASKS_NOT_FOUND_MESSAGE)

        requested_class_id = params.class_id if params is not None else None
        requested_module_id = params.module_id if params is not None else None
        requested_subject_id = params.subject_id if params is not None else None
        requested_status = params.status if params is not None else None
        requested_is_mandatory = params.is_mandatory if params is not None else None
        requested_search = params.search if params is not None else None

        if requested_class_id is not None:
            academic_class = self._repository.get_class_by_id(requested_class_id)
            if academic_class is None:
                raise NotFoundException(message=PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE)
            if (
                current_user.role == UserRole.TEACHER
                and not self._repository.is_teacher_assigned_to_class(
                    teacher_id=current_user.id,
                    class_id=academic_class.id,
                )
            ):
                raise ForbiddenException(message=STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE)

        if requested_module_id is not None:
            module = self._repository.get_module_by_id(requested_module_id)
            if module is None:
                raise NotFoundException(message=PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE)

        if requested_subject_id is not None:
            subject = self._repository.get_subject_by_id(requested_subject_id)
            if subject is None:
                raise NotFoundException(message=STUDENT_TASKS_SUBJECT_NOT_FOUND_MESSAGE)

        enrollments = self._repository.list_student_enrollments(
            student.id,
            class_id=requested_class_id,
        )
        if requested_class_id is not None and not enrollments:
            raise NotFoundException(message=STUDENT_TASKS_ENROLLMENT_NOT_FOUND_MESSAGE)

        allowed_class_ids: list[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            student_class_ids = [enr.class_id for enr in enrollments]
            teacher_class_ids = self._repository.get_teacher_assigned_class_ids(
                current_user.id,
                class_ids=student_class_ids,
            )
            if not teacher_class_ids:
                raise ForbiddenException(message=STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE)
            allowed_class_ids = list(teacher_class_ids)

        submissions = self._repository.list_student_task_submissions(
            student.id,
            allowed_class_ids=allowed_class_ids,
            class_id=requested_class_id,
            module_id=requested_module_id,
            subject_id=requested_subject_id,
            is_mandatory=requested_is_mandatory,
            search=requested_search,
        )

        now = _utc_now()
        pending_count = 0
        late_count = 0
        submitted_count = 0
        evaluated_count = 0
        all_items: list[StudentPendingTaskItemSchema] = []

        for sub in submissions:
            effective_status = self.resolve_effective_submission_status(
                sub,
                due_date=sub.task.due_date,
                reference_now=now,
            )
            if effective_status == SubmissionStatus.PENDING:
                pending_count += 1
            elif effective_status == SubmissionStatus.LATE:
                late_count += 1
            elif effective_status == SubmissionStatus.SUBMITTED:
                submitted_count += 1
            elif effective_status == SubmissionStatus.EVALUATED:
                evaluated_count += 1

            all_items.append(
                self._to_student_pending_task_item(
                    sub,
                    effective_status=effective_status,
                )
            )

        completed_count = submitted_count + evaluated_count
        total_count = pending_count + late_count + completed_count

        if requested_status is not None:
            filtered_items = [
                item for item in all_items if item.status == requested_status
            ]
        else:
            filtered_items = all_items

        profile = student.profile
        student_summary = StudentAttendanceSummaryStudentSchema(
            id=student.id,
            email=student.email,
            full_name=profile.full_name if profile is not None else None,
            registration_number=(
                profile.registration_number if profile is not None else None
            ),
        )
        counts_summary = StudentTaskCountsSummarySchema(
            pending_count=pending_count,
            late_count=late_count,
            completed_count=completed_count,
            submitted_count=submitted_count,
            evaluated_count=evaluated_count,
            total_count=total_count,
        )

        return StudentPendingTasksResponseSchema(
            student_id=student.id,
            student=student_summary,
            pending_count=pending_count,
            late_count=late_count,
            completed_count=completed_count,
            submitted_count=submitted_count,
            evaluated_count=evaluated_count,
            total_count=total_count,
            summary=counts_summary,
            tasks=filtered_items,
            data=filtered_items,
        )


def get_practical_task_service(
    repository: PracticalTaskRepositoryDep,
) -> PracticalTaskService:
    """Provedor de injeção de dependência para PracticalTaskService."""
    return PracticalTaskService(repository=repository)


PracticalTaskServiceDep = Annotated[
    PracticalTaskService,
    Depends(get_practical_task_service),
]

__all__ = [
    "PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE",
    "PRACTICAL_TASK_COMPETENCY_NOT_FOUND_MESSAGE",
    "PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE",
    "PRACTICAL_TASK_INACTIVE_SUBJECT_MESSAGE",
    "PRACTICAL_TASK_MODULE_COURSE_MISMATCH_MESSAGE",
    "PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE",
    "PRACTICAL_TASK_MODULE_TEACHER_FORBIDDEN_MESSAGE",
    "PRACTICAL_TASK_NOT_FOUND_MESSAGE",
    "PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE",
    "PracticalTaskService",
    "PracticalTaskServiceDep",
    "STUDENT_TASKS_ENROLLMENT_NOT_FOUND_MESSAGE",
    "STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE",
    "STUDENT_TASKS_NOT_FOUND_MESSAGE",
    "STUDENT_TASKS_SUBJECT_NOT_FOUND_MESSAGE",
    "STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE",
    "TASK_EVALUATION_INACTIVE_ENROLLMENT_MESSAGE",
    "TASK_EVALUATION_INCOMPLETE_CRITERIA_MESSAGE",
    "TASK_EVALUATION_INVALID_CRITERION_MESSAGE",
    "TASK_EVALUATION_STUDENT_NOT_ENROLLED_MESSAGE",
    "get_practical_task_service",
]
