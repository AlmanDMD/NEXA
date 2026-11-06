/**
 * Script de Validação Automatizada — Card [DB-002]
 * Título: Elaborar Modelo Lógico Relacional Normalizado (3FN)
 *
 * Verifica programaticamente:
 * 1. Existência e sincronia da documentação do Modelo Lógico 3FN.
 * 2. Existência e validade estrutural do script SQL DDL PostgreSQL 16 (BancoNexa/sql/02_modelo_logico_3fn.sql).
 * 3. Critério 1: Todas as 33 tabelas e 18 enums em 3FN com tipos nativos e constraints.
 * 4. Critério 2: Ausência de duplicação de notas/faltas entre módulos e integridade ON DELETE RESTRICT.
 * 5. Critério 3: Chaves primárias compostas (module_competencies, student_subjects) e UNIQUE compostas.
 * 6. Observação Técnica: Uso de UUID v4 (gen_random_uuid()) como chave primária.
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '02-modelo-logico-3fn.md'),
  path.join(ROOT_DIR, 'BancoNexa', '02-modelo-logico-3fn.md'),
];
const SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');

const EXPECTED_TABLES = [
  'users',
  'user_profiles',
  'auth_sessions',
  'audit_logs',
  'courses',
  'classes',
  'subjects',
  'learning_modules',
  'competencies',
  'module_competencies',
  'enrollments',
  'student_subjects',
  'teacher_assignments',
  'class_lessons',
  'attendance_records',
  'academic_assessments',
  'student_grades',
  'practical_tasks',
  'task_criteria',
  'task_submissions',
  'submission_evaluations',
  'self_assessment_forms',
  'student_self_assessments',
  'skill_evidences',
  'academic_alerts',
  'explainable_diagnostics',
  'student_milestone_history',
  'class_announcements',
  'help_requests',
  'pedagogical_notes',
  'chat_messages',
  'gamification_badges',
  'student_achievements',
];

const EXPECTED_ENUMS = [
  'user_role_enum',
  'shift_enum',
  'class_status_enum',
  'enrollment_status_enum',
  'competency_category_enum',
  'attendance_status_enum',
  'submission_status_enum',
  'assessment_type_enum',
  'risk_level_enum',
  'alert_category_enum',
  'alert_status_enum',
  'diagnostic_type_enum',
  'milestone_type_enum',
  'announcement_priority_enum',
  'help_request_category_enum',
  'help_request_status_enum',
  'note_visibility_scope_enum',
  'note_category_enum',
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

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-002] — MODELO LÓGICO RELACIONAL 3FN (SQL)');
console.log('======================================================================\n');

// 1. Verificar existência dos artefatos
console.log('1. Verificando arquivos de documentação e script SQL DDL...');
for (const docPath of DOC_PATHS) {
  const relPath = path.relative(ROOT_DIR, docPath);
  assertCheck(fs.existsSync(docPath), `Documento presente: ${relPath}`);
}
assertCheck(fs.existsSync(SQL_PATH), `Script SQL DDL presente: ${path.relative(ROOT_DIR, SQL_PATH)}`);

const docContent = fs.readFileSync(DOC_PATHS[0], 'utf8');
const mirrorContent = fs.readFileSync(DOC_PATHS[1], 'utf8');
const sqlContent = fs.readFileSync(SQL_PATH, 'utf8');

assertCheck(
  docContent === mirrorContent,
  'Sincronia 100% idêntica entre docs/banco/02-modelo-logico-3fn.md e BancoNexa/02-modelo-logico-3fn.md'
);

// 2. Critério 1: Todas as tabelas e enums em 3FN documentadas e no SQL com tipos e constraints
console.log('\n2. Verificando Critério de Aceitação 1 (Tabelas em 3FN, Enums SQL e Constraints)...');
const createdTables = EXPECTED_TABLES.filter((table) =>
  new RegExp(`CREATE\\s+TABLE\\s+${table}\\s*\\(`, 'i').test(sqlContent)
);
assertCheck(
  createdTables.length === EXPECTED_TABLES.length,
  `Tabelas DDL declaradas em 02_modelo_logico_3fn.sql: ${createdTables.length}/${EXPECTED_TABLES.length}`
);

const documentedTables = EXPECTED_TABLES.filter((table) => docContent.includes(table));
assertCheck(
  documentedTables.length === EXPECTED_TABLES.length,
  `Tabelas documentadas em 02-modelo-logico-3fn.md: ${documentedTables.length}/${EXPECTED_TABLES.length}`
);

const createdEnums = EXPECTED_ENUMS.filter((enumName) =>
  new RegExp(`CREATE\\s+TYPE\\s+${enumName}\\s+AS\\s+ENUM`, 'i').test(sqlContent)
);
assertCheck(
  createdEnums.length === EXPECTED_ENUMS.length,
  `Tipos ENUM nativos declarados no PostgreSQL: ${createdEnums.length}/${EXPECTED_ENUMS.length}`
);

const checkConstraintCount = (sqlContent.match(/CONSTRAINT\s+chk_[a-z0-9_]+\s+CHECK/gi) || []).length;
assertCheck(
  checkConstraintCount >= 20,
  `Constraints CHECK de validação de domínio declaradas no SQL: ${checkConstraintCount} (mínimo esperado: 20)`
);

// 3. Critério 2: 3FN (Nenhuma nota ou falta duplicada entre módulos) e ON DELETE RESTRICT
console.log('\n3. Verificando Critério de Aceitação 2 (3FN e ON DELETE RESTRICT no histórico acadêmico)...');
const restrictCount = (sqlContent.match(/ON\s+DELETE\s+RESTRICT/gi) || []).length;
assertCheck(
  restrictCount >= 35,
  `Integridade referencial ON DELETE RESTRICT aplicada nas FKs de histórico acadêmico: ${restrictCount} ocorrências`
);
assertCheck(
  docContent.includes('1FN') && docContent.includes('2FN') && docContent.includes('3FN'),
  'Comprovação formal de normalização (1FN, 2FN e 3FN) documentada'
);

// 4. Critério 3: Chaves compostas modeladas para tabelas associativas (ex: aluno-disciplina)
console.log('\n4. Verificando Critério de Aceitação 3 (Chaves Compostas em Tabelas Associativas)...');
const compositeChecks = [
  {
    name: 'PRIMARY KEY composta (module_id, competency_id) em module_competencies',
    regex: /CONSTRAINT\s+pk_module_competencies\s+PRIMARY\s+KEY\s*\(\s*module_id\s*,\s*competency_id\s*\)/i,
  },
  {
    name: 'PRIMARY KEY composta (enrollment_id, subject_id) em student_subjects (aluno-disciplina)',
    regex: /CONSTRAINT\s+pk_student_subjects\s+PRIMARY\s+KEY\s*\(\s*enrollment_id\s*,\s*subject_id\s*\)/i,
  },
  {
    name: 'UNIQUE composta (student_id, class_id) em enrollments (aluno-turma)',
    regex: /CONSTRAINT\s+uq_enrollments_student_class\s+UNIQUE\s*\(\s*student_id\s*,\s*class_id\s*\)/i,
  },
  {
    name: 'UNIQUE composta (teacher_id, class_id, subject_id) em teacher_assignments',
    regex: /CONSTRAINT\s+uq_teacher_assignments_composite\s+UNIQUE\s*\(\s*teacher_id\s*,\s*class_id\s*,\s*subject_id\s*\)/i,
  },
  {
    name: 'UNIQUE composta (lesson_id, enrollment_id) em attendance_records',
    regex: /CONSTRAINT\s+uq_attendance_lesson_enrollment\s+UNIQUE\s*\(\s*lesson_id\s*,\s*enrollment_id\s*\)/i,
  },
  {
    name: 'UNIQUE composta (assessment_id, enrollment_id) em student_grades',
    regex: /CONSTRAINT\s+uq_student_grades_assessment_enrollment\s+UNIQUE\s*\(\s*assessment_id\s*,\s*enrollment_id\s*\)/i,
  },
  {
    name: 'UNIQUE composta (submission_id, criterion_id) em submission_evaluations',
    regex: /CONSTRAINT\s+uq_submission_evaluations_composite\s+UNIQUE\s*\(\s*submission_id\s*,\s*criterion_id\s*\)/i,
  },
];

for (const item of compositeChecks) {
  assertCheck(item.regex.test(sqlContent), item.name);
}

// 5. Observação Técnica: Utilizar UUID v4 como PK
console.log('\n5. Verificando Observação Técnica (UUID v4 como PK nativo)...');
const uuidPkCount = (sqlContent.match(/id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/gi) || []).length;
assertCheck(
  uuidPkCount === 31,
  `Chaves primárias UUID v4 (gen_random_uuid()) configuradas nas 31 entidades com PK simples (+ 2 tabelas com PK composta = 33 tabelas)`
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-002] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
