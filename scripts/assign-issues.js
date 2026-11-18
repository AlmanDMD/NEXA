/**
 * Script para atribuir ou remover atribuição de issues da NEXA por membro e por trilha (DB, BE, FE, DOC).
 * Uso:
 *   node scripts/assign-issues.js <username|NONE> [PREFIXOS_SEPARADOS_POR_VIRGULA]
 * Exemplos:
 *   node scripts/assign-issues.js NicolasPureza DB
 *   node scripts/assign-issues.js leticiaVieiratch DOC
 *   node scripts/assign-issues.js NONE BE,FE
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

async function getAllIssues(prefixes = null) {
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
          const p = match[1].toUpperCase();
          if (!prefixes || prefixes.includes(p)) {
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
  const assignees = (!username || username.toUpperCase() === 'NONE') ? [] : [username];
  const res = await fetch(`${GITHUB_API}/repos/${OWNER}/${REPO}/issues/${issueNumber}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ assignees })
  });
  if (res.ok) {
    if (assignees.length === 0) {
      console.log(`   🧹 Issue #${issueNumber} sem responsável (limpa) -> ${title}`);
    } else {
      console.log(`   ✅ Issue #${issueNumber} atribuída a @${username} -> ${title}`);
    }
    return true;
  } else {
    console.error(`   ❌ Falha na issue #${issueNumber}: HTTP ${res.status} - ${await res.text()}`);
    return false;
  }
}

async function main() {
  const targetUsername = process.argv[2] || 'NONE';
  const prefixArg = process.argv[3] || '';
  const prefixes = prefixArg
    ? prefixArg.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
    : null;

  if (targetUsername.toUpperCase() === 'NONE') {
    console.log('🧹 Modo de limpeza de atribuição (assignees: [])');
  } else {
    console.log(`🎯 Usuário selecionado para atribuição: @${targetUsername}`);
  }
  if (prefixes) {
    console.log(`📂 Filtro de Squads ativo: ${prefixes.map(p => `[${p}-*]`).join(', ')}`);
  }

  const issues = await getAllIssues(prefixes);
  console.log(`\n📦 Total de issues encontradas para atualizar: ${issues.length}\n`);

  const BATCH_SIZE = 5;
  for (let i = 0; i < issues.length; i += BATCH_SIZE) {
    const batch = issues.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(iss => setIssueAssignee(iss.number, iss.title, targetUsername)));
    await sleep(250);
  }

  console.log(`\n🎉 Todas as ${issues.length} issues foram atualizadas com sucesso!`);
}

main().catch(err => {
  console.error('❌ Erro fatal:', err);
  process.exit(1);
});
