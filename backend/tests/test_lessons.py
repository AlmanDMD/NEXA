"""Testes unitários e de integração para Registro e Consulta de Aulas Ministradas (BE-021)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
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
    AttendanceRecord,
    Base,
    ClassLesson,
    Course,
    Enrollment,
    LearningModule,
    Subject,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.class_lesson import (
    ClassLessonCreateSchema,
    ClassLessonListQueryParams,
    validate_lab_environment_pt,
    validate_lesson_workload_hours_pt,
    validate_topic_summary_pt,
)
from app.schemas.enums import (
    AttendanceStatus,
    ClassStatus,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.class_lesson_service import (
    ATTENDANCE_ABSENT_HOURS_EXCEED_WORKLOAD_MESSAGE,
    ATTENDANCE_INACTIVE_ENROLLMENT_MESSAGE,
    ATTENDANCE_PRESENT_WITH_ABSENT_HOURS_MESSAGE,
    ATTENDANCE_STUDENT_NOT_ENROLLED_MESSAGE,
    LESSON_CLASS_NOT_FOUND_MESSAGE,
    LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE,
    LESSON_INACTIVE_CLASS_MESSAGE,
    LESSON_MODULE_NOT_FOUND_MESSAGE,
    LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE,
    LESSON_NOT_FOUND_MESSAGE,
    LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE,
    LESSON_SUBJECT_NOT_FOUND_MESSAGE,
    LESSON_TEACHER_FORBIDDEN_MESSAGE,
    STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE,
    STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE,
    STUDENT_ENROLLMENT_NOT_FOUND_MESSAGE,
    STUDENT_NOT_FOUND_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "class_lessons_test.db"
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
def lessons_app(
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
async def lessons_client(lessons_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=lessons_app)
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
                registration_number=registration_number or f"SENAI-{role.value[:3]}-{suffix.upper()}",
                phone="(11) 98888-7777",
            ),
        )
    token = create_access_token(subject=user.id, email=user.email, role=user.role)
    return user, token


def _create_course_in_db(
    session_factory: sessionmaker[Session],
    *,
    code: str = "TEC-MEC-01",
    name: str = "Técnico em Mecânica Industrial",
) -> Course:
    with session_factory() as session:
        return CourseRepository(session=session).create(
            code=code,
            name=name,
            description="Formação em usinagem, tornearia e metrologia.",
            total_hours=1200,
            is_active=True,
        )


def _create_class_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "MEC-2026-1T",
    status_value: ClassStatus = ClassStatus.ACTIVE,
) -> AcademicClass:
    with session_factory() as session:
        return AcademicClassRepository(session=session).create(
            course_id=course_id,
            code=code,
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=status_value,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )


def _create_subject_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "USN-TOR-01",
    name: str = "Usinagem e Tornearia Mecânica",
) -> Subject:
    with session_factory() as session:
        return SubjectRepository(session=session).create(
            course_id=course_id,
            code=code,
            name=name,
            workload_hours=120,
            syllabus="Operação de torno convencional e controle dimensional.",
            is_active=True,
        )


def _create_module_in_db(
    session_factory: sessionmaker[Session],
    *,
    subject_id: UUID,
    title: str = "Torneamento Cilíndrico Externo",
    order_index: int = 1,
) -> LearningModule:
    with session_factory() as session:
        return LearningModuleRepository(session=session).create(
            subject_id=subject_id,
            title=title,
            order_index=order_index,
            practical_hours=40,
        )


def _assign_teacher(
    session_factory: sessionmaker[Session],
    *,
    teacher_id: UUID,
    class_id: UUID,
    subject_id: UUID,
) -> TeacherAssignment:
    with session_factory() as session:
        assignment = TeacherAssignment(
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            is_main_teacher=True,
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        return assignment


def _enroll_student(
    session_factory: sessionmaker[Session],
    *,
    student_id: UUID,
    class_id: UUID,
    status_value: EnrollmentStatus = EnrollmentStatus.ACTIVE,
) -> Enrollment:
    with session_factory() as session:
        enr = Enrollment(
            student_id=student_id,
            class_id=class_id,
            status=status_value,
        )
        session.add(enr)
        session.commit()
        session.refresh(enr)
        return enr


def test_class_lesson_and_attendance_orm_validations(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida restrições ORM e constraints CHECK/UNIQUE em class_lessons e attendance_records."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)
    teacher, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="orm_tch"
    )
    student, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="orm_stu"
    )
    enrollment = _enroll_student(
        db_session_factory, student_id=student.id, class_id=academic_class.id
    )

    valid_lesson = ClassLesson(
        class_id=academic_class.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        lesson_date=date(2026, 3, 10),
        workload_hours=4,
        topic_summary="  Faceamento e centragem no torno convencional  ",
        lab_environment="  Oficina de Tornearia 02  ",
    )
    assert valid_lesson.topic_summary == "Faceamento e centragem no torno convencional"
    assert valid_lesson.lab_environment == "Oficina de Tornearia 02"

    blank_lab = ClassLesson(
        class_id=academic_class.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        lesson_date=date(2026, 3, 11),
        workload_hours=2,
        topic_summary="Aula teórica de leitura de desenho",
        lab_environment="   ",
    )
    assert blank_lab.lab_environment is None

    with pytest.raises(ValueError, match="lesson_date"):
        ClassLesson(
            class_id=academic_class.id,
            subject_id=subject.id,
            teacher_id=teacher.id,
            lesson_date=datetime(2026, 3, 10, 8, 0),
            workload_hours=4,
            topic_summary="Teste",
        )

    for bad_hours in (0, 9, -2, True):
        with pytest.raises(ValueError, match="workload_hours"):
            ClassLesson(
                class_id=academic_class.id,
                subject_id=subject.id,
                teacher_id=teacher.id,
                lesson_date=date(2026, 3, 10),
                workload_hours=bad_hours,  # type: ignore[arg-type]
                topic_summary="Teste",
            )

    with pytest.raises(ValueError, match="absent_hours"):
        AttendanceRecord(
            lesson_id=uuid4(),
            enrollment_id=enrollment.id,
            student_id=student.id,
            status=AttendanceStatus.ABSENT,
            absent_hours=9,
        )

    # Persistência + UNIQUE uq_attendance_lesson_student + CHECK SQL
    with db_session_factory() as session:
        session.add(valid_lesson)
        session.commit()
        session.refresh(valid_lesson)

        rec = AttendanceRecord(
            lesson_id=valid_lesson.id,
            enrollment_id=enrollment.id,
            student_id=student.id,
            status=AttendanceStatus.PRESENT,
            absent_hours=0,
        )
        session.add(rec)
        session.commit()

    with db_session_factory() as session:
        dup_rec = AttendanceRecord(
            lesson_id=valid_lesson.id,
            enrollment_id=enrollment.id,
            student_id=student.id,
            status=AttendanceStatus.ABSENT,
            absent_hours=4,
        )
        session.add(dup_rec)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_pydantic_validators_for_class_lessons() -> None:
    """Critério de Aceitação: Validação Pydantic estrita de data (AAAA-MM-DD) e carga horária (1-8h)."""
    assert validate_lesson_workload_hours_pt(1) == 1
    assert validate_lesson_workload_hours_pt(8) == 8
    assert validate_lesson_workload_hours_pt("4") == 4
    assert validate_topic_summary_pt("  Torneamento   de   eixo H7  ") == "Torneamento de eixo H7"
    assert validate_lab_environment_pt("   ") is None
    assert validate_lab_environment_pt("  Oficina   02 ") == "Oficina 02"

    for invalid_hours in (0, -1, 9, 12, True, False, 4.5, "0", "9", "quatro"):
        with pytest.raises(Exception):
            validate_lesson_workload_hours_pt(invalid_hours)

    for bad_topic in ("ab", "<script>alert(1)</script>"):
        with pytest.raises(Exception):
            validate_topic_summary_pt(bad_topic)

    with pytest.raises(Exception):
        validate_lab_environment_pt("X" * 101)

    for bad_date in ("10/03/2026", "2026-02-30", "2026-03-10T08:00:00", 20260310, True):
        with pytest.raises(Exception):
            ClassLessonCreateSchema(
                class_id=uuid4(),
                subject_id=uuid4(),
                lesson_date=bad_date,  # type: ignore[arg-type]
                workload_hours=4,
                topic_summary="Conteúdo válido de tornearia.",
            )

    with pytest.raises(Exception):
        ClassLessonListQueryParams(
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 1),
        )


async def test_create_lesson_success_and_batch_attendance_initialization(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios BE-021: POST 201 registra aula no diário e pré-inicializa chamada apenas dos ativos."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)
    module = _create_module_in_db(db_session_factory, subject_id=subject.id)

    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tch_ok",
        full_name="Prof. Roberto Tornearia",
        registration_number="SENAI-DOC-101",
    )
    _assign_teacher(
        db_session_factory,
        teacher_id=teacher.id,
        class_id=academic_class.id,
        subject_id=subject.id,
    )

    stu_active_1, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="s1"
    )
    stu_active_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="s2"
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="s3_drop"
    )
    _enroll_student(
        db_session_factory,
        student_id=stu_active_1.id,
        class_id=academic_class.id,
        status_value=EnrollmentStatus.ACTIVE,
    )
    _enroll_student(
        db_session_factory,
        student_id=stu_active_2.id,
        class_id=academic_class.id,
        status_value=EnrollmentStatus.ACTIVE,
    )
    _enroll_student(
        db_session_factory,
        student_id=stu_dropped.id,
        class_id=academic_class.id,
        status_value=EnrollmentStatus.DROPPED,
    )

    res = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "module_id": str(module.id),
            "lesson_date": "2026-03-10",
            "workload_hours": 4,
            "topic_summary": "  Usinagem de eixo escalonado Ø25mm em torno paralelo  ",
            "lab_environment": "  Oficina de Tornearia 02  ",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    body = res.json()
    lesson_id = UUID(body["id"])
    assert body["class_id"] == str(academic_class.id)
    assert body["subject_id"] == str(subject.id)
    assert body["module_id"] == str(module.id)
    assert body["teacher_id"] == str(teacher.id)
    assert body["lesson_date"] == "2026-03-10"
    assert body["workload_hours"] == 4
    assert body["topic_summary"] == "Usinagem de eixo escalonado Ø25mm em torno paralelo"
    assert body["lab_environment"] == "Oficina de Tornearia 02"
    assert body["initialized_attendance_count"] == 2
    assert body["teacher"]["full_name"] == "Prof. Roberto Tornearia"
    assert body["subject"]["code"] == "USN-TOR-01"
    assert body["module"]["title"] == "Torneamento Cilíndrico Externo"

    # Valida pré-inicialização de attendance_records em lote apenas para alunos ACTIVE
    with db_session_factory() as session:
        records = list(
            session.scalars(
                select(AttendanceRecord).where(AttendanceRecord.lesson_id == lesson_id)
            ).all()
        )
        assert len(records) == 2
        assert {rec.student_id for rec in records} == {stu_active_1.id, stu_active_2.id}
        assert all(rec.status == AttendanceStatus.PRESENT and rec.absent_hours == 0 for rec in records)


async def test_lessons_rbac_and_contextual_teacher_authorization(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Rejeita com HTTP 403 se professor tentar criar/ver aula em turma que não leciona."""
    course = _create_course_in_db(db_session_factory)
    class_a = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-A")
    class_b = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-B")
    subject_tor = _create_subject_in_db(
        db_session_factory, course_id=course.id, code="USN-01", name="Tornearia"
    )
    subject_met = _create_subject_in_db(
        db_session_factory, course_id=course.id, code="MET-01", name="Metrologia"
    )

    teacher_a, teacher_a_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="rbac_ta"
    )
    _, unalloc_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="rbac_tb"
    )
    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="rbac_stu"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="rbac_crd"
    )

    # teacher_a leciona apenas subject_tor em class_a
    _assign_teacher(
        db_session_factory,
        teacher_id=teacher_a.id,
        class_id=class_a.id,
        subject_id=subject_tor.id,
    )

    payload_class_a_tor = {
        "class_id": str(class_a.id),
        "subject_id": str(subject_tor.id),
        "lesson_date": "2026-03-12",
        "workload_hours": 4,
        "topic_summary": "Abertura de diário de tornearia",
    }

    # Sem token -> 401
    assert (
        await lessons_client.post("/api/v1/lessons", json=payload_class_a_tor)
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await lessons_client.get(f"/api/v1/classes/{class_a.id}/lessons")
    ).status_code == status.HTTP_401_UNAUTHORIZED

    # STUDENT -> 403
    assert (
        await lessons_client.post(
            "/api/v1/lessons",
            json=payload_class_a_tor,
            headers={"Authorization": f"Bearer {student_token}"},
        )
    ).status_code == status.HTTP_403_FORBIDDEN
    assert (
        await lessons_client.get(
            f"/api/v1/classes/{class_a.id}/lessons",
            headers={"Authorization": f"Bearer {student_token}"},
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    # Professor NÃO alocado na turma -> 403 em POST e GET
    res_unalloc_post = await lessons_client.post(
        "/api/v1/lessons",
        json=payload_class_a_tor,
        headers={"Authorization": f"Bearer {unalloc_token}"},
    )
    assert res_unalloc_post.status_code == status.HTTP_403_FORBIDDEN
    assert res_unalloc_post.json()["message"] == LESSON_TEACHER_FORBIDDEN_MESSAGE

    res_unalloc_get = await lessons_client.get(
        f"/api/v1/classes/{class_a.id}/lessons",
        headers={"Authorization": f"Bearer {unalloc_token}"},
    )
    assert res_unalloc_get.status_code == status.HTTP_403_FORBIDDEN
    assert res_unalloc_get.json()["message"] == LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE

    # teacher_a tentando lançar aula para OUTRA disciplina (Metrologia) na class_a ou em class_b -> 403
    res_wrong_subject = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_a.id),
            "subject_id": str(subject_met.id),
            "lesson_date": "2026-03-12",
            "workload_hours": 4,
            "topic_summary": "Tentativa em disciplina não atribuída",
        },
        headers={"Authorization": f"Bearer {teacher_a_token}"},
    )
    assert res_wrong_subject.status_code == status.HTTP_403_FORBIDDEN
    assert res_wrong_subject.json()["message"] == LESSON_TEACHER_FORBIDDEN_MESSAGE

    res_wrong_class = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_b.id),
            "subject_id": str(subject_tor.id),
            "lesson_date": "2026-03-12",
            "workload_hours": 4,
            "topic_summary": "Tentativa em turma não atribuída",
        },
        headers={"Authorization": f"Bearer {teacher_a_token}"},
    )
    assert res_wrong_class.status_code == status.HTTP_403_FORBIDDEN

    # COORDINATOR registra aula em nome de teacher_a -> 201
    res_coord = await lessons_client.post(
        "/api/v1/lessons",
        json={**payload_class_a_tor, "teacher_id": str(teacher_a.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_coord.status_code == status.HTTP_201_CREATED
    assert res_coord.json()["teacher_id"] == str(teacher_a.id)


async def test_list_class_lessons_filters_chronological_order_and_domain_errors(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/classes/{class_id}/lessons (ordem cronológica e filtros) e erros 400/404/422."""
    course_mec = _create_course_in_db(db_session_factory, code="TEC-MEC-01", name="Mecânica")
    course_ele = _create_course_in_db(db_session_factory, code="TEC-ELE-01", name="Eletrotécnica")
    class_active = _create_class_in_db(
        db_session_factory, course_id=course_mec.id, code="MEC-AT-01", status_value=ClassStatus.ACTIVE
    )
    class_planning = _create_class_in_db(
        db_session_factory, course_id=course_mec.id, code="MEC-PL-02", status_value=ClassStatus.PLANNING
    )
    sub_tor = _create_subject_in_db(
        db_session_factory, course_id=course_mec.id, code="USN-01", name="Usinagem"
    )
    sub_met = _create_subject_in_db(
        db_session_factory, course_id=course_mec.id, code="MET-01", name="Metrologia"
    )
    sub_ele = _create_subject_in_db(
        db_session_factory, course_id=course_ele.id, code="ELE-01", name="Comandos Elétricos"
    )
    mod_tor = _create_module_in_db(
        db_session_factory, subject_id=sub_tor.id, title="Tornearia Básica"
    )
    mod_met = _create_module_in_db(
        db_session_factory, subject_id=sub_met.id, title="Paquímetro Vernier"
    )

    teacher, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="lst_t"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="lst_c"
    )
    _assign_teacher(
        db_session_factory, teacher_id=teacher.id, class_id=class_active.id, subject_id=sub_tor.id
    )
    _assign_teacher(
        db_session_factory, teacher_id=teacher.id, class_id=class_active.id, subject_id=sub_met.id
    )

    for payload in (
        {
            "class_id": str(class_active.id),
            "subject_id": str(sub_tor.id),
            "module_id": str(mod_tor.id),
            "lesson_date": "2026-03-02",
            "workload_hours": 4,
            "topic_summary": "Aula 1: Faceamento",
            "lab_environment": "Oficina 01",
        },
        {
            "class_id": str(class_active.id),
            "subject_id": str(sub_met.id),
            "module_id": str(mod_met.id),
            "lesson_date": "2026-03-15",
            "workload_hours": 2,
            "topic_summary": "Aula 3: Paquímetro",
        },
        {
            "class_id": str(class_active.id),
            "subject_id": str(sub_tor.id),
            "lesson_date": "2026-03-09",
            "workload_hours": 6,
            "topic_summary": "Aula 2: Desbaste Cilíndrico",
        },
    ):
        assert (
            await lessons_client.post(
                "/api/v1/lessons",
                json=payload,
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
        ).status_code == status.HTTP_201_CREATED

    # Listagem cronológica descendente
    res_all = await lessons_client.get(
        f"/api/v1/classes/{class_active.id}/lessons",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_all.status_code == status.HTTP_200_OK
    body_all = res_all.json()
    assert body_all["total"] == 3
    assert [item["lesson_date"] for item in body_all["data"]] == [
        "2026-03-15",
        "2026-03-09",
        "2026-03-02",
    ]

    # Filtros por disciplina, módulo e intervalo de datas
    res_filtered = await lessons_client.get(
        f"/api/v1/classes/{class_active.id}/lessons?subject_id={sub_tor.id}&start_date=2026-03-01&end_date=2026-03-10",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_filtered.status_code == status.HTTP_200_OK
    assert res_filtered.json()["total"] == 2

    res_by_module = await lessons_client.get(
        f"/api/v1/classes/{class_active.id}/lessons?module_id={mod_met.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_by_module.status_code == status.HTTP_200_OK
    assert res_by_module.json()["total"] == 1

    # Validações de erro 404/422/400
    assert (
        await lessons_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(uuid4()),
                "subject_id": str(sub_tor.id),
                "lesson_date": "2026-03-12",
                "topic_summary": "Turma inexistente",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
    ).json()["message"] == LESSON_CLASS_NOT_FOUND_MESSAGE

    assert (
        await lessons_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(class_active.id),
                "subject_id": str(uuid4()),
                "lesson_date": "2026-03-12",
                "topic_summary": "Disciplina inexistente",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
    ).json()["message"] == LESSON_SUBJECT_NOT_FOUND_MESSAGE

    res_inactive_cls = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_planning.id),
            "subject_id": str(sub_tor.id),
            "lesson_date": "2026-03-12",
            "topic_summary": "Turma ainda não ativa",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_cls.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_inactive_cls.json()["message"] == LESSON_INACTIVE_CLASS_MESSAGE

    res_sub_mismatch = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_active.id),
            "subject_id": str(sub_ele.id),
            "lesson_date": "2026-03-12",
            "topic_summary": "Disciplina de outro curso",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_sub_mismatch.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_sub_mismatch.json()["message"] == LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE

    res_mod_404 = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_active.id),
            "subject_id": str(sub_tor.id),
            "module_id": str(uuid4()),
            "lesson_date": "2026-03-12",
            "topic_summary": "Módulo inexistente",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_mod_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_mod_404.json()["message"] == LESSON_MODULE_NOT_FOUND_MESSAGE

    res_mod_mismatch = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(class_active.id),
            "subject_id": str(sub_tor.id),
            "module_id": str(mod_met.id),
            "lesson_date": "2026-03-12",
            "topic_summary": "Módulo de outra disciplina",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_mod_mismatch.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_mod_mismatch.json()["message"] == LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE

    assert (
        await lessons_client.get(
            f"/api/v1/classes/{uuid4()}/lessons",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
    ).status_code == status.HTTP_404_NOT_FOUND

    assert (
        await lessons_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(class_active.id),
                "subject_id": str(sub_tor.id),
                "lesson_date": "2026-03-12",
                "workload_hours": 9,
                "topic_summary": "Carga horária acima do limite",
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
    ).status_code == status.HTTP_400_BAD_REQUEST


async def test_batch_attendance_upsert_recalculates_attendance_rate_and_triggers_risk_evaluation(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios BE-022: Upsert transacional, recálculo server-side, JUSTIFIED e limiar de risco <78%."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)

    teacher, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="att_tch"
    )
    _assign_teacher(
        db_session_factory,
        teacher_id=teacher.id,
        class_id=academic_class.id,
        subject_id=subject.id,
    )

    stu_1, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="att_s1"
    )
    stu_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="att_s2"
    )
    stu_3, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="att_s3"
    )
    enr_1 = _enroll_student(db_session_factory, student_id=stu_1.id, class_id=academic_class.id)
    enr_2 = _enroll_student(db_session_factory, student_id=stu_2.id, class_id=academic_class.id)
    enr_3 = _enroll_student(db_session_factory, student_id=stu_3.id, class_id=academic_class.id)

    headers = {"Authorization": f"Bearer {teacher_token}"}
    res_l1 = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "lesson_date": "2026-03-10",
            "workload_hours": 4,
            "topic_summary": "Aula 1: Torneamento paralelo",
        },
        headers=headers,
    )
    res_l2 = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "lesson_date": "2026-03-12",
            "workload_hours": 4,
            "topic_summary": "Aula 2: Controle dimensional",
        },
        headers=headers,
    )
    assert res_l1.status_code == status.HTTP_201_CREATED
    assert res_l2.status_code == status.HTTP_201_CREATED
    lesson1_id = res_l1.json()["id"]
    lesson2_id = res_l2.json()["id"]

    # Aula 1: todos presentes (100.00%)
    res_call_1 = await lessons_client.post(
        f"/api/v1/lessons/{lesson1_id}/attendance",
        json={
            "records": [
                {"student_id": str(stu_1.id), "status": "PRESENT"},
                {"student_id": str(stu_2.id), "status": "PRESENT", "absent_hours": 0},
                {"student_id": str(stu_3.id), "status": "PRESENT"},
            ]
        },
        headers=headers,
    )
    assert res_call_1.status_code == status.HTTP_200_OK
    body_1 = res_call_1.json()
    assert body_1["total_processed"] == 3
    assert body_1["present_count"] == 3
    assert body_1["absent_count"] == 0
    assert body_1["at_risk_students_count"] == 0

    # Aula 2: stu_1 JUSTIFIED (100%), stu_2 LATE 2h (6/8 = 75.00% HIGH), stu_3 ABSENT 4h (4/8 = 50.00% CRITICAL)
    res_call_2 = await lessons_client.post(
        f"/api/v1/lessons/{lesson2_id}/attendance",
        json={
            "records": [
                {
                    "student_id": str(stu_1.id),
                    "status": "JUSTIFIED",
                    "absent_hours": 4,
                    "justification_note": "  Atestado   médico SENAI  ",
                },
                {
                    "student_id": str(stu_2.id),
                    "status": "LATE",
                    "absent_hours": 2,
                    "justification_note": "Chegou após intervalo",
                },
                {
                    "student_id": str(stu_3.id),
                    "status": "ABSENT",
                },
            ]
        },
        headers=headers,
    )
    assert res_call_2.status_code == status.HTTP_200_OK
    body_2 = res_call_2.json()
    assert body_2["total_processed"] == 3
    assert body_2["present_count"] == 2
    assert body_2["absent_count"] == 1
    assert body_2["at_risk_students_count"] == 2

    by_stu = {item["student_id"]: item for item in body_2["updated_enrollments"]}
    assert by_stu[str(stu_1.id)]["attendance_rate"] == "100.00"
    assert by_stu[str(stu_1.id)]["is_attendance_critical"] is False
    assert by_stu[str(stu_1.id)]["risk_level"] == RiskLevel.LOW.value

    assert by_stu[str(stu_2.id)]["attendance_rate"] == "75.00"
    assert by_stu[str(stu_2.id)]["is_attendance_critical"] is True
    assert by_stu[str(stu_2.id)]["risk_level"] == RiskLevel.HIGH.value

    assert by_stu[str(stu_3.id)]["absent_hours"] == 4
    assert by_stu[str(stu_3.id)]["attendance_rate"] == "50.00"
    assert by_stu[str(stu_3.id)]["is_attendance_critical"] is True
    assert by_stu[str(stu_3.id)]["risk_level"] == RiskLevel.CRITICAL.value

    # Confirma persistência real em enrollments e retificação idempotente via upsert
    with db_session_factory() as session:
        assert session.get(Enrollment, enr_1.id).attendance_rate == Decimal("100.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_2.id).attendance_rate == Decimal("75.00")  # type: ignore[union-attr]
        assert session.get(Enrollment, enr_3.id).attendance_rate == Decimal("50.00")  # type: ignore[union-attr]

    # Retificação de chamada: corrige stu_3 de ABSENT para PRESENT sem duplicar registros
    res_rectify = await lessons_client.post(
        f"/api/v1/lessons/{lesson2_id}/attendance",
        json={
            "records": [
                {"student_id": str(stu_3.id), "status": "PRESENT"},
            ]
        },
        headers=headers,
    )
    assert res_rectify.status_code == status.HTTP_200_OK
    assert res_rectify.json()["total_processed"] == 1
    assert res_rectify.json()["at_risk_students_count"] == 0
    assert res_rectify.json()["updated_enrollments"][0]["attendance_rate"] == "100.00"
    assert res_rectify.json()["updated_enrollments"][0]["risk_level"] == RiskLevel.LOW.value

    with db_session_factory() as session:
        rec_count = int(
            session.scalar(
                select(sa.func.count())
                .select_from(AttendanceRecord)
                .where(AttendanceRecord.lesson_id == UUID(lesson2_id))
            )
            or 0
        )
        assert rec_count == 3
        assert session.get(Enrollment, enr_3.id).attendance_rate == Decimal("100.00")  # type: ignore[union-attr]


async def test_batch_attendance_rejects_unenrolled_student_invalid_payloads_and_rbac(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios BE-022: HTTP 400 para não matriculado/extra/inválido, 401/403 RBAC e atomicidade."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)

    teacher, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="b_tch"
    )
    _, other_teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="b_otch"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="b_adm"
    )
    stu_active, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="b_s1"
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="b_s2_drp"
    )
    stu_outsider, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="b_s_out"
    )
    enr_active = _enroll_student(
        db_session_factory,
        student_id=stu_active.id,
        class_id=academic_class.id,
        status_value=EnrollmentStatus.ACTIVE,
    )
    _enroll_student(
        db_session_factory,
        student_id=stu_dropped.id,
        class_id=academic_class.id,
        status_value=EnrollmentStatus.DROPPED,
    )
    _assign_teacher(
        db_session_factory,
        teacher_id=teacher.id,
        class_id=academic_class.id,
        subject_id=subject.id,
    )

    res_lesson = await lessons_client.post(
        "/api/v1/lessons",
        json={
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "lesson_date": "2026-03-15",
            "workload_hours": 4,
            "topic_summary": "Prática de metrologia",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_lesson.status_code == status.HTTP_201_CREATED
    lesson_id = res_lesson.json()["id"]

    # 1. Estudante não matriculado misturado com aluno válido -> HTTP 400 atômico (sem persistir nada)
    res_outsider = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={
            "records": [
                {"student_id": str(stu_active.id), "status": "ABSENT"},
                {"student_id": str(stu_outsider.id), "status": "PRESENT"},
            ]
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_outsider.status_code == status.HTTP_400_BAD_REQUEST
    assert res_outsider.json()["message"] == ATTENDANCE_STUDENT_NOT_ENROLLED_MESSAGE

    with db_session_factory() as session:
        # Matrícula ativa permanece intacta (não recalculada nem marcada como falta)
        assert session.get(Enrollment, enr_active.id).attendance_rate is None  # type: ignore[union-attr]

    # 2. Matrícula DROPPED rejeitada com HTTP 400
    res_dropped = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={"records": [{"student_id": str(stu_dropped.id), "status": "PRESENT"}]},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_dropped.status_code == status.HTTP_400_BAD_REQUEST
    assert res_dropped.json()["message"] == ATTENDANCE_INACTIVE_ENROLLMENT_MESSAGE

    # 3. Payload tentando injetar attendance_rate manualmente -> HTTP 400 (extra="forbid")
    res_client_rate = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={
            "records": [{"student_id": str(stu_active.id), "status": "ABSENT"}],
            "attendance_rate": "100.00",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_client_rate.status_code == status.HTTP_400_BAD_REQUEST

    # 4. student_id duplicado no mesmo lote -> HTTP 400
    res_dup_stu = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={
            "records": [
                {"student_id": str(stu_active.id), "status": "PRESENT"},
                {"student_id": str(stu_active.id), "status": "ABSENT"},
            ]
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_dup_stu.status_code == status.HTTP_400_BAD_REQUEST

    # 5. absent_hours excedendo carga horária da aula (4h) ou PRESENT com absent_hours > 0 -> HTTP 400
    res_exceed = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={"records": [{"student_id": str(stu_active.id), "status": "ABSENT", "absent_hours": 6}]},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_exceed.status_code == status.HTTP_400_BAD_REQUEST
    assert res_exceed.json()["message"] == ATTENDANCE_ABSENT_HOURS_EXCEED_WORKLOAD_MESSAGE

    res_present_bad = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={"records": [{"student_id": str(stu_active.id), "status": "PRESENT", "absent_hours": 1}]},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_present_bad.status_code == status.HTTP_400_BAD_REQUEST
    assert res_present_bad.json()["message"] == ATTENDANCE_PRESENT_WITH_ABSENT_HOURS_MESSAGE

    # 6. RBAC e 404: 401 sem token, 403 STUDENT e docente não alocado, 404 aula inexistente, 200 ADMIN
    assert (
        await lessons_client.post(
            f"/api/v1/lessons/{lesson_id}/attendance",
            json={"records": [{"student_id": str(stu_active.id), "status": "PRESENT"}]},
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_tok in (student_token, other_teacher_token):
        assert (
            await lessons_client.post(
                f"/api/v1/lessons/{lesson_id}/attendance",
                json={"records": [{"student_id": str(stu_active.id), "status": "PRESENT"}]},
                headers={"Authorization": f"Bearer {forbidden_tok}"},
            )
        ).status_code == status.HTTP_403_FORBIDDEN

    res_404 = await lessons_client.post(
        f"/api/v1/lessons/{uuid4()}/attendance",
        json={"records": [{"student_id": str(stu_active.id), "status": "PRESENT"}]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == LESSON_NOT_FOUND_MESSAGE

    res_admin_ok = await lessons_client.post(
        f"/api/v1/lessons/{lesson_id}/attendance",
        json={"records": [{"student_id": str(stu_active.id), "status": "PRESENT"}]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_ok.status_code == status.HTTP_200_OK
    assert res_admin_ok.json()["total_processed"] == 1


@pytest.mark.asyncio
async def test_student_consolidated_attendance_via_view_margins_and_zero_division(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/students/{id}/attendance agrupado por disciplina/módulo via vw_module_attendance_risk (BE-023)."""
    teacher, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="extrato023",
        full_name="Prof. Extrato Frequência",
        registration_number="SENAI-PROF-0230",
    )
    student, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="extrato023",
        full_name="Lucas Andrade",
        registration_number="SENAI-ALU-0231",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            name="Técnico em Fabricação Mecânica",
            code="TEC-FAB-023",
            description="Curso técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session).create(
            course_id=course.id,
            code="FAB-2026-1M",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subj_usinagem = SubjectRepository(session).create(
            course_id=course.id,
            code="USI-101",
            name="Usinagem Convencional",
            workload_hours=80,
            syllabus="Tornearia e fresamento",
            is_active=True,
        )
        subj_metrologia = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-102",
            name="Metrologia Aplicada",
            workload_hours=40,
            syllabus="Instrumentos de medição",
            is_active=True,
        )
        mod_tornearia = LearningModuleRepository(session).create(
            subject_id=subj_usinagem.id,
            title="Tornearia Cilíndrica",
            order_index=1,
            description="Operação de torno mecânico",
            practical_hours=40,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_fresamento = LearningModuleRepository(session).create(
            subject_id=subj_usinagem.id,
            title="Fresamento de Engrenagens",
            order_index=2,
            description="Módulo ainda sem aulas ministradas (teste de divisão por zero)",
            practical_hours=32,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )
        mod_micrometro = LearningModuleRepository(session).create(
            subject_id=subj_metrologia.id,
            title="Medição com Micrômetro",
            order_index=1,
            description="Leitura milesimal",
            practical_hours=20,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )

        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subj_usinagem.id,
                    is_main_teacher=True,
                ),
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subj_metrologia.id,
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

    # Registra 5 aulas de 4h (20h) no módulo de Tornearia:
    # 3 PRESENT, 1 ABSENT (4h), 1 JUSTIFIED (4h -> não penaliza presença) => 16/20 = 80.00%
    tornearia_statuses = [
        ("2026-03-02", "PRESENT", 0, None),
        ("2026-03-03", "PRESENT", 0, None),
        ("2026-03-04", "ABSENT", 4, "Falta sem justificativa"),
        ("2026-03-05", "JUSTIFIED", 4, "Atestado médico odontológico"),
        ("2026-03-06", "PRESENT", 0, None),
    ]
    for lesson_date_str, rec_status, absent_h, note in tornearia_statuses:
        create_res = await lessons_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(academic_class.id),
                "subject_id": str(subj_usinagem.id),
                "module_id": str(mod_tornearia.id),
                "lesson_date": lesson_date_str,
                "workload_hours": 4,
                "topic_summary": f"Aula prática de tornearia em {lesson_date_str}.",
                "lab_environment": "Oficina de Usinagem 01",
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        lid = create_res.json()["id"]
        att_res = await lessons_client.post(
            f"/api/v1/lessons/{lid}/attendance",
            json={
                "records": [
                    {
                        "student_id": str(student.id),
                        "status": rec_status,
                        "absent_hours": absent_h,
                        "justification_note": note,
                    }
                ]
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert att_res.status_code == status.HTTP_200_OK

    # Registra 5 aulas de 4h (20h) no módulo de Micrômetro (Metrologia):
    # 3 PRESENT, 1 ABSENT (4h), 1 LATE (1h) => 15/20 = 75.00% (is_critical=True pois <78%, risk_level=HIGH)
    metrologia_statuses = [
        ("2026-03-10", "PRESENT", 0, None),
        ("2026-03-11", "ABSENT", 4, None),
        ("2026-03-12", "LATE", 1, "Atraso de 1 hora no transporte"),
        ("2026-03-13", "PRESENT", 0, None),
        ("2026-03-14", "PRESENT", 0, None),
    ]
    for lesson_date_str, rec_status, absent_h, note in metrologia_statuses:
        create_res = await lessons_client.post(
            "/api/v1/lessons",
            json={
                "class_id": str(academic_class.id),
                "subject_id": str(subj_metrologia.id),
                "module_id": str(mod_micrometro.id),
                "lesson_date": lesson_date_str,
                "workload_hours": 4,
                "topic_summary": f"Aula prática de metrologia em {lesson_date_str}.",
                "lab_environment": "Laboratório de Metrologia",
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        lid = create_res.json()["id"]
        att_res = await lessons_client.post(
            f"/api/v1/lessons/{lid}/attendance",
            json={
                "records": [
                    {
                        "student_id": str(student.id),
                        "status": rec_status,
                        "absent_hours": absent_h,
                        "justification_note": note,
                    }
                ]
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert att_res.status_code == status.HTTP_200_OK

    # Consulta consolidada pelo próprio estudante autenticado
    res = await lessons_client.get(
        f"/api/v1/students/{student.id}/attendance",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == status.HTTP_200_OK
    body = res.json()

    # Totais consolidados: 40h ministradas, 31h presença, 9h faltas não justificadas, 4h justificadas -> 77.50% (<78%)
    assert body["student_id"] == str(student.id)
    assert body["student"]["full_name"] == "Lucas Andrade"
    assert body["class_id"] == str(academic_class.id)
    assert body["total_hours"] == 40
    assert body["attended_hours"] == 31
    assert body["absent_hours"] == 9
    assert body["justified_absent_hours"] == 4
    assert body["attendance_percentage"] == "77.50"
    assert body["is_critical"] is True
    assert body["is_attendance_critical"] is True
    assert body["risk_level"] == RiskLevel.HIGH.value
    assert body["min_required_percentage"] == "75.00"
    assert body["max_allowed_absent_hours"] == "10.00"
    assert body["remaining_absent_hours_margin"] == "1.00"
    assert body["percentage_margin_to_limit"] == "2.50"
    assert body["critical_modules_count"] == 1

    # Agrupamento por disciplinas (MET-102 e USI-101 ordenadas por código)
    assert len(body["subjects"]) == 2
    subjects_by_code = {s["subject_code"]: s for s in body["subjects"]}

    met_subj = subjects_by_code["MET-102"]
    assert met_subj["total_hours"] == 20
    assert met_subj["attended_hours"] == 15
    assert met_subj["absent_hours"] == 5
    assert met_subj["attendance_percentage"] == "75.00"
    assert met_subj["is_critical"] is True
    assert met_subj["risk_level"] == RiskLevel.HIGH.value
    assert met_subj["remaining_absent_hours_margin"] == "0.00"
    assert len(met_subj["modules"]) == 1

    usi_subj = subjects_by_code["USI-101"]
    assert usi_subj["total_hours"] == 20
    assert usi_subj["attended_hours"] == 16
    assert usi_subj["absent_hours"] == 4
    assert usi_subj["justified_absent_hours"] == 4
    assert usi_subj["attendance_percentage"] == "80.00"
    assert usi_subj["is_critical"] is False
    assert usi_subj["risk_level"] == RiskLevel.LOW.value
    assert len(usi_subj["modules"]) == 2

    # Verificação por módulo (incluindo divisão por zero no módulo de Fresamento -> 100.00%)
    mod_tornearia_item = usi_subj["modules"][0]
    assert mod_tornearia_item["module_id"] == str(mod_tornearia.id)
    assert mod_tornearia_item["total_hours"] == 20
    assert mod_tornearia_item["attended_hours"] == 16
    assert mod_tornearia_item["absent_hours"] == 4
    assert mod_tornearia_item["justified_absent_hours"] == 4
    assert mod_tornearia_item["attendance_percentage"] == "80.00"
    assert mod_tornearia_item["is_critical"] is False
    assert mod_tornearia_item["max_allowed_absent_hours"] == "5.00"
    assert mod_tornearia_item["remaining_absent_hours_margin"] == "1.00"
    assert mod_tornearia_item["planned_max_allowed_absent_hours"] == "10.00"
    assert mod_tornearia_item["planned_remaining_absent_hours_margin"] == "6.00"

    mod_fresamento_item = usi_subj["modules"][1]
    assert mod_fresamento_item["module_id"] == str(mod_fresamento.id)
    assert mod_fresamento_item["total_hours"] == 0
    assert mod_fresamento_item["attended_hours"] == 0
    assert mod_fresamento_item["absent_hours"] == 0
    assert mod_fresamento_item["attendance_percentage"] == "100.00"
    assert mod_fresamento_item["is_critical"] is False
    assert mod_fresamento_item["risk_level"] == RiskLevel.LOW.value
    assert mod_fresamento_item["planned_max_allowed_absent_hours"] == "8.00"
    assert mod_fresamento_item["planned_remaining_absent_hours_margin"] == "8.00"

    # Histórico de faltas/atrasos/justificativas (4 registros não-PRESENT)
    assert len(body["absence_records"]) == 4

    # Filtro opcional por subject_id
    res_filtered = await lessons_client.get(
        f"/api/v1/students/{student.id}/attendance?subject_id={subj_usinagem.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_filtered.status_code == status.HTTP_200_OK
    filtered_body = res_filtered.json()
    assert len(filtered_body["subjects"]) == 1
    assert filtered_body["subjects"][0]["subject_id"] == str(subj_usinagem.id)
    assert filtered_body["total_hours"] == 20
    assert filtered_body["attendance_percentage"] == "80.00"
    assert filtered_body["is_critical"] is False


@pytest.mark.asyncio
async def test_student_consolidated_attendance_idor_prevention_and_contextual_rbac(
    lessons_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida prevenção IDOR (403 entre estudantes), RBAC docente por turma e erros 401/404 (BE-023)."""
    admin, admin_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="idor023",
        full_name="Admin Frequência",
        registration_number="SENAI-ADM-0232",
    )
    _coordinator, coord_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="idor023",
        full_name="Coordenador Frequência",
        registration_number="SENAI-CRD-0233",
    )
    assigned_teacher, assigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="alocado023",
        full_name="Prof. Alocado",
        registration_number="SENAI-PRF-0234",
    )
    _unassigned_teacher, unassigned_teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="externo023",
        full_name="Prof. Outra Turma",
        registration_number="SENAI-PRF-0235",
    )
    student_a, student_a_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="alunoa023",
        full_name="Aluno A",
        registration_number="SENAI-ALU-0236",
    )
    student_b, _student_b_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="alunob023",
        full_name="Aluno B",
        registration_number="SENAI-ALU-0237",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            name="Técnico em Mecatrônica",
            code="TEC-MEC-023",
            description="Curso técnico",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-1A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        class_b = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-1B",
            period="2026.1",
            shift=Shift.AFTERNOON,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
        )
        subject = SubjectRepository(session).create(
            course_id=course.id,
            code="CLP-101",
            name="Controladores Lógicos Programáveis",
            workload_hours=60,
            syllabus="Automação industrial",
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

    # 1. Sem autenticação -> HTTP 401
    res_unauth = await lessons_client.get(f"/api/v1/students/{student_a.id}/attendance")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Prevenção IDOR: Aluno A tentando consultar Aluno B ou UUID arbitrário -> HTTP 403 Forbidden
    res_idor_peer = await lessons_client.get(
        f"/api/v1/students/{student_b.id}/attendance",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_idor_peer.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_peer.json()["message"] == STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE

    res_idor_random = await lessons_client.get(
        f"/api/v1/students/{uuid4()}/attendance",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_idor_random.status_code == status.HTTP_403_FORBIDDEN
    assert res_idor_random.json()["message"] == STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE

    # 3. Aluno A consultando seus próprios dados -> HTTP 200 OK
    res_self = await lessons_client.get(
        f"/api/v1/students/{student_a.id}/attendance",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert res_self.status_code == status.HTTP_200_OK
    assert res_self.json()["student_id"] == str(student_a.id)

    # 4. Docente alocado à turma do Aluno A -> HTTP 200 OK; mas consultando Aluno B (de outra turma) -> HTTP 403
    res_teacher_ok = await lessons_client.get(
        f"/api/v1/students/{student_a.id}/attendance",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_teacher_ok.status_code == status.HTTP_200_OK

    res_teacher_other_class = await lessons_client.get(
        f"/api/v1/students/{student_b.id}/attendance",
        headers={"Authorization": f"Bearer {assigned_teacher_token}"},
    )
    assert res_teacher_other_class.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_teacher_other_class.json()["message"]
        == STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE
    )

    res_unassigned_teacher = await lessons_client.get(
        f"/api/v1/students/{student_a.id}/attendance",
        headers={"Authorization": f"Bearer {unassigned_teacher_token}"},
    )
    assert res_unassigned_teacher.status_code == status.HTTP_403_FORBIDDEN

    # 5. Coordenador e Admin podem consultar qualquer estudante -> HTTP 200 OK
    for privileged_token in (coord_token, admin_token):
        res_priv = await lessons_client.get(
            f"/api/v1/students/{student_b.id}/attendance",
            headers={"Authorization": f"Bearer {privileged_token}"},
        )
        assert res_priv.status_code == status.HTTP_200_OK

    # 6. Estudante inexistente ou ID pertencente a um docente -> HTTP 404 Not Found
    res_not_found = await lessons_client.get(
        f"/api/v1/students/{uuid4()}/attendance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_not_found.status_code == status.HTTP_404_NOT_FOUND
    assert res_not_found.json()["message"] == STUDENT_NOT_FOUND_MESSAGE

    res_non_student = await lessons_client.get(
        f"/api/v1/students/{assigned_teacher.id}/attendance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_non_student.status_code == status.HTTP_404_NOT_FOUND
    assert res_non_student.json()["message"] == STUDENT_NOT_FOUND_MESSAGE

    # 7. Filtro class_id para turma onde o estudante não está matriculado -> HTTP 404
    res_wrong_class = await lessons_client.get(
        f"/api/v1/students/{student_a.id}/attendance?class_id={class_b.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_wrong_class.status_code == status.HTTP_404_NOT_FOUND
    assert res_wrong_class.json()["message"] == STUDENT_ENROLLMENT_NOT_FOUND_MESSAGE


