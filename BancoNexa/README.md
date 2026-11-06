# 🗄️ Workspace de Banco de Dados — Projeto NEXA (SENAI)

Este diretório concentra os artefatos, modelos, scripts **SQL nativos (PostgreSQL 16)**, configuração **Docker**, **Migrations SQL versionadas**, contratos de **Tipos Enum** e validações da trilha de **Banco de Dados (`DB-001` a `DB-050`)** do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**.

> **Diretriz Arquitetural de Banco de Dados**: Todo o desenvolvimento de banco de dados do projeto NEXA é construído sobre **Docker + PostgreSQL 16 + SQL Nativo (DDL/DML/PLpgSQL)**.

---

## 📂 Estrutura de Entregáveis (Sprint 1 / Lote 1)

| Card | Entregável | Caminho no Repositório | Status |
|---|---|---|---|
| **`DB-001`** | Modelo Conceitual e Entidades do Domínio Acadêmico SENAI | [`docs/banco/01-modelo-conceitual.md`](../docs/banco/01-modelo-conceitual.md) e [`BancoNexa/01-modelo-conceitual.md`](./01-modelo-conceitual.md) | ✅ Concluído |
| **`DB-002`** | Modelo Lógico Relacional Normalizado (3FN) + Script DDL SQL | [`docs/banco/02-modelo-logico-3fn.md`](../docs/banco/02-modelo-logico-3fn.md) e [`BancoNexa/sql/02_modelo_logico_3fn.sql`](./sql/02_modelo_logico_3fn.sql) | ✅ Concluído |
| **`DB-003`** | Instância PostgreSQL 16 e Ambiente Docker Compose | [`docker-compose.yml`](../docker-compose.yml), [`.env.example`](../.env.example), [`BancoNexa/docker/initdb/`](./docker/initdb/) e [`docs/banco/03-instancia-postgresql-docker.md`](../docs/banco/03-instancia-postgresql-docker.md) | ✅ Concluído |
| **`DB-004`** | Estrutura de Esquema e Migrations SQL Versionadas | [`prisma/schema.prisma`](../prisma/schema.prisma), [`prisma/migrations/`](../prisma/migrations/), [`BancoNexa/migrations/`](./migrations/), [`scripts/db-migrate.js`](../scripts/db-migrate.js) e [`docs/banco/04-estrutura-migrations-versionadas.md`](../docs/banco/04-estrutura-migrations-versionadas.md) | ✅ Concluído |
| **`DB-005`** | Enumerações Globais de Sistema (Roles, Status, Graus de Risco) | [`BancoNexa/sql/05_enums_globais.sql`](./sql/05_enums_globais.sql), [`BancoNexa/types/`](./types/) e [`docs/banco/05-enumeracoes-globais-sistema.md`](../docs/banco/05-enumeracoes-globais-sistema.md) | ✅ Concluído |
| **`DB-006`** | Tabela de Usuários (`users`) com Hash Seguro de Senha | [`BancoNexa/sql/06_tabela_users.sql`](./sql/06_tabela_users.sql), [`prisma/migrations/20261105000000_create_users_table/`](../prisma/migrations/20261105000000_create_users_table/) e [`docs/banco/06-tabela-usuarios-hash-senha.md`](../docs/banco/06-tabela-usuarios-hash-senha.md) | ✅ Concluído |
| **`DB-007`** | Tabela de Perfis de Usuário (`user_profiles`) e Dados de Contato | [`BancoNexa/sql/07_tabela_user_profiles.sql`](./sql/07_tabela_user_profiles.sql), [`prisma/migrations/20261105010000_create_user_profiles_table/`](../prisma/migrations/20261105010000_create_user_profiles_table/) e [`docs/banco/07-tabela-perfis-usuario-lgpd.md`](../docs/banco/07-tabela-perfis-usuario-lgpd.md) | ✅ Concluído |
| **`DB-008`** | Tabela de Sessões e Refresh Tokens com Revogação (`auth_sessions`) | [`BancoNexa/sql/08_tabela_auth_sessions.sql`](./sql/08_tabela_auth_sessions.sql), [`prisma/migrations/20261105020000_create_auth_sessions_table/`](../prisma/migrations/20261105020000_create_auth_sessions_table/) e [`docs/banco/08-tabela-sessoes-refresh-tokens.md`](../docs/banco/08-tabela-sessoes-refresh-tokens.md) | ✅ Concluído |
| **`DB-009`** | Tabela de Registro de Atividades e Auditoria (`audit_logs`) | [`BancoNexa/sql/09_tabela_audit_logs.sql`](./sql/09_tabela_audit_logs.sql), [`prisma/migrations/20261105030000_create_audit_logs_table/`](../prisma/migrations/20261105030000_create_audit_logs_table/) e [`docs/banco/09-tabela-auditoria-logs-jsonb.md`](../docs/banco/09-tabela-auditoria-logs-jsonb.md) | ✅ Concluído |
| **`DB-010`** | Script Base de Migração Inicial e Verificação de Conexão | [`prisma/check-connection.ts`](../prisma/check-connection.ts), [`BancoNexa/sql/10_migracao_inicial_lote1_e_sanidade.sql`](./sql/10_migracao_inicial_lote1_e_sanidade.sql), [`README.md`](../README.md) e [`docs/banco/10-migracao-inicial-verificacao-conexao.md`](../docs/banco/10-migracao-inicial-verificacao-conexao.md) | ✅ Concluído (Lote 1 Finalizado) |

---

## 🧪 Validação Automatizada dos Cards Concluídos

Para executar todos os testes de validação de conformidade dos cards de Banco de Dados na raiz do repositório:

```bash
npm.cmd run db:validate
```
