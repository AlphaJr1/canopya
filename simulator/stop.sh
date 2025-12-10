#!/bin/bash

# Shutdown script untuk Simulator pH & TDS
# Gracefully stop background generator dan FastAPI server

set -e

echo "🛑 Stopping Aeropon Simulator..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop background generator
if [ -f "data/background_generator.pid" ]; then
    BG_GENERATOR_PID=$(cat data/background_generator.pid)
    if ps -p $BG_GENERATOR_PID > /dev/null 2>&1; then
        echo "🔄 Stopping background generator (PID: $BG_GENERATOR_PID)..."
        kill -TERM $BG_GENERATOR_PID
        
        # Wait for graceful shutdown (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p $BG_GENERATOR_PID > /dev/null 2>&1; then
                echo "   ✅ Background generator stopped"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if ps -p $BG_GENERATOR_PID > /dev/null 2>&1; then
            echo "   ⚠️  Force killing background generator..."
            kill -9 $BG_GENERATOR_PID
        fi
    else
        echo "   ℹ️  Background generator not running"
    fi
    rm -f data/background_generator.pid
else
    echo "   ℹ️  Background generator PID file not found"
fi

# Stop FastAPI server
if [ -f "data/server.pid" ]; then
    SERVER_PID=$(cat data/server.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "🌐 Stopping FastAPI server (PID: $SERVER_PID)..."
        kill -TERM $SERVER_PID
        
        # Wait for graceful shutdown (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p $SERVER_PID > /dev/null 2>&1; then
                echo "   ✅ FastAPI server stopped"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo "   ⚠️  Force killing FastAPI server..."
            kill -9 $SERVER_PID
        fi
    else
        echo "   ℹ️  FastAPI server not running"
    fi
    rm -f data/server.pid
else
    echo "   ℹ️  FastAPI server PID file not found"
fi

echo ""
echo "✅ Simulator stopped successfully"
echo ""
