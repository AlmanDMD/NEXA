-- =============================================================================
-- PROJETO NEXA — SEED IDEMPOTENTE LOTE 4: AUTOAVALIAÇÃO, ALERTAS & DIAGNÓSTICOS (DB-040)
-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)
-- 4 Formulários, 20 Autoavaliações, 16 Evidências, 8 Alertas, 10 Diagnósticos, 8 Marcos
-- =============================================================================

BEGIN;

-- 1. Formulários de Autoavaliação (self_assessment_forms — DB-031)
INSERT INTO self_assessment_forms (id, module_id, class_id, title, instructions, opens_at, closes_at, is_active, created_by)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, lm.id, cl.id, 'Autoavaliação — Metrologia com Paquímetro e Tolerância H7 (MEC-2026-1)', 'Avalie honestamente seu nível de domínio (1 a 5) e confiança na leitura de instrumentos metrológicos.', TIMESTAMPTZ '2026-03-01T08:00:00Z', TIMESTAMPTZ '2026-06-30T23:59:59Z', TRUE, u.id
FROM subjects s
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, instructions = EXCLUDED.instructions, opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_active = EXCLUDED.is_active;

INSERT INTO self_assessment_forms (id, module_id, class_id, title, instructions, opens_at, closes_at, is_active, created_by)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, lm.id, cl.id, 'Autoavaliação — Módulo de Tornearia Cilíndrica e NR-12 (MEC-2026-1)', 'Indique seu grau de segurança operacional, cálculo de RPM e domínio do torno convencional.', TIMESTAMPTZ '2026-03-15T08:00:00Z', TIMESTAMPTZ '2026-06-30T23:59:59Z', TRUE, u.id
FROM subjects s
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, instructions = EXCLUDED.instructions, opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_active = EXCLUDED.is_active;

INSERT INTO self_assessment_forms (id, module_id, class_id, title, instructions, opens_at, closes_at, is_active, created_by)
SELECT '40000000-0000-4000-8000-000000000003'::UUID, lm.id, cl.id, 'Autoavaliação — Metrologia Dimensional e Calibração (MEC-2026-2)', 'Registre sua percepção de domínio nas medições lineares com paquímetro e conservação de instrumentos.', TIMESTAMPTZ '2026-08-20T18:00:00Z', TIMESTAMPTZ '2026-12-10T23:59:59Z', TRUE, u.id
FROM subjects s
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, instructions = EXCLUDED.instructions, opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_active = EXCLUDED.is_active;

INSERT INTO self_assessment_forms (id, module_id, class_id, title, instructions, opens_at, closes_at, is_active, created_by)
SELECT '40000000-0000-4000-8000-000000000004'::UUID, lm.id, cl.id, 'Autoavaliação — Tornearia Cilíndrica e Segurança NR-12 (MEC-2026-2)', 'Informe seu domínio prático no faceamento, cilindramento externo e cumprimento da NR-12.', TIMESTAMPTZ '2026-09-01T18:00:00Z', TIMESTAMPTZ '2026-12-10T23:59:59Z', TRUE, u.id
FROM subjects s
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, instructions = EXCLUDED.instructions, opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_active = EXCLUDED.is_active;

