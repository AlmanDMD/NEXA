/**
 * ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate` — CARD [DB-005]
 * Tipos Enum Exportados do Schema do Banco de Dados (PostgreSQL 16)
 * Compatíveis com validações de API, Front-end e Prisma Client.
 */

/** Mapeado para o tipo nativo PostgreSQL: `user_role_enum` */
export const Role = {
  ADMIN: 'ADMIN',
  COORDINATOR: 'COORDINATOR',
  TEACHER: 'TEACHER',
  STUDENT: 'STUDENT',
} as const;
export type Role = (typeof Role)[keyof typeof Role];
export const RoleValues: readonly Role[] = Object.values(Role);

/** Mapeado para o tipo nativo PostgreSQL: `enrollment_status_enum` */
export const EnrollmentStatus = {
  ACTIVE: 'ACTIVE',
  COMPLETED: 'COMPLETED',
  DROPPED: 'DROPPED',
  SUSPENDED: 'SUSPENDED',
} as const;
export type EnrollmentStatus = (typeof EnrollmentStatus)[keyof typeof EnrollmentStatus];
export const EnrollmentStatusValues: readonly EnrollmentStatus[] = Object.values(EnrollmentStatus);

/** Mapeado para o tipo nativo PostgreSQL: `risk_level_enum` */
export const RiskLevel = {
  LOW: 'LOW',
  MODERATE: 'MODERATE',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
} as const;
export type RiskLevel = (typeof RiskLevel)[keyof typeof RiskLevel];
export const RiskLevelValues: readonly RiskLevel[] = Object.values(RiskLevel);

/** Mapeado para o tipo nativo PostgreSQL: `submission_status_enum` */
export const SubmissionStatus = {
  PENDING: 'PENDING',
  SUBMITTED: 'SUBMITTED',
  EVALUATED: 'EVALUATED',
  LATE: 'LATE',
} as const;
export type SubmissionStatus = (typeof SubmissionStatus)[keyof typeof SubmissionStatus];
export const SubmissionStatusValues: readonly SubmissionStatus[] = Object.values(SubmissionStatus);

/** Mapeado para o tipo nativo PostgreSQL: `help_request_status_enum` */
export const HelpRequestStatus = {
  OPEN: 'OPEN',
  IN_PROGRESS: 'IN_PROGRESS',
  RESOLVED: 'RESOLVED',
  CLOSED: 'CLOSED',
} as const;
export type HelpRequestStatus = (typeof HelpRequestStatus)[keyof typeof HelpRequestStatus];
export const HelpRequestStatusValues: readonly HelpRequestStatus[] = Object.values(HelpRequestStatus);

/** Mapeado para o tipo nativo PostgreSQL: `shift_enum` */
export const Shift = {
  MORNING: 'MORNING',
  AFTERNOON: 'AFTERNOON',
  NIGHT: 'NIGHT',
} as const;
export type Shift = (typeof Shift)[keyof typeof Shift];
export const ShiftValues: readonly Shift[] = Object.values(Shift);

/** Mapeado para o tipo nativo PostgreSQL: `class_status_enum` */
export const ClassStatus = {
  PLANNING: 'PLANNING',
  ACTIVE: 'ACTIVE',
  COMPLETED: 'COMPLETED',
  ARCHIVED: 'ARCHIVED',
} as const;
export type ClassStatus = (typeof ClassStatus)[keyof typeof ClassStatus];
export const ClassStatusValues: readonly ClassStatus[] = Object.values(ClassStatus);

/** Mapeado para o tipo nativo PostgreSQL: `competency_category_enum` */
export const CompetencyCategory = {
  TECHNICAL: 'TECHNICAL',
  SAFETY: 'SAFETY',
  PROCEDURAL: 'PROCEDURAL',
} as const;
export type CompetencyCategory = (typeof CompetencyCategory)[keyof typeof CompetencyCategory];
export const CompetencyCategoryValues: readonly CompetencyCategory[] = Object.values(CompetencyCategory);

/** Mapeado para o tipo nativo PostgreSQL: `attendance_status_enum` */
export const AttendanceStatus = {
  PRESENT: 'PRESENT',
  ABSENT: 'ABSENT',
  LATE: 'LATE',
  JUSTIFIED: 'JUSTIFIED',
} as const;
export type AttendanceStatus = (typeof AttendanceStatus)[keyof typeof AttendanceStatus];
export const AttendanceStatusValues: readonly AttendanceStatus[] = Object.values(AttendanceStatus);

/** Mapeado para o tipo nativo PostgreSQL: `assessment_type_enum` */
export const AssessmentType = {
  EXAM: 'EXAM',
  MICRO_EVALUATION: 'MICRO_EVALUATION',
  PROJECT: 'PROJECT',
} as const;
export type AssessmentType = (typeof AssessmentType)[keyof typeof AssessmentType];
export const AssessmentTypeValues: readonly AssessmentType[] = Object.values(AssessmentType);

