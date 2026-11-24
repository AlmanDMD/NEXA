-- =============================================================================
-- PROJETO NEXA — SEED IDEMPOTENTE DE FREQUÊNCIAS, PRÁTICAS E NOTAS (DB-030)
-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)
-- 30 estudantes fictícios anônimos (zero CPFs ou nomes reais)
-- =============================================================================

BEGIN;

-- 1. 30 Estudantes Fictícios Anônimos + Perfis + Matrículas Ativas (MEC-2026-1 e MEC-2026-2)
INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo01@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 01', 'SENAI-2026-0001', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.16, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo02@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 02', 'SENAI-2026-0002', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.71, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo03@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 03', 'SENAI-2026-0003', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico AT_RISK).'
FROM users u WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 4.57, 68.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo04@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 04', 'SENAI-2026-0004', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 9.38, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo05@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 05', 'SENAI-2026-0005', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 7.11, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo06@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 06', 'SENAI-2026-0006', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico ATTENDANCE_BORDERLINE).'
FROM users u WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 6.51, 76.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo07@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 07', 'SENAI-2026-0007', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.27, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo08@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 08', 'SENAI-2026-0008', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.36, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo09@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 09', 'SENAI-2026-0009', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.16, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo10@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 10', 'SENAI-2026-0010', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.71, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo11@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 11', 'SENAI-2026-0011', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 9.27, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo12@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 12', 'SENAI-2026-0012', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 6.91, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo13@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 13', 'SENAI-2026-0013', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 7.16, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo14@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 14', 'SENAI-2026-0014', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 7.16, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo15@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 15', 'SENAI-2026-0015', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 6.91, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo16@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 16', 'SENAI-2026-0016', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 7.16, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo17@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 17', 'SENAI-2026-0017', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico ATTENDANCE_BORDERLINE).'
FROM users u WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 6.56, 76.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo18@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 18', 'SENAI-2026-0018', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico ATTENDANCE_BORDERLINE).'
FROM users u WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 6.56, 76.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo19@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 19', 'SENAI-2026-0019', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico ATTENDANCE_BORDERLINE).'
FROM users u WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 6.56, 76.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo20@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 20', 'SENAI-2026-0020', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico AT_RISK).'
FROM users u WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 4.46, 68.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo21@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 21', 'SENAI-2026-0021', 'Estudante fictício anônimo da turma MEC-2026-1 (cenário pedagógico AT_RISK).'
FROM users u WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, 4.57, 68.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo22@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 22', 'SENAI-2026-0022', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 9.73, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo23@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 23', 'SENAI-2026-0023', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 9.23, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo24@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 24', 'SENAI-2026-0024', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 9.38, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo25@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 25', 'SENAI-2026-0025', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico HIGH_PERFORMER).'
FROM users u WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 9.18, 100.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo26@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 26', 'SENAI-2026-0026', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 7.11, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo27@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 27', 'SENAI-2026-0027', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico LATE_DELIVERY).'
FROM users u WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 6.93, 80.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo28@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 28', 'SENAI-2026-0028', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico ATTENDANCE_BORDERLINE).'
FROM users u WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 6.51, 76.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo29@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 29', 'SENAI-2026-0029', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico AT_RISK).'
FROM users u WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 4.35, 68.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo30@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 30', 'SENAI-2026-0030', 'Estudante fictício anônimo da turma MEC-2026-2 (cenário pedagógico AT_RISK).'
FROM users u WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, 4.49, 68.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

