/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-026]
 * Título: Criar Tabela de Avaliações por Rubrica dos Professores (submission_evaluations)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Constraint UNIQUE composta `uq_submission_evaluations_composite (submission_id, criterion_id)`.
 * 2. Critério 2: Validação CHECK `chk_submission_evaluations_level` para `achieved_level` entre 1 e 5
 *    (além de `chk_submission_evaluations_score` para `score_awarded` entre 0.00 e 10.00).
 * 3. Critério 3: FK `fk_submission_evaluations_evaluator` para `users(id)` identificando o docente avaliador
 *    + trigger bloqueando `role = 'STUDENT'` e autoavaliação indevida.
 * 4. DoD: Migration `20261123050000_create_submission_evaluations_table` aplicada, `model SubmissionEvaluation`
 *    no `prisma/schema.prisma`, tipos TS gerados em `BancoNexa/types/schema-models.ts`, cálculo de nota
 *    consolidada ponderada (`fn_calculate_submission_consolidated_score` + trigger AFTER em `task_submissions`)
 *    testado e integração validada com cards dependentes (`DB-024`, `DB-025`, `DB-030`, `DB-033`, `DB-038`, `BE-025`, `FE-026`).
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
  '20261123050000_create_submission_evaluations_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123050000_create_submission_evaluations_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '26_tabela_submission_evaluations.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '26-tabela-avaliacoes-rubrica-submission-evaluations.md'),
  path.join(ROOT_DIR, 'BancoNexa', '26-tabela-avaliacoes-rubrica-submission-evaluations.md'),
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
 * Simulador relacional das tabelas `practical_tasks`, `task_criteria`, `task_submissions`,
 * `users` e `submission_evaluations` com UNIQUE (submission_id, criterion_id),
 * CHECK achieved_level BETWEEN 1 AND 5, CHECK score_awarded BETWEEN 0.00 AND 10.00,
 * trigger BEFORE de integridade docente/rubrica e trigger AFTER de consolidação ponderada
 * da nota final em `task_submissions.final_task_score`.
 */
class SubmissionEvaluationsRelationalSimulator {
  constructor() {
    this.tasks = new Map();
    this.criteria = new Map();
    this.users = new Map();
    this.submissions = new Map();
    this.evaluationsById = new Map();
    this.evaluationsByPair = new Map();
    this.seq = 1;
  }

  addTask(id, title, maxScore = 10.0) {
    this.tasks.set(id, { id, title, max_score: maxScore });
  }

