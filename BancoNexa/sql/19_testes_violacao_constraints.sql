-- =============================================================================
-- PROJETO NEXA — TESTES DE VIOLAÇÃO PROPOSITAL DE CONSTRAINTS (DB-019)
-- SGBD: PostgreSQL 16 (Execução isolada em transação com ROLLBACK automático)
-- =============================================================================
-- Valida diretamente no PostgreSQL 16 que todas as constraints de integridade
-- acadêmica de `classes` e `enrollments` rejeitam gravações inválidas:
--   1. Nota final 10.50 -> check_violation (23514 / chk_enrollments_final_grade)
--   2. Frequência -5.00% -> check_violation (23514 / chk_enrollments_attendance_rate)
--   3. Datas invertidas (start_date >= end_date) -> check_violation (23514 / chk_classes_date_range)
--   4. Capacidade excedida (3º aluno em turma max_students = 2) -> check_violation (23514)
--   5. Redução de max_students abaixo de ativos -> check_violation (23514)
--   6. Duplicidade (student_id, class_id) -> unique_violation (23505)
-- =============================================================================

BEGIN;

DO $$
DECLARE
    v_course_id UUID;
    v_class_id UUID;
    v_stu1_id UUID;
    v_stu2_id UUID;
    v_stu3_id UUID;
    v_caught BOOLEAN;
BEGIN
    -- Massa temporária isolada (será descartada pelo ROLLBACK final)
    INSERT INTO courses (code, name, total_hours)
    VALUES ('TST-DB019', 'Curso Teste Integridade DB-019', 400)
    RETURNING id INTO v_course_id;

    INSERT INTO classes (course_id, code, period, shift, max_students, status, start_date, end_date)
    VALUES (v_course_id, 'TST-019-A', '2026.9', 'MORNING', 2, 'ACTIVE', DATE '2026-02-01', DATE '2026-07-01')
    RETURNING id INTO v_class_id;

    INSERT INTO users (email, password_hash, role)
    VALUES ('db019.s1@senai.test', '$2b$12$01234567890123456789012345678901234567890123456789012', 'STUDENT')
    RETURNING id INTO v_stu1_id;

    INSERT INTO users (email, password_hash, role)
    VALUES ('db019.s2@senai.test', '$2b$12$01234567890123456789012345678901234567890123456789012', 'STUDENT')
    RETURNING id INTO v_stu2_id;

    INSERT INTO users (email, password_hash, role)
    VALUES ('db019.s3@senai.test', '$2b$12$01234567890123456789012345678901234567890123456789012', 'STUDENT')
    RETURNING id INTO v_stu3_id;

    -- 1. Teste de violação: final_grade = 10.50
    v_caught := FALSE;
    BEGIN
        INSERT INTO enrollments (student_id, class_id, final_grade)
        VALUES (v_stu1_id, v_class_id, 10.50);
    EXCEPTION WHEN check_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: final_grade = 10.50 deveria ter sido rejeitada!';
    END IF;

    -- 2. Teste de violação: attendance_rate = -5.00
    v_caught := FALSE;
    BEGIN
        INSERT INTO enrollments (student_id, class_id, attendance_rate)
        VALUES (v_stu1_id, v_class_id, -5.00);
    EXCEPTION WHEN check_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: attendance_rate = -5.00 deveria ter sido rejeitada!';
    END IF;

    -- 3. Teste de violação: start_date >= end_date em classes
    v_caught := FALSE;
    BEGIN
        INSERT INTO classes (course_id, code, period, shift, max_students, start_date, end_date)
        VALUES (v_course_id, 'TST-019-INV', '2026.9', 'NIGHT', 20, DATE '2026-08-01', DATE '2026-07-01');
    EXCEPTION WHEN check_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: start_date > end_date deveria ter sido rejeitada!';
    END IF;

    -- 4. Preencher as 2 vagas válidas e testar violação de duplicidade + capacidade máxima
    INSERT INTO enrollments (student_id, class_id, final_grade, attendance_rate)
    VALUES (v_stu1_id, v_class_id, 8.50, 95.00);

    INSERT INTO enrollments (student_id, class_id, final_grade, attendance_rate)
    VALUES (v_stu2_id, v_class_id, 7.00, 88.00);

    -- 4a. Violação de unicidade (student_id, class_id)
    v_caught := FALSE;
    BEGIN
        INSERT INTO enrollments (student_id, class_id)
        VALUES (v_stu1_id, v_class_id);
    EXCEPTION WHEN unique_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: matrícula duplicada deveria ter sido rejeitada!';
    END IF;

    -- 4b. Violação de capacidade máxima (3º aluno ativo em turma de 2 vagas)
    v_caught := FALSE;
    BEGIN
        INSERT INTO enrollments (student_id, class_id)
        VALUES (v_stu3_id, v_class_id);
    EXCEPTION WHEN check_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: 3º aluno em turma max_students=2 deveria ter sido bloqueado!';
    END IF;

    -- 5. Violação de redução de max_students abaixo do total de ativos (2 -> 1)
    v_caught := FALSE;
    BEGIN
        UPDATE classes SET max_students = 1 WHERE id = v_class_id;
    EXCEPTION WHEN check_violation THEN
        v_caught := TRUE;
    END;
    IF NOT v_caught THEN
        RAISE EXCEPTION 'FALHA DB-019: redução de max_students abaixo de alunos ativos deveria falhar!';
    END IF;

    RAISE NOTICE '✅ Todos os testes de violação proposital DB-019 foram bloqueados corretamente pelo PostgreSQL 16!';
END
$$;

ROLLBACK;
