# 🛡️ [DB-049] Políticas de Retenção de Dados e Anonimização LGPD

> **Epic**: EPIC-10: Relatórios, Governança de Dados & Qualidade  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P1 | **Estimativa**: 5 SP  
> **Migration SQL**: `20261127070000_create_lgpd_retention_and_anonymization`  
> **Referência Legal / Documental**: Lei nº 13.709/2018 (LGPD), Seção 14 e `DOC-017`

---

## 🎯 Objetivo

Garantir minimização, retenção controlada (padrão institucional de **5 anos** após encerramento/inativação) e anonimização irreversível de dados pessoais (PII) de ex-alunos mediante solicitação formal ou expiração de prazo legal, preservando 100% da integridade referencial das métricas estatísticas anônimas por curso, turma e módulo.

---

## 🔄 Matriz de Anonimização Irreversível (`fn_anonymize_user_lgpd`)

| Tabela | Tratamento LGPD Aplicado | Integridade Referencial / Estatística |
|---|---|---|
| `users` | `email` → `anon_<sha256_20>@anonymized.nexa.local`; `password_hash` → hash irreversível; `is_active = FALSE` | UUID mantido como chave pseudonimizada (sem reidentificação possível) |
| `user_profiles` | `full_name` → `Titular Anonimizado #<HASH8>`; `registration_number` → `ANON-<HASH12>`; `phone`, `avatar_url`, `bio` → `NULL` | Registro 1:1 preservado sem PII |
| `auth_sessions` | `is_revoked = TRUE`; `ip_address = '0.0.0.0'`; `user_agent = 'ANONYMIZED_LGPD'` | Todas as sessões invalidadas |
| `help_requests` | `subject_title`, `description`, `resolution_summary` → marcadores `[ANONIMIZADO LGPD]` | `category`, `status`, `subject_id`, `module_id` e datas mantidos |
| `chat_messages` | `message_body` → `[MENSAGEM ANONIMIZADA CONFORME LGPD]` | Estrutura da thread preservada sem PII |
| `pedagogical_notes` | `note_content` → `[OBSERVAÇÃO PEDAGÓGICA ANONIMIZADA CONFORME LGPD]` | `category`, `visibility_scope` e datas mantidos |
| `student_self_assessments` | `difficulty_notes` → `NULL` | `perceived_level` e `confidence_score` preservados para análise agregada |
| `enrollments`, `attendance_records`, `student_grades`, `skill_evidences`, `academic_alerts`, `explainable_diagnostics`, `student_achievements` | **Preservados integralmente** (sem PII direto) | Estatísticas históricas da turma/curso 100% intactas |

---

## 📝 Auditoria Obrigatória (`audit_logs`)

- Toda execução individual (`fn_anonymize_user_lgpd`) grava `action = 'LGPD_USER_ANONYMIZATION'` em `audit_logs` contendo apenas o resumo quantitativo das tabelas afetadas e o prefixo do hash — **jamais registrando nome, e-mail ou telefone original no log**.
- Toda execução periódica em lote (`fn_enforce_lgpd_retention_policy(p_retention_years, p_actor_id)`) grava `action = 'LGPD_RETENTION_BATCH_RUN'`.
- Operação CLI disponível via `npm run db:lgpd-anonymize`.

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127070000_create_lgpd_retention_and_anonymization/migration.sql`](../../prisma/migrations/20261127070000_create_lgpd_retention_and_anonymization/migration.sql)
- [`BancoNexa/sql/49_politicas_retencao_anonimizacao_lgpd.sql`](../../BancoNexa/sql/49_politicas_retencao_anonimizacao_lgpd.sql)
- [`scripts/db-lgpd-anonymize.js`](../../scripts/db-lgpd-anonymize.js)
- [`scripts/validate-db-049.js`](../../scripts/validate-db-049.js)
