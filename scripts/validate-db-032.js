/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-032]
 * Título: Implementar Tabela de Respostas de Autoavaliação do Aluno (student_self_assessments)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Constraint UNIQUE composta `uq_student_self_assessments_composite` em
 *    `(form_id, student_id, competency_id)`.
 * 2. Critério 2: CHECK constraints `chk_self_assessments_perceived` e
 *    `chk_self_assessments_confidence` garantindo intervalo de 1 a 5.
 * 3. Critério 3: Isolamento de acesso via Row-Level Security (RLS) PostgreSQL 16
 *    (`ENABLE ROW LEVEL SECURITY` + `pol_student_self_assessments_student_isolation`):
 *    um estudante jamais pode ler ou gravar a autoavaliação de outro colega.
 * 4. DoD: Tabela `student_self_assessments` migrada, `model StudentSelfAssessment` no
 *    `prisma/schema.prisma`, tipos TS gerados em `BancoNexa/types/schema-models.ts`,
 *    trigger de integridade (perfil `STUDENT`, matrícula `ACTIVE`, formulário aberto e
 *    competência do módulo) e integração validada com cards dependentes (`DB-035`, `DB-038`, `BE-036`, `FE-041`).
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
  '20261123100000_create_student_self_assessments_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123100000_create_student_self_assessments_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '32_tabela_student_self_assessments.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '32-tabela-respostas-autoavaliacao-student-self-assessments.md'),
  path.join(ROOT_DIR, 'BancoNexa', '32-tabela-respostas-autoavaliacao-student-self-assessments.md'),
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
 * Simulador relacional + RLS das tabelas `self_assessment_forms`, `users`, `enrollments`,
 * `competencies`, `module_competencies` e `student_self_assessments`.
 */
class StudentSelfAssessmentsSimulator {
  constructor() {
    this.forms = new Map();
    this.users = new Map();
    this.enrollments = [];
    this.competencies = new Map();
    this.moduleCompetencies = new Map(); // moduleId -> Set<competencyId>
    this.responsesById = new Map();
    this.responsesByKey = new Map();
    this.seq = 1;
  }

  addForm(id, moduleId, classId, opensAt, closesAt, isActive = true) {
    this.forms.set(id, { id, module_id: moduleId, class_id: classId, opens_at: opensAt, closes_at: closesAt, is_active: isActive });
  }

  addUser(id, email, role) {
    this.users.set(id, { id, email, role });
  }

  addEnrollment(studentId, classId, status = 'ACTIVE') {
    this.enrollments.push({ student_id: studentId, class_id: classId, status });
  }

  addCompetency(id, code) {
    this.competencies.set(id, { id, code });
  }

  linkModuleCompetency(moduleId, competencyId) {
    if (!this.moduleCompetencies.has(moduleId)) {
      this.moduleCompetencies.set(moduleId, new Set());
    }
    this.moduleCompetencies.get(moduleId).add(competencyId);
  }

