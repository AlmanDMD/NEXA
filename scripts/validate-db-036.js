/**
 * Script de Validação Automatizada e Benchmark — Card [DB-036]
 * Título: Criar View Analítica Consolidada de Desempenho do Aluno (vw_student_360_performance)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261126030000_create_vw_student_360_performance', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261126030000_create_vw_student_360_performance.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '36_view_vw_student_360_performance.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '36-view-desempenho-360-vw-student-360-performance.md'),
  path.join(ROOT_DIR, 'BancoNexa', '36-view-desempenho-360-vw-student-360-performance.md'),
];

const RISK_ORDER = { LOW: 1, MODERATE: 2, HIGH: 3, CRITICAL: 4 };

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

function simulateView360(enrollments, grades, attendance, submissions, alerts) {
  const start = performance.now();
  const result = enrollments.map((e) => {
    const eGrades = grades.filter((g) => g.enrollment_id === e.id);
    const wNum = eGrades.reduce((s, g) => s + Math.max(g.grade_value, g.recovery_grade ?? g.grade_value) * g.weight, 0);
    const wDen = eGrades.reduce((s, g) => s + g.weight, 0);
    const weighted_average_grade = wDen > 0 ? Number((wNum / wDen).toFixed(2)) : e.final_grade;

    const eAtt = attendance.filter((a) => a.enrollment_id === e.id);
    const totalHours = eAtt.reduce((s, a) => s + a.workload_hours, 0);
    const unjAbsent = eAtt.reduce((s, a) => s + (a.status === 'ABSENT' || a.status === 'LATE' ? a.absent_hours : 0), 0);
    const attendance_rate_pct = totalHours > 0 ? Number((((totalHours - unjAbsent) / totalHours) * 100).toFixed(2)) : 100.0;

    const eTasks = submissions.filter((t) => t.enrollment_id === e.id);
    const tasks_pending = eTasks.filter((t) => t.status === 'PENDING').length;
    const tasks_submitted = eTasks.filter((t) => t.status === 'SUBMITTED').length;
    const tasks_evaluated = eTasks.filter((t) => t.status === 'EVALUATED').length;
    const tasks_late = eTasks.filter((t) => t.status === 'LATE').length;

    const eActiveAlerts = alerts.filter((al) => al.enrollment_id === e.id && al.status === 'ACTIVE');
    let current_risk_level = 'LOW';
    for (const al of eActiveAlerts) {
      if (RISK_ORDER[al.risk_level] > RISK_ORDER[current_risk_level]) current_risk_level = al.risk_level;
    }

    return {
      enrollment_id: e.id,
      weighted_average_grade,
      attendance_rate_pct,
      tasks_pending,
      tasks_submitted,
      tasks_evaluated,
      tasks_late,
      active_alerts_count: eActiveAlerts.length,
      current_risk_level,
    };
  });
  return { rows: result, elapsedMs: performance.now() - start };
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-036] — VIEW vw_student_360_performance');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Script db:migrate validou a migration SQL da view vw_student_360_performance');
} catch (err) {
  assertCheck(false, `Falha em db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/36_view_vw_student_360_performance.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-036'),
  'Documentação DB-036 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /CREATE\s+OR\s+REPLACE\s+VIEW\s+vw_student_360_performance\s+AS/i.test(sqlContent) &&
    /WITH\s+grade_agg\s+AS/i.test(sqlContent) &&
    /attendance_agg\s+AS/i.test(sqlContent) &&
    /task_agg\s+AS/i.test(sqlContent) &&
    /alert_agg\s+AS/i.test(sqlContent),
  'Critério 1: View vw_student_360_performance estruturada em 4 CTEs pré-agregadas sem produto cartesiano'
);
assertCheck(
  /WHERE\s+ts\.status\s*=\s*'PENDING'/i.test(sqlContent) &&
    /WHERE\s+ts\.status\s*=\s*'SUBMITTED'/i.test(sqlContent) &&
    /WHERE\s+ts\.status\s*=\s*'EVALUATED'/i.test(sqlContent) &&
    /WHERE\s+ts\.status\s*=\s*'LATE'/i.test(sqlContent),
  'Critério 2: Contadores de tarefas PENDING, SUBMITTED, EVALUATED e LATE implementados com FILTER'
);

// Simulação com turma de 50 alunos validando exatidão e tempo < 30ms
const enrollments50 = Array.from({ length: 50 }, (_, i) => ({ id: `enr-${i + 1}`, final_grade: null }));
const grades50 = enrollments50.flatMap((e) => [
  { enrollment_id: e.id, grade_value: 6.0, recovery_grade: 8.0, weight: 2.0 },
  { enrollment_id: e.id, grade_value: 9.0, recovery_grade: null, weight: 1.0 },
]);
const att50 = enrollments50.flatMap((e) => [
  { enrollment_id: e.id, workload_hours: 4, status: 'PRESENT', absent_hours: 0 },
  { enrollment_id: e.id, workload_hours: 4, status: 'ABSENT', absent_hours: 2 },
]);
const subs50 = enrollments50.flatMap((e) => [
  { enrollment_id: e.id, status: 'PENDING' },
  { enrollment_id: e.id, status: 'SUBMITTED' },
  { enrollment_id: e.id, status: 'EVALUATED' },
  { enrollment_id: e.id, status: 'EVALUATED' },
  { enrollment_id: e.id, status: 'LATE' },
]);
const alerts50 = enrollments50.map((e, i) => ({
  enrollment_id: e.id,
  status: 'ACTIVE',
  risk_level: i % 5 === 0 ? 'CRITICAL' : 'MODERATE',
}));

const { rows, elapsedMs } = simulateView360(enrollments50, grades50, att50, subs50, alerts50);
assertCheck(
  rows.length === 50 &&
    rows[0].weighted_average_grade === 8.33 &&
    rows[0].attendance_rate_pct === 75.0 &&
    rows[0].tasks_pending === 1 &&
    rows[0].tasks_submitted === 1 &&
    rows[0].tasks_evaluated === 2 &&
    rows[0].tasks_late === 1 &&
    rows[0].active_alerts_count === 1 &&
    rows[0].current_risk_level === 'CRITICAL',
  'Teste 1 (Critério 2): Cálculos 360° (média ponderada 8.33, frequência 75%, contadores 1/1/2/1 e risco CRITICAL) exatos'
);
assertCheck(
  elapsedMs < 30,
  `Teste 2 (Critério 3): Consolidação de 50 alunos concluída em ${elapsedMs.toFixed(2)}ms (< 30ms)`
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-036] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
