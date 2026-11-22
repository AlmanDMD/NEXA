"""Suíte de testes de integração ponta a ponta do Lote 3: Frequência, Rubricas, Recuperação, Médias, Período Encerrado e IDOR (BE-030)."""

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
from sqlalchemy import create_engine, event, select
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
    AuditLog,
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
    AcademicStandingStatus,
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.class_lesson_service import STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE
from app.services.practical_task_service import STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "lote3_attendance_grading_test.db"
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
    """Hasher rápido para testes automatizados."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def lote3_app(
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
async def lote3_client(lote3_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono para testes de integração do Lote 3."""
    transport = ASGITransport(app=lote3_app)
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
    """Persiste usuário de teste e retorna instância + JWT."""
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


@pytest.mark.asyncio
async def test_attendance_justified_vs_unjustified_zero_lessons_and_full_absence_edge_cases(
    lote3_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida frequência com faltas justificadas vs injustificadas e casos de borda: 0 aulas dadas e 100% faltas (BE-030)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="att030_t",
        full_name="Instrutor Frequência",
    )
    stu_justified, stu_justified_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="att030_j",
        full_name="Aluno Justificado",
    )
    stu_all_absent, stu_all_absent_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="att030_z",
        full_name="Aluno Cem Por Cento Falta",
    )
    stu_borderline, stu_borderline_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="att030_b",
        full_name="Aluno Limiar 75",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-INT-030",
            name="Técnico em Fabricação Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="FAB-2026-030",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="USI-030",
            name="Usinagem e Controle Dimensional",
            workload_hours=80,
            syllabus="Tornearia e metrologia",
            is_active=True,
        )
        mod_active = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_empty = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Fresamento (0 Aulas Dadas)",
            order_index=2,
            practical_hours=40,
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
                    student_id=stu_justified.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_all_absent.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=stu_borderline.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    headers = {"Authorization": f"Bearer {teacher_token}"}

    # Caso de borda: consulta com 0 aulas dadas no sistema inteiro -> 100.00% sem erro
    res_zero_lessons = await lote3_client.get(
        f"/api/v1/students/{stu_justified.id}/attendance",
        headers={"Authorization": f"Bearer {stu_justified_token}"},
    )
    assert res_zero_lessons.status_code == status.HTTP_200_OK
    zero_body = res_zero_lessons.json()
    assert zero_body["total_hours"] == 0
    assert zero_body["attendance_percentage"] == "100.00"
    assert zero_body["is_critical"] is False
    assert zero_body["risk_level"] == RiskLevel.LOW.value

    # Ministra 4 aulas de 4h (total 16h) apenas em mod_active (mod_empty continua com 0 aulas dadas):
    # - stu_justified: 2 PRESENT + 2 JUSTIFIED (8h justificadas) => 16/16 = 100.00% (LOW)
    # - stu_all_absent: 4 ABSENT (16h de falta) => 0/16 = 0.00% (CRITICAL)
    # - stu_borderline: 3 PRESENT + 1 ABSENT (4h de falta) => 12/16 = 75.00% (HIGH, is_critical=True, margem=0.00)
    lesson_plan = [
        ("2026-03-02", "PRESENT", "ABSENT", "PRESENT"),
        ("2026-03-03", "JUSTIFIED", "ABSENT", "PRESENT"),
        ("2026-03-04", "JUSTIFIED", "ABSENT", "PRESENT"),
        ("2026-03-05", "PRESENT", "ABSENT", "ABSENT"),
    ]
    for lesson_date_str, st_j, st_z, st_b in lesson_plan:
        res_l = await lote3_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(academic_class.id),
                "subject_id": str(subject.id),
                "module_id": str(mod_active.id),
                "lesson_date": lesson_date_str,
                "workload_hours": 4,
                "topic_summary": f"Prática de oficina em {lesson_date_str}",
            },
            headers=headers,
        )
        assert res_l.status_code == status.HTTP_201_CREATED
        lid = res_l.json()["id"]

        res_att = await lote3_client.post(
            f"/api/v1/lessons/{lid}/attendance",
            json={
                "records": [
                    {
                        "student_id": str(stu_justified.id),
                        "status": st_j,
                        "absent_hours": 4 if st_j == "JUSTIFIED" else 0,
                        "justification_note": "Atestado médico" if st_j == "JUSTIFIED" else None,
                    },
                    {"student_id": str(stu_all_absent.id), "status": st_z},
                    {"student_id": str(stu_borderline.id), "status": st_b},
                ]
            },
            headers=headers,
        )
        assert res_att.status_code == status.HTTP_200_OK

    # Verifica extrato do Aluno Justificado: 100.00% presença e 8h justificadas
    res_j = await lote3_client.get(
        f"/api/v1/students/{stu_justified.id}/attendance",
        headers={"Authorization": f"Bearer {stu_justified_token}"},
    )
    assert res_j.status_code == status.HTTP_200_OK
    body_j = res_j.json()
    assert body_j["total_hours"] == 16
    assert body_j["attended_hours"] == 16
    assert body_j["absent_hours"] == 0
    assert body_j["justified_absent_hours"] == 8
    assert body_j["attendance_percentage"] == "100.00"
    assert body_j["is_critical"] is False
    assert body_j["risk_level"] == RiskLevel.LOW.value
    # Módulo sem aulas dadas retorna 100.00% sem divisão por zero
    mod_by_id = {m["module_id"]: m for m in body_j["modules"]}
    assert mod_by_id[str(mod_empty.id)]["total_hours"] == 0
    assert mod_by_id[str(mod_empty.id)]["attendance_percentage"] == "100.00"

    # Verifica extrato do Aluno 100% Faltas: 0.00% CRITICAL
    res_z = await lote3_client.get(
        f"/api/v1/students/{stu_all_absent.id}/attendance",
        headers={"Authorization": f"Bearer {stu_all_absent_token}"},
    )
    assert res_z.status_code == status.HTTP_200_OK
    body_z = res_z.json()
    assert body_z["total_hours"] == 16
    assert body_z["attended_hours"] == 0
    assert body_z["absent_hours"] == 16
    assert body_z["attendance_percentage"] == "0.00"
    assert body_z["is_critical"] is True
    assert body_z["risk_level"] == RiskLevel.CRITICAL.value
    assert body_z["remaining_absent_hours_margin"] == "0.00"

    # Verifica extrato do Aluno no limiar exato 75.00%: HIGH / is_critical=True / margem 0.00
    res_b = await lote3_client.get(
        f"/api/v1/students/{stu_borderline.id}/attendance",
        headers={"Authorization": f"Bearer {stu_borderline_token}"},
    )
    assert res_b.status_code == status.HTTP_200_OK
    body_b = res_b.json()
    assert body_b["attendance_percentage"] == "75.00"
    assert body_b["is_critical"] is True
    assert body_b["risk_level"] == RiskLevel.HIGH.value
    assert body_b["remaining_absent_hours_margin"] == "0.00"
    assert body_b["percentage_margin_to_limit"] == "0.00"


