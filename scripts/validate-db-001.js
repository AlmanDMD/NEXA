/**
 * Script de Validação Automatizada — Card [DB-001]
 * Título: Mapear Modelo Conceitual e Entidades do Domínio Acadêmico SENAI
 *
 * Verifica programaticamente todos os Critérios de Aceitação, Regras de Negócio
 * e integração com os cards dependentes (DB-002, DB-010 e DB-050).
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '01-modelo-conceitual.md'),
  path.join(ROOT_DIR, 'BancoNexa', '01-modelo-conceitual.md'),
];

const EXPECTED_ENTITIES = [
  // Domínio 1: Identidade, Segurança (RBAC), Sessões e Auditoria
  'users',
  'user_profiles',
  'auth_sessions',
  'audit_logs',
  // Domínio 2: Estrutura Curricular e Gestão Acadêmica SENAI
  'courses',
  'classes',
  'subjects',
  'learning_modules',
  'competencies',
  'module_competencies',
  'enrollments',
  'teacher_assignments',
  // Domínio 3: Diário de Classe, Frequência e Avaliações Formativas
  'class_lessons',
  'attendance_records',
  'academic_assessments',
  'student_grades',
  // Domínio 4: Oficina Prática, Rubricas e Entregas
  'practical_tasks',
  'task_criteria',
  'task_submissions',
  'submission_evaluations',
  // Domínio 5: Autoavaliação, Evidências, Alertas e Diagnóstico 360°
  'self_assessment_forms',
  'student_self_assessments',
  'skill_evidences',
  'academic_alerts',
  'explainable_diagnostics',
  'student_milestone_history',
  // Domínio 6: Comunicação, Apoio Confidencial, Notas Pedagógicas e Gamificação
  'class_announcements',
  'help_requests',
  'pedagogical_notes',
  'chat_messages',
  'gamification_badges',
  'student_achievements',
];

const EXPECTED_VIEWS = [
  'vw_student_360_performance',
  'vw_module_attendance_risk',
  'vw_self_eval_discrepancy',
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
console.log('🧪 VALIDAÇÃO DO CARD [DB-001] — MODELO CONCEITUAL SENAI (PROJETO NEXA)');
console.log('======================================================================\n');

// 1. Verificar existência dos artefatos de documentação
console.log('1. Verificando arquivos de documentação do Modelo Conceitual...');
for (const docPath of DOC_PATHS) {
  const relPath = path.relative(ROOT_DIR, docPath);
  assertCheck(fs.existsSync(docPath), `Arquivo presente: ${relPath}`);
}

const content = fs.readFileSync(DOC_PATHS[0], 'utf8');
const bancoNexaContent = fs.readFileSync(DOC_PATHS[1], 'utf8');
assertCheck(
  content === bancoNexaContent,
  'Sincronia 100% idêntica entre docs/banco/01-modelo-conceitual.md e BancoNexa/01-modelo-conceitual.md'
);

// 2. Critério de Aceitação 1: Diagrama conceitual cobrindo no mínimo 15 entidades primárias
console.log('\n2. Verificando Critério de Aceitação 1 (Diagrama Conceitual e >= 15 Entidades)...');
assertCheck(content.includes('```mermaid') && content.includes('erDiagram'), 'Diagrama Mermaid erDiagram presente no documento');

const mappedEntities = EXPECTED_ENTITIES.filter(
  (entity) => content.includes(`\`${entity}\``) && content.includes(entity.toUpperCase())
);
assertCheck(
  mappedEntities.length >= 15 && mappedEntities.length === EXPECTED_ENTITIES.length,
  `Entidades conceituais mapeadas no catálogo e no diagrama ER: ${mappedEntities.length}/${EXPECTED_ENTITIES.length} (mínimo exigido: 15)`
);

const mappedViews = EXPECTED_VIEWS.filter((view) => content.includes(view));
assertCheck(
  mappedViews.length === EXPECTED_VIEWS.length,
  `Views analíticas derivadas documentadas: ${mappedViews.length}/${EXPECTED_VIEWS.length} (${EXPECTED_VIEWS.join(', ')})`
);

// 3. Critério de Aceitação 2: Cardinalidades definidas (1:N, N:M) entre Aluno, Turma, Módulo e Avaliações
console.log('\n3. Verificando Critério de Aceitação 2 (Cardinalidades 1:1, 1:N e N:M)...');
const requiredRelationships = [
  { name: 'Usuário 1:1 Perfil (users ||--|| user_profiles)', pattern: 'USERS ||--|| USER_PROFILES' },
  { name: 'Aluno N:M Turma via Matrícula (enrollments)', pattern: 'CLASSES ||--o{ ENROLLMENTS' },
  { name: 'Disciplina 1:N Módulo Prático (learning_modules)', pattern: 'SUBJECTS ||--o{ LEARNING_MODULES' },
  { name: 'Módulo N:M Competência via module_competencies', pattern: 'LEARNING_MODULES ||--o{ MODULE_COMPETENCIES' },
  { name: 'Módulo 1:N Tarefa Prática (practical_tasks)', pattern: 'LEARNING_MODULES ||--o{ PRACTICAL_TASKS' },
  { name: 'Avaliação Formativa 1:N Notas do Estudante (student_grades)', pattern: 'ACADEMIC_ASSESSMENTS ||--o{ STUDENT_GRADES' },
  { name: 'Autoavaliação 1:N Respostas do Estudante (student_self_assessments)', pattern: 'SELF_ASSESSMENT_FORMS ||--o{ STUDENT_SELF_ASSESSMENTS' },
];

for (const rel of requiredRelationships) {
  assertCheck(content.includes(rel.pattern), `Cardinalidade formalizada: ${rel.name}`);
}

// 4. Critério de Aceitação 3: Regra de isolamento de notas pedagógicas confidenciais
console.log('\n4. Verificando Critério de Aceitação 3 (Isolamento de Notas Pedagógicas Confidenciais)...');
assertCheck(
  content.includes('pedagogical_notes') && content.includes('visibility_scope'),
  'Entidade pedagogical_notes com controle granular de visibility_scope documentada'
);
assertCheck(
  content.includes('PRIVATE_AUTHOR') &&
    content.includes('TEACHERS_AND_COORD') &&
    content.includes('COORDINATION_ONLY'),
  'Três níveis de escopo de visibilidade restrita definidos (PRIVATE_AUTHOR, TEACHERS_AND_COORD, COORDINATION_ONLY)'
);
assertCheck(
  content.includes('AES-256') && content.includes('audit_logs'),
  'Criptografia AES-256 em repouso e rastreabilidade obrigatória em audit_logs especificadas'
);

// 5. Observação Técnica: Especialização sem redundância (ADMIN, COORDINATOR, TEACHER, STUDENT)
console.log('\n5. Verificando Observação Técnica (Especialização de Perfis sem Redundância)...');
assertCheck(
  content.includes('ADMIN') &&
    content.includes('COORDINATOR') &&
    content.includes('TEACHER') &&
    content.includes('STUDENT') &&
    content.includes('teacher_assignments') &&
    content.includes('enrollments'),
  'Especialização sem redundância via users (RBAC) + user_profiles (1:1 LGPD) + enrollments/teacher_assignments'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-001] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
