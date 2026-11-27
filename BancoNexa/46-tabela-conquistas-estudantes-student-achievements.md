# 🏆 [DB-046] Tabela de Conquistas Desbloqueadas pelos Estudantes (`student_achievements`)

> **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P2 | **Estimativa**: 2 SP  
> **Migration SQL**: `20261127050000_create_student_achievements_table`

---

## 🎯 Objetivo

Registrar as insígnias técnicas desbloqueadas por cada estudante e sua origem pedagógica, garantindo unicidade `(student_id, badge_id)`, integridade referencial com `enrollments` e `gamification_badges` e consulta cronológica otimizada em `(student_id, unlocked_at DESC)`.

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `student_id` | `UUID` | Não | FK `users(id)` (`STUDENT`) | Estudante premiado |
| `enrollment_id` | `UUID` | Não | FK `enrollments(id)` | Matrícula ativa vinculada |
| `badge_id` | `UUID` | Não | FK `gamification_badges(id)` | Conquista desbloqueada |
| `unlocked_at` | `TIMESTAMPTZ` | Não | `CURRENT_TIMESTAMP` | Data/hora do desbloqueio |
| `origin_reference` | `VARCHAR(150)` | Não | `>= 3` caracteres | Módulo, tarefa ou ciclo de origem |

---

## 🔒 Constraints, Triggers e Índices

- **`uq_student_achievements_composite`**: `UNIQUE (student_id, badge_id)` impedindo ganho duplicado da mesma insígnia.
- **`trg_student_achievements_validate_integrity`**: valida role `STUDENT`, titularidade da matrícula e exige `gamification_badges.is_active = TRUE` na concessão.
- **`idx_student_achievements_student_unlocked`**: índice B-Tree composto em `(student_id, unlocked_at DESC)`.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127050000_create_student_achievements_table/migration.sql`](../../prisma/migrations/20261127050000_create_student_achievements_table/migration.sql)
- [`BancoNexa/sql/46_tabela_student_achievements.sql`](../../BancoNexa/sql/46_tabela_student_achievements.sql)
- [`scripts/validate-db-046.js`](../../scripts/validate-db-046.js)
