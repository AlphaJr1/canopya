#!/bin/bash

# ============================================================
# Aeropon - Master Startup Script (Auto Port Detection)
# ============================================================
# Script untuk menjalankan semua komponen sistem Aeropon:
# 1. FastAPI Chatbot (default port 8000, auto-detect jika terpakai)
# 2. Simulator IoT + LSTM (default port 3456, auto-detect jika terpakai)
# 3. WhatsApp Webhook via Baileys (default port 3000, auto-detect jika terpakai)
# 4. Dashboard Streamlit (default port 8501, auto-detect jika terpakai)
#
# Jika port default terpakai, akan otomatis mencari port kosong
# Semua log disimpan di folder logs/ dengan nama terpisah
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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PORT_INFO_FILE="$PROJECT_ROOT/.ports.info"

# Create logs directory
mkdir -p "$LOG_DIR"

# Clear screen
clear

echo -e "${CYAN}"
echo "============================================================"
echo "           🌱 AEROPON - STARTUP MASTER SCRIPT 🌱"
echo "============================================================"
echo -e "${NC}"
echo ""

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

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

find_free_port() {
    local default_port=$1
    local port=$default_port
    local max_attempts=100
    
    # Check if default port is free
    if ! check_port $port; then
        echo $port
        return 0
    fi
    
    print_warning "Port $default_port is in use, searching for alternative..." >&2
    
    # Find next available port
    for ((i=1; i<=$max_attempts; i++)); do
        port=$((default_port + i))
        
        # Skip common ports to avoid conflicts
        if [ $port -eq 8080 ] || [ $port -eq 8081 ] || [ $port -eq 3001 ]; then
            continue
        fi
        
        if ! check_port $port; then
            print_success "Found free port: $port" >&2
            echo $port
            return 0
        fi
    done
    
    # If no port found, return error
    echo "0"
    return 1
}

wait_for_port() {
    local port=$1
    local service=$2
    local max_wait=30
    local waited=0
    
    echo -n "   Waiting for $service to start on port $port"
    while [ $waited -lt $max_wait ]; do
        if check_port $port; then
            echo ""
            print_success "$service is up on port $port"
            return 0
        fi
        echo -n "."
        sleep 1
        waited=$((waited + 1))
    done
    echo ""
    print_error "$service failed to start on port $port after ${max_wait}s"
    return 1
}

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================

print_step "Running pre-flight checks..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found!"
    exit 1
fi
print_success "Python3 detected: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js not found!"
    exit 1
fi
print_success "Node.js detected: $(node --version)"

# Check virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_error "Virtual environment not found at $PROJECT_ROOT/venv"
    print_info "Create it with: python3 -m venv venv"
    exit 1
fi
print_success "Virtual environment found"

# Check Qdrant
if ! curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    print_warning "Qdrant not detected on port 6333"
    print_info "Start with: docker run -p 6333:6333 qdrant/qdrant"
else
    print_success "Qdrant is running on port 6333"
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_warning "Ollama not detected on port 11434"
    print_info "Start with: ollama serve"
else
    print_success "Ollama is running on port 11434"
fi

echo ""
print_success "All pre-flight checks passed!"
echo ""

# ============================================================
# FIND FREE PORTS
# ============================================================

print_step "Finding available ports..."
echo ""

# Find free ports for each service
FASTAPI_PORT=$(find_free_port 8000)
if [ "$FASTAPI_PORT" == "0" ]; then
    print_error "Could not find free port for FastAPI"
    exit 1
fi
if [ "$FASTAPI_PORT" != "8000" ]; then
    print_info "FastAPI will use port $FASTAPI_PORT (default 8000 was busy)"
else
    print_success "FastAPI will use default port 8000"
fi

SIMULATOR_PORT=$(find_free_port 3456)
if [ "$SIMULATOR_PORT" == "0" ]; then
    print_error "Could not find free port for Simulator"
    exit 1
