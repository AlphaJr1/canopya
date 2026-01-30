#!/bin/bash

# Start Database Manager Dashboard
# Script untuk menjalankan dashboard database manager

echo "🗄️ Starting Database Manager Dashboard..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit tidak terinstall!"
    echo "Install dengan: pip install streamlit"
    exit 1
fi

# Set port
PORT=8503

# Ensure logs directory exists
mkdir -p logs

# Log file
LOG_FILE="logs/db_manager.log"

# Remove old database_viewer.log if exists
if [ -f "logs/database_viewer.log" ]; then
    echo "🗑️  Removing old database_viewer.log..."
    rm -f logs/database_viewer.log
fi

echo "📊 Dashboard akan berjalan di: http://localhost:$PORT"
echo "📁 Database: aeropon.db"
echo "📄 JSON Directory: data/conversations/"
echo "📝 Log file: $LOG_FILE"
echo ""
echo "Tekan Ctrl+C untuk menghentikan dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Write port to log file for detection
echo "" > "$LOG_FILE"
echo "  You can now view your Streamlit app in your browser." >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "  URL: http://localhost:$PORT" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "DB_MANAGER_PORT=$PORT" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Run streamlit and redirect output to log file
streamlit run services/dbmanager/db_manager.py --server.port=$PORT --server.headless=true >> "$LOG_FILE" 2>&1
