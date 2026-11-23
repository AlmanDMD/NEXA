-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: PERFIS DE USUÁRIO (DB-007)
-- Versão: 20261105010000_create_user_profiles_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `user_profiles` para separar dados pessoais identificáveis
-- (PII) das credenciais de login (`users`), atendendo ao princípio de minimização
-- e anonimização futura da LGPD (DB-049):
-- 1. Relacionamento estrito 1:1 com `users` (`uq_user_profiles_user_id`) e
--    exclusão em cascata (`ON DELETE CASCADE`).
-- 2. Matrícula / Registro Funcional SENAI único (`uq_user_profiles_registration_number`).
-- 3. Índices B-Tree em `registration_number` e `full_name` para buscas rápidas da secretaria.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de perfis de usuário (`user_profiles`)
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

    -- Garante cardinalidade estrita 1:1 com a tabela `users`
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id),

    -- Garante unicidade da matrícula / registro funcional SENAI no sistema
    CONSTRAINT uq_user_profiles_registration_number UNIQUE (registration_number),

    -- Validações de integridade de campos obrigatórios não vazios
    CONSTRAINT chk_user_profiles_full_name_not_empty CHECK (CHAR_LENGTH(BTRIM(full_name)) >= 2),
    CONSTRAINT chk_user_profiles_registration_not_empty CHECK (CHAR_LENGTH(BTRIM(registration_number)) >= 3),

    -- Chave estrangeira 1:1 com deleção em cascata (ON DELETE CASCADE)
    CONSTRAINT fk_user_profiles_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. Criar índices B-Tree para agilizar buscas da secretaria acadêmica e coordenação
CREATE INDEX IF NOT EXISTS idx_user_profiles_registration_number
    ON user_profiles USING BTREE (registration_number);

CREATE INDEX IF NOT EXISTS idx_user_profiles_full_name
    ON user_profiles USING BTREE (full_name);

-- 4. Função e Trigger PL/pgSQL para padronizar registration_number (UPPER/TRIM) e atualizar updated_at
CREATE OR REPLACE FUNCTION fn_user_profiles_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.registration_number IS NOT NULL THEN
        NEW.registration_number := UPPER(BTRIM(NEW.registration_number));
    END IF;

    IF NEW.full_name IS NOT NULL THEN
        NEW.full_name := BTRIM(NEW.full_name);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_user_profiles_normalize_and_touch ON user_profiles;

CREATE TRIGGER trg_user_profiles_normalize_and_touch
    BEFORE INSERT OR UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION fn_user_profiles_normalize_and_touch();

COMMIT;
