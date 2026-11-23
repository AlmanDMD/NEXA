/**
 * ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate`
 * Tipos TypeScript dos Modelos Prisma / Tabelas PostgreSQL 16 (Projeto NEXA)
 * Sincronizado com `prisma/schema.prisma` (camelCase na aplicação e snake_case no SQL).
 */

import type { ClassStatus, CompetencyCategory, EnrollmentStatus, Role, Shift } from './system-enums';

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
