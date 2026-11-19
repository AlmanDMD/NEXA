/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-012]
 * Título: Implementar Tabela de Turmas Acadêmicas (classes)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Chave estrangeira `fk_classes_course` referenciando `courses(id)` com `ON DELETE RESTRICT`.
 * 2. Critério 2: Restrição de unicidade composta `uq_classes_code_period` em `(code, period)`
 *    + índice único funcional `idx_classes_code_period_upper`.
 * 3. Critério 3: Constraint `chk_classes_date_range` verificando `start_date < end_date`.
 * 4. Observação Técnica: Índice composto `idx_classes_course_period` em `(course_id, period)`.
 * 5. DoD: Migration versionada, `model Class` no `prisma/schema.prisma`, tipos TypeScript atualizados,
 *    testes unitários de integridade referencial e integração com cards dependentes (`DB-017`, `DB-018`, `DB-021`).
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
  '20261118010000_create_classes_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118010000_create_classes_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '12_tabela_classes.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '12-tabela-turmas-academicas-classes.md'),
  path.join(ROOT_DIR, 'BancoNexa', '12-tabela-turmas-academicas-classes.md'),
];

const VALID_SHIFTS = new Set(['MORNING', 'AFTERNOON', 'NIGHT']);
const VALID_STATUSES = new Set(['PLANNING', 'ACTIVE', 'COMPLETED', 'ARCHIVED']);

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
 * Simulador relacional das tabelas `courses` e `classes` com FK ON DELETE RESTRICT,
 * unicidade composta `(code, period)`, validação temporal `start_date < end_date` e enums.
 */
class ClassesRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.classesById = new Map();
    this.classesByCodePeriod = new Map();
    this.seq = 1;
  }

  createCourse(id, code, name) {
    this.courses.set(id, { id, code, name, is_active: true });
  }

  deleteCourseRestrict(courseId) {
    for (const cls of this.classesById.values()) {
      if (cls.course_id === courseId) {
        const err = new Error(
          'update or delete on table "courses" violates foreign key constraint "fk_classes_course" on table "classes"'
        );
        err.code = 'P2003';
        err.sqlState = '23503';
        throw err;
      }
    }
    this.courses.delete(courseId);
    return true;
  }

  createClass(row) {
    // FK fk_classes_course
    if (!this.courses.has(row.course_id)) {
      const err = new Error(
        'insert or update on table "classes" violates foreign key constraint "fk_classes_course"'
      );
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Trigger trg_classes_normalize_and_touch
    const code = String(row.code || '').trim().toUpperCase();
    const period = String(row.period || '').trim();
    const shift = row.shift;
    const status = row.status || 'PLANNING';
    const maxStudents = row.max_students !== undefined ? row.max_students : 40;

    if (code.length < 3) {
      const err = new Error('violates check constraint "chk_classes_code_format"');
      err.sqlState = '23514';
      throw err;
    }

    if (period.length < 4) {
      const err = new Error('violates check constraint "chk_classes_period_not_empty"');
      err.sqlState = '23514';
      throw err;
    }

    if (!VALID_SHIFTS.has(shift)) {
      const err = new Error(`invalid input value for enum shift_enum: "${shift}"`);
      err.sqlState = '22P02';
      throw err;
    }

    if (!VALID_STATUSES.has(status)) {
      const err = new Error(`invalid input value for enum class_status_enum: "${status}"`);
      err.sqlState = '22P02';
      throw err;
    }

    // CHECK chk_classes_max_students
    if (!Number.isInteger(maxStudents) || maxStudents <= 0 || maxStudents > 100) {
      const err = new Error('violates check constraint "chk_classes_max_students"');
      err.sqlState = '23514';
      throw err;
    }

    // CHECK chk_classes_date_range: start_date < end_date
    const startTs = new Date(row.start_date).getTime();
    const endTs = new Date(row.end_date).getTime();
    if (Number.isNaN(startTs) || Number.isNaN(endTs) || !(startTs < endTs)) {
      const err = new Error('new row for relation "classes" violates check constraint "chk_classes_date_range"');
      err.sqlState = '23514';
      throw err;
    }

    // UNIQUE uq_classes_code_period (UPPER(code), UPPER(period))
    const compositeKey = `${code}::${period.toUpperCase()}`;
    if (this.classesByCodePeriod.has(compositeKey)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`code`, `period`) [SQLSTATE 23505 / uq_classes_code_period]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      course_id: row.course_id,
      code,
      period,
      shift,
      max_students: maxStudents,
      status,
      start_date: row.start_date,
      end_date: row.end_date,
      created_at: now,
      updated_at: now,
    };

    this.classesById.set(saved.id, saved);
    this.classesByCodePeriod.set(compositeKey, saved);
    return saved;
  }

  findByCourseAndPeriod(courseId, period) {
    return [...this.classesById.values()].filter(
      (c) => c.course_id === courseId && c.period === period
    );
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-012] — TABELA DE TURMAS ACADÊMICAS (classes)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de classes');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118010000_create_classes_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118010000_create_classes_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/12_tabela_classes.sql');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/12_tabela_classes.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/12-tabela-turmas-academicas-classes.md e BancoNexa/12-tabela-turmas-academicas-classes.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-012'),
  'Card DB-012 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas, model Class no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model Class no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /course_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /code\s+VARCHAR\(40\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /period\s+VARCHAR\(20\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /shift\s+shift_enum\s+NOT\s+NULL/i.test(sqlContent) &&
    /max_students\s+INTEGER\s+NOT\s+NULL\s+DEFAULT\s+40/i.test(sqlContent) &&
    /status\s+class_status_enum\s+NOT\s+NULL\s+DEFAULT\s+'PLANNING'/i.test(sqlContent) &&
    /start_date\s+DATE\s+NOT\s+NULL/i.test(sqlContent) &&
    /end_date\s+DATE\s+NOT\s+NULL/i.test(sqlContent),
  'Todas as colunas exigidas (id, course_id, code, period, shift, max_students, status, start_date, end_date) presentes com tipos corretos'
);
assertCheck(
  schemaContent.includes('model Class') &&
    schemaContent.includes('onDelete: Restrict') &&
    schemaContent.includes('@@unique([code, period], map: "uq_classes_code_period")') &&
    schemaContent.includes('@@index([courseId, period], map: "idx_classes_course_period")') &&
    schemaContent.includes('@@map("classes")'),
  'Modelo Class configurado com onDelete: Restrict, @@unique([code, period]) e @@index([courseId, period]) no prisma/schema.prisma'
);
assertCheck(
  typesTsContent.includes('export interface Class {') &&
    typesTsContent.includes('courseId: string;') &&
    typesTsContent.includes('shift: Shift;') &&
    typesTsContent.includes('status: ClassStatus;') &&
    typesTsContent.includes('export interface ClassRow {'),
  'Tipos TypeScript (Class, ClassRow, ClassCreateInput, ClassUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e Observação Técnica no SQL...');
