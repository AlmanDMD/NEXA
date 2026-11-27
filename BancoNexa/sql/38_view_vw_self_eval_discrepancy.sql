-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: VIEW DISCREPÂNCIA (DB-038)
-- Versão: 20261126050000_create_vw_self_eval_discrepancy
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Cria a View analítica `vw_self_eval_discrepancy` (EPIC-07: Autoavaliação &
-- Motor de Diagnóstico Explicável — Sprint S4 / Lote 4) cruzando
-- `student_self_assessments` (DB-032) com a média das evidências verificadas
-- em `skill_evidences` (DB-033) por `(student_id, competency_id)`:
-- 1. Retorna lado a lado: `perceived_level`, `avg_verified_level`,
--    `evidence_count` e `discrepancy_delta = perceived_level - avg_verified_level`.
-- 2. Classifica divergências >= 1.50 pontos para revisão pedagógica:
--    - `OVERCONFIDENCE_RISK` (delta >= 1.50: superestimação / risco técnico/segurança)
--    - `UNDERCONFIDENCE_SUPPORT` (delta <= -1.50: subestimação / insegurança)
--    - `INSUFFICIENT_EVIDENCE` (evidence_count = 0)
--    - `ALIGNED` (|delta| < 1.50 com evidência docente)
-- 3. Otimizada para os gráficos radar (`FE-038`), comparativo (`FE-042`) e
--    serviços de diagnóstico explicável (`BE-037` / `BE-038`).
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW vw_self_eval_discrepancy AS
WITH evidence_agg AS (
    SELECT
        se.student_id,
        se.competency_id,
        ROUND(AVG(se.verified_level), 2) AS avg_verified_level,
        COUNT(se.id)::INTEGER AS evidence_count,
        MAX(se.recorded_at) AS last_evidence_at
    FROM skill_evidences se
    GROUP BY se.student_id, se.competency_id
)
SELECT
    ssa.id AS self_assessment_id,
    ssa.form_id,
    saf.class_id,
    saf.module_id,
    lm.title AS module_title,
    ssa.student_id,
    up.full_name AS student_name,
    ssa.competency_id,
    cp.code AS competency_code,
    cp.title AS competency_title,
    cp.category AS competency_category,
    ssa.perceived_level::NUMERIC(3,2) AS perceived_level,
    ssa.confidence_score,
    ea.avg_verified_level,
    COALESCE(ea.evidence_count, 0) AS evidence_count,
    CASE
        WHEN COALESCE(ea.evidence_count, 0) = 0 THEN NULL::NUMERIC(3,2)
        ELSE ROUND(ssa.perceived_level::NUMERIC - ea.avg_verified_level, 2)
    END AS discrepancy_delta,
    CASE
        WHEN COALESCE(ea.evidence_count, 0) = 0 THEN 'INSUFFICIENT_EVIDENCE'::diagnostic_type_enum
        WHEN (ssa.perceived_level::NUMERIC - ea.avg_verified_level) >= 1.50 THEN 'OVERCONFIDENCE_RISK'::diagnostic_type_enum
        WHEN (ssa.perceived_level::NUMERIC - ea.avg_verified_level) <= -1.50 THEN 'UNDERCONFIDENCE_SUPPORT'::diagnostic_type_enum
        ELSE 'ALIGNED'::diagnostic_type_enum
    END AS diagnostic_classification,
    (
        COALESCE(ea.evidence_count, 0) = 0
        OR ABS(ssa.perceived_level::NUMERIC - ea.avg_verified_level) >= 1.50
    ) AS requires_pedagogical_review,
    ssa.difficulty_notes,
    ssa.submitted_at,
    ea.last_evidence_at
FROM student_self_assessments ssa
INNER JOIN self_assessment_forms saf ON saf.id = ssa.form_id
INNER JOIN learning_modules lm ON lm.id = saf.module_id
INNER JOIN competencies cp ON cp.id = ssa.competency_id
LEFT JOIN user_profiles up ON up.user_id = ssa.student_id
LEFT JOIN evidence_agg ea
    ON ea.student_id = ssa.student_id
   AND ea.competency_id = ssa.competency_id;

COMMENT ON VIEW vw_self_eval_discrepancy IS
    'View de discrepância Autoavaliação vs. Avaliação Docente (DB-038): cruza student_self_assessments e skill_evidences por (student_id, competency_id) classificando divergências >= 1.50 em OVERCONFIDENCE_RISK ou UNDERCONFIDENCE_SUPPORT.';

COMMIT;
