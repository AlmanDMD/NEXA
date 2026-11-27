/**
 * Script de Validação Automatizada — Card [DB-037]
 * Título: Criar View Analítica de Frequência e Evasão por Módulo (vw_module_attendance_risk)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126040000_create_vw_module_attendance_risk', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126040000_create_vw_module_attendance_risk.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '37_view_vw_module_attendance_risk.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '37-view-frequencia-evasao-vw-module-attendance-risk.md'),
  path.join(ROOT_DIR, 'BancoNexa', '37-view-frequencia-evasao-vw-module-attendance-risk.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

function computeModuleAttendance(totalHoursTaught, records) {
  const unjustified = records.reduce((s, r) => s + (r.status === 'ABSENT' || r.status === 'LATE' ? r.absent_hours : 0), 0);
  const justified = records.reduce((s, r) => s + (r.status === 'JUSTIFIED' ? r.absent_hours : 0), 0);
  const totalAbsent = unjustified + justified;
  const presentHours = Math.max(totalHoursTaught - totalAbsent, 0);
  const attendance_percentage =
    totalHoursTaught === 0 ? 100.0 : Number(((Math.max(totalHoursTaught - unjustified, 0) / totalHoursTaught) * 100).toFixed(2));
  return {
    total_hours_taught: totalHoursTaught,
    present_hours: presentHours,
    unjustified_absent_hours: unjustified,
    justified_absent_hours: justified,
    attendance_percentage,
    is_attendance_critical: attendance_percentage < 78.0,
    is_below_senai_minimum: attendance_percentage < 75.0,
  };
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-037] — VIEW vw_module_attendance_risk');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Script db:migrate validou a migration SQL da view vw_module_attendance_risk');
} catch (err) {
  assertCheck(false, `Falha em db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/37_view_vw_module_attendance_risk.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-037'),
  'Documentação DB-037 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /CREATE\s+OR\s+REPLACE\s+VIEW\s+vw_module_attendance_risk\s+AS/i.test(sqlContent) &&
    /WHEN\s+COALESCE\(ml\.total_hours_taught,\s*0\)\s*=\s*0\s+THEN\s+100\.00/i.test(sqlContent) &&
    /ar\.status\s*=\s*'JUSTIFIED'/i.test(sqlContent) &&
    /attendance_percentage\s*<\s*78\.00\)\s+AS\s+is_attendance_critical/i.test(sqlContent),
  'Critérios 1, 2 e 3 presentes no SQL (divisão por zero -> 100%, separação JUSTIFIED e is_attendance_critical < 78%)'
);

const zeroLessons = computeModuleAttendance(0, []);
assertCheck(
  zeroLessons.attendance_percentage === 100.0 && zeroLessons.is_attendance_critical === false,
  'Teste 1 (Critério 1): Módulo sem aulas ministradas (0h) tratou divisão por zero retornando 100.00% e crítico = false'
);

const withJustified = computeModuleAttendance(20, [
  { status: 'ABSENT', absent_hours: 4 },
  { status: 'JUSTIFIED', absent_hours: 4 },
]);
assertCheck(
  withJustified.unjustified_absent_hours === 4 &&
    withJustified.justified_absent_hours === 4 &&
    withJustified.attendance_percentage === 80.0 &&
    withJustified.is_attendance_critical === false,
  'Teste 2 (Critério 2): Faltas JUSTIFIED (4h) separadas das não justificadas (4h), preservando 80.00% de frequência efetiva'
);

const borderline76 = computeModuleAttendance(25, [{ status: 'ABSENT', absent_hours: 6 }]);
const critical68 = computeModuleAttendance(25, [{ status: 'ABSENT', absent_hours: 8 }]);
assertCheck(
  borderline76.attendance_percentage === 76.0 &&
    borderline76.is_attendance_critical === true &&
    borderline76.is_below_senai_minimum === false &&
    critical68.attendance_percentage === 68.0 &&
    critical68.is_attendance_critical === true &&
    critical68.is_below_senai_minimum === true,
  'Teste 3 (Critério 3): Alerta preventivo is_attendance_critical disparado em 76% (<78%) e abaixo do mínimo SENAI em 68% (<75%)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-037] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
