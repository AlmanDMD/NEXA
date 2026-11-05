/**
 * Script de Validação Automatizada — Card [DB-003]
 * Título: Configurar Instância PostgreSQL 16 e Ambiente Docker Compose
 *
 * Verifica programaticamente:
 * 1. Existência e validade sintática do docker-compose.yml (PostgreSQL 16 Alpine).
 * 2. Parametrização via variáveis de ambiente (.env.example) sem senhas hardcoded no docker-compose.yml.
 * 3. Volume persistente mapeado em /var/lib/postgresql/data.
 * 4. Timezone America/Sao_Paulo configurado.
 * 5. Healthcheck configurado com comando pg_isready.
 * 6. Scripts SQL de inicialização presentes em BancoNexa/docker/initdb/ e validação via `docker compose config`.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const COMPOSE_PATH = path.join(ROOT_DIR, 'docker-compose.yml');
const ENV_EXAMPLE_PATH = path.join(ROOT_DIR, '.env.example');
const GITIGNORE_PATH = path.join(ROOT_DIR, '.gitignore');
const INIT_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'docker', 'initdb', '01_init_extensions.sql');
const INIT_DDL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'docker', 'initdb', '02_modelo_logico_3fn.sql');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '03-instancia-postgresql-docker.md'),
  path.join(ROOT_DIR, 'BancoNexa', '03-instancia-postgresql-docker.md'),
];

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
console.log('🧪 VALIDAÇÃO DO CARD [DB-003] — POSTGRESQL 16 & DOCKER COMPOSE');
console.log('======================================================================\n');

// 1. Verificar existência dos arquivos
console.log('1. Verificando arquivos de infraestrutura Docker e documentação...');
assertCheck(fs.existsSync(COMPOSE_PATH), 'Arquivo docker-compose.yml presente na raiz');
assertCheck(fs.existsSync(ENV_EXAMPLE_PATH), 'Arquivo .env.example presente na raiz');
assertCheck(fs.existsSync(INIT_SQL_PATH), 'Script SQL de inicialização 01_init_extensions.sql presente em BancoNexa/docker/initdb/');
assertCheck(fs.existsSync(INIT_DDL_PATH), 'Script SQL DDL 3FN 02_modelo_logico_3fn.sql presente em BancoNexa/docker/initdb/');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const composeContent = fs.readFileSync(COMPOSE_PATH, 'utf8');
const envExampleContent = fs.readFileSync(ENV_EXAMPLE_PATH, 'utf8');
const gitignoreContent = fs.readFileSync(GITIGNORE_PATH, 'utf8');

// 2. Critério de Aceitação 1: docker-compose.yml funcional com PostgreSQL 16, timezone e porta 5432
console.log('\n2. Verificando Critério de Aceitação 1 (PostgreSQL 16 Alpine, Timezone e Porta 5432)...');
assertCheck(
  /image:\s*postgres:16-alpine/.test(composeContent),
  'Imagem oficial postgres:16-alpine configurada no serviço postgres'
);
assertCheck(
  composeContent.includes('America/Sao_Paulo'),
  'Timezone America/Sao_Paulo configurado no ambiente e comando do PostgreSQL'
);
assertCheck(
  composeContent.includes('${POSTGRES_PORT:-5432}:5432'),
  'Mapeamento da porta padrão 5432 parametrizado via ${POSTGRES_PORT:-5432}:5432'
);

// 3. Critério de Aceitação 2: Volume persistente mapeado
console.log('\n3. Verificando Critério de Aceitação 2 (Volume Persistente Mapeado)...');
assertCheck(
  composeContent.includes('nexa_postgres_data:/var/lib/postgresql/data') &&
    /volumes:\s*\r?\n\s*nexa_postgres_data:/.test(composeContent),
  'Volume persistente nomeado nexa_postgres_data mapeado para /var/lib/postgresql/data'
);
assertCheck(
  composeContent.includes('./BancoNexa/docker/initdb:/docker-entrypoint-initdb.d:ro'),
  'Diretório de scripts SQL de inicialização mapeado em /docker-entrypoint-initdb.d (read-only)'
);

// 4. Critério de Aceitação 3: Healthcheck configurado com pg_isready
console.log('\n4. Verificando Critério de Aceitação 3 (Healthcheck com pg_isready)...');
assertCheck(
  composeContent.includes('healthcheck:') &&
    composeContent.includes('pg_isready') &&
    composeContent.includes('interval:') &&
    composeContent.includes('timeout:') &&
    composeContent.includes('retries:'),
  'Healthcheck configurado com pg_isready, interval, timeout e retries'
);

// 5. Observação Técnica: Sem senhas hardcoded; referências a .env
console.log('\n5. Verificando Observação Técnica (Segurança de Credenciais e .env)...');
assertCheck(
  composeContent.includes('${POSTGRES_USER:?') &&
    composeContent.includes('${POSTGRES_PASSWORD:?') &&
    composeContent.includes('${POSTGRES_DB:?'),
  'Credenciais POSTGRES_USER, POSTGRES_PASSWORD e POSTGRES_DB parametrizadas via .env sem senha hardcoded no docker-compose.yml'
);
assertCheck(
  envExampleContent.includes('POSTGRES_USER=') &&
    envExampleContent.includes('POSTGRES_PASSWORD=') &&
    envExampleContent.includes('POSTGRES_DB=') &&
    envExampleContent.includes('DATABASE_URL='),
  'Variáveis POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB e DATABASE_URL documentadas no .env.example'
);
assertCheck(
  gitignoreContent.includes('.env') && gitignoreContent.includes('!.env.example'),
  'Arquivo .gitignore protege .env real e permite versionamento de .env.example'
);

// 6. Validação real do Docker Compose CLI (`docker compose config`)
console.log('\n6. Validando sintaxe e interpolação com Docker Compose CLI...');
try {
  const renderedConfig = execSync('docker compose --env-file .env.example config', {
    cwd: ROOT_DIR,
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  assertCheck(
    renderedConfig.includes('postgres:16-alpine') && renderedConfig.includes('pg_isready'),
    'Comando `docker compose --env-file .env.example config` validou o arquivo com código de saída 0'
  );
} catch (err) {
  assertCheck(false, `Falha ao validar com docker compose config: ${err.message}`);
}

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-003] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