fi
if [ "$SIMULATOR_PORT" != "3456" ]; then
    print_info "Simulator will use port $SIMULATOR_PORT (default 3456 was busy)"
else
    print_success "Simulator will use default port 3456"
fi

WHATSAPP_PORT=$(find_free_port 3000)
if [ "$WHATSAPP_PORT" == "0" ]; then
    print_error "Could not find free port for WhatsApp"
    exit 1
fi
if [ "$WHATSAPP_PORT" != "3000" ]; then
    print_info "WhatsApp will use port $WHATSAPP_PORT (default 3000 was busy)"
else
    print_success "WhatsApp will use default port 3000"
fi

DASHBOARD_PORT=$(find_free_port 8501)
if [ "$DASHBOARD_PORT" == "0" ]; then
    print_error "Could not find free port for Dashboard"
    exit 1
fi
if [ "$DASHBOARD_PORT" != "8501" ]; then
    print_info "Dashboard will use port $DASHBOARD_PORT (default 8501 was busy)"
else
    print_success "Dashboard will use default port 8501"
fi

DB_VIEWER_PORT=$(find_free_port 8502)
if [ "$DB_VIEWER_PORT" == "0" ]; then
    print_error "Could not find free port for Database Viewer"
    exit 1
fi
if [ "$DB_VIEWER_PORT" != "8502" ]; then
    print_info "Database Viewer will use port $DB_VIEWER_PORT (default 8502 was busy)"
else
    print_success "Database Viewer will use default port 8502"
fi

# Save port info to file
cat > "$PORT_INFO_FILE" << EOF
FASTAPI_PORT=$FASTAPI_PORT
SIMULATOR_PORT=$SIMULATOR_PORT
WHATSAPP_PORT=$WHATSAPP_PORT
DASHBOARD_PORT=$DASHBOARD_PORT
DB_VIEWER_PORT=$DB_VIEWER_PORT
EOF

echo ""
print_success "All ports allocated!"
echo ""

# ============================================================
# START SERVICES
# ============================================================

echo -e "${CYAN}"
echo "============================================================"
echo "                    STARTING SERVICES"
echo "============================================================"
echo -e "${NC}"
echo ""

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# ============================================================
# 1. START FASTAPI CHATBOT
# ============================================================

print_step "1/4 Starting FastAPI Chatbot (Port $FASTAPI_PORT)..."
cd "$PROJECT_ROOT/api"

nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port $FASTAPI_PORT \
    --log-level info \
    > "$LOG_DIR/fastapi.log" 2>&1 &

FASTAPI_PID=$!
echo $FASTAPI_PID > "$PROJECT_ROOT/.fastapi.pid"

if wait_for_port $FASTAPI_PORT "FastAPI"; then
    print_info "Log: $LOG_DIR/fastapi.log"
    print_info "PID: $FASTAPI_PID"
    echo "FASTAPI_PORT=$FASTAPI_PORT" >> "$LOG_DIR/fastapi.log"
else
    print_error "FastAPI failed to start. Check logs: $LOG_DIR/fastapi.log"
    exit 1
fi

echo ""

# ============================================================
# 2. START SIMULATOR
# ============================================================

print_step "2/4 Starting IoT Simulator + LSTM (Port $SIMULATOR_PORT)..."
cd "$PROJECT_ROOT/simulator"

# Update config.json with new port
python3 << EOF
import json
with open('config.json', 'r') as f:
    config = json.load(f)
config['server']['port'] = $SIMULATOR_PORT
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
EOF

# Start background generator (using venv python)
nohup "$PROJECT_ROOT/venv/bin/python" background_generator.py \
    > "$LOG_DIR/simulator_generator.log" 2>&1 &

BG_GEN_PID=$!
echo $BG_GEN_PID > "$PROJECT_ROOT/.simulator_generator.pid"
print_info "Background generator started (PID: $BG_GEN_PID)"

sleep 2

