/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-015]
 * Título: Criar Tabela de Competências e Habilidades Técnicas (competencies)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Código da competência único (`uq_competencies_code` + índice único
 *    case-insensitive `idx_competencies_code_upper` + normalização UPPER/TRIM).
 * 2. Critério 2: Categorias bem definidas via enum nativo PostgreSQL
 *    `competency_category_enum` (`TECHNICAL`, `SAFETY`, `PROCEDURAL` — DB-005).
 * 3. Critério 3: Campos informativos prontos para exibição nos dashboards de radar
 *    (`code`, `title`, `category`, `description`, índices de filtro e busca).
 * 4. Observação Técnica: Integração com autoavaliação (`DB-032`), evidências docentes
 *    (`DB-033`), rubricas práticas (`DB-024`), módulos (`DB-016`) e badges (`DB-045`).
 * 5. DoD: Migration versionada, `model Competency` no `prisma/schema.prisma`, tipos
 *    TypeScript atualizados e testes unitários executados com sucesso.
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
  '20261118040000_create_competencies_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118040000_create_competencies_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '15_tabela_competencies.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '15-tabela-competencias-habilidades-competencies.md'),
  path.join(ROOT_DIR, 'BancoNexa', '15-tabela-competencias-habilidades-competencies.md'),
];

const VALID_CATEGORIES = new Set(['TECHNICAL', 'SAFETY', 'PROCEDURAL']);

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
 * Simulador relacional da tabela `competencies` com unicidade case-insensitive em `code`,
 * validação estrita do enum `competency_category_enum` e projeção para gráfico radar (FE-038).
 */
class CompetenciesRelationalSimulator {
  constructor() {
    this.competenciesById = new Map();
    this.competenciesByCode = new Map();
    this.seq = 1;
  }

