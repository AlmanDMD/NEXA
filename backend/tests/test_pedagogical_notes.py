"""Testes unitários e de integração para Observações Pedagógicas com Acesso Restrito, Criptografia e Auditoria (BE-045)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
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
from app.core.encryption import (
    ENCRYPTION_ENVELOPE_PREFIX,
    PedagogicalNoteCipher,
)
from app.main import create_app
from app.models import (
    AuditLog,
    Base,
    Enrollment,
    PedagogicalNote,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import (
    ClassStatus,
    EnrollmentStatus,
    NoteCategory,
    NoteVisibilityScope,
    Shift,
    UserRole,
)
from app.schemas.pedagogical_note import (
    PedagogicalNoteCreateSchema,
    PedagogicalNoteListQueryParams,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.pedagogical_note_service import (
    PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE,
    PEDAGOGICAL_NOTE_ENROLLMENT_STUDENT_MISMATCH_MESSAGE,
    PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE,
    PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE,
    PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE,
    PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE,
    PEDAGOGICAL_NOTE_TEACHER_COORD_SCOPE_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "pedagogical_notes_test.db"
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
def pedagogical_notes_app(
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
async def client(pedagogical_notes_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=pedagogical_notes_app)
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


class TestPedagogicalNoteUnitValidations:
    """Testes unitários de criptografia Fernet/AES-256, schemas Pydantic v2 e modelo ORM (BE-045)."""

    def test_cipher_encrypt_decrypt_roundtrip_and_tamper_detection(self) -> None:
        cipher = PedagogicalNoteCipher(
            secret_key="chave-secreta-pedagogica-senai-2026-aes256"
        )
        plaintext = "Acompanhamento individual de adaptação em bancada de Tornearia CNC (NR-12)."
        encrypted = cipher.encrypt(plaintext)

        assert encrypted != plaintext
        assert encrypted.startswith(ENCRYPTION_ENVELOPE_PREFIX)
        assert plaintext not in encrypted
        assert cipher.is_encrypted(encrypted) is True
        assert cipher.decrypt(encrypted) == plaintext

        # Idempotente quando já cifrado
        assert cipher.encrypt(encrypted) == encrypted

        # Chave diferente falha na descriptografia autenticada
        other_cipher = PedagogicalNoteCipher(
            secret_key="outra-chave-diferente-invalida-2026-aes256"
        )
        with pytest.raises(ValueError, match="Falha ao descriptografar"):
            other_cipher.decrypt(encrypted)

        with pytest.raises(ValueError, match="pelo menos 16 caracteres"):
            PedagogicalNoteCipher(secret_key="curta")

    def test_create_and_list_schemas_validation(self) -> None:
        student_id = uuid4()
        # Quando followup_date é enviado sem requires_followup explícito, promove requires_followup=True
        auto_followup = PedagogicalNoteCreateSchema(
            student_id=student_id,
            visibility_scope="teachers_and_coord",  # type: ignore[arg-type]
            category="mentoring",  # type: ignore[arg-type]
            note_content="  Anotação pedagógica de mentoria prática em metrologia.  ",
            followup_date="2026-07-20",  # type: ignore[arg-type]
        )
        assert auto_followup.visibility_scope == NoteVisibilityScope.TEACHERS_AND_COORD
        assert auto_followup.category == NoteCategory.MENTORING
        assert auto_followup.requires_followup is True
        assert auto_followup.followup_date == date(2026, 7, 20)

        # Quando requires_followup=False explicitamente mas followup_date é enviada -> erro Pydantic
        with pytest.raises(ValidationError):
            PedagogicalNoteCreateSchema(
                student_id=student_id,
                category=NoteCategory.INTERVENTION,
                note_content="Conteúdo válido de observação.",
                requires_followup=False,
                followup_date=date(2026, 7, 20),
            )

        with pytest.raises(ValidationError):
            PedagogicalNoteCreateSchema(
                student_id=student_id,
                category=NoteCategory.INTERVENTION,
                note_content="oi",
            )

        params = PedagogicalNoteListQueryParams(
            page=1,
            limit=30,
            visibility_scope="coordination_only",  # type: ignore[arg-type]
            category="behavioral",  # type: ignore[arg-type]
            requires_followup=True,
        )
        assert params.visibility_scope == NoteVisibilityScope.COORDINATION_ONLY
        assert params.category == NoteCategory.BEHAVIORAL
        assert params.requires_followup is True

    def test_orm_model_validations(self) -> None:
        note = PedagogicalNote(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            author_id=uuid4(),
            visibility_scope=NoteVisibilityScope.PRIVATE_AUTHOR,
            category=NoteCategory.ACCOMMODATION,
            note_content="  Adaptação ergonômica na bancada 01.  ",
            requires_followup=True,
            followup_date=date(2026, 8, 10),
        )
        assert note.note_content == "Adaptação ergonômica na bancada 01."

        with pytest.raises(ValueError, match="pelo menos 5 caracteres"):
            PedagogicalNote(
                student_id=uuid4(),
                enrollment_id=uuid4(),
                author_id=uuid4(),
                category=NoteCategory.INTERVENTION,
                note_content="1234",
            )


@pytest.mark.asyncio
async def test_student_access_is_strictly_blocked_403_and_generates_security_alert_in_audit_logs(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 1 de BE-045: Qualquer tentativa de acesso por perfil STUDENT retorna HTTP 403 Forbidden e gera alerta em audit_logs."""
    student, student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.invasor045@senai.br",
        role=UserRole.STUDENT,
        full_name="Estudante Bloqueado 045",
        registration_number="ALU-045-BLK",
    )
    stu_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Estudante tentando criar observação pedagógica -> HTTP 403 + audit_logs
    post_res = await client.post(
        "/api/v1/pedagogical-notes",
        headers=stu_headers,
        json={
            "student_id": str(student.id),
            "category": "INTERVENTION",
            "note_content": "Tentativa de estudante criar observação restrita.",
        },
    )
    assert post_res.status_code == status.HTTP_403_FORBIDDEN
    assert post_res.json()["message"] == PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE

    # 2. Estudante tentando consultar observações pedagógicas -> HTTP 403 + audit_logs
    get_res = await client.get(
        f"/api/v1/students/{student.id}/pedagogical-notes",
        headers=stu_headers,
    )
    assert get_res.status_code == status.HTTP_403_FORBIDDEN
    assert get_res.json()["message"] == PEDAGOGICAL_NOTE_STUDENT_FORBIDDEN_MESSAGE

    # 3. Confirma que ambos os bloqueios registraram alerta em audit_logs
    with db_session_factory() as session:
        logs = list(
            session.scalars(
                select(AuditLog)
                .where(
                    AuditLog.user_id == student.id,
                    AuditLog.action == "PEDAGOGICAL_NOTE_FORBIDDEN_STUDENT_ACCESS",
                    AuditLog.entity == "pedagogical_notes",
                )
                .order_by(AuditLog.created_at.asc())
            ).all()
        )
        assert len(logs) == 2
        assert (
            logs[0].new_values["security_alert"]
            == "UNAUTHORIZED_STUDENT_ACCESS_ATTEMPT"
        )
        assert logs[0].new_values["attempted_operation"] == "CREATE_PEDAGOGICAL_NOTE"
        assert (
            logs[1].new_values["attempted_operation"]
            == "READ_STUDENT_PEDAGOGICAL_NOTES"
        )


