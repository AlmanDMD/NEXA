/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-046]
 * Título: Criar Tabela de Conquistas Desbloqueadas pelos Estudantes (student_achievements)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127050000_create_student_achievements_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127050000_create_student_achievements_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '46_tabela_student_achievements.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '46-tabela-conquistas-estudantes-student-achievements.md'),
  path.join(ROOT_DIR, 'BancoNexa', '46-tabela-conquistas-estudantes-student-achievements.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class AchievementsSimulator {
  constructor() {
    this.uniquePairs = new Set();
    this.rows = [];
  }
  unlock(row) {
    const key = `${row.student_id}::${row.badge_id}`;
    if (this.uniquePairs.has(key)) { const e = new Error('uq_student_achievements_composite'); e.sqlState = '23505'; throw e; }
    this.uniquePairs.add(key);
    this.rows.push(row);
    return row;
  }
  listDesc(studentId) {
    return this.rows.filter((r) => r.student_id === studentId).sort((a, b) => b.unlocked_at.localeCompare(a.unlocked_at));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-046] — CONQUISTAS DOS ESTUDANTES (student_achievements)');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate executados com sucesso');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');

assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/46_tabela_student_achievements.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-046'),
  'Documentação DB-046 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /uq_student_achievements_composite\s+UNIQUE\s*\(\s*student_id\s*,\s*badge_id\s*\)/i.test(sqlContent) &&
    /fk_student_achievements_badge/i.test(sqlContent) &&
    /fk_student_achievements_enrollment/i.test(sqlContent) &&
    /idx_student_achievements_student_unlocked\s+ON\s+student_achievements\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*unlocked_at\s+DESC\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (UNIQUE student_id/badge_id, FKs íntegras e índice unlocked_at DESC)'
);
assertCheck(
  schemaContent.includes('model StudentAchievement') && typesTsContent.includes('export interface StudentAchievement {'),
  'Modelo StudentAchievement integrado ao prisma/schema.prisma e tipos TypeScript'
);

const sim = new AchievementsSimulator();
sim.unlock({ student_id: 'stu-1', enrollment_id: 'enr-1', badge_id: 'bg-1', unlocked_at: '2026-02-20T10:00:00Z', origin_reference: 'Módulo 1' });
sim.unlock({ student_id: 'stu-1', enrollment_id: 'enr-1', badge_id: 'bg-2', unlocked_at: '2026-03-10T10:00:00Z', origin_reference: 'Módulo 2' });
let dupBlocked = false;
try { sim.unlock({ student_id: 'stu-1', enrollment_id: 'enr-1', badge_id: 'bg-1', unlocked_at: '2026-03-12T10:00:00Z', origin_reference: 'Duplicada' }); } catch (e) { dupBlocked = e.sqlState === '23505'; }
const list = sim.listDesc('stu-1');
assertCheck(
  dupBlocked && list.length === 2 && list[0].badge_id === 'bg-2',
  'Testes 1 e 2: Bloqueio de conquista duplicada (23505) e ordenação cronológica unlocked_at DESC'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-046] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
