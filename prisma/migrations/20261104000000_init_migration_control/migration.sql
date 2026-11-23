-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA INICIAL (DB-004)
-- Versão: 20261104000000_init_migration_control
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo (gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de controle de versão de migrations SQL (snake_case)
CREATE TABLE IF NOT EXISTS schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(100) NOT NULL,
    migration_name VARCHAR(255) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    applied_by VARCHAR(100) NOT NULL DEFAULT 'docker-sql-runner',
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_schema_migrations_version UNIQUE (version),
    CONSTRAINT chk_schema_migrations_exec_time CHECK (execution_time_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
    ON schema_migrations (applied_at DESC);

COMMIT;
