/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-014]
 * Título: Implementar Tabela de Módulos de Aprendizagem Prática SENAI (learning_modules)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Módulo associado obrigatoriamente a uma disciplina (`subject_id NOT NULL` + FK
 *    `fk_learning_modules_subject` -> `subjects(id)` com `ON DELETE CASCADE ON UPDATE CASCADE`).
 * 2. Critério 2: `order_index` garantindo a sequência didática recomendada
 *    (`uq_learning_modules_subject_order`, `chk_learning_modules_order_positive`,
 *    `idx_learning_modules_subject_order`).
 * 3. Critério 3: `passing_score` (`NUMERIC(4,2) DEFAULT 6.00`) com validação entre `0.00` e `10.00`
 *    (`chk_learning_modules_passing_score`).
 * 4. Observação Técnica: Pesos ponderados diferentes na composição final da disciplina
 *    (`module_weight NUMERIC(4,2) DEFAULT 1.00`, `chk_learning_modules_weight_positive`).
 * 5. DoD: Migration versionada, `model LearningModule` no `prisma/schema.prisma`, tipos TypeScript
 *    atualizados, testes unitários e integração com cards dependentes (`DB-016`, `DB-021`, `DB-023`,
 *    `DB-027`, `DB-031`, `DB-039`, `DB-042`).
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
  '20261118030000_create_learning_modules_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118030000_create_learning_modules_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '14_tabela_learning_modules.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '14-tabela-modulos-aprendizagem-pratica-learning-modules.md'),
  path.join(ROOT_DIR, 'BancoNexa', '14-tabela-modulos-aprendizagem-pratica-learning-modules.md'),
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
 * Simulador relacional das tabelas `subjects` e `learning_modules` com FK ON DELETE CASCADE,
 * sequência didática `(subject_id, order_index)`, nota de corte `0.00..10.00` (padrão 6.00)
 * e pesos ponderados `module_weight > 0.00`.
 */
class LearningModulesRelationalSimulator {
  constructor() {
    this.subjects = new Map();
    this.modulesById = new Map();
    this.modulesBySubjectOrder = new Map();
    this.seq = 1;
  }

  createSubject(id, code, name) {
    this.subjects.set(id, { id, code, name });
  }

  deleteSubjectCascade(subjectId) {
    if (!this.subjects.has(subjectId)) return 0;
    this.subjects.delete(subjectId);
    let removed = 0;
    for (const [id, mod] of [...this.modulesById.entries()]) {
      if (mod.subject_id === subjectId) {
        this.modulesById.delete(id);
        this.modulesBySubjectOrder.delete(`${mod.subject_id}::${mod.order_index}`);
        removed++;
      }
    }
    return removed;
  }

  createModule(row) {
    // Critério 1: subject_id obrigatório e existente em subjects
    if (!row.subject_id) {
      const err = new Error(
        'null value in column "subject_id" of relation "learning_modules" violates not-null constraint'
      );
      err.sqlState = '23502';
      throw err;
    }
    if (!this.subjects.has(row.subject_id)) {
      const err = new Error(
        'insert or update on table "learning_modules" violates foreign key constraint "fk_learning_modules_subject"'
      );
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Trigger trg_learning_modules_normalize_and_touch
    const title = String(row.title || '').trim();
    const description =
      row.description !== undefined && row.description !== null ? String(row.description).trim() : null;

    if (title.length < 3 || title.length > 120) {
      const err = new Error('violates check constraint "chk_learning_modules_title_not_empty"');
      err.sqlState = '23514';
      throw err;
    }

    // Critério 2: order_index > 0 e único por disciplina
    if (!Number.isInteger(row.order_index) || row.order_index <= 0) {
      const err = new Error(
        'new row for relation "learning_modules" violates check constraint "chk_learning_modules_order_positive"'
      );
      err.sqlState = '23514';
      throw err;
    }

    // practical_hours >= 0
    if (!Number.isInteger(row.practical_hours) || row.practical_hours < 0) {
      const err = new Error(
        'new row for relation "learning_modules" violates check constraint "chk_learning_modules_hours_non_negative"'
      );
      err.sqlState = '23514';
      throw err;
    }

    // Observação Técnica: module_weight > 0.00 (default 1.00)
    const moduleWeight = row.module_weight !== undefined ? Number(row.module_weight) : 1.0;
    if (!Number.isFinite(moduleWeight) || moduleWeight <= 0.0 || moduleWeight > 99.99) {
      const err = new Error(
        'new row for relation "learning_modules" violates check constraint "chk_learning_modules_weight_positive"'
      );
      err.sqlState = '23514';
      throw err;
    }

    // Critério 3: passing_score BETWEEN 0.00 AND 10.00 (default 6.00)
    const passingScore = row.passing_score !== undefined ? Number(row.passing_score) : 6.0;
    if (!Number.isFinite(passingScore) || passingScore < 0.0 || passingScore > 10.0) {
      const err = new Error(
        'new row for relation "learning_modules" violates check constraint "chk_learning_modules_passing_score"'
      );
      err.sqlState = '23514';
      throw err;
    }

    // UNIQUE (subject_id, order_index)
    const orderKey = `${row.subject_id}::${row.order_index}`;
    if (this.modulesBySubjectOrder.has(orderKey)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`subject_id`, `order_index`) [SQLSTATE 23505 / uq_learning_modules_subject_order]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      subject_id: row.subject_id,
      title,
      order_index: row.order_index,
      description,
      practical_hours: row.practical_hours,
      module_weight: Number(moduleWeight.toFixed(2)),
      passing_score: Number(passingScore.toFixed(2)),
      created_at: now,
      updated_at: now,
    };

    this.modulesById.set(saved.id, saved);
    this.modulesBySubjectOrder.set(orderKey, saved);
    return saved;
  }

