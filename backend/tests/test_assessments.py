"""Testes unitários e de integração para Avaliações Formativas e Lançamento de Notas (BE-027)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    CLASS_PERIOD_CLOSED_ERROR_CODE,
    CLASS_PERIOD_CLOSED_MESSAGE,
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    AcademicAssessment,
    AcademicClass,
    AuditLog,
    Base,
    Competency,
    Course,
    Enrollment,
    LearningModule,
    StudentGrade,
    Subject,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.competency_repository import CompetencyRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.academic_assessment import (
    BatchStudentGradesRequestSchema,
    StudentGradeItemInputSchema,
    validate_assessment_max_grade_pt,
    validate_assessment_title_pt,
    validate_assessment_weight_pt,
    validate_optional_recovery_grade_pt,
    validate_student_grade_value_pt,
)
from app.schemas.enums import (
    AcademicStandingStatus,
    AssessmentType,
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.academic_assessment_service import (
    ASSESSMENT_CLASS_NOT_FOUND_MESSAGE,
    ASSESSMENT_INACTIVE_CLASS_MESSAGE,
    ASSESSMENT_INACTIVE_SUBJECT_MESSAGE,
    ASSESSMENT_MODULE_NOT_FOUND_MESSAGE,
    ASSESSMENT_MODULE_SUBJECT_MISMATCH_MESSAGE,
    ASSESSMENT_NOT_FOUND_MESSAGE,
    ASSESSMENT_SUBJECT_COURSE_MISMATCH_MESSAGE,
    ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE,
    ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE,
    CLASS_AVERAGES_CLOSED_CLASS_MESSAGE,
    CLASS_AVERAGES_TEACHER_FORBIDDEN_MESSAGE,
    GRADE_EXCEEDS_MAX_GRADE_MESSAGE,
    GRADE_INACTIVE_ENROLLMENT_MESSAGE,
    GRADE_STUDENT_NOT_ENROLLED_MESSAGE,
    classify_academic_standing,
    compute_senai_effective_grade,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "assessments_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: sa.Engine) -> sessionmaker[Session]:
    """Cria a fábrica de sessões SQLAlchemy acoplada à engine isolada."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def assessments_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância FastAPI com dependências de banco e hasher sobrescritas."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher
    return application


@pytest.fixture
async def assessments_client(assessments_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=assessments_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
    full_name: str | None = None,
    registration_number: str | None = None,
) -> tuple[User, str]:
    """Cria usuário persistido no banco de testes e gera Access Token JWT."""
    with session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=full_name or f"Usuário {role.value} {suffix}",
                registration_number=registration_number
                or f"SENAI-{role.value[:3]}-{suffix.upper()}",
                phone="(11) 98888-7777",
            ),
        )
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return user, token


