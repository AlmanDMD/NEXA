-- =============================================================================
-- PROJETO NEXA — MIGRATION SQL VERSIONADA: ENUMERAÇÕES GLOBAIS (DB-005)
-- Versão: 20261104010000_create_global_system_enums
-- SGBD: PostgreSQL 16 (Docker: postgres:16-alpine)
-- =============================================================================
-- Cria de forma idempotente os tipos ENUM nativos do PostgreSQL 16 garantindo
-- performance superior, armazenamento compacto (4 bytes por valor) e rejeição
-- imediata de valores inválidos no nível do motor SQL.
-- =============================================================================

BEGIN;

-- 1. Role -> user_role_enum (ADMIN, COORDINATOR, TEACHER, STUDENT)
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'COORDINATOR', 'TEACHER', 'STUDENT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. EnrollmentStatus -> enrollment_status_enum (ACTIVE, COMPLETED, DROPPED, SUSPENDED)
DO $$ BEGIN
    CREATE TYPE enrollment_status_enum AS ENUM ('ACTIVE', 'COMPLETED', 'DROPPED', 'SUSPENDED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 3. RiskLevel -> risk_level_enum (LOW, MODERATE, HIGH, CRITICAL)
DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MODERATE', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 4. SubmissionStatus -> submission_status_enum (PENDING, SUBMITTED, EVALUATED, LATE)
DO $$ BEGIN
    CREATE TYPE submission_status_enum AS ENUM ('PENDING', 'SUBMITTED', 'EVALUATED', 'LATE');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 5. HelpRequestStatus -> help_request_status_enum (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
DO $$ BEGIN
    CREATE TYPE help_request_status_enum AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 6. Shift -> shift_enum (MORNING, AFTERNOON, NIGHT)
DO $$ BEGIN
    CREATE TYPE shift_enum AS ENUM ('MORNING', 'AFTERNOON', 'NIGHT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 7. ClassStatus -> class_status_enum (PLANNING, ACTIVE, COMPLETED, ARCHIVED)
DO $$ BEGIN
    CREATE TYPE class_status_enum AS ENUM ('PLANNING', 'ACTIVE', 'COMPLETED', 'ARCHIVED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 8. CompetencyCategory -> competency_category_enum (TECHNICAL, SAFETY, PROCEDURAL)
DO $$ BEGIN
    CREATE TYPE competency_category_enum AS ENUM ('TECHNICAL', 'SAFETY', 'PROCEDURAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 9. AttendanceStatus -> attendance_status_enum (PRESENT, ABSENT, LATE, JUSTIFIED)
DO $$ BEGIN
    CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'JUSTIFIED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 10. AssessmentType -> assessment_type_enum (EXAM, MICRO_EVALUATION, PROJECT)
DO $$ BEGIN
    CREATE TYPE assessment_type_enum AS ENUM ('EXAM', 'MICRO_EVALUATION', 'PROJECT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 11. AlertCategory -> alert_category_enum (ATTENDANCE, GRADE_DROP, PENDING_TASKS, SELF_EVAL_GAP)
DO $$ BEGIN
    CREATE TYPE alert_category_enum AS ENUM ('ATTENDANCE', 'GRADE_DROP', 'PENDING_TASKS', 'SELF_EVAL_GAP');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 12. AlertStatus -> alert_status_enum (ACTIVE, ACKNOWLEDGED, RESOLVED)
DO $$ BEGIN
    CREATE TYPE alert_status_enum AS ENUM ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 13. DiagnosticType -> diagnostic_type_enum
DO $$ BEGIN
    CREATE TYPE diagnostic_type_enum AS ENUM ('ALIGNED', 'OVERCONFIDENCE_RISK', 'UNDERCONFIDENCE_SUPPORT', 'INSUFFICIENT_EVIDENCE');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 14. MilestoneType -> milestone_type_enum
DO $$ BEGIN
    CREATE TYPE milestone_type_enum AS ENUM ('MODULE_COMPLETED', 'SKILL_LEVEL_UP', 'PERFECT_ATTENDANCE', 'RECOVERY_ACHIEVED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 15. AnnouncementPriority -> announcement_priority_enum (NORMAL, IMPORTANT, URGENT)
DO $$ BEGIN
    CREATE TYPE announcement_priority_enum AS ENUM ('NORMAL', 'IMPORTANT', 'URGENT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 16. HelpRequestCategory -> help_request_category_enum
DO $$ BEGIN
    CREATE TYPE help_request_category_enum AS ENUM ('TECHNICAL_DOUBT', 'PRACTICAL_DIFFICULTY', 'PERSONAL_PEDAGOGICAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 17. NoteVisibilityScope -> note_visibility_scope_enum
DO $$ BEGIN
    CREATE TYPE note_visibility_scope_enum AS ENUM ('PRIVATE_AUTHOR', 'TEACHERS_AND_COORD', 'COORDINATION_ONLY');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 18. NoteCategory -> note_category_enum
DO $$ BEGIN
    CREATE TYPE note_category_enum AS ENUM ('INTERVENTION', 'MENTORING', 'BEHAVIORAL', 'ACCOMMODATION');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

COMMIT;
