-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA class_announcements (DB-041)
-- Versão: 20261127000000_create_class_announcements_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-005 (announcement_priority_enum), DB-006 (users),
--               DB-012 (classes), DB-013 (subjects)
-- =============================================================================
-- Armazena comunicados oficiais publicados por professores e coordenadores no
-- mural de uma turma ou disciplina, com suporte a fixação (is_pinned) e
-- prioridade visual ordenada no feed.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE announcement_priority_enum AS ENUM ('NORMAL', 'IMPORTANT', 'URGENT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS class_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID,
    author_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    priority announcement_priority_enum NOT NULL DEFAULT 'NORMAL',
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    CONSTRAINT chk_announcements_title_not_empty
        CHECK (CHAR_LENGTH(BTRIM(title)) >= 3),
    CONSTRAINT chk_announcements_content_not_empty
        CHECK (CHAR_LENGTH(BTRIM(content)) >= 5),
    CONSTRAINT chk_announcements_expiration
        CHECK (expires_at IS NULL OR expires_at > published_at),
    CONSTRAINT fk_announcements_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_announcements_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_announcements_author
        FOREIGN KEY (author_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Trigger de integridade acadêmica:
-- 1) author_id deve pertencer a TEACHER, COORDINATOR ou ADMIN (bloqueia STUDENT).
-- 2) Se subject_id for informado, deve pertencer ao mesmo curso da turma (class_id).
CREATE OR REPLACE FUNCTION fn_class_announcements_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_author_role user_role_enum;
    v_class_course_id UUID;
    v_subject_course_id UUID;
BEGIN
    SELECT role INTO v_author_role
    FROM users
    WHERE id = NEW.author_id;

    IF v_author_role IS NULL OR v_author_role NOT IN ('TEACHER', 'COORDINATOR', 'ADMIN') THEN
        RAISE EXCEPTION 'Somente docentes, coordenadores ou administradores podem publicar avisos oficiais na turma (author_id=%).', NEW.author_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_announcements_author_role';
    END IF;

    IF NEW.subject_id IS NOT NULL THEN
        SELECT course_id INTO v_class_course_id FROM classes WHERE id = NEW.class_id;
        SELECT course_id INTO v_subject_course_id FROM subjects WHERE id = NEW.subject_id;

        IF v_subject_course_id IS DISTINCT FROM v_class_course_id THEN
            RAISE EXCEPTION 'A disciplina (%) não pertence ao mesmo curso da turma (%).', NEW.subject_id, NEW.class_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_announcements_subject_course';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_class_announcements_validate_integrity ON class_announcements;
CREATE TRIGGER trg_class_announcements_validate_integrity
    BEFORE INSERT OR UPDATE ON class_announcements
    FOR EACH ROW
    EXECUTE FUNCTION fn_class_announcements_validate_integrity();

-- Índice composto exigido pelo Critério 3 de DB-041: mural ordenado por fixados e mais recentes
CREATE INDEX IF NOT EXISTS idx_class_announcements_feed
    ON class_announcements USING BTREE (class_id, is_pinned DESC, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_class_announcements_priority
    ON class_announcements USING BTREE (class_id, priority, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_class_announcements_author
    ON class_announcements USING BTREE (author_id);

COMMENT ON TABLE class_announcements IS
    '[DB-041] Mural oficial de avisos por turma e disciplina (SENAI/NEXA), com fixação e prioridade visual.';
COMMENT ON COLUMN class_announcements.is_pinned IS
    'Quando TRUE, mantém o comunicado fixado no topo do mural da turma.';

COMMIT;
