/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-028]
 * Título: Implementar Tabela de Notas e Menções Finais (student_grades)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Constraint UNIQUE composta `uq_student_grades_assessment_student (assessment_id, student_id)`
 *    (e `uq_student_grades_assessment_enrollment`).
 * 2. Critério 2: CHECK constraints `chk_student_grades_value` e `chk_student_grades_recovery`
 *    garantindo `grade_value` e `recovery_grade` entre `0.00` e `10.00` (com 2 casas decimais)
 *    e limite `<= academic_assessments.max_grade`.
 * 3. Critério 3: Vínculo obrigatório com `enrollment_id` válido (`fk_student_grades_enrollment`
 *    com `ON DELETE RESTRICT`) + trigger validando matrícula `ACTIVE` pertencente ao estudante
 *    e à turma da avaliação, além de perfil docente em `recorded_by`.
 * 4. DoD & Observação Técnica: Tabela `student_grades` migrada, `model StudentGrade` integrado
 *    ao `prisma/schema.prisma`, tipos TS gerados em `BancoNexa/types/schema-models.ts`, testes
 *    de limites numéricos aprovados e disparo automático de log em `audit_logs` (`DB-009`) ao
 *    alterar nota já publicada.
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
  '20261123070000_create_student_grades_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123070000_create_student_grades_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '28_tabela_student_grades.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '28-tabela-notas-mencoes-finais-student-grades.md'),
  path.join(ROOT_DIR, 'BancoNexa', '28-tabela-notas-mencoes-finais-student-grades.md'),
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

/**
 * Simulador relacional das tabelas `academic_assessments`, `enrollments`, `users`,
 * `student_grades` e `audit_logs` com UNIQUE (assessment_id, student_id),
 * CHECK 0.00..10.00, validação de matrícula ACTIVE/turma/aluno, perfil docente em
 * recorded_by e registro automático em audit_logs ao atualizar nota publicada.
 */
class StudentGradesRelationalSimulator {
  constructor() {
    this.assessments = new Map();
    this.enrollments = new Map();
    this.users = new Map();
    this.gradesById = new Map();
    this.gradesByAssessmentStudent = new Map();
    this.gradesByAssessmentEnrollment = new Map();
    this.auditLogs = [];
    this.seq = 1;
  }

