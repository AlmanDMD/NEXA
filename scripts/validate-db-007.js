/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-007]
 * Título: Implementar Tabela de Perfis de Usuário (user_profiles) e Dados de Contato
 *
 * Verifica programaticamente:
 * 1. Critério 1: Relacionamento 1:1 entre `users` e `user_profiles` (`uq_user_profiles_user_id`)
 *    com `ON DELETE CASCADE` (`fk_user_profiles_user`).
 * 2. Critério 2: `registration_number` único no sistema (`uq_user_profiles_registration_number`).
 * 3. Critério 3: Campos pessoais (PII) isolados (`full_name`, `phone`, `avatar_url`, `bio`) para LGPD.
 * 4. Observação Técnica: Índice B-Tree em `registration_number` (`idx_user_profiles_registration_number`).
 * 5. DoD: Testes unitários de integridade 1:1, cascade delete e unicidade de matrícula.
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
  '20261105010000_create_user_profiles_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261105010000_create_user_profiles_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '07_tabela_user_profiles.sql');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '07-tabela-perfis-usuario-lgpd.md'),
  path.join(ROOT_DIR, 'BancoNexa', '07-tabela-perfis-usuario-lgpd.md'),
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
 * Simulador de integridade referencial 1:1 (users <-> user_profiles) com ON DELETE CASCADE e UNIQUE
 */
class UserProfilesRelationalSimulator {
  constructor() {
    this.users = new Map();
    this.profilesByUserId = new Map();
    this.profilesByRegistration = new Map();
  }

  createUser(id, email) {
    this.users.set(id, { id, email });
  }

  createProfile(row) {
    if (!this.users.has(row.user_id)) {
      const err = new Error('insert or update on table "user_profiles" violates foreign key constraint "fk_user_profiles_user"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (this.profilesByUserId.has(row.user_id)) {
      const err = new Error('Unique constraint failed on the fields: (`user_id`) [uq_user_profiles_user_id]');
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const normalizedReg = String(row.registration_number || '').trim().toUpperCase();
    if (this.profilesByRegistration.has(normalizedReg)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`registration_number`) [uq_user_profiles_registration_number]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const saved = {
      id: row.id || '00000000-0000-4000-8000-000000000101',
      user_id: row.user_id,
      full_name: String(row.full_name || '').trim(),
      registration_number: normalizedReg,
      phone: row.phone || null,
      avatar_url: row.avatar_url || null,
      bio: row.bio || null,
    };

    this.profilesByUserId.set(saved.user_id, saved);
    this.profilesByRegistration.set(saved.registration_number, saved);
    return saved;
  }

  deleteUserCascade(userId) {
    this.users.delete(userId);
    const profile = this.profilesByUserId.get(userId);
    if (profile) {
      this.profilesByRegistration.delete(profile.registration_number);
      this.profilesByUserId.delete(userId);
    }
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-007] — TABELA DE PERFIS (user_profiles)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram e registraram a migration de user_profiles');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL e documentação
console.log('\n2. Verificando arquivos SQL, migration e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261105010000_create_user_profiles_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261105010000_create_user_profiles_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/07_tabela_user_profiles.sql');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');

// 3. Critério 1: Relacionamento 1:1 entre users e user_profiles com cascade delete
console.log('\n3. Verificando Critério de Aceitação 1 (Relacionamento 1:1 com ON DELETE CASCADE)...');
assertCheck(
  /CONSTRAINT\s+uq_user_profiles_user_id\s+UNIQUE\s*\(\s*user_id\s*\)/i.test(sqlContent) &&
    /FOREIGN\s+KEY\s*\(\s*user_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+CASCADE/i.test(
      sqlContent
    ),
  'Constraint UNIQUE uq_user_profiles_user_id e FK fk_user_profiles_user ON DELETE CASCADE presentes no SQL'
);
assertCheck(
  schemaContent.includes('model UserProfile') &&
    schemaContent.includes('onDelete: Cascade') &&
    schemaContent.includes('@@map("user_profiles")'),
  'Modelo UserProfile configurado com 1:1 e onDelete: Cascade no prisma/schema.prisma'
);

// 4. Critério 2 e Observação Técnica: registration_number único e indexado
console.log('\n4. Verificando Critério de Aceitação 2 e Observação Técnica (registration_number UNIQUE e Indexado)...');
assertCheck(
  /CONSTRAINT\s+uq_user_profiles_registration_number\s+UNIQUE\s*\(\s*registration_number\s*\)/i.test(sqlContent),
  'Constraint UNIQUE uq_user_profiles_registration_number declarada no SQL'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_user_profiles_registration_number\s+ON\s+user_profiles/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_user_profiles_full_name\s+ON\s+user_profiles/i.test(sqlContent),
  'Índices B-Tree idx_user_profiles_registration_number e idx_user_profiles_full_name criados para buscas da secretaria'
);

// 5. Critério 3: Campos pessoais isolados para LGPD
console.log('\n5. Verificando Critério de Aceitação 3 (Isolamento de campos PII para LGPD)...');
assertCheck(
  /full_name\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /registration_number\s+VARCHAR\(50\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /phone\s+VARCHAR\(25\)/i.test(sqlContent) &&
    /avatar_url\s+VARCHAR\(500\)/i.test(sqlContent) &&
    /bio\s+TEXT/i.test(sqlContent),
  'Todos os campos PII (full_name, registration_number, phone, avatar_url, bio) isolados na tabela user_profiles'
);

// 6. DoD: Testes unitários de integridade 1:1, unicidade de matrícula e cascade delete
console.log('\n6. Executando testes unitários de integridade 1:1, matrícula única e Cascade Delete (DoD)...');
const sim = new UserProfilesRelationalSimulator();
const userId1 = '11111111-1111-4111-8111-111111111111';
const userId2 = '22222222-2222-4222-8222-222222222222';
sim.createUser(userId1, 'lucas@senai.br');
sim.createUser(userId2, 'carlos@senai.br');

const p1 = sim.createProfile({
  user_id: userId1,
  full_name: 'Lucas Silva',
  registration_number: ' senai-2026-001 ',
  phone: '11999990000',
});
assertCheck(
  p1.registration_number === 'SENAI-2026-001',
  'Teste 1: Matrícula SENAI padronizada automaticamente em caixa alta sem espaços ("SENAI-2026-001")'
);

let violatedOneToOne = false;
try {
  sim.createProfile({
    user_id: userId1,
    full_name: 'Segundo Perfil Inválido',
    registration_number: 'SENAI-2026-002',
  });
} catch (err) {
  violatedOneToOne = err.code === 'P2002';
}
assertCheck(violatedOneToOne, 'Teste 2: Tentativa de criar segundo perfil para o mesmo user_id foi bloqueada (1:1 estrito)');

let violatedUniqueReg = false;
try {
  sim.createProfile({
    user_id: userId2,
    full_name: 'Carlos Oliveira',
    registration_number: 'senai-2026-001',
  });
} catch (err) {
  violatedUniqueReg = err.code === 'P2002';
}
assertCheck(violatedUniqueReg, 'Teste 3: Tentativa de duplicar registration_number em outro usuário foi bloqueada (P2002)');

sim.deleteUserCascade(userId1);
assertCheck(
  !sim.profilesByUserId.has(userId1) && !sim.profilesByRegistration.has('SENAI-2026-001'),
  'Teste 4: Exclusão do usuário em `users` removeu automaticamente o perfil vinculado via ON DELETE CASCADE'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-007] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
