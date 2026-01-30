#!/bin/bash

# Start Local Qdrant dengan Docker
# Menggunakan existing container: qdrant_aeropon

echo "🚀 Starting Local Qdrant..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if qdrant_aeropon exists
if docker ps -a | grep -q qdrant_aeropon; then
    echo "📦 Found existing container: qdrant_aeropon"
    
    # Check if already running
    if docker ps | grep -q qdrant_aeropon; then
        echo "✅ Qdrant is already running!"
    else
        echo "▶️  Starting qdrant_aeropon..."
        docker start qdrant_aeropon
        sleep 3
    fi
else
    # Create new container if not exists
    echo "📦 Creating new Qdrant container..."
    docker run -d \
        --name qdrant_aeropon \
        -p 6333:6333 \
        -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant
    sleep 5
fi

# Check if Qdrant is running
if curl -s http://localhost:6333 > /dev/null; then
    echo "✅ Local Qdrant is running!"
    echo "📊 Dashboard: http://localhost:6333/dashboard"
    echo "🔌 API: http://localhost:6333"
else
    echo "❌ Failed to start Qdrant"
    exit 1
fi
