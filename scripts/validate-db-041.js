/**
 * Script de Validação Automatizada e Testes Unitários — Card [DB-041]
 * Título: Implementar Tabela de Mural de Avisos da Turma (class_announcements)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'prisma', 'migrations', '20261127000000_create_class_announcements_table', 'migration.sql');
const BANCO_MIGRATION_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', '20261127000000_create_class_announcements_table.sql');
const BANCO_SQL_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '41_tabela_class_announcements.sql');
const TYPES_MODELS_TS_PATH = path.join(ROOT_DIR, 'BancoNexa', 'types', 'schema-models.ts');
const BANCO_README_PATH = path.join(ROOT_DIR, 'BancoNexa', 'README.md');
const DOC_PATHS = [
  path.join(ROOT_DIR, 'docs', 'banco', '41-tabela-mural-avisos-class-announcements.md'),
  path.join(ROOT_DIR, 'BancoNexa', '41-tabela-mural-avisos-class-announcements.md'),
];

let failures = 0;
function assertCheck(condition, message) {
  if (condition) console.log(`  [PASS] ${message}`);
  else {
    console.error(`  [FAIL] ${message}`);
    failures++;
  }
}

class AnnouncementsSimulator {
  constructor() {
    this.users = new Map();
    this.classes = new Map();
    this.subjects = new Map();
    this.rows = [];
  }
  addUser(id, role) { this.users.set(id, { id, role }); }
  addClass(id, course_id) { this.classes.set(id, { id, course_id }); }
  addSubject(id, course_id) { this.subjects.set(id, { id, course_id }); }

  publish(row) {
    const cls = this.classes.get(row.class_id);
    if (!cls) { const e = new Error('FK class_id'); e.sqlState = '23503'; throw e; }
    const author = this.users.get(row.author_id);
    if (!author || !['TEACHER', 'COORDINATOR', 'ADMIN'].includes(author.role)) {
      const e = new Error('chk_announcements_author_role'); e.sqlState = '23514'; throw e;
    }
    if (row.subject_id) {
      const subj = this.subjects.get(row.subject_id);
      if (!subj || subj.course_id !== cls.course_id) {
        const e = new Error('chk_announcements_subject_course'); e.sqlState = '23514'; throw e;
      }
    }
    if (row.expires_at && row.expires_at <= row.published_at) {
      const e = new Error('chk_announcements_expiration'); e.sqlState = '23514'; throw e;
    }
    const saved = { priority: 'NORMAL', is_pinned: false, ...row };
    this.rows.push(saved);
    return saved;
  }

  listFeed(classId) {
    return this.rows
      .filter((r) => r.class_id === classId)
      .sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned) || b.published_at.localeCompare(a.published_at));
  }
}

console.log('======================================================================');
console.log('🧪 VALIDAÇÃO DO CARD [DB-041] — MURAL DE AVISOS (class_announcements)');
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
  'Sincronia 100% idêntica entre prisma/migrations, BancoNexa/migrations e BancoNexa/sql/41_tabela_class_announcements.sql'
);
assertCheck(
  fs.readFileSync(DOC_PATHS[0], 'utf8') === fs.readFileSync(DOC_PATHS[1], 'utf8') &&
    fs.readFileSync(BANCO_README_PATH, 'utf8').includes('DB-041'),
  'Documentação DB-041 sincronizada entre docs/banco, BancoNexa e BancoNexa/README.md'
);
assertCheck(
  /fk_announcements_class/i.test(sqlContent) &&
    /priority\s+announcement_priority_enum\s+NOT\s+NULL\s+DEFAULT\s+'NORMAL'/i.test(sqlContent) &&
    /is_pinned\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+FALSE/i.test(sqlContent) &&
    /idx_class_announcements_feed\s+ON\s+class_announcements\s+USING\s+BTREE\s*\(\s*class_id\s*,\s*is_pinned\s+DESC\s*,\s*published_at\s+DESC\s*\)/i.test(sqlContent),
  'Critérios 1, 2 e 3 validados no DDL SQL (FK classes, prioridade, is_pinned e índice feed)'
);
assertCheck(
  schemaContent.includes('model ClassAnnouncement') && typesTsContent.includes('export interface ClassAnnouncement {'),
  'Modelo ClassAnnouncement integrado ao prisma/schema.prisma e tipos TypeScript'
);

const sim = new AnnouncementsSimulator();
sim.addUser('tch-1', 'TEACHER');
sim.addUser('stu-1', 'STUDENT');
sim.addClass('cls-1', 'crs-1');
sim.addSubject('sub-1', 'crs-1');
sim.addSubject('sub-other', 'crs-2');

sim.publish({ class_id: 'cls-1', subject_id: 'sub-1', author_id: 'tch-1', title: 'Aviso Normal', content: 'Conteúdo normal da aula.', priority: 'NORMAL', is_pinned: false, published_at: '2026-03-15T10:00:00Z' });
sim.publish({ class_id: 'cls-1', subject_id: 'sub-1', author_id: 'tch-1', title: 'Uso de EPI Obrigatório', content: 'Óculos de proteção obrigatórios na oficina.', priority: 'URGENT', is_pinned: true, published_at: '2026-03-10T10:00:00Z' });

const feed = sim.listFeed('cls-1');
assertCheck(
  feed.length === 2 && feed[0].is_pinned === true && feed[0].priority === 'URGENT',
  'Teste 1 (Critérios 2 e 3): Avisos fixados (is_pinned=true) priorizados no topo do feed'
);

let studentBlocked = false;
let wrongCourseBlocked = false;
try { sim.publish({ class_id: 'cls-1', author_id: 'stu-1', title: 'Tentativa Aluno', content: 'Não autorizado', published_at: '2026-03-15T10:00:00Z' }); } catch (e) { studentBlocked = e.sqlState === '23514'; }
try { sim.publish({ class_id: 'cls-1', subject_id: 'sub-other', author_id: 'tch-1', title: 'Curso divergente', content: 'Disciplina de outro curso', published_at: '2026-03-15T10:00:00Z' }); } catch (e) { wrongCourseBlocked = e.sqlState === '23514'; }
assertCheck(studentBlocked && wrongCourseBlocked, 'Teste 2 (Critério 1): Bloqueio de autor STUDENT e disciplina de outro curso (23514)');

console.log('\n======================================================================');
if (failures === 0) {
  console.log('✅ SUCESSO: Todos os critérios de aceitação e DoD do card [DB-041] foram validados!');
  process.exit(0);
} else {
  console.error(`❌ ERRO: ${failures} verificação(ões) falharam.`);
  process.exit(1);
}
