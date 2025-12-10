#!/bin/bash

# Script untuk backup percakapan

CONV_DIR="conversations"
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/conversations_backup_$DATE.tar.gz"

echo "💾 Backup Percakapan WhatsApp Bot"
echo "=========================================="
echo ""

# Cek apakah ada percakapan
if [ ! -d "$CONV_DIR" ] || [ -z "$(ls -A $CONV_DIR 2>/dev/null)" ]; then
    echo "❌ Tidak ada percakapan untuk di-backup"
    exit 1
fi

# Buat folder backup
mkdir -p "$BACKUP_DIR"

# Hitung jumlah file
FILE_COUNT=$(ls -1 "$CONV_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')

echo "📁 Jumlah file: $FILE_COUNT"
echo "📦 Membuat backup..."

# Buat tar.gz
tar -czf "$BACKUP_FILE" "$CONV_DIR"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "✅ Backup berhasil!"
    echo "📦 File: $BACKUP_FILE"
    echo "📊 Size: $BACKUP_SIZE"
    echo ""
    
    # List backups yang ada
    echo "Daftar Backup:"
    echo "----------------------------------------"
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9, "("$5")"}'
    
    echo ""
    echo "💡 Restore backup dengan:"
    echo "   tar -xzf $BACKUP_FILE"
else
    echo "❌ Backup gagal!"
    exit 1
fi
