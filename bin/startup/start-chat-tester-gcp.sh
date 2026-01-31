#!/bin/bash
cd /home/adrianalfajri/canopya

export PATH=$PATH:~/.local/bin
source .env

LOG_DIR=".run/logs"
mkdir -p $LOG_DIR

LOG_FILE="$LOG_DIR/chat-tester.log"

echo "🚀 Starting Chat Tester..."
nohup python3 -m streamlit run services/dashboardrag/chat_tester.py \
  --server.port 3001 \
  --server.address 0.0.0.0 \
  > $LOG_FILE 2>&1 &

PID=$!
echo $PID > .run/chat-tester.pid
echo "✅ Chat Tester started (PID: $PID)"
echo "📝 Logs: $LOG_FILE"
