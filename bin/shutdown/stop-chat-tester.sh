#!/bin/bash

# Stop Chat Tester Streamlit App

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

PID_FILE=".run/pids/chat-tester.pid"

echo "🛑 Stopping Chat Tester..."

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  PID file tidak ditemukan"
    echo "   Chat Tester mungkin tidak running"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "   Stopping process (PID: $PID)..."
    kill "$PID"
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "   Force kill..."
        kill -9 "$PID"
    fi
    
    echo "✅ Chat Tester stopped"
else
    echo "⚠️  Process tidak ditemukan (PID: $PID)"
fi

rm "$PID_FILE"
echo "🧹 Cleanup complete"
