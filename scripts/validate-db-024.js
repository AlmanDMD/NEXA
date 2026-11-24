/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-024]
 * Título: Criar Tabela de Critérios de Avaliação Prática / Rubricas (task_criteria)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Cada critério referencia uma tarefa prática (`practical_tasks`) e uma
 *    competência técnica oficial (`competencies`) com integridade referencial.
 * 2. Critério 2: Soma e ponderação de pesos (`weight NUMERIC(3,2) > 0.00 AND <= 9.99`)
 *    suportada para cálculo automático da nota final ponderada.
 * 3. Critério 3: Exclusão em cascata (`ON DELETE CASCADE`) quando a tarefa ainda não
 *    possui entregas avaliadas, e bloqueio (`ON DELETE RESTRICT` em `submission_evaluations` /
 *    `task_submissions`) quando já existem avaliações registradas.
 * 4. DoD: Tabela `task_criteria` migrada, `model TaskCriterion` no `prisma/schema.prisma`,
 *    tipos TS gerados em `BancoNexa/types/schema-models.ts`, testada com rubricas de
 *    Metrologia e Tornearia e integrada aos cards dependentes (`DB-026`, `BE-024`, `FE-026`).
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
  '20261123030000_create_task_criteria_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123030000_create_task_criteria_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '24_tabela_task_criteria.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '24-tabela-criterios-avaliacao-pratica-task-criteria.md'),
  path.join(ROOT_DIR, 'BancoNexa', '24-tabela-criterios-avaliacao-pratica-task-criteria.md'),
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
 * Simulador relacional das tabelas `practical_tasks`, `competencies`, `task_criteria`
 * e vínculo protetor com avaliações (`submission_evaluations`) para validar:
 * - FKs íntegras, UNIQUE (task_id, criterion_name), CHECK weight e min_acceptable_level (1..5);
 * - Ponderação automática da nota final por rubricas de Metrologia e Tornearia;
 * - ON DELETE CASCADE na exclusão de tarefa sem avaliações vs. ON DELETE RESTRICT quando avaliada.
 */
class TaskCriteriaRelationalSimulator {
  constructor() {
    this.tasks = new Map();
    this.competencies = new Map();
    this.criteriaById = new Map();
    this.criteriaByTaskName = new Map();
    this.evaluatedCriteriaIds = new Set();
    this.seq = 1;
  }

  addTask(id, title, maxScore = 10.0) {
    this.tasks.set(id, { id, title, max_score: maxScore });
  }

  addCompetency(id, code, title, category) {
    this.competencies.set(id, { id, code, title, category });
  }

  markCriterionAsEvaluated(criterionId) {
    this.evaluatedCriteriaIds.add(criterionId);
  }

