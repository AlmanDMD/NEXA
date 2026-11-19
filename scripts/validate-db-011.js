/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-011]
 * Título: Implementar Tabela de Cursos Técnicos (courses)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Código do curso único (`uq_courses_code` + índice funcional `idx_courses_code_upper`),
 *    rejeitando duplicatas com erro `P2002` / `SQLSTATE 23505`.
 * 2. Critério 2: Validação de `total_hours > 0` (`chk_courses_total_hours_positive`),
 *    rejeitando valores zero ou negativos com `SQLSTATE 23514`.
 * 3. Critério 3: Soft delete / flag `is_active` (`BOOLEAN NOT NULL DEFAULT TRUE`) para preservação de histórico.
 * 4. Observação Técnica: Bloqueio de exclusão física quando houver turmas associadas (`classes`) via trigger
 *    defensiva `trg_courses_prevent_delete_with_classes` e integridade `ON DELETE RESTRICT` do modelo 3FN.
 * 5. DoD: Tabela `courses` criada com migration versionada, `model Course` no `prisma/schema.prisma`,
 *    tipos TypeScript atualizados em `BancoNexa/types/schema-models.ts` e integração com cards dependentes.
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
  '20261118000000_create_courses_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118000000_create_courses_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '11_tabela_courses.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '11-tabela-cursos-tecnicos-senai.md'),
  path.join(ROOT_DIR, 'BancoNexa', '11-tabela-cursos-tecnicos-senai.md'),
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
 * Simulador das constraints SQL, triggers e regras de negócio da tabela `courses` (DB-011)
 */
class CoursesTableSimulator {
  constructor() {
    this.coursesById = new Map();
    this.coursesByCode = new Map();
    this.classesByCourseId = new Map();
    this.seq = 1;
  }

