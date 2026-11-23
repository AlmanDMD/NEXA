/**
 * Script de Validação Automatizada — Card [DB-005]
 * Título: Criar Enumerações Globais de Sistema (Roles, Status, Graus de Risco)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Enums criados e validados no `prisma/schema.prisma` (Role, EnrollmentStatus,
 *    RiskLevel, SubmissionStatus, HelpRequestStatus + enums complementares de domínio).
 * 2. Critério 2: Migration SQL versionada gerada criando os tipos nativos `ENUM` no PostgreSQL 16.
 * 3. Critério 3: Tipos exportados (`system-enums.ts`, `system_enums.py`, `system-enums.json`)
 *    compatíveis com as validações da API e testados em tempo de execução.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'prisma',
  'migrations',
  '20261104010000_create_global_system_enums',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261104010000_create_global_system_enums.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '05_enums_globais.sql');
const TYPES_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'system-enums.ts');
const TYPES_PY_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'system_enums.py');
const TYPES_JSON_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'system-enums.json');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '05-enumeracoes-globais-sistema.md'),
  path.join(ROOT_DIR, 'BancoNexa', '05-enumeracoes-globais-sistema.md'),
];

const CORE_ENUMS_SPEC = {
  Role: {
    pgTypeName: 'user_role_enum',
    values: ['ADMIN', 'COORDINATOR', 'TEACHER', 'STUDENT'],
  },
  EnrollmentStatus: {
    pgTypeName: 'enrollment_status_enum',
    values: ['ACTIVE', 'COMPLETED', 'DROPPED', 'SUSPENDED'],
  },
  RiskLevel: {
    pgTypeName: 'risk_level_enum',
    values: ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'],
  },
  SubmissionStatus: {
    pgTypeName: 'submission_status_enum',
    values: ['PENDING', 'SUBMITTED', 'EVALUATED', 'LATE'],
  },
  HelpRequestStatus: {
    pgTypeName: 'help_request_status_enum',
    values: ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'],
  },
  CompetencyCategory: {
    pgTypeName: 'competency_category_enum',
    values: ['TECHNICAL', 'SAFETY', 'PROCEDURAL'],
  },
};

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
console.log('🧪 VALIDAÇÃO DO CARD [DB-005] — ENUMERAÇÕES GLOBAIS DE SISTEMA');
console.log('======================================================================\n');

// 1. Executar geração e migração para garantir sincronia
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate executaram e atualizaram os artefatos com sucesso');
} catch (err) {
  assertCheck(false, `Erro ao executar db:generate / db:migrate: ${err.message}`);
}

// 2. Critério 1: Enums criados e validados no schema.prisma
console.log('\n2. Verificando Critério de Aceitação 1 (Enums declarados em prisma/schema.prisma)...');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
for (const [enumName, spec] of Object.entries(CORE_ENUMS_SPEC)) {
  const hasEnumBlock = new RegExp(`enum\\s+${enumName}\\s*\\{[\\s\\S]*?@@map\\("${spec.pgTypeName}"\\)[\\s\\S]*?\\}`).test(
    schemaContent
  );
  const hasAllValues = spec.values.every((v) => schemaContent.includes(v));
  assertCheck(
    hasEnumBlock && hasAllValues,
    `Enum ${enumName} -> @@map("${spec.pgTypeName}") validado com valores [${spec.values.join(', ')}]`
  );
}

// 3. Critério 2: Migration SQL gerada criando os tipos nativos ENUM no PostgreSQL
console.log('\n3. Verificando Critério de Aceitação 2 (Migration SQL nativa PostgreSQL 16)...');
assertCheck(fs.existsSync(MIGRATION_SQL_PATH), 'Migration SQL presente em prisma/migrations/20261104010000_create_global_system_enums/migration.sql');
assertCheck(fs.existsSync(BANCO_MIGRATION_SQL_PATH), 'Migration SQL espelhada em BancoNexa/migrations/');
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL disponível em BancoNexa/sql/05_enums_globais.sql');

const migSql = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
for (const [enumName, spec] of Object.entries(CORE_ENUMS_SPEC)) {
  const expectedValuesSql = spec.values.map((v) => `'${v}'`).join(', ');
  const hasCreateType = migSql.includes(`CREATE TYPE ${spec.pgTypeName} AS ENUM (${expectedValuesSql})`);
  assertCheck(
    hasCreateType,
    `SQL CREATE TYPE ${spec.pgTypeName} AS ENUM (${expectedValuesSql}) presente na migration`
  );
}

// 4. Critério 3: Tipos exportados compatíveis com as validações da API
console.log('\n4. Verificando Critério de Aceitação 3 (Tipos exportados para API: TS, Python e JSON)...');
assertCheck(fs.existsSync(TYPES_TS_PATH), 'Tipos TypeScript exportados em BancoNexa/types/system-enums.ts');
assertCheck(fs.existsSync(TYPES_PY_PATH), 'Tipos Python (StrEnum) exportados em BancoNexa/types/system_enums.py');
assertCheck(fs.existsSync(TYPES_JSON_PATH), 'Contrato JSON exportado em BancoNexa/types/system-enums.json');

const exportedJson = JSON.parse(fs.readFileSync(TYPES_JSON_PATH, 'utf8'));
assertCheck(
  Array.isArray(exportedJson.enums) && exportedJson.enums.length === 18,
  `Contrato JSON contém todos os 18 enums globais do sistema (${exportedJson.enums.length}/18)`
);

const tsContent = fs.readFileSync(TYPES_TS_PATH, 'utf8');
const pyContent = fs.readFileSync(TYPES_PY_PATH, 'utf8');
for (const [enumName, spec] of Object.entries(CORE_ENUMS_SPEC)) {
  assertCheck(
    tsContent.includes(`export const ${enumName} =`) && pyContent.includes(`class ${enumName}(StrEnum):`),
    `Tipo ${enumName} exportado e sincronizado tanto para TypeScript quanto para Python/FastAPI`
  );
}

// 5. Documentação
console.log('\n5. Verificando documentação técnica do card DB-005...');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-005] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
