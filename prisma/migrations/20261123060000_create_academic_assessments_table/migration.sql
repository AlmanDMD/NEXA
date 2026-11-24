-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: AVALIAÇÕES FORMATIVAS E PROVAS (DB-027)
-- Versão: 20261123060000_create_academic_assessments_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `academic_assessments` (EPIC-03: Diário de Classe: Notas
-- & Frequência) para cadastrar provas teóricas, microavaliações e projetos
-- aplicados por turma (`classes`), disciplina (`subjects`) e, opcionalmente,
-- módulo prático SENAI (`learning_modules`), com peso configurável (`weight`)
-- e nota máxima (`max_grade` padrão `10.00`), servindo de base direta para
-- `student_grades` (`DB-028`), `BE-027` e `FE-027`:
-- 1. Validação `chk_assessments_weight_positive` exigindo peso estritamente
--    maior que zero (`weight > 0.00 AND weight <= 9.99`, padrão `1.00`), além
--    de `chk_assessments_max_grade` (`0.00 < max_grade <= 10.00`, padrão `10.00`)
--    e `chk_assessments_title_not_blank` (`length(btrim(title)) >= 3`).
-- 2. Vinculação obrigatória (`NOT NULL`) à turma (`fk_assessments_class`) e à
--    disciplina (`fk_assessments_subject`), além de vínculo opcional ao módulo
--    (`fk_assessments_module`), todos com `ON DELETE RESTRICT ON UPDATE CASCADE`.
-- 3. Índices B-Tree para ordenação cronológica por `application_date`:
--    `idx_academic_assessments_class_subject_date (class_id, subject_id, application_date)`
--    e `idx_academic_assessments_application_date (application_date)`, além de
--    `idx_academic_assessments_module` e `idx_academic_assessments_type`.
-- 4. Trigger PL/pgSQL `trg_academic_assessments_validate_integrity` garantindo:
--    - `subject_id` pertence ao mesmo curso (`course_id`) da turma `class_id`;
--    - quando `module_id` for informado, o módulo pertence à disciplina `subject_id`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Garantir existência do enum nativo assessment_type_enum (criado em DB-005)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assessment_type_enum') THEN
        CREATE TYPE assessment_type_enum AS ENUM ('EXAM', 'MICRO_EVALUATION', 'PROJECT');
    END IF;
END
$$;

-- 3. Criar tabela de avaliações formativas e provas (`academic_assessments`)
CREATE TABLE IF NOT EXISTS academic_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    title VARCHAR(150) NOT NULL,
    assessment_type assessment_type_enum NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    application_date DATE NOT NULL,
    max_grade NUMERIC(4,2) NOT NULL DEFAULT 10.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Peso estritamente maior que zero (até 9.99 para composição ponderada)
    CONSTRAINT chk_assessments_weight_positive CHECK (weight > 0.00 AND weight <= 9.99),

    -- Regra de domínio: nota máxima estritamente positiva até 10.00 (padrão 10.00)
    CONSTRAINT chk_assessments_max_grade CHECK (max_grade > 0.00 AND max_grade <= 10.00),

    -- Higiene de domínio: título descritivo mínimo de 3 caracteres úteis
    CONSTRAINT chk_assessments_title_not_blank CHECK (length(btrim(title)) >= 3),

    -- Critério de Aceitação 2: Vinculação obrigatória a turma e disciplina (ON DELETE RESTRICT)
    CONSTRAINT fk_assessments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_assessments_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Vinculação opcional a módulo prático SENAI (ON DELETE RESTRICT protege histórico avaliado)
    CONSTRAINT fk_assessments_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 4. Critério de Aceitação 3: Índices B-Tree para ordenação rápida por application_date (BE-027 / FE-027)
CREATE INDEX IF NOT EXISTS idx_academic_assessments_class_subject_date
    ON academic_assessments USING BTREE (class_id, subject_id, application_date);

CREATE INDEX IF NOT EXISTS idx_academic_assessments_application_date
    ON academic_assessments USING BTREE (application_date);

-- Índices auxiliares para consolidação por módulo prático (BE-028) e filtro por tipo avaliativo
CREATE INDEX IF NOT EXISTS idx_academic_assessments_module
    ON academic_assessments USING BTREE (module_id);

CREATE INDEX IF NOT EXISTS idx_academic_assessments_type
    ON academic_assessments USING BTREE (assessment_type);

-- 5. Função e Trigger PL/pgSQL para coerência curricular (turma-disciplina e disciplina-módulo)
CREATE OR REPLACE FUNCTION fn_academic_assessments_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_class_course_id UUID;
    v_subject_course_id UUID;
    v_module_subject_id UUID;
BEGIN
    -- 5.1. Garantir que a disciplina pertença ao mesmo curso da turma
    IF TG_OP = 'INSERT'
       OR NEW.class_id IS DISTINCT FROM OLD.class_id
       OR NEW.subject_id IS DISTINCT FROM OLD.subject_id THEN
        SELECT c.course_id
          INTO v_class_course_id
          FROM classes c
         WHERE c.id = NEW.class_id;

        SELECT s.course_id
          INTO v_subject_course_id
          FROM subjects s
         WHERE s.id = NEW.subject_id;

        IF v_class_course_id IS NOT NULL
           AND v_subject_course_id IS NOT NULL
           AND v_class_course_id <> v_subject_course_id THEN
            RAISE EXCEPTION
                'Integridade curricular violada: a disciplina % pertence ao curso % e não ao curso % da turma %.',
                NEW.subject_id, v_subject_course_id, v_class_course_id, NEW.class_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_academic_assessments_subject_course';
        END IF;
    END IF;

    -- 5.2. Quando module_id for informado, garantir que o módulo pertença à disciplina informada
    IF NEW.module_id IS NOT NULL AND (
        TG_OP = 'INSERT'
        OR NEW.module_id IS DISTINCT FROM OLD.module_id
        OR NEW.subject_id IS DISTINCT FROM OLD.subject_id
    ) THEN
        SELECT lm.subject_id
          INTO v_module_subject_id
          FROM learning_modules lm
         WHERE lm.id = NEW.module_id;

        IF FOUND AND v_module_subject_id <> NEW.subject_id THEN
            RAISE EXCEPTION
                'Integridade modular violada: o módulo prático % pertence à disciplina % e não à disciplina %.',
                NEW.module_id, v_module_subject_id, NEW.subject_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_academic_assessments_module_subject';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_academic_assessments_validate_integrity ON academic_assessments;

CREATE TRIGGER trg_academic_assessments_validate_integrity
    BEFORE INSERT OR UPDATE ON academic_assessments
    FOR EACH ROW
    EXECUTE FUNCTION fn_academic_assessments_validate_integrity();

-- 6. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE academic_assessments IS
    'Avaliações teóricas, microavaliações e projetos formativos aplicados por turma, disciplina e módulo opcional (DB-027). Base para student_grades (DB-028), BE-027 e FE-027.';

COMMENT ON CONSTRAINT chk_assessments_weight_positive ON academic_assessments IS
    'Regra DB-027: o peso (weight) da avaliação deve ser estritamente maior que 0.00 (até 9.99) para composição de média ponderada.';

COMMENT ON CONSTRAINT chk_assessments_max_grade ON academic_assessments IS
    'Regra DB-027: max_grade deve ser estritamente maior que 0.00 e menor ou igual a 10.00 (padrão 10.00).';

COMMIT;
