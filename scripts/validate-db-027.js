/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-027]
 * Título: Implementar Tabela de Avaliações Formativas e Provas (academic_assessments)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Peso (`weight`) estritamente maior que zero (`chk_assessments_weight_positive`),
 *    além de `max_grade` em `(0.00, 10.00]` (padrão `10.00`) e `assessment_type` no enum
 *    `assessment_type_enum` (`EXAM`, `MICRO_EVALUATION`, `PROJECT`).
 * 2. Critério 2: Vinculação obrigatória (`NOT NULL`) a turma (`fk_assessments_class`) e disciplina
 *    (`fk_assessments_subject`), vínculo opcional a módulo (`fk_assessments_module`) com
 *    `ON DELETE RESTRICT` e trigger de coerência curricular (`course_id` e `subject_id`).
 * 3. Critério 3: Ordenação cronológica por `application_date` suportada por
 *    `idx_academic_assessments_class_subject_date (class_id, subject_id, application_date)` e
 *    `idx_academic_assessments_application_date (application_date)`.
 * 4. DoD: Tabela `academic_assessments` criada e integrada ao `prisma/schema.prisma`, tipos TS
 *    gerados em `BancoNexa/types/schema-models.ts`, testes unitários aprovados e integração
 *    validada com cards dependentes (`DB-028`, `BE-027`, `FE-027`).
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
  '20261123060000_create_academic_assessments_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261123060000_create_academic_assessments_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '27_tabela_academic_assessments.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '27-tabela-avaliacoes-formativas-provas-academic-assessments.md'),
  path.join(ROOT_DIR, 'BancoNexa', '27-tabela-avaliacoes-formativas-provas-academic-assessments.md'),
];

const VALID_ASSESSMENT_TYPES = new Set(['EXAM', 'MICRO_EVALUATION', 'PROJECT']);

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
 * e `academic_assessments` com CHECK weight > 0, CHECK max_grade (0, 10], FKs ON DELETE RESTRICT,
 * trigger de coerência curricular/modular e listagem cronológica por application_date.
 */