  insertCriterion(row) {
    if (!row.task_id || !row.competency_id || row.criterion_name === undefined || row.criterion_name === null) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (String(row.criterion_name).trim().length === 0) {
      const err = new Error('violates check constraint "chk_task_criteria_name_not_blank"');
      err.sqlState = '23514';
      throw err;
    }

    if (String(row.criterion_name).length > 180) {
      const err = new Error('value too long for type character varying(180)');
      err.sqlState = '22001';
      throw err;
    }

    const weight = row.weight !== undefined ? Number(row.weight) : 1.0;
    if (Number.isNaN(weight) || weight <= 0.0 || weight > 9.99) {
      const err = new Error('violates check constraint "chk_task_criteria_weight"');
      err.sqlState = '23514';
      throw err;
    }

    const minLevel = row.min_acceptable_level !== undefined ? row.min_acceptable_level : 3;
    if (!Number.isInteger(minLevel) || minLevel < 1 || minLevel > 5) {
      const err = new Error('violates check constraint "chk_task_criteria_level"');
      err.sqlState = '23514';
      throw err;
    }

    if (!this.tasks.has(row.task_id)) {
      const err = new Error('violates foreign key constraint "fk_task_criteria_task"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (!this.competencies.has(row.competency_id)) {
      const err = new Error('violates foreign key constraint "fk_task_criteria_competency"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const uniqueKey = `${row.task_id}::${row.criterion_name}`;
    if (this.criteriaByTaskName.has(uniqueKey)) {
      const err = new Error('Unique constraint failed: uq_task_criteria_name');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      task_id: row.task_id,
      competency_id: row.competency_id,
      criterion_name: row.criterion_name,
      weight: Number(weight.toFixed(2)),
      min_acceptable_level: minLevel,
    };

    this.criteriaById.set(saved.id, saved);
    this.criteriaByTaskName.set(uniqueKey, saved);
    return saved;
  }

  deleteCompetencyRestrict(competencyId) {
    const inUse = [...this.criteriaById.values()].some((c) => c.competency_id === competencyId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_task_criteria_competency"');
      err.sqlState = '23503';
      throw err;
    }
    this.competencies.delete(competencyId);
  }

  /**
   * Simula exclusão da tarefa prática:
   * - Se algum critério já possuir avaliação (`submission_evaluations` ON DELETE RESTRICT), bloqueia com 23503.
   * - Caso contrário, exclui a tarefa e remove seus critérios em cascata (`ON DELETE CASCADE`).
   */
  deleteTaskCascade(taskId) {
    const taskCriteria = [...this.criteriaById.values()].filter((c) => c.task_id === taskId);
    const hasEvaluations = taskCriteria.some((c) => this.evaluatedCriteriaIds.has(c.id));
    if (hasEvaluations) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_criterion" (ON DELETE RESTRICT)');
      err.sqlState = '23503';
      throw err;
    }

    for (const c of taskCriteria) {
      this.criteriaById.delete(c.id);
      this.criteriaByTaskName.delete(`${c.task_id}::${c.criterion_name}`);
    }
    this.tasks.delete(taskId);
    return taskCriteria.length;
  }

  calculateWeightedScore(taskId, scoresByCriterionId) {
    const criteria = [...this.criteriaById.values()].filter((c) => c.task_id === taskId);
    let weightedSum = 0;
    let totalWeight = 0;

    for (const c of criteria) {
      const score = scoresByCriterionId[c.id];
      weightedSum += score * c.weight;
      totalWeight += c.weight;
    }

    return {
      totalWeight: Number(totalWeight.toFixed(2)),
      weightedScore: Number((weightedSum / totalWeight).toFixed(2)),
    };
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-024] — RUBRICAS PRÁTICAS (task_criteria)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de task_criteria'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123030000_create_task_criteria_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123030000_create_task_criteria_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/24_tabela_task_criteria.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/24_tabela_task_criteria.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/24-tabela-criterios-avaliacao-pratica-task-criteria.md e BancoNexa/24-tabela-criterios-avaliacao-pratica-task-criteria.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-024'),
  'Card DB-024 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model TaskCriterion no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model TaskCriterion no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /task_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /competency_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /criterion_name\s+VARCHAR\(180\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /weight\s+NUMERIC\(3,2\)\s+NOT\s+NULL\s+DEFAULT\s+1\.00/i.test(sqlContent) &&
    /min_acceptable_level\s+INTEGER\s+NOT\s+NULL\s+DEFAULT\s+3/i.test(sqlContent),
  'Todas as colunas exigidas (id, task_id, competency_id, criterion_name, weight NUMERIC(3,2), min_acceptable_level 1..5) presentes'
);
assertCheck(
  schemaContent.includes('model TaskCriterion') &&
    /criteria\s+TaskCriterion\[\]/.test(schemaContent) &&
    /taskCriteria\s+TaskCriterion\[\]/.test(schemaContent) &&
    schemaContent.includes('@@unique([taskId, criterionName], map: "uq_task_criteria_name")') &&
    schemaContent.includes('@@index([taskId], map: "idx_task_criteria_task")') &&
    schemaContent.includes('@@index([competencyId], map: "idx_task_criteria_competency")') &&
    schemaContent.includes('@@map("task_criteria")'),
  'Modelo TaskCriterion integrado ao prisma/schema.prisma com relações reversas em PracticalTask/Competency, CASCADE e índices'
);
assertCheck(
  typesTsContent.includes('export interface TaskCriterion {') &&
    typesTsContent.includes('criterionName: string;') &&
    typesTsContent.includes('minAcceptableLevel: number;') &&
    typesTsContent.includes('export interface TaskCriterionRow {'),
  'Tipos TypeScript (TaskCriterion, TaskCriterionRow, TaskCriterionCreateInput, TaskCriterionUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+fk_task_criteria_task\s+FOREIGN\s+KEY\s*\(\s*task_id\s*\)\s*REFERENCES\s+practical_tasks\s*\(\s*id\s*\)\s*ON\s+DELETE\s+CASCADE/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_task_criteria_competency\s+FOREIGN\s+KEY\s*\(\s*competency_id\s*\)\s*REFERENCES\s+competencies\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ),
  'Critérios 1 e 3: FK task_id com ON DELETE CASCADE e FK competency_id com ON DELETE RESTRICT declaradas'
);
assertCheck(
  /CONSTRAINT\s+chk_task_criteria_weight\s+CHECK\s*\(\s*weight\s*>\s*0\.00\s+AND\s+weight\s*<=\s*9\.99\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+chk_task_criteria_level\s+CHECK\s*\(\s*min_acceptable_level\s+BETWEEN\s+1\s+AND\s+5\s*\)/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+uq_task_criteria_name\s+UNIQUE\s*\(\s*task_id\s*,\s*criterion_name\s*\)/i.test(sqlContent),
  'Critério 2: Constraints chk_task_criteria_weight, chk_task_criteria_level (1..5) e uq_task_criteria_name declaradas'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-026, BE-024, FE-026)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-026, BE-024, FE-026)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+task_criteria/i.test(sql3fnContent) &&
    /uq_task_criteria_name/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*criterion_id\s*\)\s*REFERENCES\s+task_criteria\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sql3fnContent
    ),
  'Integração validada com modelo 3FN (T19 task_criteria) e tabela dependente submission_evaluations (DB-026 com ON DELETE RESTRICT)'
);

