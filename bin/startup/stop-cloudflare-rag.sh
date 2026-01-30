#!/bin/bash

# ============================================================
# Stop Cloudflare Tunnel untuk RAG Dashboard
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
CF_PID_FILE="$RUN_DIR/pids/cloudflare-rag.pid"
CF_URL_FILE="$PROJECT_ROOT/.cloudflare_rag_url"

echo "🛑 Stopping Cloudflare Tunnel for RAG Dashboard..."

# Check PID file
if [ -f "$CF_PID_FILE" ]; then
    PID=$(cat "$CF_PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Stopping tunnel (PID: $PID)..."
        kill $PID
        
        # Wait for process to stop
        sleep 2
        
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Tunnel stopped successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  Force killing tunnel...${NC}"
            kill -9 $PID
        fi
    else
        echo -e "${YELLOW}⚠️  Process not running (stale PID file)${NC}"
    fi
    
    rm "$CF_PID_FILE"
else
    echo -e "${YELLOW}⚠️  PID file not found${NC}"
fi

# Kill any remaining cloudflared processes for port 8507
if ps aux | grep -v grep | grep "cloudflared.*8507" > /dev/null 2>&1; then
    echo "   Cleaning up remaining processes..."
    pkill -f "cloudflared.*8507" || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
fi

# Remove URL file
if [ -f "$CF_URL_FILE" ]; then
    rm "$CF_URL_FILE"
fi

echo ""
echo -e "${GREEN}✅ Cloudflare Tunnel for RAG Dashboard stopped${NC}"
