#!/bin/bash

# ============================================================
# Configure Cloudflare Tunnel untuk canopya.cloud
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "============================================================"
echo "   🌐 CLOUDFLARE TUNNEL CONFIGURATION - CANOPYA.CLOUD"
echo "============================================================"
echo -e "${NC}"
echo ""

echo -e "${BLUE}Langkah-langkah konfigurasi Cloudflare Tunnel:${NC}"
echo ""

echo -e "${YELLOW}1. Login ke Cloudflare Dashboard${NC}"
echo "   https://dash.cloudflare.com"
echo ""

echo -e "${YELLOW}2. Pilih domain canopya.cloud${NC}"
echo ""

echo -e "${YELLOW}3. Buka menu 'Zero Trust' > 'Access' > 'Tunnels'${NC}"
echo ""

echo -e "${YELLOW}4. Buat tunnel baru atau gunakan yang sudah ada${NC}"
echo "   - Jika belum ada, klik 'Create a tunnel'"
echo "   - Beri nama: 'canopya-fastapi'"
echo "   - Pilih environment: 'Cloudflared'"
echo ""

echo -e "${YELLOW}5. Install connector (sudah dilakukan):${NC}"
echo "   brew install cloudflared"
echo ""

echo -e "${YELLOW}6. Authenticate (gunakan token yang diberikan):${NC}"
echo "   sudo cloudflared service install <TOKEN>"
echo ""

echo -e "${YELLOW}7. Configure Public Hostname:${NC}"
echo "   - Subdomain: (kosongkan untuk root domain)"
echo "   - Domain: canopya.cloud"
echo "   - Type: HTTP"
echo "   - URL: localhost:8000"
echo ""

echo -e "${YELLOW}8. Atau gunakan command berikut:${NC}"
echo ""
echo "   # Login ke Cloudflare"
echo "   cloudflared tunnel login"
echo ""
echo "   # Buat tunnel"
echo "   cloudflared tunnel create canopya-fastapi"
echo ""
echo "   # Route domain ke tunnel"
echo "   cloudflared tunnel route dns canopya-fastapi canopya.cloud"
echo ""
echo "   # Jalankan tunnel"
echo "   cloudflared tunnel run canopya-fastapi"
echo ""

echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}Setelah konfigurasi selesai:${NC}"
echo ""
echo "1. Domain canopya.cloud akan otomatis route ke FastAPI"
echo "2. URL tidak akan berubah setiap restart"
echo "3. Gratis selamanya dengan Cloudflare Free plan"
echo "4. Built-in DDoS protection dan CDN"
echo ""
echo -e "${CYAN}============================================================${NC}"
echo ""

echo -e "${YELLOW}Current Status:${NC}"
echo "  • Temporary URL: https://displayed-perl-beads-renew.trycloudflare.com"
echo "  • Target Domain: https://canopya.cloud"
echo "  • Local Port: 8000"
echo ""

echo -e "${BLUE}Untuk menggunakan domain permanen, ikuti langkah di atas.${NC}"
echo -e "${BLUE}Atau hubungi admin Cloudflare untuk konfigurasi DNS.${NC}"
