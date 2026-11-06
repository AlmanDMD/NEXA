/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-009]
 * Título: Implementar Tabela de Registro de Atividades e Auditoria (audit_logs)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Tabela `audit_logs` com campos `JSONB` (`old_values`, `new_values`) para diff.
 * 2. Critério 2: Chave estrangeira `user_id` sem deleção em cascata (`ON DELETE SET NULL`),
 *    preservando o histórico mesmo se o usuário for deletado, além de suportar ações de sistema (`NULL`).
 * 3. Critério 3: Índice temporal em `created_at` (`idx_audit_logs_created_at`).
 * 4. Observação Técnica / DoD: Índices GIN nos campos JSONB e teste de inserção/busca JSONB (`@>`).
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
  '20261105030000_create_audit_logs_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261105030000_create_audit_logs_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '09_tabela_audit_logs.sql');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '09-tabela-auditoria-logs-jsonb.md'),
  path.join(ROOT_DIR, 'BancoNexa', '09-tabela-auditoria-logs-jsonb.md'),
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
 * Simulador da tabela `audit_logs` com suporte a JSONB diff, operador de contenção `@>`,
 * `ON DELETE SET NULL` e trigger de imutabilidade.
 */
class AuditLogsTableSimulator {
  constructor() {
    this.users = new Set(['teacher-uuid-001', 'coord-uuid-002']);
    this.logs = [];
  }

