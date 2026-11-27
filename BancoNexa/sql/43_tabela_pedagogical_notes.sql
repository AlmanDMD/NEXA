-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA pedagogical_notes (DB-043)
-- Versão: 20261127020000_create_pedagogical_notes_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-005 (note_visibility_scope_enum, note_category_enum),
--               DB-006 (users), DB-009 (audit_logs), DB-017 (enrollments)
-- =============================================================================
-- Armazena observações pedagógicas restritas registradas por professores e
-- coordenação com controle rigoroso de visibility_scope, RLS e rastro
-- obrigatório em audit_logs (escrita via trigger + leitura via função auditada).
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE note_visibility_scope_enum AS ENUM ('PRIVATE_AUTHOR', 'TEACHERS_AND_COORD', 'COORDINATION_ONLY');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE note_category_enum AS ENUM ('INTERVENTION', 'MENTORING', 'BEHAVIORAL', 'ACCOMMODATION');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS pedagogical_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    author_id UUID NOT NULL,
    visibility_scope note_visibility_scope_enum NOT NULL DEFAULT 'PRIVATE_AUTHOR',
    category note_category_enum NOT NULL,
    note_content TEXT NOT NULL,
    requires_followup BOOLEAN NOT NULL DEFAULT FALSE,
    followup_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_pedagogical_notes_content_not_empty
        CHECK (CHAR_LENGTH(BTRIM(note_content)) >= 5),
    CONSTRAINT chk_pedagogical_notes_followup_consistency
        CHECK (followup_date IS NULL OR requires_followup = TRUE),
    CONSTRAINT fk_pedagogical_notes_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pedagogical_notes_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pedagogical_notes_author
        FOREIGN KEY (author_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Trigger de integridade:
-- 1) student_id deve ter role STUDENT e ser o titular da matrícula (enrollment_id).
-- 2) author_id deve ter role TEACHER, COORDINATOR ou ADMIN (nunca STUDENT).
-- 3) Atualiza updated_at automaticamente.
CREATE OR REPLACE FUNCTION fn_pedagogical_notes_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_enrollment_student_id UUID;
    v_author_role user_role_enum;
BEGIN
    SELECT role INTO v_student_role FROM users WHERE id = NEW.student_id;
    IF v_student_role IS DISTINCT FROM 'STUDENT' THEN
        RAISE EXCEPTION 'Observação pedagógica deve referenciar usuário STUDENT (student_id=%).', NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_pedagogical_notes_student_role';
    END IF;

    SELECT student_id INTO v_enrollment_student_id FROM enrollments WHERE id = NEW.enrollment_id;
    IF v_enrollment_student_id IS DISTINCT FROM NEW.student_id THEN
        RAISE EXCEPTION 'A matrícula (%) não pertence ao estudante (%).', NEW.enrollment_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_pedagogical_notes_enrollment_owner';
    END IF;

    SELECT role INTO v_author_role FROM users WHERE id = NEW.author_id;
    IF v_author_role IS NULL OR v_author_role NOT IN ('TEACHER', 'COORDINATOR', 'ADMIN') THEN
        RAISE EXCEPTION 'Somente TEACHER, COORDINATOR ou ADMIN podem criar observações pedagógicas (author_id=%).', NEW.author_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_pedagogical_notes_author_role';
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_pedagogical_notes_validate_integrity ON pedagogical_notes;
CREATE TRIGGER trg_pedagogical_notes_validate_integrity
    BEFORE INSERT OR UPDATE ON pedagogical_notes
    FOR EACH ROW
    EXECUTE FUNCTION fn_pedagogical_notes_validate_integrity();

-- Trigger de auditoria obrigatória em audit_logs (Critério 3 de DB-043)
-- Registra metadados estruturais sem jamais expor note_content em texto claro nos logs.
CREATE OR REPLACE FUNCTION fn_pedagogical_notes_audit_trail()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_actor_id UUID;
    v_entity_id UUID;
    v_action VARCHAR(60);
    v_old JSONB;
    v_new JSONB;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_actor_id := NEW.author_id;
        v_entity_id := NEW.id;
        v_action := 'PEDAGOGICAL_NOTE_CREATE';
        v_old := NULL;
        v_new := jsonb_build_object(
            'student_id', NEW.student_id,
            'enrollment_id', NEW.enrollment_id,
            'visibility_scope', NEW.visibility_scope,
            'category', NEW.category,
            'requires_followup', NEW.requires_followup,
            'followup_date', NEW.followup_date
        );
    ELSIF TG_OP = 'UPDATE' THEN
        v_actor_id := COALESCE(
            NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID,
            NEW.author_id
        );
        v_entity_id := NEW.id;
        v_action := 'PEDAGOGICAL_NOTE_UPDATE';
        v_old := jsonb_build_object(
            'visibility_scope', OLD.visibility_scope,
            'category', OLD.category,
            'requires_followup', OLD.requires_followup,
            'followup_date', OLD.followup_date
        );
        v_new := jsonb_build_object(
            'visibility_scope', NEW.visibility_scope,
            'category', NEW.category,
            'requires_followup', NEW.requires_followup,
            'followup_date', NEW.followup_date
        );
    ELSE
        v_actor_id := COALESCE(
            NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID,
            OLD.author_id
        );
        v_entity_id := OLD.id;
        v_action := 'PEDAGOGICAL_NOTE_DELETE';
        v_old := jsonb_build_object(
            'student_id', OLD.student_id,
            'visibility_scope', OLD.visibility_scope,
            'category', OLD.category
        );
        v_new := NULL;
    END IF;

    INSERT INTO audit_logs (user_id, action, entity, entity_id, old_values, new_values)
    VALUES (v_actor_id, v_action, 'pedagogical_notes', v_entity_id::TEXT, v_old, v_new);

    RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_pedagogical_notes_audit_trail ON pedagogical_notes;
