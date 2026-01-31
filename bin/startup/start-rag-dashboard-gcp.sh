#!/bin/bash
cd /home/adrianalfajri/canopya

export PATH=$PATH:~/.local/bin
source .env

LOG_DIR=".run/logs"
mkdir -p $LOG_DIR

LOG_FILE="$LOG_DIR/rag-dashboard.log"

echo "🚀 Starting RAG Dashboard..."
nohup python3 -m streamlit run services/dashboardrag/rag_dashboard.py \
  --server.port 3000 \
  --server.address 0.0.0.0 \
  > $LOG_FILE 2>&1 &

PID=$!
echo $PID > .run/rag-dashboard.pid
echo "✅ RAG Dashboard started (PID: $PID)"
echo "📝 Logs: $LOG_FILE"
