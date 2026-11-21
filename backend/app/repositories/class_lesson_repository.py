"""Repositório SQLAlchemy 2.0 para Diário de Classe e pré-inicialização de chamada (BE-021)."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import DbSessionDep
from app.models.academic_class import AcademicClass
from app.models.base import _utc_now
from app.models.class_lesson import AttendanceRecord, ClassLesson
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.enums import AttendanceStatus, EnrollmentStatus


class ClassLessonRepository:
    """Repositório SQLAlchemy 2.0 para criação e consulta de aulas ministradas (class_lessons)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy ativa."""
        return self._session

    def get_by_id(self, lesson_id: UUID) -> ClassLesson | None:
        """Busca uma aula pelo UUID carregando docente, disciplina, módulo e registros de chamada."""
        stmt = (
            select(ClassLesson)
            .options(
                joinedload(ClassLesson.teacher).selectinload(User.profile),
                joinedload(ClassLesson.subject),
                joinedload(ClassLesson.module),
                selectinload(ClassLesson.attendance_records),
            )
            .where(ClassLesson.id == lesson_id)
        )
        return self._session.scalar(stmt)

    def get_class_by_id(self, class_id: UUID) -> AcademicClass | None:
        """Busca uma turma acadêmica pelo UUID."""
        stmt = (
            select(AcademicClass)
            .options(joinedload(AcademicClass.course))
            .where(AcademicClass.id == class_id)
        )
        return self._session.scalar(stmt)

    def get_subject_by_id(self, subject_id: UUID) -> Subject | None:
        """Busca uma disciplina técnica pelo UUID."""
        stmt = select(Subject).where(Subject.id == subject_id)
        return self._session.scalar(stmt)

    def get_module_by_id(self, module_id: UUID) -> LearningModule | None:
        """Busca um módulo de aprendizagem prática pelo UUID."""
        stmt = select(LearningModule).where(LearningModule.id == module_id)
        return self._session.scalar(stmt)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Busca um usuário pelo UUID com seu perfil carregado."""
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return self._session.scalar(stmt)

    def is_teacher_assigned_to_class_and_subject(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
    ) -> bool:
        """Verifica se o docente possui atribuição ativa para a turma e disciplina em teacher_assignments."""
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

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
    ) -> bool:
        """Verifica se o docente leciona ao menos uma disciplina na turma informada."""
        stmt = (
            select(TeacherAssignment.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def create_lesson_with_initial_attendance(
        self,
        *,
        class_id: UUID,
        subject_id: UUID,
        module_id: UUID | None,
        teacher_id: UUID,
        lesson_date: date,
        workload_hours: int,
        topic_summary: str,
        lab_environment: str | None,
    ) -> ClassLesson:
        """Persiste a aula e pré-inicializa a lista de chamada em lote para alunos ACTIVE da turma."""
        lesson = ClassLesson(
            class_id=class_id,
            subject_id=subject_id,
            module_id=module_id,
            teacher_id=teacher_id,
            lesson_date=lesson_date,
            workload_hours=workload_hours,
            topic_summary=topic_summary,
            lab_environment=lab_environment,
        )
        self._session.add(lesson)
        self._session.flush()

        active_enrollments = list(
            self._session.scalars(
                select(Enrollment).where(
                    Enrollment.class_id == class_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            ).all()
        )
        if active_enrollments:
            initial_records = [
                AttendanceRecord(
                    lesson_id=lesson.id,
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    status=AttendanceStatus.PRESENT,
                    absent_hours=0,
                )
                for enrollment in active_enrollments
            ]
            self._session.add_all(initial_records)

        self._session.commit()
        self._session.refresh(lesson)
        return self.get_by_id(lesson.id) or lesson

    def list_by_class(
        self,
        class_id: UUID,
        *,
        page: int,
        limit: int,
        subject_id: UUID | None = None,
        module_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[list[ClassLesson], int]:
        """Lista aulas da turma paginadas e ordenadas cronologicamente com filtros opcionais."""
        stmt = select(ClassLesson).where(ClassLesson.class_id == class_id)

        if subject_id is not None:
            stmt = stmt.where(ClassLesson.subject_id == subject_id)

        if module_id is not None:
            stmt = stmt.where(ClassLesson.module_id == module_id)

        if start_date is not None:
            stmt = stmt.where(ClassLesson.lesson_date >= start_date)

        if end_date is not None:
            stmt = stmt.where(ClassLesson.lesson_date <= end_date)

        total = int(self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        offset = (page - 1) * limit
        items_stmt = (
            stmt.options(
                joinedload(ClassLesson.teacher).selectinload(User.profile),
                joinedload(ClassLesson.subject),
                joinedload(ClassLesson.module),
                selectinload(ClassLesson.attendance_records),
            )
            .order_by(
                ClassLesson.lesson_date.desc(),
                ClassLesson.created_at.desc(),
                ClassLesson.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self._session.scalars(items_stmt).unique().all())
        return items, total

    def get_enrollments_by_class(self, class_id: UUID) -> dict[UUID, Enrollment]:
        """Retorna mapa {student_id: Enrollment} de todas as matrículas vinculadas à turma."""
        stmt = select(Enrollment).where(Enrollment.class_id == class_id)
        enrollments = list(self._session.scalars(stmt).all())
        return {enr.student_id: enr for enr in enrollments}

    def get_existing_attendance_by_lesson(
        self,
        lesson_id: UUID,
    ) -> dict[UUID, AttendanceRecord]:
        """Retorna mapa {student_id: AttendanceRecord} dos registros já existentes para a aula."""
        stmt = select(AttendanceRecord).where(AttendanceRecord.lesson_id == lesson_id)
        records = list(self._session.scalars(stmt).all())
        return {rec.student_id: rec for rec in records}

    def recalculate_class_enrollments_attendance_rates(
        self,
        *,
        class_id: UUID,
        student_ids: Sequence[UUID],
    ) -> dict[UUID, Decimal]:
        """Recalcula no servidor o attendance_rate consolidado em enrollments para os alunos informados."""
        target_ids = list(dict.fromkeys(student_ids))
        if not target_ids:
            return {}

        stmt = (
            select(
                AttendanceRecord.student_id,
                AttendanceRecord.status,
                AttendanceRecord.absent_hours,
                ClassLesson.workload_hours,
            )
            .join(ClassLesson, ClassLesson.id == AttendanceRecord.lesson_id)
            .where(
                ClassLesson.class_id == class_id,
                AttendanceRecord.student_id.in_(target_ids),
            )
        )
        rows = self._session.execute(stmt).all()

        totals: dict[UUID, list[int]] = {sid: [0, 0] for sid in target_ids}
        for student_id, rec_status, absent_hours, lesson_workload in rows:
            total_hours = int(lesson_workload)
            if rec_status in (AttendanceStatus.PRESENT, AttendanceStatus.JUSTIFIED):
                effective_absent = 0
            else:
                effective_absent = min(total_hours, max(0, int(absent_hours)))
            attended = max(0, total_hours - effective_absent)
            totals[student_id][0] += attended
            totals[student_id][1] += total_hours

        rates_by_student: dict[UUID, Decimal] = {}
        for sid, (attended_sum, total_sum) in totals.items():
            if total_sum <= 0:
                rate = Decimal("100.00")
            else:
                rate = (
                    (Decimal(attended_sum) * Decimal("100")) / Decimal(total_sum)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            rates_by_student[sid] = rate

        enrollments = list(
            self._session.scalars(
                select(Enrollment).where(
                    Enrollment.class_id == class_id,
                    Enrollment.student_id.in_(target_ids),
                )
            ).all()
        )
        now = _utc_now()
        for enrollment in enrollments:
            enrollment.attendance_rate = rates_by_student.get(
                enrollment.student_id,
                Decimal("100.00"),
            )
            enrollment.updated_at = now
            self._session.add(enrollment)

        return rates_by_student

    def upsert_batch_attendance(
        self,
        *,
        lesson: ClassLesson,
        normalized_items: Sequence[tuple[Enrollment, AttendanceStatus, int, str | None]],
    ) -> dict[UUID, Decimal]:
        """Executa upsert transacional em attendance_records e recalcula attendance_rate na mesma transação."""
        existing_map = self.get_existing_attendance_by_lesson(lesson.id)
        now = _utc_now()

        for enrollment, rec_status, absent_hours, justification_note in normalized_items:
            existing = existing_map.get(enrollment.student_id)
            if existing is not None:
                existing.status = rec_status
                existing.absent_hours = absent_hours
                existing.justification_note = justification_note
                existing.recorded_at = now
                self._session.add(existing)
            else:
                new_record = AttendanceRecord(
                    lesson_id=lesson.id,
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    status=rec_status,
                    absent_hours=absent_hours,
                    justification_note=justification_note,
                    recorded_at=now,
                )
                self._session.add(new_record)

        self._session.flush()
        rates_by_student = self.recalculate_class_enrollments_attendance_rates(
            class_id=lesson.class_id,
            student_ids=[enr.student_id for enr, _, _, _ in normalized_items],
        )
        self._session.commit()
        return rates_by_student


def get_class_lesson_repository(session: DbSessionDep) -> ClassLessonRepository:
    """Provedor de injeção de dependência para ClassLessonRepository."""
    return ClassLessonRepository(session=session)


ClassLessonRepositoryDep = Annotated[
    ClassLessonRepository,
    Depends(get_class_lesson_repository),
]

__all__ = [
    "ClassLessonRepository",
    "ClassLessonRepositoryDep",
    "get_class_lesson_repository",
]
