#!/bin/bash

# ============================================================
# Setup Cloudflare Tunnel Credentials
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "============================================================"
echo "     🔐 CLOUDFLARE TUNNEL CREDENTIALS SETUP"
echo "============================================================"
echo -e "${NC}"
echo ""

TUNNEL_ID="0dec19a6-0c0b-4376-adf7-d8dfef46d273"
CF_DIR="$HOME/.cloudflared"
CRED_FILE="$CF_DIR/$TUNNEL_ID.json"

# Create .cloudflared directory
mkdir -p "$CF_DIR"

echo -e "${BLUE}Checking Cloudflare authentication...${NC}"
echo ""

# Check if already authenticated
if [ -f "$CRED_FILE" ]; then
    echo -e "${GREEN}✅ Credentials file already exists${NC}"
    echo -e "${BLUE}Location: $CRED_FILE${NC}"
    echo ""
    exit 0
fi

echo -e "${YELLOW}Credentials file not found${NC}"
echo ""
echo -e "${CYAN}Untuk setup tunnel, Anda perlu:${NC}"
echo ""
echo "1. Login ke Cloudflare:"
echo "   ${BLUE}cloudflared tunnel login${NC}"
echo ""
echo "2. Atau download credentials dari Cloudflare Dashboard:"
echo "   - Buka: https://dash.cloudflare.com"
echo "   - Pilih domain: canopya.cloud"
echo "   - Buka: Networks > Tunnels > CanopyaAPI"
echo "   - Klik tab 'Configure'"
echo "   - Download credentials JSON file"
echo "   - Simpan ke: $CRED_FILE"
echo ""
echo "3. Atau gunakan token untuk install service:"
echo "   ${BLUE}sudo cloudflared service install eyJhIjoiMWZlYzFmYjJjOTdmOTExMDgwODhmM2ZmMmRkYTQwNWUiLCJ0IjoiMDBlYzE5YTYtMGMwYi00Mzc2LWFkZjctZDhkZmVmNDZkMjczIiwicyI6Ik1UWmlNRGhtWVRJdE5EZGtaaTAwTWpJM0xXSTBZVFF0T0dKa09EZzNOR1k1WVdFMyJ9${NC}"
echo ""

read -p "Apakah Anda ingin login sekarang? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Menjalankan cloudflared login...${NC}"
    cloudflared tunnel login
    
    if [ -f "$HOME/.cloudflared/cert.pem" ]; then
        echo ""
        echo -e "${GREEN}✅ Login berhasil!${NC}"
        echo ""
        echo -e "${CYAN}Next steps:${NC}"
        echo "1. Jalankan: ./bin/startup/start-cloudflare.sh"
        echo ""
    fi
else
    echo ""
    echo -e "${YELLOW}Setup dibatalkan${NC}"
    echo -e "${BLUE}Jalankan script ini lagi setelah credentials tersedia${NC}"
    echo ""
fi
