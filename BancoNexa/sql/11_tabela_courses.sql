-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE CURSOS TÉCNICOS (DB-011)
-- Versão: 20261118000000_create_courses_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `courses` para persistir os cursos técnicos oferecidos
-- pela unidade SENAI (ex.: Técnico em Mecânica, Eletromecânica, ADS):
-- 1. Identificador universal UUID v4 nativo (`gen_random_uuid()`).
-- 2. Código SENAI único (`uq_courses_code`, ex.: 'TEC-MEC-01'), normalizado em
--    caixa alta sem espaços extras e protegido por índice funcional único.
-- 3. Validação de carga horária estritamente positiva (`total_hours > 0`).
-- 4. Preservação de histórico via flag `is_active` (soft delete lógico).
-- 5. Proteção contra exclusão física caso existam turmas associadas em `classes`
--    (defesa em profundidade complementar ao `ON DELETE RESTRICT` de DB-012).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de cursos técnicos (`courses`)
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    total_hours INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Código SENAI único (dispara SQLSTATE 23505 / Prisma P2002)
    CONSTRAINT uq_courses_code UNIQUE (code),

    -- Padronização de código SENAI (caixa alta, sem espaços extras, mínimo 3 caracteres)
    CONSTRAINT chk_courses_code_format CHECK (
        code = UPPER(BTRIM(code))
        AND CHAR_LENGTH(code) >= 3
    ),

    -- Validação de nome não vazio
    CONSTRAINT chk_courses_name_not_empty CHECK (
        CHAR_LENGTH(BTRIM(name)) >= 3
    ),

    -- Critério de Aceitação 2: Carga horária total estritamente maior que zero
    CONSTRAINT chk_courses_total_hours_positive CHECK (total_hours > 0)
);

-- 3. Criar índices B-Tree para busca por código, nome (autocompletar/paginação) e status ativo
CREATE INDEX IF NOT EXISTS idx_courses_code
    ON courses USING BTREE (code);

CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_code_upper
    ON courses (UPPER(code));

CREATE INDEX IF NOT EXISTS idx_courses_name
    ON courses USING BTREE (name);

CREATE INDEX IF NOT EXISTS idx_courses_is_active
    ON courses USING BTREE (is_active);

-- 4. Função e Trigger PL/pgSQL para padronizar code (UPPER/TRIM), limpar textos e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_courses_normalize_and_touch()
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

    IF NEW.description IS NOT NULL THEN
        NEW.description := BTRIM(NEW.description);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_courses_normalize_and_touch ON courses;

CREATE TRIGGER trg_courses_normalize_and_touch
    BEFORE INSERT OR UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION fn_courses_normalize_and_touch();

-- 5. Observação Técnica: Impedir exclusão física de cursos com turmas associadas
-- Complementa a restrição ON DELETE RESTRICT definida em `classes.course_id` (DB-012)
CREATE OR REPLACE FUNCTION fn_courses_prevent_delete_with_classes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_has_classes BOOLEAN := FALSE;
BEGIN
    IF to_regclass('public.classes') IS NOT NULL THEN
        EXECUTE 'SELECT EXISTS (SELECT 1 FROM public.classes WHERE course_id = $1)'
            INTO v_has_classes
            USING OLD.id;

        IF v_has_classes THEN
            RAISE EXCEPTION 'Operacao bloqueada: o curso "%" (%) possui turmas associadas e nao pode ser excluido fisicamente. Utilize desativacao logica (is_active = FALSE).', OLD.code, OLD.id
                USING ERRCODE = '23503';
        END IF;
    END IF;

    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_courses_prevent_delete_with_classes ON courses;

CREATE TRIGGER trg_courses_prevent_delete_with_classes
    BEFORE DELETE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION fn_courses_prevent_delete_with_classes();

COMMIT;
