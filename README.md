# 🌳 Canopya - AI-Powered Smart Hydroponics Assistant

> Your digital canopy for smart growing

Sistem chatbot berbasis AI untuk monitoring dan konsultasi sistem hidroponik dengan integrasi RAG (Retrieval-Augmented Generation), rule-based diagnostics, dan deployment production via Cloudflare Tunnel.

---

## 🎯 Gambaran Umum

**Canopya** adalah sistem chatbot cerdas yang menggabungkan:

- **Hybrid AI Engine**: RAG (knowledge-based) + Rule-Based (sensor diagnostics)
- **Production Deployment**: GCP VM dengan Cloudflare Tunnel
- **Multi-Platform**: FastAPI backend + Streamlit dashboards
- **Real-time Monitoring**: RAG process visualization dan chat testing

### ✨ Fitur Utama

✅ **Hybrid Chatbot**: Kombinasi RAG + Rule-Based untuk jawaban akurat  
✅ **Production Ready**: Deployed di GCP dengan 3 public domains  
✅ **RAG Dashboard**: Visualisasi proses retrieval dan generation  
✅ **Chat Tester**: Interface testing untuk validasi chatbot  
✅ **Multimodal**: Mendukung text, images, dan tables dari knowledge base  
✅ **Sensor Diagnostics**: Analisis pH, TDS, suhu, kelembapan dengan threshold checking

---

## 🌐 Live Demo

**Production URLs:**
- **FastAPI Docs**: https://app.canopya.cloud/docs
- **RAG Dashboard**: https://rag.canopya.cloud
- **Chat Tester**: https://test.canopya.cloud

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER (Web/API Client)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cloudflare Tunnel (Production)                     │
│  - app.canopya.cloud  → FastAPI (Port 8000)                     │
│  - rag.canopya.cloud  → RAG Dashboard (Port 3000)               │
│  - test.canopya.cloud → Chat Tester (Port 3001)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GCP VM (e2-medium, 4GB RAM)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         FastAPI Server (Port 8000)                       │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │         Hybrid Chatbot Engine                      │  │   │
│  │  │  ┌──────────────┐      ┌──────────────────────┐   │  │   │
│  │  │  │ RAG Engine   │      │ Rule-Based Engine    │   │  │   │
│  │  │  │ - Qdrant     │      │ - Sensor Diagnostics │   │  │   │
│  │  │  │ - E5 Embed   │      │ - Threshold Check    │   │  │   │
│  │  │  │ - Ollama LLM │      │ - Recommendations    │   │  │   │
│  │  │  └──────────────┘      └──────────────────────┘   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │    RAG Dashboard (Streamlit - Port 3000)                 │   │
│  │    - Query input                                         │   │
│  │    - Retrieved documents visualization                   │   │
│  │    - Similarity scores                                   │   │
│  │    - Generated answers                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │    Chat Tester (Streamlit - Port 3001)                   │   │
│  │    - Interactive chat interface                          │   │
│  │    - Conversation history                                │   │
│  │    - Quick test questions                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  - Qdrant (Vector DB - Port 6333)                               │
│  - Ollama (LLM - Port 11434)                                    │
│  - SQLite Database (aeropon.db)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Komponen Utama

### 1. **FastAPI Server** (`services/fastapi/`)

Server utama yang menangani semua request chatbot.

**Endpoints:**
- `POST /chat`: Chat dengan hybrid chatbot
- `POST /diagnose`: Diagnostik sensor langsung
- `GET /health`: Health check
- `GET /stats`: System statistics
- `GET /user/{user_id}`: User profile

**Port:** 8000  
**Production:** https://app.canopya.cloud

---

### 2. **Hybrid Chatbot Engine** (`src/core/`)

#### a. **RAG Engine** (`rag_engine.py`)

Retrieval-Augmented Generation untuk menjawab pertanyaan knowledge-based.

**Cara Kerja:**
1. **Retrieve**: Query → E5 embedding → Qdrant search → top-k documents
2. **Generate**: Documents + query → Ollama LLM → answer
3. **Storage**: Save RAG process untuk dashboard visualization

**Komponen:**
- **Embedder**: `intfloat/multilingual-e5-base`
- **Vector DB**: Qdrant (collection: `aquaponics_knowledge`)
- **LLM**: Ollama `ministral-3:3b` (lightweight, efficient)

