/**
 * Gerador de Manifesto de Schema, Tipos Enum Exportados e Validador SQL/ORM — Cards [DB-004] e [DB-005]
 * Comando: npm run db:generate
 *
 * Funcionalidades:
 * 1. Valida `prisma/schema.prisma` garantindo provider `postgresql` e `env("DATABASE_URL")`.
 * 2. Verifica a convenção `snake_case` no banco de dados via diretivas `@map` e `@@map`.
 * 3. Extrai todas as enumerações (`enum`) do `schema.prisma` e exporta tipos compatíveis com
 *    validações da API:
 *    - TypeScript / Node (`BancoNexa/types/system-enums.ts`)
 *    - Python 3.12+ / FastAPI / Pydantic v2 (`BancoNexa/types/system_enums.py`)
 *    - JSON Schema Contract (`BancoNexa/types/system-enums.json`)
 * 4. Sincroniza o manifesto de metadados SQL (`BancoNexa/migrations/migration-manifest.json`).
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT_DIR = path.resolve(__dirname, '..');
const SCHEMA_PRISMA_PATH = path.join(ROOT_DIR, 'prisma', 'schema.prisma');
const PRISMA_MIGRATIONS_DIR = path.join(ROOT_DIR, 'prisma', 'migrations');
const SQL_3FN_PATH = path.join(ROOT_DIR, 'BancoNexa', 'sql', '02_modelo_logico_3fn.sql');
const MANIFEST_OUTPUT_PATH = path.join(ROOT_DIR, 'BancoNexa', 'migrations', 'migration-manifest.json');
const TYPES_DIR = path.join(ROOT_DIR, 'BancoNexa', 'types');

function sha256(content) {
  return crypto.createHash('sha256').update(content, 'utf8').digest('hex');
}

function parsePrismaEnums(schemaContent) {
  const enumRegex = /enum\s+([A-Za-z0-9_]+)\s*\{([\s\S]*?)\}/g;
  const parsedEnums = [];
  let match;

  while ((match = enumRegex.exec(schemaContent)) !== null) {
    const name = match[1];
    const body = match[2];
    let pgTypeName = name.toLowerCase();
    const values = [];

    for (const rawLine of body.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('//')) continue;
      const mapMatch = line.match(/^@@map\("([^"]+)"\)/);
      if (mapMatch) {
        pgTypeName = mapMatch[1];
        continue;
      }
      if (/^[A-Z0-9_]+$/.test(line)) {
        values.push(line);
      }
    }

    parsedEnums.push({
      name,
      pgTypeName,
      values,
    });
  }

  return parsedEnums;
}

function generateTypeScriptEnums(enums) {
  const lines = [
    '/**',
    ' * ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate` — CARD [DB-005]',
    ' * Tipos Enum Exportados do Schema do Banco de Dados (PostgreSQL 16)',
    ' * Compatíveis com validações de API, Front-end e Prisma Client.',
    ' */',
    '',
  ];

  for (const e of enums) {
    lines.push(`/** Mapeado para o tipo nativo PostgreSQL: \`${e.pgTypeName}\` */`);
    lines.push(`export const ${e.name} = {`);
    for (const v of e.values) {
      lines.push(`  ${v}: '${v}',`);
    }
    lines.push(`} as const;`);
    lines.push(`export type ${e.name} = (typeof ${e.name})[keyof typeof ${e.name}];`);
    lines.push(`export const ${e.name}Values: readonly ${e.name}[] = Object.values(${e.name});`);
    lines.push('');
  }

  return lines.join('\n');
}

function generatePythonEnums(enums) {
  const lines = [
    '"""',
    'ARQUIVO GERADO AUTOMATICAMENTE POR `npm run db:generate` — CARD [DB-005]',
    'Enumerações Globais de Sistema sincronizadas com os tipos ENUM nativos do PostgreSQL 16.',
    'Compatíveis com FastAPI, Pydantic v2 e SQLAlchemy 2.0 (BE-005, BE-009).',
    '"""',
    '',
    'from enum import StrEnum',
    '',
  ];

  for (const e of enums) {
    lines.push(`class ${e.name}(StrEnum):`);
    lines.push(`    """Mapeado no PostgreSQL 16 como '${e.pgTypeName}'."""`);
    for (const v of e.values) {
      lines.push(`    ${v} = "${v}"`);
    }
    lines.push('');
    lines.push('');
  }

  return lines.join('\n');
}

