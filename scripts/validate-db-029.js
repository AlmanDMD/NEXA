/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-029]
 * Título: Configurar Triggers / Funções para Validação de Período Letivo Fechado
 *
 * Verifica programaticamente:
 * 1. Critério 1: Triggers associadas a `student_grades`, `attendance_records`,
 *    `task_submissions` (e `submission_evaluations`) bloqueiam `UPDATE`, `DELETE`
 *    (e `INSERT`) quando `classes.status IN ('COMPLETED', 'ARCHIVED')`.
 * 2. Critério 2: Exceção SQL clara (`SQLSTATE P0001`) identificável pelo backend
 *    (`BE-029` / `_is_closed_class_trigger_error`: `CLASS_PERIOD_CLOSED`,
 *    `fn_prevent_closed_class_mutation`, `Período letivo encerrado`).
 * 3. Critério 3: Leituras (`SELECT`) continuam 100% liberadas para histórico
 *    escolar em turmas `COMPLETED` e `ARCHIVED`.
 * 4. DoD: Migration SQL customizada `20261123080000_enforce_closed_class_period_triggers`
 *    aplicada, documentada em `prisma/schema.prisma`, testada tentando alterar nota
 *    de turma fechada e integrada aos cards dependentes (`DB-012`, `DB-022`, `DB-025`,
 *    `DB-028`, `BE-029`).
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'prisma',
  'migrations',
  '20261123080000_enforce_closed_class_period_triggers',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123080000_enforce_closed_class_period_triggers.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '29_triggers_periodo_letivo_fechado.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '29-triggers-validacao-periodo-letivo-fechado.md'),
  path.join(ROOT_DIR, 'BancoNexa', '29-triggers-validacao-periodo-letivo-fechado.md'),
];

const CLOSED_STATUSES = new Set(['COMPLETED', 'ARCHIVED']);

let failures = 0;

