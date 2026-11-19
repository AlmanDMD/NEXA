-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE MÓDULOS PRÁTICOS (DB-014)
-- Versão: 20261118030000_create_learning_modules_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `learning_modules` para modelar a estrutura modular
-- prática característica do SENAI dentro de cada disciplina (ex.: 'Módulo de
-- Tornearia Cilíndrica', 'Metrologia com Micrômetro'):
-- 1. Vínculo obrigatório a uma disciplina (`subject_id UUID NOT NULL`) com FK
--    `fk_learning_modules_subject` (`ON DELETE CASCADE ON UPDATE CASCADE`).
-- 2. Sequência didática recomendada por disciplina (`order_index INTEGER > 0` +
--    unicidade composta `uq_learning_modules_subject_order (subject_id, order_index)`).
-- 3. Nota de corte (`passing_score NUMERIC(4,2) DEFAULT 6.00`) validada entre
--    `0.00` e `10.00` (`chk_learning_modules_passing_score`).
-- 4. Peso ponderado por módulo (`module_weight NUMERIC(4,2) DEFAULT 1.00`,
--    `chk_learning_modules_weight_positive`: `module_weight > 0.00`) para
--    composição ponderada da média final da disciplina (BE-028).
-- 5. Carga horária prática não negativa (`practical_hours >= 0`) e trigger
--    PL/pgSQL para higienização de textos e atualização automática de `updated_at`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de módulos de aprendizagem prática SENAI (`learning_modules`)
CREATE TABLE IF NOT EXISTS learning_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    title VARCHAR(120) NOT NULL,
    order_index INTEGER NOT NULL,
    description TEXT,
    practical_hours INTEGER NOT NULL,
    module_weight NUMERIC(4,2) NOT NULL DEFAULT 1.00,
    passing_score NUMERIC(4,2) NOT NULL DEFAULT 6.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 2: Unicidade e ordem didática sequencial dentro da disciplina
    CONSTRAINT uq_learning_modules_subject_order UNIQUE (subject_id, order_index),
    CONSTRAINT chk_learning_modules_order_positive CHECK (order_index > 0),

    -- Validação de título não vazio e carga horária prática não negativa
    CONSTRAINT chk_learning_modules_title_not_empty CHECK (
        CHAR_LENGTH(BTRIM(title)) >= 3
    ),
    CONSTRAINT chk_learning_modules_hours_non_negative CHECK (practical_hours >= 0),

    -- Observação Técnica: Pesos ponderados diferentes na composição final da disciplina
    CONSTRAINT chk_learning_modules_weight_positive CHECK (module_weight > 0.00),

    -- Critério de Aceitação 3: Nota de corte válida entre 0.00 e 10.00 (padrão 6.00)
    CONSTRAINT chk_learning_modules_passing_score CHECK (
        passing_score >= 0.00 AND passing_score <= 10.00
    ),

    -- Critério de Aceitação 1: Módulo associado a uma disciplina (FK com cascade)
    CONSTRAINT fk_learning_modules_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. Índices para listagem ordenada por sequência didática (BE-014) e busca por título
CREATE INDEX IF NOT EXISTS idx_learning_modules_subject_order
    ON learning_modules USING BTREE (subject_id, order_index ASC);

CREATE INDEX IF NOT EXISTS idx_learning_modules_title
    ON learning_modules USING BTREE (title);

CREATE INDEX IF NOT EXISTS idx_learning_modules_title_lower
    ON learning_modules USING BTREE (LOWER(title) text_pattern_ops);

-- 4. Função e Trigger PL/pgSQL para higienizar textos e atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION fn_learning_modules_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
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

DROP TRIGGER IF EXISTS trg_learning_modules_normalize_and_touch ON learning_modules;

CREATE TRIGGER trg_learning_modules_normalize_and_touch
    BEFORE INSERT OR UPDATE ON learning_modules
    FOR EACH ROW
    EXECUTE FUNCTION fn_learning_modules_normalize_and_touch();

COMMIT;
