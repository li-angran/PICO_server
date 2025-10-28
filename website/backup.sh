#!/bin/bash

# PICO Platform Backup Script

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="pico_platform_backup_${TIMESTAMP}"

echo "Creating backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create temporary directory for this backup
TEMP_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "${TEMP_DIR}"

# Backup database
echo "Backing up database..."
cp pico_platform.db "${TEMP_DIR}/" 2>/dev/null || echo "No database found"

# Backup configuration
echo "Backing up configuration..."
cp app.py "${TEMP_DIR}/"
cp config.py "${TEMP_DIR}/" 2>/dev/null || echo "No config.py found"

# Create archive
echo "Creating archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
cd ..

echo "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Keep only last 10 backups
echo "Cleaning old backups..."
cd "${BACKUP_DIR}"
ls -t pico_platform_backup_*.tar.gz | tail -n +11 | xargs -r rm
cd ..

echo "Backup complete!"
