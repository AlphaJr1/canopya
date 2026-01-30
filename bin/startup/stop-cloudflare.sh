#!/bin/bash

# ============================================================
# Stop Cloudflare Tunnel
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
CF_PID_FILE="$RUN_DIR/pids/cloudflare.pid"

echo -e "${YELLOW}Stopping Cloudflare Tunnel...${NC}"

if [ -f "$CF_PID_FILE" ]; then
    CF_PID=$(cat "$CF_PID_FILE")
    
    if ps -p $CF_PID > /dev/null 2>&1; then
        kill $CF_PID
        echo -e "${GREEN}✅ Cloudflare Tunnel stopped (PID: $CF_PID)${NC}"
        rm -f "$CF_PID_FILE"
        rm -f "$PROJECT_ROOT/.cloudflare_url"
    else
        echo -e "${YELLOW}⚠️  Cloudflare Tunnel not running${NC}"
        rm -f "$CF_PID_FILE"
    fi
else
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    
    # Try to kill any cloudflared process
    if pkill -f "cloudflared tunnel" 2>/dev/null; then
        echo -e "${GREEN}✅ Killed cloudflared processes${NC}"
    else
        echo -e "${YELLOW}No cloudflared processes found${NC}"
    fi
fi
