-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: DIAGNÓSTICOS EXPLICÁVEIS (DB-035)
-- Versão: 20261126020000_create_explainable_diagnostics_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `explainable_diagnostics` (EPIC-07: Autoavaliação &
-- Motor de Diagnóstico Explicável — Sprint S4 / Lote 4) para persistir
-- relatórios pedagógicos comparativos entre percepção discente
-- (`self_perceived_level`) e evidência docente (`teacher_verified_level`) com
-- transparência total de critérios e limitações, desbloqueando `DB-038`,
-- `DB-040`, `BE-037`, `BE-038` e `FE-042`:
-- 1. Campos obrigatórios `explanation_text`, `limitations_note` e
--    `recommended_action` não vazios garantindo inteligência explicável.
-- 2. Cálculo e consistência automática de `discrepancy_gap =
--    ROUND(self_perceived_level - teacher_verified_level, 2)` via trigger.
-- 3. Índice composto `idx_explainable_diagnostics_class_type` em
--    `(class_id, diagnostic_type)` para filtragem no dashboard de turma.
-- 4. Enum nativo `diagnostic_type_enum` (`ALIGNED`, `OVERCONFIDENCE_RISK`,
--    `UNDERCONFIDENCE_SUPPORT`, `INSUFFICIENT_EVIDENCE` — DB-005).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enum nativo diagnostic_type_enum (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE diagnostic_type_enum AS ENUM (
        'ALIGNED',
        'OVERCONFIDENCE_RISK',
        'UNDERCONFIDENCE_SUPPORT',
        'INSUFFICIENT_EVIDENCE'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de diagnósticos explicáveis (`explainable_diagnostics`)
CREATE TABLE IF NOT EXISTS explainable_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    class_id UUID NOT NULL,
    module_id UUID NOT NULL,
    competency_id UUID,
    self_perceived_level NUMERIC(3,2) NOT NULL,
    teacher_verified_level NUMERIC(3,2) NOT NULL,
    discrepancy_gap NUMERIC(3,2) NOT NULL,
    diagnostic_type diagnostic_type_enum NOT NULL,
    explanation_text TEXT NOT NULL,
    limitations_note TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Validação das escalas comparativas (1.00..5.00) e amplitude do gap (-4.00..4.00)
    CONSTRAINT chk_diagnostics_self_level CHECK (self_perceived_level BETWEEN 1.00 AND 5.00),
    CONSTRAINT chk_diagnostics_teacher_level CHECK (teacher_verified_level BETWEEN 1.00 AND 5.00),
    CONSTRAINT chk_diagnostics_gap_range CHECK (discrepancy_gap BETWEEN -4.00 AND 4.00),

    -- Critério de Aceitação 1: Explicação, limitações e ação recomendada obrigatórias
    CONSTRAINT chk_diagnostics_explanation_not_empty CHECK (CHAR_LENGTH(BTRIM(explanation_text)) >= 10),
    CONSTRAINT chk_diagnostics_limitations_not_empty CHECK (CHAR_LENGTH(BTRIM(limitations_note)) >= 10),
    CONSTRAINT chk_diagnostics_action_not_empty CHECK (CHAR_LENGTH(BTRIM(recommended_action)) >= 5),

    -- Integridade referencial estrita (ON DELETE RESTRICT protege histórico diagnóstico)
    CONSTRAINT fk_diagnostics_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_diagnostics_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_diagnostics_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_diagnostics_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice em (class_id, diagnostic_type) e índices complementares
CREATE INDEX IF NOT EXISTS idx_explainable_diagnostics_class_type
    ON explainable_diagnostics USING BTREE (class_id, diagnostic_type);

CREATE INDEX IF NOT EXISTS idx_explainable_diagnostics_student_module
    ON explainable_diagnostics USING BTREE (student_id, module_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_explainable_diagnostics_competency
    ON explainable_diagnostics USING BTREE (competency_id)
    WHERE competency_id IS NOT NULL;

-- 4. Função e Trigger PL/pgSQL para calcular discrepancy_gap (Critério 2) e validar integridade
CREATE OR REPLACE FUNCTION fn_explainable_diagnostics_compute_and_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_expected_gap NUMERIC(3,2);
BEGIN
    NEW.explanation_text := BTRIM(NEW.explanation_text);
    NEW.limitations_note := BTRIM(NEW.limitations_note);
    NEW.recommended_action := BTRIM(NEW.recommended_action);

    -- 4.1. Garantir que student_id possui role = 'STUDENT'
    SELECT u.role
      INTO v_student_role
      FROM users u
     WHERE u.id = NEW.student_id;

    IF FOUND AND v_student_role <> 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "%" e apenas estudantes ("STUDENT") podem receber diagnósticos.',
            NEW.student_id, v_student_role
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_diagnostics_student_role';
    END IF;

    -- 4.2. Critério 2: Calcular automaticamente discrepancy_gap = self_perceived_level - teacher_verified_level
    v_expected_gap := ROUND(NEW.self_perceived_level - NEW.teacher_verified_level, 2);
    NEW.discrepancy_gap := v_expected_gap;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_explainable_diagnostics_compute_and_validate ON explainable_diagnostics;

CREATE TRIGGER trg_explainable_diagnostics_compute_and_validate
    BEFORE INSERT OR UPDATE ON explainable_diagnostics
    FOR EACH ROW
    EXECUTE FUNCTION fn_explainable_diagnostics_compute_and_validate();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE explainable_diagnostics IS
    'Diagnósticos pedagógicos explicáveis comparando autoavaliação discente e evidência docente, com registro explícito de critérios, limitações e ação recomendada (DB-035).';

COMMENT ON CONSTRAINT chk_diagnostics_limitations_not_empty ON explainable_diagnostics IS
    'Regra DB-035: obriga explicitar limitações da análise (ex.: quantidade de evidências e caráter não definitivo da autoavaliação).';

COMMIT;