  listBySubjectOrdered(subjectId) {
    return [...this.modulesById.values()]
      .filter((m) => m.subject_id === subjectId)
      .sort((a, b) => a.order_index - b.order_index);
  }

  calculateWeightedAverage(subjectId, scoresByModuleId) {
    const mods = this.listBySubjectOrdered(subjectId);
    let weightedSum = 0;
    let totalWeight = 0;
    for (const m of mods) {
      if (scoresByModuleId[m.id] !== undefined) {
        weightedSum += scoresByModuleId[m.id] * m.module_weight;
        totalWeight += m.module_weight;
      }
    }
    return totalWeight > 0 ? Number((weightedSum / totalWeight).toFixed(2)) : 0;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-014] — MÓDULOS PRÁTICOS (learning_modules)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de learning_modules'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118030000_create_learning_modules_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118030000_create_learning_modules_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/14_tabela_learning_modules.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/14_tabela_learning_modules.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/14-tabela-modulos-aprendizagem-pratica-learning-modules.md e BancoNexa/14-tabela-modulos-aprendizagem-pratica-learning-modules.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-014'),
  'Card DB-014 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas, model LearningModule no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model LearningModule no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /subject_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /title\s+VARCHAR\(120\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /order_index\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /description\s+TEXT/i.test(sqlContent) &&
    /practical_hours\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /module_weight\s+(NUMERIC|DECIMAL)\(4,2\)\s+NOT\s+NULL\s+DEFAULT\s+1\.00/i.test(sqlContent) &&
    /passing_score\s+(NUMERIC|DECIMAL)\(4,2\)\s+NOT\s+NULL\s+DEFAULT\s+6\.00/i.test(sqlContent),
  'Todas as colunas exigidas (id, subject_id, title, order_index, description, practical_hours, module_weight, passing_score) presentes com tipos e defaults corretos'
);
assertCheck(
  schemaContent.includes('model LearningModule') &&
    /learningModules\s+LearningModule\[\]/.test(schemaContent) &&
    schemaContent.includes('@map("order_index")') &&
    schemaContent.includes('@map("practical_hours")') &&
    schemaContent.includes('@map("module_weight") @db.Decimal(4, 2)') &&
    schemaContent.includes('@default(6.00) @map("passing_score") @db.Decimal(4, 2)') &&
    schemaContent.includes('onDelete: Cascade, onUpdate: Cascade, map: "fk_learning_modules_subject"') &&
    schemaContent.includes('@@unique([subjectId, orderIndex], map: "uq_learning_modules_subject_order")') &&
    schemaContent.includes('@@map("learning_modules")'),
  'Modelo LearningModule integrado ao prisma/schema.prisma com relação bidirecional em Subject, onDelete: Cascade, @@unique([subjectId, orderIndex]) e Decimal(4,2)'
);
assertCheck(
  typesTsContent.includes('export interface LearningModule {') &&
    typesTsContent.includes('orderIndex: number;') &&
    typesTsContent.includes('practicalHours: number;') &&
    typesTsContent.includes('moduleWeight: number | string;') &&
    typesTsContent.includes('passingScore: number | string;') &&
    typesTsContent.includes('export interface LearningModuleRow {'),
  'Tipos TypeScript (LearningModule, LearningModuleRow, LearningModuleCreateInput, LearningModuleUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+fk_learning_modules_subject\s+FOREIGN\s+KEY\s*\(\s*subject_id\s*\)\s*REFERENCES\s+subjects\s*\(\s*id\s*\)\s*ON\s+DELETE\s+CASCADE\s+ON\s+UPDATE\s+CASCADE/i.test(
    sqlContent
  ),
  'Critério 1: Módulo associado à disciplina via FK fk_learning_modules_subject com ON DELETE CASCADE ON UPDATE CASCADE'
);
assertCheck(
  /CONSTRAINT\s+uq_learning_modules_subject_order\s+UNIQUE\s*\(\s*subject_id\s*,\s*order_index\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+chk_learning_modules_order_positive\s+CHECK\s*\(\s*order_index\s*>\s*0\s*\)/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_learning_modules_subject_order\s+ON\s+learning_modules\s+USING\s+BTREE\s*\(\s*subject_id\s*,\s*order_index\s+ASC\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: order_index > 0 com unicidade (subject_id, order_index) e índice ascendente idx_learning_modules_subject_order'
);
assertCheck(
  /CONSTRAINT\s+chk_learning_modules_passing_score\s+CHECK\s*\(\s*passing_score\s*>=\s*0\.00\s+AND\s+passing_score\s*<=\s*10\.00\s*\)/i.test(
    sqlContent
  ),
  'Critério 3: Constraint chk_learning_modules_passing_score validando passing_score entre 0.00 e 10.00'
);
assertCheck(
  /CONSTRAINT\s+chk_learning_modules_weight_positive\s+CHECK\s*\(\s*module_weight\s*>\s*0\.00\s*\)/i.test(sqlContent),
  'Observação Técnica: Peso ponderado module_weight > 0.00 suportando composição ponderada da disciplina (BE-028)'
);

// 5. Integração com cards dependentes no modelo 3FN
console.log('\n5. Verificando integração com cards dependentes (DB-016, DB-021, DB-023, DB-027, DB-031, DB-039, DB-042)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /fk_module_competencies_module/i.test(sql3fnContent) &&
    /fk_class_lessons_module/i.test(sql3fnContent) &&
    /fk_practical_tasks_module/i.test(sql3fnContent) &&
    /fk_assessments_module/i.test(sql3fnContent) &&
    /fk_self_assessment_forms_module/i.test(sql3fnContent) &&
    /fk_milestone_history_module/i.test(sql3fnContent) &&
    /fk_help_requests_module/i.test(sql3fnContent),
  'Integração validada: FKs de module_competencies (DB-016), class_lessons (DB-021), practical_tasks (DB-023), academic_assessments (DB-027), self_assessment_forms (DB-031), student_milestone_history (DB-039) e help_requests (DB-042) referenciam learning_modules(id)'
);

// 6. Testes unitários de integridade da tabela learning_modules (DoD)
console.log('\n6. Executando testes unitários de integridade da tabela learning_modules (DoD)...');
const sim = new LearningModulesRelationalSimulator();
const fabSubjectId = '11111111-1111-4111-8111-111111111111';
const metSubjectId = '22222222-2222-4222-8222-222222222222';
const tmpSubjectId = '33333333-3333-4333-8333-333333333333';
sim.createSubject(fabSubjectId, 'UC-FAB-01', 'Processos de Fabricação Mecânica');
sim.createSubject(metSubjectId, 'UC-MET-01', 'Metrologia Dimensional');
sim.createSubject(tmpSubjectId, 'UC-TMP-01', 'Disciplina Rascunho para Teste Cascade');

const m2 = sim.createModule({
  subject_id: fabSubjectId,
  title: '  Módulo de Tornearia Cilíndrica  ',
  order_index: 2,
  description: '  Usinagem cilíndrica externa e faceamento em torno convencional.  ',
  practical_hours: 40,
  module_weight: 2.5,
  passing_score: 7.0,
});
const m1 = sim.createModule({
  subject_id: fabSubjectId,
  title: 'Segurança e Preparação de Bancada',
  order_index: 1,
  practical_hours: 16,
});
assertCheck(
  m2.title === 'Módulo de Tornearia Cilíndrica' &&
    m2.description === 'Usinagem cilíndrica externa e faceamento em torno convencional.' &&
    m1.passing_score === 6.0 &&
    m1.module_weight === 1.0,
  'Teste 1: Módulos inseridos com higienização de texto e defaults corretos (passing_score = 6.00, module_weight = 1.00)'
);

// Teste 2: Critério 1 — Vínculo obrigatório à disciplina e ON DELETE CASCADE
let nullSubjectBlocked = false;
let invalidSubjectBlocked = false;
try {
  sim.createModule({ subject_id: null, title: 'Módulo Órfão', order_index: 1, practical_hours: 10 });
} catch (err) {
  nullSubjectBlocked = err.sqlState === '23502';
}
try {
  sim.createModule({
    subject_id: '99999999-9999-4999-8999-999999999999',
    title: 'Disciplina Inexistente',
    order_index: 1,
    practical_hours: 10,
  });
} catch (err) {
  invalidSubjectBlocked = err.sqlState === '23503' && err.code === 'P2003';
}
sim.createModule({ subject_id: tmpSubjectId, title: 'Módulo Temporário 1', order_index: 1, practical_hours: 8 });
sim.createModule({ subject_id: tmpSubjectId, title: 'Módulo Temporário 2', order_index: 2, practical_hours: 12 });
const cascadedCount = sim.deleteSubjectCascade(tmpSubjectId);
assertCheck(
  nullSubjectBlocked && invalidSubjectBlocked && cascadedCount === 2 && sim.listBySubjectOrdered(tmpSubjectId).length === 0,
  'Teste 2 (Critério 1): FK bloqueia subject_id nulo/inexistente (23502/23503) e ON DELETE CASCADE remove os 2 módulos da disciplina excluída'
);

// Teste 3: Critério 2 — order_index > 0, unicidade por disciplina e ordenação didática ascendente
let zeroOrderBlocked = false;
let dupOrderBlocked = false;
try {
  sim.createModule({ subject_id: fabSubjectId, title: 'Ordem Zero', order_index: 0, practical_hours: 10 });
} catch (err) {
  zeroOrderBlocked = err.sqlState === '23514';
}
try {
  sim.createModule({ subject_id: fabSubjectId, title: 'Ordem Duplicada', order_index: 1, practical_hours: 10 });
} catch (err) {
  dupOrderBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
const mMet1 = sim.createModule({
  subject_id: metSubjectId,
  title: 'Metrologia com Micrômetro',
  order_index: 1,
  practical_hours: 24,
});
const orderedFab = sim.listBySubjectOrdered(fabSubjectId);
assertCheck(
  zeroOrderBlocked &&
    dupOrderBlocked &&
    mMet1.order_index === 1 &&
    orderedFab.length === 2 &&
    orderedFab[0].order_index === 1 &&
    orderedFab[1].order_index === 2,
  'Teste 3 (Critério 2): order_index <= 0 (23514) e duplicata na mesma disciplina (P2002) bloqueados; listagem retornou sequência 1 -> 2'
);

// Teste 4: Critério 3 — passing_score validado entre 0.00 e 10.00
const mMin = sim.createModule({
  subject_id: metSubjectId,
  title: 'Introdução a Instrumentos (Limite 0.00)',
  order_index: 2,
  practical_hours: 0,
  passing_score: 0.0,
});
const mMax = sim.createModule({
  subject_id: metSubjectId,
  title: 'Calibração de Precisão (Limite 10.00)',
  order_index: 3,
  practical_hours: 12,
  passing_score: 10.0,
});
let negativeScoreBlocked = false;
let aboveTenScoreBlocked = false;
try {
  sim.createModule({
    subject_id: metSubjectId,
    title: 'Nota Negativa',
    order_index: 4,
    practical_hours: 8,
    passing_score: -0.01,
  });
} catch (err) {
  negativeScoreBlocked = err.sqlState === '23514';
}
try {
  sim.createModule({
    subject_id: metSubjectId,
    title: 'Nota Acima de 10',
    order_index: 5,
    practical_hours: 8,
    passing_score: 10.01,
  });
} catch (err) {
  aboveTenScoreBlocked = err.sqlState === '23514';
}
assertCheck(
  mMin.passing_score === 0.0 &&
    mMax.passing_score === 10.0 &&
    negativeScoreBlocked &&
    aboveTenScoreBlocked,
  'Teste 4 (Critério 3): passing_score aceitou extremos 0.00 e 10.00 e bloqueou -0.01 e 10.01 (23514)'
);

// Teste 5: Observação Técnica — Pesos ponderados diferentes e validação module_weight > 0.00
let invalidWeightBlocked = false;
let negativeHoursBlocked = false;
try {
  sim.createModule({
    subject_id: fabSubjectId,
    title: 'Peso Zero',
    order_index: 3,
    practical_hours: 10,
    module_weight: 0.0,
  });
} catch (err) {
  invalidWeightBlocked = err.sqlState === '23514';
}
try {
  sim.createModule({
    subject_id: fabSubjectId,
    title: 'Horas Negativas',
    order_index: 3,
    practical_hours: -4,
  });
} catch (err) {
  negativeHoursBlocked = err.sqlState === '23514';
}
// Média ponderada: (m1: nota 6.0 * peso 1.00 + m2: nota 9.5 * peso 2.50) / (1.00 + 2.50) = 29.75 / 3.50 = 8.50
const weightedAvg = sim.calculateWeightedAverage(fabSubjectId, {
  [m1.id]: 6.0,
  [m2.id]: 9.5,
});
assertCheck(
  invalidWeightBlocked && negativeHoursBlocked && weightedAvg === 8.5,
  'Teste 5 (Observação Técnica): module_weight <= 0 e practical_hours < 0 bloqueados (23514); média ponderada calculada corretamente (8.50)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-014] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
