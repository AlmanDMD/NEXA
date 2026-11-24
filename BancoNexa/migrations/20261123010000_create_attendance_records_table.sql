-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: REGISTROS DE PRESENÇA E FALTAS (DB-022)
-- Versão: 20261123010000_create_attendance_records_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `attendance_records` (EPIC-03: Diário de Classe: Notas & Frequência)
-- para armazenar a frequência individual de cada estudante por aula ministrada com
-- suporte a chamada rápida em 1 clique e upsert em lote (`BE-022` / `FE-022`),
-- automatizando o cálculo do limite legal de 75% de frequência SENAI:
-- 1. Constraint UNIQUE composta `uq_attendance_lesson_student (lesson_id, student_id)`
--    (e `uq_attendance_lesson_enrollment (lesson_id, enrollment_id)`) impedindo
--    chamada duplicada na mesma aula e habilitando `ON CONFLICT ... DO UPDATE`.
-- 2. Chaves estrangeiras íntegras com `ON DELETE RESTRICT ON UPDATE CASCADE` para
--    `class_lessons`, `enrollments` e `users`, garantindo que apenas estudantes
--    matriculados na turma recebam presença.
-- 3. Índice composto `idx_attendance_student_status (student_id, status)` para
--    agregação instantânea de faltas, complementado por `idx_attendance_lesson`
--    e `idx_attendance_enrollment_status`.
-- 4. Constraints CHECK e Trigger PL/pgSQL `trg_attendance_records_validate_integrity`
--    garantindo `absent_hours BETWEEN 0 AND 8`, `absent_hours <= lesson.workload_hours`,
--    `status = 'PRESENT' => absent_hours = 0`, coerência entre `enrollment_id` e
--    `student_id` e pertencimento da matrícula à mesma turma da aula.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Garantir existência do enum nativo attendance_status_enum (criado em DB-005)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendance_status_enum') THEN
        CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'JUSTIFIED');
    END IF;
END
$$;

-- 3. Criar tabela de registros atômicos de presença e faltas (`attendance_records`)
CREATE TABLE IF NOT EXISTS attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    status attendance_status_enum NOT NULL DEFAULT 'PRESENT',
    absent_hours INTEGER NOT NULL DEFAULT 0,
    justification_note TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Impede chamada duplicada do mesmo estudante na mesma aula (suporte a upsert em lote)
    CONSTRAINT uq_attendance_lesson_student UNIQUE (lesson_id, student_id),
    CONSTRAINT uq_attendance_lesson_enrollment UNIQUE (lesson_id, enrollment_id),

    -- Regras de domínio para horas ausentes por encontro letivo
    CONSTRAINT chk_attendance_absent_hours CHECK (absent_hours >= 0 AND absent_hours <= 8),
    CONSTRAINT chk_attendance_present_zero_absent CHECK (status <> 'PRESENT' OR absent_hours = 0),

    -- Critério de Aceitação 2: FKs íntegras para class_lessons, enrollments e users (ON DELETE RESTRICT)
    CONSTRAINT fk_attendance_lesson
        FOREIGN KEY (lesson_id) REFERENCES class_lessons (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_attendance_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 4. Critério de Aceitação 3: Índice em (student_id, status) para agregação instantânea de faltas
CREATE INDEX IF NOT EXISTS idx_attendance_student_status
    ON attendance_records USING BTREE (student_id, status);

-- Índices auxiliares para matriz de chamada em lote (BE-022 / FE-022) e consolidação por matrícula (BE-023 / DB-036)
CREATE INDEX IF NOT EXISTS idx_attendance_lesson
    ON attendance_records USING BTREE (lesson_id);

CREATE INDEX IF NOT EXISTS idx_attendance_enrollment_status
    ON attendance_records USING BTREE (enrollment_id, status);

-- 5. Função e Trigger PL/pgSQL para integridade entre matrícula, turma da aula e horas ausentes
CREATE OR REPLACE FUNCTION fn_attendance_records_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_lesson_class_id UUID;
    v_lesson_workload_hours INTEGER;
    v_enrollment_student_id UUID;
    v_enrollment_class_id UUID;
BEGIN
    SELECT cl.class_id, cl.workload_hours
      INTO v_lesson_class_id, v_lesson_workload_hours
      FROM class_lessons cl
     WHERE cl.id = NEW.lesson_id;

    SELECT e.student_id, e.class_id
      INTO v_enrollment_student_id, v_enrollment_class_id
      FROM enrollments e
     WHERE e.id = NEW.enrollment_id;

    -- 5.1. Garantir que enrollment_id pertence ao mesmo student_id informado
    IF v_enrollment_student_id IS NOT NULL AND v_enrollment_student_id <> NEW.student_id THEN
        RAISE EXCEPTION
            'Integridade de matrícula violada: a matrícula % pertence ao estudante % e não ao estudante %.',
            NEW.enrollment_id, v_enrollment_student_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_attendance_enrollment_student';
    END IF;

    -- 5.2. Garantir que o estudante está matriculado na mesma turma da aula ministrada
    IF v_enrollment_class_id IS NOT NULL
       AND v_lesson_class_id IS NOT NULL
       AND v_enrollment_class_id <> v_lesson_class_id THEN
        RAISE EXCEPTION
            'Integridade de turma violada: a matrícula % pertence à turma % e não à turma % da aula %.',
            NEW.enrollment_id, v_enrollment_class_id, v_lesson_class_id, NEW.lesson_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_attendance_enrollment_class';
    END IF;

    -- 5.3. Garantir que absent_hours nunca ultrapasse a carga horária da aula
    IF v_lesson_workload_hours IS NOT NULL AND NEW.absent_hours > v_lesson_workload_hours THEN
        RAISE EXCEPTION
            'Carga horária de falta inválida: absent_hours (%) excede workload_hours (%) da aula %.',
            NEW.absent_hours, v_lesson_workload_hours, NEW.lesson_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_attendance_absent_exceeds_workload';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_attendance_records_validate_integrity ON attendance_records;

CREATE TRIGGER trg_attendance_records_validate_integrity
    BEFORE INSERT OR UPDATE ON attendance_records
    FOR EACH ROW
    EXECUTE FUNCTION fn_attendance_records_validate_integrity();

-- 6. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE attendance_records IS
    'Registros atômicos de presença e faltas por estudante em cada aula ministrada (DB-022). Suporta chamada em lote via ON CONFLICT (lesson_id, student_id).';

COMMENT ON CONSTRAINT uq_attendance_lesson_student ON attendance_records IS
    'Regra DB-022: impede chamada duplicada do mesmo estudante na mesma aula e ancora o upsert em lote (BE-022).';

COMMENT ON CONSTRAINT chk_attendance_absent_hours ON attendance_records IS
    'Regra DB-022: absent_hours deve estar entre 0 e 8 horas por aula, nunca excedendo class_lessons.workload_hours.';

COMMIT;
