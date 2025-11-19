#!/bin/bash
RCON_PASSWORD=$(cat "$HOME/minecraft-server/mc/rcon")
#mcrcon -H localhost -P 25575 -p "$RCON_PASSWORD" "$@"
cd ../tools/mcrcon/
./mcrcon -H localhost -P 25575 -p "$RCON_PASSWORD" "$@"
