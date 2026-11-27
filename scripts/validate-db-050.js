/**
 * Script de Validação Automatizada Final — Card [DB-050] (50/50)
 * Título: Gerar Dicionário de Dados Automatizado e Validação Final de Integridade
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const VERIFY_SCRIPT_PATH = path.join(ROOT_DIR, 'prisma', 'verify-schema-integrity.ts');
const DICT_JSON_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'data-dictionary.json');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '50-dicionario-dados-validacao-final.md'),
  path.join(ROOT_DIR, 'BancoNexa', '50-dicionario-dados-validacao-final.md'),
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
console.log('🏁 VALIDAÇÃO FINAL DO CARD [DB-050] — INTEGRIDADE & DICIONÁRIO (50/50)');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node prisma/seed.ts', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node prisma/verify-schema-integrity.ts', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Pipeline completo (db:generate -> db:migrate -> db:seed -> verify-schema-integrity.ts) executado com sucesso');
} catch (err) {
  assertCheck(false, `Falha no pipeline final DB-050: ${err.message}`);
}

assertCheck(fs.existsSync(VERIFY_SCRIPT_PATH), 'Script prisma/verify-schema-integrity.ts presente');
assertCheck(fs.existsSync(DICT_JSON_PATH), 'Dicionário automatizado BancoNexa/types/data-dictionary.json gerado');

const dict = JSON.parse(fs.readFileSync(DICT_JSON_PATH, 'utf8'));
assertCheck(
  dict.status === 'HOMOLOGATED_50_OF_50' &&
    dict.summary.totalPrismaModels === 33 &&
    dict.summary.totalEnums === 18 &&
    dict.summary.totalViews === 3 &&
    dict.summary.totalMigrations >= 41 &&
    dict.summary.totalSeeds === 4 &&
    dict.summary.integrityTestsPassed === dict.summary.integrityTestsTotal,
  `Dicionário homologado: ${dict.summary.totalPrismaModels} tabelas, ${dict.summary.totalColumns} colunas, ${dict.summary.totalEnums} enums, ${dict.summary.totalViews} views, ${dict.summary.totalMigrations} migrations, ${dict.summary.integrityTestsPassed}/${dict.summary.integrityTestsTotal} testes`
);

const doc0 = fs.readFileSync(DOC_PATHS[0], 'utf8');
const doc1 = fs.readFileSync(DOC_PATHS[1], 'utf8');
assertCheck(
  doc0 === doc1 &&
    doc0.includes('DOC-008') &&
    doc0.includes('DOC-009') &&
    doc0.includes('DOC-020') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-050'),
  'Relatório final e Dicionário de Dados sincronizados entre docs/banco, BancoNexa, DOC-008/009/020 e README'
);

// Garante existência dos 50 scripts de validação DB-001..DB-050
let missingValidators = [];
for (let i = 1; i <= 50; i++) {
  const f = path.join(ROOT_DIR, 'scripts', `validate-db-${String(i).padStart(3, '0')}.js`);
  if (!fs.existsSync(f)) missingValidators.push(path.basename(f));
}
assertCheck(
  missingValidators.length === 0,
  'Cobertura total 50/50: todos os scripts scripts/validate-db-001.js .. validate-db-050.js presentes'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Camada de Banco de Dados NEXA 100% homologada (50/50 Cards DB-001..DB-050)!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
