"""Testes unitários e de integração para o Motor de Identificação Precoce de Risco Acadêmico (BE-032)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, select
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
from app.services.risk_engine_service import (
    RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE,
    RISK_ENGINE_MODULE_NOT_FOUND_MESSAGE,
    RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE,
    StudentRiskMetricsInput,
    evaluate_student_risk_rules,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL e views analíticas."""
    db_file = tmp_path / "risk_engine_test.db"
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
def risk_app(
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
async def risk_client(risk_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=risk_app)
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


class TestRiskEngineDeterministicRulesUnit:
    """Testes unitários cobrindo todos os graus (LOW, MODERATE, HIGH, CRITICAL), explicabilidade e diretriz ética (BE-032)."""

    def test_low_risk_when_all_metrics_healthy(self) -> None:
        """Grau LOW: frequência >= 78%, < 2 tarefas atrasadas e média >= passing_score -> nenhum alerta."""
        risk, rules = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("85.00"),
                total_lesson_hours=20,
                attended_hours=17,
                absent_hours=3,
                late_tasks_count=1,
                total_tasks_count=4,
                overall_average=Decimal("7.50"),
                passing_score=Decimal("6.00"),
            )
        )
        assert risk == RiskLevel.LOW
        assert rules == []

    def test_moderate_risk_when_two_practical_tasks_late(self) -> None:
        """Grau MODERATE: 2 tarefas práticas em atraso (LATE) com frequência e média normais."""
        risk, rules = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("90.00"),
                late_tasks_count=2,
                total_tasks_count=5,
                overall_average=Decimal("8.00"),
                passing_score=Decimal("6.00"),
            )
        )
        assert risk == RiskLevel.MODERATE
        assert len(rules) == 1
        rule = rules[0]
        assert rule.alert_category == AlertCategory.PENDING_TASKS
        assert rule.risk_level == RiskLevel.MODERATE
        assert "2 atividades práticas de oficina em atraso" in rule.explainable_reason
        assert "não constitui reprovação automática" in rule.explainable_reason
        assert rule.metric_snapshot["late_tasks_count"] == 2
        assert "ethical_disclaimer" in rule.metric_snapshot

    @pytest.mark.parametrize("att_rate", [Decimal("75.00"), Decimal("76.50"), Decimal("77.99")])
    def test_high_risk_when_attendance_in_preventive_band_75_to_78(
        self,
        att_rate: Decimal,
    ) -> None:
        """Grau HIGH (Regra 1 preventiva): frequência entre 75.00% e 77.99%."""
        risk, rules = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=att_rate,
                total_lesson_hours=40,
                attended_hours=31,
                absent_hours=9,
            )
        )
        assert risk == RiskLevel.HIGH
        assert len(rules) == 1
        assert rules[0].alert_category == AlertCategory.ATTENDANCE
        assert rules[0].risk_level == RiskLevel.HIGH
        assert str(att_rate) in rules[0].explainable_reason

    def test_high_risk_when_three_or_more_tasks_late_or_grade_below_passing(self) -> None:
        """Grau HIGH (Regras 2 e 3): >= 3 tarefas atrasadas e média parcial abaixo de passing_score."""
        risk, rules = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("92.00"),
                late_tasks_count=3,
                total_tasks_count=4,
                overall_average=Decimal("4.80"),
                passing_score=Decimal("6.00"),
            )
        )
        assert risk == RiskLevel.HIGH
        assert len(rules) == 2
        by_cat = {r.alert_category: r for r in rules}
        assert by_cat[AlertCategory.PENDING_TASKS].risk_level == RiskLevel.HIGH
        assert by_cat[AlertCategory.GRADE_DROP].risk_level == RiskLevel.HIGH
        assert by_cat[AlertCategory.GRADE_DROP].metric_snapshot["grade_deficit"] == "1.20"
        assert "4.80" in by_cat[AlertCategory.GRADE_DROP].explainable_reason

    @pytest.mark.parametrize("att_rate", [Decimal("74.99"), Decimal("60.00"), Decimal("0.00")])
    def test_critical_risk_when_attendance_below_75_percent(
        self,
        att_rate: Decimal,
    ) -> None:
        """Grau CRITICAL (Regra 1 crítica): frequência abaixo de 75.00%."""
        risk, rules = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=att_rate,
                total_lesson_hours=20,
                attended_hours=12,
                absent_hours=8,
                late_tasks_count=2,
                overall_average=Decimal("5.00"),
                passing_score=Decimal("6.00"),
            )
        )
        assert risk == RiskLevel.CRITICAL
        assert len(rules) == 3
        by_cat = {r.alert_category: r for r in rules}
        assert by_cat[AlertCategory.ATTENDANCE].risk_level == RiskLevel.CRITICAL
        assert "abaixo do limiar mínimo legal de 75.00%" in by_cat[AlertCategory.ATTENDANCE].explainable_reason