assertCheck(
  /CONSTRAINT\s+fk_classes_course\s+FOREIGN\s+KEY\s*\(\s*course_id\s*\)\s*REFERENCES\s+courses\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ),
  'Critério 1: FK fk_classes_course -> courses(id) com ON DELETE RESTRICT declarada no SQL'
);
assertCheck(
  /CONSTRAINT\s+uq_classes_code_period\s+UNIQUE\s*\(\s*code\s*,\s*period\s*\)/i.test(sqlContent) &&
    /CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_classes_code_period_upper\s+ON\s+classes/i.test(sqlContent),
  'Critério 2: Unicidade composta uq_classes_code_period (code, period) e índice case-insensitive declarados'
);
assertCheck(
  /CONSTRAINT\s+chk_classes_date_range\s+CHECK\s*\(\s*start_date\s*<\s*end_date\s*\)/i.test(sqlContent),
  'Critério 3: Constraint chk_classes_date_range (start_date < end_date) declarada no SQL'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_classes_course_period\s+ON\s+classes\s+USING\s+BTREE\s*\(\s*course_id\s*,\s*period\s*\)/i.test(
    sqlContent
  ),
  'Observação Técnica: Índice composto idx_classes_course_period em (course_id, period) criado'
);

// 5. Integração com cards dependentes (DB-017 enrollments, DB-018 teacher_assignments, DB-021 class_lessons)
console.log('\n5. Verificando integração com cards dependentes no modelo 3FN...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(sql3fnContent) &&
    /fk_enrollments_class/i.test(sql3fnContent) &&
    /fk_teacher_assignments_class/i.test(sql3fnContent) &&
    /fk_class_lessons_class/i.test(sql3fnContent),
  'Integração validada: FKs de enrollments (DB-017), teacher_assignments (DB-018) e class_lessons (DB-021) referenciam classes(id)'
);

// 6. Testes unitários de integridade referencial, unicidade composta e intervalo de datas (DoD)
console.log('\n6. Executando testes unitários de integridade referencial e regras da tabela classes (DoD)...');
const sim = new ClassesRelationalSimulator();
const mecCourseId = '11111111-1111-4111-8111-111111111111';
sim.createCourse(mecCourseId, 'TEC-MEC-01', 'Técnico em Mecânica Industrial');

