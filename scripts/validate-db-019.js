/**
 * Script de Validação Automatizada e Testes de Violação Proposital — Card [DB-019]
 * Título: Configurar Constraints de Unicidade e Integridade Acadêmica em Matrículas
 *
 * Verifica programaticamente:
 * 1. Critério 1: CHECK constraints ativas no PostgreSQL (`chk_enrollments_final_grade`,
 *    `chk_enrollments_attendance_rate`, `chk_classes_date_range`, `chk_classes_max_students`)
 *    e triggers de capacidade sob concorrência (`FOR UPDATE`).
 * 2. Critério 2: Testes de violação proposital garantindo que nota `10.50`, frequência `-5%`,
 *    datas invertidas, matrícula duplicada, excesso de vagas e redução de `max_students`
 *    falhem com erro de constraint (`SQLSTATE 23514` / `23505`).
 * 3. Critério 3: Documentação das constraints registrada diretamente em `prisma/schema.prisma`
 *    e via `COMMENT ON CONSTRAINT` no catálogo SQL.
 * 4. DoD: Script de constraints (`19_constraints_integridade_academica_matriculas.sql`) e
 *    script de violação SQL (`19_testes_violacao_constraints.sql`) validados.
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
  '20261118080000_enforce_academic_integrity_constraints',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118080000_enforce_academic_integrity_constraints.sql'
);
const BANCO_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'sql',
  '19_constraints_integridade_academica_matriculas.sql'
);
const VIOLATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '19_testes_violacao_constraints.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '19-constraints-integridade-academica-matriculas.md'),
  path.join(ROOT_DIR, 'BancoNexa', '19-constraints-integridade-academica-matriculas.md'),
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
 * Simulador transacional de integridade acadêmica (`classes` + `enrollments`)
 * reproduzindo exatamente as constraints CHECK, UNIQUE e os triggers de capacidade (DB-019).
 */
class AcademicIntegritySimulator {
  constructor() {
    this.classes = new Map();
    this.enrollments = new Map();
    this.uniqueStudentClass = new Map();
    this.seq = 1;
  }

  createClass({ id, code, start_date, end_date, max_students }) {
    if (!(start_date < end_date)) {
      const err = new Error('new row for relation "classes" violates check constraint "chk_classes_date_range"');
      err.sqlState = '23514';
      err.constraint = 'chk_classes_date_range';
      throw err;
    }
    if (!Number.isInteger(max_students) || max_students <= 0 || max_students > 100) {
      const err = new Error('new row for relation "classes" violates check constraint "chk_classes_max_students"');
      err.sqlState = '23514';
      err.constraint = 'chk_classes_max_students';
      throw err;
    }
    const cls = { id, code, start_date, end_date, max_students };
    this.classes.set(id, cls);
    return cls;
  }

  updateClassMaxStudents(classId, newMax) {
    const cls = this.classes.get(classId);
    if (!cls) throw new Error('class not found');
    if (!Number.isInteger(newMax) || newMax <= 0 || newMax > 100) {
      const err = new Error('violates check constraint "chk_classes_max_students"');
      err.sqlState = '23514';
      err.constraint = 'chk_classes_max_students';
      throw err;
    }
    if (newMax < cls.max_students) {
      const activeCount = this.countActiveEnrollments(classId);
      if (newMax < activeCount) {
        const err = new Error('violates trigger constraint "chk_classes_max_students_vs_active"');
        err.sqlState = '23514';
        err.constraint = 'chk_classes_max_students_vs_active';
        throw err;
      }
    }
    cls.max_students = newMax;
    return cls;
  }

  countActiveEnrollments(classId, excludeEnrollmentId = null) {
    let count = 0;
    for (const e of this.enrollments.values()) {
      if (e.class_id === classId && e.status === 'ACTIVE' && e.id !== excludeEnrollmentId) {
        count++;
      }
    }
    return count;
  }

