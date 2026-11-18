import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { databaseCards } from './data/database.js';
import { backendCards } from './data/backend.js';
import { frontendCards } from './data/frontend.js';
import { docsCards } from './data/docs.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const docsDir = path.resolve(__dirname, '../docs/backlog');

function getLotLabel(cardId) {
  const [prefix, numStr] = cardId.split('-');
  const num = parseInt(numStr, 10);
  if (prefix === 'DOC') {
    if (num <= 5) return 'Lote 1 (S1)';
    if (num <= 10) return 'Lote 2 (S2)';
    if (num <= 13) return 'Lote 3 (S3)';
    if (num <= 16) return 'Lote 4 (S4)';
    return 'Lote 5 (S5)';
  }
  if (num <= 10) return 'Lote 1 (S1)';
  if (num <= 20) return 'Lote 2 (S2)';
  if (num <= 30) return 'Lote 3 (S3)';
  if (num <= 40) return 'Lote 4 (S4)';
  return 'Lote 5 (S5)';
}

function renderMarkdownDoc({ title, subtitle, intro, lotsSummary, cards }) {
  const tableRows = cards.map(c => {
    const lot = getLotLabel(c.id);
    return `| \`${c.id}\` | ${c.title} | ${c.epic.split(':')[0]} | ${c.priority} | ${c.estimate} | ${lot} | \`${c.dependencies}\` |`;
  }).join('\n');

  const details = cards.map((c, idx) => {
    const prev = idx > 0 ? cards[idx - 1].id : 'Início da Trilha';
    const next = idx < cards.length - 1 ? cards[idx + 1].id : 'Marco Final Concluído (100%)';
    return `### [${c.id}] ${c.title}
- **ID**: \`${c.id}\`
- **Título**: ${c.title}
- **Área**: ${c.area}
- **Epic**: ${c.epic}
- **Lote / Sprint**: ${getLotLabel(c.id)}
- **Sequência na Squad**: ⬅️ Anterior: \`${prev}\` | ➡️ Próximo: \`${next}\`
- **Dependências Diretas**: \`${c.dependencies}\`
- **Prioridade**: ${c.priority} | **Estimativa**: ${c.estimate} | **Tipo**: ${c.type}
- **Objetivo**: ${c.objective}
- **Descrição**: ${c.description}
- **História de Usuário**: ${c.user_story}
- **Critérios de Aceitação**:
${c.acceptance_criteria}
- **Definição de Pronto (DoD)**: ${c.dod}
- **Observações Técnicas**: ${c.technical_notes}
`;
  }).join('\n---\n\n');

  return `# ${title}
## ${subtitle}

${intro}

---

### Resumo dos Lotes / Sprints de Implementação
${lotsSummary}

---

### Tabela Geral Encadeada (${cards.length} Cards)

| ID | Título | Epic | Prioridade | Estimativa | Lote / Sprint | Dependências |
|---|---|---|---|---|---|---|
${tableRows}

---

## Detalhamento Completo e Encadeado dos ${cards.length} Cards

${details}
`;
}

