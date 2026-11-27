# 📢 [DB-041] Tabela de Mural de Avisos da Turma (`class_announcements`)

> **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P1 | **Estimativa**: 2 SP  
> **Migration SQL**: `20261127000000_create_class_announcements_table`

---

## 🎯 Objetivo

Armazenar comunicados oficiais enviados por professores, coordenadores e administradores direcionados a uma turma (`classes`) e, opcionalmente, a uma disciplina (`subjects`), suportando fixação no topo (`is_pinned`) e prioridade visual (`NORMAL`, `IMPORTANT`, `URGENT`).

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `class_id` | `UUID` | Não | FK `classes(id)` (`RESTRICT`) | Turma destinatária obrigatória |
| `subject_id` | `UUID` | Sim | FK `subjects(id)` (`RESTRICT`) | Disciplina opcional (mesmo curso da turma) |
| `author_id` | `UUID` | Não | FK `users(id)` (`RESTRICT`) | Autor (`TEACHER`, `COORDINATOR` ou `ADMIN`) |
| `title` | `VARCHAR(150)` | Não | `CHAR_LENGTH(BTRIM(title)) >= 3` | Título do comunicado |
| `content` | `TEXT` | Não | `CHAR_LENGTH(BTRIM(content)) >= 5` | Corpo completo do aviso |
| `priority` | `announcement_priority_enum` | Não | `'NORMAL'` | `NORMAL`, `IMPORTANT` ou `URGENT` |
| `is_pinned` | `BOOLEAN` | Não | `FALSE` | Fixação no topo do mural |
| `published_at` | `TIMESTAMPTZ` | Não | `CURRENT_TIMESTAMP` | Data/hora de publicação |
| `expires_at` | `TIMESTAMPTZ` | Sim | `expires_at > published_at` | Expiração opcional do aviso |

---

## 🔒 Constraints, Triggers e Índices

- **`chk_announcements_expiration`**: impede aviso expirando antes da data de publicação.
- **`trg_class_announcements_validate_integrity`**: bloqueia autoria por `STUDENT` e garante coerência entre `subject.course_id` e `class.course_id`.
- **`idx_class_announcements_feed`**: índice B-Tree composto em `(class_id, is_pinned DESC, published_at DESC)` garantindo leitura imediata do mural ordenado.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127000000_create_class_announcements_table/migration.sql`](../../prisma/migrations/20261127000000_create_class_announcements_table/migration.sql)
- [`BancoNexa/sql/41_tabela_class_announcements.sql`](../../BancoNexa/sql/41_tabela_class_announcements.sql)
- [`scripts/validate-db-041.js`](../../scripts/validate-db-041.js)