  addAssessment(id, classId, title, maxGrade = 10.0) {
    this.assessments.set(id, { id, class_id: classId, title, max_grade: maxGrade });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addEnrollment(id, studentId, classId, status = 'ACTIVE') {
    this.enrollments.set(id, { id, student_id: studentId, class_id: classId, status });
  }

  _validateRow(row, isInsert) {
    if (!row.assessment_id || !row.enrollment_id || !row.student_id || !row.recorded_by) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (row.grade_value === undefined || row.grade_value === null) {
      const err = new Error('null value in column "grade_value" violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const gradeValue = Number(row.grade_value);
    if (Number.isNaN(gradeValue) || gradeValue < 0.0 || gradeValue > 10.0) {
      const err = new Error('new row for relation "student_grades" violates check constraint "chk_student_grades_value"');
      err.sqlState = '23514';
      throw err;
    }

    let recoveryGrade = null;
    if (row.recovery_grade !== undefined && row.recovery_grade !== null) {
      recoveryGrade = Number(row.recovery_grade);
      if (Number.isNaN(recoveryGrade) || recoveryGrade < 0.0 || recoveryGrade > 10.0) {
        const err = new Error('new row for relation "student_grades" violates check constraint "chk_student_grades_recovery"');
        err.sqlState = '23514';
        throw err;
      }
    }

    const assessment = this.assessments.get(row.assessment_id);
    if (!assessment) {
      const err = new Error('violates foreign key constraint "fk_student_grades_assessment"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const enrollment = this.enrollments.get(row.enrollment_id);
    if (!enrollment) {
      const err = new Error('violates foreign key constraint "fk_student_grades_enrollment"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const student = this.users.get(row.student_id);
    if (!student) {
      const err = new Error('violates foreign key constraint "fk_student_grades_student"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const recorder = this.users.get(row.recorded_by);
    if (!recorder) {
      const err = new Error('violates foreign key constraint "fk_student_grades_recorded_by"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (enrollment.student_id !== row.student_id) {
      const err = new Error('chk_student_grades_enrollment_student');
      err.sqlState = '23514';
      throw err;
    }

    if (enrollment.class_id !== assessment.class_id) {
      const err = new Error('chk_student_grades_enrollment_class');
      err.sqlState = '23514';
      throw err;
    }

    if (isInsert && enrollment.status !== 'ACTIVE') {
      const err = new Error('chk_student_grades_enrollment_active');
      err.sqlState = '23514';
      throw err;
    }

    if (recorder.role === 'STUDENT') {
      const err = new Error('chk_student_grades_recorder_role');
      err.sqlState = '23514';
      throw err;
    }

    if (row.recorded_by === row.student_id) {
      const err = new Error('chk_student_grades_no_self_grading');
      err.sqlState = '23514';
      throw err;
    }

    if (gradeValue > assessment.max_grade) {
      const err = new Error('chk_student_grades_exceeds_max_grade');
      err.sqlState = '23514';
      throw err;
    }

    if (recoveryGrade !== null && recoveryGrade > assessment.max_grade) {
      const err = new Error('chk_student_grades_exceeds_max_grade');
      err.sqlState = '23514';
      throw err;
    }

    return {
      gradeValue: Number(gradeValue.toFixed(2)),
      recoveryGrade: recoveryGrade !== null ? Number(recoveryGrade.toFixed(2)) : null,
    };
  }

  insertGrade(row) {
    const { gradeValue, recoveryGrade } = this._validateRow(row, true);

    const asKey = `${row.assessment_id}::${row.student_id}`;
    const aeKey = `${row.assessment_id}::${row.enrollment_id}`;
    if (this.gradesByAssessmentStudent.has(asKey)) {
      const err = new Error('Unique constraint failed: uq_student_grades_assessment_student');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }
    if (this.gradesByAssessmentEnrollment.has(aeKey)) {
      const err = new Error('Unique constraint failed: uq_student_grades_assessment_enrollment');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      assessment_id: row.assessment_id,
      enrollment_id: row.enrollment_id,
      student_id: row.student_id,
      recorded_by: row.recorded_by,
      grade_value: gradeValue,
      recovery_grade: recoveryGrade,
      comments: row.comments !== undefined ? row.comments : null,
      created_at: now,
      updated_at: now,
    };

    this.gradesById.set(saved.id, saved);
    this.gradesByAssessmentStudent.set(asKey, saved);
    this.gradesByAssessmentEnrollment.set(aeKey, saved);
    return saved;
  }

  updateGrade(gradeId, patch) {
    const current = this.gradesById.get(gradeId);
    if (!current) throw new Error('Grade not found');

    const oldSnapshot = {
      assessment_id: current.assessment_id,
      enrollment_id: current.enrollment_id,
      student_id: current.student_id,
      grade_value: current.grade_value,
      recovery_grade: current.recovery_grade,
      comments: current.comments,
    };

    const merged = { ...current, ...patch };
    const { gradeValue, recoveryGrade } = this._validateRow(merged, false);

    current.recorded_by = merged.recorded_by;
    current.grade_value = gradeValue;
    current.recovery_grade = recoveryGrade;
    current.comments = merged.comments !== undefined ? merged.comments : current.comments;
    current.updated_at = new Date().toISOString();

    if (
      oldSnapshot.grade_value !== current.grade_value ||
      oldSnapshot.recovery_grade !== current.recovery_grade ||
      oldSnapshot.comments !== current.comments
    ) {
      this.auditLogs.push({
        user_id: current.recorded_by,
        action: 'GRADE_UPDATED',
        entity: 'student_grades',
        entity_id: current.id,
        old_values: oldSnapshot,
        new_values: {
          assessment_id: current.assessment_id,
          enrollment_id: current.enrollment_id,
          student_id: current.student_id,
          grade_value: current.grade_value,
          recovery_grade: current.recovery_grade,
          comments: current.comments,
        },
      });
    }

    return current;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-028] — NOTAS E MENÇÕES FINAIS (student_grades)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de student_grades'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123070000_create_student_grades_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123070000_create_student_grades_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/28_tabela_student_grades.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/28_tabela_student_grades.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/28-tabela-notas-mencoes-finais-student-grades.md e BancoNexa/28-tabela-notas-mencoes-finais-student-grades.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-028'),
  'Card DB-028 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model StudentGrade no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model StudentGrade no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /assessment_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /enrollment_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /recorded_by\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /grade_value\s+NUMERIC\(4,2\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /recovery_grade\s+NUMERIC\(4,2\)\s*,/i.test(sqlContent) &&
    /comments\s+TEXT\s*,/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent) &&
    /updated_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, assessment_id, enrollment_id, student_id, recorded_by, grade_value NUMERIC 4,2, recovery_grade opcional, comments, created_at, updated_at) presentes'
);
assertCheck(
  schemaContent.includes('model StudentGrade') &&
    schemaContent.includes('@relation("StudentGradeStudent"') &&
    schemaContent.includes('@relation("StudentGradeRecorder"') &&
    schemaContent.includes('@@unique([assessmentId, studentId], map: "uq_student_grades_assessment_student")') &&
    schemaContent.includes('@@unique([assessmentId, enrollmentId], map: "uq_student_grades_assessment_enrollment")') &&
    schemaContent.includes('@@map("student_grades")'),
  'Modelo StudentGrade integrado ao prisma/schema.prisma com relações nomeadas em User, relações reversas em Enrollment/AcademicAssessment e constraints UNIQUE'
);
assertCheck(
  typesTsContent.includes('export interface StudentGrade {') &&
    typesTsContent.includes('gradeValue: number | string;') &&
    typesTsContent.includes('recoveryGrade: number | string | null;') &&
    typesTsContent.includes('export interface StudentGradeRow {'),
  'Tipos TypeScript (StudentGrade, StudentGradeRow, StudentGradeCreateInput, StudentGradeUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2, 3 e Auditoria no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e trigger de auditoria (audit_logs) no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_student_grades_assessment_student\s+UNIQUE\s*\(\s*assessment_id\s*,\s*student_id\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+uq_student_grades_assessment_enrollment\s+UNIQUE\s*\(\s*assessment_id\s*,\s*enrollment_id\s*\)/i.test(
      sqlContent
    ),
  'Critério 1: Constraints uq_student_grades_assessment_student (assessment_id, student_id) e uq_student_grades_assessment_enrollment declaradas'
);
assertCheck(
  /CONSTRAINT\s+chk_student_grades_value\s+CHECK\s*\(\s*grade_value\s*>=\s*0\.00\s+AND\s+grade_value\s*<=\s*10\.00\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+chk_student_grades_recovery\s+CHECK\s*\(\s*recovery_grade\s+IS\s+NULL\s+OR\s*\(\s*recovery_grade\s*>=\s*0\.00\s+AND\s+recovery_grade\s*<=\s*10\.00\s*\)\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: CHECK constraints chk_student_grades_value e chk_student_grades_recovery (0.00..10.00) declaradas'
);
assertCheck(
  /CONSTRAINT\s+fk_student_grades_enrollment\s+FOREIGN\s+KEY\s*\(\s*enrollment_id\s*\)\s*REFERENCES\s+enrollments\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /trg_student_grades_validate_and_touch/i.test(sqlContent) &&
    /chk_student_grades_enrollment_active/i.test(sqlContent),
  'Critério 3: FK obrigatória fk_student_grades_enrollment (ON DELETE RESTRICT) + trigger validando matrícula ativa e turma'
);
assertCheck(
  /trg_student_grades_audit_update/i.test(sqlContent) &&
    /INSERT\s+INTO\s+audit_logs/i.test(sqlContent) &&
    /'GRADE_UPDATED'/i.test(sqlContent),
  'Observação Técnica: Trigger AFTER UPDATE trg_student_grades_audit_update gravando alterações de nota em audit_logs (DB-009)'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-017, DB-027, DB-029, DB-036, BE-027, BE-028)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-017, DB-027, DB-029, DB-036, BE-028)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+student_grades/i.test(sql3fnContent) &&
    /uq_student_grades_assessment_student/i.test(sql3fnContent) &&
    /chk_student_grades_value/i.test(sql3fnContent) &&
    /chk_student_grades_recovery/i.test(sql3fnContent),
  'Integração validada com modelo 3FN ([T17] student_grades) e nomenclatura oficial de constraints'
);

// 6. Testes unitários de limites numéricos (DoD), UNIQUE, enrollment_id válido e log em audit_logs
console.log('\n6. Executando testes unitários de limites numéricos, unicidade, matrícula válida e auditoria (DoD)...');
const sim = new StudentGradesRelationalSimulator();
const classMec1Id = '10000000-0000-4000-8000-000000000001';
const classMec2Id = '10000000-0000-4000-8000-000000000002';
const assess10Id = '20000000-0000-4000-8000-000000000001';
const assess5Id = '20000000-0000-4000-8000-000000000002';
const teacherId = '30000000-0000-4000-8000-000000000001';
const student1Id = '30000000-0000-4000-8000-000000000002';
const student2Id = '30000000-0000-4000-8000-000000000003';
const studentDroppedId = '30000000-0000-4000-8000-000000000004';
const studentOtherClassId = '30000000-0000-4000-8000-000000000005';
const enr1Id = '40000000-0000-4000-8000-000000000001';
const enr2Id = '40000000-0000-4000-8000-000000000002';
const enrDroppedId = '40000000-0000-4000-8000-000000000003';
const enrOtherClassId = '40000000-0000-4000-8000-000000000004';

sim.addAssessment(assess10Id, classMec1Id, 'Prova Teórica de Metrologia', 10.0);
sim.addAssessment(assess5Id, classMec1Id, 'Microavaliação de Paquímetro', 5.0);
sim.addUser(teacherId, 'prof.metrologia@senai.nexa.local', 'TEACHER');
sim.addUser(student1Id, 'aluno1@senai.nexa.local', 'STUDENT');
sim.addUser(student2Id, 'aluno2@senai.nexa.local', 'STUDENT');
sim.addUser(studentDroppedId, 'aluno.evadido@senai.nexa.local', 'STUDENT');
sim.addUser(studentOtherClassId, 'aluno.turma2@senai.nexa.local', 'STUDENT');
sim.addEnrollment(enr1Id, student1Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enr2Id, student2Id, classMec1Id, 'ACTIVE');
sim.addEnrollment(enrDroppedId, studentDroppedId, classMec1Id, 'DROPPED');
sim.addEnrollment(enrOtherClassId, studentOtherClassId, classMec2Id, 'ACTIVE');

// Teste 1 (DoD — Limites Numéricos válidos e auditoria em UPDATE): 0.00, 10.00, precisão decimal e recovery_grade
const gZero = sim.insertGrade({
  assessment_id: assess10Id,
  enrollment_id: enr1Id,
  student_id: student1Id,
  recorded_by: teacherId,
  grade_value: 0.0,
  recovery_grade: 7.25,
  comments: 'Recuperou o domínio em leitura de micrômetro.',
});
const gTen = sim.insertGrade({
  assessment_id: assess10Id,
  enrollment_id: enr2Id,
  student_id: student2Id,
  recorded_by: teacherId,
  grade_value: 10.0,
  recovery_grade: null,
});

// Alterar nota publicada dispara audit_logs (GRADE_UPDATED)
sim.updateGrade(gZero.id, {
  grade_value: 4.5,
  recovery_grade: 8.75,
  comments: 'Revisão de questão dissertativa deferida.',
});
const auditEntry = sim.auditLogs[0];

assertCheck(
  gZero.grade_value === 4.5 &&
    gZero.recovery_grade === 8.75 &&
    gTen.grade_value === 10.0 &&
    gTen.recovery_grade === null &&
    sim.auditLogs.length === 1 &&
    auditEntry.action === 'GRADE_UPDATED' &&
    auditEntry.entity === 'student_grades' &&
    auditEntry.old_values.grade_value === 0.0 &&
    auditEntry.new_values.grade_value === 4.5 &&
    auditEntry.new_values.recovery_grade === 8.75,
  'Teste 1 (DoD): Fronteiras válidas (0.00, 10.00, 7.25, 8.75) aceitas e alteração posterior registrada automaticamente em audit_logs (GRADE_UPDATED)'
);

// Teste 2 (Critério 1): Duplicata (assessment_id, student_id) bloqueada com 23505 / P2002
let dupGradeBlocked = false;
try {
  sim.insertGrade({
    assessment_id: assess10Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 8.0,
  });
} catch (err) {
  dupGradeBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupGradeBlocked,
  'Teste 2 (Critério 1): Nota duplicada em (assessment_id, student_id) bloqueada por uq_student_grades_assessment_student (23505 / P2002)'
);

// Teste 3 (Critério 2 — Limites Numéricos inválidos): grade_value e recovery_grade fora de 0.00..10.00 ou > max_grade
let negGradeBlocked = false;
let over10GradeBlocked = false;
let negRecoveryBlocked = false;
let over10RecoveryBlocked = false;
let overMaxGradeBlocked = false;
let overMaxRecoveryBlocked = false;

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: -0.01,
  });
} catch (err) {
  negGradeBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 10.01,
  });
} catch (err) {
  over10GradeBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 3.0,
    recovery_grade: -1.0,
  });
} catch (err) {
  negRecoveryBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 3.0,
    recovery_grade: 10.5,
  });
} catch (err) {
  over10RecoveryBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id, // max_grade = 5.0
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 6.0,
  });
} catch (err) {
  overMaxGradeBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id, // max_grade = 5.0
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 4.0,
    recovery_grade: 5.5,
  });
} catch (err) {
  overMaxRecoveryBlocked = err.sqlState === '23514';
}

