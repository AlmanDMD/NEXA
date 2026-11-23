# 🏷️ [DB-005] Enumerações Globais de Sistema (Roles, Status, Graus de Risco) — Projeto NEXA

> **ID do Card**: `DB-005` | **Epic**: `EPIC-01: Autenticação, Perfis (RBAC) & Segurança` | **Sprint / Lote**: `Lote 1 (S1)`  
> **Prioridade**: `P0` | **Estimativa**: `1 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/schema.prisma`](../../prisma/schema.prisma), [`prisma/migrations/20261104010000_create_global_system_enums/migration.sql`](../../prisma/migrations/20261104010000_create_global_system_enums/migration.sql), [`BancoNexa/sql/05_enums_globais.sql`](../../BancoNexa/sql/05_enums_globais.sql), [`BancoNexa/types/`](../../BancoNexa/types/)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-004`](./04-estrutura-migrations-versionadas.md) | ➡️ Próximo: `DB-006` | 🔓 Desbloqueia: `DB-006`, `DB-010`, `DB-015`, `DB-034`, `DB-042`, `BE-009`

---

## 1. Objetivo e Vantagem Técnica de `ENUM` Nativo no PostgreSQL 16

O card **`DB-005`** padroniza todas as constantes de estado e domínio do sistema **NEXA** diretamente no motor **PostgreSQL 16 (Docker)** e nos contratos exportados para a API.

### Por que usar `ENUM` nativo do PostgreSQL em vez de `VARCHAR` livre?
1. **Performance Superior e Economia de Armazenamento**: No PostgreSQL 16, um valor `ENUM` ocupa apenas **4 bytes** no disco e na memória RAM (um identificador inteiro interno mapeado no catálogo `pg_enum`), enquanto strings `VARCHAR` ocupam tamanho variável e exigem comparação caractere a caractere em filtros `WHERE` e índices `B-Tree`.
2. **Rejeição Imediata de Estados Inválidos**: Qualquer tentativa de inserir um papel ou status com erro de digitação (ex.: `'STUDNT'` em vez de `'STUDENT'`) é bloqueada instantaneamente pelo motor SQL antes mesmo de tocar no disco.
3. **Fonte Única da Verdade (Single Source of Truth)**: A partir do schema do banco, o comando `npm run db:generate` gera automaticamente os tipos em **TypeScript** (`BancoNexa/types/system-enums.ts`), **Python/FastAPI** (`BancoNexa/types/system_enums.py`) e **JSON** (`BancoNexa/types/system-enums.json`).

---

## 2. Catálogo das Enumerações Globais Criadas

### 2.1. Os 5 Enums Primários Exigidos pelo Card `DB-005`

| Nome no Schema (`PascalCase`) | Tipo Nativo PostgreSQL (`@@map`) | Valores Constantes Permitidos | Entidades Consumidoras |
|---|---|---|---|
| **`Role`** | `user_role_enum` | `'ADMIN'`, `'COORDINATOR'`, `'TEACHER'`, `'STUDENT'` | `users.role` (`DB-006`), RBAC (`BE-009`) |
| **`EnrollmentStatus`** | `enrollment_status_enum` | `'ACTIVE'`, `'COMPLETED'`, `'DROPPED'`, `'SUSPENDED'` | `enrollments.status` (`DB-017`), `student_subjects.status` |
| **`RiskLevel`** | `risk_level_enum` | `'LOW'`, `'MODERATE'`, `'HIGH'`, `'CRITICAL'` | `academic_alerts.risk_level` (`DB-034`) |
| **`SubmissionStatus`** | `submission_status_enum` | `'PENDING'`, `'SUBMITTED'`, `'EVALUATED'`, `'LATE'` | `task_submissions.status` (`DB-025`) |
| **`HelpRequestStatus`** | `help_request_status_enum` | `'OPEN'`, `'IN_PROGRESS'`, `'RESOLVED'`, `'CLOSED'` | `help_requests.status` (`DB-042`) |

---

### 2.2. Enums Complementares de Domínio Acadêmico SENAI (Sincronia com `DB-012` a `DB-043`)

| Nome no Schema (`PascalCase`) | Tipo Nativo PostgreSQL (`@@map`) | Valores Constantes Permitidos | Card Consumidor |
|---|---|---|---|
| **`Shift`** | `shift_enum` | `'MORNING'`, `'AFTERNOON'`, `'NIGHT'` | `DB-012` (`classes`) |
| **`ClassStatus`** | `class_status_enum` | `'PLANNING'`, `'ACTIVE'`, `'COMPLETED'`, `'ARCHIVED'` | `DB-012` / `DB-029` |
| **`CompetencyCategory`** | `competency_category_enum` | `'TECHNICAL'`, `'SAFETY'`, `'PROCEDURAL'` | `DB-015` (`competencies`) |
| **`AttendanceStatus`** | `attendance_status_enum` | `'PRESENT'`, `'ABSENT'`, `'LATE'`, `'JUSTIFIED'` | `DB-022` (`attendance_records`) |
| **`AssessmentType`** | `assessment_type_enum` | `'EXAM'`, `'MICRO_EVALUATION'`, `'PROJECT'` | `DB-027` (`academic_assessments`) |
| **`AlertCategory`** | `alert_category_enum` | `'ATTENDANCE'`, `'GRADE_DROP'`, `'PENDING_TASKS'`, `'SELF_EVAL_GAP'` | `DB-034` (`academic_alerts`) |
| **`AlertStatus`** | `alert_status_enum` | `'ACTIVE'`, `'ACKNOWLEDGED'`, `'RESOLVED'` | `DB-034` (`academic_alerts`) |
| **`DiagnosticType`** | `diagnostic_type_enum` | `'ALIGNED'`, `'OVERCONFIDENCE_RISK'`, `'UNDERCONFIDENCE_SUPPORT'`, `'INSUFFICIENT_EVIDENCE'` | `DB-035` (`explainable_diagnostics`) |
| **`MilestoneType`** | `milestone_type_enum` | `'MODULE_COMPLETED'`, `'SKILL_LEVEL_UP'`, `'PERFECT_ATTENDANCE'`, `'RECOVERY_ACHIEVED'` | `DB-039` (`student_milestone_history`) |
| **`AnnouncementPriority`** | `announcement_priority_enum` | `'NORMAL'`, `'IMPORTANT'`, `'URGENT'` | `DB-041` (`class_announcements`) |
| **`HelpRequestCategory`** | `help_request_category_enum` | `'TECHNICAL_DOUBT'`, `'PRACTICAL_DIFFICULTY'`, `'PERSONAL_PEDAGOGICAL'` | `DB-042` (`help_requests`) |
| **`NoteVisibilityScope`** | `note_visibility_scope_enum` | `'PRIVATE_AUTHOR'`, `'TEACHERS_AND_COORD'`, `'COORDINATION_ONLY'` | `DB-043` (`pedagogical_notes`) |
| **`NoteCategory`** | `note_category_enum` | `'INTERVENTION'`, `'MENTORING'`, `'BEHAVIORAL'`, `'ACCOMMODATION'` | `DB-043` (`pedagogical_notes`) |

---

## 3. Implementação Idempotente em SQL (PostgreSQL 16 + Docker)

Na migration [`20261104010000_create_global_system_enums/migration.sql`](../../prisma/migrations/20261104010000_create_global_system_enums/migration.sql), cada tipo `ENUM` é criado dentro de um bloco anônimo PL/pgSQL `DO $$ ... END $$;` que captura `duplicate_object`, permitindo reexecução segura (idempotência) em qualquer container Docker:

```sql
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'COORDINATOR', 'TEACHER', 'STUDENT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
```

---

## 4. Tipos Exportados para Validação na API (Back-end e Front-end)

Ao rodar `npm run db:generate`, os seguintes artefatos são gerados e sincronizados em [`BancoNexa/types/`](../../BancoNexa/types/):
- **[`BancoNexa/types/system-enums.ts`](../../BancoNexa/types/system-enums.ts)**: Objetos `as const`, Union Types e arrays `*Values` prontos para Zod / TypeScript.
- **[`BancoNexa/types/system_enums.py`](../../BancoNexa/types/system_enums.py)**: Classes `StrEnum` nativas do Python 3.12+ prontas para validação automática no Pydantic v2 e FastAPI (`BE-005`, `BE-009`).
- **[`BancoNexa/types/system-enums.json`](../../BancoNexa/types/system-enums.json)**: Contrato neutro em JSON para testes de contrato e integração.

---

## 5. Checklist de Verificação dos Critérios de Aceitação (`DB-005`)

- [x] **Critério 1 — Enums criados e validados no `schema.prisma`**: Todos os 5 enums principais (`Role`, `EnrollmentStatus`, `RiskLevel`, `SubmissionStatus`, `HelpRequestStatus`) + 13 enums de domínio declarados com `@@map` em `snake_case`.
- [x] **Critério 2 — Migration gerada criando os tipos nativos enum no PostgreSQL**: Migration SQL versionada criada em `prisma/migrations/20261104010000_create_global_system_enums/migration.sql` e `BancoNexa/migrations/`.
- [x] **Critério 3 — Tipos exportados compatíveis com as validações da API**: Gerados e testados em `BancoNexa/types/system-enums.ts`, `system_enums.py` e `system-enums.json`.
