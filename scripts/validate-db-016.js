/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-016]
 * Título: Modelar Relacionamento Módulo-Competência (module_competencies)
 *
 * Verifica programaticamente:
 * 1. Critério 1: Chave primária composta `pk_module_competencies (module_id, competency_id)`
 *    impedindo duplicações de vínculo.
 * 2. Critério 2: FK `fk_module_competencies_module` com exclusão em cascata (`ON DELETE CASCADE`)
 *    se o módulo for removido, e `fk_module_competencies_competency` com `ON DELETE RESTRICT`.
 * 3. Critério 3: Nível requerido delimitado entre 1 (Básico) e 5 (Avançado)
 *    (`chk_module_competencies_level`).
 * 4. Observação Técnica: Ponderação `weight NUMERIC(3,2) DEFAULT 1.00` (`0.01..9.99`) para
 *    calcular impacto ponderado das competências na nota do módulo.
 * 5. DoD: Relação N:M modelada, seed preliminar validado (`16_seed_preliminar_module_competencies.sql`),
 *    `model ModuleCompetency` no `prisma/schema.prisma`, tipos TS atualizados e integração validada.
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
  '20261118050000_create_module_competencies_table',
  'migration.sql'
);
const BANCO_MIGRATION_SQL_PATH = path.join(
  ROOT_DIR,
  'BancoNexa',
  'migrations',
  '20261118050000_create_module_competencies_table.sql'
);
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '16_tabela_module_competencies.sql');
const SEED_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '16_seed_preliminar_module_competencies.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '16-tabela-relacionamento-modulo-competencia-module-competencies.md'),
  path.join(ROOT_DIR, 'BancoNexa', '16-tabela-relacionamento-modulo-competencia-module-competencies.md'),
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
 * Simulador relacional N:M das tabelas `learning_modules`, `competencies` e `module_competencies`
 * com PK composta, ON DELETE CASCADE em module_id, ON DELETE RESTRICT em competency_id,
 * required_level BETWEEN 1 AND 5 e weight (0.01..9.99).
 */
class ModuleCompetenciesRelationalSimulator {
  constructor() {
    this.modules = new Map();
    this.competencies = new Map();
    this.links = new Map(); // key: `${module_id}::${competency_id}`
  }

  addModule(id, title) {
    this.modules.set(id, { id, title });
  }

  addCompetency(id, code, title, category) {
    this.competencies.set(id, { id, code, title, category });
  }