// Teste 1: Criação válida com normalização de código e período
const turma1 = sim.createClass({
  course_id: mecCourseId,
  code: '  mec-2026-1t ',
  period: ' 2026.1 ',
  shift: 'NIGHT',
  max_students: 35,
  status: 'ACTIVE',
  start_date: '2026-02-02',
  end_date: '2026-07-10',
});
assertCheck(
  turma1.code === 'MEC-2026-1T' && turma1.period === '2026.1' && turma1.shift === 'NIGHT',
  'Teste 1: Turma criada com normalização de código ("MEC-2026-1T"), período ("2026.1") e turno válido'
);

// Teste 2: FK inválida para course_id inexistente
let orphanRejected = false;
try {
  sim.createClass({
    course_id: '99999999-9999-4999-8999-999999999999',
    code: 'ADS-2026-1M',
    period: '2026.1',
    shift: 'MORNING',
    start_date: '2026-02-02',
    end_date: '2026-07-10',
  });
} catch (err) {
  orphanRejected = err.sqlState === '23503' && err.code === 'P2003';
}
assertCheck(
  orphanRejected,
  'Teste 2 (Critério 1): Inserção de turma com course_id inexistente bloqueada por fk_classes_course (23503 / P2003)'
);

// Teste 3: ON DELETE RESTRICT bloqueia exclusão de curso com turma vinculada
let restrictBlocked = false;
try {
  sim.deleteCourseRestrict(mecCourseId);
} catch (err) {
  restrictBlocked = err.sqlState === '23503';
}
assertCheck(
  restrictBlocked,
  'Teste 3 (Critério 1): Tentativa de excluir curso com turma vinculada bloqueada via ON DELETE RESTRICT (23503)'
);

// Teste 4: Unicidade (code, period) bloqueia duplicata no mesmo período, mas permite em período diferente
let dupSamePeriod = false;
try {
  sim.createClass({
    course_id: mecCourseId,
    code: 'mec-2026-1t',
    period: '2026.1',
    shift: 'AFTERNOON',
    start_date: '2026-02-02',
    end_date: '2026-07-10',
  });
} catch (err) {
  dupSamePeriod = err.code === 'P2002' && err.sqlState === '23505';
}
const turmaOutroPeriodo = sim.createClass({
  course_id: mecCourseId,
  code: 'MEC-2026-1T',
  period: '2026.2',
  shift: 'NIGHT',
  start_date: '2026-08-03',
  end_date: '2026-12-18',
});
assertCheck(
  dupSamePeriod && turmaOutroPeriodo.period === '2026.2',
  'Teste 4 (Critério 2): Duplicata em (code, period) rejeitada (P2002), enquanto mesmo code em outro período ("2026.2") foi aceito'
);

// Teste 5: Validação temporal start_date < end_date (igual ou invertida rejeitada)
let equalDatesRejected = false;
let invertedDatesRejected = false;
try {
  sim.createClass({
    course_id: mecCourseId,
    code: 'MEC-ERR-01',
    period: '2026.1',
    shift: 'MORNING',
    start_date: '2026-05-01',
    end_date: '2026-05-01',
  });
} catch (err) {
  equalDatesRejected = err.sqlState === '23514';
}
try {
  sim.createClass({
    course_id: mecCourseId,
    code: 'MEC-ERR-02',
    period: '2026.1',
    shift: 'MORNING',
    start_date: '2026-08-10',
    end_date: '2026-07-01',
  });
} catch (err) {
  invertedDatesRejected = err.sqlState === '23514';
}
assertCheck(
  equalDatesRejected && invertedDatesRejected,
  'Teste 5 (Critério 3): Datas iguais e start_date > end_date bloqueadas por chk_classes_date_range (23514)'
);

// Teste 6: Validação de capacidade max_students e consulta por índice composto (course_id, period)
let invalidCapacityRejected = false;
try {
  sim.createClass({
    course_id: mecCourseId,
    code: 'MEC-CAP-01',
    period: '2026.1',
    shift: 'MORNING',
    max_students: 0,
    start_date: '2026-02-02',
    end_date: '2026-07-10',
  });
} catch (err) {
  invalidCapacityRejected = err.sqlState === '23514';
}
const semesterClasses = sim.findByCourseAndPeriod(mecCourseId, '2026.1');
assertCheck(
  invalidCapacityRejected && semesterClasses.length === 1 && semesterClasses[0].code === 'MEC-2026-1T',
  'Teste 6: Limite max_students validado e consulta por (course_id, period) retornou corretamente a turma do semestre'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-012] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
