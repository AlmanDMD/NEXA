-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: RETENÇÃO & ANONIMIZAÇÃO LGPD (DB-049)
-- Versão: 20261127070000_create_lgpd_retention_and_anonymization
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-006 (users), DB-007 (user_profiles), DB-008 (auth_sessions),
--               DB-009 (audit_logs), DB-017 (enrollments), DB-042 (help_requests),
--               DB-043 (pedagogical_notes), DB-044 (chat_messages)
-- =============================================================================
-- Implementa a política de retenção e anonimização irreversível (LGPD — Lei nº
-- 13.709/2018, Seção 14 do Projeto NEXA):
-- 1) Remove PII em users, user_profiles, auth_sessions, help_requests,
--    chat_messages e pedagogical_notes via hash SHA-256 irreversível.
-- 2) Preserva 100% da integridade referencial de matrículas, notas, frequências,
--    evidências, diagnósticos e alertas para estatísticas históricas anônimas.
-- 3) Registra obrigatoriamente cada operação na trilha imutável audit_logs.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Função de anonimização individual sob demanda ou por expiração de retenção
CREATE OR REPLACE FUNCTION fn_anonymize_user_lgpd(
    p_user_id UUID,
    p_actor_id UUID DEFAULT NULL,
    p_reason TEXT DEFAULT 'LGPD_RETENTION_POLICY'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_user users%ROWTYPE;
    v_hash TEXT;
    v_anon_email VARCHAR(255);
    v_anon_password_hash VARCHAR(255);
    v_anon_full_name VARCHAR(150);
    v_anon_registration VARCHAR(50);
    v_profiles_updated INTEGER := 0;
    v_sessions_revoked INTEGER := 0;
    v_help_requests_updated INTEGER := 0;
    v_chat_messages_updated INTEGER := 0;
    v_pedagogical_notes_updated INTEGER := 0;
    v_self_assessments_sanitized INTEGER := 0;
    v_summary JSONB;
BEGIN
    SELECT * INTO v_user FROM users WHERE id = p_user_id FOR UPDATE;
    IF v_user.id IS NULL THEN
        RAISE EXCEPTION 'Usuário (%) não encontrado para anonimização LGPD.', p_user_id
            USING ERRCODE = 'P0002';
    END IF;

    -- Idempotência: se o e-mail já estiver no domínio anonimizado, retorna resumo sem reprocessar
    IF v_user.email LIKE 'anon_%@anonymized.nexa.local' THEN
        RETURN jsonb_build_object(
            'status', 'ALREADY_ANONYMIZED',
            'user_id', p_user_id,
            'anonymized_email', v_user.email
        );
    END IF;

    -- Hash criptográfico irreversível SHA-256 (sal aleatório + id + timestamp)
    v_hash := encode(
        digest(
            p_user_id::TEXT || '|' || v_user.email || '|' || gen_random_uuid()::TEXT || '|' || CURRENT_TIMESTAMP::TEXT,
            'sha256'
        ),
        'hex'
    );

    v_anon_email := 'anon_' || LEFT(v_hash, 20) || '@anonymized.nexa.local';
    -- Mantém formato >= 60 chars compatível com chk_users_password_hash_not_plaintext (DB-006)
    v_anon_password_hash := '$2b$12$LGPDANON' || LEFT(v_hash, 45);
    v_anon_full_name := 'Titular Anonimizado #' || UPPER(LEFT(v_hash, 8));
    v_anon_registration := 'ANON-' || UPPER(LEFT(v_hash, 12));

    -- 1.1 users: substitui e-mail e credencial por hashes irreversíveis e desativa conta
    UPDATE users
    SET email = v_anon_email,
        password_hash = v_anon_password_hash,
        is_active = FALSE,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_user_id;

    -- 1.2 user_profiles: remove nome real, matrícula identificável, telefone, avatar e bio
    UPDATE user_profiles
    SET full_name = v_anon_full_name,
        registration_number = v_anon_registration,
        phone = NULL,
        avatar_url = NULL,
        bio = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_profiles_updated = ROW_COUNT;

    -- 1.3 auth_sessions: revoga todas as sessões e limpa metadados identificáveis de rede
    UPDATE auth_sessions
    SET is_revoked = TRUE,
        user_agent = 'ANONYMIZED_LGPD',
        ip_address = '0.0.0.0'
    WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_sessions_revoked = ROW_COUNT;

    -- 1.4 help_requests: sanitiza textos livres mantendo categoria, disciplina, módulo e status para estatística
    UPDATE help_requests
    SET subject_title = '[ANONIMIZADO LGPD]',
        description = '[CONTEÚDO CONFIDENCIAL ANONIMIZADO CONFORME LGPD]',
        resolution_summary = CASE
            WHEN resolution_summary IS NOT NULL THEN '[RESUMO ANONIMIZADO CONFORME LGPD]'
            ELSE NULL
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE student_id = p_user_id;
    GET DIAGNOSTICS v_help_requests_updated = ROW_COUNT;

    -- 1.5 chat_messages: sanitiza mensagens privadas vinculadas ao titular ou aos seus chamados
    UPDATE chat_messages
    SET message_body = '[MENSAGEM ANONIMIZADA CONFORME LGPD]'
    WHERE sender_id = p_user_id
       OR help_request_id IN (SELECT id FROM help_requests WHERE student_id = p_user_id);
    GET DIAGNOSTICS v_chat_messages_updated = ROW_COUNT;

    -- 1.6 pedagogical_notes: substitui conteúdo livre sensível preservando categoria e datas agregadas
    UPDATE pedagogical_notes
    SET note_content = '[OBSERVAÇÃO PEDAGÓGICA ANONIMIZADA CONFORME LGPD]',
        updated_at = CURRENT_TIMESTAMP
    WHERE student_id = p_user_id;
    GET DIAGNOSTICS v_pedagogical_notes_updated = ROW_COUNT;

    -- 1.7 student_self_assessments: limpa textos livres em difficulty_notes preservando níveis numéricos (1..5)
    UPDATE student_self_assessments
    SET difficulty_notes = NULL
    WHERE student_id = p_user_id
      AND difficulty_notes IS NOT NULL;
    GET DIAGNOSTICS v_self_assessments_sanitized = ROW_COUNT;

    -- Resumo estruturado sem nenhum dado pessoal (zero PII nos logs!)
    v_summary := jsonb_build_object(
        'status', 'ANONYMIZED',
        'user_id', p_user_id,
        'anonymization_hash_prefix', LEFT(v_hash, 16),
        'reason', COALESCE(NULLIF(BTRIM(p_reason), ''), 'LGPD_RETENTION_POLICY'),
        'affected_tables', jsonb_build_object(
            'users', 1,
            'user_profiles', v_profiles_updated,
            'auth_sessions', v_sessions_revoked,
            'help_requests', v_help_requests_updated,
            'chat_messages', v_chat_messages_updated,
            'pedagogical_notes', v_pedagogical_notes_updated,
            'student_self_assessments', v_self_assessments_sanitized
        ),
        'preserved_statistical_aggregates', jsonb_build_array(
            'enrollments',
            'attendance_records',
            'student_grades',
            'skill_evidences',
            'academic_alerts',
            'explainable_diagnostics',
            'student_achievements'
        ),
        'executed_at', CURRENT_TIMESTAMP
    );

    -- 1.8 Trilha de auditoria obrigatória em audit_logs (Critério 3 de DB-049)
    INSERT INTO audit_logs (user_id, action, entity, entity_id, old_values, new_values)
    VALUES (
        p_actor_id,
        'LGPD_USER_ANONYMIZATION',
        'users',
        p_user_id::TEXT,
        jsonb_build_object('role', v_user.role, 'was_active', v_user.is_active),
        v_summary
    );

    RETURN v_summary;
END;
$$;

-- 2. Política automatizada de retenção em lote (padrão legal: 5 anos após encerramento/inativação)
CREATE OR REPLACE FUNCTION fn_enforce_lgpd_retention_policy(
    p_retention_years INTEGER DEFAULT 5,
    p_actor_id UUID DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_cutoff TIMESTAMPTZ;
    v_candidate RECORD;
    v_processed_count INTEGER := 0;
    v_processed_ids UUID[] := ARRAY[]::UUID[];
    v_result JSONB;
BEGIN
    IF p_retention_years < 1 OR p_retention_years > 50 THEN
        RAISE EXCEPTION 'Prazo de retenção LGPD inválido (% anos). Utilize valor entre 1 e 50 anos.', p_retention_years
            USING ERRCODE = '22023';
    END IF;

    v_cutoff := CURRENT_TIMESTAMP - make_interval(years => p_retention_years);

    FOR v_candidate IN
        SELECT u.id
        FROM users u
        WHERE u.role = 'STUDENT'
          AND u.is_active = FALSE
          AND u.email NOT LIKE 'anon_%@anonymized.nexa.local'
          AND u.updated_at <= v_cutoff
          AND NOT EXISTS (
              SELECT 1
              FROM enrollments e
              WHERE e.student_id = u.id
                AND e.status = 'ACTIVE'
          )
    LOOP
        PERFORM fn_anonymize_user_lgpd(
            v_candidate.id,
            p_actor_id,
            'LGPD_AUTOMATIC_RETENTION_' || p_retention_years || 'Y'
        );
        v_processed_count := v_processed_count + 1;
        v_processed_ids := array_append(v_processed_ids, v_candidate.id);
    END LOOP;

    v_result := jsonb_build_object(
        'policy', 'LGPD_RETENTION_BATCH',
        'retention_years', p_retention_years,
        'cutoff_timestamp', v_cutoff,
        'anonymized_users_count', v_processed_count,
        'executed_at', CURRENT_TIMESTAMP
    );

    INSERT INTO audit_logs (user_id, action, entity, entity_id, new_values)
    VALUES (
        p_actor_id,
        'LGPD_RETENTION_BATCH_RUN',
        'users',
        'BATCH_' || to_char(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS'),
        v_result
    );

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION fn_anonymize_user_lgpd(UUID, UUID, TEXT) IS
    '[DB-049] Anonimiza irreversivelmente PII do titular (users, user_profiles, auth_sessions, help_requests, chat_messages, pedagogical_notes) preservando estatísticas acadêmicas e registrando em audit_logs.';

COMMENT ON FUNCTION fn_enforce_lgpd_retention_policy(INTEGER, UUID) IS
    '[DB-049] Aplica a política de retenção LGPD em lote para ex-alunos inativos após o prazo legal configurado.';

COMMIT;
