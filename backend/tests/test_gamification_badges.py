"""Testes unitários e de integração para Conquistas, Níveis de Habilidade e Badges Desbloqueadas pelo Estudante (BE-046)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

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
    Competency,
    Enrollment,
    GamificationBadge,
    StudentAchievement,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.enums import (
    ClassStatus,
    CompetencyCategory,
    EnrollmentStatus,
    Shift,
    SkillLevel,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.gamification_service import compute_skill_level_from_xp


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "gamification_badges_test.db"
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
def gamification_app(
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
async def client(gamification_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=gamification_app)
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
        user = AuthRepository(session=session).create_user(
            email=email,
            password_hash=fast_hasher.hash_password("Senai@2026!Secret"),
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


class TestGamificationUnitValidations:
    """Testes unitários de regras de XP, níveis de habilidade e modelos ORM (BE-046)."""

    def test_compute_skill_level_from_xp_tiers(self) -> None:
        # 0 XP -> Nível 1 Iniciante
        tier_0, next_0, rem_0, pct_0 = compute_skill_level_from_xp(0)
        assert tier_0.level_key == SkillLevel.BEGINNER
        assert tier_0.level_number == 1
        assert next_0 is not None and next_0.level_key == SkillLevel.PRACTITIONER
        assert rem_0 == 150
        assert pct_0 == Decimal("0.00")

        # 225 XP -> Nível 2 Praticante (metade do caminho entre 150 e 300)
        tier_2, next_2, rem_2, pct_2 = compute_skill_level_from_xp(225)
        assert tier_2.level_key == SkillLevel.PRACTITIONER
        assert tier_2.level_number == 2
        assert next_2 is not None and next_2.level_key == SkillLevel.PROFICIENT
        assert rem_2 == 75
        assert pct_2 == Decimal("50.00")

        # 370 XP -> Nível 3 Proficiente
        tier_3, next_3, rem_3, pct_3 = compute_skill_level_from_xp(370)
        assert tier_3.level_key == SkillLevel.PROFICIENT
        assert tier_3.level_number == 3
        assert next_3 is not None and next_3.level_key == SkillLevel.SPECIALIST
        assert rem_3 == 130
        assert pct_3 == Decimal("35.00")

        # 600 XP -> Nível 4 Especialista (nível máximo)
        tier_4, next_4, rem_4, pct_4 = compute_skill_level_from_xp(600)
        assert tier_4.level_key == SkillLevel.SPECIALIST
        assert tier_4.level_number == 4
        assert next_4 is None
        assert rem_4 == 0
        assert pct_4 == Decimal("100.00")

    def test_orm_models_validation(self) -> None:
        badge = GamificationBadge(
            code="  badge-metrologia-100  ",
            title="  Mestre do Micrômetro  ",
            description="  Excelência em medição centesimal na oficina SENAI.  ",
            criteria_explanation="  Atingir nível verificado >= 4.50 nas atividades práticas de Metrologia.  ",
            icon_name="  micrometer-star  ",
            xp_reward=150,
            is_active=True,
        )
        assert badge.code == "BADGE-METROLOGIA-100"
        assert badge.title == "Mestre do Micrômetro"
        assert badge.xp_reward == 150

        with pytest.raises(ValueError, match="pelo menos 15 caracteres"):
            GamificationBadge(
                code="BADGE-CURTA",
                title="Badge Teste",
                description="Descrição válida com mais de dez caracteres.",
                criteria_explanation="Regra curta",
                icon_name="award",
                xp_reward=100,
            )

        with pytest.raises(ValueError, match="entre 1 e 5000"):
            GamificationBadge(
                code="BADGE-XP-ZERO",
                title="Badge XP Inválido",
                description="Descrição válida com mais de dez caracteres.",
                criteria_explanation="Critério transparente com mais de quinze caracteres.",
                icon_name="award",
                xp_reward=0,
            )

        ach = StudentAchievement(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            badge_id=uuid4(),
            unlocked_at=datetime(2026, 6, 15, 18, 0, tzinfo=timezone.utc),
            origin_reference="  Módulo 01: Metrologia Dimensional (Nota 9.80)  ",
        )
        assert ach.origin_reference == "Módulo 01: Metrologia Dimensional (Nota 9.80)"

        with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
            StudentAchievement(
                student_id=uuid4(),
                enrollment_id=uuid4(),
                badge_id=uuid4(),
                origin_reference="ab",
            )


@pytest.mark.asyncio
async def test_get_gamification_badges_catalog_unlocked_upcoming_criteria_and_no_punitive_ranking(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/gamification/badges: catálogo cruzado com conquistas do aluno, criteria_explanation e zero ranking vexatório (BE-046)."""
    student_a, student_a_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.a046@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Conquistador A",
        registration_number="ALU-046-A",
    )
    student_b, student_b_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.b046@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Iniciante B",
        registration_number="ALU-046-B",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-046",
            name="Técnico em Mecânica 046",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-046A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        comp_met = Competency(
            code="COMP-MET-046",
            title="Medição com Micrômetro Centesimal",
            description="Medição externa e interna",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_tor = Competency(
            code="COMP-TOR-046",
            title="Operação de Torno Mecânico",
            description="Faceamento e cilindramento",
            category=CompetencyCategory.TECHNICAL,
        )
        session.add_all([comp_met, comp_tor])
        session.flush()

        b_met = GamificationBadge(
            code="BADGE-METROLOGIA-100",
            title="Mestre do Micrômetro",
            description="Excelência em medição centesimal com micrômetro externo.",
            criteria_explanation="Atingir nível verificado >= 4.50 nas atividades práticas de Metrologia Dimensional.",
            icon_name="micrometer-star",
            xp_reward=150,
            competency_id=comp_met.id,
            is_active=True,
        )
        b_paq = GamificationBadge(
            code="BADGE-PAQUIMETRO-PRO",
            title="Olho de Precisão H7",
            description="Domínio consistente na inspeção dimensional com paquímetro universal.",
            criteria_explanation="Concluir entrega prática de controle dimensional com nota >= 9.00.",
            icon_name="caliper-check",
            xp_reward=120,
            competency_id=comp_met.id,
            is_active=True,
        )
        b_tor = GamificationBadge(
            code="BADGE-TORNEARIA-EXACT",
            title="Especialista em Tornearia Cilíndrica",
            description="Execução precisa de faceamento e cilindramento em torno mecânico.",
            criteria_explanation="Obter avaliação docente nível 5 nos critérios de acabamento e tolerância em Tornearia.",
            icon_name="lathe-award",
            xp_reward=200,
            competency_id=comp_tor.id,
            is_active=True,
        )
        b_assid = GamificationBadge(
            code="BADGE-ASSIDUIDADE-100",
            title="Presença de Aço 100%",
            description="Assiduidade integral em aulas teóricas e oficinas práticas.",
            criteria_explanation="Registrar 100% de presença efetiva (zero faltas não justificadas) nas aulas do módulo.",
            icon_name="calendar-medal",
            xp_reward=100,
            competency_id=None,
            is_active=True,
        )
        enrollment_a = Enrollment(
            student_id=student_a.id,
            class_id=class_a.id,
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("92.00"),
        )
        enrollment_b = Enrollment(
            student_id=student_b.id,
            class_id=class_a.id,
            status=EnrollmentStatus.ACTIVE,
            attendance_rate=Decimal("80.00"),
        )
        session.add_all([b_met, b_paq, b_tor, b_assid, enrollment_a, enrollment_b])
        session.flush()

        # Aluno A desbloqueou 2 badges (150 + 120 = 270 XP -> Nível 2 Praticante)
        session.add_all(
            [
                StudentAchievement(
                    student_id=student_a.id,
                    enrollment_id=enrollment_a.id,
                    badge_id=b_met.id,
                    unlocked_at=datetime(2026, 3, 10, 14, 0, tzinfo=timezone.utc),
                    origin_reference="Módulo 01: Metrologia com Micrômetro (Nível 4.90)",
                ),
                StudentAchievement(
                    student_id=student_a.id,
                    enrollment_id=enrollment_a.id,
                    badge_id=b_paq.id,
                    unlocked_at=datetime(2026, 3, 5, 17, 30, tzinfo=timezone.utc),
                    origin_reference="Tarefa: Inspeção Dimensional de Pino Guia (Nota 9.60)",
                ),
            ]
        )
        session.commit()
        comp_met_id = comp_met.id

    # 1. Sem token -> 401 Unauthorized
    assert (
        await client.get("/api/v1/gamification/badges")
    ).status_code == status.HTTP_401_UNAUTHORIZED

    stu_a_headers = {"Authorization": f"Bearer {student_a_token}"}
    stu_b_headers = {"Authorization": f"Bearer {student_b_token}"}

    # 2. Consulta do Aluno A (270 XP -> Nível 2 — Praticante, faltam 30 XP para Nível 3 — Proficiente)
    res_a = await client.get("/api/v1/gamification/badges", headers=stu_a_headers)
    assert res_a.status_code == status.HTTP_200_OK
    body_a = res_a.json()

    assert body_a["student_id"] == str(student_a.id)
    assert body_a["total_xp"] == 270
    assert body_a["current_level_number"] == 2
    assert body_a["current_level"] == "PRACTITIONER"
    assert body_a["current_level_title"] == "Nível 2 — Praticante"
    assert body_a["next_level"] == "PROFICIENT"
    assert body_a["next_level_title"] == "Nível 3 — Proficiente"
    assert body_a["next_level_xp_threshold"] == 300
    assert body_a["xp_to_next_level"] == 30
    assert Decimal(str(body_a["level_progress_percentage"])) == Decimal("80.00")
    assert body_a["unlocked_count"] == 2
    assert body_a["locked_count"] == 2
    assert body_a["total_badges"] == 4
    assert Decimal(str(body_a["completion_percentage"])) == Decimal("50.00")
    assert len(body_a["level_tiers"]) == 4

    # Critério 2: Exibe criteria_explanation de todas as badges
    assert len(body_a["badges"]) == 4
    for badge_item in body_a["badges"]:
        assert isinstance(badge_item["criteria_explanation"], str)
        assert len(badge_item["criteria_explanation"]) >= 15

    # Verifica insígnias desbloqueadas vs próximas conquistas
    assert {b["code"] for b in body_a["unlocked_badges"]} == {
        "BADGE-METROLOGIA-100",
        "BADGE-PAQUIMETRO-PRO",
    }
    assert all(
        b["unlocked"] is True
        and b["is_unlocked"] is True
        and Decimal(str(b["progress_percentage"])) == Decimal("100.00")
        and b["unlocked_at"] is not None
        and b["origin_reference"] is not None
        for b in body_a["unlocked_badges"]
    )

    assert {b["code"] for b in body_a["upcoming_badges"]} == {
        "BADGE-ASSIDUIDADE-100",
        "BADGE-TORNEARIA-EXACT",
    }
    # A próxima conquista de assiduidade reflete a presença atual de 92.00% do Aluno A
    assid_upcoming = next(
        b
        for b in body_a["upcoming_badges"]
        if b["code"] == "BADGE-ASSIDUIDADE-100"
    )
    assert assid_upcoming["is_unlocked"] is False
    assert Decimal(str(assid_upcoming["progress_percentage"])) == Decimal("92.00")

    # Critério 3: Não expõe ranking vexatório nem dados de outros estudantes
    assert "ranking" not in body_a
    assert "leaderboard" not in body_a
    assert str(student_b.id) not in str(body_a)
    assert "Aluno Iniciante B" not in str(body_a)
    assert "ranking" in body_a["ethical_privacy_note"].lower()

    # 3. Filtros opcionais: unlocked_only=true e competency_id
    unlocked_only_res = await client.get(
        "/api/v1/gamification/badges?unlocked_only=true",
        headers=stu_a_headers,
    )
    assert unlocked_only_res.status_code == status.HTTP_200_OK
    assert len(unlocked_only_res.json()["badges"]) == 2

    comp_filter_res = await client.get(
        f"/api/v1/gamification/badges?competency_id={comp_met_id}",
        headers=stu_a_headers,
    )
    assert comp_filter_res.status_code == status.HTTP_200_OK
    assert {b["code"] for b in comp_filter_res.json()["badges"]} == {
        "BADGE-METROLOGIA-100",
        "BADGE-PAQUIMETRO-PRO",
    }

    # 4. Consulta do Aluno B (0 XP -> Nível 1 — Iniciante, 0 desbloqueadas, sem ver conquistas do Aluno A)
    res_b = await client.get("/api/v1/gamification/badges", headers=stu_b_headers)
    assert res_b.status_code == status.HTTP_200_OK
    body_b = res_b.json()
    assert body_b["student_id"] == str(student_b.id)
    assert body_b["total_xp"] == 0
    assert body_b["current_level"] == "BEGINNER"
    assert body_b["unlocked_count"] == 0
    assert body_b["locked_count"] == 4
    assert body_b["unlocked_badges"] == []
    assert str(student_a.id) not in str(body_b)
