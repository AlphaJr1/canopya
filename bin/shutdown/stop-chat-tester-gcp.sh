#!/bin/bash
cd /home/adrianalfajri/canopya

PID_FILE=".run/chat-tester.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "🛑 Stopping Chat Tester (PID: $PID)..."
    kill $PID 2>/dev/null
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ Force killing..."
        kill -9 $PID 2>/dev/null
    fi
    
    rm -f $PID_FILE
    echo "✅ Chat Tester stopped"
else
    echo "⚠️ PID file not found, trying pkill..."
    pkill -f "streamlit run services/dashboardrag/chat_tester.py"
    echo "✅ Done"
fi
