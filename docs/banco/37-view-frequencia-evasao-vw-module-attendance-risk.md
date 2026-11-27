# 📉 [DB-037] View Analítica de Frequência e Evasão por Módulo (`vw_module_attendance_risk`) — Projeto NEXA

> **ID do Card**: `DB-037` | **Epic**: `EPIC-05: Dashboard Híbrido do Professor & Visão 360°` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P1` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126040000_create_vw_module_attendance_risk/migration.sql`](../../prisma/migrations/20261126040000_create_vw_module_attendance_risk/migration.sql), [`BancoNexa/sql/37_view_vw_module_attendance_risk.sql`](../../BancoNexa/sql/37_view_vw_module_attendance_risk.sql)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-036`](./36-view-desempenho-360-vw-student-360-performance.md) | ➡️ Próximo: `DB-038` | 🔒 Depende de: `DB-014`, `DB-021`, `DB-022` | 🔓 Desbloqueia: `BE-032`, `FE-023`

---

## 1. Objetivo e Regras de Cálculo

A view SQL **`vw_module_attendance_risk`** consolida presença e faltas por estudante, disciplina e módulo prático (`learning_modules`), permitindo identificar precocemente estudantes abaixo do limiar preventivo de **78%** (`is_attendance_critical = TRUE`) antes que ultrapassem o teto de 25% de faltas do SENAI (`is_below_senai_minimum` para `< 75%`).

- **Divisão por Zero Segura**: Quando nenhuma aula foi ministrada ainda no módulo (`total_hours_taught = 0`), retorna `100.00%` e `is_attendance_critical = FALSE`.
- **Separação de Faltas Justificadas**: Segrega `justified_absent_hours` (`status = 'JUSTIFIED'`) de `unjustified_absent_hours` (`status IN ('ABSENT', 'LATE')`), expondo tanto `attendance_percentage` (descontando apenas faltas não justificadas) quanto `raw_attendance_percentage`.

---

## 2. Checklist de Verificação (`DB-037`)

- [x] **Critério 1 — Trata divisão por zero (retorna 100%)**: `CASE WHEN COALESCE(ml.total_hours_taught, 0) = 0 THEN 100.00::NUMERIC(5,2)`.
- [x] **Critério 2 — Separa `JUSTIFIED` de faltas não justificadas**: Colunas dedicadas `justified_absent_hours` e `unjustified_absent_hours`.
- [x] **Critério 3 — Integrada ao motor de alertas (`BE-032`)**: Flags `is_attendance_critical (< 78%)` e `is_below_senai_minimum (< 75%)` validadas em `scripts/validate-db-037.js`.
