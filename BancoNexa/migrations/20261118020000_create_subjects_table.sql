-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE DISCIPLINAS (DB-013)
-- Versão: 20261118020000_create_subjects_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `subjects` para estruturar as unidades curriculares
-- teórico-práticas que compõem a matriz dos cursos técnicos SENAI (ex.:
-- 'Metrologia Dimensional', 'Processos de Fabricação Mecânica'):
-- 1. Vínculo obrigatório a um curso (`course_id UUID NOT NULL`) com FK
--    `fk_subjects_course` (`ON DELETE RESTRICT ON UPDATE CASCADE`).
-- 2. Carga horária estritamente positiva (`chk_subjects_workload_positive`:
--    `workload_hours > 0`).
-- 3. Unicidade de código da disciplina por curso (`uq_subjects_course_code` +
--    índice funcional case-insensitive `idx_subjects_course_code_upper`).
-- 4. Índices em `name` (`idx_subjects_name` e `idx_subjects_name_lower` com
--    `text_pattern_ops`) para pesquisas autocompletar rápidas na secretaria/API.
-- 5. Suporte a ementa técnica (`syllabus TEXT`) e soft delete (`is_active`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de disciplinas teórico-práticas (`subjects`)
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(150) NOT NULL,
    workload_hours INTEGER NOT NULL,
    syllabus TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Unicidade de código de unidade curricular dentro de um mesmo curso
    CONSTRAINT uq_subjects_course_code UNIQUE (course_id, code),

    -- Padronização de código e nome não vazios
    CONSTRAINT chk_subjects_code_format CHECK (
        code = UPPER(BTRIM(code))
        AND CHAR_LENGTH(code) >= 2
    ),
    CONSTRAINT chk_subjects_name_not_empty CHECK (
        CHAR_LENGTH(BTRIM(name)) >= 3
    ),

    -- Critério de Aceitação 2: Carga horária estritamente positiva
    CONSTRAINT chk_subjects_workload_positive CHECK (workload_hours > 0),

    -- Critério de Aceitação 1: Disciplina vinculada obrigatoriamente a um curso
    CONSTRAINT fk_subjects_course
        FOREIGN KEY (course_id) REFERENCES courses (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índices em `name` para pesquisas autocompletar e filtros da API
CREATE INDEX IF NOT EXISTS idx_subjects_name
    ON subjects USING BTREE (name);

CREATE INDEX IF NOT EXISTS idx_subjects_name_lower
    ON subjects USING BTREE (LOWER(name) text_pattern_ops);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subjects_course_code_upper
    ON subjects (course_id, UPPER(code));

CREATE INDEX IF NOT EXISTS idx_subjects_course_active
    ON subjects USING BTREE (course_id, is_active);

-- 4. Função e Trigger PL/pgSQL para padronizar code (UPPER/TRIM), limpar textos e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_subjects_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.code IS NOT NULL THEN
        NEW.code := UPPER(BTRIM(NEW.code));
    END IF;

    IF NEW.name IS NOT NULL THEN
        NEW.name := BTRIM(NEW.name);
    END IF;

    IF NEW.syllabus IS NOT NULL THEN
        NEW.syllabus := BTRIM(NEW.syllabus);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_subjects_normalize_and_touch ON subjects;

CREATE TRIGGER trg_subjects_normalize_and_touch
    BEFORE INSERT OR UPDATE ON subjects
    FOR EACH ROW
    EXECUTE FUNCTION fn_subjects_normalize_and_touch();

COMMIT;
