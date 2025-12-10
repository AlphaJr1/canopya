#!/bin/bash

# Script untuk melihat statistik percakapan

CONV_DIR="conversations"

if [ ! -d "$CONV_DIR" ]; then
    echo "❌ Folder conversations tidak ditemukan"
    exit 1
fi

echo "📊 Statistik Percakapan WhatsApp Bot"
echo "=========================================="
echo ""

# Hitung jumlah file percakapan
TOTAL_CONVERSATIONS=$(ls -1 "$CONV_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')

if [ "$TOTAL_CONVERSATIONS" -eq 0 ]; then
    echo "ℹ️  Belum ada percakapan tersimpan"
    exit 0
fi

echo "📁 Total Percakapan: $TOTAL_CONVERSATIONS"
echo ""

# List semua percakapan dengan info
echo "Daftar Percakapan:"
echo "----------------------------------------"

for file in "$CONV_DIR"/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        
        # Extract info dari JSON
        session_id=$(grep -o '"session_id": "[^"]*"' "$file" | head -1 | cut -d'"' -f4)
        phone=$(grep -o '"phone_number": "[^"]*"' "$file" | head -1 | cut -d'"' -f4)
        last_activity=$(grep -o '"last_activity": "[^"]*"' "$file" | head -1 | cut -d'"' -f4)
        message_count=$(grep -c '"role":' "$file")
        
        echo "📱 Session: $session_id"
        echo "   Phone: $phone"
        echo "   Messages: $message_count"
        echo "   Last Activity: $last_activity"
        echo "   File: $filename"
        echo ""
    fi
done

echo "=========================================="
echo ""
echo "💡 Tips:"
echo "  - Lihat detail percakapan: cat conversations/<filename>.json"
echo "  - Format JSON pretty: cat conversations/<filename>.json | python -m json.tool"
