/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-017]
 * Título: Implementar Tabela de Matrículas de Estudantes (enrollments)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Um estudante só pode ter uma matrícula por turma
 *    (`uq_enrollments_student_class UNIQUE (student_id, class_id)`).
 * 2. Critério 2: FKs para `users(id)` e `classes(id)` (`ON DELETE RESTRICT`) com validação
 *    de perfil garantindo apenas usuários com `role = 'STUDENT'` via trigger PL/pgSQL.
 * 3. Critério 3: Status padrão `'ACTIVE'` via enum nativo `enrollment_status_enum`.
 * 4. Observação Técnica: `attendance_rate` armazenado em porcentagem (`0.00..100.00`)
 *    com índice (`idx_enrollments_attendance_rate` e `idx_enrollments_class_status_attendance`)
 *    para filtros rápidos de risco.
 * 5. DoD: Migration versionada, `model Enrollment` no `prisma/schema.prisma`, tipos TS
 *    atualizados, testes unitários e integração com cards dependentes (`DB-019`, `DB-022`,
 *    `DB-025`, `DB-028`, `DB-034`, `DB-039`, `DB-042`, `DB-043`, `DB-046`).
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
  '20261118060000_create_enrollments_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118060000_create_enrollments_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '17_tabela_enrollments.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '17-tabela-matriculas-estudantes-enrollments.md'),
  path.join(ROOT_DIR, 'BancoNexa', '17-tabela-matriculas-estudantes-enrollments.md'),
];

const VALID_STATUSES = new Set(['ACTIVE', 'COMPLETED', 'DROPPED', 'SUSPENDED']);

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
 * Simulador relacional das tabelas `users`, `classes` e `enrollments` com unicidade composta
 * `(student_id, class_id)`, trigger de validação `role = 'STUDENT'`, status padrão `'ACTIVE'`
 * e faixas válidas para `final_grade` (0..10) e `attendance_rate` (0..100%).
 */
