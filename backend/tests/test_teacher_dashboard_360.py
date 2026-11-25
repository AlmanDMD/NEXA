"""Testes unitários, de integração e performance (<150ms) para Dashboard do Professor e Visão 360° (BE-031)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
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
    AcademicAlert,
    Base,
    Enrollment,
    ModuleCompetency,
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
    AlertCategory,
    AlertStatus,
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.dashboard_service import (
    DASHBOARD_CLASS_NOT_FOUND_MESSAGE,
    DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE,
    DASHBOARD_MODULE_NOT_FOUND_MESSAGE,
    DASHBOARD_STUDENT_NOT_FOUND_MESSAGE,
    DASHBOARD_SUBJECT_NOT_FOUND_MESSAGE,
    DASHBOARD_TEACHER_CLASS_FORBIDDEN_MESSAGE,
    DASHBOARD_TEACHER_STUDENT_FORBIDDEN_MESSAGE,
    _compute_median,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL e views analíticas."""
    db_file = tmp_path / "dashboard_360_test.db"
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
def dashboard_app(
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
async def dashboard_client(dashboard_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=dashboard_app)
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


def test_academic_alert_orm_and_median_helper_validations() -> None:
    """Valida regras unitárias de mediana Decimal e validação ORM de AcademicAlert."""
    assert _compute_median([]) is None
    assert _compute_median([Decimal("8.00")]) == Decimal("8.00")
    assert _compute_median([Decimal("9.00"), Decimal("5.00"), Decimal("7.00")]) == Decimal("7.00")
    assert _compute_median([Decimal("6.00"), Decimal("8.50")]) == Decimal("7.25")

    with pytest.raises(ValueError, match="ao menos 5 caracteres"):
        AcademicAlert(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            class_id=uuid4(),
            risk_level=RiskLevel.HIGH,
            alert_category=AlertCategory.ATTENDANCE,
            explainable_reason="   ",
        )


@pytest.mark.asyncio
async def test_teacher_class_dashboard_and_student_360_kpis_modules_and_performance_under_150ms(
    dashboard_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/dashboard/teacher/classes/{id} e GET /api/v1/students/{id}/360 via vw_student_360_performance em < 150ms (BE-031)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="dash031_t",
        full_name="Prof. Oficina Mecânica",
    )
    stu_ok, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="dash031_s1",
        full_name="Amanda Oliveira",
    )
    stu_risk, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="dash031_s2",
        full_name="Bernardo Costa",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="dash031_sd",
        full_name="Caio Trancado",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-031",
            name="Técnico em Mecânica Industrial",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-031",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="FAB-031",
            name="Processos de Fabricação Mecânica",
            workload_hours=120,
            syllabus="Desenho, Metrologia e Tornearia",
            is_active=True,
        )
        mod_desenho = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Desenho Técnico",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_metrologia = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Metrologia",
            order_index=2,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_tornearia = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia",
            order_index=3,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp_met = CompetencyRepository(session).create(
            code="COMP-MET-031",
            title="Medição com Micrômetro Externo",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_tor = CompetencyRepository(session).create(
            code="COMP-TOR-031",
            title="Operação Segura de Torno NR-12",
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
        enr_ok = Enrollment(
            student_id=stu_ok.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        enr_risk = Enrollment(
            student_id=stu_risk.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
        )
        enr_dropped = Enrollment(
            student_id=stu_dropped.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.DROPPED,
        )
        session.add_all([enr_ok, enr_risk, enr_dropped])
        session.flush()

        # Alerta explicável ativo para Bernardo (stu_risk) em academic_alerts (DB-034)
        session.add(
            AcademicAlert(
                student_id=stu_risk.id,
                enrollment_id=enr_risk.id,
                class_id=academic_class.id,
                module_id=mod_metrologia.id,
                risk_level=RiskLevel.CRITICAL,
                alert_category=AlertCategory.ATTENDANCE,
                explainable_reason="Frequência em 50.00% (< 75%) e entrega prática em atraso.",
                metric_snapshot={"attendance_percentage": "50.00", "late_tasks": 1},
                status=AlertStatus.ACTIVE,
            )
        )
        session.commit()

    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Registra 2 aulas de 4h no módulo Metrologia:
    # - Amanda: 2 PRESENT => 100.00%
    # - Bernardo: 1 PRESENT + 1 ABSENT => 50.00% (CRITICAL)
    for idx, (d_str, b_status) in enumerate(
        [("2026-03-10", "PRESENT"), ("2026-03-12", "ABSENT")],
        start=1,
    ):
        res_l = await dashboard_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(academic_class.id),
                "subject_id": str(subject.id),
                "module_id": str(mod_metrologia.id),
                "lesson_date": d_str,
                "workload_hours": 4,
                "topic_summary": f"Aula Metrologia {idx}",
            },
            headers=headers,
        )
        assert res_l.status_code == status.HTTP_201_CREATED
        lid = res_l.json()["id"]
        assert (
            await dashboard_client.post(
                f"/api/v1/lessons/{lid}/attendance",
                json={
                    "records": [
                        {"student_id": str(stu_ok.id), "status": "PRESENT"},
                        {"student_id": str(stu_risk.id), "status": b_status},
                    ]
                },
                headers=headers,
            )
        ).status_code == status.HTTP_200_OK

    # 2. Cria atividade prática em Metrologia com prazo futuro (2030) e avalia Amanda no prazo (nível 5 -> 10.00)
    res_t1 = await dashboard_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(mod_metrologia.id),
            "class_id": str(academic_class.id),
            "title": "Calibração de Eixo no Micrômetro",
            "due_date": "2030-06-15T18:00:00Z",
            "max_score": "10.00",
            "criteria": [
                {
                    "competency_id": str(comp_met.id),
                    "criterion_name": "Leitura Milesimal ±0,01mm",
                    "weight": "1.00",
                    "min_acceptable_level": 4,
                }
            ],
        },
        headers=headers,
    )
    assert res_t1.status_code == status.HTTP_201_CREATED
    t1_id = UUID(res_t1.json()["id"])
    t1_crit_id = UUID(res_t1.json()["criteria"][0]["id"])

    assert (
        await dashboard_client.post(
            f"/api/v1/tasks/{t1_id}/evaluations",
            json={
                "student_id": str(stu_ok.id),
                "status": "EVALUATED",
                "evaluations": [{"criterion_id": str(t1_crit_id), "achieved_level": 5}],
            },
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    # 3. Cria prova em Desenho Técnico (weight=1.00): Amanda=8.00, Bernardo=4.00
    res_a1 = await dashboard_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(mod_desenho.id),
            "title": "Prova Leitura de Desenho Técnico",
            "assessment_type": "EXAM",
            "weight": "1.00",
            "application_date": "2026-03-20",
            "max_grade": "10.00",
        },
        headers=headers,
    )
    assert res_a1.status_code == status.HTTP_201_CREATED
    a1_id = UUID(res_a1.json()["id"])

    assert (
        await dashboard_client.post(
            f"/api/v1/assessments/{a1_id}/grades",
            json={
                "grades": [
                    {"student_id": str(stu_ok.id), "grade_value": "8.00"},
                    {"student_id": str(stu_risk.id), "grade_value": "4.00"},
                ]
            },
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    # 4. Consulta Dashboard do Professor validando tempo < 150ms
    t0 = time.perf_counter()
    dash_res = await dashboard_client.get(
        f"/api/v1/dashboard/teacher/classes/{academic_class.id}",
        headers=headers,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert dash_res.status_code == status.HTTP_200_OK
    assert elapsed_ms < 150.0, f"Dashboard excedeu 150ms: {elapsed_ms:.2f}ms"

    dash_body = dash_res.json()
    kpis = dash_body["kpis"]
    # Apenas os 2 alunos ativos (Caio DROPPED excluído):
    # - Amanda: overall_average = (8.00 + 10.00) / 2 = 9.00, attendance = 100.00%
    # - Bernardo: overall_average = 4.00, attendance = 50.00%
    # Média da turma = (9.00 + 4.00) / 2 = 6.50 | Presença média = (100 + 50) / 2 = 75.00%
    # Tarefas: 2 atribuídas, 1 concluída no prazo => 50.00%
    assert kpis["total_students"] == 2
    assert kpis["class_average_grade"] == "6.50"
    assert kpis["average_attendance_rate"] == "75.00"
    assert kpis["on_time_tasks_percentage"] == "50.00"
    assert kpis["completed_tasks_percentage"] == "50.00"
    assert kpis["at_risk_students_count"] == 1
    assert kpis["critical_students_count"] == 1
    assert kpis["active_alerts_count"] == 1

    # Distribuição nos 3 módulos (Desenho Técnico, Metrologia, Tornearia)
    mods = dash_body["modules_distribution"]
    assert [m["module_title"] for m in mods] == [
        "Desenho Técnico",
        "Metrologia",
        "Tornearia",
    ]
    assert mods[0]["average_grade"] == "6.00"
    assert mods[0]["median_grade"] == "6.00"
    assert mods[1]["average_grade"] == "10.00"
    assert mods[1]["average_attendance_rate"] == "75.00"
    assert mods[1]["completion_rate"] == "50.00"
    assert mods[1]["average_skill_level"] == "5.00"

    # 5. Consulta Ficha 360° do Aluno (Amanda e Bernardo) validando tempo < 150ms
    t0_360 = time.perf_counter()
    s360_res = await dashboard_client.get(
        f"/api/v1/students/{stu_ok.id}/360",
        headers=headers,
    )
    elapsed_360_ms = (time.perf_counter() - t0_360) * 1000.0
    assert s360_res.status_code == status.HTTP_200_OK
    assert elapsed_360_ms < 150.0, f"Student 360 excedeu 150ms: {elapsed_360_ms:.2f}ms"

    s360_body = s360_res.json()
    assert s360_body["student"]["full_name"] == "Amanda Oliveira"
    assert s360_body["overview"]["overall_average"] == "9.00"
    assert s360_body["overview"]["attendance_percentage"] == "100.00"
    assert s360_body["overview"]["standing_status"] == AcademicStandingStatus.APPROVED.value
    assert s360_body["overview"]["risk_level"] == RiskLevel.LOW.value
    assert len(s360_body["subjects"]) == 1
    assert len(s360_body["attendance_by_module"]) == 3
    assert len(s360_body["practical_submissions"]) == 1

    comps_by_code = {c["code"]: c for c in s360_body["competencies"]}
    assert comps_by_code["COMP-MET-031"]["verified_level"] == "5.00"
    assert comps_by_code["COMP-MET-031"]["required_level"] == 4
    assert comps_by_code["COMP-MET-031"]["is_proficient"] is True
    assert comps_by_code["COMP-TOR-031"]["verified_level"] is None
    assert comps_by_code["COMP-TOR-031"]["is_proficient"] is False

    # Ficha 360° de Bernardo retorna alerta ativo explicável e risco CRITICAL
    b360_res = await dashboard_client.get(
        f"/api/v1/students/{stu_risk.id}/360",
        headers=headers,
    )
    assert b360_res.status_code == status.HTTP_200_OK
    b360_body = b360_res.json()
    assert b360_body["overview"]["risk_level"] == RiskLevel.CRITICAL.value
    assert len(b360_body["active_alerts"]) == 1
    assert b360_body["active_alerts"][0]["alert_category"] == AlertCategory.ATTENDANCE.value


@pytest.mark.asyncio
async def test_dashboard_and_student_360_rbac_and_not_found_errors(
    dashboard_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida RBAC (401, 403 para STUDENT e docente não alocado) e 404 nas rotas de Dashboard e Ficha 360° (BE-031)."""
    _admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="adm031",
        full_name="Admin 031",
    )
    _coord, coord_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="crd031",
        full_name="Coord 031",
    )
    assigned_teacher, assigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_a_031",
        full_name="Prof Turma A",
    )
    _other_teacher, other_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tchr_b_031",
        full_name="Prof Externo",
    )
    stu_a, stu_a_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stua_031",
        full_name="Aluno Turma A",
    )
    stu_b, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="stub_031",
        full_name="Aluno Turma B",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-RBAC-031",
            name="Técnico em Automação",
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
            code="CLP-031",
            name="Controladores Programáveis",
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
                    student_id=stu_a.id,
                    class_id=class_a.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_b.id,
                    class_id=class_b.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    # 1. 401 sem token
    assert (
        await dashboard_client.get(f"/api/v1/dashboard/teacher/classes/{class_a.id}")
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await dashboard_client.get(f"/api/v1/students/{stu_a.id}/360")
    ).status_code == status.HTTP_401_UNAUTHORIZED

    # 2. 403 para STUDENT em ambas as rotas exclusivas do corpo docente/coordenação
    for url in (
        f"/api/v1/dashboard/teacher/classes/{class_a.id}",
        f"/api/v1/students/{stu_a.id}/360",
        f"/api/v1/students/{stu_b.id}/360",
    ):
        assert (
            await dashboard_client.get(
                url,
                headers={"Authorization": f"Bearer {stu_a_token}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    # 3. 403 para TEACHER não alocado à turma
    res_forb_cls = await dashboard_client.get(
        f"/api/v1/dashboard/teacher/classes/{class_a.id}",
        headers={"Authorization": f"Bearer {other_teacher_token}"},
    )
    assert res_forb_cls.status_code == status.HTTP_403_FORBIDDEN
    assert res_forb_cls.json()["message"] == DASHBOARD_TEACHER_CLASS_FORBIDDEN_MESSAGE

    res_forb_stu = await dashboard_client.get(
        f"/api/v1/students/{stu_b.id}/360",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_forb_stu.status_code == status.HTTP_403_FORBIDDEN
    assert res_forb_stu.json()["message"] == DASHBOARD_TEACHER_STUDENT_FORBIDDEN_MESSAGE

    # 4. 200 OK para COORD e ADMIN em qualquer turma/estudante
    for priv_tok in (coord_token, admin_token):
        assert (
            await dashboard_client.get(
                f"/api/v1/dashboard/teacher/classes/{class_b.id}",
                headers={"Authorization": f"Bearer {priv_tok}"},
            )
        ).status_code == status.HTTP_200_OK
        assert (
            await dashboard_client.get(
                f"/api/v1/students/{stu_b.id}/360",
                headers={"Authorization": f"Bearer {priv_tok}"},
            )
        ).status_code == status.HTTP_200_OK

    # 5. Erros 404
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert (
        await dashboard_client.get(
            f"/api/v1/dashboard/teacher/classes/{uuid4()}",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_CLASS_NOT_FOUND_MESSAGE
    assert (
        await dashboard_client.get(
            f"/api/v1/dashboard/teacher/classes/{class_a.id}?subject_id={uuid4()}",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_SUBJECT_NOT_FOUND_MESSAGE
    assert (
        await dashboard_client.get(
            f"/api/v1/dashboard/teacher/classes/{class_a.id}?module_id={uuid4()}",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_MODULE_NOT_FOUND_MESSAGE
    assert (
        await dashboard_client.get(
            f"/api/v1/students/{uuid4()}/360",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_STUDENT_NOT_FOUND_MESSAGE
    assert (
        await dashboard_client.get(
            f"/api/v1/students/{assigned_teacher.id}/360",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_STUDENT_NOT_FOUND_MESSAGE
    assert (
        await dashboard_client.get(
            f"/api/v1/students/{stu_a.id}/360?class_id={class_b.id}",
            headers=admin_headers,
        )
    ).json()["message"] == DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE
