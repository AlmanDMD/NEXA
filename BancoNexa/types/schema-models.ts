/**
 * ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate`
 * Tipos TypeScript dos Modelos Prisma / Tabelas PostgreSQL 16 (Projeto NEXA)
 * Sincronizado com `prisma/schema.prisma` (camelCase na aplicação e snake_case no SQL).
 */

import type { AlertCategory, AlertStatus, AnnouncementPriority, AssessmentType, AttendanceStatus, ClassStatus, CompetencyCategory, DiagnosticType, EnrollmentStatus, HelpRequestCategory, HelpRequestStatus, MilestoneType, NoteCategory, NoteVisibilityScope, RiskLevel, Role, Shift, SubmissionStatus } from './system-enums';

/** Modelo Prisma `SchemaMigration` mapeado para a tabela PostgreSQL `schema_migrations` */
export interface SchemaMigration {
  id: string;
  version: string;
  migrationName: string;
  checksumSha256: string;
  executionTimeMs: number;
  appliedBy: string;
  appliedAt: Date;
}

/** Registro SQL snake_case da tabela `schema_migrations` */
export interface SchemaMigrationRow {
  id: string;
  version: string;
  migration_name: string;
  checksum_sha256: string;
  execution_time_ms: number;
  applied_by: string;
  applied_at: Date;
}

/** Payload de criação para `SchemaMigration` */
export interface SchemaMigrationCreateInput {
  id?: string;
  version: string;
  migrationName: string;
  checksumSha256: string;
  executionTimeMs?: number;
  appliedBy?: string;
  appliedAt?: Date;
}

/** Payload de atualização parcial para `SchemaMigration` */
export type SchemaMigrationUpdateInput = Partial<Omit<SchemaMigrationCreateInput, 'id'>>;

