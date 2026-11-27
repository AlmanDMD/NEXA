-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: TABELA student_achievements (DB-046)
-- Versão: 20261127050000_create_student_achievements_table
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-006 (users), DB-017 (enrollments), DB-045 (gamification_badges)
-- =============================================================================
-- Registra as insígnias técnicas desbloqueadas por cada estudante, impedindo
-- duplicação via UNIQUE (student_id, badge_id) e mantendo histórico ordenado
-- por (student_id, unlocked_at DESC).
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS student_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    badge_id UUID NOT NULL,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origin_reference VARCHAR(150) NOT NULL,

    CONSTRAINT uq_student_achievements_composite UNIQUE (student_id, badge_id),
    CONSTRAINT chk_student_achievements_origin_not_empty
        CHECK (CHAR_LENGTH(BTRIM(origin_reference)) >= 3),
    CONSTRAINT fk_student_achievements_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_achievements_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_achievements_badge
        FOREIGN KEY (badge_id) REFERENCES gamification_badges (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Trigger de integridade acadêmica:
-- 1) student_id deve ter role = STUDENT e ser titular de enrollment_id.
-- 2) badge_id deve estar ativo (is_active = TRUE) no momento da concessão (INSERT).
CREATE OR REPLACE FUNCTION fn_student_achievements_validate_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_student_role user_role_enum;
    v_enrollment_student_id UUID;
    v_badge_active BOOLEAN;
BEGIN
    SELECT role INTO v_student_role FROM users WHERE id = NEW.student_id;
    IF v_student_role IS DISTINCT FROM 'STUDENT' THEN
        RAISE EXCEPTION 'Conquista de gamificação só pode ser concedida a usuário STUDENT (student_id=%).', NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_achievements_student_role';
    END IF;

    SELECT student_id INTO v_enrollment_student_id FROM enrollments WHERE id = NEW.enrollment_id;
    IF v_enrollment_student_id IS DISTINCT FROM NEW.student_id THEN
        RAISE EXCEPTION 'A matrícula (%) não pertence ao estudante (%).', NEW.enrollment_id, NEW.student_id
            USING ERRCODE = '23514',
                  CONSTRAINT = 'chk_student_achievements_enrollment_owner';
    END IF;

    IF TG_OP = 'INSERT' THEN
        SELECT is_active INTO v_badge_active FROM gamification_badges WHERE id = NEW.badge_id;
        IF v_badge_active IS DISTINCT FROM TRUE THEN
            RAISE EXCEPTION 'Não é possível conceder conquista inativa (badge_id=%).', NEW.badge_id
                USING ERRCODE = '23514',
                      CONSTRAINT = 'chk_student_achievements_badge_active';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_student_achievements_validate_integrity ON student_achievements;
CREATE TRIGGER trg_student_achievements_validate_integrity
    BEFORE INSERT OR UPDATE ON student_achievements
    FOR EACH ROW
    EXECUTE FUNCTION fn_student_achievements_validate_integrity();

-- Índice obrigatório do Critério 3 de DB-046: conquistas mais recentes do aluno
CREATE INDEX IF NOT EXISTS idx_student_achievements_student_unlocked
    ON student_achievements USING BTREE (student_id, unlocked_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_achievements_enrollment
    ON student_achievements USING BTREE (enrollment_id);

CREATE INDEX IF NOT EXISTS idx_student_achievements_badge
    ON student_achievements USING BTREE (badge_id);

COMMENT ON TABLE student_achievements IS
    '[DB-046] Registro de insígnias pedagógicas desbloqueadas por estudante com unicidade em (student_id, badge_id).';

COMMIT;
