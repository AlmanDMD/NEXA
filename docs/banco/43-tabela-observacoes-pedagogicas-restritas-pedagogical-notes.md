# 🔐 [DB-043] Tabela de Observações Pedagógicas Restritas (`pedagogical_notes`)

> **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P0 | **Estimativa**: 3 SP  
> **Migration SQL**: `20261127020000_create_pedagogical_notes_table`

---

## 🎯 Objetivo

Armazenar observações pedagógicas sigilosas registradas por professores e coordenação sobre intervenções e acompanhamentos de estudantes matriculados, garantindo controle estrito por `visibility_scope`, bloqueio total a estudantes (RLS) e rastro obrigatório de leitura e escrita em `audit_logs` (DB-009).

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `student_id` | `UUID` | Não | FK `users(id)` (`STUDENT`) | Estudante acompanhado |
| `enrollment_id` | `UUID` | Não | FK `enrollments(id)` | Matrícula obrigatória do estudante |
| `author_id` | `UUID` | Não | FK `users(id)` (`TEACHER`/`COORDINATOR`/`ADMIN`) | Autor responsável |
| `visibility_scope` | `note_visibility_scope_enum` | Não | `'PRIVATE_AUTHOR'` | `PRIVATE_AUTHOR`, `TEACHERS_AND_COORD`, `COORDINATION_ONLY` |
| `category` | `note_category_enum` | Não | `INTERVENTION` / `MENTORING` / `BEHAVIORAL` / `ACCOMMODATION` | Natureza do acompanhamento |
| `note_content` | `TEXT` | Não | `>= 5` caracteres | Texto restrito (cifrado em camada de aplicação) |
| `requires_followup` | `BOOLEAN` | Não | `FALSE` | Indica necessidade de retorno agendado |
| `followup_date` | `DATE` | Sim | Exige `requires_followup = TRUE` | Data prevista do acompanhamento |
| `created_at` / `updated_at` | `TIMESTAMPTZ` | Não | `CURRENT_TIMESTAMP` | Auditoria temporal |

---

## 🛡️ Controle de Acesso & Auditoria Obrigatória

1. **RLS (`pol_pedagogical_notes_scope_isolation`)**: nega acesso absoluto ao papel `STUDENT`; `TEACHER` acessa `TEACHERS_AND_COORD` e próprias notas; `COORDINATOR` acessa `TEACHERS_AND_COORD`, `COORDINATION_ONLY` e próprias notas.
2. **Escrita auditada (`trg_pedagogical_notes_audit_trail`)**: grava automaticamente `PEDAGOGICAL_NOTE_CREATE`, `PEDAGOGICAL_NOTE_UPDATE` e `PEDAGOGICAL_NOTE_DELETE` em `audit_logs` sem jamais copiar `note_content` para os logs.
3. **Leitura auditada (`fn_read_pedagogical_note_audited`)**: valida `visibility_scope` e registra `PEDAGOGICAL_NOTE_READ` em `audit_logs` a cada consulta sensível.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127020000_create_pedagogical_notes_table/migration.sql`](../../prisma/migrations/20261127020000_create_pedagogical_notes_table/migration.sql)
- [`BancoNexa/sql/43_tabela_pedagogical_notes.sql`](../../BancoNexa/sql/43_tabela_pedagogical_notes.sql)
- [`scripts/validate-db-043.js`](../../scripts/validate-db-043.js)
