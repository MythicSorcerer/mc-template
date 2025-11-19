#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/world-backups"
WORLD_DIR="$PROJECT_DIR/server/world"

echo "🌍 Available world backups:"
ls -lht "$BACKUP_DIR"/world-backup-*.tar.gz 2>/dev/null | awk '{print NR": "$9" ("$5" - "$6" "$7")"}'

if [ ! -f "$BACKUP_DIR"/world-backup-*.tar.gz 2>/dev/null ]; then
    echo "❌ No world backups found in $BACKUP_DIR"
    exit 1
fi

echo ""
read -p "Enter backup number to restore (or 'q' to quit): " choice

if [ "$choice" = "q" ]; then
    echo "Cancelled."
    exit 0
fi

BACKUP_FILE=$(ls -t "$BACKUP_DIR"/world-backup-*.tar.gz 2>/dev/null | sed -n "${choice}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Invalid selection"
    exit 1
fi

# Check if server is running
if pgrep -f "fabric-server-mc" > /dev/null; then
    echo "❌ Server is currently running!"
    echo "Please stop the server before restoring a world backup."
    exit 1
fi

echo "⚠️  WARNING: This will overwrite your current world!"
echo "Restoring: $(basename $BACKUP_FILE)"
read -p "Are you sure? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Backup current world before overwriting (just in case)
if [ -d "$WORLD_DIR" ]; then
    SAFETY_BACKUP="$BACKUP_DIR/world-pre-restore-$(date +"%Y-%m-%d_%H-%M-%S").tar.gz"
    echo "💾 Creating safety backup of current world..."
    cd "$PROJECT_DIR/server"
    tar -czf "$SAFETY_BACKUP" world 2>/dev/null
    echo "Safety backup created: $(basename $SAFETY_BACKUP)"
fi

echo "🔄 Restoring world backup: $(basename $BACKUP_FILE)"

# Remove old world
rm -rf "$WORLD_DIR"

# Extract backup
cd "$PROJECT_DIR/server"
tar -xzf "$BACKUP_FILE"

echo "✅ World restore complete!"
echo "You can now start your server."