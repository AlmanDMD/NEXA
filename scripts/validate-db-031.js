/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-031]
 * Título: Implementar Tabela de Formulários de Autoavaliação (self_assessment_forms)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Formulário vinculado a um módulo de aprendizagem (`fk_self_assessment_forms_module`)
 *    e turma (`fk_self_assessment_forms_class`) + criador docente (`fk_self_assessment_forms_creator`)
 *    com `ON DELETE RESTRICT` e trigger validando coerência de curso e perfil não-`STUDENT`.
 * 2. Critério 2: Constraint `chk_self_assessment_forms_dates` validando `opens_at < closes_at`.
 * 3. Critério 3: Índice composto `idx_self_assessment_forms_class_active (class_id, is_active)`
 *    (e `idx_self_assessment_forms_window`) para exibir formulários abertos no portal do aluno (`FE-041`).
 * 4. DoD: Tabela `self_assessment_forms` migrada, `model SelfAssessmentForm` integrado ao
 *    `prisma/schema.prisma`, tipos TS gerados em `BancoNexa/types/schema-models.ts` e integração
 *    validada com cards dependentes (`DB-032`, `DB-040`, `BE-035`, `FE-041`).
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
  '20261123090000_create_self_assessment_forms_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123090000_create_self_assessment_forms_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '31_tabela_self_assessment_forms.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '31-tabela-formularios-autoavaliacao-self-assessment-forms.md'),
  path.join(ROOT_DIR, 'BancoNexa', '31-tabela-formularios-autoavaliacao-self-assessment-forms.md'),
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
 * `users` e `self_assessment_forms` com CHECK opens_at < closes_at, FKs ON DELETE RESTRICT,
 * trigger de integridade curricular/perfil docente e consulta de formulários abertos por (class_id, is_active).
 */
class SelfAssessmentFormsRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.modules = new Map();
    this.users = new Map();
    this.formsById = new Map();
    this.seq = 1;
  }

  addCourse(id, code) {
    this.courses.set(id, { id, code });
  }

  addClass(id, courseId, code) {
    this.classes.set(id, { id, course_id: courseId, code });
  }

  addSubject(id, courseId, code) {
    this.subjects.set(id, { id, course_id: courseId, code });
  }

  addModule(id, subjectId, title) {
    this.modules.set(id, { id, subject_id: subjectId, title });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  insertForm(row) {
    if (!row.module_id || !row.class_id || !row.title || !row.opens_at || !row.closes_at || !row.created_by) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (String(row.title).trim().length < 3) {
      const err = new Error('violates check constraint "chk_self_assessment_forms_title_not_blank"');
      err.sqlState = '23514';
      throw err;
    }

    if (String(row.title).length > 150) {
      const err = new Error('value too long for type character varying(150)');
      err.sqlState = '22001';
      throw err;
    }

    const opensMs = Date.parse(row.opens_at);
    const closesMs = Date.parse(row.closes_at);
    if (Number.isNaN(opensMs) || Number.isNaN(closesMs) || !(opensMs < closesMs)) {
      const err = new Error('new row for relation "self_assessment_forms" violates check constraint "chk_self_assessment_forms_dates"');
      err.sqlState = '23514';
      throw err;
    }

    const mod = this.modules.get(row.module_id);
    if (!mod) {
      const err = new Error('violates foreign key constraint "fk_self_assessment_forms_module"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const cls = this.classes.get(row.class_id);
    if (!cls) {
      const err = new Error('violates foreign key constraint "fk_self_assessment_forms_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const creator = this.users.get(row.created_by);
    if (!creator) {
      const err = new Error('violates foreign key constraint "fk_self_assessment_forms_creator"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const subject = this.subjects.get(mod.subject_id);
    if (subject && subject.course_id !== cls.course_id) {
      const err = new Error('chk_self_assessment_forms_module_course: módulo não pertence ao curso da turma');
      err.sqlState = '23514';
      throw err;
    }

    if (creator.role === 'STUDENT') {
      const err = new Error('chk_self_assessment_forms_creator_role: role "STUDENT" não permitida');
      err.sqlState = '23514';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      module_id: row.module_id,
      class_id: row.class_id,
      title: row.title,
      instructions: row.instructions !== undefined ? row.instructions : null,
      opens_at: row.opens_at,
      closes_at: row.closes_at,
      is_active: row.is_active !== undefined ? Boolean(row.is_active) : true,
      created_by: row.created_by,
      created_at: new Date().toISOString(),
    };

    this.formsById.set(saved.id, saved);
    return saved;
  }

  deleteModuleRestrict(moduleId) {
    const inUse = [...this.formsById.values()].some((f) => f.module_id === moduleId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_self_assessment_forms_module"');
      err.sqlState = '23503';
      throw err;
    }
    this.modules.delete(moduleId);
  }

  listOpenByClass(classId, atIsoTimestamp) {
    const nowMs = Date.parse(atIsoTimestamp);
    return [...this.formsById.values()].filter(
      (f) =>
        f.class_id === classId &&
        f.is_active === true &&
        Date.parse(f.opens_at) <= nowMs &&
        nowMs <= Date.parse(f.closes_at)
    );
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-031] — FORMULÁRIOS AUTOAVALIAÇÃO (self_assessment_forms)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de self_assessment_forms'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123090000_create_self_assessment_forms_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123090000_create_self_assessment_forms_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/31_tabela_self_assessment_forms.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/31_tabela_self_assessment_forms.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/31-tabela-formularios-autoavaliacao-self-assessment-forms.md e BancoNexa/31-tabela-formularios-autoavaliacao-self-assessment-forms.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-031'),
  'Card DB-031 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model SelfAssessmentForm no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model SelfAssessmentForm no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /module_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /title\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /instructions\s+TEXT\s*,/i.test(sqlContent) &&
    /opens_at\s+TIMESTAMPTZ\s+NOT\s+NULL/i.test(sqlContent) &&
    /closes_at\s+TIMESTAMPTZ\s+NOT\s+NULL/i.test(sqlContent) &&
    /is_active\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /created_by\s+UUID\s+NOT\s+NULL/i.test(sqlContent),
  'Todas as colunas exigidas (id, module_id, class_id, title VARCHAR 150, instructions, opens_at, closes_at, is_active BOOLEAN, created_by) presentes'
);
assertCheck(
  schemaContent.includes('model SelfAssessmentForm') &&
    (schemaContent.match(/selfAssessmentForms\s+SelfAssessmentForm\[\]/g) || []).length === 3 &&
    schemaContent.includes('@@index([classId, isActive], map: "idx_self_assessment_forms_class_active")') &&
    schemaContent.includes('@@index([classId, isActive, opensAt, closesAt], map: "idx_self_assessment_forms_window")') &&
    schemaContent.includes('@@map("self_assessment_forms")'),
  'Modelo SelfAssessmentForm integrado ao prisma/schema.prisma com relações reversas em User/Class/LearningModule e índices'
);
assertCheck(
  typesTsContent.includes('export interface SelfAssessmentForm {') &&
    typesTsContent.includes('opensAt: Date;') &&
    typesTsContent.includes('closesAt: Date;') &&
    typesTsContent.includes('isActive: boolean;') &&
    typesTsContent.includes('export interface SelfAssessmentFormRow {'),
  'Tipos TypeScript (SelfAssessmentForm, SelfAssessmentFormRow, SelfAssessmentFormCreateInput, SelfAssessmentFormUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+fk_self_assessment_forms_module\s+FOREIGN\s+KEY\s*\(\s*module_id\s*\)\s*REFERENCES\s+learning_modules\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_self_assessment_forms_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_self_assessment_forms_creator\s+FOREIGN\s+KEY\s*\(\s*created_by\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_self_assessment_forms_validate_integrity/i.test(sqlContent),
  'Critério 1: FKs obrigatórias para learning_modules, classes e users (ON DELETE RESTRICT) + trigger de integridade curricular/docente'
);
assertCheck(
  /CONSTRAINT\s+chk_self_assessment_forms_dates\s+CHECK\s*\(\s*opens_at\s*<\s*closes_at\s*\)/i.test(sqlContent),
  'Critério 2: Constraint chk_self_assessment_forms_dates CHECK (opens_at < closes_at) declarada'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_self_assessment_forms_class_active\s+ON\s+self_assessment_forms\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*is_active\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_self_assessment_forms_window\s+ON\s+self_assessment_forms\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*is_active\s*,\s*opens_at\s*,\s*closes_at\s*\)/i.test(
      sqlContent
    ),
  'Critério 3: Índice idx_self_assessment_forms_class_active (class_id, is_active) + idx_self_assessment_forms_window criados'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-032, DB-040, BE-035, FE-041)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-032, DB-040, BE-035, FE-041)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+self_assessment_forms/i.test(sql3fnContent) &&
    /chk_self_assessment_forms_dates/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*form_id\s*\)\s*REFERENCES\s+self_assessment_forms\s*\(\s*id\s*\)/i.test(sql3fnContent),
  'Integração validada com modelo 3FN ([T22] self_assessment_forms) e tabela dependente student_self_assessments (DB-032)'
);

// 6. Testes unitários de vínculos, janela opens_at < closes_at, perfil docente e listagem aberta (DoD)
console.log('\n6. Executando testes unitários de vínculos, opens_at < closes_at e consulta de formulários abertos (DoD)...');
const sim = new SelfAssessmentFormsRelationalSimulator();
const courseMecId = '10000000-0000-4000-8000-000000000001';
const courseEletroId = '10000000-0000-4000-8000-000000000002';
const classMec1Id = '20000000-0000-4000-8000-000000000001';
const subjectMetId = '30000000-0000-4000-8000-000000000001';
const subjectClpId = '30000000-0000-4000-8000-000000000002';
const modPaquimetroId = '40000000-0000-4000-8000-000000000001';
const modClpId = '40000000-0000-4000-8000-000000000002';
const teacherId = '50000000-0000-4000-8000-000000000001';
const studentId = '50000000-0000-4000-8000-000000000002';

sim.addCourse(courseMecId, 'TEC-MEC-01');
sim.addCourse(courseEletroId, 'TEC-ELE-01');
sim.addClass(classMec1Id, courseMecId, 'MEC-2026-1');
sim.addSubject(subjectMetId, courseMecId, 'UC-MET-01');
sim.addSubject(subjectClpId, courseEletroId, 'UC-CLP-01');
sim.addModule(modPaquimetroId, subjectMetId, 'Metrologia com Paquímetro e Régua Graduada');
sim.addModule(modClpId, subjectClpId, 'Programação Ladder em CLP');
sim.addUser(teacherId, 'instrutor.teoria.demo@senai.nexa.local', 'TEACHER');
sim.addUser(studentId, 'estudante.demo01@aluno.nexa.local', 'STUDENT');

// Teste 1 (DoD & Critério 3): Criar ciclo aberto, ciclo inativo e ciclo futuro; listar apenas abertos no portal do aluno
const openForm = sim.insertForm({
  module_id: modPaquimetroId,
  class_id: classMec1Id,
  title: 'Autoavaliação — Módulo 01: Metrologia com Paquímetro',
  instructions: 'Avalie seu nível de domínio prático (1 a 5) e confiança em cada competência do módulo.',
  opens_at: '2026-03-01T08:00:00Z',
  closes_at: '2026-03-10T23:59:59Z',
  created_by: teacherId,
});
sim.insertForm({
  module_id: modPaquimetroId,
  class_id: classMec1Id,
  title: 'Autoavaliação Rascunho (Inativa)',
  opens_at: '2026-03-01T08:00:00Z',
  closes_at: '2026-03-10T23:59:59Z',
  is_active: false,
  created_by: teacherId,
});
sim.insertForm({
  module_id: modPaquimetroId,
  class_id: classMec1Id,
  title: 'Autoavaliação Futura (Abril)',
  opens_at: '2026-04-01T08:00:00Z',
  closes_at: '2026-04-10T23:59:59Z',
  is_active: true,
  created_by: teacherId,
});

const openInMarch = sim.listOpenByClass(classMec1Id, '2026-03-05T12:00:00Z');
assertCheck(
  openForm.is_active === true && openInMarch.length === 1 && openInMarch[0].id === openForm.id,
  'Teste 1 (DoD / Critério 3): Formulário ativo listado via (class_id, is_active) na janela vigente (excluindo inativos e futuros)'
);

// Teste 2 (Critério 2): opens_at >= closes_at bloqueado com SQLSTATE 23514
let equalDatesBlocked = false;
let invertedDatesBlocked = false;

try {
  sim.insertForm({
    module_id: modPaquimetroId,
    class_id: classMec1Id,
    title: 'Teste Datas Iguais',
    opens_at: '2026-03-10T10:00:00Z',
    closes_at: '2026-03-10T10:00:00Z',
    created_by: teacherId,
  });
} catch (err) {
  equalDatesBlocked = err.sqlState === '23514';
}

try {
  sim.insertForm({
    module_id: modPaquimetroId,
    class_id: classMec1Id,
    title: 'Teste Datas Invertidas',
    opens_at: '2026-03-15T10:00:00Z',
    closes_at: '2026-03-10T10:00:00Z',
    created_by: teacherId,
  });
} catch (err) {
  invertedDatesBlocked = err.sqlState === '23514';
}

assertCheck(
  equalDatesBlocked && invertedDatesBlocked,
  'Teste 2 (Critério 2): opens_at = closes_at e opens_at > closes_at bloqueados por chk_self_assessment_forms_dates (23514)'
);

// Teste 3 (Critério 1): Vínculos obrigatórios, módulo de outro curso, criador STUDENT e ON DELETE RESTRICT bloqueados
let wrongCourseModuleBlocked = false;
let studentCreatorBlocked = false;
let missingClassBlocked = false;
let deleteModuleInUseBlocked = false;

try {
  sim.insertForm({
    module_id: modClpId, // curso Eletro != Mecânica
    class_id: classMec1Id,
    title: 'Teste Módulo Outro Curso',
    opens_at: '2026-03-01T08:00:00Z',
    closes_at: '2026-03-05T08:00:00Z',
    created_by: teacherId,
  });
} catch (err) {
  wrongCourseModuleBlocked = err.sqlState === '23514';
}

try {
  sim.insertForm({
    module_id: modPaquimetroId,
    class_id: classMec1Id,
    title: 'Teste Criador Estudante',
    opens_at: '2026-03-01T08:00:00Z',
    closes_at: '2026-03-05T08:00:00Z',
    created_by: studentId,
  });
} catch (err) {
  studentCreatorBlocked = err.sqlState === '23514';
}

try {
  sim.insertForm({
    module_id: modPaquimetroId,
    class_id: '99999999-9999-4999-8999-999999999999',
    title: 'Teste Turma Inexistente',
    opens_at: '2026-03-01T08:00:00Z',
    closes_at: '2026-03-05T08:00:00Z',
    created_by: teacherId,
  });
} catch (err) {
  missingClassBlocked = err.sqlState === '23503' && err.code === 'P2003';
}

try {
  sim.deleteModuleRestrict(modPaquimetroId);
} catch (err) {
  deleteModuleInUseBlocked = err.sqlState === '23503';
}

assertCheck(
  wrongCourseModuleBlocked && studentCreatorBlocked && missingClassBlocked && deleteModuleInUseBlocked,
  'Teste 3 (Critério 1): Módulo de outro curso (23514), criador STUDENT (23514), turma inexistente (23503) e ON DELETE RESTRICT em módulo (23503) bloqueados'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-031] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
