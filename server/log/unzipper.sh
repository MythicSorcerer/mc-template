#!/bin/bash

# Minecraft Log Decompression Script
# Place this script in /opt/minecraft/server/logs/
# Run with: ./decompress_logs.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located (should be logs folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"
TARGET_DIR="$SCRIPT_DIR/readable"

echo -e "${BLUE}=== Minecraft Log Decompression Utility ===${NC}"
echo -e "${YELLOW}Source directory: $SOURCE_DIR${NC}"
echo -e "${YELLOW}Target directory: $TARGET_DIR${NC}"
echo ""

# Check if we're in the logs directory
if [[ ! "$SCRIPT_DIR" == *"/logs"* ]]; then
    echo -e "${YELLOW}Warning: This script appears to not be in a logs directory.${NC}"
    echo -e "${YELLOW}Expected to be in: /opt/minecraft/server/logs/${NC}"
    echo -e "${YELLOW}Current location: $SCRIPT_DIR${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
fi

# Create target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${BLUE}Creating readable directory...${NC}"
    mkdir -p "$TARGET_DIR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Created $TARGET_DIR${NC}"
    else
        echo -e "${RED}✗ Failed to create $TARGET_DIR${NC}"
        exit 1
    fi
fi

# Clean up existing .log files in readable directory
existing_logs=($(find "$TARGET_DIR" -maxdepth 1 -name "*.log" -type f))
if [ ${#existing_logs[@]} -gt 0 ]; then
    echo -e "${BLUE}Cleaning up ${#existing_logs[@]} existing .log file(s)...${NC}"
    rm -f "$TARGET_DIR"/*.log 2>/dev/null
    echo -e "${GREEN}✓ Cleanup complete${NC}"
    echo ""
fi

# Find all .gz files in the source directory
gz_files=($(find "$SOURCE_DIR" -maxdepth 1 -name "*.gz" -type f))

if [ ${#gz_files[@]} -eq 0 ]; then
    echo -e "${YELLOW}No .gz files found in $SOURCE_DIR${NC}"
    exit 0
fi

echo -e "${BLUE}Found ${#gz_files[@]} .gz file(s) to decompress:${NC}"
for file in "${gz_files[@]}"; do
    echo -e "${YELLOW}  $(basename "$file")${NC}"
done
echo ""

# Counter for processed files
processed=0
successful=0
failed=0

# Process each .gz file
for gz_file in "${gz_files[@]}"; do
    filename=$(basename "$gz_file")
    # Remove .gz extension for target filename
    target_filename="${filename%.gz}"
    target_path="$TARGET_DIR/$target_filename"
    
    echo -e "${BLUE}Processing: $filename${NC}"
    
    # Check if target file already exists - skip automatically
    if [ -f "$target_path" ]; then
        echo -e "${YELLOW}  Already exists, skipping: $target_filename${NC}"
        continue
    fi
    
    # Decompress the file
    if gunzip -c "$gz_file" > "$target_path" 2>/dev/null; then
        file_size=$(stat -c%s "$target_path" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}  ✓ Decompressed: $target_filename (${file_size} bytes)${NC}"
        ((successful++))
    else
        echo -e "${RED}  ✗ Failed to decompress: $filename${NC}"
        # Remove failed target file if it exists
        [ -f "$target_path" ] && rm -f "$target_path"
        ((failed++))
    fi
    
    ((processed++))
done

echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}Successfully decompressed: $successful files${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed to decompress: $failed files${NC}"
fi
echo -e "${BLUE}Total processed: $processed files${NC}"
echo -e "${YELLOW}Readable files location: $TARGET_DIR${NC}"

# List the contents of the readable directory
echo ""
echo -e "${BLUE}Contents of readable directory:${NC}"
if [ "$(ls -A "$TARGET_DIR")" ]; then
    ls -la "$TARGET_DIR"
else
    echo -e "${YELLOW}(empty)${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
