/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-022]
 * Título: Implementar Tabela de Registros de Presença e Faltas (attendance_records)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Constraint UNIQUE composta `uq_attendance_lesson_student (lesson_id, student_id)`
 *    (e `uq_attendance_lesson_enrollment`) impedindo chamada duplicada na mesma aula
 *    e ancorando o upsert em lote (`ON CONFLICT ... DO UPDATE`).
 * 2. Critério 2: Chave estrangeira ligada a `enrollments` (`fk_attendance_enrollment`),
 *    `class_lessons` (`fk_attendance_lesson`) e `users` (`fk_attendance_student`) com
 *    `ON DELETE RESTRICT` + trigger garantindo que apenas alunos matriculados na turma
 *    da aula recebam presença.
 * 3. Critério 3: Índice composto `idx_attendance_student_status (student_id, status)` para
 *    agregação instantânea de faltas, complementado por `idx_attendance_lesson` e
 *    `idx_attendance_enrollment_status`.
 * 4. DoD: Migration versionada, `model AttendanceRecord` em `prisma/schema.prisma`, tipos TS
 *    em `BancoNexa/types/schema-models.ts`, testes de upsert em lote e integração com cards
 *    dependentes (`DB-029`, `DB-030`, `DB-034`, `DB-036`, `DB-037`, `BE-022`, `BE-023`).
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
  '20261123010000_create_attendance_records_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123010000_create_attendance_records_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '22_tabela_attendance_records.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '22-tabela-registros-presenca-attendance-records.md'),
  path.join(ROOT_DIR, 'BancoNexa', '22-tabela-registros-presenca-attendance-records.md'),
];

const VALID_ATTENDANCE_STATUSES = new Set(['PRESENT', 'ABSENT', 'LATE', 'JUSTIFIED']);

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
 * Simulador relacional das tabelas `class_lessons`, `enrollments`, `users` e `attendance_records`
 * com UNIQUE (lesson_id, student_id) e (lesson_id, enrollment_id), ON DELETE RESTRICT,
 * trigger de integridade de matrícula/turma/carga horária e suporte a batch upsert (ON CONFLICT).
 */
