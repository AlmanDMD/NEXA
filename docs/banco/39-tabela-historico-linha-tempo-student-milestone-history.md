# 🏆 [DB-039] Tabela de Histórico e Linha do Tempo Acadêmica (`student_milestone_history`) — Projeto NEXA

> **ID do Card**: `DB-039` | **Epic**: `EPIC-06: Portal de Autonomia do Aluno & Pendências` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P2` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126060000_create_student_milestone_history_table/migration.sql`](../../prisma/migrations/20261126060000_create_student_milestone_history_table/migration.sql), [`BancoNexa/sql/39_tabela_student_milestone_history.sql`](../../BancoNexa/sql/39_tabela_student_milestone_history.sql), [`prisma/schema.prisma`](../../prisma/schema.prisma), [`BancoNexa/types/schema-models.ts`](../../BancoNexa/types/schema-models.ts)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-038`](./38-view-discrepancia-autoavaliacao-vw-self-eval-discrepancy.md) | ➡️ Próximo: `DB-040` | 🔒 Depende de: `DB-014`, `DB-017`, `DB-025` | 🔓 Desbloqueia: `DB-040`, `BE-034`, `FE-039`

---

## 1. Objetivo e Engajamento Positivo

O card **`DB-039`** implementa a tabela `student_milestone_history` no **PostgreSQL 16 (Docker)** para registrar os marcos cronológicos de evolução do estudante (`MODULE_COMPLETED`, `SKILL_LEVEL_UP`, `PERFECT_ATTENDANCE`, `RECOVERY_ACHIEVED`), reforçando sua autonomia e visibilidade de progresso no Portal do Aluno (`BE-034` / `FE-039`).

---

## 2. Especificação Relacional (`student_milestone_history`)

| Coluna | Tipo SQL Nativo | Campo Prisma / TS | Nulo? | Default | Constraints e Regras de Negócio |
|---|---|---|:---:|---|---|
| `id` | `UUID` | `id: string` | `NOT NULL` | `gen_random_uuid()` | `PRIMARY KEY` |
| `student_id` | `UUID` | `studentId: string` | `NOT NULL` | — | `FK -> users(id) ON DELETE RESTRICT`, validado como `STUDENT` |
| `enrollment_id` | `UUID` | `enrollmentId: string` | `NOT NULL` | — | `FK -> enrollments(id) ON DELETE RESTRICT`; coerente com `student_id` |
| `module_id` | `UUID` | `moduleId: string \| null` | `NULL` | `NULL` | `FK -> learning_modules(id) ON DELETE RESTRICT` |
| `milestone_type` | `milestone_type_enum` | `milestoneType: MilestoneType` | `NOT NULL` | — | `MODULE_COMPLETED`, `SKILL_LEVEL_UP`, `PERFECT_ATTENDANCE`, `RECOVERY_ACHIEVED` |
| `title` | `VARCHAR(150)` | `title: string` | `NOT NULL` | — | `CHECK (CHAR_LENGTH(BTRIM(title)) >= 3)` |
| `description` | `TEXT` | `description: string \| null` | `NULL` | `NULL` | Descrição amigável do marco alcançado |
| `metadata` | `JSONB` | `metadata: Record<string, unknown> \| null` | `NULL` | `NULL` | `CHECK (metadata IS NULL OR jsonb_typeof(metadata) = 'object')` |
| `achieved_at` | `TIMESTAMPTZ` | `achievedAt: Date` | `NOT NULL` | `CURRENT_TIMESTAMP` | Ordenação cronológica da linha do tempo |

---

## 3. Checklist de Verificação (`DB-039`)

- [x] **Critério 1 — Eventos ordenados cronologicamente por `achieved_at`**: Índice `idx_milestone_history_student_achieved (student_id, achieved_at DESC)`.
- [x] **Critério 2 — Vinculação íntegra com matrícula e módulo prático**: FKs `ON DELETE RESTRICT` + trigger validando `enrollments.student_id = student_id`.
- [x] **Critério 3 — Índice composto `(student_id, achieved_at DESC)`**: Declarado no SQL e no `prisma/schema.prisma`, validado em `scripts/validate-db-039.js`.