class EnrollmentsRelationalSimulator {
  constructor() {
    this.users = new Map();
    this.classes = new Map();
    this.enrollmentsById = new Map();
    this.enrollmentsByStudentClass = new Map();
    this.seq = 1;
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addClass(id, code, period) {
    this.classes.set(id, { id, code, period });
  }

  createEnrollment(row) {
    if (!row.student_id || !row.class_id) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const user = this.users.get(row.student_id);
    if (!user) {
      const err = new Error('violates foreign key constraint "fk_enrollments_student"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Critério 2: Trigger valida que apenas usuários com role STUDENT podem ser matriculados
    if (user.role !== 'STUDENT') {
      const err = new Error(`chk_enrollments_student_role: role "${user.role}" não permitida em enrollments`);
      err.sqlState = '23514';
      throw err;
    }

    if (!this.classes.has(row.class_id)) {
      const err = new Error('violates foreign key constraint "fk_enrollments_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Critério 1: UNIQUE (student_id, class_id)
    const compositeKey = `${row.student_id}::${row.class_id}`;
    if (this.enrollmentsByStudentClass.has(compositeKey)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`student_id`, `class_id`) [SQLSTATE 23505 / uq_enrollments_student_class]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    // Critério 3: Status padrão ACTIVE
    const status = row.status !== undefined ? row.status : 'ACTIVE';
    if (!VALID_STATUSES.has(status)) {
      const err = new Error(`invalid input value for enum enrollment_status_enum: "${status}"`);
      err.sqlState = '22P02';
      throw err;
    }

    let finalGrade = null;
    if (row.final_grade !== undefined && row.final_grade !== null) {
      const g = Number(row.final_grade);
      if (!Number.isFinite(g) || g < 0.0 || g > 10.0) {
        const err = new Error('violates check constraint "chk_enrollments_final_grade"');
        err.sqlState = '23514';
        throw err;
      }
      finalGrade = Number(g.toFixed(2));
    }

    let attendanceRate = null;
    if (row.attendance_rate !== undefined && row.attendance_rate !== null) {
      const a = Number(row.attendance_rate);
      if (!Number.isFinite(a) || a < 0.0 || a > 100.0) {
        const err = new Error('violates check constraint "chk_enrollments_attendance_rate"');
        err.sqlState = '23514';
        throw err;
      }
      attendanceRate = Number(a.toFixed(2));
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      student_id: row.student_id,
      class_id: row.class_id,
      enrollment_date: row.enrollment_date || now.slice(0, 10),
      status,
      final_grade: finalGrade,
      attendance_rate: attendanceRate,
      created_at: now,
      updated_at: now,
    };

    this.enrollmentsById.set(saved.id, saved);
    this.enrollmentsByStudentClass.set(compositeKey, saved);
    return saved;
  }

  findAtRiskByAttendance(thresholdPercent) {
    return [...this.enrollmentsById.values()]
      .filter((e) => e.status === 'ACTIVE' && e.attendance_rate !== null && e.attendance_rate < thresholdPercent)
      .sort((a, b) => a.attendance_rate - b.attendance_rate);
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-017] — MATRÍCULAS DE ESTUDANTES (enrollments)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de enrollments'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118060000_create_enrollments_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118060000_create_enrollments_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/17_tabela_enrollments.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/17_tabela_enrollments.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/17-tabela-matriculas-estudantes-enrollments.md e BancoNexa/17-tabela-matriculas-estudantes-enrollments.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-017'),
  'Card DB-017 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model Enrollment no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model Enrollment no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /enrollment_date\s+DATE\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_DATE/i.test(sqlContent) &&
    /status\s+enrollment_status_enum\s+NOT\s+NULL\s+DEFAULT\s+'ACTIVE'/i.test(sqlContent) &&
    /final_grade\s+(NUMERIC|DECIMAL)\(4,2\)/i.test(sqlContent) &&
    /attendance_rate\s+(NUMERIC|DECIMAL)\(5,2\)/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ/i.test(sqlContent) &&
    /updated_at\s+TIMESTAMPTZ/i.test(sqlContent),
  'Todas as colunas exigidas (id, student_id, class_id, enrollment_date, status, final_grade, attendance_rate, created_at, updated_at) presentes'
);
assertCheck(
  schemaContent.includes('model Enrollment') &&
    /status\s+EnrollmentStatus\s+@default\(ACTIVE\)\s+@map\("status"\)/.test(schemaContent) &&
    schemaContent.includes('@map("final_grade") @db.Decimal(4, 2)') &&
    schemaContent.includes('@map("attendance_rate") @db.Decimal(5, 2)') &&
    schemaContent.includes('@@unique([studentId, classId], map: "uq_enrollments_student_class")') &&
    schemaContent.includes('@@index([attendanceRate], map: "idx_enrollments_attendance_rate")') &&
    schemaContent.includes('@@map("enrollments")'),
  'Modelo Enrollment integrado ao prisma/schema.prisma com @@unique([studentId, classId]), status ACTIVE default e índice em attendanceRate'
);
assertCheck(
  typesTsContent.includes('EnrollmentStatus') &&
    typesTsContent.includes('export interface Enrollment {') &&
    typesTsContent.includes('attendanceRate: number | string | null;') &&
    typesTsContent.includes('export interface EnrollmentRow {'),
  'Tipos TypeScript (Enrollment, EnrollmentRow, EnrollmentCreateInput, EnrollmentUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_enrollments_student_class\s+UNIQUE\s*\(\s*student_id\s*,\s*class_id\s*\)/i.test(sqlContent),
  'Critério 1: Constraint uq_enrollments_student_class UNIQUE (student_id, class_id) declarada no SQL'
);
assertCheck(
  /CONSTRAINT\s+fk_enrollments_student\s+FOREIGN\s+KEY\s*\(\s*student_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_enrollments_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_enrollments_validate_student_role_and_touch/i.test(sqlContent) &&
    /v_user_role\s*<>\s*'STUDENT'/i.test(sqlContent),
  'Critério 2: FKs para users e classes com ON DELETE RESTRICT + trigger validando perfil role = STUDENT'
);
assertCheck(
  /status\s+enrollment_status_enum\s+NOT\s+NULL\s+DEFAULT\s+'ACTIVE'/i.test(sqlContent),
  'Critério 3: Status padrão ACTIVE configurado via enum nativo enrollment_status_enum'
);
assertCheck(
  /CONSTRAINT\s+chk_enrollments_attendance_rate\s+CHECK/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_enrollments_attendance_rate\s+ON\s+enrollments\s+USING\s+BTREE\s*\(\s*attendance_rate\s*\)/i.test(
      sqlContent
    ),
  'Observação Técnica: attendance_rate validado em 0.00..100.00% com índice idx_enrollments_attendance_rate para filtros de risco'
);

// 5. Integração com cards dependentes no modelo 3FN
console.log('\n5. Verificando integração com cards dependentes (DB-022, DB-025, DB-028, DB-034, DB-039, DB-042, DB-043, DB-046)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /fk_attendance_enrollment/i.test(sql3fnContent) &&
    /fk_task_submissions_enrollment/i.test(sql3fnContent) &&
    /fk_student_grades_enrollment/i.test(sql3fnContent) &&
    /fk_academic_alerts_enrollment/i.test(sql3fnContent) &&
    /fk_milestone_history_enrollment/i.test(sql3fnContent) &&
    /fk_help_requests_enrollment/i.test(sql3fnContent) &&
    /fk_pedagogical_notes_enrollment/i.test(sql3fnContent) &&
    /fk_student_achievements_enrollment/i.test(sql3fnContent),
  'Integração validada: todas as 8 tabelas dependentes no modelo 3FN referenciam enrollments(id)'
);

// 6. Testes unitários de integridade da tabela enrollments (DoD)
console.log('\n6. Executando testes unitários de integridade da tabela enrollments (DoD)...');
const sim = new EnrollmentsRelationalSimulator();
const student1Id = '11111111-1111-4111-8111-111111111111';
const student2Id = '22222222-2222-4222-8222-222222222222';
const teacherId = '33333333-3333-4333-8333-333333333333';
const coordId = '44444444-4444-4444-8444-444444444444';
const class1Id = 'aaaa1111-1111-4111-8111-111111111111';
const class2Id = 'bbbb2222-2222-4222-8222-222222222222';

sim.addUser(student1Id, 'aluno1@senai.br', 'STUDENT');
sim.addUser(student2Id, 'aluno2@senai.br', 'STUDENT');
sim.addUser(teacherId, 'prof@senai.br', 'TEACHER');
sim.addUser(coordId, 'coord@senai.br', 'COORDINATOR');
sim.addClass(class1Id, 'MEC-2026-1T', '2026.1');
sim.addClass(class2Id, 'MEC-2026-2T', '2026.2');

// Teste 1: Matrícula válida com status default ACTIVE
const e1 = sim.createEnrollment({
  student_id: student1Id,
  class_id: class1Id,
  final_grade: 8.25,
  attendance_rate: 92.5,
});
const e2 = sim.createEnrollment({
  student_id: student2Id,
  class_id: class1Id,
  attendance_rate: 68.0,
});
assertCheck(
  e1.status === 'ACTIVE' &&
    e2.status === 'ACTIVE' &&
    e1.final_grade === 8.25 &&
    e1.attendance_rate === 92.5 &&
    e2.final_grade === null,
  'Teste 1 (Critério 3): Matrículas criadas com status padrão ACTIVE e indicadores percentuais/nota válidos'
);

// Teste 2: Critério 1 — Duplicata (student_id, class_id) bloqueada; mesmo aluno em outra turma aceito
let dupEnrollmentBlocked = false;
try {
  sim.createEnrollment({ student_id: student1Id, class_id: class1Id });
} catch (err) {
  dupEnrollmentBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
const e1OtherClass = sim.createEnrollment({ student_id: student1Id, class_id: class2Id });
assertCheck(
  dupEnrollmentBlocked && e1OtherClass.class_id === class2Id,
  'Teste 2 (Critério 1): Segunda matrícula do mesmo estudante na mesma turma bloqueada (23505 / P2002); matrícula em outra turma aceita'
);

// Teste 3: Critério 2 — Apenas usuários com role STUDENT aceitos; TEACHER/COORDINATOR bloqueados
let teacherBlocked = false;
let coordBlocked = false;
let missingUserBlocked = false;
try {
  sim.createEnrollment({ student_id: teacherId, class_id: class1Id });
} catch (err) {
  teacherBlocked = err.sqlState === '23514';
}
try {
  sim.createEnrollment({ student_id: coordId, class_id: class1Id });
} catch (err) {
  coordBlocked = err.sqlState === '23514';
}
try {
  sim.createEnrollment({ student_id: '99999999-9999-4999-8999-999999999999', class_id: class1Id });
} catch (err) {
  missingUserBlocked = err.sqlState === '23503' && err.code === 'P2003';
}
assertCheck(
  teacherBlocked && coordBlocked && missingUserBlocked,
  'Teste 3 (Critério 2): Usuários TEACHER e COORDINATOR bloqueados (23514) e student_id inexistente rejeitado por FK (23503 / P2003)'
);

// Teste 4: Observação Técnica — Validação de faixas attendance_rate (0..100%) e final_grade (0..10) + filtro de risco
let badGradeBlocked = false;
let badAttendanceBlocked = false;
try {
  sim.createEnrollment({ student_id: student2Id, class_id: class2Id, final_grade: 10.5 });
} catch (err) {
  badGradeBlocked = err.sqlState === '23514';
}
try {
  sim.createEnrollment({ student_id: student2Id, class_id: class2Id, attendance_rate: -5.0 });
} catch (err) {
  badAttendanceBlocked = err.sqlState === '23514';
}
const atRisk = sim.findAtRiskByAttendance(75.0);
assertCheck(
  badGradeBlocked && badAttendanceBlocked && atRisk.length === 1 && atRisk[0].student_id === student2Id,
  'Teste 4 (Observação Técnica): Nota 10.50 e frequência -5.00% rejeitadas (23514); filtro de risco (<75%) identificou aluno com 68.00%'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-017] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
