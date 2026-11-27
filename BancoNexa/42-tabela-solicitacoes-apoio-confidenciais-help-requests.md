# 🆘 [DB-042] Tabela de Solicitações de Apoio e Mentoria Confidenciais (`help_requests`)

> **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P0 | **Estimativa**: 3 SP  
> **Migration SQL**: `20261127010000_create_help_requests_table`

---

## 🎯 Objetivo

Persistir pedidos confidenciais de ajuda pedagógica e mentoria feitos por estudantes, com isolamento estrito contra visualização por outros colegas (`is_confidential = TRUE` por padrão + Row-Level Security) e rastreamento completo da máquina de estados `OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED`.

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `student_id` | `UUID` | Não | FK `users(id)` (`role = STUDENT`) | Estudante solicitante |
| `enrollment_id` | `UUID` | Não | FK `enrollments(id)` | Matrícula ativa vinculada ao aluno |
| `subject_id` | `UUID` | Não | FK `subjects(id)` | Disciplina do pedido |
| `module_id` | `UUID` | Sim | FK `learning_modules(id)` | Módulo prático opcional da disciplina |
| `assigned_teacher_id` | `UUID` | Sim | FK `users(id)` (`ON DELETE SET NULL`) | Professor/coordenador responsável |
| `category` | `help_request_category_enum` | Não | `TECHNICAL_DOUBT` / `PRACTICAL_DIFFICULTY` / `PERSONAL_PEDAGOGICAL` | Categoria da demanda |
| `subject_title` | `VARCHAR(150)` | Não | `>= 3` caracteres | Assunto resumido |
| `description` | `TEXT` | Não | `>= 10` caracteres | Relato confidencial da dificuldade |
| `is_confidential` | `BOOLEAN` | Não | `TRUE` | Proteção padrão contra exposição à turma |
| `status` | `help_request_status_enum` | Não | `'OPEN'` | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED` |
| `resolution_summary` | `TEXT` | Sim | — | Resumo da resolução pedagógica |
| `created_at` / `updated_at` / `closed_at` | `TIMESTAMPTZ` | `closed_at` Sim | `closed_at` obrigatório em `CLOSED` | Rastreamento temporal do ciclo |

---

## 🔒 Sigilo (RLS), Máquina de Estados e Índices

- **RLS (`pol_help_requests_confidential_isolation`)**: quando `app.current_user_role = 'STUDENT'`, somente registros onde `student_id = app.current_user_id` são visíveis.
- **Trigger (`trg_help_requests_validate_integrity`)**: valida papel `STUDENT`, titularidade de `enrollment_id`, vínculo `module -> subject`, transições válidas de status e preenchimento automático de `closed_at` e `updated_at`.
- **Índices obrigatórios**: `idx_help_requests_teacher_status (assigned_teacher_id, status)` e `idx_help_requests_student_status (student_id, status)`.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127010000_create_help_requests_table/migration.sql`](../../prisma/migrations/20261127010000_create_help_requests_table/migration.sql)
- [`BancoNexa/sql/42_tabela_help_requests.sql`](../../BancoNexa/sql/42_tabela_help_requests.sql)
- [`scripts/validate-db-042.js`](../../scripts/validate-db-042.js)
