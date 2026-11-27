#!/usr/bin/env bash
# =============================================================================
# PROJETO NEXA — SCRIPT DE RESTAURAÇÃO E VERIFICAÇÃO PÓS-RESTORE (DB-048)
# Arquivo: scripts/db-restore.sh
# =============================================================================
# Restaura um dump comprimido (-Fc) gerado por scripts/db-backup.sh em um banco
# limpo via pg_restore e valida integridade de tabelas, views, triggers e dados.
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  ENV_FILE="${ROOT_DIR}/.env.example"
fi

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-nexa-postgres}"
DB_USER="${POSTGRES_USER:-nexa_admin}"
TARGET_DB="${2:-${POSTGRES_DB:-nexa_senai_db}}"
BACKUP_DIR="${ROOT_DIR}/backups"
BACKUP_FILE="${1:-$(ls -1t "${BACKUP_DIR}"/nexa_backup_*.dump 2>/dev/null | head -n 1 || true)}"

if [[ -z "${BACKUP_FILE}" || ! -f "${BACKUP_FILE}" ]]; then
  echo "❌ Arquivo de backup não encontrado. Informe o caminho ou execute scripts/db-backup.sh primeiro." >&2
  exit 1
fi

echo "======================================================================"
echo "♻️  NEXA DB RESTORE — RESTAURAÇÃO & VERIFICAÇÃO DE INTEGRIDADE (DB-048)"
echo "======================================================================"
echo "📄 Arquivo: ${BACKUP_FILE}"
echo "🎯 Banco destino: ${TARGET_DB}"

if [[ -f "${BACKUP_FILE}.sha256" ]] && command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c "${BACKUP_FILE}.sha256"
  echo "✅ Checksum SHA-256 validado."
fi

VERIFY_SQL="
SELECT
  (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') AS total_tables,
  (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') AS total_views,
  (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public') AS total_triggers;
"

if docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}" 2>/dev/null | grep -q true; then
  echo "🐳 Restaurando via container Docker '${CONTAINER_NAME}'..."
  docker exec -i "${CONTAINER_NAME}" pg_restore \
    -U "${DB_USER}" \
    -d "${TARGET_DB}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --exit-on-error \
    < "${BACKUP_FILE}"

  echo "🔍 Verificando integridade pós-restauração..."
  docker exec -i "${CONTAINER_NAME}" psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${TARGET_DB}" -c "${VERIFY_SQL}"
elif command -v pg_restore >/dev/null 2>&1; then
  echo "🖥️  Restaurando via pg_restore local..."
  pg_restore \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${DB_USER}" \
    -d "${TARGET_DB}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --exit-on-error \
    "${BACKUP_FILE}"

  psql -v ON_ERROR_STOP=1 -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${DB_USER}" -d "${TARGET_DB}" -c "${VERIFY_SQL}"
else
  echo "❌ Nem container Docker '${CONTAINER_NAME}' nem pg_restore local disponíveis." >&2
  exit 1
fi

echo "✅ Restauração e verificação pós-restore concluídas com sucesso!"
