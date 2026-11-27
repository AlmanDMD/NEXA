"""Testes unitários e de integração para Resolução e Histórico de Alertas Acadêmicos (EPIC-05 / BE-039)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

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
    AuditLog,
    Base,
    Enrollment,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import (
    AlertCategory,
    AlertStatus,
    ClassStatus,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    UserRole,
)
from app.schemas.risk_engine import AcademicAlertResolveRequestSchema
from app.schemas.user import UserProfileCreateSchema
from app.services.risk_engine_service import (
    RISK_ENGINE_ALERT_NOT_FOUND_MESSAGE,
    RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "alert_resolution_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_pragma(
        dbapi_connection: Any,
        _connection_record: Any,
    ) -> None:
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
def alert_app(
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
async def client(alert_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=alert_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as http_client:
        yield http_client


def _seed_user_with_token(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    *,
    email: str,
    role: UserRole,
    full_name: str,
    registration_number: str,
) -> tuple[User, str]:
    with db_session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=email,
            password_hash=fast_hasher.hash_password("Senai@123"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=full_name,
                registration_number=registration_number,
                phone="(11) 98888-7777",
            ),
        )
        token = create_access_token(
            subject=user.id,
            email=user.email,
            role=user.role,
        )
        return user, token


def test_alert_resolve_request_schema_validation_unit() -> None:
    """Critério 2: Valida unitariamente status permitidos (ACKNOWLEDGED/RESOLVED) e mínimo de 10 caracteres em resolution_notes."""
    ack_payload = AcademicAlertResolveRequestSchema(
        status="ACKNOWLEDGED",
        resolution_notes="  Contato inicial realizado com o aluno na bancada de metrologia.  ",
    )
    assert ack_payload.status == AlertStatus.ACKNOWLEDGED
    assert ack_payload.resolution_notes.startswith("Contato inicial")

    res_payload = AcademicAlertResolveRequestSchema(
        status="RESOLVED",
        resolution_notes="Estudante concluiu o plano de reposição prática e atingiu média mínima.",
    )
    assert res_payload.status == AlertStatus.RESOLVED

    # Aceita verbos equivalentes enviados pelo front-end
    ack_verb = AcademicAlertResolveRequestSchema(
        status="ACKNOWLEDGE",
        resolution_notes="Assumindo o acompanhamento pedagógico do alerta.",
    )
    assert ack_verb.status == AlertStatus.ACKNOWLEDGED

    # Rejeita status ACTIVE
    with pytest.raises(Exception):
        AcademicAlertResolveRequestSchema(
            status="ACTIVE",
            resolution_notes="Tentativa inválida de reativar alerta manualmente.",
        )

    # Rejeita resolution_notes menor que 10 caracteres
    with pytest.raises(Exception):
        AcademicAlertResolveRequestSchema(
            status="RESOLVED",
            resolution_notes="Curto",
        )


@pytest.mark.asyncio
async def test_resolve_academic_alert_acknowledge_resolve_audit_and_360_history(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios 1, 2, 3 e DoD do BE-039:

    - PATCH /api/v1/alerts/{id}/resolve (HTTP 200) para ACKNOWLEDGED e RESOLVED.
    - Exige resolution_notes com mínimo de 10 caracteres (400 VALIDATION_ERROR caso contrário).
    - Grava resolved_by com o ID do professor autenticado e registra auditoria em audit_logs.
    - Mantém histórico completo de intervenções na Ficha 360° do aluno e em GET /api/v1/alerts/{id}/history.
    - Bloqueia docente não alocado (403), estudante (403) e alerta inexistente (404).
    """
    teacher, teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.mentoria@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Carlos Mentoria",
        registration_number="PROF-2026-0391",
    )
    other_teacher, other_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.externo039@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Externo 039",
        registration_number="PROF-2026-0392",
    )
    _coord, coord_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord.039@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coord. Pedagógico 039",
        registration_number="COORD-2026-0391",
    )
    student, student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.alerta039@senai.br",
        role=UserRole.STUDENT,
        full_name="João Pedro Alerta",
        registration_number="ALU-2026-0391",
    )

    with db_session_factory() as session:
        course = CourseRepository(session=session).create(
            name="Técnico em Eletromecânica",
            code="TEC-ELE-039",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session=session).create(
            course_id=course.id,
            code="ELE-2026-039",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 15),
        )
        subject = SubjectRepository(session=session).create(
            course_id=course.id,
            name="Manutenção Mecânica Industrial",
            code="MAN-MEC-039",
            workload_hours=80,
            is_active=True,
        )
        enrollment = Enrollment(
            student_id=student.id,
            class_id=academic_class.id,
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("72.00"),
            final_grade=Decimal("5.40"),
        )
        session.add(enrollment)
        session.add(
            TeacherAssignment(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            )
        )
        session.flush()

        alert = AcademicAlert(
            student_id=student.id,
            enrollment_id=enrollment.id,
            class_id=academic_class.id,
            module_id=None,
            risk_level=RiskLevel.CRITICAL,
            alert_category=AlertCategory.ATTENDANCE,
            explainable_reason="Frequência acumulada em 72.00%, abaixo do limiar mínimo legal de 75.00%.",
            metric_snapshot={
                "attendance_percentage": "72.00",
                "rule_code": "ATTENDANCE_CRITICAL_BELOW_75",
            },
            status=AlertStatus.ACTIVE,
        )
        session.add(alert)
        session.commit()
        alert_id = alert.id

    # 1. Validação: resolution_notes com menos de 10 caracteres retorna HTTP 400 VALIDATION_ERROR
    short_notes_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "status": "ACKNOWLEDGED",
            "resolution_notes": "Em curso",
        },
    )
    assert short_notes_res.status_code == status.HTTP_400_BAD_REQUEST
    assert short_notes_res.json()["error"] == "VALIDATION_ERROR"

    # 2. Segurança RBAC: Estudante recebe 403 Forbidden
    student_forbidden_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "status": "RESOLVED",
            "resolution_notes": "Tentativa de estudante encerrar seu próprio alerta.",
        },
    )
    assert student_forbidden_res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Segurança Contextual: Professor não alocado na turma recebe 403 Forbidden
    other_teacher_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {other_teacher_token}"},
        json={
            "status": "ACKNOWLEDGED",
            "resolution_notes": "Tentativa de professor sem atribuição na turma.",
        },
    )
    assert other_teacher_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        other_teacher_res.json()["message"] == RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE
    )

    # 4. Alerta inexistente retorna 404 Not Found
    not_found_res = await client.patch(
        f"/api/v1/alerts/{uuid4()}/resolve",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={
            "status": "RESOLVED",
            "resolution_notes": "Tentativa em identificador de alerta inexistente.",
        },
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == RISK_ENGINE_ALERT_NOT_FOUND_MESSAGE

    # 5. Professor alocado assume acompanhamento do alerta (ACKNOWLEDGED) -> HTTP 200
    ack_notes = "Acolhimento presencial realizado; definido plano de reposição de faltas na oficina."
    ack_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "status": "ACKNOWLEDGED",
            "resolution_notes": ack_notes,
        },
    )
    assert ack_res.status_code == status.HTTP_200_OK
    ack_body = ack_res.json()
    assert ack_body["id"] == str(alert_id)
    assert ack_body["alert_id"] == str(alert_id)
    assert ack_body["previous_status"] == "ACTIVE"
    assert ack_body["status"] == "ACKNOWLEDGED"
    assert ack_body["resolved_by"] == str(teacher.id)
    assert ack_body["resolution_notes"] == ack_notes
    assert ack_body["resolver"]["full_name"] == "Prof. Carlos Mentoria"
    assert ack_body["audit_log_id"] is not None
    assert len(ack_body["intervention_history"]) == 1
    assert ack_body["intervention_history"][0]["action"] == "ACADEMIC_ALERT_ACKNOWLEDGED"
    assert ack_body["intervention_history"][0]["new_status"] == "ACKNOWLEDGED"

    # 6. Professor encerra o alerta após conclusão da intervenção (RESOLVED) -> HTTP 200
    resolve_notes = "Aluno concluiu todas as atividades de reposição e regularizou presença acima de 78%."
    resolve_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "status": "RESOLVED",
            "resolution_notes": resolve_notes,
        },
    )
    assert resolve_res.status_code == status.HTTP_200_OK
    resolve_body = resolve_res.json()
    assert resolve_body["previous_status"] == "ACKNOWLEDGED"
    assert resolve_body["status"] == "RESOLVED"
    assert resolve_body["resolved_by"] == str(teacher.id)
    assert resolve_body["resolution_notes"] == resolve_notes
    assert len(resolve_body["intervention_history"]) == 2
    assert resolve_body["intervention_history"][0]["new_status"] == "ACKNOWLEDGED"
    assert resolve_body["intervention_history"][1]["action"] == "ACADEMIC_ALERT_RESOLVED"
    assert resolve_body["intervention_history"][1]["new_status"] == "RESOLVED"

    # 7. Verifica persistência imutável em audit_logs no banco
    with db_session_factory() as session:
        audit_entries = list(
            session.scalars(
                select(AuditLog)
                .where(
                    AuditLog.entity == "academic_alerts",
                    AuditLog.entity_id == str(alert_id),
                )
                .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
            ).all()
        )
        assert len(audit_entries) == 2
        assert audit_entries[0].user_id == teacher.id
        assert audit_entries[0].action == "ACADEMIC_ALERT_ACKNOWLEDGED"
        assert audit_entries[0].old_values["status"] == "ACTIVE"
        assert audit_entries[0].new_values["status"] == "ACKNOWLEDGED"
        assert audit_entries[0].new_values["resolution_notes"] == ack_notes

        assert audit_entries[1].user_id == teacher.id
        assert audit_entries[1].action == "ACADEMIC_ALERT_RESOLVED"
        assert audit_entries[1].old_values["status"] == "ACKNOWLEDGED"
        assert audit_entries[1].new_values["status"] == "RESOLVED"
        assert audit_entries[1].new_values["resolution_notes"] == resolve_notes

    # 8. Verifica endpoint dedicado de histórico do alerta GET /api/v1/alerts/{id}/history
    history_res = await client.get(
        f"/api/v1/alerts/{alert_id}/history",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert history_res.status_code == status.HTTP_200_OK
    history_items = history_res.json()
    assert len(history_items) == 2
    assert history_items[0]["actor_name"] == "Prof. Carlos Mentoria"
    assert history_items[1]["resolution_notes"] == resolve_notes

    # 9. Verifica manutenção do histórico completo na Ficha 360° do aluno (GET /api/v1/students/{id}/360)
    s360_res = await client.get(
        f"/api/v1/students/{student.id}/360",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert s360_res.status_code == status.HTTP_200_OK
    s360_body = s360_res.json()
    # Alerta resolvido não aparece mais como ativo
    assert s360_body["active_alerts"] == []
    # Histórico completo preserva o alerta e suas 2 intervenções pedagógicas
    assert len(s360_body["alerts_history"]) == 1
    hist_alert = s360_body["alerts_history"][0]
    assert hist_alert["id"] == str(alert_id)
    assert hist_alert["status"] == "RESOLVED"
    assert hist_alert["resolved_by"] == str(teacher.id)
    assert hist_alert["resolved_by_name"] == "Prof. Carlos Mentoria"
    assert hist_alert["resolution_notes"] == resolve_notes
    assert len(hist_alert["interventions"]) == 2
