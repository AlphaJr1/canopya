#!/bin/bash
cd /home/adrianalfajri/canopya

PID_FILE=".run/rag-dashboard.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "🛑 Stopping RAG Dashboard (PID: $PID)..."
    kill $PID 2>/dev/null
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ Force killing..."
        kill -9 $PID 2>/dev/null
    fi
    
    rm -f $PID_FILE
    echo "✅ RAG Dashboard stopped"
else
    echo "⚠️ PID file not found, trying pkill..."
    pkill -f "streamlit run services/dashboardrag/app.py"
    echo "✅ Done"
fi
