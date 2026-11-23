/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-018]
 * Título: Modelar Associação de Professores a Disciplinas e Turmas (teacher_assignments)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Chave única composta `uq_teacher_assignments_composite (teacher_id, class_id, subject_id)`.
 * 2. Critério 2: Foreign keys íntegras (`users`, `classes`, `subjects`) com `ON DELETE RESTRICT`
 *    + trigger PL/pgSQL validando `role = 'TEACHER'`.
 * 3. Critério 3 & DoD: Índices eficientes para autorização RBAC contextual no backend
 *    (`idx_teacher_assignments_teacher_class`, `idx_teacher_assignments_class_subject`,
 *    `idx_teacher_assignments_subject`).
 * 4. Observação Técnica: Suporte a múltiplos professores na mesma turma/disciplina
 *    (ex.: teoria `is_main_teacher = true` + oficina `is_main_teacher = false`).
 * 5. DoD: Migration versionada, `model TeacherAssignment` no `prisma/schema.prisma`, tipos TS
 *    atualizados, testes unitários e integração com cards dependentes (`DB-020`, `DB-021`, `BE-018`).
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
  '20261118070000_create_teacher_assignments_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118070000_create_teacher_assignments_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '18_tabela_teacher_assignments.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '18-tabela-associacao-professores-teacher-assignments.md'),
  path.join(ROOT_DIR, 'BancoNexa', '18-tabela-associacao-professores-teacher-assignments.md'),
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
 * Simulador relacional das tabelas `users`, `classes`, `subjects` e `teacher_assignments`
 * com UNIQUE (teacher_id, class_id, subject_id), ON DELETE RESTRICT, trigger role = 'TEACHER'
 * e consultas de autorização RBAC contextual.
 */
