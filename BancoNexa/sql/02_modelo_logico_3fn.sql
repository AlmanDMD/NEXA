-- =============================================================================
-- PROJETO NEXA — SISTEMA INTELIGENTE DE MONITORAMENTO ACADÊMICO SENAI
-- CARD: [DB-002] Elaborar Modelo Lógico Relacional Normalizado (3FN)
-- SGBD ALVO: PostgreSQL 16 (Executado via Docker)
-- =============================================================================
-- Características do Modelo Lógico Relacional (3FN):
-- 1. Chaves Primárias (PK) em UUID v4 nativo (gen_random_uuid()) para evitar
--    ID enumeration e facilitar sincronização distribuída.
-- 2. Chaves Compostas (PRIMARY KEY / UNIQUE compostas) em todas as tabelas
--    associativas (ex.: module_competencies, student_subjects, enrollments,
--    teacher_assignments, attendance_records, submission_evaluations, etc.).
-- 3. Integridade Referencial Estrita: ON DELETE RESTRICT em todo o histórico
--    acadêmico (cursos, turmas, matrículas, aulas, notas, frequências e entregas).
-- 4. Normalização até a 3ª Forma Normal (3FN): Eliminação de grupos repetitivos
--    (1FN), dependências parciais (2FN) e dependências transitivas (3FN).
--    Nenhuma nota ou falta é duplicada entre módulos ou disciplinas.
-- =============================================================================

BEGIN;

-- Extensão complementar para funções criptográficas e UUID no PostgreSQL 16
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. TIPOS ENUMERADOS GLOBAIS DE DOMÍNIO (POSTGRESQL NATIVE ENUMS)
-- =============================================================================

CREATE TYPE user_role_enum AS ENUM (
    'ADMIN',
    'COORDINATOR',
    'TEACHER',
    'STUDENT'
);

CREATE TYPE shift_enum AS ENUM (
    'MORNING',
    'AFTERNOON',
    'NIGHT'
);

CREATE TYPE class_status_enum AS ENUM (
    'PLANNING',
    'ACTIVE',
    'COMPLETED',
    'ARCHIVED'
);

CREATE TYPE enrollment_status_enum AS ENUM (
    'ACTIVE',
    'COMPLETED',
    'DROPPED',
    'SUSPENDED'
);

CREATE TYPE competency_category_enum AS ENUM (
    'TECHNICAL',
    'SAFETY',
    'PROCEDURAL'
);

CREATE TYPE attendance_status_enum AS ENUM (
    'PRESENT',
    'ABSENT',
    'LATE',
    'JUSTIFIED'
);

CREATE TYPE submission_status_enum AS ENUM (
    'PENDING',
    'SUBMITTED',
    'EVALUATED',
    'LATE'
);

CREATE TYPE assessment_type_enum AS ENUM (
    'EXAM',
    'MICRO_EVALUATION',
    'PROJECT'
);

CREATE TYPE risk_level_enum AS ENUM (
    'LOW',
    'MODERATE',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE alert_category_enum AS ENUM (
    'ATTENDANCE',
    'GRADE_DROP',
    'PENDING_TASKS',
    'SELF_EVAL_GAP'
);

CREATE TYPE alert_status_enum AS ENUM (
    'ACTIVE',
    'ACKNOWLEDGED',
    'RESOLVED'
);

CREATE TYPE diagnostic_type_enum AS ENUM (
    'ALIGNED',
    'OVERCONFIDENCE_RISK',
    'UNDERCONFIDENCE_SUPPORT',
    'INSUFFICIENT_EVIDENCE'
);

CREATE TYPE milestone_type_enum AS ENUM (
    'MODULE_COMPLETED',
    'SKILL_LEVEL_UP',
    'PERFECT_ATTENDANCE',
    'RECOVERY_ACHIEVED'
);

CREATE TYPE announcement_priority_enum AS ENUM (
    'NORMAL',
    'IMPORTANT',
    'URGENT'
);

CREATE TYPE help_request_category_enum AS ENUM (
    'TECHNICAL_DOUBT',
    'PRACTICAL_DIFFICULTY',
    'PERSONAL_PEDAGOGICAL'
);

CREATE TYPE help_request_status_enum AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'RESOLVED',
    'CLOSED'
);

