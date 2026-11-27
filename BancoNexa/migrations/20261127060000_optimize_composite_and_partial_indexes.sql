-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: OTIMIZAÇÃO DE ÍNDICES (DB-047)
-- Versão: 20261127060000_optimize_composite_and_partial_indexes
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- Dependências: DB-022, DB-025, DB-028, DB-034, DB-042
-- =============================================================================
-- Adiciona índices B-Tree compostos e índices parciais estratégicos nas tabelas
-- críticas dos Lotes 1 a 5 para eliminar Sequential Scans em filtros por turma,
-- aluno, status e risco, garantindo latência < 50ms em dashboards e relatórios.
-- =============================================================================

BEGIN;

-- 1. Matrículas (enrollments): filtros frequentes por turma e status + índice parcial de ativos
CREATE INDEX IF NOT EXISTS idx_enrollments_class_status
    ON enrollments USING BTREE (class_id, status);

CREATE INDEX IF NOT EXISTS idx_enrollments_active_class_student
    ON enrollments USING BTREE (class_id, student_id)
    WHERE status = 'ACTIVE';

-- 2. Submissões práticas (task_submissions): fila por estudante/status e pendências/atrasos
CREATE INDEX IF NOT EXISTS idx_task_submissions_student_status
    ON task_submissions USING BTREE (student_id, status);

CREATE INDEX IF NOT EXISTS idx_task_submissions_pending_late
    ON task_submissions USING BTREE (enrollment_id, task_id, status)
    WHERE status IN ('PENDING', 'LATE');

-- 3. Alertas acadêmicos (academic_alerts): dashboard de risco por turma e fila de alertas ativos
CREATE INDEX IF NOT EXISTS idx_academic_alerts_class_risk_level
    ON academic_alerts USING BTREE (class_id, risk_level);

CREATE INDEX IF NOT EXISTS idx_academic_alerts_active_priority
    ON academic_alerts USING BTREE (class_id, risk_level, created_at DESC)
    WHERE status = 'ACTIVE';

-- 4. Frequências (attendance_records): apuração por matrícula/status e índice parcial de faltas
CREATE INDEX IF NOT EXISTS idx_attendance_records_enrollment_status
    ON attendance_records USING BTREE (enrollment_id, status);

CREATE INDEX IF NOT EXISTS idx_attendance_records_absences
    ON attendance_records USING BTREE (enrollment_id, lesson_id)
    WHERE status IN ('ABSENT', 'LATE');

-- 5. Notas e avaliações (student_grades): consolidação por avaliação/matrícula e notas abaixo da média
CREATE INDEX IF NOT EXISTS idx_student_grades_assessment_score
    ON student_grades USING BTREE (assessment_id, grade_value);

CREATE INDEX IF NOT EXISTS idx_student_grades_enrollment_assessment
    ON student_grades USING BTREE (enrollment_id, assessment_id);

-- 6. Solicitações de ajuda (help_requests): índice parcial de chamados em aberto / andamento
CREATE INDEX IF NOT EXISTS idx_help_requests_open_queue
    ON help_requests USING BTREE (assigned_teacher_id, created_at DESC)
    WHERE status IN ('OPEN', 'IN_PROGRESS');

-- 7. Usuários ativos (users): acelera autenticação e listagens por perfil ignorando contas inativas
CREATE INDEX IF NOT EXISTS idx_users_active_role
    ON users USING BTREE (role, email)
    WHERE is_active = TRUE;

-- 8. Mural de avisos fixados (class_announcements) e badges ativos (gamification_badges)
CREATE INDEX IF NOT EXISTS idx_class_announcements_pinned
    ON class_announcements USING BTREE (class_id, published_at DESC)
    WHERE is_pinned = TRUE;

CREATE INDEX IF NOT EXISTS idx_gamification_badges_active_code
    ON gamification_badges USING BTREE (code)
    WHERE is_active = TRUE;

-- 9. Atualiza estatísticas do planejador de queries (PostgreSQL Query Planner)
ANALYZE users;
ANALYZE enrollments;
ANALYZE attendance_records;
ANALYZE task_submissions;
ANALYZE student_grades;
ANALYZE academic_alerts;
ANALYZE help_requests;
ANALYZE class_announcements;
ANALYZE gamification_badges;
ANALYZE student_achievements;

COMMIT;
