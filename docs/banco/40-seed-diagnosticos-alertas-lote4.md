# 🌱 [DB-040] Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards — Projeto NEXA

> **ID do Card**: `DB-040` | **Epic**: `EPIC-05: Dashboard Híbrido do Professor & Visão 360°` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P1` | **Estimativa**: `3 SP` | **Tipo**: `Feature` | **Status**: `Concluído (Lote 4 Finalizado)`  
> **Arquivos Principais**: [`prisma/seed.ts`](../../prisma/seed.ts), [`BancoNexa/sql/40_seed_diagnosticos_alertas_lote4.sql`](../../BancoNexa/sql/40_seed_diagnosticos_alertas_lote4.sql), [`package.json`](../../package.json)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-039`](./39-tabela-historico-linha-tempo-student-milestone-history.md) | ➡️ Próximo: `DB-041` | 🔒 Depende de: `DB-030` a `DB-035`, `DB-039` | 🔓 Desbloqueia: Demonstração e homologação dos dashboards `BE-031..039` e `FE-031..042`

---

## 1. Objetivo e Comando de Execução

O card **`DB-040`** conclui o **Lote 4 (S4)** atualizando [`prisma/seed.ts`](../../prisma/seed.ts) e sincronizando [`BancoNexa/sql/40_seed_diagnosticos_alertas_lote4.sql`](../../BancoNexa/sql/40_seed_diagnosticos_alertas_lote4.sql) com dados 100% anônimos, coerentes e idempotentes (UPSERT) para homologação imediata dos dashboards do professor, ficha 360° e portal do aluno:

```bash
npm run db:seed
```

---

## 2. Inventário de Dados Populados no Lote 4 (`DB-040`)

| Entidade (`Tabela PostgreSQL`) | Quantidade | Cobertura Pedagógica |
|---|:---:|---|
| `self_assessment_forms` | `4` | Ciclos ativos de **Metrologia** e **Tornearia Cilíndrica** nas turmas `MEC-2026-1` e `MEC-2026-2` |
| `student_self_assessments` | `20` | Respostas realistas na escala 1..5 com notas de dificuldade dentro da janela aberta |
| `skill_evidences` | `16` | Evidências certificadas por docentes vinculadas a `task_submissions` e `academic_assessments` do Lote 3 |
| `academic_alerts` | `8` | Cobertura completa de `LOW`, `MODERATE`, `HIGH`, `CRITICAL` e categorias `ATTENDANCE`, `GRADE_DROP`, `PENDING_TASKS`, `SELF_EVAL_GAP` |
| `explainable_diagnostics` | `10` | Casos reais de divergência (`OVERCONFIDENCE_RISK` e `UNDERCONFIDENCE_SUPPORT`) e `ALIGNED` em **Metrologia** e **Tornearia** |
| `student_milestone_history` | `8` | Marcos positivos `MODULE_COMPLETED`, `SKILL_LEVEL_UP`, `PERFECT_ATTENDANCE` e `RECOVERY_ACHIEVED` |

---

## 3. Checklist de Verificação (`DB-040`)

- [x] **Critério 1 — Todos os gráficos e cards dos Lotes 4 e 5 renderizam dados coerentes após `npm run db:seed`**: 4 formulários, 20 autoavaliações, 16 evidências, 8 alertas, 10 diagnósticos e 8 marcos.
- [x] **Critério 2 — Exemplos reais de divergência em Metrologia e Tornearia**: Superestimação e subestimação modeladas em `COMP-MET-01`, `COMP-USI-01`, `COMP-USI-02` e `COMP-SEG-02`.
- [x] **Critério 3 — Idempotente e sem erros de chave duplicada**: Todas as instruções usam `ON CONFLICT ... DO UPDATE`, validadas em 2 execuções consecutivas.
- [x] **DoD — Seed completo rodando em < 5 segundos**: Validado com medição real em `scripts/validate-db-040.js`.
