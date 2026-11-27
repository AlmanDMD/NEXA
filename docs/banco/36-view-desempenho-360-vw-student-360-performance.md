# 📊 [DB-036] View Analítica Consolidada de Desempenho do Aluno (`vw_student_360_performance`) — Projeto NEXA

> **ID do Card**: `DB-036` | **Epic**: `EPIC-05: Dashboard Híbrido do Professor & Visão 360°` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P0` | **Estimativa**: `5 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126030000_create_vw_student_360_performance/migration.sql`](../../prisma/migrations/20261126030000_create_vw_student_360_performance/migration.sql), [`BancoNexa/sql/36_view_vw_student_360_performance.sql`](../../BancoNexa/sql/36_view_vw_student_360_performance.sql)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-035`](./35-tabela-diagnosticos-explicaveis-explainable-diagnostics.md) | ➡️ Próximo: `DB-037` | 🔒 Depende de: `DB-017`, `DB-022`, `DB-025`, `DB-028`, `DB-034` | 🔓 Desbloqueia: `BE-031`, `BE-034`, `FE-031`, `FE-034`, `FE-035`

---

## 1. Objetivo e Estratégia de Performance (< 30ms)

A view SQL **`vw_student_360_performance`** consolida por matrícula (`enrollment_id`) os indicadores completos do Dashboard Híbrido do Professor e da Ficha 360° do Estudante: dados cadastrais, turma, média geral ponderada, frequência atualizada, contadores de tarefas (`PENDING`, `SUBMITTED`, `EVALUATED`, `LATE`), total de alertas ativos e maior nível de risco vigente.

Para garantir execução **inferior a 30ms em turmas de até 50 alunos** (validável via `EXPLAIN ANALYZE SELECT * FROM vw_student_360_performance WHERE class_id = $1;`), a view utiliza **4 CTEs pré-agregadas independentes** (`grade_agg`, `attendance_agg`, `task_agg`, `alert_agg`) agrupadas por `enrollment_id`, evitando qualquer multiplicação cartesiana entre notas, presenças, submissões e alertas e aproveitando os índices B-Tree dedicados em `enrollment_id`.

---

## 2. Colunas Expostas pela View

- **Identificação**: `enrollment_id`, `student_id`, `student_name`, `registration_number`, `student_email`, `class_id`, `class_code`, `class_period`, `class_status`, `enrollment_status`.
- **Desempenho e Presença**: `weighted_average_grade`, `graded_assessments_count`, `avg_practical_score`, `attendance_rate_pct`, `total_lesson_hours`, `unjustified_absent_hours`, `justified_absent_hours`.
- **Tarefas Práticas**: `tasks_total`, `tasks_pending`, `tasks_submitted`, `tasks_evaluated`, `tasks_late`, `tasks_completed`.
- **Risco e Alertas**: `active_alerts_count`, `current_risk_level` (`CRITICAL` > `HIGH` > `MODERATE` > `LOW`).

---

## 3. Checklist de Verificação (`DB-036`)

- [x] **Critério 1 — View criada via migration SQL do Prisma**: `20261126030000_create_vw_student_360_performance/migration.sql`.
- [x] **Critério 2 — Contadores `PENDING`, `SUBMITTED`, `EVALUATED` e `LATE`**: Agregados com `COUNT(*) FILTER (WHERE ts.status = ...)`.
- [x] **Critério 3 — Tempo < 30ms para turmas de até 50 alunos**: Arquitetura sem produto cartesiano (4 CTEs indexadas por `enrollment_id`) validada em `scripts/validate-db-036.js`.
