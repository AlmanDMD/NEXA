-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA chat_messages (DB-044)
-- Versão: 20261127030000_create_chat_messages_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-006 (users), DB-042 (help_requests)
-- =============================================================================
-- Persiste mensagens contextualizadas dentro de uma solicitação confidencial
-- de apoio (help_requests), com confirmação de leitura (is_read / read_at),
-- exclusão em cascata junto ao chamado e índice cronológico crescente.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    help_request_id UUID NOT NULL,
    sender_id UUID NOT NULL,
    message_body TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_chat_messages_body_not_empty
        CHECK (CHAR_LENGTH(BTRIM(message_body)) >= 1),
    CONSTRAINT chk_chat_messages_read_consistency
        CHECK (
            (is_read = FALSE AND read_at IS NULL)
            OR (is_read = TRUE AND read_at IS NOT NULL)
        ),
    CONSTRAINT chk_chat_messages_read_after_sent
        CHECK (read_at IS NULL OR read_at >= sent_at),
    CONSTRAINT fk_chat_messages_help_request
        FOREIGN KEY (help_request_id) REFERENCES help_requests (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_chat_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Trigger de integridade e sigilo dos participantes:
-- 1) Apenas o estudante titular do help_request ou docentes/coordenação/admin podem enviar mensagens.
-- 2) Preenche read_at automaticamente quando is_read = TRUE e read_at vier nulo.
CREATE OR REPLACE FUNCTION fn_chat_messages_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_sender_role user_role_enum;
    v_request_student_id UUID;
BEGIN
    SELECT role INTO v_sender_role FROM users WHERE id = NEW.sender_id;
    SELECT student_id INTO v_request_student_id FROM help_requests WHERE id = NEW.help_request_id;

    IF v_sender_role = 'STUDENT' AND NEW.sender_id IS DISTINCT FROM v_request_student_id THEN
        RAISE EXCEPTION 'Acesso negado: estudante (%) não é titular da solicitação de apoio (%).', NEW.sender_id, NEW.help_request_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_chat_messages_authorized_sender';
    END IF;

    IF NEW.is_read = TRUE AND NEW.read_at IS NULL THEN
        NEW.read_at := GREATEST(CURRENT_TIMESTAMP, NEW.sent_at);
    ELSIF NEW.is_read = FALSE THEN
        NEW.read_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_chat_messages_validate_integrity ON chat_messages;
CREATE TRIGGER trg_chat_messages_validate_integrity
    BEFORE INSERT OR UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION fn_chat_messages_validate_integrity();

-- Row-Level Security (RLS) garantindo que somente o aluno titular ou docentes acessem a thread
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_chat_messages_participants_only ON chat_messages;
CREATE POLICY pol_chat_messages_participants_only
    ON chat_messages
    USING (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') IN ('ADMIN', 'COORDINATOR', 'TEACHER')
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'STUDENT'
            AND EXISTS (
                SELECT 1
                FROM help_requests hr
                WHERE hr.id = chat_messages.help_request_id
                  AND hr.student_id::TEXT = current_setting('app.current_user_id', TRUE)
            )
        )
    )
    WITH CHECK (
        COALESCE(current_setting('app.current_user_role', TRUE), 'ADMIN') IN ('ADMIN', 'COORDINATOR', 'TEACHER')
        OR (
            COALESCE(current_setting('app.current_user_role', TRUE), '') = 'STUDENT'
            AND sender_id::TEXT = current_setting('app.current_user_id', TRUE)
            AND EXISTS (
                SELECT 1
                FROM help_requests hr
                WHERE hr.id = chat_messages.help_request_id
                  AND hr.student_id::TEXT = current_setting('app.current_user_id', TRUE)
            )
        )
    );

-- Índice composto obrigatório do Critério 3 de DB-044: histórico cronológico crescente
CREATE INDEX IF NOT EXISTS idx_chat_messages_request_sent
    ON chat_messages USING BTREE (help_request_id, sent_at ASC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_unread
    ON chat_messages USING BTREE (help_request_id, sender_id)
    WHERE is_read = FALSE;

COMMENT ON TABLE chat_messages IS
    '[DB-044] Mensagens privadas dentro de solicitações de apoio (help_requests) com confirmação de leitura e RLS.';

COMMIT;
