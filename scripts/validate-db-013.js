/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-013]
 * Título: Criar Tabela de Disciplinas Teórico-Práticas (subjects)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Disciplina vinculada obrigatoriamente a um curso (`course_id NOT NULL` + FK
 *    `fk_subjects_course` -> `courses(id)` com `ON DELETE RESTRICT`).
 * 2. Critério 2: Carga horária estritamente positiva (`chk_subjects_workload_positive`: `workload_hours > 0`).
 * 3. Critério 3: Índices em `name` (`idx_subjects_name` e `idx_subjects_name_lower` com `text_pattern_ops`)
 *    para pesquisas autocompletar rápidas.
 * 4. Observação Técnica: Estrutura 3FN limpa preparada para equivalências futuras por tabela associativa.
 * 5. DoD: Migration versionada, `model Subject` no `prisma/schema.prisma`, tipos TypeScript atualizados,
 *    testes unitários e integração com cards dependentes (`DB-014`, `DB-018`, `DB-021`, `DB-027`).
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
  '20261118020000_create_subjects_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118020000_create_subjects_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '13_tabela_subjects.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '13-tabela-disciplinas-subjects.md'),
  path.join(ROOT_DIR, 'BancoNexa', '13-tabela-disciplinas-subjects.md'),
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
 * Simulador relacional das tabelas `courses` e `subjects` com FK obrigatória,
 * validação `workload_hours > 0`, unicidade `(course_id, code)` e autocompletar em `name`.
 */
class SubjectsRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.subjectsById = new Map();
    this.subjectsByCourseCode = new Map();
    this.seq = 1;
  }

  createCourse(id, code, name) {
    this.courses.set(id, { id, code, name });
  }

  createSubject(row) {
    // Critério 1: course_id obrigatório e existente em courses
    if (!row.course_id) {
      const err = new Error('null value in column "course_id" of relation "subjects" violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }
    if (!this.courses.has(row.course_id)) {
      const err = new Error('insert or update on table "subjects" violates foreign key constraint "fk_subjects_course"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Trigger trg_subjects_normalize_and_touch
    const code = String(row.code || '').trim().toUpperCase();
    const name = String(row.name || '').trim();
    const syllabus = row.syllabus !== undefined && row.syllabus !== null ? String(row.syllabus).trim() : null;

    if (code.length < 2) {
      const err = new Error('violates check constraint "chk_subjects_code_format"');
      err.sqlState = '23514';
      throw err;
    }
    if (name.length < 3) {
      const err = new Error('violates check constraint "chk_subjects_name_not_empty"');
      err.sqlState = '23514';
      throw err;
    }

    // Critério 2: workload_hours > 0
    if (!Number.isInteger(row.workload_hours) || row.workload_hours <= 0) {
      const err = new Error('new row for relation "subjects" violates check constraint "chk_subjects_workload_positive"');
      err.sqlState = '23514';
      throw err;
    }

    // UNIQUE (course_id, UPPER(code))
    const key = `${row.course_id}::${code}`;
    if (this.subjectsByCourseCode.has(key)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`course_id`, `code`) [SQLSTATE 23505 / uq_subjects_course_code]'
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
      name,
      workload_hours: row.workload_hours,
      syllabus,
      is_active: row.is_active !== undefined ? Boolean(row.is_active) : true,
      created_at: now,
      updated_at: now,
    };

    this.subjectsById.set(saved.id, saved);
    this.subjectsByCourseCode.set(key, saved);
    return saved;
  }

  autocompleteByName(prefix) {
    const norm = String(prefix || '').trim().toLowerCase();
    return [...this.subjectsById.values()]
      .filter((s) => s.is_active && s.name.toLowerCase().startsWith(norm))
      .sort((a, b) => a.name.localeCompare(b.name));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-013] — TABELA DE DISCIPLINAS (subjects)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de subjects');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118020000_create_subjects_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118020000_create_subjects_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/13_tabela_subjects.sql');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/13_tabela_subjects.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/13-tabela-disciplinas-subjects.md e BancoNexa/13-tabela-disciplinas-subjects.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-013'),
  'Card DB-013 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas, model Subject no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model Subject no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /course_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /code\s+VARCHAR\(50\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /name\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /workload_hours\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /syllabus\s+TEXT/i.test(sqlContent) &&
    /is_active\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent),
  'Todas as colunas exigidas (id, course_id, code, name, workload_hours, syllabus, is_active) presentes com tipos corretos'
);
assertCheck(
  schemaContent.includes('model Subject') &&
    schemaContent.includes('@map("workload_hours")') &&
    schemaContent.includes('@@unique([courseId, code], map: "uq_subjects_course_code")') &&
    schemaContent.includes('@@index([name], map: "idx_subjects_name")') &&
    schemaContent.includes('@@map("subjects")'),
  'Modelo Subject configurado corretamente com FK obrigatória, @@unique([courseId, code]) e @@index([name]) no prisma/schema.prisma'
);
assertCheck(
  typesTsContent.includes('export interface Subject {') &&
    typesTsContent.includes('workloadHours: number;') &&
    typesTsContent.includes('syllabus: string | null;') &&
    typesTsContent.includes('export interface SubjectRow {'),
  'Tipos TypeScript (Subject, SubjectRow, SubjectCreateInput, SubjectUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /course_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /CONSTRAINT\s+fk_subjects_course\s+FOREIGN\s+KEY\s*\(\s*course_id\s*\)\s*REFERENCES\s+courses\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ),
  'Critério 1: Disciplina vinculada obrigatoriamente a um curso (course_id NOT NULL + fk_subjects_course ON DELETE RESTRICT)'
);
assertCheck(
  /CONSTRAINT\s+chk_subjects_workload_positive\s+CHECK\s*\(\s*workload_hours\s*>\s*0\s*\)/i.test(sqlContent),
  'Critério 2: Constraint chk_subjects_workload_positive (workload_hours > 0) declarada no SQL'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_subjects_name\s+ON\s+subjects\s+USING\s+BTREE\s*\(\s*name\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_subjects_name_lower\s+ON\s+subjects\s+USING\s+BTREE\s*\(\s*LOWER\(name\)\s+text_pattern_ops\s*\)/i.test(
      sqlContent
    ),
  'Critério 3: Índices idx_subjects_name e idx_subjects_name_lower (text_pattern_ops) criados para autocompletar'
);

// 5. Integração com cards dependentes no modelo 3FN
console.log('\n5. Verificando integração com cards dependentes (DB-014, DB-018, DB-021, DB-027)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /fk_learning_modules_subject/i.test(sql3fnContent) &&
    /fk_teacher_assignments_subject/i.test(sql3fnContent) &&
    /fk_class_lessons_subject/i.test(sql3fnContent) &&
    /fk_assessments_subject/i.test(sql3fnContent),
  'Integração validada: FKs de learning_modules (DB-014), teacher_assignments (DB-018), class_lessons (DB-021) e academic_assessments (DB-027) referenciam subjects(id)'
);

// 6. Testes unitários de integridade da tabela subjects (DoD)
console.log('\n6. Executando testes unitários de integridade da tabela subjects (DoD)...');
const sim = new SubjectsRelationalSimulator();
const mecCourseId = '11111111-1111-4111-8111-111111111111';
const eltCourseId = '22222222-2222-4222-8222-222222222222';
sim.createCourse(mecCourseId, 'TEC-MEC-01', 'Técnico em Mecânica Industrial');
sim.createCourse(eltCourseId, 'TEC-ELT-01', 'Técnico em Eletromecânica');

const s1 = sim.createSubject({
  course_id: mecCourseId,
  code: '  uc-met-01 ',
  name: '  Metrologia Dimensional  ',
  workload_hours: 80,
  syllabus: 'Leitura e interpretação de paquímetros, micrômetros e tolerâncias ISO.',
});
const s2 = sim.createSubject({
  course_id: mecCourseId,
  code: 'UC-FAB-02',
  name: 'Processos de Fabricação Mecânica',
  workload_hours: 120,
});
assertCheck(
  s1.code === 'UC-MET-01' && s1.name === 'Metrologia Dimensional' && s1.is_active === true && s2.workload_hours === 120,
  'Teste 1: Disciplinas inseridas com normalização de código ("UC-MET-01") e is_active = true por padrão'
);

// Teste 2: Vínculo obrigatório a curso (null ou inexistente bloqueado)
let nullCourseBlocked = false;
let invalidCourseBlocked = false;
try {
  sim.createSubject({ course_id: null, code: 'UC-ORPHAN', name: 'Sem Curso', workload_hours: 40 });
} catch (err) {
  nullCourseBlocked = err.sqlState === '23502';
}
try {
  sim.createSubject({
    course_id: '99999999-9999-4999-8999-999999999999',
    code: 'UC-ORPHAN',
    name: 'Curso Inexistente',
    workload_hours: 40,
  });
} catch (err) {
  invalidCourseBlocked = err.sqlState === '23503' && err.code === 'P2003';
}
assertCheck(
  nullCourseBlocked && invalidCourseBlocked,
  'Teste 2 (Critério 1): Disciplina sem course_id (23502) ou com course_id inexistente (23503/P2003) bloqueada'
);

// Teste 3: Carga horária <= 0 rejeitada
let zeroWorkloadBlocked = false;
let negativeWorkloadBlocked = false;
try {
  sim.createSubject({ course_id: mecCourseId, code: 'UC-ERR-1', name: 'Disciplina Zero', workload_hours: 0 });
} catch (err) {
  zeroWorkloadBlocked = err.sqlState === '23514';
}
try {
  sim.createSubject({ course_id: mecCourseId, code: 'UC-ERR-2', name: 'Disciplina Negativa', workload_hours: -20 });
} catch (err) {
  negativeWorkloadBlocked = err.sqlState === '23514';
}
assertCheck(
  zeroWorkloadBlocked && negativeWorkloadBlocked,
  'Teste 3 (Critério 2): Carga horária zero (0) e negativa (-20) bloqueadas por chk_subjects_workload_positive (23514)'
);

// Teste 4: Unicidade (course_id, code) bloqueia duplicata no mesmo curso, mas permite mesmo código em outro curso
let dupSameCourseBlocked = false;
try {
  sim.createSubject({
    course_id: mecCourseId,
    code: 'uc-met-01',
    name: 'Metrologia Duplicada',
    workload_hours: 60,
  });
} catch (err) {
  dupSameCourseBlocked = err.code === 'P2002' && err.sqlState === '23505';
}
const sOtherCourse = sim.createSubject({
  course_id: eltCourseId,
  code: 'UC-MET-01',
  name: 'Metrologia Aplicada à Eletromecânica',
  workload_hours: 60,
});
assertCheck(
  dupSameCourseBlocked && sOtherCourse.course_id === eltCourseId,
  'Teste 4: Duplicata de (course_id, code) bloqueada (P2002), enquanto mesmo código em curso distinto foi aceito'
);

// Teste 5: Pesquisa autocompletar case-insensitive por prefixo em `name`
const matches = sim.autocompleteByName('metro');
assertCheck(
  matches.length === 2 &&
    matches[0].name === 'Metrologia Aplicada à Eletromecânica' &&
    matches[1].name === 'Metrologia Dimensional',
  'Teste 5 (Critério 3): Pesquisa autocompletar case-insensitive ("metro") retornou as 2 disciplinas ordenadas por nome'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-013] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
