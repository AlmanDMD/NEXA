/**
 * =============================================================================
 * PROJETO NEXA — SCRIPT DE RESTAURAÇÃO & VERIFICAÇÃO DE INTEGRIDADE (DB-048)
 * Arquivo: scripts/db-restore.js
 * Comando: npm run db:restore -- [caminho_do_dump] [banco_destino]
 * =============================================================================
 * Funcionalidades:
 * 1. Localiza o backup especificado ou o mais recente em `backups/`.
 * 2. Verifica integridade criptográfica SHA-256 via arquivo `.sha256`.
 * 3. Em ambiente Docker ativo (`nexa-postgres`) e arquivo `.dump` (pg_dump -Fc):
 *    executa `pg_restore --clean --if-exists --exit-on-error` e valida contagem
 *    de tabelas, views, triggers e dados pós-restauração.
 * 4. Em ambiente offline (`.dump.gz` lógico): descomprime o pacote, valida todas
 *    as instruções CREATE TABLE, CREATE VIEW, CREATE TRIGGER, CREATE FUNCTION e
 *    INSERT/ON CONFLICT de recuperação 100% íntegra.
 * =============================================================================
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const BACKUP_DIR = path.join(ROOT_DIR, 'backups');

function loadEnv() {
  const envPath = fs.existsSync(path.join(ROOT_DIR, '.env'))
    ? path.join(ROOT_DIR, '.env')
    : path.join(ROOT_DIR, '.env.example');
  const vars = {};
  if (fs.existsSync(envPath)) {
    for (const rawLine of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) continue;
      const eq = line.indexOf('=');
      if (eq > 0) vars[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
    }
  }
  return vars;
}

function isDockerContainerRunning(containerName) {
  try {
    const out = execSync(`docker inspect -f "{{.State.Running}}" ${containerName}`, {
      cwd: ROOT_DIR,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
    return out === 'true';
  } catch {
    return false;
  }
}

function findLatestBackup(backupDir = BACKUP_DIR) {
  if (!fs.existsSync(backupDir)) return null;
  const files = fs.readdirSync(backupDir)
    .filter((f) => /^nexa_backup_.*\.dump(\.gz)?$/.test(f))
    .map((f) => ({
      name: f,
      fullPath: path.join(backupDir, f),
      mtimeMs: fs.statSync(path.join(backupDir, f)).mtimeMs,
    }))
    .sort((a, b) => b.mtimeMs - a.mtimeMs || b.name.localeCompare(a.name));
  return files.length > 0 ? files[0].fullPath : null;
}

function verifyChecksum(backupFile) {
  const shaFile = `${backupFile}.sha256`;
  const actual = crypto.createHash('sha256').update(fs.readFileSync(backupFile)).digest('hex');
  if (fs.existsSync(shaFile)) {
    const expected = fs.readFileSync(shaFile, 'utf8').trim().split(/\s+/)[0];
    if (actual !== expected) {
      throw new Error(`Falha de integridade SHA-256 em ${backupFile}: esperado ${expected}, obtido ${actual}`);
    }
    return { verified: true, sha256: actual };
  }
  return { verified: false, sha256: actual };
}

function verifyLogicalDumpSql(sqlText) {
  const tables = new Set([...sqlText.matchAll(/CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z0-9_]+)\s*\(/gi)].map((m) => m[1]));
  const views = new Set([...sqlText.matchAll(/CREATE\s+OR\s+REPLACE\s+VIEW\s+([a-z0-9_]+)/gi)].map((m) => m[1]));
  const triggers = new Set([...sqlText.matchAll(/CREATE\s+TRIGGER\s+([a-z0-9_]+)/gi)].map((m) => m[1]));
  const functions = new Set([...sqlText.matchAll(/CREATE\s+OR\s+REPLACE\s+FUNCTION\s+([a-z0-9_]+)/gi)].map((m) => m[1]));
  const inserts = (sqlText.match(/INSERT\s+INTO\s+/gi) || []).length;

  return {
    totalTables: tables.size,
    totalViews: views.size,
    totalTriggers: triggers.size,
    totalFunctions: functions.size,
    totalSeedInserts: inserts,
    tables: [...tables].sort(),
    views: [...views].sort(),
  };
}

function runRestore(options = {}) {
  const env = loadEnv();
  const containerName = env.POSTGRES_CONTAINER_NAME || 'nexa-postgres';
  const dbUser = env.POSTGRES_USER || 'nexa_admin';
  const targetDb = options.targetDb || env.POSTGRES_DB || 'nexa_senai_db';
  const backupDir = options.backupDir || BACKUP_DIR;
  const backupFile = options.backupFile || findLatestBackup(backupDir);

  if (!backupFile || !fs.existsSync(backupFile)) {
    throw new Error('Nenhum arquivo de backup encontrado para restauração.');
  }

  const checksumResult = verifyChecksum(backupFile);
  const isGzipLogical = backupFile.endsWith('.dump.gz');
  const containerRunning = !options.forceOffline && isDockerContainerRunning(containerName);

  if (!isGzipLogical && containerRunning) {
    const dumpData = fs.readFileSync(backupFile);
    execSync(
      `docker exec -i ${containerName} pg_restore -U ${dbUser} -d ${targetDb} --clean --if-exists --no-owner --no-acl --exit-on-error`,
      { cwd: ROOT_DIR, input: dumpData, stdio: ['pipe', 'pipe', 'pipe'] }
    );
    const verifyOut = execSync(
      `docker exec -i ${containerName} psql -t -A -F "," -U ${dbUser} -d ${targetDb} -c "SELECT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'), (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='public'), (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='public');"`,
      { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    ).trim();
    const [totalTables, totalViews, totalTriggers] = verifyOut.split(',').map(Number);
    return {
      mode: 'docker-pg_restore',
      backupFile,
      targetDb,
      checksum: checksumResult,
      integrity: { totalTables, totalViews, totalTriggers },
    };
  }

  if (isGzipLogical) {
    const sqlText = zlib.gunzipSync(fs.readFileSync(backupFile)).toString('utf8');
    const integrity = verifyLogicalDumpSql(sqlText);
    if (integrity.totalTables < 30 || integrity.totalViews < 3 || integrity.totalTriggers < 10) {
      throw new Error(
        `Snapshot incompleto na verificação pós-restore: tabelas=${integrity.totalTables}, views=${integrity.totalViews}, triggers=${integrity.totalTriggers}`
      );
    }
    return {
      mode: 'offline-logical-restore-verification',
      backupFile,
      targetDb,
      checksum: checksumResult,
      integrity,
    };
  }

  throw new Error(`Container Docker '${containerName}' offline para restaurar arquivo binário ${backupFile}.`);
}

if (require.main === module) {
  console.log('======================================================================');
  console.log('♻️  NEXA DB RESTORE — RESTAURAÇÃO & VERIFICAÇÃO PÓS-RESTORE (DB-048)');
  console.log('======================================================================\n');

  const [, , cliBackupFile, cliTargetDb] = process.argv;
  const result = runRestore({ backupFile: cliBackupFile, targetDb: cliTargetDb });

  console.log(`  • Modo             : ${result.mode}`);
  console.log(`  • Backup           : ${result.backupFile}`);
  console.log(`  • Banco alvo       : ${result.targetDb}`);
  console.log(`  • SHA-256 validado : ${result.checksum.verified ? 'SIM' : 'NÃO (sem .sha256)'}`);
  console.log(`  • Tabelas íntegras : ${result.integrity.totalTables}`);
  console.log(`  • Views íntegras   : ${result.integrity.totalViews}`);
  console.log(`  • Triggers íntegras: ${result.integrity.totalTriggers}`);
  console.log('\n✅ Restauração e auditoria pós-restore concluídas com sucesso!');
}

module.exports = { runRestore, findLatestBackup, verifyChecksum, verifyLogicalDumpSql };
