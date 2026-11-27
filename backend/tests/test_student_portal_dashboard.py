"""Testes unitários, de integração, privacidade e performance para o Portal do Aluno (BE-034)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import time
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    Base,
    Enrollment,
    ModuleCompetency,
    StudentMilestoneHistory,
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
    AcademicStandingStatus,
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    MilestoneType,
    RiskLevel,
    Shift,
    SubmissionStatus,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.dashboard_service import (
    DASHBOARD_CLASS_NOT_FOUND_MESSAGE,
    DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL e views analíticas."""
    db_file = tmp_path / "student_portal_dashboard_test.db"
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
    """Fábrica de sessões SQLAlchemy vinculada à engine isolada."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Hasher rápido para testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def portal_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância FastAPI configurada com banco isolado."""
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
async def portal_client(portal_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=portal_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
    full_name: str,
) -> tuple[User, str]:
    """Cria usuário de teste e retorna instância + JWT."""
    with session_factory() as session:
        user = AuthRepository(session=session).create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=full_name,
                registration_number=f"SENAI-{role.value[:3]}-{suffix.upper()}",
                phone="(11) 98888-7777",
            ),
        )
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return user, token


def test_student_milestone_history_orm_validations() -> None:
    """Valida regras unitárias de validação ORM do modelo StudentMilestoneHistory (DB-039)."""
    valid_milestone = StudentMilestoneHistory(
        student_id=uuid4(),
        enrollment_id=uuid4(),
        module_id=uuid4(),
        milestone_type=MilestoneType.MODULE_COMPLETED,
        title="  Módulo de Metrologia Concluído  ",
        description="  Excelente desempenho em medições lineares.  ",
        milestone_metadata={"final_score": 9.5},
    )
    assert valid_milestone.title == "Módulo de Metrologia Concluído"
    assert valid_milestone.description == "Excelente desempenho em medições lineares."
    assert valid_milestone.milestone_metadata == {"final_score": 9.5}

    with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
        StudentMilestoneHistory(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            milestone_type=MilestoneType.SKILL_LEVEL_UP,
            title="  ab  ",
        )

    with pytest.raises(ValueError, match="objeto JSON válido"):
        StudentMilestoneHistory(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            milestone_type=MilestoneType.PERFECT_ATTENDANCE,
            title="Presença Perfeita no Módulo",
            milestone_metadata=["invalido"],  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_student_portal_dashboard_me_returns_full_progress_radar_and_timeline(
    portal_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/dashboard/student/me retornando frequência, médias, progresso modular, radar, contadores e timeline (BE-034)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="be034_t",
        full_name="Prof. Mecânica SENAI",
    )
    stu_me, stu_me_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="be034_me",
        full_name="Lucas Andrade",
    )
    stu_other, stu_other_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="be034_other",
        full_name="Mariana Souza",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-034",
            name="Técnico em Mecânica de Precisão",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-034",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="USI-034",
            name="Usinagem e Metrologia Aplicada",
            workload_hours=80,
            syllabus="Metrologia e Tornearia",
            is_active=True,
        )
        mod_metrologia = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Metrologia Dimensional",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_tornearia = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia Convencional",
            order_index=2,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp_met = CompetencyRepository(session).create(
            code="COMP-MET-034",
            title="Leitura com Paquímetro e Micrômetro",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_tor = CompetencyRepository(session).create(
            code="COMP-TOR-034",
            title="Operação Segura em Torno NR-12",
            category=CompetencyCategory.SAFETY,
        )
        session.add_all(
            [
                ModuleCompetency(
                    module_id=mod_metrologia.id,
                    competency_id=comp_met.id,
                    weight=Decimal("1.00"),
                    required_level=4,
                ),
                ModuleCompetency(
                    module_id=mod_tornearia.id,
                    competency_id=comp_tor.id,
                    weight=Decimal("1.00"),
                    required_level=4,
                ),
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject.id,
                    is_main_teacher=True,
                ),
            ]
        )
        enr_me = Enrollment(
            student_id=stu_me.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        enr_other = Enrollment(
            student_id=stu_other.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        session.add_all([enr_me, enr_other])
        session.flush()

        # Marcos da linha do tempo para Lucas (stu_me) e um marco para Mariana (stu_other)
        session.add_all(
            [
                StudentMilestoneHistory(
                    student_id=stu_me.id,
                    enrollment_id=enr_me.id,
                    module_id=mod_metrologia.id,
                    milestone_type=MilestoneType.MODULE_COMPLETED,
                    title="Módulo de Metrologia Dimensional Concluído",
                    description="Superou a nota de corte com precisão nas medições.",
                    milestone_metadata={"final_module_score": 9.5, "passing_score": 6.0},
                    achieved_at=datetime(2026, 3, 15, 14, 0, tzinfo=timezone.utc),
                ),
                StudentMilestoneHistory(
                    student_id=stu_me.id,
                    enrollment_id=enr_me.id,
                    module_id=mod_metrologia.id,
                    milestone_type=MilestoneType.SKILL_LEVEL_UP,
                    title="Nível 5 Alcançado em Leitura com Micrômetro",
                    description="Domínio pleno verificado em bancada.",
                    milestone_metadata={"competency_code": "COMP-MET-034", "verified_level": 5},
                    achieved_at=datetime(2026, 3, 25, 16, 30, tzinfo=timezone.utc),
                ),
                StudentMilestoneHistory(
                    student_id=stu_other.id,
                    enrollment_id=enr_other.id,
                    module_id=mod_tornearia.id,
                    milestone_type=MilestoneType.PERFECT_ATTENDANCE,
                    title="Marco Exclusivo de Mariana",
                    description="Não deve aparecer para Lucas.",
                    achieved_at=datetime(2026, 3, 28, 10, 0, tzinfo=timezone.utc),
                ),
            ]
        )
        session.commit()

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Registra aula de 4h em Metrologia com presença para Lucas e falta para Mariana
    res_lesson = await portal_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(mod_metrologia.id),
            "lesson_date": "2026-03-10",
            "workload_hours": 4,
            "topic_summary": "Medição de Eixos com Micrômetro",
        },
        headers=teacher_headers,
    )
    assert res_lesson.status_code == status.HTTP_201_CREATED
    lesson_id = res_lesson.json()["id"]

    assert (
        await portal_client.post(
            f"/api/v1/lessons/{lesson_id}/attendance",
            json={
                "records": [
                    {"student_id": str(stu_me.id), "status": "PRESENT"},
                    {"student_id": str(stu_other.id), "status": "ABSENT"},
                ]
            },
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 2. Cria tarefa prática 1 em Metrologia e avalia Lucas com nível 5 (nota 10.00)
    res_t1 = await portal_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_metrologia.id),
            "class_id": str(academic_class.id),
            "title": "Inspeção Dimensional de Pino Guia",
            "due_date": "2030-06-15T18:00:00Z",
            "max_score": "10.00",
            "criteria": [
                {
                    "competency_id": str(comp_met.id),
                    "criterion_name": "Tolerância ±0,01mm",
                    "weight": "1.00",
                    "min_acceptable_level": 4,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert res_t1.status_code == status.HTTP_201_CREATED
    t1_id = UUID(res_t1.json()["id"])
    t1_crit_id = UUID(res_t1.json()["criteria"][0]["id"])

    assert (
        await portal_client.post(
            f"/api/v1/tasks/{t1_id}/evaluations",
            json={
                "student_id": str(stu_me.id),
                "status": "EVALUATED",
                "evaluations": [{"criterion_id": str(t1_crit_id), "achieved_level": 5}],
            },
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 3. Cria tarefa prática 2 em Tornearia (permanece PENDING para Lucas)
    res_t2 = await portal_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_tornearia.id),
            "class_id": str(academic_class.id),
            "title": "Desbaste Cilíndrico Externo",
            "due_date": "2030-07-20T18:00:00Z",
            "max_score": "10.00",
            "criteria": [
                {
                    "competency_id": str(comp_tor.id),
                    "criterion_name": "Segurança Operacional NR-12",
                    "weight": "1.00",
                    "min_acceptable_level": 4,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert res_t2.status_code == status.HTTP_201_CREATED

    # 4. Cria prova teórica em Metrologia e lança nota 9.00 para Lucas
    res_a1 = await portal_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(mod_metrologia.id),
            "title": "Prova Teórica de Metrologia",
            "assessment_type": "EXAM",
            "weight": "1.00",
            "application_date": "2026-03-14",
            "max_grade": "10.00",
        },
        headers=teacher_headers,
    )
    assert res_a1.status_code == status.HTTP_201_CREATED
    a1_id = UUID(res_a1.json()["id"])

    assert (
        await portal_client.post(
            f"/api/v1/assessments/{a1_id}/grades",
            json={
                "grades": [
                    {"student_id": str(stu_me.id), "grade_value": "9.00"},
                    {"student_id": str(stu_other.id), "grade_value": "5.00"},
                ]
            },
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 5. Estudante Lucas consulta GET /api/v1/dashboard/student/me (< 150ms)
    t0 = time.perf_counter()
    res_me = await portal_client.get(
        "/api/v1/dashboard/student/me",
        headers={"Authorization": f"Bearer {stu_me_token}"},
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert res_me.status_code == status.HTTP_200_OK
    assert elapsed_ms < 150.0, f"Portal do Aluno excedeu 150ms: {elapsed_ms:.2f}ms"

    body = res_me.json()

    # Identidade estrita extraída do token JWT (current_user.id)
    assert body["student_id"] == str(stu_me.id)
    assert body["student"]["id"] == str(stu_me.id)
    assert body["student"]["full_name"] == "Lucas Andrade"
    assert body["course_code"] == "TEC-MEC-034"

    # Resumo global e de frequência
    # Média de Lucas: (9.00 prova + 10.00 prática) / 2 = 9.50 | Frequência = 100.00%
    assert body["overall_average"] == "9.50"
    assert body["attendance_percentage"] == "100.00"
    assert body["overall_progress_percentage"] == "50.00"
    assert body["standing_status"] == AcademicStandingStatus.APPROVED.value
    assert body["risk_level"] == RiskLevel.LOW.value

    att_summary = body["attendance_summary"]
    assert att_summary["attendance_percentage"] == "100.00"
    assert att_summary["total_hours"] == 4
    assert att_summary["attended_hours"] == 4
    assert att_summary["absent_hours"] == 0
    assert len(att_summary["by_subject"]) == 1
    assert len(att_summary["by_module"]) == 2

    # Médias por disciplina
    assert len(body["subjects"]) == 1
    assert body["subjects"][0]["subject_code"] == "USI-034"
    assert body["subjects"][0]["subject_average"] == "9.50"

    # Progresso percentual em cada módulo prático
    mods_prog = body["modules_progress"]
    assert len(mods_prog) == 2
    assert mods_prog[0]["module_title"] == "Metrologia Dimensional"
    assert mods_prog[0]["total_tasks_count"] == 1
    assert mods_prog[0]["completed_tasks_count"] == 1
    assert mods_prog[0]["progress_percentage"] == "100.00"
    assert mods_prog[0]["is_completed"] is True
    assert mods_prog[0]["module_average"] == "9.50"

    assert mods_prog[1]["module_title"] == "Tornearia Convencional"
    assert mods_prog[1]["total_tasks_count"] == 1
    assert mods_prog[1]["completed_tasks_count"] == 0
    assert mods_prog[1]["pending_tasks_count"] == 1
    assert mods_prog[1]["progress_percentage"] == "0.00"
    assert mods_prog[1]["is_completed"] is False

    # Evolução de nível por competência técnica (Gráfico Radar)
    comps_by_code = {c["code"]: c for c in body["competencies"]}
    assert comps_by_code["COMP-MET-034"]["verified_level"] == "5.00"
    assert comps_by_code["COMP-MET-034"]["required_level"] == 4
    assert comps_by_code["COMP-MET-034"]["is_proficient"] is True
    assert comps_by_code["COMP-TOR-034"]["verified_level"] is None
    assert comps_by_code["COMP-TOR-034"]["is_proficient"] is False
    assert body["competencies_radar"] == body["competencies"]

    # Contadores de atividades práticas e próximas entregas
    counts = body["task_counts"]
    assert counts["total_count"] == 2
    assert counts["completed_count"] == 1
    assert counts["evaluated_count"] == 1
    assert counts["pending_count"] == 1
    assert counts["late_count"] == 0
    assert len(body["upcoming_tasks"]) == 1
    assert body["upcoming_tasks"][0]["title"] == "Desbaste Cilíndrico Externo"
    assert body["upcoming_tasks"][0]["status"] == SubmissionStatus.PENDING.value

    # Linha do tempo (student_milestone_history) ordenada da mais recente para a mais antiga
    timeline = body["timeline"]
    assert len(timeline) == 2
    assert timeline[0]["milestone_type"] == MilestoneType.SKILL_LEVEL_UP.value
    assert timeline[0]["title"] == "Nível 5 Alcançado em Leitura com Micrômetro"
    assert timeline[0]["module_title"] == "Metrologia Dimensional"
    assert timeline[0]["subject_code"] == "USI-034"
    assert timeline[1]["milestone_type"] == MilestoneType.MODULE_COMPLETED.value
    assert body["milestone_history"] == timeline

    # Garantia de privacidade: nunca expõe observações pedagógicas restritas ou dados de terceiros
    serialized_str = res_me.text.lower()
    assert "pedagogical_notes" not in serialized_str
    assert "pedagogical_note" not in serialized_str
    assert "marco exclusivo de mariana" not in serialized_str
    assert str(stu_other.id) not in serialized_str

    # 6. Quando Mariana consulta /dashboard/student/me com seu próprio JWT, vê apenas seus dados
    res_other = await portal_client.get(
        "/api/v1/dashboard/student/me",
        headers={"Authorization": f"Bearer {stu_other_token}"},
    )
    assert res_other.status_code == status.HTTP_200_OK
    other_body = res_other.json()
    assert other_body["student_id"] == str(stu_other.id)
    assert other_body["overall_average"] == "5.00"
    assert other_body["attendance_percentage"] == "0.00"
    assert len(other_body["timeline"]) == 1
    assert other_body["timeline"][0]["title"] == "Marco Exclusivo de Mariana"


@pytest.mark.asyncio
async def test_student_portal_dashboard_rbac_unenrolled_and_filters(
    portal_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida RBAC (401 sem token, 403 para TEACHER/COORDINATOR/ADMIN), aluno sem matrícula e filtro class_id (BE-034)."""
    _admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm034",
        full_name="Admin 034",
    )
    _coord, coord_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="crd034",
        full_name="Coord 034",
    )
    _teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tch034",
        full_name="Prof 034",
    )
    stu_empty, stu_empty_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stu_empty_034",
        full_name="Aluno Sem Matrícula",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-AUT-034",
            name="Técnico em Automação",
            description="Curso técnico",
            total_hours=1200,
            is_active=True,
        )
        other_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="AUT-2026-034",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        session.commit()

    # 1. 401 sem token
    assert (
        await portal_client.get("/api/v1/dashboard/student/me")
    ).status_code == status.HTTP_401_UNAUTHORIZED

    # 2. 403 para perfis não-estudante (endpoint exclusivo do próprio estudante autenticado)
    for non_student_tok in (teacher_token, coord_token, admin_token):
        assert (
            await portal_client.get(
                "/api/v1/dashboard/student/me",
                headers={"Authorization": f"Bearer {non_student_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    # 3. 200 OK com estado vazio gracioso para estudante ainda sem matrícula ativa
    stu_headers = {"Authorization": f"Bearer {stu_empty_token}"}
    res_empty = await portal_client.get(
        "/api/v1/dashboard/student/me",
        headers=stu_headers,
    )
    assert res_empty.status_code == status.HTTP_200_OK
    empty_body = res_empty.json()
    assert empty_body["student_id"] == str(stu_empty.id)
    assert empty_body["enrollment_id"] is None
    assert empty_body["overall_average"] is None
    assert empty_body["overall_progress_percentage"] == "0.00"
    assert empty_body["attendance_percentage"] == "100.00"
    assert empty_body["modules_progress"] == []
    assert empty_body["timeline"] == []
    assert empty_body["task_counts"]["total_count"] == 0

    # 4. 404 quando filtra por turma inexistente ou turma em que o estudante não está matriculado
    res_nf_class = await portal_client.get(
        f"/api/v1/dashboard/student/me?class_id={uuid4()}",
        headers=stu_headers,
    )
    assert res_nf_class.status_code == status.HTTP_404_NOT_FOUND
    assert res_nf_class.json()["message"] == DASHBOARD_CLASS_NOT_FOUND_MESSAGE

    res_nf_enr = await portal_client.get(
        f"/api/v1/dashboard/student/me?class_id={other_class.id}",
        headers=stu_headers,
    )
    assert res_nf_enr.status_code == status.HTTP_404_NOT_FOUND
    assert res_nf_enr.json()["message"] == DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE
