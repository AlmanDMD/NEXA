# 📚 [DB-050] Dicionário de Dados Automatizado & Validação Final de Integridade (50/50)

> **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade  
> **Sprint / Lote**: S5 / Lote 5 (Marco de Encerramento 50/50) | **Prioridade**: P0 | **Estimativa**: 2 SP  
> **Gerado automaticamente por**: `prisma/verify-schema-integrity.ts` (`npm run db:verify`)  
> **Sincronizado com**: `DOC-008`, `DOC-009`, `DOC-020`, `BE-050` e `FE-050`

---

## ✅ Resumo Executivo de Homologação da Camada de Dados

| Indicador Consolidado | Quantidade / Status | Conformidade |
|---|---:|---|
| Cards de Banco de Dados Concluídos | **50 / 50** (`DB-001` a `DB-050`) | ✅ 100% |
| Tabelas Relacionais 3FN (Prisma + PostgreSQL 16) | **33** | ✅ Paridade Total |
| Colunas Mapeadas (`snake_case` ↔ `camelCase`) | **300** | ✅ 100% |
| Enumerações Globais Nativas (`CREATE TYPE ... AS ENUM`) | **18** | ✅ Exportadas (TS / Python / JSON) |
| Views Analíticas Consolidadas | **3** | ✅ `vw_student_360_performance`, `vw_module_attendance_risk`, `vw_self_eval_discrepancy` |
| Migrations SQL Versionadas (SHA-256) | **41** | ✅ Imutáveis e Idempotentes |
| Scripts de Seed Idempotentes (Lotes 2 a 5) | **4** | ✅ Verificados em Dupla Passagem |
| Índices B-Tree / Compostos / GIN / Parciais | **121** | ✅ Meta `< 50ms` (`DB-047`) |
| Triggers & Funções de Regra Acadêmica / Auditoria | **40** | ✅ Inclui Período Fechado (`DB-029`) e LGPD (`DB-049`) |
| Tabelas Protegidas por Row-Level Security (RLS) | **4** | ✅ `student_self_assessments`, `help_requests`, `pedagogical_notes`, `chat_messages` |
| Testes Finais de Integridade Referencial | **7 / 7** | ✅ Aprovado |

---

## 🔤 Catálogo de Enumerações Globais (18 Enums)

| Enum Prisma | Tipo PostgreSQL 16 | Valores Permitidos |
|---|---|---|
| `Role` | `user_role_enum` | `ADMIN`, `COORDINATOR`, `TEACHER`, `STUDENT` |
| `EnrollmentStatus` | `enrollment_status_enum` | `ACTIVE`, `COMPLETED`, `DROPPED`, `SUSPENDED` |
| `RiskLevel` | `risk_level_enum` | `LOW`, `MODERATE`, `HIGH`, `CRITICAL` |
| `SubmissionStatus` | `submission_status_enum` | `PENDING`, `SUBMITTED`, `EVALUATED`, `LATE` |
| `HelpRequestStatus` | `help_request_status_enum` | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED` |
| `Shift` | `shift_enum` | `MORNING`, `AFTERNOON`, `NIGHT` |
| `ClassStatus` | `class_status_enum` | `PLANNING`, `ACTIVE`, `COMPLETED`, `ARCHIVED` |
| `CompetencyCategory` | `competency_category_enum` | `TECHNICAL`, `SAFETY`, `PROCEDURAL` |
| `AttendanceStatus` | `attendance_status_enum` | `PRESENT`, `ABSENT`, `LATE`, `JUSTIFIED` |
| `AssessmentType` | `assessment_type_enum` | `EXAM`, `MICRO_EVALUATION`, `PROJECT` |
| `AlertCategory` | `alert_category_enum` | `ATTENDANCE`, `GRADE_DROP`, `PENDING_TASKS`, `SELF_EVAL_GAP` |
| `AlertStatus` | `alert_status_enum` | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED` |
| `DiagnosticType` | `diagnostic_type_enum` | `ALIGNED`, `OVERCONFIDENCE_RISK`, `UNDERCONFIDENCE_SUPPORT`, `INSUFFICIENT_EVIDENCE` |
| `MilestoneType` | `milestone_type_enum` | `MODULE_COMPLETED`, `SKILL_LEVEL_UP`, `PERFECT_ATTENDANCE`, `RECOVERY_ACHIEVED` |
| `AnnouncementPriority` | `announcement_priority_enum` | `NORMAL`, `IMPORTANT`, `URGENT` |
| `HelpRequestCategory` | `help_request_category_enum` | `TECHNICAL_DOUBT`, `PRACTICAL_DIFFICULTY`, `PERSONAL_PEDAGOGICAL` |
| `NoteVisibilityScope` | `note_visibility_scope_enum` | `PRIVATE_AUTHOR`, `TEACHERS_AND_COORD`, `COORDINATION_ONLY` |
| `NoteCategory` | `note_category_enum` | `INTERVENTION`, `MENTORING`, `BEHAVIORAL`, `ACCOMMODATION` |

---

## 👁️ Views Analíticas Homologadas (3 Views)

| View SQL | Card | Finalidade |
|---|---|---|
| `vw_student_360_performance` | `DB-036` | Consolidação 360° de notas, frequência, entregas práticas e alertas por matrícula (4 CTEs sem produto cartesiano) |
| `vw_module_attendance_risk` | `DB-037` | Monitoramento de frequência/evasão por módulo com divisão segura por zero e flags `< 78%` / `< 75%` SENAI |
| `vw_self_eval_discrepancy` | `DB-038` | Comparação autoavaliação discente vs. evidências docentes (`OVERCONFIDENCE_RISK`, `UNDERCONFIDENCE_SUPPORT`, `ALIGNED`) |

---

## 🗂️ Dicionário de Dados Consolidado (33 Tabelas — `DOC-009`)

| # | Tabela PostgreSQL | Modelo Prisma | Colunas | FKs | CHECKs | Índices | Triggers | RLS |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | `schema_migrations` | `SchemaMigration` | 7 | 0 | 1 | 1 | 0 | — |
| 2 | `users` | `User` | 7 | 0 | 2 | 4 | 1 | — |
| 3 | `user_profiles` | `UserProfile` | 9 | 1 | 2 | 2 | 1 | — |
| 4 | `auth_sessions` | `AuthSession` | 8 | 1 | 2 | 4 | 1 | — |
| 5 | `audit_logs` | `AuditLog` | 9 | 1 | 3 | 5 | 1 | — |
| 6 | `courses` | `Course` | 8 | 0 | 3 | 4 | 2 | — |
| 7 | `classes` | `Class` | 11 | 1 | 4 | 4 | 2 | — |
| 8 | `subjects` | `Subject` | 9 | 1 | 3 | 4 | 1 | — |
| 9 | `learning_modules` | `LearningModule` | 10 | 1 | 5 | 3 | 1 | — |
| 10 | `competencies` | `Competency` | 7 | 0 | 2 | 5 | 1 | — |
| 11 | `module_competencies` | `ModuleCompetency` | 6 | 2 | 2 | 2 | 1 | — |
| 12 | `enrollments` | `Enrollment` | 9 | 2 | 2 | 5 | 2 | — |
| 13 | `teacher_assignments` | `TeacherAssignment` | 6 | 3 | 0 | 3 | 1 | — |
| 14 | `class_lessons` | `ClassLesson` | 10 | 4 | 2 | 3 | 1 | — |
| 15 | `attendance_records` | `AttendanceRecord` | 8 | 3 | 2 | 5 | 2 | — |
| 16 | `practical_tasks` | `PracticalTask` | 11 | 2 | 3 | 3 | 1 | — |
| 17 | `task_criteria` | `TaskCriterion` | 6 | 2 | 3 | 2 | 0 | — |
| 18 | `task_submissions` | `TaskSubmission` | 11 | 3 | 2 | 4 | 2 | — |
| 19 | `submission_evaluations` | `SubmissionEvaluation` | 8 | 3 | 2 | 3 | 3 | — |
| 20 | `academic_assessments` | `AcademicAssessment` | 10 | 3 | 3 | 4 | 1 | — |
| 21 | `student_grades` | `StudentGrade` | 10 | 4 | 2 | 6 | 3 | — |
| 22 | `self_assessment_forms` | `SelfAssessmentForm` | 10 | 3 | 2 | 4 | 1 | — |
| 23 | `student_self_assessments` | `StudentSelfAssessment` | 8 | 3 | 2 | 3 | 1 | 🔒 Sim |
| 24 | `skill_evidences` | `SkillEvidence` | 8 | 5 | 2 | 5 | 1 | — |
| 25 | `academic_alerts` | `AcademicAlert` | 13 | 5 | 2 | 7 | 1 | — |
| 26 | `explainable_diagnostics` | `ExplainableDiagnostic` | 13 | 4 | 6 | 3 | 1 | — |
| 27 | `student_milestone_history` | `StudentMilestoneHistory` | 9 | 3 | 2 | 4 | 1 | — |
| 28 | `class_announcements` | `ClassAnnouncement` | 10 | 3 | 3 | 4 | 1 | — |
| 29 | `help_requests` | `HelpRequest` | 15 | 5 | 3 | 4 | 1 | 🔒 Sim |
| 30 | `pedagogical_notes` | `PedagogicalNote` | 11 | 3 | 2 | 3 | 2 | 🔒 Sim |
| 31 | `chat_messages` | `ChatMessage` | 7 | 2 | 3 | 2 | 1 | 🔒 Sim |
| 32 | `gamification_badges` | `GamificationBadge` | 10 | 1 | 6 | 3 | 0 | — |
| 33 | `student_achievements` | `StudentAchievement` | 6 | 3 | 1 | 3 | 1 | — |

---

## 🧪 Resultado dos Testes de Integridade Referencial (`DB-050`)

- [PASS] student_grades bloqueia inserção para aluno/matrícula/avaliação inexistente (FKs + trigger)
- [PASS] attendance_records bloqueia inserção para aluno/aula/matrícula inexistente (FKs + trigger)
- [PASS] student_self_assessments bloqueia inserção para aluno/formulário/competência inexistente (FKs + RLS)
- [PASS] pedagogical_notes bloqueia inserção para aluno/matrícula inexistente e exige trilha audit_logs + RLS
- [PASS] Período letivo fechado (DB-029) protege student_grades, attendance_records, task_submissions e submission_evaluations
- [PASS] Política LGPD (DB-049) remove PII e registra obrigatoriamente em audit_logs
- [PASS] Simulador referencial rejeitou 100% das inserções órfãs (SQLSTATE 23503) em notas, frequência, autoavaliação e observações

---

## 📂 Artefatos de Fechamento (`DOC-008` / `DOC-009` / `DOC-020`)

- [`prisma/verify-schema-integrity.ts`](../../prisma/verify-schema-integrity.ts)
- [`BancoNexa/types/data-dictionary.json`](../../BancoNexa/types/data-dictionary.json)
- [`BancoNexa/migrations/migration-manifest.json`](../../BancoNexa/migrations/migration-manifest.json)
- [`scripts/validate-db-050.js`](../../scripts/validate-db-050.js)
