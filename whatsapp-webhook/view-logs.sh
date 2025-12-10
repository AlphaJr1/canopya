#!/bin/bash

# Script untuk melihat log secara real-time

LOG_FILE="logs/webhook.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file tidak ditemukan: $LOG_FILE"
    echo "ℹ️  Jalankan bot terlebih dahulu dengan: ./start.sh"
    exit 1
fi

echo "📋 Monitoring log: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

tail -f "$LOG_FILE"
