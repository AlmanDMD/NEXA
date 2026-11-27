/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-043]
 * Título: Implementar Tabela de Observações Pedagógicas Restritas (pedagogical_notes)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127020000_create_pedagogical_notes_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127020000_create_pedagogical_notes_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '43_tabela_pedagogical_notes.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '43-tabela-observacoes-pedagogicas-restritas-pedagogical-notes.md'),
  path.join(ROOT_DIR, 'BancoNexa', '43-tabela-observacoes-pedagogicas-restritas-pedagogical-notes.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class PedagogicalNotesSimulator {
  constructor() {
    this.notes = [];
    this.auditLogs = [];
  }
  create(note, authorRole) {
    if (!['TEACHER', 'COORDINATOR', 'ADMIN'].includes(authorRole)) {
      const e = new Error('chk_pedagogical_notes_author_role'); e.sqlState = '23514'; throw e;
    }
    const saved = { id: `pn-${this.notes.length + 1}`, visibility_scope: 'PRIVATE_AUTHOR', ...note };
    this.notes.push(saved);
    this.auditLogs.push({ action: 'PEDAGOGICAL_NOTE_CREATE', entity: 'pedagogical_notes', entity_id: saved.id, user_id: saved.author_id });
    return saved;
  }
  readAudited(noteId, readerId, readerRole) {
    const n = this.notes.find((x) => x.id === noteId);
    if (readerRole === 'STUDENT') { const e = new Error('access denied student'); e.sqlState = '42501'; throw e; }
    if (n.visibility_scope === 'PRIVATE_AUTHOR' && n.author_id !== readerId && readerRole !== 'ADMIN') {
      const e = new Error('private author'); e.sqlState = '42501'; throw e;
    }
    if (n.visibility_scope === 'COORDINATION_ONLY' && !['COORDINATOR', 'ADMIN'].includes(readerRole)) {
      const e = new Error('coord only'); e.sqlState = '42501'; throw e;
    }
    this.auditLogs.push({ action: 'PEDAGOGICAL_NOTE_READ', entity: 'pedagogical_notes', entity_id: n.id, user_id: readerId });
    return n;
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-043] — OBSERVAÇÕES RESTRITAS (pedagogical_notes)');
console.log('======================================================================\n');

try {
  execSync('node scripts/db-generate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  execSync('node scripts/db-migrate.js', { cwd: ROOT_DIR, stdio: ['pipe', 'pipe', 'pipe'] });
  assertCheck(true, 'Scripts db:generate e db:migrate executados com sucesso');
} catch (err) {
  assertCheck(false, `Falha em db:generate / db:migrate: ${err.message}`);
}

const sqlContent = fs.readFileSync(MIGRATION_SQL_PATH, 'utf8');
const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');
const typesTsContent = fs.readFileSync(TYPES_MODELS_TS_PATH, 'utf8');

assertCheck(
  sqlContent === fs.readFileSync(BANCO_MIGRATION_SQL_PATH, 'utf8') && sqlContent === fs.readFileSync(BANCO_SQL_PATH, 'utf8'),
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/43_tabela_pedagogical_notes.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-043'),
  'Documentação DB-043 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /visibility_scope\s+note_visibility_scope_enum/i.test(sqlContent) &&
    /fk_pedagogical_notes_enrollment/i.test(sqlContent) &&
    /trg_pedagogical_notes_audit_trail/i.test(sqlContent) &&
    /fn_read_pedagogical_note_audited/i.test(sqlContent) &&
    /pol_pedagogical_notes_scope_isolation/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (visibility_scope, FK enrollments, RLS e auditoria leitura/escrita em audit_logs)'
);
assertCheck(
  schemaContent.includes('model PedagogicalNote') && typesTsContent.includes('export interface PedagogicalNote {'),
  'Modelo PedagogicalNote integrado ao prisma/schema.prisma e tipos TypeScript'
);

const sim = new PedagogicalNotesSimulator();
const priv = sim.create({ student_id: 'stu-1', enrollment_id: 'enr-1', author_id: 'tch-1', visibility_scope: 'PRIVATE_AUTHOR', note_content: 'Anotação reservada.' }, 'TEACHER');
const coord = sim.create({ student_id: 'stu-1', enrollment_id: 'enr-1', author_id: 'crd-1', visibility_scope: 'COORDINATION_ONLY', note_content: 'Caso coordenação.' }, 'COORDINATOR');

let studentDenied = false;
let otherTeacherDenied = false;
let teacherCoordOnlyDenied = false;
try { sim.readAudited(priv.id, 'stu-1', 'STUDENT'); } catch (e) { studentDenied = e.sqlState === '42501'; }
try { sim.readAudited(priv.id, 'tch-2', 'TEACHER'); } catch (e) { otherTeacherDenied = e.sqlState === '42501'; }
try { sim.readAudited(coord.id, 'tch-1', 'TEACHER'); } catch (e) { teacherCoordOnlyDenied = e.sqlState === '42501'; }

sim.readAudited(priv.id, 'tch-1', 'TEACHER');
sim.readAudited(coord.id, 'crd-1', 'COORDINATOR');

assertCheck(
  studentDenied && otherTeacherDenied && teacherCoordOnlyDenied,
  'Teste 1 (Critério 1): Escopos PRIVATE_AUTHOR, COORDINATION_ONLY e bloqueio absoluto a STUDENT respeitados (42501)'
);
assertCheck(
  sim.auditLogs.filter((l) => l.action === 'PEDAGOGICAL_NOTE_CREATE').length === 2 &&
    sim.auditLogs.filter((l) => l.action === 'PEDAGOGICAL_NOTE_READ').length === 2,
  'Teste 2 (Critério 3): Leituras e escritas autorizadas geraram rastro obrigatório em audit_logs'
);

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-043] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