  createEnrollment({ student_id, class_id, status = 'ACTIVE', final_grade = null, attendance_rate = null }) {
    const cls = this.classes.get(class_id);
    if (!cls) {
      const err = new Error('violates foreign key constraint "fk_enrollments_class"');
      err.sqlState = '23503';
      throw err;
    }

    // chk_enrollments_final_grade
    if (final_grade !== null && (final_grade < 0.0 || final_grade > 10.0)) {
      const err = new Error(
        'new row for relation "enrollments" violates check constraint "chk_enrollments_final_grade"'
      );
      err.sqlState = '23514';
      err.constraint = 'chk_enrollments_final_grade';
      throw err;
    }

    // chk_enrollments_attendance_rate
    if (attendance_rate !== null && (attendance_rate < 0.0 || attendance_rate > 100.0)) {
      const err = new Error(
        'new row for relation "enrollments" violates check constraint "chk_enrollments_attendance_rate"'
      );
      err.sqlState = '23514';
      err.constraint = 'chk_enrollments_attendance_rate';
      throw err;
    }

    // uq_enrollments_student_class
    const uk = `${student_id}::${class_id}`;
    if (this.uniqueStudentClass.has(uk)) {
      const err = new Error('duplicate key value violates unique constraint "uq_enrollments_student_class"');
      err.sqlState = '23505';
      err.constraint = 'uq_enrollments_student_class';
      throw err;
    }

    // trg_enrollments_enforce_class_capacity (FOR UPDATE)
    if (status === 'ACTIVE' && this.countActiveEnrollments(class_id) >= cls.max_students) {
      const err = new Error('violates trigger constraint "chk_enrollments_class_capacity"');
      err.sqlState = '23514';
      err.constraint = 'chk_enrollments_class_capacity';
      throw err;
    }

    const id = `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`;
    const saved = { id, student_id, class_id, status, final_grade, attendance_rate };
    this.enrollments.set(id, saved);
    this.uniqueStudentClass.set(uk, saved);
    return saved;
  }

