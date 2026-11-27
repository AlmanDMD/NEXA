-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: ALERTAS ACADÊMICOS (DB-034)
-- Versão: 20261126010000_create_academic_alerts_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `academic_alerts` (EPIC-05: Dashboard Híbrido do Professor
-- & Visão 360° — Sprint S4 / Lote 4) para armazenar alertas precoces, explicáveis
-- e pedagógicos de apoio ao docente/coordenação (nunca rótulos permanentes ao
-- estudante), desbloqueando `DB-035`, `DB-036` (`vw_student_360_performance`),
-- `DB-040`, `BE-032`, `BE-033` e `FE-032`:
-- 1. Campo `explainable_reason TEXT NOT NULL` obrigatório detalhando de forma
--    transparente os dados e a regra pedagógica disparada.
-- 2. Campo `metric_snapshot JSONB NOT NULL` (objeto JSON validado + índice GIN)
--    preservando os indicadores exatos do momento da geração do alerta.
-- 3. Índice composto `idx_academic_alerts_class_status_risk` em
--    `(class_id, status, risk_level)` para ordenação de prioridade no dashboard.
-- 4. Enums nativos `risk_level_enum`, `alert_category_enum` e `alert_status_enum`
--    (DB-005) com guardas idempotentes e trigger de integridade referencial/perfil.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e enums nativos (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_category_enum AS ENUM ('ATTENDANCE', 'GRADE_DROP', 'PENDING_TASKS', 'SELF_EVAL_GAP');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status_enum AS ENUM ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela de alertas e indicadores de risco (`academic_alerts`)
CREATE TABLE IF NOT EXISTS academic_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    class_id UUID NOT NULL,
    module_id UUID,
    risk_level risk_level_enum NOT NULL,
    alert_category alert_category_enum NOT NULL,
    explainable_reason TEXT NOT NULL,
    metric_snapshot JSONB NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'ACTIVE',
    resolved_by UUID,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Critério de Aceitação 1: Razão explicável obrigatória e informativa
    CONSTRAINT chk_academic_alerts_reason_not_empty CHECK (
        CHAR_LENGTH(BTRIM(explainable_reason)) >= 10
    ),

    -- Critério de Aceitação 2: Snapshot de métricas em JSONB válido (objeto JSON)
    CONSTRAINT chk_academic_alerts_metric_snapshot_object CHECK (
        jsonb_typeof(metric_snapshot) = 'object'
    ),

    -- Integridade referencial estrita (ON DELETE RESTRICT no histórico acadêmico; SET NULL em resolved_by)
    CONSTRAINT fk_academic_alerts_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_academic_alerts_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_academic_alerts_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_academic_alerts_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_academic_alerts_resolver
        FOREIGN KEY (resolved_by) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice em (class_id, status, risk_level) e índices complementares
CREATE INDEX IF NOT EXISTS idx_academic_alerts_class_status_risk
    ON academic_alerts USING BTREE (class_id, status, risk_level);

CREATE INDEX IF NOT EXISTS idx_academic_alerts_student_status
    ON academic_alerts USING BTREE (student_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_academic_alerts_enrollment_status
    ON academic_alerts USING BTREE (enrollment_id, status);

CREATE INDEX IF NOT EXISTS idx_academic_alerts_module
    ON academic_alerts USING BTREE (module_id)
    WHERE module_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_academic_alerts_metric_snapshot_gin
    ON academic_alerts USING GIN (metric_snapshot);

-- 4. Função e Trigger PL/pgSQL para validar matrícula/turma/estudante e perfil do resolvedor
CREATE OR REPLACE FUNCTION fn_academic_alerts_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_enr_student_id UUID;
    v_enr_class_id UUID;
    v_resolver_role user_role_enum;
BEGIN
    NEW.explainable_reason := BTRIM(NEW.explainable_reason);

    IF NEW.resolution_notes IS NOT NULL THEN
        NEW.resolution_notes := BTRIM(NEW.resolution_notes);
    END IF;

    -- 4.1. Garantir coerência entre enrollment_id, student_id e class_id
    SELECT e.student_id, e.class_id
      INTO v_enr_student_id, v_enr_class_id
      FROM enrollments e
     WHERE e.id = NEW.enrollment_id;

    IF FOUND AND (v_enr_student_id <> NEW.student_id OR v_enr_class_id <> NEW.class_id) THEN
        RAISE EXCEPTION
            'Inconsistência de matrícula no alerta: enrollment % pertence ao estudante % / turma %, divergindo de student % / turma %.',
            NEW.enrollment_id, v_enr_student_id, v_enr_class_id, NEW.student_id, NEW.class_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_academic_alerts_enrollment_coherence';
    END IF;

    -- 4.2. Garantir que resolved_by (quando informado) não seja um estudante
    IF NEW.resolved_by IS NOT NULL THEN
        SELECT u.role
          INTO v_resolver_role
          FROM users u
         WHERE u.id = NEW.resolved_by;

        IF FOUND AND v_resolver_role = 'STUDENT' THEN
            RAISE EXCEPTION
                'Permissão inválida: o usuário % possui role "STUDENT" e não pode resolver alertas acadêmicos.',
                NEW.resolved_by
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_academic_alerts_resolver_role';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_academic_alerts_validate_integrity ON academic_alerts;

CREATE TRIGGER trg_academic_alerts_validate_integrity
    BEFORE INSERT OR UPDATE ON academic_alerts
    FOR EACH ROW
    EXECUTE FUNCTION fn_academic_alerts_validate_integrity();

-- 5. Metadados de catálogo PostgreSQL (COMMENT ON)
COMMENT ON TABLE academic_alerts IS
    'Alertas precoces e explicáveis de risco acadêmico com snapshot JSONB de métricas (DB-034). Indicadores pedagógicos de apoio ao docente (BE-032 / vw_student_360_performance).';

COMMENT ON CONSTRAINT chk_academic_alerts_reason_not_empty ON academic_alerts IS
    'Regra DB-034: exige justificativa explicável transparente (explainable_reason >= 10 chars) descrevendo os dados e a regra disparada.';

COMMENT ON CONSTRAINT chk_academic_alerts_metric_snapshot_object ON academic_alerts IS
    'Regra DB-034: exige metric_snapshot em formato de objeto JSONB com os indicadores exatos do momento do disparo.';

COMMIT;