# Start simulator API server (using venv python)
nohup "$PROJECT_ROOT/venv/bin/python" server.py \
    > "$LOG_DIR/simulator_api.log" 2>&1 &

SIMULATOR_PID=$!
echo $SIMULATOR_PID > "$PROJECT_ROOT/.simulator_api.pid"

if wait_for_port $SIMULATOR_PORT "Simulator API"; then
    print_info "Log (Generator): $LOG_DIR/simulator_generator.log"
    print_info "Log (API): $LOG_DIR/simulator_api.log"
    print_info "PID (Generator): $BG_GEN_PID"
    print_info "PID (API): $SIMULATOR_PID"
    echo "SIMULATOR_PORT=$SIMULATOR_PORT" >> "$LOG_DIR/simulator_api.log"
else
    print_error "Simulator failed to start. Check logs."
    exit 1
fi

echo ""

# ============================================================
# 3. START WHATSAPP WEBHOOK
# ============================================================

print_step "3/6 Starting WhatsApp Webhook (Port $WHATSAPP_PORT)..."
cd "$PROJECT_ROOT/whatsapp-webhook"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_info "Installing npm dependencies..."
    npm install
fi

# Create required directories
mkdir -p logs conversations auth_info

# Set environment variable for port
export WHATSAPP_HTTP_PORT=$WHATSAPP_PORT
export FASTAPI_URL="http://localhost:$FASTAPI_PORT"

# Start WhatsApp webhook
node index.js > "$LOG_DIR/whatsapp.log" 2>&1 &

WHATSAPP_PID=$!
echo $WHATSAPP_PID > "$PROJECT_ROOT/.whatsapp.pid"
print_info "WhatsApp webhook started (PID: $WHATSAPP_PID)"
print_info "Log: $LOG_DIR/whatsapp.log"

# Check if already logged in
if [ -f "auth_info/creds.json" ]; then
    print_success "WhatsApp session found - auto login"
    
    # Wait for HTTP server to start (happens after login)
    if wait_for_port $WHATSAPP_PORT "WhatsApp HTTP"; then
        print_success "WhatsApp HTTP server ready on port $WHATSAPP_PORT"
        echo "WHATSAPP_PORT=$WHATSAPP_PORT" >> "$LOG_DIR/whatsapp.log"
    else
        print_warning "WhatsApp HTTP server tidak start, tapi proses berjalan"
    fi
else
    print_warning "WhatsApp belum login - menunggu QR code..."
    echo ""
    
    # Wait for QR code to appear in log
    print_info "Menunggu QR code (max 30 detik)..."
    waited=0
    max_wait=30
    
    while [ $waited -lt $max_wait ]; do
        if grep -q "QR CODE" "$LOG_DIR/whatsapp.log" 2>/dev/null; then
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done
    
    if [ $waited -ge $max_wait ]; then
        print_error "QR code tidak muncul dalam $max_wait detik"
        print_info "Cek log: tail -f $LOG_DIR/whatsapp.log"
    else
        echo ""
        echo -e "${YELLOW}"
        echo "============================================================"
        echo "           📱 SCAN QR CODE DENGAN WHATSAPP ANDA"
        echo "============================================================"
        echo -e "${NC}"
        
        # Display QR code from log
        tail -100 "$LOG_DIR/whatsapp.log" | grep -A 35 "QR CODE" | head -40
        
        echo ""
        echo -e "${YELLOW}============================================================${NC}"
        echo -e "${CYAN}CARA SCAN:${NC}"
        echo "  1. Buka WhatsApp di HP"
        echo "  2. Tap Menu (⋮) > Linked Devices"
        echo "  3. Tap 'Link a Device'"
        echo "  4. Scan QR code di atas"
        echo -e "${YELLOW}============================================================${NC}"
        echo ""
        
        # Wait for connection
        print_info "Menunggu WhatsApp connect (max 120 detik)..."
        print_info "Silakan scan QR code di atas..."
        echo ""
        
        waited=0
        max_wait=120
        
        while [ $waited -lt $max_wait ]; do
            # Check if connected (look for "WhatsApp terhubung" or HTTP server started)
            if grep -q "WhatsApp terhubung" "$LOG_DIR/whatsapp.log" 2>/dev/null || \
               grep -q "HTTP server untuk simulator started" "$LOG_DIR/whatsapp.log" 2>/dev/null; then
                echo ""
                print_success "WhatsApp berhasil terhubung!"
                
                # Wait a bit for HTTP server to fully start
                sleep 3
                
                if check_port $WHATSAPP_PORT; then
                    print_success "WhatsApp HTTP server ready on port $WHATSAPP_PORT"
                    echo "WHATSAPP_PORT=$WHATSAPP_PORT" >> "$LOG_DIR/whatsapp.log"
                fi
                break
            fi
            
            # Show progress
            echo -n "."
            sleep 2
            waited=$((waited + 2))
        done
        
        echo ""
        
        if [ $waited -ge $max_wait ]; then
            print_warning "Timeout menunggu WhatsApp connect"
            print_info "WhatsApp webhook tetap berjalan di background"
            print_info "Anda bisa scan QR code nanti dengan: tail -f $LOG_DIR/whatsapp.log"
        fi
    fi
