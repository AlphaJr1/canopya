#!/bin/bash

# ============================================================
# Start Cloudflare Tunnel untuk RAG Dashboard
# Domain: https://rag.canopya.cloud
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
CF_LOG_FILE="$RUN_DIR/logs/active/cloudflare-rag.log"
CF_PID_FILE="$RUN_DIR/pids/cloudflare-rag.pid"
CF_URL_FILE="$PROJECT_ROOT/.cloudflare_rag_url"

# Permanent domain
PERMANENT_DOMAIN="https://rag.canopya.cloud"
TUNNEL_NAME="CanopyaAPI"

# RAG Dashboard port
RAG_PORT=8507

# Create directories
mkdir -p "$RUN_DIR/logs/active" "$RUN_DIR/pids"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ cloudflared not found!${NC}"
    echo -e "${YELLOW}Install cloudflared:${NC}"
    echo "  brew install cloudflared"
    exit 1
fi

echo -e "${CYAN}"
echo "============================================================"
echo "        🌐 CLOUDFLARE TUNNEL - RAG.CANOPYA.CLOUD"
echo "============================================================"
echo -e "${NC}"
echo ""

# Check if RAG dashboard is running
if ! lsof -Pi :$RAG_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ RAG Dashboard not running on port $RAG_PORT${NC}"
    echo -e "${YELLOW}Start RAG Dashboard first:${NC}"
    echo "  ./bin/startup/start-rag-dashboard.sh"
    exit 1
fi

# Check if tunnel is already running
if ps aux | grep -v grep | grep "cloudflared tunnel run $TUNNEL_NAME" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Cloudflare Tunnel already running!${NC}"
    echo -e "${BLUE}Domain: $PERMANENT_DOMAIN${NC}"
    echo -e "${BLUE}Local Port: $RAG_PORT${NC}"
    echo ""
    
    # Save URL to file
    echo "$PERMANENT_DOMAIN" > "$CF_URL_FILE"
    
    # Update .ports.info
    if grep -q "RAG_DASHBOARD_URL=" "$PROJECT_ROOT/.ports.info" 2>/dev/null; then
        sed -i '' "s|RAG_DASHBOARD_URL=.*|RAG_DASHBOARD_URL=$PERMANENT_DOMAIN|" "$PROJECT_ROOT/.ports.info"
    else
        echo "RAG_DASHBOARD_URL=$PERMANENT_DOMAIN" >> "$PROJECT_ROOT/.ports.info"
    fi
    
    echo -e "${CYAN}Test connection:${NC}"
    echo "  curl $PERMANENT_DOMAIN"
    echo ""
    exit 0
fi

echo -e "${BLUE}Starting Cloudflare Tunnel: $TUNNEL_NAME${NC}"
echo -e "${YELLOW}Domain: $PERMANENT_DOMAIN → localhost:$RAG_PORT${NC}"
echo ""
echo -e "${YELLOW}Note: Menggunakan tunnel yang sama dengan FastAPI (CanopyaAPI)${NC}"
echo -e "${YELLOW}      Routing ke subdomain rag.canopya.cloud sudah dikonfigurasi di Cloudflare${NC}"
echo ""

# Save permanent URL to file
echo "$PERMANENT_DOMAIN" > "$CF_URL_FILE"

# Update .ports.info
if grep -q "RAG_DASHBOARD_URL=" "$PROJECT_ROOT/.ports.info" 2>/dev/null; then
    sed -i '' "s|RAG_DASHBOARD_URL=.*|RAG_DASHBOARD_URL=$PERMANENT_DOMAIN|" "$PROJECT_ROOT/.ports.info"
else
    echo "RAG_DASHBOARD_URL=$PERMANENT_DOMAIN" >> "$PROJECT_ROOT/.ports.info"
fi

echo -e "${GREEN}✅ RAG Dashboard Configuration Updated!${NC}"
echo ""
echo -e "${BLUE}Domain:${NC}      $PERMANENT_DOMAIN"
echo -e "${BLUE}Local Port:${NC}  $RAG_PORT"
echo ""

echo -e "${CYAN}Test Endpoints:${NC}"
echo "  • Dashboard: $PERMANENT_DOMAIN"
echo "  • With Query: $PERMANENT_DOMAIN/?query_id=<query_id>"
echo ""

echo -e "${CYAN}Environment Variable:${NC}"
echo "  export RAG_DASHBOARD_URL=\"$PERMANENT_DOMAIN\""
echo ""

echo -e "${CYAN}Note:${NC}"
echo "  Tunnel CanopyaAPI sudah menangani routing untuk:"
echo "  • app.canopya.cloud  → localhost:8000 (FastAPI)"
echo "  • rag.canopya.cloud  → localhost:8507 (RAG Dashboard)"
echo ""

echo -e "${GREEN}🎉 Domain ready: $PERMANENT_DOMAIN${NC}"
