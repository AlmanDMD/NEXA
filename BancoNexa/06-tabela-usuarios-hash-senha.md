# 🔐 [DB-006] Tabela de Usuários (`users`) com Hash Seguro de Senha — Projeto NEXA

> **ID do Card**: `DB-006` | **Epic**: `EPIC-01: Autenticação, Perfis (RBAC) & Segurança` | **Sprint / Lote**: `Lote 1 (S1)`  
> **Prioridade**: `P0` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261105000000_create_users_table/migration.sql`](../../prisma/migrations/20261105000000_create_users_table/migration.sql), [`BancoNexa/sql/06_tabela_users.sql`](../../BancoNexa/sql/06_tabela_users.sql), [`prisma/schema.prisma`](../../prisma/schema.prisma)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-005`](./05-enumeracoes-globais-sistema.md) | ➡️ Próximo: `DB-007` | 🔓 Desbloqueia: `DB-007`, `DB-008`, `DB-009`, `DB-010`, `DB-017`, `DB-018`, `DB-041`, `DB-043`, `DB-044`, `DB-049`, `BE-005`

---

## 1. Objetivo e Arquitetura de Segurança da Entidade `users`

O card **`DB-006`** implementa a tabela central de autenticação (`users`) no **PostgreSQL 16 (Docker)**, desenhada com **Defesa em Profundidade (Defense-in-Depth)** para proteger credenciais e impedir inconsistências de identidade:

1. **Identificador Universal `UUID v4` (`gen_random_uuid()`)**: Impede enumeração sequencial de contas de alunos, professores e coordenadores nas rotas REST.
2. **Normalização Automática de E-mail em Minúsculo (`lowercased`)**: Uma função PL/pgSQL com Trigger `BEFORE INSERT OR UPDATE` (`fn_users_normalize_and_touch`) aplica `LOWER(BTRIM(NEW.email))` antes da gravação, combinada à constraint `chk_users_email_lowercase` e ao índice único `idx_users_email_lower`. Assim, `'Aluno@SENAI.br'` e `'aluno@senai.br'` são tratados de forma idêntica e qualquer tentativa de duplicidade é rejeitada com erro de chave única (`SQLSTATE 23505` / código Prisma `P2002`).
3. **Bloqueio de Senha em Texto Puro no Motor SQL**: A constraint `chk_users_password_hash_not_plaintext` exige que `password_hash` tenha no mínimo 50 caracteres e obedeça ao padrão de algoritmos de hash criptográfico (`$2a$`, `$2b$`, `$2y$` do **Bcrypt** ou `$argon2` do **Argon2**), tornando impossível gravar senhas em texto puro no banco mesmo por falha de código.
4. **Indexação `B-Tree` Otimizada**: Índices dedicados para `email` (`idx_users_email`) e para filtros compostos de papel e status (`idx_users_role_is_active`).

---

## 2. Estrutura Relacional da Tabela `users` (PostgreSQL 16)

| Coluna | Tipo SQL Nativo | Nulo? | Default | Constraints e Regras de Negócio |
|---|---|:---:|---|---|
| `id` | `UUID` | `NOT NULL` | `gen_random_uuid()` | `PRIMARY KEY` |
| `email` | `VARCHAR(255)` | `NOT NULL` | — | `UNIQUE (uq_users_email)`, `CHECK (email = LOWER(BTRIM(email)) AND POSITION('@' IN email) > 1)` |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | — | `CHECK (CHAR_LENGTH >= 50 AND regex Bcrypt/Argon2)` — proíbe texto puro |
| `role` | `user_role_enum` | `NOT NULL` | `'STUDENT'` | Papel RBAC (`ADMIN`, `COORDINATOR`, `TEACHER`, `STUDENT`) |
| `is_active` | `BOOLEAN` | `NOT NULL` | `TRUE` | Controle de conta ativa / desativada |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | Data/hora de criação com timezone |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | Atualizado automaticamente por Trigger em `UPDATE` |

---

## 3. Índices e Triggers Implementados em SQL

### 3.1. Índices Criados
- **`uq_users_email`**: Constraint `UNIQUE` primária sobre a coluna `email`.
- **`idx_users_email`**: Índice `B-Tree` explícito no campo `email` para busca em $O(\log n)$ durante o login (`BE-005`).
- **`idx_users_email_lower`**: Índice único funcional em `LOWER(email)` garantindo proteção case-insensitive absoluta.
- **`idx_users_role_is_active`**: Índice composto em `(role, is_active)` para listagens administrativas de alunos e docentes ativos.

### 3.2. Trigger de Normalização (`trg_users_normalize_and_touch`)
```sql
CREATE OR REPLACE FUNCTION fn_users_normalize_and_touch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.email IS NOT NULL THEN
        NEW.email := LOWER(BTRIM(NEW.email));
    END IF;

    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;
```

---

## 4. Comportamento de Rejeição de Duplicidade (`SQLSTATE 23505` / `P2002`)

Quando uma segunda inserção tenta cadastrar um e-mail já existente (mesmo com letras maiúsculas/minúsculas diferentes, ex.: `'Professor.Mec@SENAI.br'` após `'professor.mec@senai.br'`):
1. O Trigger converte para `'professor.mec@senai.br'`;
2. O PostgreSQL 16 aborta a transação lançando `ERROR: duplicate key value violates unique constraint "uq_users_email" (SQLSTATE 23505)`;
3. Na camada ORM/API, esse código é traduzido para o código de erro **`P2002`** (`Unique constraint failed on the fields: (email)`).

---

## 5. Checklist de Verificação dos Critérios de Aceitação (`DB-006`)

- [x] **Critério 1 — Tabela `users` com constraint `UNIQUE` em `email`**: Implementada via `CONSTRAINT uq_users_email UNIQUE (email)` e `idx_users_email_lower`.
- [x] **Critério 2 — Campo `password_hash` não nulo sem armazenamento de texto puro**: `password_hash VARCHAR(255) NOT NULL` protegido pela constraint `chk_users_password_hash_not_plaintext` que exige hash Bcrypt/Argon2 válido.
- [x] **Critério 3 — Índices criados no campo `email`**: Criados `idx_users_email`, `uq_users_email` e `idx_users_email_lower`.
- [x] **Observação Técnica — E-mail em minúsculo (`lowercased`)**: Garantido por Trigger `BEFORE INSERT OR UPDATE` e `CHECK (email = LOWER(BTRIM(email)))`.
