-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: SUBMISSÕES E ENTREGAS PRÁTICAS (DB-025)
-- Versão: 20261123040000_create_task_submissions_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `task_submissions` (EPIC-04: Atividades Práticas de Oficina
-- & Competências) para controlar o ciclo de vida e o estado de entrega/execução
-- de cada atividade prática (`practical_tasks`) por estudante matriculado,
-- alimentando diretamente `DB-026` (`submission_evaluations`), `BE-025`, `BE-026`,
-- `FE-025` e `FE-036` (painel de pendências do portal do aluno):
-- 1. Constraint UNIQUE composta `uq_task_submissions_task_student (task_id, student_id)`
--    (e `uq_task_submissions_task_enrollment (task_id, enrollment_id)`).
-- 2. Índices em `(student_id, status)` para consulta instantânea da lista de
--    pendências do estudante, além de `(task_id, status)` e `(enrollment_id, status)`.
-- 3. Chaves estrangeiras íntegras com `ON DELETE RESTRICT ON UPDATE CASCADE` para
--    `practical_tasks`, `users` e `enrollments`.
-- 4. Trigger PL/pgSQL `trg_task_submissions_validate_and_touch` assegurando:
--    - coerência entre `enrollment_id` e `student_id`;
--    - pertencimento da matrícula à mesma turma da tarefa prática;
--    - matrícula com status `ACTIVE` na criação da submissão;
--    - `final_task_score <= practical_tasks.max_score`;
--    - controle de transições de estado (bloqueia regressão `EVALUATED -> PENDING`),
--      preenchimento automático de `completed_at` e atualização de `updated_at`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Garantir existência do enum nativo submission_status_enum (criado em DB-005)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submission_status_enum') THEN
        CREATE TYPE submission_status_enum AS ENUM ('PENDING', 'SUBMITTED', 'EVALUATED', 'LATE');
    END IF;
END
$$;

