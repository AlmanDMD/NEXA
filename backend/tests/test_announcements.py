"""Testes unitários e de integração para Publicação, Edição, Fixação e Exclusão de Avisos no Mural da Turma (BE-041)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
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
    ClassAnnouncement,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.class_announcement import (
    ClassAnnouncementCreateSchema,
    ClassAnnouncementUpdateSchema,
)
from app.schemas.enums import (
    AnnouncementPriority,
    ClassStatus,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.class_announcement_service import (
    ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE,
    ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE,
    ANNOUNCEMENT_NOT_FOUND_MESSAGE,
    ANNOUNCEMENT_SUBJECT_COURSE_MISMATCH_MESSAGE,
    ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE,
    ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE,
    ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE,
    ANNOUNCEMENT_TEACHER_SUBJECT_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "announcements_test.db"
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
def announcements_app(
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
async def client(announcements_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=announcements_app)
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


class TestClassAnnouncementUnitValidations:
    """Testes unitários de validação Pydantic v2 e ORM para ClassAnnouncement (BE-041)."""

    def test_create_schema_validates_title_content_priority_and_expires_at(self) -> None:
        valid = ClassAnnouncementCreateSchema(
            class_id=uuid4(),
            title="  Uso   de   EPI   no Torno  ",
            content="  Obrigatório uso de óculos de proteção e jaleco no laboratório 02.  ",
            priority="urgent",  # type: ignore[arg-type]
            is_pinned=True,
            expires_at="2030-05-10",  # type: ignore[arg-type]
        )
        assert valid.title == "Uso de EPI no Torno"
        assert (
            valid.content
            == "Obrigatório uso de óculos de proteção e jaleco no laboratório 02."
        )
        assert valid.priority == AnnouncementPriority.URGENT
        assert valid.is_pinned is True
        assert valid.expires_at == datetime(2030, 5, 10, 23, 59, 59, tzinfo=timezone.utc)

        # Rejeita título curto, conteúdo curto e prioridade inválida
        with pytest.raises(ValidationError):
            ClassAnnouncementCreateSchema(
                class_id=uuid4(),
                title="Oi",
                content="Conteúdo válido de aviso.",
            )

        with pytest.raises(ValidationError):
            ClassAnnouncementCreateSchema(
                class_id=uuid4(),
                title="Aviso válido",
                content="oi",
            )

        with pytest.raises(ValidationError):
            ClassAnnouncementCreateSchema(
                class_id=uuid4(),
                title="Aviso válido",
                content="Conteúdo válido de aviso.",
                priority="CRITICAL",  # type: ignore[arg-type]
            )

        with pytest.raises(ValidationError):
            ClassAnnouncementCreateSchema(
                class_id=uuid4(),
                title="Aviso válido",
                content="Conteúdo válido de aviso.",
                expires_at=True,  # type: ignore[arg-type]
            )

    def test_update_schema_requires_at_least_one_field_and_blocks_null_non_nullable(
        self,
    ) -> None:
        with pytest.raises(ValidationError):
            ClassAnnouncementUpdateSchema()

        with pytest.raises(ValidationError):
            ClassAnnouncementUpdateSchema(title=None)

        with pytest.raises(ValidationError):
            ClassAnnouncementUpdateSchema(is_pinned=None)

        ok = ClassAnnouncementUpdateSchema(is_pinned=False, subject_id=None)
        assert ok.is_pinned is False
        assert "subject_id" in ok.model_fields_set

    def test_orm_model_validations(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        ann = ClassAnnouncement(
            class_id=uuid4(),
            author_id=uuid4(),
            title="  Mudança de Oficina  ",
            content="  A aula prática será na Bancada 04.  ",
            priority=AnnouncementPriority.IMPORTANT,
            is_pinned=True,
            published_at=now,
            expires_at=now + timedelta(days=2),
        )
        assert ann.title == "Mudança de Oficina"
        assert ann.content == "A aula prática será na Bancada 04."

        with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
            ClassAnnouncement(
                class_id=uuid4(),
                author_id=uuid4(),
                title="ab",
                content="Conteúdo válido",
            )

        with pytest.raises(ValueError, match="pelo menos 5 caracteres"):
            ClassAnnouncement(
                class_id=uuid4(),
                author_id=uuid4(),
                title="Aviso válido",
                content="1234",
            )

        with pytest.raises(ValueError, match="posterior à publicação"):
            ClassAnnouncement(
                class_id=uuid4(),
                author_id=uuid4(),
                title="Aviso válido",
                content="Conteúdo válido",
                published_at=now,
                expires_at=now - timedelta(minutes=5),
            )


@pytest.mark.asyncio
async def test_announcements_crud_priorities_pinning_and_rbac_flow(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST, PATCH e DELETE /api/v1/announcements com RBAC, prioridades, fixação e integridade (BE-041)."""
    teacher_a, teacher_a_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.a041@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Turma A",
        registration_number="PROF-041-A",
    )
    teacher_b, teacher_b_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.b041@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Co-Docente Turma A",
        registration_number="PROF-041-B",
    )
    outsider_teacher, outsider_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.externo041@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Externo",
        registration_number="PROF-041-OUT",
    )
    _coord, coord_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord041@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coordenador Pedagógico",
        registration_number="COORD-041",
    )
    _admin, admin_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="admin041@senai.br",
        role=UserRole.ADMIN,
        full_name="Admin SENAI",
        registration_number="ADM-041",
    )
    _student, student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno041@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Bloqueado",
        registration_number="ALU-041",
    )

    with db_session_factory() as session:
        course_1 = CourseRepository(session).create(
            code="TEC-MEC-041",
            name="Técnico em Mecânica",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        course_2 = CourseRepository(session).create(
            code="TEC-ELE-041",
            name="Técnico em Eletrotécnica",
            description="Outro curso",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course_1.id,
            code="MEC-2026-041",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subj_met = SubjectRepository(session).create(
            course_id=course_1.id,
            code="MET-041",
            name="Metrologia Dimensional",
            workload_hours=60,
            is_active=True,
        )
        subj_tor = SubjectRepository(session).create(
            course_id=course_1.id,
            code="TOR-041",
            name="Tornearia Mecânica",
            workload_hours=80,
            is_active=True,
        )
        subj_other_course = SubjectRepository(session).create(
            course_id=course_2.id,
            code="ELE-041",
            name="Comandos Elétricos",
            workload_hours=60,
            is_active=True,
        )
        session.add_all(
            [
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
                    is_main_teacher=False,
                ),
            ]
        )
        session.commit()

    ta_headers = {"Authorization": f"Bearer {teacher_a_token}"}
    tb_headers = {"Authorization": f"Bearer {teacher_b_token}"}
    out_headers = {"Authorization": f"Bearer {outsider_teacher_token}"}
    coord_headers = {"Authorization": f"Bearer {coord_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    stu_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Bloqueio 401 sem token e 403 para perfil STUDENT
    assert (
        await client.post(
            "/api/v1/announcements",
            json={
                "class_id": str(class_a.id),
                "title": "Aviso sem auth",
                "content": "Conteúdo do aviso sem autenticação.",
            },
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    stu_create_res = await client.post(
        "/api/v1/announcements",
        headers=stu_headers,
        json={
            "class_id": str(class_a.id),
            "title": "Tentativa de estudante",
            "content": "Estudante não pode publicar aviso oficial.",
        },
    )
    assert stu_create_res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Validações Pydantic -> HTTP 400 VALIDATION_ERROR
    bad_payload_res = await client.post(
        "/api/v1/announcements",
        headers=ta_headers,
        json={
            "class_id": str(class_a.id),
            "title": "AB",
            "content": "Curto",
        },
    )
    assert bad_payload_res.status_code == status.HTTP_400_BAD_REQUEST
    assert bad_payload_res.json()["error"] == "VALIDATION_ERROR"

    # 3. Bloqueios contextuais de professor (não atribuído à turma / não leciona disciplina)
    out_res = await client.post(
        "/api/v1/announcements",
        headers=out_headers,
        json={
            "class_id": str(class_a.id),
            "title": "Aviso de professor externo",
            "content": "Professor sem alocação na turma deve receber 403.",
        },
    )
    assert out_res.status_code == status.HTTP_403_FORBIDDEN
    assert out_res.json()["message"] == ANNOUNCEMENT_TEACHER_CLASS_FORBIDDEN_MESSAGE

    wrong_subj_teacher_res = await client.post(
        "/api/v1/announcements",
        headers=ta_headers,
        json={
            "class_id": str(class_a.id),
            "subject_id": str(subj_tor.id),
            "title": "Aviso sobre Tornearia",
            "content": "Prof A não leciona Tornearia nesta turma.",
        },
    )
    assert wrong_subj_teacher_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        wrong_subj_teacher_res.json()["message"]
        == ANNOUNCEMENT_TEACHER_SUBJECT_FORBIDDEN_MESSAGE
    )

    # 4. Disciplina de outro curso -> 422; Turma/Disciplina inexistente -> 404; Expiração no passado -> 422
    mismatch_res = await client.post(
        "/api/v1/announcements",
        headers=coord_headers,
        json={
            "class_id": str(class_a.id),
            "subject_id": str(subj_other_course.id),
            "title": "Aviso disciplina outro curso",
            "content": "Disciplina pertence a outro curso técnico.",
        },
    )
    assert mismatch_res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert mismatch_res.json()["message"] == ANNOUNCEMENT_SUBJECT_COURSE_MISMATCH_MESSAGE

    not_found_cls = await client.post(
        "/api/v1/announcements",
        headers=coord_headers,
        json={
            "class_id": str(uuid4()),
            "title": "Turma inexistente",
            "content": "Deve retornar 404 Not Found.",
        },
    )
    assert not_found_cls.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_cls.json()["message"] == ANNOUNCEMENT_CLASS_NOT_FOUND_MESSAGE

    not_found_subj = await client.post(
        "/api/v1/announcements",
        headers=coord_headers,
        json={
            "class_id": str(class_a.id),
            "subject_id": str(uuid4()),
            "title": "Disciplina inexistente",
            "content": "Deve retornar 404 Not Found.",
        },
    )
    assert not_found_subj.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_subj.json()["message"] == ANNOUNCEMENT_SUBJECT_NOT_FOUND_MESSAGE

    past_exp = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    invalid_exp_res = await client.post(
        "/api/v1/announcements",
        headers=ta_headers,
        json={
            "class_id": str(class_a.id),
            "title": "Aviso com expiração passada",
            "content": "Expiração anterior à publicação não é permitida.",
            "expires_at": past_exp,
        },
    )
    assert invalid_exp_res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid_exp_res.json()["message"] == ANNOUNCEMENT_INVALID_EXPIRATION_MESSAGE

    # 5. Criação bem-sucedida (HTTP 201) pelo professor da turma com URGENT e is_pinned=True
    future_exp = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = await client.post(
        "/api/v1/announcements",
        headers=ta_headers,
        json={
            "class_id": str(class_a.id),
            "subject_id": str(subj_met.id),
            "title": "Uso obrigatório de óculos de segurança na oficina",
            "content": "Na próxima aula prática no laboratório de Metrologia, trazer paquímetro e EPI completo.",
            "priority": "URGENT",
            "is_pinned": True,
            "expires_at": future_exp,
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    created_body = create_res.json()
    ann_id = UUID(created_body["id"])
    assert created_body["class_id"] == str(class_a.id)
    assert created_body["subject_id"] == str(subj_met.id)
    assert created_body["author_id"] == str(teacher_a.id)
    assert created_body["priority"] == "URGENT"
    assert created_body["is_pinned"] is True
    assert created_body["subject"]["code"] == "MET-041"
    assert created_body["author"]["full_name"] == "Prof. Turma A"
    assert created_body["academic_class"]["code"] == "MEC-2026-041"

    # 6. Criação pelo Coordenador e Admin (HTTP 201) com prioridades IMPORTANT e NORMAL
    coord_create_res = await client.post(
        "/api/v1/announcements",
        headers=coord_headers,
        json={
            "class_id": str(class_a.id),
            "title": "Calendário de Conselho de Classe",
            "content": "O conselho intermediário da turma acontecerá na próxima sexta-feira.",
            "priority": "IMPORTANT",
            "is_pinned": False,
        },
    )
    assert coord_create_res.status_code == status.HTTP_201_CREATED
    coord_ann_id = UUID(coord_create_res.json()["id"])
    assert coord_create_res.json()["subject"] is None

    admin_create_res = await client.post(
        "/api/v1/announcements",
        headers=admin_headers,
        json={
            "class_id": str(class_a.id),
            "title": "Manutenção Preventiva do Laboratório",
            "content": "Laboratório passará por calibração dos instrumentos na terça-feira.",
        },
    )
    assert admin_create_res.status_code == status.HTTP_201_CREATED
    assert admin_create_res.json()["priority"] == "NORMAL"
    assert admin_create_res.json()["is_pinned"] is False

    # 7. Segurança em PATCH/DELETE: estudante (403) e outro professor da mesma turma que não é autor (403)
    assert (
        await client.patch(
            f"/api/v1/announcements/{ann_id}",
            headers=stu_headers,
            json={"is_pinned": False},
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    other_teacher_patch = await client.patch(
        f"/api/v1/announcements/{ann_id}",
        headers=tb_headers,
        json={"title": "Tentativa de edição por colega"},
    )
    assert other_teacher_patch.status_code == status.HTTP_403_FORBIDDEN
    assert (
        other_teacher_patch.json()["message"]
        == ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE
    )

    other_teacher_del = await client.delete(
        f"/api/v1/announcements/{ann_id}",
        headers=tb_headers,
    )
    assert other_teacher_del.status_code == status.HTTP_403_FORBIDDEN
    assert (
        other_teacher_del.json()["message"]
        == ANNOUNCEMENT_TEACHER_AUTHOR_FORBIDDEN_MESSAGE
    )

    # 8. PATCH pelo próprio autor: altera prioridade, desafixa e limpa subject_id/expires_at
    patch_res = await client.patch(
        f"/api/v1/announcements/{ann_id}",
        headers=ta_headers,
        json={
            "title": "Uso obrigatório de EPI atualizado",
            "priority": "IMPORTANT",
            "is_pinned": False,
            "subject_id": None,
            "expires_at": None,
        },
    )
    assert patch_res.status_code == status.HTTP_200_OK
    patched = patch_res.json()
    assert patched["title"] == "Uso obrigatório de EPI atualizado"
    assert patched["priority"] == "IMPORTANT"
    assert patched["is_pinned"] is False
    assert patched["subject_id"] is None
    assert patched["subject"] is None
    assert patched["expires_at"] is None

    # 9. Coordenação pode fixar/editar qualquer aviso da turma e excluir avisos
    coord_pin_res = await client.patch(
        f"/api/v1/announcements/{ann_id}",
        headers=coord_headers,
        json={"is_pinned": True},
    )
    assert coord_pin_res.status_code == status.HTTP_200_OK
    assert coord_pin_res.json()["is_pinned"] is True

    # 10. DELETE pelo autor (204) e pela coordenação (204), seguido de 404
    del_res = await client.delete(
        f"/api/v1/announcements/{ann_id}",
        headers=ta_headers,
    )
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
    assert del_res.content == b""

    del_again = await client.delete(
        f"/api/v1/announcements/{ann_id}",
        headers=coord_headers,
    )
    assert del_again.status_code == status.HTTP_404_NOT_FOUND
    assert del_again.json()["message"] == ANNOUNCEMENT_NOT_FOUND_MESSAGE

    del_coord = await client.delete(
        f"/api/v1/announcements/{coord_ann_id}",
        headers=coord_headers,
    )
    assert del_coord.status_code == status.HTTP_204_NO_CONTENT

    with db_session_factory() as session:
        assert session.get(ClassAnnouncement, ann_id) is None
        assert session.get(ClassAnnouncement, coord_ann_id) is None