function main() {
  console.log('======================================================================');
  console.log('⚙️  NEXA DB GENERATE — VALIDAÇÃO DE SCHEMA & GERAÇÃO DE TIPOS ENUM');
  console.log('======================================================================\n');

  if (!fs.existsSync(SCHEMA_PRISMA_PATH)) {
    throw new Error('Arquivo prisma/schema.prisma não encontrado!');
  }

  const schemaContent = fs.readFileSync(SCHEMA_PRISMA_PATH, 'utf8');

  if (!schemaContent.includes('provider = "postgresql"')) {
    throw new Error('O datasource do schema.prisma deve utilizar provider = "postgresql".');
  }
  if (!schemaContent.includes('env("DATABASE_URL")')) {
    throw new Error('O datasource do schema.prisma deve apontar para env("DATABASE_URL").');
  }
  if (!schemaContent.includes('@map(') || !schemaContent.includes('@@map(')) {
    throw new Error('O schema.prisma deve utilizar @map e @@map para manter snake_case no PostgreSQL.');
  }

  const parsedEnums = parsePrismaEnums(schemaContent);
  const sql3fnContent = fs.existsSync(SQL_3FN_PATH) ? fs.readFileSync(SQL_3FN_PATH, 'utf8') : '';
  const tableMatches = [...sql3fnContent.matchAll(/CREATE\s+TABLE\s+([a-z0-9_]+)\s*\(/gi)].map((m) => m[1]);
  const enumMatches = [...sql3fnContent.matchAll(/CREATE\s+TYPE\s+([a-z0-9_]+)\s+AS\s+ENUM/gi)].map((m) => m[1]);

  fs.mkdirSync(TYPES_DIR, { recursive: true });
  fs.writeFileSync(path.join(TYPES_DIR, 'system-enums.ts'), generateTypeScriptEnums(parsedEnums), 'utf8');
  fs.writeFileSync(path.join(TYPES_DIR, 'system_enums.py'), generatePythonEnums(parsedEnums), 'utf8');
  fs.writeFileSync(
    path.join(TYPES_DIR, 'system-enums.json'),
    JSON.stringify({ generatedAt: 'DB-005', enums: parsedEnums }, null, 2) + '\n',
    'utf8'
  );

  const migrations = [];
  if (fs.existsSync(PRISMA_MIGRATIONS_DIR)) {
    const entries = fs.readdirSync(PRISMA_MIGRATIONS_DIR, { withFileTypes: true });
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const migSqlPath = path.join(PRISMA_MIGRATIONS_DIR, entry.name, 'migration.sql');
        if (fs.existsSync(migSqlPath)) {
          const content = fs.readFileSync(migSqlPath, 'utf8');
          migrations.push({
            id: entry.name,
            checksumSha256: sha256(content),
            path: `prisma/migrations/${entry.name}/migration.sql`,
          });
        }
      }
    }
  }

  const manifest = {
    project: 'NEXA — Sistema Inteligente de Monitoramento Acadêmico SENAI',
    databaseEngine: 'PostgreSQL 16 Alpine (Docker)',
    namingConvention: 'snake_case (Database) / camelCase (@map Application)',
    schemaSha256: sha256(schemaContent),
    logicalModel3fnSha256: sha256(sql3fnContent),
    totalTables3fn: tableMatches.length,
    totalEnums: parsedEnums.length,
    tables: tableMatches,
    enums: parsedEnums,
    sqlEnumTypes: enumMatches,
    migrations,
  };

  fs.mkdirSync(path.dirname(MANIFEST_OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(MANIFEST_OUTPUT_PATH, JSON.stringify(manifest, null, 2) + '\n', 'utf8');

  console.log(`  [OK] Schema validado: prisma/schema.prisma (PostgreSQL + DATABASE_URL + @map/@@map)`);
  console.log(`  [OK] Enums extraídos e exportados (TS, Python, JSON): ${parsedEnums.length}`);
  console.log(`  [OK] Tabelas 3FN catalogadas no manifesto SQL: ${tableMatches.length}`);
  console.log(`  [OK] Manifesto atualizado em: BancoNexa/migrations/migration-manifest.json\n`);
  console.log('✅ Geração de artefatos e tipos de banco concluída com sucesso!');
}

main();