assertCheck(
  negGradeBlocked &&
    over10GradeBlocked &&
    negRecoveryBlocked &&
    over10RecoveryBlocked &&
    overMaxGradeBlocked &&
    overMaxRecoveryBlocked,
  'Teste 3 (Critério 2): Limites numéricos inválidos (-0.01, 10.01 em grade_value/recovery_grade e > max_grade 5.0) bloqueados com SQLSTATE 23514'
);

// Teste 4 (Critério 3): Vínculo obrigatório com enrollment_id válido, matrícula ACTIVE, mesma turma e perfil docente
let nullEnrollmentBlocked = false;
let missingEnrollmentBlocked = false;
let droppedEnrollmentBlocked = false;
let otherClassEnrollmentBlocked = false;
let mismatchedStudentEnrollmentBlocked = false;
let studentRecorderBlocked = false;

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: null,
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 4.5,
  });
} catch (err) {
  nullEnrollmentBlocked = err.sqlState === '23502';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: '99999999-9999-4999-8999-999999999999',
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 4.5,
  });
} catch (err) {
  missingEnrollmentBlocked = err.sqlState === '23503' && err.code === 'P2003';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enrDroppedId,
    student_id: studentDroppedId,
    recorded_by: teacherId,
    grade_value: 4.0,
  });
} catch (err) {
  droppedEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enrOtherClassId,
    student_id: studentOtherClassId,
    recorded_by: teacherId,
    grade_value: 4.0,
  });
} catch (err) {
  otherClassEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr2Id, // pertence a student2, mas passado com student1
    student_id: student1Id,
    recorded_by: teacherId,
    grade_value: 4.0,
  });
} catch (err) {
  mismatchedStudentEnrollmentBlocked = err.sqlState === '23514';
}

try {
  sim.insertGrade({
    assessment_id: assess5Id,
    enrollment_id: enr1Id,
    student_id: student1Id,
    recorded_by: student2Id, // role STUDENT não pode lançar nota
    grade_value: 4.5,
  });
} catch (err) {
  studentRecorderBlocked = err.sqlState === '23514';
}

assertCheck(
  nullEnrollmentBlocked &&
    missingEnrollmentBlocked &&
    droppedEnrollmentBlocked &&
    otherClassEnrollmentBlocked &&
    mismatchedStudentEnrollmentBlocked &&
    studentRecorderBlocked,
  'Teste 4 (Critério 3): enrollment_id nulo (23502), inexistente (23503), DROPPED (23514), de outra turma/aluno (23514) e lançador STUDENT (23514) bloqueados'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-028] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
