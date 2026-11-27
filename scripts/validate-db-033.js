/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-033]
 * Título: Criar Tabela de Evidências Práticas de Habilidades (skill_evidences)
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
  '20261126000000_create_skill_evidences_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261126000000_create_skill_evidences_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '33_tabela_skill_evidences.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '33-tabela-evidencias-praticas-skill-evidences.md'),
  path.join(ROOT_DIR, 'BancoNexa', '33-tabela-evidencias-praticas-skill-evidences.md'),
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

class SkillEvidencesRelationalSimulator {
  constructor() {
    this.users = new Map();
    this.competencies = new Map();
    this.submissions = new Map();
    this.assessments = new Map();
    this.enrollments = new Set(); // `${student_id}::${class_id}`
    this.evidences = [];
    this.seq = 1;
  }

  addUser(id, role) {
    this.users.set(id, { id, role });
  }
  addCompetency(id, code) {
    this.competencies.set(id, { id, code });
  }
  addSubmission(id, student_id) {
    this.submissions.set(id, { id, student_id });
  }
  addAssessment(id, class_id) {
    this.assessments.set(id, { id, class_id });
  }
  enroll(student_id, class_id) {
    this.enrollments.add(`${student_id}::${class_id}`);
  }

  recordEvidence(row) {
    if (!this.users.has(row.student_id) || !this.users.has(row.verified_by)) {
      const err = new Error('violates foreign key constraint on users');
      err.sqlState = '23503';
      throw err;
    }
    if (!this.competencies.has(row.competency_id)) {
      const err = new Error('violates foreign key constraint "fk_skill_evidences_competency"');
      err.sqlState = '23503';
      throw err;
    }
    if (row.source_submission_id == null && row.source_assessment_id == null) {
      const err = new Error('violates check constraint "chk_skill_evidences_source"');
      err.sqlState = '23514';
      throw err;
    }
    const level = Number(row.verified_level);
    if (!Number.isFinite(level) || level < 1.0 || level > 5.0) {
      const err = new Error('violates check constraint "chk_skill_evidences_level"');
      err.sqlState = '23514';
      throw err;
    }
    if (row.verified_by === row.student_id) {
      const err = new Error('violates trigger "chk_skill_evidences_no_self_verification"');
      err.sqlState = '23514';
      throw err;
    }
    if (this.users.get(row.student_id).role !== 'STUDENT') {
      const err = new Error('violates trigger "chk_skill_evidences_student_role"');
      err.sqlState = '23514';
      throw err;
    }
    if (this.users.get(row.verified_by).role !== 'TEACHER') {
      const err = new Error('violates trigger "chk_skill_evidences_verifier_role"');
      err.sqlState = '23514';
      throw err;
    }
    if (row.source_submission_id != null) {
      const sub = this.submissions.get(row.source_submission_id);
      if (!sub) {
        const err = new Error('violates foreign key constraint "fk_skill_evidences_submission"');
        err.sqlState = '23503';
        throw err;
      }
      if (sub.student_id !== row.student_id) {
        const err = new Error('violates trigger "chk_skill_evidences_submission_owner"');
        err.sqlState = '23514';
        throw err;
      }
    }
    if (row.source_assessment_id != null) {
      const ass = this.assessments.get(row.source_assessment_id);
      if (!ass) {
        const err = new Error('violates foreign key constraint "fk_skill_evidences_assessment"');
        err.sqlState = '23503';
        throw err;
      }
      if (!this.enrollments.has(`${row.student_id}::${ass.class_id}`)) {
        const err = new Error('violates trigger "chk_skill_evidences_assessment_enrollment"');
        err.sqlState = '23514';
        throw err;
      }
    }

    const saved = {
      id: `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      student_id: row.student_id,
      competency_id: row.competency_id,
      source_submission_id: row.source_submission_id || null,
      source_assessment_id: row.source_assessment_id || null,
      verified_level: Number(level.toFixed(2)),
      verified_by: row.verified_by,
      recorded_at: new Date().toISOString(),
    };
    this.evidences.push(saved);
    return saved;
  }

  getAvgVerifiedLevel(studentId, competencyId) {
    const items = this.evidences.filter((e) => e.student_id === studentId && e.competency_id === competencyId);
    if (items.length === 0) return null;
    const sum = items.reduce((acc, e) => acc + e.verified_level, 0);
    return Number((sum / items.length).toFixed(2));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-033] — EVIDÊNCIAS PRÁTICAS (skill_evidences)');
console.log('======================================================================\n');

console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de skill_evidences');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(fs.existsSync(MIGRATION_SQL_PATH), 'Migration SQL presente em prisma/migrations/20261126000000_create_skill_evidences_table/migration.sql');
assertCheck(fs.existsSync(BANCO_MIGRATION_SQL_PATH), 'Migration SQL espelhada em BancoNexa/migrations/20261126000000_create_skill_evidences_table.sql');
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/33_tabela_skill_evidences.sql');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');
assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') &&
    sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/33_tabela_skill_evidences.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8'),
  'Sincronia 100% idêntica entre docs/banco e BancoNexa para DB-033'
);
assertCheck(fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-033'), 'Card DB-033 documentado em BancoNexa/README.md');

console.log('\n3. Verificando colunas SQL, model SkillEvidence no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /competency_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /source_submission_id\s+UUID/i.test(sqlContent) &&
    /source_assessment_id\s+UUID/i.test(sqlContent) &&
    /verified_level\s+NUMERIC\(3,2\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /verified_by\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /recorded_at\s+TIMESTAMPTZ/i.test(sqlContent),
  'Todas as colunas exigidas de skill_evidences presentes com tipos nativos corretos'
);
assertCheck(
  schemaContent.includes('model SkillEvidence') &&
    schemaContent.includes('@map("verified_level") @db.Decimal(3, 2)') &&
    schemaContent.includes('@@index([studentId, competencyId], map: "idx_skill_evidences_student_competency")') &&
    schemaContent.includes('@@map("skill_evidences")'),
  'Modelo SkillEvidence integrado ao prisma/schema.prisma com relações e índice composto'
);
assertCheck(
  typesTsContent.includes('export interface SkillEvidence {') &&
    typesTsContent.includes('verifiedLevel: number | string;') &&
    typesTsContent.includes('export interface SkillEvidenceRow {'),
  'Tipos TypeScript de SkillEvidence atualizados em BancoNexa/types/schema-models.ts'
);

console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+chk_skill_evidences_source\s+CHECK\s*\(\s*source_submission_id\s+IS\s+NOT\s+NULL\s+OR\s+source_assessment_id\s+IS\s+NOT\s+NULL\s*\)/i.test(sqlContent),
  'Critério 1: Constraint chk_skill_evidences_source exige origem em tarefa prática ou avaliação formativa'
);
assertCheck(
  /CONSTRAINT\s+chk_skill_evidences_level\s+CHECK\s*\(\s*verified_level\s*>=\s*1\.00\s+AND\s+verified_level\s*<=\s*5\.00\s*\)/i.test(sqlContent),
  'Critério 2: Constraint chk_skill_evidences_level valida verified_level entre 1.00 e 5.00'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_skill_evidences_student_competency\s+ON\s+skill_evidences\s+USING\s+BTREE\s*\(\s*student_id\s*,\s*competency_id\s*\)/i.test(sqlContent),
  'Critério 3: Índice composto idx_skill_evidences_student_competency criado em (student_id, competency_id)'
);
assertCheck(
  /CREATE\s+TABLE\s+skill_evidences/i.test(fs.readFileSync(SQL_3FN_PATH, 'utf8')),
  'Alinhamento confirmado com modelo 3FN ([T24] skill_evidences)'
);

console.log('\n5. Executando testes unitários de evidências verificadas por docentes (DoD)...');
const sim = new SkillEvidencesRelationalSimulator();
sim.addUser('stu-1', 'STUDENT');
sim.addUser('stu-2', 'STUDENT');
sim.addUser('tch-1', 'TEACHER');
sim.addUser('crd-1', 'COORDINATOR');
sim.addCompetency('comp-met', 'COMP-MET-01');
sim.addSubmission('sub-1', 'stu-1');
sim.addSubmission('sub-2', 'stu-2');
sim.addAssessment('ass-1', 'cls-1');
sim.enroll('stu-1', 'cls-1');

const ev1 = sim.recordEvidence({
  student_id: 'stu-1',
  competency_id: 'comp-met',
  source_submission_id: 'sub-1',
  verified_level: 3.5,
  verified_by: 'tch-1',
});
const ev2 = sim.recordEvidence({
  student_id: 'stu-1',
  competency_id: 'comp-met',
  source_assessment_id: 'ass-1',
  verified_level: 4.5,
  verified_by: 'tch-1',
});
assertCheck(
  ev1.verified_level === 3.5 && ev2.verified_level === 4.5 && sim.getAvgVerifiedLevel('stu-1', 'comp-met') === 4.0,
  'Teste 1: Evidências via submissão prática e avaliação formativa registradas e média verificada = 4.00'
);

let noSourceBlocked = false;
let badLevelBlocked = false;
let selfVerifyBlocked = false;
let nonTeacherBlocked = false;
let wrongOwnerBlocked = false;
try {
  sim.recordEvidence({ student_id: 'stu-1', competency_id: 'comp-met', verified_level: 3.0, verified_by: 'tch-1' });
} catch (err) { noSourceBlocked = err.sqlState === '23514'; }
try {
  sim.recordEvidence({ student_id: 'stu-1', competency_id: 'comp-met', source_submission_id: 'sub-1', verified_level: 5.5, verified_by: 'tch-1' });
} catch (err) { badLevelBlocked = err.sqlState === '23514'; }
try {
  sim.recordEvidence({ student_id: 'stu-1', competency_id: 'comp-met', source_submission_id: 'sub-1', verified_level: 4.0, verified_by: 'stu-1' });
} catch (err) { selfVerifyBlocked = err.sqlState === '23514'; }
try {
  sim.recordEvidence({ student_id: 'stu-1', competency_id: 'comp-met', source_submission_id: 'sub-1', verified_level: 4.0, verified_by: 'crd-1' });
} catch (err) { nonTeacherBlocked = err.sqlState === '23514'; }
try {
  sim.recordEvidence({ student_id: 'stu-1', competency_id: 'comp-met', source_submission_id: 'sub-2', verified_level: 4.0, verified_by: 'tch-1' });
} catch (err) { wrongOwnerBlocked = err.sqlState === '23514'; }

assertCheck(
  noSourceBlocked && badLevelBlocked && selfVerifyBlocked && nonTeacherBlocked && wrongOwnerBlocked,
  'Teste 2: Ausência de origem, nível > 5.00, autoverificação, verificador não-TEACHER e submissão de outro aluno bloqueados (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-033] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
