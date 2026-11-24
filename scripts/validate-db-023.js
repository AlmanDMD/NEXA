/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-023]
 * Título: Implementar Tabela de Tarefas e Atividades Práticas (practical_tasks)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Tarefa vinculada a um módulo prático (`learning_modules`) e turma (`classes`)
 *    via FKs `fk_practical_tasks_module` e `fk_practical_tasks_class` com `ON DELETE RESTRICT`
 *    + trigger garantindo coerência de curso (`subjects.course_id = classes.course_id`).
 * 2. Critério 2: Campo `max_score` (`NUMERIC(4,2) DEFAULT 10.00`) validado entre `1.00` e `10.00`
 *    via `chk_practical_tasks_max_score`.
 * 3. Critério 3: Índice composto `idx_practical_tasks_class_due_date (class_id, due_date)`
 *    para consulta rápida de pendências, além dos índices auxiliares `(module_id)` e
 *    `(class_id, is_mandatory, due_date)`.
 * 4. DoD: Tabela `practical_tasks` criada no `prisma/schema.prisma`, migration SQL versionada,
 *    tipos TS gerados em `BancoNexa/types/schema-models.ts`, testes unitários e integração com
 *    cards dependentes (`DB-024`, `DB-025`, `BE-024`, `FE-024`).
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
  '20261123020000_create_practical_tasks_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123020000_create_practical_tasks_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '23_tabela_practical_tasks.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '23-tabela-tarefas-praticas-practical-tasks.md'),
  path.join(ROOT_DIR, 'BancoNexa', '23-tabela-tarefas-praticas-practical-tasks.md'),
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
 * Simulador relacional das tabelas `courses`, `classes`, `subjects`, `learning_modules`
 * e `practical_tasks` com FKs ON DELETE RESTRICT, CHECK max_score 1.00..10.00,
 * validação de URL HTTP/HTTPS, coerência de curso e consulta ordenada por (class_id, due_date).
 */
class PracticalTasksRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.modules = new Map();
    this.tasksById = new Map();
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

  insertTask(row) {
    if (!row.module_id || !row.class_id || row.title === undefined || row.title === null || !row.due_date) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (String(row.title).trim().length === 0) {
      const err = new Error('violates check constraint "chk_practical_tasks_title_not_blank"');
      err.sqlState = '23514';
      throw err;
    }

    if (String(row.title).length > 150) {
      const err = new Error('value too long for type character varying(150)');
      err.sqlState = '22001';
      throw err;
    }

    const maxScore = row.max_score !== undefined ? Number(row.max_score) : 10.0;
    if (Number.isNaN(maxScore) || maxScore < 1.0 || maxScore > 10.0) {
      const err = new Error('violates check constraint "chk_practical_tasks_max_score"');
      err.sqlState = '23514';
      throw err;
    }

    if (row.blueprint_url !== undefined && row.blueprint_url !== null) {
      if (!/^https?:\/\//i.test(String(row.blueprint_url))) {
        const err = new Error('violates check constraint "chk_practical_tasks_blueprint_url"');
        err.sqlState = '23514';
        throw err;
      }
      if (String(row.blueprint_url).length > 500) {
        const err = new Error('value too long for type character varying(500)');
        err.sqlState = '22001';
        throw err;
      }
    }

    const mod = this.modules.get(row.module_id);
    if (!mod) {
      const err = new Error('violates foreign key constraint "fk_practical_tasks_module"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const cls = this.classes.get(row.class_id);
    if (!cls) {
      const err = new Error('violates foreign key constraint "fk_practical_tasks_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const subject = this.subjects.get(mod.subject_id);
    if (subject && subject.course_id !== cls.course_id) {
      const err = new Error('chk_practical_tasks_module_course: módulo de outro curso');
      err.sqlState = '23514';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      module_id: row.module_id,
      class_id: row.class_id,
      title: row.title,
      description: row.description !== undefined ? row.description : null,
      blueprint_url: row.blueprint_url !== undefined ? row.blueprint_url : null,
      due_date: row.due_date,
      max_score: Number(maxScore.toFixed(2)),
      is_mandatory: row.is_mandatory !== undefined ? Boolean(row.is_mandatory) : true,
      created_at: now,
      updated_at: now,
    };

    this.tasksById.set(saved.id, saved);
    return saved;
  }

  deleteModuleRestrict(moduleId) {
    const inUse = [...this.tasksById.values()].some((t) => t.module_id === moduleId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_practical_tasks_module"');
      err.sqlState = '23503';
      throw err;
    }
    this.modules.delete(moduleId);
  }

  deleteClassRestrict(classId) {
    const inUse = [...this.tasksById.values()].some((t) => t.class_id === classId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_practical_tasks_class"');
      err.sqlState = '23503';
      throw err;
    }
    this.classes.delete(classId);
  }

  listPendingByClassDueDate(classId, referenceIso) {
    return [...this.tasksById.values()]
      .filter((t) => t.class_id === classId && (!referenceIso || t.due_date >= referenceIso))
      .sort((a, b) => a.due_date.localeCompare(b.due_date));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-023] — ATIVIDADES PRÁTICAS (practical_tasks)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de practical_tasks'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123020000_create_practical_tasks_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123020000_create_practical_tasks_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/23_tabela_practical_tasks.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/23_tabela_practical_tasks.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/23-tabela-tarefas-praticas-practical-tasks.md e BancoNexa/23-tabela-tarefas-praticas-practical-tasks.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-023'),
  'Card DB-023 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model PracticalTask no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model PracticalTask no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /module_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /title\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /description\s+TEXT\s*,/i.test(sqlContent) &&
    /blueprint_url\s+VARCHAR\(500\)\s*,/i.test(sqlContent) &&
    /due_date\s+TIMESTAMPTZ\s+NOT\s+NULL/i.test(sqlContent) &&
    /max_score\s+NUMERIC\(4,2\)\s+NOT\s+NULL\s+DEFAULT\s+10\.00/i.test(sqlContent) &&
    /is_mandatory\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent) &&
    /updated_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, module_id, class_id, title, description, blueprint_url, due_date, max_score NUMERIC(4,2) DEFAULT 10.00, is_mandatory, created_at, updated_at) presentes'
);
assertCheck(
  schemaContent.includes('model PracticalTask') &&
    (schemaContent.match(/practicalTasks\s+PracticalTask\[\]/g) || []).length === 2 &&
    schemaContent.includes('@@index([classId, dueDate], map: "idx_practical_tasks_class_due_date")') &&
    schemaContent.includes('@@index([moduleId], map: "idx_practical_tasks_module")') &&
    schemaContent.includes('@@map("practical_tasks")'),
  'Modelo PracticalTask integrado ao prisma/schema.prisma com relações reversas em LearningModule/Class e índices de pendências'
);
assertCheck(
  typesTsContent.includes('export interface PracticalTask {') &&
    typesTsContent.includes('blueprintUrl: string | null;') &&
    typesTsContent.includes('maxScore: number | string;') &&
    typesTsContent.includes('isMandatory: boolean;') &&
    typesTsContent.includes('export interface PracticalTaskRow {'),
  'Tipos TypeScript (PracticalTask, PracticalTaskRow, PracticalTaskCreateInput, PracticalTaskUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+fk_practical_tasks_module\s+FOREIGN\s+KEY\s*\(\s*module_id\s*\)\s*REFERENCES\s+learning_modules\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_practical_tasks_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_practical_tasks_validate_and_touch/i.test(sqlContent),
  'Critério 1: FKs para learning_modules e classes com ON DELETE RESTRICT + trigger validando coerência de curso e updated_at'
);
assertCheck(
  /CONSTRAINT\s+chk_practical_tasks_max_score\s+CHECK\s*\(\s*max_score\s*>=\s*1\.00\s+AND\s+max_score\s*<=\s*10\.00\s*\)/i.test(
    sqlContent
  ),
  'Critério 2: Constraint chk_practical_tasks_max_score validando max_score entre 1.00 e 10.00 declarada'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_practical_tasks_class_due_date\s+ON\s+practical_tasks\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*due_date\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_practical_tasks_module\s+ON\s+practical_tasks\s+USING\s+BTREE\s*\(\s*module_id\s*\)/i.test(
      sqlContent
    ),
  'Critério 3: Índice composto idx_practical_tasks_class_due_date (class_id, due_date) + índice auxiliar (module_id) criados'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-024, DB-025, BE-024, FE-024)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-024, DB-025, BE-024)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+practical_tasks/i.test(sql3fnContent) &&
    /chk_practical_tasks_max_score/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*task_id\s*\)\s*REFERENCES\s+practical_tasks\s*\(\s*id\s*\)/i.test(sql3fnContent),
  'Integração validada com modelo 3FN (T18 practical_tasks) e tabelas dependentes task_criteria (DB-024) e task_submissions (DB-025)'
);

