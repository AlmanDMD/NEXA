# 💬 [DB-044] Tabela de Conversações e Mensagens Internas (`chat_messages`)

> **Epic**: EPIC-08: Comunicação Oficial & Solicitações Confidenciais  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P2 | **Estimativa**: 3 SP  
> **Migration SQL**: `20261127030000_create_chat_messages_table`

---

## 🎯 Objetivo

Viabilizar troca de mensagens privadas contextualizadas dentro de uma solicitação de apoio (`help_requests`) entre estudante titular e docentes/coordenação, com controle de confirmação de leitura (`is_read` e `read_at`), exclusão em cascata (`ON DELETE CASCADE`) e ordenação cronológica crescente.

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `help_request_id` | `UUID` | Não | FK `help_requests(id)` (`ON DELETE CASCADE`) | Chamado confidencial associado |
| `sender_id` | `UUID` | Não | FK `users(id)` (`RESTRICT`) | Remetente autorizado |
| `message_body` | `TEXT` | Não | `>= 1` caractere útil | Conteúdo da mensagem |
| `is_read` | `BOOLEAN` | Não | `FALSE` | Confirmação de leitura |
| `read_at` | `TIMESTAMPTZ` | Sim | Consistente com `is_read` e `>= sent_at` | Momento da leitura |
| `sent_at` | `TIMESTAMPTZ` | Não | `CURRENT_TIMESTAMP` | Momento do envio |

---

## 🔒 Integridade, Sigilo e Índices

- **`trg_chat_messages_validate_integrity`**: impede que qualquer outro estudante envie mensagens em um `help_request` de terceiro e sincroniza `read_at` quando `is_read = TRUE`.
- **`pol_chat_messages_participants_only` (RLS)**: restringe a consulta e envio ao titular do `help_request` e docentes/gestão.
- **`idx_chat_messages_request_sent`**: índice B-Tree composto em `(help_request_id, sent_at ASC)` + índice parcial `idx_chat_messages_unread` (`WHERE is_read = FALSE`).

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127030000_create_chat_messages_table/migration.sql`](../../prisma/migrations/20261127030000_create_chat_messages_table/migration.sql)
- [`BancoNexa/sql/44_tabela_chat_messages.sql`](../../BancoNexa/sql/44_tabela_chat_messages.sql)
- [`scripts/validate-db-044.js`](../../scripts/validate-db-044.js)