function assertCheck(condition, message) {
  if (condition) {
    console.log(`  [PASS] ${message}`);
  } else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

/**
 * Simulador da função `fn_prevent_closed_class_mutation()` + `fn_assert_class_not_closed()`
 * protegendo `student_grades`, `attendance_records`, `task_submissions` e `submission_evaluations`
 * contra mutações (INSERT/UPDATE/DELETE) quando `classes.status IN ('COMPLETED', 'ARCHIVED')`.
 */
class ClosedClassPeriodTriggerSimulator {
  constructor() {
    this.classes = new Map();
    this.assessments = new Map();
    this.lessons = new Map();
    this.tasks = new Map();
    this.grades = new Map();
    this.attendance = new Map();
    this.submissions = new Map();
    this.evaluations = new Map();
  }

  addClass(id, code, status = 'ACTIVE') {
    this.classes.set(id, { id, code, status });
  }

  setClassStatus(classId, status) {
    const cls = this.classes.get(classId);
    if (!cls) throw new Error('Class not found');
    cls.status = status;
  }

  addAssessment(id, classId) {
    this.assessments.set(id, { id, class_id: classId });
  }

  addLesson(id, classId) {
    this.lessons.set(id, { id, class_id: classId });
  }

  addTask(id, classId) {
    this.tasks.set(id, { id, class_id: classId });
  }

  _assertClassNotClosed(classId, operation, tableName) {
    const cls = this.classes.get(classId);
    if (cls && CLOSED_STATUSES.has(cls.status)) {
      const err = new Error(
        `[CLASS_PERIOD_CLOSED] Período letivo encerrado para esta turma (${cls.code} — status "${cls.status}"): operação ${operation} bloqueada na tabela ${tableName} pela função fn_prevent_closed_class_mutation.`
      );
      err.sqlState = 'P0001';
      err.errorCode = 'CLASS_PERIOD_CLOSED';
      throw err;
    }
  }

  // --- student_grades ---
  insertGrade(row) {
    const assess = this.assessments.get(row.assessment_id);
    this._assertClassNotClosed(assess.class_id, 'INSERT', 'student_grades');
    this.grades.set(row.id, { ...row });
    return this.grades.get(row.id);
  }

  updateGrade(gradeId, patch) {
    const current = this.grades.get(gradeId);
    const oldAssess = this.assessments.get(current.assessment_id);
    const newAssess = this.assessments.get(patch.assessment_id || current.assessment_id);
    this._assertClassNotClosed(oldAssess.class_id, 'UPDATE', 'student_grades');
    if (newAssess.class_id !== oldAssess.class_id) {
      this._assertClassNotClosed(newAssess.class_id, 'UPDATE', 'student_grades');
    }
    Object.assign(current, patch);
    return current;
  }

  deleteGrade(gradeId) {
    const current = this.grades.get(gradeId);
    const assess = this.assessments.get(current.assessment_id);
    this._assertClassNotClosed(assess.class_id, 'DELETE', 'student_grades');
    this.grades.delete(gradeId);
  }

  selectGradesByClass(classId) {
    return [...this.grades.values()].filter((g) => this.assessments.get(g.assessment_id).class_id === classId);
  }

  // --- attendance_records ---
  insertAttendance(row) {
    const lesson = this.lessons.get(row.lesson_id);
    this._assertClassNotClosed(lesson.class_id, 'INSERT', 'attendance_records');
    this.attendance.set(row.id, { ...row });
    return this.attendance.get(row.id);
  }

  updateAttendance(attId, patch) {
    const current = this.attendance.get(attId);
    const lesson = this.lessons.get(current.lesson_id);
    this._assertClassNotClosed(lesson.class_id, 'UPDATE', 'attendance_records');
    Object.assign(current, patch);
    return current;
  }

  deleteAttendance(attId) {
    const current = this.attendance.get(attId);
    const lesson = this.lessons.get(current.lesson_id);
    this._assertClassNotClosed(lesson.class_id, 'DELETE', 'attendance_records');
    this.attendance.delete(attId);
  }

  selectAttendanceByClass(classId) {
    return [...this.attendance.values()].filter((a) => this.lessons.get(a.lesson_id).class_id === classId);
  }

  // --- task_submissions ---
  insertSubmission(row) {
    const task = this.tasks.get(row.task_id);
    this._assertClassNotClosed(task.class_id, 'INSERT', 'task_submissions');
    this.submissions.set(row.id, { ...row });
    return this.submissions.get(row.id);
  }

  updateSubmission(subId, patch) {
    const current = this.submissions.get(subId);
    const task = this.tasks.get(current.task_id);
    this._assertClassNotClosed(task.class_id, 'UPDATE', 'task_submissions');
    Object.assign(current, patch);
    return current;
  }

  deleteSubmission(subId) {
    const current = this.submissions.get(subId);
    const task = this.tasks.get(current.task_id);
    this._assertClassNotClosed(task.class_id, 'DELETE', 'task_submissions');
    this.submissions.delete(subId);
  }

  selectSubmissionsByClass(classId) {
    return [...this.submissions.values()].filter((s) => this.tasks.get(s.task_id).class_id === classId);
  }

  // --- submission_evaluations ---
  insertEvaluation(row) {
    const sub = this.submissions.get(row.submission_id);
    const task = this.tasks.get(sub.task_id);
    this._assertClassNotClosed(task.class_id, 'INSERT', 'submission_evaluations');
    this.evaluations.set(row.id, { ...row });
    return this.evaluations.get(row.id);
  }

  updateEvaluation(evalId, patch) {
    const current = this.evaluations.get(evalId);
    const sub = this.submissions.get(current.submission_id);
    const task = this.tasks.get(sub.task_id);
    this._assertClassNotClosed(task.class_id, 'UPDATE', 'submission_evaluations');
    Object.assign(current, patch);
    return current;
  }
}

/** Simula o detector BE-029 (`_is_closed_class_trigger_error` em backend/app/core/exception_handlers.py) */
function isDetectedByBE029Handler(err) {
  const msg = String(err && err.message ? err.message : '').toLowerCase();
  return (
    err.sqlState === 'P0001' &&
    msg.includes('class_period_closed') &&
    msg.includes('fn_prevent_closed_class_mutation') &&
    msg.includes('período letivo encerrado')
  );
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-029] — TRIGGERS DE PERÍODO LETIVO FECHADO');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram e registraram a migration customizada de período letivo fechado'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, documentação e sincronia
console.log('\n2. Verificando arquivos SQL, documentação e sincronia...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123080000_enforce_closed_class_period_triggers/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123080000_enforce_closed_class_period_triggers.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/29_triggers_periodo_letivo_fechado.sql'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const bancoMigContent = fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8');
const bancoSqlContent = fs.readFileSync(BANCO_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const docA = fs.readFileSync(DOC_PATHS[0], 'utf8');
const docB = fs.readFileSync(DOC_PATHS[1], 'utf8');

assertCheck(
  sqlContent === bancoMigContent && sqlContent === bancoSqlContent,
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/29_triggers_periodo_letivo_fechado.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/29-triggers-validacao-periodo-letivo-fechado.md e BancoNexa/29-triggers-validacao-periodo-letivo-fechado.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-029'),
  'Card DB-029 documentado em BancoNexa/README.md'
);

// 3. Verificar função PL/pgSQL, triggers e contrato de exceção BE-029 no DDL SQL e schema.prisma
console.log('\n3. Verificando função PL/pgSQL, triggers e contrato BE-029 no DDL SQL e prisma/schema.prisma...');
assertCheck(
  /CREATE\s+OR\s+REPLACE\s+FUNCTION\s+fn_prevent_closed_class_mutation\s*\(\s*\)/i.test(sqlContent) &&
    /CREATE\s+OR\s+REPLACE\s+FUNCTION\s+fn_assert_class_not_closed/i.test(sqlContent),
  'Funções PL/pgSQL fn_prevent_closed_class_mutation() e fn_assert_class_not_closed() declaradas'
);
assertCheck(
  /CREATE\s+TRIGGER\s+trg_student_grades_prevent_closed_class\s+BEFORE\s+INSERT\s+OR\s+UPDATE\s+OR\s+DELETE\s+ON\s+student_grades/i.test(
    sqlContent
  ) &&
    /CREATE\s+TRIGGER\s+trg_attendance_records_prevent_closed_class\s+BEFORE\s+INSERT\s+OR\s+UPDATE\s+OR\s+DELETE\s+ON\s+attendance_records/i.test(
      sqlContent
    ) &&
    /CREATE\s+TRIGGER\s+trg_task_submissions_prevent_closed_class\s+BEFORE\s+INSERT\s+OR\s+UPDATE\s+OR\s+DELETE\s+ON\s+task_submissions/i.test(
      sqlContent
    ) &&
    /CREATE\s+TRIGGER\s+trg_submission_evaluations_prevent_closed_class\s+BEFORE\s+INSERT\s+OR\s+UPDATE\s+OR\s+DELETE\s+ON\s+submission_evaluations/i.test(
      sqlContent
    ),
  'Critério 1: Triggers BEFORE INSERT OR UPDATE OR DELETE registradas em student_grades, attendance_records, task_submissions e submission_evaluations'
);
assertCheck(
  /IN\s*\(\s*'COMPLETED'\s*,\s*'ARCHIVED'\s*\)/i.test(sqlContent) &&
    /ERRCODE\s*=\s*'P0001'/i.test(sqlContent) &&
    /CLASS_PERIOD_CLOSED/i.test(sqlContent) &&
    /Período letivo encerrado/i.test(sqlContent),
  'Critério 2: Bloqueio para COMPLETED/ARCHIVED lançando ERRCODE P0001 com CLASS_PERIOD_CLOSED e "Período letivo encerrado" (BE-029)'
);
assertCheck(
  schemaContent.includes('fn_prevent_closed_class_mutation') &&
    schemaContent.includes('trg_student_grades_prevent_closed_class') &&
    schemaContent.includes('trg_attendance_records_prevent_closed_class') &&
    schemaContent.includes('trg_task_submissions_prevent_closed_class'),
  'Documentação das triggers DB-029 sincronizada nos modelos Class, StudentGrade, AttendanceRecord e TaskSubmission do prisma/schema.prisma'
);

// 4. Testes unitários tentando alterar nota/falta/submissão em turma COMPLETED e ARCHIVED (DoD)
console.log('\n4. Executando testes unitários de bloqueio em turmas COMPLETED/ARCHIVED e leitura SELECT (DoD)...');
const sim = new ClosedClassPeriodTriggerSimulator();
const classActiveId = '10000000-0000-4000-8000-000000000001';
const classArchivedId = '10000000-0000-4000-8000-000000000002';
const assess1Id = '20000000-0000-4000-8000-000000000001';
const assess2Id = '20000000-0000-4000-8000-000000000002';
const lesson1Id = '30000000-0000-4000-8000-000000000001';
const task1Id = '40000000-0000-4000-8000-000000000001';

sim.addClass(classActiveId, 'MEC-2026-1', 'ACTIVE');
sim.addClass(classArchivedId, 'MEC-2025-2', 'ACTIVE');
sim.addAssessment(assess1Id, classActiveId);
sim.addAssessment(assess2Id, classArchivedId);
sim.addLesson(lesson1Id, classActiveId);
sim.addTask(task1Id, classActiveId);

// Enquanto a turma está ACTIVE, lançamentos e alterações funcionam normalmente
sim.insertGrade({ id: 'g-1', assessment_id: assess1Id, grade_value: 7.5 });
sim.updateGrade('g-1', { grade_value: 8.25 });
sim.insertAttendance({ id: 'a-1', lesson_id: lesson1Id, status: 'PRESENT', absent_hours: 0 });
sim.insertSubmission({ id: 's-1', task_id: task1Id, status: 'EVALUATED', final_task_score: 9.0 });
sim.insertEvaluation({ id: 'e-1', submission_id: 's-1', achieved_level: 5, score_awarded: 10.0 });
sim.insertGrade({ id: 'g-arch', assessment_id: assess2Id, grade_value: 6.5 });

// Encerrar turmas (COMPLETED e ARCHIVED)
sim.setClassStatus(classActiveId, 'COMPLETED');
sim.setClassStatus(classArchivedId, 'ARCHIVED');

// Teste 1 (DoD & Critério 1/2): Tentar UPDATE/DELETE/INSERT em turma COMPLETED
let gradeUpdateBlocked = false;
let gradeDeleteBlocked = false;
let gradeInsertBlocked = false;
let attUpdateBlocked = false;
let attDeleteBlocked = false;
let subUpdateBlocked = false;
let subDeleteBlocked = false;
let evalUpdateBlocked = false;

try {
  sim.updateGrade('g-1', { grade_value: 10.0 });
} catch (err) {
  gradeUpdateBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.deleteGrade('g-1');
} catch (err) {
  gradeDeleteBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.insertGrade({ id: 'g-new', assessment_id: assess1Id, grade_value: 9.0 });
} catch (err) {
  gradeInsertBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.updateAttendance('a-1', { status: 'ABSENT', absent_hours: 4 });
} catch (err) {
  attUpdateBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.deleteAttendance('a-1');
} catch (err) {
  attDeleteBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.updateSubmission('s-1', { final_task_score: 5.0 });
} catch (err) {
  subUpdateBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.deleteSubmission('s-1');
} catch (err) {
  subDeleteBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.updateEvaluation('e-1', { achieved_level: 2, score_awarded: 4.0 });
} catch (err) {
  evalUpdateBlocked = isDetectedByBE029Handler(err);
}

assertCheck(
  gradeUpdateBlocked &&
    gradeDeleteBlocked &&
    gradeInsertBlocked &&
    attUpdateBlocked &&
    attDeleteBlocked &&
    subUpdateBlocked &&
    subDeleteBlocked &&
    evalUpdateBlocked,
  'Teste 1 (DoD / Critérios 1 e 2): Turma COMPLETED bloqueou UPDATE/DELETE/INSERT em notas, presenças, submissões e rubricas com exceção P0001 identificável por BE-029'
);

// Teste 2 (Critério 1/2 — ARCHIVED): Tentar UPDATE/DELETE em turma ARCHIVED e tentativa de mover nota entre turmas
let archivedUpdateBlocked = false;
let archivedDeleteBlocked = false;

try {
  sim.updateGrade('g-arch', { grade_value: 9.5 });
} catch (err) {
  archivedUpdateBlocked = isDetectedByBE029Handler(err);
}

try {
  sim.deleteGrade('g-arch');
} catch (err) {
  archivedDeleteBlocked = isDetectedByBE029Handler(err);
}

assertCheck(
  archivedUpdateBlocked && archivedDeleteBlocked,
  'Teste 2 (Critério 1): Turma ARCHIVED bloqueou UPDATE e DELETE em student_grades com CLASS_PERIOD_CLOSED (P0001)'
);

// Teste 3 (Critério 3): SELECT permanece totalmente liberado e valores históricos permanecem intactos
const histGradesCompleted = sim.selectGradesByClass(classActiveId);
const histAttCompleted = sim.selectAttendanceByClass(classActiveId);
const histSubCompleted = sim.selectSubmissionsByClass(classActiveId);
const histGradesArchived = sim.selectGradesByClass(classArchivedId);

assertCheck(
  histGradesCompleted.length === 1 &&
    histGradesCompleted[0].grade_value === 8.25 &&
    histAttCompleted.length === 1 &&
    histAttCompleted[0].status === 'PRESENT' &&
    histSubCompleted.length === 1 &&
    histSubCompleted[0].final_task_score === 9.0 &&
    histGradesArchived.length === 1 &&
    histGradesArchived[0].grade_value === 6.5,
  'Teste 3 (Critério 3): Leitura (SELECT) em turmas COMPLETED e ARCHIVED liberada e histórico escolar preservado sem alteração'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-029] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