CREATE TYPE note_visibility_scope_enum AS ENUM (
    'PRIVATE_AUTHOR',
    'TEACHERS_AND_COORD',
    'COORDINATION_ONLY'
);

CREATE TYPE note_category_enum AS ENUM (
    'INTERVENTION',
    'MENTORING',
    'BEHAVIORAL',
    'ACCOMMODATION'
);

-- =============================================================================
-- 2. DOMÍNIO 1: IDENTIDADE, ACESSO (RBAC), SESSÕES E AUDITORIA
-- =============================================================================

-- [T01] users: Identidade central de autenticação (3FN: sem dados pessoais de perfil)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'STUDENT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_email_lowercase CHECK (email = LOWER(email))
);

-- [T02] user_profiles: Dados pessoais e institucionais isolados (1:1 com users para LGPD)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    registration_number VARCHAR(50) NOT NULL,
    phone VARCHAR(25),
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id),
    CONSTRAINT uq_user_profiles_registration_number UNIQUE (registration_number),
    CONSTRAINT fk_user_profiles_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- [T03] auth_sessions: Controle de sessões e Refresh Tokens com revogação
CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_auth_sessions_token_hash UNIQUE (refresh_token_hash),
    CONSTRAINT chk_auth_sessions_expiration CHECK (expires_at > created_at),
    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- [T04] audit_logs: Trilha de auditoria imutável (ON DELETE SET NULL preserva histórico)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- =============================================================================
-- 3. DOMÍNIO 2: ESTRUTURA CURRICULAR E GESTÃO ACADÊMICA SENAI
-- =============================================================================

-- [T05] courses: Cursos técnicos profissionalizantes SENAI
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    total_hours INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_courses_code UNIQUE (code),
    CONSTRAINT chk_courses_total_hours_positive CHECK (total_hours > 0)
);

-- [T06] classes: Turmas acadêmicas ofertadas por período letivo
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    code VARCHAR(40) NOT NULL,
    period VARCHAR(20) NOT NULL,
    shift shift_enum NOT NULL,
    max_students INTEGER NOT NULL DEFAULT 40,
    status class_status_enum NOT NULL DEFAULT 'PLANNING',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_classes_code_period UNIQUE (code, period),
    CONSTRAINT chk_classes_max_students CHECK (max_students > 0 AND max_students <= 100),
    CONSTRAINT chk_classes_date_range CHECK (start_date < end_date),
    CONSTRAINT fk_classes_course
        FOREIGN KEY (course_id) REFERENCES courses (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T07] subjects: Disciplinas (Unidades Curriculares) da matriz do curso
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(150) NOT NULL,
    workload_hours INTEGER NOT NULL,
    syllabus TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_subjects_course_code UNIQUE (course_id, code),
    CONSTRAINT chk_subjects_workload_positive CHECK (workload_hours > 0),
    CONSTRAINT fk_subjects_course
        FOREIGN KEY (course_id) REFERENCES courses (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T08] learning_modules: Módulos de Aprendizagem Prática SENAI dentro de uma disciplina
CREATE TABLE learning_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    title VARCHAR(120) NOT NULL,
    order_index INTEGER NOT NULL,
    description TEXT,
    practical_hours INTEGER NOT NULL,
    module_weight NUMERIC(4,2) NOT NULL DEFAULT 1.00,
    passing_score NUMERIC(4,2) NOT NULL DEFAULT 6.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_learning_modules_subject_order UNIQUE (subject_id, order_index),
    CONSTRAINT chk_learning_modules_order_positive CHECK (order_index > 0),
    CONSTRAINT chk_learning_modules_hours_non_negative CHECK (practical_hours >= 0),
    CONSTRAINT chk_learning_modules_weight_positive CHECK (module_weight > 0.00),
    CONSTRAINT chk_learning_modules_passing_score CHECK (passing_score >= 0.00 AND passing_score <= 10.00),
    CONSTRAINT fk_learning_modules_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T09] competencies: Taxonomia de competências e habilidades técnicas SENAI
