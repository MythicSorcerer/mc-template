#!/bin/bash

# Minecraft Log Reader Script
# Place this script in /opt/minecraft/server/logs/readable/
# Run with: ./readall.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Get the directory where the script is located (should be readable folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== Minecraft Log Reader ===${NC}"
echo -e "${YELLOW}Reading logs from: $SCRIPT_DIR${NC}"
echo ""

# Check if we're in the readable directory
if [[ ! "$SCRIPT_DIR" == *"/readable"* ]]; then
    echo -e "${YELLOW}Warning: This script appears to not be in a readable directory.${NC}"
    echo -e "${YELLOW}Expected to be in: /opt/minecraft/server/logs/readable/${NC}"
    echo -e "${YELLOW}Current location: $SCRIPT_DIR${NC}"
    echo ""
fi

# Find all log files and sort them by modification time (oldest first)
log_files=($(find "$SCRIPT_DIR" -maxdepth 1 -name "*.log" -type f -printf '%T@ %p\n' | sort -n | cut -d' ' -f2-))

# Also include current latest.log from parent directory if it exists
parent_dir="$(dirname "$SCRIPT_DIR")"
if [ -f "$parent_dir/latest.log" ]; then
    # Get modification time of latest.log for proper sorting
    latest_time=$(stat -c %Y "$parent_dir/latest.log" 2>/dev/null || echo 0)
    
    # Insert latest.log in the right chronological position
    temp_array=()
    inserted=false
    
    for log_file in "${log_files[@]}"; do
        file_time=$(stat -c %Y "$log_file" 2>/dev/null || echo 0)
        
        if [ "$latest_time" -lt "$file_time" ] && [ "$inserted" = false ]; then
            temp_array+=("$parent_dir/latest.log")
            inserted=true
        fi
        temp_array+=("$log_file")
    done
    
    # If latest.log is newer than all archived logs, add it at the end
    if [ "$inserted" = false ]; then
        temp_array+=("$parent_dir/latest.log")
    fi
    
    log_files=("${temp_array[@]}")
fi

if [ ${#log_files[@]} -eq 0 ]; then
    echo -e "${RED}No log files found in $SCRIPT_DIR${NC}"
    if [ -f "$parent_dir/latest.log" ]; then
        echo -e "${YELLOW}However, latest.log exists in parent directory: $parent_dir/latest.log${NC}"
    fi
    exit 0
fi

echo -e "${GREEN}Found ${#log_files[@]} log file(s) (ordered oldest to newest):${NC}"
for file in "${log_files[@]}"; do
    filename=$(basename "$file")
    file_date=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    echo -e "${CYAN}  $filename ${NC}(${file_date})"
done
echo ""

# Ask user for confirmation before displaying all logs
total_size=0
for file in "${log_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        total_size=$((total_size + size))
    fi
done

# Convert bytes to human readable
if [ $total_size -gt 1048576 ]; then
    size_display="$(echo "scale=1; $total_size/1048576" | bc 2>/dev/null || echo $((total_size/1048576)))MB"
elif [ $total_size -gt 1024 ]; then
    size_display="$(echo "scale=1; $total_size/1024" | bc 2>/dev/null || echo $((total_size/1024)))KB"
else
    size_display="${total_size}B"
fi

echo -e "${YELLOW}Total size of all logs: $size_display${NC}"
echo -e "${YELLOW}This may produce a lot of output. Consider using: ./readall | less +G${NC}"
echo ""

read -p "Continue and display all logs? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Aborted. Use ./readall | less +G for easier reading (starts at bottom).${NC}"
    exit 0
fi

echo ""
echo -e "${MAGENTA}=================================================================================${NC}"
echo -e "${MAGENTA}                           DISPLAYING ALL LOGS                                  ${NC}"
echo -e "${MAGENTA}=================================================================================${NC}"
echo ""

# Display each log file with header
for log_file in "${log_files[@]}"; do
    if [ ! -f "$log_file" ]; then
        echo -e "${RED}File not found: $log_file${NC}"
        continue
    fi
    
    filename=$(basename "$log_file")
    file_date=$(stat -c %y "$log_file" 2>/dev/null | cut -d' ' -f1-2 || echo "unknown date")
    file_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
    
    # Convert file size to human readable
    if [ $file_size -gt 1048576 ]; then
        size_display="$(echo "scale=1; $file_size/1048576" | bc 2>/dev/null || echo $((file_size/1048576)))MB"
    elif [ $file_size -gt 1024 ]; then
        size_display="$(echo "scale=1; $file_size/1024" | bc 2>/dev/null || echo $((file_size/1024)))KB"
    else
        size_display="${file_size}B"
    fi
    
    echo -e "${GREEN}################################################################################${NC}"
    echo -e "${GREEN}# FILE: $filename${NC}"
    echo -e "${GREEN}# DATE: $file_date${NC}"
    echo -e "${GREEN}# SIZE: $size_display${NC}"
    echo -e "${GREEN}# PATH: $log_file${NC}"
    echo -e "${GREEN}################################################################################${NC}"
    echo ""
    
    # Display the file contents
    cat "$log_file"
    
    echo ""
    echo -e "${BLUE}--- End of $filename ---${NC}"
    echo ""
    echo ""
done

echo -e "${MAGENTA}=================================================================================${NC}"
echo -e "${MAGENTA}                              ALL LOGS COMPLETE                                 ${NC}"
echo -e "${MAGENTA}=================================================================================${NC}"
echo ""
echo -e "${GREEN}Displayed ${#log_files[@]} log files in chronological order.${NC}"
