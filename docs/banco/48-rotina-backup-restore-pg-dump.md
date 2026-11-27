# 💾 [DB-048] Rotina de Backup Automatizado e Script de Restauração (`pg_dump` / `pg_restore`)

> **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P1 | **Estimativa**: 3 SP  
> **Referência Documental**: `DOC-017` (Segurança, Continuidade e LGPD)

---

## 🎯 Objetivo

Garantir continuidade operacional e proteção contra perda acidental do banco PostgreSQL 16 com backup comprimido (`pg_dump -Fc`), verificação de integridade por hash SHA-256, rotação automática dos últimos **7 backups** em `backups/` (pasta ignorada pelo Git) e restauração auditada com verificação pós-restore.

---

## 🛠️ Scripts Disponíveis

| Script | Ambiente | Comando | Descrição |
|---|---|---|---|
| `scripts/db-backup.sh` | Linux / macOS / WSL / CI | `bash scripts/db-backup.sh` | Executa `pg_dump -Fc -Z 9`, gera `.sha256` e mantém últimos 7 dumps |
| `scripts/db-restore.sh` | Linux / macOS / WSL / CI | `bash scripts/db-restore.sh [arquivo.dump] [banco]` | Valida SHA-256, executa `pg_restore --clean --if-exists` e verifica tabelas, views e triggers |
| `scripts/db-backup.js` | Windows PowerShell / Node 20+ | `npm run db:backup` | Equivalente multiplataforma com suporte Docker live (`pg_dump -Fc`) e modo offline/CI (`.dump.gz`) |
| `scripts/db-restore.js` | Windows PowerShell / Node 20+ | `npm run db:restore` | Restaura dump live ou audita integridade lógica pós-restore de schema, views, triggers e seeds |

---

## 📋 Procedimento Operacional Padrão (Alinhado a `DOC-017`)

### 1. Gerar Backup Diário
```bash
npm run db:backup
# ou em Linux/CI:
bash scripts/db-backup.sh
```
- Os arquivos são salvos em `backups/nexa_backup_YYYYMMDD_HHMMSS.dump` (junto ao `.sha256` e `.meta.json`).
- A pasta `backups/` está explicitamente listada em `.gitignore` para impedir versionamento acidental de dumps acadêmicos.
- A rotação automática preserva os **7 backups mais recentes** e remove os excedentes.

### 2. Restaurar em Banco Limpo e Auditar Integridade
```bash
npm run db:restore -- backups/nexa_backup_20261127_030000.dump nexa_senai_db
# ou em Linux/CI:
bash scripts/db-restore.sh backups/nexa_backup_20261127_030000.dump nexa_senai_db
```
- Valida o hash criptográfico SHA-256 antes de tocar o banco alvo.
- Restaura 100% do schema, tipos ENUM, views analíticas (`vw_student_360_performance`, `vw_module_attendance_risk`, `vw_self_eval_discrepancy`), triggers, funções e dados.
- Executa consulta pós-restauração confirmando contagem íntegra de tabelas, views e triggers.

---

## 📂 Artefatos Relacionados

- [`scripts/db-backup.sh`](../../scripts/db-backup.sh) · [`scripts/db-restore.sh`](../../scripts/db-restore.sh)
- [`scripts/db-backup.js`](../../scripts/db-backup.js) · [`scripts/db-restore.js`](../../scripts/db-restore.js)
- [`scripts/validate-db-048.js`](../../scripts/validate-db-048.js)
