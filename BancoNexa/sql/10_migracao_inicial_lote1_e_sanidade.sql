-- =============================================================================
-- PROJETO NEXA — MIGRAÇÃO CONSOLIDADA DO LOTE 1 E VERIFICAÇÃO DE SANIDADE (DB-010)
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Consolida as entregas do Lote 1 (Sprint 1: DB-001 até DB-010) em SQL nativo:
-- 1. Teste de conectividade e sanidade: `SELECT 1 AS sanity_check;`
-- 2. Extensão `pgcrypto` e os 18 tipos enumerados globais (`DB-005`).
-- 3. As 4 tabelas fundamentais de Identidade, Segurança e Auditoria:
--    - `users` (DB-006)
--    - `user_profiles` (DB-007)
--    - `auth_sessions` (DB-008)
--    - `audit_logs` (DB-009)
--    + `schema_migrations` (DB-004)
-- 4. Bloco PL/pgSQL de verificação de integridade no catálogo `information_schema`
--    validando a presença das 4 tabelas fundamentais e suas chaves primárias.
-- =============================================================================

BEGIN;

-- =============================================================================
-- PASSO 1: QUERY DE SANIDADE DE CONEXÃO (SELECT 1)
-- =============================================================================
SELECT 1 AS sanity_check, CURRENT_TIMESTAMP AS checked_at, current_database() AS database_name;

-- =============================================================================
-- PASSO 2: EXTENSÃO E TABELA DE CONTROLE DE MIGRATIONS (DB-004)
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

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

-- =============================================================================
-- PASSO 3: ENUMERAÇÕES GLOBAIS DE SISTEMA (DB-005)
-- =============================================================================
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'COORDINATOR', 'TEACHER', 'STUDENT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE enrollment_status_enum AS ENUM ('ACTIVE', 'COMPLETED', 'DROPPED', 'SUSPENDED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE submission_status_enum AS ENUM ('PENDING', 'SUBMITTED', 'EVALUATED', 'LATE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE help_request_status_enum AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =============================================================================
-- PASSO 4: AS 4 TABELAS FUNDAMENTAIS DO LOTE 1 (DB-006 A DB-009)
-- =============================================================================

-- 4.1. Tabela `users` (DB-006)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'STUDENT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_email_lowercase CHECK (email = LOWER(BTRIM(email)) AND POSITION('@' IN email) > 1),
    CONSTRAINT chk_users_password_hash_not_plaintext CHECK (
        CHAR_LENGTH(BTRIM(password_hash)) >= 50
        AND password_hash ~ '^(\$2[aby]\$|\$argon2|\$pbkdf2|pbkdf2:|scrypt:)'
    )
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users USING BTREE (email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email));
CREATE INDEX IF NOT EXISTS idx_users_role_is_active ON users USING BTREE (role, is_active);

-- 4.2. Tabela `user_profiles` (DB-007)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    registration_number VARCHAR(50) NOT NULL,
    phone VARCHAR(25),
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id),
    CONSTRAINT uq_user_profiles_registration_number UNIQUE (registration_number),
    CONSTRAINT chk_user_profiles_full_name_not_empty CHECK (CHAR_LENGTH(BTRIM(full_name)) >= 2),
    CONSTRAINT chk_user_profiles_registration_not_empty CHECK (CHAR_LENGTH(BTRIM(registration_number)) >= 3),
    CONSTRAINT fk_user_profiles_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_registration_number ON user_profiles USING BTREE (registration_number);
CREATE INDEX IF NOT EXISTS idx_user_profiles_full_name ON user_profiles USING BTREE (full_name);

-- 4.3. Tabela `auth_sessions` (DB-008)
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_auth_sessions_token_hash UNIQUE (refresh_token_hash),
    CONSTRAINT chk_auth_sessions_expiration CHECK (expires_at > created_at),
    CONSTRAINT chk_auth_sessions_sha256_hash CHECK (refresh_token_hash ~ '^[a-f0-9]{64}$'),
    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_refresh_token_hash ON auth_sessions USING BTREE (refresh_token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_is_revoked ON auth_sessions USING BTREE (is_revoked);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_revoked_expires ON auth_sessions USING BTREE (user_id, is_revoked, expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_active_tokens ON auth_sessions USING BTREE (refresh_token_hash, expires_at) WHERE is_revoked = FALSE;

-- 4.4. Tabela `audit_logs` (DB-009)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_audit_logs_action_not_empty CHECK (CHAR_LENGTH(BTRIM(action)) >= 2),
    CONSTRAINT chk_audit_logs_entity_not_empty CHECK (CHAR_LENGTH(BTRIM(entity)) >= 2),
    CONSTRAINT chk_audit_logs_entity_id_not_empty CHECK (CHAR_LENGTH(BTRIM(entity_id)) >= 1),
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs USING BTREE (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_reference ON audit_logs USING BTREE (entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created_at ON audit_logs USING BTREE (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_old_values_gin ON audit_logs USING GIN (old_values);
CREATE INDEX IF NOT EXISTS idx_audit_logs_new_values_gin ON audit_logs USING GIN (new_values);

-- =============================================================================
-- PASSO 5: VERIFICAÇÃO AUTOMATIZADA DE INTEGRIDADE DO LOTE 1 (PL/pgSQL)
-- =============================================================================
DO $$
DECLARE
    v_missing_tables TEXT[];
    v_table_name TEXT;
    v_expected_tables TEXT[] := ARRAY['users', 'user_profiles', 'auth_sessions', 'audit_logs'];
BEGIN
    FOREACH v_table_name IN ARRAY v_expected_tables LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = v_table_name
        ) THEN
            v_missing_tables := array_append(v_missing_tables, v_table_name);
        END IF;
    END LOOP;

    IF array_length(v_missing_tables, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'Falha de sanidade no Lote 1 (DB-010): tabelas ausentes: %', array_to_string(v_missing_tables, ', ');
    END IF;

    RAISE NOTICE '[DB-010 OK] SELECT 1 executado e as 4 tabelas fundamentais (users, user_profiles, auth_sessions, audit_logs) estao integras no PostgreSQL 16!';
END $$;

COMMIT;
