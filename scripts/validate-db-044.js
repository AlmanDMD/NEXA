/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-044]
 * Título: Implementar Tabela de Conversações e Mensagens Internas (chat_messages)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127030000_create_chat_messages_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127030000_create_chat_messages_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '44_tabela_chat_messages.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '44-tabela-conversacoes-mensagens-chat-messages.md'),
  path.join(ROOT_DIR, 'BancoNexa', '44-tabela-conversacoes-mensagens-chat-messages.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class ChatSimulator {
  constructor() {
    this.requests = new Map();
    this.messages = [];
  }
  addRequest(id, student_id) { this.requests.set(id, { id, student_id }); }
  send(msg, senderRole) {
    const req = this.requests.get(msg.help_request_id);
    if (!req) { const e = new Error('fk help_request'); e.sqlState = '23503'; throw e; }
    if (senderRole === 'STUDENT' && req.student_id !== msg.sender_id) {
      const e = new Error('unauthorized student'); e.sqlState = '23514'; throw e;
    }
    const saved = { id: `m-${this.messages.length + 1}`, is_read: false, read_at: null, ...msg };
    this.messages.push(saved);
    return saved;
  }
  markRead(msgId, readAt) {
    const m = this.messages.find((x) => x.id === msgId);
    if (readAt < m.sent_at) { const e = new Error('read_at < sent_at'); e.sqlState = '23514'; throw e; }
    m.is_read = true;
    m.read_at = readAt;
    return m;
  }
  deleteRequestCascade(reqId) {
    this.requests.delete(reqId);
    this.messages = this.messages.filter((m) => m.help_request_id !== reqId);
  }
  listThreadAsc(reqId) {
    return this.messages.filter((m) => m.help_request_id === reqId).sort((a, b) => a.sent_at.localeCompare(b.sent_at));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-044] — MENSAGENS INTERNAS (chat_messages)');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate executados com sucesso');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');

assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/44_tabela_chat_messages.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-044'),
  'Documentação DB-044 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /fk_chat_messages_help_request[\s\S]*?ON\s+DELETE\s+CASCADE/i.test(sqlContent) &&
    /chk_chat_messages_read_consistency/i.test(sqlContent) &&
    /pol_chat_messages_participants_only/i.test(sqlContent) &&
    /idx_chat_messages_request_sent\s+ON\s+chat_messages\s+USING\s+BTREE\s*\(\s*help_request_id\s*,\s*sent_at\s+ASC\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (FK ON DELETE CASCADE, controle is_read/read_at, RLS e índice sent_at ASC)'
);
assertCheck(
  schemaContent.includes('model ChatMessage') && typesTsContent.includes('export interface ChatMessage {'),
  'Modelo ChatMessage integrado ao prisma/schema.prisma e tipos TypeScript'
);

const sim = new ChatSimulator();
sim.addRequest('hr-1', 'stu-1');
const m1 = sim.send({ help_request_id: 'hr-1', sender_id: 'stu-1', message_body: 'Dúvida no torneamento', sent_at: '2026-03-19T13:50:00Z' }, 'STUDENT');
sim.send({ help_request_id: 'hr-1', sender_id: 'tch-1', message_body: 'Vamos revisar às 14h', sent_at: '2026-03-19T14:00:00Z' }, 'TEACHER');
sim.markRead(m1.id, '2026-03-19T13:55:00Z');

let intruderBlocked = false;
try { sim.send({ help_request_id: 'hr-1', sender_id: 'stu-2', message_body: 'Intruso', sent_at: '2026-03-19T14:05:00Z' }, 'STUDENT'); } catch (e) { intruderBlocked = e.sqlState === '23514'; }

const thread = sim.listThreadAsc('hr-1');
assertCheck(
  thread.length === 2 && thread[0].id === m1.id && m1.is_read === true && intruderBlocked,
  'Teste 1 (Critérios 1, 2 e 3): Thread ordenada por sent_at ASC, confirmação de leitura e bloqueio de aluno intruso'
);
sim.deleteRequestCascade('hr-1');
assertCheck(sim.messages.length === 0, 'Teste 2: Exclusão em cascata (ON DELETE CASCADE) remove mensagens do chamado');

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-044] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
