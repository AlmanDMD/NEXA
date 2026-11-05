-- =============================================================================
-- PROJETO NEXA — SCRIPT DE INICIALIZAÇÃO DO CONTAINER POSTGRESQL 16 (DB-003)
-- Executado automaticamente pelo entrypoint oficial (/docker-entrypoint-initdb.d)
-- na criação inicial do volume persistente nexa_postgres_data.
-- =============================================================================

-- 1. Garantir extensões nativas para geração de UUID v4 e criptografia (LGPD)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Configurar Timezone padrão da sessão e do banco para America/Sao_Paulo
SET TIME ZONE 'America/Sao_Paulo';
