/**
 * Script de Validação Automatizada — Card [DB-004]
 * Título: Inicializar Prisma ORM e Estrutura de Migrations Versionadas
 *
 * Verifica programaticamente:
 * 1. Existência do arquivo `prisma/schema.prisma` apontando para `env("DATABASE_URL")` com provider `postgresql`.
 * 2. Uso da convenção `snake_case` nas colunas e tabelas via `@map` e `@@map`.
 * 3. Pasta `prisma/migrations/` e `BancoNexa/migrations/` com `migration_lock.toml` e `migration.sql` monitoradas pelo Git.
 * 4. Execução real com sucesso dos scripts `npm run db:generate` e `npm run db:migrate`.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const PACKAGE_JSON_PATH = path.join(ROOT_DIR, 'package.json');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_LOCK_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', 'migration_lock.toml');
const INITIAL_MIGRATION_SQL = path.join(
  ROOT_DIR,
  'prisma',
  'migrations',
  '20261104000000_init_migration_control',
  'migration.sql'
);
const BANCO_MIGRATION_SQL = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261104000000_init_migration_control.sql'
);
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '04-estrutura-migrations-versionadas.md'),
  path.join(ROOT_DIR, 'BancoNexa', '04-estrutura-migrations-versionadas.md'),
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
console.log('🧪 VALIDAÇÃO DO CARD [DB-004] — ESTRUTURA DE MIGRATIONS VERSIONADAS');
console.log('======================================================================\n');

// 1. Verificar existência dos arquivos
console.log('1. Verificando estrutura de pastas e arquivos de migration...');
assertCheck(fs.existsSync(PACKAGE_JSON_PATH), 'Arquivo package.json presente na raiz');
assertCheck(fs.existsSync(SCHEMA_PRISMA_PATH), 'Arquivo prisma/schema.prisma presente');
assertCheck(fs.existsSync(MIGRATION_LOCK_PATH), 'Arquivo prisma/migrations/migration_lock.toml presente');
assertCheck(
  fs.existsSync(INITIAL_MIGRATION_SQL),
  'Migration SQL inicial presente em prisma/migrations/20261104000000_init_migration_control/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL),
  'Migration SQL espelhada em BancoNexa/migrations/20261104000000_init_migration_control.sql'
);

for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

// 2. Critério 1 e Observação Técnica: schema.prisma com DATABASE_URL e @map / @@map snake_case
console.log('\n2. Verificando Critério de Aceitação 1 e Convenção snake_case (@map / @@map)...');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
assertCheck(
  schemaContent.includes('provider = "postgresql"') && schemaContent.includes('url      = env("DATABASE_URL")'),
  'schema.prisma configurado com provider = "postgresql" e url = env("DATABASE_URL")'
);
assertCheck(
  schemaContent.includes('@map("migration_name")') &&
    schemaContent.includes('@map("checksum_sha256")') &&
    schemaContent.includes('@@map("schema_migrations")'),
  'Convenção camelCase -> snake_case aplicada com @map e @@map no schema.prisma'
);

// 3. Critério 2: Scripts npm run db:migrate e npm run db:generate funcionando
console.log('\n3. Verificando Critério de Aceitação 2 (Execução de npm run db:generate e npm run db:migrate)...');
const pkg = JSON.parse(fs.readFileSync(PACKAGE_JSON_PATH, 'utf8'));
assertCheck(
  Boolean(pkg.scripts && pkg.scripts['db:migrate'] && pkg.scripts['db:generate']),
  'Scripts "db:migrate" e "db:generate" declarados no package.json'
);

try {
  const genOut = execSync('npm run db:generate', {
    cwd: ROOT_DIR,
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  assertCheck(
    genOut.includes('concluída com sucesso'),
    'Comando `npm run db:generate` executado com sucesso (exit code 0)'
  );
} catch (err) {
  assertCheck(false, `Falha ao executar npm run db:generate: ${err.message}`);
}

try {
  const migOut = execSync('npm run db:migrate', {
    cwd: ROOT_DIR,
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  assertCheck(
    migOut.includes('concluído com sucesso'),
    'Comando `npm run db:migrate` executado com sucesso (exit code 0)'
  );
} catch (err) {
  assertCheck(false, `Falha ao executar npm run db:migrate: ${err.message}`);
}

// 4. Critério 3: Pasta prisma/migrations/ monitorada pelo Git (não ignorada pelo .gitignore)
console.log('\n4. Verificando Critério de Aceitação 3 (Monitoramento da pasta prisma/migrations/ pelo Git)...');
try {
  // git check-ignore retorna exit code 1 quando o caminho NÃO é ignorado (ou seja, é monitorado!)
  let isIgnored = false;
  try {
    execSync('git check-ignore prisma/migrations/migration_lock.toml', {
      cwd: ROOT_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    isIgnored = true;
  } catch {
    isIgnored = false;
  }
  assertCheck(!isIgnored, 'Pasta prisma/migrations/ está habilitada para rastreamento pelo Git (não ignorada)');
} catch (err) {
  assertCheck(false, `Erro ao verificar git check-ignore: ${err.message}`);
}

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-004] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
