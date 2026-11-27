# 🚨 [DB-034] Tabela de Alertas e Indicadores de Risco (`academic_alerts`) — Projeto NEXA

> **ID do Card**: `DB-034` | **Epic**: `EPIC-05: Dashboard Híbrido do Professor & Visão 360°` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P0` | **Estimativa**: `5 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126010000_create_academic_alerts_table/migration.sql`](../../prisma/migrations/20261126010000_create_academic_alerts_table/migration.sql), [`BancoNexa/sql/34_tabela_academic_alerts.sql`](../../BancoNexa/sql/34_tabela_academic_alerts.sql), [`prisma/schema.prisma`](../../prisma/schema.prisma), [`BancoNexa/types/schema-models.ts`](../../BancoNexa/types/schema-models.ts)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-033`](./33-tabela-evidencias-praticas-skill-evidences.md) | ➡️ Próximo: `DB-035` | 🔒 Depende de: `DB-005`, `DB-017`, `DB-022`, `DB-025`, `DB-028` | 🔓 Desbloqueia: `DB-035`, `DB-036`, `DB-040`, `BE-032`, `BE-033`, `FE-032`

---

## 1. Objetivo e Governança Pedagógica

O card **`DB-034`** implementa a tabela `academic_alerts` no **PostgreSQL 16 (Docker)** para armazenar alertas precoces e totalmente explicáveis voltados ao apoio preventivo de docentes e coordenadores (ex.: *"3 tarefas práticas atrasadas e 74% de presença"*). Alertas são **indicadores pedagógicos transitórios** (`ACTIVE -> ACKNOWLEDGED -> RESOLVED`), jamais rótulos permanentes ao estudante.

---

## 2. Especificação Relacional da Tabela `academic_alerts` (PostgreSQL 16)

| Coluna | Tipo SQL Nativo | Campo Prisma / TS | Nulo? | Default | Constraints e Regras de Negócio |
|---|---|---|:---:|---|---|
| `id` | `UUID` | `id: string` | `NOT NULL` | `gen_random_uuid()` | `PRIMARY KEY` |
| `student_id` | `UUID` | `studentId: string` | `NOT NULL` | — | `FK -> users(id) ON DELETE RESTRICT` |
| `enrollment_id` | `UUID` | `enrollmentId: string` | `NOT NULL` | — | `FK -> enrollments(id) ON DELETE RESTRICT`; coerente com `student_id` e `class_id` |
| `class_id` | `UUID` | `classId: string` | `NOT NULL` | — | `FK -> classes(id) ON DELETE RESTRICT` |
| `module_id` | `UUID` | `moduleId: string \| null` | `NULL` | `NULL` | `FK -> learning_modules(id) ON DELETE RESTRICT` |
| `risk_level` | `risk_level_enum` | `riskLevel: RiskLevel` | `NOT NULL` | — | `LOW`, `MODERATE`, `HIGH`, `CRITICAL` (`DB-005`) |
| `alert_category` | `alert_category_enum` | `alertCategory: AlertCategory` | `NOT NULL` | — | `ATTENDANCE`, `GRADE_DROP`, `PENDING_TASKS`, `SELF_EVAL_GAP` |
| `explainable_reason` | `TEXT` | `explainableReason: string` | `NOT NULL` | — | `CHECK (CHAR_LENGTH(BTRIM(explainable_reason)) >= 10)` |
| `metric_snapshot` | `JSONB` | `metricSnapshot: Record<string, unknown>` | `NOT NULL` | — | `CHECK (jsonb_typeof(metric_snapshot) = 'object')` + índice GIN |
| `status` | `alert_status_enum` | `status: AlertStatus` | `NOT NULL` | `'ACTIVE'` | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED` |
| `resolved_by` | `UUID` | `resolvedBy: string \| null` | `NULL` | `NULL` | `FK -> users(id) ON DELETE SET NULL`; proibido `role = 'STUDENT'` |
| `resolution_notes` | `TEXT` | `resolutionNotes: string \| null` | `NULL` | `NULL` | Notas pedagógicas da intervenção realizada |
| `created_at` | `TIMESTAMPTZ` | `createdAt: Date` | `NOT NULL` | `CURRENT_TIMESTAMP` | Data/hora de disparo do alerta |

---

## 3. Checklist de Verificação dos Critérios de Aceitação (`DB-034`)

- [x] **Critério 1 — `explainable_reason` obrigatório**: `NOT NULL` + `chk_academic_alerts_reason_not_empty`.
- [x] **Critério 2 — `metric_snapshot` em JSONB**: `JSONB NOT NULL` + `chk_academic_alerts_metric_snapshot_object` + índice `idx_academic_alerts_metric_snapshot_gin`.
- [x] **Critério 3 — Índice `(class_id, status, risk_level)`**: `idx_academic_alerts_class_status_risk` criado para ordenação prioritária no dashboard.
- [x] **DoD — Tabela `academic_alerts` migrada, integrada ao Prisma e validada**: Migration `20261126010000_create_academic_alerts_table`, `model AcademicAlert` e testes em `scripts/validate-db-034.js`.
