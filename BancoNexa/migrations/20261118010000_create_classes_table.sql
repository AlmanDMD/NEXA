-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE TURMAS ACADÊMICAS (DB-012)
-- Versão: 20261118010000_create_classes_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `classes` para modelar as turmas letivas vinculadas a um
-- curso técnico (`courses`) e período letivo (ex.: '2026.1'):
-- 1. Chave estrangeira `course_id -> courses(id)` com `ON DELETE RESTRICT` e
--    `ON UPDATE CASCADE`, impedindo exclusão física de cursos com turmas.
-- 2. Restrição de unicidade composta `uq_classes_code_period` em `(code, period)`
--    + índice único funcional case-insensitive `idx_classes_code_period_upper`.
-- 3. Constraint temporal `chk_classes_date_range` exigindo `start_date < end_date`.
-- 4. Capacidade controlada (`max_students > 0 AND max_students <= 100`) e enums
--    nativos `shift_enum` (MORNING, AFTERNOON, NIGHT) e `class_status_enum`.
-- 5. Índice composto `idx_classes_course_period` em `(course_id, period)` para
--    consultas frequentes de turmas por curso e semestre letivo.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enums nativos (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE shift_enum AS ENUM ('MORNING', 'AFTERNOON', 'NIGHT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE class_status_enum AS ENUM ('PLANNING', 'ACTIVE', 'COMPLETED', 'ARCHIVED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de turmas acadêmicas (`classes`)
CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    code VARCHAR(40) NOT NULL,
    period VARCHAR(20) NOT NULL,
    shift shift_enum NOT NULL,
    max_students INTEGER NOT NULL DEFAULT 40,
    status class_status_enum NOT NULL DEFAULT 'PLANNING',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 2: Unicidade de código da turma por período letivo (SQLSTATE 23505 / P2002)
    CONSTRAINT uq_classes_code_period UNIQUE (code, period),

    -- Padronização de código da turma e período letivo não vazios
    CONSTRAINT chk_classes_code_format CHECK (
        code = UPPER(BTRIM(code))
        AND CHAR_LENGTH(code) >= 3
    ),
    CONSTRAINT chk_classes_period_not_empty CHECK (
        period = BTRIM(period)
        AND CHAR_LENGTH(period) >= 4
    ),

    -- Validação de capacidade de alunos na turma/oficina SENAI
    CONSTRAINT chk_classes_max_students CHECK (max_students > 0 AND max_students <= 100),

    -- Critério de Aceitação 3: Data de início estritamente anterior à data de término
    CONSTRAINT chk_classes_date_range CHECK (start_date < end_date),

    -- Critério de Aceitação 1: Chave estrangeira para courses com ON DELETE RESTRICT
    CONSTRAINT fk_classes_course
        FOREIGN KEY (course_id) REFERENCES courses (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Observação Técnica: Índice composto em (course_id, period) e índices de suporte a filtros
CREATE INDEX IF NOT EXISTS idx_classes_course_period
    ON classes USING BTREE (course_id, period);

CREATE UNIQUE INDEX IF NOT EXISTS idx_classes_code_period_upper
    ON classes (UPPER(code), UPPER(period));

CREATE INDEX IF NOT EXISTS idx_classes_status_period
    ON classes USING BTREE (status, period);

CREATE INDEX IF NOT EXISTS idx_classes_shift
    ON classes USING BTREE (shift);

-- 4. Função e Trigger PL/pgSQL para padronizar code/period e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_classes_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.code IS NOT NULL THEN
        NEW.code := UPPER(BTRIM(NEW.code));
    END IF;

    IF NEW.period IS NOT NULL THEN
        NEW.period := BTRIM(NEW.period);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_classes_normalize_and_touch ON classes;

CREATE TRIGGER trg_classes_normalize_and_touch
    BEFORE INSERT OR UPDATE ON classes
    FOR EACH ROW
    EXECUTE FUNCTION fn_classes_normalize_and_touch();

COMMIT;
