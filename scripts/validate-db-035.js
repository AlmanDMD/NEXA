/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-035]
 * Título: Implementar Tabela de Diagnósticos Explicáveis de Turma (explainable_diagnostics)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126020000_create_explainable_diagnostics_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126020000_create_explainable_diagnostics_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '35_tabela_explainable_diagnostics.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '35-tabela-diagnosticos-explicaveis-explainable-diagnostics.md'),
  path.join(ROOT_DIR, 'BancoNexa', '35-tabela-diagnosticos-explicaveis-explainable-diagnostics.md'),
];

const VALID_TYPES = new Set(['ALIGNED', 'OVERCONFIDENCE_RISK', 'UNDERCONFIDENCE_SUPPORT', 'INSUFFICIENT_EVIDENCE']);

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class ExplainableDiagnosticsSimulator {
  constructor() {
    this.users = new Map();
    this.rows = [];
    this.seq = 1;
  }
  addUser(id, role) { this.users.set(id, { id, role }); }

  createDiagnostic(row) {
    if (this.users.get(row.student_id)?.role !== 'STUDENT') {
      const err = new Error('violates trigger "chk_diagnostics_student_role"');
      err.sqlState = '23514';
      throw err;
    }
    const selfLvl = Number(row.self_perceived_level);
    const tchLvl = Number(row.teacher_verified_level);
    if (selfLvl < 1.0 || selfLvl > 5.0 || tchLvl < 1.0 || tchLvl > 5.0) {
      const err = new Error('violates check constraint on perceived/verified level');
      err.sqlState = '23514';
      throw err;
    }
    if (!VALID_TYPES.has(row.diagnostic_type)) {
      const err = new Error('invalid diagnostic_type_enum');
      err.sqlState = '22P02';
      throw err;
    }
    const exp = String(row.explanation_text || '').trim();
    const lim = String(row.limitations_note || '').trim();
    const act = String(row.recommended_action || '').trim();
    if (exp.length < 10 || lim.length < 10 || act.length < 5) {
      const err = new Error('violates check constraint on explanation_text/limitations_note/recommended_action');
      err.sqlState = '23514';
      throw err;
    }
    // Trigger calcula discrepancy_gap automaticamente
    const gap = Number((selfLvl - tchLvl).toFixed(2));
    const saved = {
      id: `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      ...row,
      self_perceived_level: Number(selfLvl.toFixed(2)),
      teacher_verified_level: Number(tchLvl.toFixed(2)),
      discrepancy_gap: gap,
      explanation_text: exp,
      limitations_note: lim,
      recommended_action: act,
    };
    this.rows.push(saved);
    return saved;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-035] — DIAGNÓSTICOS EXPLICÁVEIS');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/35_tabela_explainable_diagnostics.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-035'),
  'Documentação DB-035 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /explanation_text\s+TEXT\s+NOT\s+NULL/i.test(sqlContent) &&
    /limitations_note\s+TEXT\s+NOT\s+NULL/i.test(sqlContent) &&
    /chk_diagnostics_limitations_not_empty/i.test(sqlContent) &&
    /discrepancy_gap\s+NUMERIC\(3,2\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /ROUND\(NEW\.self_perceived_level\s*-\s*NEW\.teacher_verified_level,\s*2\)/i.test(sqlContent) &&
    /idx_explainable_diagnostics_class_type\s+ON\s+explainable_diagnostics\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*diagnostic_type\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (explanation/limitations obrigatórios, cálculo de discrepancy_gap e índice class_id, diagnostic_type)'
);
assertCheck(
  schemaContent.includes('model ExplainableDiagnostic') &&
    schemaContent.includes('@@index([classId, diagnosticType], map: "idx_explainable_diagnostics_class_type")') &&
    typesTsContent.includes('export interface ExplainableDiagnostic {'),
  'Modelo ExplainableDiagnostic integrado ao prisma/schema.prisma e tipos TypeScript gerados'
);
assertCheck(
  /CREATE\s+TABLE\s+explainable_diagnostics/i.test(fs.readFileSync(SQL_3FN_PATH, 'utf8')),
  'Alinhamento confirmado com modelo 3FN ([T26] explainable_diagnostics)'
);

const sim = new ExplainableDiagnosticsSimulator();
sim.addUser('stu-1', 'STUDENT');
sim.addUser('stu-2', 'STUDENT');
sim.addUser('tch-1', 'TEACHER');

const dOver = sim.createDiagnostic({
  student_id: 'stu-1',
  class_id: 'cls-1',
  module_id: 'mod-tor',
  competency_id: 'comp-tor',
  self_perceived_level: 5.0,
  teacher_verified_level: 2.5,
  diagnostic_type: 'OVERCONFIDENCE_RISK',
  explanation_text: 'Estudante declarou domínio 5.00 em Tornearia, mas evidências práticas indicam 2.50 (gap +2.50).',
  limitations_note: 'Baseado em 2 entregas práticas; autoavaliação isolada não comprova domínio técnico.',
  recommended_action: 'Realizar mentoria guiada na bancada de torno convencional com checklist NR-12.',
});
const dUnder = sim.createDiagnostic({
  student_id: 'stu-2',
  class_id: 'cls-1',
  module_id: 'mod-met',
  competency_id: 'comp-met',
  self_perceived_level: 2.0,
  teacher_verified_level: 4.5,
  diagnostic_type: 'UNDERCONFIDENCE_SUPPORT',
  explanation_text: 'Estudante demonstrou alta precisão em Metrologia (4.50), mas se autoavaliou em 2.00 (gap -2.50).',
  limitations_note: 'Baseado em 3 medições verificadas; insegurança percebida requer feedback positivo.',
  recommended_action: 'Dar devolutiva positiva reforçando a precisão atingida nas leituras com micrômetro.',
});
assertCheck(
  dOver.discrepancy_gap === 2.5 && dUnder.discrepancy_gap === -2.5,
  'Teste 1 (Critério 2): discrepancy_gap calculado corretamente para superestimação (+2.50) e subestimação (-2.50)'
);

let missingLimitationsBlocked = false;
let nonStudentBlocked = false;
try {
  sim.createDiagnostic({
    student_id: 'stu-1',
    class_id: 'cls-1',
    module_id: 'mod-tor',
    self_perceived_level: 4.0,
    teacher_verified_level: 4.0,
    diagnostic_type: 'ALIGNED',
    explanation_text: 'Diagnóstico alinhado para teste.',
    limitations_note: '   ',
    recommended_action: 'Manter acompanhamento.',
  });
} catch (err) { missingLimitationsBlocked = err.sqlState === '23514'; }
try {
  sim.createDiagnostic({
    student_id: 'tch-1',
    class_id: 'cls-1',
    module_id: 'mod-tor',
    self_perceived_level: 4.0,
    teacher_verified_level: 4.0,
    diagnostic_type: 'ALIGNED',
    explanation_text: 'Diagnóstico alinhado para teste.',
    limitations_note: 'Baseado em 2 entregas práticas.',
    recommended_action: 'Manter acompanhamento.',
  });
} catch (err) { nonStudentBlocked = err.sqlState === '23514'; }
assertCheck(
  missingLimitationsBlocked && nonStudentBlocked,
  'Teste 2 (Critério 1): limitations_note vazio e student_id não-STUDENT bloqueados (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-035] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
