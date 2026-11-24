/**
 * Script de Validação Automatizada e Testes de Idempotência — Card [DB-030]
 * Título: Criar Seed com Registro Realista de Frequências e Notas Parciais
 *
 * Verifica programaticamente:
 * 1. Existência de `prisma/seed.ts`, `BancoNexa/sql/30_seed_frequencias_notas_parciais.sql`,
 *    script `"db:seed"` em `package.json`, documentação sincronizada e entrada em `BancoNexa/README.md`.
 * 2. Critério 1: Cenários pedagógicos realistas presentes:
 *    - 30 estudantes matriculados em Mecânica (`MEC-2026-1` e `MEC-2026-2`)
 *    - 12 aulas ministradas (`class_lessons`)
 *    - Presenças variadas: `100.00%` (ótimo desempenho), `80.00%` (regular/entregas atrasadas),
 *      `76.00%` (24% faltas — próximo ao limite de 25%) e `68.00%` (risco crítico)
 *    - 6 tarefas práticas de oficina (`practical_tasks`), 18 rubricas (`task_criteria`),
 *      entregas `EVALUATED`, `SUBMITTED`, `LATE` e `PENDING`, avaliações por rubrica
 *      (`submission_evaluations`) e notas parciais (`student_grades`) com recuperação.
 * 3. Critério 2: Execução idempotente (`npm run db:seed` executado 2x consecutivas com saída
 *    determinística e 100% de instruções `ON CONFLICT ... DO UPDATE`).
 * 4. Critério 3: Zero uso de CPFs ou nomes/e-mails reais (100% `Estudante Demo XX` e `@aluno.nexa.local`).
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SEED_TS_PATH = path.join(ROOT_DIR, 'prisma', 'seed.ts');
const SEED_LOTE3_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '30_seed_frequencias_notas_parciais.sql');
const PACKAGE_JSON_PATH = path.join(ROOT_DIR, 'package.json');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '30-seed-frequencias-notas-parciais.md'),
  path.join(ROOT_DIR, 'BancoNexa', '30-seed-frequencias-notas-parciais.md'),
];

let failures = 0;

function assertCheck(condition, message) {
  if (condition) {
    console.log(`  [PASS] ${message}`);
  } else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-030] — SEED REALISTA LOTE 3 (30 ALUNOS)');
console.log('======================================================================\n');

// 1. Verificar artefatos, comando npm run db:seed e documentação
console.log('1. Verificando prisma/seed.ts, package.json e documentação...');
assertCheck(fs.existsSync(SEED_TS_PATH), 'Script prisma/seed.ts presente');
const pkg = JSON.parse(fs.readFileSync(PACKAGE_JSON_PATH, 'utf8'));
assertCheck(
  Boolean(pkg.scripts && pkg.scripts['db:seed'] && pkg.scripts['db:seed'].includes('prisma/seed.ts')),
  'Script "db:seed" configurado em package.json apontando para prisma/seed.ts'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8'),
  'Sincronia 100% idêntica entre docs/banco/30-seed-frequencias-notas-parciais.md e BancoNexa/30-seed-frequencias-notas-parciais.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-030'),
  'Card DB-030 documentado em BancoNexa/README.md'
);

// 2. Critério 2 & DoD: Execução idempotente 2x seguidas de `node prisma/seed.ts`
console.log('\n2. Verificando Critério 2 e DoD (execução idempotente 2x via npm run db:seed)...');
let run1Out = '';
let run2Out = '';
let sqlRun1 = '';
let sqlRun2 = '';
try {
  run1Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  sqlRun1 = fs.readFileSync(SEED_LOTE3_SQL_PATH, 'utf8');
  run2Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  sqlRun2 = fs.readFileSync(SEED_LOTE3_SQL_PATH, 'utf8');
  assertCheck(
    run1Out.includes('DB-030 SUCESSO') && run2Out.includes('DB-030 SUCESSO') && sqlRun1 === sqlRun2,
    'Critério 2: `npm run db:seed` executou 2x consecutivas com código 0 e SQL determinístico 100% idempotente'
  );
} catch (err) {
  assertCheck(false, `Falha ao executar prisma/seed.ts: ${err.message}`);
}

const seedSql = fs.existsSync(SEED_LOTE3_SQL_PATH) ? fs.readFileSync(SEED_LOTE3_SQL_PATH, 'utf8') : '';
const totalInserts = (seedSql.match(/INSERT\s+INTO\s+/gi) || []).length;
const totalUpserts = (seedSql.match(/ON\s+CONFLICT\s*\([^)]+\)\s+DO\s+UPDATE/gi) || []).length;
assertCheck(
  totalInserts > 500 && totalInserts === totalUpserts,
  `Idempotência SQL total: ${totalUpserts}/${totalInserts} instruções INSERT protegidas com ON CONFLICT ... DO UPDATE`
);

// 3. Verificar volumes exatos do Lote 3 solicitados na descrição do card
console.log('\n3. Verificando volumes do Lote 3 (30 alunos, 12 aulas, 6 tarefas práticas, rubricas e notas)...');
const userInserts = (seedSql.match(/INSERT\s+INTO\s+users\b/gi) || []).length;
const enrollmentInserts = (seedSql.match(/INSERT\s+INTO\s+enrollments\b/gi) || []).length;
const lessonInserts = (seedSql.match(/INSERT\s+INTO\s+class_lessons\b/gi) || []).length;
const attendanceInserts = (seedSql.match(/INSERT\s+INTO\s+attendance_records\b/gi) || []).length;
const taskInserts = (seedSql.match(/INSERT\s+INTO\s+practical_tasks\b/gi) || []).length;
const criteriaInserts = (seedSql.match(/INSERT\s+INTO\s+task_criteria\b/gi) || []).length;
const submissionInserts = (seedSql.match(/INSERT\s+INTO\s+task_submissions\b/gi) || []).length;
const evaluationInserts = (seedSql.match(/INSERT\s+INTO\s+submission_evaluations\b/gi) || []).length;
const assessmentInserts = (seedSql.match(/INSERT\s+INTO\s+academic_assessments\b/gi) || []).length;
const gradeInserts = (seedSql.match(/INSERT\s+INTO\s+student_grades\b/gi) || []).length;

assertCheck(
  userInserts === 30 && enrollmentInserts === 30,
  `30 alunos fictícios matriculados nas turmas de Mecânica (${userInserts}/30 usuários, ${enrollmentInserts}/30 matrículas)`
);
assertCheck(lessonInserts === 12, `12 aulas ministradas populadas em class_lessons (${lessonInserts}/12)`);
assertCheck(
  attendanceInserts === 186,
  `186 registros de presença populados em attendance_records (18×7 + 12×5) (${attendanceInserts}/186)`
);
assertCheck(
  taskInserts === 6 && criteriaInserts === 18,
  `6 tarefas práticas em practical_tasks e 18 rubricas técnicas em task_criteria (${taskInserts}/6, ${criteriaInserts}/18)`
);
assertCheck(
  submissionInserts === 96 && evaluationInserts >= 150,
  `${submissionInserts} submissões práticas em task_submissions e ${evaluationInserts} avaliações por rubrica em submission_evaluations`
);
assertCheck(
  assessmentInserts === 4 && gradeInserts === 60,
  `4 avaliações formativas (academic_assessments) e 60 notas parciais (student_grades) populadas (${assessmentInserts}/4, ${gradeInserts}/60)`
);

// 4. Critério 1: Cenários pedagógicos realistas (ótimo desempenho 100%, regular/atrasos 80%, limite faltas 76% e risco 68%)
console.log('\n4. Verificando Critério 1 (cenários realistas: 100%, 80%, limite 25% faltas, 68% risco e entregas atrasadas)...');
const has100Attendance = /'ACTIVE'::enrollment_status_enum,\s*[0-9.]+,\s*100\.00/.test(seedSql);
const has80Attendance = /'ACTIVE'::enrollment_status_enum,\s*[0-9.]+,\s*80\.00/.test(seedSql);
const has76Attendance = /'ACTIVE'::enrollment_status_enum,\s*[0-9.]+,\s*76\.00/.test(seedSql);
const has68Attendance = /'ACTIVE'::enrollment_status_enum,\s*[0-9.]+,\s*68\.00/.test(seedSql);
const hasEvaluatedSub = /'EVALUATED'::submission_status_enum/.test(seedSql);
const hasSubmittedSub = /'SUBMITTED'::submission_status_enum/.test(seedSql);
const hasLateSub = /'LATE'::submission_status_enum/.test(seedSql);
const hasPendingSub = /'PENDING'::submission_status_enum/.test(seedSql);
const hasRecoveryGrade = /INSERT\s+INTO\s+student_grades[\s\S]*?,\s*(?:5\.40|7\.20)\s*,/.test(seedSql);

assertCheck(
  has100Attendance && has80Attendance && has76Attendance && has68Attendance,
  'Perfis reais de presença gerados: 100% (ótimo), 80% (regular), 76% (próximo ao limite de 25% de faltas) e 68% (risco)'
);
assertCheck(
  hasEvaluatedSub && hasSubmittedSub && hasLateSub && hasPendingSub && hasRecoveryGrade,
  'Cenários reais de entregas (EVALUATED, SUBMITTED, LATE, PENDING) e notas com recuperação (recovery_grade) presentes'
);

// 5. Critério 3: Zero uso de CPFs ou nomes/e-mails reais
console.log('\n5. Verificando Critério 3 (zero CPFs, zero nomes reais e domínios 100% fictícios)...');
const studentEmails = [...seedSql.matchAll(/INSERT\s+INTO\s+users[\s\S]*?VALUES\s*\('([^']+)'/g)].map((m) => m[1]);
const studentNames = [...seedSql.matchAll(/INSERT\s+INTO\s+user_profiles[\s\S]*?SELECT\s+u\.id,\s*'([^']+)'/g)].map(
  (m) => m[1]
);
const allAnonymousEmails =
  studentEmails.length === 30 && studentEmails.every((e) => /^estudante\.demo\d{2}@aluno\.nexa\.local$/.test(e));
const allAnonymousNames =
  studentNames.length === 30 && studentNames.every((n) => /^Estudante Demo \d{2}$/.test(n));
const hasFormattedCpf = /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/.test(seedSql);
const hasRealEmailDomains = /@(gmail|hotmail|outlook|yahoo|icloud|uol|bol)\./i.test(seedSql);

assertCheck(
  allAnonymousEmails && allAnonymousNames && !hasFormattedCpf && !hasRealEmailDomains,
  'Critério 3: 30/30 estudantes com nomes sintéticos (Estudante Demo 01..30), e-mails @aluno.nexa.local e 0 CPFs reais'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-030] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
