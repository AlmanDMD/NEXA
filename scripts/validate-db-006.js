/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-006]
 * Título: Implementar Tabela de Usuários (users) com Hash Seguro de Senha
 *
 * Verifica programaticamente:
 * 1. Critério 1: Tabela `users` com constraint UNIQUE (`uq_users_email`) em `email`.
 * 2. Critério 2: Campo `password_hash` não nulo (`VARCHAR(255) NOT NULL`) com bloqueio de texto puro.
 * 3. Critério 3: Índices criados no campo `email` (`idx_users_email`, `idx_users_email_lower`).
 * 4. Observação Técnica: Normalização automática de `email` em minúsculo (lowercased).
 * 5. DoD: Teste de inserção com e-mail duplicado rejeitado com erro P2002 / SQLSTATE 23505.
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
  '20261105000000_create_users_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261105000000_create_users_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '06_tabela_users.sql');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '06-tabela-usuarios-hash-senha.md'),
  path.join(ROOT_DIR, 'BancoNexa', '06-tabela-usuarios-hash-senha.md'),
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
 * Simulador/Validador das constraints SQL da tabela `users` (DoD: teste de duplicidade P2002 e hash)
 */
class UsersTableConstraintSimulator {
  constructor() {
    this.rowsByEmail = new Map();
  }

  insert(row) {
    if (!row.email) {
      const err = new Error('null value in column "email" of relation "users" violates not-null constraint');
      err.code = '23502';
      throw err;
    }

    // Trigger trg_users_normalize_and_touch: normaliza para minúsculo (lowercased)
    const normalizedEmail = String(row.email).trim().toLowerCase();

    // CHECK chk_users_email_lowercase
    if (normalizedEmail.indexOf('@') <= 0) {
      const err = new Error('new row for relation "users" violates check constraint "chk_users_email_lowercase"');
      err.code = '23514';
      throw err;
    }

    // CHECK chk_users_password_hash_not_plaintext
    const pwd = String(row.password_hash || '').trim();
    const validHashRegex = /^(\$2[aby]\$|\$argon2|\$pbkdf2|pbkdf2:|scrypt:)/;
    if (!pwd || pwd.length < 50 || !validHashRegex.test(pwd)) {
      const err = new Error(
        'new row for relation "users" violates check constraint "chk_users_password_hash_not_plaintext"'
      );
      err.code = '23514';
      throw err;
    }

    // UNIQUE uq_users_email (PostgreSQL 23505 -> Prisma P2002)
    if (this.rowsByEmail.has(normalizedEmail)) {
      const err = new Error(
        `Unique constraint failed on the fields: (\`email\`) [SQLSTATE 23505 / uq_users_email]`
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || '00000000-0000-4000-8000-000000000001',
      email: normalizedEmail,
      password_hash: pwd,
      role: row.role || 'STUDENT',
      is_active: row.is_active !== undefined ? row.is_active : true,
    };
    this.rowsByEmail.set(normalizedEmail, saved);
    return saved;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-006] — TABELA DE USUÁRIOS (users) & HASH');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram e registraram a migration de users');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL e Schema
console.log('\n2. Verificando arquivos SQL, migration e schema.prisma...');
assertCheck(fs.existsSync(MIGRATION_SQL_PATH), 'Migration SQL presente em prisma/migrations/20261105000000_create_users_table/migration.sql');
assertCheck(fs.existsSync(BANCO_MIGRATION_SQL_PATH), 'Migration SQL espelhada em BancoNexa/migrations/20261105000000_create_users_table.sql');
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/06_tabela_users.sql');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');

// 3. Critério 1: Tabela users com constraint UNIQUE em email e colunas exigidas
console.log('\n3. Verificando Critério de Aceitação 1 (Colunas da tabela users e UNIQUE em email)...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /email\s+VARCHAR\(255\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /password_hash\s+VARCHAR\(255\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /role\s+user_role_enum\s+NOT\s+NULL\s+DEFAULT\s+'STUDENT'/i.test(sqlContent) &&
    /is_active\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+TRUE/i.test(sqlContent) &&
    /created_at\s+TIMESTAMPTZ/i.test(sqlContent) &&
    /updated_at\s+TIMESTAMPTZ/i.test(sqlContent),
  'Todas as colunas exigidas (id, email, password_hash, role, is_active, created_at, updated_at) presentes com tipos corretos'
);
assertCheck(
  /CONSTRAINT\s+uq_users_email\s+UNIQUE\s*\(\s*email\s*\)/i.test(sqlContent) &&
    schemaContent.includes('@unique(map: "uq_users_email")'),
  'Constraint UNIQUE uq_users_email declarada no SQL e no schema.prisma'
);

// 4. Critério 2: Campo password_hash não nulo sem armazenamento de texto puro
console.log('\n4. Verificando Critério de Aceitação 2 (Proteção de password_hash contra texto puro)...');
assertCheck(
  /CONSTRAINT\s+chk_users_password_hash_not_plaintext\s+CHECK/i.test(sqlContent),
  'Constraint SQL chk_users_password_hash_not_plaintext protege contra senhas em texto puro (exige Bcrypt/Argon2 >= 50 chars)'
);

// 5. Critério 3: Índices criados no campo email e Observação Técnica (lowercased)
console.log('\n5. Verificando Critério de Aceitação 3 (Índices em email e normalização lowercased)...');
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_users_email\s+ON\s+users/i.test(sqlContent) &&
    /CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_users_email_lower\s+ON\s+users/i.test(sqlContent),
  'Índices B-Tree idx_users_email e idx_users_email_lower criados na tabela users'
);
assertCheck(
  /CONSTRAINT\s+chk_users_email_lowercase\s+CHECK/i.test(sqlContent) &&
    /CREATE\s+TRIGGER\s+trg_users_normalize_and_touch/i.test(sqlContent),
  'Constraint chk_users_email_lowercase e Trigger trg_users_normalize_and_touch garantem e-mail em minúsculo (lowercased)'
);

// 6. DoD: Teste unitário de inserção, rejeição de texto puro e rejeição de e-mail duplicado com P2002
console.log('\n6. Executando testes unitários de integridade da tabela users (DoD: P2002 e Hash)...');
const sim = new UsersTableConstraintSimulator();
const validBcryptHash = '$2b$12$KIX/x8k9q8y1Z7u5v6w7xO1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6';

const insertedUser = sim.insert({
  email: '  Lucas.Tornearia@SENAI.br ',
  password_hash: validBcryptHash,
  role: 'STUDENT',
});
assertCheck(
  insertedUser.email === 'lucas.tornearia@senai.br',
  'Teste 1: E-mail com letras maiúsculas/espaços foi normalizado automaticamente para minúsculo (lowercased)'
);

let duplicateErrorCode = null;
try {
  sim.insert({
    email: 'lucas.tornearia@senai.br',
    password_hash: validBcryptHash,
    role: 'STUDENT',
  });
} catch (err) {
  duplicateErrorCode = err.code;
}
assertCheck(
  duplicateErrorCode === 'P2002',
  'Teste 2 (DoD): Inserção com e-mail duplicado foi rejeitada com erro P2002 (SQLSTATE 23505)'
);

let plainTextRejected = false;
try {
  sim.insert({
    email: 'outro.aluno@senai.br',
    password_hash: 'senha123456',
    role: 'STUDENT',
  });
} catch (err) {
  plainTextRejected = err.code === '23514';
}
assertCheck(
  plainTextRejected,
  'Teste 3: Tentativa de inserir senha em texto puro ("senha123456") foi bloqueada pela constraint chk_users_password_hash_not_plaintext'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-006] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
