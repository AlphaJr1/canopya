#!/bin/bash

# Stop Database Viewer Dashboard

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/.database-viewer.pid"
LOG_FILE="$PROJECT_DIR/database-viewer.log"

cd "$PROJECT_DIR"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  Database viewer is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Database viewer is not running (process $PID not found)"
    rm "$PID_FILE"
    exit 0
fi

echo "🛑 Stopping Database Viewer Dashboard (PID: $PID)..."

# Kill the process
kill $PID

# Wait for process to stop
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# Force kill if still running
if ps -p $PID > /dev/null 2>&1; then
    echo "   Force stopping..."
    kill -9 $PID
    sleep 1
fi

# Remove PID file
rm "$PID_FILE"

# Log stop time
echo "" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"
echo "Stopped: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

echo "✅ Database viewer stopped"
echo ""
echo "   Logs saved in: database-viewer.log"
echo ""