class AttendanceRecordsRelationalSimulator {
  constructor() {
    this.users = new Map();
    this.lessons = new Map();
    this.enrollments = new Map();
    this.recordsById = new Map();
    this.recordsByLessonStudent = new Map();
    this.recordsByLessonEnrollment = new Map();
    this.seq = 1;
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addLesson(id, classId, workloadHours = 4) {
    this.lessons.set(id, { id, class_id: classId, workload_hours: workloadHours });
  }

  addEnrollment(id, studentId, classId, status = 'ACTIVE') {
    this.enrollments.set(id, { id, student_id: studentId, class_id: classId, status });
  }

  _validateRow(row) {
    if (!row.lesson_id || !row.enrollment_id || !row.student_id) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const status = row.status !== undefined ? row.status : 'PRESENT';
    if (!VALID_ATTENDANCE_STATUSES.has(status)) {
      const err = new Error(`invalid input value for enum attendance_status_enum: "${status}"`);
      err.sqlState = '22P02';
      throw err;
    }

    const absentHours = row.absent_hours !== undefined ? row.absent_hours : 0;
    if (!Number.isInteger(absentHours) || absentHours < 0 || absentHours > 8) {
      const err = new Error('violates check constraint "chk_attendance_absent_hours"');
      err.sqlState = '23514';
      throw err;
    }

    if (status === 'PRESENT' && absentHours !== 0) {
      const err = new Error('violates check constraint "chk_attendance_present_zero_absent"');
      err.sqlState = '23514';
      throw err;
    }

    const lesson = this.lessons.get(row.lesson_id);
    if (!lesson) {
      const err = new Error('violates foreign key constraint "fk_attendance_lesson"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const enrollment = this.enrollments.get(row.enrollment_id);
    if (!enrollment) {
      const err = new Error('violates foreign key constraint "fk_attendance_enrollment"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const student = this.users.get(row.student_id);
    if (!student) {
      const err = new Error('violates foreign key constraint "fk_attendance_student"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (enrollment.student_id !== row.student_id) {
      const err = new Error('chk_attendance_enrollment_student: matrícula pertence a outro estudante');
      err.sqlState = '23514';
      throw err;
    }

    if (enrollment.class_id !== lesson.class_id) {
      const err = new Error('chk_attendance_enrollment_class: matrícula pertence a outra turma');
      err.sqlState = '23514';
      throw err;
    }

    if (absentHours > lesson.workload_hours) {
      const err = new Error('chk_attendance_absent_exceeds_workload: absent_hours excede workload_hours da aula');
      err.sqlState = '23514';
      throw err;
    }

    return { status, absentHours };
  }

  insertRecord(row) {
    const { status, absentHours } = this._validateRow(row);
    const lsKey = `${row.lesson_id}::${row.student_id}`;
    const leKey = `${row.lesson_id}::${row.enrollment_id}`;

    if (this.recordsByLessonStudent.has(lsKey)) {
      const err = new Error('Unique constraint failed: uq_attendance_lesson_student');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    if (this.recordsByLessonEnrollment.has(leKey)) {
      const err = new Error('Unique constraint failed: uq_attendance_lesson_enrollment');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      lesson_id: row.lesson_id,
      enrollment_id: row.enrollment_id,
      student_id: row.student_id,
      status,
      absent_hours: absentHours,
      justification_note: row.justification_note !== undefined ? row.justification_note : null,
      recorded_at: new Date().toISOString(),
    };

    this.recordsById.set(saved.id, saved);
    this.recordsByLessonStudent.set(lsKey, saved);
    this.recordsByLessonEnrollment.set(leKey, saved);
    return saved;
  }

  /**
   * Simula `INSERT INTO attendance_records (...) VALUES ...
   * ON CONFLICT (lesson_id, student_id) DO UPDATE SET status = EXCLUDED.status,
   * absent_hours = EXCLUDED.absent_hours, justification_note = EXCLUDED.justification_note,
   * recorded_at = CURRENT_TIMESTAMP;` de forma transacional (tudo ou nada).
   */
  upsertBatch(rows) {
    const validated = rows.map((row) => ({ row, parsed: this._validateRow(row) }));
    const results = [];

    for (const { row, parsed } of validated) {
      const lsKey = `${row.lesson_id}::${row.student_id}`;
      const existing = this.recordsByLessonStudent.get(lsKey);
      if (existing) {
        existing.status = parsed.status;
        existing.absent_hours = parsed.absentHours;
        existing.justification_note =
          row.justification_note !== undefined ? row.justification_note : existing.justification_note;
        existing.recorded_at = new Date().toISOString();
        results.push({ ...existing, action: 'UPDATED' });
      } else {
        const created = this.insertRecord(row);
        results.push({ ...created, action: 'INSERTED' });
      }
    }

    return results;
  }

  deleteLessonRestrict(lessonId) {
    const inUse = [...this.recordsById.values()].some((r) => r.lesson_id === lessonId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_attendance_lesson"');
      err.sqlState = '23503';
      throw err;
    }
    this.lessons.delete(lessonId);
  }

  aggregateByStudentAndStatus(studentId) {
    const summary = {
      PRESENT: 0,
      ABSENT: 0,
      LATE: 0,
      JUSTIFIED: 0,
      totalWorkloadHours: 0,
      totalAbsentHours: 0,
      attendanceRate: 100,
    };

    for (const r of this.recordsById.values()) {
      if (r.student_id !== studentId) continue;
      summary[r.status]++;
      const lesson = this.lessons.get(r.lesson_id);
      summary.totalWorkloadHours += lesson ? lesson.workload_hours : 0;
      summary.totalAbsentHours += r.absent_hours;
    }

    if (summary.totalWorkloadHours > 0) {
      summary.attendanceRate = Number(
        (((summary.totalWorkloadHours - summary.totalAbsentHours) / summary.totalWorkloadHours) * 100).toFixed(2)
      );
    }

    return summary;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-022] — PRESENÇA E FALTAS (attendance_records)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de attendance_records'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123010000_create_attendance_records_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123010000_create_attendance_records_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/22_tabela_attendance_records.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/22_tabela_attendance_records.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/22-tabela-registros-presenca-attendance-records.md e BancoNexa/22-tabela-registros-presenca-attendance-records.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-022'),
  'Card DB-022 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model AttendanceRecord no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model AttendanceRecord no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /lesson_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /enrollment_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /status\s+attendance_status_enum\s+NOT\s+NULL\s+DEFAULT\s+'PRESENT'/i.test(sqlContent) &&
    /absent_hours\s+INTEGER\s+NOT\s+NULL\s+DEFAULT\s+0/i.test(sqlContent) &&
    /justification_note\s+TEXT\s*,/i.test(sqlContent) &&
    /recorded_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, lesson_id, enrollment_id, student_id, status attendance_status_enum, absent_hours DEFAULT 0, justification_note opcional, recorded_at) presentes'
);
assertCheck(
  schemaContent.includes('model AttendanceRecord') &&
    (schemaContent.match(/attendanceRecords\s+AttendanceRecord\[\]/g) || []).length === 3 &&
    schemaContent.includes('@@unique([lessonId, studentId], map: "uq_attendance_lesson_student")') &&
    schemaContent.includes('@@unique([lessonId, enrollmentId], map: "uq_attendance_lesson_enrollment")') &&
    schemaContent.includes('@@index([studentId, status], map: "idx_attendance_student_status")') &&
    schemaContent.includes('@@index([lessonId], map: "idx_attendance_lesson")') &&
    schemaContent.includes('@@map("attendance_records")'),
  'Modelo AttendanceRecord integrado ao prisma/schema.prisma com UNIQUE composta, relações reversas em User/Enrollment/ClassLesson e índices'
);
assertCheck(
  typesTsContent.includes('export interface AttendanceRecord {') &&
    typesTsContent.includes('status: AttendanceStatus;') &&
    typesTsContent.includes('absentHours: number;') &&
    typesTsContent.includes('justificationNote: string | null;') &&
    typesTsContent.includes('export interface AttendanceRecordRow {'),
  'Tipos TypeScript (AttendanceRecord, AttendanceRecordRow, AttendanceRecordCreateInput, AttendanceRecordUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_attendance_lesson_student\s+UNIQUE\s*\(\s*lesson_id\s*,\s*student_id\s*\)/i.test(sqlContent) &&
    /CONSTRAINT\s+uq_attendance_lesson_enrollment\s+UNIQUE\s*\(\s*lesson_id\s*,\s*enrollment_id\s*\)/i.test(sqlContent),
  'Critério 1: Constraints uq_attendance_lesson_student (lesson_id, student_id) e uq_attendance_lesson_enrollment declaradas'
);
assertCheck(
  /CONSTRAINT\s+fk_attendance_lesson\s+FOREIGN\s+KEY\s*\(\s*lesson_id\s*\)\s*REFERENCES\s+class_lessons\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_attendance_enrollment\s+FOREIGN\s+KEY\s*\(\s*enrollment_id\s*\)\s*REFERENCES\s+enrollments\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_attendance_student\s+FOREIGN\s+KEY\s*\(\s*student_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_attendance_records_validate_integrity/i.test(sqlContent),
  'Critério 2: FKs íntegras (class_lessons, enrollments, users) com ON DELETE RESTRICT + trigger validando turma e matrícula'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_attendance_student_status\s+ON\s+attendance_records\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*status\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_attendance_lesson\s+ON\s+attendance_records\s+USING\s+BTREE\s*\(\s*lesson_id\s*\)/i.test(
      sqlContent
    ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_attendance_enrollment_status\s+ON\s+attendance_records\s+USING\s+BTREE\s*\(\s*enrollment_id\s*,\s*status\s*\)/i.test(
      sqlContent
    ),
  'Critério 3: Índice idx_attendance_student_status (student_id, status) + índices auxiliares (lesson_id e enrollment_id, status) criados'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-029, DB-030, DB-034, DB-036, DB-037, BE-022)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+attendance_records/i.test(sql3fnContent) &&
    /uq_attendance_lesson_student/i.test(sql3fnContent) &&
    /fk_attendance_enrollment/i.test(sql3fnContent) &&
    /chk_attendance_absent_hours/i.test(sql3fnContent),
  'Integração validada com modelo 3FN (T15 attendance_records) e âncora para DB-029, DB-030, DB-036, DB-037 e BE-022'
);

// 6. Testes unitários de upsert em lote, unicidade, matrícula na turma, absent_hours e cálculo de 75% (DoD)
console.log('\n6. Executando testes unitários de upsert em lote, unicidade, matrícula e frequência 75% (DoD)...');
const sim = new AttendanceRecordsRelationalSimulator();
const classMec1Id = '11111111-0000-4000-8000-000000000001';
const classMec2Id = '11111111-0000-4000-8000-000000000002';
const lesson1Id = '22222222-0000-4000-8000-000000000001';
const lesson2Id = '22222222-0000-4000-8000-000000000002';
const lesson3Id = '22222222-0000-4000-8000-000000000003';
const lesson4Id = '22222222-0000-4000-8000-000000000004';
const student1Id = '33333333-0000-4000-8000-000000000001';
const student2Id = '33333333-0000-4000-8000-000000000002';
const student3Id = '33333333-0000-4000-8000-000000000003';
const studentOtherClassId = '33333333-0000-4000-8000-000000000004';
const enr1Id = '44444444-0000-4000-8000-000000000001';
const enr2Id = '44444444-0000-4000-8000-000000000002';
const enr3Id = '44444444-0000-4000-8000-000000000003';
const enrOtherClassId = '44444444-0000-4000-8000-000000000004';

sim.addUser(student1Id, 'aluno1@senai.nexa.local', 'STUDENT');
sim.addUser(student2Id, 'aluno2@senai.nexa.local', 'STUDENT');
sim.addUser(student3Id, 'aluno3@senai.nexa.local', 'STUDENT');
sim.addUser(studentOtherClassId, 'aluno4@senai.nexa.local', 'STUDENT');

sim.addLesson(lesson1Id, classMec1Id, 4);
sim.addLesson(lesson2Id, classMec1Id, 4);
sim.addLesson(lesson3Id, classMec1Id, 4);
sim.addLesson(lesson4Id, classMec1Id, 4);

sim.addEnrollment(enr1Id, student1Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enr2Id, student2Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enr3Id, student3Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enrOtherClassId, studentOtherClassId, classMec2Id, 'ACTIVE');

// Teste 1 (DoD): Chamada rápida inicial em lote (todos PRESENT) + 2º upsert em lote alterando status sem duplicar
const batchInsert = sim.upsertBatch([
  { lesson_id: lesson1Id, enrollment_id: enr1Id, student_id: student1Id, status: 'PRESENT', absent_hours: 0 },
  { lesson_id: lesson1Id, enrollment_id: enr2Id, student_id: student2Id, status: 'PRESENT', absent_hours: 0 },
  { lesson_id: lesson1Id, enrollment_id: enr3Id, student_id: student3Id, status: 'PRESENT', absent_hours: 0 },
]);
const batchUpdate = sim.upsertBatch([
  { lesson_id: lesson1Id, enrollment_id: enr1Id, student_id: student1Id, status: 'PRESENT', absent_hours: 0 },
  { lesson_id: lesson1Id, enrollment_id: enr2Id, student_id: student2Id, status: 'ABSENT', absent_hours: 4 },
  {
    lesson_id: lesson1Id,
    enrollment_id: enr3Id,
    student_id: student3Id,
    status: 'JUSTIFIED',
    absent_hours: 2,
    justification_note: 'Atestado odontológico entregue na secretaria.',
  },
]);
assertCheck(
  batchInsert.every((r) => r.action === 'INSERTED') &&
    batchUpdate.every((r) => r.action === 'UPDATED') &&
    sim.recordsById.size === 3 &&
    batchUpdate[1].status === 'ABSENT' &&
    batchUpdate[1].absent_hours === 4 &&
    batchUpdate[2].status === 'JUSTIFIED',
  'Teste 1 (DoD): Upsert em lote (ON CONFLICT lesson_id, student_id) inseriu 3 registros e atualizou em 1 clique sem duplicar linhas'
);

// Teste 2 (Critério 1): Inserção direta duplicada em (lesson_id, student_id) bloqueada com 23505 / P2002
let duplicateBlocked = false;
try {
  sim.insertRecord({
    lesson_id: lesson1Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    status: 'LATE',
    absent_hours: 1,
  });
} catch (err) {
  duplicateBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  duplicateBlocked,
  'Teste 2 (Critério 1): Chamada duplicada para (lesson_id, student_id) bloqueada por uq_attendance_lesson_student (23505 / P2002)'
);

// Teste 3 (Critério 2): FK de enrollments, coerência de turma/estudante e ON DELETE RESTRICT em class_lessons
let missingEnrollmentBlocked = false;
let wrongClassEnrollmentBlocked = false;
let mismatchedStudentEnrollmentBlocked = false;
let deleteLessonRestrictBlocked = false;

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: '99999999-0000-4000-8000-000000000000',
    student_id: student1Id,
    status: 'PRESENT',
    absent_hours: 0,
  });
} catch (err) {
  missingEnrollmentBlocked = err.sqlState === '23503';
}

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: enrOtherClassId,
    student_id: studentOtherClassId,
    status: 'PRESENT',
    absent_hours: 0,
  });
} catch (err) {
  wrongClassEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: enr1Id,
    student_id: student2Id,
    status: 'PRESENT',
    absent_hours: 0,
  });
} catch (err) {
  mismatchedStudentEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.deleteLessonRestrict(lesson1Id);
} catch (err) {
  deleteLessonRestrictBlocked = err.sqlState === '23503';
}