**Features:**
- Multimodal: text + images + tables
- Conversation history aware
- Markdown formatting removal untuk clean output
- RAG process logging untuk transparency

#### b. **Rule-Based Engine** (`rule_engine.py`)

Diagnostik sensor berdasarkan threshold.

**Thresholds:**
```
pH: 5.5-6.5 (optimal), <5.0 or >7.0 (warning), <4.5 or >7.5 (critical)
TDS:
  - Seedling: 500-1000 ppm
  - Vegetative: 800-1200 ppm
  - Fruiting: 1000-1500 ppm
Temperature: 18-24°C (optimal), <16 or >26°C (warning)
Humidity: 50-70% (optimal), <40 or >80% (warning)
```

**Output:**
- Diagnostic report dengan severity (optimal/warning/critical)
- Recommended actions (add_nutrient, add_water, add_ph_down, add_ph_up)

#### c. **Hybrid Chatbot** (`hybrid_chatbot.py`)

Orchestrator yang menggabungkan RAG dan Rule-Based Engine.

**Intent Detection:**
- `rag`: Knowledge-based questions (cara, bagaimana, apa, dll)
- `rule_based`: Sensor diagnostics (ada data sensor)
- `hybrid`: Both (sensor data + knowledge keywords)

---

### 3. **RAG Dashboard** (`services/dashboardrag/rag_dashboard.py`)

Streamlit dashboard untuk visualisasi proses RAG.

**Features:**
- Query input dengan conversation history
- Top-k retrieved documents dengan similarity scores
- Document metadata (source, page, section)
- Generated answer dengan confidence score
- Image support untuk visual context

**Port:** 3000  
**Production:** https://rag.canopya.cloud

---

### 4. **Chat Tester** (`services/dashboardrag/chat_tester.py`)

Interface testing untuk validasi chatbot responses.

**Features:**
- Interactive chat interface
- Conversation history tracking
- Quick test questions (4 random relevant questions)
- Real-time response dari FastAPI backend

**Port:** 3001  
**Production:** https://test.canopya.cloud

---

### 5. **Database** (`src/database/`)

SQLite database untuk persistent storage.

**Models:**
- `User`: user_id, name, onboarding_completed, last_active
- `Plant`: plant_id, user_id, plant_name, plant_type, growth_stage
- `Message`: message_id, user_id, role, content, intent, timestamp
- `SensorReading`: reading_id, ph, tds, temperature, humidity, status
- `RAGProcess`: process_id, query, retrieved_docs, answer, confidence

---

## 🔄 Cara Kerja Sistem

### Flow 1: User Chat Request

```
1. User kirim query via web/API
   ↓
2. FastAPI /chat endpoint terima request
   ↓
3. Hybrid Chatbot:
   - Extract sensor data (jika ada)
   - Detect intent (rag/rule_based/hybrid)
   - Execute appropriate engine(s)
   ↓
4. RAG Engine (jika intent = rag/hybrid):
   - Embed query dengan E5 model
   - Search di Qdrant vector database
   - Retrieve top-k documents
   - Generate answer dengan Ollama
   ↓
5. Rule-Based Engine (jika intent = rule_based/hybrid):
   - Parse sensor values
   - Compare dengan thresholds
   - Generate diagnostic report
   ↓
6. Format response (natural, conversational)
   ↓
7. Return to user
   ↓
8. Save to database (message, RAG process)
```

### Flow 2: RAG Dashboard Visualization

```
1. User input query di dashboard
   ↓
2. Call FastAPI /chat endpoint
   ↓
3. RAG Engine process query
   ↓
4. Save RAG process (query, docs, scores, answer)
   ↓
5. Dashboard retrieve RAG process dari database
   ↓
6. Visualize:
   - Retrieved documents dengan similarity scores
   - Document content preview
   - Generated answer
   - Confidence metrics
```

---

## 🔧 Prerequisites

### 1. Ollama (LLM)

```bash
# Install Ollama
brew install ollama  # macOS
# atau download dari https://ollama.ai

# Pull model
ollama pull ministral-3:3b

# Start server (jika belum auto-start)
ollama serve
# Should run on http://localhost:11434
```

### 2. Qdrant (Vector Database)

```bash
# Run with Docker
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# Should run on http://localhost:6333
```

### 3. Python 3.9+

