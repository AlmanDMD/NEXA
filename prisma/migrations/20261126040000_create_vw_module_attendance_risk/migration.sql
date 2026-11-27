-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: VIEW RISCO DE FALTAS (DB-037)
-- Versão: 20261126040000_create_vw_module_attendance_risk
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Cria a View analítica `vw_module_attendance_risk` (EPIC-05: Dashboard Híbrido
-- do Professor & Visão 360° — Sprint S4 / Lote 4) para monitoramento precoce de
-- risco de reprovação por faltas (< 75% mínimo SENAI; alerta preventivo < 78%):
-- 1. Trata divisão por zero quando nenhuma aula foi ministrada ainda no módulo
--    (retornando 100.00% de frequência e `is_attendance_critical = FALSE`).
-- 2. Separa faltas justificadas (`JUSTIFIED`) de faltas não justificadas
--    (`ABSENT`, `LATE`), preservando transparência pedagógica e legal.
-- 3. Expõe `is_attendance_critical` (`attendance_percentage < 78.00`) para o
--    motor de alertas (`BE-032`) e o indicador visual de 75% (`FE-023`).
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW vw_module_attendance_risk AS
WITH module_lessons AS (
    SELECT
        cl.class_id,
        cl.subject_id,
        cl.module_id,
        COUNT(cl.id)::INTEGER AS lessons_count,
        COALESCE(SUM(cl.workload_hours), 0)::INTEGER AS total_hours_taught
    FROM class_lessons cl
    WHERE cl.module_id IS NOT NULL
    GROUP BY cl.class_id, cl.subject_id, cl.module_id
),
student_module_attendance AS (
    SELECT
        ar.enrollment_id,
        ar.student_id,
        cl.class_id,
        cl.subject_id,
        cl.module_id,
        COALESCE(
            SUM(CASE WHEN ar.status IN ('ABSENT', 'LATE') THEN ar.absent_hours ELSE 0 END),
            0
        )::INTEGER AS unjustified_absent_hours,
        COALESCE(
            SUM(CASE WHEN ar.status = 'JUSTIFIED' THEN ar.absent_hours ELSE 0 END),
            0
        )::INTEGER AS justified_absent_hours,
        COALESCE(SUM(ar.absent_hours), 0)::INTEGER AS total_absent_hours
    FROM attendance_records ar
    INNER JOIN class_lessons cl ON cl.id = ar.lesson_id
    WHERE cl.module_id IS NOT NULL
    GROUP BY ar.enrollment_id, ar.student_id, cl.class_id, cl.subject_id, cl.module_id
),
base_calc AS (
    SELECT
        e.id AS enrollment_id,
        e.student_id,
        e.class_id,
        s.id AS subject_id,
        s.code AS subject_code,
        s.name AS subject_name,
        lm.id AS module_id,
        lm.title AS module_title,
        lm.order_index AS module_order_index,
        COALESCE(ml.lessons_count, 0) AS lessons_count,
        COALESCE(ml.total_hours_taught, 0) AS total_hours_taught,
        COALESCE(sma.unjustified_absent_hours, 0) AS unjustified_absent_hours,
        COALESCE(sma.justified_absent_hours, 0) AS justified_absent_hours,
        COALESCE(sma.total_absent_hours, 0) AS total_absent_hours,
        GREATEST(COALESCE(ml.total_hours_taught, 0) - COALESCE(sma.total_absent_hours, 0), 0) AS present_hours,
        CASE
            WHEN COALESCE(ml.total_hours_taught, 0) = 0 THEN 100.00::NUMERIC(5,2)
            ELSE ROUND(
                (GREATEST(ml.total_hours_taught - COALESCE(sma.unjustified_absent_hours, 0), 0)::NUMERIC
                 / ml.total_hours_taught::NUMERIC) * 100.00,
                2
            )
        END AS attendance_percentage,
        CASE
            WHEN COALESCE(ml.total_hours_taught, 0) = 0 THEN 100.00::NUMERIC(5,2)
            ELSE ROUND(
                (GREATEST(ml.total_hours_taught - COALESCE(sma.total_absent_hours, 0), 0)::NUMERIC
                 / ml.total_hours_taught::NUMERIC) * 100.00,
                2
            )
        END AS raw_attendance_percentage
    FROM enrollments e
    INNER JOIN classes c ON c.id = e.class_id
    INNER JOIN subjects s ON s.course_id = c.course_id
    INNER JOIN learning_modules lm ON lm.subject_id = s.id
    LEFT JOIN module_lessons ml
        ON ml.class_id = e.class_id
       AND ml.subject_id = s.id
       AND ml.module_id = lm.id
    LEFT JOIN student_module_attendance sma
        ON sma.enrollment_id = e.id
       AND sma.module_id = lm.id
)
SELECT
    enrollment_id,
    student_id,
    class_id,
    subject_id,
    subject_code,
    subject_name,
    module_id,
    module_title,
    module_order_index,
    lessons_count,
    total_hours_taught,
    present_hours,
    unjustified_absent_hours,
    justified_absent_hours,
    total_absent_hours,
    attendance_percentage,
    raw_attendance_percentage,
    (attendance_percentage < 78.00) AS is_attendance_critical,
    (attendance_percentage < 75.00) AS is_below_senai_minimum
FROM base_calc;

COMMENT ON VIEW vw_module_attendance_risk IS
    'View analítica de frequência e evasão por módulo (DB-037): trata divisão por zero (100.00%), separa faltas JUSTIFIED das não justificadas e sinaliza is_attendance_critical quando frequência < 78%.';

COMMIT;
