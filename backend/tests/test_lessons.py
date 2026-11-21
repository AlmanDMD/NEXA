"""Testes unitários e de integração para Registro e Consulta de Aulas Ministradas (BE-021)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime
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
from app.schemas.enums import AttendanceStatus, ClassStatus, EnrollmentStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.class_lesson_service import (
    LESSON_CLASS_NOT_FOUND_MESSAGE,
    LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE,
    LESSON_INACTIVE_CLASS_MESSAGE,
    LESSON_MODULE_NOT_FOUND_MESSAGE,
    LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE,
    LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE,
    LESSON_SUBJECT_NOT_FOUND_MESSAGE,
    LESSON_TEACHER_FORBIDDEN_MESSAGE,
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
