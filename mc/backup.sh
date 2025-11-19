#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
SERVER_DIR="$PROJECT_DIR/server"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="minecraft-backup-$TIMESTAMP.tar.gz"

echo "🗂️  Starting Minecraft server backup..."

# Create backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Warn via RCON if server is running
if pgrep -f "fabric-server-mc" > /dev/null; then
    echo "⚠️  Server is running, sending warning to players..."
    "$SCRIPT_DIR/connect.sh" "say Server backup starting in 10 seconds..." 2>/dev/null || true
    sleep 10
    "$SCRIPT_DIR/connect.sh" "save-off" 2>/dev/null || true
    "$SCRIPT_DIR/connect.sh" "save-all flush" 2>/dev/null || true
    sleep 5
fi

# Create backup (exclude logs and cache)
echo "📦 Creating backup: $BACKUP_NAME"
cd "$SERVER_DIR"
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude='logs' \
    --exclude='crash-reports' \
    --exclude='.fabric' \
    --exclude='libraries' \
    . 2>/dev/null

# Re-enable saving if server is running
if pgrep -f "fabric-server-mc" > /dev/null; then
    "$SCRIPT_DIR/connect.sh" "save-on" 2>/dev/null || true
    "$SCRIPT_DIR/connect.sh" "say Backup complete!" 2>/dev/null || true
fi

# Delete backups older than 14 days
echo "🧹 Removing backups older than 14 days..."
find "$BACKUP_DIR" -name "minecraft-backup-*.tar.gz" -type f -mtime +14 -delete

# Show backup info
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/minecraft-backup-*.tar.gz 2>/dev/null | wc -l | tr -d ' ')

echo "✅ Backup complete!"
echo "📊 Backup size: $BACKUP_SIZE"
echo "📚 Total backups: $BACKUP_COUNT"
echo "📂 Location: $BACKUP_DIR"
