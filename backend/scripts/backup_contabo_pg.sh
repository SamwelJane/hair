#!/usr/bin/env bash
# Contabo PostgreSQL Disaster Recovery & Automated Backup Script
# Usage: Run via cron daily (e.g. 0 2 * * * /path/to/backup_contabo_pg.sh)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/hiar_business}"
DB_NAME="${DB_NAME:-hiar_business}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS=14

mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/db_${DB_NAME}_${TIMESTAMP}.dump"

echo "[$(date)] Starting backup of ${DB_NAME} on Contabo server..."
pg_dump -Fc -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_FILE}"
echo "[$(date)] Backup completed successfully: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# Prune backups older than RETENTION_DAYS
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "db_${DB_NAME}_*.dump" -mtime +${RETENTION_DAYS} -exec rm -f {} +
echo "[$(date)] Disaster recovery routine complete."