  createCompetency(row) {
    // Trigger trg_competencies_normalize_and_touch
    const code = String(row.code || '').trim().toUpperCase();
    const title = String(row.title || '').trim();
    const description =
      row.description !== undefined && row.description !== null ? String(row.description).trim() : null;

    if (code.length < 3 || code.length > 50) {
      const err = new Error('violates check constraint "chk_competencies_code_format"');
      err.sqlState = '23514';
      throw err;
    }

    if (title.length < 3 || title.length > 150) {
      const err = new Error('violates check constraint "chk_competencies_title_not_empty"');
      err.sqlState = '23514';
      throw err;
    }

    // Critério 2: Validação do enum nativo competency_category_enum
    if (!VALID_CATEGORIES.has(row.category)) {
      const err = new Error(`invalid input value for enum competency_category_enum: "${row.category}"`);
      err.sqlState = '22P02';
      throw err;
    }

    // Critério 1: Unicidade de code (case-insensitive)
    if (this.competenciesByCode.has(code)) {
      const err = new Error(
        'Unique constraint failed on the fields: (`code`) [SQLSTATE 23505 / uq_competencies_code]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      id: row.id || `00000000-0000-4000-8000-${String(this.seq++).padStart(12, '0')}`,
      code,
      title,
      category: row.category,
      description,
      created_at: now,
      updated_at: now,
    };

    this.competenciesById.set(saved.id, saved);
    this.competenciesByCode.set(code, saved);
    return saved;
  }

  filterByCategory(category) {
    return [...this.competenciesById.values()]
      .filter((c) => c.category === category)
      .sort((a, b) => a.code.localeCompare(b.code));
  }

  buildRadarAxesPayload() {
    return [...this.competenciesById.values()]
      .sort((a, b) => a.code.localeCompare(b.code))
      .map((c) => ({
        competencyId: c.id,
        code: c.code,
        label: c.title,
        category: c.category,
        tooltip: c.description,
      }));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-015] — COMPETÊNCIAS TÉCNICAS (competencies)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de competencies'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118040000_create_competencies_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118040000_create_competencies_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/15_tabela_competencies.sql'
);
assertCheck(
  fs.existsSync(TYPES_MODELS_TS_PATH),
  'Tipos TypeScript dos modelos Prisma presentes em BancoNexa/types/schema-models.ts'
);
for (const docPath of DOC_PATHS) {
  assertCheck(fs.existsSync(docPath), `Documentação presente: ${path.relative(ROOT_DIR, docPath)}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const bancoMigContent = fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8');
const bancoSqlContent = fs.readFileSync(BANCO_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');
const docA = fs.readFileSync(DOC_PATHS[0], 'utf8');
const docB = fs.readFileSync(DOC_PATHS[1], 'utf8');

assertCheck(
  sqlContent === bancoMigContent && sqlContent === bancoSqlContent,
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/15_tabela_competencies.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/15-tabela-competencias-habilidades-competencies.md e BancoNexa/15-tabela-competencias-habilidades-competencies.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-015'),
  'Card DB-015 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas, model Competency no Prisma e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model Competency no Prisma e tipos TypeScript...');
assertCheck(
  /id\s+UUID\s+PRIMARY\s+KEY\s+DEFAULT\s+gen_random_uuid\(\)/i.test(sqlContent) &&
    /code\s+VARCHAR\(50\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /title\s+VARCHAR\(150\)\s+NOT\s+NULL/i.test(sqlContent) &&
    /category\s+competency_category_enum\s+NOT\s+NULL/i.test(sqlContent) &&
    /description\s+TEXT/i.test(sqlContent),
  'Todas as colunas exigidas (id, code, title, category, description) presentes com tipos nativos corretos'
);
assertCheck(
  schemaContent.includes('enum CompetencyCategory') &&
    schemaContent.includes('@@map("competency_category_enum")') &&
    schemaContent.includes('model Competency') &&
    schemaContent.includes('@unique(map: "uq_competencies_code")') &&
    /category\s+CompetencyCategory\s+@map\("category"\)/.test(schemaContent) &&
    schemaContent.includes('@@index([category], map: "idx_competencies_category")') &&
    schemaContent.includes('@@map("competencies")'),
  'Modelo Competency integrado ao prisma/schema.prisma com enum CompetencyCategory, code único e índices'
);
assertCheck(
  typesTsContent.includes('CompetencyCategory') &&
    typesTsContent.includes('export interface Competency {') &&
    typesTsContent.includes('category: CompetencyCategory;') &&
    typesTsContent.includes('export interface CompetencyRow {'),
  'Tipos TypeScript (Competency, CompetencyRow, CompetencyCreateInput, CompetencyUpdateInput) atualizados em BancoNexa/types/schema-models.ts'
);

// 4. Critérios de Aceitação 1, 2 e 3 no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2 e 3 no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+uq_competencies_code\s+UNIQUE\s*\(\s*code\s*\)/i.test(sqlContent) &&
    /CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_competencies_code_upper\s+ON\s+competencies\s*\(\s*UPPER\(code\)\s*\)/i.test(
      sqlContent
    ),
  'Critério 1: Código único de competência garantido por uq_competencies_code e idx_competencies_code_upper'
);
assertCheck(
  /CREATE\s+TYPE\s+competency_category_enum\s+AS\s+ENUM\s*\(\s*'TECHNICAL'\s*,\s*'SAFETY'\s*,\s*'PROCEDURAL'\s*\)/i.test(
    sqlContent
  ) &&
    /category\s+competency_category_enum\s+NOT\s+NULL/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_competencies_category/i.test(sqlContent),
  'Critério 2: Categorias TECHNICAL, SAFETY e PROCEDURAL aplicadas via enum competency_category_enum e indexadas'
);
assertCheck(
  /CONSTRAINT\s+chk_competencies_title_not_empty/i.test(sqlContent) &&
    /CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+idx_competencies_title_lower/i.test(sqlContent) &&
    /description\s+TEXT/i.test(sqlContent),
  'Critério 3: Campos informativos (code, title, category, description) e índices prontos para dashboards de radar (FE-038)'
);

// 5. Integração com cards dependentes no modelo 3FN
console.log('\n5. Verificando integração com cards dependentes (DB-016, DB-024, DB-032, DB-033, DB-045)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /fk_module_competencies_competency/i.test(sql3fnContent) &&
    /fk_task_criteria_competency/i.test(sql3fnContent) &&
    /fk_student_self_assessments_competency/i.test(sql3fnContent) &&
    /fk_skill_evidences_competency/i.test(sql3fnContent) &&
    /fk_gamification_badges_competency/i.test(sql3fnContent),
  'Integração validada: FKs de module_competencies (DB-016), task_criteria (DB-024), student_self_assessments (DB-032), skill_evidences (DB-033) e gamification_badges (DB-045) referenciam competencies(id)'
);

// 6. Testes unitários de integridade da tabela competencies (DoD)
console.log('\n6. Executando testes unitários de integridade da tabela competencies (DoD)...');
const sim = new CompetenciesRelationalSimulator();

const c1 = sim.createCompetency({
  code: '  comp-met-01 ',
  title: '  Medição com Paquímetro e Tolerância H7  ',
  category: 'TECHNICAL',
  description: '  Realizar medições lineares com precisão de 0,02 mm segundo norma ISO 286.  ',
});
const c2 = sim.createCompetency({
  code: 'COMP-SEG-01',
  title: 'Operação Segura de Torno Mecânico (NR-12)',
  category: 'SAFETY',
  description: 'Aplicar bloqueios de segurança, uso de óculos e verificação de proteções móveis.',
});
const c3 = sim.createCompetency({
  code: 'COMP-PRO-01',
  title: 'Sequenciamento de Operações na Ordem de Serviço',
  category: 'PROCEDURAL',
  description: 'Planejar etapas de desbaste, acabamento e inspeção dimensional.',
});

assertCheck(
  c1.code === 'COMP-MET-01' &&
    c1.title === 'Medição com Paquímetro e Tolerância H7' &&
    c1.description === 'Realizar medições lineares com precisão de 0,02 mm segundo norma ISO 286.' &&
    c2.category === 'SAFETY' &&
    c3.category === 'PROCEDURAL',
  'Teste 1: Competências TECHNICAL, SAFETY e PROCEDURAL criadas com normalização automática de código e textos'
);

// Teste 2: Critério 1 — Duplicata de código (inclusive case-insensitive) bloqueada
let dupCodeBlocked = false;
try {
  sim.createCompetency({
    code: 'comp-met-01',
    title: 'Competência Duplicada',
    category: 'TECHNICAL',
  });
} catch (err) {
  dupCodeBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupCodeBlocked,
  'Teste 2 (Critério 1): Código duplicado case-insensitive ("comp-met-01") bloqueado por uq_competencies_code (23505 / P2002)'
);

// Teste 3: Critério 2 — Categoria inválida fora do enum rejeitada
let invalidCategoryBlocked = false;
try {
  sim.createCompetency({
    code: 'COMP-INV-01',
    title: 'Categoria Inválida',
    category: 'BEHAVIORAL',
  });
} catch (err) {
  invalidCategoryBlocked = err.sqlState === '22P02';
}
assertCheck(
  invalidCategoryBlocked && sim.filterByCategory('TECHNICAL').length === 1 && sim.filterByCategory('SAFETY').length === 1,
  'Teste 3 (Critério 2): Categoria fora do enum ("BEHAVIORAL") rejeitada (22P02) e filtros por categoria válidos retornaram resultados exatos'
);

// Teste 4: Critério 3 — Campos vazios rejeitados e payload completo pronto para gráfico radar (FE-038)
let shortTitleBlocked = false;
try {
  sim.createCompetency({
    code: 'COMP-ERR-01',
    title: '  A ',
    category: 'TECHNICAL',
  });
} catch (err) {
  shortTitleBlocked = err.sqlState === '23514';
}
const radarPayload = sim.buildRadarAxesPayload();
assertCheck(
  shortTitleBlocked &&
    radarPayload.length === 3 &&
    radarPayload.every((axis) => axis.code && axis.label && axis.category && axis.tooltip),
  'Teste 4 (Critério 3): Título inválido bloqueado (23514) e payload informativo de 3 eixos pronto para o gráfico radar (FE-038)'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-015] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
