#!/bin/bash

# Startup script untuk Simulator pH & TDS
# Menjalankan background generator dan FastAPI server

set -e

echo "🚀 Starting Aeropon Simulator..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "❌ Error: config.json not found"
    exit 1
fi

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Check Python dependencies
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check Ollama
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama tidak terdeteksi di localhost:11434"
    echo "   LLM predictor mungkin tidak berfungsi."
    echo "   Jalankan: ollama serve"
else
    echo "✅ Ollama running"
fi

# Initialize database (create tables if not exist)
echo "🗄️  Initializing database..."
python3 -c "from database_integration import SimulatorDatabase; SimulatorDatabase()" 2>/dev/null || true

# Start background generator
echo "🔄 Starting background data generator..."
python3 background_generator.py > logs/background_generator.log 2>&1 &
BG_GENERATOR_PID=$!
echo $BG_GENERATOR_PID > data/background_generator.pid
echo "   PID: $BG_GENERATOR_PID"

# Wait a bit untuk ensure generator started
sleep 2

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
python3 server.py > logs/server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > data/server.pid
echo "   PID: $SERVER_PID"

# Wait a bit untuk ensure server started
sleep 3

# Check if processes are running
if ps -p $BG_GENERATOR_PID > /dev/null 2>&1; then
    echo "✅ Background generator running (PID: $BG_GENERATOR_PID)"
else
    echo "❌ Background generator failed to start"
    exit 1
fi

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ FastAPI server running (PID: $SERVER_PID)"
else
    echo "❌ FastAPI server failed to start"
    kill $BG_GENERATOR_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "✨ Simulator started successfully!"
echo ""
echo "📊 Server info:"
echo "   - API: http://localhost:3456"
echo "   - Docs: http://localhost:3456/docs"
echo "   - Logs: logs/simulator.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo ""
