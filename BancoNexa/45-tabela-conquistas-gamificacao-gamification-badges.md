# 🏅 [DB-045] Tabela de Conquistas e Níveis de Gamificação (`gamification_badges`)

> **Epic**: EPIC-09: Gamificação Pedagógica Transparente & Níveis  
> **Sprint / Lote**: S5 / Lote 5 | **Prioridade**: P2 | **Estimativa**: 2 SP  
> **Migration SQL**: `20261127040000_create_gamification_badges_table`

---

## 🎯 Objetivo

Cadastrar o catálogo transparente de insígnias (badges) e pontuação de experiência técnica (XP) baseadas no domínio de competências industriais SENAI e assiduidade, com `criteria_explanation` obrigatório e sem rankings punitivos.

---

## 🧱 Estrutura da Tabela

| Coluna | Tipo PostgreSQL 16 | Nulo | Padrão / Regra | Descrição |
|---|---|---|---|---|
| `id` | `UUID` | Não | `gen_random_uuid()` | Chave primária |
| `code` | `VARCHAR(60)` | Não | `UNIQUE`, regex `^[A-Z0-9][A-Z0-9_-]{2,59}$` | Código único (ex.: `BADGE-METROLOGIA-100`) |
| `title` | `VARCHAR(120)` | Não | `>= 3` caracteres | Título da conquista (ex.: `Mestre do Micrômetro`) |
| `description` | `TEXT` | Não | `>= 10` caracteres | Descrição pedagógica |
| `criteria_explanation` | `TEXT` | Não | `>= 15` caracteres (obrigatório) | Regra transparente de desbloqueio |
| `icon_name` | `VARCHAR(80)` | Não | `>= 2` caracteres | Identificador visual do ícone |
| `xp_reward` | `INTEGER` | Não | `DEFAULT 50`, `CHECK (xp_reward > 0 AND xp_reward <= 5000)` | XP técnico positivo |
| `competency_id` | `UUID` | Sim | FK `competencies(id)` | Competência técnica vinculada (opcional) |
| `is_active` | `BOOLEAN` | Não | `TRUE` | Controle de ativação |
| `created_at` | `TIMESTAMPTZ` | Não | `CURRENT_TIMESTAMP` | Data de criação |

---

## 🌱 Conquistas Técnicas SENAI Populadas no Seed

O seed (`prisma/seed.ts` → `BancoNexa/sql/45_seed_gamification_badges.sql`) cadastra 6 conquistas oficiais:
1. `BADGE-METROLOGIA-100` — **Mestre do Micrômetro** (150 XP)
2. `BADGE-PAQUIMETRO-PRO` — **Olho de Precisão H7** (120 XP)
3. `BADGE-TORNEARIA-EXACT` — **Especialista em Tornearia Cilíndrica** (200 XP)
4. `BADGE-SEGURANCA-NR12` — **Guardião NR-12 & 5S** (180 XP)
5. `BADGE-ASSIDUIDADE-100` — **Presença de Aço 100%** (100 XP)
6. `BADGE-AUTOCONHECIMENTO-360` — **Calibração Metacognitiva** (130 XP)

---

## 📂 Artefatos Relacionados

- [`prisma/migrations/20261127040000_create_gamification_badges_table/migration.sql`](../../prisma/migrations/20261127040000_create_gamification_badges_table/migration.sql)
- [`BancoNexa/sql/45_tabela_gamification_badges.sql`](../../BancoNexa/sql/45_tabela_gamification_badges.sql)
- [`BancoNexa/sql/45_seed_gamification_badges.sql`](../../BancoNexa/sql/45_seed_gamification_badges.sql)
- [`scripts/validate-db-045.js`](../../scripts/validate-db-045.js)
