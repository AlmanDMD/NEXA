/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-045]
 * Título: Implementar Tabela de Conquistas e Níveis de Gamificação (gamification_badges)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127040000_create_gamification_badges_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127040000_create_gamification_badges_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '45_tabela_gamification_badges.sql');
const SEED_LOTE5_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '45_seed_gamification_badges.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '45-tabela-conquistas-gamificacao-gamification-badges.md'),
  path.join(ROOT_DIR, 'BancoNexa', '45-tabela-conquistas-gamificacao-gamification-badges.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-045] — CONQUISTAS & GAMIFICAÇÃO (gamification_badges)');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node prisma/seed.ts', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate, db:migrate e db:seed executados com sucesso');
} catch (err) {
  assertCheck(false, `Falha nos scripts base: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const seedLote5Content = fs.readFileSync(SEED_LOTE5_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');

assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/45_tabela_gamification_badges.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-045'),
  'Documentação DB-045 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /criteria_explanation\s+TEXT\s+NOT\s+NULL/i.test(sqlContent) &&
    /chk_gamification_badges_criteria_not_empty/i.test(sqlContent) &&
    /uq_gamification_badges_code\s+UNIQUE\s*\(\s*code\s*\)/i.test(sqlContent) &&
    /chk_gamification_badges_xp_positive[\s\S]*?xp_reward\s*>\s*0/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (criteria_explanation obrigatório, code UNIQUE e xp_reward > 0)'
);
assertCheck(
  schemaContent.includes('model GamificationBadge') && typesTsContent.includes('export interface GamificationBadge {'),
  'Modelo GamificationBadge integrado ao prisma/schema.prisma e tipos TypeScript'
);
assertCheck(
  seedLote5Content.includes('BADGE-METROLOGIA-100') &&
    seedLote5Content.includes('Mestre do Micrômetro') &&
    (seedLote5Content.match(/INSERT INTO gamification_badges/gi) || []).length >= 6,
  'DoD validado: tabela gamification_badges populada com 6 conquistas técnicas transparentes SENAI'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-045] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