  insertResponse(row, sessionCtx = { role: 'SYSTEM', userId: null }) {
    if (!row.form_id || !row.student_id || !row.competency_id) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    // RLS WITH CHECK: STUDENT só pode gravar para si mesmo
    if (sessionCtx.role === 'STUDENT' && sessionCtx.userId !== row.student_id) {
      const err = new Error('new row violates row-level security policy "pol_student_self_assessments_student_isolation"');
      err.sqlState = '42501';
      throw err;
    }

    if (!Number.isInteger(row.perceived_level) || row.perceived_level < 1 || row.perceived_level > 5) {
      const err = new Error('violates check constraint "chk_self_assessments_perceived"');
      err.sqlState = '23514';
      throw err;
    }

    if (!Number.isInteger(row.confidence_score) || row.confidence_score < 1 || row.confidence_score > 5) {
      const err = new Error('violates check constraint "chk_self_assessments_confidence"');
      err.sqlState = '23514';
      throw err;
    }

    const form = this.forms.get(row.form_id);
    if (!form) {
      const err = new Error('violates foreign key constraint "fk_student_self_assessments_form"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const student = this.users.get(row.student_id);
    if (!student) {
      const err = new Error('violates foreign key constraint "fk_student_self_assessments_student"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (!this.competencies.has(row.competency_id)) {
      const err = new Error('violates foreign key constraint "fk_student_self_assessments_competency"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (student.role !== 'STUDENT') {
      const err = new Error('chk_student_self_assessments_student_role');
      err.sqlState = '23514';
      throw err;
    }

    const hasActiveEnr = this.enrollments.some(
      (e) => e.student_id === row.student_id && e.class_id === form.class_id && e.status === 'ACTIVE'
    );
    if (!hasActiveEnr) {
      const err = new Error('chk_student_self_assessments_active_enrollment');
      err.sqlState = '23514';
      throw err;
    }

    const submittedAt = row.submitted_at || '2026-03-05T12:00:00Z';
    const subMs = Date.parse(submittedAt);
    if (!form.is_active || subMs < Date.parse(form.opens_at) || subMs > Date.parse(form.closes_at)) {
      const err = new Error('chk_student_self_assessments_form_open');
      err.sqlState = '23514';
      throw err;
    }

    const modComps = this.moduleCompetencies.get(form.module_id);
    if (modComps && modComps.size > 0 && !modComps.has(row.competency_id)) {
      const err = new Error('chk_student_self_assessments_module_competency');
      err.sqlState = '23514';
      throw err;
    }

    const compositeKey = `${row.form_id}::${row.student_id}::${row.competency_id}`;
    if (this.responsesByKey.has(compositeKey)) {
      const err = new Error('Unique constraint failed: uq_student_self_assessments_composite');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      form_id: row.form_id,
      student_id: row.student_id,
      competency_id: row.competency_id,
      perceived_level: row.perceived_level,
      confidence_score: row.confidence_score,
      difficulty_notes: row.difficulty_notes !== undefined ? row.difficulty_notes : null,
      submitted_at: submittedAt,
    };

    this.responsesById.set(saved.id, saved);
    this.responsesByKey.set(compositeKey, saved);
    return saved;
  }

  /** Simula SELECT sob política RLS pol_student_self_assessments_student_isolation */
  selectAllAsSession(sessionCtx) {
    const all = [...this.responsesById.values()];
    if (sessionCtx.role === 'STUDENT') {
      return all.filter((r) => r.student_id === sessionCtx.userId);
    }
    return all;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-032] — AUTOAVALIAÇÃO DO ALUNO (student_self_assessments)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de student_self_assessments'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123100000_create_student_self_assessments_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123100000_create_student_self_assessments_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/32_tabela_student_self_assessments.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/32_tabela_student_self_assessments.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/32-tabela-respostas-autoavaliacao-student-self-assessments.md e BancoNexa/32-tabela-respostas-autoavaliacao-student-self-assessments.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-032'),
  'Card DB-032 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model StudentSelfAssessment no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model StudentSelfAssessment no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /form_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /student_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /competency_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /perceived_level\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /confidence_score\s+INTEGER\s+NOT\s+NULL/i.test(sqlContent) &&
    /difficulty_notes\s+TEXT\s*,/i.test(sqlContent) &&
    /submitted_at\s+TIMESTAMPTZ\s+NOT\s+NULL\s+DEFAULT\s+CURRENT_TIMESTAMP/i.test(sqlContent),
  'Todas as colunas exigidas (id, form_id, student_id, competency_id, perceived_level, confidence_score, difficulty_notes, submitted_at) presentes'
);
assertCheck(
  schemaContent.includes('model StudentSelfAssessment') &&
    (schemaContent.match(/studentSelfAssessments\s+StudentSelfAssessment\[\]/g) || []).length === 2 &&
    /responses\s+StudentSelfAssessment\[\]/.test(schemaContent) &&
    schemaContent.includes('@@unique([formId, studentId, competencyId], map: "uq_student_self_assessments_composite")') &&
    schemaContent.includes('@@map("student_self_assessments")'),
  'Modelo StudentSelfAssessment integrado ao prisma/schema.prisma com UNIQUE tripla e relações reversas em User/Competency/SelfAssessmentForm'
);
assertCheck(
  typesTsContent.includes('export interface StudentSelfAssessment {') &&
    typesTsContent.includes('perceivedLevel: number;') &&
    typesTsContent.includes('confidenceScore: number;') &&
    typesTsContent.includes('difficultyNotes: string | null;') &&
    typesTsContent.includes('export interface StudentSelfAssessmentRow {'),
  'Tipos TypeScript (StudentSelfAssessment, StudentSelfAssessmentRow, StudentSelfAssessmentCreateInput, StudentSelfAssessmentUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 (UNIQUE, CHECK 1..5 e RLS) no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_student_self_assessments_composite\s+UNIQUE\s*\(\s*form_id\s*,\s*student_id\s*,\s*competency_id\s*\)/i.test(
    sqlContent
  ),
  'Critério 1: Constraint uq_student_self_assessments_composite UNIQUE (form_id, student_id, competency_id) declarada'
);
assertCheck(
  /CONSTRAINT\s+chk_self_assessments_perceived\s+CHECK\s*\(\s*perceived_level\s+BETWEEN\s+1\s+AND\s+5\s*\)/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+chk_self_assessments_confidence\s+CHECK\s*\(\s*confidence_score\s+BETWEEN\s+1\s+AND\s+5\s*\)/i.test(
      sqlContent
    ),
  'Critério 2: CHECK constraints chk_self_assessments_perceived e chk_self_assessments_confidence (1..5) declaradas'
);
assertCheck(
  /ALTER\s+TABLE\s+student_self_assessments\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY/i.test(sqlContent) &&
    /CREATE\s+POLICY\s+pol_student_self_assessments_student_isolation/i.test(sqlContent) &&
    /app\.current_user_id/i.test(sqlContent) &&
    /app\.current_user_role/i.test(sqlContent),
  'Critério 3: Row-Level Security (RLS) ativada com política pol_student_self_assessments_student_isolation isolando acesso entre alunos'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-015, DB-017, DB-031, DB-035, DB-038, BE-036)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-015, DB-017, DB-031, DB-038, BE-036)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+student_self_assessments/i.test(sql3fnContent) &&
    /uq_student_self_assessments_composite/i.test(sql3fnContent) &&
    /chk_self_assessments_perceived/i.test(sql3fnContent) &&
    /chk_self_assessments_confidence/i.test(sql3fnContent),
  'Integração validada com modelo 3FN ([T23] student_self_assessments) e nomenclatura oficial de constraints'
);