fi

echo ""

# ============================================================
# 4. START RAG DASHBOARD
# ============================================================

print_step "4/6 Starting RAG Dashboard (Port $DASHBOARD_PORT)..."
cd "$PROJECT_ROOT"

nohup streamlit run rag_dashboard.py \
    --server.port $DASHBOARD_PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > "$LOG_DIR/dashboard.log" 2>&1 &

DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$PROJECT_ROOT/.dashboard.pid"

if wait_for_port $DASHBOARD_PORT "RAG Dashboard"; then
    print_info "Log: $LOG_DIR/dashboard.log"
    print_info "PID: $DASHBOARD_PID"
    echo "DASHBOARD_PORT=$DASHBOARD_PORT" >> "$LOG_DIR/dashboard.log"
else
    print_error "RAG Dashboard failed to start. Check logs: $LOG_DIR/dashboard.log"
    exit 1
fi

echo ""

# ============================================================
# 4.5. START NGROK TUNNEL
# ============================================================

print_step "4.5/6 Starting Ngrok Tunnel for RAG Dashboard..."

# Start ngrok
bash "$PROJECT_ROOT/bin/start-ngrok.sh" > "$LOG_DIR/ngrok.log" 2>&1 &
sleep 4

# Get ngrok URL
if [ -f "$PROJECT_ROOT/.ngrok_url" ]; then
    NGROK_URL=$(cat "$PROJECT_ROOT/.ngrok_url")
    print_success "Ngrok tunnel started: $NGROK_URL"
    print_info "Log: $LOG_DIR/ngrok.log"
    
    # Set environment variable for chatbot
    export RAG_DASHBOARD_URL="$NGROK_URL"
    echo "RAG_DASHBOARD_URL=$NGROK_URL" >> "$PORT_INFO_FILE"
else
    print_warning "Ngrok URL not found. Dashboard will use localhost."
    print_info "You can start ngrok manually: ./bin/start-ngrok.sh"
fi

echo ""

# ============================================================
# 5. START DATABASE VIEWER
# ============================================================

print_step "5/6 Starting Database Viewer (Port $DB_VIEWER_PORT)..."
cd "$PROJECT_ROOT"

nohup streamlit run database_viewer.py \
    --server.port $DB_VIEWER_PORT \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false \
    > "$LOG_DIR/database_viewer.log" 2>&1 &

DB_VIEWER_PID=$!
echo $DB_VIEWER_PID > "$PROJECT_ROOT/.database_viewer.pid"

if wait_for_port $DB_VIEWER_PORT "Database Viewer"; then
    print_info "Log: $LOG_DIR/database_viewer.log"
    print_info "PID: $DB_VIEWER_PID"
    echo "DB_VIEWER_PORT=$DB_VIEWER_PORT" >> "$LOG_DIR/database_viewer.log"