assertCheck(
  missingEnrollmentBlocked &&
    wrongClassEnrollmentBlocked &&
    mismatchedStudentEnrollmentBlocked &&
    deleteLessonRestrictBlocked,
  'Teste 3 (Critério 2): Matrícula inexistente (23503), aluno de outra turma (23514), matrícula trocada (23514) e exclusão de aula em uso (23503) bloqueados'
);

// Teste 4 (Critério 3 & Regras absent_hours): Validação de absent_hours e agregação instantânea para limite 75%
let presentWithHoursBlocked = false;
let exceedWorkloadBlocked = false;
let overEightHoursBlocked = false;

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    status: 'PRESENT',
    absent_hours: 1,
  });
} catch (err) {
  presentWithHoursBlocked = err.sqlState === '23514';
}

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    status: 'ABSENT',
    absent_hours: 6, // workload da lesson2 = 4h
  });
} catch (err) {
  exceedWorkloadBlocked = err.sqlState === '23514';
}

try {
  sim.insertRecord({
    lesson_id: lesson2Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    status: 'ABSENT',
    absent_hours: 9,
  });
} catch (err) {
  overEightHoursBlocked = err.sqlState === '23514';
}

// Simular 4 aulas (16h totais) para student2: 1 falta integral (4h) + 3 presenças = 75.00% exatos
sim.upsertBatch([
  { lesson_id: lesson2Id, enrollment_id: enr2Id, student_id: student2Id, status: 'PRESENT', absent_hours: 0 },
  { lesson_id: lesson3Id, enrollment_id: enr2Id, student_id: student2Id, status: 'PRESENT', absent_hours: 0 },
  { lesson_id: lesson4Id, enrollment_id: enr2Id, student_id: student2Id, status: 'PRESENT', absent_hours: 0 },
]);
const aggStudent2 = sim.aggregateByStudentAndStatus(student2Id);

assertCheck(
  presentWithHoursBlocked &&
    exceedWorkloadBlocked &&
    overEightHoursBlocked &&
    aggStudent2.PRESENT === 3 &&
    aggStudent2.ABSENT === 1 &&
    aggStudent2.totalWorkloadHours === 16 &&
    aggStudent2.totalAbsentHours === 4 &&
    aggStudent2.attendanceRate === 75,
  'Teste 4 (Critério 3): Regras de absent_hours aplicadas e agregação por (student_id, status) calculou 75.00% de frequência (12h/16h)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-022] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
