#!/usr/bin/env bash
# =============================================================================
# PROJETO NEXA — ROTINA AUTOMATIZADA DE BACKUP COMPRIMIDO (DB-048)
# Arquivo: scripts/db-backup.sh
# =============================================================================
# Executa pg_dump em formato custom comprimido (-Fc) com timestamp na pasta
# backups/ (ignorada pelo git), gera checksum SHA-256 e aplica rotação mantendo
# os últimos 7 arquivos de backup.
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
DB_NAME="${POSTGRES_DB:-nexa_senai_db}"
BACKUP_DIR="${ROOT_DIR}/backups"
RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/nexa_backup_${TIMESTAMP}.dump"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "======================================================================"
echo "💾 NEXA DB BACKUP — PG_DUMP COMPRIMIDO (-Fc) & ROTAÇÃO (${RETENTION_COUNT} ÚLTIMOS)"
echo "======================================================================"

if docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}" 2>/dev/null | grep -q true; then
  echo "🐳 Container '${CONTAINER_NAME}' ativo. Executando pg_dump -Fc -Z 9..."
  docker exec "${CONTAINER_NAME}" pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -Fc \
    -Z 9 \
    --no-owner \
    --no-acl \
    > "${BACKUP_FILE}"
elif command -v pg_dump >/dev/null 2>&1; then
  echo "🖥️  Executando pg_dump local em formato custom (-Fc)..."
  pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -Fc \
    -Z 9 \
    --no-owner \
    --no-acl \
    -f "${BACKUP_FILE}"
else
  echo "❌ Nem container Docker '${CONTAINER_NAME}' nem pg_dump local disponíveis." >&2
  exit 1
fi

if [[ ! -s "${BACKUP_FILE}" ]]; then
  echo "❌ Arquivo de backup vazio: ${BACKUP_FILE}" >&2
  rm -f "${BACKUP_FILE}"
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
fi

echo "✅ Backup gerado com sucesso: ${BACKUP_FILE}"

# Rotação mantendo apenas os últimos N backups (padrão: 7)
mapfile -t ALL_BACKUPS < <(ls -1t "${BACKUP_DIR}"/nexa_backup_*.dump 2>/dev/null || true)
if (( ${#ALL_BACKUPS[@]} > RETENTION_COUNT )); then
  for (( i=RETENTION_COUNT; i<${#ALL_BACKUPS[@]}; i++ )); do
    OLD_FILE="${ALL_BACKUPS[$i]}"
    rm -f "${OLD_FILE}" "${OLD_FILE}.sha256"
    echo "🧹 Rotação: removido backup antigo $(basename "${OLD_FILE}")"
  done
fi

echo "📦 Backups retidos em ${BACKUP_DIR}: $(ls -1 "${BACKUP_DIR}"/nexa_backup_*.dump 2>/dev/null | wc -l)"
