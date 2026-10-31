#!/usr/bin/env bash
# =============================================================================
# DentalAI — Secure Database Backup Script
# Creates timestamped, gzip-compressed SQL dumps of the PostgreSQL database.
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/dentalai_backup_${TIMESTAMP}.sql.gz"
CONTAINER_NAME="${DB_CONTAINER:-dentalai-postgres}"
DB_USER="${POSTGRES_USER:-dentalai}"
DB_NAME="${POSTGRES_DB:-dentalai}"

mkdir -p "${BACKUP_DIR}"

echo "================================================================="
echo "DentalAI — Starting Database Backup"
echo "Target Container: ${CONTAINER_NAME}"
echo "Database:         ${DB_NAME}"
echo "Output Archive:   ${BACKUP_FILE}"
echo "Timestamp:        ${TIMESTAMP}"
echo "================================================================="

# Check if Docker container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[INFO] Running pg_dump inside Docker container '${CONTAINER_NAME}'..."
    docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"
else
    echo "[INFO] Container not found. Attempting local pg_dump..."
    pg_dump -U "${DB_USER}" -d "${DB_NAME}" -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" --clean --if-exists | gzip > "${BACKUP_FILE}"
fi

if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "================================================================="
    echo "✓ Backup Completed Successfully!"
    echo "File Size: ${SIZE}"
    echo "Location:  ${BACKUP_FILE}"
    echo "================================================================="
    exit 0
else
    echo "[ERROR] Backup failed or generated an empty file." >&2
    exit 1
fi

