/**
 * Script de Automação para Criação, Encadeamento (Linking) e Sincronização
 * das 170 Issues (50 DB + 50 BE + 50 FE + 20 DOC) nos 5 GitHub Projects (v2)
 * Repositório: AlmanDMD/NEXA
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { databaseCards } from './data/database.js';
import { backendCards } from './data/backend.js';
import { frontendCards } from './data/frontend.js';
import { docsCards } from './data/docs.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function loadEnv() {
  const envPath = path.resolve(__dirname, '../.env');
  if (!fs.existsSync(envPath)) {
    console.error('❌ Arquivo .env não encontrado na raiz do projeto!');
    process.exit(1);
  }
  const lines = fs.readFileSync(envPath, 'utf-8').split('\n');
  const env = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...values] = trimmed.split('=');
      env[key.trim()] = values.join('=').trim();
    }
  }
  return env;
}

const env = loadEnv();
const TOKEN = env.GITHUB_TOKEN;
const OWNER = env.GITHUB_REPO_OWNER || 'AlmanDMD';
const REPO = env.GITHUB_REPO_NAME || 'NEXA';

if (!TOKEN || TOKEN === 'coloque_seu_token_ghp_aqui') {
  console.error('❌ Erro: Configure o seu GITHUB_TOKEN no arquivo .env antes de rodar este script.');
  process.exit(1);
}

const GITHUB_API = 'https://api.github.com';
const GRAPHQL_URL = 'https://api.github.com/graphql';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'Content-Type': 'application/json',
  'User-Agent': 'NEXA-Backlog-Automation',
  'X-GitHub-Api-Version': '2022-11-28'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function graphqlRequest(query, variables = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
      'User-Agent': 'NEXA-Backlog-Automation'
    },
    body: JSON.stringify({ query, variables })
  });
  const json = await res.json();
  if (json.errors) {
    const msg = json.errors.map(e => e.message).join('; ');
    throw new Error(`GraphQL Error: ${msg}`);
  }
  return json.data;
}

const allCards = [
  ...databaseCards,
  ...backendCards,
  ...frontendCards,
  ...docsCards
];

const cardById = new Map(allCards.map(c => [c.id, c]));

// Extrai IDs de dependências (suporta listas e intervalos "DB-001 até DB-009")
function extractDependencyIds(depString) {
  if (!depString || depString === 'Nenhuma') return [];
  const result = new Set();

  const rangeRegex = /([A-Z]+)-(\d+)\s+at[ée]\s+([A-Z]+)-(\d+)/gi;
  let match;
  while ((match = rangeRegex.exec(depString)) !== null) {
    const prefix = match[1].toUpperCase();
    const start = parseInt(match[2], 10);
    const end = parseInt(match[4], 10);
    for (let n = start; n <= end; n++) {
      result.add(`${prefix}-${String(n).padStart(3, '0')}`);
    }
  }

  const idRegex = /\b(DB|BE|FE|DOC)-(\d{3})\b/g;
  while ((match = idRegex.exec(depString)) !== null) {
    result.add(`${match[1]}-${match[2]}`);
  }

  return Array.from(result);
}

// Construir grafo de dependências (Depende de / Desbloqueia)
const dependsOnMap = new Map();
const unlocksMap = new Map();

for (const card of allCards) {
  dependsOnMap.set(card.id, []);
  unlocksMap.set(card.id, []);
}

for (const card of allCards) {
  const depIds = extractDependencyIds(card.dependencies).filter(id => id !== card.id && cardById.has(id));
  dependsOnMap.set(card.id, depIds);
  for (const depId of depIds) {
    unlocksMap.get(depId).push(card.id);
  }
}

function getSprintForCard(cardId) {
  const match = cardId.match(/^([A-Z]+)-(\d+)$/);
  if (!match) return 'S1';
  const prefix = match[1];
  const num = parseInt(match[2], 10);

  if (prefix === 'DOC') {
    if (num <= 5) return 'S1';
    if (num <= 10) return 'S2';
    if (num <= 13) return 'S3';
    if (num <= 16) return 'S4';
    return 'S5';
  }

  if (num <= 10) return 'S1';
  if (num <= 20) return 'S2';
  if (num <= 30) return 'S3';
  if (num <= 40) return 'S4';
  return 'S5';
}

function getModelLabelsForCard(card) {
  const prefix = card.id.split('-')[0];
  let squadLabel = 'squad:frontend';
  if (prefix === 'BE') squadLabel = 'squad:backend';
  else if (prefix === 'DB') squadLabel = 'squad:database';
  else if (prefix === 'DOC') squadLabel = 'squad:docs';

  return [
    `priority:${card.priority || 'P0'}`,
    squadLabel,
    'release:v1.0.0',
    'type:task'
  ];
}

function getSequentialSiblings(cardId) {
  const [prefix, numStr] = cardId.split('-');
  const num = parseInt(numStr, 10);
  const maxNum = prefix === 'DOC' ? 20 : 50;

  const prevId = num > 1 ? `${prefix}-${String(num - 1).padStart(3, '0')}` : null;
  const nextId = num < maxNum ? `${prefix}-${String(num + 1).padStart(3, '0')}` : null;

  // Pares equivalentes nas outras camadas (mesmo número de card 001..050)
  const crossLayerIds = [];
  if (prefix !== 'DOC') {
    for (const otherPrefix of ['DB', 'BE', 'FE']) {
      if (otherPrefix !== prefix) {
        const candidateId = `${otherPrefix}-${numStr}`;
        if (cardById.has(candidateId)) {
          crossLayerIds.push(candidateId);
        }
      }
    }
  }

  return { prevId, nextId, crossLayerIds, maxNum };
}

function formatCardBodyWithLinks(card, issueMap) {
  const sprint = getSprintForCard(card.id);
  const { prevId, nextId, crossLayerIds, maxNum } = getSequentialSiblings(card.id);
  const upstreamIds = dependsOnMap.get(card.id) || [];
  const downstreamIds = unlocksMap.get(card.id) || [];

  const formatRef = (id, asCheckbox = false) => {
    const c = cardById.get(id);
    const info = issueMap.get(id);
    const refTag = info ? `#${info.number}` : `\`${id}\``;
    const prefixBox = asCheckbox ? '- [ ] ' : '- ';
    return `${prefixBox}${refTag} — **[${id}]** ${c ? c.title : ''} *(${c ? c.area : ''})*`;
  };

  let navSection = `#### 🧭 Sequência na Squad (Fluxo Contínuo até o Card ${maxNum}/${maxNum})\n`;
  if (prevId) {
    const prevInfo = issueMap.get(prevId);
    const prevCard = cardById.get(prevId);
    navSection += `- **⬅️ Card Anterior na Squad**: ${prevInfo ? `#${prevInfo.number}` : ''} (**[${prevId}]** ${prevCard?.title || ''})\n`;
  } else {
    navSection += `- **⬅️ Card Anterior na Squad**: *Início da Trilha (Card 001)*\n`;
  }
  navSection += `- **📍 Card Atual**: \`${card.id}\` — **Sprint \`${sprint}\`**\n`;
  if (nextId) {
    const nextInfo = issueMap.get(nextId);
    const nextCard = cardById.get(nextId);
    navSection += `- **➡️ Próximo Card na Squad**: ${nextInfo ? `#${nextInfo.number}` : ''} (**[${nextId}]** ${nextCard?.title || ''})\n`;
  } else {
    navSection += `- **🏁 Próximo Card na Squad**: *Marco Final da Squad (${maxNum}/${maxNum} Concluído!)*\n`;
  }

  let upstreamSection = `#### 🔒 Pré-requisitos e Dependências Diretas (Depende de)\n`;
  if (upstreamIds.length > 0) {
    upstreamSection += upstreamIds.map(id => formatRef(id, true)).join('\n');
  } else {
    upstreamSection += `- *Nenhuma dependência bloqueante — pode ser iniciado imediatamente.*`;
  }

  let downstreamSection = `#### 🔓 Próximas Tarefas Desbloqueadas por este Card (Desbloqueia)\n`;
  if (downstreamIds.length > 0) {
    downstreamSection += downstreamIds.map(id => formatRef(id, false)).join('\n');
  } else {
    downstreamSection += `- *Entrega de fechamento de trilha / validação final do sistema.*`;
  }

  let crossLayerSection = '';
  if (crossLayerIds.length > 0) {
    crossLayerSection = `\n#### 🔄 Sincronia Horizontal entre Squads (Mesma Onda)\n` +
      crossLayerIds.map(id => formatRef(id, false)).join('\n') + '\n';
  }

  return `### 📋 Identificação do Item
- **ID**: \`${card.id}\`
- **Título**: ${card.title}
- **Área**: **${card.area}**
- **Epic**: ${card.epic}
- **Sprint / Lote**: \`${sprint}\`
- **Prioridade**: **${card.priority}** | **Estimativa**: \`${card.estimate}\`
- **Tipo**: \`${card.type}\`

---

### 🎯 Objetivo
${card.objective}

---

### 📝 Descrição do Trabalho
${card.description}

---

### 👤 História de Usuário
> ${card.user_story}

---

### ✅ Critérios de Aceitação
${card.acceptance_criteria}

---

### 🔗 Encadeamento e Rastreabilidade Completa (Links Diretos)

${navSection}
${crossLayerSection}
${upstreamSection}

${downstreamSection}

---

### 🏁 Definição de Pronto (Definition of Done - DoD)
- [ ] ${card.dod}
- [ ] Código/documento em conformidade com o padrão do projeto
- [ ] Testes unitários/validações executados com sucesso
- [ ] Integração validada com os cards dependentes
- [ ] Pull Request revisado e aprovado

---

### 🛠️ Observações Técnicas & Regras de Negócio
${card.technical_notes}
`;
}

async function getExistingIssuesMap() {
  console.log('🔍 Consultando issues existentes no repositório...');
  const issueMap = new Map();
  let page = 1;

  while (true) {
    const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues?state=all&per_page=100&page=${page}`, {
      headers
    });
    if (!res.ok) break;
    const issues = await res.json();
    if (!Array.isArray(issues) || issues.length === 0) break;

    for (const issue of issues) {
      const match = issue.title.match(/^\[([A-Z]+-\d+)\]/);
      if (match) {
        issueMap.set(match[1], {
          number: issue.number,
          node_id: issue.node_id,
          title: issue.title,
          state: issue.state
        });
      }
    }
    page++;
  }

  console.log(`ℹ️  Issues mapeadas atualmente no repositório: ${issueMap.size}`);
  return issueMap;
}

async function createMissingIssue(card, issueMap) {
  const title = `[${card.id}] ${card.title}`;
  const body = formatCardBodyWithLinks(card, issueMap);
  const labels = getModelLabelsForCard(card);

  const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ title, body, labels })
  });

  if (res.status === 201) {
    const data = await res.json();
    issueMap.set(card.id, {
      number: data.number,
      node_id: data.node_id,
      title: data.title,
      state: data.state
    });
    console.log(`   ✅ Criada #${data.number} -> [${card.id}] ${card.title}`);
    return data;
  } else {
    const errText = await res.text();
    console.error(`   ❌ Erro ao criar [${card.id}] (HTTP ${res.status}):`, errText);
    return null;
  }
}

async function updateIssueBodyWithLinks(card, issueMap) {
  const info = issueMap.get(card.id);
  if (!info) return;

  const body = formatCardBodyWithLinks(card, issueMap);
  const labels = getModelLabelsForCard(card);

  const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues/${info.number}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ body, labels })
  });

  if (res.ok) {
    console.log(`   🔗 Links atualizados em #${info.number} [${card.id}]`);
  } else {
    console.warn(`   ⚠️ Falha ao atualizar corpo de #${info.number} [${card.id}]: ${res.status}`);
  }
}

async function main() {
  console.log('======================================================================');
  console.log('🚀 CRIAÇÃO E ENCADEAMENTO COMPLETO DAS 170 ISSUES DA NEXA');
  console.log('======================================================================\n');

  const issueMap = await getExistingIssuesMap();

  const missingCards = allCards.filter(c => !issueMap.has(c.id));
  console.log(`\n📦 Total planejado: ${allCards.length} cards (50 DB + 50 BE + 50 FE + 20 DOC)`);
  console.log(`   - Já existentes no GitHub: ${issueMap.size}`);
  console.log(`   - Novas issues a criar agora: ${missingCards.length}\n`);

  // Fase 1: Criar todas as issues faltantes (na ordem DB -> BE -> FE -> DOC)
  for (let i = 0; i < missingCards.length; i++) {
    const card = missingCards[i];
    process.stdout.write(`[${i + 1}/${missingCards.length}] `);
    await createMissingIssue(card, issueMap);
    await sleep(750); // Respeitar secondary rate limit de criação do GitHub
  }

  // Fase 2: Agora que todas as 170 issues possuem #number, atualizar o corpo de todas para que
  // todos os links (Anterior, Próximo, Depende de, Desbloqueia) tenham #number clicável!
  console.log('\n🔗 Fase 2: Sincronizando referências cruzadas (#number) em todas as 170 issues...');
  for (let i = 0; i < allCards.length; i += 5) {
    const batch = allCards.slice(i, i + 5);
    await Promise.all(batch.map(card => updateIssueBodyWithLinks(card, issueMap)));
    await sleep(300);
  }

  console.log('\n🎉 Todas as 170 issues foram criadas e interligadas com sucesso!');
}

main().catch(err => {
  console.error('❌ Erro fatal:', err);
  process.exit(1);
});
