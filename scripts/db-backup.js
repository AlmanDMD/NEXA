/**
 * =============================================================================
 * PROJETO NEXA — ROTINA AUTOMATIZADA DE BACKUP & ROTAÇÃO (DB-048)
 * Arquivo: scripts/db-backup.js
 * Comando: npm run db:backup
 * =============================================================================
 * Funcionalidades:
 * 1. Lê variáveis do .env (ou .env.example).
 * 2. Se o container Docker `nexa-postgres` estiver ativo, executa `pg_dump -Fc -Z 9`
 *    gerando um dump binário custom comprimido com timestamp em `backups/`.
 * 3. Se o Docker estiver offline (modo CI/validação local), gera um pacote
 *    comprimido (.dump.gz) contendo todas as migrations SQL versionadas, views,
 *    triggers, seeds e manifesto de integridade para validar o ciclo completo
 *    de backup + checksum + rotação dos últimos 7 arquivos.
 * 4. Calcula checksum SHA-256 e remove backups excedentes além dos últimos 7.
 * =============================================================================
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const BACKUP_DIR = path.join(ROOT_DIR, 'backups');
const PRISMA_MIGRATIONS_DIR = path.join(ROOT_DIR, 'prisma', 'migrations');
const BANCO_SQL_DIR = path.join(ROOT_DIR, 'BancoNexa', 'sql');

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

function formatTimestamp(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return [
    date.getUTCFullYear(),
    pad(date.getUTCMonth() + 1),
    pad(date.getUTCDate()),
    '_',
    pad(date.getUTCHours()),
    pad(date.getUTCMinutes()),
    pad(date.getUTCSeconds()),
    '_',
    String(date.getUTCMilliseconds()).padStart(3, '0'),
  ].join('');
}

function sha256Buffer(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

function buildOfflineLogicalDumpPayload() {
  const migrations = [];
  if (fs.existsSync(PRISMA_MIGRATIONS_DIR)) {
    const entries = fs.readdirSync(PRISMA_MIGRATIONS_DIR, { withFileTypes: true })
      .filter((e) => e.isDirectory())
      .sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      const sqlPath = path.join(PRISMA_MIGRATIONS_DIR, entry.name, 'migration.sql');
      if (fs.existsSync(sqlPath)) {
        migrations.push({
          name: entry.name,
          sql: fs.readFileSync(sqlPath, 'utf8'),
        });
      }
    }
  }

  const seeds = [];
  for (const seedFile of [
    '20_seed_estrutura_curricular_senai.sql',
    '30_seed_frequencias_notas_parciais.sql',
    '40_seed_diagnosticos_alertas_lote4.sql',
    '45_seed_gamification_badges.sql',
  ]) {
    const fullPath = path.join(BANCO_SQL_DIR, seedFile);
    if (fs.existsSync(fullPath)) {
      seeds.push({ name: seedFile, sql: fs.readFileSync(fullPath, 'utf8') });
    }
  }

  const fullSql = [
    '-- NEXA LOGICAL SNAPSHOT BACKUP (OFFLINE MODE - DB-048)',
    `-- GeneratedAtUTC: ${new Date().toISOString()}`,
    `-- Migrations: ${migrations.length} | Seeds: ${seeds.length}`,
    ...migrations.map((m) => `\n-- >>> MIGRATION: ${m.name}\n${m.sql}`),
    ...seeds.map((s) => `\n-- >>> SEED: ${s.name}\n${s.sql}`),
  ].join('\n');

  return {
    fullSql,
    migrationsCount: migrations.length,
    seedsCount: seeds.length,
  };
}

function rotateBackups(backupDir, maxKeep = 7) {
  if (!fs.existsSync(backupDir)) return [];
  const dumpFiles = fs.readdirSync(backupDir)
    .filter((f) => /^nexa_backup_.*\.dump(\.gz)?$/.test(f))
    .map((f) => ({
      name: f,
      fullPath: path.join(backupDir, f),
      mtimeMs: fs.statSync(path.join(backupDir, f)).mtimeMs,
    }))
    .sort((a, b) => b.mtimeMs - a.mtimeMs || b.name.localeCompare(a.name));

  const removed = [];
  for (let i = maxKeep; i < dumpFiles.length; i++) {
    const target = dumpFiles[i];
    fs.unlinkSync(target.fullPath);
    const shaPath = `${target.fullPath}.sha256`;
    if (fs.existsSync(shaPath)) fs.unlinkSync(shaPath);
    const metaPath = `${target.fullPath}.meta.json`;
    if (fs.existsSync(metaPath)) fs.unlinkSync(metaPath);
    removed.push(target.name);
  }
  return removed;
}

function runBackup(options = {}) {
  const env = loadEnv();
  const containerName = env.POSTGRES_CONTAINER_NAME || 'nexa-postgres';
  const dbUser = env.POSTGRES_USER || 'nexa_admin';
  const dbName = env.POSTGRES_DB || 'nexa_senai_db';
  const backupDir = options.backupDir || BACKUP_DIR;
  const maxKeep = Number(options.retentionCount || env.BACKUP_RETENTION_COUNT || 7);
  const timestamp = formatTimestamp(options.date || new Date());

  fs.mkdirSync(backupDir, { recursive: true });

  const containerRunning = !options.forceOffline && isDockerContainerRunning(containerName);
  let backupFile;
  let mode;
  let stats;

  if (containerRunning) {
    mode = 'docker-pg_dump-custom';
    backupFile = path.join(backupDir, `nexa_backup_${timestamp}.dump`);
    const dumpBuffer = execSync(
      `docker exec ${containerName} pg_dump -U ${dbUser} -d ${dbName} -Fc -Z 9 --no-owner --no-acl`,
      { cwd: ROOT_DIR, maxBuffer: 256 * 1024 * 1024 }
    );
    fs.writeFileSync(backupFile, dumpBuffer);
    stats = { bytes: dumpBuffer.length };
  } else {
    mode = 'offline-logical-snapshot-gzip';
    backupFile = path.join(backupDir, `nexa_backup_${timestamp}.dump.gz`);
    const payload = buildOfflineLogicalDumpPayload();
    const compressed = zlib.gzipSync(Buffer.from(payload.fullSql, 'utf8'), { level: 9 });
    fs.writeFileSync(backupFile, compressed);
    stats = {
      bytes: compressed.length,
      migrationsCount: payload.migrationsCount,
      seedsCount: payload.seedsCount,
    };
  }

  const fileBuffer = fs.readFileSync(backupFile);
  const checksum = sha256Buffer(fileBuffer);
  const checksumFile = `${backupFile}.sha256`;
  fs.writeFileSync(checksumFile, `${checksum}  ${path.basename(backupFile)}\n`, 'utf8');

  const meta = {
    card: 'DB-048',
    mode,
    database: dbName,
    file: path.basename(backupFile),
    sha256: checksum,
    createdAt: new Date().toISOString(),
    retentionLimit: maxKeep,
    ...stats,
  };
  fs.writeFileSync(`${backupFile}.meta.json`, JSON.stringify(meta, null, 2) + '\n', 'utf8');

  const removed = rotateBackups(backupDir, maxKeep);

  return {
    backupFile,
    checksumFile,
    checksum,
    mode,
    removed,
    meta,
  };
}

if (require.main === module) {
  console.log('======================================================================');
  console.log('💾 NEXA DB BACKUP — BACKUP COMPRIMIDO & ROTAÇÃO AUTOMÁTICA (DB-048)');
  console.log('======================================================================\n');

  const result = runBackup();
  console.log(`  • Modo de execução : ${result.mode}`);
  console.log(`  • Arquivo gerado   : ${result.backupFile}`);
  console.log(`  • Checksum SHA-256 : ${result.checksum.slice(0, 16)}...`);
  console.log(`  • Tamanho          : ${result.meta.bytes} bytes`);
  if (result.removed.length > 0) {
    console.log(`  • Rotação (remov.) : ${result.removed.join(', ')}`);
  }
  console.log('\n✅ Backup concluído com sucesso!');
}

module.exports = { runBackup, rotateBackups, sha256Buffer };
