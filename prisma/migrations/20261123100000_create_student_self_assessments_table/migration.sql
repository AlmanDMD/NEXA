-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: AUTOAVALIAÇÃO DO ALUNO (DB-032)
-- Versão: 20261123100000_create_student_self_assessments_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `student_self_assessments` (EPIC-07: Autoavaliação &
-- Motor de Diagnóstico Explicável — Sprint S4 / Lote 4) para persistir o nível
-- percebido de domínio (`perceived_level`, 1..5), o grau de confiança
-- (`confidence_score`, 1..5) e dificuldades relatadas (`difficulty_notes`)
-- declarados pelo próprio estudante para cada competência técnica do módulo,
-- desbloqueando `DB-035`, `DB-038` (`vw_self_eval_discrepancy`), `DB-040`,
-- `BE-036` e `FE-041`:
-- 1. Constraint UNIQUE composta `uq_student_self_assessments_composite` em
--    `(form_id, student_id, competency_id)` impedindo respostas duplicadas no
--    mesmo ciclo de autoavaliação.
-- 2. CHECK constraints `chk_self_assessments_perceived` e
--    `chk_self_assessments_confidence` garantindo intervalo inteiro de `1` a `5`.
-- 3. Isolamento estrito de acesso via Row-Level Security (RLS) PostgreSQL 16
--    (`pol_student_self_assessments_student_isolation`): um estudante jamais
--    pode ler ou modificar a autoavaliação de outro colega.
-- 4. Trigger PL/pgSQL `trg_student_self_assessments_validate_integrity`
--    validando perfil `STUDENT`, matrícula `ACTIVE` na turma do formulário,
--    formulário ativo na janela `[opens_at, closes_at]` e pertinência da
--    competência ao módulo em `module_competencies`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de respostas de autoavaliação do estudante (`student_self_assessments`)
CREATE TABLE IF NOT EXISTS student_self_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL,
    student_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    perceived_level INTEGER NOT NULL,
    confidence_score INTEGER NOT NULL,
    difficulty_notes TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Unicidade por formulário, estudante e competência
    CONSTRAINT uq_student_self_assessments_composite UNIQUE (form_id, student_id, competency_id),

    -- Critério de Aceitação 2: Escala inteira de 1 a 5 para nível percebido e confiança
    CONSTRAINT chk_self_assessments_perceived CHECK (perceived_level BETWEEN 1 AND 5),
    CONSTRAINT chk_self_assessments_confidence CHECK (confidence_score BETWEEN 1 AND 5),

    -- Integridade referencial estrita (ON DELETE RESTRICT protege histórico diagnóstico)
    CONSTRAINT fk_student_self_assessments_form
        FOREIGN KEY (form_id) REFERENCES self_assessment_forms (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_student_self_assessments_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_student_self_assessments_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Índices B-Tree para cruzamento em vw_self_eval_discrepancy (DB-038), submissão (BE-036) e diagnósticos (DB-035)
CREATE INDEX IF NOT EXISTS idx_student_self_assessments_student_competency
    ON student_self_assessments USING BTREE (student_id, competency_id);

CREATE INDEX IF NOT EXISTS idx_student_self_assessments_form_student
    ON student_self_assessments USING BTREE (form_id, student_id);

CREATE INDEX IF NOT EXISTS idx_student_self_assessments_competency
    ON student_self_assessments USING BTREE (competency_id);

-- 4. Critério de Aceitação 3: Row-Level Security (RLS) garantindo isolamento total entre estudantes
ALTER TABLE student_self_assessments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_student_self_assessments_student_isolation ON student_self_assessments;

CREATE POLICY pol_student_self_assessments_student_isolation
    ON student_self_assessments
    FOR ALL
    USING (
        COALESCE(NULLIF(current_setting('app.current_user_role', TRUE), ''), 'SYSTEM') <> 'STUDENT'
        OR student_id::TEXT = NULLIF(current_setting('app.current_user_id', TRUE), '')
    )
    WITH CHECK (
        COALESCE(NULLIF(current_setting('app.current_user_role', TRUE), ''), 'SYSTEM') <> 'STUDENT'
        OR student_id::TEXT = NULLIF(current_setting('app.current_user_id', TRUE), '')
    );

-- 5. Função e Trigger PL/pgSQL para validar perfil STUDENT, matrícula ativa na turma, janela aberta e competência do módulo
CREATE OR REPLACE FUNCTION fn_student_self_assessments_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_form_module_id UUID;
    v_form_class_id UUID;
    v_form_is_active BOOLEAN;
    v_form_opens_at TIMESTAMPTZ;
    v_form_closes_at TIMESTAMPTZ;
    v_has_active_enrollment BOOLEAN;
    v_module_has_competencies BOOLEAN;
    v_competency_in_module BOOLEAN;
BEGIN
    -- 5.1. Garantir que student_id possui role = 'STUDENT'
    SELECT u.role
      INTO v_student_role
      FROM users u
     WHERE u.id = NEW.student_id;

    IF FOUND AND v_student_role <> 'STUDENT' THEN
        RAISE EXCEPTION
            'Integridade de perfil violada: o usuário % possui role "%" e apenas usuários "STUDENT" podem responder autoavaliações.',
            NEW.student_id, v_student_role
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_self_assessments_student_role';
    END IF;

    -- 5.2. Carregar formulário de autoavaliação
    SELECT saf.module_id, saf.class_id, saf.is_active, saf.opens_at, saf.closes_at
      INTO v_form_module_id, v_form_class_id, v_form_is_active, v_form_opens_at, v_form_closes_at
      FROM self_assessment_forms saf
     WHERE saf.id = NEW.form_id;

    IF FOUND THEN
        -- 5.3. Garantir matrícula ACTIVE do estudante na turma do formulário (DB-017)
        SELECT EXISTS (
            SELECT 1
              FROM enrollments e
             WHERE e.student_id = NEW.student_id
               AND e.class_id = v_form_class_id
               AND e.status = 'ACTIVE'
        ) INTO v_has_active_enrollment;

        IF TG_OP = 'INSERT' AND NOT v_has_active_enrollment THEN
            RAISE EXCEPTION
                'Vínculo de matrícula inválido: o estudante % não possui matrícula ACTIVE na turma % do formulário %.',
                NEW.student_id, v_form_class_id, NEW.form_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_student_self_assessments_active_enrollment';
        END IF;

        -- 5.4. Validar formulário ativo e dentro da janela temporal [opens_at, closes_at] no INSERT
        IF TG_OP = 'INSERT' AND (
            NOT v_form_is_active
            OR NEW.submitted_at < v_form_opens_at
            OR NEW.submitted_at > v_form_closes_at
        ) THEN
            RAISE EXCEPTION
                'Formulário fechado ou inativo: o formulário % não está aberto para submissões em %.',
                NEW.form_id, NEW.submitted_at
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_student_self_assessments_form_open';
        END IF;

        -- 5.5. Quando o módulo possuir competências cadastradas em module_competencies, exigir pertinência
        SELECT EXISTS (
            SELECT 1 FROM module_competencies mc WHERE mc.module_id = v_form_module_id
        ) INTO v_module_has_competencies;

        IF v_module_has_competencies THEN
            SELECT EXISTS (
                SELECT 1
                  FROM module_competencies mc
                 WHERE mc.module_id = v_form_module_id
                   AND mc.competency_id = NEW.competency_id
            ) INTO v_competency_in_module;

            IF NOT v_competency_in_module THEN
                RAISE EXCEPTION
                    'Integridade curricular violada: a competência % não pertence ao módulo % do formulário %.',
                    NEW.competency_id, v_form_module_id, NEW.form_id
                    USING ERRCODE = '23514',
                          CONSTRAINT = 'chk_student_self_assessments_module_competency';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_student_self_assessments_validate_integrity ON student_self_assessments;

CREATE TRIGGER trg_student_self_assessments_validate_integrity
    BEFORE INSERT OR UPDATE ON student_self_assessments
    FOR EACH ROW
    EXECUTE FUNCTION fn_student_self_assessments_validate_integrity();

-- 6. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE student_self_assessments IS
    'Respostas de autoavaliação de domínio (1..5) e confiança (1..5) declaradas pelo estudante por competência (DB-032). Protegida por RLS contra acesso cruzado entre colegas e consumida em DB-038 / BE-036.';

COMMENT ON CONSTRAINT uq_student_self_assessments_composite ON student_self_assessments IS
    'Regra DB-032: garante no máximo uma resposta de autoavaliação por (form_id, student_id, competency_id).';

COMMENT ON POLICY pol_student_self_assessments_student_isolation ON student_self_assessments IS
    'Regra DB-032 (Isolamento de Acesso): um estudante (app.current_user_role = STUDENT) só pode consultar/gravar seus próprios registros (student_id = app.current_user_id).';

COMMIT;
