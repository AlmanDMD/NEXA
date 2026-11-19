-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: ALOCAÇÃO DE PROFESSORES (DB-018)
-- Versão: 20261118070000_create_teacher_assignments_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `teacher_assignments` para vincular instrutores/docentes
-- (`users` com `role = 'TEACHER'`) às turmas (`classes`) e disciplinas
-- (`subjects`), servindo como base do RBAC contextual para diário de classe,
-- chamada, atividades práticas e lançamento de notas:
-- 1. Chave única composta `uq_teacher_assignments_composite` em
--    `(teacher_id, class_id, subject_id)` impedindo duplicidade de alocação do
--    mesmo professor, mas permitindo múltiplos professores (titular + instrutor
--    de oficina) na mesma disciplina e turma.
-- 2. Chaves estrangeiras íntegras com `ON DELETE RESTRICT ON UPDATE CASCADE`
--    para `users`, `classes` e `subjects`.
-- 3. Trigger PL/pgSQL `trg_teacher_assignments_validate_teacher_role` exigindo
--    que o usuário alocado possua `role = 'TEACHER'`.
-- 4. Índices compostos eficientes para checagem rápida de autorização RBAC
--    (`idx_teacher_assignments_teacher_class`, `idx_teacher_assignments_class_subject`,
--    `idx_teacher_assignments_subject`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de atribuição docente (`teacher_assignments`)
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL,
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_main_teacher BOOLEAN NOT NULL DEFAULT TRUE,

    -- Critério de Aceitação 1: Chave única composta (permite múltiplos docentes na mesma turma/disciplina)
    CONSTRAINT uq_teacher_assignments_composite UNIQUE (teacher_id, class_id, subject_id),

    -- Critério de Aceitação 2: Foreign keys íntegras com ON DELETE RESTRICT
    CONSTRAINT fk_teacher_assignments_teacher
        FOREIGN KEY (teacher_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_teacher_assignments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_teacher_assignments_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3 & DoD: Índices eficientes para checagem de autorização RBAC contextual
CREATE INDEX IF NOT EXISTS idx_teacher_assignments_teacher_class
    ON teacher_assignments USING BTREE (teacher_id, class_id);

CREATE INDEX IF NOT EXISTS idx_teacher_assignments_class_subject
    ON teacher_assignments USING BTREE (class_id, subject_id);

CREATE INDEX IF NOT EXISTS idx_teacher_assignments_subject
    ON teacher_assignments USING BTREE (subject_id);

-- 4. Função e Trigger PL/pgSQL para validar que teacher_id pertence a um usuário com role = 'TEACHER'
CREATE OR REPLACE FUNCTION fn_teacher_assignments_validate_teacher_role()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_role user_role_enum;
BEGIN
    IF TG_OP = 'INSERT' OR NEW.teacher_id IS DISTINCT FROM OLD.teacher_id THEN
        SELECT u.role INTO v_user_role
        FROM users u
        WHERE u.id = NEW.teacher_id;

        IF FOUND AND v_user_role <> 'TEACHER' THEN
            RAISE EXCEPTION
                'Integridade de perfil violada: o usuário % possui role "%" e apenas usuários com role "TEACHER" podem ser alocados em teacher_assignments.',
                NEW.teacher_id, v_user_role
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_teacher_assignments_teacher_role';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_teacher_assignments_validate_teacher_role ON teacher_assignments;

CREATE TRIGGER trg_teacher_assignments_validate_teacher_role
    BEFORE INSERT OR UPDATE ON teacher_assignments
    FOR EACH ROW
    EXECUTE FUNCTION fn_teacher_assignments_validate_teacher_role();

COMMIT;
