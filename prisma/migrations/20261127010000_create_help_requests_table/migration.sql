-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA help_requests (DB-042)
-- Versão: 20261127010000_create_help_requests_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-005 (help_request_category_enum, help_request_status_enum),
--               DB-006 (users), DB-013 (subjects), DB-014 (learning_modules),
--               DB-017 (enrollments)
-- =============================================================================
-- Persiste solicitações confidenciais de apoio pedagógico e mentoria criadas
-- por estudantes, com sigilo estrito (is_confidential DEFAULT TRUE + RLS),
-- máquina de estados (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED) e índices de
-- atendimento por professor e aluno.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE help_request_category_enum AS ENUM ('TECHNICAL_DOUBT', 'PRACTICAL_DIFFICULTY', 'PERSONAL_PEDAGOGICAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE help_request_status_enum AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS help_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    assigned_teacher_id UUID,
    category help_request_category_enum NOT NULL,
    subject_title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    is_confidential BOOLEAN NOT NULL DEFAULT TRUE,
    status help_request_status_enum NOT NULL DEFAULT 'OPEN',
    resolution_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,

    CONSTRAINT chk_help_requests_title_not_empty
        CHECK (CHAR_LENGTH(BTRIM(subject_title)) >= 3),
    CONSTRAINT chk_help_requests_desc_not_empty
        CHECK (CHAR_LENGTH(BTRIM(description)) >= 10),
    CONSTRAINT chk_help_requests_closed_at_consistency
        CHECK (
            (status = 'CLOSED' AND closed_at IS NOT NULL)
            OR (status <> 'CLOSED' AND closed_at IS NULL)
        ),
    CONSTRAINT fk_help_requests_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_teacher
        FOREIGN KEY (assigned_teacher_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Trigger de integridade acadêmica, sigilo e máquina de estados:
-- 1) student_id deve ter role = STUDENT e ser o titular de enrollment_id.
-- 2) assigned_teacher_id (se informado) deve ter role TEACHER, COORDINATOR ou ADMIN.
-- 3) module_id (se informado) deve pertencer à disciplina subject_id.
-- 4) Transições válidas: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED (e fechamento direto permitido).
-- 5) Atualiza updated_at automaticamente e preenche closed_at ao transicionar para CLOSED.
CREATE OR REPLACE FUNCTION fn_help_requests_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_enrollment_student_id UUID;
    v_teacher_role user_role_enum;
    v_module_subject_id UUID;
BEGIN
    SELECT role INTO v_student_role FROM users WHERE id = NEW.student_id;
    IF v_student_role IS DISTINCT FROM 'STUDENT' THEN
        RAISE EXCEPTION 'Solicitação de ajuda deve pertencer a um usuário com role STUDENT (student_id=%).', NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_help_requests_student_role';
    END IF;

    SELECT student_id INTO v_enrollment_student_id FROM enrollments WHERE id = NEW.enrollment_id;
    IF v_enrollment_student_id IS DISTINCT FROM NEW.student_id THEN
        RAISE EXCEPTION 'A matrícula (%) não pertence ao estudante (%).', NEW.enrollment_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_help_requests_enrollment_owner';
    END IF;

    IF NEW.assigned_teacher_id IS NOT NULL THEN
        SELECT role INTO v_teacher_role FROM users WHERE id = NEW.assigned_teacher_id;
        IF v_teacher_role IS NULL OR v_teacher_role NOT IN ('TEACHER', 'COORDINATOR', 'ADMIN') THEN
            RAISE EXCEPTION 'Responsável pelo atendimento deve ser TEACHER, COORDINATOR ou ADMIN (assigned_teacher_id=%).', NEW.assigned_teacher_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_help_requests_teacher_role';
        END IF;
    END IF;

    IF NEW.module_id IS NOT NULL THEN
        SELECT subject_id INTO v_module_subject_id FROM learning_modules WHERE id = NEW.module_id;
        IF v_module_subject_id IS DISTINCT FROM NEW.subject_id THEN
            RAISE EXCEPTION 'O módulo (%) não pertence à disciplina informada (%).', NEW.module_id, NEW.subject_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_help_requests_module_subject';
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.status IS DISTINCT FROM OLD.status THEN
        IF OLD.status = 'CLOSED' THEN
            RAISE EXCEPTION 'Solicitação de apoio já encerrada (CLOSED) não pode regressar para estado %.', NEW.status
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_help_requests_status_transition';
        END IF;
        IF OLD.status = 'RESOLVED' AND NEW.status = 'OPEN' THEN
            RAISE EXCEPTION 'Transição inválida de RESOLVED para OPEN; utilize IN_PROGRESS ou CLOSED.'
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_help_requests_status_transition';
        END IF;
    END IF;

    IF NEW.status = 'CLOSED' AND NEW.closed_at IS NULL THEN
        NEW.closed_at := CURRENT_TIMESTAMP;
    ELSIF NEW.status <> 'CLOSED' THEN
        NEW.closed_at := NULL;
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_help_requests_validate_integrity ON help_requests;
CREATE TRIGGER trg_help_requests_validate_integrity
    BEFORE INSERT OR UPDATE ON help_requests
    FOR EACH ROW
    EXECUTE FUNCTION fn_help_requests_validate_integrity();

-- Row-Level Security (RLS) garantindo confidencialidade estrita entre estudantes
ALTER TABLE help_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_help_requests_confidential_isolation ON help_requests;
CREATE POLICY pol_help_requests_confidential_isolation
    ON help_requests
    USING (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') IN ('ADMIN', 'COORDINATOR', 'TEACHER')
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'STUDENT'
            AND student_id::TEXT = current_setting('app.current_user_id', TRUE)
        )
    )
    WITH CHECK (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') IN ('ADMIN', 'COORDINATOR', 'TEACHER')
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'STUDENT'
            AND student_id::TEXT = current_setting('app.current_user_id', TRUE)
        )
    );

-- Índices obrigatórios do Critério 3 de DB-042
CREATE INDEX IF NOT EXISTS idx_help_requests_teacher_status
    ON help_requests USING BTREE (assigned_teacher_id, status);

CREATE INDEX IF NOT EXISTS idx_help_requests_student_status
    ON help_requests USING BTREE (student_id, status);

CREATE INDEX IF NOT EXISTS idx_help_requests_enrollment_status
    ON help_requests USING BTREE (enrollment_id, status);

COMMENT ON TABLE help_requests IS
    '[DB-042] Solicitações confidenciais de apoio pedagógico e mentoria feitas por estudantes (protegidas por RLS).';
COMMENT ON COLUMN help_requests.is_confidential IS
    'Ativa por padrão (TRUE), impedindo visualização por outros estudantes da turma.';

COMMIT;