-- 2. 12 Aulas Ministradas (class_lessons — DB-021)
INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-02-11', 4, 'Leitura em milímetros e polegadas com paquímetro universal e resolução 0,02mm.', 'Laboratório de Metrologia 01'
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-02-18', 4, 'Medição externa centesimal com micrômetro e inspeção de batimento com relógio comparador.', 'Laboratório de Metrologia 01'
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-02-25', 4, 'Interpretação de vistas ortográficas em 1º diedro, cortes totais e cotagem funcional.', 'Sala de Desenho Técnico 03'
FROM classes cl
JOIN subjects s ON s.code = 'UC-DTM-02'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-03-04', 3, 'Tolerâncias dimensionais ISO 286 (ajustes H7/g6) e simbologia de rugosidade superficial Ra.', 'Sala de Desenho Técnico 03'
FROM classes cl
JOIN subjects s ON s.code = 'UC-DTM-02'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-03-11', 4, 'Setup de torno paralelo convencional, centragem de ferramenta, faceamento e cilindramento.', 'Oficina de Tornearia 02'
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-03-18', 3, 'Fresamento de superfícies planas, esquadrejamento de blocos e rasgos chavetados.', 'Oficina de Fresagem 01'
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-03-25', 3, 'Inspeção pré-operacional de bancada, uso obrigatório de EPIs e bloqueio NR-12.', 'Oficina Integrada SENAI'
FROM classes cl
JOIN subjects s ON s.code = 'UC-SEG-04'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-08-10', 5, 'Fundamentos de metrologia linear com paquímetro e conferência dimensional de peças padrão.', 'Laboratório de Metrologia 01'
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-08-17', 5, 'Leitura de projeções ortográficas ABNT, cortes parciais e interpretação de cotas críticas.', 'Sala de Desenho Técnico 03'
FROM classes cl
JOIN subjects s ON s.code = 'UC-DTM-02'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-08-24', 5, 'Torneamento cilíndrico externo, cálculo de velocidade de corte e controle de avanço.', 'Oficina de Tornearia 02'
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-08-31', 5, 'Operação de fresadora universal, fixação em morsa de precisão e acabamento superficial.', 'Oficina de Fresagem 01'
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

INSERT INTO class_lessons (id, class_id, subject_id, module_id, teacher_id, lesson_date, workload_hours, topic_summary, lab_environment)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, cl.id, s.id, lm.id, u.id, DATE '2026-09-07', 5, 'Procedimentos LOTO, dispositivos de parada de emergência NR-12 e organização 5S.', 'Oficina Integrada SENAI'
FROM classes cl
JOIN subjects s ON s.code = 'UC-SEG-04'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET workload_hours = EXCLUDED.workload_hours, topic_summary = EXCLUDED.topic_summary, lab_environment = EXCLUDED.lab_environment;

-- 3. Registros de Presença e Faltas Variados (attendance_records — DB-022: 100%, 80%, 76% e 68%)
INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso na saída do turno industrial.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso no transporte coletivo.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso no transporte coletivo.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso no transporte coletivo.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso no transporte coletivo.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso no transporte coletivo.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 3, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000001'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000002'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000003'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 4, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000004'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000005'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000006'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000007'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 1, 'Atraso na saída do turno industrial.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 3, 'Saída antecipada sem compensação.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000008'::uuid, e.id, u.id, 'ABSENT'::attendance_status_enum, 5, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000009'::uuid, e.id, u.id, 'LATE'::attendance_status_enum, 3, 'Saída antecipada sem compensação.'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000010'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000011'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

INSERT INTO attendance_records (lesson_id, enrollment_id, student_id, status, absent_hours, justification_note)
SELECT '30000000-0000-4000-8000-000000000012'::uuid, e.id, u.id, 'PRESENT'::attendance_status_enum, 0, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (lesson_id, student_id) DO UPDATE
SET status = EXCLUDED.status, absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note;

-- 4. 6 Tarefas Práticas de Oficina (practical_tasks — DB-023)
INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, lm.id, cl.id, 'Inspeção Dimensional de Pino Calibrado com Paquímetro', 'Realizar 12 medições externas, internas e de profundidade com preenchimento de folha de controle H7.', 'https://cdn.senai.nexa.local/blueprints/pino-calibrado-h7.pdf', TIMESTAMPTZ '2026-02-20T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, lm.id, cl.id, 'Interpretação de Tolerância ISO e Rugosidade em Eixo Motriz', 'Identificar ajustes eixo-furo H7/g6, desvios geométricos e simbologia Ra no desenho técnico.', 'https://cdn.senai.nexa.local/blueprints/eixo-motriz-iso286.pdf', TIMESTAMPTZ '2026-03-08T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-DTM-02'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, lm.id, cl.id, 'Usinagem de Eixo Escalonado Ø25mm em Torno Paralelo', 'Executar faceamento, furo de centro, cilindramento escalonado e acabamento conforme tolerância ±0,02mm.', 'https://cdn.senai.nexa.local/blueprints/eixo-escalonado-25mm.pdf', TIMESTAMPTZ '2026-03-22T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, lm.id, cl.id, 'Fresamento de Bloco Prismático com Rasgo Chavetado', 'Esquadrejar bloco em aço SAE 1020 e fresar rasgo central garantindo paralelismo e segurança NR-12.', 'https://cdn.senai.nexa.local/blueprints/bloco-prismatico-chaveta.pdf', TIMESTAMPTZ '2026-04-05T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, lm.id, cl.id, 'Laudo Metrológico de Bucha Cilíndrica com Paquímetro', 'Conferir diâmetro interno, externo e altura de bucha padronizada registrando incerteza de leitura.', 'https://cdn.senai.nexa.local/blueprints/bucha-cilindrica-met.pdf', TIMESTAMPTZ '2026-08-21T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