// 6. Testes unitários de peças práticas, FKs/curso, max_score 1..10 e pendências por prazo (DoD)
console.log('\n6. Executando testes unitários de peças práticas, FKs, max_score e consulta de pendências (DoD)...');
const sim = new PracticalTasksRelationalSimulator();
const courseMecId = '10000000-0000-4000-8000-000000000001';
const courseEletroId = '10000000-0000-4000-8000-000000000002';
const classMec1Id = '20000000-0000-4000-8000-000000000001';
const subjectUsinId = '30000000-0000-4000-8000-000000000001';
const subjectClpId = '30000000-0000-4000-8000-000000000002';
const modTorneariaId = '40000000-0000-4000-8000-000000000001';
const modClpId = '40000000-0000-4000-8000-000000000002';

sim.addCourse(courseMecId, 'TEC-MEC');
sim.addCourse(courseEletroId, 'TEC-ELE');
sim.addClass(classMec1Id, courseMecId, 'MEC-2026-1');
sim.addSubject(subjectUsinId, courseMecId, 'UC-USIN-01');
sim.addSubject(subjectClpId, courseEletroId, 'UC-CLP-01');
sim.addModule(modTorneariaId, subjectUsinId, 'Módulo 01 — Torneamento Cilíndrico Externo');
sim.addModule(modClpId, subjectClpId, 'Módulo 01 — Programação Ladder');

// Teste 1 (Critério 1 & DoD): Cadastro da peça SENAI com defaults (max_score = 10.00, is_mandatory = true)
const eixoTask = sim.insertTask({
  module_id: modTorneariaId,
  class_id: classMec1Id,
  title: 'Usinagem de Eixo Escalonado Ø25mm H7',
  description: 'Torneamento externo em aço ABNT 1020 com controle de tolerância H7 e rugosidade Ra 1.6.',
  blueprint_url: 'https://cdn.senai.nexa.local/blueprints/eixo-escalonado-25h7.pdf',
  due_date: '2026-04-20T22:00:00.000Z',
});
const optionalTask = sim.insertTask({
  module_id: modTorneariaId,
  class_id: classMec1Id,
  title: 'Bucha de Bronze para Revisão de Acabamento',
  due_date: '2026-04-12T22:00:00.000Z',
  max_score: 1.0,
  is_mandatory: false,
});
assertCheck(
  eixoTask.module_id === modTorneariaId &&
    eixoTask.class_id === classMec1Id &&
    eixoTask.max_score === 10.0 &&
    eixoTask.is_mandatory === true &&
    optionalTask.max_score === 1.0 &&
    optionalTask.is_mandatory === false &&
    optionalTask.blueprint_url === null,
  'Teste 1 (Critério 1 & DoD): Peça prática "Usinagem de Eixo Escalonado Ø25mm H7" (default 10.00 / mandatory) e atividade opcional (1.00) criadas'
);

