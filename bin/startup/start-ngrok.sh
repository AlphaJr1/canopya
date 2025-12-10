#!/bin/bash

# ============================================================
# Start Ngrok Tunnel untuk RAG Dashboard
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGROK_URL_FILE="$PROJECT_ROOT/.ngrok_url"
NGROK_PID_FILE="$PROJECT_ROOT/.ngrok.pid"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ Ngrok not found!${NC}"
    echo -e "${YELLOW}Install ngrok:${NC}"
    echo "  1. Download from https://ngrok.com/download"
    echo "  2. Or install via brew: brew install ngrok"
    echo "  3. Setup auth token: ngrok authtoken YOUR_TOKEN"
    exit 1
fi

# Get dashboard port from .ports.info
if [ -f "$PROJECT_ROOT/.ports.info" ]; then
    source "$PROJECT_ROOT/.ports.info"
    DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
else
    DASHBOARD_PORT=8501
fi

echo -e "${BLUE}Starting ngrok tunnel for RAG Dashboard (port $DASHBOARD_PORT)...${NC}"

# Start ngrok in background
nohup ngrok http $DASHBOARD_PORT > /dev/null 2>&1 &
NGROK_PID=$!
echo $NGROK_PID > "$NGROK_PID_FILE"

# Wait for ngrok to start
sleep 3

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Failed to get ngrok URL${NC}"
    echo -e "${YELLOW}Check if ngrok is running: curl http://localhost:4040/api/tunnels${NC}"
    exit 1
fi

# Save ngrok URL to file
echo "$NGROK_URL" > "$NGROK_URL_FILE"

echo -e "${GREEN}✅ Ngrok tunnel started!${NC}"
echo -e "${GREEN}Public URL: $NGROK_URL${NC}"
echo -e "${BLUE}PID: $NGROK_PID${NC}"
echo ""
echo -e "${YELLOW}Set this as environment variable:${NC}"
echo "export RAG_DASHBOARD_URL=\"$NGROK_URL\""
echo ""
echo -e "${YELLOW}Or add to .env file:${NC}"
echo "RAG_DASHBOARD_URL=$NGROK_URL"
