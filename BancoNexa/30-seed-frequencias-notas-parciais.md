# 🌱 [DB-030] Seed com Registro Realista de Frequências e Notas Parciais — Projeto NEXA

> **ID do Card**: `DB-030` | **Epic**: `EPIC-03: Diário de Classe: Notas & Frequência` | **Sprint / Lote**: `Lote 3 (S3)`  
> **Prioridade**: `P1` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído (Lote 3 Finalizado)`  
> **Arquivos Principais**: [`prisma/seed.ts`](../../prisma/seed.ts), [`BancoNexa/sql/30_seed_frequencias_notas_parciais.sql`](../../BancoNexa/sql/30_seed_frequencias_notas_parciais.sql), [`scripts/validate-db-030.js`](../../scripts/validate-db-030.js)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-029`](./29-triggers-validacao-periodo-letivo-fechado.md) | ➡️ Próximo: `DB-031` | 🔒 Depende de: `DB-020`, `DB-021`, `DB-022`, `DB-025`, `DB-026`, `DB-028` | 🔓 Desbloqueia: `DB-040`, `DB-050`, `BE-030`

---

## 1. Objetivo e Cobertura de Cenários Pedagógicos

O card **`DB-030`** estende o script oficial [`prisma/seed.ts`](../../prisma/seed.ts) (`npm run db:seed`) para popular o banco de desenvolvimento com um histórico realista, determinístico e 100% idempotente de aulas, chamadas, entregas práticas, avaliações por rubrica e notas parciais de **30 estudantes fictícios anônimos** matriculados nas turmas de Mecânica (`MEC-2026-1` e `MEC-2026-2`).

Essa massa de dados garante que os dashboards e endpoints de médias, frequência e alertas (`FE-031` a `FE-038`, `BE-030`, `DB-040`) já abram imediatamente preenchidos com cenários pedagógicos reais.

---

## 2. Composição da Massa de Dados Fictícios (`DB-030`)

### 2.1. Distribuição dos 30 Estudantes Anônimos por Perfil Pedagógico

| Perfil Pedagógico | Qtd. Alunos | Turmas (`MEC-2026-1` / `MEC-2026-2`) | Presença Calculada | Entregas Práticas | Notas Parciais |
|---|:---:|:---:|:---:|---|---|
| **Ótimo Desempenho (`HIGH_PERFORMER`)** | `12` | `7` / `5` | `100.00%` (`0h` falta / `25h`) | `100% EVALUATED` (níveis `4..5`) | `8.60` a `9.65` |
| **Entregas Atrasadas (`LATE_DELIVERY`)** | `8` | `5` / `3` | `80.00%` (`5h` falta / `25h`) | `EVALUATED` + `LATE` + `PENDING` | `6.40` a `7.40` |
| **Próximo ao Limite de Faltas (`ATTENDANCE_BORDERLINE`)** | `5` | `3` / `2` | `76.00%` (`6h` falta / `25h` — `24%` faltas) | `EVALUATED` + `SUBMITTED` | `5.60` a `6.20` (com recuperação `7.20`) |
| **Em Risco Crítico (`AT_RISK`)** | `5` | `3` / `2` | `68.00%` (`8h` falta / `25h` — `32%` faltas) | `EVALUATED` (nível `2`) + `LATE` + `PENDING` | `3.20` a `4.50` (com recuperação `5.40`) |
| **Total** | **`30`** | **`18` / `12`** | **`68%` a `100%`** | **Todos os status do enum** | **`60` lançamentos** |

### 2.2. Volume Completo Gerado em `BancoNexa/sql/30_seed_frequencias_notas_parciais.sql`

- **`users` & `user_profiles` & `enrollments`**: `30` estudantes fictícios (`estudante.demo01@aluno.nexa.local` a `estudante.demo30@aluno.nexa.local`, `Estudante Demo 01` a `Estudante Demo 30`, matrículas `SENAI-2026-0001` a `SENAI-2026-0030`) — **zero CPFs e zero nomes reais**.
- **`class_lessons` (`DB-021`)**: `12` aulas ministradas (`7` em `MEC-2026-1` somando `25h` e `5` em `MEC-2026-2` somando `25h`), vinculadas às 4 disciplinas e módulos práticos.
- **`attendance_records` (`DB-022`)**: `186` registros de presença (`18 × 7 + 12 × 5`) com `PRESENT`, `ABSENT` e `LATE`, respeitando `absent_hours <= workload_hours` e gerando exatamente `100%`, `80%`, `76%` e `68%`.
- **`practical_tasks` (`DB-023`) & `task_criteria` (`DB-024`)**: `6` tarefas práticas de oficina (`4` em `MEC-2026-1`, `2` em `MEC-2026-2`) e `18` rubricas ponderadas (`2.00`, `1.50`, `0.50`) vinculadas às competências SENAI.
- **`task_submissions` (`DB-025`) & `submission_evaluations` (`DB-026`)**: `96` submissões cobrindo `EVALUATED`, `SUBMITTED`, `LATE` e `PENDING`, e `201` avaliações por rubrica com média ponderada consolidada.
- **`academic_assessments` (`DB-027`) & `student_grades` (`DB-028`)**: `4` avaliações formativas (`EXAM`, `MICRO_EVALUATION`, `PROJECT`) e `60` notas parciais (incluindo `recovery_grade`).

---

## 3. Idempotência e Execução (`npm run db:seed`)

Todo o script SQL gerado em [`BancoNexa/sql/30_seed_frequencias_notas_parciais.sql`](../../BancoNexa/sql/30_seed_frequencias_notas_parciais.sql) utiliza UUIDs determinísticos para entidades sem chave natural única (`class_lessons`, `practical_tasks`, `academic_assessments`) e `ON CONFLICT (...) DO UPDATE` em **todas** as inserções.

```bash
npm.cmd run db:seed
```

Ao executar repetidamente:
- Com Docker PostgreSQL 16 ativo: aplica `20_seed_estrutura_curricular_senai.sql` e `30_seed_frequencias_notas_parciais.sql` dentro de transações `BEGIN ... COMMIT` sem duplicar nenhum registro.
- Com Docker offline: executa 2 passagens completas de validação/simulação em memória e gera arquivos SQL byte-a-byte idênticos.

---

## 4. Checklist de Verificação dos Critérios de Aceitação (`DB-030`)

- [x] **Critério 1 — Cenários reais de ótimo desempenho, entregas atrasadas e limite de faltas (25%)**: 12 alunos `100%`, 8 alunos `80%` com entregas `LATE`/`PENDING`, 5 alunos `76%` (`24%` faltas, limítrofe a `25%`) e 5 alunos `68%` em risco crítico.
- [x] **Critério 2 — Execução idempotente integrada ao comando `npm run db:seed`**: Validado em `scripts/validate-db-030.js` com 2 execuções consecutivas e 100% `ON CONFLICT ... DO UPDATE`.
- [x] **Critério 3 — Zero uso de CPFs ou nomes de alunos reais**: Todos os 30 estudantes utilizam exclusivamente nomes sintéticos (`Estudante Demo 01..30`) e domínios locais fictícios (`@aluno.nexa.local`), sem nenhum padrão de CPF ou provedor real.
- [x] **DoD — Seed executado gerando massa de dados completa para o Lote 3 e Lote 4**: Integrado ao `prisma/seed.ts` e validado em `npm run db:validate`.
