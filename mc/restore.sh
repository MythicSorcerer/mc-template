#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"

echo "📚 Available backups:"
ls -lht "$BACKUP_DIR"/minecraft-backup-*.tar.gz | awk '{print NR": "$9" ("$5" - "$6" "$7")"}'

echo ""
read -p "Enter backup number to restore (or 'q' to quit): " choice

if [ "$choice" = "q" ]; then
    echo "Cancelled."
    exit 0
fi

BACKUP_FILE=$(ls -t "$BACKUP_DIR"/minecraft-backup-*.tar.gz | sed -n "${choice}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Invalid selection"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite your current server files!"
read -p "Are you sure? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Restoring backup: $(basename $BACKUP_FILE)"
cd "$PROJECT_DIR/server"
tar -xzf "$BACKUP_FILE"
echo "✅ Restore complete!"
