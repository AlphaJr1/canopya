#!/bin/bash

# ============================================================
# Aeropon - Log Viewer Helper
# ============================================================
# Script untuk melihat logs dengan mudah
# ============================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

print_header() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

show_menu() {
    clear
    echo -e "${CYAN}"
    echo "============================================================"
    echo "           📝 AEROPON - LOG VIEWER 📝"
    echo "============================================================"
    echo -e "${NC}"
    echo ""
    echo "Pilih log yang ingin dilihat:"
    echo ""
    echo "  1) FastAPI Chatbot"
    echo "  2) Simulator Generator"
    echo "  3) Simulator API"
    echo "  4) WhatsApp Webhook"
    echo "  5) Dashboard"
    echo "  6) Database Viewer"
    echo "  7) Semua Logs (tail -f)"
    echo "  8) WhatsApp QR Code"
    echo "  9) List semua log files"
    echo "  0) Exit"
    echo ""
    echo -n "Pilihan [0-9]: "
}

view_log() {
    local log_file=$1
    local service_name=$2
    
    if [ -f "$log_file" ]; then
        print_header "$service_name LOG"
        echo ""
        echo -e "${BLUE}File: $log_file${NC}"
        echo -e "${BLUE}Press Ctrl+C to exit${NC}"
        echo ""
        sleep 2
        tail -f "$log_file"
    else
        echo -e "${RED}❌ Log file not found: $log_file${NC}"
        echo ""
        echo "Press Enter to continue..."
        read
    fi
}

show_qr() {
    if [ -f "$LOG_DIR/whatsapp.log" ]; then
        print_header "WHATSAPP QR CODE"
        echo ""
        grep -A 20 'QR CODE' "$LOG_DIR/whatsapp.log" | tail -25
        echo ""
        echo "Press Enter to continue..."
        read
    else
        echo -e "${RED}❌ WhatsApp log not found${NC}"
        echo ""
        echo "Press Enter to continue..."
        read
    fi
}

list_logs() {
    print_header "LOG FILES"
    echo ""
    if [ -d "$LOG_DIR" ]; then
        ls -lh "$LOG_DIR"
    else
        echo -e "${RED}❌ Logs directory not found${NC}"
    fi
    echo ""
    echo "Press Enter to continue..."
    read
}

view_all_logs() {
    print_header "ALL LOGS (Real-time)"
    echo ""
    echo -e "${BLUE}Monitoring all log files...${NC}"
    echo -e "${BLUE}Press Ctrl+C to exit${NC}"
    echo ""
    sleep 2
    tail -f "$LOG_DIR"/*.log
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            view_log "$LOG_DIR/fastapi.log" "FASTAPI CHATBOT"
            ;;
        2)
            view_log "$LOG_DIR/simulator_generator.log" "SIMULATOR GENERATOR"
            ;;
        3)
            view_log "$LOG_DIR/simulator_api.log" "SIMULATOR API"
            ;;
        4)
            view_log "$LOG_DIR/whatsapp.log" "WHATSAPP WEBHOOK"
            ;;
        5)
            view_log "$LOG_DIR/dashboard.log" "DASHBOARD"
            ;;
        6)
            view_log "$LOG_DIR/database_viewer.log" "DATABASE VIEWER"
            ;;
        7)
            view_all_logs
            ;;
        8)
            show_qr
            ;;
        9)
            list_logs
            ;;
        0)
            echo ""
            echo -e "${GREEN}Goodbye! 👋${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 2
            ;;
    esac
done
