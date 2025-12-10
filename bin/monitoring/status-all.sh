#!/bin/bash

# ============================================================
# Aeropon - Status Check Script (Auto Port Detection)
# ============================================================
# Script untuk mengecek status semua komponen sistem Aeropon
# Membaca port dari .ports.info jika ada
# ============================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT_INFO_FILE="$PROJECT_ROOT/.ports.info"

# Default ports
FASTAPI_PORT=8000
SIMULATOR_PORT=3456
WHATSAPP_PORT=3000
DASHBOARD_PORT=8501
DB_VIEWER_PORT=8502

# Load actual ports if file exists
if [ -f "$PORT_INFO_FILE" ]; then
    source "$PORT_INFO_FILE"
fi

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

print_header() {
    echo -e "${CYAN}$1${NC}"
}

check_service() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$service_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if ps -p $pid > /dev/null 2>&1; then
            print_success "Running (PID: $pid)"
            
            # Get process info
            local cpu_mem=$(ps -p $pid -o %cpu,%mem | tail -1)
            echo "   CPU/MEM: $cpu_mem"
            
            # Get uptime
            local start_time=$(ps -p $pid -o lstart= | xargs)
            echo "   Started: $start_time"
        else
            print_error "Not running (stale PID file)"
        fi
    else
        print_error "Not running (no PID file)"
    fi
    
    # Check port
    if [ -n "$port" ]; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_success "Port $port is listening"
            
            # Try to get health status if available
            case $service_name in
                "FastAPI Chatbot")
                    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                        echo "   Health: OK"
                    fi
                    ;;
                "Simulator API")
                    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                        echo "   Health: OK"
                    fi
                    ;;
                "WhatsApp HTTP")
                    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                        echo "   Health: OK"
                    fi
                    ;;
            esac
        else
            print_error "Port $port is not listening"
        fi
    fi
    
    echo ""
}

check_dependency() {
    local dep_name=$1
    local check_cmd=$2
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        print_success "$dep_name is running"
    else
        print_error "$dep_name is not running"
    fi
}

# ============================================================
# MAIN
# ============================================================

clear

echo -e "${CYAN}"
echo "============================================================"
echo "           📊 AEROPON - STATUS CHECK REPORT 📊"
echo "============================================================"
echo -e "${NC}"
echo ""

# Show port info if available
if [ -f "$PORT_INFO_FILE" ]; then
    print_info "Using ports from: $PORT_INFO_FILE"
    echo "   FastAPI: $FASTAPI_PORT | Simulator: $SIMULATOR_PORT | WhatsApp: $WHATSAPP_PORT | Dashboard: $DASHBOARD_PORT | DB Viewer: $DB_VIEWER_PORT"
    echo ""
fi

# Check dependencies first
print_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_header "DEPENDENCIES"
print_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dependency "Qdrant (port 6333)" "curl -s http://localhost:6333/collections"
check_dependency "Ollama (port 11434)" "curl -s http://localhost:11434/api/tags"

echo ""

# Check services
check_service "FastAPI Chatbot" "$PROJECT_ROOT/.fastapi.pid" "$FASTAPI_PORT"
check_service "Simulator Generator" "$PROJECT_ROOT/.simulator_generator.pid" ""
check_service "Simulator API" "$PROJECT_ROOT/.simulator_api.pid" "$SIMULATOR_PORT"
check_service "WhatsApp Webhook" "$PROJECT_ROOT/.whatsapp.pid" "$WHATSAPP_PORT"
check_service "Dashboard" "$PROJECT_ROOT/.dashboard.pid" "$DASHBOARD_PORT"
check_service "Database Viewer" "$PROJECT_ROOT/.database_viewer.pid" "$DB_VIEWER_PORT"

# Summary
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SUMMARY${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Count running services
RUNNING=0
TOTAL=6

for pid_file in "$PROJECT_ROOT/.fastapi.pid" "$PROJECT_ROOT/.simulator_generator.pid" "$PROJECT_ROOT/.simulator_api.pid" "$PROJECT_ROOT/.whatsapp.pid" "$PROJECT_ROOT/.dashboard.pid" "$PROJECT_ROOT/.database_viewer.pid"; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            RUNNING=$((RUNNING + 1))
        fi
    fi
done

echo ""
if [ $RUNNING -eq $TOTAL ]; then
    print_success "All services running ($RUNNING/$TOTAL)"
elif [ $RUNNING -eq 0 ]; then
    print_error "No services running ($RUNNING/$TOTAL)"
else
    print_warning "Some services running ($RUNNING/$TOTAL)"
fi

echo ""
print_info "Service URLs:"
echo "  • FastAPI:     http://localhost:$FASTAPI_PORT/docs"
echo "  • Simulator:   http://localhost:$SIMULATOR_PORT/docs"
echo "  • WhatsApp:    http://localhost:$WHATSAPP_PORT/health"
echo "  • Dashboard:   http://localhost:$DASHBOARD_PORT"
echo "  • DB Viewer:   http://localhost:$DB_VIEWER_PORT"

echo ""
print_info "Logs directory: $PROJECT_ROOT/logs/"
echo ""