-- 2. Respostas de Autoavaliação dos Estudantes (student_self_assessments — DB-032)
INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 5, 5, NULL, TIMESTAMPTZ '2026-03-12T10:15:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 4, 4, NULL, TIMESTAMPTZ '2026-03-12T10:16:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-04'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 2, 2, 'Sinto insegurança ao conferir tolerância H7 em furos internos.', TIMESTAMPTZ '2026-03-13T09:20:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 5, 5, 'Acredito dominar totalmente a leitura do nônio.', TIMESTAMPTZ '2026-03-14T11:00:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 4, 4, NULL, TIMESTAMPTZ '2026-03-14T11:10:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000001'::UUID, u.id, cp.id, 4, 3, 'Aguardando primeira prática de calibração com blocos-padrão.', TIMESTAMPTZ '2026-03-15T08:30:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-04'
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 5, 5, NULL, TIMESTAMPTZ '2026-03-28T10:00:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 2, 2, 'Tenho receio de errar o passe final de acabamento no torno.', TIMESTAMPTZ '2026-03-28T10:15:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 5, 5, 'Faço o cálculo de RPM de cabeça sem dificuldade.', TIMESTAMPTZ '2026-03-29T09:40:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 5, 5, 'Conheço bem todas as regras da NR-12 no torno.', TIMESTAMPTZ '2026-03-29T10:05:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 4, 4, NULL, TIMESTAMPTZ '2026-03-30T11:20:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE u.email = 'estudante.demo07@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000002'::UUID, u.id, cp.id, 3, 3, 'Dúvida na seleção de avanço para aço 1045.', TIMESTAMPTZ '2026-03-30T11:35:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE u.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000003'::UUID, u.id, cp.id, 5, 5, NULL, TIMESTAMPTZ '2026-09-02T20:10:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000003'::UUID, u.id, cp.id, 2, 2, 'Acho que levo tempo demais para conferir medidas com micrômetro.', TIMESTAMPTZ '2026-09-02T20:25:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000003'::UUID, u.id, cp.id, 5, 4, 'Leitura em polegada fracionária já dominada.', TIMESTAMPTZ '2026-09-03T19:45:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000003'::UUID, u.id, cp.id, 3, 3, NULL, TIMESTAMPTZ '2026-09-03T20:00:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-MET-04'
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000004'::UUID, u.id, cp.id, 5, 4, NULL, TIMESTAMPTZ '2026-09-22T20:00:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE u.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000004'::UUID, u.id, cp.id, 5, 5, 'Já usinei eixos parecidos antes.', TIMESTAMPTZ '2026-09-22T20:15:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE u.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000004'::UUID, u.id, cp.id, 2, 2, 'Insegurança no cálculo da profundidade de corte.', TIMESTAMPTZ '2026-09-23T19:50:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE u.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

INSERT INTO student_self_assessments (form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at)
SELECT '40000000-0000-4000-8000-000000000004'::UUID, u.id, cp.id, 4, 4, NULL, TIMESTAMPTZ '2026-09-23T20:10:00Z'
FROM users u
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE u.email = 'estudante.demo23@aluno.nexa.local'
ON CONFLICT (form_id, student_id, competency_id) DO UPDATE
SET perceived_level = EXCLUDED.perceived_level, confidence_score = EXCLUDED.confidence_score, difficulty_notes = EXCLUDED.difficulty_notes, submitted_at = EXCLUDED.submitted_at;

-- 3. Evidências Práticas Verificadas por Docentes (skill_evidences — DB-033)
INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000001'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000001'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.80, tch.id, TIMESTAMPTZ '2026-03-10T11:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000002'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000001'::UUID, 4.60, tch.id, TIMESTAMPTZ '2026-03-11T11:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000003'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000001'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.50, tch.id, TIMESTAMPTZ '2026-03-10T11:30:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000004'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000001'::UUID, 4.30, tch.id, TIMESTAMPTZ '2026-03-11T11:30:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000005'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000001'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 2.40, tch.id, TIMESTAMPTZ '2026-03-10T12:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000006'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000001'::UUID, 2.20, tch.id, TIMESTAMPTZ '2026-03-11T12:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000007'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000001'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 3.80, tch.id, TIMESTAMPTZ '2026-03-10T12:20:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000008'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000003'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.90, tch.id, TIMESTAMPTZ '2026-03-26T11:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-USI-01'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000009'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000003'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.20, tch.id, TIMESTAMPTZ '2026-03-26T11:20:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-USI-01'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000010'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000002'::UUID, 2.30, tch.id, TIMESTAMPTZ '2026-03-27T11:40:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-USI-02'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000011'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000003'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 2.10, tch.id, TIMESTAMPTZ '2026-03-26T12:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000012'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000005'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.70, tch.id, TIMESTAMPTZ '2026-09-01T21:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000013'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000005'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 4.40, tch.id, TIMESTAMPTZ '2026-09-01T21:15:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000014'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000003'::UUID, 2.50, tch.id, TIMESTAMPTZ '2026-09-01T21:30:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-MET-01'
JOIN users tch ON tch.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000015'::UUID, stu.id, cp.id, (SELECT ts.id FROM task_submissions ts WHERE ts.task_id = '31000000-0000-4000-8000-000000000006'::UUID AND ts.student_id = stu.id LIMIT 1), NULL::UUID, 2.60, tch.id, TIMESTAMPTZ '2026-09-21T21:00:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-USI-01'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

