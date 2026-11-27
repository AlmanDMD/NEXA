# 🧠 [DB-035] Tabela de Diagnósticos Explicáveis de Turma (`explainable_diagnostics`) — Projeto NEXA

> **ID do Card**: `DB-035` | **Epic**: `EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P1` | **Estimativa**: `5 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126020000_create_explainable_diagnostics_table/migration.sql`](../../prisma/migrations/20261126020000_create_explainable_diagnostics_table/migration.sql), [`BancoNexa/sql/35_tabela_explainable_diagnostics.sql`](../../BancoNexa/sql/35_tabela_explainable_diagnostics.sql), [`prisma/schema.prisma`](../../prisma/schema.prisma), [`BancoNexa/types/schema-models.ts`](../../BancoNexa/types/schema-models.ts)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-034`](./34-tabela-alertas-indicadores-risco-academic-alerts.md) | ➡️ Próximo: `DB-036` | 🔒 Depende de: `DB-032`, `DB-033`, `DB-034` | 🔓 Desbloqueia: `DB-038`, `DB-040`, `BE-037`, `BE-038`, `FE-042`

---

## 1. Objetivo e Inteligência Pedagógica Explicável

O card **`DB-035`** implementa a tabela `explainable_diagnostics` no **PostgreSQL 16 (Docker)** para persistir diagnósticos pedagógicos comparativos entre a autopercepção do estudante (`self_perceived_level`) e a evidência prática verificada pelo professor (`teacher_verified_level`), exigindo registro explícito de `explanation_text`, `limitations_note` e `recommended_action` — sem caixas-pretas.

---

## 2. Especificação Relacional da Tabela `explainable_diagnostics` (PostgreSQL 16)

| Coluna | Tipo SQL Nativo | Campo Prisma / TS | Nulo? | Default | Constraints e Regras de Negócio |
|---|---|---|:---:|---|---|
| `id` | `UUID` | `id: string` | `NOT NULL` | `gen_random_uuid()` | `PRIMARY KEY` |
| `student_id` | `UUID` | `studentId: string` | `NOT NULL` | — | `FK -> users(id) ON DELETE RESTRICT`, validado como `STUDENT` |
| `class_id` | `UUID` | `classId: string` | `NOT NULL` | — | `FK -> classes(id) ON DELETE RESTRICT` |
| `module_id` | `UUID` | `moduleId: string` | `NOT NULL` | — | `FK -> learning_modules(id) ON DELETE RESTRICT` |
| `competency_id` | `UUID` | `competencyId: string \| null` | `NULL` | `NULL` | `FK -> competencies(id) ON DELETE RESTRICT` |
| `self_perceived_level` | `NUMERIC(3,2)` | `selfPerceivedLevel: number \| string` | `NOT NULL` | — | `CHECK (self_perceived_level BETWEEN 1.00 AND 5.00)` |
| `teacher_verified_level` | `NUMERIC(3,2)` | `teacherVerifiedLevel: number \| string` | `NOT NULL` | — | `CHECK (teacher_verified_level BETWEEN 1.00 AND 5.00)` |
| `discrepancy_gap` | `NUMERIC(3,2)` | `discrepancyGap: number \| string` | `NOT NULL` | — | Calculado via trigger: `ROUND(self_perceived_level - teacher_verified_level, 2)` |
| `diagnostic_type` | `diagnostic_type_enum` | `diagnosticType: DiagnosticType` | `NOT NULL` | — | `ALIGNED`, `OVERCONFIDENCE_RISK`, `UNDERCONFIDENCE_SUPPORT`, `INSUFFICIENT_EVIDENCE` |
| `explanation_text` | `TEXT` | `explanationText: string` | `NOT NULL` | — | Obrigatório (`>= 10` chars) |
| `limitations_note` | `TEXT` | `limitationsNote: string` | `NOT NULL` | — | Obrigatório (`>= 10` chars) — explicita limites da análise |
| `recommended_action` | `TEXT` | `recommendedAction: string` | `NOT NULL` | — | Obrigatório (`>= 5` chars) — recomendação pedagógica prática |
| `generated_at` | `TIMESTAMPTZ` | `generatedAt: Date` | `NOT NULL` | `CURRENT_TIMESTAMP` | Data/hora de geração do diagnóstico |

---

## 3. Checklist de Verificação dos Critérios de Aceitação (`DB-035`)

- [x] **Critério 1 — `explanation_text` e `limitations_note` obrigatórios**: Validados por `chk_diagnostics_explanation_not_empty` e `chk_diagnostics_limitations_not_empty`.
- [x] **Critério 2 — Cálculo de `discrepancy_gap`**: Trigger `trg_explainable_diagnostics_compute_and_validate` calcula e impõe `ROUND(self_perceived_level - teacher_verified_level, 2)`.
- [x] **Critério 3 — Índice `(class_id, diagnostic_type)`**: `idx_explainable_diagnostics_class_type` criado para consultas de turma em `BE-037`/`BE-038`/`FE-042`.
- [x] **DoD — Tabela `explainable_diagnostics` migrada e validada**: Migration `20261126020000_create_explainable_diagnostics_table`, `model ExplainableDiagnostic` e testes em `scripts/validate-db-035.js`.