CREATE TRIGGER trg_pedagogical_notes_audit_trail
    AFTER INSERT OR UPDATE OR DELETE ON pedagogical_notes
    FOR EACH ROW
    EXECUTE FUNCTION fn_pedagogical_notes_audit_trail();

-- Função auditada de leitura: verifica visibility_scope e registra PEDAGOGICAL_NOTE_READ em audit_logs
CREATE OR REPLACE FUNCTION fn_read_pedagogical_note_audited(
    p_note_id UUID,
    p_reader_id UUID
)
RETURNS TABLE (
    id UUID,
    student_id UUID,
    enrollment_id UUID,
    author_id UUID,
    visibility_scope note_visibility_scope_enum,
    category note_category_enum,
    note_content TEXT,
    requires_followup BOOLEAN,
    followup_date DATE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_reader_role user_role_enum;
    v_note pedagogical_notes%ROWTYPE;
BEGIN
    SELECT role INTO v_reader_role FROM users WHERE users.id = p_reader_id;
    SELECT * INTO v_note FROM pedagogical_notes pn WHERE pn.id = p_note_id;

    IF v_note.id IS NULL THEN
        RETURN;
    END IF;

    IF v_reader_role IS NULL OR v_reader_role = 'STUDENT' THEN
        RAISE EXCEPTION 'Acesso negado: estudantes não podem consultar pedagogical_notes.'
            USING ERRCODE = '42501';
    END IF;

    IF v_note.visibility_scope = 'PRIVATE_AUTHOR' AND v_note.author_id <> p_reader_id AND v_reader_role <> 'ADMIN' THEN
        RAISE EXCEPTION 'Acesso negado: observação restrita ao autor (PRIVATE_AUTHOR).'
            USING ERRCODE = '42501';
    END IF;

    IF v_note.visibility_scope = 'COORDINATION_ONLY' AND v_reader_role NOT IN ('COORDINATOR', 'ADMIN') THEN
        RAISE EXCEPTION 'Acesso negado: observação restrita à coordenação (COORDINATION_ONLY).'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO audit_logs (user_id, action, entity, entity_id, new_values)
    VALUES (
        p_reader_id,
        'PEDAGOGICAL_NOTE_READ',
        'pedagogical_notes',
        v_note.id::TEXT,
        jsonb_build_object(
            'reader_role', v_reader_role,
            'visibility_scope', v_note.visibility_scope,
            'student_id', v_note.student_id
        )
    );

    RETURN QUERY
    SELECT
        v_note.id,
        v_note.student_id,
        v_note.enrollment_id,
        v_note.author_id,
        v_note.visibility_scope,
        v_note.category,
        v_note.note_content,
        v_note.requires_followup,
        v_note.followup_date,
        v_note.created_at,
        v_note.updated_at;
END;
$$;

-- Row-Level Security (RLS) alinhada ao visibility_scope
ALTER TABLE pedagogical_notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_pedagogical_notes_scope_isolation ON pedagogical_notes;
CREATE POLICY pol_pedagogical_notes_scope_isolation
    ON pedagogical_notes
    USING (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') = 'ADMIN'
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'COORDINATOR'
            AND (
                visibility_scope IN ('TEACHERS_AND_COORD', 'COORDINATION_ONLY')
                OR author_id::TEXT = current_setting('app.current_user_id', TRUE)
            )
        )
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'TEACHER'
            AND (
                visibility_scope = 'TEACHERS_AND_COORD'
                OR author_id::TEXT = current_setting('app.current_user_id', TRUE)
            )
        )
    )
    WITH CHECK (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') IN ('ADMIN', 'COORDINATOR', 'TEACHER')
    );

CREATE INDEX IF NOT EXISTS idx_pedagogical_notes_student_created
    ON pedagogical_notes USING BTREE (student_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pedagogical_notes_enrollment_scope
    ON pedagogical_notes USING BTREE (enrollment_id, visibility_scope);

CREATE INDEX IF NOT EXISTS idx_pedagogical_notes_author_followup
    ON pedagogical_notes USING BTREE (author_id, requires_followup, followup_date);

COMMENT ON TABLE pedagogical_notes IS
    '[DB-043] Observações pedagógicas restritas com visibility_scope, RLS e auditoria obrigatória em audit_logs.';

COMMIT;