@pytest.mark.asyncio
async def test_risk_engine_integration_all_levels_deduplication_and_auto_resolution(
    risk_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida integração do RiskEngineService: todos os graus (LOW, MODERATE, HIGH, CRITICAL), sem alertas duplicados e auto-resolução (BE-032)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="risk032_t",
        full_name="Instrutor Motor Risco",
    )
    stu_low, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="risk032_low",
        full_name="Aluno Regular Low",
    )
    stu_mod, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="risk032_mod",
        full_name="Aluno Atraso Moderate",
    )
    stu_high, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="risk032_high",
        full_name="Aluno Nota Baixa High",
    )
    stu_crit, stu_crit_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="risk032_crit",
        full_name="Aluno Faltas Critical",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-RSK-032",
            name="Técnico em Usinagem Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="USI-2026-032",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-032",
            name="Tornearia Mecânica",
            workload_hours=80,
            syllabus="Operações de torno",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Tornearia de Precisão",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        comp = CompetencyRepository(session).create(
            code="COMP-RSK-032",
            title="Tolerância ISO H7",
            category=CompetencyCategory.TECHNICAL,
        )
        session.add(
            TeacherAssignment(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
                is_main_teacher=True,
            )
        )
        for stu in (stu_low, stu_mod, stu_high, stu_crit):
            session.add(
                Enrollment(
                    student_id=stu.id,
                    class_id=academic_class.id,
                    enrollment_date=date(2026, 2, 1),
                    status=EnrollmentStatus.ACTIVE,
                )
            )
        session.commit()

    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Cria 2 tarefas práticas com due_date expirado (2020):
    # Avaliamos stu_low, stu_high e stu_crit nas 2 tarefas (para que não fiquem LATE para eles),
    # deixando apenas stu_mod com 2 tarefas LATE -> stu_mod terá exatamente grau MODERATE!
    task_ids_and_crits: list[tuple[UUID, UUID]] = []
    for idx in (1, 2):
        res_t = await risk_client.post(
            "/api/v1/practical-tasks",
            json={
                "module_id": str(module.id),
                "class_id": str(academic_class.id),
                "title": f"Peça Expirada 0{idx}",
                "due_date": f"2020-04-1{idx}T18:00:00Z",
                "max_score": "10.00",
                "criteria": [
                    {
                        "competency_id": str(comp.id),
                        "criterion_name": f"Medição 0{idx}",
                        "weight": "1.00",
                        "min_acceptable_level": 3,
                    }
                ],
            },
            headers=headers,
        )
        assert res_t.status_code == status.HTTP_201_CREATED
        task_ids_and_crits.append(
            (UUID(res_t.json()["id"]), UUID(res_t.json()["criteria"][0]["id"]))
        )

    for tid, cid in task_ids_and_crits:
        # stu_low e stu_crit tiram nível 4 (8.00 >= 6.00); stu_high tira nível 2 (4.00 < 6.00 -> GRADE_DROP HIGH)
        for stu_id, lvl in ((stu_low.id, 4), (stu_crit.id, 4), (stu_high.id, 2)):
            assert (
                await risk_client.post(
                    f"/api/v1/tasks/{tid}/evaluations",
                    json={
                        "student_id": str(stu_id),
                        "status": "EVALUATED",
                        "evaluations": [{"criterion_id": str(cid), "achieved_level": lvl}],
                    },
                    headers=headers,
                )
            ).status_code == status.HTTP_200_OK

    # 2. Cria aula e registra chamada onde apenas stu_crit falta (0% < 75% -> CRITICAL disparado pelo BE-022!)
    res_l = await risk_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "lesson_date": "2026-03-15",
            "workload_hours": 4,
            "topic_summary": "Aula de bancada",
        },
        headers=headers,
    )
    assert res_l.status_code == status.HTTP_201_CREATED
    lesson_id = res_l.json()["id"]

    assert (
        await risk_client.post(
            f"/api/v1/lessons/{lesson_id}/attendance",
            json={
                "records": [
                    {"student_id": str(stu_low.id), "status": "PRESENT"},
                    {"student_id": str(stu_mod.id), "status": "PRESENT"},
                    {"student_id": str(stu_high.id), "status": "PRESENT"},
                    {"student_id": str(stu_crit.id), "status": "ABSENT"},
                ]
            },
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    # 3. Executa avaliação completa da turma via endpoint:
    # - stu_low -> LOW (100% presença, 0 atrasos, média 8.00)
    # - stu_mod -> MODERATE (100% presença, 2 tarefas LATE)
    # - stu_high -> HIGH (100% presença, 0 atrasos, média 4.00 < 6.00)
    # - stu_crit -> CRITICAL (0% presença < 75%)
    eval_1 = await risk_client.post(
        f"/api/v1/dashboard/teacher/classes/{academic_class.id}/evaluate-risk",
        headers=headers,
    )
    assert eval_1.status_code == status.HTTP_200_OK
    b1 = eval_1.json()
    assert b1["total_students_evaluated"] == 4
    assert b1["low_risk_count"] == 1
    assert b1["moderate_risk_count"] == 1
    assert b1["high_risk_count"] == 1
    assert b1["critical_risk_count"] == 1
    assert b1["at_risk_students_count"] == 3

    # 4. Reexecução idempotente: ZERO novos alertas criados (apenas atualiza os 3 abertos sem duplicar!)
    eval_2 = await risk_client.post(
        f"/api/v1/dashboard/teacher/classes/{academic_class.id}/evaluate-risk",
        headers=headers,
    )
    assert eval_2.status_code == status.HTTP_200_OK
    b2 = eval_2.json()
    assert b2["created_alerts_count"] == 0
    assert b2["updated_alerts_count"] == 3

    with db_session_factory() as session:
        active_alerts = list(
            session.scalars(
                select(AcademicAlert).where(
                    AcademicAlert.class_id == academic_class.id,
                    AcademicAlert.status == AlertStatus.ACTIVE,
                )
            ).all()
        )
        assert len(active_alerts) == 3
        for al in active_alerts:
            assert len(al.explainable_reason) > 20
            assert al.metric_snapshot is not None
            assert "rule_code" in al.metric_snapshot

    # 5. Recuperação automática: retifica chamada de stu_crit para PRESENT -> alerta ATTENDANCE é auto-resolvido!
    assert (
        await risk_client.post(
            f"/api/v1/lessons/{lesson_id}/attendance",
            json={"records": [{"student_id": str(stu_crit.id), "status": "PRESENT"}]},
            headers=headers,
        )
    ).status_code == status.HTTP_200_OK

    with db_session_factory() as session:
        crit_alerts = list(
            session.scalars(
                select(AcademicAlert).where(AcademicAlert.student_id == stu_crit.id)
            ).all()
        )
        assert len(crit_alerts) == 1
        assert crit_alerts[0].status == AlertStatus.RESOLVED

    # 6. RBAC e 404 na rota evaluate-risk
    assert (
        await risk_client.post(
            f"/api/v1/dashboard/teacher/classes/{academic_class.id}/evaluate-risk"
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await risk_client.post(
            f"/api/v1/dashboard/teacher/classes/{academic_class.id}/evaluate-risk",
            headers={"Authorization": f"Bearer {stu_crit_token}"},
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    _other_t, other_t_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="risk032_out",
        full_name="Prof Outra Turma",
    )
    res_forb = await risk_client.post(
        f"/api/v1/dashboard/teacher/classes/{academic_class.id}/evaluate-risk",
        headers={"Authorization": f"Bearer {other_t_token}"},
    )
    assert res_forb.status_code == status.HTTP_403_FORBIDDEN
    assert res_forb.json()["message"] == RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE

    _adm, adm_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="risk032_adm",
        full_name="Admin Risk",
    )
    res_404 = await risk_client.post(
        f"/api/v1/dashboard/teacher/classes/{uuid4()}/evaluate-risk",
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE



@pytest.mark.asyncio
async def test_at_risk_students_listing_ordering_filters_pagination_and_rbac(
    risk_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/dashboard/teacher/at-risk: severidade, filtros, paginação, explicabilidade e RBAC (BE-033)."""
    teacher_a, teacher_a_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ar033_ta", full_name="Prof Turma A"
    )
    teacher_b, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ar033_tb", full_name="Prof Turma B"
    )
    _teacher_c, teacher_c_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ar033_tc", full_name="Prof Sem Turma"
    )
    _coord, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="ar033_co", full_name="Coordenação"
    )
    _adm, adm_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="ar033_ad", full_name="Admin"
    )
    students: list[tuple[User, str]] = [
        _create_user_and_token(
            db_session_factory,
            fast_hasher,
            role=UserRole.STUDENT,
            suffix=f"ar033_s{idx}",
            full_name=name,
        )
        for idx, name in enumerate(
            ("Ana Critica", "Bruno Nota", "Carla Oficina", "Diego Autoavaliacao", "Eva Outra Turma"),
            start=1,
        )
    ]
    s1, s2, s3, s4, s5 = (s for s, _ in students)
    student_token = students[0][1]

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-RSK-033",
            name="Técnico em Mecânica",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        class_repo = AcademicClassRepository(session)
        class_a = class_repo.create(
            course_id=course.id,
            code="MEC-2026-033A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        class_b = class_repo.create(
            course_id=course.id,
            code="MEC-2026-033B",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-033",
            name="Metrologia Dimensional",
            workload_hours=60,
            syllabus="Instrumentos de medição",
            is_active=True,
        )
        module = LearningModuleRepository(session).create(
            subject_id=subject.id,
            title="Metrologia",
            order_index=1,
            practical_hours=30,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher_a.id, class_id=class_a.id, subject_id=subject.id, is_main_teacher=True
                ),
                TeacherAssignment(
                    teacher_id=teacher_b.id, class_id=class_b.id, subject_id=subject.id, is_main_teacher=True
                ),
            ]
        )
        enrollments: dict[UUID, Enrollment] = {}
        for stu, klass in ((s1, class_a), (s2, class_a), (s3, class_a), (s4, class_a), (s5, class_b)):
            enr = Enrollment(
                student_id=stu.id,
                class_id=klass.id,
                enrollment_date=date(2026, 2, 1),
                status=EnrollmentStatus.ACTIVE,
            )
            session.add(enr)
            enrollments[stu.id] = enr
        session.flush()

        def _alert(
            stu: User,
            klass_id: UUID,
            level: RiskLevel,
            category: AlertCategory,
            *,
            module_id: UUID | None = None,
            alert_status: AlertStatus = AlertStatus.ACTIVE,
            snapshot: dict[str, Any] | None = None,
        ) -> AcademicAlert:
            return AcademicAlert(
                student_id=stu.id,
                enrollment_id=enrollments[stu.id].id,
                class_id=klass_id,
                module_id=module_id,
                risk_level=level,
                alert_category=category,
                explainable_reason=f"Indicador de atenção pedagógica {category.value} nível {level.value}.",
                metric_snapshot=snapshot,
                status=alert_status,
            )

        # Inserção fora de ordem para garantir que a ordenação seja por severidade
        session.add_all(
            [
                _alert(s4, class_a.id, RiskLevel.LOW, AlertCategory.SELF_EVAL_GAP),
                _alert(s4, class_a.id, RiskLevel.CRITICAL, AlertCategory.ATTENDANCE, alert_status=AlertStatus.RESOLVED),
                _alert(s3, class_a.id, RiskLevel.MODERATE, AlertCategory.PENDING_TASKS, module_id=module.id),
                _alert(
                    s1,
                    class_a.id,
                    RiskLevel.CRITICAL,
                    AlertCategory.ATTENDANCE,
                    snapshot={"recommended_action": "Convocar estudante para acolhimento imediato."},
                ),
                _alert(s2, class_a.id, RiskLevel.HIGH, AlertCategory.GRADE_DROP, module_id=module.id),
                _alert(s5, class_b.id, RiskLevel.HIGH, AlertCategory.ATTENDANCE),
            ]
        )
        session.commit()

    url = "/api/v1/dashboard/teacher/at-risk"
    coord_h = {"Authorization": f"Bearer {coord_token}"}

    # 1. Coordenação: visão global, ordenação CRITICAL -> HIGH -> MODERATE -> LOW e contadores
    res = await risk_client.get(url, headers=coord_h)
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["total"] == 5
    assert body["page"] == 1
    assert [i["risk_level"] for i in body["data"]] == ["CRITICAL", "HIGH", "HIGH", "MODERATE", "LOW"]
    assert (body["critical_count"], body["high_count"], body["moderate_count"], body["low_count"]) == (1, 2, 1, 1)
    assert "nunca constitui reprovação" in body["ethical_disclaimer"]
    assert all(i["status"] == "ACTIVE" for i in body["data"])

    critical_item = body["data"][0]
    assert critical_item["student"]["full_name"] == "Ana Critica"
    assert critical_item["academic_class"]["code"] == "MEC-2026-033A"
    assert critical_item["recommended_action"] == "Convocar estudante para acolhimento imediato."
    assert critical_item["explainable_reason"].startswith("Indicador de atenção pedagógica")
    assert critical_item["module"] is None
    assert critical_item["suggested_pedagogical_action"]
    assert critical_item["ethical_disclaimer"]
    assert critical_item["alert_id"] == critical_item["id"]
    metrics = critical_item["current_metrics"]
    assert set(metrics) >= {
        "overall_average",
        "attendance_percentage",
        "pending_tasks_count",
        "late_tasks_count",
        "completed_tasks_count",
        "active_alerts_count",
    }

    # 2. Filtro por módulo com ação pedagógica contextual
    res_mod = await risk_client.get(url, params={"module_id": str(module.id)}, headers=coord_h)
    assert res_mod.status_code == status.HTTP_200_OK
    mod_items = res_mod.json()["data"]
    assert [i["risk_level"] for i in mod_items] == ["HIGH", "MODERATE"]
    for item in mod_items:
        assert item["module"]["title"] == "Metrologia"
        assert item["module"]["subject_code"] == "MET-033"
        assert item["suggested_pedagogical_action"] == "Agendar mentoria prática no módulo de Metrologia."

    # 3. Filtros por risk_level, alert_category, class_id e busca textual
    res_high = await risk_client.get(url, params={"risk_level": "HIGH"}, headers=coord_h)
    assert res_high.json()["total"] == 2
    res_cat = await risk_client.get(url, params={"alert_category": "ATTENDANCE"}, headers=coord_h)
    assert [i["risk_level"] for i in res_cat.json()["data"]] == ["CRITICAL", "HIGH"]
    res_cls = await risk_client.get(url, params={"class_id": str(class_b.id)}, headers=coord_h)
    assert [i["student_id"] for i in res_cls.json()["data"]] == [str(s5.id)]
    res_search = await risk_client.get(url, params={"search": "carla"}, headers=coord_h)
    assert [i["student_id"] for i in res_search.json()["data"]] == [str(s3.id)]

    # 4. Paginação
    res_page = await risk_client.get(url, params={"page": 2, "limit": 2}, headers=coord_h)
    page_body = res_page.json()
    assert page_body["total"] == 5
    assert page_body["limit"] == 2
    assert [i["risk_level"] for i in page_body["data"]] == ["HIGH", "MODERATE"]

    # 5. Validações de entrada e 404
    assert (await risk_client.get(url, params={"risk_level": "EXTREME"}, headers=coord_h)).status_code == (
        status.HTTP_400_BAD_REQUEST
    )
    assert (await risk_client.get(url, params={"limit": 101}, headers=coord_h)).status_code == (
        status.HTTP_400_BAD_REQUEST
    )
    adm_h = {"Authorization": f"Bearer {adm_token}"}
    res_404_cls = await risk_client.get(url, params={"class_id": str(uuid4())}, headers=adm_h)
    assert res_404_cls.status_code == status.HTTP_404_NOT_FOUND
    assert res_404_cls.json()["message"] == RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE
    res_404_mod = await risk_client.get(url, params={"module_id": str(uuid4())}, headers=adm_h)
    assert res_404_mod.status_code == status.HTTP_404_NOT_FOUND
    assert res_404_mod.json()["message"] == RISK_ENGINE_MODULE_NOT_FOUND_MESSAGE
    assert (await risk_client.get(url, headers=adm_h)).json()["total"] == 5

    # 6. RBAC: professor vê apenas suas turmas
    ta_h = {"Authorization": f"Bearer {teacher_a_token}"}
    res_ta = await risk_client.get(url, headers=ta_h)
    assert res_ta.status_code == status.HTTP_200_OK
    ta_body = res_ta.json()
    assert ta_body["total"] == 4
    assert {i["class_id"] for i in ta_body["data"]} == {str(class_a.id)}
    assert (ta_body["critical_count"], ta_body["high_count"]) == (1, 1)

    res_ta_other = await risk_client.get(url, params={"class_id": str(class_b.id)}, headers=ta_h)
    assert res_ta_other.status_code == status.HTTP_403_FORBIDDEN
    assert res_ta_other.json()["message"] == RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE

    res_tc = await risk_client.get(url, headers={"Authorization": f"Bearer {teacher_c_token}"})
    assert res_tc.status_code == status.HTTP_403_FORBIDDEN

    assert (
        await risk_client.get(url, headers={"Authorization": f"Bearer {student_token}"})
    ).status_code == status.HTTP_403_FORBIDDEN
    assert (await risk_client.get(url)).status_code == status.HTTP_401_UNAUTHORIZED
