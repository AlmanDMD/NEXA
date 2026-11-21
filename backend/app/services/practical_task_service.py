"""Serviço de domínio para Atividades Práticas de Oficina e Critérios de Tolerância (BE-024)."""

from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.practical_task import PracticalTask
from app.models.user import User
from app.repositories.practical_task_repository import (
    PracticalTaskRepository,
    PracticalTaskRepositoryDep,
)
from app.schemas.class_lesson import LessonModuleSummarySchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import ClassStatus, SubmissionStatus, UserRole
from app.schemas.practical_task import (
    PracticalTaskCreateSchema,
    PracticalTaskListQueryParams,
    PracticalTaskPaginatedResponseSchema,
    PracticalTaskResponseSchema,
    TaskCriterionCompetencySummarySchema,
    TaskCriterionResponseSchema,
)

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
    "PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE",
    "PracticalTaskService",
    "PracticalTaskServiceDep",
    "get_practical_task_service",
]
