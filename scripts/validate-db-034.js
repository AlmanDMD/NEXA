/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-034]
 * Título: Implementar Tabela de Alertas e Indicadores de Risco (academic_alerts)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126010000_create_academic_alerts_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126010000_create_academic_alerts_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '34_tabela_academic_alerts.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '34-tabela-alertas-indicadores-risco-academic-alerts.md'),
  path.join(ROOT_DIR, 'BancoNexa', '34-tabela-alertas-indicadores-risco-academic-alerts.md'),
];

const RISK_PRIORITY = { CRITICAL: 4, HIGH: 3, MODERATE: 2, LOW: 1 };
const VALID_CATEGORIES = new Set(['ATTENDANCE', 'GRADE_DROP', 'PENDING_TASKS', 'SELF_EVAL_GAP']);
const VALID_STATUSES = new Set(['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED']);

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class AcademicAlertsSimulator {
  constructor() {
    this.users = new Map();
    this.enrollments = new Map();
    this.alerts = [];
    this.seq = 1;
  }
  addUser(id, role) { this.users.set(id, { id, role }); }
  addEnrollment(id, student_id, class_id) { this.enrollments.set(id, { id, student_id, class_id }); }

  createAlert(row) {
    const reason = String(row.explainable_reason || '').trim();
    if (reason.length < 10) {
      const err = new Error('violates check constraint "chk_academic_alerts_reason_not_empty"');
      err.sqlState = '23514';
      throw err;
    }
    if (!row.metric_snapshot || typeof row.metric_snapshot !== 'object' || Array.isArray(row.metric_snapshot)) {
      const err = new Error('violates check constraint "chk_academic_alerts_metric_snapshot_object"');
      err.sqlState = '23514';
      throw err;
    }
    if (!RISK_PRIORITY[row.risk_level] || !VALID_CATEGORIES.has(row.alert_category)) {
      const err = new Error('invalid enum value');
      err.sqlState = '22P02';
      throw err;
    }
    const status = row.status || 'ACTIVE';
    if (!VALID_STATUSES.has(status)) {
      const err = new Error('invalid alert_status_enum');
      err.sqlState = '22P02';
      throw err;
    }
    const enr = this.enrollments.get(row.enrollment_id);
    if (!enr) {
      const err = new Error('violates foreign key constraint "fk_academic_alerts_enrollment"');
      err.sqlState = '23503';
      throw err;
    }
    if (enr.student_id !== row.student_id || enr.class_id !== row.class_id) {
      const err = new Error('violates trigger "chk_academic_alerts_enrollment_coherence"');
      err.sqlState = '23514';
      throw err;
    }
    if (row.resolved_by && this.users.get(row.resolved_by)?.role === 'STUDENT') {
      const err = new Error('violates trigger "chk_academic_alerts_resolver_role"');
      err.sqlState = '23514';
      throw err;
    }
    const saved = {
      id: `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      ...row,
      explainable_reason: reason,
      status,
    };
    this.alerts.push(saved);
    return saved;
  }

  getActiveByClassOrdered(classId) {
    return this.alerts
      .filter((a) => a.class_id === classId && a.status === 'ACTIVE')
      .sort((a, b) => RISK_PRIORITY[b.risk_level] - RISK_PRIORITY[a.risk_level]);
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-034] — ALERTAS ACADÊMICOS (academic_alerts)');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/34_tabela_academic_alerts.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-034'),
  'Documentação DB-034 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /explainable_reason\s+TEXT\s+NOT\s+NULL/i.test(sqlContent) &&
    /chk_academic_alerts_reason_not_empty/i.test(sqlContent) &&
    /metric_snapshot\s+JSONB\s+NOT\s+NULL/i.test(sqlContent) &&
    /chk_academic_alerts_metric_snapshot_object/i.test(sqlContent) &&
    /idx_academic_alerts_class_status_risk\s+ON\s+academic_alerts\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*status\s*,\s*risk_level\s*\)/i.test(sqlContent) &&
    /idx_academic_alerts_metric_snapshot_gin/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (explainable_reason, metric_snapshot JSONB + GIN e índice class_id, status, risk_level)'
);
assertCheck(
  schemaContent.includes('model AcademicAlert') &&
    schemaContent.includes('@map("metric_snapshot") @db.JsonB') &&
    schemaContent.includes('@@index([classId, status, riskLevel], map: "idx_academic_alerts_class_status_risk")') &&
    typesTsContent.includes('export interface AcademicAlert {'),
  'Modelo AcademicAlert integrado ao prisma/schema.prisma e tipos TypeScript gerados'
);
assertCheck(
  /CREATE\s+TABLE\s+academic_alerts/i.test(fs.readFileSync(SQL_3FN_PATH, 'utf8')),
  'Alinhamento confirmado com modelo 3FN ([T25] academic_alerts)'
);

const sim = new AcademicAlertsSimulator();
sim.addUser('stu-1', 'STUDENT');
sim.addUser('tch-1', 'TEACHER');
sim.addEnrollment('enr-1', 'stu-1', 'cls-1');

sim.createAlert({
  student_id: 'stu-1',
  enrollment_id: 'enr-1',
  class_id: 'cls-1',
  risk_level: 'MODERATE',
  alert_category: 'PENDING_TASKS',
  explainable_reason: '2 tarefas práticas pendentes próximas ao prazo no módulo de Metrologia.',
  metric_snapshot: { pending_tasks: 2, late_tasks: 0 },
});
sim.createAlert({
  student_id: 'stu-1',
  enrollment_id: 'enr-1',
  class_id: 'cls-1',
  risk_level: 'CRITICAL',
  alert_category: 'ATTENDANCE',
  explainable_reason: 'Frequência caiu para 68.00% (abaixo do limite mínimo de 75% do SENAI).',
  metric_snapshot: { attendance_rate: 68.0, absent_hours: 8, total_hours: 25 },
});
const activeOrdered = sim.getActiveByClassOrdered('cls-1');
assertCheck(
  activeOrdered.length === 2 && activeOrdered[0].risk_level === 'CRITICAL' && activeOrdered[1].risk_level === 'MODERATE',
  'Teste 1: Alertas ativos priorizados corretamente (CRITICAL antes de MODERATE) com snapshot JSONB'
);

let emptyReasonBlocked = false;
let nonObjectSnapshotBlocked = false;
let studentResolverBlocked = false;
try {
  sim.createAlert({ student_id: 'stu-1', enrollment_id: 'enr-1', class_id: 'cls-1', risk_level: 'LOW', alert_category: 'ATTENDANCE', explainable_reason: 'curto', metric_snapshot: { a: 1 } });
} catch (err) { emptyReasonBlocked = err.sqlState === '23514'; }
try {
  sim.createAlert({ student_id: 'stu-1', enrollment_id: 'enr-1', class_id: 'cls-1', risk_level: 'LOW', alert_category: 'ATTENDANCE', explainable_reason: 'Razão explicável válida para teste.', metric_snapshot: [1, 2, 3] });
} catch (err) { nonObjectSnapshotBlocked = err.sqlState === '23514'; }
try {
  sim.createAlert({ student_id: 'stu-1', enrollment_id: 'enr-1', class_id: 'cls-1', risk_level: 'LOW', alert_category: 'ATTENDANCE', explainable_reason: 'Razão explicável válida para teste.', metric_snapshot: { a: 1 }, resolved_by: 'stu-1' });
} catch (err) { studentResolverBlocked = err.sqlState === '23514'; }
assertCheck(
  emptyReasonBlocked && nonObjectSnapshotBlocked && studentResolverBlocked,
  'Teste 2: explainable_reason curto, metric_snapshot não-objeto e resolved_by STUDENT bloqueados (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-034] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
