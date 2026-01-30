#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR=".run/logs/active"
PID_DIR=".run/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

LOG_FILE="$LOG_DIR/fastapi.log"
PID_FILE="$PID_DIR/fastapi.pid"
PORT=8000

echo "🚀 Starting FastAPI Server..."

if [ -f "$PID_FILE" ]; then
    PID_CONTENT=$(cat "$PID_FILE")
    # Extract PID from JSON if needed
    if [[ "$PID_CONTENT" =~ \"pid\":\ ([0-9]+) ]]; then
        OLD_PID="${BASH_REMATCH[1]}"
    else
        OLD_PID=$(echo "$PID_CONTENT" | grep -oE '[0-9]+' | head -1)
    fi

    if [ ! -z "$OLD_PID" ] && ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  FastAPI sudah berjalan (PID: $OLD_PID)"
        echo "   Gunakan bin/shutdown/stop-fastapi.sh untuk menghentikan"
        exit 1
    else
        echo "🧹 Cleaning stale PID file..."
        rm "$PID_FILE"
    fi
fi

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port $PORT sudah digunakan"
    echo "   Process yang menggunakan:"
    lsof -i :$PORT
    exit 1
fi

source venv/bin/activate

echo "🔥 Starting FastAPI on port $PORT..."
echo "   Log: $LOG_FILE"

PYTHONPATH="$PROJECT_ROOT" nohup uvicorn services.fastapi.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ FastAPI started successfully!"
    echo "   PID: $PID"
    echo "   URL: http://localhost:$PORT"
    echo "   Docs: http://localhost:$PORT/docs"
    echo "   Log: $LOG_FILE"
else
    echo "❌ Failed to start FastAPI"
    echo "   Check log: $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
