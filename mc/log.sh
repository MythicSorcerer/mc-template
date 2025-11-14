#!/bin/bash

# Path to your Minecraft server directory
SERVER_DIR="../server"

cd "$SERVER_DIR/logs" || exit 1

echo "Tailing latest.log... (Ctrl+C to exit)"

tail -n 150 --follow=name --retry latest.log