```bash
# Verify
python3 --version

# Install virtualenv
pip3 install virtualenv
```

---

## 📦 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/AlphaJr1/canopya.git
cd canopya
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Database

```bash
# Initialize database
python -c "from src.database.base import init_db; init_db()"
```

### 4. Download E5 Model (jika belum ada)

Model akan auto-download saat pertama kali digunakan. Atau download manual:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-base")
model.save("models/intfloat--multilingual-e5-base")
```

### 5. Populate Knowledge Base (jika belum ada)

```bash
# Run full pipeline
python src/utils/pipeline.py full
```

---

## 🚀 Menjalankan Sistem

### Local Development

#### 1. Start FastAPI Server

```bash
./bin/startup/start-fastapi.sh
# atau
cd services/fastapi && python main.py
```

#### 2. Start RAG Dashboard

```bash
./bin/startup/start-rag-dashboard.sh
# atau
streamlit run services/dashboardrag/rag_dashboard.py --server.port 3000
```

#### 3. Start Chat Tester

```bash
./bin/startup/start-chat-tester.sh
# atau
streamlit run services/dashboardrag/chat_tester.py --server.port 3001
```

### Production (GCP VM)

**SSH ke VM:**
```bash
gcloud compute ssh canopya-chatbot-server --zone=asia-southeast2-a
```

**Start All Services:**
```bash
cd canopya
./bin/startup/start-fastapi-gcp.sh
./bin/startup/start-rag-dashboard-gcp.sh
./bin/startup/start-chat-tester-gcp.sh
```

**Check Status:**
```bash
ps aux | grep -E "fastapi|streamlit|cloudflared" | grep -v grep
```

**View Logs:**
```bash
tail -f .run/logs/fastapi.log
tail -f .run/logs/rag-dashboard.log
tail -f .run/logs/chat-tester.log
```

### Shutdown

**Local:**
```bash
./bin/shutdown/stop-all.sh
```

**GCP VM:**
```bash
./bin/shutdown/stop-fastapi-gcp.sh
./bin/shutdown/stop-rag-dashboard-gcp.sh
./bin/shutdown/stop-chat-tester-gcp.sh
```

---

## 📁 Struktur Project

```
canopya/
├── services/                     # Main services
│   ├── fastapi/                  # FastAPI application
│   │   └── main.py               # Main server
│   └── dashboardrag/             # Streamlit dashboards
│       ├── rag_dashboard.py      # RAG visualization
│       └── chat_tester.py        # Chat testing interface
│
├── src/                          # Source code
│   ├── core/                     # Core engines
│   │   ├── hybrid_chatbot.py     # Hybrid chatbot orchestrator
│   │   ├── rag_engine.py         # RAG engine
│   │   ├── rule_engine.py        # Rule-based diagnostics
│   │   └── rag_storage.py        # RAG process storage
│   │
│   ├── database/                 # Database operations
│   │   ├── base.py               # Database setup
│   │   ├── models.py             # SQLAlchemy models
│   │   └── operations.py         # CRUD operations
│   │
│   └── utils/                    # Utilities
│       ├── pipeline.py           # Knowledge base pipeline
│       ├── log_manager.py        # Log management
│       └── pid_manager.py        # Process management
│
├── bin/                          # Shell scripts
│   ├── startup/                  # Start scripts
│   │   ├── start-fastapi-gcp.sh
│   │   ├── start-rag-dashboard-gcp.sh
│   │   └── start-chat-tester-gcp.sh
│   └── shutdown/                 # Stop scripts
│       ├── stop-fastapi-gcp.sh
│       ├── stop-rag-dashboard-gcp.sh
│       └── stop-chat-tester-gcp.sh
│
├── docs/                         # Documentation
│   └── GCP_DEPLOYMENT.md         # GCP deployment guide
│
├── data/                         # Data files
│   ├── raw/                      # Scraped data
│   ├── processed/                # Processed chunks
│   └── kb/                       # Knowledge base
│
├── models/                       # ML models
│   └── intfloat--multilingual-e5-base/
│
├── qdrant_storage/               # Qdrant vector database
├── aeropon.db                    # SQLite database
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🌐 API Endpoints

### FastAPI Server (Port 8000)

#### **POST /chat**

Chat dengan hybrid chatbot.