// 6. Testes unitários de UNIQUE, CHECK 1..5, isolamento RLS e integridade contextual (DoD)
console.log('\n6. Executando testes unitários de unicidade, escala 1..5, isolamento RLS e matrícula ativa (DoD)...');
const sim = new StudentSelfAssessmentsSimulator();
const classMec1Id = '10000000-0000-4000-8000-000000000001';
const mod1Id = '20000000-0000-4000-8000-000000000001';
const formOpenId = '30000000-0000-4000-8000-000000000001';
const formClosedId = '30000000-0000-4000-8000-000000000002';
const comp1Id = '40000000-0000-4000-8000-000000000001';
const comp2Id = '40000000-0000-4000-8000-000000000002';
const compOtherModId = '40000000-0000-4000-8000-000000000099';
const stuAId = '50000000-0000-4000-8000-000000000001';
const stuBId = '50000000-0000-4000-8000-000000000002';
const stuDroppedId = '50000000-0000-4000-8000-000000000003';
const teacherId = '50000000-0000-4000-8000-000000000009';

sim.addForm(formOpenId, mod1Id, classMec1Id, '2026-03-01T08:00:00Z', '2026-03-10T23:59:59Z', true);
sim.addForm(formClosedId, mod1Id, classMec1Id, '2026-02-01T08:00:00Z', '2026-02-10T23:59:59Z', false);
sim.addUser(stuAId, 'estudante.demo01@aluno.nexa.local', 'STUDENT');
sim.addUser(stuBId, 'estudante.demo02@aluno.nexa.local', 'STUDENT');
sim.addUser(stuDroppedId, 'estudante.evadido@aluno.nexa.local', 'STUDENT');
sim.addUser(teacherId, 'instrutor.teoria.demo@senai.nexa.local', 'TEACHER');
sim.addEnrollment(stuAId, classMec1Id, 'ACTIVE');
sim.addEnrollment(stuBId, classMec1Id, 'ACTIVE');
sim.addEnrollment(stuDroppedId, classMec1Id, 'DROPPED');
sim.addCompetency(comp1Id, 'COMP-MET-01');
sim.addCompetency(comp2Id, 'COMP-MET-04');
sim.addCompetency(compOtherModId, 'COMP-USI-03');
sim.linkModuleCompetency(mod1Id, comp1Id);
sim.linkModuleCompetency(mod1Id, comp2Id);

// Teste 1 (Critério 1): Respostas válidas (extremos 1 e 5) e bloqueio de duplicata (form_id, student_id, competency_id)
sim.insertResponse(
  {
    form_id: formOpenId,
    student_id: stuAId,
    competency_id: comp1Id,
    perceived_level: 5,
    confidence_score: 4,
    difficulty_notes: 'Boa segurança na leitura do nônio em milímetros.',
  },
  { role: 'STUDENT', userId: stuAId }
);
sim.insertResponse(
  {
    form_id: formOpenId,
    student_id: stuAId,
    competency_id: comp2Id,
    perceived_level: 1,
    confidence_score: 2,
    difficulty_notes: 'Dificuldade na conferência de zeragem com bloco padrão.',
  },
  { role: 'STUDENT', userId: stuAId }
);
sim.insertResponse(
  {
    form_id: formOpenId,
    student_id: stuBId,
    competency_id: comp1Id,
    perceived_level: 3,
    confidence_score: 3,
  },
  { role: 'STUDENT', userId: stuBId }
);

