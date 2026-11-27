-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: VIEW DESEMPENHO 360° (DB-036)
-- Versão: 20261126030000_create_vw_student_360_performance
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Cria a View analítica consolidada `vw_student_360_performance` (EPIC-05:
-- Dashboard Híbrido do Professor & Visão 360° — Sprint S4 / Lote 4) agregando
-- por matrícula (`enrollment_id`):
-- 1. Dados do estudante (`users` + `user_profiles`) e da turma (`classes`).
-- 2. Média geral ponderada (`weighted_average_grade`) considerando a maior nota
--    entre `grade_value` e `recovery_grade` ponderada por `academic_assessments.weight`.
-- 3. Percentual atualizado de frequência (`attendance_rate_pct`).
-- 4. Contadores precisos de tarefas práticas por status (`PENDING`, `SUBMITTED`,
--    `EVALUATED`, `LATE`) sem multiplicação cartesiana via CTEs pré-agregadas.
-- 5. Quantidade de alertas ativos (`active_alerts_count`) e maior nível de
--    risco atual (`current_risk_level`), otimizado para < 30ms em turmas de até
--    50 alunos (validável via EXPLAIN ANALYZE).
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW vw_student_360_performance AS
WITH grade_agg AS (
    SELECT
        sg.enrollment_id,
        ROUND(
            SUM(GREATEST(sg.grade_value, COALESCE(sg.recovery_grade, sg.grade_value)) * aa.weight)
            / NULLIF(SUM(aa.weight), 0),
            2
        ) AS weighted_average_grade,
        COUNT(*)::INTEGER AS graded_assessments_count
    FROM student_grades sg
    INNER JOIN academic_assessments aa ON aa.id = sg.assessment_id
    GROUP BY sg.enrollment_id
),
attendance_agg AS (
    SELECT
        ar.enrollment_id,
        COALESCE(SUM(cl.workload_hours), 0)::INTEGER AS total_lesson_hours,
        COALESCE(
            SUM(CASE WHEN ar.status IN ('ABSENT', 'LATE') THEN ar.absent_hours ELSE 0 END),
            0
        )::INTEGER AS unjustified_absent_hours,
        COALESCE(
            SUM(CASE WHEN ar.status = 'JUSTIFIED' THEN ar.absent_hours ELSE 0 END),
            0
        )::INTEGER AS justified_absent_hours
    FROM attendance_records ar
    INNER JOIN class_lessons cl ON cl.id = ar.lesson_id
    GROUP BY ar.enrollment_id
),
task_agg AS (
    SELECT
        ts.enrollment_id,
        COUNT(*)::INTEGER AS tasks_total,
        COUNT(*) FILTER (WHERE ts.status = 'PENDING')::INTEGER AS tasks_pending,
        COUNT(*) FILTER (WHERE ts.status = 'SUBMITTED')::INTEGER AS tasks_submitted,
        COUNT(*) FILTER (WHERE ts.status = 'EVALUATED')::INTEGER AS tasks_evaluated,
        COUNT(*) FILTER (WHERE ts.status = 'LATE')::INTEGER AS tasks_late,
        ROUND(AVG(ts.final_task_score) FILTER (WHERE ts.final_task_score IS NOT NULL), 2) AS avg_practical_score
    FROM task_submissions ts
    GROUP BY ts.enrollment_id
),
alert_agg AS (
    SELECT
        al.enrollment_id,
        COUNT(*) FILTER (WHERE al.status = 'ACTIVE')::INTEGER AS active_alerts_count,
        CASE MAX(
            CASE
                WHEN al.status = 'ACTIVE' THEN
                    CASE al.risk_level
                        WHEN 'CRITICAL' THEN 4
                        WHEN 'HIGH' THEN 3
                        WHEN 'MODERATE' THEN 2
                        WHEN 'LOW' THEN 1
                        ELSE 0
                    END
                ELSE 0
            END
        )
            WHEN 4 THEN 'CRITICAL'::risk_level_enum
            WHEN 3 THEN 'HIGH'::risk_level_enum
            WHEN 2 THEN 'MODERATE'::risk_level_enum
            ELSE 'LOW'::risk_level_enum
        END AS current_risk_level
    FROM academic_alerts al
    GROUP BY al.enrollment_id
)
SELECT
    e.id AS enrollment_id,
    e.student_id,
    up.full_name AS student_name,
    up.registration_number,
    u.email AS student_email,
    e.class_id,
    c.code AS class_code,
    c.period AS class_period,
    c.status AS class_status,
    e.status AS enrollment_status,
    COALESCE(ga.weighted_average_grade, e.final_grade) AS weighted_average_grade,
    COALESCE(ga.graded_assessments_count, 0) AS graded_assessments_count,
    ta.avg_practical_score,
    CASE
        WHEN COALESCE(att.total_lesson_hours, 0) > 0 THEN
            ROUND(
                ((att.total_lesson_hours - att.unjustified_absent_hours)::NUMERIC / att.total_lesson_hours::NUMERIC) * 100.00,
                2
            )
        ELSE COALESCE(e.attendance_rate, 100.00)
    END AS attendance_rate_pct,
    COALESCE(att.total_lesson_hours, 0) AS total_lesson_hours,
    COALESCE(att.unjustified_absent_hours, 0) AS unjustified_absent_hours,
    COALESCE(att.justified_absent_hours, 0) AS justified_absent_hours,
    COALESCE(ta.tasks_total, 0) AS tasks_total,
    COALESCE(ta.tasks_pending, 0) AS tasks_pending,
    COALESCE(ta.tasks_submitted, 0) AS tasks_submitted,
    COALESCE(ta.tasks_evaluated, 0) AS tasks_evaluated,
    COALESCE(ta.tasks_late, 0) AS tasks_late,
    (COALESCE(ta.tasks_submitted, 0) + COALESCE(ta.tasks_evaluated, 0)) AS tasks_completed,
    COALESCE(aa.active_alerts_count, 0) AS active_alerts_count,
    COALESCE(aa.current_risk_level, 'LOW'::risk_level_enum) AS current_risk_level
FROM enrollments e
INNER JOIN users u ON u.id = e.student_id
LEFT JOIN user_profiles up ON up.user_id = u.id
INNER JOIN classes c ON c.id = e.class_id
LEFT JOIN grade_agg ga ON ga.enrollment_id = e.id
LEFT JOIN attendance_agg att ON att.enrollment_id = e.id
LEFT JOIN task_agg ta ON ta.enrollment_id = e.id
LEFT JOIN alert_agg aa ON aa.enrollment_id = e.id;

COMMENT ON VIEW vw_student_360_performance IS
    'View analítica 360° consolidada por matrícula (DB-036): média ponderada, frequência atualizada, contadores PENDING/SUBMITTED/EVALUATED/LATE, alertas ativos e nível de risco atual (< 30ms para turmas <= 50 alunos).';

COMMIT;
