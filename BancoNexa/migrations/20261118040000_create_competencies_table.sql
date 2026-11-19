-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE COMPETÊNCIAS (DB-015)
-- Versão: 20261118040000_create_competencies_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `competencies` para cadastrar a taxonomia oficial de
-- competências e habilidades técnicas do perfil profissional SENAI (ex.:
-- 'COMP-MET-01' — 'Medição com Paquímetro e Tolerância H7'):
-- 1. Código único de competência (`uq_competencies_code` + índice único
--    funcional case-insensitive `idx_competencies_code_upper`), padronizado em
--    caixa alta via trigger.
-- 2. Categorias padronizadas pelo tipo nativo PostgreSQL
--    `competency_category_enum` (`TECHNICAL`, `SAFETY`, `PROCEDURAL` — DB-005).
-- 3. Campos informativos estruturados (`code`, `title`, `category`,
--    `description`) prontos para exibição nos dashboards de gráfico radar
--    (`FE-038`), rubricas práticas (`DB-024`), autoavaliação (`DB-032`),
--    evidências docentes (`DB-033`) e gamificação (`DB-045`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enum nativo competency_category_enum (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE competency_category_enum AS ENUM ('TECHNICAL', 'SAFETY', 'PROCEDURAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de competências e habilidades técnicas (`competencies`)
CREATE TABLE IF NOT EXISTS competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    category competency_category_enum NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Código único da competência técnica
    CONSTRAINT uq_competencies_code UNIQUE (code),

    -- Padronização de código em caixa alta e título informativo não vazio para dashboards de radar
    CONSTRAINT chk_competencies_code_format CHECK (
        code = UPPER(BTRIM(code))
        AND CHAR_LENGTH(code) >= 3
    ),
    CONSTRAINT chk_competencies_title_not_empty CHECK (
        CHAR_LENGTH(BTRIM(title)) >= 3
    )
);

-- 3. Índices para unicidade case-insensitive, filtros por categoria (BE-015) e buscas textuais
CREATE INDEX IF NOT EXISTS idx_competencies_code
    ON competencies USING BTREE (code);

CREATE UNIQUE INDEX IF NOT EXISTS idx_competencies_code_upper
    ON competencies (UPPER(code));

CREATE INDEX IF NOT EXISTS idx_competencies_category
    ON competencies USING BTREE (category);

CREATE INDEX IF NOT EXISTS idx_competencies_title
    ON competencies USING BTREE (title);

CREATE INDEX IF NOT EXISTS idx_competencies_title_lower
    ON competencies USING BTREE (LOWER(title) text_pattern_ops);

-- 4. Função e Trigger PL/pgSQL para padronizar code (UPPER/TRIM), limpar textos e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_competencies_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.code IS NOT NULL THEN
        NEW.code := UPPER(BTRIM(NEW.code));
    END IF;

    IF NEW.title IS NOT NULL THEN
        NEW.title := BTRIM(NEW.title);
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

DROP TRIGGER IF EXISTS trg_competencies_normalize_and_touch ON competencies;

CREATE TRIGGER trg_competencies_normalize_and_touch
    BEFORE INSERT OR UPDATE ON competencies
    FOR EACH ROW
    EXECUTE FUNCTION fn_competencies_normalize_and_touch();

COMMIT;