INSERT INTO skill_evidences (id, student_id, competency_id, source_submission_id, source_assessment_id, verified_level, verified_by, recorded_at)
SELECT '41000000-0000-4000-8000-000000000016'::UUID, stu.id, cp.id, NULL::UUID, '32000000-0000-4000-8000-000000000004'::UUID, 4.10, tch.id, TIMESTAMPTZ '2026-09-21T21:20:00Z'
FROM users stu
JOIN competencies cp ON cp.code = 'COMP-USI-02'
JOIN users tch ON tch.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE stu.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET verified_level = EXCLUDED.verified_level, verified_by = EXCLUDED.verified_by, recorded_at = EXCLUDED.recorded_at;

-- 4. Alertas Acadêmicos Explicáveis (8 alertas: LOW, MODERATE, HIGH, CRITICAL — DB-034)
INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000001'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-USI-03' AND lm.order_index = 1 LIMIT 1), 'CRITICAL'::risk_level_enum, 'ATTENDANCE'::alert_category_enum, 'Frequência acumulada atingiu 68.00% (8h de faltas não justificadas em 25h ministradas), abaixo do mínimo institucional de 75% do SENAI.', '{"attendance_rate_pct":68,"absent_hours":8,"total_hours":25,"senai_min_pct":75}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-03-28T13:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000002'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-USI-03' AND lm.order_index = 1 LIMIT 1), 'CRITICAL'::risk_level_enum, 'SELF_EVAL_GAP'::alert_category_enum, 'Superestimação crítica em Segurança NR-12 no Torno: aluno declarou nível 5.00, mas evidência prática docente registrou 2.10 (gap +2.90).', '{"competency_code":"COMP-SEG-02","perceived_level":5,"avg_verified_level":2.1,"discrepancy_gap":2.9}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-03-29T14:15:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000003'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'HIGH'::risk_level_enum, 'ATTENDANCE'::alert_category_enum, 'Frequência em 76.00% no limiar preventivo (< 78%); mais 1 falta de 4h colocará o estudante abaixo do mínimo de 75%.', '{"attendance_rate_pct":76,"absent_hours":6,"total_hours":25,"warning_threshold_pct":78}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-03-25T15:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000004'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-USI-03' AND lm.order_index = 1 LIMIT 1), 'HIGH'::risk_level_enum, 'GRADE_DROP'::alert_category_enum, 'Queda de rendimento nas avaliações formativas: média ponderada caiu de 7.40 para 5.20 abaixo da nota de corte (7.00) em Usinagem.', '{"previous_avg":7.4,"current_avg":5.2,"passing_score":7,"drop_points":-2.2}'::JSONB, 'ACKNOWLEDGED'::alert_status_enum, (SELECT u2.id FROM users u2 WHERE u2.email = 'instrutor.oficina.demo@senai.nexa.local' LIMIT 1), 'Agendada revisão prática de parâmetros de corte na próxima oficina.', TIMESTAMPTZ '2026-03-29T16:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo08@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000005'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'MODERATE'::risk_level_enum, 'PENDING_TASKS'::alert_category_enum, '2 entregas práticas em atraso/pendentes na oficina de Metrologia e Desenho Técnico necessitando reagendamento de bancada.', '{"late_tasks":1,"pending_tasks":1,"total_tasks":4}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-03-24T11:30:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000006'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-USI-03' AND lm.order_index = 1 LIMIT 1), 'HIGH'::risk_level_enum, 'SELF_EVAL_GAP'::alert_category_enum, 'Divergência elevada em Tornearia Cilíndrica (MEC-2026-2): autopercepção 5.00 vs. evidência prática docente 2.60 (gap +2.40).', '{"competency_code":"COMP-USI-01","perceived_level":5,"avg_verified_level":2.6,"discrepancy_gap":2.4}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-09-23T21:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000007'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'MODERATE'::risk_level_enum, 'GRADE_DROP'::alert_category_enum, 'Nota parcial de Metrologia Dimensional em 5.80, ligeiramente abaixo da nota de corte (6.00); recomendada prática adicional com micrômetro.', '{"current_avg":5.8,"passing_score":6,"recovery_available":true}'::JSONB, 'ACTIVE'::alert_status_enum, NULL::UUID, NULL, TIMESTAMPTZ '2026-09-10T21:15:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo22@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

