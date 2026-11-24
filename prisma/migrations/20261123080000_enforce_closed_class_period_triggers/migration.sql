-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: PERÍODO LETIVO FECHADO (DB-029)
-- Versão: 20261123080000_enforce_closed_class_period_triggers
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa proteção em nível de banco de dados (defesa em profundidade em
-- conjunto com o middleware BE-029 `check_class_is_active`) para impedir
-- alterações retroativas em diários de turmas encerradas (`classes.status IN
-- ('COMPLETED', 'ARCHIVED')`):
-- 1. Função auxiliar `fn_assert_class_not_closed(UUID, TEXT, TEXT)` consultando
--    `classes.status` e lançando exceção SQL clara (`SQLSTATE P0001`) contendo
--    o código `CLASS_PERIOD_CLOSED`, a frase `Período letivo encerrado` e o
--    nome `fn_prevent_closed_class_mutation` (detectável por BE-029).
-- 2. Função PL/pgSQL `fn_prevent_closed_class_mutation()` resolvendo a turma
--    alvo de forma íntegra para `student_grades`, `attendance_records`,
--    `task_submissions` e `submission_evaluations` em operações `INSERT`,
--    `UPDATE` e `DELETE`.
-- 3. Triggers BEFORE associadas às tabelas `student_grades`,
--    `attendance_records`, `task_submissions` e `submission_evaluations`.
-- 4. Consultas de leitura (`SELECT`) permanecem 100% liberadas para histórico,
--    boletins, auditoria e relatórios analíticos.
-- =============================================================================

BEGIN;

