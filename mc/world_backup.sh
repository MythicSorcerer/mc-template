#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/world-backups"
WORLD_DIR="$PROJECT_DIR/server/world"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="world-backup-$TIMESTAMP.tar.gz"

echo "🌍 Starting world backup..."

# Check if world directory exists
if [ ! -d "$WORLD_DIR" ]; then
    echo "❌ World directory not found: $WORLD_DIR"
    exit 1
fi

# Create backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Warn via RCON if server is running
if pgrep -f "fabric-server-mc" > /dev/null; then
    echo "⚠️  Server is running, sending warning to players..."
    "$SCRIPT_DIR/connect.sh" "say World backup starting in 10 seconds..." 2>/dev/null || true
    sleep 10
    "$SCRIPT_DIR/connect.sh" "save-off" 2>/dev/null || true
    "$SCRIPT_DIR/connect.sh" "save-all flush" 2>/dev/null || true
    sleep 5
fi

# Create backup
echo "📦 Creating backup: $BACKUP_NAME"
cd "$PROJECT_DIR/server"
tar -czf "$BACKUP_DIR/$BACKUP_NAME" world 2>/dev/null

# Re-enable saving if server is running
if pgrep -f "fabric-server-mc" > /dev/null; then
    "$SCRIPT_DIR/connect.sh" "save-on" 2>/dev/null || true
    "$SCRIPT_DIR/connect.sh" "say World backup complete!" 2>/dev/null || true
fi

# Delete backups older than 14 days
echo "🧹 Removing world backups older than 14 days..."
find "$BACKUP_DIR" -name "world-backup-*.tar.gz" -type f -mtime +14 -delete

# Show backup info
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/world-backup-*.tar.gz 2>/dev/null | wc -l | tr -d ' ')

echo "✅ World backup complete!"
echo "📊 Backup size: $BACKUP_SIZE"
echo "📚 Total world backups: $BACKUP_COUNT"
echo "📂 Location: $BACKUP_DIR"