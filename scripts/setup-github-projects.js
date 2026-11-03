/**
 * Script de Automação para Estruturação dos 5 GitHub Projects (v2) da NEXA
 * no formato idêntico ao template "Plataforma Digital — 2026.2" (UniSENAI-Sorocaba)
 *
 * Popula as 70 issues do repositório AlmanDMD/NEXA nos projetos:
 *  - NEXA – Frontend (#15) -> recebe FE-001 a FE-020
 *  - NEXA – Backend (#16) -> recebe BE-001 a BE-020
 *  - NEXA – Banco de Dados (#17) -> recebe DB-001 a DB-020
 *  - NEXA – Documentação (#18) -> recebe DOC-001 a DOC-010
 *  - NEXA – Geral (#19) -> recebe todas as 70 issues consolidadas
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
const TEMPLATE_PROJECT_ID = 'PVT_kwDOEy7Fts4BjGVB';

const GRAPHQL_URL = 'https://api.github.com/graphql';
const REST_URL = 'https://api.github.com';

const restHeaders = {
  'Authorization': `Bearer ${TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'User-Agent': 'NEXA-Projects-Automation',
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
      'User-Agent': 'NEXA-Projects-Automation'
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

const allLocalCards = [...databaseCards, ...backendCards, ...frontendCards, ...docsCards];
const cardById = new Map(allLocalCards.map(c => [c.id, c]));

const PROJECTS_CONFIG = [
  { key: 'frontend', title: 'NEXA – Frontend', squadOption: 'Frontend' },
  { key: 'backend', title: 'NEXA – Backend', squadOption: 'Backend' },
  { key: 'database', title: 'NEXA – Banco de Dados', squadOption: 'Database' },
  { key: 'docs', title: 'NEXA – Documentação', squadOption: 'Product' },
  { key: 'general', title: 'NEXA – Geral', squadOption: null }
];

async function getOwnerAndRepoInfo() {
  const query = `
    query($owner: String!, $repo: String!) {
      repositoryOwner(login: $owner) {
        id
        login
        ... on Organization {
          projectsV2(first: 50) {
            nodes {
              id
              number
              title
              closed
              url
              views(first: 5) {
                nodes {
                  name
                  layout
                }
              }
            }
          }
        }
      }
      repository(owner: $owner, name: $repo) {
        id
        name
      }
    }
  `;
  const data = await graphqlRequest(query, { owner: OWNER, repo: REPO });
  return {
    ownerId: data.repositoryOwner.id,
    existingProjects: data.repositoryOwner.projectsV2.nodes || [],
    repoId: data.repository.id
  };
}

async function copyFromTemplateProject(ownerId, title) {
  console.log(`   📋 Clonando estrutura de Board e Views do modelo para "${title}"...`);
  const mutation = `
    mutation($projectId: ID!, $ownerId: ID!, $title: String!) {
      copyProjectV2(input: {
        projectId: $projectId,
        ownerId: $ownerId,
        title: $title,
        includeDraftIssues: false
      }) {
        projectV2 {
          id
          number
          title
          url
        }
      }
    }
  `;
  const data = await graphqlRequest(mutation, {
    projectId: TEMPLATE_PROJECT_ID,
    ownerId,
    title
  });
  return data.copyProjectV2.projectV2;
}

async function getProjectFieldsMap(projectId) {
  const query = `
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 40) {
            nodes {
              __typename
              ... on ProjectV2Field {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                dataType
                options {
                  id
                  name
                  color
                }
              }
            }
          }
        }
      }
    }
  `;
  const data = await graphqlRequest(query, { projectId });
  const nodes = data.node?.fields?.nodes || [];
  const map = {};
  for (const f of nodes) {
    if (f && f.name) {
      map[f.name] = f;
    }
  }
  return map;
}

async function fetchAllRepoIssues() {
  const issues = [];
  let hasNextPage = true;
  let endCursor = null;

  const query = `
    query($owner: String!, $repo: String!, $after: String) {
      repository(owner: $owner, name: $repo) {
        issues(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            number
            title
            state
          }
        }
      }
    }
  `;

  while (hasNextPage) {
    const data = await graphqlRequest(query, { owner: OWNER, repo: REPO, after: endCursor });
    const conn = data.repository.issues;
    issues.push(...conn.nodes);
    hasNextPage = conn.pageInfo.hasNextPage;
    endCursor = conn.pageInfo.endCursor;
  }
  return issues;
}

function parseIssueMetadata(issue) {
  const match = issue.title.match(/^\[([A-Z]+)-(\d+)\]/);
  if (!match) return null;

  const prefix = match[1];
  const num = parseInt(match[2], 10);
  const cardId = `${prefix}-${match[2]}`;
  const localCard = cardById.get(cardId);

  let sectorKey = 'frontend';
  let squadLabel = 'squad:frontend';
  let squadOption = 'Frontend';

  if (prefix === 'BE') {
    sectorKey = 'backend';
    squadLabel = 'squad:backend';
    squadOption = 'Backend';
  } else if (prefix === 'DB') {
    sectorKey = 'database';
    squadLabel = 'squad:database';
    squadOption = 'Database';
  } else if (prefix === 'DOC') {
    sectorKey = 'docs';
    squadLabel = 'squad:docs';
    squadOption = 'Product';
  }

  const priority = localCard?.priority || 'P0';
  const priorityLabel = `priority:${priority}`;
  const sprintOption = num <= 10 ? 'S1' : 'S2';
  const sizeNumber = localCard?.estimate ? parseInt(localCard.estimate, 10) || 3 : 3;
  const dependencies = localCard?.dependencies || 'Nenhuma';

  return {
    cardId,
    prefix,
    num,
    sectorKey,
    squadLabel,
    squadOption,
    priority,
    priorityLabel,
    sprintOption,
    sizeNumber,
    dependencies
  };
}

async function updateIssueLabels(issueNumber, labels) {
  await fetch(`${REST_URL}/repos/${OWNER}/${REPO}/issues/${issueNumber}/labels`, {
    method: 'PUT',
    headers: restHeaders,
    body: JSON.stringify({ labels })
  });
}

async function addItemAndPopulateFields(projectMeta, issue, meta) {
  const projectId = projectMeta.project.id;
  const fields = projectMeta.fields;

  const addMutation = `
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
        item { id }
      }
    }
  `;
  const addData = await graphqlRequest(addMutation, { projectId, contentId: issue.id });
  const itemId = addData.addProjectV2ItemById.item.id;

  function buildSingleSelectPromise(fieldName, optionName) {
    const field = fields[fieldName];
    if (!field || !field.options) return Promise.resolve();
    const opt = field.options.find(o => o.name.toLowerCase() === optionName.toLowerCase());
    if (!opt) return Promise.resolve();
    return graphqlRequest(`
      mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { singleSelectOptionId: $optionId }
        }) { projectV2Item { id } }
      }
    `, { projectId, itemId, fieldId: field.id, optionId: opt.id });
  }

  function buildTextPromise(fieldName, textValue) {
    const field = fields[fieldName];
    if (!field) return Promise.resolve();
    return graphqlRequest(`
      mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { text: $text }
        }) { projectV2Item { id } }
      }
    `, { projectId, itemId, fieldId: field.id, text: String(textValue) });
  }

  function buildNumberPromise(fieldName, numValue) {
    const field = fields[fieldName];
    if (!field) return Promise.resolve();
    return graphqlRequest(`
      mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $number: Float!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { number: $number }
        }) { projectV2Item { id } }
      }
    `, { projectId, itemId, fieldId: field.id, number: Number(numValue) });
  }

  await Promise.all([
    buildSingleSelectPromise('Status', issue.state === 'CLOSED' ? 'Done' : 'Backlog'),
    buildSingleSelectPromise('Sprint', meta.sprintOption),
    buildSingleSelectPromise('Squad', meta.squadOption),
    buildSingleSelectPromise('Priority', meta.priority),
    buildNumberPromise('Size', meta.sizeNumber),
    buildTextPromise('Work ID', meta.cardId),
    buildTextPromise('Dependencies', meta.dependencies)
  ]);
}

async function main() {
  const { ownerId, existingProjects } = await getOwnerAndRepoInfo();
  const projectMap = {};

  for (const cfg of PROJECTS_CONFIG) {
    let project = existingProjects.find(
      p => !p.closed && p.title.trim().toLowerCase() === cfg.title.trim().toLowerCase()
    );
    if (!project) {
      project = await copyFromTemplateProject(ownerId, cfg.title);
    } else {
      console.log(`✅ Projeto verificado: "${project.title}" (#${project.number}) -> ${project.url}`);
    }
    const fields = await getProjectFieldsMap(project.id);
    projectMap[cfg.key] = { ...cfg, project, fields };
  }

  const issues = await fetchAllRepoIssues();
  console.log(`\n🔄 Sincronizando todas as ${issues.length} issues existentes da NEXA nos 5 projetos...`);

  for (let i = 0; i < issues.length; i++) {
    const issue = issues[i];
    const meta = parseIssueMetadata(issue);
    if (!meta) continue;

    const newLabels = [
      meta.priorityLabel,
      meta.squadLabel,
      'release:v1.0.0',
      'type:task'
    ];

    const sectorMeta = projectMap[meta.sectorKey];
    const generalMeta = projectMap.general;

    await Promise.all([
      updateIssueLabels(issue.number, newLabels),
      sectorMeta ? addItemAndPopulateFields(sectorMeta, issue, meta) : Promise.resolve(),
      addItemAndPopulateFields(generalMeta, issue, meta)
    ]);

    console.log(
      `   ✅ [${i + 1}/${issues.length}] Issue #${issue.number} [${meta.cardId}] sincronizada -> ${sectorMeta.title} & NEXA – Geral (Sprint: ${meta.sprintOption}, Squad: ${meta.squadOption})`
    );
  }

  console.log('\n🎉 TODAS AS 70 ISSUES DA NEXA FORAM SINCRONIZADAS COM SUCESSO NOS 5 PROJETOS!');
  for (const cfg of PROJECTS_CONFIG) {
    const p = projectMap[cfg.key].project;
    console.log(`🔗 ${p.title.padEnd(24, ' ')} -> ${p.url}`);
  }
}

main().catch(err => {
  console.error('\n❌ Erro:', err);
  process.exit(1);
});
