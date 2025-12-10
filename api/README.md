# Aeropon Chatbot API

FastAPI server untuk mengakses Aeropon Hybrid Chatbot (RAG + Rule-Based Engine).

## Features

- **POST /chat** - Endpoint utama untuk chat dengan bot
- **POST /diagnose** - Endpoint khusus untuk diagnostik sensor
- **GET /health** - Health check (Qdrant, Ollama, Chatbot)
- **GET /stats** - Statistik sistem (jumlah vectors, model info)
- **GET /docs** - Interactive API documentation (Swagger UI)
- **GET /redoc** - Alternative API documentation (ReDoc)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Atau gunakan requirements.txt utama project
pip install -r ../requirements.txt
pip install fastapi uvicorn[standard]
```

## Running the Server

### Development Mode (dengan auto-reload)

```bash
# Dari folder api/
python main.py

# Atau dengan uvicorn langsung
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server akan berjalan di: `http://localhost:8000`

## API Documentation

Setelah server berjalan, akses:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### 1. Chat dengan Bot

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "pH saya 4.5, TDS 1500, bagaimana cara memperbaikinya?",
    "language": "id",
    "include_images": true,
    "session_id": "user-123"
  }'
```

Response:
```json
{
  "success": true,
  "answer": "Berdasarkan bacaan sensor Anda...",
  "intent": "hybrid",
  "confidence": 0.9,
  "has_sensor_data": true,
  "sensor_data": {
    "ph": 4.5,
    "tds": 1500,
    "temperature": null,
    "humidity": null,
    "growth_stage": "vegetative"
  },
  "rag_confidence": 0.85,
  "sources": ["Panduan Hidroponik", "Manual NFT"],
  "images": ["path/to/diagram1.jpg"],
  "num_images": 1,
  "has_visual_support": true,
  "timestamp": "2025-12-08T01:20:00",
  "session_id": "user-123"
}
```

### 2. Diagnostik Sensor Langsung

```bash
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "ph": 4.5,
    "tds": 1500,
    "temperature": 28,
    "humidity": 65,
    "growth_stage": "vegetative"
  }'
```

### 3. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "chatbot_ready": true,
  "qdrant_status": "healthy",
  "ollama_status": "healthy",
  "timestamp": "2025-12-08T01:20:00"
}
```

### 4. Get Statistics

```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "qdrant_vectors": 1250,
  "qdrant_collection": "aquaponics_knowledge",
  "ollama_model": "qwen3:8b",
  "embedding_model": "intfloat/multilingual-e5-base",
  "timestamp": "2025-12-08T01:20:00"
}
```

## Python Client Example

```python
import requests

# Chat
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "apa kelebihan hidroponik NFT?",
        "language": "id",
        "include_images": True
    }
)
result = response.json()
print(result['answer'])

# Diagnose
response = requests.post(
    "http://localhost:8000/diagnose",
    json={
        "ph": 6.5,
        "tds": 1200,
        "temperature": 25,
        "growth_stage": "vegetative"
    }
)
diagnosis = response.json()
print(diagnosis['summary'])
```

## Request/Response Models

### ChatRequest
```json
{
  "message": "string (required)",
  "language": "id | en (default: id)",
  "include_images": "boolean (default: true)",
  "session_id": "string (optional)"
}
```

### ChatResponse
```json
{
  "success": "boolean",
  "answer": "string",
  "intent": "rule_based | rag | hybrid",
  "confidence": "float (0-1)",
  "has_sensor_data": "boolean",
  "sensor_data": "object | null",
  "rag_confidence": "float | null",
  "sources": "array[string] | null",
  "images": "array[string]",
  "num_images": "integer",
  "pages": "array[integer] | null",
  "has_visual_support": "boolean",
  "timestamp": "string (ISO 8601)",
  "session_id": "string | null"
}
```

### SensorData
```json
{
  "ph": "float | null",
  "tds": "float | null",
  "temperature": "float | null",
  "humidity": "float | null",
  "growth_stage": "seedling | vegetative | fruiting | null"
}
```

## CORS Configuration

Default: Allow all origins (`*`)

Untuk production, edit `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variables

Opsional - bisa ditambahkan untuk konfigurasi:

```bash
export AEROPON_HOST=0.0.0.0
export AEROPON_PORT=8000
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export OLLAMA_MODEL=qwen3:8b
```

## Troubleshooting

### Chatbot not initialized
- Pastikan Qdrant running: `docker ps` (cek container qdrant)
- Pastikan Ollama running: `ollama list`
- Cek logs saat startup

### Qdrant connection failed
```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Ollama connection failed
```bash
# Start Ollama
ollama serve

# Pull model jika belum ada
ollama pull qwen3:8b
```

## Production Deployment

### Dengan Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dengan systemd

```ini
[Unit]
Description=Aeropon Chatbot API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/aeropon/api
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

Same as parent project.
