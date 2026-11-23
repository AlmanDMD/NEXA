# 📜 [DB-009] Tabela de Registro de Atividades e Auditoria (`audit_logs`) — Projeto NEXA

> **ID do Card**: `DB-009` | **Epic**: `EPIC-10: Relatórios, Governança de Dados & Qualidade` | **Sprint / Lote**: `Lote 1 (S1)`  
> **Prioridade**: `P1` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261105030000_create_audit_logs_table/migration.sql`](../../prisma/migrations/20261105030000_create_audit_logs_table/migration.sql), [`BancoNexa/sql/09_tabela_audit_logs.sql`](../../BancoNexa/sql/09_tabela_audit_logs.sql), [`prisma/schema.prisma`](../../prisma/schema.prisma)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-008`](./08-tabela-sessoes-refresh-tokens.md) | ➡️ Próximo: `DB-010` | 🔓 Desbloqueia: `DB-010`, `DB-043`, `DB-049`, `BE-019`, `BE-027`, `BE-039`, `BE-045`, `BE-048`, `DOC-017`

---

## 1. Objetivo e Governança de Dados Acadêmicos (LGPD)

O card **`DB-009`** implementa a tabela `audit_logs` no **PostgreSQL 16 (Docker)** para rastrear de forma transparente e inviolável todas as operações sensíveis do ecossistema SENAI:
- **Retificação de Notas e Médias (`entity = 'StudentGrade'`)**: Registra qual docente alterou a nota, o valor anterior (`old_values`) e o novo valor (`new_values`);
- **Alteração de Frequência e Matrículas (`entity = 'AttendanceRecord' | 'Enrollment'`)**: Rastreia mudanças de status (`ACTIVE -> DROPPED`) e justificativas de faltas;
- **Acesso e Escrita em Observações Pedagógicas Confidenciais (`entity = 'PedagogicalNote'`)**: Exigência direta da regra de isolamento LGPD (`DB-001` / `DB-043`);
- **Execução de Rotinas de Sistema (`user_id IS NULL`)**: Como jobs automatizados de anonimização LGPD (`DB-049`).

---

## 2. Por que `JSONB` com Índices `GIN` e `ON DELETE SET NULL`?

```mermaid
flowchart LR
    ACT["Ação Crítica na API<br/>(Ex.: Alterar Nota 5.5 -> 7.0)"] --> LOG["INSERT INTO audit_logs"]
    subgraph Postgres16["PostgreSQL 16 (audit_logs)"]
        OLD["old_values (JSONB)<br/>{\"grade_value\": 5.50}"]
        NEW["new_values (JSONB)<br/>{\"grade_value\": 7.00}"]
        GIN["Índices GIN:<br/>idx_audit_logs_old_values_gin<br/>idx_audit_logs_new_values_gin<br/>(Suporta operador @>)"]
        FK["FK user_id:<br/>ON DELETE SET NULL<br/>(Nunca apaga o histórico!)"]
        TRG["Trigger: trg_audit_logs_prevent_delete<br/>(Bloqueia DELETE físico)"]
    end
    LOG --> OLD
    LOG --> NEW
    OLD --- GIN
    NEW --- GIN
```

1. **Armazenamento Binário Indexado (`JSONB` + `GIN`)**: Diferentemente do tipo `JSON` textual, o `JSONB` do PostgreSQL 16 decompõe o documento em formato binário estruturado, permitindo criar índices **GIN (*Generalized Inverted Index*)** (`idx_audit_logs_old_values_gin` e `idx_audit_logs_new_values_gin`) para consultas instantâneas com o operador de contenção `@>`:
   ```sql
   -- Exemplo: Buscar todas as auditorias onde a nota antiga era 5.50
   SELECT * FROM audit_logs
   WHERE entity = 'StudentGrade'
     AND old_values @> '{"grade_value": 5.50}'::jsonb
   ORDER BY created_at DESC;
   ```
2. **Preservação Perpétua do Histórico (`ON DELETE SET NULL`)**: A chave estrangeira `fk_audit_logs_user` **não utiliza `CASCADE`**. Caso uma conta de usuário seja removida no futuro, o campo `user_id` passa para `NULL`, mas o registro da alteração em `audit_logs` permanece 100% íntegro.
3. **Imutabilidade contra Exclusão (`trg_audit_logs_prevent_delete`)**: Uma trigger PL/pgSQL bloqueia comandos `DELETE FROM audit_logs`, garantindo que nem mesmo acessos diretos apaguem rastros de auditoria.

---

## 3. Especificação Relacional da Tabela `audit_logs` (PostgreSQL 16)

| Coluna | Tipo SQL Nativo | Nulo? | Default | Constraints e Regras de Negócio |
|---|---|:---:|---|---|
| `id` | `UUID` | `NOT NULL` | `gen_random_uuid()` | `PRIMARY KEY` |
| `user_id` | `UUID` | `NULL` | `NULL` | `FK -> users(id) ON DELETE SET NULL ON UPDATE CASCADE` |
| `action` | `VARCHAR(100)` | `NOT NULL` | — | `CHECK (CHAR_LENGTH(BTRIM(action)) >= 2)` (ex.: `'UPDATE_GRADE'`) |
| `entity` | `VARCHAR(100)` | `NOT NULL` | — | `CHECK (CHAR_LENGTH(BTRIM(entity)) >= 2)` (ex.: `'PedagogicalNote'`) |
| `entity_id` | `VARCHAR(100)` | `NOT NULL` | — | Identificador do registro afetado |
| `old_values` | `JSONB` | `NULL` | `NULL` | Estado anterior do registro (`USING GIN`) |
| `new_values` | `JSONB` | `NULL` | `NULL` | Novo estado do registro (`USING GIN`) |
| `ip_address` | `VARCHAR(45)` | `NULL` | `NULL` | Endereço IPv4 ou IPv6 de origem da operação |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | Índice temporal decrescente (`idx_audit_logs_created_at`) |

---

## 4. Checklist de Verificação dos Critérios de Aceitação (`DB-009`)

- [x] **Critério 1 — Tabela com campos `JSONB` para armazenar diff de valores antigos e novos**: Colunas `old_values JSONB` e `new_values JSONB` criadas e indexadas com `GIN`.
- [x] **Critério 2 — Sem foreign key estrita com deleção em cascata (manter histórico mesmo se usuário for deletado)**: Implementado com `user_id UUID NULL` e `ON DELETE SET NULL`.
- [x] **Critério 3 — Índice temporal em `created_at` para relatórios rápidos**: Criado `idx_audit_logs_created_at ON audit_logs USING BTREE (created_at DESC)`.
- [x] **Observação Técnica — Tipo `JSONB` para buscas indexadas com `@>`**: Índices `GIN` configurados e validados com teste unitário de contenção `@>`.