else
    print_error "Database Viewer failed to start. Check logs: $LOG_DIR/database_viewer.log"
    exit 1
fi

echo ""

# ============================================================
# SUMMARY
# ============================================================

echo -e "${GREEN}"
echo "============================================================"
echo "              ✅ ALL SERVICES STARTED SUCCESSFULLY"
echo "============================================================"
echo -e "${NC}"
echo ""

echo -e "${CYAN}📊 Service URLs:${NC}"
echo "  • FastAPI Chatbot:     http://localhost:$FASTAPI_PORT"
echo "  • FastAPI Docs:        http://localhost:$FASTAPI_PORT/docs"
echo "  • Simulator API:       http://localhost:$SIMULATOR_PORT"
echo "  • Simulator Docs:      http://localhost:$SIMULATOR_PORT/docs"
echo "  • WhatsApp HTTP:       http://localhost:$WHATSAPP_PORT/health"
echo "  • RAG Dashboard:       http://localhost:$DASHBOARD_PORT"
if [ -f "$PROJECT_ROOT/.ngrok_url" ]; then
    NGROK_URL=$(cat "$PROJECT_ROOT/.ngrok_url")
    echo "  • RAG Dashboard (Public): $NGROK_URL"
fi
echo "  • Database Viewer:     http://localhost:$DB_VIEWER_PORT"
echo ""

echo -e "${CYAN}📝 Log Files:${NC}"
echo "  • FastAPI:             $LOG_DIR/fastapi.log"
echo "  • Simulator (Gen):     $LOG_DIR/simulator_generator.log"
echo "  • Simulator (API):     $LOG_DIR/simulator_api.log"
echo "  • WhatsApp:            $LOG_DIR/whatsapp.log"
echo "  • RAG Dashboard:       $LOG_DIR/dashboard.log"
echo "  • Ngrok:               $LOG_DIR/ngrok.log"
echo "  • Database Viewer:     $LOG_DIR/database_viewer.log"
echo ""

echo -e "${CYAN}🔢 Process IDs:${NC}"
echo "  • FastAPI:             $FASTAPI_PID"
echo "  • Simulator (Gen):     $BG_GEN_PID"
echo "  • Simulator (API):     $SIMULATOR_PID"
echo "  • WhatsApp:            $WHATSAPP_PID"
echo "  • Dashboard:           $DASHBOARD_PID"
echo "  • Database Viewer:     $DB_VIEWER_PID"
echo ""

echo -e "${CYAN}🔌 Port Allocation:${NC}"
echo "  • FastAPI:             $FASTAPI_PORT $([ "$FASTAPI_PORT" != "8000" ] && echo "(default: 8000)" || echo "")"
echo "  • Simulator:           $SIMULATOR_PORT $([ "$SIMULATOR_PORT" != "3456" ] && echo "(default: 3456)" || echo "")"
echo "  • WhatsApp:            $WHATSAPP_PORT $([ "$WHATSAPP_PORT" != "3000" ] && echo "(default: 3000)" || echo "")"
echo "  • Dashboard:           $DASHBOARD_PORT $([ "$DASHBOARD_PORT" != "8501" ] && echo "(default: 8501)" || echo "")"
echo "  • Database Viewer:     $DB_VIEWER_PORT $([ "$DB_VIEWER_PORT" != "8502" ] && echo "(default: 8502)" || echo "")"
echo ""

print_info "Port info saved to: $PORT_INFO_FILE"
echo ""

echo -e "${CYAN}🛠️  Useful Commands:${NC}"
echo "  • View all logs:       tail -f $LOG_DIR/*.log"
echo "  • Stop all services:   ./stop-all.sh"
echo "  • Check status:        ./status-all.sh"
echo "  • View port info:      cat $PORT_INFO_FILE"
echo ""

echo -e "${GREEN}🎉 Aeropon is ready for testing!${NC}"
echo ""