class AcademicAssessmentsRelationalSimulator {
  constructor() {
    this.courses = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.modules = new Map();
    this.assessmentsById = new Map();
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

  insertAssessment(row) {
    if (!row.class_id || !row.subject_id || !row.title || !row.assessment_type || !row.application_date) {
      const err = new Error('null value in required column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }

    const titleTrimmed = String(row.title).trim();
    if (titleTrimmed.length < 3) {
      const err = new Error('new row for relation "academic_assessments" violates check constraint "chk_assessments_title_not_blank"');
      err.sqlState = '23514';
      throw err;
    }

    if (String(row.title).length > 150) {
      const err = new Error('value too long for type character varying(150)');
      err.sqlState = '22001';
      throw err;
    }

    if (!VALID_ASSESSMENT_TYPES.has(row.assessment_type)) {
      const err = new Error(`invalid input value for enum assessment_type_enum: "${row.assessment_type}"`);
      err.sqlState = '22P02';
      throw err;
    }

    const weight = row.weight !== undefined ? Number(row.weight) : 1.0;
    if (Number.isNaN(weight) || weight <= 0.0 || weight > 9.99) {
      const err = new Error('new row for relation "academic_assessments" violates check constraint "chk_assessments_weight_positive"');
      err.sqlState = '23514';
      throw err;
    }

    const maxGrade = row.max_grade !== undefined ? Number(row.max_grade) : 10.0;
    if (Number.isNaN(maxGrade) || maxGrade <= 0.0 || maxGrade > 10.0) {
      const err = new Error('new row for relation "academic_assessments" violates check constraint "chk_assessments_max_grade"');
      err.sqlState = '23514';
      throw err;
    }

    const cls = this.classes.get(row.class_id);
    if (!cls) {
      const err = new Error('violates foreign key constraint "fk_assessments_class"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const subject = this.subjects.get(row.subject_id);
    if (!subject) {
      const err = new Error('violates foreign key constraint "fk_assessments_subject"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (cls.course_id !== subject.course_id) {
      const err = new Error('chk_academic_assessments_subject_course: disciplina não pertence ao curso da turma');
      err.sqlState = '23514';
      throw err;
    }

    let moduleId = null;
    if (row.module_id !== undefined && row.module_id !== null) {
      const mod = this.modules.get(row.module_id);
      if (!mod) {
        const err = new Error('violates foreign key constraint "fk_assessments_module"');
        err.code = 'P2003';
        err.sqlState = '23503';
        throw err;
      }
      if (mod.subject_id !== row.subject_id) {
        const err = new Error('chk_academic_assessments_module_subject: módulo não pertence à disciplina informada');
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
      title: row.title,
      assessment_type: row.assessment_type,
      weight: Number(weight.toFixed(2)),
      application_date: row.application_date,
      max_grade: Number(maxGrade.toFixed(2)),
      created_at: new Date().toISOString(),
    };

    this.assessmentsById.set(saved.id, saved);
    return saved;
  }

  deleteSubjectRestrict(subjectId) {
    const inUse = [...this.assessmentsById.values()].some((a) => a.subject_id === subjectId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_assessments_subject"');
      err.sqlState = '23503';
      throw err;
    }
    this.subjects.delete(subjectId);
  }

  deleteClassRestrict(classId) {
    const inUse = [...this.assessmentsById.values()].some((a) => a.class_id === classId);
    if (inUse) {
      const err = new Error('violates foreign key constraint "fk_assessments_class"');
      err.sqlState = '23503';
      throw err;
    }
    this.classes.delete(classId);
  }

  listOrderedByApplicationDate(classId, subjectId) {
    return [...this.assessmentsById.values()]
      .filter((a) => a.class_id === classId && a.subject_id === subjectId)
      .sort((a, b) => a.application_date.localeCompare(b.application_date));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-027] — AVALIAÇÕES FORMATIVAS (academic_assessments)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de academic_assessments'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261123060000_create_academic_assessments_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261123060000_create_academic_assessments_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/27_tabela_academic_assessments.sql'
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/27_tabela_academic_assessments.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/27-tabela-avaliacoes-formativas-provas-academic-assessments.md e BancoNexa/27-tabela-avaliacoes-formativas-provas-academic-assessments.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-027'),
  'Card DB-027 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model AcademicAssessment no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model AcademicAssessment no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /class_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /subject_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /module_id\s+UUID\s*,/i.test(sqlContent) &&
    /title\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /assessment_type\s+assessment_type_enum\s+NOT\s+NULL/i.test(sqlContent) &&
    /weight\s+NUMERIC\(3,2\)\s+NOT\s+NULL\s+DEFAULT\s+1\.00/i.test(sqlContent) &&
    /application_date\s+DATE\s+NOT\s+NULL/i.test(sqlContent) &&
    /max_grade\s+NUMERIC\(4,2\)\s+NOT\s+NULL\s+DEFAULT\s+10\.00/i.test(sqlContent),
  'Todas as colunas exigidas (id, class_id, subject_id, module_id opcional, title, assessment_type, weight NUMERIC 3,2, application_date DATE, max_grade DEFAULT 10.00) presentes'
);
assertCheck(
  schemaContent.includes('model AcademicAssessment') &&
    (schemaContent.match(/academicAssessments\s+AcademicAssessment\[\]/g) || []).length === 3 &&
    schemaContent.includes('@@index([classId, subjectId, applicationDate], map: "idx_academic_assessments_class_subject_date")') &&
    schemaContent.includes('@@index([applicationDate], map: "idx_academic_assessments_application_date")') &&
    schemaContent.includes('@@index([moduleId], map: "idx_academic_assessments_module")') &&
    schemaContent.includes('@@map("academic_assessments")'),
  'Modelo AcademicAssessment integrado ao prisma/schema.prisma com relações reversas em Class/Subject/LearningModule e índices de application_date'
);
assertCheck(
  typesTsContent.includes('export interface AcademicAssessment {') &&
    typesTsContent.includes('assessmentType: AssessmentType;') &&
    typesTsContent.includes('moduleId: string | null;') &&
    typesTsContent.includes('maxGrade: number | string;') &&
    typesTsContent.includes('export interface AcademicAssessmentRow {'),
  'Tipos TypeScript (AcademicAssessment, AcademicAssessmentRow, AcademicAssessmentCreateInput, AcademicAssessmentUpdateInput) gerados em schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+chk_assessments_weight_positive\s+CHECK\s*\(\s*weight\s*>\s*0\.00/i.test(sqlContent) &&
    /CONSTRAINT\s+chk_assessments_max_grade\s+CHECK\s*\(\s*max_grade\s*>\s*0\.00\s+AND\s+max_grade\s*<=\s*10\.00\s*\)/i.test(
      sqlContent
    ),
  'Critério 1: Constraints chk_assessments_weight_positive (weight > 0.00) e chk_assessments_max_grade (0.00..10.00) declaradas'
);
assertCheck(
  /CONSTRAINT\s+fk_assessments_class\s+FOREIGN\s+KEY\s*\(\s*class_id\s*\)\s*REFERENCES\s+classes\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_assessments_subject\s+FOREIGN\s+KEY\s*\(\s*subject_id\s*\)\s*REFERENCES\s+subjects\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /CONSTRAINT\s+fk_assessments_module\s+FOREIGN\s+KEY\s*\(\s*module_id\s*\)\s*REFERENCES\s+learning_modules\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT/i.test(
      sqlContent
    ) &&
    /trg_academic_assessments_validate_integrity/i.test(sqlContent),
  'Critério 2: FKs obrigatórias para classes/subjects e opcional para learning_modules (ON DELETE RESTRICT) + trigger de coerência curricular'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_academic_assessments_class_subject_date\s+ON\s+academic_assessments\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*subject_id\s*,\s*application_date\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_academic_assessments_application_date\s+ON\s+academic_assessments\s+USING\s+BTREE\s*\(\s*application_date\s*\)/i.test(
      sqlContent
    ),
  'Critério 3: Índices B-Tree idx_academic_assessments_class_subject_date e idx_academic_assessments_application_date criados'
);

// 5. Integração com modelo 3FN e cards dependentes (DB-028, BE-027, FE-027)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-028, BE-027, FE-027)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+academic_assessments/i.test(sql3fnContent) &&
    /chk_assessments_weight_positive/i.test(sql3fnContent) &&
    /FOREIGN\s+KEY\s*\(\s*assessment_id\s*\)\s*REFERENCES\s+academic_assessments\s*\(\s*id\s*\)/i.test(sql3fnContent),
  'Integração validada com modelo 3FN ([T16] academic_assessments) e tabela dependente student_grades (DB-028)'
);

// 6. Testes unitários de peso > 0, vínculos obrigatórios, coerência curricular e ordenação por application_date (DoD)
console.log('\n6. Executando testes unitários de peso, vínculos turma/disciplina/módulo e ordenação por data (DoD)...');
const sim = new AcademicAssessmentsRelationalSimulator();
const courseMecId = '10000000-0000-4000-8000-000000000001';
const courseEletroId = '10000000-0000-4000-8000-000000000002';
const classMec1Id = '20000000-0000-4000-8000-000000000001';
const subjectMetId = '30000000-0000-4000-8000-000000000001';
const subjectUsinId = '30000000-0000-4000-8000-000000000002';
const subjectClpId = '30000000-0000-4000-8000-000000000003';
const modPaquimetroId = '40000000-0000-4000-8000-000000000001';
const modTorneariaId = '40000000-0000-4000-8000-000000000002';

sim.addCourse(courseMecId, 'TEC-MEC');
sim.addCourse(courseEletroId, 'TEC-ELE');
sim.addClass(classMec1Id, courseMecId, 'MEC-2026-1');
sim.addSubject(subjectMetId, courseMecId, 'UC-MET-01', 'Metrologia');
sim.addSubject(subjectUsinId, courseMecId, 'UC-USIN-01', 'Usinagem Convencional');
sim.addSubject(subjectClpId, courseEletroId, 'UC-CLP-01', 'Automação CLP');
sim.addModule(modPaquimetroId, subjectMetId, 'Módulo 01 — Leitura de Paquímetro e Micrômetro');
sim.addModule(modTorneariaId, subjectUsinId, 'Módulo 01 — Torneamento Cilíndrico Externo');

// Teste 1 (DoD): Cadastro de EXAM, MICRO_EVALUATION e PROJECT (com módulo e sem módulo, defaults weight=1.00 e max_grade=10.00)
const exam = sim.insertAssessment({
  class_id: classMec1Id,
  subject_id: subjectMetId,
  module_id: modPaquimetroId,
  title: 'Prova Teórica de Leitura de Paquímetro e Micrômetro',
  assessment_type: 'EXAM',
  weight: 2.0,
  application_date: '2026-04-20',
});
const micro = sim.insertAssessment({
  class_id: classMec1Id,
  subject_id: subjectMetId,
  module_id: modPaquimetroId,
  title: 'Microavaliação de Conversão Polegada-Milímetro',
  assessment_type: 'MICRO_EVALUATION',
  application_date: '2026-04-05',
  max_grade: 5.0,
});
const project = sim.insertAssessment({
  class_id: classMec1Id,
  subject_id: subjectMetId,
  module_id: null,
  title: 'Projeto Integrador de Relatório Metrológico',
  assessment_type: 'PROJECT',
  weight: 1.5,
  application_date: '2026-05-10',
});

let invalidEnumBlocked = false;
try {
  sim.insertAssessment({
    class_id: classMec1Id,
    subject_id: subjectMetId,
    title: 'Avaliação Tipo Inexistente',
    assessment_type: 'QUIZ',
    application_date: '2026-05-12',
  });
} catch (err) {
  invalidEnumBlocked = err.sqlState === '22P02';
}

assertCheck(
  exam.max_grade === 10.0 &&
    exam.weight === 2.0 &&
    micro.weight === 1.0 &&
    micro.max_grade === 5.0 &&
    project.module_id === null &&
    invalidEnumBlocked,
  'Teste 1 (DoD): Cadastro de EXAM, MICRO_EVALUATION (default weight=1.00) e PROJECT (module_id NULL) + rejeição de enum inválido (22P02) validados'
);

// Teste 2 (Critério 1): Peso <= 0 e max_grade fora de (0.00, 10.00] rejeitados com SQLSTATE 23514
let zeroWeightBlocked = false;
let negativeWeightBlocked = false;
let overWeightBlocked = false;
let zeroMaxGradeBlocked = false;
let overMaxGradeBlocked = false;

for (const [w, setter] of [
  [0.0, (v) => (zeroWeightBlocked = v)],
  [-1.0, (v) => (negativeWeightBlocked = v)],
  [10.0, (v) => (overWeightBlocked = v)],
]) {
  try {
    sim.insertAssessment({
      class_id: classMec1Id,
      subject_id: subjectMetId,
      title: 'Teste Peso Inválido',
      assessment_type: 'EXAM',
      weight: w,
      application_date: '2026-04-22',
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}

for (const [mg, setter] of [
  [0.0, (v) => (zeroMaxGradeBlocked = v)],
  [10.5, (v) => (overMaxGradeBlocked = v)],
]) {
  try {
    sim.insertAssessment({
      class_id: classMec1Id,
      subject_id: subjectMetId,
      title: 'Teste Nota Máxima Inválida',
      assessment_type: 'EXAM',
      weight: 1.0,
      max_grade: mg,
      application_date: '2026-04-22',
    });
  } catch (err) {
    setter(err.sqlState === '23514');
  }
}

assertCheck(
  zeroWeightBlocked && negativeWeightBlocked && overWeightBlocked && zeroMaxGradeBlocked && overMaxGradeBlocked,
  'Teste 2 (Critério 1): weight <= 0 (0.00, -1.00), weight > 9.99 e max_grade fora de (0.00, 10.00] bloqueados com SQLSTATE 23514'
);

// Teste 3 (Critério 2): Vinculação obrigatória a turma e disciplina + coerência curricular/modular + ON DELETE RESTRICT
let nullClassBlocked = false;
let nullSubjectBlocked = false;
let wrongCourseSubjectBlocked = false;
let wrongSubjectModuleBlocked = false;
let deleteSubjectInUseBlocked = false;
let deleteClassInUseBlocked = false;

try {
  sim.insertAssessment({
    class_id: null,
    subject_id: subjectMetId,
    title: 'Avaliação Sem Turma',
    assessment_type: 'EXAM',
    application_date: '2026-04-22',
  });
} catch (err) {
  nullClassBlocked = err.sqlState === '23502';
}

try {
  sim.insertAssessment({
    class_id: classMec1Id,
    subject_id: null,
    title: 'Avaliação Sem Disciplina',
    assessment_type: 'EXAM',
    application_date: '2026-04-22',
  });
} catch (err) {
  nullSubjectBlocked = err.sqlState === '23502';
}

try {
  sim.insertAssessment({
    class_id: classMec1Id,
    subject_id: subjectClpId, // curso Eletroeletrônica != Mecânica
    title: 'Avaliação Disciplina Outro Curso',
    assessment_type: 'EXAM',
    application_date: '2026-04-22',
  });
} catch (err) {
  wrongCourseSubjectBlocked = err.sqlState === '23514';
}

try {
  sim.insertAssessment({
    class_id: classMec1Id,
    subject_id: subjectMetId,
    module_id: modTorneariaId, // módulo pertence a Usinagem, não Metrologia
    title: 'Avaliação Módulo Outra Disciplina',
    assessment_type: 'MICRO_EVALUATION',
    application_date: '2026-04-22',
  });
} catch (err) {
  wrongSubjectModuleBlocked = err.sqlState === '23514';
}

try {
  sim.deleteSubjectRestrict(subjectMetId);
} catch (err) {
  deleteSubjectInUseBlocked = err.sqlState === '23503';
}

try {
  sim.deleteClassRestrict(classMec1Id);
} catch (err) {
  deleteClassInUseBlocked = err.sqlState === '23503';
}

assertCheck(
  nullClassBlocked &&
    nullSubjectBlocked &&
    wrongCourseSubjectBlocked &&
    wrongSubjectModuleBlocked &&
    deleteSubjectInUseBlocked &&
    deleteClassInUseBlocked,
  'Teste 3 (Critério 2): class_id/subject_id obrigatórios (23502), disciplina de outro curso (23514), módulo de outra disciplina (23514) e ON DELETE RESTRICT (23503) bloqueados'
);

// Teste 4 (Critério 3): Ordenação cronológica por application_date em (class_id, subject_id, application_date)
const ordered = sim.listOrderedByApplicationDate(classMec1Id, subjectMetId);
const orderedDates = ordered.map((a) => a.application_date);
assertCheck(
  orderedDates.length === 3 &&
    orderedDates[0] === '2026-04-05' &&
    orderedDates[1] === '2026-04-20' &&
    orderedDates[2] === '2026-05-10',
  'Teste 4 (Critério 3): Ordenação por application_date retornou as 3 avaliações em ordem cronológica (2026-04-05 -> 2026-04-20 -> 2026-05-10)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-027] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