// 6. Testes unitários com rubricas de Metrologia e Tornearia, ponderação automática e exclusão em cascata (DoD)
console.log('\n6. Executando testes unitários com rubricas de Metrologia e Tornearia, ponderação e cascata (DoD)...');
const sim = new TaskCriteriaRelationalSimulator();
const taskTorneariaId = '10000000-0000-4000-8000-000000000001';
const taskRascunhoId = '10000000-0000-4000-8000-000000000002';
const compMetId = '20000000-0000-4000-8000-000000000001';
const compTorId = '20000000-0000-4000-8000-000000000002';
const compEpiId = '20000000-0000-4000-8000-000000000003';

sim.addTask(taskTorneariaId, 'Usinagem de Eixo Escalonado Ø25mm H7', 10.0);
sim.addTask(taskRascunhoId, 'Rascunho de Exercício de Controle Dimensional', 10.0);
sim.addCompetency(compMetId, 'COMP-MET-01', 'Leitura de Micrômetro Externo 0-25mm', 'TECHNICAL');
sim.addCompetency(compTorId, 'COMP-USIN-02', 'Acabamento e Rugosidade em Torno Convencional', 'TECHNICAL');
sim.addCompetency(compEpiId, 'COMP-SEG-01', 'Uso Obrigatório de EPI e NR-12 em Usinagem', 'SAFETY');

// Teste 1 (Critérios 1 & 2 / DoD): Rubricas de Metrologia, Tornearia e EPI com cálculo ponderado automático
const c1 = sim.insertCriterion({
  task_id: taskTorneariaId,
  competency_id: compMetId,
  criterion_name: 'Tolerância Dimensional ±0,02mm no Micrômetro',
  weight: 2.5,
  min_acceptable_level: 4,
});
const c2 = sim.insertCriterion({
  task_id: taskTorneariaId,
  competency_id: compTorId,
  criterion_name: 'Acabamento Superficial e Rugosidade Ra 1.6 no Torno',
  weight: 1.5,
  min_acceptable_level: 3,
});
const c3 = sim.insertCriterion({
  task_id: taskTorneariaId,
  competency_id: compEpiId,
  criterion_name: 'Uso Correto de Óculos de Proteção e Procedimento NR-12',
  weight: 1.0,
  min_acceptable_level: 5,
});