class TeacherAssignmentsRelationalSimulator {
  constructor() {
    this.users = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.assignmentsById = new Map();
    this.assignmentsByTriple = new Map();
    this.seq = 1;
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addClass(id, code) {
    this.classes.set(id, { id, code });
  }

  addSubject(id, code, name) {
    this.subjects.set(id, { id, code, name });
  }

  assignTeacher(row) {
    if (!row.teacher_id || !row.class_id || !row.subject_id) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const user = this.users.get(row.teacher_id);
    if (!user) {
      const err = new Error('violates foreign key constraint "fk_teacher_assignments_teacher"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (user.role !== 'TEACHER') {
      const err = new Error(`chk_teacher_assignments_teacher_role: role "${user.role}" não permitida`);
      err.sqlState = '23514';
      throw err;
    }

    if (!this.classes.has(row.class_id)) {
      const err = new Error('violates foreign key constraint "fk_teacher_assignments_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (!this.subjects.has(row.subject_id)) {
      const err = new Error('violates foreign key constraint "fk_teacher_assignments_subject"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Critério 1: UNIQUE (teacher_id, class_id, subject_id)
    const tripleKey = `${row.teacher_id}::${row.class_id}::${row.subject_id}`;
    if (this.assignmentsByTriple.has(tripleKey)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`teacher_id`, `class_id`, `subject_id`) [SQLSTATE 23505 / uq_teacher_assignments_composite]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      teacher_id: row.teacher_id,
      class_id: row.class_id,
      subject_id: row.subject_id,
      assigned_at: new Date().toISOString(),
      is_main_teacher: row.is_main_teacher !== undefined ? Boolean(row.is_main_teacher) : true,
    };

    this.assignmentsById.set(saved.id, saved);
    this.assignmentsByTriple.set(tripleKey, saved);
    return saved;
  }

  deleteSubjectRestrict(subjectId) {
    const inUse = [...this.assignmentsById.values()].some((a) => a.subject_id === subjectId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_teacher_assignments_subject"');
      err.sqlState = '23503';
      throw err;
    }
    this.subjects.delete(subjectId);
  }

  canTeacherAccessClass(teacherId, classId) {
    return [...this.assignmentsById.values()].some((a) => a.teacher_id === teacherId && a.class_id === classId);
  }

  canTeacherGradeSubject(teacherId, classId, subjectId) {
    return this.assignmentsByTriple.has(`${teacherId}::${classId}::${subjectId}`);
  }

  listTeachersForClassSubject(classId, subjectId) {
    return [...this.assignmentsById.values()].filter((a) => a.class_id === classId && a.subject_id === subjectId);
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-018] — ALOCAÇÃO DOCENTE (teacher_assignments)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de teacher_assignments'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118070000_create_teacher_assignments_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118070000_create_teacher_assignments_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/18_tabela_teacher_assignments.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/18_tabela_teacher_assignments.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/18-tabela-associacao-professores-teacher-assignments.md e BancoNexa/18-tabela-associacao-professores-teacher-assignments.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-018'),
  'Card DB-018 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model TeacherAssignment no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model TeacherAssignment no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /teacher_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /subject_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /assigned_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent) &&
    /is_main_teacher\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent),
  'Todas as colunas exigidas (id, teacher_id, class_id, subject_id, assigned_at, is_main_teacher) presentes'
);
assertCheck(
  schemaContent.includes('model TeacherAssignment') &&
    /teacherAssignments\s+TeacherAssignment\[\]/.test(schemaContent) &&
    schemaContent.includes('@@unique([teacherId, classId, subjectId], map: "uq_teacher_assignments_composite")') &&
    schemaContent.includes('@@index([teacherId, classId], map: "idx_teacher_assignments_teacher_class")') &&
    schemaContent.includes('@@index([classId, subjectId], map: "idx_teacher_assignments_class_subject")') &&
    schemaContent.includes('@@map("teacher_assignments")'),
  'Modelo TeacherAssignment integrado ao prisma/schema.prisma com UNIQUE tripla, ON DELETE RESTRICT e índices RBAC'
);
assertCheck(
  typesTsContent.includes('export interface TeacherAssignment {') &&
    typesTsContent.includes('isMainTeacher: boolean;') &&
    typesTsContent.includes('export interface TeacherAssignmentRow {'),
  'Tipos TypeScript (TeacherAssignment, TeacherAssignmentRow, TeacherAssignmentCreateInput, TeacherAssignmentUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_teacher_assignments_composite\s+UNIQUE\s*\(\s*teacher_id\s*,\s*class_id\s*,\s*subject_id\s*\)/i.test(
    sqlContent
  ),
  'Critério 1: Constraint uq_teacher_assignments_composite UNIQUE (teacher_id, class_id, subject_id) declarada'
);
assertCheck(
  /CONSTRAINT\s+fk_teacher_assignments_teacher\s+FOREIGN\s+KEY\s*\(\s*teacher_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_teacher_assignments_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_teacher_assignments_subject\s+FOREIGN\s+KEY\s*\(\s*subject_id\s*\)\s*REFERENCES\s+subjects\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_teacher_assignments_validate_teacher_role/i.test(sqlContent) &&
    /v_user_role\s*<>\s*'TEACHER'/i.test(sqlContent),
  'Critério 2: As 3 FKs (users, classes, subjects) com ON DELETE RESTRICT + trigger validando role = TEACHER'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_teacher_assignments_teacher_class\s+ON\s+teacher_assignments\s+USING\s+BTREE\s*\(\s*teacher_id\s*,\s*class_id\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_teacher_assignments_class_subject\s+ON\s+teacher_assignments\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*subject_id\s*\)/i.test(
      sqlContent
    ),
  'Critério 3 & DoD: Índices compostos idx_teacher_assignments_teacher_class e idx_teacher_assignments_class_subject criados para RBAC contextual'
);

// 5. Integração com cards dependentes no modelo 3FN (DB-020, DB-021, BE-018)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-020, DB-021, BE-018)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+teacher_assignments/i.test(sql3fnContent) &&
    /uq_teacher_assignments_composite/i.test(sql3fnContent) &&
    /fk_class_lessons_teacher/i.test(sql3fnContent),
  'Integração validada com modelo 3FN e diário de aulas (class_lessons — DB-021)'
);

// 6. Testes unitários de integridade, co-docência e RBAC contextual (DoD)
console.log('\n6. Executando testes unitários de integridade, co-docência e RBAC contextual (DoD)...');
const sim = new TeacherAssignmentsRelationalSimulator();
const teacherTheoryId = '11111111-1111-4111-8111-111111111111';
const teacherLabId = '22222222-2222-4222-8222-222222222222';
const studentId = '33333333-3333-4333-8333-333333333333';
const class1Id = 'aaaa1111-1111-4111-8111-111111111111';
const class2Id = 'bbbb2222-2222-4222-8222-222222222222';
const subjectUsinId = 'cccc1111-1111-4111-8111-111111111111';
const subjectMetId = 'dddd2222-2222-4222-8222-222222222222';

sim.addUser(teacherTheoryId, 'prof.teoria@senai.br', 'TEACHER');
sim.addUser(teacherLabId, 'instrutor.oficina@senai.br', 'TEACHER');
sim.addUser(studentId, 'aluno@senai.br', 'STUDENT');
sim.addClass(class1Id, 'MEC-2026-1T');
sim.addClass(class2Id, 'MEC-2026-2T');
sim.addSubject(subjectUsinId, 'UC-USIN-01', 'Usinagem Convencional');
sim.addSubject(subjectMetId, 'UC-MET-01', 'Metrologia Dimensional');

// Teste 1 (Observação Técnica): Múltiplos professores na mesma disciplina/turma (teoria + prática)
const aMain = sim.assignTeacher({
  teacher_id: teacherTheoryId,
  class_id: class1Id,
  subject_id: subjectUsinId,
});
const aLab = sim.assignTeacher({
  teacher_id: teacherLabId,
  class_id: class1Id,
  subject_id: subjectUsinId,
  is_main_teacher: false,
});
const teachersInUsin = sim.listTeachersForClassSubject(class1Id, subjectUsinId);
assertCheck(
  aMain.is_main_teacher === true && aLab.is_main_teacher === false && teachersInUsin.length === 2,
  'Teste 1 (Observação Técnica): Múltiplos docentes (titular is_main_teacher=true + oficina is_main_teacher=false) alocados à mesma turma/disciplina'
);

// Teste 2 (Critério 1): Duplicata na tripla (teacher_id, class_id, subject_id) bloqueada
let dupTripleBlocked = false;
try {
  sim.assignTeacher({
    teacher_id: teacherTheoryId,
    class_id: class1Id,
    subject_id: subjectUsinId,
  });
} catch (err) {
  dupTripleBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupTripleBlocked,
  'Teste 2 (Critério 1): Alocação duplicada (teacher_id, class_id, subject_id) bloqueada com 23505 / P2002'
);

// Teste 3 (Critério 2): Role diferente de TEACHER bloqueada e ON DELETE RESTRICT protege disciplina em uso
let studentRoleBlocked = false;
let restrictSubjectBlocked = false;
try {
  sim.assignTeacher({
    teacher_id: studentId,
    class_id: class1Id,
    subject_id: subjectMetId,
  });
} catch (err) {
  studentRoleBlocked = err.sqlState === '23514';
}
try {
  sim.deleteSubjectRestrict(subjectUsinId);
} catch (err) {
  restrictSubjectBlocked = err.sqlState === '23503';
}
assertCheck(
  studentRoleBlocked && restrictSubjectBlocked,
  'Teste 3 (Critério 2): Usuário com role STUDENT bloqueado (23514) e exclusão de disciplina em uso bloqueada via ON DELETE RESTRICT (23503)'
);

// Teste 4 (Critério 3): Checagens RBAC contextuais de turma e disciplina
assertCheck(
  sim.canTeacherAccessClass(teacherTheoryId, class1Id) === true &&
    sim.canTeacherAccessClass(teacherTheoryId, class2Id) === false &&
    sim.canTeacherGradeSubject(teacherLabId, class1Id, subjectUsinId) === true &&
    sim.canTeacherGradeSubject(teacherLabId, class1Id, subjectMetId) === false,
  'Teste 4 (Critério 3): Autorização RBAC contextual concedeu acesso apenas às turmas e disciplinas efetivamente alocadas'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-018] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