def test_academic_assessment_and_student_grade_orm_validations(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida regras ORM e constraints de AcademicAssessment (DB-027) e StudentGrade (DB-028)."""
    teacher, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="ormt027",
    )
    student, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="orms027",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MET-027",
            name="Técnico em Metrologia",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MET-2026-027",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-101",
            name="Metrologia Dimensional",
            workload_hours=60,
            syllabus="Paquímetro e micrômetro",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Leitura de Paquímetro e Micrômetro",
            order_index=1,
            practical_hours=30,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        enrollment = Enrollment(
            student_id=student.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(enrollment)
        session.commit()

        # Validações de erro em AcademicAssessment
        with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
            AcademicAssessment(
                class_id=academic_class.id,
                subject_id=subject.id,
                title="AB",
                application_date=date(2026, 4, 15),
            )

        with pytest.raises(ValueError, match="maior que 0.00"):
            AcademicAssessment(
                class_id=academic_class.id,
                subject_id=subject.id,
                title="Prova Teórica 01",
                weight=Decimal("0.00"),
                application_date=date(2026, 4, 15),
            )

        with pytest.raises(ValueError, match="entre 1.00 e 10.00"):
            AcademicAssessment(
                class_id=academic_class.id,
                subject_id=subject.id,
                title="Prova Teórica 01",
                max_grade=Decimal("10.50"),
                application_date=date(2026, 4, 15),
            )

        assessment = AcademicAssessment(
            class_id=academic_class.id,
            subject_id=subject.id,
            module_id=module.id,
            title="  Prova Teórica de Leitura de Paquímetro e Micrômetro  ",
            assessment_type=AssessmentType.EXAM,
            weight=Decimal("2.00"),
            application_date=date(2026, 4, 15),
            max_grade=Decimal("10.00"),
        )
        session.add(assessment)
        session.flush()
        assert assessment.title == "Prova Teórica de Leitura de Paquímetro e Micrômetro"

        # Validações de erro em StudentGrade (< 0.00 ou > 10.00)
        with pytest.raises(ValueError, match="entre 0.00 e 10.00"):
            StudentGrade(
                assessment_id=assessment.id,
                enrollment_id=enrollment.id,
                student_id=student.id,
                recorded_by=teacher.id,
                grade_value=Decimal("-0.50"),
            )

        with pytest.raises(ValueError, match="entre 0.00 e 10.00"):
            StudentGrade(
                assessment_id=assessment.id,
                enrollment_id=enrollment.id,
                student_id=student.id,
                recorded_by=teacher.id,
                grade_value=Decimal("7.00"),
                recovery_grade=Decimal("10.50"),
            )

        grade = StudentGrade(
            assessment_id=assessment.id,
            enrollment_id=enrollment.id,
            student_id=student.id,
            recorded_by=teacher.id,
            grade_value=Decimal("5.50"),
            recovery_grade=Decimal("8.00"),
            comments="  Recuperação aplicada em laboratório.  ",
        )
        session.add(grade)
        session.commit()
        assert grade.effective_grade == Decimal("8.00")

        # Constraint UNIQUE (assessment_id, student_id)
        grade_dup = StudentGrade(
            assessment_id=assessment.id,
            enrollment_id=enrollment.id,
            student_id=student.id,
            recorded_by=teacher.id,
            grade_value=Decimal("9.00"),
        )
        session.add(grade_dup)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_pydantic_validators_for_assessments_and_grades_range() -> None:
    """Valida schemas Pydantic v2 impedindo notas < 0.00 ou > 10.00 e regra de maior nota SENAI."""
    assert validate_assessment_title_pt("  Microavaliação 01  ") == "Microavaliação 01"
    assert validate_assessment_weight_pt("1.5") == Decimal("1.50")
    assert validate_assessment_max_grade_pt("10") == Decimal("10.00")
    assert validate_student_grade_value_pt("0") == Decimal("0.00")
    assert validate_student_grade_value_pt("10.00") == Decimal("10.00")
    assert validate_optional_recovery_grade_pt(None) is None
    assert validate_optional_recovery_grade_pt("8.75") == Decimal("8.75")

    # Regra pedagógica SENAI: maior nota entre grade_value e recovery_grade
    assert compute_senai_effective_grade(Decimal("4.50"), Decimal("7.50")) == (
        Decimal("7.50"),
        True,
    )
    assert compute_senai_effective_grade(Decimal("8.00"), Decimal("6.50")) == (
        Decimal("8.00"),
        False,
    )
    assert compute_senai_effective_grade(Decimal("7.00"), None) == (
        Decimal("7.00"),
        False,
    )

    # Rejeição Pydantic para nota < 0.00 ou > 10.00
    for invalid_grade in ("-0.01", -1, "10.01", 11):
        with pytest.raises(ValidationError):
            StudentGradeItemInputSchema.model_validate(
                {
                    "student_id": str(uuid4()),
                    "grade_value": invalid_grade,
                }
            )
        with pytest.raises(ValidationError):
            StudentGradeItemInputSchema.model_validate(
                {
                    "student_id": str(uuid4()),
                    "grade_value": "7.00",
                    "recovery_grade": invalid_grade,
                }
            )

    # Rejeição de student_id duplicado no mesmo lote
    dup_id = uuid4()
    with pytest.raises(ValidationError, match="student_id duplicado"):
        BatchStudentGradesRequestSchema.model_validate(
            {
                "grades": [
                    {"student_id": str(dup_id), "grade_value": "7.00"},
                    {"student_id": str(dup_id), "grade_value": "8.00"},
                ]
            }
        )


@pytest.mark.asyncio
async def test_create_assessment_and_record_batch_grades_with_senai_recovery_and_audit_logs(
    assessments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/assessments e POST /api/v1/assessments/{id}/grades: lançamento em lote, maior nota SENAI e audit_logs em retificações (BE-027)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr027",
        full_name="Prof. Avaliador Metrologia",
        registration_number="SENAI-PRF-0270",
    )
    stu_1, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu1_027",
        full_name="Aluno 01",
    )
    stu_2, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu2_027",
        full_name="Aluno 02",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-USI-027",
            name="Técnico em Usinagem Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="USI-2026-027",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-027",
            name="Metrologia Dimensional",
            workload_hours=60,
            syllabus="Instrumentos de medição",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Leitura com Micrômetro Milesimal",
            order_index=1,
            practical_hours=30,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject.id,
                    is_main_teacher=True,
                ),
                Enrollment(
                    student_id=stu_1.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_2.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    # 1. Cadastra avaliação formativa (POST /api/v1/assessments)
    create_res = await assessments_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "title": "Prova Teórica de Leitura de Paquímetro e Micrômetro",
            "assessment_type": "EXAM",
            "weight": "2.00",
            "application_date": "2026-04-15",
            "max_grade": "10.00",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    created_body = create_res.json()
    assessment_id = UUID(created_body["id"])

    assert created_body["title"] == "Prova Teórica de Leitura de Paquímetro e Micrômetro"
    assert created_body["assessment_type"] == AssessmentType.EXAM.value
    assert created_body["weight"] == "2.00"
    assert created_body["max_grade"] == "10.00"
    assert created_body["graded_students_count"] == 0

    # 2. Primeiro lançamento em lote (POST /api/v1/assessments/{id}/grades):
    # - stu_1: grade_value=4.50, recovery_grade=7.50 -> effective_grade=7.50 (is_recovery_applied=True)
    # - stu_2: grade_value=8.50, recovery_grade=None -> effective_grade=8.50 (is_recovery_applied=False)
    # Como é o primeiro lançamento (criação), nenhuma retificação deve ser registrada em audit_logs.
    batch_1_res = await assessments_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={
            "grades": [
                {
                    "student_id": str(stu_1.id),
                    "grade_value": "4.50",
                    "recovery_grade": "7.50",
                    "comments": "Recuperação paralela concluída.",
                },
                {
                    "student_id": str(stu_2.id),
                    "grade_value": "8.50",
                },
            ]
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert batch_1_res.status_code == status.HTTP_200_OK
    b1_body = batch_1_res.json()

    assert b1_body["assessment_id"] == str(assessment_id)
    assert b1_body["total_processed"] == 2
    assert b1_body["created_count"] == 2
    assert b1_body["rectified_count"] == 0

    grades_by_student = {g["student_id"]: g for g in b1_body["grades"]}
    assert grades_by_student[str(stu_1.id)]["grade_value"] == "4.50"
    assert grades_by_student[str(stu_1.id)]["recovery_grade"] == "7.50"
    assert grades_by_student[str(stu_1.id)]["effective_grade"] == "7.50"
    assert grades_by_student[str(stu_1.id)]["is_recovery_applied"] is True
    assert grades_by_student[str(stu_1.id)]["was_rectified"] is False

    assert grades_by_student[str(stu_2.id)]["grade_value"] == "8.50"
    assert grades_by_student[str(stu_2.id)]["recovery_grade"] is None
    assert grades_by_student[str(stu_2.id)]["effective_grade"] == "8.50"
    assert grades_by_student[str(stu_2.id)]["is_recovery_applied"] is False
    assert grades_by_student[str(stu_2.id)]["was_rectified"] is False

    with db_session_factory() as session:
        audit_rows_initial = list(
            session.scalars(
                select(AuditLog).where(AuditLog.entity == "student_grades")
            ).all()
        )
        assert len(audit_rows_initial) == 0

    # 3. Retificação de nota já existente:
    # - stu_1 mantém 4.50 / 7.50 (sem mudança numérica -> não gera log de retificação)
    # - stu_2 tem nota retificada de 8.50 para 9.25 (gera log em audit_logs com old_values e new_values)
    batch_2_res = await assessments_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={
            "grades": [
                {
                    "student_id": str(stu_1.id),
                    "grade_value": "4.50",
                    "recovery_grade": "7.50",
                    "comments": "Recuperação paralela concluída.",
                },
                {
                    "student_id": str(stu_2.id),
                    "grade_value": "9.25",
                    "recovery_grade": "7.00",
                    "comments": "Revisão de questão discursiva.",
                },
            ]
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert batch_2_res.status_code == status.HTTP_200_OK
    b2_body = batch_2_res.json()

    assert b2_body["total_processed"] == 2
    assert b2_body["created_count"] == 0
    assert b2_body["rectified_count"] == 1

    b2_grades = {g["student_id"]: g for g in b2_body["grades"]}
    assert b2_grades[str(stu_1.id)]["was_rectified"] is False
    assert b2_grades[str(stu_2.id)]["was_rectified"] is True
    assert b2_grades[str(stu_2.id)]["grade_value"] == "9.25"
    assert b2_grades[str(stu_2.id)]["recovery_grade"] == "7.00"
    # Como grade_value (9.25) > recovery_grade (7.00), effective_grade permanece 9.25 (regra SENAI)
    assert b2_grades[str(stu_2.id)]["effective_grade"] == "9.25"
    assert b2_grades[str(stu_2.id)]["is_recovery_applied"] is False

    # Confirma registro em audit_logs da retificação
    with db_session_factory() as session:
        audit_rows = list(
            session.scalars(
                select(AuditLog).where(AuditLog.entity == "student_grades")
            ).all()
        )
        assert len(audit_rows) == 1
        audit_entry = audit_rows[0]
        assert audit_entry.action == "STUDENT_GRADE_RECTIFIED"
        assert audit_entry.user_id == teacher.id
        assert audit_entry.old_values is not None
        assert audit_entry.new_values is not None
        assert audit_entry.old_values["student_id"] == str(stu_2.id)
        assert audit_entry.old_values["grade_value"] == "8.50"
        assert audit_entry.old_values["recovery_grade"] is None
        assert audit_entry.new_values["grade_value"] == "9.25"
        assert audit_entry.new_values["recovery_grade"] == "7.00"
        assert audit_entry.new_values["effective_grade"] == "9.25"

    # 4. Listagem de avaliações reflete graded_students_count == 2
    list_res = await assessments_client.get(
        f"/api/v1/assessments?class_id={academic_class.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1
    assert list_res.json()["data"][0]["graded_students_count"] == 2


@pytest.mark.asyncio
async def test_assessments_and_grades_reject_unenrolled_students_out_of_range_grades_and_rbac(
    assessments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida rejeição de notas < 0.0 ou > 10.0, aluno fora da turma, matrícula DROPPED, max_grade customizado e RBAC (BE-027)."""
    admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm027",
    )
    assigned_teacher, assigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchrok027",
    )
    unassigned_teacher, unassigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchrout027",
    )
    stu_active, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stuact027",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="studrop027",
    )
    stu_outsider, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stuout027",
    )

    with db_session_factory() as session:
        course_1 = CourseRepository(session).create(
            code="TEC-AUT-027",
            name="Técnico em Automação",
            description="Curso 1",
            total_hours=1200,
            is_active=True,
        )
        course_2 = CourseRepository(session).create(
            code="TEC-ELT-027",
            name="Técnico em Eletrotécnica",
            description="Curso 2",
            total_hours=1200,
            is_active=True,
        )
        active_class = AcademicClassRepository(session).create(
            course_id=course_1.id,
            code="AUT-2026-027",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        planning_class = AcademicClassRepository(session).create(
            course_id=course_1.id,
            code="AUT-PLAN-027",
            period="2026.1",
            shift=Shift.AFTERNOON,
            max_students=30,
            status=ClassStatus.PLANNING,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject_1 = SubjectRepository(session).create(
            course_id=course_1.id,
            code="CLP-027",
            name="Programação de CLP",
            workload_hours=60,
            syllabus="Ladder",
            is_active=True,
        )
        subject_2_other_course = SubjectRepository(session).create(
            course_id=course_2.id,
            code="ELT-027",
            name="Instalações Elétricas",
            workload_hours=60,
            syllabus="NBR 5410",
            is_active=True,
        )
        inactive_subject = SubjectRepository(session).create(
            course_id=course_1.id,
            code="INA-027",
            name="Disciplina Inativa",
            workload_hours=40,
            syllabus="Inativa",
            is_active=False,
        )
        mod_other_subj = LearningModuleRepository(session).create(
            subject_id=subject_2_other_course.id,
            title="Quadros de Distribuição",
            order_index=1,
            practical_hours=20,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=assigned_teacher.id,
                    class_id=active_class.id,
                    subject_id=subject_1.id,
                    is_main_teacher=True,
                ),
                Enrollment(
                    student_id=stu_active.id,
                    class_id=active_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_dropped.id,
                    class_id=active_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.DROPPED,
                ),
            ]
        )
        session.commit()

    base_assessment_payload = {
        "class_id": str(active_class.id),
        "subject_id": str(subject_1.id),
        "title": "Microavaliação de Comandos Ladder",
        "assessment_type": "MICRO_EVALUATION",
        "weight": "1.00",
        "application_date": "2026-04-20",
        "max_grade": "8.00",
    }

    # 1. RBAC na criação de avaliação: 401 sem token, 403 STUDENT e TEACHER não alocado
    assert (
        await assessments_client.post("/api/v1/assessments", json=base_assessment_payload)
    ).status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_tok in (student_token, unassigned_teacher_token):
        res_forb = await assessments_client.post(
            "/api/v1/assessments",
            json=base_assessment_payload,
            headers={"Authorization": f"Bearer {forbidden_tok}"},
        )
        assert res_forb.status_code == status.HTTP_403_FORBIDDEN

    # 2. Validações de domínio na criação: 404 (turma/disciplina/módulo inexistente) e 422 (turma inativa, disciplina inativa, curso/módulo divergente)
    res_no_cls = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "class_id": str(uuid4())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_cls.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_cls.json()["message"] == ASSESSMENT_CLASS_NOT_FOUND_MESSAGE

    res_no_subj = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "subject_id": str(uuid4())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_subj.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_subj.json()["message"] == ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE

    res_no_mod = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "module_id": str(uuid4())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_mod.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_mod.json()["message"] == ASSESSMENT_MODULE_NOT_FOUND_MESSAGE

    res_inactive_cls = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "class_id": str(planning_class.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inactive_cls.status_code == 422
    assert res_inactive_cls.json()["message"] == ASSESSMENT_INACTIVE_CLASS_MESSAGE

    res_inactive_subj = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "subject_id": str(inactive_subject.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inactive_subj.status_code == 422
    assert res_inactive_subj.json()["message"] == ASSESSMENT_INACTIVE_SUBJECT_MESSAGE

    res_course_mismatch = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "subject_id": str(subject_2_other_course.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_course_mismatch.status_code == 422
    assert (
        res_course_mismatch.json()["message"]
        == ASSESSMENT_SUBJECT_COURSE_MISMATCH_MESSAGE
    )

    res_mod_mismatch = await assessments_client.post(
        "/api/v1/assessments",
        json={**base_assessment_payload, "module_id": str(mod_other_subj.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_mod_mismatch.status_code == 422
    assert (
        res_mod_mismatch.json()["message"]
        == ASSESSMENT_MODULE_SUBJECT_MISMATCH_MESSAGE
    )

    # Cria avaliação válida com max_grade = 8.00
    create_ok = await assessments_client.post(
        "/api/v1/assessments",
        json=base_assessment_payload,
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert create_ok.status_code == status.HTTP_201_CREATED
    assessment_id = UUID(create_ok.json()["id"])

    # 3. Validação Pydantic HTTP 400 para notas < 0.00 ou > 10.00
    for bad_payload in (
        {"grades": [{"student_id": str(stu_active.id), "grade_value": "-0.50"}]},
        {"grades": [{"student_id": str(stu_active.id), "grade_value": "10.50"}]},
        {
            "grades": [
                {
                    "student_id": str(stu_active.id),
                    "grade_value": "5.00",
                    "recovery_grade": "-1.00",
                }
            ]
        },
        {
            "grades": [
                {
                    "student_id": str(stu_active.id),
                    "grade_value": "5.00",
                    "recovery_grade": "11.00",
                }
            ]
        },
    ):
        res_bad_range = await assessments_client.post(
            f"/api/v1/assessments/{assessment_id}/grades",
            json=bad_payload,
            headers={"Authorization": f"Bearer {assigned_teacher_token}"},
        )
        assert res_bad_range.status_code == status.HTTP_400_BAD_REQUEST

    # 4. Nota entre 0 e 10 mas acima do max_grade (8.00) configurado na avaliação -> HTTP 400
    res_exceed_max = await assessments_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={"grades": [{"student_id": str(stu_active.id), "grade_value": "8.50"}]},
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_exceed_max.status_code == status.HTTP_400_BAD_REQUEST
    assert res_exceed_max.json()["message"] == GRADE_EXCEEDS_MAX_GRADE_MESSAGE

    # 5. Estudante não pertencente à turma (misturado com estudante válido) -> HTTP 400 atômico (nada é gravado)
    res_unenrolled = await assessments_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={
            "grades": [
                {"student_id": str(stu_active.id), "grade_value": "7.00"},
                {"student_id": str(stu_outsider.id), "grade_value": "7.00"},
            ]
        },
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_unenrolled.status_code == status.HTTP_400_BAD_REQUEST
    assert res_unenrolled.json()["message"] == GRADE_STUDENT_NOT_ENROLLED_MESSAGE

    with db_session_factory() as session:
        saved_grades = list(
            session.scalars(
                select(StudentGrade).where(
                    StudentGrade.assessment_id == assessment_id
                )
            ).all()
        )
        assert len(saved_grades) == 0

    # 6. Matrícula trancada (DROPPED) -> HTTP 400
    res_dropped = await assessments_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={"grades": [{"student_id": str(stu_dropped.id), "grade_value": "7.00"}]},
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_dropped.status_code == status.HTTP_400_BAD_REQUEST
    assert res_dropped.json()["message"] == GRADE_INACTIVE_ENROLLMENT_MESSAGE

    # 7. RBAC e 404 no lançamento de notas
    valid_grade_payload = {
        "grades": [{"student_id": str(stu_active.id), "grade_value": "7.50"}]
    }
    assert (
        await assessments_client.post(
            f"/api/v1/assessments/{assessment_id}/grades",
            json=valid_grade_payload,
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_tok in (student_token, unassigned_teacher_token):
        assert (
            await assessments_client.post(
                f"/api/v1/assessments/{assessment_id}/grades",
                json=valid_grade_payload,
                headers={"Authorization": f"Bearer {forbidden_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    res_404 = await assessments_client.post(
        f"/api/v1/assessments/{uuid4()}/grades",
        json=valid_grade_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == ASSESSMENT_NOT_FOUND_MESSAGE


def test_classify_academic_standing_rules() -> None:
    """Valida classificação determinística APPROVED, IN_RECOVERY e AT_RISK com precisão Decimal (BE-028)."""
    # Acima da nota de corte (6.00) com boa frequência -> APPROVED / LOW
    assert classify_academic_standing(
        Decimal("7.50"),
        passing_score=Decimal("6.00"),
        attendance_rate=Decimal("92.00"),
    ) == (AcademicStandingStatus.APPROVED, RiskLevel.LOW, False)

    # Entre 4.00 e 5.99 com frequência OK -> IN_RECOVERY / MODERATE
    assert classify_academic_standing(
        Decimal("5.25"),
        passing_score=Decimal("6.00"),
        attendance_rate=Decimal("88.00"),
    ) == (AcademicStandingStatus.IN_RECOVERY, RiskLevel.MODERATE, True)

    # Abaixo de 4.00 -> AT_RISK / CRITICAL
    assert classify_academic_standing(
        Decimal("3.50"),
        passing_score=Decimal("6.00"),
        attendance_rate=Decimal("95.00"),
    ) == (AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, True)

    # Nota acima da corte mas frequência < 75% -> AT_RISK / CRITICAL
    assert classify_academic_standing(
        Decimal("8.50"),
        passing_score=Decimal("6.00"),
        attendance_rate=Decimal("70.00"),
    ) == (AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, False)

    # Sem notas ainda (None) e sem faltas críticas -> IN_RECOVERY / LOW (não abaixo da corte)
    assert classify_academic_standing(
        None,
        passing_score=Decimal("6.00"),
        attendance_rate=None,
    ) == (AcademicStandingStatus.IN_RECOVERY, RiskLevel.LOW, False)


@pytest.mark.asyncio
async def test_calculate_class_averages_and_grades_summary_weighted_decimal_precision(
    assessments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/classes/{id}/calculate-averages e GET /api/v1/classes/{id}/grades-summary combinando provas e tarefas práticas (BE-028)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="avg_tchr028",
        full_name="Prof. Fechamento Médias",
    )
    stu_approved, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="avg_a028",
        full_name="Ana Beatriz",
    )
    stu_recovery, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="avg_b028",
        full_name="Bruno Silva",
    )
    stu_at_risk, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="avg_c028",
        full_name="Carlos Souza",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="avg_d028",
        full_name="Daniel Trancado",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-USI-028",
            name="Técnico em Usinagem de Precisão",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="USI-2026-028",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-028",
            name="Tornearia e Metrologia",
            workload_hours=80,
            syllabus="Operações de bancada e medição",
            is_active=True,
        )
        # Módulo 1: peso 2.00, nota de corte 6.00
        mod_1 = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("2.00"),
            passing_score=Decimal("6.00"),
        )
        # Módulo 2: peso 1.00, nota de corte 6.00
        mod_2 = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Metrologia com Micrômetro",
            order_index=2,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-USI-028",
            title="Controle Dimensional H7",
            category=CompetencyCategory.TECHNICAL,
        )
        enr_approved = Enrollment(
            student_id=stu_approved.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("95.00"),
        )
        enr_recovery = Enrollment(
            student_id=stu_recovery.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("88.00"),
        )
        enr_at_risk = Enrollment(
            student_id=stu_at_risk.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("90.00"),
        )
        enr_dropped = Enrollment(
            student_id=stu_dropped.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.DROPPED,
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject.id,
                    is_main_teacher=True,
                ),
                enr_approved,
                enr_recovery,
                enr_at_risk,
                enr_dropped,
            ]
        )
        session.commit()
        enr_approved_id = enr_approved.id
        enr_recovery_id = enr_recovery.id
        enr_at_risk_id = enr_at_risk.id

    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Cria 2 avaliações formativas:
    # - Prova Módulo 1 (weight=2.00)
    # - Microavaliação Módulo 2 (weight=1.00)
    res_a1 = await assessments_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(mod_1.id),
            "title": "Prova Teórica Tornearia",
            "assessment_type": "EXAM",
            "weight": "2.00",
            "application_date": "2026-04-10",
            "max_grade": "10.00",
        },
        headers=headers,
    )
    assert res_a1.status_code == status.HTTP_201_CREATED
    a1_id = UUID(res_a1.json()["id"])

    res_a2 = await assessments_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(mod_2.id),
            "title": "Microavaliação Micrômetro",
            "assessment_type": "MICRO_EVALUATION",
            "weight": "1.00",
            "application_date": "2026-04-20",
            "max_grade": "10.00",
        },
        headers=headers,
    )
    assert res_a2.status_code == status.HTTP_201_CREATED
    a2_id = UUID(res_a2.json()["id"])

    # 2. Cria 1 atividade prática no Módulo 1 (weight padrão=1.00) e avalia os 3 alunos:
    res_task = await assessments_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_1.id),
            "class_id": str(academic_class.id),
            "title": "Usinagem de Eixo Escalonado",
            "due_date": "2026-04-25T18:00:00Z",
            "max_score": "10.00",
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Tolerância Dimensional ±0,02mm",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers=headers,
    )
    assert res_task.status_code == status.HTTP_201_CREATED
    task_id = UUID(res_task.json()["id"])
    crit_id = UUID(res_task.json()["criteria"][0]["id"])

    # Notas práticas (achieved_level 1..5 -> score = level * 2.00):
    # - Ana: nível 5 -> 10.00
    # - Bruno: nível 3 -> 6.00
    # - Carlos: nível 1 -> 2.00
    for stu_id, level in (
        (stu_approved.id, 5),
        (stu_recovery.id, 3),
        (stu_at_risk.id, 1),
    ):
        eval_res = await assessments_client.post(
            f"/api/v1/tasks/{task_id}/evaluations",
            json={
                "student_id": str(stu_id),
                "status": "EVALUATED",
                "evaluations": [{"criterion_id": str(crit_id), "achieved_level": level}],
            },
            headers=headers,
        )
        assert eval_res.status_code == status.HTTP_200_OK

    # 3. Lança notas formativas:
    # Módulo 1 (Prova weight=2.00 + Prática weight=1.00):
    # - Ana: grade=4.00, recovery=7.00 -> effective=7.00 => Mod1 = (7.00*2 + 10.00*1)/3 = 24/3 = 8.00
    # - Bruno: grade=4.50 => Mod1 = (4.50*2 + 6.00*1)/3 = 15/3 = 5.00
    # - Carlos: grade=2.50 => Mod1 = (2.50*2 + 2.00*1)/3 = 7/3 = 2.33
    assert (
        await assessments_client.post(
            f"/api/v1/assessments/{a1_id}/grades",
            json={
                "grades": [
                    {
                        "student_id": str(stu_approved.id),
                        "grade_value": "4.00",
                        "recovery_grade": "7.00",
                    },
                    {"student_id": str(stu_recovery.id), "grade_value": "4.50"},
                    {"student_id": str(stu_at_risk.id), "grade_value": "2.50"},
                ]
            },
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    # Módulo 2 (Microavaliação weight=1.00):
    # - Ana: 5.00 => Subject/Final = (8.00*2 + 5.00*1)/3 = 21/3 = 7.00 (APPROVED)
    # - Bruno: 5.00 => Subject/Final = (5.00*2 + 5.00*1)/3 = 15/3 = 5.00 (IN_RECOVERY)
    # - Carlos: 4.00 => Subject/Final = (2.33*2 + 4.00*1)/3 = 8.66/3 = 2.89 (AT_RISK)
    assert (
        await assessments_client.post(
            f"/api/v1/assessments/{a2_id}/grades",
            json={
                "grades": [
                    {"student_id": str(stu_approved.id), "grade_value": "5.00"},
                    {"student_id": str(stu_recovery.id), "grade_value": "5.00"},
                    {"student_id": str(stu_at_risk.id), "grade_value": "4.00"},
                ]
            },
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    # 4. GET /api/v1/classes/{id}/grades-summary (consulta read-only sem mutar enrollments.final_grade)
    summary_res = await assessments_client.get(
        f"/api/v1/classes/{academic_class.id}/grades-summary",
        headers=headers,
    )
    assert summary_res.status_code == status.HTTP_200_OK
    summary_body = summary_res.json()
    assert summary_body["persisted_to_enrollments"] is False
    assert summary_body["updated_enrollments_count"] == 0
    assert summary_body["total_students"] == 3
    assert summary_body["approved_count"] == 1
    assert summary_body["in_recovery_count"] == 1
    assert summary_body["at_risk_count"] == 1

    with db_session_factory() as session:
        assert session.get(Enrollment, enr_approved_id).final_grade is None  # type: ignore[union-attr]

    # 5. POST /api/v1/classes/{id}/calculate-averages (calcula e persiste enrollments.final_grade)
    calc_res = await assessments_client.post(
        f"/api/v1/classes/{academic_class.id}/calculate-averages",
        headers=headers,
    )
    assert calc_res.status_code == status.HTTP_200_OK
    calc_body = calc_res.json()

    assert calc_body["persisted_to_enrollments"] is True
    assert calc_body["updated_enrollments_count"] == 3
    assert calc_body["total_students"] == 3
    assert calc_body["approved_count"] == 1
    assert calc_body["in_recovery_count"] == 1
    assert calc_body["at_risk_count"] == 1
    # Média da turma: (7.00 + 5.00 + 2.89) / 3 = 14.89 / 3 = 4.96
    assert calc_body["class_average_grade"] == "4.96"

    # Ordenação alfabética: Ana Beatriz, Bruno Silva, Carlos Souza
    assert [s["student"]["full_name"] for s in calc_body["students"]] == [
        "Ana Beatriz",
        "Bruno Silva",
        "Carlos Souza",
    ]
    by_stu = {s["student_id"]: s for s in calc_body["students"]}

    ana = by_stu[str(stu_approved.id)]
    assert ana["final_grade"] == "7.00"
    assert ana["status"] == AcademicStandingStatus.APPROVED.value
    assert ana["is_below_passing_score"] is False
    assert ana["below_passing_modules_count"] == 1  # Módulo 2 = 5.00 < 6.00
    assert ana["modules"][0]["module_average"] == "8.00"
    assert ana["modules"][0]["assessments_average"] == "7.00"
    assert ana["modules"][0]["practical_tasks_average"] == "10.00"
    assert ana["modules"][0]["status"] == AcademicStandingStatus.APPROVED.value
    assert ana["modules"][1]["module_average"] == "5.00"
    assert ana["modules"][1]["status"] == AcademicStandingStatus.IN_RECOVERY.value

    bruno = by_stu[str(stu_recovery.id)]
    assert bruno["final_grade"] == "5.00"
    assert bruno["status"] == AcademicStandingStatus.IN_RECOVERY.value
    assert bruno["is_below_passing_score"] is True

    carlos = by_stu[str(stu_at_risk.id)]
    assert carlos["final_grade"] == "2.89"
    assert carlos["status"] == AcademicStandingStatus.AT_RISK.value
    assert carlos["is_below_passing_score"] is True
    assert carlos["risk_level"] == RiskLevel.CRITICAL.value

    # Confirma persistência real de final_grade em enrollments no banco
    with db_session_factory() as session:
        assert session.get(Enrollment, enr_approved_id).final_grade == Decimal("7.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_recovery_id).final_grade == Decimal("5.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_at_risk_id).final_grade == Decimal("2.89")  # type: ignore[union-attr]

    # 6. Filtro por status=AT_RISK em GET /api/v1/classes/{id}/grades-summary
    filter_res = await assessments_client.get(
        f"/api/v1/classes/{academic_class.id}/grades-summary?status=AT_RISK",
        headers=headers,
    )
    assert filter_res.status_code == status.HTTP_200_OK
    assert len(filter_res.json()["students"]) == 1
    assert filter_res.json()["students"][0]["student_id"] == str(stu_at_risk.id)


@pytest.mark.asyncio
async def test_class_averages_rbac_closed_class_and_not_found(
    assessments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida RBAC (401/403), 404 e bloqueio 422 ao tentar fechar médias de turma encerrada (BE-028)."""
    _admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm028",
    )
    _unassigned_teacher, unassigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchrout028",
    )
    _student, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu028",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-FECH-028",
            name="Técnico em Mecatrônica",
            description="Curso técnico",
            total_hours=1200,
            is_active=True,
        )
        closed_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2025-END",
            period="2025.2",
            shift=Shift.NIGHT,
            max_students=30,
            status=ClassStatus.COMPLETED,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 12, 20),
        )
        session.commit()

    # 1. Sem token -> 401
    assert (
        await assessments_client.post(
            f"/api/v1/classes/{closed_class.id}/calculate-averages"
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    # 2. STUDENT e TEACHER não alocado -> 403
    for tok in (student_token, unassigned_teacher_token):
        assert (
            await assessments_client.post(
                f"/api/v1/classes/{closed_class.id}/calculate-averages",
                headers={"Authorization": f"Bearer {tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN
        assert (
            await assessments_client.get(
                f"/api/v1/classes/{closed_class.id}/grades-summary",
                headers={"Authorization": f"Bearer {tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    # 3. Turma inexistente -> 404
    res_404 = await assessments_client.post(
        f"/api/v1/classes/{uuid4()}/calculate-averages",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == ASSESSMENT_CLASS_NOT_FOUND_MESSAGE

    # 4. POST calculate-averages em turma COMPLETED -> 422 com CLASS_PERIOD_CLOSED (BE-029), mas GET grades-summary -> 200 OK
    res_closed_post = await assessments_client.post(
        f"/api/v1/classes/{closed_class.id}/calculate-averages",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_closed_post.status_code == 422
    assert res_closed_post.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
    assert res_closed_post.json()["message"] == CLASS_PERIOD_CLOSED_MESSAGE

    res_closed_get = await assessments_client.get(
        f"/api/v1/classes/{closed_class.id}/grades-summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_closed_get.status_code == status.HTTP_200_OK
    assert res_closed_get.json()["persisted_to_enrollments"] is False

