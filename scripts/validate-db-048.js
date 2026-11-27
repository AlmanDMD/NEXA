/**
 * Script de Validação Automatizada — Card [DB-048]
 * Título: Implementar Rotina de Backup Automatizado e Script de Restauração (pg_dump/restore)
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { runBackup } = require('./db-backup');
const { runRestore } = require('./db-restore');

const ROOT_DIR = path.resolve(__dirname, '..');
const GITIGNORE_PATH = path.join(ROOT_DIR, '.gitignore');
const BACKUP_SH_PATH = path.join(ROOT_DIR, 'scripts', 'db-backup.sh');
const RESTORE_SH_PATH = path.join(ROOT_DIR, 'scripts', 'db-restore.sh');
const BACKUP_JS_PATH = path.join(ROOT_DIR, 'scripts', 'db-backup.js');
const RESTORE_JS_PATH = path.join(ROOT_DIR, 'scripts', 'db-restore.js');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '48-rotina-backup-restore-pg-dump.md'),
  path.join(ROOT_DIR, 'BancoNexa', '48-rotina-backup-restore-pg-dump.md'),
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
console.log('🧪 VALIDAÇÃO DO CARD [DB-048] — BACKUP COMPRIMIDO & RESTAURAÇÃO');
console.log('======================================================================\n');

const gitignore = fs.readFileSync(GITIGNORE_PATH, 'utf8');
const backupSh = fs.readFileSync(BACKUP_SH_PATH, 'utf8');
const restoreSh = fs.readFileSync(RESTORE_SH_PATH, 'utf8');

assertCheck(
  /backups\//i.test(gitignore),
  'Critério 1: Pasta backups/ ignorada no .gitignore'
);
assertCheck(
  fs.existsSync(BACKUP_SH_PATH) &&
    fs.existsSync(RESTORE_SH_PATH) &&
    fs.existsSync(BACKUP_JS_PATH) &&
    fs.existsSync(RESTORE_JS_PATH) &&
    /pg_dump[\s\S]*-Fc/i.test(backupSh) &&
    /pg_restore[\s\S]*--clean/i.test(restoreSh),
  'Scripts Bash (.sh) e Node (.js) de pg_dump (-Fc) e pg_restore presentes e válidos'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-048') &&
    fs.readFileSync(DOC_PATHS[0], 'utf8').includes('DOC-017'),
  'Critério 3: Procedimento de backup/restore documentado e alinhado a DOC-017'
);

// Teste end-to-end em diretório temporário: 9 backups -> rotação mantém exatamente 7 + restore íntegro
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'nexa-db048-'));
try {
  let latest;
  for (let i = 0; i < 9; i++) {
    const fakeDate = new Date(Date.UTC(2026, 10, 20 + i, 3, 0, i));
    latest = runBackup({ backupDir: tmpDir, retentionCount: 7, forceOffline: true, date: fakeDate });
  }
  const remaining = fs.readdirSync(tmpDir).filter((f) => /^nexa_backup_.*\.dump(\.gz)?$/.test(f));
  assertCheck(
    remaining.length === 7 && fs.existsSync(latest.checksumFile),
    `Teste 1 (Rotação): Após 9 execuções, exatamente ${remaining.length} backups recentes + .sha256 foram retidos`
  );

  const restoreRes = runRestore({ backupDir: tmpDir, backupFile: latest.backupFile, forceOffline: true });
  assertCheck(
    restoreRes.checksum.verified === true &&
      restoreRes.integrity.totalTables >= 32 &&
      restoreRes.integrity.totalViews === 3 &&
      restoreRes.integrity.totalTriggers >= 15,
    `Teste 2 (Critério 2 — Restore): SHA-256 validado e integridade pós-restore confirmada (${restoreRes.integrity.totalTables} tabelas, ${restoreRes.integrity.totalViews} views, ${restoreRes.integrity.totalTriggers} triggers)`
  );
} finally {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-048] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