INSERT INTO academic_alerts (id, student_id, enrollment_id, class_id, module_id, risk_level, alert_category, explainable_reason, metric_snapshot, status, resolved_by, resolution_notes, created_at)
SELECT '42000000-0000-4000-8000-000000000008'::UUID, stu.id, enr.id, cl.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'LOW'::risk_level_enum, 'PENDING_TASKS'::alert_category_enum, '1 atividade prática com entrega próxima do vencimento; desempenho geral e frequência permanecem saudáveis (88%).', '{"pending_tasks":1,"late_tasks":0,"attendance_rate_pct":88}'::JSONB, 'RESOLVED'::alert_status_enum, (SELECT u2.id FROM users u2 WHERE u2.email = 'instrutor.teoria.demo@senai.nexa.local' LIMIT 1), 'Estudante entregou o laudo metrológico dentro do prazo estendido.', TIMESTAMPTZ '2026-03-18T10:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET risk_level = EXCLUDED.risk_level, explainable_reason = EXCLUDED.explainable_reason, metric_snapshot = EXCLUDED.metric_snapshot, status = EXCLUDED.status, resolved_by = EXCLUDED.resolved_by, resolution_notes = EXCLUDED.resolution_notes;

-- 5. Diagnósticos Explicáveis Comparativos (10 diagnósticos em Metrologia e Tornearia — DB-035)
INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000001'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 2.30, 2.70, 'OVERCONFIDENCE_RISK'::diagnostic_type_enum, 'Divergência de +2.70 pontos em Metrologia (Paquímetro e Tolerância H7): estudante se autoavaliou em 5.00, enquanto 2 evidências docentes (prática + prova) resultaram em média 2.30.', 'Baseado em 2 evidências (1 peça de bancada e 1 prova teórica); autoavaliação isolada não comprova domínio metrológico.', 'Realizar sessão prática assistida de leitura de nônio 0,02 mm com conferência cruzada pelo instrutor.', TIMESTAMPTZ '2026-03-15T14:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000002'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 2.10, 2.90, 'OVERCONFIDENCE_RISK'::diagnostic_type_enum, 'Risco crítico de superestimação em Tornearia / Segurança NR-12: percepção 5.00 contra 2.10 verificado na bancada (gap +2.90).', 'Baseado em 1 avaliação prática de torno convencional; requer nova observação direta de checklist NR-12 antes de operação autônoma.', 'Bloquear operação autônoma do torno até aprovação no checklist presencial de segurança NR-12.', TIMESTAMPTZ '2026-03-30T14:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE stu.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000003'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 2.30, 2.70, 'OVERCONFIDENCE_RISK'::diagnostic_type_enum, 'Divergência de +2.70 pontos em Tornearia (Cálculo de RPM e Avanço): estudante declarou domínio máximo (5.00), mas a microavaliação apontou 2.30.', 'Baseado em 1 microavaliação escrita; confirmar domínio na regulagem da caixa Norton durante a oficina.', 'Aplicar exercícios guiados de velocidade de corte e seleção de engrenagens no torno.', TIMESTAMPTZ '2026-03-30T14:20:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE stu.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000004'::UUID, stu.id, cl.id, lm.id, cp.id, 2.00, 4.40, -2.40, 'UNDERCONFIDENCE_SUPPORT'::diagnostic_type_enum, 'Subestimação em Metrologia (Paquímetro e Tolerância H7): estudante se avaliou em 2.00 apesar de média docente 4.40 (gap -2.40).', 'Baseado em 2 evidências consistentes; indica insegurança percebida mesmo com desempenho técnico sólido.', 'Oferecer feedback positivo com os laudos corrigidos para fortalecer a autoconfiança na bancada.', TIMESTAMPTZ '2026-03-15T14:30:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000005'::UUID, stu.id, cl.id, lm.id, cp.id, 2.00, 4.20, -2.20, 'UNDERCONFIDENCE_SUPPORT'::diagnostic_type_enum, 'Subestimação em Tornearia Cilíndrica: estudante marcou nível 2.00, porém entregou eixo escalonado avaliado em 4.20 (gap -2.20).', 'Baseado em 1 peça usinada avaliada por rubrica; acompanhar confiança nos passes de acabamento.', 'Propor desafio prático progressivo de acabamento com validação imediata de rugosidade.', TIMESTAMPTZ '2026-03-30T14:40:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000006'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 4.70, 0.30, 'ALIGNED'::diagnostic_type_enum, 'Alinhamento excelente em Metrologia: autopercepção 5.00 compatível com média docente 4.70 (gap +0.30).', 'Baseado em 2 evidências (bancada e prova); manter acompanhamento no módulo de micrômetro centesimal.', 'Avançar para desafios de medição avançada e monitoria entre pares na oficina.', TIMESTAMPTZ '2026-03-15T15:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000007'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 4.90, 0.10, 'ALIGNED'::diagnostic_type_enum, 'Alinhamento consistente em Tornearia Cilíndrica: autopercepção 5.00 e avaliação docente 4.90 (gap +0.10).', 'Baseado na peça prática de torneamento externo avaliada com rubrica completa.', 'Liberar avanço para o módulo de Fresamento de Superfícies Planas e Rasgos.', TIMESTAMPTZ '2026-03-30T15:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000008'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 2.50, 2.50, 'OVERCONFIDENCE_RISK'::diagnostic_type_enum, 'Superestimação em Metrologia Dimensional (MEC-2026-2): percepção 5.00 versus evidência docente 2.50 (gap +2.50).', 'Baseado em 1 avaliação teórica; complementar com checagem prática de leitura de paquímetro na oficina.', 'Agendar bancada de reforço de leitura de paquímetro em milímetros e polegadas.', TIMESTAMPTZ '2026-09-05T21:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE stu.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000009'::UUID, stu.id, cl.id, lm.id, cp.id, 5.00, 2.60, 2.40, 'OVERCONFIDENCE_RISK'::diagnostic_type_enum, 'Superestimação em Tornearia Cilíndrica (MEC-2026-2): autopercepção 5.00 frente a 2.60 na peça avaliada (gap +2.40).', 'Baseado na entrega prática do pino guia; desvios dimensionais acima da tolerância especificada.', 'Revisar alinhamento de contraponta e conferência intermediária com micrômetro antes do passe final.', TIMESTAMPTZ '2026-09-24T21:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE stu.email = 'estudante.demo21@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

