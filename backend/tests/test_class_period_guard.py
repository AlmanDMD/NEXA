"""Testes de integração para o bloqueio de mutação em período letivo encerrado (BE-029 / DB-029)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
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
    AcademicClass,
    Base,
    Enrollment,
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
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "class_period_guard_test.db"
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
    """Cria fábrica de sessões SQLAlchemy acoplada à engine isolada."""
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
def guard_app(
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
async def guard_client(guard_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=guard_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
) -> tuple[User, str]:
    """Cria usuário no banco de testes e gera token JWT."""
    with session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=f"Usuário {role.value} {suffix}",
                registration_number=f"SENAI-{role.value[:3]}-{suffix.upper()}",
                phone="(11) 98888-7777",
            ),
        )
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return user, token


@pytest.mark.asyncio
async def test_closed_class_blocks_all_diary_mutations_and_allows_reads_until_admin_reopens(
    guard_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida BE-029: bloqueia com HTTP 422 CLASS_PERIOD_CLOSED aulas, chamadas, tarefas, avaliações e médias em turma COMPLETED/ARCHIVED e libera após reabertura formal por ADMIN."""
    _admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm029",
    )
    _coord, coord_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="crd029",
    )
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr029",
    )
    student, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu029",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-029",
            name="Técnico em Mecânica Industrial",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-029",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="USI-029",
            name="Usinagem Convencional",
            workload_hours=80,
            syllabus="Torneamento e fresamento",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-USI-029",
            title="Tolerância Dimensional H7",
            category=CompetencyCategory.TECHNICAL,
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

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    coord_headers = {"Authorization": f"Bearer {coord_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Enquanto a turma está ACTIVE, cria aula, tarefa prática e avaliação formativa
    res_lesson = await guard_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "lesson_date": "2026-03-10",
            "workload_hours": 4,
            "topic_summary": "Aula de torneamento cilíndrico externo.",
        },
        headers=teacher_headers,
    )
    assert res_lesson.status_code == status.HTTP_201_CREATED
    lesson_id = UUID(res_lesson.json()["id"])

    res_task = await guard_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Peça Prática Eixo H7",
            "due_date": "2026-04-20T18:00:00Z",
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Medição Externa ±0,02mm",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert res_task.status_code == status.HTTP_201_CREATED
    task_id = UUID(res_task.json()["id"])
    criterion_id = UUID(res_task.json()["criteria"][0]["id"])

    res_assessment = await guard_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "title": "Prova Teórica 01",
            "assessment_type": "EXAM",
            "weight": "2.00",
            "application_date": "2026-04-15",
            "max_grade": "10.00",
        },
        headers=teacher_headers,
    )
    assert res_assessment.status_code == status.HTTP_201_CREATED
    assessment_id = UUID(res_assessment.json()["id"])

    # 2. Coordenador encerra a turma (ACTIVE -> COMPLETED)
    res_close = await guard_client.patch(
        f"/api/v1/classes/{academic_class.id}/status",
        json={"status": "COMPLETED"},
        headers=coord_headers,
    )
    assert res_close.status_code == status.HTTP_200_OK
    assert res_close.json()["status"] == ClassStatus.COMPLETED.value

    # 3. Todas as rotas de mutação devem ser bloqueadas com HTTP 422 + error="CLASS_PERIOD_CLOSED"
    mutation_requests = [
        (
            "/api/v1/lessons",
            {
                "class_id": str(academic_class.id),
                "subject_id": str(subject.id),
                "lesson_date": "2026-03-15",
                "workload_hours": 4,
                "topic_summary": "Tentativa após encerramento.",
            },
        ),
        (
            f"/api/v1/lessons/{lesson_id}/attendance",
            {"records": [{"student_id": str(student.id), "status": "ABSENT"}]},
        ),
        (
            "/api/v1/practical-tasks",
            {
                "module_id": str(module.id),
                "class_id": str(academic_class.id),
                "title": "Tentativa Tarefa Turma Fechada",
                "due_date": "2026-05-01T18:00:00Z",
                "criteria": [
                    {
                        "competency_id": str(comp.id),
                        "criterion_name": "Rubrica Teste",
                        "weight": "1.00",
                        "min_acceptable_level": 3,
                    }
                ],
            },
        ),
        (
            f"/api/v1/tasks/{task_id}/evaluations",
            {
                "student_id": str(student.id),
                "status": "EVALUATED",
                "evaluations": [{"criterion_id": str(criterion_id), "achieved_level": 4}],
            },
        ),
        (
            "/api/v1/assessments",
            {
                "class_id": str(academic_class.id),
                "subject_id": str(subject.id),
                "title": "Tentativa Prova Turma Fechada",
                "application_date": "2026-04-25",
            },
        ),
        (
            f"/api/v1/assessments/{assessment_id}/grades",
            {"grades": [{"student_id": str(student.id), "grade_value": "8.00"}]},
        ),
        (
            f"/api/v1/classes/{academic_class.id}/calculate-averages",
            None,
        ),
    ]

    for endpoint_url, body_payload in mutation_requests:
        res = await guard_client.post(
            endpoint_url,
            json=body_payload,
            headers=teacher_headers,
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
            f"Esperado 422 em {endpoint_url}, recebido {res.status_code}: {res.text}"
        )
        err_body = res.json()
        assert err_body["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
        assert err_body["message"] == CLASS_PERIOD_CLOSED_MESSAGE

    # 4. Leituras (GET) permanecem permitidas normalmente em turma encerrada
    assert (
        await guard_client.get(
            f"/api/v1/classes/{academic_class.id}/lessons",
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK
    assert (
        await guard_client.get(
            f"/api/v1/classes/{academic_class.id}/grades-summary",
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK
    assert (
        await guard_client.get(
            f"/api/v1/students/{student.id}/pending-tasks",
            headers=student_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 5. Coordenador não pode reabrir turma encerrada (403); somente ADMIN pode reabrir (200)
    res_coord_reopen = await guard_client.patch(
        f"/api/v1/classes/{academic_class.id}/status",
        json={"status": "ACTIVE"},
        headers=coord_headers,
    )
    assert res_coord_reopen.status_code == status.HTTP_403_FORBIDDEN

    res_admin_reopen = await guard_client.patch(
        f"/api/v1/classes/{academic_class.id}/status",
        json={"status": "ACTIVE"},
        headers=admin_headers,
    )
    assert res_admin_reopen.status_code == status.HTTP_200_OK
    assert res_admin_reopen.json()["status"] == ClassStatus.ACTIVE.value

    # 6. Após reabertura formal pelo ADMIN, as mutações voltam a funcionar normalmente
    res_grade_after_reopen = await guard_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={"grades": [{"student_id": str(student.id), "grade_value": "8.50"}]},
        headers=teacher_headers,
    )
    assert res_grade_after_reopen.status_code == status.HTTP_200_OK

    res_att_after_reopen = await guard_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={"records": [{"student_id": str(student.id), "status": "PRESENT"}]},
        headers=teacher_headers,
    )
    assert res_att_after_reopen.status_code == status.HTTP_200_OK

    res_eval_after_reopen = await guard_client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        json={
            "student_id": str(student.id),
            "status": "EVALUATED",
            "evaluations": [{"criterion_id": str(criterion_id), "achieved_level": 5}],
        },
        headers=teacher_headers,
    )
    assert res_eval_after_reopen.status_code == status.HTTP_200_OK

    # 7. Arquivamento (ARCHIVED) também bloqueia mutações com CLASS_PERIOD_CLOSED
    with db_session_factory() as session:
        cls_row = session.get(AcademicClass, academic_class.id)
        assert cls_row is not None
        cls_row.status = ClassStatus.ARCHIVED
        session.add(cls_row)
        session.commit()

    res_archived_blocked = await guard_client.post(
        f"/api/v1/assessments/{assessment_id}/grades",
        json={"grades": [{"student_id": str(student.id), "grade_value": "9.00"}]},
        headers=admin_headers,
    )
    assert res_archived_blocked.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_archived_blocked.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE


@pytest.mark.asyncio
async def test_sqlalchemy_handler_maps_db029_trigger_error_to_http_422_class_period_closed(
    guard_app: FastAPI,
) -> None:
    """Valida alinhamento com a trigger DB-029 (fn_prevent_closed_class_mutation): exceção SQL vira HTTP 422 CLASS_PERIOD_CLOSED."""

    @guard_app.post("/api/v1/_test-db029-trigger")
    async def _simulate_db029_trigger() -> dict[str, str]:
        raise OperationalError(
            statement="UPDATE student_grades SET grade_value = 9.00",
            params={},
            orig=Exception(
                "CLASS_PERIOD_CLOSED: fn_prevent_closed_class_mutation - Período letivo encerrado para esta turma."
            ),
        )

    transport = ASGITransport(app=guard_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        res = await client.post("/api/v1/_test-db029-trigger")

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = res.json()
    assert body["success"] is False
    assert body["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
    assert body["message"] == CLASS_PERIOD_CLOSED_MESSAGE
