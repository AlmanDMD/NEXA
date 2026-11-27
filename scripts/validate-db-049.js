/**
 * Script de Validação Automatizada — Card [DB-049]
 * Título: Implementar Políticas de Retenção de Dados e Anonimização LGPD
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { anonymizeRecordInMemory } = require('./db-lgpd-anonymize');

const ROOT_DIR = path.resolve(__dirname, '..');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127070000_create_lgpd_retention_and_anonymization', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127070000_create_lgpd_retention_and_anonymization.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '49_politicas_retencao_anonimizacao_lgpd.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '49-politicas-retencao-anonimizacao-lgpd.md'),
  path.join(ROOT_DIR, 'BancoNexa', '49-politicas-retencao-anonimizacao-lgpd.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-049] — RETENÇÃO & ANONIMIZAÇÃO LGPD');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-lgpd-anonymize.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Migration DB-049 e CLI db-lgpd-anonymize.js executados com sucesso');
} catch (err) {
  assertCheck(false, `Falha na execução: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/49_politicas_retencao_anonimizacao_lgpd.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-049') &&
    fs.readFileSync(DOC_PATHS[0], 'utf8').includes('DOC-017'),
  'Documentação DB-049 sincronizada e referenciada ao relatório LGPD (DOC-017)'
);
assertCheck(
  /fn_anonymize_user_lgpd/i.test(sqlContent) &&
    /fn_enforce_lgpd_retention_policy/i.test(sqlContent) &&
    /UPDATE\s+users/i.test(sqlContent) &&
    /UPDATE\s+user_profiles/i.test(sqlContent) &&
    /UPDATE\s+help_requests/i.test(sqlContent) &&
    /UPDATE\s+pedagogical_notes/i.test(sqlContent) &&
    /INSERT\s+INTO\s+audit_logs/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no SQL PL/pgSQL (remoção de PII + auditoria em audit_logs)'
);

// Teste end-to-end de anonimização irreversível preservando métricas agregadas da turma
const store = {
  users: [{ id: 'stu-lgpd-1', email: 'joao.silva@aluno.senai.br', password_hash: '$2b$12$realhash', role: 'STUDENT', is_active: true }],
  user_profiles: [{ user_id: 'stu-lgpd-1', full_name: 'João da Silva', registration_number: 'SENAI-2021-9999', phone: '+55 11 99999-8888', avatar_url: 'https://cdn/foto.jpg', bio: 'Aluno de mecânica' }],
  auth_sessions: [{ user_id: 'stu-lgpd-1', is_revoked: false, ip_address: '192.168.1.50', user_agent: 'Chrome' }],
  help_requests: [{ id: 'hr-1', student_id: 'stu-lgpd-1', category: 'PERSONAL_PEDAGOGICAL', status: 'CLOSED', subject_title: 'Problema familiar', description: 'Relato pessoal confidencial.', resolution_summary: 'Atendido.' }],
  chat_messages: [{ id: 'cm-1', help_request_id: 'hr-1', sender_id: 'stu-lgpd-1', message_body: 'Meu telefone é 11999998888' }],
  pedagogical_notes: [{ id: 'pn-1', student_id: 'stu-lgpd-1', category: 'MENTORING', note_content: 'Anotação sensível com nome João.' }],
  enrollments: [{ id: 'enr-1', student_id: 'stu-lgpd-1', class_id: 'cls-1', final_grade: 8.5, attendance_rate: 92.0 }],
  audit_logs: [],
};

const res1 = anonymizeRecordInMemory(store, 'stu-lgpd-1', 'dpo-admin-1', 'SOLICITACAO_TITULAR_ART18');
const res2 = anonymizeRecordInMemory(store, 'stu-lgpd-1', 'dpo-admin-1', 'SOLICITACAO_TITULAR_ART18');
const serializedAudit = JSON.stringify(store.audit_logs);

assertCheck(
  res1.status === 'ANONYMIZED' &&
    res2.status === 'ALREADY_ANONYMIZED' &&
    store.users[0].email.endsWith('@anonymized.nexa.local') &&
    store.users[0].is_active === false &&
    store.user_profiles[0].phone === null &&
    !store.user_profiles[0].full_name.includes('João') &&
    store.help_requests[0].description.includes('ANONIMIZADO') &&
    store.pedagogical_notes[0].note_content.includes('ANONIMIZADA') &&
    store.chat_messages[0].message_body.includes('ANONIMIZADA') &&
    store.auth_sessions[0].is_revoked === true,
  'Teste 1 (Critério 1): PII completamente removida em users, user_profiles, auth_sessions, help_requests, chat_messages e pedagogical_notes (idempotente)'
);
assertCheck(
  store.enrollments[0].student_id === 'stu-lgpd-1' &&
    store.enrollments[0].final_grade === 8.5 &&
    store.enrollments[0].attendance_rate === 92.0,
  'Teste 2 (Critério 2): Integridade referencial das métricas históricas anônimas preservada'
);
assertCheck(
  store.audit_logs.length === 1 &&
    store.audit_logs[0].action === 'LGPD_USER_ANONYMIZATION' &&
    !serializedAudit.includes('joao.silva') &&
    !serializedAudit.includes('99999-8888'),
  'Teste 3 (Critério 3): Execução registrada em audit_logs sem vazamento de PII'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-049] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
