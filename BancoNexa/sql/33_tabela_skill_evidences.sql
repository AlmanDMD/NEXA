-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: EVIDÊNCIAS PRÁTICAS (DB-033)
-- Versão: 20261126000000_create_skill_evidences_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `skill_evidences` (EPIC-07: Autoavaliação & Motor de
-- Diagnóstico Explicável — Sprint S4 / Lote 4) para consolidar as evidências
-- acadêmicas reais (avaliações de bancada/rubricas ou avaliações formativas)
-- verificadas pelo docente que comprovam o nível técnico do estudante em cada
-- competência, desbloqueando `DB-035`, `DB-038` (`vw_self_eval_discrepancy`),
-- `DB-040`, `BE-025`, `BE-037` e `BE-038`:
-- 1. Vínculo obrigatório à evidência de origem (`chk_skill_evidences_source`):
--    pelo menos `source_submission_id` (`task_submissions`) ou
--    `source_assessment_id` (`academic_assessments`) deve ser informado.
-- 2. Escala padronizada `verified_level NUMERIC(3,2)` entre `1.00` e `5.00`
--    (`chk_skill_evidences_level`), idêntica à escala 1..5 da autoavaliação.
-- 3. Índice composto `idx_skill_evidences_student_competency` em
--    `(student_id, competency_id)` para cruzamentos rápidos no diagnóstico.
-- 4. Trigger PL/pgSQL `trg_skill_evidences_validate_integrity` validando perfil
--    `STUDENT` em `student_id`, perfil `TEACHER` em `verified_by`, bloqueio de
--    autoverificação e coerência da submissão/avaliação com o estudante.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de evidências práticas verificadas (`skill_evidences`)
CREATE TABLE IF NOT EXISTS skill_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    source_submission_id UUID,
    source_assessment_id UUID,
    verified_level NUMERIC(3,2) NOT NULL,
    verified_by UUID NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 2: Nível verificado pelo docente na escala 1.00..5.00
    CONSTRAINT chk_skill_evidences_level CHECK (verified_level >= 1.00 AND verified_level <= 5.00),

    -- Critério de Aceitação 1: Origem obrigatória (submissão prática ou avaliação formativa)
    CONSTRAINT chk_skill_evidences_source CHECK (
        source_submission_id IS NOT NULL OR source_assessment_id IS NOT NULL
    ),

    -- Integridade referencial estrita (ON DELETE RESTRICT protege histórico de evidências)
    CONSTRAINT fk_skill_evidences_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_skill_evidences_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_skill_evidences_submission
        FOREIGN KEY (source_submission_id) REFERENCES task_submissions (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_skill_evidences_assessment
        FOREIGN KEY (source_assessment_id) REFERENCES academic_assessments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_skill_evidences_verifier
        FOREIGN KEY (verified_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice composto (student_id, competency_id) e índices de suporte
CREATE INDEX IF NOT EXISTS idx_skill_evidences_student_competency
    ON skill_evidences USING BTREE (student_id, competency_id);

CREATE INDEX IF NOT EXISTS idx_skill_evidences_student_recorded
    ON skill_evidences USING BTREE (student_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_skill_evidences_source_submission
    ON skill_evidences USING BTREE (source_submission_id)
    WHERE source_submission_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_skill_evidences_source_assessment
    ON skill_evidences USING BTREE (source_assessment_id)
    WHERE source_assessment_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_skill_evidences_verified_by
    ON skill_evidences USING BTREE (verified_by);

-- 4. Função e Trigger PL/pgSQL para validar perfis (STUDENT/TEACHER) e coerência da origem da evidência
CREATE OR REPLACE FUNCTION fn_skill_evidences_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_verifier_role user_role_enum;
    v_submission_student_id UUID;
    v_assessment_class_id UUID;
    v_enrolled_in_class BOOLEAN;
BEGIN
    -- 4.1. Impedir autoverificação (garante que autoavaliação jamais seja gravada como evidência docente)
    IF NEW.verified_by = NEW.student_id THEN
        RAISE EXCEPTION
            'Autoverificação proibida: o estudante % não pode registrar evidência docente para si mesmo.',
            NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_skill_evidences_no_self_verification';
    END IF;

    -- 4.2. Garantir que student_id possui role = 'STUDENT'
    SELECT u.role
      INTO v_student_role
      FROM users u
     WHERE u.id = NEW.student_id;

    IF FOUND AND v_student_role <> 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "%" e apenas usuários "STUDENT" podem receber evidências em skill_evidences.',
            NEW.student_id, v_student_role
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_skill_evidences_student_role';
    END IF;

    -- 4.3. Garantir que verified_by possui role = 'TEACHER'
    SELECT u.role
      INTO v_verifier_role
      FROM users u
     WHERE u.id = NEW.verified_by;

    IF FOUND AND v_verifier_role <> 'TEACHER' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o verificador % possui role "%" e apenas docentes ("TEACHER") podem certificar evidências práticas.',
            NEW.verified_by, v_verifier_role
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_skill_evidences_verifier_role';
    END IF;

    -- 4.4. Validar coerência da submissão prática de origem com o estudante
    IF NEW.source_submission_id IS NOT NULL THEN
        SELECT ts.student_id
          INTO v_submission_student_id
          FROM task_submissions ts
         WHERE ts.id = NEW.source_submission_id;

        IF FOUND AND v_submission_student_id <> NEW.student_id THEN
            RAISE EXCEPTION
                'Origem incompatível: a submissão % pertence ao estudante % e não pode comprovar competência do estudante %.',
                NEW.source_submission_id, v_submission_student_id, NEW.student_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_skill_evidences_submission_owner';
        END IF;
    END IF;

    -- 4.5. Validar vínculo do estudante na turma da avaliação formativa de origem
    IF NEW.source_assessment_id IS NOT NULL THEN
        SELECT aa.class_id
          INTO v_assessment_class_id
          FROM academic_assessments aa
         WHERE aa.id = NEW.source_assessment_id;

        IF FOUND THEN
            SELECT EXISTS (
                SELECT 1
                  FROM enrollments e
                 WHERE e.student_id = NEW.student_id
                   AND e.class_id = v_assessment_class_id
            ) INTO v_enrolled_in_class;

            IF NOT v_enrolled_in_class THEN
                RAISE EXCEPTION
                    'Origem incompatível: o estudante % não possui matrícula na turma % da avaliação %.',
                    NEW.student_id, v_assessment_class_id, NEW.source_assessment_id
                    USING ERRCODE = '23514',
                          CONSTRAINT = 'chk_skill_evidences_assessment_enrollment';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_skill_evidences_validate_integrity ON skill_evidences;

CREATE TRIGGER trg_skill_evidences_validate_integrity
    BEFORE INSERT OR UPDATE ON skill_evidences
    FOR EACH ROW
    EXECUTE FUNCTION fn_skill_evidences_validate_integrity();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE skill_evidences IS
    'Evidências práticas e formativas verificadas por docentes por competência na escala 1.00..5.00 (DB-033). Contrasta com student_self_assessments em vw_self_eval_discrepancy (DB-038).';

COMMENT ON CONSTRAINT chk_skill_evidences_source ON skill_evidences IS
    'Regra DB-033: toda evidência deve referenciar ao menos uma submissão prática (source_submission_id) ou uma avaliação formativa (source_assessment_id).';

COMMENT ON CONSTRAINT chk_skill_evidences_level ON skill_evidences IS
    'Regra DB-033: nível verificado pelo docente parametrizado na escala 1.00 a 5.00, compatível com a autoavaliação discente.';

COMMIT;
