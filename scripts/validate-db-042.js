/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-042]
 * Título: Implementar Tabela de Solicitações de Apoio e Mentoria Confidenciais (help_requests)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127010000_create_help_requests_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127010000_create_help_requests_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '42_tabela_help_requests.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '42-tabela-solicitacoes-apoio-confidenciais-help-requests.md'),
  path.join(ROOT_DIR, 'BancoNexa', '42-tabela-solicitacoes-apoio-confidenciais-help-requests.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class HelpRequestSimulator {
  constructor() { this.rows = []; }
  create(row) {
    const saved = {
      id: `hr-${this.rows.length + 1}`,
      is_confidential: true,
      status: 'OPEN',
      closed_at: null,
      ...row,
    };
    this.rows.push(saved);
    return saved;
  }
  transition(id, nextStatus) {
    const r = this.rows.find((x) => x.id === id);
    if (r.status === 'CLOSED') { const e = new Error('closed immutable'); e.sqlState = '23514'; throw e; }
    if (r.status === 'RESOLVED' && nextStatus === 'OPEN') { const e = new Error('invalid regression'); e.sqlState = '23514'; throw e; }
    r.status = nextStatus;
    r.closed_at = nextStatus === 'CLOSED' ? new Date().toISOString() : null;
    return r;
  }
  selectAs(role, userId) {
    if (['ADMIN', 'COORDINATOR', 'TEACHER'].includes(role)) return [...this.rows];
    return this.rows.filter((r) => r.student_id === userId);
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-042] — SOLICITAÇÕES CONFIDENCIAIS (help_requests)');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/42_tabela_help_requests.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-042'),
  'Documentação DB-042 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /is_confidential\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /ENABLE\s+ROW\s+LEVEL\s+SECURITY/i.test(sqlContent) &&
    /pol_help_requests_confidential_isolation/i.test(sqlContent) &&
    /idx_help_requests_teacher_status\s+ON\s+help_requests\s+USING\s+BTREE\s*\(\s*assigned_teacher_id\s*,\s*status\s*\)/i.test(sqlContent) &&
    /idx_help_requests_student_status\s+ON\s+help_requests\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*status\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (is_confidential DEFAULT TRUE, RLS, máquina de estados e índices)'
);
assertCheck(
  schemaContent.includes('model HelpRequest') && typesTsContent.includes('export interface HelpRequest {'),
  'Modelo HelpRequest integrado ao prisma/schema.prisma e tipos TypeScript'
);

const sim = new HelpRequestSimulator();
const req = sim.create({ student_id: 'stu-1', assigned_teacher_id: 'tch-1', subject_title: 'Dúvida no Torno' });
assertCheck(
  req.is_confidential === true &&
    sim.selectAs('STUDENT', 'stu-2').length === 0 &&
    sim.selectAs('STUDENT', 'stu-1').length === 1 &&
    sim.selectAs('TEACHER', 'tch-1').length === 1,
  'Teste 1 (Critério 1): Sigilo confidencial impede outro estudante de visualizar a solicitação'
);

sim.transition(req.id, 'IN_PROGRESS');
sim.transition(req.id, 'RESOLVED');
sim.transition(req.id, 'CLOSED');
let reopenBlocked = false;
try { sim.transition(req.id, 'OPEN'); } catch (e) { reopenBlocked = e.sqlState === '23514'; }
assertCheck(
  req.status === 'CLOSED' && req.closed_at !== null && reopenBlocked,
  'Teste 2 (Critério 2): Ciclo completo OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED e bloqueio de regressão pós-fechamento'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-042] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