@pytest.mark.asyncio
async def test_pedagogical_notes_encryption_at_rest_visibility_scopes_followup_and_audit(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/pedagogical-notes e GET /api/v1/students/{id}/pedagogical-notes: criptografia em repouso, visibility_scope e followup (BE-045)."""
    teacher_a, teacher_a_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.a045@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Autor A",
        registration_number="PROF-045-A",
    )
    teacher_b, teacher_b_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.b045@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Co-Docente B (Mesma Turma)",
        registration_number="PROF-045-B",
    )
    teacher_outsider, teacher_outsider_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.out045@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Outra Turma",
        registration_number="PROF-045-OUT",
    )
    coord, coord_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord045@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coordenador Pedagógico 045",
        registration_number="COORD-045",
    )
    _admin, admin_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="admin045@senai.br",
        role=UserRole.ADMIN,
        full_name="Admin 045",
        registration_number="ADM-045",
    )
    student_1, _student_1_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno1.045@senai.br",
        role=UserRole.STUDENT,
        full_name="Estudante Acompanhado 01",
        registration_number="ALU-045-01",
    )
    student_2, _student_2_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno2.045@senai.br",
        role=UserRole.STUDENT,
        full_name="Estudante Outro 02",
        registration_number="ALU-045-02",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-045",
            name="Técnico em Mecânica 045",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-045A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subj_met = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-045",
            name="Metrologia",
            workload_hours=60,
            is_active=True,
        )
        subj_tor = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-045",
            name="Tornearia",
            workload_hours=80,
            is_active=True,
        )
        enrollment_1 = Enrollment(
            student_id=student_1.id,
            class_id=class_a.id,
            status=EnrollmentStatus.ACTIVE,
        )
        enrollment_2 = Enrollment(
            student_id=student_2.id,
            class_id=class_a.id,
            status=EnrollmentStatus.ACTIVE,
        )
        session.add_all(
            [
                enrollment_1,
                enrollment_2,
                TeacherAssignment(
                    teacher_id=teacher_a.id,
                    class_id=class_a.id,
                    subject_id=subj_met.id,
                    is_main_teacher=True,
                ),
                TeacherAssignment(
                    teacher_id=teacher_b.id,
                    class_id=class_a.id,
                    subject_id=subj_tor.id,
                    is_main_teacher=True,
                ),
            ]
        )
        session.commit()
        enrollment_1_id = enrollment_1.id
        enrollment_2_id = enrollment_2.id

    ta_headers = {"Authorization": f"Bearer {teacher_a_token}"}
    tb_headers = {"Authorization": f"Bearer {teacher_b_token}"}
    out_headers = {"Authorization": f"Bearer {teacher_outsider_token}"}
    coord_headers = {"Authorization": f"Bearer {coord_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Validações de erro e autorização contextual:
    # - Professor de outra turma não pode criar ou listar observações do aluno -> 403
    out_post = await client.post(
        "/api/v1/pedagogical-notes",
        headers=out_headers,
        json={
            "student_id": str(student_1.id),
            "category": "INTERVENTION",
            "note_content": "Professor externo não pode registrar nota.",
        },
    )
    assert out_post.status_code == status.HTTP_403_FORBIDDEN
    assert out_post.json()["message"] == PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE

    out_get = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes",
        headers=out_headers,
    )
    assert out_get.status_code == status.HTTP_403_FORBIDDEN
    assert out_get.json()["message"] == PEDAGOGICAL_NOTE_TEACHER_CLASS_FORBIDDEN_MESSAGE

    # - Professor não pode criar nota com escopo COORDINATION_ONLY -> 403
    teacher_coord_scope = await client.post(
        "/api/v1/pedagogical-notes",
        headers=ta_headers,
        json={
            "student_id": str(student_1.id),
            "visibility_scope": "COORDINATION_ONLY",
            "category": "BEHAVIORAL",
            "note_content": "Tentativa de professor usar escopo exclusivo da coordenação.",
        },
    )
    assert teacher_coord_scope.status_code == status.HTTP_403_FORBIDDEN
    assert (
        teacher_coord_scope.json()["message"]
        == PEDAGOGICAL_NOTE_TEACHER_COORD_SCOPE_FORBIDDEN_MESSAGE
    )

    # - Estudante inexistente -> 404; Usuário alvo que não é STUDENT -> 422; enrollment_id de outro aluno -> 422
    assert (
        await client.post(
            "/api/v1/pedagogical-notes",
            headers=coord_headers,
            json={
                "student_id": str(uuid4()),
                "category": "INTERVENTION",
                "note_content": "Aluno inexistente.",
            },
        )
    ).json()["message"] == PEDAGOGICAL_NOTE_STUDENT_NOT_FOUND_MESSAGE

    assert (
        await client.post(
            "/api/v1/pedagogical-notes",
            headers=coord_headers,
            json={
                "student_id": str(teacher_a.id),
                "category": "INTERVENTION",
                "note_content": "Alvo é um professor e não estudante.",
            },
        )
    ).json()["message"] == PEDAGOGICAL_NOTE_INVALID_STUDENT_ROLE_MESSAGE

    assert (
        await client.post(
            "/api/v1/pedagogical-notes",
            headers=coord_headers,
            json={
                "student_id": str(student_1.id),
                "enrollment_id": str(enrollment_2_id),
                "category": "INTERVENTION",
                "note_content": "Matrícula pertence a outro estudante.",
            },
        )
    ).json()["message"] == PEDAGOGICAL_NOTE_ENROLLMENT_STUDENT_MISMATCH_MESSAGE

    assert (
        await client.post(
            "/api/v1/pedagogical-notes",
            headers=coord_headers,
            json={
                "student_id": str(student_1.id),
                "enrollment_id": str(uuid4()),
                "category": "INTERVENTION",
                "note_content": "Matrícula inexistente.",
            },
        )
    ).json()["message"] == PEDAGOGICAL_NOTE_ENROLLMENT_NOT_FOUND_MESSAGE

    # 2. Criação de 3 observações com os 3 escopos distintos (PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY):
    # Nota 1: Prof A cria PRIVATE_AUTHOR com agendamento de acompanhamento (requires_followup + followup_date)
    secret_text_1 = "Observação privada do Prof A: estudante relatou ansiedade na medição com micrômetro."
    n1_res = await client.post(
        "/api/v1/pedagogical-notes",
        headers=ta_headers,
        json={
            "student_id": str(student_1.id),
            "enrollment_id": str(enrollment_1_id),
            "visibility_scope": "PRIVATE_AUTHOR",
            "category": "MENTORING",
            "note_content": secret_text_1,
            "requires_followup": True,
            "followup_date": "2026-06-25",
        },
    )
    assert n1_res.status_code == status.HTTP_201_CREATED
    n1_body = n1_res.json()
    n1_id = UUID(n1_body["id"])
    assert n1_body["note_content"] == secret_text_1
    assert n1_body["is_encrypted_at_rest"] is True
    assert n1_body["visibility_scope"] == "PRIVATE_AUTHOR"
    assert n1_body["category"] == "MENTORING"
    assert n1_body["requires_followup"] is True
    assert n1_body["followup_date"] == "2026-06-25"
    assert n1_body["author"]["full_name"] == "Prof. Autor A"
    assert n1_body["student"]["full_name"] == "Estudante Acompanhado 01"

    # Nota 2: Prof A cria TEACHERS_AND_COORD (resolvendo enrollment_id automaticamente)
    secret_text_2 = "Compartilhado com docentes: reforçar revisão de leitura de paquímetro na próxima aula."
    n2_res = await client.post(
        "/api/v1/pedagogical-notes",
        headers=ta_headers,
        json={
            "student_id": str(student_1.id),
            "visibility_scope": "TEACHERS_AND_COORD",
            "category": "INTERVENTION",
            "note_content": secret_text_2,
        },
    )
    assert n2_res.status_code == status.HTTP_201_CREATED
    n2_id = UUID(n2_res.json()["id"])
    assert n2_res.json()["enrollment_id"] == str(enrollment_1_id)

    # Nota 3: Coordenação cria COORDINATION_ONLY com followup
    secret_text_3 = "Exclusivo Coordenação: atendimento psicopedagógico e adaptação de cronograma."
    n3_res = await client.post(
        "/api/v1/pedagogical-notes",
        headers=coord_headers,
        json={
            "student_id": str(student_1.id),
            "visibility_scope": "COORDINATION_ONLY",
            "category": "ACCOMMODATION",
            "note_content": secret_text_3,
            "requires_followup": True,
            "followup_date": "2026-07-10",
        },
    )
    assert n3_res.status_code == status.HTTP_201_CREATED
    n3_id = UUID(n3_res.json()["id"])

    # 3. VERIFICAÇÃO DE CRIPTOGRAFIA EM REPOUSO NO BANCO DE DADOS E SEGURANÇA NOS LOGS DE AUDITORIA:
    with db_session_factory() as session:
        raw_note_1 = session.get(PedagogicalNote, n1_id)
        assert raw_note_1 is not None
        assert raw_note_1.note_content.startswith(ENCRYPTION_ENVELOPE_PREFIX)
        assert secret_text_1 not in raw_note_1.note_content

        # Garante que audit_logs registrou PEDAGOGICAL_NOTE_CREATE sem vazar o texto claro de note_content
        create_logs = list(
            session.scalars(
                select(AuditLog).where(
                    AuditLog.action == "PEDAGOGICAL_NOTE_CREATE",
                    AuditLog.entity == "pedagogical_notes",
                )
            ).all()
        )
        assert len(create_logs) == 3
        for log_entry in create_logs:
            serialized_new = str(log_entry.new_values)
            assert secret_text_1 not in serialized_new
            assert secret_text_2 not in serialized_new
            assert secret_text_3 not in serialized_new

    # 4. VERIFICAÇÃO RIGOROSA DE visibility_scope NA CONSULTA GET /api/v1/students/{id}/pedagogical-notes:
    # - Prof A (autor de n1 e n2): vê n1 (PRIVATE_AUTHOR própria) e n2 (TEACHERS_AND_COORD); NÃO vê n3 (COORDINATION_ONLY)
    ta_list = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes",
        headers=ta_headers,
    )
    assert ta_list.status_code == status.HTTP_200_OK
    ta_ids = {UUID(item["id"]) for item in ta_list.json()["data"]}
    assert ta_ids == {n1_id, n2_id}

    # - Prof B (co-docente da mesma turma, mas NÃO é autor de n1): vê APENAS n2 (TEACHERS_AND_COORD); NÃO vê n1 nem n3!
    tb_list = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes",
        headers=tb_headers,
    )
    assert tb_list.status_code == status.HTTP_200_OK
    tb_data = tb_list.json()
    assert tb_data["total"] == 1
    assert UUID(tb_data["data"][0]["id"]) == n2_id
    assert tb_data["data"][0]["note_content"] == secret_text_2

    # - Coordenação: vê n2 (TEACHERS_AND_COORD) e n3 (COORDINATION_ONLY); NÃO vê n1 (PRIVATE_AUTHOR de Prof A)!
    coord_list = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes",
        headers=coord_headers,
    )
    assert coord_list.status_code == status.HTTP_200_OK
    coord_ids = {UUID(item["id"]) for item in coord_list.json()["data"]}
    assert coord_ids == {n2_id, n3_id}

    # - Admin: possui visão de auditoria completa (n1, n2, n3) e pode filtrar por requires_followup=true
    admin_list = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes",
        headers=admin_headers,
    )
    assert admin_list.status_code == status.HTTP_200_OK
    assert {UUID(item["id"]) for item in admin_list.json()["data"]} == {
        n1_id,
        n2_id,
        n3_id,
    }

    followup_filter = await client.get(
        f"/api/v1/students/{student_1.id}/pedagogical-notes?requires_followup=true",
        headers=admin_headers,
    )
    assert followup_filter.status_code == status.HTTP_200_OK
    assert {UUID(item["id"]) for item in followup_filter.json()["data"]} == {
        n1_id,
        n3_id,
    }

    # 5. Confirma que as leituras geraram rastro PEDAGOGICAL_NOTE_READ em audit_logs
    with db_session_factory() as session:
        read_logs = list(
            session.scalars(
                select(AuditLog).where(
                    AuditLog.action == "PEDAGOGICAL_NOTE_READ",
                    AuditLog.entity == "pedagogical_notes",
                )
            ).all()
        )
        assert len(read_logs) == 5
