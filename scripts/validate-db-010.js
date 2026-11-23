/**
 * Script de Validação Automatizada — Card [DB-010]
 * Título: Criar Script Base de Migração Inicial e Verificação de Conexão
 *
 * Verifica programaticamente:
 * 1. Existência de `prisma/check-connection.ts` e `BancoNexa/sql/10_migracao_inicial_lote1_e_sanidade.sql`.
 * 2. Critério 1: Execução de `prisma/check-connection.ts` retorna código 0 quando saudável.
 * 3. Critério 2: Verifica as 4 tabelas fundamentais (`users`, `user_profiles`, `auth_sessions`, `audit_logs`) e `SELECT 1`.
 * 4. Critério 3: Documentado no `README.md` principal do projeto e em `BancoNexa/README.md`.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const CHECK_CONN_TS_PATH = path.join(ROOT_DIR, 'prisma', 'check-connection.ts');
const CONSOLIDATED_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '10_migracao_inicial_lote1_e_sanidade.sql');
const INITDB_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'docker', 'initdb', '03_lote1_identidade_seguranca.sql');
const ROOT_README_PATH = path.join(ROOT_DIR, 'README.md');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '10-migracao-inicial-verificacao-conexao.md'),
  path.join(ROOT_DIR, 'BancoNexa', '10-migracao-inicial-verificacao-conexao.md'),
];

const FOUR_FUNDAMENTAL_TABLES = ['users', 'user_profiles', 'auth_sessions', 'audit_logs'];

let failures = 0;

function assertCheck(condition, message) {
  if (condition) {
    console.log(`  [PASS] ${message}`);
  } else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-010] — MIGRAÇÃO INICIAL E CHECK-CONNECTION');
console.log('======================================================================\n');

// 1. Verificar existência dos artefatos
console.log('1. Verificando arquivos de script TypeScript, SQL consolidado e documentação...');
assertCheck(fs.existsSync(CHECK_CONN_TS_PATH), 'Script prisma/check-connection.ts presente');
assertCheck(
  fs.existsSync(CONSOLIDATED_SQL_PATH),
  'Script SQL consolidado BancoNexa/sql/10_migracao_inicial_lote1_e_sanidade.sql presente'
);
assertCheck(
  fs.existsSync(INITDB_SQL_PATH),
  'Script SQL do Lote 1 copiado em BancoNexa/docker/initdb/03_lote1_identidade_seguranca.sql'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

// 2. Critério 1 e 2: Execução de prisma/check-connection.ts retorna código 0 e verifica as 4 tabelas
console.log('\n2. Verificando Critérios de Aceitação 1 e 2 (Execução código 0 e 4 tabelas fundamentais)...');
let checkOutput = '';
let checkExitCode = 1;
try {
  checkOutput = execSync('node prisma/check-connection.ts', {
    cwd: ROOT_DIR,
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  checkExitCode = 0;
} catch (err) {
  checkExitCode = err.status || 1;
}

assertCheck(checkExitCode === 0, 'Script `node prisma/check-connection.ts` executou e retornou código 0');
assertCheck(
  checkOutput.includes('SELECT 1'),
  'Script executa e valida a query de sanidade `SELECT 1`'
);

const sqlContent = fs.readFileSync(CONSOLIDATED_SQL_PATH, 'utf8');
for (const table of FOUR_FUNDAMENTAL_TABLES) {
  assertCheck(
    checkOutput.includes(table) &&
      checkOutput.includes('SAUDÁVEL') &&
      sqlContent.includes(`CREATE TABLE IF NOT EXISTS ${table}`),
    `Tabela fundamental '${table}' verificada pelo check-connection.ts e presente no SQL consolidado`
  );
}

// 3. Critério 3: Documentado no README do projeto
console.log('\n3. Verificando Critério de Aceitação 3 (Documentado no README do projeto)...');
const rootReadme = fs.readFileSync(ROOT_README_PATH, 'utf8');
const bancoReadme = fs.readFileSync(BANCO_README_PATH, 'utf8');
assertCheck(
  rootReadme.includes('prisma/check-connection.ts') &&
    rootReadme.includes('users') &&
    rootReadme.includes('user_profiles') &&
    rootReadme.includes('auth_sessions') &&
    rootReadme.includes('audit_logs'),
  'Verificador check-connection.ts e as 4 tabelas fundamentais estão documentados no README.md principal do projeto'
);
assertCheck(
  bancoReadme.includes('DB-010'),
  'Card DB-010 documentado em BancoNexa/README.md'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-010] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
