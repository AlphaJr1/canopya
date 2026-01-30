#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR=".run/logs/active"
PID_DIR=".run/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

LOG_FILE="$LOG_DIR/rag-dashboard.log"
PID_FILE="$PID_DIR/rag-dashboard.pid"
PORT=8507

echo "🚀 Starting RAG Dashboard..."

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  RAG Dashboard sudah berjalan (PID: $OLD_PID)"
        echo "   Gunakan bin/shutdown/stop-rag-dashboard.sh untuk menghentikan"
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

echo "📊 Starting Streamlit RAG Dashboard on port $PORT..."
echo "   Log: $LOG_FILE"

PYTHONPATH="$PROJECT_ROOT" nohup streamlit run services/dashboardrag/rag_dashboard.py \
    --server.port $PORT \
    --server.headless true \
    --server.address localhost \
    --browser.gatherUsageStats false \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ RAG Dashboard started successfully!"
    echo "   PID: $PID"
    echo "   URL: http://localhost:$PORT"
    echo "   Log: $LOG_FILE"
    
    echo "RAG_DASHBOARD_URL=http://localhost:$PORT" >> .ports.info
    
    echo ""
    echo "📝 Dashboard ini menampilkan visualisasi RAG process:"
    echo "   - Query user"
    echo "   - Retrieved documents dengan scores"
    echo "   - Bot response"
    echo ""
    echo "   Akses via link yang dikirim chatbot setelah RAG query"
else
    echo "❌ Failed to start RAG Dashboard"
    echo "   Check log: $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
