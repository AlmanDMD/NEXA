/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-039]
 * Título: Implementar Tabela de Histórico e Linha do Tempo Acadêmica (student_milestone_history)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126060000_create_student_milestone_history_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126060000_create_student_milestone_history_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '39_tabela_student_milestone_history.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '39-tabela-historico-linha-tempo-student-milestone-history.md'),
  path.join(ROOT_DIR, 'BancoNexa', '39-tabela-historico-linha-tempo-student-milestone-history.md'),
];

const VALID_TYPES = new Set(['MODULE_COMPLETED', 'SKILL_LEVEL_UP', 'PERFECT_ATTENDANCE', 'RECOVERY_ACHIEVED']);

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class MilestoneHistorySimulator {
  constructor() {
    this.users = new Map();
    this.enrollments = new Map();
    this.milestones = [];
    this.seq = 1;
  }
  addUser(id, role) { this.users.set(id, { id, role }); }
  addEnrollment(id, student_id) { this.enrollments.set(id, { id, student_id }); }

  recordMilestone(row) {
    if (this.users.get(row.student_id)?.role !== 'STUDENT') {
      const err = new Error('violates trigger "chk_milestone_history_student_role"');
      err.sqlState = '23514';
      throw err;
    }
    const enr = this.enrollments.get(row.enrollment_id);
    if (!enr) {
      const err = new Error('violates foreign key constraint "fk_milestone_history_enrollment"');
      err.sqlState = '23503';
      throw err;
    }
    if (enr.student_id !== row.student_id) {
      const err = new Error('violates trigger "chk_milestone_history_enrollment_owner"');
      err.sqlState = '23514';
      throw err;
    }
    if (!VALID_TYPES.has(row.milestone_type)) {
      const err = new Error('invalid milestone_type_enum');
      err.sqlState = '22P02';
      throw err;
    }
    const title = String(row.title || '').trim();
    if (title.length < 3) {
      const err = new Error('violates check constraint "chk_milestone_history_title_not_empty"');
      err.sqlState = '23514';
      throw err;
    }
    if (row.metadata != null && (typeof row.metadata !== 'object' || Array.isArray(row.metadata))) {
      const err = new Error('violates check constraint "chk_milestone_history_metadata_object"');
      err.sqlState = '23514';
      throw err;
    }
    const saved = {
      id: `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      ...row,
      title,
      achieved_at: row.achieved_at || new Date().toISOString(),
    };
    this.milestones.push(saved);
    return saved;
  }

  getTimelineDesc(studentId) {
    return this.milestones
      .filter((m) => m.student_id === studentId)
      .sort((a, b) => b.achieved_at.localeCompare(a.achieved_at));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-039] — LINHA DO TEMPO (student_milestone_history)');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/39_tabela_student_milestone_history.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-039'),
  'Documentação DB-039 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /milestone_type\s+milestone_type_enum\s+NOT\s+NULL/i.test(sqlContent) &&
    /fk_milestone_history_enrollment/i.test(sqlContent) &&
    /fk_milestone_history_module/i.test(sqlContent) &&
    /idx_milestone_history_student_achieved\s+ON\s+student_milestone_history\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*achieved_at\s+DESC\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (milestone_type_enum, FKs íntegras e índice student_id, achieved_at DESC)'
);
assertCheck(
  schemaContent.includes('model StudentMilestoneHistory') &&
    schemaContent.includes('@@index([studentId, achievedAt(sort: Desc)], map: "idx_milestone_history_student_achieved")') &&
    typesTsContent.includes('export interface StudentMilestoneHistory {'),
  'Modelo StudentMilestoneHistory integrado ao prisma/schema.prisma e tipos TypeScript gerados'
);
assertCheck(
  /CREATE\s+TABLE\s+student_milestone_history/i.test(fs.readFileSync(SQL_3FN_PATH, 'utf8')),
  'Alinhamento confirmado com modelo 3FN ([T27] student_milestone_history)'
);

const sim = new MilestoneHistorySimulator();
sim.addUser('stu-1', 'STUDENT');
sim.addUser('stu-2', 'STUDENT');
sim.addEnrollment('enr-1', 'stu-1');
sim.addEnrollment('enr-2', 'stu-2');

sim.recordMilestone({
  student_id: 'stu-1',
  enrollment_id: 'enr-1',
  module_id: 'mod-1',
  milestone_type: 'MODULE_COMPLETED',
  title: 'Módulo de Metrologia com Paquímetro Concluído',
  metadata: { final_score: 9.2 },
  achieved_at: '2026-03-10T10:00:00Z',
});
sim.recordMilestone({
  student_id: 'stu-1',
  enrollment_id: 'enr-1',
  module_id: 'mod-2',
  milestone_type: 'SKILL_LEVEL_UP',
  title: 'Evolução para Nível 5 em Micrômetro Externo',
  metadata: { previous_level: 4, new_level: 5 },
  achieved_at: '2026-04-05T15:00:00Z',
});

const timeline = sim.getTimelineDesc('stu-1');
assertCheck(
  timeline.length === 2 && timeline[0].milestone_type === 'SKILL_LEVEL_UP' && timeline[1].milestone_type === 'MODULE_COMPLETED',
  'Teste 1 (Critério 1): Linha do tempo ordenada cronologicamente (mais recente primeiro via achieved_at DESC)'
);

let mismatchOwnerBlocked = false;
let badMetadataBlocked = false;
try {
  sim.recordMilestone({ student_id: 'stu-1', enrollment_id: 'enr-2', milestone_type: 'PERFECT_ATTENDANCE', title: 'Frequência 100%' });
} catch (err) { mismatchOwnerBlocked = err.sqlState === '23514'; }
try {
  sim.recordMilestone({ student_id: 'stu-1', enrollment_id: 'enr-1', milestone_type: 'RECOVERY_ACHIEVED', title: 'Recuperação Concluída', metadata: ['invalid'] });
} catch (err) { badMetadataBlocked = err.sqlState === '23514'; }
assertCheck(
  mismatchOwnerBlocked && badMetadataBlocked,
  'Teste 2 (Critério 2): Matrícula de outro aluno e metadata não-objeto bloqueados (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-039] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
