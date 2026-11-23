/**
 * Script de Validação Automatizada e Testes de Idempotência — Card [DB-020]
 * Título: Criar Seed de Estrutura Curricular SENAI (Mecânica e Metrologia)
 *
 * Verifica programaticamente:
 * 1. Existência de `prisma/seed.ts`, `BancoNexa/sql/20_seed_estrutura_curricular_senai.sql`,
 *    script `"db:seed"` no `package.json` e documentação sincronizada.
 * 2. Critério 1: Execução idempotente (`npm run db:seed` executado 2x consecutivas sem erro,
 *    sem duplicação e produzindo SQL UPSERT determinístico com `ON CONFLICT ... DO UPDATE`).
 * 3. Critério 2: Grade curricular SENAI coerente:
 *    - 1 Curso Técnico em Mecânica Industrial
 *    - 2 Turmas (`MEC-2026-1` e `MEC-2026-2`)
 *    - 4 Disciplinas (`Metrologia`, `Desenho Técnico Mecânico`, `Usinagem Convencional`, `Segurança do Trabalho`)
 *    - 8 Módulos práticos sequenciais
 *    - 15 Competências industriais
 * 4. Critério 3: Todas as 15 competências vinculadas aos 8 módulos práticos em `module_competencies`.
 * 5. Observação Técnica: Dados 100% anônimos e fictícios (domínios `.nexa.local`, zero PII real).
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SEED_TS_PATH = path.join(ROOT_DIR, 'prisma', 'seed.ts');
const SEED_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '20_seed_estrutura_curricular_senai.sql');
const PACKAGE_JSON_PATH = path.join(ROOT_DIR, 'package.json');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '20-seed-estrutura-curricular-senai.md'),
  path.join(ROOT_DIR, 'BancoNexa', '20-seed-estrutura-curricular-senai.md'),
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

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-020] — SEED CURRICULAR SENAI (MECÂNICA)');
console.log('======================================================================\n');

// 1. Verificar existência dos artefatos e configuração do comando npm run db:seed
console.log('1. Verificando arquivos de seed, package.json e documentação...');
assertCheck(fs.existsSync(SEED_TS_PATH), 'Script prisma/seed.ts presente');
const pkg = JSON.parse(fs.readFileSync(PACKAGE_JSON_PATH, 'utf8'));
assertCheck(
  Boolean(pkg.scripts && pkg.scripts['db:seed'] && pkg.scripts['db:seed'].includes('prisma/seed.ts')),
  'Script "db:seed" configurado em package.json apontando para prisma/seed.ts'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8'),
  'Sincronia 100% idêntica entre docs/banco/20-seed-estrutura-curricular-senai.md e BancoNexa/20-seed-estrutura-curricular-senai.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-020'),
  'Card DB-020 documentado em BancoNexa/README.md'
);

// 2. Critério 1 & DoD: Executar `node prisma/seed.ts` 2 vezes seguidas comprovando idempotência
console.log('\n2. Verificando Critério 1 e DoD (execução repetida idempotente via UPSERT)...');
let run1Out = '';
let run2Out = '';
let sqlRun1 = '';
let sqlRun2 = '';
try {
  run1Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  sqlRun1 = fs.readFileSync(SEED_SQL_PATH, 'utf8');
  run2Out = execSync('node prisma/seed.ts', { cwd: ROOT_DIR, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  sqlRun2 = fs.readFileSync(SEED_SQL_PATH, 'utf8');
  assertCheck(
    run1Out.includes('DB-020 SUCESSO') && run2Out.includes('DB-020 SUCESSO') && sqlRun1 === sqlRun2,
    'Critério 1 & DoD: `npm run db:seed` executou 2x consecutivas com código 0 e resultado determinístico/idempotente'
  );
} catch (err) {
  assertCheck(false, `Falha ao executar prisma/seed.ts: ${err.message}`);
}

const seedSql = fs.existsSync(SEED_SQL_PATH) ? fs.readFileSync(SEED_SQL_PATH, 'utf8') : '';
const upsertCount = (seedSql.match(/ON\s+CONFLICT\s*\([^)]+\)\s+DO\s+UPDATE/gi) || []).length;
assertCheck(
  upsertCount >= 70,
  `Instruções SQL UPSERT (ON CONFLICT ... DO UPDATE) verificadas: ${upsertCount} upserts idempotentes`
);

// 3. Critério 2: Verificar quantidades exatas da estrutura curricular SENAI solicitada
console.log('\n3. Verificando Critério 2 (1 curso, 2 turmas, 4 disciplinas, 8 módulos, 15 competências)...');
const courseInserts = (seedSql.match(/INSERT\s+INTO\s+courses\b/gi) || []).length;
const classInserts = (seedSql.match(/INSERT\s+INTO\s+classes\b/gi) || []).length;
const subjectInserts = (seedSql.match(/INSERT\s+INTO\s+subjects\b/gi) || []).length;
const moduleInserts = (seedSql.match(/INSERT\s+INTO\s+learning_modules\b/gi) || []).length;
const compInserts = (seedSql.match(/INSERT\s+INTO\s+competencies\b/gi) || []).length;
const modCompInserts = (seedSql.match(/INSERT\s+INTO\s+module_competencies\b/gi) || []).length;
const enrollmentInserts = (seedSql.match(/INSERT\s+INTO\s+enrollments\b/gi) || []).length;
const teacherAssignInserts = (seedSql.match(/INSERT\s+INTO\s+teacher_assignments\b/gi) || []).length;

assertCheck(
  courseInserts === 1 && seedSql.includes('Curso Técnico em Mecânica Industrial'),
  `Curso Técnico em Mecânica Industrial configurado (${courseInserts}/1)`
);
assertCheck(
  classInserts === 2 && seedSql.includes("'MEC-2026-1'") && seedSql.includes("'MEC-2026-2'"),
  `2 Turmas SENAI configuradas: MEC-2026-1 e MEC-2026-2 (${classInserts}/2)`
);
assertCheck(
  subjectInserts === 4 &&
    seedSql.includes("'Metrologia'") &&
    seedSql.includes("'Desenho Técnico Mecânico'") &&
    seedSql.includes("'Usinagem Convencional'") &&
    seedSql.includes("'Segurança do Trabalho'"),
  `4 Disciplinas obrigatórias configuradas (Metrologia, Desenho Técnico Mecânico, Usinagem Convencional, Segurança do Trabalho) (${subjectInserts}/4)`
);
assertCheck(moduleInserts === 8, `8 Módulos práticos sequenciais configurados (${moduleInserts}/8)`);
assertCheck(compInserts === 15, `15 Competências industriais configuradas (${compInserts}/15)`);
assertCheck(
  enrollmentInserts >= 6 && teacherAssignInserts >= 8,
  `Integração Lote 2: ${enrollmentInserts} matrículas (DB-017) e ${teacherAssignInserts} alocações docentes (DB-018) populadas`
);

// 4. Critério 3: Todas as 15 competências vinculadas aos módulos em module_competencies
console.log('\n4. Verificando Critério 3 (vínculo real de todas as 15 competências aos 8 módulos)...');
const compCodes = [...seedSql.matchAll(/INSERT\s+INTO\s+competencies[\s\S]*?VALUES\s*\('([A-Z0-9-]+)'/g)].map(
  (m) => m[1]
);
const linkedCodes = new Set(
  [...seedSql.matchAll(/INSERT\s+INTO\s+module_competencies[\s\S]*?cp\.code\s*=\s*'([A-Z0-9-]+)'/g)].map((m) => m[1])
);
const unlinked = compCodes.filter((code) => !linkedCodes.has(code));
assertCheck(
  modCompInserts >= 20 && compCodes.length === 15 && unlinked.length === 0,
  `Critério 3: ${modCompInserts} vínculos N:M criados cobrindo 15/15 competências industriais (0 competências órfãs)`
);

// 5. Observação Técnica: Dados 100% anônimos e fictícios (zero dados pessoais reais)
console.log('\n5. Verificando Observação Técnica (dados 100% anônimos e fictícios)...');
const emails = [...seedSql.matchAll(/INSERT\s+INTO\s+users[\s\S]*?VALUES\s*\('([^']+)'/g)].map((m) => m[1]);
const allLocalDemoEmails = emails.length >= 6 && emails.every((e) => e.endsWith('.nexa.local'));
const hasNoRealEmailDomains = !/@(gmail|hotmail|outlook|yahoo|icloud)\./i.test(seedSql);
assertCheck(
  allLocalDemoEmails && hasNoRealEmailDomains,
  `Observação Técnica: Todos os ${emails.length} e-mails são fictícios (*.nexa.local), sem domínios ou dados pessoais reais`
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-020] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
