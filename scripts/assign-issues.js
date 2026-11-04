/**
 * Script para atribuir issues da NEXA por membro e/ou por trilha (DB, BE, FE, DOC).
 * Uso:
 *   node scripts/assign-issues.js <username> [PREFIXO_OPCIONAL]
 * Exemplo:
 *   node scripts/assign-issues.js leticiaVieiratch DOC
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

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
  'User-Agent': 'NEXA-Assignee-Automation',
  'X-GitHub-Api-Version': '2022-11-28'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getAllIssues(prefixFilter = null) {
  const all = [];
  let page = 1;
  while (true) {
    const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues?state=all&per_page=100&page=${page}`, {
      headers
    });
    if (!res.ok) break;
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) break;
    for (const item of data) {
      if (!item.pull_request) {
        const match = item.title.match(/^\[([A-Z]+)-\d+\]/);
        if (match) {
          if (!prefixFilter || match[1].toUpperCase() === prefixFilter.toUpperCase()) {
            all.push(item);
          }
        }
      }
    }
    page++;
  }
  return all.sort((a, b) => a.number - b.number);
}

async function setIssueAssignee(issueNumber, title, username) {
  const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues/${issueNumber}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ assignees: [username] })
  });
  if (res.ok) {
    console.log(`   ✅ Issue #${issueNumber} atribuída a @${username} -> ${title}`);
    return true;
  } else {
    console.error(`   ❌ Falha na issue #${issueNumber}: HTTP ${res.status} - ${await res.text()}`);
    return false;
  }
}

async function main() {
  const targetUsername = process.argv[2] || 'leticiaVieiratch';
  const prefixFilter = process.argv[3] || null;

  console.log(`🎯 Usuário selecionado para atribuição: @${targetUsername}`);
  if (prefixFilter) {
    console.log(`📂 Filtro de Squad/Trilha ativo: [${prefixFilter}-*]`);
  }

  const issues = await getAllIssues(prefixFilter);
  console.log(`\n📦 Total de issues encontradas para atribuir: ${issues.length}\n`);

  const BATCH_SIZE = 5;
  for (let i = 0; i < issues.length; i += BATCH_SIZE) {
    const batch = issues.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(iss => setIssueAssignee(iss.number, iss.title, targetUsername)));
    await sleep(250);
  }

  console.log(`\n🎉 Todas as ${issues.length} issues foram atribuídas com sucesso para @${targetUsername}!`);
}

main().catch(err => {
  console.error('❌ Erro fatal:', err);
  process.exit(1);
});
