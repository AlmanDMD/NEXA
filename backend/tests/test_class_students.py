"""Testes de integração, segurança e prevenção de N+1 para Consulta de Alunos da Turma (BE-017)."""

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
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import AcademicClass, Base, Course, Enrollment, User
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.academic_class_service import (
    CLASS_NOT_FOUND_MESSAGE,
    CLASS_TEACHER_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "class_students_test.db"
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
def class_students_app(
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
async def class_students_client(
    class_students_app: FastAPI,
) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=class_students_app)
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
    with_profile: bool = True,
) -> tuple[User, str]:
    """Cria um usuário persistido no banco de testes e gera seu Access Token JWT."""
    profile_data: UserProfileCreateSchema | None = None
    if with_profile:
        profile_data = UserProfileCreateSchema(
            full_name=full_name or f"Usuário {role.value} {suffix}",
            registration_number=registration_number or f"SENAI-{role.value[:3]}-{suffix.upper()}",
            phone="(11) 98888-7777",
        )

    with session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=True,
            profile_data=profile_data,
        )

    token = create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role,
    )
    return user, token


def _create_course_in_db(
    session_factory: sessionmaker[Session],
    *,
    code: str = "TEC-MEC-01",
    name: str = "Técnico em Mecânica Industrial",
) -> Course:
    """Persiste um curso técnico SENAI diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description="Formação prática em tornearia CNC, ajustagem e metrologia.",
            total_hours=1200,
            is_active=True,
        )


def _create_class_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "MEC-2026-1T",
    period: str = "2026.1",
    shift: Shift = Shift.MORNING,
    max_students: int = 30,
    status_value: ClassStatus = ClassStatus.ACTIVE,
) -> AcademicClass:
    """Persiste uma turma acadêmica diretamente via repositório."""
    with session_factory() as session:
        repo = AcademicClassRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            period=period,
            shift=shift,
            max_students=max_students,
            status=status_value,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )


def _create_auxiliary_teacher_assignments_table(engine: sa.Engine) -> sa.Table:
    """Cria tabela auxiliar 'teacher_assignments' compatível com AcademicClassRepository."""
    aux_metadata = sa.MetaData()
    ta_table = sa.Table(
        "teacher_assignments",
        aux_metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("teacher_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("class_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subject_id", sa.Uuid(as_uuid=True), nullable=False),
    )
    aux_metadata.create_all(bind=engine)
    return ta_table


def _seed_enrollment(
    session_factory: sessionmaker[Session],
    *,
    student_id: UUID,
    class_id: UUID,
    enrollment_date: date = date(2026, 2, 2),
    status_value: EnrollmentStatus = EnrollmentStatus.ACTIVE,
    attendance_rate: Decimal | None = None,
    final_grade: Decimal | None = None,
) -> Enrollment:
    """Persiste diretamente um registro de matrícula com frequência e nota parcial/final."""
    with session_factory() as session:
        enrollment = Enrollment(
            student_id=student_id,
            class_id=class_id,
            enrollment_date=enrollment_date,
            status=status_value,
            attendance_rate=attendance_rate,
            final_grade=final_grade,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)
        return enrollment


async def test_list_class_students_alphabetical_order_and_metadata(
    class_students_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida retorno HTTP 200, ordenação alfabética (incluindo acentos), campos obrigatórios e metadados da turma."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        max_students=25,
    )
    other_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-2T",
        shift=Shift.AFTERNOON,
    )

    teacher_user, teacher_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="prof1",
        full_name="Prof. Roberto Metrologia",
    )
    ta_table = _create_auxiliary_teacher_assignments_table(db_engine)
    with db_engine.begin() as conn:
        conn.execute(
            ta_table.insert(),
            {
                "id": uuid4(),
                "teacher_id": teacher_user.id,
                "class_id": academic_class.id,
                "subject_id": uuid4(),
            },
        )

    # Inseridos propositalmente fora de ordem alfabética (com nomes acentuados)
    seed_students = [
        ("stu1", "Lucas Ferreira Alves", "SENAI-2026-0005", EnrollmentStatus.ACTIVE, Decimal("95.50"), Decimal("8.75")),
        ("stu2", "Érica Nogueira Lima", "SENAI-2026-0003", EnrollmentStatus.COMPLETED, Decimal("98.00"), Decimal("9.40")),
        ("stu3", "Álvaro Mendes Costa", "SENAI-2026-0001", EnrollmentStatus.ACTIVE, Decimal("88.25"), Decimal("7.80")),
        ("stu4", "Carlos Eduardo Rocha", "SENAI-2026-0002", EnrollmentStatus.DROPPED, Decimal("62.00"), Decimal("4.50")),
        ("stu5", "Ana Clara Souza", "SENAI-2026-0004", EnrollmentStatus.ACTIVE, None, None),
    ]
    seeded_ids: dict[str, tuple[UUID, UUID]] = {}
    for suffix, full_name, reg_num, enr_status, att, grade in seed_students:
        student_user, _ = _create_user_and_token(
            db_session_factory,
            fast_hasher,
            role=UserRole.STUDENT,
            suffix=suffix,
            full_name=full_name,
            registration_number=reg_num,
        )
        enr = _seed_enrollment(
            db_session_factory,
            student_id=student_user.id,
            class_id=academic_class.id,
            status_value=enr_status,
            attendance_rate=att,
            final_grade=grade,
        )
        seeded_ids[suffix] = (student_user.id, enr.id)

    # Matrícula em outra turma não deve vazar na listagem
    intruder, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="intruder",
        full_name="Zélia Outra Turma",
        registration_number="SENAI-2026-9999",
    )
    _seed_enrollment(db_session_factory, student_id=intruder.id, class_id=other_class.id)

    res = await class_students_client.get(
        f"/api/v1/classes/{academic_class.id}/students",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res.status_code == status.HTTP_200_OK
    body = res.json()

    # Metadados da turma: apenas 3 alunos possuem status ACTIVE (stu1, stu3, stu5)
    assert body["academic_class"]["id"] == str(academic_class.id)
    assert body["academic_class"]["code"] == "MEC-2026-1T"
    assert body["academic_class"]["period"] == "2026.1"
    assert body["academic_class"]["shift"] == "MORNING"
    assert body["academic_class"]["max_students"] == 25
    assert body["academic_class"]["enrolled_students_count"] == 3
    assert body["academic_class"]["available_slots"] == 22
    assert body["academic_class"]["course"]["code"] == "TEC-MEC-01"
    assert body["total"] == 5

    # Ordenação alfabética estrita (Álvaro -> Ana -> Carlos -> Érica -> Lucas)
    returned_names = [item["full_name"] for item in body["data"]]
    assert returned_names == [
        "Álvaro Mendes Costa",
        "Ana Clara Souza",
        "Carlos Eduardo Rocha",
        "Érica Nogueira Lima",
        "Lucas Ferreira Alves",
    ]

    alvaro = body["data"][0]
    assert alvaro["id"] == str(seeded_ids["stu3"][0])
    assert alvaro["student_id"] == str(seeded_ids["stu3"][0])
    assert alvaro["enrollment_id"] == str(seeded_ids["stu3"][1])
    assert alvaro["registration_number"] == "SENAI-2026-0001"
    assert alvaro["status"] == "ACTIVE"
    assert alvaro["attendance_rate"] == "88.25"
    assert alvaro["final_grade"] == "7.80"

    ana = body["data"][1]
    assert ana["attendance_rate"] is None
    assert ana["final_grade"] is None


async def test_list_class_students_rbac_and_teacher_allocation(
    class_students_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Apenas docentes alocados à turma, coordenadores e admins podem visualizar (401/403 para demais)."""
    course = _create_course_in_db(db_session_factory)
    class_a = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-A")
    class_b = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-B")

    allocated_teacher, allocated_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="alloc"
    )
    unallocated_teacher, unallocated_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="unalloc"
    )
    _, coordinator_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="coord"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="admin"
    )
    student_user, student_token = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="rbac_stu",
        full_name="Bruno Pereira",
        registration_number="SENAI-2026-RBAC",
    )
    _seed_enrollment(db_session_factory, student_id=student_user.id, class_id=class_a.id)

    # Sem tabela teacher_assignments ainda -> docente recebe 403
    res_no_table = await class_students_client.get(
        f"/api/v1/classes/{class_a.id}/students",
        headers={"Authorization": f"Bearer {allocated_token}"},
    )
    assert res_no_table.status_code == status.HTTP_403_FORBIDDEN
    assert res_no_table.json()["message"] == CLASS_TEACHER_FORBIDDEN_MESSAGE

    ta_table = _create_auxiliary_teacher_assignments_table(db_engine)
    with db_engine.begin() as conn:
        conn.execute(
            ta_table.insert(),
            [
                {
                    "id": uuid4(),
                    "teacher_id": allocated_teacher.id,
                    "class_id": class_a.id,
                    "subject_id": uuid4(),
                },
                {
                    "id": uuid4(),
                    "teacher_id": unallocated_teacher.id,
                    "class_id": class_b.id,
                    "subject_id": uuid4(),
                },
            ],
        )

    # Não autenticado -> 401
    res_unauth = await class_students_client.get(f"/api/v1/classes/{class_a.id}/students")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # STUDENT -> 403
    res_student = await class_students_client.get(
        f"/api/v1/classes/{class_a.id}/students",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == status.HTTP_403_FORBIDDEN

    # Docente alocado em outra turma -> 403
    res_unallocated = await class_students_client.get(
        f"/api/v1/classes/{class_a.id}/students",
        headers={"Authorization": f"Bearer {unallocated_token}"},
    )
    assert res_unallocated.status_code == status.HTTP_403_FORBIDDEN
    assert res_unallocated.json()["message"] == CLASS_TEACHER_FORBIDDEN_MESSAGE

    # Docente alocado nesta turma -> 200
    res_allocated = await class_students_client.get(
        f"/api/v1/classes/{class_a.id}/students",
        headers={"Authorization": f"Bearer {allocated_token}"},
    )
    assert res_allocated.status_code == status.HTTP_200_OK
    assert res_allocated.json()["total"] == 1

    # COORDINATOR e ADMIN -> 200 em qualquer turma
    for privileged_token in (coordinator_token, admin_token):
        res_priv = await class_students_client.get(
            f"/api/v1/classes/{class_a.id}/students",
            headers={"Authorization": f"Bearer {privileged_token}"},
        )
        assert res_priv.status_code == status.HTTP_200_OK
        assert res_priv.json()["total"] == 1


async def test_list_class_students_filters_empty_and_errors(
    class_students_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida filtros opcionais (status, search), turma vazia, 404 inexistente e 400 UUID inválido."""
    course = _create_course_in_db(db_session_factory)
    populated_class = _create_class_in_db(
        db_session_factory, course_id=course.id, code="MEC-POP-01"
    )
    empty_class = _create_class_in_db(
        db_session_factory, course_id=course.id, code="MEC-EMP-02"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="filt"
    )

    stu_active, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="flt1",
        full_name="Beatriz Helena Costa",
        registration_number="SENAI-MEC-1001",
    )
    stu_dropped, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="flt2",
        full_name="Marcos Vinícius Dias",
        registration_number="SENAI-MEC-1002",
    )
    stu_no_profile, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="noprof",
        with_profile=False,
    )
    _seed_enrollment(
        db_session_factory,
        student_id=stu_active.id,
        class_id=populated_class.id,
        status_value=EnrollmentStatus.ACTIVE,
        attendance_rate=Decimal("92.00"),
        final_grade=Decimal("8.50"),
    )
    _seed_enrollment(
        db_session_factory,
        student_id=stu_dropped.id,
        class_id=populated_class.id,
        status_value=EnrollmentStatus.DROPPED,
        attendance_rate=Decimal("40.00"),
        final_grade=Decimal("3.00"),
    )
    _seed_enrollment(
        db_session_factory,
        student_id=stu_no_profile.id,
        class_id=populated_class.id,
        status_value=EnrollmentStatus.ACTIVE,
    )

    # Filtro por status=DROPPED
    res_dropped = await class_students_client.get(
        f"/api/v1/classes/{populated_class.id}/students?status=DROPPED",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_dropped.status_code == status.HTTP_200_OK
    assert res_dropped.json()["total"] == 1
    assert res_dropped.json()["data"][0]["full_name"] == "Marcos Vinícius Dias"
    # Metadado da turma preserva contagem total de matrículas ACTIVE (2: Beatriz + sem perfil)
    assert res_dropped.json()["academic_class"]["enrolled_students_count"] == 2

    # Filtro por search (matrícula SENAI)
    res_search_reg = await class_students_client.get(
        f"/api/v1/classes/{populated_class.id}/students?search=1001",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_search_reg.status_code == status.HTTP_200_OK
    assert res_search_reg.json()["total"] == 1
    assert res_search_reg.json()["data"][0]["full_name"] == "Beatriz Helena Costa"

    # Fallback para email quando estudante não possui UserProfile cadastrado
    res_no_profile = await class_students_client.get(
        f"/api/v1/classes/{populated_class.id}/students?search=noprof",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_no_profile.status_code == status.HTTP_200_OK
    assert res_no_profile.json()["total"] == 1
    assert res_no_profile.json()["data"][0]["full_name"] == stu_no_profile.email
    assert res_no_profile.json()["data"][0]["registration_number"] is None

    # Turma sem matrículas retorna array vazio e total=0
    res_empty = await class_students_client.get(
        f"/api/v1/classes/{empty_class.id}/students",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_empty.status_code == status.HTTP_200_OK
    assert res_empty.json()["total"] == 0
    assert res_empty.json()["data"] == []

    # Turma inexistente -> HTTP 404
    res_404 = await class_students_client.get(
        f"/api/v1/classes/{uuid4()}/students",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == CLASS_NOT_FOUND_MESSAGE

    # UUID inválido -> HTTP 400
    res_400 = await class_students_client.get(
        "/api/v1/classes/id-invalido/students",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_400.status_code == status.HTTP_400_BAD_REQUEST


async def test_list_class_students_avoids_n_plus_one_queries(
    class_students_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante ausência de queries N+1 via joinedload/JOIN único independente do número de alunos."""
    course = _create_course_in_db(db_session_factory)
    class_small = _create_class_in_db(
        db_session_factory, course_id=course.id, code="MEC-N1-02"
    )
    class_large = _create_class_in_db(
        db_session_factory, course_id=course.id, code="MEC-N1-10"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="nplus1"
    )

    for idx in range(2):
        stu, _ = _create_user_and_token(
            db_session_factory,
            fast_hasher,
            role=UserRole.STUDENT,
            suffix=f"s{idx}",
            full_name=f"Aluno Pequeno {idx:02d}",
            registration_number=f"SENAI-S-{idx:03d}",
        )
        _seed_enrollment(db_session_factory, student_id=stu.id, class_id=class_small.id)

    for idx in range(10):
        stu, _ = _create_user_and_token(
            db_session_factory,
            fast_hasher,
            role=UserRole.STUDENT,
            suffix=f"l{idx}",
            full_name=f"Aluno Grande {idx:02d}",
            registration_number=f"SENAI-L-{idx:03d}",
        )
        _seed_enrollment(db_session_factory, student_id=stu.id, class_id=class_large.id)

    select_queries: list[str] = []

    def _capture_select(
        _conn: Any,
        _cursor: Any,
        statement: str,
        _parameters: Any,
        _context: Any,
        _executemany: Any,
    ) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            select_queries.append(statement)

    event.listen(db_engine, "before_cursor_execute", _capture_select)
    try:
        # 1. Repositório isolado executa exatamente 1 SELECT tanto para 2 quanto para 10 alunos
        select_queries.clear()
        with db_session_factory() as session:
            repo = AcademicClassRepository(session=session)
            small_rows = repo.list_enrolled_students(class_small.id)
        assert len(small_rows) == 2
        assert len(select_queries) == 1

        select_queries.clear()
        with db_session_factory() as session:
            repo = AcademicClassRepository(session=session)
            large_rows = repo.list_enrolled_students(class_large.id)
        assert len(large_rows) == 10
        assert len(select_queries) == 1

        # 2. Fluxo HTTP completo mantém número de SELECTs constante (auth + turma + count + alunos)
        select_queries.clear()
        res_small = await class_students_client.get(
            f"/api/v1/classes/{class_small.id}/students",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res_small.status_code == status.HTTP_200_OK
        assert res_small.json()["total"] == 2
        small_http_selects = len(select_queries)

        select_queries.clear()
        res_large = await class_students_client.get(
            f"/api/v1/classes/{class_large.id}/students",
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res_large.status_code == status.HTTP_200_OK
        assert res_large.json()["total"] == 10
        large_http_selects = len(select_queries)

        assert small_http_selects == large_http_selects
        assert small_http_selects <= 5
    finally:
        event.remove(db_engine, "before_cursor_execute", _capture_select)
