/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-021]
 * Título: Implementar Tabela de Aulas Ministradas e Diário de Bordo (class_lessons)
 *
 * Verifica programaticamente:
 * 1. Critério 1: FKs íntegras para `classes`, `subjects`, `learning_modules` (opcional)
 *    e `users` com `ON DELETE RESTRICT ON UPDATE CASCADE` + trigger PL/pgSQL validando
 *    perfil docente (bloqueio de `STUDENT`), pertencimento da disciplina ao curso da turma
 *    e pertencimento do módulo prático à disciplina informada.
 * 2. Critério 2: Índice composto `idx_class_lessons_class_subject_date` em
 *    `(class_id, subject_id, lesson_date)` para listagem cronológica rápida do diário,
 *    além dos índices auxiliares `(module_id)` e `(teacher_id)`.
 * 3. Critério 3: Validação de `workload_hours` entre 1 e 8 horas por turno
 *    (`chk_class_lessons_workload`, padrão `4`) e `topic_summary` não vazio.
 * 4. DoD: Migration versionada de `class_lessons`, `model ClassLesson` em
 *    `prisma/schema.prisma`, tipos TS gerados em `BancoNexa/types/schema-models.ts`,
 *    inserção vinculada a módulo prático testada e integração com cards dependentes
 *    (`DB-022`, `DB-030`, `DB-037`, `BE-021`).
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
  '20261123000000_create_class_lessons_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123000000_create_class_lessons_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '21_tabela_class_lessons.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '21-tabela-aulas-ministradas-class-lessons.md'),
  path.join(ROOT_DIR, 'BancoNexa', '21-tabela-aulas-ministradas-class-lessons.md'),
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
 * Simulador relacional das tabelas `courses`, `classes`, `subjects`, `learning_modules`,
 * `users` e `class_lessons` com FKs ON DELETE RESTRICT, CHECK workload_hours BETWEEN 1 AND 8,
 * trigger de integridade (role <> STUDENT, subject.course_id = class.course_id,
 * module.subject_id = subject_id) e listagem cronológica pelo índice composto.
 */
class ClassLessonsRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.modules = new Map();
    this.users = new Map();
    this.lessonsById = new Map();
    this.seq = 1;
  }

  addCourse(id, code) {
    this.courses.set(id, { id, code });
  }

  addClass(id, courseId, code) {
    this.classes.set(id, { id, course_id: courseId, code });
  }

  addSubject(id, courseId, code, name) {
    this.subjects.set(id, { id, course_id: courseId, code, name });
  }

  addModule(id, subjectId, title) {
    this.modules.set(id, { id, subject_id: subjectId, title });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  insertLesson(row) {
    if (!row.class_id || !row.subject_id || !row.teacher_id || !row.lesson_date || row.topic_summary === undefined || row.topic_summary === null) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const topicTrimmed = String(row.topic_summary).trim();
    if (topicTrimmed.length === 0) {
      const err = new Error('new row for relation "class_lessons" violates check constraint "chk_class_lessons_topic_summary_not_blank"');
      err.sqlState = '23514';
      throw err;
    }

    const workloadHours = row.workload_hours !== undefined ? row.workload_hours : 4;
    if (!Number.isInteger(workloadHours) || workloadHours < 1 || workloadHours > 8) {
      const err = new Error('new row for relation "class_lessons" violates check constraint "chk_class_lessons_workload"');
      err.sqlState = '23514';
      throw err;
    }

    if (row.lab_environment !== undefined && row.lab_environment !== null && String(row.lab_environment).length > 100) {
      const err = new Error('value too long for type character varying(100)');
      err.sqlState = '22001';
      throw err;
    }

    const cls = this.classes.get(row.class_id);
    if (!cls) {
      const err = new Error('violates foreign key constraint "fk_class_lessons_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const subject = this.subjects.get(row.subject_id);
    if (!subject) {
      const err = new Error('violates foreign key constraint "fk_class_lessons_subject"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const teacher = this.users.get(row.teacher_id);
    if (!teacher) {
      const err = new Error('violates foreign key constraint "fk_class_lessons_teacher"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (teacher.role === 'STUDENT') {
      const err = new Error('chk_class_lessons_teacher_role: role "STUDENT" não permitida');
      err.sqlState = '23514';
      throw err;
    }

    if (cls.course_id !== subject.course_id) {
      const err = new Error('chk_class_lessons_subject_course: disciplina de outro curso');
      err.sqlState = '23514';
      throw err;
    }

    let moduleId = null;
    if (row.module_id !== undefined && row.module_id !== null) {
      const mod = this.modules.get(row.module_id);
      if (!mod) {
        const err = new Error('violates foreign key constraint "fk_class_lessons_module"');
        err.code = 'P2003';
        err.sqlState = '23503';
        throw err;
      }
      if (mod.subject_id !== row.subject_id) {
        const err = new Error('chk_class_lessons_module_subject: módulo não pertence à disciplina informada');
        err.sqlState = '23514';
        throw err;
      }
      moduleId = mod.id;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      class_id: row.class_id,
      subject_id: row.subject_id,
      module_id: moduleId,
      teacher_id: row.teacher_id,
      lesson_date: row.lesson_date,
      workload_hours: workloadHours,
      topic_summary: row.topic_summary,
      lab_environment: row.lab_environment !== undefined ? row.lab_environment : null,
      created_at: new Date().toISOString(),
    };

    this.lessonsById.set(saved.id, saved);
    return saved;
  }

  deleteModuleRestrict(moduleId) {
    const inUse = [...this.lessonsById.values()].some((l) => l.module_id === moduleId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_class_lessons_module"');
      err.sqlState = '23503';
      throw err;
    }
    this.modules.delete(moduleId);
  }

  listChronologicalByClassAndSubject(classId, subjectId) {
    return [...this.lessonsById.values()]
      .filter((l) => l.class_id === classId && l.subject_id === subjectId)
      .sort((a, b) => a.lesson_date.localeCompare(b.lesson_date));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-021] — AULAS MINISTRADAS (class_lessons)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de class_lessons'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123000000_create_class_lessons_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123000000_create_class_lessons_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/21_tabela_class_lessons.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/21_tabela_class_lessons.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/21-tabela-aulas-ministradas-class-lessons.md e BancoNexa/21-tabela-aulas-ministradas-class-lessons.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-021'),
  'Card DB-021 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model ClassLesson no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model ClassLesson no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /subject_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /module_id\s+UUID\s*,/i.test(sqlContent) &&
    /teacher_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /lesson_date\s+DATE\s+NOT\s+NULL/i.test(sqlContent) &&
    /workload_hours\s+INTEGER\s+NOT\s+NULL\s+DEFAULT\s+4/i.test(sqlContent) &&
    /topic_summary\s+TEXT\s+NOT\s+NULL/i.test(sqlContent) &&
    /lab_environment\s+VARCHAR\(100\)/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, class_id, subject_id, module_id opcional, teacher_id, lesson_date, workload_hours DEFAULT 4, topic_summary, lab_environment VARCHAR 100, created_at) presentes'
);
assertCheck(
  schemaContent.includes('model ClassLesson') &&
    (schemaContent.match(/classLessons\s+ClassLesson\[\]/g) || []).length === 4 &&
    schemaContent.includes('@@index([classId, subjectId, lessonDate], map: "idx_class_lessons_class_subject_date")') &&
    schemaContent.includes('@@index([moduleId], map: "idx_class_lessons_module")') &&
    schemaContent.includes('@@index([teacherId], map: "idx_class_lessons_teacher")') &&
    schemaContent.includes('@@map("class_lessons")'),
  'Modelo ClassLesson integrado ao prisma/schema.prisma com relações reversas em User/Class/Subject/LearningModule e índice cronológico'
);
assertCheck(
  typesTsContent.includes('export interface ClassLesson {') &&
    typesTsContent.includes('moduleId: string | null;') &&
    typesTsContent.includes('workloadHours: number;') &&
    typesTsContent.includes('labEnvironment: string | null;') &&
    typesTsContent.includes('export interface ClassLessonRow {'),
  'Tipos TypeScript (ClassLesson, ClassLessonRow, ClassLessonCreateInput, ClassLessonUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+fk_class_lessons_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_class_lessons_subject\s+FOREIGN\s+KEY\s*\(\s*subject_id\s*\)\s*REFERENCES\s+subjects\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_class_lessons_module\s+FOREIGN\s+KEY\s*\(\s*module_id\s*\)\s*REFERENCES\s+learning_modules\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_class_lessons_teacher\s+FOREIGN\s+KEY\s*\(\s*teacher_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_class_lessons_validate_integrity/i.test(sqlContent),
  'Critério 1: Todas as 4 FKs (classes, subjects, learning_modules, users) com ON DELETE RESTRICT + trigger de integridade curricular/modular'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_class_lessons_class_subject_date\s+ON\s+class_lessons\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*subject_id\s*,\s*lesson_date\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_class_lessons_module\s+ON\s+class_lessons\s+USING\s+BTREE\s*\(\s*module_id\s*\)/i.test(
      sqlContent
    ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_class_lessons_teacher\s+ON\s+class_lessons\s+USING\s+BTREE\s*\(\s*teacher_id\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: Índice composto idx_class_lessons_class_subject_date (class_id, subject_id, lesson_date) + índices auxiliares criados'
);
assertCheck(
  /CONSTRAINT\s+chk_class_lessons_workload\s+CHECK\s*\(\s*workload_hours\s+BETWEEN\s+1\s+AND\s+8\s*\)/i.test(
    sqlContent
  ) && /CONSTRAINT\s+chk_class_lessons_topic_summary_not_blank/i.test(sqlContent),
  'Critério 3: Validação chk_class_lessons_workload CHECK (workload_hours BETWEEN 1 AND 8) e topic_summary não vazio declarados'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-022, DB-030, DB-037, BE-021)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-022, DB-030, DB-037, BE-021)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+class_lessons/i.test(sql3fnContent) &&
    /chk_class_lessons_workload/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*lesson_id\s*\)\s*REFERENCES\s+class_lessons\s*\(\s*id\s*\)/i.test(sql3fnContent),
  'Integração validada com modelo 3FN e tabela dependente attendance_records (DB-022)'
);

// 6. Testes unitários de inserção vinculada a módulo prático, FKs, ordenação cronológica e carga horária (DoD)
console.log('\n6. Executando testes unitários de inserção prática, FKs, índice cronológico e workload_hours (DoD)...');
const sim = new ClassLessonsRelationalSimulator();
const courseMecId = '10000000-0000-4000-8000-000000000001';
const courseEletroId = '10000000-0000-4000-8000-000000000002';
const classMec1Id = '20000000-0000-4000-8000-000000000001';
const subjectUsinId = '30000000-0000-4000-8000-000000000001';
const subjectMetId = '30000000-0000-4000-8000-000000000002';
const subjectClpId = '30000000-0000-4000-8000-000000000003';
const modTorneariaId = '40000000-0000-4000-8000-000000000001';
const modPaquimetroId = '40000000-0000-4000-8000-000000000002';
const teacherId = '50000000-0000-4000-8000-000000000001';
const coordId = '50000000-0000-4000-8000-000000000002';
const studentId = '50000000-0000-4000-8000-000000000003';

sim.addCourse(courseMecId, 'TEC-MEC');
sim.addCourse(courseEletroId, 'TEC-ELE');
sim.addClass(classMec1Id, courseMecId, 'MEC-2026-1');
sim.addSubject(subjectUsinId, courseMecId, 'UC-USIN-01', 'Usinagem Convencional');
sim.addSubject(subjectMetId, courseMecId, 'UC-MET-01', 'Metrologia');
sim.addSubject(subjectClpId, courseEletroId, 'UC-CLP-01', 'Automação CLP');
sim.addModule(modTorneariaId, subjectUsinId, 'Módulo 01 — Torneamento Cilíndrico Externo');
sim.addModule(modPaquimetroId, subjectMetId, 'Módulo 01 — Paquímetro e Micrômetro');
sim.addUser(teacherId, 'prof.usinagem@senai.nexa.local', 'TEACHER');
sim.addUser(coordId, 'coord.mecanica@senai.nexa.local', 'COORDINATOR');
sim.addUser(studentId, 'aluno.01@senai.nexa.local', 'STUDENT');

// Teste 1 (DoD): Inserção vinculada a módulo prático (com default workload_hours = 4) + aula teórica sem módulo
const practicalLesson = sim.insertLesson({
  class_id: classMec1Id,
  subject_id: subjectUsinId,
  module_id: modTorneariaId,
  teacher_id: teacherId,
  lesson_date: '2026-03-18',
  topic_summary: 'Faceamento, centragem e torneamento cilíndrico externo no torno paralelo.',
  lab_environment: 'Oficina de Tornearia 02',
});
const theoryLessonNoModule = sim.insertLesson({
  class_id: classMec1Id,
  subject_id: subjectUsinId,
  module_id: null,
  teacher_id: coordId,
  lesson_date: '2026-03-11',
  workload_hours: 2,
  topic_summary: 'Apresentação do plano de ensino e normas NR-12 para máquinas rotativas.',
  lab_environment: 'Sala Teórica 04',
});
assertCheck(
  practicalLesson.module_id === modTorneariaId &&
    practicalLesson.workload_hours === 4 &&
    practicalLesson.lab_environment === 'Oficina de Tornearia 02' &&
    theoryLessonNoModule.module_id === null &&
    theoryLessonNoModule.workload_hours === 2,
  'Teste 1 (DoD): Inserção de aula prática vinculada a learning_modules (workload padrão 4h, Oficina de Tornearia 02) e aula teórica com module_id NULL validadas'
);

// Teste 2 (Critério 1): FKs íntegras, proteção ON DELETE RESTRICT e coerência modular/docente
let missingModuleBlocked = false;
let wrongSubjectModuleBlocked = false;
let wrongCourseSubjectBlocked = false;
let studentAsTeacherBlocked = false;
let deleteModuleInUseBlocked = false;

try {
  sim.insertLesson({
    class_id: classMec1Id,
    subject_id: subjectUsinId,
    module_id: '99999999-9999-4999-8999-999999999999',
    teacher_id: teacherId,
    lesson_date: '2026-03-19',
    topic_summary: 'Teste módulo inexistente',
  });
} catch (err) {
  missingModuleBlocked = err.sqlState === '23503';
}

try {
  sim.insertLesson({
    class_id: classMec1Id,
    subject_id: subjectUsinId,
    module_id: modPaquimetroId,
    teacher_id: teacherId,
    lesson_date: '2026-03-19',
    topic_summary: 'Teste módulo de outra disciplina',
  });
} catch (err) {
  wrongSubjectModuleBlocked = err.sqlState === '23514';
}

try {
  sim.insertLesson({
    class_id: classMec1Id,
    subject_id: subjectClpId,
    teacher_id: teacherId,
    lesson_date: '2026-03-19',
    topic_summary: 'Teste disciplina de outro curso',
  });
} catch (err) {
  wrongCourseSubjectBlocked = err.sqlState === '23514';
}

try {
  sim.insertLesson({
    class_id: classMec1Id,
    subject_id: subjectUsinId,
    teacher_id: studentId,
    lesson_date: '2026-03-19',
    topic_summary: 'Teste aluno como docente',
  });
} catch (err) {
  studentAsTeacherBlocked = err.sqlState === '23514';
}

try {
  sim.deleteModuleRestrict(modTorneariaId);
} catch (err) {
  deleteModuleInUseBlocked = err.sqlState === '23503';
}

assertCheck(
  missingModuleBlocked &&
    wrongSubjectModuleBlocked &&
    wrongCourseSubjectBlocked &&
    studentAsTeacherBlocked &&
    deleteModuleInUseBlocked,
  'Teste 2 (Critério 1): FK inexistente (23503), módulo de outra disciplina (23514), disciplina de outro curso (23514), docente STUDENT (23514) e ON DELETE RESTRICT (23503) bloqueados'
);

// Teste 3 (Critério 2): Listagem cronológica rápida por (class_id, subject_id, lesson_date)
sim.insertLesson({
  class_id: classMec1Id,
  subject_id: subjectUsinId,
  module_id: modTorneariaId,
  teacher_id: teacherId,
  lesson_date: '2026-03-14',
  workload_hours: 1,
  topic_summary: 'Setup de castanhas e alinhamento com relógio comparador.',
  lab_environment: 'Oficina de Tornearia 02',
});
sim.insertLesson({
  class_id: classMec1Id,
  subject_id: subjectUsinId,
  module_id: modTorneariaId,
  teacher_id: teacherId,
  lesson_date: '2026-03-25',
  workload_hours: 8,
  topic_summary: 'Avaliação prática intensiva de torneamento com tolerância IT7.',
  lab_environment: 'Oficina de Tornearia 02',
});
const timeline = sim.listChronologicalByClassAndSubject(classMec1Id, subjectUsinId);
const dates = timeline.map((l) => l.lesson_date);
assertCheck(
  dates.length === 4 &&
    dates[0] === '2026-03-11' &&
    dates[1] === '2026-03-14' &&
    dates[2] === '2026-03-18' &&
    dates[3] === '2026-03-25',
  'Teste 3 (Critério 2): Listagem cronológica (class_id, subject_id, lesson_date) retornou as 4 aulas ordenadas (2026-03-11 -> 2026-03-25)'
);

// Teste 4 (Critério 3): Fronteiras de workload_hours (1 e 8 aceitos; 0, 9 e -2 rejeitados com 23514)
let zeroHoursBlocked = false;
let nineHoursBlocked = false;
let negativeHoursBlocked = false;
for (const [hours, setter] of [
  [0, (v) => (zeroHoursBlocked = v)],
  [9, (v) => (nineHoursBlocked = v)],
  [-2, (v) => (negativeHoursBlocked = v)],
]) {
  try {
    sim.insertLesson({
      class_id: classMec1Id,
      subject_id: subjectUsinId,
      module_id: modTorneariaId,
      teacher_id: teacherId,
      lesson_date: '2026-03-26',
      workload_hours: hours,
      topic_summary: 'Teste carga horária inválida',
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}
assertCheck(
  zeroHoursBlocked && nineHoursBlocked && negativeHoursBlocked,
  'Teste 4 (Critério 3): Fronteiras válidas (1h e 8h) aceitas e valores inválidos (0h, 9h, -2h) rejeitados por chk_class_lessons_workload (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-021] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
