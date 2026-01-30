#!/bin/bash

# Quick reference untuk monitoring logs

echo "📊 AEROPON - Log Monitoring Quick Reference"
echo "============================================"
echo ""

RUN_DIR=".run"
LOG_DIR="$RUN_DIR/logs/active"

echo "📁 Log Directory: $LOG_DIR"
echo ""

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Log directory tidak ditemukan!"
    exit 1
fi

echo "📝 Available Logs:"
ls -lh "$LOG_DIR" 2>/dev/null | grep -v "^total" | awk '{print "  - " $9 " (" $5 ")"}'
echo ""

echo "🔍 Quick Commands:"
echo "  # View all active logs"
echo "  tail -f $LOG_DIR/*.log"
echo ""
echo "  # View specific log"
echo "  tail -f $LOG_DIR/fastapi.log"
echo "  tail -f $LOG_DIR/ngrok.log"
echo ""
echo "  # Search in logs"
echo "  grep 'error' $LOG_DIR/*.log"
echo ""
echo "  # Ngrok web interface"
echo "  open http://localhost:4040"
echo ""

echo "📊 Current Status:"
if [ -d "$RUN_DIR/pids" ]; then
    echo "  Running services:"
    for pid_file in "$RUN_DIR/pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            service_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "    ✅ $service_name (PID: $pid)"
            else
                echo "    ❌ $service_name (stale PID: $pid)"
            fi
        fi
    done
else
    echo "  ❌ No services running"
fi
echo ""
