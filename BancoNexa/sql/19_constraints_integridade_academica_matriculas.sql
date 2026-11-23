-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: CONSTRAINTS ACADÊMICAS (DB-019)
-- Versão: 20261118080000_enforce_academic_integrity_constraints
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Consolida e reforça no nível do motor PostgreSQL 16 todas as constraints de
-- unicidade, CHECK e integridade transacional de matrículas (`enrollments`) e
-- turmas (`classes`), prevenindo violações por concorrência ou falhas da camada
-- de aplicação:
-- 1. Notas finais (`enrollments.final_grade`) estritamente entre `0.00` e `10.00`
--    (`chk_enrollments_final_grade`).
-- 2. Taxa de frequência (`enrollments.attendance_rate`) estritamente entre
--    `0.00` e `100.00` (`chk_enrollments_attendance_rate`).
-- 3. Datas letivas coerentes (`classes.start_date < classes.end_date`,
--    `chk_classes_date_range`) e limite de capacidade (`max_students BETWEEN 1 AND 100`,
--    `chk_classes_max_students`).
-- 4. Unicidade de matrícula por estudante e turma (`uq_enrollments_student_class`).
-- 5. Controle atômico de capacidade máxima de alunos ativos por turma com
--    bloqueio pessimista `SELECT ... FOR UPDATE` (`trg_enrollments_enforce_class_capacity`)
--    e proteção contra redução indevida de `classes.max_students` abaixo do total
--    de alunos ativos já matriculados (`trg_classes_validate_max_students_reduction`).
-- =============================================================================

BEGIN;

-- 1. Garantir de forma idempotente as constraints CHECK e UNIQUE em `enrollments`
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_enrollments_student_class'
          AND conrelid = 'enrollments'::regclass
    ) THEN
        ALTER TABLE enrollments
            ADD CONSTRAINT uq_enrollments_student_class
            UNIQUE (student_id, class_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_enrollments_final_grade'
          AND conrelid = 'enrollments'::regclass
    ) THEN
        ALTER TABLE enrollments
            ADD CONSTRAINT chk_enrollments_final_grade
            CHECK (final_grade IS NULL OR (final_grade >= 0.00 AND final_grade <= 10.00));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_enrollments_attendance_rate'
          AND conrelid = 'enrollments'::regclass
    ) THEN
        ALTER TABLE enrollments
            ADD CONSTRAINT chk_enrollments_attendance_rate
            CHECK (attendance_rate IS NULL OR (attendance_rate >= 0.00 AND attendance_rate <= 100.00));
    END IF;
END
$$;

-- 2. Garantir de forma idempotente as constraints CHECK temporais e de capacidade em `classes`
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_classes_date_range'
          AND conrelid = 'classes'::regclass
    ) THEN
        ALTER TABLE classes
            ADD CONSTRAINT chk_classes_date_range
            CHECK (start_date < end_date);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_classes_max_students'
          AND conrelid = 'classes'::regclass
    ) THEN
        ALTER TABLE classes
            ADD CONSTRAINT chk_classes_max_students
            CHECK (max_students > 0 AND max_students <= 100);
    END IF;
END
$$;

-- 3. Trigger transacional com FOR UPDATE garantindo respeito à capacidade máxima da turma
CREATE OR REPLACE FUNCTION fn_enrollments_enforce_class_capacity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_max_students INTEGER;
    v_active_count INTEGER;
    v_requires_check BOOLEAN := FALSE;
BEGIN
    IF NEW.status = 'ACTIVE' THEN
        IF TG_OP = 'INSERT' THEN
            v_requires_check := TRUE;
        ELSIF TG_OP = 'UPDATE' AND (
            OLD.status IS DISTINCT FROM 'ACTIVE'
            OR OLD.class_id IS DISTINCT FROM NEW.class_id
        ) THEN
            v_requires_check := TRUE;
        END IF;
    END IF;

    IF v_requires_check THEN
        -- Bloqueio pessimista na linha da turma para evitar race condition sob matrículas concorrentes
        SELECT c.max_students INTO v_max_students
        FROM classes c
        WHERE c.id = NEW.class_id
        FOR UPDATE;

        IF FOUND THEN
            SELECT COUNT(*) INTO v_active_count
            FROM enrollments e
            WHERE e.class_id = NEW.class_id
              AND e.status = 'ACTIVE'
              AND (TG_OP = 'INSERT' OR e.id <> NEW.id);

            IF v_active_count >= v_max_students THEN
                RAISE EXCEPTION
                    'Capacidade máxima da turma % excedida: já existem % matrícula(s) ACTIVE para o limite de % vaga(s).',
                    NEW.class_id, v_active_count, v_max_students
                    USING ERRCODE = '23514',
                          CONSTRAINT = 'chk_enrollments_class_capacity';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enrollments_enforce_class_capacity ON enrollments;

CREATE TRIGGER trg_enrollments_enforce_class_capacity
    BEFORE INSERT OR UPDATE OF class_id, status ON enrollments
    FOR EACH ROW
    EXECUTE FUNCTION fn_enrollments_enforce_class_capacity();

-- 4. Trigger de proteção contra redução de `classes.max_students` abaixo do número de alunos ativos
CREATE OR REPLACE FUNCTION fn_classes_validate_max_students_reduction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_active_count INTEGER;
BEGIN
    IF NEW.max_students < OLD.max_students THEN
        SELECT COUNT(*) INTO v_active_count
        FROM enrollments e
        WHERE e.class_id = NEW.id
          AND e.status = 'ACTIVE';

        IF NEW.max_students < v_active_count THEN
            RAISE EXCEPTION
                'Não é possível reduzir max_students da turma % para %: há % estudante(s) com matrícula ACTIVE.',
                NEW.id, NEW.max_students, v_active_count
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_classes_max_students_vs_active';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_classes_validate_max_students_reduction ON classes;

CREATE TRIGGER trg_classes_validate_max_students_reduction
    BEFORE UPDATE OF max_students ON classes
    FOR EACH ROW
    EXECUTE FUNCTION fn_classes_validate_max_students_reduction();

-- 5. Comentários de catálogo PostgreSQL (documentação viva das constraints no SGBD)
COMMENT ON CONSTRAINT chk_enrollments_final_grade ON enrollments IS
    '[DB-019] Garante que a nota final consolidada esteja sempre no intervalo de 0.00 a 10.00.';

COMMENT ON CONSTRAINT chk_enrollments_attendance_rate ON enrollments IS
    '[DB-019] Garante que a taxa de frequência percentual esteja sempre no intervalo de 0.00 a 100.00.';

COMMENT ON CONSTRAINT uq_enrollments_student_class ON enrollments IS
    '[DB-017/DB-019] Impede duplicidade de matrícula do mesmo estudante na mesma turma.';

COMMENT ON CONSTRAINT chk_classes_date_range ON classes IS
    '[DB-012/DB-019] Garante que a data de início letivo (start_date) seja estritamente anterior à data de término (end_date).';

COMMENT ON CONSTRAINT chk_classes_max_students ON classes IS
    '[DB-012/DB-019] Garante que a capacidade máxima da turma esteja entre 1 e 100 alunos.';

COMMIT;
