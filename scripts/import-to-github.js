/**
 * Script de Automação para Criação de Issues e Labels no GitHub
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
const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'User-Agent': 'NEXA-Backlog-Automation',
  'X-GitHub-Api-Version': '2022-11-28'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function formatCardBody(card) {
  return `### 📋 Identificação do Item
- **ID**: \`${card.id}\`
- **Título**: ${card.title}
- **Área**: **${card.area}**
- **Epic**: ${card.epic}
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

### 🔗 Dependências
- **Pré-requisitos**: \`${card.dependencies}\`

---

### 🏁 Definição de Pronto (Definition of Done - DoD)
- [ ] ${card.dod}
- [ ] Código/documento em conformidade com o padrão do projeto
- [ ] Testes unitários/validações executados com sucesso
- [ ] Pull Request revisado e aprovado

---

### 🛠️ Observações Técnicas & Regras de Negócio
${card.technical_notes}
`;
}

// Obter issues existentes para não duplicar
async function getExistingIssues() {
  console.log('🔍 Verificando issues já existentes no repositório...');
  const existing = new Set();
  let page = 1;

  while (true) {
    try {
      const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues?state=all&per_page=100&page=${page}`, {
        headers
      });
      if (!res.ok) break;
      const issues = await res.json();
      if (!Array.isArray(issues) || issues.length === 0) break;

      for (const issue of issues) {
        // Se o título começar com [ID], guardamos o ID
        const match = issue.title.match(/^\[([A-Z]+-\d+)\]/);
        if (match) {
          existing.add(match[1]);
        }
      }
      page++;
    } catch (err) {
      console.warn('Aviso ao consultar issues existentes:', err.message);
      break;
    }
  }

  console.log(`ℹ️  Total de issues pré-existentes identificadas: ${existing.size}`);
  return existing;
}

async function createIssue(card) {
  const body = formatCardBody(card);
  const title = `[${card.id}] ${card.title}`;

  try {
    const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title,
        body,
        labels: card.labels
      })
    });

    if (res.status === 201) {
      const data = await res.json();
      console.log(`✅ Issue criada: #${data.number} -> [${card.id}] ${card.title}`);
      return data;
    } else {
      const err = await res.text();
      console.error(`❌ Falha ao criar issue [${card.id}]:`, res.status, err);
      return null;
    }
  } catch (error) {
    console.error(`❌ Erro de rede ao criar [${card.id}]:`, error.message);
    return null;
  }
}

async function main() {
  console.log(`🚀 Iniciando criação das Issues para o repositório: ${OWNER}/${REPO}\n`);

  const existing = await getExistingIssues();

  const allCards = [
    ...databaseCards,
    ...backendCards,
    ...frontendCards,
    ...docsCards
  ];

  console.log(`\n📦 Lote preparado: ${allCards.length} cards no total.`);
  console.log(`   - Banco de Dados: ${databaseCards.length} cards (DB-001 a DB-020)`);
  console.log(`   - Back-end: ${backendCards.length} cards (BE-001 a BE-020)`);
  console.log(`   - Front-end: ${frontendCards.length} cards (FE-001 a FE-020)`);
  console.log(`   - Documentação: ${docsCards.length} cards (DOC-001 a DOC-010)\n`);

  let createdCount = 0;
  let skippedCount = 0;

  for (let i = 0; i < allCards.length; i++) {
    const card = allCards[i];
    if (existing.has(card.id)) {
      console.log(`⏭️  Pulando [${card.id}] (já existe no repositório).`);
      skippedCount++;
      continue;
    }

    process.stdout.write(`[${i + 1}/${allCards.length}] Criando `);
    const result = await createIssue(card);
    if (result) {
      createdCount++;
    }
    // Aguardar 800ms entre as requisições para evitar rate limit do GitHub
    await sleep(800);
  }

  console.log(`\n🎉 Processamento concluído!`);
  console.log(`   ✅ Issues novas criadas: ${createdCount}`);
  console.log(`   ⏭️  Issues puladas (já existiam): ${skippedCount}`);
  console.log(`   📊 Total no repositório: ${createdCount + skippedCount}`);
}

main();
