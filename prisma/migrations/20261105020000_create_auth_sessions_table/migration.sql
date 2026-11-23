-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: SESSÕES E REFRESH TOKENS (DB-008)
-- Versão: 20261105020000_create_auth_sessions_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `auth_sessions` para renovação segura de sessões JWT,
-- rastreamento de dispositivos e revogação imediata (Logout / Anti-Theft):
-- 1. Chave estrangeira `user_id` para `users(id)` com `ON DELETE CASCADE`.
-- 2. Proteção estrita contra token em texto puro: `refresh_token_hash` validado
--    por regex exigindo exclusivamente hash SHA-256 hexadecimal de 64 caracteres.
-- 3. Constraint verificável de expiração (`chk_auth_sessions_expiration: expires_at > created_at`).
-- 4. Índices B-Tree de alta performance em `is_revoked`, `refresh_token_hash` e
--    índice parcial para sessões ativas (`WHERE is_revoked = FALSE`).
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 e SHA-256
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de sessões e Refresh Tokens (`auth_sessions`)
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Unicidade absoluta do hash SHA-256 do Refresh Token
    CONSTRAINT uq_auth_sessions_token_hash UNIQUE (refresh_token_hash),

    -- Critério de Aceitação 3: Constraint de expiração verificável
    CONSTRAINT chk_auth_sessions_expiration CHECK (expires_at > created_at),

    -- Observação Técnica: O token nunca é salvo puro, apenas o hash SHA-256 (64 hex chars)
    CONSTRAINT chk_auth_sessions_sha256_hash CHECK (
        refresh_token_hash ~ '^[a-f0-9]{64}$'
    ),

    -- Critério de Aceitação 1: Chave estrangeira para users(id)
    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. Criar índices B-Tree e Índice Parcial para consulta ultra-rápida no middleware de Auth
CREATE INDEX IF NOT EXISTS idx_auth_sessions_refresh_token_hash
    ON auth_sessions USING BTREE (refresh_token_hash);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_is_revoked
    ON auth_sessions USING BTREE (is_revoked);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_revoked_expires
    ON auth_sessions USING BTREE (user_id, is_revoked, expires_at);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_active_tokens
    ON auth_sessions USING BTREE (refresh_token_hash, expires_at)
    WHERE is_revoked = FALSE;

-- 4. Função e Trigger PL/pgSQL para normalizar hash SHA-256 em minúsculo
CREATE OR REPLACE FUNCTION fn_auth_sessions_normalize_hash()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.refresh_token_hash IS NOT NULL THEN
        NEW.refresh_token_hash := LOWER(BTRIM(NEW.refresh_token_hash));
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_auth_sessions_normalize_hash ON auth_sessions;

CREATE TRIGGER trg_auth_sessions_normalize_hash
    BEFORE INSERT OR UPDATE ON auth_sessions
    FOR EACH ROW
    EXECUTE FUNCTION fn_auth_sessions_normalize_hash();

COMMIT;
