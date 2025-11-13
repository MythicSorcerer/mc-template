#!/bin/bash

# Exit on error
set -e

echo "🎮 Initializing Minecraft Server..."

# Get the script's directory (works regardless of where it's called from)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go up one level since we're now in mc/ subdirectory
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if mcrcon is available
if [ ! -f "$PROJECT_DIR/tools/mcrcon/mcrcon" ]; then
    echo "⚠️  mcrcon not found. Building it..."
    mkdir -p "$PROJECT_DIR/tools"
    cd "$PROJECT_DIR/tools"
    
    if [ ! -d "mcrcon" ]; then
        git clone https://github.com/Tiiffi/mcrcon.git
    fi
    
    cd mcrcon
    make
    echo "✅ mcrcon built successfully"
fi

# Generate random RCON password
RCON_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
RCON_PORT=25575

# Create mc directory if it doesn't exist (we're already in it, but make sure)
mkdir -p "$SCRIPT_DIR"

# Save RCON credentials
echo "$RCON_PASSWORD" > "$SCRIPT_DIR/rcon"
chmod 600 "$SCRIPT_DIR/rcon"

echo "🔐 Generated new RCON password"

# Update server.properties
SERVER_PROPS="$PROJECT_DIR/server/server.properties"

if [ -f "$SERVER_PROPS" ]; then
    # Backup existing server.properties
    cp "$SERVER_PROPS" "$SERVER_PROPS.backup"
    
    # Update RCON settings
    sed -i '' "s/^rcon.password=.*/rcon.password=$RCON_PASSWORD/" "$SERVER_PROPS"
    sed -i '' "s/^enable-rcon=.*/enable-rcon=true/" "$SERVER_PROPS"
    sed -i '' "s/^rcon.port=.*/rcon.port=$RCON_PORT/" "$SERVER_PROPS"
    
    # If settings don't exist, add them
    if ! grep -q "^enable-rcon=" "$SERVER_PROPS"; then
        echo "enable-rcon=true" >> "$SERVER_PROPS"
    fi
    if ! grep -q "^rcon.port=" "$SERVER_PROPS"; then
        echo "rcon.port=$RCON_PORT" >> "$SERVER_PROPS"
    fi
    if ! grep -q "^rcon.password=" "$SERVER_PROPS"; then
        echo "rcon.password=$RCON_PASSWORD" >> "$SERVER_PROPS"
    fi
    
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
cat > "$SCRIPT_DIR/connect.sh" << EOF
#!/bin/bash
SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="\$(dirname "\$SCRIPT_DIR")"
RCON_PASSWORD=\$(cat "\$SCRIPT_DIR/rcon")
"\$PROJECT_DIR/tools/mcrcon/mcrcon" -H localhost -P 25575 -p "\$RCON_PASSWORD" "\$@"
EOF

chmod +x "$SCRIPT_DIR/connect.sh"

echo ""
echo "✨ Setup complete!"
echo ""
echo "📂 Server directory: $SCRIPT_DIR"
echo "📝 RCON password saved to: $SCRIPT_DIR/mc/rcon"
echo "🔌 RCON port: $RCON_PORT"
echo ""
echo "To connect with mcrcon, use:"
echo "  $SCRIPT_DIR/mc/connect.sh"
echo ""
echo "Examples:"
echo "  $SCRIPT_DIR/mc/connect.sh 'list'"
echo "  $SCRIPT_DIR/mc/connect.sh 'stop'"
echo ""
