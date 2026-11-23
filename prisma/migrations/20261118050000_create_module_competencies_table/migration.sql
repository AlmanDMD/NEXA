-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: MÓDULO-COMPETÊNCIA (DB-016)
-- Versão: 20261118050000_create_module_competencies_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela associativa N:M `module_competencies` vinculando módulos
-- de aprendizagem prática SENAI (`learning_modules`) às competências técnicas
-- (`competencies`):
-- 1. Chave primária composta `pk_module_competencies (module_id, competency_id)`
--    impedindo duplicações de vínculo da mesma competência no mesmo módulo.
-- 2. Exclusão em cascata quando o módulo prático é removido
--    (`fk_module_competencies_module`: `ON DELETE CASCADE ON UPDATE CASCADE`) e
--    proteção referencial da taxonomia (`fk_module_competencies_competency`:
--    `ON DELETE RESTRICT ON UPDATE CASCADE`).
-- 3. Nível requerido delimitado entre 1 (Básico) e 5 (Avançado)
--    (`chk_module_competencies_level`: `required_level BETWEEN 1 AND 5`).
-- 4. Peso ponderado (`weight NUMERIC(3,2) DEFAULT 1.00`,
--    `chk_module_competencies_weight`: `weight > 0.00 AND weight <= 9.99`) para
--    ponderar quais habilidades têm maior impacto na nota do módulo.
-- =============================================================================

BEGIN;

-- 1. Criar tabela associativa N:M (`module_competencies`)
CREATE TABLE IF NOT EXISTS module_competencies (
    module_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    required_level INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Chave primária composta impedindo duplicações
    CONSTRAINT pk_module_competencies PRIMARY KEY (module_id, competency_id),

    -- Observação Técnica: Ponderação de impacto da competência na nota do módulo
    CONSTRAINT chk_module_competencies_weight CHECK (
        weight > 0.00 AND weight <= 9.99
    ),

    -- Critério de Aceitação 3: Nível requerido delimitado entre 1 (Básico) e 5 (Avançado)
    CONSTRAINT chk_module_competencies_level CHECK (
        required_level BETWEEN 1 AND 5
    ),

    -- Critério de Aceitação 2: FK com exclusão em cascata se o módulo for removido
    CONSTRAINT fk_module_competencies_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_module_competencies_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 2. Índices complementares para consultas reversas por competência e filtro por nível requerido
CREATE INDEX IF NOT EXISTS idx_module_competencies_competency
    ON module_competencies USING BTREE (competency_id);

CREATE INDEX IF NOT EXISTS idx_module_competencies_module_level
    ON module_competencies USING BTREE (module_id, required_level);

-- 3. Função e Trigger PL/pgSQL para atualizar updated_at em alterações de peso ou nível requerido
CREATE OR REPLACE FUNCTION fn_module_competencies_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_module_competencies_touch ON module_competencies;

CREATE TRIGGER trg_module_competencies_touch
    BEFORE UPDATE ON module_competencies
    FOR EACH ROW
    EXECUTE FUNCTION fn_module_competencies_touch();

COMMIT;
