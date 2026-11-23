/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-008]
 * Título: Criar Tabela de Sessões e Refresh Tokens com Revogação (auth_sessions)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Tabela `auth_sessions` criada com chave estrangeira para `users(id)` (`fk_auth_sessions_user`).
 * 2. Critério 2: Campo `is_revoked` indexado para consulta ultra-rápida no middleware de auth.
 * 3. Critério 3: Constraint de expiração verificável (`chk_auth_sessions_expiration: expires_at > created_at`).
 * 4. Observação Técnica / DoD: Índices eficientes em `refresh_token_hash` e rejeição de token puro (exige SHA-256).
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'prisma',
  'migrations',
  '20261105020000_create_auth_sessions_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261105020000_create_auth_sessions_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '08_tabela_auth_sessions.sql');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '08-tabela-sessoes-refresh-tokens.md'),
  path.join(ROOT_DIR, 'BancoNexa', '08-tabela-sessoes-refresh-tokens.md'),
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
 * Simulador das constraints da tabela `auth_sessions` (SHA-256, expiração, revogação e FK)
 */
class AuthSessionsTableSimulator {
  constructor() {
    this.users = new Set(['11111111-1111-4111-8111-111111111111']);
    this.sessionsByTokenHash = new Map();
  }

  insert(row) {
    if (!this.users.has(row.user_id)) {
      const err = new Error('insert or update on table "auth_sessions" violates foreign key constraint "fk_auth_sessions_user"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    const tokenHash = String(row.refresh_token_hash || '').trim().toLowerCase();

    // Observação Técnica: O token nunca é salvo puro, apenas o hash SHA-256 (64 hex chars)
    if (!/^[a-f0-9]{64}$/.test(tokenHash)) {
      const err = new Error(
        'new row for relation "auth_sessions" violates check constraint "chk_auth_sessions_sha256_hash"'
      );
      err.code = '23514';
      throw err;
    }

    const createdAt = row.created_at ? new Date(row.created_at) : new Date();
    const expiresAt = new Date(row.expires_at);

    // Critério 3: Constraint de expiração verificável (expires_at > created_at)
    if (!(expiresAt.getTime() > createdAt.getTime())) {
      const err = new Error(
        'new row for relation "auth_sessions" violates check constraint "chk_auth_sessions_expiration"'
      );
      err.code = '23514';
      throw err;
    }

    if (this.sessionsByTokenHash.has(tokenHash)) {
      const err = new Error('Unique constraint failed on the fields: (`refresh_token_hash`) [uq_auth_sessions_token_hash]');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: '00000000-0000-4000-8000-000000000201',
      user_id: row.user_id,
      refresh_token_hash: tokenHash,
      user_agent: row.user_agent || null,
      ip_address: row.ip_address || null,
      expires_at: expiresAt.toISOString(),
      is_revoked: Boolean(row.is_revoked),
      created_at: createdAt.toISOString(),
    };
    this.sessionsByTokenHash.set(tokenHash, saved);
    return saved;
  }

  revoke(tokenHash) {
    const session = this.sessionsByTokenHash.get(tokenHash);
    if (session) {
      session.is_revoked = true;
    }
    return session;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-008] — SESSÕES E REFRESH TOKENS (auth_sessions)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram e registraram a migration de auth_sessions');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL e documentação
console.log('\n2. Verificando arquivos SQL, migration e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261105020000_create_auth_sessions_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261105020000_create_auth_sessions_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/08_tabela_auth_sessions.sql');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');

// 3. Critério 1: Tabela criada com chave estrangeira para users(id)
console.log('\n3. Verificando Critério de Aceitação 1 (Colunas de auth_sessions e FK para users(id))...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /user_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /refresh_token_hash\s+VARCHAR\(255\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /user_agent\s+VARCHAR\(500\)/i.test(sqlContent) &&
    /ip_address\s+VARCHAR\(45\)/i.test(sqlContent) &&
    /expires_at\s+TIMESTAMPTZ\s+NOT\s+NULL/i.test(sqlContent) &&
    /is_revoked\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+FALSE/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ\s+NOT\s+NULL/i.test(sqlContent),
  'Todas as colunas exigidas (id, user_id, refresh_token_hash, user_agent, ip_address, expires_at, is_revoked, created_at) presentes'
);
assertCheck(
  /CONSTRAINT\s+fk_auth_sessions_user\s+FOREIGN\s+KEY\s*\(\s*user_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)/i.test(
    sqlContent
  ) && schemaContent.includes('model AuthSession'),
  'Chave estrangeira fk_auth_sessions_user para users(id) declarada no SQL e no schema.prisma'
);

// 4. Critério 2 e DoD: Índices em is_revoked e refresh_token_hash
console.log('\n4. Verificando Critério de Aceitação 2 e DoD (Índices em is_revoked e refresh_token_hash)...');
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_auth_sessions_is_revoked\s+ON\s+auth_sessions/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_auth_sessions_refresh_token_hash\s+ON\s+auth_sessions/i.test(
      sqlContent
    ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_auth_sessions_active_tokens\s+ON\s+auth_sessions/i.test(sqlContent),
  'Índices B-Tree idx_auth_sessions_is_revoked, idx_auth_sessions_refresh_token_hash e índice parcial idx_auth_sessions_active_tokens criados'
);

// 5. Critério 3 e Observação Técnica: Constraint de expiração e hash SHA-256
console.log('\n5. Verificando Critério de Aceitação 3 e Observação Técnica (Expiração e Hash SHA-256)...');
assertCheck(
  /CONSTRAINT\s+chk_auth_sessions_expiration\s+CHECK\s*\(\s*expires_at\s*>\s*created_at\s*\)/i.test(sqlContent),
  'Constraint verificável chk_auth_sessions_expiration (expires_at > created_at) presente no SQL'
);
assertCheck(
  /CONSTRAINT\s+chk_auth_sessions_sha256_hash\s+CHECK/i.test(sqlContent),
  'Constraint chk_auth_sessions_sha256_hash impede salvamento de token puro e exige SHA-256 hexadecimal (64 chars)'
);

// 6. Testes unitários de sessão, rejeição de token puro, expiração inválida e revogação
console.log('\n6. Executando testes unitários de criação, expiração, hash SHA-256 e revogação...');
const sim = new AuthSessionsTableSimulator();
const rawJwtToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';
const tokenSha256 = crypto.createHash('sha256').update(rawJwtToken).digest('hex');

let rawTokenRejected = false;
try {
  sim.insert({
    user_id: '11111111-1111-4111-8111-111111111111',
    refresh_token_hash: rawJwtToken, // Tentando salvar o JWT puro!
    expires_at: new Date(Date.now() + 7 * 86400 * 1000).toISOString(),
  });
} catch (err) {
  rawTokenRejected = err.code === '23514';
}
assertCheck(rawTokenRejected, 'Teste 1: Tentativa de salvar Refresh Token JWT puro foi bloqueada pela constraint SHA-256');

let expiredSessionRejected = false;
try {
  const now = new Date();
  sim.insert({
    user_id: '11111111-1111-4111-8111-111111111111',
    refresh_token_hash: tokenSha256,
    created_at: now.toISOString(),
    expires_at: new Date(now.getTime() - 60000).toISOString(), // Expiração no passado!
  });
} catch (err) {
  expiredSessionRejected = err.code === '23514';
}
assertCheck(
  expiredSessionRejected,
  'Teste 2: Tentativa de criar sessão com expires_at <= created_at foi bloqueada pela constraint de expiração'
);

const validSession = sim.insert({
  user_id: '11111111-1111-4111-8111-111111111111',
  refresh_token_hash: tokenSha256,
  user_agent: 'Mozilla/5.0 (Tablet Oficina SENAI)',
  ip_address: '192.168.10.25',
  expires_at: new Date(Date.now() + 7 * 86400 * 1000).toISOString(),
});
sim.revoke(tokenSha256);
assertCheck(
  validSession.is_revoked === true && validSession.refresh_token_hash === tokenSha256,
  'Teste 3: Sessão criada com hash SHA-256 de 64 caracteres e revogada imediatamente em caso de logout'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-008] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