INSERT INTO practical_tasks (id, module_id, class_id, title, description, blueprint_url, due_date, max_score, is_mandatory)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, lm.id, cl.id, 'Torneamento de Pino Guia com Chanfro 45° e Controle NR-12', 'Usinar pino guia em torno convencional cumprindo parâmetros de corte, acabamento e checklist EPI.', 'https://cdn.senai.nexa.local/blueprints/pino-guia-45graus.pdf', TIMESTAMPTZ '2026-09-14T22:00:00Z', 10.00, TRUE
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, due_date = EXCLUDED.due_date, max_score = EXCLUDED.max_score;

-- 5. 18 Rubricas / Critérios Técnicos (task_criteria — DB-024)
INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, cp.id, 'Precisão na Leitura com Paquímetro (±0,02mm)', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-MET-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, cp.id, 'Calibração, Zeragem e Conservação do Instrumento', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-MET-04'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, cp.id, 'Organização da Bancada e 5S', 0.50, 3
FROM competencies cp WHERE cp.code = 'COMP-SEG-03'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, cp.id, 'Análise de Ajustes ISO 286 (H7/g6)', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-DTM-02'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, cp.id, 'Leitura de Rugosidade Ra e GD&T', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-DTM-03'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, cp.id, 'Interpretação de Vistas e Cortes ABNT', 0.50, 3
FROM competencies cp WHERE cp.code = 'COMP-DTM-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, cp.id, 'Tolerância Dimensional do Eixo (±0,02mm)', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-02'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, cp.id, 'Acabamento Superficial e Controle de Cavacos', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-04'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, cp.id, 'Uso Obrigatório de EPIs e Segurança NR-12', 0.50, 4
FROM competencies cp WHERE cp.code = 'COMP-SEG-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, cp.id, 'Esquadrejamento e Profundidade do Rasgo', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-03'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, cp.id, 'Cálculo de RPM e Parâmetros de Corte', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, cp.id, 'Bloqueio LOTO e Segurança na Fresadora', 0.50, 4
FROM competencies cp WHERE cp.code = 'COMP-SEG-02'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, cp.id, 'Conferência de Diâmetro Interno e Externo', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-MET-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, cp.id, 'Preenchimento Técnico do Laudo Metrológico', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-MET-04'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, cp.id, 'Conservação e Organização 5S', 0.50, 3
FROM competencies cp WHERE cp.code = 'COMP-SEG-03'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, cp.id, 'Precisão do Pino Guia e Chanfro 45°', 2.00, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-02'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, cp.id, 'Qualidade de Acabamento Superficial', 1.50, 3
FROM competencies cp WHERE cp.code = 'COMP-USI-04'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

INSERT INTO task_criteria (task_id, competency_id, criterion_name, weight, min_acceptable_level)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, cp.id, 'Conformidade EPI e Segurança NR-12', 0.50, 4
FROM competencies cp WHERE cp.code = 'COMP-SEG-01'
ON CONFLICT (task_id, criterion_name) DO UPDATE
SET weight = EXCLUDED.weight, min_acceptable_level = EXCLUDED.min_acceptable_level;

