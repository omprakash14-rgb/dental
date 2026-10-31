#!/usr/bin/env bash
# =============================================================================
# DentalAI — Secure Database Restore Script
# Restores a gzip-compressed SQL dump into PostgreSQL with confirmation checks.
# =============================================================================

set -euo pipefail

BACKUP_FILE="${1:-}"
CONTAINER_NAME="${DB_CONTAINER:-dentalai-postgres}"
DB_USER="${POSTGRES_USER:-dentalai}"
DB_NAME="${POSTGRES_DB:-dentalai}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <path_to_backup.sql.gz>"
    echo "Available backups in ./backups:"
    ls -lh ./backups/*.sql.gz 2>/dev/null || echo "  (no backups found in ./backups)"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file not found: ${BACKUP_FILE}" >&2
    exit 1
fi

echo "================================================================="
echo "WARNING: DATABASE RESTORATION OPERATION"
echo "Target Container: ${CONTAINER_NAME}"
echo "Database:         ${DB_NAME}"
echo "Source File:      ${BACKUP_FILE}"
echo "================================================================="
echo "This operation will OVERWRITE existing patient records, screening"
echo "data, and audit logs with the state from the backup."
echo "================================================================="

read -p "Type 'RESTORE' to confirm restoration: " CONFIRMATION

if [ "${CONFIRMATION}" != "RESTORE" ]; then
    echo "[ABORTED] Restoration cancelled by user."
    exit 0
fi

echo "[INFO] Restoring database from archive..."

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"
else
    gunzip -c "${BACKUP_FILE}" | psql -U "${DB_USER}" -d "${DB_NAME}" -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}"
fi

echo "================================================================="
echo "✓ Database Restoration Completed Successfully!"
echo "================================================================="
exit 0

