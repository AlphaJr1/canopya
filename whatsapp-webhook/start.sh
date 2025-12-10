#!/bin/bash

# Aeropon WhatsApp Webhook - Start Script
# Script untuk memulai webhook bot dengan pengecekan otomatis

set -e

echo "🤖 Aeropon WhatsApp Webhook - Starting..."
echo "=========================================="

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fungsi untuk print dengan warna
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
    echo -e "ℹ️  $1"
}

# 1. Cek apakah di directory yang benar
if [ ! -f "package.json" ]; then
    print_error "package.json tidak ditemukan!"
    print_info "Pastikan Anda menjalankan script ini dari folder whatsapp-webhook/"
    exit 1
fi

print_success "Directory check passed"

# 2. Cek Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js tidak terinstall!"
    print_info "Install Node.js dari: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v)
print_success "Node.js detected: $NODE_VERSION"

# 3. Cek npm
if ! command -v npm &> /dev/null; then
    print_error "npm tidak terinstall!"
    exit 1
fi

NPM_VERSION=$(npm -v)
print_success "npm detected: $NPM_VERSION"

# 4. Cek dependencies
if [ ! -d "node_modules" ]; then
    print_warning "node_modules tidak ditemukan, installing dependencies..."
    npm install
    print_success "Dependencies installed"
else
    print_success "Dependencies check passed"
fi

# 5. Buat folder yang diperlukan
mkdir -p logs
mkdir -p conversations
mkdir -p auth_info

print_success "Folders created/verified"

# 6. Cek FastAPI server
FASTAPI_URL=${FASTAPI_URL:-"http://localhost:8000"}
print_info "Checking FastAPI server at $FASTAPI_URL..."

if curl -s -f "$FASTAPI_URL/health" > /dev/null 2>&1; then
    print_success "FastAPI server is running"
else
    print_warning "FastAPI server tidak dapat dijangkau di $FASTAPI_URL"
    print_info "Bot akan tetap berjalan, tapi pastikan FastAPI server running untuk fitur chatbot"
    print_info "Jalankan FastAPI dengan: cd ../api && ./start_server.sh"
fi

# 7. Info tentang log
echo ""
echo "=========================================="
print_info "Log file: logs/webhook.log"
print_info "Conversations: conversations/"
print_info "Auth info: auth_info/"
echo "=========================================="
echo ""

# 8. Info QR Code
if [ ! -f "auth_info/creds.json" ]; then
    print_warning "Belum ada session WhatsApp"
    print_info "QR Code akan muncul di logs/webhook.log"
    print_info "Buka file tersebut dan scan QR code dengan WhatsApp"
    echo ""
    print_info "Cara melihat QR code:"
    echo "  tail -f logs/webhook.log"
    echo "  atau"
    echo "  grep -A 20 'QR CODE' logs/webhook.log"
else
    print_success "WhatsApp session ditemukan, akan auto-login"
fi

echo ""
echo "=========================================="
print_info "Starting WhatsApp Bot..."
echo "=========================================="
echo ""

# 9. Start bot
node index.js