-- 6. Submissões Práticas (task_submissions — DB-025: EVALUATED, SUBMITTED, LATE e PENDING)
INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo01-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo01-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo01-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo01-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo02-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo02-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo02-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo02-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo03-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 4.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo04-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo04-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo05-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo06-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'SUBMITTED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo06-t2.jpg', 'Entrega enviada para conferência do instrutor.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo07-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo07-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo07-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo07-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo08-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo08-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo08-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo08-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo09-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo09-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo09-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo09-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo10-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo10-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo10-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo10-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo11-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo11-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo11-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo11-t4.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo12-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo12-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo13-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo13-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo14-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo14-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo15-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo15-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo16-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo16-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo17-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo17-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo17-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'SUBMITTED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo17-t4.jpg', 'Entrega enviada para conferência do instrutor.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo18-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo18-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo18-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'SUBMITTED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo18-t4.jpg', 'Entrega enviada para conferência do instrutor.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo19-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-08T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo19-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-03-22T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo19-t3.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'SUBMITTED'::submission_status_enum, TIMESTAMPTZ '2026-04-05T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo19-t4.jpg', 'Entrega enviada para conferência do instrutor.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo20-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 4.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-02-20T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo21-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 4.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000004'::uuid, u.id, e.id, 'PENDING'::submission_status_enum, NULL, NULL, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo22-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo22-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo23-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo23-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo24-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo24-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 10.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo25-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo25-t2.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 9.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo26-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo27-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 7.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo28-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 6.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'SUBMITTED'::submission_status_enum, TIMESTAMPTZ '2026-09-14T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo28-t2.jpg', 'Entrega enviada para conferência do instrutor.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo29-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 4.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000005'::uuid, u.id, e.id, 'EVALUATED'::submission_status_enum, TIMESTAMPTZ '2026-08-21T22:00:00Z', 'https://cdn.senai.nexa.local/evidences/demo30-t1.jpg', 'Peça usinada e conferida em bancada com folha de inspeção.', 4.25
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

INSERT INTO task_submissions (task_id, student_id, enrollment_id, status, completed_at, evidence_url, student_notes, final_task_score)
SELECT '31000000-0000-4000-8000-000000000006'::uuid, u.id, e.id, 'LATE'::submission_status_enum, NULL, NULL, 'Entrega atrasada — aguardando reposição em oficina.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
WHERE u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (task_id, student_id) DO UPDATE
SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, evidence_url = EXCLUDED.evidence_url, student_notes = EXCLUDED.student_notes, final_task_score = EXCLUDED.final_task_score;

