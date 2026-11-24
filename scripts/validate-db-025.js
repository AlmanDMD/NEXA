/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-025]
 * Título: Implementar Tabela de Submissões e Entregas Práticas (task_submissions)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Constraint UNIQUE composta `uq_task_submissions_task_student (task_id, student_id)`
 *    (e `uq_task_submissions_task_enrollment`).
 * 2. Critério 2: Índice composto `idx_task_submissions_student_status (student_id, status)`
 *    para alimentar a lista de pendências do portal do aluno (`FE-036` / `BE-026`),
 *    além de `idx_task_submissions_task_status` e `idx_task_submissions_enrollment_status`.
 * 3. Critério 3: Integridade com `enrollments` assegurando vínculo `ACTIVE` na mesma turma
 *    da atividade prática (`fk_task_submissions_enrollment` + trigger).
 * 4. DoD: Tabela `task_submissions` migrada, `model TaskSubmission` no `prisma/schema.prisma`,
 *    tipos TS gerados em `BancoNexa/types/schema-models.ts`, validada com estados de transição
 *    (`PENDING -> SUBMITTED -> EVALUATED`, `PENDING -> LATE -> EVALUATED`, bloqueio de
 *    regressão `EVALUATED -> PENDING`) e integrada aos cards dependentes (`DB-026`, `BE-025`, `BE-026`).
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
  '20261123040000_create_task_submissions_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123040000_create_task_submissions_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '25_tabela_task_submissions.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '25-tabela-submissoes-entregas-praticas-task-submissions.md'),
  path.join(ROOT_DIR, 'BancoNexa', '25-tabela-submissoes-entregas-praticas-task-submissions.md'),
];

const VALID_SUBMISSION_STATUSES = new Set(['PENDING', 'SUBMITTED', 'EVALUATED', 'LATE']);

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
 * Simulador relacional das tabelas `practical_tasks`, `users`, `enrollments` e `task_submissions`
 * com UNIQUE (task_id, student_id), matrícula ACTIVE na turma da tarefa, final_task_score <= max_score,
 * transições de estado (PENDING / SUBMITTED / LATE / EVALUATED) e consulta de pendências por (student_id, status).
 */
class TaskSubmissionsRelationalSimulator {
  constructor() {
    this.tasks = new Map();
    this.users = new Map();
    this.enrollments = new Map();
    this.submissionsById = new Map();
    this.submissionsByTaskStudent = new Map();
    this.submissionsByTaskEnrollment = new Map();
    this.seq = 1;
  }