@pytest.mark.asyncio
async def test_end_to_end_rubrics_recovery_edge_grades_closed_period_and_idor_security(
    lote3_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida fluxo integrado Lote 3: nota 0, nota 10, rubricas, recuperação SENAI, auditoria, bloqueio período encerrado e isolamento IDOR (BE-030)."""
    _admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="e2e030_adm",
        full_name="Administrador SENAI",
    )
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="e2e030_tchr",
        full_name="Instrutor Oficina",
    )
    stu_a_ten, stu_a_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="e2e030_a",
        full_name="Alice Nota Dez",
    )
    stu_b_zero, stu_b_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="e2e030_b",
        full_name="Bruno Nota Zero",
    )
    stu_c_rec, _stu_c_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="e2e030_c",
        full_name="Carla Recuperacao",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-E2E-030",
            name="Técnico em Mecatrônica Industrial",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MCT-2026-030",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-030",
            name="Metrologia e Oficina Mecânica",
            workload_hours=80,
            syllabus="Metrologia e usinagem",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Controle Dimensional",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-MET-030",
            title="Medição de Precisão com Micrômetro",
            category=CompetencyCategory.TECHNICAL,
        )
        enr_a = Enrollment(
            student_id=stu_a_ten.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("100.00"),
        )
        enr_b = Enrollment(
            student_id=stu_b_zero.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("100.00"),
        )
        enr_c = Enrollment(
            student_id=stu_c_rec.id,
            class_id=academic_class.id,
            enrollment_date=date(2026, 2, 1),
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("90.00"),
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject.id,
                    is_main_teacher=True,
                ),
                enr_a,
                enr_b,
                enr_c,
            ]
        )
        session.commit()
        enr_a_id, enr_b_id, enr_c_id = enr_a.id, enr_b.id, enr_c.id

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    stu_a_headers = {"Authorization": f"Bearer {stu_a_token}"}
    stu_b_headers = {"Authorization": f"Bearer {stu_b_token}"}

    # 1. Cria tarefa prática (weight=1.00) e avaliação formativa (weight=2.00)
    res_task = await lote3_client.post(
        "/api/v1/practical-tasks",
        json={
            "module_id": str(module.id),
            "class_id": str(academic_class.id),
            "title": "Peça Calibrada Ø20mm H7",
            "due_date": "2026-04-20T18:00:00Z",
            "max_score": "10.00",
            "criteria": [
                {
                    "competency_id": str(comp.id),
                    "criterion_name": "Tolerância ±0,01mm",
                    "weight": "1.00",
                    "min_acceptable_level": 3,
                }
            ],
        },
        headers=teacher_headers,
    )
    assert res_task.status_code == status.HTTP_201_CREATED
    task_id = UUID(res_task.json()["id"])
    crit_id = UUID(res_task.json()["criteria"][0]["id"])

    # Avalia rubricas:
    # - Alice: nível 5 -> 10.00
    # - Carla: nível 4 -> 8.00
    # - Bruno: sem avaliação prática (apenas nota 0.00 na prova)
    for sid, lvl in ((stu_a_ten.id, 5), (stu_c_rec.id, 4)):
        assert (
            await lote3_client.post(
                f"/api/v1/tasks/{task_id}/evaluations",
                json={
                    "student_id": str(sid),
                    "status": "EVALUATED",
                    "evaluations": [{"criterion_id": str(crit_id), "achieved_level": lvl}],
                },
                headers=teacher_headers,
            )
        ).status_code == status.HTTP_200_OK

    res_assess = await lote3_client.post(
        "/api/v1/assessments",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "title": "Prova Teórica de Metrologia",
            "assessment_type": "EXAM",
            "weight": "2.00",
            "application_date": "2026-04-15",
            "max_grade": "10.00",
        },
        headers=teacher_headers,
    )
    assert res_assess.status_code == status.HTTP_201_CREATED
    assess_id = UUID(res_assess.json()["id"])

    # 2. Lançamento inicial de notas (casos de borda 10.00 e 0.00 + recuperação)
    assert (
        await lote3_client.post(
            f"/api/v1/assessments/{assess_id}/grades",
            json={
                "grades": [
                    {"student_id": str(stu_a_ten.id), "grade_value": "10.00"},
                    {"student_id": str(stu_b_zero.id), "grade_value": "0.00"},
                    {"student_id": str(stu_c_rec.id), "grade_value": "3.00"},
                ]
            },
            headers=teacher_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 3. Retificação com nota de recuperação para Carla (3.00 -> recovery 6.50 => gera audit_log)
    res_rect = await lote3_client.post(
        f"/api/v1/assessments/{assess_id}/grades",
        json={
            "grades": [
                {
                    "student_id": str(stu_c_rec.id),
                    "grade_value": "3.00",
                    "recovery_grade": "6.50",
                    "comments": "Recuperação paralela aplicada.",
                }
            ]
        },
        headers=teacher_headers,
    )
    assert res_rect.status_code == status.HTTP_200_OK
    assert res_rect.json()["rectified_count"] == 1
    assert res_rect.json()["grades"][0]["effective_grade"] == "6.50"
    assert res_rect.json()["grades"][0]["is_recovery_applied"] is True

    with db_session_factory() as session:
        logs = list(
            session.scalars(select(AuditLog).where(AuditLog.entity == "student_grades")).all()
        )
        assert len(logs) == 1
        assert logs[0].action == "STUDENT_GRADE_RECTIFIED"

    # 4. Fechamento de médias ponderadas:
    # - Alice: (10.00*2 + 10.00*1)/3 = 10.00 (APPROVED)
    # - Bruno: (0.00*2)/2 = 0.00 (AT_RISK / CRITICAL)
    # - Carla: (6.50*2 + 8.00*1)/3 = 21.00/3 = 7.00 (APPROVED graças à recuperação SENAI)
    res_calc = await lote3_client.post(
        f"/api/v1/classes/{academic_class.id}/calculate-averages",
        headers=teacher_headers,
    )
    assert res_calc.status_code == status.HTTP_200_OK
    calc_body = res_calc.json()
    by_stu = {s["student_id"]: s for s in calc_body["students"]}

    assert by_stu[str(stu_a_ten.id)]["final_grade"] == "10.00"
    assert by_stu[str(stu_a_ten.id)]["status"] == AcademicStandingStatus.APPROVED.value

    assert by_stu[str(stu_b_zero.id)]["final_grade"] == "0.00"
    assert by_stu[str(stu_b_zero.id)]["status"] == AcademicStandingStatus.AT_RISK.value
    assert by_stu[str(stu_b_zero.id)]["risk_level"] == RiskLevel.CRITICAL.value

    assert by_stu[str(stu_c_rec.id)]["final_grade"] == "7.00"
    assert by_stu[str(stu_c_rec.id)]["status"] == AcademicStandingStatus.APPROVED.value

    with db_session_factory() as session:
        assert session.get(Enrollment, enr_a_id).final_grade == Decimal("10.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_b_id).final_grade == Decimal("0.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_c_id).final_grade == Decimal("7.00")  # type: ignore[union-attr]

    # 5. Isolamento de Segurança Anti-IDOR: Aluno A não pode ver frequência, tarefas ou boletim do Aluno B
    res_idor_att = await lote3_client.get(
        f"/api/v1/students/{stu_b_zero.id}/attendance",
        headers=stu_a_headers,
    )
    assert res_idor_att.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_att.json()["message"] == STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE

    res_idor_tasks = await lote3_client.get(
        f"/api/v1/students/{stu_b_zero.id}/pending-tasks",
        headers=stu_a_headers,
    )
    assert res_idor_tasks.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_tasks.json()["message"] == STUDENT_TASKS_IDOR_FORBIDDEN_MESSAGE

    res_idor_summary = await lote3_client.get(
        f"/api/v1/classes/{academic_class.id}/grades-summary",
        headers=stu_a_headers,
    )
    assert res_idor_summary.status_code == status.HTTP_403_FORBIDDEN

    # Aluno A e Aluno B acessam seus próprios dados com sucesso (200 OK)
    assert (
        await lote3_client.get(
            f"/api/v1/students/{stu_a_ten.id}/pending-tasks",
            headers=stu_a_headers,
        )
    ).status_code == status.HTTP_200_OK
    assert (
        await lote3_client.get(
            f"/api/v1/students/{stu_b_zero.id}/attendance",
            headers=stu_b_headers,
        )
    ).status_code == status.HTTP_200_OK

    # 6. Encerramento do período letivo (COMPLETED) bloqueia mutações com HTTP 422 CLASS_PERIOD_CLOSED
    assert (
        await lote3_client.patch(
            f"/api/v1/classes/{academic_class.id}/status",
            json={"status": "COMPLETED"},
            headers=admin_headers,
        )
    ).status_code == status.HTTP_200_OK

    res_blocked = await lote3_client.post(
        f"/api/v1/assessments/{assess_id}/grades",
        json={"grades": [{"student_id": str(stu_b_zero.id), "grade_value": "5.00"}]},
        headers=teacher_headers,
    )
    assert res_blocked.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_blocked.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
    assert res_blocked.json()["message"] == CLASS_PERIOD_CLOSED_MESSAGE
