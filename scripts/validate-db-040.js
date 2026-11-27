/**
 * Script de Validação Automatizada — Card [DB-040]
 * Título: Criar Seed de Diagnósticos e Alertas Simulados para Validação de Dashboards
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SEED_LOTE4_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '40_seed_diagnosticos_alertas_lote4.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '40-seed-diagnosticos-alertas-lote4.md'),
  path.join(ROOT_DIR, 'BancoNexa', '40-seed-diagnosticos-alertas-lote4.md'),
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
console.log('🧪 VALIDAÇÃO DO CARD [DB-040] — SEED DIAGNÓSTICOS & ALERTAS (LOTE 4)');
console.log('======================================================================\n');

// 1. Executar node prisma/seed.ts 2x consecutivas medindo tempo (< 5s) e comprovando idempotência
const t0 = Date.now();
let run1Out = '';
let run2Out = '';
let sql1 = '';
let sql2 = '';
let run1Ms = 0;
try {
  run1Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  run1Ms = Date.now() - t0;
  sql1 = fs.readFileSync(SEED_LOTE4_SQL_PATH, 'utf8');
  run2Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  sql2 = fs.readFileSync(SEED_LOTE4_SQL_PATH, 'utf8');
  assertCheck(
    run1Out.includes('DB-040 SUCESSO') && run2Out.includes('DB-040 SUCESSO') && sql1 === sql2,
    'Critério 3: `npm run db:seed` executado 2x consecutivas de forma 100% idempotente e determinística'
  );
  assertCheck(run1Ms < 5000, `DoD: Seed completo dos Lotes 2, 3 e 4 concluído em ${run1Ms}ms (< 5000ms)`);
} catch (err) {
  assertCheck(false, `Falha ao executar prisma/seed.ts: ${err.message}`);
}

assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-040'),
  'Documentação DB-040 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);

const sql = fs.existsSync(SEED_LOTE4_SQL_PATH) ? fs.readFileSync(SEED_LOTE4_SQL_PATH, 'utf8') : '';
const formsCount = (sql.match(/INSERT\s+INTO\s+self_assessment_forms\b/gi) || []).length;
const selfAssessCount = (sql.match(/INSERT\s+INTO\s+student_self_assessments\b/gi) || []).length;
const evidencesCount = (sql.match(/INSERT\s+INTO\s+skill_evidences\b/gi) || []).length;
const alertsCount = (sql.match(/INSERT\s+INTO\s+academic_alerts\b/gi) || []).length;
const diagnosticsCount = (sql.match(/INSERT\s+INTO\s+explainable_diagnostics\b/gi) || []).length;
const milestonesCount = (sql.match(/INSERT\s+INTO\s+student_milestone_history\b/gi) || []).length;
const upsertCount = (sql.match(/ON\s+CONFLICT\s*\([^)]+\)\s+DO\s+UPDATE/gi) || []).length;

assertCheck(
  formsCount >= 4 && selfAssessCount >= 16 && evidencesCount >= 12 && milestonesCount >= 6,
  `Critério 1: Populados ${formsCount} formulários, ${selfAssessCount} autoavaliações, ${evidencesCount} evidências e ${milestonesCount} marcos`
);
assertCheck(
  alertsCount === 8 &&
    sql.includes("'LOW'::risk_level_enum") &&
    sql.includes("'MODERATE'::risk_level_enum") &&
    sql.includes("'HIGH'::risk_level_enum") &&
    sql.includes("'CRITICAL'::risk_level_enum"),
  `Critério 1: Exatamente ${alertsCount}/8 alertas acadêmicos explicáveis cobrindo LOW, MODERATE, HIGH e CRITICAL`
);
assertCheck(
  diagnosticsCount === 10 &&
    sql.includes("'OVERCONFIDENCE_RISK'::diagnostic_type_enum") &&
    sql.includes("'UNDERCONFIDENCE_SUPPORT'::diagnostic_type_enum") &&
    sql.includes("'ALIGNED'::diagnostic_type_enum") &&
    /Metrologia/i.test(sql) &&
    /Tornearia/i.test(sql),
  `Critério 2: Exatamente ${diagnosticsCount}/10 diagnósticos comparativos incluindo divergências reais em Metrologia e Tornearia`
);
assertCheck(
  upsertCount >= 60,
  `Critério 3: ${upsertCount} instruções UPSERT (ON CONFLICT ... DO UPDATE) idempotentes em 40_seed_diagnosticos_alertas_lote4.sql`
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-040] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