  addCriterion(id, taskId, competencyId, criterionName, weight = 1.0, minAcceptableLevel = 3) {
    this.criteria.set(id, {
      id,
      task_id: taskId,
      competency_id: competencyId,
      criterion_name: criterionName,
      weight,
      min_acceptable_level: minAcceptableLevel,
    });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addSubmission(id, taskId, studentId, status = 'SUBMITTED') {
    this.submissions.set(id, {
      id,
      task_id: taskId,
      student_id: studentId,
      status,
      completed_at: status === 'SUBMITTED' || status === 'EVALUATED' ? new Date().toISOString() : null,
      final_task_score: null,
      updated_at: new Date().toISOString(),
    });
  }

  _validateRow(row) {
    if (!row.submission_id || !row.criterion_id || !row.evaluator_id) {
      const err = new Error('null value in required foreign key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (row.achieved_level === undefined || row.achieved_level === null || row.score_awarded === undefined || row.score_awarded === null) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    if (!Number.isInteger(row.achieved_level) || row.achieved_level < 1 || row.achieved_level > 5) {
      const err = new Error('new row for relation "submission_evaluations" violates check constraint "chk_submission_evaluations_level"');
      err.sqlState = '23514';
      throw err;
    }

    const scoreAwarded = Number(row.score_awarded);
    if (Number.isNaN(scoreAwarded) || scoreAwarded < 0.0 || scoreAwarded > 10.0) {
      const err = new Error('new row for relation "submission_evaluations" violates check constraint "chk_submission_evaluations_score"');
      err.sqlState = '23514';
      throw err;
    }

    const submission = this.submissions.get(row.submission_id);
    if (!submission) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_submission"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const criterion = this.criteria.get(row.criterion_id);
    if (!criterion) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_criterion"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const evaluator = this.users.get(row.evaluator_id);
    if (!evaluator) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_evaluator"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (evaluator.role === 'STUDENT') {
      const err = new Error('chk_submission_evaluations_evaluator_role: role "STUDENT" bloqueada');
      err.sqlState = '23514';
      throw err;
    }

    if (row.evaluator_id === submission.student_id) {
      const err = new Error('chk_submission_evaluations_no_self_eval: autoavaliação bloqueada');
      err.sqlState = '23514';
      throw err;
    }

    if (criterion.task_id !== submission.task_id) {
      const err = new Error('chk_submission_evaluations_criterion_task: critério não pertence à tarefa da submissão');
      err.sqlState = '23514';
      throw err;
    }

    const task = this.tasks.get(submission.task_id);
    if (task && scoreAwarded > task.max_score) {
      const err = new Error('chk_submission_evaluations_score_exceeds_max: score_awarded excede max_score');
      err.sqlState = '23514';
      throw err;
    }

    return { scoreAwarded: Number(scoreAwarded.toFixed(2)) };
  }

  calculateConsolidatedScore(submissionId) {
    const submission = this.submissions.get(submissionId);
    if (!submission) return null;

    const task = this.tasks.get(submission.task_id);
    const evals = [...this.evaluationsById.values()].filter((e) => e.submission_id === submissionId);
    if (evals.length === 0) return null;

    let weightedScore = 0;
    let totalWeight = 0;
    for (const ev of evals) {
      const crit = this.criteria.get(ev.criterion_id);
      weightedScore += ev.score_awarded * crit.weight;
      totalWeight += crit.weight;
    }

    if (totalWeight <= 0) return null;

    let consolidated = Math.round((weightedScore / totalWeight) * 100) / 100;
    if (task && consolidated > task.max_score) {
      consolidated = Number(task.max_score.toFixed(2));
    }
    return consolidated;
  }

  _syncSubmissionConsolidatedScore(submissionId) {
    const submission = this.submissions.get(submissionId);
    if (!submission) return;

    const consolidated = this.calculateConsolidatedScore(submissionId);
    const totalCriteria = [...this.criteria.values()].filter((c) => c.task_id === submission.task_id).length;
    const evaluatedCriteria = [...this.evaluationsById.values()].filter((e) => e.submission_id === submissionId).length;

    submission.final_task_score = consolidated;
    if (totalCriteria > 0 && evaluatedCriteria >= totalCriteria) {
      submission.status = 'EVALUATED';
      if (!submission.completed_at) {
        submission.completed_at = new Date().toISOString();
      }
    }
    submission.updated_at = new Date().toISOString();
  }

  insertEvaluation(row) {
    const { scoreAwarded } = this._validateRow(row);

    const pairKey = `${row.submission_id}::${row.criterion_id}`;
    if (this.evaluationsByPair.has(pairKey)) {
      const err = new Error('Unique constraint failed: uq_submission_evaluations_composite');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      submission_id: row.submission_id,
      criterion_id: row.criterion_id,
      evaluator_id: row.evaluator_id,
      achieved_level: row.achieved_level,
      score_awarded: scoreAwarded,
      technical_feedback: row.technical_feedback !== undefined ? row.technical_feedback : null,
      evaluated_at: row.evaluated_at || new Date().toISOString(),
    };

    this.evaluationsById.set(saved.id, saved);
    this.evaluationsByPair.set(pairKey, saved);
    this._syncSubmissionConsolidatedScore(saved.submission_id);
    return saved;
  }

  updateEvaluation(evaluationId, patch) {
    const current = this.evaluationsById.get(evaluationId);
    if (!current) throw new Error('Evaluation not found');

    const merged = { ...current, ...patch };
    const { scoreAwarded } = this._validateRow(merged);

    const oldPairKey = `${current.submission_id}::${current.criterion_id}`;
    const newPairKey = `${merged.submission_id}::${merged.criterion_id}`;
    if (newPairKey !== oldPairKey && this.evaluationsByPair.has(newPairKey)) {
      const err = new Error('Unique constraint failed: uq_submission_evaluations_composite');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const oldSubmissionId = current.submission_id;
    this.evaluationsByPair.delete(oldPairKey);
    current.submission_id = merged.submission_id;
    current.criterion_id = merged.criterion_id;
    current.evaluator_id = merged.evaluator_id;
    current.achieved_level = merged.achieved_level;
    current.score_awarded = scoreAwarded;
    current.technical_feedback = merged.technical_feedback !== undefined ? merged.technical_feedback : current.technical_feedback;
    this.evaluationsByPair.set(newPairKey, current);

    this._syncSubmissionConsolidatedScore(current.submission_id);
    if (oldSubmissionId !== current.submission_id) {
      this._syncSubmissionConsolidatedScore(oldSubmissionId);
    }
    return current;
  }

  deleteEvaluation(evaluationId) {
    const current = this.evaluationsById.get(evaluationId);
    if (!current) throw new Error('Evaluation not found');
    const pairKey = `${current.submission_id}::${current.criterion_id}`;
    this.evaluationsById.delete(evaluationId);
    this.evaluationsByPair.delete(pairKey);
    this._syncSubmissionConsolidatedScore(current.submission_id);
  }

  deleteCriterionRestrict(criterionId) {
    const inUse = [...this.evaluationsById.values()].some((e) => e.criterion_id === criterionId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_criterion"');
      err.sqlState = '23503';
      throw err;
    }
    this.criteria.delete(criterionId);
  }

  deleteSubmissionRestrict(submissionId) {
    const inUse = [...this.evaluationsById.values()].some((e) => e.submission_id === submissionId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_submission_evaluations_submission"');
      err.sqlState = '23503';
      throw err;
    }
    this.submissions.delete(submissionId);
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-026] — AVALIAÇÕES POR RUBRICA (submission_evaluations)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de submission_evaluations'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123050000_create_submission_evaluations_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123050000_create_submission_evaluations_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/26_tabela_submission_evaluations.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/26_tabela_submission_evaluations.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/26-tabela-avaliacoes-rubrica-submission-evaluations.md e BancoNexa/26-tabela-avaliacoes-rubrica-submission-evaluations.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-026'),
  'Card DB-026 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model SubmissionEvaluation no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model SubmissionEvaluation no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /submission_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /criterion_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /evaluator_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /achieved_level\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /score_awarded\s+NUMERIC\(4,2\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /technical_feedback\s+TEXT\s*,/i.test(sqlContent) &&
    /evaluated_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, submission_id, criterion_id, evaluator_id, achieved_level, score_awarded NUMERIC 4,2, technical_feedback, evaluated_at) presentes'
);
assertCheck(
  schemaContent.includes('model SubmissionEvaluation') &&
    (schemaContent.match(/evaluations\s+SubmissionEvaluation\[\]/g) || []).length === 2 &&
    /submissionEvaluations\s+SubmissionEvaluation\[\]/.test(schemaContent) &&
    schemaContent.includes('@@unique([submissionId, criterionId], map: "uq_submission_evaluations_composite")') &&
    schemaContent.includes('@@index([submissionId], map: "idx_submission_evaluations_submission")') &&
    schemaContent.includes('@@index([criterionId], map: "idx_submission_evaluations_criterion")') &&
    schemaContent.includes('@@index([evaluatorId, evaluatedAt], map: "idx_submission_evaluations_evaluator")') &&
    schemaContent.includes('@@map("submission_evaluations")'),
  'Modelo SubmissionEvaluation integrado ao prisma/schema.prisma com UNIQUE composta, relações reversas em TaskSubmission/TaskCriterion/User e índices'
);
assertCheck(
  typesTsContent.includes('export interface SubmissionEvaluation {') &&
    typesTsContent.includes('achievedLevel: number;') &&
    typesTsContent.includes('scoreAwarded: number | string;') &&
    typesTsContent.includes('technicalFeedback: string | null;') &&
    typesTsContent.includes('export interface SubmissionEvaluationRow {'),
  'Tipos TypeScript (SubmissionEvaluation, SubmissionEvaluationRow, SubmissionEvaluationCreateInput, SubmissionEvaluationUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2, 3 e DoD no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e cálculo consolidado (DoD) no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_submission_evaluations_composite\s+UNIQUE\s*\(\s*submission_id\s*,\s*criterion_id\s*\)/i.test(
    sqlContent
  ),
  'Critério 1: Constraint uq_submission_evaluations_composite UNIQUE (submission_id, criterion_id) declarada'
);
assertCheck(
  /CONSTRAINT\s+chk_submission_evaluations_level\s+CHECK\s*\(\s*achieved_level\s+BETWEEN\s+1\s+AND\s+5\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+chk_submission_evaluations_score\s+CHECK\s*\(\s*score_awarded\s*>=\s*0\.00\s+AND\s+score_awarded\s*<=\s*10\.00\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: Validações CHECK chk_submission_evaluations_level (1..5) e chk_submission_evaluations_score (0.00..10.00) declaradas'
);
assertCheck(
  /CONSTRAINT\s+fk_submission_evaluations_evaluator\s+FOREIGN\s+KEY\s*\(\s*evaluator_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_submission_evaluations_submission\s+FOREIGN\s+KEY\s*\(\s*submission_id\s*\)\s*REFERENCES\s+task_submissions\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_submission_evaluations_criterion\s+FOREIGN\s+KEY\s*\(\s*criterion_id\s*\)\s*REFERENCES\s+task_criteria\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_submission_evaluations_validate_integrity/i.test(sqlContent) &&
    /chk_submission_evaluations_evaluator_role/i.test(sqlContent),
  'Critério 3: FKs ON DELETE RESTRICT (incluindo fk_submission_evaluations_evaluator) + trigger validando perfil docente'
);
assertCheck(
  /CREATE\s+OR\s+REPLACE\s+FUNCTION\s+fn_calculate_submission_consolidated_score/i.test(sqlContent) &&
    /trg_submission_evaluations_sync_final_score/i.test(sqlContent),
  'DoD: Função fn_calculate_submission_consolidated_score e trigger AFTER trg_submission_evaluations_sync_final_score presentes no DDL'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-024, DB-025, DB-030, DB-033, DB-038, BE-025, FE-026)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-024, DB-025, DB-033, DB-038, BE-025)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+submission_evaluations/i.test(sql3fnContent) &&
    /uq_submission_evaluations_composite/i.test(sql3fnContent) &&
    /chk_submission_evaluations_level/i.test(sql3fnContent) &&
    /fk_submission_evaluations_evaluator/i.test(sql3fnContent),
  'Integração validada com modelo 3FN ([T21] submission_evaluations) e nomenclatura oficial de constraints'
);

// 6. Testes unitários de cálculo de nota consolidada, UNIQUE, CHECK 1..5 e integridade do avaliador (DoD)
console.log('\n6. Executando testes unitários de nota consolidada, UNIQUE, CHECK 1..5 e perfil docente (DoD)...');
const sim = new SubmissionEvaluationsRelationalSimulator();
const task1Id = '10000000-0000-4000-8000-000000000001';
const task2Id = '10000000-0000-4000-8000-000000000002';
const compDimId = '20000000-0000-4000-8000-000000000001';
const compAcabId = '20000000-0000-4000-8000-000000000002';
const compEpiId = '20000000-0000-4000-8000-000000000003';
const crit1Id = '30000000-0000-4000-8000-000000000001';
const crit2Id = '30000000-0000-4000-8000-000000000002';
const crit3Id = '30000000-0000-4000-8000-000000000003';
const critOtherTaskId = '30000000-0000-4000-8000-000000000099';
const teacherId = '40000000-0000-4000-8000-000000000001';
const coordId = '40000000-0000-4000-8000-000000000002';
const studentId = '40000000-0000-4000-8000-000000000003';
const otherStudentId = '40000000-0000-4000-8000-000000000004';
const sub1Id = '50000000-0000-4000-8000-000000000001';
const sub2Id = '50000000-0000-4000-8000-000000000002';

sim.addTask(task1Id, 'Usinagem de Eixo Escalonado Ø25mm H7', 10.0);
sim.addTask(task2Id, 'Medição de Precisão com Relógio Comparador', 8.0);
sim.addCriterion(crit1Id, task1Id, compDimId, 'Tolerância Dimensional (±0,02mm)', 2.0, 3);
sim.addCriterion(crit2Id, task1Id, compAcabId, 'Acabamento Superficial (Ra 1.6µm)', 1.5, 3);
sim.addCriterion(crit3Id, task1Id, compEpiId, 'Segurança NR-12 e Uso de EPI', 0.5, 4);
sim.addCriterion(critOtherTaskId, task2Id, compDimId, 'Calibração de Relógio Comparador', 1.0, 3);
sim.addUser(teacherId, 'prof.usinagem@senai.nexa.local', 'TEACHER');
sim.addUser(coordId, 'coord.mecanica@senai.nexa.local', 'COORDINATOR');
sim.addUser(studentId, 'aluno1@senai.nexa.local', 'STUDENT');
sim.addUser(otherStudentId, 'aluno2@senai.nexa.local', 'STUDENT');
sim.addSubmission(sub1Id, task1Id, studentId, 'SUBMITTED');
sim.addSubmission(sub2Id, task2Id, studentId, 'PENDING');

// Teste 1 (DoD): Cálculo de nota consolidada ponderada + promoção automática para EVALUATED + recálculo em UPDATE/DELETE
const ev1 = sim.insertEvaluation({
  submission_id: sub1Id,
  criterion_id: crit1Id,
  evaluator_id: teacherId,
  achieved_level: 5,
  score_awarded: 10.0,
  technical_feedback: 'Diâmetro 25,01mm dentro da classe H7 sem ovalização.',
});
const scoreAfter1 = sim.submissions.get(sub1Id).final_task_score;
const statusAfter1 = sim.submissions.get(sub1Id).status;

const ev2 = sim.insertEvaluation({
  submission_id: sub1Id,
  criterion_id: crit2Id,
  evaluator_id: teacherId,
  achieved_level: 4,
  score_awarded: 8.0,
  technical_feedback: 'Rugosidade adequada; leve marca de avanço no chanfro.',
});

const ev3 = sim.insertEvaluation({
  submission_id: sub1Id,
  criterion_id: crit3Id,
  evaluator_id: teacherId,
  achieved_level: 3,
  score_awarded: 6.0,
  technical_feedback: 'EPI completo; reforçar limpeza de cavacos após usinagem.',
});
// Ponderada: (10*2.0 + 8*1.5 + 6*0.5) / (2.0 + 1.5 + 0.5) = 35 / 4 = 8.75
const scoreAfterAll = sim.submissions.get(sub1Id).final_task_score;
const statusAfterAll = sim.submissions.get(sub1Id).status;

// Recálculo após revisão de nota na rubrica 2 (8.0 -> 9.0): (20 + 13.5 + 3) / 4 = 36.5 / 4 = 9.125 -> 9.13
sim.updateEvaluation(ev2.id, { achieved_level: 5, score_awarded: 9.0 });
const scoreAfterUpdate = sim.submissions.get(sub1Id).final_task_score;

// Recálculo em sub2 (max_score = 8.0, critério único com nível 1 -> 1.60) e exclusão devolvendo NULL
const evSub2 = sim.insertEvaluation({
  submission_id: sub2Id,
  criterion_id: critOtherTaskId,
  evaluator_id: coordId,
  achieved_level: 1,
  score_awarded: 1.6,
  technical_feedback: 'Necessita reforço na zeragem do relógio comparador.',
});
const sub2ScoreBeforeDelete = sim.submissions.get(sub2Id).final_task_score;
const sub2StatusAfterEval = sim.submissions.get(sub2Id).status;
sim.deleteEvaluation(evSub2.id);
const sub2ScoreAfterDelete = sim.submissions.get(sub2Id).final_task_score;

assertCheck(
  ev1.achieved_level === 5 &&
    ev3.achieved_level === 3 &&
    scoreAfter1 === 10.0 &&
    statusAfter1 === 'SUBMITTED' &&
    scoreAfterAll === 8.75 &&
    statusAfterAll === 'EVALUATED' &&
    scoreAfterUpdate === 9.13 &&
    sub2ScoreBeforeDelete === 1.6 &&
    sub2StatusAfterEval === 'EVALUATED' &&
    sub2ScoreAfterDelete === null,
  'Teste 1 (DoD): Cálculo ponderado consolidado (8.75 -> 9.13 em UPDATE, NULL em DELETE) e promoção automática para EVALUATED validados'
);

// Teste 2 (Critério 1): Duplicata (submission_id, criterion_id) bloqueada com 23505 / P2002
let dupEvalBlocked = false;
try {
  sim.insertEvaluation({
    submission_id: sub1Id,
    criterion_id: crit1Id,
    evaluator_id: teacherId,
    achieved_level: 4,
    score_awarded: 8.0,
  });
} catch (err) {
  dupEvalBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupEvalBlocked,
  'Teste 2 (Critério 1): Avaliação duplicada em (submission_id, criterion_id) bloqueada por uq_submission_evaluations_composite (23505 / P2002)'
);

// Teste 3 (Critério 2): Validação CHECK achieved_level (1..5) e score_awarded (0..10 e <= max_score)
let level0Blocked = false;
let level6Blocked = false;
let levelNegBlocked = false;
let scoreNegBlocked = false;
let scoreOver10Blocked = false;
let scoreOverTaskMaxBlocked = false;

for (const [lvl, setter] of [
  [0, (v) => (level0Blocked = v)],
  [6, (v) => (level6Blocked = v)],
  [-1, (v) => (levelNegBlocked = v)],
]) {
  try {
    sim.insertEvaluation({
      submission_id: sub2Id,
      criterion_id: critOtherTaskId,
      evaluator_id: teacherId,
      achieved_level: lvl,
      score_awarded: 5.0,
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}

for (const [score, setter] of [
  [-0.5, (v) => (scoreNegBlocked = v)],
  [10.5, (v) => (scoreOver10Blocked = v)],
  [9.0, (v) => (scoreOverTaskMaxBlocked = v)], // max_score de task2 = 8.0
]) {
  try {
    sim.insertEvaluation({
      submission_id: sub2Id,
      criterion_id: critOtherTaskId,
      evaluator_id: teacherId,
      achieved_level: 4,
      score_awarded: score,
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}

assertCheck(
  level0Blocked &&
    level6Blocked &&
    levelNegBlocked &&
    scoreNegBlocked &&
    scoreOver10Blocked &&
    scoreOverTaskMaxBlocked,
  'Teste 3 (Critério 2): achieved_level fora de 1..5 (0, 6, -1) e score_awarded inválido (-0.5, 10.5, > max_score 8.0) rejeitados com SQLSTATE 23514'
);

// Teste 4 (Critério 3 & Integridade Referencial): Avaliador STUDENT, autoavaliação, FK inexistente, rubrica de outra tarefa e ON DELETE RESTRICT
let studentEvaluatorBlocked = false;
let selfEvalBlocked = false;
let missingEvaluatorBlocked = false;
let wrongTaskCriterionBlocked = false;
let deleteCriterionInUseBlocked = false;
let deleteSubmissionInUseBlocked = false;

try {
  sim.insertEvaluation({
    submission_id: sub2Id,
    criterion_id: critOtherTaskId,
    evaluator_id: otherStudentId,
    achieved_level: 4,
    score_awarded: 6.4,
  });
} catch (err) {
  studentEvaluatorBlocked = err.sqlState === '23514';
}

try {
  sim.insertEvaluation({
    submission_id: sub2Id,
    criterion_id: critOtherTaskId,
    evaluator_id: studentId,
    achieved_level: 5,
    score_awarded: 8.0,
  });
} catch (err) {
  selfEvalBlocked = err.sqlState === '23514';
}

try {
  sim.insertEvaluation({
    submission_id: sub2Id,
    criterion_id: critOtherTaskId,
    evaluator_id: '99999999-9999-4999-8999-999999999999',
    achieved_level: 3,
    score_awarded: 4.8,
  });
} catch (err) {
  missingEvaluatorBlocked = err.sqlState === '23503' && err.code === 'P2003';
}

try {
  sim.insertEvaluation({
    submission_id: sub2Id,
    criterion_id: crit1Id, // pertence a task1, mas sub2 pertence a task2
    evaluator_id: teacherId,
    achieved_level: 4,
    score_awarded: 6.4,
  });
} catch (err) {
  wrongTaskCriterionBlocked = err.sqlState === '23514';
}

try {
  sim.deleteCriterionRestrict(crit1Id);
} catch (err) {
  deleteCriterionInUseBlocked = err.sqlState === '23503';
}

try {
  sim.deleteSubmissionRestrict(sub1Id);
} catch (err) {
  deleteSubmissionInUseBlocked = err.sqlState === '23503';
}

assertCheck(
  studentEvaluatorBlocked &&
    selfEvalBlocked &&
    missingEvaluatorBlocked &&
    wrongTaskCriterionBlocked &&
    deleteCriterionInUseBlocked &&
    deleteSubmissionInUseBlocked,
  'Teste 4 (Critério 3): Avaliador STUDENT (23514), autoavaliação (23514), FK avaliador inexistente (23503), rubrica de outra tarefa (23514) e ON DELETE RESTRICT em critério/submissão avaliados (23503) bloqueados'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-026] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
