#!/bin/bash

# View Database Viewer Dashboard Logs

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/database-viewer.log"

cd "$PROJECT_DIR"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️  No log file found: database-viewer.log"
    exit 1
fi

# Check if argument is provided
if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
    echo "📋 Following database viewer logs (Ctrl+C to stop)..."
    echo ""
    tail -f "$LOG_FILE"
else
    echo "📋 Database Viewer Logs"
    echo "=================================================="
    echo ""
    cat "$LOG_FILE"
    echo ""
    echo "=================================================="
    echo "To follow logs in real-time: $0 -f"
    echo ""
fi
