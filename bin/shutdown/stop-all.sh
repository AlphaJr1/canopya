#!/bin/bash

# ============================================================
# Aeropon - Master Shutdown Script
# ============================================================
# Script untuk menghentikan semua komponen sistem Aeropon
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
PID_DIR="$RUN_DIR/pids"
LOG_DIR="$RUN_DIR/logs/active"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if ps -p $pid > /dev/null 2>&1; then
            print_step "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null || true
            
            # Wait for process to stop
            local waited=0
            while ps -p $pid > /dev/null 2>&1 && [ $waited -lt 10 ]; do
                sleep 1
                waited=$((waited + 1))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "$service_name didn't stop gracefully, force killing..."
                kill -9 $pid 2>/dev/null || true
            fi
            
            print_success "$service_name stopped"
        else
            print_info "$service_name not running (stale PID file)"
        fi
        
        rm "$pid_file"
    else
        print_info "$service_name PID file not found (not running)"
    fi
}

# ============================================================
# MAIN
# ============================================================

clear

echo -e "${CYAN}"
echo "============================================================"
echo "          🛑 AEROPON - SHUTDOWN MASTER SCRIPT 🛑"
echo "============================================================"
echo -e "${NC}"
echo ""

print_step "Stopping all Aeropon services..."
echo ""

# Stop services in reverse order
stop_service "Database Viewer" "$PID_DIR/database_viewer.pid"
echo ""

stop_service "Dashboard" "$PID_DIR/dashboard.pid"
echo ""

# Stop ngrok
if [ -f "$PID_DIR/ngrok.pid" ]; then
    stop_service "Ngrok" "$PID_DIR/ngrok.pid"
    rm -f "$PROJECT_ROOT/.ngrok_url"
else
    # Try to kill ngrok by name
    if pgrep -x "ngrok" > /dev/null; then
        print_step "Stopping Ngrok..."
        pkill -x "ngrok"
        print_success "Ngrok stopped"
    fi
fi
echo ""

stop_service "WhatsApp Webhook" "$PID_DIR/whatsapp.pid"
echo ""

stop_service "Simulator API" "$PID_DIR/simulator_api.pid"
echo ""

stop_service "Simulator Generator" "$PID_DIR/simulator_generator.pid"
echo ""

stop_service "FastAPI Chatbot" "$PID_DIR/fastapi.pid"
echo ""

# Check for any remaining processes on our ports
print_step "Checking for remaining processes on ports..."
echo ""

PORTS=(8000 3456 3000 8501)
PORT_NAMES=("FastAPI" "Simulator" "WhatsApp HTTP" "Dashboard")

for i in "${!PORTS[@]}"; do
    port=${PORTS[$i]}
    name=${PORT_NAMES[$i]}
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port ($name) still in use"
        print_info "Kill with: kill \$(lsof -ti:$port)"
    else
        print_success "Port $port ($name) is free"
    fi
done

echo ""
echo -e "${GREEN}"
echo "============================================================"
echo "              ✅ ALL SERVICES STOPPED"
echo "============================================================"
echo -e "${NC}"
echo ""

print_info "Logs are preserved in $LOG_DIR directory"
print_info "To start again: ./start-all.sh"
echo ""