INSERT INTO explainable_diagnostics (id, student_id, class_id, module_id, competency_id, self_perceived_level, teacher_verified_level, discrepancy_gap, diagnostic_type, explanation_text, limitations_note, recommended_action, generated_at)
SELECT '43000000-0000-4000-8000-000000000010'::UUID, stu.id, cl.id, lm.id, cp.id, 2.00, 4.40, -2.40, 'UNDERCONFIDENCE_SUPPORT'::diagnostic_type_enum, 'Subestimação em Metrologia (MEC-2026-2): estudante declarou nível 2.00, mas obteve 4.40 na entrega prática (gap -2.40).', 'Baseado em 1 entrega prática com excelente precisão; reforçar confiança na execução sob tempo.', 'Destacar a acurácia alcançada no laudo metrológico e estimular participação ativa em equipe.', TIMESTAMPTZ '2026-09-05T21:30:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE stu.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET self_perceived_level = EXCLUDED.self_perceived_level, teacher_verified_level = EXCLUDED.teacher_verified_level, discrepancy_gap = EXCLUDED.discrepancy_gap, diagnostic_type = EXCLUDED.diagnostic_type, explanation_text = EXCLUDED.explanation_text, limitations_note = EXCLUDED.limitations_note, recommended_action = EXCLUDED.recommended_action;

