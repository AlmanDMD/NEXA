-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: CRITÉRIOS E RUBRICAS PRÁTICAS (DB-024)
-- Versão: 20261123030000_create_task_criteria_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `task_criteria` (EPIC-04: Atividades Práticas de Oficina
-- & Competências) para decompor cada tarefa prática (`practical_tasks`) em
-- critérios técnicos objetivos (tolerância dimensional, rugosidade superficial,
-- acabamento, uso de EPI) vinculados às competências oficiais SENAI (`competencies`),
-- servindo de base para `submission_evaluations` (DB-026), `BE-024`/`BE-025` e
-- o modal de rubricas `FE-026`:
-- 1. Referência obrigatória a `practical_tasks` (`fk_task_criteria_task` com
--    `ON DELETE CASCADE ON UPDATE CASCADE`) e a uma competência técnica oficial
--    em `competencies` (`fk_task_criteria_competency` com `ON DELETE RESTRICT`).
-- 2. Suporte a ponderação automática via `weight NUMERIC(3,2) DEFAULT 1.00`
--    validado em `(0.00, 9.99]` e escala de domínio `min_acceptable_level` de `1` a `5`.
-- 3. Unicidade `uq_task_criteria_name (task_id, criterion_name)` impedindo
--    rubricas duplicadas na mesma peça prática.
-- 4. Exclusão em cascata segura: ao excluir uma tarefa sem entregas avaliadas,
--    todos os critérios em `task_criteria` são removidos automaticamente; quando
--    houver entregas (`task_submissions` — DB-025) ou avaliações (`submission_evaluations`
--    — DB-026), as FKs `ON DELETE RESTRICT` protegem o histórico avaliado.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de critérios de avaliação prática / rubricas (`task_criteria`)
CREATE TABLE IF NOT EXISTS task_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    criterion_name VARCHAR(180) NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    min_acceptable_level INTEGER NOT NULL DEFAULT 3,

    -- Unicidade do nome do critério dentro da mesma atividade prática
    CONSTRAINT uq_task_criteria_name UNIQUE (task_id, criterion_name),

    -- Critério de Aceitação 2: Pesos positivos para soma/ponderação automática
    CONSTRAINT chk_task_criteria_weight CHECK (weight > 0.00 AND weight <= 9.99),

    -- Escala SENAI de proficiência mínima aceitável (1 a 5)
    CONSTRAINT chk_task_criteria_level CHECK (min_acceptable_level BETWEEN 1 AND 5),

    -- Higiene de domínio: nome da rubrica não pode ser vazio/branco
    CONSTRAINT chk_task_criteria_name_not_blank CHECK (length(btrim(criterion_name)) > 0),

    -- Critérios de Aceitação 1 e 3: FK para practical_tasks com ON DELETE CASCADE
    -- (bloqueada automaticamente por ON DELETE RESTRICT em task_submissions / submission_evaluations quando já houver entregas avaliadas)
    CONSTRAINT fk_task_criteria_task
        FOREIGN KEY (task_id) REFERENCES practical_tasks (id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- Critério de Aceitação 1: FK para competência técnica oficial (ON DELETE RESTRICT)
    CONSTRAINT fk_task_criteria_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Índices B-Tree para carregamento de rubricas da tarefa (BE-024 / FE-026) e rastreio por competência
CREATE INDEX IF NOT EXISTS idx_task_criteria_task
    ON task_criteria USING BTREE (task_id);

CREATE INDEX IF NOT EXISTS idx_task_criteria_competency
    ON task_criteria USING BTREE (competency_id);

-- 4. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE task_criteria IS
    'Critérios técnicos objetivos e rubricas de avaliação prática vinculadas a practical_tasks e competencies (DB-024). Base para submission_evaluations (DB-026) e FE-026.';

COMMENT ON CONSTRAINT chk_task_criteria_weight ON task_criteria IS
    'Regra DB-024: weight > 0.00 e <= 9.99 para cálculo de média ponderada automática das rubricas.';

COMMENT ON CONSTRAINT chk_task_criteria_level ON task_criteria IS
    'Regra DB-024: min_acceptable_level na escala inteira de 1 a 5 (padrão 3).';

COMMIT;
