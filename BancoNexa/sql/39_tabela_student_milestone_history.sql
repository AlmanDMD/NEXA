-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: LINHA DO TEMPO ACADÊMICA (DB-039)
-- Versão: 20261126060000_create_student_milestone_history_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `student_milestone_history` (EPIC-06: Portal de Autonomia
-- do Aluno & Pendências — Sprint S4 / Lote 4) para registrar a linha do tempo
-- cronológica de marcos positivos e evolução acadêmica do estudante ao longo
-- dos módulos práticos SENAI, desbloqueando `DB-040`, `BE-034` e `FE-039`:
-- 1. Eventos cronológicos ordenados por `achieved_at` com índice composto
--    `idx_milestone_history_student_achieved` em `(student_id, achieved_at DESC)`.
-- 2. Vinculação íntegra com `users(id)`, `enrollments(id)` e `learning_modules(id)`
--    (opcional) via `ON DELETE RESTRICT ON UPDATE CASCADE` + trigger de coerência.
-- 3. Enum nativo `milestone_type_enum` (`MODULE_COMPLETED`, `SKILL_LEVEL_UP`,
--    `PERFECT_ATTENDANCE`, `RECOVERY_ACHIEVED` — DB-005) e `metadata JSONB`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enum nativo milestone_type_enum (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE milestone_type_enum AS ENUM (
        'MODULE_COMPLETED',
        'SKILL_LEVEL_UP',
        'PERFECT_ATTENDANCE',
        'RECOVERY_ACHIEVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de histórico e linha do tempo acadêmica (`student_milestone_history`)
CREATE TABLE IF NOT EXISTS student_milestone_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    module_id UUID,
    milestone_type milestone_type_enum NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    metadata JSONB,
    achieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Validações de conteúdo textual e formato JSONB opcional
    CONSTRAINT chk_milestone_history_title_not_empty CHECK (
        CHAR_LENGTH(BTRIM(title)) >= 3
    ),
    CONSTRAINT chk_milestone_history_metadata_object CHECK (
        metadata IS NULL OR jsonb_typeof(metadata) = 'object'
    ),

    -- Critério de Aceitação 2: Vinculação íntegra com estudante, matrícula e módulo prático
    CONSTRAINT fk_milestone_history_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_milestone_history_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_milestone_history_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice composto (student_id, achieved_at DESC) e índices complementares
CREATE INDEX IF NOT EXISTS idx_milestone_history_student_achieved
    ON student_milestone_history USING BTREE (student_id, achieved_at DESC);

CREATE INDEX IF NOT EXISTS idx_milestone_history_enrollment_achieved
    ON student_milestone_history USING BTREE (enrollment_id, achieved_at DESC);

CREATE INDEX IF NOT EXISTS idx_milestone_history_module
    ON student_milestone_history USING BTREE (module_id)
    WHERE module_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_milestone_history_type
    ON student_milestone_history USING BTREE (milestone_type);

-- 4. Função e Trigger PL/pgSQL para validar perfil STUDENT e coerência com enrollment_id
CREATE OR REPLACE FUNCTION fn_student_milestone_history_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_enr_student_id UUID;
BEGIN
    NEW.title := BTRIM(NEW.title);

    IF NEW.description IS NOT NULL THEN
        NEW.description := BTRIM(NEW.description);
    END IF;

    SELECT u.role
      INTO v_student_role
      FROM users u
     WHERE u.id = NEW.student_id;

    IF FOUND AND v_student_role <> 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "%" e apenas estudantes ("STUDENT") possuem linha do tempo acadêmica.',
            NEW.student_id, v_student_role
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_milestone_history_student_role';
    END IF;

    SELECT e.student_id
      INTO v_enr_student_id
      FROM enrollments e
     WHERE e.id = NEW.enrollment_id;

    IF FOUND AND v_enr_student_id <> NEW.student_id THEN
        RAISE EXCEPTION
            'Inconsistência de matrícula: enrollment % pertence ao estudante % e não ao estudante %.',
            NEW.enrollment_id, v_enr_student_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_milestone_history_enrollment_owner';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_student_milestone_history_validate_integrity ON student_milestone_history;

CREATE TRIGGER trg_student_milestone_history_validate_integrity
    BEFORE INSERT OR UPDATE ON student_milestone_history
    FOR EACH ROW
    EXECUTE FUNCTION fn_student_milestone_history_validate_integrity();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE student_milestone_history IS
    'Linha do tempo cronológica de marcos positivos de evolução do estudante ao longo dos módulos SENAI (DB-039). Alimenta BE-034 e FE-039.';

COMMIT;