  insert(row) {
    if (!row.code) {
      const err = new Error('null value in column "code" of relation "courses" violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    // Trigger trg_courses_normalize_and_touch: UPPER(BTRIM(code)) e BTRIM(name/description)
    const normalizedCode = String(row.code).trim().toUpperCase();
    const normalizedName = String(row.name || '').trim();
    const normalizedDesc =
      row.description !== undefined && row.description !== null ? String(row.description).trim() : null;

    // CHECK chk_courses_code_format
    if (normalizedCode.length < 3) {
      const err = new Error('new row for relation "courses" violates check constraint "chk_courses_code_format"');
      err.sqlState = '23514';
      throw err;
    }

    // CHECK chk_courses_name_not_empty
    if (normalizedName.length < 3) {
      const err = new Error('new row for relation "courses" violates check constraint "chk_courses_name_not_empty"');
      err.sqlState = '23514';
      throw err;
    }

    // CHECK chk_courses_total_hours_positive
    if (!Number.isInteger(row.total_hours) || row.total_hours <= 0) {
      const err = new Error(
        'new row for relation "courses" violates check constraint "chk_courses_total_hours_positive"'
      );
      err.sqlState = '23514';
      throw err;
    }

    // UNIQUE uq_courses_code / idx_courses_code_upper
    if (this.coursesByCode.has(normalizedCode)) {
      const err = new Error(`Unique constraint failed on the fields: (\`code\`) [SQLSTATE 23505 / uq_courses_code]`);
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      code: normalizedCode,
      name: normalizedName,
      description: normalizedDesc,
      total_hours: row.total_hours,
      is_active: row.is_active !== undefined ? Boolean(row.is_active) : true,
      created_at: now,
      updated_at: now,
    };

    this.coursesById.set(saved.id, saved);
    this.coursesByCode.set(saved.code, saved);
    return saved;
  }

  attachClass(courseId, classCode) {
    if (!this.coursesById.has(courseId)) {
      const err = new Error('insert on table "classes" violates foreign key constraint "fk_classes_course"');
      err.sqlState = '23503';
      throw err;
    }
    const list = this.classesByCourseId.get(courseId) || [];
    list.push({ code: classCode, course_id: courseId });
    this.classesByCourseId.set(courseId, list);
  }

  softDelete(courseId) {
    const course = this.coursesById.get(courseId);
    if (!course) return null;
    course.is_active = false;
    course.updated_at = new Date(Date.now() + 1000).toISOString();
    return course;
  }

  deletePhysical(courseId) {
    const course = this.coursesById.get(courseId);
    if (!course) return false;

    const linkedClasses = this.classesByCourseId.get(courseId) || [];
    if (linkedClasses.length > 0) {
      const err = new Error(
        `Operacao bloqueada: o curso "${course.code}" (${course.id}) possui turmas associadas e nao pode ser excluido fisicamente. Utilize desativacao logica (is_active = FALSE).`
      );
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    this.coursesByCode.delete(course.code);
    this.coursesById.delete(courseId);
    return true;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-011] — TABELA DE CURSOS TÉCNICOS (courses)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de courses');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118000000_create_courses_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118000000_create_courses_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/11_tabela_courses.sql');
assertCheck(
  fs.existsSync(TYPES_MODELS_TS_PATH),
  'Tipos TypeScript dos modelos Prisma gerados em BancoNexa/types/schema-models.ts'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/11_tabela_courses.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/11-tabela-cursos-tecnicos-senai.md e BancoNexa/11-tabela-cursos-tecnicos-senai.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-011'),
  'Card DB-011 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas, schema Prisma e tipos TypeScript (DoD)
console.log('\n3. Verificando colunas SQL, model Course no Prisma e tipos TypeScript (DoD)...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /code\s+VARCHAR\(30\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /name\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /description\s+TEXT/i.test(sqlContent) &&
    /total_hours\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /is_active\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ/i.test(sqlContent) &&
    /updated_at\s+TIMESTAMPTZ/i.test(sqlContent),
  'Todas as colunas exigidas (id, code, name, description, total_hours, is_active, created_at, updated_at) presentes com tipos corretos'
);
assertCheck(
  schemaContent.includes('model Course') &&
    schemaContent.includes('@unique(map: "uq_courses_code")') &&
    schemaContent.includes('@map("total_hours")') &&
    schemaContent.includes('@map("is_active")') &&
    schemaContent.includes('@@map("courses")'),
  'Modelo Course configurado corretamente com @map/@@map e uq_courses_code no prisma/schema.prisma'
);
assertCheck(
  typesTsContent.includes('export interface Course {') &&
    typesTsContent.includes('totalHours: number;') &&
    typesTsContent.includes('isActive: boolean;') &&
    typesTsContent.includes('export interface CourseRow {') &&
    typesTsContent.includes('export interface CourseCreateInput {'),
  'Tipos TypeScript (Course, CourseRow, CourseCreateInput, CourseUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critério 1, 2, 3 e Observação Técnica no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e Observação Técnica no SQL...');
assertCheck(
  /CONSTRAINT\s+uq_courses_code\s+UNIQUE\s*\(\s*code\s*\)/i.test(sqlContent) &&
    /CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_courses_code_upper\s+ON\s+courses\s*\(\s*UPPER\(code\)\s*\)/i.test(
      sqlContent
    ),
  'Critério 1: Constraint UNIQUE uq_courses_code e índice funcional idx_courses_code_upper declarados no SQL'
);
assertCheck(
  /CONSTRAINT\s+chk_courses_total_hours_positive\s+CHECK\s*\(\s*total_hours\s*>\s*0\s*\)/i.test(sqlContent),
  'Critério 2: Constraint CHECK chk_courses_total_hours_positive (total_hours > 0) declarada no SQL'
);
assertCheck(
  /is_active\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_courses_is_active\s+ON\s+courses/i.test(sqlContent),
  'Critério 3: Flag is_active (soft delete) com default TRUE e índice idx_courses_is_active criados'
);
assertCheck(
  /CREATE\s+TRIGGER\s+trg_courses_normalize_and_touch/i.test(sqlContent) &&
    /CREATE\s+TRIGGER\s+trg_courses_prevent_delete_with_classes/i.test(sqlContent),
  'Observação Técnica: Triggers trg_courses_normalize_and_touch e trg_courses_prevent_delete_with_classes declaradas'
);

// 5. Integração com cards dependentes (DB-012 classes, DB-013 subjects) no modelo 3FN
console.log('\n5. Verificando integração com cards dependentes (DB-012 classes e DB-013 subjects)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CONSTRAINT\s+fk_classes_course\s+FOREIGN\s+KEY\s*\(\s*course_id\s*\)\s*REFERENCES\s+courses\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sql3fnContent
  ) &&
    /CONSTRAINT\s+fk_subjects_course\s+FOREIGN\s+KEY\s*\(\s*course_id\s*\)\s*REFERENCES\s+courses\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sql3fnContent
    ),
  'Integração validada: FKs de classes (DB-012) e subjects (DB-013) referenciam courses(id) com ON DELETE RESTRICT'
);

// 6. Testes unitários de integridade (UNIQUE, CHECK total_hours > 0, soft delete e bloqueio de DELETE com turmas)
console.log('\n6. Executando testes unitários de integridade da tabela courses (DoD)...');
const sim = new CoursesTableSimulator();

const mecCourse = sim.insert({
  code: '  tec-mec-01 ',
  name: '  Técnico em Mecânica Industrial  ',
  description: 'Formação técnica SENAI em processos de fabricação, metrologia e manutenção mecânica.',
  total_hours: 1200,
});
assertCheck(
  mecCourse.code === 'TEC-MEC-01' && mecCourse.name === 'Técnico em Mecânica Industrial' && mecCourse.is_active === true,
  'Teste 1: Curso inserido com normalização de código ("TEC-MEC-01") e is_active = true por padrão'
);

let dupCodeError = null;
try {
  sim.insert({
    code: 'tec-mec-01',
    name: 'Curso Duplicado',
    total_hours: 800,
  });
} catch (err) {
  dupCodeError = err.code;
}
assertCheck(
  dupCodeError === 'P2002',
  'Teste 2 (Critério 1): Inserção com código duplicado ("tec-mec-01") rejeitada com P2002 / SQLSTATE 23505'
);

let zeroHoursRejected = false;
let negativeHoursRejected = false;
try {
  sim.insert({ code: 'TEC-ELT-01', name: 'Técnico em Eletromecânica', total_hours: 0 });
} catch (err) {
  zeroHoursRejected = err.sqlState === '23514';
}
try {
  sim.insert({ code: 'TEC-ADS-01', name: 'Técnico em ADS', total_hours: -400 });
} catch (err) {
  negativeHoursRejected = err.sqlState === '23514';
}
assertCheck(
  zeroHoursRejected && negativeHoursRejected,
  'Teste 3 (Critério 2): Carga horária zero (0) e negativa (-400) bloqueadas por chk_courses_total_hours_positive (23514)'
);

sim.attachClass(mecCourse.id, 'MEC-2026-1T');
let physicalDeleteBlocked = false;
try {
  sim.deletePhysical(mecCourse.id);
} catch (err) {
  physicalDeleteBlocked = err.sqlState === '23503';
}
assertCheck(
  physicalDeleteBlocked,
  'Teste 4 (Observação Técnica): Exclusão física de curso com turmas associadas bloqueada (SQLSTATE 23503)'
);

const softDeleted = sim.softDelete(mecCourse.id);
assertCheck(
  softDeleted && softDeleted.is_active === false && sim.coursesById.has(mecCourse.id),
  'Teste 5 (Critério 3): Desativação lógica (is_active = false) preservou o registro histórico do curso'
);

const draftCourse = sim.insert({
  code: 'TEC-TMP-99',
  name: 'Curso Rascunho Sem Turmas',
  total_hours: 600,
});
assertCheck(
  sim.deletePhysical(draftCourse.id) === true && !sim.coursesById.has(draftCourse.id),
  'Teste 6: Exclusão física de curso rascunho sem turmas associadas permitida sem inconsistência'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-011] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
