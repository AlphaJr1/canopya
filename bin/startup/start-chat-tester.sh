#!/bin/bash

# Start Chat Tester Streamlit App

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR=".run/logs/active"
PID_DIR=".run/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

LOG_FILE="$LOG_DIR/chat-tester.log"
PID_FILE="$PID_DIR/chat-tester.pid"
PORT=8501

echo "🚀 Starting Chat Tester..."

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Chat Tester sudah berjalan (PID: $OLD_PID)"
        echo "   URL: http://localhost:$PORT"
        exit 0
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

echo "💬 Starting Streamlit Chat Tester on port $PORT..."
echo "   Log: $LOG_FILE"

PYTHONPATH="$PROJECT_ROOT" nohup streamlit run services/dashboardrag/chat_tester.py \
    --server.port $PORT \
    --server.headless true \
    --server.address localhost \
    --browser.gatherUsageStats false \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ Chat Tester started successfully!"
    echo "   PID: $PID"
    echo "   URL: http://localhost:$PORT"
    echo "   Log: $LOG_FILE"
    echo ""
    echo "📝 Gunakan interface ini untuk test chatbot tanpa WhatsApp"
    echo "   Otomatis connect ke FastAPI di http://localhost:8000"
else
    echo "❌ Failed to start Chat Tester"
    echo "   Check log: $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