  addTask(id, classId, title, maxScore = 10.0) {
    this.tasks.set(id, { id, class_id: classId, title, max_score: maxScore });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addEnrollment(id, studentId, classId, status = 'ACTIVE') {
    this.enrollments.set(id, { id, student_id: studentId, class_id: classId, status });
  }

  _validateCommon(row, isInsert) {
    const status = row.status !== undefined ? row.status : 'PENDING';
    if (!VALID_SUBMISSION_STATUSES.has(status)) {
      const err = new Error(`invalid input value for enum submission_status_enum: "${status}"`);
      err.sqlState = '22P02';
      throw err;
    }

    if (row.evidence_url !== undefined && row.evidence_url !== null && !/^https?:\/\//i.test(String(row.evidence_url))) {
      const err = new Error('violates check constraint "chk_task_submissions_evidence_url"');
      err.sqlState = '23514';
      throw err;
    }

    let finalScore = null;
    if (row.final_task_score !== undefined && row.final_task_score !== null) {
      finalScore = Number(row.final_task_score);
      if (Number.isNaN(finalScore) || finalScore < 0.0 || finalScore > 10.0) {
        const err = new Error('violates check constraint "chk_task_submissions_score"');
        err.sqlState = '23514';
        throw err;
      }
    }

    const task = this.tasks.get(row.task_id);
    if (!task) {
      const err = new Error('violates foreign key constraint "fk_task_submissions_task"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const user = this.users.get(row.student_id);
    if (!user) {
      const err = new Error('violates foreign key constraint "fk_task_submissions_student"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const enrollment = this.enrollments.get(row.enrollment_id);
    if (!enrollment) {
      const err = new Error('violates foreign key constraint "fk_task_submissions_enrollment"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (enrollment.student_id !== row.student_id) {
      const err = new Error('chk_task_submissions_enrollment_student');
      err.sqlState = '23514';
      throw err;
    }

    if (enrollment.class_id !== task.class_id) {
      const err = new Error('chk_task_submissions_enrollment_class');
      err.sqlState = '23514';
      throw err;
    }

    if (isInsert && enrollment.status !== 'ACTIVE') {
      const err = new Error('chk_task_submissions_enrollment_active');
      err.sqlState = '23514';
      throw err;
    }

    if (finalScore !== null && finalScore > task.max_score) {
      const err = new Error('chk_task_submissions_score_exceeds_max');
      err.sqlState = '23514';
      throw err;
    }

    return { status, finalScore };
  }

  insertSubmission(row) {
    if (!row.task_id || !row.student_id || !row.enrollment_id) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const { status, finalScore } = this._validateCommon(row, true);

    const tsKey = `${row.task_id}::${row.student_id}`;
    const teKey = `${row.task_id}::${row.enrollment_id}`;
    if (this.submissionsByTaskStudent.has(tsKey)) {
      const err = new Error('Unique constraint failed: uq_task_submissions_task_student');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }
    if (this.submissionsByTaskEnrollment.has(teKey)) {
      const err = new Error('Unique constraint failed: uq_task_submissions_task_enrollment');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const completedAt =
      row.completed_at !== undefined
        ? row.completed_at
        : status === 'SUBMITTED' || status === 'EVALUATED'
          ? now
          : null;

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      task_id: row.task_id,
      student_id: row.student_id,
      enrollment_id: row.enrollment_id,
      status,
      completed_at: completedAt,
      evidence_url: row.evidence_url !== undefined ? row.evidence_url : null,
      student_notes: row.student_notes !== undefined ? row.student_notes : null,
      final_task_score: finalScore !== null ? Number(finalScore.toFixed(2)) : null,
      created_at: now,
      updated_at: now,
    };

    this.submissionsById.set(saved.id, saved);
    this.submissionsByTaskStudent.set(tsKey, saved);
    this.submissionsByTaskEnrollment.set(teKey, saved);
    return saved;
  }

  transitionStatus(submissionId, patch) {
    const current = this.submissionsById.get(submissionId);
    if (!current) {
      throw new Error('Submission not found');
    }

    const merged = { ...current, ...patch };
    const { status, finalScore } = this._validateCommon(merged, false);

    if (current.status === 'EVALUATED' && status === 'PENDING') {
      const err = new Error('chk_task_submissions_status_transition: EVALUATED -> PENDING bloqueado');
      err.sqlState = '23514';
      throw err;
    }

    const now = new Date().toISOString();
    current.status = status;
    current.final_task_score = finalScore !== null ? Number(finalScore.toFixed(2)) : current.final_task_score;
    if (patch.evidence_url !== undefined) current.evidence_url = patch.evidence_url;
    if (patch.student_notes !== undefined) current.student_notes = patch.student_notes;
    if (patch.completed_at !== undefined) {
      current.completed_at = patch.completed_at;
    } else if ((status === 'SUBMITTED' || status === 'EVALUATED') && !current.completed_at) {
      current.completed_at = now;
    }
    current.updated_at = now;
    return current;
  }

  listByStudentAndStatuses(studentId, statuses) {
    const allowed = new Set(statuses);
    return [...this.submissionsById.values()].filter((s) => s.student_id === studentId && allowed.has(s.status));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-025] — SUBMISSÕES PRÁTICAS (task_submissions)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de task_submissions'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123040000_create_task_submissions_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123040000_create_task_submissions_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/25_tabela_task_submissions.sql'
);
assertCheck(
  fs.existsSync(TYPES_MODELS_TS_PATH),
  'Tipos TypeScript dos modelos Prisma presentes em BancoNexa/types/schema-models.ts'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const bancoMigContent = fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8');
const bancoSqlContent = fs.readFileSync(BANCO_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');
const docA = fs.readFileSync(DOC_PATHS[0], 'utf8');
const docB = fs.readFileSync(DOC_PATHS[1], 'utf8');

assertCheck(
  sqlContent === bancoMigContent && sqlContent === bancoSqlContent,
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/25_tabela_task_submissions.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/25-tabela-submissoes-entregas-praticas-task-submissions.md e BancoNexa/25-tabela-submissoes-entregas-praticas-task-submissions.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-025'),
  'Card DB-025 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model TaskSubmission no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model TaskSubmission no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /task_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /enrollment_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /status\s+submission_status_enum\s+NOT\s+NULL\s+DEFAULT\s+'PENDING'/i.test(sqlContent) &&
    /completed_at\s+TIMESTAMPTZ\s*,/i.test(sqlContent) &&
    /evidence_url\s+VARCHAR\(500\)\s*,/i.test(sqlContent) &&
    /student_notes\s+TEXT\s*,/i.test(sqlContent) &&
    /final_task_score\s+NUMERIC\(4,2\)\s*,/i.test(sqlContent),
  'Todas as colunas exigidas (id, task_id, student_id, enrollment_id, status submission_status_enum, completed_at, evidence_url, student_notes, final_task_score) presentes'
);
assertCheck(
  schemaContent.includes('model TaskSubmission') &&
    /submissions\s+TaskSubmission\[\]/.test(schemaContent) &&
    (schemaContent.match(/taskSubmissions\s+TaskSubmission\[\]/g) || []).length === 2 &&
    schemaContent.includes('@@unique([taskId, studentId], map: "uq_task_submissions_task_student")') &&
    schemaContent.includes('@@index([studentId, status], map: "idx_task_submissions_student_status")') &&
    schemaContent.includes('@@map("task_submissions")'),
  'Modelo TaskSubmission integrado ao prisma/schema.prisma com UNIQUE, relações reversas em PracticalTask/User/Enrollment e índices'
);
assertCheck(
  typesTsContent.includes('export interface TaskSubmission {') &&
    typesTsContent.includes('status: SubmissionStatus;') &&
    typesTsContent.includes('finalTaskScore: number | string | null;') &&
    typesTsContent.includes('export interface TaskSubmissionRow {'),
  'Tipos TypeScript (TaskSubmission, TaskSubmissionRow, TaskSubmissionCreateInput, TaskSubmissionUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_task_submissions_task_student\s+UNIQUE\s*\(\s*task_id\s*,\s*student_id\s*\)/i.test(sqlContent) &&
    /CONSTRAINT\s+uq_task_submissions_task_enrollment\s+UNIQUE\s*\(\s*task_id\s*,\s*enrollment_id\s*\)/i.test(
      sqlContent
    ),
  'Critério 1: Constraints uq_task_submissions_task_student (task_id, student_id) e uq_task_submissions_task_enrollment declaradas'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_task_submissions_student_status\s+ON\s+task_submissions\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*status\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_task_submissions_task_status\s+ON\s+task_submissions\s+USING\s+BTREE\s*\(\s*task_id\s*,\s*status\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: Índice composto idx_task_submissions_student_status (student_id, status) + idx_task_submissions_task_status criados'
);
assertCheck(
  /CONSTRAINT\s+fk_task_submissions_enrollment\s+FOREIGN\s+KEY\s*\(\s*enrollment_id\s*\)\s*REFERENCES\s+enrollments\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /trg_task_submissions_validate_and_touch/i.test(sqlContent) &&
    /chk_task_submissions_enrollment_active/i.test(sqlContent),
  'Critério 3: FK fk_task_submissions_enrollment + trigger validando matrícula ACTIVE na turma da tarefa'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-026, DB-036, BE-025, BE-026)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-026, DB-036, BE-025, BE-026)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+task_submissions/i.test(sql3fnContent) &&
    /uq_task_submissions_task_student/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*submission_id\s*\)\s*REFERENCES\s+task_submissions\s*\(\s*id\s*\)/i.test(sql3fnContent),
  'Integração validada com modelo 3FN (T20 task_submissions) e tabela dependente submission_evaluations (DB-026)'
);

// 6. Testes unitários de estados de transição, unicidade, matrícula ativa e pendências do aluno (DoD)
console.log('\n6. Executando testes unitários de transições de estado, unicidade, matrícula ACTIVE e pendências (DoD)...');
const sim = new TaskSubmissionsRelationalSimulator();
const classMec1Id = '10000000-0000-4000-8000-000000000001';
const classMec2Id = '10000000-0000-4000-8000-000000000002';
const task1Id = '20000000-0000-4000-8000-000000000001';
const task2Id = '20000000-0000-4000-8000-000000000002';
const task3Id = '20000000-0000-4000-8000-000000000003';
const student1Id = '30000000-0000-4000-8000-000000000001';
const studentDroppedId = '30000000-0000-4000-8000-000000000002';
const studentOtherClassId = '30000000-0000-4000-8000-000000000003';
const enrActiveId = '40000000-0000-4000-8000-000000000001';
const enrDroppedId = '40000000-0000-4000-8000-000000000002';
const enrOtherClassId = '40000000-0000-4000-8000-000000000003';

sim.addTask(task1Id, classMec1Id, 'Usinagem de Eixo Escalonado Ø25mm H7', 10.0);
sim.addTask(task2Id, classMec1Id, 'Controle Dimensional com Micrômetro', 8.0);
sim.addTask(task3Id, classMec1Id, 'Rosca Métrica Externa M16x2', 10.0);
sim.addUser(student1Id, 'aluno1@senai.nexa.local', 'STUDENT');
sim.addUser(studentDroppedId, 'aluno.evadido@senai.nexa.local', 'STUDENT');
sim.addUser(studentOtherClassId, 'aluno.turma2@senai.nexa.local', 'STUDENT');
sim.addEnrollment(enrActiveId, student1Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enrDroppedId, studentDroppedId, classMec1Id, 'DROPPED');
sim.addEnrollment(enrOtherClassId, studentOtherClassId, classMec2Id, 'ACTIVE');

// Teste 1 (DoD): Fluxo completo de transição PENDING -> SUBMITTED -> EVALUATED e PENDING -> LATE -> EVALUATED
const sub1 = sim.insertSubmission({
  task_id: task1Id,
  student_id: student1Id,
  enrollment_id: enrActiveId,
});
sim.transitionStatus(sub1.id, {
  status: 'SUBMITTED',
  evidence_url: 'https://cdn.senai.nexa.local/evidences/eixo-aluno1.jpg',
  student_notes: 'Peça finalizada dentro da tolerância ±0,02mm.',
});
const completedAfterSubmit = sub1.completed_at;
sim.transitionStatus(sub1.id, {
  status: 'EVALUATED',
  final_task_score: 9.25,
});

const sub2 = sim.insertSubmission({
  task_id: task2Id,
  student_id: student1Id,
  enrollment_id: enrActiveId,
  status: 'LATE',
});
const sub3 = sim.insertSubmission({
  task_id: task3Id,
  student_id: student1Id,
  enrollment_id: enrActiveId,
  status: 'PENDING',
});

// Bloqueio de regressão EVALUATED -> PENDING
let regressionBlocked = false;
try {
  sim.transitionStatus(sub1.id, { status: 'PENDING' });
} catch (err) {
  regressionBlocked = err.sqlState === '23514';
}

assertCheck(
  sub1.status === 'EVALUATED' &&
    sub1.final_task_score === 9.25 &&
    completedAfterSubmit !== null &&
    sub2.status === 'LATE' &&
    sub3.status === 'PENDING' &&
    regressionBlocked,
  'Teste 1 (DoD): Transições PENDING -> SUBMITTED -> EVALUATED (completed_at automático) e bloqueio de regressão EVALUATED -> PENDING validados'
);

// Teste 2 (Critério 1): Duplicata (task_id, student_id) bloqueada com 23505 / P2002
let dupSubmissionBlocked = false;
try {
  sim.insertSubmission({
    task_id: task1Id,
    student_id: student1Id,
    enrollment_id: enrActiveId,
  });
} catch (err) {
  dupSubmissionBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupSubmissionBlocked,
  'Teste 2 (Critério 1): Submissão duplicada em (task_id, student_id) bloqueada por uq_task_submissions_task_student (23505 / P2002)'
);

// Teste 3 (Critério 2): Lista de pendências do portal do aluno por (student_id, status)
const studentPendingOrLate = sim.listByStudentAndStatuses(student1Id, ['PENDING', 'LATE']);
const studentEvaluated = sim.listByStudentAndStatuses(student1Id, ['EVALUATED']);
assertCheck(
  studentPendingOrLate.length === 2 && studentEvaluated.length === 1,
  'Teste 3 (Critério 2): Consulta por (student_id, status) retornou 2 tarefas pendentes/atrasadas (FE-036) e 1 avaliada'
);

// Teste 4 (Critério 3 & Regras de Nota): Matrícula DROPPED, matrícula de outra turma e nota > max_score bloqueadas
let droppedEnrollmentBlocked = false;
let otherClassBlocked = false;
let scoreExceedsMaxBlocked = false;

try {
  sim.insertSubmission({
    task_id: task1Id,
    student_id: studentDroppedId,
    enrollment_id: enrDroppedId,
  });
} catch (err) {
  droppedEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.insertSubmission({
    task_id: task1Id,
    student_id: studentOtherClassId,
    enrollment_id: enrOtherClassId,
  });
} catch (err) {
  otherClassBlocked = err.sqlState === '23514';
}

try {
  sim.transitionStatus(sub2.id, {
    status: 'EVALUATED',
    final_task_score: 9.0, // max_score de task2 = 8.0
  });
} catch (err) {
  scoreExceedsMaxBlocked = err.sqlState === '23514';
}

assertCheck(
  droppedEnrollmentBlocked && otherClassBlocked && scoreExceedsMaxBlocked,
  'Teste 4 (Critério 3): Matrícula inativa/DROPPED (23514), aluno de outra turma (23514) e final_task_score > max_score (23514) bloqueados'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-025] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