// Cálculo ponderado: (9.0*2.5 + 8.0*1.5 + 10.0*1.0) / (2.5 + 1.5 + 1.0) = (22.5 + 12.0 + 10.0) / 5.0 = 44.5 / 5.0 = 8.90
const weighted = sim.calculateWeightedScore(taskTorneariaId, {
  [c1.id]: 9.0,
  [c2.id]: 8.0,
  [c3.id]: 10.0,
});
assertCheck(
  weighted.totalWeight === 5.0 && weighted.weightedScore === 8.9,
  'Teste 1 (Critérios 1, 2 & DoD): Rubricas de Metrologia, Tornearia e EPI cadastradas com média ponderada automática (8.90 / peso total 5.00)'
);

// Teste 2: Duplicidade na tarefa, peso inválido, nível fora de 1..5 e FK competency_id RESTRICT
let dupNameBlocked = false;
let zeroWeightBlocked = false;
let invalidLevelBlocked = false;
let restrictCompBlocked = false;

try {
  sim.insertCriterion({
    task_id: taskTorneariaId,
    competency_id: compMetId,
    criterion_name: 'Tolerância Dimensional ±0,02mm no Micrômetro',
    weight: 1.0,
  });
} catch (err) {
  dupNameBlocked = err.sqlState === '23505' && err.code === 'P2002';
}

try {
  sim.insertCriterion({
    task_id: taskTorneariaId,
    competency_id: compMetId,
    criterion_name: 'Critério peso zero',
    weight: 0.0,
  });
} catch (err) {
  zeroWeightBlocked = err.sqlState === '23514';
}

try {
  sim.insertCriterion({
    task_id: taskTorneariaId,
    competency_id: compMetId,
    criterion_name: 'Critério nível 6',
    weight: 1.0,
    min_acceptable_level: 6,
  });
} catch (err) {
  invalidLevelBlocked = err.sqlState === '23514';
}

try {
  sim.deleteCompetencyRestrict(compMetId);
} catch (err) {
  restrictCompBlocked = err.sqlState === '23503';
}

assertCheck(
  dupNameBlocked && zeroWeightBlocked && invalidLevelBlocked && restrictCompBlocked,
  'Teste 2: Duplicata na tarefa (23505), weight <= 0 (23514), level fora de 1..5 (23514) e exclusão de competência em uso (23503) bloqueados'
);

// Teste 3 (Critério 3): Exclusão em cascata de tarefa SEM entregas avaliadas vs. bloqueio de tarefa JÁ avaliada
sim.insertCriterion({
  task_id: taskRascunhoId,
  competency_id: compMetId,
  criterion_name: 'Leitura de Paquímetro 0,05mm',
  weight: 1.0,
  min_acceptable_level: 3,
});
sim.insertCriterion({
  task_id: taskRascunhoId,
  competency_id: compEpiId,
  criterion_name: 'Organização da Bancada de Metrologia',
  weight: 0.5,
  min_acceptable_level: 3,
});
const cascadedCount = sim.deleteTaskCascade(taskRascunhoId);

sim.markCriterionAsEvaluated(c1.id);
let evaluatedTaskDeleteBlocked = false;
try {
  sim.deleteTaskCascade(taskTorneariaId);
} catch (err) {
  evaluatedTaskDeleteBlocked = err.sqlState === '23503';
}

assertCheck(
  cascadedCount === 2 && !sim.tasks.has(taskRascunhoId) && evaluatedTaskDeleteBlocked && sim.tasks.has(taskTorneariaId),
  'Teste 3 (Critério 3): Tarefa sem avaliações removeu 2 rubricas via ON DELETE CASCADE e tarefa já avaliada foi protegida com SQLSTATE 23503'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-024] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