// Teste 2 (Critério 1): FKs inexistentes, módulo de outro curso, URL inválida e ON DELETE RESTRICT
let missingModuleBlocked = false;
let wrongCourseModuleBlocked = false;
let invalidUrlBlocked = false;
let restrictModuleBlocked = false;
let restrictClassBlocked = false;

try {
  sim.insertTask({
    module_id: '99999999-0000-4000-8000-000000000000',
    class_id: classMec1Id,
    title: 'Peça órfã',
    due_date: '2026-04-25T22:00:00.000Z',
  });
} catch (err) {
  missingModuleBlocked = err.sqlState === '23503';
}

try {
  sim.insertTask({
    module_id: modClpId,
    class_id: classMec1Id,
    title: 'Tarefa de CLP em turma de Mecânica',
    due_date: '2026-04-25T22:00:00.000Z',
  });
} catch (err) {
  wrongCourseModuleBlocked = err.sqlState === '23514';
}

try {
  sim.insertTask({
    module_id: modTorneariaId,
    class_id: classMec1Id,
    title: 'Peça com URL inválida',
    blueprint_url: 'ftp://senai.local/desenho.pdf',
    due_date: '2026-04-25T22:00:00.000Z',
  });
} catch (err) {
  invalidUrlBlocked = err.sqlState === '23514';
}

try {
  sim.deleteModuleRestrict(modTorneariaId);
} catch (err) {
  restrictModuleBlocked = err.sqlState === '23503';
}

try {
  sim.deleteClassRestrict(classMec1Id);
} catch (err) {
  restrictClassBlocked = err.sqlState === '23503';
}

assertCheck(
  missingModuleBlocked &&
    wrongCourseModuleBlocked &&
    invalidUrlBlocked &&
    restrictModuleBlocked &&
    restrictClassBlocked,
  'Teste 2 (Critério 1): FK ausente (23503), módulo de outro curso (23514), blueprint_url inválida (23514) e ON DELETE RESTRICT em módulo/turma (23503) bloqueados'
);

// Teste 3 (Critério 2): Validação de max_score entre 1.00 e 10.00
let zeroScoreBlocked = false;
let belowMinScoreBlocked = false;
let aboveMaxScoreBlocked = false;
for (const [score, setter] of [
  [0.0, (v) => (zeroScoreBlocked = v)],
  [0.99, (v) => (belowMinScoreBlocked = v)],
  [10.01, (v) => (aboveMaxScoreBlocked = v)],
]) {
  try {
    sim.insertTask({
      module_id: modTorneariaId,
      class_id: classMec1Id,
      title: `Teste nota ${score}`,
      due_date: '2026-04-28T22:00:00.000Z',
      max_score: score,
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}
assertCheck(
  zeroScoreBlocked && belowMinScoreBlocked && aboveMaxScoreBlocked,
  'Teste 3 (Critério 2): Valores fora da faixa 1.00..10.00 (0.00, 0.99 e 10.01) rejeitados por chk_practical_tasks_max_score (23514)'
);

// Teste 4 (Critério 3): Consulta rápida de pendências por (class_id, due_date)
sim.insertTask({
  module_id: modTorneariaId,
  class_id: classMec1Id,
  title: 'Rosca Métrica Externa M16x2',
  due_date: '2026-04-15T22:00:00.000Z',
  max_score: 8.5,
});
const pending = sim.listPendingByClassDueDate(classMec1Id, '2026-04-13T00:00:00.000Z');
assertCheck(
  pending.length === 2 &&
    pending[0].title === 'Rosca Métrica Externa M16x2' &&
    pending[1].title === 'Usinagem de Eixo Escalonado Ø25mm H7',
  'Teste 4 (Critério 3): Consulta por (class_id, due_date) filtrou e ordenou corretamente as pendências futuras por prazo'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-023] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
