#!/bin/bash

# Script untuk menjalankan Aeropon FastAPI Server

echo "🚀 Starting Aeropon Chatbot API..."

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate"
    exit 1
fi

# Activate virtual environment
source ../venv/bin/activate

# Check if dependencies installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing FastAPI dependencies..."
    pip install fastapi uvicorn[standard] pydantic python-multipart
fi

# Check if Qdrant is running
if ! curl -s http://localhost:6333/collections >/dev/null 2>&1; then
    echo "⚠️  Warning: Qdrant might not be running on localhost:6333"
    echo "   Start Qdrant: docker run -p 6333:6333 qdrant/qdrant"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "⚠️  Warning: Ollama might not be running"
    echo "   Start Ollama: ollama serve"
fi

# Run server
echo ""
echo "✅ Starting server on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo ""

cd "$(dirname "$0")"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