CREATE TABLE competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    category competency_category_enum NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_competencies_code UNIQUE (code)
);

-- [T10] module_competencies: Tabela Associativa N:M (Chave Primária Composta)
CREATE TABLE module_competencies (
    module_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    required_level INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_module_competencies PRIMARY KEY (module_id, competency_id),
    CONSTRAINT chk_module_competencies_weight CHECK (weight > 0.00 AND weight <= 9.99),
    CONSTRAINT chk_module_competencies_level CHECK (required_level BETWEEN 1 AND 5),
    CONSTRAINT fk_module_competencies_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_module_competencies_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T11] enrollments: Matrícula do Estudante na Turma (3FN: sem duplicar notas/faltas de módulos)
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    class_id UUID NOT NULL,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status enrollment_status_enum NOT NULL DEFAULT 'ACTIVE',
    final_grade NUMERIC(4,2),
    attendance_rate NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_enrollments_student_class UNIQUE (student_id, class_id),
    CONSTRAINT chk_enrollments_final_grade CHECK (final_grade IS NULL OR (final_grade >= 0.00 AND final_grade <= 10.00)),
    CONSTRAINT chk_enrollments_attendance_rate CHECK (attendance_rate IS NULL OR (attendance_rate >= 0.00 AND attendance_rate <= 100.00)),
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_enrollments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T12] student_subjects: Tabela Associativa Aluno-Disciplina (Chave Primária Composta)
-- Modela o vínculo N:M entre a Matrícula do Aluno e as Disciplinas cursadas (aproveitamento/dispensa/status)
CREATE TABLE student_subjects (
    enrollment_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    status enrollment_status_enum NOT NULL DEFAULT 'ACTIVE',
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_student_subjects PRIMARY KEY (enrollment_id, subject_id),
    CONSTRAINT fk_student_subjects_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_subjects_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T13] teacher_assignments: Associação Docente-Turma-Disciplina (Chave Única Composta)
CREATE TABLE teacher_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL,
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_main_teacher BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_teacher_assignments_composite UNIQUE (teacher_id, class_id, subject_id),
    CONSTRAINT fk_teacher_assignments_teacher
        FOREIGN KEY (teacher_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_teacher_assignments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_teacher_assignments_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================================================================
-- 4. DOMÍNIO 3: DIÁRIO DE CLASSE, FREQUÊNCIA E AVALIAÇÕES FORMATIVAS (3FN)
-- =============================================================================

-- [T14] class_lessons: Aulas ministradas e diário de bordo por turma, disciplina e módulo
CREATE TABLE class_lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    teacher_id UUID NOT NULL,
    lesson_date DATE NOT NULL,
    workload_hours INTEGER NOT NULL DEFAULT 4,
    topic_summary TEXT NOT NULL,
    lab_environment VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_class_lessons_workload CHECK (workload_hours BETWEEN 1 AND 8),
    CONSTRAINT fk_class_lessons_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_class_lessons_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_class_lessons_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_class_lessons_teacher
        FOREIGN KEY (teacher_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T15] attendance_records: Registro atômico de presença por aula (3FN: sem redundância entre módulos)
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    status attendance_status_enum NOT NULL DEFAULT 'PRESENT',
    absent_hours INTEGER NOT NULL DEFAULT 0,
    justification_note TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_attendance_lesson_student UNIQUE (lesson_id, student_id),
    CONSTRAINT uq_attendance_lesson_enrollment UNIQUE (lesson_id, enrollment_id),
    CONSTRAINT chk_attendance_absent_hours CHECK (absent_hours >= 0 AND absent_hours <= 8),
    CONSTRAINT fk_attendance_lesson
        FOREIGN KEY (lesson_id) REFERENCES class_lessons (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_attendance_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T16] academic_assessments: Provas teóricas, microavaliações e projetos
CREATE TABLE academic_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    title VARCHAR(150) NOT NULL,
    assessment_type assessment_type_enum NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    application_date DATE NOT NULL,
    max_grade NUMERIC(4,2) NOT NULL DEFAULT 10.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_assessments_weight_positive CHECK (weight > 0.00),
    CONSTRAINT chk_assessments_max_grade CHECK (max_grade > 0.00 AND max_grade <= 10.00),
    CONSTRAINT fk_assessments_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_assessments_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_assessments_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T17] student_grades: Notas atômicas por avaliação formativa (3FN: zero duplicação entre módulos)
