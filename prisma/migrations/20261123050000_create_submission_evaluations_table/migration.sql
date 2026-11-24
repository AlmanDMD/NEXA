-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: AVALIAÇÕES POR RUBRICA (DB-026)
-- Versão: 20261123050000_create_submission_evaluations_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `submission_evaluations` (EPIC-04: Atividades Práticas
-- de Oficina & Competências) para registrar a nota (`score_awarded`), o nível
-- de domínio técnico (`achieved_level`, escala 1..5) e o feedback técnico
-- atribuído pelo docente avaliador em cada rubrica (`task_criteria`) de uma
-- entrega prática (`task_submissions`), fornecendo os dados reais verificados
-- para comparação com a autoavaliação do estudante (`DB-038` / `BE-037`) e
-- desbloqueando `DB-030`, `DB-033`, `BE-025` e `FE-026`:
-- 1. Constraint UNIQUE composta `uq_submission_evaluations_composite (submission_id, criterion_id)`
--    impedindo duas avaliações concorrentes para a mesma rubrica na mesma entrega.
-- 2. Validação CHECK `chk_submission_evaluations_level` exigindo `achieved_level BETWEEN 1 AND 5`
--    e `chk_submission_evaluations_score` exigindo `score_awarded BETWEEN 0.00 AND 10.00`.
-- 3. Chaves estrangeiras íntegras (`ON DELETE RESTRICT ON UPDATE CASCADE`) para
--    `task_submissions`, `task_criteria` e `users` (`evaluator_id` identificando
--    o docente avaliador).
-- 4. Trigger BEFORE `trg_submission_evaluations_validate_integrity` assegurando:
--    - `evaluator_id` não possui `role = 'STUDENT'` (exige perfil docente/coordenação/admin);
--    - `evaluator_id` não é o próprio estudante dono da submissão;
--    - `criterion_id` pertence à mesma tarefa prática (`task_id`) da submissão;
--    - `score_awarded <= practical_tasks.max_score`.
-- 5. Função `fn_calculate_submission_consolidated_score` + Trigger AFTER
--    `trg_submission_evaluations_sync_final_score` consolidando automaticamente
--    a média ponderada (`task_criteria.weight`) em `task_submissions.final_task_score`
--    e promovendo o status para `EVALUATED` quando todas as rubricas da peça
--    estiverem avaliadas.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de avaliações por rubrica dos professores (`submission_evaluations`)
CREATE TABLE IF NOT EXISTS submission_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL,
    criterion_id UUID NOT NULL,
    evaluator_id UUID NOT NULL,
    achieved_level INTEGER NOT NULL,
    score_awarded NUMERIC(4,2) NOT NULL,
    technical_feedback TEXT,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Unicidade por submissão e critério/rubrica
    CONSTRAINT uq_submission_evaluations_composite UNIQUE (submission_id, criterion_id),

    -- Critério de Aceitação 2: Nível de domínio na escala SENAI de 1 a 5
    CONSTRAINT chk_submission_evaluations_level CHECK (achieved_level BETWEEN 1 AND 5),

    -- Regra de domínio: nota atribuída à rubrica entre 0.00 e 10.00
    CONSTRAINT chk_submission_evaluations_score CHECK (score_awarded >= 0.00 AND score_awarded <= 10.00),

    -- Integridade referencial estrita (ON DELETE RESTRICT protege histórico avaliado)
    CONSTRAINT fk_submission_evaluations_submission
        FOREIGN KEY (submission_id) REFERENCES task_submissions (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_submission_evaluations_criterion
        FOREIGN KEY (criterion_id) REFERENCES task_criteria (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Critério de Aceitação 3: FK para evaluator_id identificando o docente avaliador
    CONSTRAINT fk_submission_evaluations_evaluator
        FOREIGN KEY (evaluator_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Índices B-Tree para consolidação de notas, rastreio por rubrica/competência (DB-033/DB-038) e auditoria docente
CREATE INDEX IF NOT EXISTS idx_submission_evaluations_submission
    ON submission_evaluations USING BTREE (submission_id);

CREATE INDEX IF NOT EXISTS idx_submission_evaluations_criterion
    ON submission_evaluations USING BTREE (criterion_id);

CREATE INDEX IF NOT EXISTS idx_submission_evaluations_evaluator
    ON submission_evaluations USING BTREE (evaluator_id, evaluated_at);

-- 4. Função e Trigger PL/pgSQL BEFORE para integridade docente, coerência rubrica-tarefa e teto de nota
CREATE OR REPLACE FUNCTION fn_submission_evaluations_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_evaluator_role user_role_enum;
    v_submission_task_id UUID;
    v_submission_student_id UUID;
    v_criterion_task_id UUID;
    v_task_max_score NUMERIC(4,2);
BEGIN
    -- 4.1. Critério de Aceitação 3: validar que evaluator_id possui perfil docente (não STUDENT)
    SELECT u.role
      INTO v_evaluator_role
      FROM users u
     WHERE u.id = NEW.evaluator_id;

    IF FOUND AND v_evaluator_role = 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "STUDENT" e não pode registrar avaliações docentes em submission_evaluations.',
            NEW.evaluator_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_submission_evaluations_evaluator_role';
    END IF;

    -- 4.2. Carregar tarefa e estudante da submissão
    SELECT ts.task_id, ts.student_id
      INTO v_submission_task_id, v_submission_student_id
      FROM task_submissions ts
     WHERE ts.id = NEW.submission_id;

    -- Impedir autoavaliação indevida na tabela docente (autoavaliação pertence a student_self_assessments — DB-032)
    IF v_submission_student_id IS NOT NULL AND NEW.evaluator_id = v_submission_student_id THEN
        RAISE EXCEPTION
            'Autoavaliação bloqueada em submission_evaluations: o avaliador % não pode ser o próprio estudante da submissão %.',
            NEW.evaluator_id, NEW.submission_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_submission_evaluations_no_self_eval';
    END IF;

    -- 4.3. Garantir que criterion_id pertence à mesma practical_task da submissão
    SELECT tc.task_id
      INTO v_criterion_task_id
      FROM task_criteria tc
     WHERE tc.id = NEW.criterion_id;

    IF v_submission_task_id IS NOT NULL
       AND v_criterion_task_id IS NOT NULL
       AND v_submission_task_id <> v_criterion_task_id THEN
        RAISE EXCEPTION
            'Integridade de rubrica violada: o critério % pertence à tarefa % e não à tarefa % da submissão %.',
            NEW.criterion_id, v_criterion_task_id, v_submission_task_id, NEW.submission_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_submission_evaluations_criterion_task';
    END IF;

    -- 4.4. Garantir que score_awarded não excede practical_tasks.max_score
    IF v_submission_task_id IS NOT NULL THEN
        SELECT pt.max_score
          INTO v_task_max_score
          FROM practical_tasks pt
         WHERE pt.id = v_submission_task_id;

        IF v_task_max_score IS NOT NULL AND NEW.score_awarded > v_task_max_score THEN
            RAISE EXCEPTION
                'Nota de rubrica inválida: score_awarded (%) excede max_score (%) da tarefa prática %.',
                NEW.score_awarded, v_task_max_score, v_submission_task_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_submission_evaluations_score_exceeds_max';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_submission_evaluations_validate_integrity ON submission_evaluations;

CREATE TRIGGER trg_submission_evaluations_validate_integrity
    BEFORE INSERT OR UPDATE ON submission_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION fn_submission_evaluations_validate_integrity();

-- 5. Função PL/pgSQL para cálculo da nota consolidada ponderada da submissão (DoD DB-026)
CREATE OR REPLACE FUNCTION fn_calculate_submission_consolidated_score(p_submission_id UUID)
RETURNS NUMERIC(4,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_weighted_score NUMERIC(10,4);
    v_total_weight NUMERIC(10,4);
    v_max_score NUMERIC(4,2);
    v_consolidated NUMERIC(4,2);
BEGIN
    SELECT pt.max_score
      INTO v_max_score
      FROM task_submissions ts
      JOIN practical_tasks pt ON pt.id = ts.task_id
     WHERE ts.id = p_submission_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    SELECT SUM(se.score_awarded * tc.weight), SUM(tc.weight)
      INTO v_weighted_score, v_total_weight
      FROM submission_evaluations se
      JOIN task_criteria tc ON tc.id = se.criterion_id
     WHERE se.submission_id = p_submission_id;

    IF v_total_weight IS NULL OR v_total_weight <= 0 THEN
        RETURN NULL;
    END IF;

    v_consolidated := ROUND(v_weighted_score / v_total_weight, 2);

    IF v_max_score IS NOT NULL AND v_consolidated > v_max_score THEN
        v_consolidated := v_max_score;
    END IF;

    RETURN v_consolidated;
END;
$$;

-- 6. Trigger PL/pgSQL AFTER para sincronizar task_submissions.final_task_score e status EVALUATED
CREATE OR REPLACE FUNCTION fn_submission_evaluations_sync_final_score()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_submission_id UUID;
    v_consolidated_score NUMERIC(4,2);
    v_total_criteria INTEGER;
    v_evaluated_criteria INTEGER;
BEGIN
    v_target_submission_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.submission_id ELSE NEW.submission_id END;

    v_consolidated_score := fn_calculate_submission_consolidated_score(v_target_submission_id);

    SELECT COUNT(tc.id)
      INTO v_total_criteria
      FROM task_submissions ts
      JOIN task_criteria tc ON tc.task_id = ts.task_id
     WHERE ts.id = v_target_submission_id;

    SELECT COUNT(se.id)
      INTO v_evaluated_criteria
      FROM submission_evaluations se
     WHERE se.submission_id = v_target_submission_id;

    UPDATE task_submissions
       SET final_task_score = v_consolidated_score,
           status = CASE
               WHEN v_total_criteria > 0 AND v_evaluated_criteria >= v_total_criteria
                   THEN 'EVALUATED'::submission_status_enum
               ELSE status
           END,
           completed_at = CASE
               WHEN v_total_criteria > 0 AND v_evaluated_criteria >= v_total_criteria AND completed_at IS NULL
                   THEN CURRENT_TIMESTAMP
               ELSE completed_at
           END,
           updated_at = CURRENT_TIMESTAMP
     WHERE id = v_target_submission_id;

    -- Caso uma atualização tenha alterado submission_id, recalcular também a submissão anterior
    IF TG_OP = 'UPDATE' AND OLD.submission_id IS DISTINCT FROM NEW.submission_id THEN
        UPDATE task_submissions
           SET final_task_score = fn_calculate_submission_consolidated_score(OLD.submission_id),
               updated_at = CURRENT_TIMESTAMP
         WHERE id = OLD.submission_id;
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_submission_evaluations_sync_final_score ON submission_evaluations;

CREATE TRIGGER trg_submission_evaluations_sync_final_score
    AFTER INSERT OR UPDATE OR DELETE ON submission_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION fn_submission_evaluations_sync_final_score();

-- 7. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE submission_evaluations IS
    'Avaliações por rubrica/critério técnico registradas pelo docente sobre cada entrega prática (DB-026). Fornece evidência real para comparação com autoavaliação (DB-038 / BE-037) e consolida task_submissions.final_task_score.';

COMMENT ON CONSTRAINT uq_submission_evaluations_composite ON submission_evaluations IS
    'Regra DB-026: garante no máximo uma avaliação docente por par (submission_id, criterion_id).';

COMMENT ON CONSTRAINT chk_submission_evaluations_level ON submission_evaluations IS
    'Regra DB-026: achieved_level deve estar na escala inteira SENAI de domínio técnico entre 1 e 5.';

COMMENT ON CONSTRAINT fk_submission_evaluations_evaluator ON submission_evaluations IS
    'Regra DB-026: identifica o docente avaliador (users.id) com proteção ON DELETE RESTRICT e validação de perfil não-STUDENT via trigger.';

COMMENT ON FUNCTION fn_calculate_submission_consolidated_score(UUID) IS
    'Calcula a média ponderada de score_awarded pelos pesos de task_criteria para consolidar task_submissions.final_task_score (DoD DB-026).';

COMMIT;
