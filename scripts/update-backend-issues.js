/**
 * Script para atualizar os 50 cards de Back-end (BE-001 a BE-050) no GitHub
 * com as novas descrições, títulos e tecnologias adaptadas para Python / FastAPI.
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
    console.error('❌ Arquivo .env não encontrado!');
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
const GITHUB_API = 'https://api.github.com';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'Content-Type': 'application/json',
  'User-Agent': 'NEXA-Backend-Python-Migration',
  'X-GitHub-Api-Version': '2022-11-28'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const allCards = [
  ...databaseCards,
  ...backendCards,
  ...frontendCards,
  ...docsCards
];
const cardById = new Map(allCards.map(c => [c.id, c]));

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

function getSequentialSiblings(cardId) {
  const [prefix, numStr] = cardId.split('-');
  const num = parseInt(numStr, 10);
  const maxNum = prefix === 'DOC' ? 20 : 50;

  const prevId = num > 1 ? `${prefix}-${String(num - 1).padStart(3, '0')}` : null;
  const nextId = num < maxNum ? `${prefix}-${String(num + 1).padStart(3, '0')}` : null;

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
- **Stack**: **Python 3.12+ (FastAPI / Pydantic v2 / SQLAlchemy 2.0 / Pytest)**
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
- [ ] Código/documento em conformidade com as PEPs (PEP 8, Type Hints) e padrão do projeto
- [ ] Testes unitários/validações com pytest executados com sucesso
- [ ] Integração validada com os endpoints do FastAPI e modelos do SQLAlchemy
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
          title: issue.title
        });
      }
    }
    page++;
  }
  return issueMap;
}

async function updateBackendIssue(card, issueMap) {
  const info = issueMap.get(card.id);
  if (!info) {
    console.warn(`⚠️ Issue para ${card.id} não encontrada no GitHub.`);
    return;
  }

  const title = `[${card.id}] ${card.title}`;
  const body = formatCardBodyWithLinks(card, issueMap);

  const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues/${info.number}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ title, body })
  });

  if (res.ok) {
    console.log(`   ✅ #${info.number} atualizada para Python -> ${title}`);
  } else {
    console.error(`   ❌ Erro ao atualizar #${info.number} (${card.id}): HTTP ${res.status}`);
  }
}

async function main() {
  console.log('======================================================================');
  console.log('🐍 ATUALIZAÇÃO DOS 50 CARDS DE BACKEND PARA PYTHON / FASTAPI');
  console.log('======================================================================\n');

  const issueMap = await getExistingIssuesMap();
  console.log(`📦 Issues mapeadas: ${issueMap.size}`);
  console.log(`🎯 Atualizando ${backendCards.length} issues de Backend (BE-001 a BE-050)...\n`);

  const BATCH_SIZE = 5;
  for (let i = 0; i < backendCards.length; i += BATCH_SIZE) {
    const batch = backendCards.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(card => updateBackendIssue(card, issueMap)));
    await sleep(350);
  }

  console.log('\n🎉 Todas as 50 issues de Backend foram migradas para Python com sucesso!');
}

main().catch(err => {
  console.error('❌ Erro fatal:', err);
  process.exit(1);
});