-- 3. Criar tabela de submissões e entregas práticas (`task_submissions`)
CREATE TABLE IF NOT EXISTS task_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    status submission_status_enum NOT NULL DEFAULT 'PENDING',
    completed_at TIMESTAMPTZ,
    evidence_url VARCHAR(500),
    student_notes TEXT,
    final_task_score NUMERIC(4,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Unicidade por tarefa prática e estudante/matrícula
    CONSTRAINT uq_task_submissions_task_student UNIQUE (task_id, student_id),
    CONSTRAINT uq_task_submissions_task_enrollment UNIQUE (task_id, enrollment_id),

    -- Regras de domínio: nota final entre 0.00 e 10.00 e URL de evidência HTTP/HTTPS
    CONSTRAINT chk_task_submissions_score CHECK (
        final_task_score IS NULL OR (final_task_score >= 0.00 AND final_task_score <= 10.00)
    ),
    CONSTRAINT chk_task_submissions_evidence_url CHECK (
        evidence_url IS NULL OR evidence_url ~* '^https?://'
    ),

    -- Critério de Aceitação 3: Integridade referencial estrita (ON DELETE RESTRICT)
    CONSTRAINT fk_task_submissions_task
        FOREIGN KEY (task_id) REFERENCES practical_tasks (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_task_submissions_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_task_submissions_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 4. Critério de Aceitação 2: Índice em (student_id, status) para pendências do portal do aluno (FE-036 / BE-026)
CREATE INDEX IF NOT EXISTS idx_task_submissions_student_status
    ON task_submissions USING BTREE (student_id, status);

-- Índices auxiliares para painel docente (BE-025 / FE-025) e visão 360° (DB-036)
CREATE INDEX IF NOT EXISTS idx_task_submissions_task_status
    ON task_submissions USING BTREE (task_id, status);

CREATE INDEX IF NOT EXISTS idx_task_submissions_enrollment_status
    ON task_submissions USING BTREE (enrollment_id, status);

-- 5. Função e Trigger PL/pgSQL para matrícula ativa na turma, nota <= max_score e transições de status
CREATE OR REPLACE FUNCTION fn_task_submissions_validate_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_task_class_id UUID;
    v_task_max_score NUMERIC(4,2);
    v_enrollment_student_id UUID;
    v_enrollment_class_id UUID;
    v_enrollment_status enrollment_status_enum;
BEGIN
    SELECT pt.class_id, pt.max_score
      INTO v_task_class_id, v_task_max_score
      FROM practical_tasks pt
     WHERE pt.id = NEW.task_id;

    SELECT e.student_id, e.class_id, e.status
      INTO v_enrollment_student_id, v_enrollment_class_id, v_enrollment_status
      FROM enrollments e
     WHERE e.id = NEW.enrollment_id;

    -- 5.1. Garantir que enrollment_id pertence ao mesmo student_id
    IF v_enrollment_student_id IS NOT NULL AND v_enrollment_student_id <> NEW.student_id THEN
        RAISE EXCEPTION
            'Integridade de matrícula violada: a matrícula % pertence ao estudante % e não ao estudante %.',
            NEW.enrollment_id, v_enrollment_student_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_task_submissions_enrollment_student';
    END IF;

    -- 5.2. Garantir que a matrícula pertence à mesma turma da tarefa prática
    IF v_enrollment_class_id IS NOT NULL
       AND v_task_class_id IS NOT NULL
       AND v_enrollment_class_id <> v_task_class_id THEN
        RAISE EXCEPTION
            'Integridade de turma violada: a matrícula % pertence à turma % e não à turma % da tarefa %.',
            NEW.enrollment_id, v_enrollment_class_id, v_task_class_id, NEW.task_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_task_submissions_enrollment_class';
    END IF;

    -- 5.3. Critério 3: Assegurar vínculo ativo (status = 'ACTIVE') na turma ao registrar nova submissão
    IF TG_OP = 'INSERT' AND v_enrollment_status IS NOT NULL AND v_enrollment_status <> 'ACTIVE' THEN
        RAISE EXCEPTION
            'Vínculo inativo: a matrícula % possui status "%" e exige status "ACTIVE" para receber entregas práticas.',
            NEW.enrollment_id, v_enrollment_status
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_task_submissions_enrollment_active';
    END IF;

    -- 5.4. Garantir que final_task_score nunca ultrapasse practical_tasks.max_score
    IF NEW.final_task_score IS NOT NULL
       AND v_task_max_score IS NOT NULL
       AND NEW.final_task_score > v_task_max_score THEN
        RAISE EXCEPTION
            'Nota inválida: final_task_score (%) excede max_score (%) da tarefa prática %.',
            NEW.final_task_score, v_task_max_score, NEW.task_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_task_submissions_score_exceeds_max';
    END IF;

    -- 5.5. Controle de transição de estado: impede regressão de EVALUATED para PENDING
    IF TG_OP = 'UPDATE' AND OLD.status = 'EVALUATED' AND NEW.status = 'PENDING' THEN
        RAISE EXCEPTION
            'Transição de estado inválida na submissão %: uma submissão já avaliada (EVALUATED) não pode retornar para PENDING.',
            NEW.id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_task_submissions_status_transition';
    END IF;

    -- 5.6. Preencher completed_at automaticamente ao concluir/avaliar e atualizar updated_at
    IF NEW.status IN ('SUBMITTED', 'EVALUATED') AND NEW.completed_at IS NULL THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_task_submissions_validate_and_touch ON task_submissions;

CREATE TRIGGER trg_task_submissions_validate_and_touch
    BEFORE INSERT OR UPDATE ON task_submissions
    FOR EACH ROW
    EXECUTE FUNCTION fn_task_submissions_validate_and_touch();

-- 6. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE task_submissions IS
    'Submissões e controle de estado de entrega/execução das tarefas práticas de oficina por estudante (DB-025). Alimenta DB-026, BE-025, BE-026 e FE-036.';

COMMENT ON CONSTRAINT uq_task_submissions_task_student ON task_submissions IS
    'Regra DB-025: garante no máximo uma entrega consolidada por estudante em cada atividade prática.';

COMMIT;
