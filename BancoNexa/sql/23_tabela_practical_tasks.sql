-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TAREFAS E ATIVIDADES PRÁTICAS (DB-023)
-- Versão: 20261123020000_create_practical_tasks_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `practical_tasks` (EPIC-04: Atividades Práticas de Oficina
-- & Competências) para modelar as peças, exercícios de bancada e atividades de
-- usinagem associadas aos módulos práticos SENAI (`learning_modules`) e turmas
-- (`classes`), servindo de base direta para rubricas (`task_criteria` — DB-024),
-- entregas (`task_submissions` — DB-025), endpoint `BE-024` e painel `FE-024`:
-- 1. Chaves estrangeiras íntegras com `ON DELETE RESTRICT ON UPDATE CASCADE` para
--    `learning_modules` e `classes`.
-- 2. Validação `chk_practical_tasks_max_score` exigindo `max_score` entre `1.00`
--    e `10.00` (padrão `10.00`), `title` não vazio e `blueprint_url` válida (`http/https`).
-- 3. Índice composto `idx_practical_tasks_class_due_date (class_id, due_date)`
--    para consulta rápida de pendências de oficina, complementado por
--    `idx_practical_tasks_module` e `idx_practical_tasks_class_mandatory_due`.
-- 4. Trigger PL/pgSQL `trg_practical_tasks_validate_and_touch` garantindo que o
--    módulo prático pertença a uma disciplina do mesmo curso da turma (`course_id`)
--    e atualizando `updated_at` automaticamente em operações `UPDATE`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de tarefas e atividades práticas de oficina (`practical_tasks`)
CREATE TABLE IF NOT EXISTS practical_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL,
    class_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    blueprint_url VARCHAR(500),
    due_date TIMESTAMPTZ NOT NULL,
    max_score NUMERIC(4,2) NOT NULL DEFAULT 10.00,
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 2: Pontuação máxima validada entre 1.00 e 10.00
    CONSTRAINT chk_practical_tasks_max_score CHECK (max_score >= 1.00 AND max_score <= 10.00),

    -- Higiene de domínio: título não vazio e URL de desenho técnico válida (quando informada)
    CONSTRAINT chk_practical_tasks_title_not_blank CHECK (length(btrim(title)) > 0),
    CONSTRAINT chk_practical_tasks_blueprint_url CHECK (
        blueprint_url IS NULL OR blueprint_url ~* '^https?://'
    ),

    -- Critério de Aceitação 1: Tarefa vinculada a módulo prático (learning_modules) e turma (classes)
    CONSTRAINT fk_practical_tasks_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_practical_tasks_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice composto por (class_id, due_date) para consulta rápida de pendências
CREATE INDEX IF NOT EXISTS idx_practical_tasks_class_due_date
    ON practical_tasks USING BTREE (class_id, due_date);

-- Índices auxiliares para listagem por módulo (BE-024 / FE-024) e filtro de tarefas obrigatórias pendentes (BE-026)
CREATE INDEX IF NOT EXISTS idx_practical_tasks_module
    ON practical_tasks USING BTREE (module_id);

CREATE INDEX IF NOT EXISTS idx_practical_tasks_class_mandatory_due
    ON practical_tasks USING BTREE (class_id, is_mandatory, due_date);

-- 4. Função e Trigger PL/pgSQL para coerência curricular (curso do módulo = curso da turma) e updated_at
CREATE OR REPLACE FUNCTION fn_practical_tasks_validate_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_module_course_id UUID;
    v_class_course_id UUID;
BEGIN
    IF TG_OP = 'INSERT'
       OR NEW.module_id IS DISTINCT FROM OLD.module_id
       OR NEW.class_id IS DISTINCT FROM OLD.class_id THEN
        SELECT s.course_id INTO v_module_course_id
        FROM learning_modules lm
        JOIN subjects s ON s.id = lm.subject_id
        WHERE lm.id = NEW.module_id;

        SELECT c.course_id INTO v_class_course_id
        FROM classes c
        WHERE c.id = NEW.class_id;

        IF v_module_course_id IS NOT NULL
           AND v_class_course_id IS NOT NULL
           AND v_module_course_id <> v_class_course_id THEN
            RAISE EXCEPTION
                'Integridade curricular violada: o módulo prático % pertence ao curso % e não ao curso % da turma %.',
                NEW.module_id, v_module_course_id, v_class_course_id, NEW.class_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_practical_tasks_module_course';
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_practical_tasks_validate_and_touch ON practical_tasks;

CREATE TRIGGER trg_practical_tasks_validate_and_touch
    BEFORE INSERT OR UPDATE ON practical_tasks
    FOR EACH ROW
    EXECUTE FUNCTION fn_practical_tasks_validate_and_touch();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE practical_tasks IS
    'Tarefas e peças práticas de bancada/oficina associadas aos módulos técnicos SENAI e turmas (DB-023). Base para task_criteria (DB-024) e task_submissions (DB-025).';

COMMENT ON CONSTRAINT chk_practical_tasks_max_score ON practical_tasks IS
    'Regra DB-023: max_score deve estar entre 1.00 e 10.00 (padrão 10.00).';

COMMIT;
