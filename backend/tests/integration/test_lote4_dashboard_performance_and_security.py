"""Suíte de testes de carga, performance (<200ms), segurança (zero vazamento) e validação com seed do Lote 4 (BE-040)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import statistics
import time
from typing import Any
from uuid import UUID

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
    AcademicAssessment,
    AttendanceRecord,
    Base,
    ClassLesson,
    Enrollment,
    ExplainableDiagnostic,
    ModuleCompetency,
    PracticalTask,
    SelfAssessmentForm,
    SkillEvidence,
    StudentGrade,
    StudentMilestoneHistory,
    StudentSelfAssessment,
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
    AlertCategory,
    AlertStatus,
    AssessmentType,
    AttendanceStatus,
    ClassStatus,
    CompetencyCategory,
    DiagnosticType,
    EnrollmentStatus,
    MilestoneType,
    RiskLevel,
    Shift,
    SubmissionStatus,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.diagnostic_service import (
    DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE,
    DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE,
)
from app.services.self_assessment_service import (
    SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria engine SQLite isolada com modo WAL para simular carga concorrente do Lote 4."""
    db_file = tmp_path / "lote4_load_perf_seed.db"
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
    """Hasher rápido para criação em lote dos usuários do seed."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def lote4_app(
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
async def client(lote4_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=lote4_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as http_client:
        yield http_client


def _seed_user(
    session: Session,
    hasher: PasswordHasher,
    *,
    email: str,
    role: UserRole,
    full_name: str,
    registration_number: str,
) -> tuple[User, str]:
    user = AuthRepository(session=session).create_user(
        email=email,
        password_hash=hasher.hash_password("Senai@2026!Secret"),
        role=role,
        is_active=True,
        profile_data=UserProfileCreateSchema(
            full_name=full_name,
            registration_number=registration_number,
            phone="(11) 98888-7777",
        ),
    )
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return user, token


@pytest.fixture
def seeded_lote4_dataset(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> dict[str, Any]:
    """Popula cenário realista equivalente ao DB-030 + DB-040:

    - 2 turmas (MEC-2026-1 com 20 alunos, MEC-2026-2 com 10 alunos = 30 estudantes)
    - 3 módulos práticos (Desenho Técnico, Metrologia Dimensional, Tornearia Cilíndrica)
    - 4 competências (COMP-MET-01, COMP-USI-01, COMP-USI-02, COMP-SEG-02)
    - Aulas com distribuições de presença (100%, 80%, 76%, 68%)
    - Tarefas práticas, avaliações formativas e notas
    - 4 formulários de autoavaliação, 20 respostas, 16 skill_evidences,
      8 academic_alerts (LOW/MODERATE/HIGH/CRITICAL), 10 explainable_diagnostics
      (ALIGNED, OVERCONFIDENCE_RISK, UNDERCONFIDENCE_SUPPORT, INSUFFICIENT_EVIDENCE)
      e 8 student_milestone_history.
    """
    now = datetime.now(timezone.utc)
    with db_session_factory() as session:
        admin, admin_token = _seed_user(
            session,
            fast_hasher,
            email="admin.seed@senai.br",
            role=UserRole.ADMIN,
            full_name="Administrador Seed",
            registration_number="ADM-SEED-001",
        )
        coord, coord_token = _seed_user(
            session,
            fast_hasher,
            email="coord.seed@senai.br",
            role=UserRole.COORDINATOR,
            full_name="Coordenação Pedagógica Seed",
            registration_number="CRD-SEED-001",
        )
        teacher_1, teacher_1_token = _seed_user(
            session,
            fast_hasher,
            email="prof.metrologia.seed@senai.br",
            role=UserRole.TEACHER,
            full_name="Prof. Roberto Metrologia",
            registration_number="PRF-SEED-001",
        )
        teacher_2, teacher_2_token = _seed_user(
            session,
            fast_hasher,
            email="prof.tornearia.seed@senai.br",
            role=UserRole.TEACHER,
            full_name="Prof. Helena Tornearia",
            registration_number="PRF-SEED-002",
        )

        students_c1: list[tuple[User, str]] = []
        for idx in range(1, 21):
            students_c1.append(
                _seed_user(
                    session,
                    fast_hasher,
                    email=f"aluno.c1.{idx:02d}@senai.br",
                    role=UserRole.STUDENT,
                    full_name=f"Estudante Turma1 {idx:02d}",
                    registration_number=f"ALU-2026-1{idx:02d}",
                )
            )

        students_c2: list[tuple[User, str]] = []
        for idx in range(21, 31):
            students_c2.append(
                _seed_user(
                    session,
                    fast_hasher,
                    email=f"aluno.c2.{idx:02d}@senai.br",
                    role=UserRole.STUDENT,
                    full_name=f"Estudante Turma2 {idx:02d}",
                    registration_number=f"ALU-2026-2{idx:02d}",
                )
            )

        course = CourseRepository(session).create(
            code="TEC-MEC-SEED",
            name="Técnico em Mecânica Industrial",
            description="Curso técnico padrão SENAI para validação Lote 4",
            total_hours=1200,
            is_active=True,
        )
        class_1 = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-1",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=35,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 20),
        )
        class_2 = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-2",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=35,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 20),
        )

        subj_met = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-SEED",
            name="Metrologia e Desenho Técnico",
            workload_hours=80,
            is_active=True,
        )
        subj_tor = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-SEED",
            name="Tornearia Convencional",
            workload_hours=80,
            is_active=True,
        )

        mod_desenho = LearningModuleRepository(session).create(
            subject_id=subj_met.id,
            title="Desenho Técnico",
            order_index=1,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_metrologia = LearningModuleRepository(session).create(
            subject_id=subj_met.id,
            title="Metrologia",
            order_index=2,
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_tornearia = LearningModuleRepository(session).create(
            subject_id=subj_tor.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            practical_hours=80,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )

        comp_repo = CompetencyRepository(session)
        comp_met_01 = comp_repo.create(
            code="COMP-MET-01",
            title="Leitura de Micrômetro e Paquímetro",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_usi_01 = comp_repo.create(
            code="COMP-USI-01",
            title="Faceamento e Cilindramento Externo",
            category=CompetencyCategory.PROCEDURAL,
        )
        comp_usi_02 = comp_repo.create(
            code="COMP-USI-02",
            title="Controle de Tolerância ISO H7",
            category=CompetencyCategory.TECHNICAL,
        )
        comp_seg_02 = comp_repo.create(
            code="COMP-SEG-02",
            title="Proteção de Máquina e Segurança NR-12",
            category=CompetencyCategory.SAFETY,
        )

        session.add_all(
            [
                ModuleCompetency(module_id=mod_metrologia.id, competency_id=comp_met_01.id, weight=Decimal("1.00"), required_level=4),
                ModuleCompetency(module_id=mod_metrologia.id, competency_id=comp_usi_02.id, weight=Decimal("1.00"), required_level=4),
                ModuleCompetency(module_id=mod_tornearia.id, competency_id=comp_usi_01.id, weight=Decimal("1.00"), required_level=4),
                ModuleCompetency(module_id=mod_tornearia.id, competency_id=comp_seg_02.id, weight=Decimal("1.50"), required_level=5),
                TeacherAssignment(teacher_id=teacher_1.id, class_id=class_1.id, subject_id=subj_met.id, is_main_teacher=True),
                TeacherAssignment(teacher_id=teacher_1.id, class_id=class_1.id, subject_id=subj_tor.id, is_main_teacher=False),
                TeacherAssignment(teacher_id=teacher_2.id, class_id=class_2.id, subject_id=subj_met.id, is_main_teacher=True),
                TeacherAssignment(teacher_id=teacher_2.id, class_id=class_2.id, subject_id=subj_tor.id, is_main_teacher=True),
            ]
        )

        enr_c1: list[Enrollment] = []
        for stu, _ in students_c1:
            enr = Enrollment(
                student_id=stu.id,
                class_id=class_1.id,
                enrollment_date=date(2026, 2, 1),
                status=EnrollmentStatus.ACTIVE,
            )
            session.add(enr)
            enr_c1.append(enr)

        enr_c2: list[Enrollment] = []
        for stu, _ in students_c2:
            enr = Enrollment(
                student_id=stu.id,
                class_id=class_2.id,
                enrollment_date=date(2026, 2, 1),
                status=EnrollmentStatus.ACTIVE,
            )
            session.add(enr)
            enr_c2.append(enr)
        session.flush()

        # 5 aulas em class_1 para simular 100%, 80%, 60% presença e alimentar views
        for lesson_idx in range(1, 6):
            lesson = ClassLesson(
                class_id=class_1.id,
                subject_id=subj_met.id,
                module_id=mod_metrologia.id,
                teacher_id=teacher_1.id,
                lesson_date=date(2026, 3, lesson_idx),
                workload_hours=4,
                topic_summary=f"Prática Metrologia Aula {lesson_idx}",
            )
            session.add(lesson)
            session.flush()
            for stu_idx, (stu, _) in enumerate(students_c1):
                # Alunos 1..15: 100% presente; Alunos 16..18: 80%; Alunos 19..20: 60% (<75%)
                att_status = AttendanceStatus.PRESENT
                if stu_idx >= 18 and lesson_idx in (4, 5):
                    att_status = AttendanceStatus.ABSENT
                elif 15 <= stu_idx < 18 and lesson_idx == 5:
                    att_status = AttendanceStatus.ABSENT
                session.add(
                    AttendanceRecord(
                        lesson_id=lesson.id,
                        enrollment_id=enr_c1[stu_idx].id,
                        student_id=stu.id,
                        status=att_status,
                        absent_hours=4 if att_status == AttendanceStatus.ABSENT else 0,
                    )
                )

        # Avaliação teórica + notas em class_1
        assess = AcademicAssessment(
            class_id=class_1.id,
            subject_id=subj_met.id,
            module_id=mod_desenho.id,
            title="Avaliação Teórica de Metrologia",
            assessment_type=AssessmentType.EXAM,
            weight=Decimal("1.00"),
            application_date=date(2026, 3, 18),
            max_grade=Decimal("10.00"),
        )
        session.add(assess)
        session.flush()
        for stu_idx, (stu, _) in enumerate(students_c1):
            grade_val = Decimal("8.50") if stu_idx < 16 else Decimal("4.50")
            session.add(
                StudentGrade(
                    assessment_id=assess.id,
                    student_id=stu.id,
                    enrollment_id=enr_c1[stu_idx].id,
                    recorded_by=teacher_1.id,
                    grade_value=grade_val,
                )
            )

        # Tarefa prática em Metrologia + submissões + 16 skill_evidences (DB-040)
        task_met = PracticalTask(
            module_id=mod_metrologia.id,
            class_id=class_1.id,
            title="Inspeção Dimensional de Eixo H7",
            due_date=now + timedelta(days=5),
            max_score=Decimal("10.00"),
        )
        task_tor_late = PracticalTask(
            module_id=mod_tornearia.id,
            class_id=class_1.id,
            title="Torneamento de Eixo Escalonado",
            due_date=now - timedelta(days=3),
            max_score=Decimal("10.00"),
        )
        session.add_all([task_met, task_tor_late])
        session.flush()
        session.add(
            TaskCriterion(
                task_id=task_met.id,
                competency_id=comp_met_01.id,
                criterion_name="Leitura Centesimal",
                weight=Decimal("1.00"),
                min_acceptable_level=3,
            )
        )

        submissions_met: list[TaskSubmission] = []
        for stu_idx, (stu, _) in enumerate(students_c1):
            sub_m = TaskSubmission(
                task_id=task_met.id,
                student_id=stu.id,
                enrollment_id=enr_c1[stu_idx].id,
                status=SubmissionStatus.EVALUATED if stu_idx < 10 else SubmissionStatus.PENDING,
                completed_at=now if stu_idx < 10 else None,
                final_task_score=Decimal("8.50") if stu_idx < 10 else None,
            )
            sub_t = TaskSubmission(
                task_id=task_tor_late.id,
                student_id=stu.id,
                enrollment_id=enr_c1[stu_idx].id,
                status=SubmissionStatus.EVALUATED if stu_idx < 15 else SubmissionStatus.LATE,
                completed_at=now if stu_idx < 15 else None,
                final_task_score=Decimal("8.00") if stu_idx < 15 else None,
            )
            session.add_all([sub_m, sub_t])
            submissions_met.append(sub_m)
        session.flush()

        # 16 skill_evidences certificadas (DB-040)
        evidence_specs = [
            (0, comp_met_01, Decimal("4.50")),
            (0, comp_usi_02, Decimal("4.00")),
            (0, comp_usi_01, Decimal("4.50")),
            (0, comp_seg_02, Decimal("5.00")),
            (1, comp_met_01, Decimal("2.00")),
            (1, comp_usi_02, Decimal("4.50")),
            (1, comp_seg_02, Decimal("2.00")),
            (2, comp_met_01, Decimal("4.80")),
            (2, comp_usi_01, Decimal("2.00")),
            (2, comp_seg_02, Decimal("4.50")),
            (3, comp_met_01, Decimal("3.50")),
            (3, comp_usi_02, Decimal("3.80")),
            (4, comp_met_01, Decimal("4.00")),
            (4, comp_usi_01, Decimal("4.20")),
            (5, comp_met_01, Decimal("2.20")),
            (6, comp_seg_02, Decimal("1.80")),
        ]
        for s_idx, comp_obj, ver_lvl in evidence_specs:
            session.add(
                SkillEvidence(
                    student_id=students_c1[s_idx][0].id,
                    competency_id=comp_obj.id,
                    source_submission_id=submissions_met[s_idx].id,
                    verified_level=ver_lvl,
                    verified_by=teacher_1.id,
                )
            )

        # 4 self_assessment_forms (DB-040)
        form_c1_met = SelfAssessmentForm(
            module_id=mod_metrologia.id,
            class_id=class_1.id,
            title="Autoavaliação — Metrologia MEC-2026-1",
            opens_at=now - timedelta(days=2),
            closes_at=now + timedelta(days=10),
            is_active=True,
            created_by=teacher_1.id,
        )
        form_c1_tor = SelfAssessmentForm(
            module_id=mod_tornearia.id,
            class_id=class_1.id,
            title="Autoavaliação — Tornearia MEC-2026-1",
            opens_at=now - timedelta(days=2),
            closes_at=now + timedelta(days=10),
            is_active=True,
            created_by=teacher_1.id,
        )
        form_c2_met = SelfAssessmentForm(
            module_id=mod_metrologia.id,
            class_id=class_2.id,
            title="Autoavaliação — Metrologia MEC-2026-2",
            opens_at=now - timedelta(days=2),
            closes_at=now + timedelta(days=10),
            is_active=True,
            created_by=teacher_2.id,
        )
        form_c2_tor = SelfAssessmentForm(
            module_id=mod_tornearia.id,
            class_id=class_2.id,
            title="Autoavaliação — Tornearia MEC-2026-2",
            opens_at=now - timedelta(days=2),
            closes_at=now + timedelta(days=10),
            is_active=True,
            created_by=teacher_2.id,
        )
        session.add_all([form_c1_met, form_c1_tor, form_c2_met, form_c2_tor])
        session.flush()

        # 20 student_self_assessments (DB-040)
        self_eval_specs = [
            (form_c1_met, 0, comp_met_01, 4, 4, "Sem dificuldades."),
            (form_c1_met, 0, comp_usi_02, 4, 4, None),
            (form_c1_tor, 0, comp_usi_01, 5, 5, None),
            (form_c1_tor, 0, comp_seg_02, 5, 5, None),
            (form_c1_met, 1, comp_met_01, 5, 5, "Acho que domino leitura centesimal."),
            (form_c1_met, 1, comp_usi_02, 2, 2, "Insegurança na conferência H7."),
            (form_c1_tor, 1, comp_seg_02, 5, 5, None),
            (form_c1_tor, 1, comp_usi_01, 3, 3, None),
            (form_c1_met, 2, comp_met_01, 5, 5, None),
            (form_c1_met, 2, comp_usi_02, 3, 3, None),
            (form_c1_tor, 2, comp_usi_01, 5, 4, None),
            (form_c1_tor, 2, comp_seg_02, 4, 4, None),
            (form_c1_met, 3, comp_met_01, 4, 4, None),
            (form_c1_met, 3, comp_usi_02, 4, 4, None),
            (form_c1_met, 4, comp_met_01, 4, 4, None),
            (form_c1_tor, 4, comp_usi_01, 4, 4, None),
            (form_c1_met, 5, comp_met_01, 5, 5, None),
            (form_c1_tor, 6, comp_seg_02, 5, 5, None),
            (form_c1_met, 7, comp_met_01, 3, 3, None),
            (form_c1_tor, 7, comp_usi_01, 2, 2, "Preciso revisar avanço automático."),
        ]
        for f_obj, s_idx, c_obj, p_lvl, c_scr, notes in self_eval_specs:
            session.add(
                StudentSelfAssessment(
                    form_id=f_obj.id,
                    student_id=students_c1[s_idx][0].id,
                    competency_id=c_obj.id,
                    perceived_level=p_lvl,
                    confidence_score=c_scr,
                    difficulty_notes=notes,
                )
            )

        # 8 academic_alerts (LOW, MODERATE, HIGH, CRITICAL) — DB-040
        alert_specs = [
            (18, mod_metrologia.id, RiskLevel.CRITICAL, AlertCategory.ATTENDANCE, "Frequência em 60.00% (< 75%)."),
            (19, mod_metrologia.id, RiskLevel.CRITICAL, AlertCategory.ATTENDANCE, "Frequência em 60.00% (< 75%)."),
            (1, mod_tornearia.id, RiskLevel.CRITICAL, AlertCategory.SELF_EVAL_GAP, "Divergência crítica NR-12 (+3.00)."),
            (16, mod_desenho.id, RiskLevel.HIGH, AlertCategory.GRADE_DROP, "Média parcial em 4.50 (< 6.00)."),
            (17, mod_metrologia.id, RiskLevel.HIGH, AlertCategory.GRADE_DROP, "Média parcial em 4.50 (< 6.00)."),
            (15, mod_tornearia.id, RiskLevel.MODERATE, AlertCategory.PENDING_TASKS, "Atraso acumulado em oficina."),
            (5, mod_metrologia.id, RiskLevel.HIGH, AlertCategory.SELF_EVAL_GAP, "Superestimação em leitura de micrômetro."),
            (7, mod_tornearia.id, RiskLevel.LOW, AlertCategory.SELF_EVAL_GAP, "Acompanhamento preventivo leve."),
        ]
        created_alerts: list[AcademicAlert] = []
        for s_idx, mod_id, r_lvl, cat, reason in alert_specs:
            al = AcademicAlert(
                student_id=students_c1[s_idx][0].id,
                enrollment_id=enr_c1[s_idx].id,
                class_id=class_1.id,
                module_id=mod_id,
                risk_level=r_lvl,
                alert_category=cat,
                explainable_reason=reason,
                metric_snapshot={"seed": "DB-040", "risk_level": r_lvl.value},
                status=AlertStatus.ACTIVE,
            )
            session.add(al)
            created_alerts.append(al)

        # 10 explainable_diagnostics (DB-040)
        diag_specs = [
            (0, mod_metrologia.id, comp_met_01.id, Decimal("4.00"), Decimal("4.50"), Decimal("-0.50"), DiagnosticType.ALIGNED),
            (0, mod_metrologia.id, comp_usi_02.id, Decimal("4.00"), Decimal("4.00"), Decimal("0.00"), DiagnosticType.ALIGNED),
            (1, mod_metrologia.id, comp_met_01.id, Decimal("5.00"), Decimal("2.00"), Decimal("3.00"), DiagnosticType.OVERCONFIDENCE_RISK),
            (1, mod_metrologia.id, comp_usi_02.id, Decimal("2.00"), Decimal("4.50"), Decimal("-2.50"), DiagnosticType.UNDERCONFIDENCE_SUPPORT),
            (1, mod_tornearia.id, comp_seg_02.id, Decimal("5.00"), Decimal("2.00"), Decimal("3.00"), DiagnosticType.OVERCONFIDENCE_RISK),
            (2, mod_tornearia.id, comp_usi_01.id, Decimal("5.00"), Decimal("2.00"), Decimal("3.00"), DiagnosticType.OVERCONFIDENCE_RISK),
            (3, mod_metrologia.id, comp_met_01.id, Decimal("4.00"), Decimal("3.50"), Decimal("0.50"), DiagnosticType.ALIGNED),
            (5, mod_metrologia.id, comp_met_01.id, Decimal("5.00"), Decimal("2.20"), Decimal("2.80"), DiagnosticType.OVERCONFIDENCE_RISK),
            (7, mod_metrologia.id, comp_met_01.id, Decimal("3.00"), Decimal("3.00"), Decimal("0.00"), DiagnosticType.INSUFFICIENT_EVIDENCE),
            (7, mod_tornearia.id, comp_usi_01.id, Decimal("2.00"), Decimal("2.00"), Decimal("0.00"), DiagnosticType.INSUFFICIENT_EVIDENCE),
        ]
        for s_idx, m_id, c_id, s_lvl, t_lvl, gap, d_type in diag_specs:
            session.add(
                ExplainableDiagnostic(
                    student_id=students_c1[s_idx][0].id,
                    class_id=class_1.id,
                    module_id=m_id,
                    competency_id=c_id,
                    self_perceived_level=s_lvl,
                    teacher_verified_level=t_lvl,
                    discrepancy_gap=gap,
                    diagnostic_type=d_type,
                    explanation_text=f"Diagnóstico seed DB-040 ({d_type.value}) para validação analítica.",
                    limitations_note="Autoavaliação possui caráter formativo e não substitui evidências práticas.",
                    recommended_action="Acompanhar evolução prática em bancada.",
                    generated_at=now,
                )
            )

        # 8 student_milestone_history (DB-040)
        milestone_specs = [
            (0, mod_metrologia.id, MilestoneType.MODULE_COMPLETED, "Módulo Metrologia Concluído"),
            (0, mod_tornearia.id, MilestoneType.SKILL_LEVEL_UP, "Nível 5 em Segurança NR-12"),
            (0, mod_desenho.id, MilestoneType.PERFECT_ATTENDANCE, "100% de Presença em Desenho Técnico"),
            (1, mod_metrologia.id, MilestoneType.SKILL_LEVEL_UP, "Evolução em Tolerância H7"),
            (2, mod_metrologia.id, MilestoneType.PERFECT_ATTENDANCE, "Assiduidade Exemplar"),
            (3, mod_metrologia.id, MilestoneType.RECOVERY_ACHIEVED, "Recuperação Concluída com Êxito"),
            (4, mod_tornearia.id, MilestoneType.MODULE_COMPLETED, "Módulo Tornearia Concluído"),
            (5, mod_desenho.id, MilestoneType.PERFECT_ATTENDANCE, "Frequência Integral no Módulo"),
        ]
        for idx, (s_idx, m_id, m_type, title) in enumerate(milestone_specs):
            session.add(
                StudentMilestoneHistory(
                    student_id=students_c1[s_idx][0].id,
                    enrollment_id=enr_c1[s_idx].id,
                    module_id=m_id,
                    milestone_type=m_type,
                    title=title,
                    description=f"Marco acadêmico seed #{idx + 1}.",
                    milestone_metadata={"seed": "DB-040"},
                    achieved_at=now - timedelta(days=idx),
                )
            )

        session.commit()
        return {
            "admin": admin,
            "admin_token": admin_token,
            "coord": coord,
            "coord_token": coord_token,
            "teacher_1": teacher_1,
            "teacher_1_token": teacher_1_token,
            "teacher_2": teacher_2,
            "teacher_2_token": teacher_2_token,
            "class_1_id": class_1.id,
            "class_2_id": class_2.id,
            "mod_metrologia_id": mod_metrologia.id,
            "mod_tornearia_id": mod_tornearia.id,
            "comp_met_01_id": comp_met_01.id,
            "comp_seg_02_id": comp_seg_02.id,
            "form_c1_met_id": form_c1_met.id,
            "form_c2_met_id": form_c2_met.id,
            "students_c1": students_c1,
            "students_c2": students_c2,
            "alert_ids": [a.id for a in created_alerts],
        }


@pytest.mark.asyncio
async def test_lote4_risk_engine_and_alert_lifecycle_with_seed_data(
    client: AsyncClient,
    seeded_lote4_dataset: dict[str, Any],
) -> None:
    """Valida motor de risco (BE-032), listagem explicável (BE-033) e resolução com histórico (BE-039) sobre seed DB-040."""
    teacher_headers = {"Authorization": f"Bearer {seeded_lote4_dataset['teacher_1_token']}"}
    class_1_id: UUID = seeded_lote4_dataset["class_1_id"]
    alert_id: UUID = seeded_lote4_dataset["alert_ids"][0]

    # 1. Executa motor de risco na turma de 20 alunos
    eval_res = await client.post(
        f"/api/v1/dashboard/teacher/classes/{class_1_id}/evaluate-risk",
        headers=teacher_headers,
    )
    assert eval_res.status_code == status.HTTP_200_OK
    eval_body = eval_res.json()
    assert eval_body["total_students_evaluated"] == 20
    assert eval_body["critical_risk_count"] >= 2
    assert eval_body["high_risk_count"] >= 2

    # 2. Lista alunos em risco ordenados por severidade (CRITICAL antes de HIGH/MODERATE/LOW)
    at_risk_res = await client.get(
        f"/api/v1/dashboard/teacher/at-risk?class_id={class_1_id}&limit=50",
        headers=teacher_headers,
    )
    assert at_risk_res.status_code == status.HTTP_200_OK
    at_risk_body = at_risk_res.json()
    assert at_risk_body["total"] >= 8
    severity_rank = {"CRITICAL": 1, "HIGH": 2, "MODERATE": 3, "LOW": 4}
    ranks = [severity_rank[item["risk_level"]] for item in at_risk_body["data"]]
    assert ranks == sorted(ranks)

    # 3. Assume acompanhamento (ACKNOWLEDGED) e depois encerra (RESOLVED) consultando histórico
    ack_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers=teacher_headers,
        json={
            "status": "ACKNOWLEDGED",
            "resolution_notes": "Acolhimento pedagógico agendado com o estudante na oficina.",
        },
    )
    assert ack_res.status_code == status.HTTP_200_OK
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    res_res = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers=teacher_headers,
        json={
            "status": "RESOLVED",
            "resolution_notes": "Estudante regularizou frequência e atividades práticas.",
        },
    )
    assert res_res.status_code == status.HTTP_200_OK
    assert res_res.json()["status"] == "RESOLVED"
    assert len(res_res.json()["intervention_history"]) == 2

    hist_res = await client.get(
        f"/api/v1/alerts/{alert_id}/history",
        headers=teacher_headers,
    )
    assert hist_res.status_code == status.HTTP_200_OK
    assert len(hist_res.json()) == 2


@pytest.mark.asyncio
async def test_lote4_diagnostic_crossover_and_discrepancies_with_seed_data(
    client: AsyncClient,
    seeded_lote4_dataset: dict[str, Any],
) -> None:
    """Valida cruzamento diagnóstico (BE-037) e consulta de discrepâncias (BE-038) sobre os 4 cenários do seed."""
    teacher_headers = {"Authorization": f"Bearer {seeded_lote4_dataset['teacher_1_token']}"}
    class_1_id: UUID = seeded_lote4_dataset["class_1_id"]

    # Executa cruzamento completo da turma
    diag_eval = await client.post(
        f"/api/v1/classes/{class_1_id}/diagnostics/evaluate",
        headers=teacher_headers,
    )
    assert diag_eval.status_code == status.HTTP_200_OK
    diag_body = diag_eval.json()
    assert diag_body["total_diagnostics_generated"] >= 10
    assert diag_body["aligned_count"] >= 1
    assert diag_body["overconfidence_risk_count"] >= 1
    assert diag_body["underconfidence_support_count"] >= 1
    assert diag_body["insufficient_evidence_count"] >= 1
    assert diag_body["pedagogical_alerts_triggered_count"] >= 1

    # Consulta discrepâncias filtrando por OVERCONFIDENCE_RISK
    disc_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_1_id}&diagnostic_type=OVERCONFIDENCE_RISK",
        headers=teacher_headers,
    )
    assert disc_res.status_code == status.HTTP_200_OK
    disc_body = disc_res.json()
    assert disc_body["total"] >= 1
    for item in disc_body["discrepancies"]:
        assert item["diagnostic_type"] == "OVERCONFIDENCE_RISK"
        assert len(item["explanation_text"]) >= 20
        assert len(item["limitations_note"]) >= 20


@pytest.mark.asyncio
async def test_lote4_zero_data_leakage_between_students_isolation(
    client: AsyncClient,
    seeded_lote4_dataset: dict[str, Any],
) -> None:
    """Confirma zero vazamento de dados entre estudantes em /dashboard/student/me, /diagnostics/discrepancies, /self-assessments e rotas docentes."""
    stu_1, stu_1_token = seeded_lote4_dataset["students_c1"][0]
    stu_2, stu_2_token = seeded_lote4_dataset["students_c1"][1]
    stu_c2, stu_c2_token = seeded_lote4_dataset["students_c2"][0]

    class_1_id: UUID = seeded_lote4_dataset["class_1_id"]
    class_2_id: UUID = seeded_lote4_dataset["class_2_id"]
    form_c1_met_id: UUID = seeded_lote4_dataset["form_c1_met_id"]
    comp_met_01_id: UUID = seeded_lote4_dataset["comp_met_01_id"]
    alert_id: UUID = seeded_lote4_dataset["alert_ids"][0]

    stu_1_headers = {"Authorization": f"Bearer {stu_1_token}"}
    stu_2_headers = {"Authorization": f"Bearer {stu_2_token}"}

    # 1. Portal do Aluno (BE-034): Estudante 1 nunca vê dados do Estudante 2 nem do aluno da Turma 2
    me_1 = await client.get("/api/v1/dashboard/student/me", headers=stu_1_headers)
    assert me_1.status_code == status.HTTP_200_OK
    me_1_body = me_1.json()
    assert me_1_body["student_id"] == str(stu_1.id)
    me_1_text = me_1.text.lower()
    assert str(stu_2.id) not in me_1_text
    assert stu_2.email.lower() not in me_1_text
    assert "estudante turma1 02" not in me_1_text
    assert str(stu_c2.id) not in me_1_text
    assert "pedagogical_note" not in me_1_text
    assert "evolução em tolerância h7" not in me_1_text  # marco exclusivo do Estudante 2

    # Mesmo tentando enviar student_id de outro aluno na query, o schema estrito rejeita ou nunca retorna outro aluno
    me_2 = await client.get("/api/v1/dashboard/student/me", headers=stu_2_headers)
    assert me_2.status_code == status.HTTP_200_OK
    assert me_2.json()["student_id"] == str(stu_2.id)
    assert str(stu_1.id) not in me_2.text.lower()

    # Estudante 1 tentando consultar class_id da turma 2 no portal recebe 404 (sem vazar dados da turma 2)
    me_other_class = await client.get(
        f"/api/v1/dashboard/student/me?class_id={class_2_id}",
        headers=stu_1_headers,
    )
    assert me_other_class.status_code == status.HTTP_404_NOT_FOUND

    # 2. Discrepâncias (BE-038): Estudante 1 vê apenas seus próprios diagnósticos e é bloqueado ao tentar acessar outro student_id ou turma
    disc_1 = await client.get("/api/v1/diagnostics/discrepancies", headers=stu_1_headers)
    assert disc_1.status_code == status.HTTP_200_OK
    for item in disc_1.json()["discrepancies"]:
        assert item["student_id"] == str(stu_1.id)
    assert str(stu_2.id) not in disc_1.text.lower()

    disc_idor = await client.get(
        f"/api/v1/diagnostics/discrepancies?student_id={stu_2.id}",
        headers=stu_1_headers,
    )
    assert disc_idor.status_code == status.HTTP_403_FORBIDDEN
    assert disc_idor.json()["message"] == DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE

    disc_other_class = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_2_id}",
        headers=stu_1_headers,
    )
    assert disc_other_class.status_code == status.HTTP_403_FORBIDDEN
    assert disc_other_class.json()["message"] == DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE

    # 3. Submissão de autoavaliação (BE-036): impede submissão passando student_id de outro aluno
    submit_idor = await client.post(
        "/api/v1/self-assessments/submit",
        headers=stu_1_headers,
        json={
            "form_id": str(form_c1_met_id),
            "student_id": str(stu_2.id),
            "responses": [
                {
                    "competency_id": str(comp_met_01_id),
                    "perceived_level": 4,
                    "confidence_score": 4,
                }
            ],
        },
    )
    assert submit_idor.status_code == status.HTTP_403_FORBIDDEN
    assert submit_idor.json()["message"] == SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE

    # 4. Bloqueio RBAC estrito (403) para STUDENT em todas as rotas de gestão/docência do Lote 4
    forbidden_student_calls = [
        ("GET", f"/api/v1/dashboard/teacher/classes/{class_1_id}"),
        ("GET", f"/api/v1/students/{stu_2.id}/360"),
        ("GET", "/api/v1/dashboard/teacher/at-risk"),
        ("POST", f"/api/v1/dashboard/teacher/classes/{class_1_id}/evaluate-risk"),
        ("POST", f"/api/v1/classes/{class_1_id}/diagnostics/evaluate"),
        ("GET", f"/api/v1/alerts/{alert_id}/history"),
    ]
    for method, url in forbidden_student_calls:
        resp = await client.request(method, url, headers=stu_1_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN, (
            f"Estudante não foi bloqueado em {method} {url}: {resp.status_code}"
        )

    patch_resp = await client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers=stu_1_headers,
        json={
            "status": "RESOLVED",
            "resolution_notes": "Tentativa não autorizada de estudante encerrar alerta.",
        },
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN

    # Estudante da turma 2 também não acessa dados da turma 1
    resp_c2_forms = await client.get(
        f"/api/v1/classes/{class_1_id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {stu_c2_token}"},
    )
    assert resp_c2_forms.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_lote4_dashboard_and_diagnostic_routes_average_response_time_under_200ms(
    client: AsyncClient,
    seeded_lote4_dataset: dict[str, Any],
) -> None:
    """Valida que o tempo de resposta médio de todas as rotas analíticas e dashboards do Lote 4 é < 200ms com dados do seed."""
    teacher_headers = {"Authorization": f"Bearer {seeded_lote4_dataset['teacher_1_token']}"}
    stu_1, stu_1_token = seeded_lote4_dataset["students_c1"][0]
    stu_1_headers = {"Authorization": f"Bearer {stu_1_token}"}

    class_1_id: UUID = seeded_lote4_dataset["class_1_id"]
    alert_id: UUID = seeded_lote4_dataset["alert_ids"][0]

    # Aquecimento (garante criação de views analíticas e cache de metadados antes da medição de carga)
    warmup_calls = [
        ("GET", f"/api/v1/dashboard/teacher/classes/{class_1_id}", teacher_headers),
        ("GET", f"/api/v1/students/{stu_1.id}/360", teacher_headers),
        ("GET", f"/api/v1/dashboard/teacher/at-risk?class_id={class_1_id}", teacher_headers),
        ("GET", "/api/v1/dashboard/student/me", stu_1_headers),
        ("GET", f"/api/v1/diagnostics/discrepancies?class_id={class_1_id}", teacher_headers),
        ("GET", f"/api/v1/alerts/{alert_id}/history", teacher_headers),
        ("POST", f"/api/v1/dashboard/teacher/classes/{class_1_id}/evaluate-risk", teacher_headers),
        ("POST", f"/api/v1/classes/{class_1_id}/diagnostics/evaluate", teacher_headers),
    ]
    for method, url, hdrs in warmup_calls:
        w_res = await client.request(method, url, headers=hdrs)
        assert w_res.status_code == status.HTTP_200_OK

    # Bateria de medição com 5 iterações por rota (40 requisições analíticas sobre o dataset de 30 alunos)
    iterations = 5
    timings_by_route: dict[str, list[float]] = {url: [] for _, url, _ in warmup_calls}

    for _ in range(iterations):
        for method, url, hdrs in warmup_calls:
            t0 = time.perf_counter()
            resp = await client.request(method, url, headers=hdrs)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == status.HTTP_200_OK, f"Falha em {method} {url}: {resp.text}"
            timings_by_route[url].append(elapsed_ms)

    all_latencies: list[float] = []
    for url, latencies in timings_by_route.items():
        route_avg = statistics.mean(latencies)
        all_latencies.extend(latencies)
        assert route_avg < 200.0, (
            f"Rota '{url}' excedeu o limite médio de 200ms: média={route_avg:.2f}ms (amostras={latencies})"
        )

    global_avg_ms = statistics.mean(all_latencies)
    assert global_avg_ms < 200.0, (
        f"Tempo médio global das rotas de dashboard excedeu 200ms: {global_avg_ms:.2f}ms"
    )
