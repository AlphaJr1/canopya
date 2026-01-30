#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

PID_FILE=".run/pids/rag-dashboard.pid"

echo "🛑 Stopping RAG Dashboard..."

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  PID file tidak ditemukan. Dashboard mungkin tidak berjalan."
    
    PIDS=$(lsof -ti:8507)
    if [ ! -z "$PIDS" ]; then
        echo "   Menemukan process di port 8507, menghentikan..."
        kill -9 $PIDS
        echo "✅ Process dihentikan"
    fi
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "   Menghentikan process (PID: $PID)..."
    kill -15 $PID
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Force killing..."
        kill -9 $PID
    fi
    
    echo "✅ RAG Dashboard stopped"
else
    echo "⚠️  Process tidak ditemukan (PID: $PID)"
fi

rm "$PID_FILE"

sed -i '' '/RAG_DASHBOARD_URL=/d' .ports.info 2>/dev/null || true

echo "🧹 Cleanup complete"