const files = [
  {
    filename: '01-banco-de-dados.md',
    title: '🗄️ Backlog de Banco de Dados (Database) — Projeto NEXA',
    subtitle: '50 Cards Exclusivos e Encadeados de Engenharia de Dados (`DB-001` a `DB-050`)',
    intro: 'Este documento contém o planejamento completo e 100% interligado da camada de persistência de dados do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**. Ao concluir o card `DB-050`, toda a infraestrutura de dados, views analíticas, segurança LGPD e governança está finalizada.',
    lotsSummary: `- **Lote 1 / Sprint 1 (DB-001 a DB-010)**: Fundação, Modelagem Conceitual/Lógica, PostgreSQL 16, Prisma ORM e Tabelas de Identidade/Segurança (RBAC).
- **Lote 2 / Sprint 2 (DB-011 a DB-020)**: Estrutura Acadêmica SENAI (Cursos, Turmas, Disciplinas, Módulos Práticos, Competências e Matrículas).
- **Lote 3 / Sprint 3 (DB-021 a DB-030)**: Diário de Classe, Frequência, Atividades Práticas de Oficina, Rubricas e Notas Formativas.
- **Lote 4 / Sprint 4 (DB-031 a DB-040)**: Autoavaliações, Evidências de Habilidades, Motor de Diagnósticos Explicáveis e Views Analíticas 360°.
- **Lote 5 / Sprint 5 (DB-041 a DB-050)**: Comunicação Oficial, Canal de Ajuda Confidencial, Notas Pedagógicas Criptografadas, Gamificação, Índices, Backup e Fechamento LGPD.`,
    cards: databaseCards
  },
  {
    filename: '02-back-end.md',
    title: '⚙️ Backlog de Back-end (API & Serviços em Python / FastAPI) — Projeto NEXA',
    subtitle: '50 Cards Exclusivos e Encadeados de Engenharia de Back-end em Python (`BE-001` a `BE-050`)',
    intro: 'Este documento contém o planejamento completo e 100% interligado da API RESTful assíncrona desenvolvida em **Python 3.12+ com FastAPI, Pydantic v2 e SQLAlchemy 2.0** do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**, conectando cada serviço ao PostgreSQL (`DB-001`..`DB-050`) e servindo a interface Front-end (`FE-001`..`FE-050`).',
    lotsSummary: `- **Lote 1 / Sprint 1 (BE-001 a BE-010)**: Setup Python 3.12+/FastAPI/Uvicorn, Arquitetura em Camadas, Schemas Pydantic v2, Autenticação JWT (PyJWT), Injeção de Dependências (Depends) e RBAC.
- **Lote 2 / Sprint 2 (BE-011 a BE-020)**: APIs de Gestão Acadêmica SENAI (Cursos, Turmas, Disciplinas, Módulos, Matriz de Competências e Matrículas em Lote com SQLAlchemy assíncrono).
- **Lote 3 / Sprint 3 (BE-021 a BE-030)**: APIs de Diário de Classe, Chamada em Lote, Tarefas Práticas de Oficina, Rubricas e Motor de Cálculo de Médias Ponderadas.
- **Lote 4 / Sprint 4 (BE-031 a BE-040)**: APIs de Autoavaliação, Cruzamento Percepção vs. Evidência Prática, Motor Explicável de Alertas Precoces e Endpoints de Dashboard 360°.
- **Lote 5 / Sprint 5 (BE-041 a BE-050)**: Mural de Avisos, Canal Confidencial de Ajuda, Criptografia AES-256 (Cryptography) de Notas Pedagógicas, Gamificação, Exportação CSV/PDF e Swagger/OpenAPI Nativo.`,
    cards: backendCards
  },
  {
    filename: '03-front-end.md',
    title: '💻 Backlog de Front-end (Interface & UX) — Projeto NEXA',
    subtitle: '50 Cards Exclusivos e Encadeados de Engenharia de Front-end (`FE-001` a `FE-050`)',
    intro: 'Este documento contém o planejamento completo e 100% interligado da interface React + TypeScript + Tailwind CSS do **Sistema Inteligente de Monitoramento do Desempenho Acadêmico — SENAI (NEXA)**, integrado aos endpoints de Back-end (`BE-001`..`BE-050`).',
    lotsSummary: `- **Lote 1 / Sprint 1 (FE-001 a FE-010)**: Setup Vite + React + TS, Design System Industrial SENAI, AppShell Responsivo, AuthContext e Fluxo de Login/RBAC.
- **Lote 2 / Sprint 2 (FE-011 a FE-020)**: Telas Administrativas de Cursos, Turmas, Módulos Práticos, Matriz Visual de Competências e Matrícula com Importação CSV.
- **Lote 3 / Sprint 3 (FE-021 a FE-030)**: Diário de Classe Digital, Chamada Rápida, Criação de Tarefas de Oficina, Avaliação por Rubrica Interativa e Planilha de Notas.
- **Lote 4 / Sprint 4 (FE-031 a FE-040)**: Wizard de Autoavaliação do Aluno, Gráfico Radar Comparativo, Dashboard Híbrido do Professor, Alertas Explicáveis e Visão 360°.
- **Lote 5 / Sprint 5 (FE-041 a FE-050)**: Mural da Turma, Canal Seguro "Pedir Ajuda", Diário Confidencial Docente, Galeria de Conquistas, Exportação de Relatórios, Acessibilidade WCAG AA e Testes E2E Playwright.`,
    cards: frontendCards
  },
  {
    filename: '04-documentacao.md',
    title: '📚 Backlog de Documentação Técnica, Acadêmica e Governança — Projeto NEXA',
    subtitle: '20 Cards Estruturados e Encadeados de Documentação (`DOC-001` a `DOC-020`)',
    intro: 'Este documento reúne todos os 20 entregáveis de documentação de engenharia de software, arquitetura, banco de dados, segurança LGPD, qualidade e apresentação para a banca avaliadora SENAI.',
    lotsSummary: `- **Lote 1 / Sprint 1 (DOC-001 a DOC-005)**: Escopo Executivo, Requisitos RF/RNF, Personas SENAI, Regras de Negócio e Arquitetura C4 Model.
- **Lote 2 / Sprint 2 (DOC-006 a DOC-010)**: Guia de Estilo UI/UX, Padrões de Código/GitFlow, DER Oficial, Dicionário de Dados e Guia de Setup Local.
- **Lote 3 / Sprint 3 (DOC-011 a DOC-013)**: Catálogo OpenAPI/Swagger, Matriz RBAC + Relatório LGPD e Guia Pedagógico de Rubricas SENAI.
- **Lote 4 / Sprint 4 (DOC-014 a DOC-016)**: Especificação da Heurística de Risco Explicável, Plano de Testes Integrados e Manual de Operação DevOps.
- **Lote 5 / Sprint 5 (DOC-017 a DOC-020)**: Manual do Professor/Coordenador, Guia do Estudante, Relatório de Auditoria Final e Roteiro de Pitch/Defesa para a Banca.`,
    cards: docsCards
  }
];

for (const f of files) {
  const outPath = path.join(docsDir, f.filename);
  fs.writeFileSync(outPath, renderMarkdownDoc(f), 'utf-8');
  console.log(`✅ Atualizado: docs/backlog/${f.filename} (${f.cards.length} cards)`);
}

