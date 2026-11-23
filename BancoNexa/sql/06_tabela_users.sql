-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA DE USUÁRIOS (DB-006)
-- Versão: 20261105000000_create_users_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a entidade central de autenticação (`users`) com:
-- 1. Identificador universal UUID v4 nativo (`gen_random_uuid()`).
-- 2. E-mail único (`uq_users_email`), indexado (`idx_users_email`) e normalizado
--    obrigatoriamente em minúsculo (lowercased) via Trigger e CHECK constraint.
-- 3. Proteção contra senha em texto puro: `password_hash` NOT NULL validado por
--    expressão regular exigindo formato de hash criptográfico (Bcrypt / Argon2).
-- 4. Papel RBAC (`user_role_enum`) com padrão `'STUDENT'` e controle `is_active`.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto e tipo user_role_enum (pré-requisito DB-005)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'COORDINATOR', 'TEACHER', 'STUDENT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Criar tabela central de autenticação `users`
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'STUDENT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Unicidade estrita de e-mail (dispara SQLSTATE 23505 / Prisma P2002 em duplicatas)
    CONSTRAINT uq_users_email UNIQUE (email),

    -- Regra de negócio: e-mail obrigatoriamente em minúsculo (lowercased) e válido
    CONSTRAINT chk_users_email_lowercase CHECK (
        email = LOWER(BTRIM(email))
        AND POSITION('@' IN email) > 1
    ),

    -- Regra de segurança: rejeita armazenamento de senha em texto puro no banco
    -- Aceita apenas hashes criptográficos Bcrypt ($2a$, $2b$, $2y$), Argon2 ($argon2...) ou PBKDF2/Scrypt (>= 50 chars)
    CONSTRAINT chk_users_password_hash_not_plaintext CHECK (
        CHAR_LENGTH(BTRIM(password_hash)) >= 50
        AND password_hash ~ '^(\$2[aby]\$|\$argon2|\$pbkdf2|pbkdf2:|scrypt:)'
    )
);

-- 3. Criar índices B-Tree para busca rápida no login e filtros RBAC
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users USING BTREE (email);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
    ON users (LOWER(email));

CREATE INDEX IF NOT EXISTS idx_users_role_is_active
    ON users USING BTREE (role, is_active);

-- 4. Função e Trigger PL/pgSQL para normalizar e-mail (lowercased) e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_users_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.email IS NOT NULL THEN
        NEW.email := LOWER(BTRIM(NEW.email));
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_normalize_and_touch ON users;

CREATE TRIGGER trg_users_normalize_and_touch
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION fn_users_normalize_and_touch();

COMMIT;