-- 6. Histórico e Linha do Tempo de Marcos Acadêmicos (student_milestone_history — DB-039)
INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000001'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'MODULE_COMPLETED'::milestone_type_enum, 'Módulo de Metrologia com Paquímetro Concluído com Excelência', 'Concluiu todas as práticas de medição linear e tolerância H7 acima da nota de corte.', '{"final_module_score":9.4,"passing_score":6}'::JSONB, TIMESTAMPTZ '2026-03-12T12:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000002'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-USI-03' AND lm.order_index = 1 LIMIT 1), 'SKILL_LEVEL_UP'::milestone_type_enum, 'Evolução para Nível 5 em Tornearia Cilíndrica', 'Atingiu domínio avançado (nível 4.90) na usinagem de eixos escalonados em torno convencional.', '{"competency_code":"COMP-USI-01","verified_level":4.9}'::JSONB, TIMESTAMPTZ '2026-03-28T12:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000003'::UUID, stu.id, enr.id, NULL::UUID, 'PERFECT_ATTENDANCE'::milestone_type_enum, '100% de Presença nas Oficinas do 1º Trimestre', 'Nenhuma falta registrada em todas as 25 horas de laboratório ministradas até o momento.', '{"attendance_rate_pct":100,"total_hours":25}'::JSONB, TIMESTAMPTZ '2026-03-31T17:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000004'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'SKILL_LEVEL_UP'::milestone_type_enum, 'Progresso Verificado em Metrologia (Nível 4.40)', 'Demonstrou alta precisão em leituras com paquímetro e conferência de tolerância ISO.', '{"competency_code":"COMP-MET-01","verified_level":4.4}'::JSONB, TIMESTAMPTZ '2026-03-14T12:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000005'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'RECOVERY_ACHIEVED'::milestone_type_enum, 'Recuperação Concluída em Metrologia Dimensional', 'Elevou o desempenho na avaliação de recuperação superando a nota de corte institucional.', '{"previous_grade":5.5,"recovery_grade":7.8}'::JSONB, TIMESTAMPTZ '2026-03-22T15:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000006'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'MODULE_COMPLETED'::milestone_type_enum, 'Módulo de Metrologia Concluído (Turma Noite)', 'Completou todas as práticas de medição dimensional com desempenho de destaque.', '{"final_module_score":9.1,"passing_score":6}'::JSONB, TIMESTAMPTZ '2026-09-05T22:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000007'::UUID, stu.id, enr.id, NULL::UUID, 'PERFECT_ATTENDANCE'::milestone_type_enum, 'Frequência Exemplar (100%) no Turno Noturno', 'Assiduidade integral em todas as aulas presenciais de laboratório da turma MEC-2026-2.', '{"attendance_rate_pct":100,"total_hours":25}'::JSONB, TIMESTAMPTZ '2026-09-25T22:00:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo19@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

INSERT INTO student_milestone_history (id, student_id, enrollment_id, module_id, milestone_type, title, description, metadata, achieved_at)
SELECT '44000000-0000-4000-8000-000000000008'::UUID, stu.id, enr.id, (SELECT lm.id FROM learning_modules lm JOIN subjects s ON s.id = lm.subject_id WHERE s.code = 'UC-MET-01' AND lm.order_index = 1 LIMIT 1), 'SKILL_LEVEL_UP'::milestone_type_enum, 'Alta Acurácia Metrológica Validada na Bancada', 'Atingiu nível 4.40 em medições com paquímetro e laudo dimensional.', '{"competency_code":"COMP-MET-01","verified_level":4.4}'::JSONB, TIMESTAMPTZ '2026-09-06T21:30:00Z'
FROM users stu
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments enr ON enr.student_id = stu.id AND enr.class_id = cl.id
WHERE stu.email = 'estudante.demo20@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET milestone_type = EXCLUDED.milestone_type, title = EXCLUDED.title, description = EXCLUDED.description, metadata = EXCLUDED.metadata, achieved_at = EXCLUDED.achieved_at;

COMMIT;
