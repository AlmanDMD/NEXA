-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: FORMULÁRIOS DE AUTOAVALIAÇÃO (DB-031)
-- Versão: 20261123090000_create_self_assessment_forms_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `self_assessment_forms` (EPIC-07: Autoavaliação & Motor
-- de Diagnóstico Explicável — Sprint S4 / Lote 4) para estruturar os ciclos e
-- questionários de autoavaliação de competências práticas por módulo SENAI
-- (`learning_modules`) e turma (`classes`), servindo de base direta para
-- `student_self_assessments` (`DB-032`), `DB-040`, `BE-035` e `FE-041`:
-- 1. Vinculação obrigatória a módulo prático (`fk_self_assessment_forms_module`)
--    e turma (`fk_self_assessment_forms_class`), além do docente/gestor criador
--    (`fk_self_assessment_forms_creator`), todos com `ON DELETE RESTRICT`.
-- 2. Validação temporal `chk_self_assessment_forms_dates` exigindo estritamente
--    `opens_at < closes_at`, além de `chk_self_assessment_forms_title_not_blank`.
-- 3. Índice composto `idx_self_assessment_forms_class_active (class_id, is_active)`
--    (e `idx_self_assessment_forms_window`) para exibir instantaneamente os
--    formulários abertos no portal do estudante (`FE-041`).
-- 4. Trigger PL/pgSQL `trg_self_assessment_forms_validate_integrity` garantindo:
--    - o módulo pertence ao mesmo curso (`course_id`) da turma informada;
--    - `created_by` possui perfil docente/gestão (`role <> 'STUDENT'`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de formulários de autoavaliação (`self_assessment_forms`)
CREATE TABLE IF NOT EXISTS self_assessment_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL,
    class_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    instructions TEXT,
    opens_at TIMESTAMPTZ NOT NULL,
    closes_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 2: Janela temporal válida (abertura estritamente anterior ao fechamento)
    CONSTRAINT chk_self_assessment_forms_dates CHECK (opens_at < closes_at),

    -- Higiene de domínio: título descritivo mínimo de 3 caracteres úteis
    CONSTRAINT chk_self_assessment_forms_title_not_blank CHECK (length(btrim(title)) >= 3),

    -- Critério de Aceitação 1: Vínculo obrigatório com módulo prático e turma (ON DELETE RESTRICT)
    CONSTRAINT fk_self_assessment_forms_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_self_assessment_forms_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Rastreabilidade do docente/coordenador criador do ciclo de autoavaliação
    CONSTRAINT fk_self_assessment_forms_creator
        FOREIGN KEY (created_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice em (class_id, is_active) para exibir formulários abertos no portal do aluno
CREATE INDEX IF NOT EXISTS idx_self_assessment_forms_class_active
    ON self_assessment_forms USING BTREE (class_id, is_active);

-- Índices auxiliares para janela ativa (FE-041 / BE-035), listagem por módulo e auditoria docente
CREATE INDEX IF NOT EXISTS idx_self_assessment_forms_window
    ON self_assessment_forms USING BTREE (class_id, is_active, opens_at, closes_at);

CREATE INDEX IF NOT EXISTS idx_self_assessment_forms_module
    ON self_assessment_forms USING BTREE (module_id);

CREATE INDEX IF NOT EXISTS idx_self_assessment_forms_creator
    ON self_assessment_forms USING BTREE (created_by);

-- 4. Função e Trigger PL/pgSQL para coerência curricular (módulo-curso-turma) e perfil docente do criador
CREATE OR REPLACE FUNCTION fn_self_assessment_forms_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_class_course_id UUID;
    v_module_course_id UUID;
    v_creator_role user_role_enum;
BEGIN
    -- 4.1. Garantir que o módulo prático pertença ao mesmo curso técnico da turma
    IF TG_OP = 'INSERT'
       OR NEW.class_id IS DISTINCT FROM OLD.class_id
       OR NEW.module_id IS DISTINCT FROM OLD.module_id THEN
        SELECT c.course_id
          INTO v_class_course_id
          FROM classes c
         WHERE c.id = NEW.class_id;

        SELECT s.course_id
          INTO v_module_course_id
          FROM learning_modules lm
          JOIN subjects s ON s.id = lm.subject_id
         WHERE lm.id = NEW.module_id;

        IF v_class_course_id IS NOT NULL
           AND v_module_course_id IS NOT NULL
           AND v_class_course_id <> v_module_course_id THEN
            RAISE EXCEPTION
                'Integridade curricular violada: o módulo prático % pertence ao curso % e não ao curso % da turma %.',
                NEW.module_id, v_module_course_id, v_class_course_id, NEW.class_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_self_assessment_forms_module_course';
        END IF;
    END IF;

    -- 4.2. Impedir que estudante (role = 'STUDENT') crie formulários de autoavaliação
    IF TG_OP = 'INSERT' OR NEW.created_by IS DISTINCT FROM OLD.created_by THEN
        SELECT u.role
          INTO v_creator_role
          FROM users u
         WHERE u.id = NEW.created_by;

        IF FOUND AND v_creator_role = 'STUDENT' THEN
            RAISE EXCEPTION
                'Integridade de perfil violada: o usuário % possui role "STUDENT" e não pode criar formulários em self_assessment_forms.',
                NEW.created_by
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_self_assessment_forms_creator_role';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_self_assessment_forms_validate_integrity ON self_assessment_forms;

CREATE TRIGGER trg_self_assessment_forms_validate_integrity
    BEFORE INSERT OR UPDATE ON self_assessment_forms
    FOR EACH ROW
    EXECUTE FUNCTION fn_self_assessment_forms_validate_integrity();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE self_assessment_forms IS
    'Ciclos e questionários de autoavaliação de competências práticas por módulo SENAI e turma (DB-031). Base para student_self_assessments (DB-032), BE-035 e FE-041.';

COMMENT ON CONSTRAINT chk_self_assessment_forms_dates ON self_assessment_forms IS
    'Regra DB-031: garante que a data/hora de abertura (opens_at) seja estritamente anterior ao encerramento (closes_at).';

COMMIT;
