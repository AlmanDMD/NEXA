-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: NOTAS E MENÇÕES FINAIS (DB-028)
-- Versão: 20261123070000_create_student_grades_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `student_grades` (EPIC-03: Diário de Classe: Notas &
-- Frequência) para armazenar as notas individuais e notas de recuperação
-- obtidas por cada estudante nas avaliações formativas e provas
-- (`academic_assessments`), com precisão de duas casas decimais (`NUMERIC(4,2)`)
-- e rastreabilidade completa de lançamentos e alterações em `audit_logs`
-- (`DB-009` / `BE-048`), desbloqueando `DB-029`, `DB-030`, `DB-033`, `DB-034`,
-- `DB-036`, `DB-047`, `BE-027`, `BE-028`, `FE-027`, `FE-028` e `FE-037`:
-- 1. Constraint UNIQUE composta `uq_student_grades_assessment_student (assessment_id, student_id)`
--    (e `uq_student_grades_assessment_enrollment (assessment_id, enrollment_id)`).
-- 2. CHECK constraints `chk_student_grades_value` e `chk_student_grades_recovery`
--    garantindo `grade_value` e `recovery_grade` (quando informada) entre `0.00` e `10.00`.
-- 3. Vínculo obrigatório com `enrollment_id` válido (`fk_student_grades_enrollment`
--    com `ON DELETE RESTRICT`) + trigger BEFORE validando coerência matrícula/aluno/turma,
--    matrícula `ACTIVE` no lançamento, perfil docente de `recorded_by` (bloqueio de
--    `STUDENT` e auto-lançamento) e teto `<= academic_assessments.max_grade`.
-- 4. Trigger AFTER `trg_student_grades_audit_update` disparando log automático
--    em `audit_logs` (`DB-009`) para qualquer alteração posterior em nota já publicada.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de notas e menções finais (`student_grades`)
CREATE TABLE IF NOT EXISTS student_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    recorded_by UUID NOT NULL,
    grade_value NUMERIC(4,2) NOT NULL,
    recovery_grade NUMERIC(4,2),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Unicidade por avaliação formativa e estudante/matrícula
    CONSTRAINT uq_student_grades_assessment_student UNIQUE (assessment_id, student_id),
    CONSTRAINT uq_student_grades_assessment_enrollment UNIQUE (assessment_id, enrollment_id),

    -- Critério de Aceitação 2: Precisão numérica e intervalo obrigatório entre 0.00 e 10.00
    CONSTRAINT chk_student_grades_value CHECK (grade_value >= 0.00 AND grade_value <= 10.00),
    CONSTRAINT chk_student_grades_recovery CHECK (
        recovery_grade IS NULL OR (recovery_grade >= 0.00 AND recovery_grade <= 10.00)
    ),

    -- Integridade referencial estrita (ON DELETE RESTRICT protege histórico acadêmico)
    CONSTRAINT fk_student_grades_assessment
        FOREIGN KEY (assessment_id) REFERENCES academic_assessments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Critério de Aceitação 3: Vínculo obrigatório com enrollment_id válido
    CONSTRAINT fk_student_grades_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_student_grades_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_student_grades_recorded_by
        FOREIGN KEY (recorded_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Índices B-Tree para lançamento de notas (BE-027), fechamento de médias (BE-028) e boletim do aluno (FE-037)
CREATE INDEX IF NOT EXISTS idx_student_grades_assessment
    ON student_grades USING BTREE (assessment_id);

CREATE INDEX IF NOT EXISTS idx_student_grades_student
    ON student_grades USING BTREE (student_id);

CREATE INDEX IF NOT EXISTS idx_student_grades_enrollment
    ON student_grades USING BTREE (enrollment_id);

CREATE INDEX IF NOT EXISTS idx_student_grades_recorded_by
    ON student_grades USING BTREE (recorded_by, updated_at);

-- 4. Função e Trigger PL/pgSQL BEFORE para validar matrícula ativa/turma, perfil docente e teto max_grade
CREATE OR REPLACE FUNCTION fn_student_grades_validate_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_assessment_class_id UUID;
    v_assessment_max_grade NUMERIC(4,2);
    v_enrollment_student_id UUID;
    v_enrollment_class_id UUID;
    v_enrollment_status enrollment_status_enum;
    v_recorder_role user_role_enum;
BEGIN
    -- 4.1. Carregar turma e nota máxima da avaliação formativa
    SELECT aa.class_id, aa.max_grade
      INTO v_assessment_class_id, v_assessment_max_grade
      FROM academic_assessments aa
     WHERE aa.id = NEW.assessment_id;

    -- 4.2. Carregar matrícula do estudante (Critério de Aceitação 3)
    SELECT e.student_id, e.class_id, e.status
      INTO v_enrollment_student_id, v_enrollment_class_id, v_enrollment_status
      FROM enrollments e
     WHERE e.id = NEW.enrollment_id;

    IF v_enrollment_student_id IS NOT NULL AND v_enrollment_student_id <> NEW.student_id THEN
        RAISE EXCEPTION
            'Integridade de matrícula violada: a matrícula % pertence ao estudante % e não ao estudante %.',
            NEW.enrollment_id, v_enrollment_student_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_enrollment_student';
    END IF;

    IF v_enrollment_class_id IS NOT NULL
       AND v_assessment_class_id IS NOT NULL
       AND v_enrollment_class_id <> v_assessment_class_id THEN
        RAISE EXCEPTION
            'Integridade de turma violada: a matrícula % pertence à turma % e não à turma % da avaliação %.',
            NEW.enrollment_id, v_enrollment_class_id, v_assessment_class_id, NEW.assessment_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_enrollment_class';
    END IF;

    IF TG_OP = 'INSERT' AND v_enrollment_status IS NOT NULL AND v_enrollment_status <> 'ACTIVE' THEN
        RAISE EXCEPTION
            'Vínculo inativo: a matrícula % possui status "%" e exige status "ACTIVE" para lançamento de novas notas.',
            NEW.enrollment_id, v_enrollment_status
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_enrollment_active';
    END IF;

    -- 4.3. Validar que recorded_by pertence a um perfil docente/gestão (não STUDENT) e não ao próprio aluno
    SELECT u.role
      INTO v_recorder_role
      FROM users u
     WHERE u.id = NEW.recorded_by;

    IF FOUND AND v_recorder_role = 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "STUDENT" e não pode lançar notas em student_grades.',
            NEW.recorded_by
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_recorder_role';
    END IF;

    IF NEW.recorded_by = NEW.student_id THEN
        RAISE EXCEPTION
            'Auto-lançamento bloqueado em student_grades: o responsável % não pode lançar nota para si mesmo.',
            NEW.recorded_by
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_no_self_grading';
    END IF;

    -- 4.4. Validar que grade_value e recovery_grade nunca excedem academic_assessments.max_grade
    IF v_assessment_max_grade IS NOT NULL AND NEW.grade_value > v_assessment_max_grade THEN
        RAISE EXCEPTION
            'Nota inválida: grade_value (%) excede max_grade (%) da avaliação %.',
            NEW.grade_value, v_assessment_max_grade, NEW.assessment_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_exceeds_max_grade';
    END IF;

    IF v_assessment_max_grade IS NOT NULL
       AND NEW.recovery_grade IS NOT NULL
       AND NEW.recovery_grade > v_assessment_max_grade THEN
        RAISE EXCEPTION
            'Nota de recuperação inválida: recovery_grade (%) excede max_grade (%) da avaliação %.',
            NEW.recovery_grade, v_assessment_max_grade, NEW.assessment_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_grades_exceeds_max_grade';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_student_grades_validate_and_touch ON student_grades;

CREATE TRIGGER trg_student_grades_validate_and_touch
    BEFORE INSERT OR UPDATE ON student_grades
    FOR EACH ROW
    EXECUTE FUNCTION fn_student_grades_validate_and_touch();

-- 5. Observação Técnica: Trigger AFTER UPDATE registrando alterações em notas publicadas em audit_logs (DB-009 / BE-048)
CREATE OR REPLACE FUNCTION fn_student_grades_audit_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.grade_value IS DISTINCT FROM NEW.grade_value
       OR OLD.recovery_grade IS DISTINCT FROM NEW.recovery_grade
       OR OLD.comments IS DISTINCT FROM NEW.comments THEN
        INSERT INTO audit_logs (
            user_id,
            action,
            entity,
            entity_id,
            old_values,
            new_values
        )
        VALUES (
            NEW.recorded_by,
            'GRADE_UPDATED',
            'student_grades',
            NEW.id::TEXT,
            jsonb_build_object(
                'assessment_id', OLD.assessment_id,
                'enrollment_id', OLD.enrollment_id,
                'student_id', OLD.student_id,
                'grade_value', OLD.grade_value,
                'recovery_grade', OLD.recovery_grade,
                'comments', OLD.comments
            ),
            jsonb_build_object(
                'assessment_id', NEW.assessment_id,
                'enrollment_id', NEW.enrollment_id,
                'student_id', NEW.student_id,
                'grade_value', NEW.grade_value,
                'recovery_grade', NEW.recovery_grade,
                'comments', NEW.comments
            )
        );
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_student_grades_audit_update ON student_grades;

CREATE TRIGGER trg_student_grades_audit_update
    AFTER UPDATE ON student_grades
    FOR EACH ROW
    EXECUTE FUNCTION fn_student_grades_audit_update();

-- 6. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE student_grades IS
    'Notas individuais e de recuperação obtidas pelos estudantes nas avaliações formativas e provas (DB-028). Alterações posteriores disparam log automático em audit_logs (DB-009).';

COMMENT ON CONSTRAINT uq_student_grades_assessment_student ON student_grades IS
    'Regra DB-028: garante no máximo uma nota registrada por estudante em cada avaliação formativa.';

COMMENT ON CONSTRAINT chk_student_grades_value ON student_grades IS
    'Regra DB-028: grade_value deve estar entre 0.00 e 10.00 com precisão de 2 casas decimais.';

COMMENT ON CONSTRAINT chk_student_grades_recovery ON student_grades IS
    'Regra DB-028: recovery_grade, quando informada, deve estar entre 0.00 e 10.00 com precisão de 2 casas decimais.';

COMMIT;
