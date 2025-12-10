#!/bin/bash

# Start Database Viewer Dashboard
# Logs akan disimpan di database-viewer.log

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/database-viewer.log"
PID_FILE="$PROJECT_DIR/.database-viewer.pid"

cd "$PROJECT_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Database viewer already running (PID: $PID)"
        echo "   View logs: tail -f database-viewer.log"
        echo "   Stop with: ./scripts/stop-database-viewer.sh"
        exit 1
    else
        # PID file exists but process not running, remove it
        rm "$PID_FILE"
    fi
fi

echo "🗄️  Starting Database Viewer Dashboard..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit >> "$LOG_FILE" 2>&1
fi

# Clear old log or create new one
echo "==================================================" > "$LOG_FILE"
echo "Database Viewer Dashboard Log" >> "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Start streamlit in background
nohup streamlit run database_viewer.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false \
    >> "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

# Wait a bit for startup
sleep 2

# Check if process is running
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ Database viewer started successfully!"
    echo ""
    echo "   URL: http://localhost:8501"
    echo "   PID: $(cat "$PID_FILE")"
    echo "   Logs: database-viewer.log"
    echo ""
    echo "Commands:"
    echo "   View logs:  tail -f database-viewer.log"
    echo "   Stop:       ./scripts/stop-database-viewer.sh"
    echo ""
else
    echo "❌ Failed to start database viewer"
    echo "   Check logs: cat database-viewer.log"
    rm "$PID_FILE"
    exit 1
fi