-- 1. Função auxiliar reutilizável de validação de período letivo encerrado
CREATE OR REPLACE FUNCTION fn_assert_class_not_closed(
    p_class_id UUID,
    p_operation TEXT,
    p_table_name TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_class_code VARCHAR(40);
    v_class_status class_status_enum;
BEGIN
    IF p_class_id IS NULL THEN
        RETURN;
    END IF;

    SELECT c.code, c.status
      INTO v_class_code, v_class_status
      FROM classes c
     WHERE c.id = p_class_id;

    IF FOUND AND v_class_status IN ('COMPLETED', 'ARCHIVED') THEN
        RAISE EXCEPTION
            '[CLASS_PERIOD_CLOSED] Período letivo encerrado para esta turma (% — status "%"): operação % bloqueada na tabela % pela função fn_prevent_closed_class_mutation.',
            v_class_code, v_class_status, p_operation, p_table_name
            USING ERRCODE = 'P0001',
                  HINT = 'Turmas com status COMPLETED ou ARCHIVED são somente leitura (SELECT permitido). Reabra a turma via coordenação acadêmica para ajustes excepcionais.';
    END IF;
END;
$$;

-- 2. Função Trigger PL/pgSQL principal (DB-029): fn_prevent_closed_class_mutation()
CREATE OR REPLACE FUNCTION fn_prevent_closed_class_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_class_id UUID;
    v_new_class_id UUID;
BEGIN
    -- 2.1. Resolver class_id conforme a tabela monitorada
    IF TG_TABLE_NAME = 'student_grades' THEN
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            SELECT COALESCE(aa.class_id, e.class_id)
              INTO v_old_class_id
              FROM academic_assessments aa
              LEFT JOIN enrollments e ON e.id = OLD.enrollment_id
             WHERE aa.id = OLD.assessment_id;
        END IF;

        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            SELECT COALESCE(aa.class_id, e.class_id)
              INTO v_new_class_id
              FROM academic_assessments aa
              LEFT JOIN enrollments e ON e.id = NEW.enrollment_id
             WHERE aa.id = NEW.assessment_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'attendance_records' THEN
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            SELECT COALESCE(cl.class_id, e.class_id)
              INTO v_old_class_id
              FROM class_lessons cl
              LEFT JOIN enrollments e ON e.id = OLD.enrollment_id
             WHERE cl.id = OLD.lesson_id;
        END IF;

        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            SELECT COALESCE(cl.class_id, e.class_id)
              INTO v_new_class_id
              FROM class_lessons cl
              LEFT JOIN enrollments e ON e.id = NEW.enrollment_id
             WHERE cl.id = NEW.lesson_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'task_submissions' THEN
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            SELECT COALESCE(pt.class_id, e.class_id)
              INTO v_old_class_id
              FROM practical_tasks pt
              LEFT JOIN enrollments e ON e.id = OLD.enrollment_id
             WHERE pt.id = OLD.task_id;
        END IF;

        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            SELECT COALESCE(pt.class_id, e.class_id)
              INTO v_new_class_id
              FROM practical_tasks pt
              LEFT JOIN enrollments e ON e.id = NEW.enrollment_id
             WHERE pt.id = NEW.task_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'submission_evaluations' THEN
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            SELECT pt.class_id
              INTO v_old_class_id
              FROM task_submissions ts
              JOIN practical_tasks pt ON pt.id = ts.task_id
             WHERE ts.id = OLD.submission_id;
        END IF;

        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            SELECT pt.class_id
              INTO v_new_class_id
              FROM task_submissions ts
              JOIN practical_tasks pt ON pt.id = ts.task_id
             WHERE ts.id = NEW.submission_id;
        END IF;
    END IF;

    -- 2.2. Validar bloqueio de período letivo encerrado (COMPLETED / ARCHIVED)
    IF v_old_class_id IS NOT NULL THEN
        PERFORM fn_assert_class_not_closed(v_old_class_id, TG_OP, TG_TABLE_NAME);
    END IF;

    IF v_new_class_id IS NOT NULL AND v_new_class_id IS DISTINCT FROM v_old_class_id THEN
        PERFORM fn_assert_class_not_closed(v_new_class_id, TG_OP, TG_TABLE_NAME);
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

-- 3. Triggers associadas às tabelas de notas, presenças, submissões e avaliações por rubrica
DROP TRIGGER IF EXISTS trg_student_grades_prevent_closed_class ON student_grades;
CREATE TRIGGER trg_student_grades_prevent_closed_class
    BEFORE INSERT OR UPDATE OR DELETE ON student_grades
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_closed_class_mutation();

DROP TRIGGER IF EXISTS trg_attendance_records_prevent_closed_class ON attendance_records;
CREATE TRIGGER trg_attendance_records_prevent_closed_class
    BEFORE INSERT OR UPDATE OR DELETE ON attendance_records
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_closed_class_mutation();

DROP TRIGGER IF EXISTS trg_task_submissions_prevent_closed_class ON task_submissions;
CREATE TRIGGER trg_task_submissions_prevent_closed_class
    BEFORE INSERT OR UPDATE OR DELETE ON task_submissions
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_closed_class_mutation();

DROP TRIGGER IF EXISTS trg_submission_evaluations_prevent_closed_class ON submission_evaluations;
CREATE TRIGGER trg_submission_evaluations_prevent_closed_class
    BEFORE INSERT OR UPDATE OR DELETE ON submission_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_closed_class_mutation();

-- 4. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON FUNCTION fn_prevent_closed_class_mutation() IS
    '[DB-029] Bloqueia mutações (INSERT/UPDATE/DELETE) em student_grades, attendance_records, task_submissions e submission_evaluations quando classes.status IN (''COMPLETED'', ''ARCHIVED''), mantendo SELECT liberado para histórico. Integrado ao middleware BE-029 (CLASS_PERIOD_CLOSED).';

COMMENT ON FUNCTION fn_assert_class_not_closed(UUID, TEXT, TEXT) IS
    '[DB-029] Valida se a turma está encerrada (COMPLETED ou ARCHIVED) e lança exceção SQL P0001 com identificador CLASS_PERIOD_CLOSED.';

COMMIT;
