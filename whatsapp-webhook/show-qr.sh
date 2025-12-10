#!/bin/bash

# Script untuk melihat QR code dari log

LOG_FILE="logs/webhook.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file tidak ditemukan: $LOG_FILE"
    echo "ℹ️  Jalankan bot terlebih dahulu dengan: ./start.sh"
    exit 1
fi

echo "🔍 Mencari QR Code di log..."
echo "=========================================="
echo ""

# Ambil QR code terakhir
QR_SECTION=$(grep -A 30 "QR CODE" "$LOG_FILE" | tail -n 35)

if [ -z "$QR_SECTION" ]; then
    echo "❌ QR Code tidak ditemukan di log"
    echo "ℹ️  Kemungkinan sudah login atau bot belum generate QR"
    echo ""
    echo "Cek status di log:"
    tail -n 20 "$LOG_FILE"
else
    echo "$QR_SECTION"
    echo ""
    echo "=========================================="
    echo "✅ Scan QR code di atas dengan WhatsApp Anda"
fi
