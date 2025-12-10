"""
Example cURL commands untuk testing Aeropon API
Bisa di-copy paste langsung ke terminal
"""

# Health Check
curl http://localhost:8000/health

# Get Stats
curl http://localhost:8000/stats

# Chat - Knowledge Question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "apa kelebihan sistem hidroponik NFT?",
    "language": "id",
    "include_images": true
  }'

# Chat - Sensor Diagnostics
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "pH saya 4.5, TDS 1500, suhu 28°C. Apakah normal?",
    "language": "id"
  }'

# Chat - Hybrid (Sensor + How to Fix)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "pH saya 4.2, bagaimana cara memperbaikinya?",
    "language": "id",
    "include_images": true,
    "session_id": "user-123"
  }'

# Direct Sensor Diagnosis
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "ph": 6.5,
    "tds": 1200,
    "temperature": 25,
    "humidity": 65,
    "growth_stage": "vegetative"
  }'

# Chat - English Response
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what is the ideal pH for NFT system?",
    "language": "en",
    "include_images": false
  }'