CREATE TABLE student_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    recorded_by UUID NOT NULL,
    grade_value NUMERIC(4,2) NOT NULL,
    recovery_grade NUMERIC(4,2),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_grades_assessment_student UNIQUE (assessment_id, student_id),
    CONSTRAINT uq_student_grades_assessment_enrollment UNIQUE (assessment_id, enrollment_id),
    CONSTRAINT chk_student_grades_value CHECK (grade_value >= 0.00 AND grade_value <= 10.00),
    CONSTRAINT chk_student_grades_recovery CHECK (recovery_grade IS NULL OR (recovery_grade >= 0.00 AND recovery_grade <= 10.00)),
    CONSTRAINT fk_student_grades_assessment
        FOREIGN KEY (assessment_id) REFERENCES academic_assessments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_grades_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_grades_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_grades_recorded_by
        FOREIGN KEY (recorded_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================================================================
-- 5. DOMÍNIO 4: OFICINA PRÁTICA, RUBRICAS DE PRECISÃO E ENTREGAS (3FN)
-- =============================================================================

-- [T18] practical_tasks: Tarefas e peças práticas de bancada/oficina
CREATE TABLE practical_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL,
    class_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    blueprint_url VARCHAR(500),
    due_date TIMESTAMPTZ NOT NULL,
    max_score NUMERIC(4,2) NOT NULL DEFAULT 10.00,
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_practical_tasks_max_score CHECK (max_score >= 1.00 AND max_score <= 10.00),
    CONSTRAINT fk_practical_tasks_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_practical_tasks_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T19] task_criteria: Rubricas e critérios técnicos objetivos da tarefa prática
CREATE TABLE task_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    criterion_name VARCHAR(150) NOT NULL,
    weight NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    min_acceptable_level INTEGER NOT NULL DEFAULT 3,
    CONSTRAINT uq_task_criteria_name UNIQUE (task_id, criterion_name),
    CONSTRAINT chk_task_criteria_weight CHECK (weight > 0.00),
    CONSTRAINT chk_task_criteria_level CHECK (min_acceptable_level BETWEEN 1 AND 5),
    CONSTRAINT fk_task_criteria_task
        FOREIGN KEY (task_id) REFERENCES practical_tasks (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_task_criteria_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T20] task_submissions: Entregas de tarefas práticas pelos estudantes
