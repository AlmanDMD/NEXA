-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE MATRÍCULAS (DB-017)
-- Versão: 20261118060000_create_enrollments_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `enrollments` para registrar formalmente o ingresso,
-- status e indicadores consolidados de um estudante em uma turma SENAI:
-- 1. Unicidade composta `uq_enrollments_student_class (student_id, class_id)`
--    impedindo múltiplas matrículas do mesmo estudante na mesma turma.
-- 2. FKs estritas (`fk_enrollments_student -> users(id)` e
--    `fk_enrollments_class -> classes(id)`) com `ON DELETE RESTRICT ON UPDATE CASCADE`
--    e trigger PL/pgSQL `trg_enrollments_validate_student_role_and_touch`
--    garantindo que apenas usuários com `role = 'STUDENT'` sejam matriculados.
-- 3. Status padrão `'ACTIVE'` tipado pelo enum nativo `enrollment_status_enum`
--    (`ACTIVE`, `COMPLETED`, `DROPPED`, `SUSPENDED` — DB-005).
-- 4. `final_grade` (`NUMERIC(4,2)` entre `0.00` e `10.00`) e `attendance_rate`
--    (`NUMERIC(5,2)` em porcentagem `0.00` a `100.00`) com índices dedicados
--    para filtros de risco acadêmico (`idx_enrollments_attendance_rate`,
--    `idx_enrollments_class_status_attendance`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enum nativo enrollment_status_enum (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE enrollment_status_enum AS ENUM ('ACTIVE', 'COMPLETED', 'DROPPED', 'SUSPENDED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de matrículas de estudantes (`enrollments`)
CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    class_id UUID NOT NULL,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status enrollment_status_enum NOT NULL DEFAULT 'ACTIVE',
    final_grade NUMERIC(4,2),
    attendance_rate NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Apenas uma matrícula por estudante em cada turma
    CONSTRAINT uq_enrollments_student_class UNIQUE (student_id, class_id),

    -- Validações numéricas de nota final (0.00..10.00) e taxa de frequência (0.00..100.00%)
    CONSTRAINT chk_enrollments_final_grade CHECK (
        final_grade IS NULL OR (final_grade >= 0.00 AND final_grade <= 10.00)
    ),
    CONSTRAINT chk_enrollments_attendance_rate CHECK (
        attendance_rate IS NULL OR (attendance_rate >= 0.00 AND attendance_rate <= 100.00)
    ),

    -- Critério de Aceitação 2: Chaves estrangeiras com integridade histórica (ON DELETE RESTRICT)
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_enrollments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Observação Técnica: Índice em attendance_rate para filtros de risco e índices operacionais (BE-016/BE-017)
CREATE INDEX IF NOT EXISTS idx_enrollments_attendance_rate
    ON enrollments USING BTREE (attendance_rate);

CREATE INDEX IF NOT EXISTS idx_enrollments_class_status_attendance
    ON enrollments USING BTREE (class_id, status, attendance_rate);

CREATE INDEX IF NOT EXISTS idx_enrollments_class_status
    ON enrollments USING BTREE (class_id, status);

CREATE INDEX IF NOT EXISTS idx_enrollments_student_status
    ON enrollments USING BTREE (student_id, status);

-- 4. Função e Trigger PL/pgSQL para validar perfil role = 'STUDENT' (Critério 2) e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_enrollments_validate_student_role_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_role user_role_enum;
BEGIN
    IF TG_OP = 'INSERT' OR NEW.student_id IS DISTINCT FROM OLD.student_id THEN
        SELECT u.role INTO v_user_role
        FROM users u
        WHERE u.id = NEW.student_id;

        IF FOUND AND v_user_role <> 'STUDENT' THEN
            RAISE EXCEPTION
                'Integridade de perfil violada: o usuário % possui role "%" e apenas usuários com role "STUDENT" podem ser matriculados em enrollments.',
                NEW.student_id, v_user_role
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_enrollments_student_role';
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enrollments_validate_student_role_and_touch ON enrollments;

CREATE TRIGGER trg_enrollments_validate_student_role_and_touch
    BEFORE INSERT OR UPDATE ON enrollments
    FOR EACH ROW
    EXECUTE FUNCTION fn_enrollments_validate_student_role_and_touch();

COMMIT;
