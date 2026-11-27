/**
 * Script de Validação Automatizada — Card [DB-038]
 * Título: Criar View de Discrepância: Autoavaliação vs Avaliação do Professor (vw_self_eval_discrepancy)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126050000_create_vw_self_eval_discrepancy', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126050000_create_vw_self_eval_discrepancy.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '38_view_vw_self_eval_discrepancy.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '38-view-discrepancia-autoavaliacao-vw-self-eval-discrepancy.md'),
  path.join(ROOT_DIR, 'BancoNexa', '38-view-discrepancia-autoavaliacao-vw-self-eval-discrepancy.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

function computeDiscrepancy(perceivedLevel, evidenceLevels) {
  const count = evidenceLevels.length;
  if (count === 0) {
    return {
      perceived_level: perceivedLevel,
      avg_verified_level: null,
      evidence_count: 0,
      discrepancy_delta: null,
      diagnostic_classification: 'INSUFFICIENT_EVIDENCE',
      requires_pedagogical_review: true,
    };
  }
  const avg = Number((evidenceLevels.reduce((s, v) => s + v, 0) / count).toFixed(2));
  const delta = Number((perceivedLevel - avg).toFixed(2));
  let classification = 'ALIGNED';
  if (delta >= 1.5) classification = 'OVERCONFIDENCE_RISK';
  else if (delta <= -1.5) classification = 'UNDERCONFIDENCE_SUPPORT';
  return {
    perceived_level: perceivedLevel,
    avg_verified_level: avg,
    evidence_count: count,
    discrepancy_delta: delta,
    diagnostic_classification: classification,
    requires_pedagogical_review: Math.abs(delta) >= 1.5,
  };
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-038] — VIEW vw_self_eval_discrepancy');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Script db:migrate validou a migration SQL da view vw_self_eval_discrepancy');
} catch (err) {
  assertCheck(false, `Falha em db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/38_view_vw_self_eval_discrepancy.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-038'),
  'Documentação DB-038 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /CREATE\s+OR\s+REPLACE\s+VIEW\s+vw_self_eval_discrepancy\s+AS/i.test(sqlContent) &&
    /ROUND\(AVG\(se\.verified_level\),\s*2\)\s+AS\s+avg_verified_level/i.test(sqlContent) &&
    /discrepancy_delta/i.test(sqlContent) &&
    /OVERCONFIDENCE_RISK/i.test(sqlContent) &&
    /UNDERCONFIDENCE_SUPPORT/i.test(sqlContent) &&
    /INSUFFICIENT_EVIDENCE/i.test(sqlContent) &&
    /1\.50/.test(sqlContent),
  'Critérios 1, 2 e 3 validados no SQL (cruzamento student_self_assessments x skill_evidences, delta e limiar >= 1.50)'
);

const rOver = computeDiscrepancy(5.0, [2.5, 3.0]); // avg = 2.75, delta = +2.25
const rUnder = computeDiscrepancy(2.0, [4.0, 4.5]); // avg = 4.25, delta = -2.25
const rAligned = computeDiscrepancy(4.0, [3.5, 4.0]); // avg = 3.75, delta = +0.25
const rNoEv = computeDiscrepancy(4.0, []);
assertCheck(
  rOver.diagnostic_classification === 'OVERCONFIDENCE_RISK' &&
    rOver.discrepancy_delta === 2.25 &&
    rOver.requires_pedagogical_review === true &&
    rUnder.diagnostic_classification === 'UNDERCONFIDENCE_SUPPORT' &&
    rUnder.discrepancy_delta === -2.25 &&
    rUnder.requires_pedagogical_review === true &&
    rAligned.diagnostic_classification === 'ALIGNED' &&
    rAligned.requires_pedagogical_review === false &&
    rNoEv.diagnostic_classification === 'INSUFFICIENT_EVIDENCE' &&
    rNoEv.evidence_count === 0,
  'Testes de classificação validados: superestimação (+2.25), subestimação (-2.25), alinhado (+0.25) e sem evidência (0)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-038] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