/** Mapeado para o tipo nativo PostgreSQL: `alert_category_enum` */
export const AlertCategory = {
  ATTENDANCE: 'ATTENDANCE',
  GRADE_DROP: 'GRADE_DROP',
  PENDING_TASKS: 'PENDING_TASKS',
  SELF_EVAL_GAP: 'SELF_EVAL_GAP',
} as const;
export type AlertCategory = (typeof AlertCategory)[keyof typeof AlertCategory];
export const AlertCategoryValues: readonly AlertCategory[] = Object.values(AlertCategory);

/** Mapeado para o tipo nativo PostgreSQL: `alert_status_enum` */
export const AlertStatus = {
  ACTIVE: 'ACTIVE',
  ACKNOWLEDGED: 'ACKNOWLEDGED',
  RESOLVED: 'RESOLVED',
} as const;
export type AlertStatus = (typeof AlertStatus)[keyof typeof AlertStatus];
export const AlertStatusValues: readonly AlertStatus[] = Object.values(AlertStatus);

/** Mapeado para o tipo nativo PostgreSQL: `diagnostic_type_enum` */
export const DiagnosticType = {
  ALIGNED: 'ALIGNED',
  OVERCONFIDENCE_RISK: 'OVERCONFIDENCE_RISK',
  UNDERCONFIDENCE_SUPPORT: 'UNDERCONFIDENCE_SUPPORT',
  INSUFFICIENT_EVIDENCE: 'INSUFFICIENT_EVIDENCE',
} as const;
export type DiagnosticType = (typeof DiagnosticType)[keyof typeof DiagnosticType];
export const DiagnosticTypeValues: readonly DiagnosticType[] = Object.values(DiagnosticType);

/** Mapeado para o tipo nativo PostgreSQL: `milestone_type_enum` */
export const MilestoneType = {
  MODULE_COMPLETED: 'MODULE_COMPLETED',
  SKILL_LEVEL_UP: 'SKILL_LEVEL_UP',
  PERFECT_ATTENDANCE: 'PERFECT_ATTENDANCE',
  RECOVERY_ACHIEVED: 'RECOVERY_ACHIEVED',
} as const;
export type MilestoneType = (typeof MilestoneType)[keyof typeof MilestoneType];
export const MilestoneTypeValues: readonly MilestoneType[] = Object.values(MilestoneType);

/** Mapeado para o tipo nativo PostgreSQL: `announcement_priority_enum` */
export const AnnouncementPriority = {
  NORMAL: 'NORMAL',
  IMPORTANT: 'IMPORTANT',
  URGENT: 'URGENT',
} as const;
export type AnnouncementPriority = (typeof AnnouncementPriority)[keyof typeof AnnouncementPriority];
export const AnnouncementPriorityValues: readonly AnnouncementPriority[] = Object.values(AnnouncementPriority);

/** Mapeado para o tipo nativo PostgreSQL: `help_request_category_enum` */
export const HelpRequestCategory = {
  TECHNICAL_DOUBT: 'TECHNICAL_DOUBT',
  PRACTICAL_DIFFICULTY: 'PRACTICAL_DIFFICULTY',
  PERSONAL_PEDAGOGICAL: 'PERSONAL_PEDAGOGICAL',
} as const;
export type HelpRequestCategory = (typeof HelpRequestCategory)[keyof typeof HelpRequestCategory];
export const HelpRequestCategoryValues: readonly HelpRequestCategory[] = Object.values(HelpRequestCategory);

/** Mapeado para o tipo nativo PostgreSQL: `note_visibility_scope_enum` */
export const NoteVisibilityScope = {
  PRIVATE_AUTHOR: 'PRIVATE_AUTHOR',
  TEACHERS_AND_COORD: 'TEACHERS_AND_COORD',
  COORDINATION_ONLY: 'COORDINATION_ONLY',
} as const;
export type NoteVisibilityScope = (typeof NoteVisibilityScope)[keyof typeof NoteVisibilityScope];
export const NoteVisibilityScopeValues: readonly NoteVisibilityScope[] = Object.values(NoteVisibilityScope);

/** Mapeado para o tipo nativo PostgreSQL: `note_category_enum` */
export const NoteCategory = {
  INTERVENTION: 'INTERVENTION',
  MENTORING: 'MENTORING',
  BEHAVIORAL: 'BEHAVIORAL',
  ACCOMMODATION: 'ACCOMMODATION',
} as const;
export type NoteCategory = (typeof NoteCategory)[keyof typeof NoteCategory];
export const NoteCategoryValues: readonly NoteCategory[] = Object.values(NoteCategory);