-- 7. Avaliações por Rubrica dos Professores (submission_evaluations — DB-026)
INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Precisão do Pino Guia e Chanfro 45°'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Qualidade de Acabamento Superficial'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Conformidade EPI e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Esquadrejamento e Profundidade do Rasgo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Cálculo de RPM e Parâmetros de Corte'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000004'::uuid AND tc.criterion_name = 'Bloqueio LOTO e Segurança na Fresadora'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Análise de Ajustes ISO 286 (H7/g6)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Leitura de Rugosidade Ra e GD&T'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000002'::uuid AND tc.criterion_name = 'Interpretação de Vistas e Cortes ABNT'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Tolerância Dimensional do Eixo (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Acabamento Superficial e Controle de Cavacos'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000003'::uuid AND tc.criterion_name = 'Uso Obrigatório de EPIs e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Precisão na Leitura com Paquímetro (±0,02mm)'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Calibração, Zeragem e Conservação do Instrumento'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000001'::uuid AND tc.criterion_name = 'Organização da Bancada e 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Precisão do Pino Guia e Chanfro 45°'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Qualidade de Acabamento Superficial'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Conformidade EPI e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Precisão do Pino Guia e Chanfro 45°'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Qualidade de Acabamento Superficial'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Conformidade EPI e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Precisão do Pino Guia e Chanfro 45°'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Qualidade de Acabamento Superficial'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Conformidade EPI e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Precisão do Pino Guia e Chanfro 45°'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Qualidade de Acabamento Superficial'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 5, 10.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000006'::uuid AND tc.criterion_name = 'Conformidade EPI e Segurança NR-12'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 4, 8.00, 'Execução técnica consistente dentro dos padrões de tolerância SENAI.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conferência de Diâmetro Interno e Externo'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 2, 4.00, 'Desvio acima da tolerância especificada; encaminhar para reforço prático em oficina.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Preenchimento Técnico do Laudo Metrológico'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

INSERT INTO submission_evaluations (submission_id, criterion_id, evaluator_id, achieved_level, score_awarded, technical_feedback)
SELECT ts.id, tc.id, eval_u.id, 3, 6.00, 'Critério atendido no nível mínimo aceitável; reforçar controle dimensional.'
FROM users stu_u
JOIN task_submissions ts ON ts.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND ts.student_id = stu_u.id
JOIN task_criteria tc ON tc.task_id = '31000000-0000-4000-8000-000000000005'::uuid AND tc.criterion_name = 'Conservação e Organização 5S'
JOIN users eval_u ON eval_u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (submission_id, criterion_id) DO UPDATE
SET evaluator_id = EXCLUDED.evaluator_id, achieved_level = EXCLUDED.achieved_level, score_awarded = EXCLUDED.score_awarded, technical_feedback = EXCLUDED.technical_feedback;

-- 8. 4 Avaliações Formativas e Provas (academic_assessments — DB-027)
INSERT INTO academic_assessments (id, class_id, subject_id, module_id, title, assessment_type, weight, application_date, max_grade)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, cl.id, s.id, lm.id, 'Prova Teórica de Leitura de Paquímetro e Micrômetro', 'EXAM'::assessment_type_enum, 2.00, DATE '2026-02-27', 10.00
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, weight = EXCLUDED.weight, application_date = EXCLUDED.application_date, max_grade = EXCLUDED.max_grade;

INSERT INTO academic_assessments (id, class_id, subject_id, module_id, title, assessment_type, weight, application_date, max_grade)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, cl.id, s.id, lm.id, 'Microavaliação de Parâmetros de Corte e Segurança NR-12', 'MICRO_EVALUATION'::assessment_type_enum, 1.00, DATE '2026-03-27', 10.00
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, weight = EXCLUDED.weight, application_date = EXCLUDED.application_date, max_grade = EXCLUDED.max_grade;

INSERT INTO academic_assessments (id, class_id, subject_id, module_id, title, assessment_type, weight, application_date, max_grade)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, cl.id, s.id, lm.id, 'Prova Teórica de Metrologia Dimensional e Tolerâncias', 'EXAM'::assessment_type_enum, 2.00, DATE '2026-08-28', 10.00
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, weight = EXCLUDED.weight, application_date = EXCLUDED.application_date, max_grade = EXCLUDED.max_grade;

INSERT INTO academic_assessments (id, class_id, subject_id, module_id, title, assessment_type, weight, application_date, max_grade)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, cl.id, s.id, lm.id, 'Projeto de Processo de Fabricação em Torno e Fresadora', 'PROJECT'::assessment_type_enum, 1.50, DATE '2026-09-18', 10.00
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, weight = EXCLUDED.weight, application_date = EXCLUDED.application_date, max_grade = EXCLUDED.max_grade;

-- 9. Notas Parciais e Recuperação (student_grades — DB-028)
INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 3.20, 5.40, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 3.85, NULL, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 7.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 5.60, 7.20, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 6.20, NULL, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo09@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo10@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo11@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.90, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo12@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 6.90, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 7.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo13@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 7.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.90, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo15@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 6.90, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 7.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo16@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 5.60, 7.20, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.20, NULL, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo17@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 5.60, 7.20, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.20, NULL, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo18@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 5.60, 7.20, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 6.20, NULL, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 4.50, 5.40, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 3.20, NULL, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000001'::uuid, e.id, stu_u.id, rec_u.id, 3.20, 5.40, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000002'::uuid, e.id, stu_u.id, rec_u.id, 3.85, NULL, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 9.65, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 8.60, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo24@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 8.95, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 9.30, NULL, 'Desempenho excelente na avaliação formativa.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo25@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 7.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo26@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 6.40, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 6.90, NULL, 'Bom aproveitamento teórico; manter regularidade nas entregas práticas.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo27@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 5.60, 7.20, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 6.20, NULL, 'Atenção ao limite de 25% de faltas; recuperação registrada.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo28@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 4.50, 5.40, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 3.20, NULL, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000003'::uuid, e.id, stu_u.id, rec_u.id, 3.20, 5.40, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

INSERT INTO student_grades (assessment_id, enrollment_id, student_id, recorded_by, grade_value, recovery_grade, comments)
SELECT '32000000-0000-4000-8000-000000000004'::uuid, e.id, stu_u.id, rec_u.id, 3.85, NULL, 'Estudante em risco acadêmico; plano de intervenção pedagógica recomendado.'
FROM users stu_u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = stu_u.id AND e.class_id = cl.id
JOIN users rec_u ON rec_u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu_u.email = 'estudante.demo30@aluno.nexa.local'
ON CONFLICT (assessment_id, student_id) DO UPDATE
SET grade_value = EXCLUDED.grade_value, recovery_grade = EXCLUDED.recovery_grade, comments = EXCLUDED.comments;

COMMIT;