**Request:**
```json
{
  "message": "pH saya 4.5, bagaimana?",
  "user_id": "user123",
  "language": "id",
  "include_images": true,
  "conversation_history": [
    {"role": "user", "message": "halo"},
    {"role": "assistant", "message": "Halo!"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "answer": "pH 4.5 terlalu rendah untuk hidroponik...",
  "intent": "hybrid",
  "confidence": 0.95,
  "has_sensor_data": true,
  "sensor_data": {
    "ph": 4.5,
    "tds": null,
    "temperature": null,
    "humidity": null
  },
  "rag_confidence": 0.87,
  "sources": ["Panduan pH Hidroponik", "Troubleshooting pH"],
  "images": [],
  "num_images": 0,
  "timestamp": "2026-01-31T09:00:00"
}
```

#### **POST /diagnose**

Diagnostik sensor langsung.

**Request:**
```json
{
  "ph": 4.5,
  "tds": 1500,
  "temperature": 25,
  "humidity": 60,
  "growth_stage": "vegetative"
}
```

**Response:**
```json
{
  "success": true,
  "summary": "2 critical, 1 optimal",
  "diagnostics": {
    "ph": {
      "value": 4.5,
      "status": "critical",
      "message": "pH terlalu rendah",
      "recommendation": "Tambahkan pH Up"
    },
    "tds": {
      "value": 1500,
      "status": "warning",
      "message": "TDS sedikit tinggi",
      "recommendation": "Tambahkan air"
    }
  }
}
```

#### **GET /health**

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "chatbot_ready": true,
  "qdrant_status": "healthy",
  "ollama_status": "healthy",
  "timestamp": "2026-01-31T09:00:00"
}
```

---

## 🧪 Testing

### Test Chat Endpoint

```bash
curl -X POST "https://app.canopya.cloud/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Bagaimana cara menanam selada hidroponik?",
    "user_id": "test_user",
    "language": "id"
  }'
```

### Test via Chat Tester

1. Buka https://test.canopya.cloud
2. Pilih quick question atau ketik manual
3. Lihat response real-time

### Test via RAG Dashboard

1. Buka https://rag.canopya.cloud
2. Input query
3. Lihat retrieved documents dan generated answer

---

## 🔍 Model & Technology Stack

### AI/ML Models

- **LLM**: Ollama `ministral-3:3b` (lightweight, efficient, 3B parameters)
- **Embeddings**: `intfloat/multilingual-e5-base` (multilingual support)
- **Vector DB**: Qdrant (fast similarity search)

### Backend

- **Framework**: FastAPI (async, high performance)
- **Database**: SQLite (lightweight, portable)
- **ORM**: SQLAlchemy

### Frontend

- **Dashboard**: Streamlit (rapid prototyping, interactive)
- **Deployment**: Cloudflare Tunnel (secure, no firewall config)

### Infrastructure

- **Cloud**: Google Cloud Platform (GCP)
- **VM**: e2-medium (2 vCPU, 4GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Tunnel**: Cloudflare (zero-trust network access)

---

## 📊 Performance

### Model Performance

- **RAG Retrieval**: ~200ms (top-5 documents)
- **LLM Generation**: ~2-5s (ministral-3:3b)
- **Total Response Time**: ~3-7s (end-to-end)

### Resource Usage

- **Memory**: ~2GB (all services running)
- **CPU**: ~30-40% (during inference)
- **Disk**: ~15GB (models + database + logs)

---

## 🚀 Deployment

Lihat [GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md) untuk panduan lengkap deployment ke production.

**Quick Summary:**
1. Setup GCP VM (e2-medium recommended)
2. Install dependencies (Python, Ollama, Qdrant)
3. Clone repository dan setup environment
4. Configure Cloudflare Tunnel
5. Start services dengan startup scripts
6. Access via public domains

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Team

**Canopya Team**
- Adrian Alfajri - Lead Developer

---

## 📧 Contact

- **Email**: adrianalfajri@example.com
- **GitHub**: [@AlphaJr1](https://github.com/AlphaJr1)
- **Project**: [Canopya](https://github.com/AlphaJr1/canopya)

---

## 🙏 Acknowledgments

- Ollama team untuk LLM inference engine
- Qdrant team untuk vector database
- Sentence Transformers untuk embedding models
- FastAPI dan Streamlit communities

---

**Built with ❤️ for smart hydroponics**