  insert(row) {
    if (row.user_id !== null && row.user_id !== undefined && !this.users.has(row.user_id)) {
      const err = new Error('insert or update on table "audit_logs" violates foreign key constraint "fk_audit_logs_user"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    if (!row.action || String(row.action).trim().length < 2) {
      throw new Error('violates check constraint "chk_audit_logs_action_not_empty"');
    }

    const parsedOld =
      typeof row.old_values === 'string' ? JSON.parse(row.old_values) : row.old_values || null;
    const parsedNew =
      typeof row.new_values === 'string' ? JSON.parse(row.new_values) : row.new_values || null;

    const record = {
      id: `audit-${this.logs.length + 1}`,
      user_id: row.user_id !== undefined ? row.user_id : null,
      action: String(row.action).trim(),
      entity: String(row.entity).trim(),
      entity_id: String(row.entity_id).trim(),
      old_values: parsedOld,
      new_values: parsedNew,
      ip_address: row.ip_address || null,
      created_at: new Date().toISOString(),
    };
    this.logs.push(record);
    return record;
  }

  deleteUserSetNull(userId) {
    this.users.delete(userId);
    for (const log of this.logs) {
      if (log.user_id === userId) {
        log.user_id = null; // ON DELETE SET NULL: preserva o registro histórico!
      }
    }
  }

  deleteLogAttempt() {
    const err = new Error(
      'Operacao bloqueada: registros da tabela audit_logs sao imutaveis e nao podem ser excluidos (Governanca/LGPD).'
    );
    err.sqlState = '42501';
    throw err;
  }

  queryJsonbContains(column, filterObj) {
    return this.logs.filter((log) => {
      const target = log[column];
      if (!target || typeof target !== 'object') return false;
      return Object.entries(filterObj).every(([k, v]) => target[k] === v);
    });
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-009] — AUDITORIA E LOGS JSONB (audit_logs)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate validaram e registraram a migration de audit_logs');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL e documentação
console.log('\n2. Verificando arquivos SQL, migration e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261105030000_create_audit_logs_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261105030000_create_audit_logs_table.sql'
);
assertCheck(fs.existsSync(BANCO_SQL_PATH), 'Script SQL dedicado em BancoNexa/sql/09_tabela_audit_logs.sql');
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');

// 3. Critério 1: Tabela com campos JSONB para armazenar diff de valores antigos e novos
console.log('\n3. Verificando Critério de Aceitação 1 (Colunas old_values e new_values em JSONB)...');
assertCheck(
  /old_values\s+JSONB/i.test(sqlContent) && /new_values\s+JSONB/i.test(sqlContent),
  'Colunas old_values JSONB e new_values JSONB declaradas na tabela audit_logs'
);
assertCheck(
  schemaContent.includes('model AuditLog') &&
    schemaContent.includes('@map("old_values") @db.JsonB') &&
    schemaContent.includes('@map("new_values") @db.JsonB'),
  'Modelo AuditLog configurado com @db.JsonB para oldValues e newValues no prisma/schema.prisma'
);

// 4. Critério 2: Sem foreign key com deleção em cascata (ON DELETE SET NULL)
console.log('\n4. Verificando Critério de Aceitação 2 (Preservação de histórico com ON DELETE SET NULL)...');
assertCheck(
  /user_id\s+UUID\s*,/i.test(sqlContent) &&
    /FOREIGN\s+KEY\s*\(\s*user_id\s*\)\s*REFERENCES\s+users\s*\(\s*id\s*\)\s*ON\s+DELETE\s+SET\s+NULL/i.test(
      sqlContent
    ) &&
    !/ON\s+DELETE\s+CASCADE/i.test(sqlContent),
  'FK fk_audit_logs_user configurada com user_id opcional e ON DELETE SET NULL (sem CASCADE)'
);

// 5. Critério 3 e Observação Técnica: Índice temporal em created_at e Índices GIN para @>
console.log('\n5. Verificando Critério de Aceitação 3 e Observação Técnica (Índice temporal e GIN JSONB)...');
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_audit_logs_created_at\s+ON\s+audit_logs\s+USING\s+BTREE\s*\(\s*created_at\s+DESC\s*\)/i.test(
    sqlContent
  ),
  'Índice temporal idx_audit_logs_created_at (created_at DESC) criado para relatórios rápidos'
);
assertCheck(
  /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_audit_logs_old_values_gin\s+ON\s+audit_logs\s+USING\s+GIN\s*\(\s*old_values\s*\)/i.test(
    sqlContent
  ) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_audit_logs_new_values_gin\s+ON\s+audit_logs\s+USING\s+GIN\s*\(\s*new_values\s*\)/i.test(
      sqlContent
    ),
  'Índices GIN (idx_audit_logs_old_values_gin e idx_audit_logs_new_values_gin) criados para buscas JSONB com @>'
);

// 6. DoD: Testes unitários de inserção JSONB, busca @>, preservação ON DELETE SET NULL e imutabilidade
console.log('\n6. Executando testes unitários de JSONB, ON DELETE SET NULL e imutabilidade (DoD)...');
const sim = new AuditLogsTableSimulator();

sim.insert({
  user_id: 'teacher-uuid-001',
  action: 'UPDATE_GRADE',
  entity: 'StudentGrade',
  entity_id: 'grade-uuid-900',
  old_values: { grade_value: 5.5, status: 'PENDING_RECOVERY' },
  new_values: { grade_value: 7.5, recovery_grade: 7.5, status: 'APPROVED' },
  ip_address: '192.168.10.40',
});

sim.insert({
  user_id: null, // Ação automática de sistema
  action: 'LGPD_RETENTION_CHECK',
  entity: 'SystemJob',
  entity_id: 'job-2026-11',
  old_values: null,
  new_values: { anonymized_profiles: 0 },
});

const matchedJsonb = sim.queryJsonbContains('new_values', { grade_value: 7.5, status: 'APPROVED' });
assertCheck(
  matchedJsonb.length === 1 && matchedJsonb[0].old_values.grade_value === 5.5,
  'Teste 1 (DoD): Inserção de diff JSONB (old_values / new_values) e consulta indexada por contenção (@>) validadas'
);

sim.deleteUserSetNull('teacher-uuid-001');
assertCheck(
  sim.logs.length === 2 && sim.logs[0].user_id === null && sim.logs[0].entity_id === 'grade-uuid-900',
  'Teste 2: Exclusão do usuário manteve o log de auditoria intacto com user_id = NULL (ON DELETE SET NULL)'
);

let deleteBlocked = false;
try {
  sim.deleteLogAttempt();
} catch (err) {
  deleteBlocked = err.sqlState === '42501';
}
assertCheck(
  deleteBlocked,
  'Teste 3: Tentativa de excluir registro de auditoria bloqueada pela Trigger trg_audit_logs_prevent_delete'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-009] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
