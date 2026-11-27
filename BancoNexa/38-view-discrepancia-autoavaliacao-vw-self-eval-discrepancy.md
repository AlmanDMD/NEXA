# ⚖️ [DB-038] View de Discrepância: Autoavaliação vs. Avaliação do Professor (`vw_self_eval_discrepancy`) — Projeto NEXA

> **ID do Card**: `DB-038` | **Epic**: `EPIC-07: Autoavaliação & Motor de Diagnóstico Explicável` | **Sprint / Lote**: `Lote 4 (S4)`  
> **Prioridade**: `P1` | **Estimativa**: `5 SP` | **Tipo**: `Feature` | **Status**: `Concluído`  
> **Arquivos Principais**: [`prisma/migrations/20261126050000_create_vw_self_eval_discrepancy/migration.sql`](../../prisma/migrations/20261126050000_create_vw_self_eval_discrepancy/migration.sql), [`BancoNexa/sql/38_view_vw_self_eval_discrepancy.sql`](../../BancoNexa/sql/38_view_vw_self_eval_discrepancy.sql)  
> **Rastreabilidade**: ⬅️ Anterior: [`DB-037`](./37-view-frequencia-evasao-vw-module-attendance-risk.md) | ➡️ Próximo: `DB-039` | 🔒 Depende de: `DB-032`, `DB-033`, `DB-035` | 🔓 Desbloqueia: `BE-037`, `BE-038`, `FE-038`, `FE-042`

---

## 1. Objetivo e Classificação Explicável

A view SQL **`vw_self_eval_discrepancy`** cruza `student_self_assessments` (`DB-032`) com a média de `skill_evidences` (`DB-033`) por `(student_id, competency_id)`, retornando lado a lado `perceived_level`, `avg_verified_level`, `evidence_count` e `discrepancy_delta = perceived_level - avg_verified_level`.

| Regra Determinística | `diagnostic_classification` | `requires_pedagogical_review` | Significado Pedagógico |
|---|---|:---:|---|
| `evidence_count = 0` | `INSUFFICIENT_EVIDENCE` | `TRUE` | Sem evidência docente suficiente para validar autopercepção |
| `discrepancy_delta >= 1.50` | `OVERCONFIDENCE_RISK` | `TRUE` | Superestimação — risco técnico/segurança em oficina |
| `discrepancy_delta <= -1.50` | `UNDERCONFIDENCE_SUPPORT` | `TRUE` | Subestimação — insegurança apesar de bom desempenho prático |
| `ABS(discrepancy_delta) < 1.50` | `ALIGNED` | `FALSE` | Percepção alinhada com as evidências docentes |

---

## 2. Checklist de Verificação (`DB-038`)

- [x] **Critério 1 — Retorna nível autoavaliado, nível verificado, contagem de evidências e delta**: Expostos lado a lado por `(student_id, competency_id)`.
- [x] **Critério 2 — Destaca superestimação e subestimação (>= 1.50 pontos)**: Classificação via `diagnostic_type_enum` + flag `requires_pedagogical_review`.
- [x] **Critério 3 — Otimizada para radar (`FE-038`) e comparativo (`FE-042`)**: Inclui metadados de competência (`code`, `title`, `category`) e módulo, validada em `scripts/validate-db-038.js`.
