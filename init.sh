#!/bin/bash

# Exit on error
set -e

echo "🎮 Initializing Minecraft Server..."

# Generate random RCON password
RCON_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
RCON_PORT=25575

# Create mc directory if it doesn't exist
mkdir -p ~/minecraft-server/mc

# Save RCON credentials
echo "$RCON_PASSWORD" > ~/minecraft-server/mc/rcon
chmod 600 ~/minecraft-server/mc/rcon

echo "🔐 Generated new RCON password"

# Update server.properties
SERVER_PROPS="~/minecraft-server/server/server.properties"

if [ -f "$SERVER_PROPS" ]; then
    # Backup existing server.properties
    cp "$SERVER_PROPS" "$SERVER_PROPS.backup"
    
    # Update RCON settings
    sed -i '' "s/^rcon.password=.*/rcon.password=$RCON_PASSWORD/" "$SERVER_PROPS"
    sed -i '' "s/^enable-rcon=.*/enable-rcon=true/" "$SERVER_PROPS"
    sed -i '' "s/^rcon.port=.*/rcon.port=$RCON_PORT/" "$SERVER_PROPS"
    
    echo "✅ Updated server.properties with RCON settings"
else
    echo "⚠️  server.properties not found. Creating default RCON config..."
    cat >> "$SERVER_PROPS" << EOF
enable-rcon=true
rcon.port=$RCON_PORT
rcon.password=$RCON_PASSWORD
EOF
fi

# Create helper script to connect with mcrcon
cat > ~/minecraft-server/mc/connect.sh << 'EOF'
#!/bin/bash
RCON_PASSWORD=$(cat ~/minecraft-server/mc/rcon)
mcrcon -H localhost -P 25575 -p "$RCON_PASSWORD" "$@"
EOF

chmod +x ~/minecraft-server/mc/connect.sh

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 RCON password saved to: ~/minecraft-server/mc/rcon"
echo "🔌 RCON port: $RCON_PORT"
echo ""
echo "To connect with mcrcon, use:"
echo "  ~/minecraft-server/mc/connect.sh"
echo ""
echo "Examples:"
echo "  ~/minecraft-server/mc/connect.sh 'list'"
echo "  ~/minecraft-server/mc/connect.sh 'stop'"
echo ""
