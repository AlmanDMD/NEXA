"""Testes unitários e de integração para Atividades Práticas e Critérios de Tolerância (BE-024)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timezone
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
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    AcademicClass,
    Base,
    Competency,
    Course,
    Enrollment,
    LearningModule,
    ModuleCompetency,
    PracticalTask,
    SkillEvidence,
    Subject,
    SubmissionEvaluation,
    TaskCriterion,
    TaskSubmission,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.competency_repository import CompetencyRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import (
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    Shift,
    SubmissionStatus,
    UserRole,
)
from app.schemas.practical_task import (
    PracticalTaskCreateSchema,
    validate_blueprint_url_pt,
    validate_practical_task_due_date_pt,
    validate_practical_task_max_score_pt,
    validate_practical_task_title_pt,
    validate_task_criterion_name_pt,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.practical_task_service import (
    PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE,
    PRACTICAL_TASK_COMPETENCY_NOT_FOUND_MESSAGE,
    PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE,
    PRACTICAL_TASK_INACTIVE_SUBJECT_MESSAGE,
    PRACTICAL_TASK_MODULE_COURSE_MISMATCH_MESSAGE,
    PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE,
    PRACTICAL_TASK_MODULE_TEACHER_FORBIDDEN_MESSAGE,
    PRACTICAL_TASK_NOT_FOUND_MESSAGE,
    PRACTICAL_TASK_TEACHER_FORBIDDEN_MESSAGE,
    STUDENT_TASKS_ENROLLMENT_NOT_FOUND_MESSAGE,
    STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE,
    STUDENT_TASKS_NOT_FOUND_MESSAGE,
    STUDENT_TASKS_SUBJECT_NOT_FOUND_MESSAGE,
    STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE,
    TASK_EVALUATION_INACTIVE_ENROLLMENT_MESSAGE,
    TASK_EVALUATION_INCOMPLETE_CRITERIA_MESSAGE,
    TASK_EVALUATION_INVALID_CRITERION_MESSAGE,
    TASK_EVALUATION_STUDENT_NOT_ENROLLED_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "practical_tasks_test.db"
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
def tasks_app(
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
async def tasks_client(tasks_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=tasks_app)
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


def test_practical_task_criteria_and_submission_orm_validations(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida regras ORM e constraints de PracticalTask (DB-023), TaskCriterion (DB-024) e TaskSubmission (DB-025)."""
    student, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="ormtask01",
    )
    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-USI-024",
            name="Técnico em Usinagem Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="USI-2026-1T",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-101",
            name="Tornearia Mecânica",
            workload_hours=80,
            syllabus="Torneamento cilíndrico e cônico",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia de Precisão",
            order_index=1,
            practical_hours=40,
            description="Operação de torno",
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-TOR-024",
            title="Controle Dimensional com Micrômetro",
            category=CompetencyCategory.TECHNICAL,
            description="Tolerância ISO H7",
        )
        enrollment = Enrollment(
            student_id=student.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(enrollment)
        session.commit()

        # Validações de erro em PracticalTask
        with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
            PracticalTask(
                module_id=module.id,
                class_id=academic_class.id,
                title="AB",
                due_date=datetime(2026, 4, 15, 18, 0, tzinfo=timezone.utc),
            )

        with pytest.raises(ValueError, match="entre 1.00 e 10.00"):
            PracticalTask(
                module_id=module.id,
                class_id=academic_class.id,
                title="Eixo Escalonado H7",
                due_date=datetime(2026, 4, 15, 18, 0, tzinfo=timezone.utc),
                max_score=Decimal("0.50"),
            )

        with pytest.raises(ValueError, match="iniciando com http:// ou https://"):
            PracticalTask(
                module_id=module.id,
                class_id=academic_class.id,
                title="Eixo Escalonado H7",
                due_date=datetime(2026, 4, 15, 18, 0, tzinfo=timezone.utc),
                blueprint_url="ftp://desenho.invalido/eixo.pdf",
            )

        task = PracticalTask(
            module_id=module.id,
            class_id=academic_class.id,
            title="  Usinagem de Eixo Escalonado Ø25mm H7  ",
            description="  Peça prática em aço SAE 1045  ",
            blueprint_url="https://cdn.senai.br/blueprints/eixo-h7.pdf",
            due_date=datetime(2026, 4, 15, 18, 0, tzinfo=timezone.utc),
            max_score=Decimal("10.00"),
            is_mandatory=True,
        )
        session.add(task)
        session.flush()
        assert task.title == "Usinagem de Eixo Escalonado Ø25mm H7"

        # Validações de erro em TaskCriterion
        with pytest.raises(ValueError, match="entre 1 e 5"):
            TaskCriterion(
                task_id=task.id,
                competency_id=comp.id,
                criterion_name="Tolerância Dimensional ±0,02mm",
                weight=Decimal("1.00"),
                min_acceptable_level=6,
            )

        criterion = TaskCriterion(
            task_id=task.id,
            competency_id=comp.id,
            criterion_name="  Tolerância Dimensional ±0,02mm no Micrômetro  ",
            weight=Decimal("2.00"),
            min_acceptable_level=4,
        )
        session.add(criterion)

        sub1 = TaskSubmission(
            task_id=task.id,
            student_id=student.id,
            enrollment_id=enrollment.id,
            status=SubmissionStatus.PENDING,
        )
        session.add(sub1)
        session.commit()

        # Constraint UNIQUE (task_id, student_id)
        sub_dup = TaskSubmission(
            task_id=task.id,
            student_id=student.id,
            enrollment_id=enrollment.id,
            status=SubmissionStatus.PENDING,
        )
        session.add(sub_dup)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_pydantic_validators_for_practical_tasks_and_criteria() -> None:
    """Valida schemas e validadores Pydantic v2 para criação de tarefa prática e rubricas."""
    assert validate_practical_task_title_pt("  Torneamento Cilíndrico  ") == "Torneamento Cilíndrico"
    assert validate_task_criterion_name_pt("  Acabamento Superficial Ra 1,6  ") == "Acabamento Superficial Ra 1,6"
    assert validate_blueprint_url_pt("https://senai.br/folha.pdf") == "https://senai.br/folha.pdf"
    assert validate_blueprint_url_pt("   ") is None
    assert validate_practical_task_max_score_pt("8.5") == Decimal("8.50")

    dt_from_date = validate_practical_task_due_date_pt("2026-05-10")
    assert dt_from_date.year == 2026 and dt_from_date.month == 5 and dt_from_date.day == 10

    # Suporta tanto 'criteria' quanto 'task_criteria'
    comp_id = uuid4()
    schema_via_alias = PracticalTaskCreateSchema.model_validate(
        {
            "module_id": str(uuid4()),
            "class_id": str(uuid4()),
            "title": "Usinagem de Bucha Guia",
            "due_date": "2026-05-15T18:00:00Z",
            "task_criteria": [
                {
                    "competency_id": str(comp_id),
                    "criterion_name": "Tolerância Interna H7",
                    "weight": "1.50",
                    "min_acceptable_level": 3,
                }
            ],
        }
    )
    assert len(schema_via_alias.criteria) == 1
    assert schema_via_alias.criteria[0].weight == Decimal("1.50")

    # Rejeita critérios com nomes duplicados no mesmo payload
    with pytest.raises(ValidationError, match="nomes duplicados"):
        PracticalTaskCreateSchema.model_validate(
            {
                "module_id": str(uuid4()),
                "class_id": str(uuid4()),
                "title": "Usinagem de Bucha Guia",
                "due_date": "2026-05-15T18:00:00Z",
                "criteria": [
                    {
                        "competency_id": str(comp_id),
                        "criterion_name": "Tolerância Interna H7",
                    },
                    {
                        "competency_id": str(comp_id),
                        "criterion_name": "tolerância interna h7",
                    },
                ],
            }
        )


@pytest.mark.asyncio
async def test_create_practical_task_validates_competencies_and_generates_pending_submissions(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/practical-tasks: cria rubricas, valida competências e gera submissões PENDING (BE-024)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="create024",
        full_name="Instrutor Tornearia",
        registration_number="SENAI-PRF-0240",
    )
    stu_active_1, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu1_024",
    )
    stu_active_2, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu2_024",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="studrop_024",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-024",
            name="Técnico em Mecânica de Precisão",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-024",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="USI-024",
            name="Usinagem em Torno e Fresadora",
            workload_hours=80,
            syllabus="Operações de bancada e usinagem",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia Cilíndrica e Faceamento",
            order_index=1,
            practical_hours=40,
            description="Módulo prático de tornearia",
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp_dim = CompetencyRepository(session).create(
            code="COMP-DIM-024",
            title="Controle Dimensional com Micrômetro Externo",
            category=CompetencyCategory.TECHNICAL,
            description="Tolerância ±0,02mm",
        )
        comp_seg = CompetencyRepository(session).create(
            code="COMP-NR12-024",
            title="Segurança Operacional NR-12 em Torno Mecânico",
            category=CompetencyCategory.SAFETY,
            description="Uso de EPI e proteções",
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
                    student_id=stu_active_1.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_active_2.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_dropped.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.DROPPED,
                ),
            ]
        )
        session.commit()

    # 1. Competência inexistente nas rubricas -> HTTP 404 Not Found e rollback integral
    bad_comp_res = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Peça com Competência Inexistente",
            "due_date": "2026-04-25T18:00:00Z",
            "criteria": [
                {
                    "competency_id": str(comp_dim.id),
                    "criterion_name": "Medição de Diâmetro Externo",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                },
                {
                    "competency_id": str(uuid4()),
                    "criterion_name": "Rubrica Inválida",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert bad_comp_res.status_code == status.HTTP_404_NOT_FOUND
    assert bad_comp_res.json()["message"] == PRACTICAL_TASK_COMPETENCY_NOT_FOUND_MESSAGE

    # 2. Criação válida com 2 rubricas -> HTTP 201 Created e 2 entregas PENDING (apenas alunos ACTIVE)
    create_res = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Usinagem de Eixo Escalonado Ø25mm H7",
            "description": "Faceamento, desbaste e acabamento com tolerância H7.",
            "blueprint_url": "https://cdn.senai.br/blueprints/eixo-escalonado-25h7.pdf",
            "due_date": "2026-04-25T18:00:00Z",
            "max_score": "10.00",
            "is_mandatory": True,
            "task_criteria": [
                {
                    "competency_id": str(comp_dim.id),
                    "criterion_name": "Tolerância Dimensional ±0,02mm no Micrômetro",
                    "weight": "2.00",
                    "min_acceptable_level": 4,
                },
                {
                    "competency_id": str(comp_seg.id),
                    "criterion_name": "Procedimento de Segurança NR-12 e Uso de Óculos/EPI",
                    "weight": "1.00",
                    "min_acceptable_level": 5,
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    body = create_res.json()
    task_id = UUID(body["id"])

    assert body["title"] == "Usinagem de Eixo Escalonado Ø25mm H7"
    assert body["module_id"] == str(module.id)
    assert body["class_id"] == str(academic_class.id)
    assert body["max_score"] == "10.00"
    assert body["is_mandatory"] is True
    assert body["initialized_submissions_count"] == 2
    assert body["total_submissions_count"] == 2
    assert body["pending_submissions_count"] == 2
    assert body["completed_submissions_count"] == 0
    assert len(body["criteria"]) == 2
    assert len(body["task_criteria"]) == 2

    # Verifica registros persistidos em task_submissions e vínculo em module_competencies no banco
    with db_session_factory() as session:
        subs = list(
            session.scalars(
                select(TaskSubmission).where(TaskSubmission.task_id == task_id)
            ).all()
        )
        assert len(subs) == 2
        assert {sub.student_id for sub in subs} == {stu_active_1.id, stu_active_2.id}
        assert all(sub.status == SubmissionStatus.PENDING for sub in subs)

        mod_links = list(
            session.scalars(
                select(ModuleCompetency).where(ModuleCompetency.module_id == module.id)
            ).all()
        )
        assert {link.competency_id for link in mod_links} == {comp_dim.id, comp_seg.id}


@pytest.mark.asyncio
async def test_list_module_practical_tasks_filters_rbac_and_domain_errors(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/modules/{module_id}/practical-tasks, filtros, RBAC docente e erros 401/403/404/422."""
    admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm024",
    )
    assigned_teacher, assigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_ok_024",
    )
    unassigned_teacher, unassigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_out_024",
    )
    _student, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu_rbac_024",
    )

    with db_session_factory() as session:
        course_1 = CourseRepository(session).create(
            code="TEC-AUT-024",
            name="Técnico em Automação",
            description="Curso 1",
            total_hours=1200,
            is_active=True,
        )
        course_2 = CourseRepository(session).create(
            code="TEC-ELT-024",
            name="Técnico em Eletrotécnica",
            description="Curso 2",
            total_hours=1200,
            is_active=True,
        )
        active_class = AcademicClassRepository(session).create(
            course_id=course_1.id,
            code="AUT-2026-1A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        planning_class = AcademicClassRepository(session).create(
            course_id=course_1.id,
            code="AUT-2026-1P",
            period="2026.1",
            shift=Shift.AFTERNOON,
            max_students=30,
            status=ClassStatus.PLANNING,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        other_course_class = AcademicClassRepository(session).create(
            course_id=course_2.id,
            code="ELT-2026-1A",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course_1.id,
            code="MET-024",
            name="Metrologia Dimensional",
            workload_hours=60,
            syllabus="Paquímetro e micrômetro",
            is_active=True,
        )
        inactive_subject = SubjectRepository(session).create(
            course_id=course_1.id,
            code="INA-024",
            name="Disciplina Inativa",
            workload_hours=40,
            syllabus="Inativa",
            is_active=False,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Metrologia de Bancada",
            order_index=1,
            practical_hours=30,
            description="Leitura com paquímetro e relógio comparador",
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        inactive_subj_module = LearningModule(
            subject_id=inactive_subject.id,
            title="Módulo de Disciplina Inativa",
            order_index=1,
            practical_hours=20,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        session.add(inactive_subj_module)
        comp = CompetencyRepository(session).create(
            code="COMP-PAQ-024",
            title="Medição com Paquímetro Universal 0,02mm",
            category=CompetencyCategory.TECHNICAL,
            description="Medição externa, interna e profundidade",
        )
        session.add(
            TeacherAssignment(
                teacher_id=assigned_teacher.id,
                class_id=active_class.id,
                subject_id=subject.id,
                is_main_teacher=True,
            )
        )
        session.commit()
        inactive_mod_id = inactive_subj_module.id

    base_payload = {
        "module_id": str(module.id),
        "class_id": str(active_class.id),
        "title": "Controle Dimensional de Flange com Paquímetro",
        "due_date": "2026-04-10T18:00:00Z",
        "max_score": "10.00",
        "is_mandatory": True,
        "criteria": [
            {
                "competency_id": str(comp.id),
                "criterion_name": "Precisão de Leitura ±0,02mm",
                "weight": "1.00",
                "min_acceptable_level": 3,
            }
        ],
    }

    # 1. RBAC: 401 sem token, 403 STUDENT e TEACHER não alocado
    assert (await tasks_client.post("/api/v1/practical-tasks", json=base_payload)).status_code == status.HTTP_401_UNAUTHORIZED
    for forbidden_tok in (student_token, unassigned_teacher_token):
        assert (
            await tasks_client.post(
                "/api/v1/practical-tasks",
                json=base_payload,
                headers={"Authorization": f"Bearer {forbidden_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN
        assert (
            await tasks_client.get(
                f"/api/v1/modules/{module.id}/practical-tasks",
                headers={"Authorization": f"Bearer {forbidden_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    # 2. Erros 404 (módulo/turma inexistentes) e 422 (turma inativa, disciplina inativa, curso divergente)
    res_no_mod = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "module_id": str(uuid4())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_mod.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_mod.json()["message"] == PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE

    res_no_cls = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "class_id": str(uuid4())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_cls.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_cls.json()["message"] == PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE

    res_inactive_cls = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "class_id": str(planning_class.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inactive_cls.status_code == 422
    assert res_inactive_cls.json()["message"] == PRACTICAL_TASK_INACTIVE_CLASS_MESSAGE

    res_inactive_subj = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "module_id": str(inactive_mod_id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inactive_subj.status_code == 422
    assert res_inactive_subj.json()["message"] == PRACTICAL_TASK_INACTIVE_SUBJECT_MESSAGE

    res_mismatch_course = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "class_id": str(other_course_class.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_mismatch_course.status_code == 422
    assert (
        res_mismatch_course.json()["message"]
        == PRACTICAL_TASK_MODULE_COURSE_MISMATCH_MESSAGE
    )

    # 3. Cria 2 tarefas no módulo e valida listagem ordenada por due_date e filtro search
    res_t1 = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "title": "Tarefa 02 - Relógio Comparador", "due_date": "2026-04-20T18:00:00Z"},
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_t1.status_code == status.HTTP_201_CREATED

    res_t2 = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={**base_payload, "title": "Tarefa 01 - Paquímetro Universal", "due_date": "2026-04-10T18:00:00Z", "is_mandatory": False},
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_t2.status_code == status.HTTP_201_CREATED

    list_res = await tasks_client.get(
        f"/api/v1/modules/{module.id}/practical-tasks",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert list_res.status_code == status.HTTP_200_OK
    list_body = list_res.json()
    assert list_body["total"] == 2
    assert list_body["data"][0]["title"] == "Tarefa 01 - Paquímetro Universal"
    assert list_body["data"][1]["title"] == "Tarefa 02 - Relógio Comparador"

    # Filtro por search e is_mandatory
    search_res = await tasks_client.get(
        f"/api/v1/modules/{module.id}/practical-tasks?search=Comparador&is_mandatory=true",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert search_res.status_code == status.HTTP_200_OK
    assert search_res.json()["total"] == 1
    assert search_res.json()["data"][0]["title"] == "Tarefa 02 - Relógio Comparador"


@pytest.mark.asyncio
async def test_evaluate_practical_task_weighted_score_and_skill_evidences(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/tasks/{id}/evaluations: nota ponderada no servidor, task_submissions e skill_evidences (BE-025)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="eval025",
        full_name="Instrutor Avaliador",
        registration_number="SENAI-PRF-0250",
    )
    student, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stueval025",
        full_name="Gabriel Rocha",
        registration_number="SENAI-ALU-0251",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-USI-025",
            name="Técnico em Usinagem CNC",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="CNC-2026-1M",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-025",
            name="Tornearia de Precisão",
            workload_hours=80,
            syllabus="Torneamento e controle dimensional",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Usinagem de Eixos e Buchas",
            order_index=1,
            practical_hours=40,
            description="Bancada de tornearia",
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp_dim = CompetencyRepository(session).create(
            code="COMP-DIM-025",
            title="Tolerância Dimensional ISO H7",
            category=CompetencyCategory.TECHNICAL,
            description="Controle com micrômetro externo",
        )
        comp_acab = CompetencyRepository(session).create(
            code="COMP-ACAB-025",
            title="Acabamento Superficial e Rugosidade",
            category=CompetencyCategory.PROCEDURAL,
            description="Acabamento Ra 1,6",
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
                    student_id=student.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    create_res = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Eixo Escalonado com Rosca M16",
            "due_date": "2026-04-30T18:00:00Z",
            "max_score": "10.00",
            "is_mandatory": True,
            "criteria": [
                {
                    "competency_id": str(comp_dim.id),
                    "criterion_name": "Tolerância Dimensional ±0,02mm",
                    "weight": "2.00",
                    "min_acceptable_level": 4,
                },
                {
                    "competency_id": str(comp_acab.id),
                    "criterion_name": "Rugosidade e Acabamento Superficial",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    created_task = create_res.json()
    task_id = UUID(created_task["id"])
    criteria_by_comp = {
        c["competency_id"]: UUID(c["id"]) for c in created_task["criteria"]
    }
    crit_dim_id = criteria_by_comp[str(comp_dim.id)]
    crit_acab_id = criteria_by_comp[str(comp_acab.id)]

    # 1. Avaliação pelo docente:
    # Critério 1 (peso 2.00): achieved_level=5 -> score_awarded=10.00
    # Critério 2 (peso 1.00): achieved_level=2 -> score_awarded=4.00
    # Nota final ponderada no servidor: (10.00*2 + 4.00*1) / 3 = 8.00
    eval_res = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={
            "student_id": str(student.id),
            "status": "EVALUATED",
            "evidence_url": "https://cdn.senai.br/evidences/peca-gabriel.jpg",
            "evaluations": [
                {
                    "criterion_id": str(crit_dim_id),
                    "achieved_level": 5,
                    "technical_feedback": "Medida exata de 25,00mm no micrômetro.",
                },
                {
                    "criterion_id": str(crit_acab_id),
                    "achieved_level": 2,
                    "technical_feedback": "Vibrado leve no passe de acabamento.",
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert eval_res.status_code == status.HTTP_200_OK
    eval_body = eval_res.json()

    assert eval_body["task_id"] == str(task_id)
    assert eval_body["student_id"] == str(student.id)
    assert eval_body["evaluator_id"] == str(teacher.id)
    assert eval_body["status"] == SubmissionStatus.EVALUATED.value
    assert eval_body["max_score"] == "10.00"
    assert eval_body["final_task_score"] == "8.00"
    assert eval_body["passing_score"] == "6.00"
    assert eval_body["is_approved"] is True
    assert len(eval_body["evaluations"]) == 2
    assert len(eval_body["skill_evidences"]) == 2

    evals_by_crit = {e["criterion_id"]: e for e in eval_body["evaluations"]}
    assert evals_by_crit[str(crit_dim_id)]["score_awarded"] == "10.00"
    assert evals_by_crit[str(crit_dim_id)]["meets_min_acceptable_level"] is True
    assert evals_by_crit[str(crit_acab_id)]["score_awarded"] == "4.00"
    assert evals_by_crit[str(crit_acab_id)]["meets_min_acceptable_level"] is False

    evidences_by_comp = {se["competency_id"]: se for se in eval_body["skill_evidences"]}
    assert evidences_by_comp[str(comp_dim.id)]["verified_level"] == "5.00"
    assert evidences_by_comp[str(comp_dim.id)]["verified_by"] == str(teacher.id)
    assert evidences_by_comp[str(comp_acab.id)]["verified_level"] == "2.00"

    # 2. Reavaliação idempotente (upsert sem duplicar submission_evaluations ou skill_evidences)
    reeval_res = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={
            "student_id": str(student.id),
            "status": "EVALUATED",
            "evaluations": [
                {
                    "criterion_id": str(crit_dim_id),
                    "achieved_level": 5,
                    "technical_feedback": "Mantido nível 5.",
                },
                {
                    "criterion_id": str(crit_acab_id),
                    "achieved_level": 5,
                    "technical_feedback": "Retrabalho concluído com ótimo acabamento.",
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert reeval_res.status_code == status.HTTP_200_OK
    assert reeval_res.json()["final_task_score"] == "10.00"

    with db_session_factory() as session:
        sub_row = session.scalar(
            select(TaskSubmission).where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.student_id == student.id,
            )
        )
        assert sub_row is not None
        assert sub_row.status == SubmissionStatus.EVALUATED
        assert sub_row.final_task_score == Decimal("10.00")

        eval_rows = list(
            session.scalars(
                select(SubmissionEvaluation).where(
                    SubmissionEvaluation.submission_id == sub_row.id
                )
            ).all()
        )
        assert len(eval_rows) == 2

        evidence_rows = list(
            session.scalars(
                select(SkillEvidence).where(
                    SkillEvidence.source_submission_id == sub_row.id
                )
            ).all()
        )
        assert len(evidence_rows) == 2
        assert all(ev.verified_level == Decimal("5.00") for ev in evidence_rows)

    # 3. Contador completed_submissions_count na listagem do módulo reflete a entrega avaliada
    list_res = await tasks_client.get(
        f"/api/v1/modules/{module.id}/practical-tasks",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_res.status_code == status.HTTP_200_OK
    task_summary = list_res.json()["data"][0]
    assert task_summary["completed_submissions_count"] == 1
    assert task_summary["pending_submissions_count"] == 0


@pytest.mark.asyncio
async def test_evaluate_practical_task_rejects_client_score_manipulation_invalid_criteria_and_rbac(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida rejeição de manipulação de nota pelo cliente, critérios incompletos, matrícula inativa e RBAC (BE-025)."""
    admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="admeval025",
    )
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchrok025",
    )
    other_teacher, other_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchrout025",
    )
    stu_active, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stuact025",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="studrop025",
    )
    stu_unenrolled, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stuout025",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MET-025",
            name="Técnico em Metrologia",
            description="Curso técnico",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MET-2026-1A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="CAL-025",
            name="Calibração Dimensional",
            workload_hours=60,
            syllabus="Blocos padrão",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Calibração de Micrômetros",
            order_index=1,
            practical_hours=30,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp_1 = CompetencyRepository(session).create(
            code="COMP-CAL-01",
            title="Aferição com Blocos Padrão",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_2 = CompetencyRepository(session).create(
            code="COMP-CAL-02",
            title="Registro de Incerteza de Medição",
            category=CompetencyCategory.PROCEDURAL,
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
                    student_id=stu_active.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_dropped.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.DROPPED,
                ),
            ]
        )
        session.commit()

    create_res = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Calibração de Micrômetro 0-25mm",
            "due_date": "2026-05-05T18:00:00Z",
            "criteria": [
                {
                    "competency_id": str(comp_1.id),
                    "criterion_name": "Paralelismo das Faces de Medição",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                },
                {
                    "competency_id": str(comp_2.id),
                    "criterion_name": "Preenchimento da Folha de Calibração",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                },
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    task_data = create_res.json()
    task_id = UUID(task_data["id"])
    crit_1_id = UUID(task_data["criteria"][0]["id"])
    crit_2_id = UUID(task_data["criteria"][1]["id"])

    valid_eval_payload = {
        "student_id": str(stu_active.id),
        "status": "EVALUATED",
        "evaluations": [
            {"criterion_id": str(crit_1_id), "achieved_level": 4},
            {"criterion_id": str(crit_2_id), "achieved_level": 4},
        ],
    }

    # 1. Cliente tentando manipular final_task_score ou score_awarded -> HTTP 400 (extra="forbid")
    res_manipulated = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={**valid_eval_payload, "final_task_score": "10.00"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_manipulated.status_code == status.HTTP_400_BAD_REQUEST

    # 2. Critérios incompletos ou criterion_id estranho à tarefa -> HTTP 400
    res_incomplete = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={
            "student_id": str(stu_active.id),
            "status": "EVALUATED",
            "evaluations": [{"criterion_id": str(crit_1_id), "achieved_level": 4}],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_incomplete.status_code == status.HTTP_400_BAD_REQUEST
    assert res_incomplete.json()["message"] == TASK_EVALUATION_INCOMPLETE_CRITERIA_MESSAGE

    res_foreign_crit = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={
            "student_id": str(stu_active.id),
            "status": "EVALUATED",
            "evaluations": [
                {"criterion_id": str(crit_1_id), "achieved_level": 4},
                {"criterion_id": str(uuid4()), "achieved_level": 4},
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_foreign_crit.status_code == status.HTTP_400_BAD_REQUEST
    assert res_foreign_crit.json()["message"] == TASK_EVALUATION_INVALID_CRITERION_MESSAGE

    # 3. Estudante não matriculado ou com matrícula DROPPED -> HTTP 400
    res_unenrolled = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={**valid_eval_payload, "student_id": str(stu_unenrolled.id)},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_unenrolled.status_code == status.HTTP_400_BAD_REQUEST
    assert res_unenrolled.json()["message"] == TASK_EVALUATION_STUDENT_NOT_ENROLLED_MESSAGE

    res_dropped = await tasks_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={**valid_eval_payload, "student_id": str(stu_dropped.id)},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_dropped.status_code == status.HTTP_400_BAD_REQUEST
    assert res_dropped.json()["message"] == TASK_EVALUATION_INACTIVE_ENROLLMENT_MESSAGE

    # 4. RBAC e 404: 401 sem token, 403 STUDENT e docente não alocado, 404 tarefa inexistente
    assert (
        await tasks_client.post(f"/api/v1/tasks/{task_id}/evaluations", json=valid_eval_payload)
    ).status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_tok in (student_token, other_teacher_token):
        assert (
            await tasks_client.post(
                f"/api/v1/tasks/{task_id}/evaluations",
                json=valid_eval_payload,
                headers={"Authorization": f"Bearer {forbidden_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    res_404 = await tasks_client.post(
        f"/api/v1/tasks/{uuid4()}/evaluations",
        json=valid_eval_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == PRACTICAL_TASK_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_list_student_pending_tasks_dynamic_late_counts_sorting_and_filters(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/students/{id}/pending-tasks: LATE dinâmico, contadores resumidos, ordenação por due_date e filtros (BE-026)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="pend026",
        full_name="Instrutor Oficina",
        registration_number="SENAI-PRF-0260",
    )
    student, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stupend026",
        full_name="Mariana Costa",
        registration_number="SENAI-ALU-0261",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-USI-026",
            name="Técnico em Usinagem Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="USI-2026-026",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject_tor = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-026",
            name="Tornearia Mecânica",
            workload_hours=80,
            syllabus="Torneamento",
            is_active=True,
        )
        subject_fre = SubjectRepository(session).create(
            course_id=course.id,
            code="FRE-026",
            name="Fresamento Universal",
            workload_hours=80,
            syllabus="Fresamento",
            is_active=True,
        )
        mod_tor = LearningModuleRepository(session).create(
            subject_id=subject_tor.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_fre = LearningModuleRepository(session).create(
            subject_id=subject_fre.id,
            title="Fresamento de Rasgos e Chavetas",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-DIM-026",
            title="Controle Dimensional de Bancada",
            category=CompetencyCategory.TECHNICAL,
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject_tor.id,
                    is_main_teacher=True,
                ),
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject_fre.id,
                    is_main_teacher=True,
                ),
                Enrollment(
                    student_id=student.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    # Cria 4 atividades práticas fora de ordem cronológica para validar ordenação por due_date ascendente:
    # 1) Tarefa com due_date no passado (2020-03-10) e status PENDING no banco -> deve virar LATE dinamicamente
    # 2) Tarefa com due_date no passado (2020-02-15) que será avaliada pelo docente -> status EVALUATED (completed)
    # 3) Tarefa com due_date no futuro (2030-05-20) que será marcada como SUBMITTED -> status SUBMITTED (completed)
    # 4) Tarefa com due_date no futuro (2030-04-10) e status PENDING -> permanece PENDING
    res_late = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_tor.id),
            "class_id": str(academic_class.id),
            "title": "Peça 02 - Eixo com Prazo Expirado",
            "due_date": "2020-03-10T18:00:00Z",
            "is_mandatory": True,
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Tolerância Externa H7",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_late.status_code == status.HTTP_201_CREATED
    task_late_id = UUID(res_late.json()["id"])

    res_eval_task = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_tor.id),
            "class_id": str(academic_class.id),
            "title": "Peça 01 - Bucha Avaliada",
            "due_date": "2020-02-15T18:00:00Z",
            "is_mandatory": True,
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Diâmetro Interno H7",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_eval_task.status_code == status.HTTP_201_CREATED
    task_eval_data = res_eval_task.json()
    task_eval_id = UUID(task_eval_data["id"])
    crit_eval_id = UUID(task_eval_data["criteria"][0]["id"])

    # Avalia a Peça 01 (status -> EVALUATED)
    eval_res = await tasks_client.post(
        f"/api/v1/tasks/{task_eval_id}/evaluations",
        json={
            "student_id": str(student.id),
            "status": "EVALUATED",
            "evaluations": [{"criterion_id": str(crit_eval_id), "achieved_level": 4}],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert eval_res.status_code == status.HTTP_200_OK

    res_sub_task = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_fre.id),
            "class_id": str(academic_class.id),
            "title": "Peça 04 - Chaveta Entregue",
            "due_date": "2030-05-20T18:00:00Z",
            "is_mandatory": False,
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Largura do Rasgo de Chaveta",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_sub_task.status_code == status.HTTP_201_CREATED
    task_sub_id = UUID(res_sub_task.json()["id"])

    # Atualiza a submissão da Peça 04 para SUBMITTED no banco
    with db_session_factory() as session:
        sub_row = session.scalar(
            select(TaskSubmission).where(
                TaskSubmission.task_id == task_sub_id,
                TaskSubmission.student_id == student.id,
            )
        )
        assert sub_row is not None
        sub_row.status = SubmissionStatus.SUBMITTED
        sub_row.completed_at = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
        session.add(sub_row)
        session.commit()

    res_pend_task = await tasks_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_fre.id),
            "class_id": str(academic_class.id),
            "title": "Peça 03 - Engrenagem Pendente no Prazo",
            "due_date": "2030-04-10T18:00:00Z",
            "is_mandatory": True,
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Passo Circular da Engrenagem",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_pend_task.status_code == status.HTTP_201_CREATED
    task_pend_id = UUID(res_pend_task.json()["id"])

    # 1. Estudante consulta todas as suas tarefas (GET /api/v1/students/{id}/pending-tasks)
    res_all = await tasks_client.get(
        f"/api/v1/students/{student.id}/pending-tasks",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_all.status_code == status.HTTP_200_OK
    body = res_all.json()

    assert body["student_id"] == str(student.id)
    assert body["student"]["full_name"] == "Mariana Costa"
    assert body["pending_count"] == 1
    assert body["late_count"] == 1
    assert body["completed_count"] == 2
    assert body["submitted_count"] == 1
    assert body["evaluated_count"] == 1
    assert body["total_count"] == 4
    assert body["summary"] == {
        "pending_count": 1,
        "late_count": 1,
        "completed_count": 2,
        "submitted_count": 1,
        "evaluated_count": 1,
        "total_count": 4,
    }

    # Lista ordenada por due_date ascendente: Peça 01 (2020-02-15), Peça 02 (2020-03-10), Peça 03 (2030-04-10), Peça 04 (2030-05-20)
    tasks_list = body["tasks"]
    assert len(tasks_list) == 4
    assert [item["task_id"] for item in tasks_list] == [
        str(task_eval_id),
        str(task_late_id),
        str(task_pend_id),
        str(task_sub_id),
    ]

    # Verifica marcação dinâmica LATE na Peça 02 (persisted_status=PENDING -> status=LATE)
    late_item = tasks_list[1]
    assert late_item["title"] == "Peça 02 - Eixo com Prazo Expirado"
    assert late_item["persisted_status"] == SubmissionStatus.PENDING.value
    assert late_item["status"] == SubmissionStatus.LATE.value
    assert late_item["is_late"] is True
    assert late_item["is_completed"] is False

    # Verifica Peça 01 avaliada (EVALUATED)
    eval_item = tasks_list[0]
    assert eval_item["status"] == SubmissionStatus.EVALUATED.value
    assert eval_item["is_late"] is False
    assert eval_item["is_completed"] is True
    assert eval_item["final_task_score"] == "8.00"
    assert eval_item["is_approved"] is True
    assert len(eval_item["evaluations"]) == 1

    # 2. Filtro por status=LATE retorna apenas a tarefa expirada mantendo os contadores do contexto
    res_filter_late = await tasks_client.get(
        f"/api/v1/students/{student.id}/pending-tasks?status=LATE",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_filter_late.status_code == status.HTTP_200_OK
    late_body = res_filter_late.json()
    assert len(late_body["tasks"]) == 1
    assert late_body["tasks"][0]["task_id"] == str(task_late_id)
    assert late_body["tasks"][0]["status"] == SubmissionStatus.LATE.value
    assert late_body["late_count"] == 1
    assert late_body["pending_count"] == 1
    assert late_body["completed_count"] == 2

    # 3. Filtro por status=PENDING retorna apenas a tarefa dentro do prazo (não inclui a expirada)
    res_filter_pending = await tasks_client.get(
        f"/api/v1/students/{student.id}/pending-tasks?status=PENDING",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_filter_pending.status_code == status.HTTP_200_OK
    pending_body = res_filter_pending.json()
    assert len(pending_body["tasks"]) == 1
    assert pending_body["tasks"][0]["task_id"] == str(task_pend_id)
    assert pending_body["tasks"][0]["status"] == SubmissionStatus.PENDING.value

    # 4. Filtro por module_id (mod_fre -> Peça 03 PENDING e Peça 04 SUBMITTED)
    res_filter_mod = await tasks_client.get(
        f"/api/v1/students/{student.id}/pending-tasks?module_id={mod_fre.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_filter_mod.status_code == status.HTTP_200_OK
    mod_body = res_filter_mod.json()
    assert mod_body["pending_count"] == 1
    assert mod_body["late_count"] == 0
    assert mod_body["completed_count"] == 1
    assert [item["task_id"] for item in mod_body["tasks"]] == [
        str(task_pend_id),
        str(task_sub_id),
    ]

    # 5. Filtro combinado por module_id + status=SUBMITTED
    res_filter_mod_sub = await tasks_client.get(
        f"/api/v1/students/{student.id}/pending-tasks?module_id={mod_fre.id}&status=SUBMITTED",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_filter_mod_sub.status_code == status.HTTP_200_OK
    assert len(res_filter_mod_sub.json()["tasks"]) == 1
    assert res_filter_mod_sub.json()["tasks"][0]["task_id"] == str(task_sub_id)


@pytest.mark.asyncio
async def test_list_student_pending_tasks_idor_isolation_rbac_and_not_found(
    tasks_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida isolamento de segurança IDOR (estudante só acessa suas próprias pendências), RBAC docente e 404 (BE-026)."""
    admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="admpend026",
    )
    _coord, coord_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="crdpend026",
    )
    assigned_teacher, assigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_a_026",
    )
    unassigned_teacher, unassigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_b_026",
    )
    student_a, student_a_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stua_026",
    )
    student_b, _student_b_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stub_026",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-AUT-026",
            name="Técnico em Automação Industrial",
            description="Curso técnico",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course.id,
            code="AUT-2026-1A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        class_b = AcademicClassRepository(session).create(
            course_id=course.id,
            code="AUT-2026-1B",
            period="2026.1",
            shift=Shift.AFTERNOON,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="CLP-026",
            name="Programação de CLP",
            workload_hours=60,
            syllabus="Ladder",
            is_active=True,
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=assigned_teacher.id,
                    class_id=class_a.id,
                    subject_id=subject.id,
                    is_main_teacher=True,
                ),
                Enrollment(
                    student_id=student_a.id,
                    class_id=class_a.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=student_b.id,
                    class_id=class_b.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    # 1. Sem token -> HTTP 401
    res_unauth = await tasks_client.get(f"/api/v1/students/{student_a.id}/pending-tasks")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Isolamento IDOR: Estudante A tentando acessar pendências do Estudante B ou UUID aleatório -> HTTP 403
    res_idor_peer = await tasks_client.get(
        f"/api/v1/students/{student_b.id}/pending-tasks",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_idor_peer.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_peer.json()["message"] == STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE

    res_idor_random = await tasks_client.get(
        f"/api/v1/students/{uuid4()}/pending-tasks",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_idor_random.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_random.json()["message"] == STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE

    # 3. Estudante A acessando suas próprias pendências -> HTTP 200 OK
    res_self = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_self.status_code == status.HTTP_200_OK
    assert res_self.json()["student_id"] == str(student_a.id)

    # 4. Docente alocado à turma do Estudante A -> HTTP 200 OK; mas tentando acessar Estudante B -> HTTP 403
    res_teacher_ok = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_teacher_ok.status_code == status.HTTP_200_OK

    res_teacher_other = await tasks_client.get(
        f"/api/v1/students/{student_b.id}/pending-tasks",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_teacher_other.status_code == status.HTTP_403_FORBIDDEN
    assert res_teacher_other.json()["message"] == STUDENT_TASKS_TEACHER_FORBIDDEN_MESSAGE

    res_unassigned_teacher = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks",
        headers={"Authorization": f"Bearer {unassigned_teacher_token}"},
    )
    assert res_unassigned_teacher.status_code == status.HTTP_403_FORBIDDEN

    # 5. Coordenador e Admin acessam qualquer estudante -> HTTP 200 OK
    for priv_tok in (coord_token, admin_token):
        res_priv = await tasks_client.get(
            f"/api/v1/students/{student_b.id}/pending-tasks",
            headers={"Authorization": f"Bearer {priv_tok}"},
        )
        assert res_priv.status_code == status.HTTP_200_OK

    # 6. Erros 404: estudante inexistente, usuário que não é STUDENT, module_id/subject_id/class_id inexistentes ou turma sem matrícula
    res_no_stu = await tasks_client.get(
        f"/api/v1/students/{uuid4()}/pending-tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_stu.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_stu.json()["message"] == STUDENT_TASKS_NOT_FOUND_MESSAGE

    res_non_stu = await tasks_client.get(
        f"/api/v1/students/{assigned_teacher.id}/pending-tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_non_stu.status_code == status.HTTP_404_NOT_FOUND
    assert res_non_stu.json()["message"] == STUDENT_TASKS_NOT_FOUND_MESSAGE

    res_no_mod = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks?module_id={uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_mod.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_mod.json()["message"] == PRACTICAL_TASK_MODULE_NOT_FOUND_MESSAGE

    res_no_subj = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks?subject_id={uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_subj.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_subj.json()["message"] == STUDENT_TASKS_SUBJECT_NOT_FOUND_MESSAGE

    res_no_cls = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks?class_id={uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_cls.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_cls.json()["message"] == PRACTICAL_TASK_CLASS_NOT_FOUND_MESSAGE

    res_unenrolled_cls = await tasks_client.get(
        f"/api/v1/students/{student_a.id}/pending-tasks?class_id={class_b.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_unenrolled_cls.status_code == status.HTTP_404_NOT_FOUND
    assert res_unenrolled_cls.json()["message"] == STUDENT_TASKS_ENROLLMENT_NOT_FOUND_MESSAGE