CREATE TABLE task_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    status submission_status_enum NOT NULL DEFAULT 'PENDING',
    completed_at TIMESTAMPTZ,
    evidence_url VARCHAR(500),
    student_notes TEXT,
    final_task_score NUMERIC(4,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_task_submissions_task_student UNIQUE (task_id, student_id),
    CONSTRAINT chk_task_submissions_score CHECK (final_task_score IS NULL OR (final_task_score >= 0.00 AND final_task_score <= 10.00)),
    CONSTRAINT fk_task_submissions_task
        FOREIGN KEY (task_id) REFERENCES practical_tasks (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_task_submissions_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_task_submissions_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T21] submission_evaluations: Avaliação do professor por rubrica da entrega
CREATE TABLE submission_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL,
    criterion_id UUID NOT NULL,
    evaluator_id UUID NOT NULL,
    achieved_level INTEGER NOT NULL,
    score_awarded NUMERIC(4,2) NOT NULL,
    technical_feedback TEXT,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_submission_evaluations_composite UNIQUE (submission_id, criterion_id),
    CONSTRAINT chk_submission_evaluations_level CHECK (achieved_level BETWEEN 1 AND 5),
    CONSTRAINT chk_submission_evaluations_score CHECK (score_awarded >= 0.00 AND score_awarded <= 10.00),
    CONSTRAINT fk_submission_evaluations_submission
        FOREIGN KEY (submission_id) REFERENCES task_submissions (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_submission_evaluations_criterion
        FOREIGN KEY (criterion_id) REFERENCES task_criteria (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_submission_evaluations_evaluator
        FOREIGN KEY (evaluator_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================================================================
-- 6. DOMÍNIO 5: AUTOAVALIAÇÃO, EVIDÊNCIAS, ALERTAS E DIAGNÓSTICO 360° (3FN)
-- =============================================================================

-- [T22] self_assessment_forms: Ciclos de questionários de autoavaliação por módulo
CREATE TABLE self_assessment_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL,
    class_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    instructions TEXT,
    opens_at TIMESTAMPTZ NOT NULL,
    closes_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_self_assessment_forms_dates CHECK (opens_at < closes_at),
    CONSTRAINT fk_self_assessment_forms_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_self_assessment_forms_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_self_assessment_forms_creator
        FOREIGN KEY (created_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T23] student_self_assessments: Respostas de autoavaliação do estudante por competência
CREATE TABLE student_self_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL,
    student_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    perceived_level INTEGER NOT NULL,
    confidence_score INTEGER NOT NULL,
    difficulty_notes TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_self_assessments_composite UNIQUE (form_id, student_id, competency_id),
    CONSTRAINT chk_self_assessments_perceived CHECK (perceived_level BETWEEN 1 AND 5),
    CONSTRAINT chk_self_assessments_confidence CHECK (confidence_score BETWEEN 1 AND 5),
    CONSTRAINT fk_student_self_assessments_form
        FOREIGN KEY (form_id) REFERENCES self_assessment_forms (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_self_assessments_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_student_self_assessments_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T24] skill_evidences: Evidências práticas verificadas pelo docente por competência
CREATE TABLE skill_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    competency_id UUID NOT NULL,
    source_submission_id UUID,
    source_assessment_id UUID,
    verified_level NUMERIC(3,2) NOT NULL,
    verified_by UUID NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_skill_evidences_level CHECK (verified_level >= 1.00 AND verified_level <= 5.00),
    CONSTRAINT chk_skill_evidences_source CHECK (
        source_submission_id IS NOT NULL OR source_assessment_id IS NOT NULL
    ),
    CONSTRAINT fk_skill_evidences_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_skill_evidences_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_skill_evidences_submission
        FOREIGN KEY (source_submission_id) REFERENCES task_submissions (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_skill_evidences_assessment
        FOREIGN KEY (source_assessment_id) REFERENCES academic_assessments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_skill_evidences_verifier
        FOREIGN KEY (verified_by) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T25] academic_alerts: Alertas precoces e explicáveis de risco acadêmico
CREATE TABLE academic_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    class_id UUID NOT NULL,
    module_id UUID,
    risk_level risk_level_enum NOT NULL,
    alert_category alert_category_enum NOT NULL,
    explainable_reason TEXT NOT NULL,
    metric_snapshot JSONB NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'ACTIVE',
    resolved_by UUID,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_academic_alerts_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_academic_alerts_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_academic_alerts_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_academic_alerts_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_academic_alerts_resolver
        FOREIGN KEY (resolved_by) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- [T26] explainable_diagnostics: Diagnósticos comparativos (Percepção Discente vs Evidência Docente)
CREATE TABLE explainable_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    class_id UUID NOT NULL,
    module_id UUID NOT NULL,
    competency_id UUID,
    self_perceived_level NUMERIC(3,2) NOT NULL,
    teacher_verified_level NUMERIC(3,2) NOT NULL,
    discrepancy_gap NUMERIC(3,2) NOT NULL,
    diagnostic_type diagnostic_type_enum NOT NULL,
    explanation_text TEXT NOT NULL,
    limitations_note TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_diagnostics_self_level CHECK (self_perceived_level BETWEEN 1.00 AND 5.00),
    CONSTRAINT chk_diagnostics_teacher_level CHECK (teacher_verified_level BETWEEN 1.00 AND 5.00),
    CONSTRAINT fk_diagnostics_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_diagnostics_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_diagnostics_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_diagnostics_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T27] student_milestone_history: Linha do tempo e marcos de evolução do estudante
CREATE TABLE student_milestone_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    module_id UUID,
    milestone_type milestone_type_enum NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    metadata JSONB,
    achieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_milestone_history_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_milestone_history_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_milestone_history_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================================================================
-- 7. DOMÍNIO 6: COMUNICAÇÃO, APOIO CONFIDENCIAL, NOTAS PEDAGÓGICAS E GAMIFICAÇÃO
-- =============================================================================

-- [T28] class_announcements: Mural de avisos oficiais da turma
CREATE TABLE class_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    subject_id UUID,
    author_id UUID NOT NULL,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    priority announcement_priority_enum NOT NULL DEFAULT 'NORMAL',
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    CONSTRAINT chk_announcements_expiration CHECK (expires_at IS NULL OR expires_at > published_at),
    CONSTRAINT fk_announcements_class
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_announcements_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_announcements_author
        FOREIGN KEY (author_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T29] help_requests: Solicitações de apoio e mentoria confidenciais
CREATE TABLE help_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    module_id UUID,
    assigned_teacher_id UUID,
    category help_request_category_enum NOT NULL,
    subject_title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    is_confidential BOOLEAN NOT NULL DEFAULT TRUE,
    status help_request_status_enum NOT NULL DEFAULT 'OPEN',
    resolution_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    CONSTRAINT fk_help_requests_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_subject
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_module
        FOREIGN KEY (module_id) REFERENCES learning_modules (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_help_requests_teacher
        FOREIGN KEY (assigned_teacher_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- [T30] pedagogical_notes: Observações pedagógicas restritas (Isoladas e criptografadas AES-256)
CREATE TABLE pedagogical_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    author_id UUID NOT NULL,
    visibility_scope note_visibility_scope_enum NOT NULL DEFAULT 'PRIVATE_AUTHOR',
    category note_category_enum NOT NULL,
    note_content TEXT NOT NULL,
    requires_followup BOOLEAN NOT NULL DEFAULT FALSE,
    followup_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedagogical_notes_student
        FOREIGN KEY (student_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pedagogical_notes_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pedagogical_notes_author
        FOREIGN KEY (author_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T31] chat_messages: Mensagens privadas dentro de solicitações de apoio
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    help_request_id UUID NOT NULL,
    sender_id UUID NOT NULL,
    message_body TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_messages_help_request
        FOREIGN KEY (help_request_id) REFERENCES help_requests (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_chat_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T32] gamification_badges: Catálogo de insígnias pedagógicas transparentes
CREATE TABLE gamification_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(60) NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    criteria_explanation TEXT NOT NULL,
    icon_name VARCHAR(80) NOT NULL,
    xp_reward INTEGER NOT NULL DEFAULT 50,
    competency_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_gamification_badges_code UNIQUE (code),
    CONSTRAINT chk_gamification_badges_xp_positive CHECK (xp_reward > 0),
    CONSTRAINT fk_gamification_badges_competency
        FOREIGN KEY (competency_id) REFERENCES competencies (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- [T33] student_achievements: Conquistas desbloqueadas pelos estudantes (Chave Única Composta)
CREATE TABLE student_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    enrollment_id UUID NOT NULL,
    badge_id UUID NOT NULL,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origin_reference VARCHAR(150) NOT NULL,
    CONSTRAINT uq_student_achievements_composite UNIQUE (student_id, badge_id),
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

COMMIT;