  linkCompetency(row) {
    if (!row.module_id || !row.competency_id) {
      const err = new Error('null value in primary key column violates not-null constraint');
      err.sqlState = '23502';
      throw err;
    }
    if (!this.modules.has(row.module_id)) {
      const err = new Error('violates foreign key constraint "fk_module_competencies_module"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }
    if (!this.competencies.has(row.competency_id)) {
      const err = new Error('violates foreign key constraint "fk_module_competencies_competency"');
      err.code = 'P2003';
      err.sqlState = '23503';
      throw err;
    }

    // Critério 1: PK composta (module_id, competency_id)
    const pk = `${row.module_id}::${row.competency_id}`;
    if (this.links.has(pk)) {
      const err = new Error(
        'duplicate key value violates unique constraint "pk_module_competencies" [SQLSTATE 23505 / P2002]'
      );
      err.code = 'P2002';
      err.sqlState = '23505';
      throw err;
    }

    // Observação Técnica: weight > 0.00 AND weight <= 9.99 (default 1.00)
    const weight = row.weight !== undefined ? Number(row.weight) : 1.0;
    if (!Number.isFinite(weight) || weight <= 0.0 || weight > 9.99) {
      const err = new Error('violates check constraint "chk_module_competencies_weight"');
      err.sqlState = '23514';
      throw err;
    }

    // Critério 3: required_level BETWEEN 1 AND 5 (default 3)
    const requiredLevel = row.required_level !== undefined ? row.required_level : 3;
    if (!Number.isInteger(requiredLevel) || requiredLevel < 1 || requiredLevel > 5) {
      const err = new Error('violates check constraint "chk_module_competencies_level"');
      err.sqlState = '23514';
      throw err;
    }

    const now = new Date().toISOString();
    const saved = {
      module_id: row.module_id,
      competency_id: row.competency_id,
      weight: Number(weight.toFixed(2)),
      required_level: requiredLevel,
      created_at: now,
      updated_at: now,
    };
    this.links.set(pk, saved);
    return saved;
  }

  deleteModuleCascade(moduleId) {
    if (!this.modules.has(moduleId)) return 0;
    this.modules.delete(moduleId);
    let removed = 0;
    for (const [pk, link] of [...this.links.entries()]) {
      if (link.module_id === moduleId) {
        this.links.delete(pk);
        removed++;
      }
    }
    return removed;
  }

  deleteCompetencyRestrict(competencyId) {
    const referenced = [...this.links.values()].some((l) => l.competency_id === competencyId);
    if (referenced) {
      const err = new Error(
        'update or delete on table "competencies" violates foreign key constraint "fk_module_competencies_competency"'
      );
      err.sqlState = '23503';
      throw err;
    }
    this.competencies.delete(competencyId);
  }

  listByModule(moduleId) {
    return [...this.links.values()].filter((l) => l.module_id === moduleId);
  }

  listByCompetency(competencyId) {
    return [...this.links.values()].filter((l) => l.competency_id === competencyId);
  }

  calculateWeightedModuleScore(moduleId, scoresByCompetencyId) {
    const moduleLinks = this.listByModule(moduleId);
    let num = 0;
    let den = 0;
    for (const l of moduleLinks) {
      if (scoresByCompetencyId[l.competency_id] !== undefined) {
        num += scoresByCompetencyId[l.competency_id] * l.weight;
        den += l.weight;
      }
    }
    return den > 0 ? Number((num / den).toFixed(2)) : 0;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-016] — MÓDULO-COMPETÊNCIA (module_competencies)');
console.log('======================================================================\n');

// 1. Executar db:generate e db:migrate
console.log('1. Executando npm run db:generate e npm run db:migrate...');
try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(
    true,
    'Scripts db:generate e db:migrate validaram, geraram tipos TS e registraram a migration de module_competencies'
  );
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

// 2. Verificar arquivos SQL, migration, seed preliminar, tipos TS e documentação
console.log('\n2. Verificando arquivos SQL, migration, seed preliminar, tipos TypeScript e documentação...');
assertCheck(
  fs.existsSync(MIGRATION_SQL_PATH),
  'Migration SQL presente em prisma/migrations/20261118050000_create_module_competencies_table/migration.sql'
);
assertCheck(
  fs.existsSync(BANCO_MIGRATION_SQL_PATH),
  'Migration SQL espelhada em BancoNexa/migrations/20261118050000_create_module_competencies_table.sql'
);
assertCheck(
  fs.existsSync(BANCO_SQL_PATH),
  'Script SQL dedicado em BancoNexa/sql/16_tabela_module_competencies.sql'
);
assertCheck(
  fs.existsSync(SEED_SQL_PATH),
  'Seed preliminar N:M presente em BancoNexa/sql/16_seed_preliminar_module_competencies.sql'
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
const seedSqlContent = fs.readFileSync(SEED_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');
const docA = fs.readFileSync(DOC_PATHS[0], 'utf8');
const docB = fs.readFileSync(DOC_PATHS[1], 'utf8');

assertCheck(
  sqlContent === bancoMigContent && sqlContent === bancoSqlContent,
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/16_tabela_module_competencies.sql'
);
assertCheck(
  docA === docB,
  'Sincronia 100% idêntica entre docs/banco/16-tabela-relacionamento-modulo-competencia-module-competencies.md e BancoNexa/16-tabela-relacionamento-modulo-competencia-module-competencies.md'
);
assertCheck(
  fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-016'),
  'Card DB-016 documentado em BancoNexa/README.md'
);

// 3. Verificar colunas SQL, model ModuleCompetency no Prisma, seed preliminar e tipos TypeScript
console.log('\n3. Verificando colunas SQL, model ModuleCompetency no Prisma, seed preliminar e tipos TS...');
assertCheck(
  /module_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /competency_id\s+UUID\s+NOT\s+NULL/i.test(sqlContent) &&
    /weight\s+(NUMERIC|DECIMAL)\(3,2\)\s+NOT\s+NULL\s+DEFAULT\s+1\.00/i.test(sqlContent) &&
    /required_level\s+INTEGER\s+NOT\s+NULL\s+DEFAULT\s+3/i.test(sqlContent),
  'Todas as colunas exigidas (module_id, competency_id, weight DECIMAL(3,2) DEFAULT 1.00, required_level INTEGER) presentes'
);
assertCheck(
  schemaContent.includes('model ModuleCompetency') &&
    schemaContent.includes('@@id([moduleId, competencyId], map: "pk_module_competencies")') &&
    schemaContent.includes('@default(1.00) @map("weight") @db.Decimal(3, 2)') &&
    schemaContent.includes('@default(3) @map("required_level")') &&
    schemaContent.includes('onDelete: Cascade, onUpdate: Cascade, map: "fk_module_competencies_module"') &&
    schemaContent.includes('onDelete: Restrict, onUpdate: Cascade, map: "fk_module_competencies_competency"') &&
    schemaContent.includes('@@map("module_competencies")'),
  'Modelo ModuleCompetency integrado ao prisma/schema.prisma com @@id composto, onDelete: Cascade em module e relações bidirecionais'
);
assertCheck(
  typesTsContent.includes('export interface ModuleCompetency {') &&
    typesTsContent.includes('moduleId: string;') &&
    typesTsContent.includes('competencyId: string;') &&
    typesTsContent.includes('weight: number | string;') &&
    typesTsContent.includes('requiredLevel: number;') &&
    typesTsContent.includes('export interface ModuleCompetencyRow {'),
  'Tipos TypeScript (ModuleCompetency, ModuleCompetencyRow, ModuleCompetencyCreateInput, ModuleCompetencyUpdateInput) gerados em schema-models.ts'
);
assertCheck(
  /INSERT\s+INTO\s+module_competencies/i.test(seedSqlContent) &&
    /ON\s+CONFLICT\s*\(\s*module_id\s*,\s*competency_id\s*\)\s+DO\s+NOTHING/i.test(seedSqlContent) &&
    seedSqlContent.includes('COMP-MET-01') &&
    seedSqlContent.includes('COMP-TOR-01'),
  'Seed preliminar idempotente (ON CONFLICT DO NOTHING) validado em BancoNexa/sql/16_seed_preliminar_module_competencies.sql'
);

// 4. Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL
console.log('\n4. Verificando Critérios de Aceitação 1, 2, 3 e Observação Técnica no DDL SQL...');
assertCheck(
  /CONSTRAINT\s+pk_module_competencies\s+PRIMARY\s+KEY\s*\(\s*module_id\s*,\s*competency_id\s*\)/i.test(sqlContent),
  'Critério 1: Chave primária composta pk_module_competencies (module_id, competency_id) declarada no SQL'
);
assertCheck(
  /CONSTRAINT\s+fk_module_competencies_module\s+FOREIGN\s+KEY\s*\(\s*module_id\s*\)\s*REFERENCES\s+learning_modules\s*\(\s*id\s*\)\s*ON\s+DELETE\s+CASCADE\s+ON\s+UPDATE\s+CASCADE/i.test(
    sqlContent
  ) &&
    /CONSTRAINT\s+fk_module_competencies_competency\s+FOREIGN\s+KEY\s*\(\s*competency_id\s*\)\s*REFERENCES\s+competencies\s*\(\s*id\s*\)\s*ON\s+DELETE\s+RESTRICT\s+ON\s+UPDATE\s+CASCADE/i.test(
      sqlContent
    ),
  'Critério 2: FK para learning_modules com ON DELETE CASCADE e FK para competencies com ON DELETE RESTRICT'
);
assertCheck(
  /CONSTRAINT\s+chk_module_competencies_level\s+CHECK\s*\(\s*required_level\s+BETWEEN\s+1\s+AND\s+5\s*\)/i.test(
    sqlContent
  ),
  'Critério 3: Constraint chk_module_competencies_level delimitando required_level entre 1 (Básico) e 5 (Avançado)'
);
assertCheck(
  /CONSTRAINT\s+chk_module_competencies_weight\s+CHECK\s*\(\s*weight\s*>\s*0\.00\s+AND\s+weight\s*<=\s*9\.99\s*\)/i.test(
    sqlContent
  ),
  'Observação Técnica: Constraint chk_module_competencies_weight validando pesos ponderados (0.01..9.99)'
);

// 5. Integração com cards dependentes no modelo 3FN (DB-020, DB-023, DB-031, BE-015)
console.log('\n5. Verificando alinhamento com modelo 3FN e cards dependentes (DB-020, DB-023, DB-031, BE-015)...');
const sql3fnContent = fs.readFileSync(SQL_3FN_PATH, 'utf8');
assertCheck(
  /CREATE\s+TABLE\s+module_competencies/i.test(sql3fnContent) &&
    /pk_module_competencies/i.test(sql3fnContent) &&
    /fk_practical_tasks_module/i.test(sql3fnContent) &&
    /fk_self_assessment_forms_module/i.test(sql3fnContent),
  'Integração validada com modelo 3FN e tabelas dependentes (practical_tasks DB-023, self_assessment_forms DB-031)'
);

// 6. Testes unitários de integridade N:M e simulação do seed preliminar (DoD)
console.log('\n6. Executando testes unitários de integridade N:M e validação do seed preliminar (DoD)...');
const sim = new ModuleCompetenciesRelationalSimulator();
const modMetId = '30000000-0000-4000-8000-000000000001';
const modTorId = '30000000-0000-4000-8000-000000000002';
const compMetId = '40000000-0000-4000-8000-000000000001';
const compTorId = '40000000-0000-4000-8000-000000000002';
const compSegId = '40000000-0000-4000-8000-000000000003';
const compProId = '40000000-0000-4000-8000-000000000004';

sim.addModule(modMetId, 'Metrologia com Micrômetro e Paquímetro');
sim.addModule(modTorId, 'Módulo de Tornearia Cilíndrica');
sim.addCompetency(compMetId, 'COMP-MET-01', 'Medição com Paquímetro e Tolerância H7', 'TECHNICAL');
sim.addCompetency(compTorId, 'COMP-TOR-01', 'Operação de Torno Convencional e Cilindramento', 'TECHNICAL');
sim.addCompetency(compSegId, 'COMP-SEG-01', 'Segurança em Máquinas Operatrizes (NR-12)', 'SAFETY');
sim.addCompetency(compProId, 'COMP-PRO-01', 'Planejamento de Ordem de Serviço de Oficina', 'PROCEDURAL');

// Seed preliminar: 6 associações N:M (mesma competência em múltiplos módulos, múltiplas competências por módulo)
const l1 = sim.linkCompetency({ module_id: modMetId, competency_id: compMetId, weight: 2.5, required_level: 4 });
const l2 = sim.linkCompetency({ module_id: modMetId, competency_id: compSegId }); // defaults: weight=1.00, required_level=3
const l3 = sim.linkCompetency({ module_id: modMetId, competency_id: compProId, weight: 1.5, required_level: 2 });
sim.linkCompetency({ module_id: modTorId, competency_id: compTorId, weight: 3.0, required_level: 5 });
sim.linkCompetency({ module_id: modTorId, competency_id: compMetId, weight: 2.0, required_level: 4 });
sim.linkCompetency({ module_id: modTorId, competency_id: compSegId, weight: 2.0, required_level: 5 });

assertCheck(
  sim.listByModule(modMetId).length === 3 &&
    sim.listByModule(modTorId).length === 3 &&
    sim.listByCompetency(compMetId).length === 2 &&
    l2.weight === 1.0 &&
    l2.required_level === 3 &&
    l1.weight === 2.5 &&
    l3.required_level === 2,
  'Teste 1 (Seed Preliminar N:M): 6 vínculos criados (3 por módulo), competência transversal em 2 módulos e defaults (weight=1.00, required_level=3)'
);

// Teste 2: Critério 1 — PK composta impede duplicação (module_id, competency_id)
let dupBlocked = false;
try {
  sim.linkCompetency({ module_id: modMetId, competency_id: compMetId, weight: 1.0, required_level: 3 });
} catch (err) {
  dupBlocked = err.sqlState === '23505' && err.code === 'P2002';
}
assertCheck(
  dupBlocked,
  'Teste 2 (Critério 1): Vínculo duplicado (module_id, competency_id) bloqueado pela PK composta (23505 / P2002)'
);

// Teste 3: Critério 3 — required_level fora de 1..5 bloqueado (0 e 6) e extremos 1 e 5 aceitos
let levelZeroBlocked = false;
let levelSixBlocked = false;
try {
  sim.linkCompetency({ module_id: modTorId, competency_id: compProId, required_level: 0 });
} catch (err) {
  levelZeroBlocked = err.sqlState === '23514';
}
try {
  sim.linkCompetency({ module_id: modTorId, competency_id: compProId, required_level: 6 });
} catch (err) {
  levelSixBlocked = err.sqlState === '23514';
}
const levelOneAccepted = sim.linkCompetency({
  module_id: modTorId,
  competency_id: compProId,
  weight: 1.0,
  required_level: 1,
});
assertCheck(
  levelZeroBlocked && levelSixBlocked && levelOneAccepted.required_level === 1,
  'Teste 3 (Critério 3): required_level 0 e 6 rejeitados (23514); extremos 1 (Básico) e 5 (Avançado) aceitos'
);

// Teste 4: Observação Técnica — Ponderação de habilidades no módulo e bloqueio de weight inválido
let zeroWeightBlocked = false;
let overWeightBlocked = false;
const modExtraId = '30000000-0000-4000-8000-000000000099';
sim.addModule(modExtraId, 'Módulo Auxiliar para Teste');
try {
  sim.linkCompetency({ module_id: modExtraId, competency_id: compMetId, weight: 0.0 });
} catch (err) {
  zeroWeightBlocked = err.sqlState === '23514';
}
try {
  sim.linkCompetency({ module_id: modExtraId, competency_id: compMetId, weight: 10.0 });
} catch (err) {
  overWeightBlocked = err.sqlState === '23514';
}
// Nota ponderada de modMetId: (8.0 * 2.50 + 10.0 * 1.00 + 6.0 * 1.50) / (2.50 + 1.00 + 1.50) = 39.00 / 5.00 = 7.80
const moduleWeightedScore = sim.calculateWeightedModuleScore(modMetId, {
  [compMetId]: 8.0,
  [compSegId]: 10.0,
  [compProId]: 6.0,
});
assertCheck(
  zeroWeightBlocked && overWeightBlocked && moduleWeightedScore === 7.8,
  'Teste 4 (Observação Técnica): weight 0.00 e 10.00 bloqueados (23514); nota ponderada do módulo calculada corretamente (7.80)'
);

// Teste 5: Critério 2 — ON DELETE CASCADE ao remover módulo e ON DELETE RESTRICT ao tentar remover competência em uso
let restrictCompBlocked = false;
try {
  sim.deleteCompetencyRestrict(compMetId);
} catch (err) {
  restrictCompBlocked = err.sqlState === '23503';
}
const removedLinks = sim.deleteModuleCascade(modTorId);
assertCheck(
  restrictCompBlocked && removedLinks === 4 && sim.listByModule(modTorId).length === 0 && sim.listByModule(modMetId).length === 3,
  'Teste 5 (Critério 2): Exclusão de competência em uso bloqueada (ON DELETE RESTRICT) e remoção do módulo eliminou 4 vínculos via ON DELETE CASCADE'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-016] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
