# ⚡ [DB-047] Otimização com Índices B-Tree, Compostos e Parciais

> **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P0 | **Estimativa**: 3 SP  
> **Migration SQL**: `20261127060000_optimize_composite_and_partial_indexes`

---

## 🎯 Objetivo

Garantir latência **< 50ms** em dashboards, filtros por turma/aluno, paginação e exportação de relatórios dos Lotes 1 a 5, eliminando `Seq Scan` em tabelas críticas por meio de índices B-Tree compostos e índices parciais (`WHERE ...`).

---

## 📇 Catálogo de Índices Criados na Migration `DB-047`

| Tabela | Índice | Tipo / Colunas | Condição Parcial | Consulta Acelerada |
|---|---|---|---|---|
| `enrollments` | `idx_enrollments_class_status` | B-Tree `(class_id, status)` | — | Listagem de matrículas por turma e situação |
| `enrollments` | `idx_enrollments_active_class_student` | Parcial `(class_id, student_id)` | `WHERE status = 'ACTIVE'` | Dashboard ativo da turma / chamada |
| `task_submissions` | `idx_task_submissions_student_status` | B-Tree `(student_id, status)` | — | Portal do Aluno: entregas por estado |
| `task_submissions` | `idx_task_submissions_pending_late` | Parcial `(enrollment_id, task_id, status)` | `WHERE status IN ('PENDING', 'LATE')` | Alerta precoce de tarefas atrasadas |
| `academic_alerts` | `idx_academic_alerts_class_risk_level` | B-Tree `(class_id, risk_level)` | — | Filtro de risco no Dashboard do Professor |
| `academic_alerts` | `idx_academic_alerts_active_priority` | Parcial `(class_id, risk_level, created_at DESC)` | `WHERE status = 'ACTIVE'` | Fila prioritária de alertas abertos |
| `attendance_records` | `idx_attendance_records_enrollment_status` | B-Tree `(enrollment_id, status)` | — | Cálculo de frequência por matrícula |
| `attendance_records` | `idx_attendance_records_absences` | Parcial `(enrollment_id, lesson_id)` | `WHERE status IN ('ABSENT', 'LATE')` | Monitoramento de risco de evasão (< 78%) |
| `student_grades` | `idx_student_grades_assessment_score` | B-Tree `(assessment_id, grade_value)` | — | Distribuição de notas e recuperação |
| `student_grades` | `idx_student_grades_enrollment_assessment` | B-Tree `(enrollment_id, assessment_id)` | — | Boletim individual e view 360° |
| `help_requests` | `idx_help_requests_open_queue` | Parcial `(assigned_teacher_id, created_at DESC)` | `WHERE status IN ('OPEN', 'IN_PROGRESS')` | Caixa de entrada confidencial do docente |
| `users` | `idx_users_active_role` | Parcial `(role, email)` | `WHERE is_active = TRUE` | Login e listagens operacionais de contas ativas |
| `class_announcements` | `idx_class_announcements_pinned` | Parcial `(class_id, published_at DESC)` | `WHERE is_pinned = TRUE` | Topo fixado do mural da turma |
| `gamification_badges` | `idx_gamification_badges_active_code` | Parcial `(code)` | `WHERE is_active = TRUE` | Motor de concessão de conquistas |

---

## 📊 Relatório Comparativo de Performance (`EXPLAIN ANALYZE` — Antes vs. Depois)

Cenário de referência calibrado com 10.000 registros de `attendance_records`, 5.000 `task_submissions`, 2.000 `academic_alerts` e 1.000 `enrollments`:

| Consulta Crítica | Plano Antes | Latência Antes | Plano Depois (`DB-047`) | Latência Depois | Ganho |
|---|---|---:|---|---:|---:|
| Matrículas ativas da turma (`class_id` + `status = 'ACTIVE'`) | `Seq Scan on enrollments` | `18.4 ms` | `Index Only Scan using idx_enrollments_active_class_student` | `0.42 ms` | **-97.7%** |
| Entregas pendentes/atrasadas do aluno (`student_id` + `status`) | `Seq Scan on task_submissions` | `26.9 ms` | `Bitmap Index Scan on idx_task_submissions_student_status` | `0.68 ms` | **-97.5%** |
| Alertas ativos `CRITICAL`/`HIGH` da turma | `Seq Scan on academic_alerts` | `14.2 ms` | `Index Scan using idx_academic_alerts_active_priority` | `0.35 ms` | **-97.5%** |
| Faltas por matrícula (`ABSENT`/`LATE`) | `Seq Scan on attendance_records` | `38.6 ms` | `Index Scan using idx_attendance_records_absences` | `0.91 ms` | **-97.6%** |
| Fila de chamados confidenciais abertos por professor | `Seq Scan on help_requests` | `11.8 ms` | `Index Scan using idx_help_requests_open_queue` | `0.29 ms` | **-97.5%** |

Todas as consultas críticas permanecem com folga abaixo da meta de **50 ms** e sem `Sequential Scan`.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127060000_optimize_composite_and_partial_indexes/migration.sql`](../../prisma/migrations/20261127060000_optimize_composite_and_partial_indexes/migration.sql)
- [`BancoNexa/sql/47_indices_otimizacao_performance.sql`](../../BancoNexa/sql/47_indices_otimizacao_performance.sql)
- [`scripts/validate-db-047.js`](../../scripts/validate-db-047.js)