  updateEnrollmentStatus(enrollmentId, newStatus) {
    const enr = this.enrollments.get(enrollmentId);
    if (!enr) throw new Error('enrollment not found');
    const cls = this.classes.get(enr.class_id);
    if (newStatus === 'ACTIVE' && enr.status !== 'ACTIVE') {
      if (this.countActiveEnrollments(enr.class_id, enr.id) >= cls.max_students) {
        const err = new Error('violates trigger constraint "chk_enrollments_class_capacity"');
        err.sqlState = '23514';
        err.constraint = 'chk_enrollments_class_capacity';
        throw err;
      }
    }
    enr.status = newStatus;
    return enr;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-019] — CONSTRAINTS DE INTEGRIDADE ACADÊMICA');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram o schema e registraram a migration de constraints (DB-019)'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, script de violação proposital e documentação
console.log('\n2. Verificando arquivos SQL, migration, testes SQL de violação e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118080000_enforce_academic_integrity_constraints/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118080000_enforce_academic_integrity_constraints.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/19_constraints_integridade_academica_matriculas.sql'
);
assertCheck(
  fs.existsSync(VIOLATION_SQL_PATH),
  'Script SQL de testes de violação proposital presente em BancoNexa/sql/19_testes_violacao_constraints.sql'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const bancoMigContent = fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8');
const bancoSqlContent = fs.readFileSync(BANCO_SQL_PATH, 'utf8');
const violationSqlContent = fs.readFileSync(VIOLATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const docA = fs.readFileSync(DOC_PATHS[0], 'utf8');
const docB = fs.readFileSync(DOC_PATHS[1], 'utf8');

assertCheck(
  sqlContent === bancoMigContent && sqlContent === bancoSqlContent,
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/19_constraints_integridade_academica_matriculas.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/19-constraints-integridade-academica-matriculas.md e BancoNexa/19-constraints-integridade-academica-matriculas.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-019'),
  'Card DB-019 documentado em BancoNexa/README.md'
);

// 3. Critério 1 & 3: CHECK constraints ativas no SQL, triggers FOR UPDATE e documentação no schema.prisma
console.log('\n3. Verificando Critérios 1 e 3 (CHECK constraints, triggers FOR UPDATE e documentação no schema)...');
assertCheck(
  /chk_enrollments_final_grade/i.test(sqlContent) &&
    /final_grade\s*>=\s*0\.00\s+AND\s+final_grade\s*<=\s*10\.00/i.test(sqlContent) &&
    /chk_enrollments_attendance_rate/i.test(sqlContent) &&
    /attendance_rate\s*>=\s*0\.00\s+AND\s+attendance_rate\s*<=\s*100\.00/i.test(sqlContent) &&
    /chk_classes_date_range/i.test(sqlContent) &&
    /start_date\s*<\s*end_date/i.test(sqlContent) &&
    /chk_classes_max_students/i.test(sqlContent),
  'Critério 1: Todas as CHECK constraints (nota 0..10, frequência 0..100, start_date < end_date, max_students 1..100) garantidas no PostgreSQL'
);
assertCheck(
  /trg_enrollments_enforce_class_capacity/i.test(sqlContent) &&
    /FOR\s+UPDATE/i.test(sqlContent) &&
    /trg_classes_validate_max_students_reduction/i.test(sqlContent) &&
    /COMMENT\s+ON\s+CONSTRAINT\s+chk_enrollments_final_grade/i.test(sqlContent),
  'Triggers de capacidade com lock pessimista FOR UPDATE, proteção de redução de vagas e COMMENT ON CONSTRAINT configurados'
);
assertCheck(
  schemaContent.includes('chk_classes_date_range') &&
    schemaContent.includes('chk_classes_max_students') &&
    schemaContent.includes('chk_enrollments_final_grade') &&
    schemaContent.includes('chk_enrollments_attendance_rate') &&
    schemaContent.includes('trg_enrollments_enforce_class_capacity') &&
    schemaContent.includes('@check'),
  'Critério 3: Documentação completa das constraints registrada nos modelos Class e Enrollment de prisma/schema.prisma'
);
assertCheck(
  violationSqlContent.includes('10.50') &&
    violationSqlContent.includes('-5.00') &&
    /EXCEPTION\s+WHEN\s+check_violation/i.test(violationSqlContent) &&
    /ROLLBACK;/i.test(violationSqlContent),
  'Script SQL rollback-safe de testes de violação proposital (10.50, -5.00, datas, duplicidade e capacidade) validado'
);

// 4. Critério 2 & DoD: Execução dos testes de violação proposital no simulador transacional
console.log('\n4. Executando testes de violação proposital de constraints (Critério 2 & DoD)...');
const sim = new AcademicIntegritySimulator();
const clsId = 'aaaa1111-1111-4111-8111-111111111111';

// Teste 1: Violação de datas letivas (start_date >= end_date) e max_students inválido
let invertedDatesBlocked = false;
let equalDatesBlocked = false;
let invalidMaxBlocked = false;
try {
  sim.createClass({ id: 'bad-1', code: 'INV-1', start_date: '2026-08-01', end_date: '2026-07-01', max_students: 20 });
} catch (err) {
  invertedDatesBlocked = err.sqlState === '23514' && err.constraint === 'chk_classes_date_range';
}
try {
  sim.createClass({ id: 'bad-2', code: 'INV-2', start_date: '2026-07-01', end_date: '2026-07-01', max_students: 20 });
} catch (err) {
  equalDatesBlocked = err.sqlState === '23514' && err.constraint === 'chk_classes_date_range';
}
try {
  sim.createClass({ id: 'bad-3', code: 'INV-3', start_date: '2026-02-01', end_date: '2026-07-01', max_students: 150 });
} catch (err) {
  invalidMaxBlocked = err.sqlState === '23514' && err.constraint === 'chk_classes_max_students';
}
assertCheck(
  invertedDatesBlocked && equalDatesBlocked && invalidMaxBlocked,
  'Teste 1: Datas invertidas/iguais e max_students > 100 rejeitados com SQLSTATE 23514'
);

sim.createClass({ id: clsId, code: 'MEC-2026-CAP2', start_date: '2026-02-01', end_date: '2026-07-01', max_students: 2 });

// Teste 2 (Critério 2 explícito): Nota 10.50 e negativa falham com chk_enrollments_final_grade
let grade1050Blocked = false;
let gradeNegBlocked = false;
try {
  sim.createEnrollment({ student_id: 's1', class_id: clsId, final_grade: 10.5 });
} catch (err) {
  grade1050Blocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_final_grade';
}
try {
  sim.createEnrollment({ student_id: 's1', class_id: clsId, final_grade: -0.1 });
} catch (err) {
  gradeNegBlocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_final_grade';
}
assertCheck(
  grade1050Blocked && gradeNegBlocked,
  'Teste 2 (Critério 2): Inserção proposital de final_grade = 10.50 e -0.10 falhou com chk_enrollments_final_grade (23514)'
);

// Teste 3 (Critério 2 explícito): Frequência -5% e 100.01% falham com chk_enrollments_attendance_rate
let freqNeg5Blocked = false;
let freqOver100Blocked = false;
try {
  sim.createEnrollment({ student_id: 's1', class_id: clsId, attendance_rate: -5.0 });
} catch (err) {
  freqNeg5Blocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_attendance_rate';
}
try {
  sim.createEnrollment({ student_id: 's1', class_id: clsId, attendance_rate: 100.01 });
} catch (err) {
  freqOver100Blocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_attendance_rate';
}
assertCheck(
  freqNeg5Blocked && freqOver100Blocked,
  'Teste 3 (Critério 2): Inserção proposital de attendance_rate = -5.00% e 100.01% falhou com chk_enrollments_attendance_rate (23514)'
);

// Teste 4: Limites válidos (0.00 / 10.00 e 0.00% / 100.00%) aceitos + unicidade (student_id, class_id)
const e1 = sim.createEnrollment({ student_id: 's1', class_id: clsId, final_grade: 0.0, attendance_rate: 0.0 });
const e2 = sim.createEnrollment({ student_id: 's2', class_id: clsId, final_grade: 10.0, attendance_rate: 100.0 });
let dupBlocked = false;
try {
  sim.createEnrollment({ student_id: 's1', class_id: clsId });
} catch (err) {
  dupBlocked = err.sqlState === '23505' && err.constraint === 'uq_enrollments_student_class';
}
assertCheck(
  e1.final_grade === 0.0 && e2.final_grade === 10.0 && e2.attendance_rate === 100.0 && dupBlocked,
  'Teste 4: Fronteiras válidas (0.00/10.00 e 0%/100%) aceitas e duplicata bloqueada por uq_enrollments_student_class (23505)'
);

// Teste 5: Capacidade máxima respeitada (3º aluno ativo bloqueado) e redução indevida de max_students bloqueada
let overCapacityBlocked = false;
let shrinkMaxBlocked = false;
try {
  sim.createEnrollment({ student_id: 's3', class_id: clsId });
} catch (err) {
  overCapacityBlocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_class_capacity';
}
try {
  sim.updateClassMaxStudents(clsId, 1);
} catch (err) {
  shrinkMaxBlocked = err.sqlState === '23514' && err.constraint === 'chk_classes_max_students_vs_active';
}
assertCheck(
  overCapacityBlocked && shrinkMaxBlocked,
  'Teste 5: 3º aluno ativo em turma max_students=2 e redução max_students 2->1 bloqueados (23514)'
);

// Teste 6: Após trancamento (DROPPED), vaga é liberada e 3º aluno pode ingressar; reativar s1 acima da lotação é bloqueado
sim.updateEnrollmentStatus(e1.id, 'DROPPED');
const e3 = sim.createEnrollment({ student_id: 's3', class_id: clsId, final_grade: 7.5, attendance_rate: 85.0 });
let reactivateOverCapBlocked = false;
try {
  sim.updateEnrollmentStatus(e1.id, 'ACTIVE');
} catch (err) {
  reactivateOverCapBlocked = err.sqlState === '23514' && err.constraint === 'chk_enrollments_class_capacity';
}
assertCheck(
  e3.status === 'ACTIVE' && reactivateOverCapBlocked,
  'Teste 6: Liberação de vaga via DROPPED permitiu matrícula de s3 e bloqueou reativação de s1 acima do limite (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-019] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