/** Modelo Prisma `User` mapeado para a tabela PostgreSQL `users` */
export interface User {
  id: string;
  email: string;
  passwordHash: string;
  role: Role;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `users` */
export interface UserRow {
  id: string;
  email: string;
  password_hash: string;
  role: Role;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `User` */
export interface UserCreateInput {
  id?: string;
  email: string;
  passwordHash: string;
  role?: Role;
  isActive?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `User` */
export type UserUpdateInput = Partial<Omit<UserCreateInput, 'id'>>;

/** Modelo Prisma `UserProfile` mapeado para a tabela PostgreSQL `user_profiles` */
export interface UserProfile {
  id: string;
  userId: string;
  fullName: string;
  registrationNumber: string;
  phone: string | null;
  avatarUrl: string | null;
  bio: string | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `user_profiles` */
export interface UserProfileRow {
  id: string;
  user_id: string;
  full_name: string;
  registration_number: string;
  phone: string | null;
  avatar_url: string | null;
  bio: string | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `UserProfile` */
export interface UserProfileCreateInput {
  id?: string;
  userId: string;
  fullName: string;
  registrationNumber: string;
  phone?: string | null;
  avatarUrl?: string | null;
  bio?: string | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `UserProfile` */
export type UserProfileUpdateInput = Partial<Omit<UserProfileCreateInput, 'id'>>;

/** Modelo Prisma `AuthSession` mapeado para a tabela PostgreSQL `auth_sessions` */
export interface AuthSession {
  id: string;
  userId: string;
  refreshTokenHash: string;
  userAgent: string | null;
  ipAddress: string | null;
  expiresAt: Date;
  isRevoked: boolean;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `auth_sessions` */
export interface AuthSessionRow {
  id: string;
  user_id: string;
  refresh_token_hash: string;
  user_agent: string | null;
  ip_address: string | null;
  expires_at: Date;
  is_revoked: boolean;
  created_at: Date;
}

/** Payload de criação para `AuthSession` */
export interface AuthSessionCreateInput {
  id?: string;
  userId: string;
  refreshTokenHash: string;
  userAgent?: string | null;
  ipAddress?: string | null;
  expiresAt: Date;
  isRevoked?: boolean;
  createdAt?: Date;
}

/** Payload de atualização parcial para `AuthSession` */
export type AuthSessionUpdateInput = Partial<Omit<AuthSessionCreateInput, 'id'>>;

/** Modelo Prisma `AuditLog` mapeado para a tabela PostgreSQL `audit_logs` */
export interface AuditLog {
  id: string;
  userId: string | null;
  action: string;
  entity: string;
  entityId: string;
  oldValues: Record<string, unknown> | null;
  newValues: Record<string, unknown> | null;
  ipAddress: string | null;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `audit_logs` */
export interface AuditLogRow {
  id: string;
  user_id: string | null;
  action: string;
  entity: string;
  entity_id: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: Date;
}

/** Payload de criação para `AuditLog` */
export interface AuditLogCreateInput {
  id?: string;
  userId?: string | null;
  action: string;
  entity: string;
  entityId: string;
  oldValues?: Record<string, unknown> | null;
  newValues?: Record<string, unknown> | null;
  ipAddress?: string | null;
  createdAt?: Date;
}

/** Payload de atualização parcial para `AuditLog` */
export type AuditLogUpdateInput = Partial<Omit<AuditLogCreateInput, 'id'>>;

/** Modelo Prisma `Course` mapeado para a tabela PostgreSQL `courses` */
export interface Course {
  id: string;
  code: string;
  name: string;
  description: string | null;
  totalHours: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `courses` */
export interface CourseRow {
  id: string;
  code: string;
  name: string;
  description: string | null;
  total_hours: number;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `Course` */
export interface CourseCreateInput {
  id?: string;
  code: string;
  name: string;
  description?: string | null;
  totalHours: number;
  isActive?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `Course` */
export type CourseUpdateInput = Partial<Omit<CourseCreateInput, 'id'>>;

/** Modelo Prisma `Class` mapeado para a tabela PostgreSQL `classes` */
export interface Class {
  id: string;
  courseId: string;
  code: string;
  period: string;
  shift: Shift;
  maxStudents: number;
  status: ClassStatus;
  startDate: Date;
  endDate: Date;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `classes` */
export interface ClassRow {
  id: string;
  course_id: string;
  code: string;
  period: string;
  shift: Shift;
  max_students: number;
  status: ClassStatus;
  start_date: Date;
  end_date: Date;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `Class` */
export interface ClassCreateInput {
  id?: string;
  courseId: string;
  code: string;
  period: string;
  shift: Shift;
  maxStudents?: number;
  status?: ClassStatus;
  startDate: Date;
  endDate: Date;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `Class` */
export type ClassUpdateInput = Partial<Omit<ClassCreateInput, 'id'>>;

/** Modelo Prisma `Subject` mapeado para a tabela PostgreSQL `subjects` */
export interface Subject {
  id: string;
  courseId: string;
  code: string;
  name: string;
  workloadHours: number;
  syllabus: string | null;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `subjects` */
export interface SubjectRow {
  id: string;
  course_id: string;
  code: string;
  name: string;
  workload_hours: number;
  syllabus: string | null;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `Subject` */
export interface SubjectCreateInput {
  id?: string;
  courseId: string;
  code: string;
  name: string;
  workloadHours: number;
  syllabus?: string | null;
  isActive?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `Subject` */
export type SubjectUpdateInput = Partial<Omit<SubjectCreateInput, 'id'>>;

/** Modelo Prisma `LearningModule` mapeado para a tabela PostgreSQL `learning_modules` */
export interface LearningModule {
  id: string;
  subjectId: string;
  title: string;
  orderIndex: number;
  description: string | null;
  practicalHours: number;
  moduleWeight: number | string;
  passingScore: number | string;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `learning_modules` */
export interface LearningModuleRow {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
  description: string | null;
  practical_hours: number;
  module_weight: number | string;
  passing_score: number | string;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `LearningModule` */
export interface LearningModuleCreateInput {
  id?: string;
  subjectId: string;
  title: string;
  orderIndex: number;
  description?: string | null;
  practicalHours: number;
  moduleWeight?: number | string;
  passingScore?: number | string;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `LearningModule` */
export type LearningModuleUpdateInput = Partial<Omit<LearningModuleCreateInput, 'id'>>;

/** Modelo Prisma `Competency` mapeado para a tabela PostgreSQL `competencies` */
export interface Competency {
  id: string;
  code: string;
  title: string;
  category: CompetencyCategory;
  description: string | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `competencies` */
export interface CompetencyRow {
  id: string;
  code: string;
  title: string;
  category: CompetencyCategory;
  description: string | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `Competency` */
export interface CompetencyCreateInput {
  id?: string;
  code: string;
  title: string;
  category: CompetencyCategory;
  description?: string | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `Competency` */
export type CompetencyUpdateInput = Partial<Omit<CompetencyCreateInput, 'id'>>;

/** Modelo Prisma `ModuleCompetency` mapeado para a tabela PostgreSQL `module_competencies` */
export interface ModuleCompetency {
  moduleId: string;
  competencyId: string;
  weight: number | string;
  requiredLevel: number;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `module_competencies` */
export interface ModuleCompetencyRow {
  module_id: string;
  competency_id: string;
  weight: number | string;
  required_level: number;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `ModuleCompetency` */
export interface ModuleCompetencyCreateInput {
  moduleId: string;
  competencyId: string;
  weight?: number | string;
  requiredLevel?: number;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `ModuleCompetency` */
export type ModuleCompetencyUpdateInput = Partial<Omit<ModuleCompetencyCreateInput, 'id'>>;

/** Modelo Prisma `Enrollment` mapeado para a tabela PostgreSQL `enrollments` */
export interface Enrollment {
  id: string;
  studentId: string;
  classId: string;
  enrollmentDate: Date;
  status: EnrollmentStatus;
  finalGrade: number | string | null;
  attendanceRate: number | string | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `enrollments` */
export interface EnrollmentRow {
  id: string;
  student_id: string;
  class_id: string;
  enrollment_date: Date;
  status: EnrollmentStatus;
  final_grade: number | string | null;
  attendance_rate: number | string | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `Enrollment` */
export interface EnrollmentCreateInput {
  id?: string;
  studentId: string;
  classId: string;
  enrollmentDate?: Date;
  status?: EnrollmentStatus;
  finalGrade?: number | string | null;
  attendanceRate?: number | string | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `Enrollment` */
export type EnrollmentUpdateInput = Partial<Omit<EnrollmentCreateInput, 'id'>>;

/** Modelo Prisma `TeacherAssignment` mapeado para a tabela PostgreSQL `teacher_assignments` */
export interface TeacherAssignment {
  id: string;
  teacherId: string;
  classId: string;
  subjectId: string;
  assignedAt: Date;
  isMainTeacher: boolean;
}

/** Registro SQL snake_case da tabela `teacher_assignments` */
export interface TeacherAssignmentRow {
  id: string;
  teacher_id: string;
  class_id: string;
  subject_id: string;
  assigned_at: Date;
  is_main_teacher: boolean;
}

/** Payload de criação para `TeacherAssignment` */
export interface TeacherAssignmentCreateInput {
  id?: string;
  teacherId: string;
  classId: string;
  subjectId: string;
  assignedAt?: Date;
  isMainTeacher?: boolean;
}

/** Payload de atualização parcial para `TeacherAssignment` */
export type TeacherAssignmentUpdateInput = Partial<Omit<TeacherAssignmentCreateInput, 'id'>>;

/** Modelo Prisma `ClassLesson` mapeado para a tabela PostgreSQL `class_lessons` */
export interface ClassLesson {
  id: string;
  classId: string;
  subjectId: string;
  moduleId: string | null;
  teacherId: string;
  lessonDate: Date;
  workloadHours: number;
  topicSummary: string;
  labEnvironment: string | null;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `class_lessons` */
export interface ClassLessonRow {
  id: string;
  class_id: string;
  subject_id: string;
  module_id: string | null;
  teacher_id: string;
  lesson_date: Date;
  workload_hours: number;
  topic_summary: string;
  lab_environment: string | null;
  created_at: Date;
}

/** Payload de criação para `ClassLesson` */
export interface ClassLessonCreateInput {
  id?: string;
  classId: string;
  subjectId: string;
  moduleId?: string | null;
  teacherId: string;
  lessonDate: Date;
  workloadHours?: number;
  topicSummary: string;
  labEnvironment?: string | null;
  createdAt?: Date;
}

/** Payload de atualização parcial para `ClassLesson` */
export type ClassLessonUpdateInput = Partial<Omit<ClassLessonCreateInput, 'id'>>;

/** Modelo Prisma `AttendanceRecord` mapeado para a tabela PostgreSQL `attendance_records` */
export interface AttendanceRecord {
  id: string;
  lessonId: string;
  enrollmentId: string;
  studentId: string;
  status: AttendanceStatus;
  absentHours: number;
  justificationNote: string | null;
  recordedAt: Date;
}

/** Registro SQL snake_case da tabela `attendance_records` */
export interface AttendanceRecordRow {
  id: string;
  lesson_id: string;
  enrollment_id: string;
  student_id: string;
  status: AttendanceStatus;
  absent_hours: number;
  justification_note: string | null;
  recorded_at: Date;
}

/** Payload de criação para `AttendanceRecord` */
export interface AttendanceRecordCreateInput {
  id?: string;
  lessonId: string;
  enrollmentId: string;
  studentId: string;
  status?: AttendanceStatus;
  absentHours?: number;
  justificationNote?: string | null;
  recordedAt?: Date;
}

/** Payload de atualização parcial para `AttendanceRecord` */
export type AttendanceRecordUpdateInput = Partial<Omit<AttendanceRecordCreateInput, 'id'>>;

/** Modelo Prisma `PracticalTask` mapeado para a tabela PostgreSQL `practical_tasks` */
export interface PracticalTask {
  id: string;
  moduleId: string;
  classId: string;
  title: string;
  description: string | null;
  blueprintUrl: string | null;
  dueDate: Date;
  maxScore: number | string;
  isMandatory: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `practical_tasks` */
export interface PracticalTaskRow {
  id: string;
  module_id: string;
  class_id: string;
  title: string;
  description: string | null;
  blueprint_url: string | null;
  due_date: Date;
  max_score: number | string;
  is_mandatory: boolean;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `PracticalTask` */
export interface PracticalTaskCreateInput {
  id?: string;
  moduleId: string;
  classId: string;
  title: string;
  description?: string | null;
  blueprintUrl?: string | null;
  dueDate: Date;
  maxScore?: number | string;
  isMandatory?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `PracticalTask` */
export type PracticalTaskUpdateInput = Partial<Omit<PracticalTaskCreateInput, 'id'>>;

/** Modelo Prisma `TaskCriterion` mapeado para a tabela PostgreSQL `task_criteria` */
export interface TaskCriterion {
  id: string;
  taskId: string;
  competencyId: string;
  criterionName: string;
  weight: number | string;
  minAcceptableLevel: number;
}

/** Registro SQL snake_case da tabela `task_criteria` */
export interface TaskCriterionRow {
  id: string;
  task_id: string;
  competency_id: string;
  criterion_name: string;
  weight: number | string;
  min_acceptable_level: number;
}

/** Payload de criação para `TaskCriterion` */
export interface TaskCriterionCreateInput {
  id?: string;
  taskId: string;
  competencyId: string;
  criterionName: string;
  weight?: number | string;
  minAcceptableLevel?: number;
}

/** Payload de atualização parcial para `TaskCriterion` */
export type TaskCriterionUpdateInput = Partial<Omit<TaskCriterionCreateInput, 'id'>>;

/** Modelo Prisma `TaskSubmission` mapeado para a tabela PostgreSQL `task_submissions` */
export interface TaskSubmission {
  id: string;
  taskId: string;
  studentId: string;
  enrollmentId: string;
  status: SubmissionStatus;
  completedAt: Date | null;
  evidenceUrl: string | null;
  studentNotes: string | null;
  finalTaskScore: number | string | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `task_submissions` */
export interface TaskSubmissionRow {
  id: string;
  task_id: string;
  student_id: string;
  enrollment_id: string;
  status: SubmissionStatus;
  completed_at: Date | null;
  evidence_url: string | null;
  student_notes: string | null;
  final_task_score: number | string | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `TaskSubmission` */
export interface TaskSubmissionCreateInput {
  id?: string;
  taskId: string;
  studentId: string;
  enrollmentId: string;
  status?: SubmissionStatus;
  completedAt?: Date | null;
  evidenceUrl?: string | null;
  studentNotes?: string | null;
  finalTaskScore?: number | string | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `TaskSubmission` */
export type TaskSubmissionUpdateInput = Partial<Omit<TaskSubmissionCreateInput, 'id'>>;

/** Modelo Prisma `SubmissionEvaluation` mapeado para a tabela PostgreSQL `submission_evaluations` */
export interface SubmissionEvaluation {
  id: string;
  submissionId: string;
  criterionId: string;
  evaluatorId: string;
  achievedLevel: number;
  scoreAwarded: number | string;
  technicalFeedback: string | null;
  evaluatedAt: Date;
}

/** Registro SQL snake_case da tabela `submission_evaluations` */
export interface SubmissionEvaluationRow {
  id: string;
  submission_id: string;
  criterion_id: string;
  evaluator_id: string;
  achieved_level: number;
  score_awarded: number | string;
  technical_feedback: string | null;
  evaluated_at: Date;
}

/** Payload de criação para `SubmissionEvaluation` */
export interface SubmissionEvaluationCreateInput {
  id?: string;
  submissionId: string;
  criterionId: string;
  evaluatorId: string;
  achievedLevel: number;
  scoreAwarded: number | string;
  technicalFeedback?: string | null;
  evaluatedAt?: Date;
}

/** Payload de atualização parcial para `SubmissionEvaluation` */
export type SubmissionEvaluationUpdateInput = Partial<Omit<SubmissionEvaluationCreateInput, 'id'>>;

/** Modelo Prisma `AcademicAssessment` mapeado para a tabela PostgreSQL `academic_assessments` */
export interface AcademicAssessment {
  id: string;
  classId: string;
  subjectId: string;
  moduleId: string | null;
  title: string;
  assessmentType: AssessmentType;
  weight: number | string;
  applicationDate: Date;
  maxGrade: number | string;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `academic_assessments` */
export interface AcademicAssessmentRow {
  id: string;
  class_id: string;
  subject_id: string;
  module_id: string | null;
  title: string;
  assessment_type: AssessmentType;
  weight: number | string;
  application_date: Date;
  max_grade: number | string;
  created_at: Date;
}

/** Payload de criação para `AcademicAssessment` */
export interface AcademicAssessmentCreateInput {
  id?: string;
  classId: string;
  subjectId: string;
  moduleId?: string | null;
  title: string;
  assessmentType: AssessmentType;
  weight?: number | string;
  applicationDate: Date;
  maxGrade?: number | string;
  createdAt?: Date;
}

/** Payload de atualização parcial para `AcademicAssessment` */
export type AcademicAssessmentUpdateInput = Partial<Omit<AcademicAssessmentCreateInput, 'id'>>;

/** Modelo Prisma `StudentGrade` mapeado para a tabela PostgreSQL `student_grades` */
export interface StudentGrade {
  id: string;
  assessmentId: string;
  enrollmentId: string;
  studentId: string;
  recordedBy: string;
  gradeValue: number | string;
  recoveryGrade: number | string | null;
  comments: string | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `student_grades` */
export interface StudentGradeRow {
  id: string;
  assessment_id: string;
  enrollment_id: string;
  student_id: string;
  recorded_by: string;
  grade_value: number | string;
  recovery_grade: number | string | null;
  comments: string | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `StudentGrade` */
export interface StudentGradeCreateInput {
  id?: string;
  assessmentId: string;
  enrollmentId: string;
  studentId: string;
  recordedBy: string;
  gradeValue: number | string;
  recoveryGrade?: number | string | null;
  comments?: string | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `StudentGrade` */
export type StudentGradeUpdateInput = Partial<Omit<StudentGradeCreateInput, 'id'>>;

/** Modelo Prisma `SelfAssessmentForm` mapeado para a tabela PostgreSQL `self_assessment_forms` */
export interface SelfAssessmentForm {
  id: string;
  moduleId: string;
  classId: string;
  title: string;
  instructions: string | null;
  opensAt: Date;
  closesAt: Date;
  isActive: boolean;
  createdBy: string;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `self_assessment_forms` */
export interface SelfAssessmentFormRow {
  id: string;
  module_id: string;
  class_id: string;
  title: string;
  instructions: string | null;
  opens_at: Date;
  closes_at: Date;
  is_active: boolean;
  created_by: string;
  created_at: Date;
}

/** Payload de criação para `SelfAssessmentForm` */
export interface SelfAssessmentFormCreateInput {
  id?: string;
  moduleId: string;
  classId: string;
  title: string;
  instructions?: string | null;
  opensAt: Date;
  closesAt: Date;
  isActive?: boolean;
  createdBy: string;
  createdAt?: Date;
}

/** Payload de atualização parcial para `SelfAssessmentForm` */
export type SelfAssessmentFormUpdateInput = Partial<Omit<SelfAssessmentFormCreateInput, 'id'>>;

/** Modelo Prisma `StudentSelfAssessment` mapeado para a tabela PostgreSQL `student_self_assessments` */
export interface StudentSelfAssessment {
  id: string;
  formId: string;
  studentId: string;
  competencyId: string;
  perceivedLevel: number;
  confidenceScore: number;
  difficultyNotes: string | null;
  submittedAt: Date;
}

/** Registro SQL snake_case da tabela `student_self_assessments` */
export interface StudentSelfAssessmentRow {
  id: string;
  form_id: string;
  student_id: string;
  competency_id: string;
  perceived_level: number;
  confidence_score: number;
  difficulty_notes: string | null;
  submitted_at: Date;
}

/** Payload de criação para `StudentSelfAssessment` */
export interface StudentSelfAssessmentCreateInput {
  id?: string;
  formId: string;
  studentId: string;
  competencyId: string;
  perceivedLevel: number;
  confidenceScore: number;
  difficultyNotes?: string | null;
  submittedAt?: Date;
}

/** Payload de atualização parcial para `StudentSelfAssessment` */
export type StudentSelfAssessmentUpdateInput = Partial<Omit<StudentSelfAssessmentCreateInput, 'id'>>;

/** Modelo Prisma `SkillEvidence` mapeado para a tabela PostgreSQL `skill_evidences` */
export interface SkillEvidence {
  id: string;
  studentId: string;
  competencyId: string;
  sourceSubmissionId: string | null;
  sourceAssessmentId: string | null;
  verifiedLevel: number | string;
  verifiedBy: string;
  recordedAt: Date;
}

/** Registro SQL snake_case da tabela `skill_evidences` */
export interface SkillEvidenceRow {
  id: string;
  student_id: string;
  competency_id: string;
  source_submission_id: string | null;
  source_assessment_id: string | null;
  verified_level: number | string;
  verified_by: string;
  recorded_at: Date;
}

/** Payload de criação para `SkillEvidence` */
export interface SkillEvidenceCreateInput {
  id?: string;
  studentId: string;
  competencyId: string;
  sourceSubmissionId?: string | null;
  sourceAssessmentId?: string | null;
  verifiedLevel: number | string;
  verifiedBy: string;
  recordedAt?: Date;
}

/** Payload de atualização parcial para `SkillEvidence` */
export type SkillEvidenceUpdateInput = Partial<Omit<SkillEvidenceCreateInput, 'id'>>;

/** Modelo Prisma `AcademicAlert` mapeado para a tabela PostgreSQL `academic_alerts` */
export interface AcademicAlert {
  id: string;
  studentId: string;
  enrollmentId: string;
  classId: string;
  moduleId: string | null;
  riskLevel: RiskLevel;
  alertCategory: AlertCategory;
  explainableReason: string;
  metricSnapshot: Record<string, unknown>;
  status: AlertStatus;
  resolvedBy: string | null;
  resolutionNotes: string | null;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `academic_alerts` */
export interface AcademicAlertRow {
  id: string;
  student_id: string;
  enrollment_id: string;
  class_id: string;
  module_id: string | null;
  risk_level: RiskLevel;
  alert_category: AlertCategory;
  explainable_reason: string;
  metric_snapshot: Record<string, unknown>;
  status: AlertStatus;
  resolved_by: string | null;
  resolution_notes: string | null;
  created_at: Date;
}

/** Payload de criação para `AcademicAlert` */
export interface AcademicAlertCreateInput {
  id?: string;
  studentId: string;
  enrollmentId: string;
  classId: string;
  moduleId?: string | null;
  riskLevel: RiskLevel;
  alertCategory: AlertCategory;
  explainableReason: string;
  metricSnapshot: Record<string, unknown>;
  status?: AlertStatus;
  resolvedBy?: string | null;
  resolutionNotes?: string | null;
  createdAt?: Date;
}

/** Payload de atualização parcial para `AcademicAlert` */
export type AcademicAlertUpdateInput = Partial<Omit<AcademicAlertCreateInput, 'id'>>;

/** Modelo Prisma `ExplainableDiagnostic` mapeado para a tabela PostgreSQL `explainable_diagnostics` */
export interface ExplainableDiagnostic {
  id: string;
  studentId: string;
  classId: string;
  moduleId: string;
  competencyId: string | null;
  selfPerceivedLevel: number | string;
  teacherVerifiedLevel: number | string;
  discrepancyGap: number | string;
  diagnosticType: DiagnosticType;
  explanationText: string;
  limitationsNote: string;
  recommendedAction: string;
  generatedAt: Date;
}

/** Registro SQL snake_case da tabela `explainable_diagnostics` */
export interface ExplainableDiagnosticRow {
  id: string;
  student_id: string;
  class_id: string;
  module_id: string;
  competency_id: string | null;
  self_perceived_level: number | string;
  teacher_verified_level: number | string;
  discrepancy_gap: number | string;
  diagnostic_type: DiagnosticType;
  explanation_text: string;
  limitations_note: string;
  recommended_action: string;
  generated_at: Date;
}

/** Payload de criação para `ExplainableDiagnostic` */
export interface ExplainableDiagnosticCreateInput {
  id?: string;
  studentId: string;
  classId: string;
  moduleId: string;
  competencyId?: string | null;
  selfPerceivedLevel: number | string;
  teacherVerifiedLevel: number | string;
  discrepancyGap: number | string;
  diagnosticType: DiagnosticType;
  explanationText: string;
  limitationsNote: string;
  recommendedAction: string;
  generatedAt?: Date;
}

/** Payload de atualização parcial para `ExplainableDiagnostic` */
export type ExplainableDiagnosticUpdateInput = Partial<Omit<ExplainableDiagnosticCreateInput, 'id'>>;

/** Modelo Prisma `StudentMilestoneHistory` mapeado para a tabela PostgreSQL `student_milestone_history` */
export interface StudentMilestoneHistory {
  id: string;
  studentId: string;
  enrollmentId: string;
  moduleId: string | null;
  milestoneType: MilestoneType;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  achievedAt: Date;
}

/** Registro SQL snake_case da tabela `student_milestone_history` */
export interface StudentMilestoneHistoryRow {
  id: string;
  student_id: string;
  enrollment_id: string;
  module_id: string | null;
  milestone_type: MilestoneType;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  achieved_at: Date;
}

/** Payload de criação para `StudentMilestoneHistory` */
export interface StudentMilestoneHistoryCreateInput {
  id?: string;
  studentId: string;
  enrollmentId: string;
  moduleId?: string | null;
  milestoneType: MilestoneType;
  title: string;
  description?: string | null;
  metadata?: Record<string, unknown> | null;
  achievedAt?: Date;
}

/** Payload de atualização parcial para `StudentMilestoneHistory` */
export type StudentMilestoneHistoryUpdateInput = Partial<Omit<StudentMilestoneHistoryCreateInput, 'id'>>;

/** Modelo Prisma `ClassAnnouncement` mapeado para a tabela PostgreSQL `class_announcements` */
export interface ClassAnnouncement {
  id: string;
  classId: string;
  subjectId: string | null;
  authorId: string;
  title: string;
  content: string;
  priority: AnnouncementPriority;
  isPinned: boolean;
  publishedAt: Date;
  expiresAt: Date | null;
}

/** Registro SQL snake_case da tabela `class_announcements` */
export interface ClassAnnouncementRow {
  id: string;
  class_id: string;
  subject_id: string | null;
  author_id: string;
  title: string;
  content: string;
  priority: AnnouncementPriority;
  is_pinned: boolean;
  published_at: Date;
  expires_at: Date | null;
}

/** Payload de criação para `ClassAnnouncement` */
export interface ClassAnnouncementCreateInput {
  id?: string;
  classId: string;
  subjectId?: string | null;
  authorId: string;
  title: string;
  content: string;
  priority?: AnnouncementPriority;
  isPinned?: boolean;
  publishedAt?: Date;
  expiresAt?: Date | null;
}

/** Payload de atualização parcial para `ClassAnnouncement` */
export type ClassAnnouncementUpdateInput = Partial<Omit<ClassAnnouncementCreateInput, 'id'>>;

/** Modelo Prisma `HelpRequest` mapeado para a tabela PostgreSQL `help_requests` */
export interface HelpRequest {
  id: string;
  studentId: string;
  enrollmentId: string;
  subjectId: string;
  moduleId: string | null;
  assignedTeacherId: string | null;
  category: HelpRequestCategory;
  subjectTitle: string;
  description: string;
  isConfidential: boolean;
  status: HelpRequestStatus;
  resolutionSummary: string | null;
  createdAt: Date;
  updatedAt: Date;
  closedAt: Date | null;
}

/** Registro SQL snake_case da tabela `help_requests` */
export interface HelpRequestRow {
  id: string;
  student_id: string;
  enrollment_id: string;
  subject_id: string;
  module_id: string | null;
  assigned_teacher_id: string | null;
  category: HelpRequestCategory;
  subject_title: string;
  description: string;
  is_confidential: boolean;
  status: HelpRequestStatus;
  resolution_summary: string | null;
  created_at: Date;
  updated_at: Date;
  closed_at: Date | null;
}

/** Payload de criação para `HelpRequest` */
export interface HelpRequestCreateInput {
  id?: string;
  studentId: string;
  enrollmentId: string;
  subjectId: string;
  moduleId?: string | null;
  assignedTeacherId?: string | null;
  category: HelpRequestCategory;
  subjectTitle: string;
  description: string;
  isConfidential?: boolean;
  status?: HelpRequestStatus;
  resolutionSummary?: string | null;
  createdAt?: Date;
  updatedAt?: Date;
  closedAt?: Date | null;
}

/** Payload de atualização parcial para `HelpRequest` */
export type HelpRequestUpdateInput = Partial<Omit<HelpRequestCreateInput, 'id'>>;

/** Modelo Prisma `PedagogicalNote` mapeado para a tabela PostgreSQL `pedagogical_notes` */
export interface PedagogicalNote {
  id: string;
  studentId: string;
  enrollmentId: string;
  authorId: string;
  visibilityScope: NoteVisibilityScope;
  category: NoteCategory;
  noteContent: string;
  requiresFollowup: boolean;
  followupDate: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

/** Registro SQL snake_case da tabela `pedagogical_notes` */
export interface PedagogicalNoteRow {
  id: string;
  student_id: string;
  enrollment_id: string;
  author_id: string;
  visibility_scope: NoteVisibilityScope;
  category: NoteCategory;
  note_content: string;
  requires_followup: boolean;
  followup_date: Date | null;
  created_at: Date;
  updated_at: Date;
}

/** Payload de criação para `PedagogicalNote` */
export interface PedagogicalNoteCreateInput {
  id?: string;
  studentId: string;
  enrollmentId: string;
  authorId: string;
  visibilityScope?: NoteVisibilityScope;
  category: NoteCategory;
  noteContent: string;
  requiresFollowup?: boolean;
  followupDate?: Date | null;
  createdAt?: Date;
  updatedAt?: Date;
}

/** Payload de atualização parcial para `PedagogicalNote` */
export type PedagogicalNoteUpdateInput = Partial<Omit<PedagogicalNoteCreateInput, 'id'>>;

/** Modelo Prisma `ChatMessage` mapeado para a tabela PostgreSQL `chat_messages` */
export interface ChatMessage {
  id: string;
  helpRequestId: string;
  senderId: string;
  messageBody: string;
  isRead: boolean;
  readAt: Date | null;
  sentAt: Date;
}

/** Registro SQL snake_case da tabela `chat_messages` */
export interface ChatMessageRow {
  id: string;
  help_request_id: string;
  sender_id: string;
  message_body: string;
  is_read: boolean;
  read_at: Date | null;
  sent_at: Date;
}

/** Payload de criação para `ChatMessage` */
export interface ChatMessageCreateInput {
  id?: string;
  helpRequestId: string;
  senderId: string;
  messageBody: string;
  isRead?: boolean;
  readAt?: Date | null;
  sentAt?: Date;
}

/** Payload de atualização parcial para `ChatMessage` */
export type ChatMessageUpdateInput = Partial<Omit<ChatMessageCreateInput, 'id'>>;

/** Modelo Prisma `GamificationBadge` mapeado para a tabela PostgreSQL `gamification_badges` */
export interface GamificationBadge {
  id: string;
  code: string;
  title: string;
  description: string;
  criteriaExplanation: string;
  iconName: string;
  xpReward: number;
  competencyId: string | null;
  isActive: boolean;
  createdAt: Date;
}

/** Registro SQL snake_case da tabela `gamification_badges` */
export interface GamificationBadgeRow {
  id: string;
  code: string;
  title: string;
  description: string;
  criteria_explanation: string;
  icon_name: string;
  xp_reward: number;
  competency_id: string | null;
  is_active: boolean;
  created_at: Date;
}

/** Payload de criação para `GamificationBadge` */
export interface GamificationBadgeCreateInput {
  id?: string;
  code: string;
  title: string;
  description: string;
  criteriaExplanation: string;
  iconName: string;
  xpReward?: number;
  competencyId?: string | null;
  isActive?: boolean;
  createdAt?: Date;
}

/** Payload de atualização parcial para `GamificationBadge` */
export type GamificationBadgeUpdateInput = Partial<Omit<GamificationBadgeCreateInput, 'id'>>;

/** Modelo Prisma `StudentAchievement` mapeado para a tabela PostgreSQL `student_achievements` */
export interface StudentAchievement {
  id: string;
  studentId: string;
  enrollmentId: string;
  badgeId: string;
  unlockedAt: Date;
  originReference: string;
}

/** Registro SQL snake_case da tabela `student_achievements` */
export interface StudentAchievementRow {
  id: string;
  student_id: string;
  enrollment_id: string;
  badge_id: string;
  unlocked_at: Date;
  origin_reference: string;
}

/** Payload de criação para `StudentAchievement` */
export interface StudentAchievementCreateInput {
  id?: string;
  studentId: string;
  enrollmentId: string;
  badgeId: string;
  unlockedAt?: Date;
  originReference: string;
}

/** Payload de atualização parcial para `StudentAchievement` */
export type StudentAchievementUpdateInput = Partial<Omit<StudentAchievementCreateInput, 'id'>>;
