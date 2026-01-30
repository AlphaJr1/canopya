#!/bin/bash

# ============================================================
# Start Cloudflare Tunnel untuk FastAPI
# Domain: https://app.canopya.cloud
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
CF_LOG_FILE="$RUN_DIR/logs/active/cloudflare.log"
CF_PID_FILE="$RUN_DIR/pids/cloudflare.pid"
CF_URL_FILE="$PROJECT_ROOT/.cloudflare_url"

# Permanent domain
PERMANENT_DOMAIN="https://app.canopya.cloud"
TUNNEL_NAME="CanopyaAPI"

# Create directories
mkdir -p "$RUN_DIR/logs/active" "$RUN_DIR/pids"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ cloudflared not found!${NC}"
    echo -e "${YELLOW}Install cloudflared:${NC}"
    echo "  brew install cloudflared"
    exit 1
fi

# Get FastAPI port from .ports.info
if [ -f "$PROJECT_ROOT/.ports.info" ]; then
    source "$PROJECT_ROOT/.ports.info"
    FASTAPI_PORT=${FASTAPI_PORT:-8000}
else
    FASTAPI_PORT=8000
fi

echo -e "${CYAN}"
echo "============================================================"
echo "        🌐 CLOUDFLARE TUNNEL - APP.CANOPYA.CLOUD"
echo "============================================================"
echo -e "${NC}"
echo ""

# Check if FastAPI is running
if ! lsof -Pi :$FASTAPI_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ FastAPI not running on port $FASTAPI_PORT${NC}"
    echo -e "${YELLOW}Start FastAPI first:${NC}"
    echo "  ./bin/startup/start-fastapi.sh"
    exit 1
fi

# Check if tunnel is already running
if ps aux | grep -v grep | grep "cloudflared tunnel run $TUNNEL_NAME" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Cloudflare Tunnel already running!${NC}"
    echo -e "${BLUE}Domain: $PERMANENT_DOMAIN${NC}"
    echo -e "${BLUE}Local Port: $FASTAPI_PORT${NC}"
    echo ""
    
    # Save URL to file
    echo "$PERMANENT_DOMAIN" > "$CF_URL_FILE"
    
    echo -e "${CYAN}Test connection:${NC}"
    echo "  curl $PERMANENT_DOMAIN/health"
    echo ""
    exit 0
fi

echo -e "${BLUE}Starting Cloudflare Tunnel: $TUNNEL_NAME${NC}"
echo -e "${YELLOW}Domain: $PERMANENT_DOMAIN → localhost:$FASTAPI_PORT${NC}"
echo ""

# Check for credentials or cert
TUNNEL_ID="0dec19a6-0c0b-4376-adf7-d8dfef46d273"
CRED_FILE="$HOME/.cloudflared/$TUNNEL_ID.json"
CERT_FILE="$HOME/.cloudflared/cert.pem"

if [ ! -f "$CRED_FILE" ] && [ ! -f "$CERT_FILE" ]; then
    echo -e "${RED}❌ Cloudflare credentials not found${NC}"
    echo ""
    echo -e "${YELLOW}Setup credentials first:${NC}"
    echo "  ./bin/startup/setup-cloudflare-credentials.sh"
    echo ""
    echo -e "${YELLOW}Or login manually:${NC}"
    echo "  cloudflared tunnel login"
    echo ""
    exit 1
fi

# Start tunnel in background using config file
nohup cloudflared tunnel --config "$HOME/.cloudflared/config.yml" run \
    > "$CF_LOG_FILE" 2>&1 &

TUNNEL_PID=$!
echo $TUNNEL_PID > "$CF_PID_FILE"

# Save permanent URL to file
echo "$PERMANENT_DOMAIN" > "$CF_URL_FILE"

# Wait a moment for tunnel to start
sleep 3

# Check if tunnel is running
if ps -p $TUNNEL_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Cloudflare Tunnel Started!${NC}"
    echo ""
    echo -e "${BLUE}Domain:${NC}      $PERMANENT_DOMAIN"
    echo -e "${BLUE}Local Port:${NC}  $FASTAPI_PORT"
    echo -e "${BLUE}PID:${NC}         $TUNNEL_PID"
    echo -e "${BLUE}Log File:${NC}    $CF_LOG_FILE"
    echo ""
    
    echo -e "${CYAN}Test Endpoints:${NC}"
    echo "  • Health:  curl $PERMANENT_DOMAIN/health"
    echo "  • Docs:    $PERMANENT_DOMAIN/docs"
    echo "  • Chat:    curl -X POST $PERMANENT_DOMAIN/chat"
    echo ""
    
    echo -e "${CYAN}Useful Commands:${NC}"
    echo "  • Check status:  ps aux | grep cloudflared"
    echo "  • View logs:     tail -f $CF_LOG_FILE"
    echo "  • Stop tunnel:   ./bin/startup/stop-cloudflare.sh"
    echo ""
    
    echo -e "${GREEN}🎉 Domain ready: $PERMANENT_DOMAIN${NC}"
else
    echo -e "${RED}❌ Failed to start tunnel${NC}"
    echo -e "${YELLOW}Check log: tail -f $CF_LOG_FILE${NC}"
    exit 1
fi