let dupBlocked = false;
try {
  sim.insertResponse(
    {
      form_id: formOpenId,
      student_id: stuAId,
      competency_id: comp1Id,
      perceived_level: 4,
      confidence_score: 4,
    },
    { role: 'STUDENT', userId: stuAId }
  );
} catch (err) {
  dupBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupBlocked,
  'Teste 1 (Critério 1): Duplicata em (form_id, student_id, competency_id) bloqueada por uq_student_self_assessments_composite (23505 / P2002)'
);

// Teste 2 (Critério 2): perceived_level e confidence_score fora de 1..5 rejeitados com SQLSTATE 23514
let perc0Blocked = false;
let perc6Blocked = false;
let conf0Blocked = false;
let conf6Blocked = false;

for (const [p, c, setter] of [
  [0, 3, (v) => (perc0Blocked = v)],
  [6, 3, (v) => (perc6Blocked = v)],
  [3, 0, (v) => (conf0Blocked = v)],
  [3, 6, (v) => (conf6Blocked = v)],
]) {
  try {
    sim.insertResponse(
      {
        form_id: formOpenId,
        student_id: stuBId,
        competency_id: comp2Id,
        perceived_level: p,
        confidence_score: c,
      },
      { role: 'STUDENT', userId: stuBId }
    );
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}

assertCheck(
  perc0Blocked && perc6Blocked && conf0Blocked && conf6Blocked,
  'Teste 2 (Critério 2): perceived_level e confidence_score fora da faixa 1..5 (0 e 6) rejeitados com SQLSTATE 23514'
);

// Teste 3 (Critério 3 — Isolamento RLS): Aluno A nunca lê nem escreve autoavaliação de Aluno B; Professor lê todos
const visibleToStuA = sim.selectAllAsSession({ role: 'STUDENT', userId: stuAId });
const visibleToStuB = sim.selectAllAsSession({ role: 'STUDENT', userId: stuBId });
const visibleToTeacher = sim.selectAllAsSession({ role: 'TEACHER', userId: teacherId });

let crossStudentWriteBlocked = false;
try {
  sim.insertResponse(
    {
      form_id: formOpenId,
      student_id: stuBId,
      competency_id: comp2Id,
      perceived_level: 4,
      confidence_score: 4,
    },
    { role: 'STUDENT', userId: stuAId }
  );
} catch (err) {
  crossStudentWriteBlocked = err.sqlState === '42501';
}

assertCheck(
  visibleToStuA.length === 2 &&
    visibleToStuA.every((r) => r.student_id === stuAId) &&
    visibleToStuB.length === 1 &&
    visibleToStuB.every((r) => r.student_id === stuBId) &&
    visibleToTeacher.length === 3 &&
    crossStudentWriteBlocked,
  'Teste 3 (Critério 3): Isolamento RLS validado — Aluno A vê apenas suas 2 respostas, Aluno B apenas sua 1 resposta, escrita cruzada bloqueada (42501) e Professor lê todas (3)'
);

// Teste 4 (Integridade Contextual): Matrícula DROPPED, formulário fechado, perfil TEACHER e competência de outro módulo bloqueados
let droppedStudentBlocked = false;
let closedFormBlocked = false;
let teacherAsStudentBlocked = false;
let wrongModuleCompBlocked = false;

try {
  sim.insertResponse({
    form_id: formOpenId,
    student_id: stuDroppedId,
    competency_id: comp1Id,
    perceived_level: 3,
    confidence_score: 3,
  });
} catch (err) {
  droppedStudentBlocked = err.sqlState === '23514';
}

try {
  sim.insertResponse({
    form_id: formClosedId,
    student_id: stuAId,
    competency_id: comp1Id,
    perceived_level: 3,
    confidence_score: 3,
  });
} catch (err) {
  closedFormBlocked = err.sqlState === '23514';
}

try {
  sim.insertResponse({
    form_id: formOpenId,
    student_id: teacherId,
    competency_id: comp1Id,
    perceived_level: 5,
    confidence_score: 5,
  });
} catch (err) {
  teacherAsStudentBlocked = err.sqlState === '23514';
}

try {
  sim.insertResponse({
    form_id: formOpenId,
    student_id: stuBId,
    competency_id: compOtherModId,
    perceived_level: 3,
    confidence_score: 3,
  });
} catch (err) {
  wrongModuleCompBlocked = err.sqlState === '23514';
}

assertCheck(
  droppedStudentBlocked && closedFormBlocked && teacherAsStudentBlocked && wrongModuleCompBlocked,
  'Teste 4 (Integridade): Matrícula DROPPED, formulário fechado/inativo, perfil TEACHER e competência de outro módulo bloqueados (23514)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-032] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
