#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

PID_FILE=".run/pids/fastapi.pid"

echo "🛑 Stopping FastAPI Server..."

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  PID file tidak ditemukan. FastAPI mungkin tidak berjalan."
    
    PIDS=$(lsof -ti:8000)
    if [ ! -z "$PIDS" ]; then
        echo "   Menemukan process di port 8000, menghentikan..."
        kill -9 $PIDS
        echo "✅ Process dihentikan"
    fi
    exit 0
fi

PID_CONTENT=$(cat "$PID_FILE")

# Extract PID from JSON if needed
if [[ "$PID_CONTENT" =~ \"pid\":\ ([0-9]+) ]]; then
    PID="${BASH_REMATCH[1]}"
elif [[ "$PID_CONTENT" =~ [0-9]+ ]]; then
    PID=$(echo "$PID_CONTENT" | grep -oE '[0-9]+' | head -1)
fi

if [ ! -z "$PID" ] && ps -p $PID > /dev/null 2>&1; then
    echo "   Menghentikan process (PID: $PID)..."
    kill -15 $PID
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Force killing PID $PID..."
        kill -9 $PID
    fi
    echo "✅ FastAPI stopped by PID"
else
    echo "⚠️  Process tidak ditemukan via PID file, mengecek port 8000..."
    PIDS=$(lsof -ti:8000)
    if [ ! -z "$PIDS" ]; then
        echo "   Menemukan process di port 8000, menghentikan..."
        kill -9 $PIDS
        echo "✅ Process di port 8000 dihentikan"
    else
        echo "✅ Tidak ada process berjalan"
    fi
fi

rm "$PID_FILE"

echo "🧹 Cleanup complete"
