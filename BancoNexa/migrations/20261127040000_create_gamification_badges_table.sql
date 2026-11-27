-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA gamification_badges (DB-045)
-- Versão: 20261127040000_create_gamification_badges_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-015 (competencies)
-- =============================================================================
-- Catálogo transparente de insígnias (badges) pedagógicas e recompensas de XP
-- baseadas no domínio de competências técnicas SENAI e assiduidade, sem
-- rankings punitivos.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS gamification_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(60) NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    criteria_explanation TEXT NOT NULL,
    icon_name VARCHAR(80) NOT NULL,
    xp_reward INTEGER NOT NULL DEFAULT 50,
    competency_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_gamification_badges_code UNIQUE (code),
    CONSTRAINT chk_gamification_badges_code_format
        CHECK (code ~ '^[A-Z0-9][A-Z0-9_-]{2,59}$'),
    CONSTRAINT chk_gamification_badges_title_not_empty
        CHECK (CHAR_LENGTH(BTRIM(title)) >= 3),
    CONSTRAINT chk_gamification_badges_description_not_empty
        CHECK (CHAR_LENGTH(BTRIM(description)) >= 10),
    CONSTRAINT chk_gamification_badges_criteria_not_empty
        CHECK (CHAR_LENGTH(BTRIM(criteria_explanation)) >= 15),
    CONSTRAINT chk_gamification_badges_icon_not_empty
        CHECK (CHAR_LENGTH(BTRIM(icon_name)) >= 2),
    CONSTRAINT chk_gamification_badges_xp_positive
        CHECK (xp_reward > 0 AND xp_reward <= 5000),
    CONSTRAINT fk_gamification_badges_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gamification_badges_active_competency
    ON gamification_badges USING BTREE (is_active, competency_id);

CREATE INDEX IF NOT EXISTS idx_gamification_badges_xp
    ON gamification_badges USING BTREE (xp_reward DESC);

COMMENT ON TABLE gamification_badges IS
    '[DB-045] Catálogo transparente de conquistas técnicas SENAI e níveis pedagógicos de XP (sem ranking punitivo).';
COMMENT ON COLUMN gamification_badges.criteria_explanation IS
    'Regra pública e explicável que detalha exatamente como o estudante conquista a insígnia.';

COMMIT;
