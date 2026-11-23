-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: AUDITORIA E LOGS JSONB (DB-009)
-- Versão: 20261105030000_create_audit_logs_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Implementa a tabela `audit_logs` para governança acadêmica e conformidade LGPD:
-- 1. Campos `old_values` e `new_values` em tipo nativo `JSONB` com índices GIN
--    para buscas indexadas usando o operador de contenção `@>`.
-- 2. Chave estrangeira `user_id` opcional com `ON DELETE SET NULL` (sem deleção
--    em cascata, preservando 100% do histórico mesmo se um usuário for removido).
-- 3. Índice temporal `idx_audit_logs_created_at` (`created_at DESC`) para relatórios.
-- 4. Trigger de imutabilidade (`trg_audit_logs_prevent_delete`) impedindo exclusão
--    de registros de auditoria.
-- =============================================================================

BEGIN;

-- 1. Garantir extensão pgcrypto para geração de UUID v4 nativo
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Criar tabela de auditoria (`audit_logs`)
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

    -- Validações de preenchimento mínimo dos identificadores do evento auditado
    CONSTRAINT chk_audit_logs_action_not_empty CHECK (CHAR_LENGTH(BTRIM(action)) >= 2),
    CONSTRAINT chk_audit_logs_entity_not_empty CHECK (CHAR_LENGTH(BTRIM(entity)) >= 2),
    CONSTRAINT chk_audit_logs_entity_id_not_empty CHECK (CHAR_LENGTH(BTRIM(entity_id)) >= 1),

    -- Critério de Aceitação 2: Sem deleção em cascata (ON DELETE SET NULL preserva o histórico)
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- 3. Critério de Aceitação 3: Índice temporal em created_at e índices compostos de busca
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs USING BTREE (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_reference
    ON audit_logs USING BTREE (entity, entity_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created_at
    ON audit_logs USING BTREE (user_id, created_at DESC);

-- 4. Observação Técnica: Índices GIN nos campos JSONB para buscas indexadas com operador `@>`
CREATE INDEX IF NOT EXISTS idx_audit_logs_old_values_gin
    ON audit_logs USING GIN (old_values);

CREATE INDEX IF NOT EXISTS idx_audit_logs_new_values_gin
    ON audit_logs USING GIN (new_values);

-- 5. Função e Trigger PL/pgSQL para impedir exclusão física (DELETE) de logs de auditoria
CREATE OR REPLACE FUNCTION fn_audit_logs_prevent_delete()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Operacao bloqueada: registros da tabela audit_logs sao imutaveis e nao podem ser excluidos (Governanca/LGPD).'
        USING ERRCODE = '42501';
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_logs_prevent_delete ON audit_logs;

CREATE TRIGGER trg_audit_logs_prevent_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION fn_audit_logs_prevent_delete();

COMMIT;
