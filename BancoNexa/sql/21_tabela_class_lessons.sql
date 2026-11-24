-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: AULAS MINISTRADAS E DIÁRIO DE BORDO (DB-021)
-- Versão: 20261123000000_create_class_lessons_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `class_lessons` (EPIC-03: Diário de Classe: Notas & Frequência)
-- para persistir os encontros letivos e aulas práticas ministradas em cada turma,
-- disciplina e módulo prático SENAI, servindo de âncora obrigatória para os
-- registros de presença (`attendance_records` — DB-022) e endpoint de diário (BE-021):
-- 1. Chaves estrangeiras íntegras com `ON DELETE RESTRICT ON UPDATE CASCADE` para
--    `classes`, `subjects`, `learning_modules` (opcional/NULL) e `users`.
-- 2. Índice composto `idx_class_lessons_class_subject_date` em
--    `(class_id, subject_id, lesson_date)` para listagem cronológica rápida do
--    diário de bordo, mais índices auxiliares em `(module_id)` e `(teacher_id)`.
-- 3. Validação de carga horária por turno `chk_class_lessons_workload` exigindo
--    `workload_hours BETWEEN 1 AND 8` (valor padrão `4`) e `topic_summary` não vazio.
-- 4. Trigger PL/pgSQL `trg_class_lessons_validate_integrity` garantindo:
--    - `teacher_id` não pertence a usuário com `role = 'STUDENT'`;
--    - `subject_id` pertence ao mesmo curso (`course_id`) da turma `class_id`;
--    - quando `module_id` for informado, o módulo pertence à disciplina `subject_id`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de aulas ministradas e diário de bordo (`class_lessons`)
CREATE TABLE IF NOT EXISTS class_lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    teacher_id UUID NOT NULL,
    lesson_date DATE NOT NULL,
    workload_hours INTEGER NOT NULL DEFAULT 4,
    topic_summary TEXT NOT NULL,
    lab_environment VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 3: Carga horária por turno entre 1 e 8 horas
    CONSTRAINT chk_class_lessons_workload CHECK (workload_hours BETWEEN 1 AND 8),

    -- Higiene de domínio: resumo de conteúdo ministrado não pode ser apenas espaços
    CONSTRAINT chk_class_lessons_topic_summary_not_blank CHECK (length(btrim(topic_summary)) > 0),

    -- Critério de Aceitação 1: FKs íntegras para classes, subjects, learning_modules e users
    CONSTRAINT fk_class_lessons_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_class_lessons_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_class_lessons_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_class_lessons_teacher
        FOREIGN KEY (teacher_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 2: Índice composto para listagem cronológica rápida do diário
CREATE INDEX IF NOT EXISTS idx_class_lessons_class_subject_date
    ON class_lessons USING BTREE (class_id, subject_id, lesson_date);

-- Índices auxiliares para consultas por módulo prático (DB-037) e por docente (BE-021)
CREATE INDEX IF NOT EXISTS idx_class_lessons_module
    ON class_lessons USING BTREE (module_id);

CREATE INDEX IF NOT EXISTS idx_class_lessons_teacher
    ON class_lessons USING BTREE (teacher_id);

-- 4. Função e Trigger PL/pgSQL para coerência relacional do diário de bordo
CREATE OR REPLACE FUNCTION fn_class_lessons_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_teacher_role user_role_enum;
    v_class_course_id UUID;
    v_subject_course_id UUID;
    v_module_subject_id UUID;
BEGIN
    -- 4.1. Impedir que um estudante (role = 'STUDENT') seja registrado como docente da aula
    IF TG_OP = 'INSERT' OR NEW.teacher_id IS DISTINCT FROM OLD.teacher_id THEN
        SELECT u.role INTO v_teacher_role
        FROM users u
        WHERE u.id = NEW.teacher_id;

        IF FOUND AND v_teacher_role = 'STUDENT' THEN
            RAISE EXCEPTION
                'Integridade de perfil violada: o usuário % possui role "STUDENT" e não pode ser registrado como docente em class_lessons.',
                NEW.teacher_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_class_lessons_teacher_role';
        END IF;
    END IF;

    -- 4.2. Garantir que a disciplina pertença ao mesmo curso da turma
    IF TG_OP = 'INSERT'
       OR NEW.class_id IS DISTINCT FROM OLD.class_id
       OR NEW.subject_id IS DISTINCT FROM OLD.subject_id THEN
        SELECT c.course_id INTO v_class_course_id
        FROM classes c
        WHERE c.id = NEW.class_id;

        SELECT s.course_id INTO v_subject_course_id
        FROM subjects s
        WHERE s.id = NEW.subject_id;

        IF v_class_course_id IS NOT NULL
           AND v_subject_course_id IS NOT NULL
           AND v_class_course_id <> v_subject_course_id THEN
            RAISE EXCEPTION
                'Integridade curricular violada: a disciplina % pertence ao curso % e não ao curso % da turma %.',
                NEW.subject_id, v_subject_course_id, v_class_course_id, NEW.class_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_class_lessons_subject_course';
        END IF;
    END IF;

    -- 4.3. Quando module_id for informado, garantir que o módulo pertença à disciplina informada
    IF NEW.module_id IS NOT NULL AND (
        TG_OP = 'INSERT'
        OR NEW.module_id IS DISTINCT FROM OLD.module_id
        OR NEW.subject_id IS DISTINCT FROM OLD.subject_id
    ) THEN
        SELECT lm.subject_id INTO v_module_subject_id
        FROM learning_modules lm
        WHERE lm.id = NEW.module_id;

        IF FOUND AND v_module_subject_id <> NEW.subject_id THEN
            RAISE EXCEPTION
                'Integridade modular violada: o módulo prático % pertence à disciplina % e não à disciplina %.',
                NEW.module_id, v_module_subject_id, NEW.subject_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_class_lessons_module_subject';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_class_lessons_validate_integrity ON class_lessons;

CREATE TRIGGER trg_class_lessons_validate_integrity
    BEFORE INSERT OR UPDATE ON class_lessons
    FOR EACH ROW
    EXECUTE FUNCTION fn_class_lessons_validate_integrity();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE class_lessons IS
    'Aulas ministradas e diário de bordo por turma, disciplina e módulo prático SENAI (DB-021). Âncora obrigatória para attendance_records (DB-022).';

COMMENT ON CONSTRAINT chk_class_lessons_workload ON class_lessons IS
    'Regra DB-021: carga horária de cada encontro letivo/oficina deve estar entre 1 e 8 horas por turno.';

COMMIT;
