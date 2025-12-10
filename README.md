# Aeropon - Sistem Chatbot Hidroponik/Aquaponik Cerdas

Sistem lengkap chatbot berbasis AI untuk monitoring dan konsultasi sistem hidroponik/aquaponik dengan integrasi WhatsApp, IoT simulator, dan RAG (Retrieval-Augmented Generation).

---

## 📋 Daftar Isi

1. [Gambaran Umum](#-gambaran-umum)
2. [Arsitektur Sistem](#-arsitektur-sistem)
3. [Komponen Utama](#-komponen-utama)
4. [Cara Kerja Sistem](#-cara-kerja-sistem)
5. [Prerequisites](#-prerequisites)
6. [Instalasi](#-instalasi)
7. [Menjalankan Sistem](#-menjalankan-sistem)
8. [Struktur Project](#-struktur-project)
9. [API Endpoints](#-api-endpoints)
10. [Testing](#-testing)
11. [Troubleshooting](#-troubleshooting)

---

## 🎯 Gambaran Umum

Aeropon adalah sistem chatbot cerdas yang menggabungkan:

- **AI Chatbot** dengan RAG Engine untuk menjawab pertanyaan tentang hidroponik/aquaponik
- **Rule-Based Engine** untuk diagnostik sensor (pH, TDS, suhu, kelembapan)
- **IoT Simulator** untuk simulasi data sensor real-time dengan prediksi LSTM
- **WhatsApp Integration** untuk interaksi user yang mudah
- **Onboarding System** untuk user baru
- **Gamification** untuk meningkatkan engagement

### Fitur Utama

✅ **Hybrid Chatbot**: Kombinasi RAG (knowledge-based) + Rule-Based (sensor diagnostics)  
✅ **Multimodal**: Mendukung text, images, dan tables dari knowledge base  
✅ **WhatsApp Bot**: Interaksi langsung via WhatsApp  
✅ **IoT Simulator**: Simulasi sensor pH, TDS, suhu, kelembapan dengan anomaly injection  
✅ **LSTM Prediction**: Prediksi kondisi sensor menggunakan LLM (Ollama)  
✅ **User Onboarding**: Guided onboarding untuk user baru  
✅ **RAG Dashboard**: Visualisasi proses RAG (top-k documents, similarity scores)  
✅ **Database Integration**: Tracking user, plants, messages, sensor readings

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (WhatsApp)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              WhatsApp Webhook (Baileys + Node.js)               │
│  - QR Code Login                                                │
│  - Message Handling                                             │
│  - Session Management                                           │
│  - Conversation Storage                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Server (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Hybrid Chatbot Engine                       │   │
│  │  ┌────────────────┐         ┌────────────────────────┐  │   │
│  │  │  RAG Engine    │         │  Rule-Based Engine     │  │   │
│  │  │  - Qdrant      │         │  - Sensor Diagnostics  │  │   │
│  │  │  - E5 Embed    │         │  - Threshold Checking  │  │   │
│  │  │  - Ollama LLM  │         │  - Action Recommender  │  │   │
│  │  └────────────────┘         └────────────────────────┘  │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │         Onboarding Engine                          │ │   │
│  │  │  - User Registration                               │ │   │
│  │  │  - Plant Setup                                     │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              IoT Simulator API (Port 3456)                      │
│  - Data Generator (pH, TDS, Temp, Humidity)                     │
│  - Anomaly Injection                                            │
│  - LSTM Predictor (via Ollama)                                  │
│  - Gamification Engine                                          │
│  - Action Executor (add_nutrient, add_water, etc)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database (SQLite)                            │
│  - Users & Plants                                               │
│  - Messages & Conversations                                     │
│  - Sensor Readings                                              │
│  - Actions & Predictions                                        │
│  - RAG Process Logs                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              External Services                                  │
│  - Qdrant (Vector DB - Port 6333)                               │
│  - Ollama (LLM - Port 11434)                                    │
│  - Ngrok (Public URL untuk RAG Dashboard)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Komponen Utama

### 1. **FastAPI Server** (`api/`)

Server utama yang menangani semua request chatbot.

**File Utama:**

- `main.py`: FastAPI application dengan endpoints untuk chat, diagnose, user management
- `test_client.py`: Client untuk testing API

**Endpoints:**

- `POST /chat`: Chat dengan hybrid chatbot
- `POST /diagnose`: Diagnostik sensor langsung
- `POST /onboarding`: Onboarding user baru
- `GET /user/{user_id}`: Get user profile
- `GET /health`: Health check
- `GET /stats`: System statistics

**Port:** 8000

---

### 2. **Hybrid Chatbot Engine** (`src/core/`)

Otak dari sistem - menggabungkan RAG dan Rule-Based Engine.

#### a. **RAG Engine** (`rag_engine.py`)

Retrieval-Augmented Generation untuk menjawab pertanyaan knowledge-based.

**Cara Kerja:**

1. **Retrieve**: Query di-embed dengan E5 model → search di Qdrant → ambil top-k documents
2. **Generate**: Documents + query → Ollama LLM → generate answer
3. **Storage**: Simpan RAG process untuk dashboard visualization

**Komponen:**

- **Embedder**: `intfloat/multilingual-e5-base` (local cache di `models/`)
- **Vector DB**: Qdrant (collection: `aquaponics_knowledge`)
- **LLM**: Ollama `qwen3:8b`

**Features:**

- Multimodal: text + images + tables
- Conversation history aware
- Markdown formatting removal untuk WhatsApp
- RAG process logging untuk dashboard

#### b. **Rule-Based Engine** (`rule_engine.py`)

Diagnostik sensor berdasarkan threshold yang telah ditentukan.

**Cara Kerja:**

1. Extract sensor data dari message (pH, TDS, suhu, kelembapan)
2. Compare dengan threshold berdasarkan growth stage
3. Generate diagnostic report dengan severity (optimal/warning/critical)
4. Recommend actions (add_nutrient, add_water, add_ph_down, add_ph_up)

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

#### c. **Hybrid Chatbot** (`hybrid_chatbot.py`)

Orchestrator yang menggabungkan RAG dan Rule-Based Engine.

**Intent Detection:**

- `rag`: Knowledge-based questions (cara, bagaimana, apa, dll)
- `rule_based`: Sensor diagnostics (ada data sensor, tidak ada knowledge keywords)
- `hybrid`: Both (ada sensor data + knowledge keywords)
- `action`: User wants to perform action (tambah nutrisi, air, dll)

**Flow:**

```
User Message
    ↓
Extract Sensor Data (regex)
    ↓
Detect Intent (rag/rule_based/hybrid/action)
    ↓
Execute:
  - RAG: query RAG engine
  - Rule: diagnose sensors
  - Hybrid: both
  - Action: execute simulator action
    ↓
Format Response (natural, conversational)
    ↓
Return to User
```

#### d. **Onboarding Engine** (`onboarding_engine.py`)

Guided onboarding untuk user baru.

**Steps:**

1. Welcome
2. Collect name
3. Collect plant name
4. Detect plant type (auto dari plant name)
5. Collect growth stage
6. Completion

**Features:**

- State machine untuk tracking progress
- Retry mechanism untuk invalid input
- Natural language processing untuk extract info
- Database integration untuk save user & plant data

---

### 3. **IoT Simulator** (`simulator/`)

Simulasi sensor real-time dengan prediksi dan gamification.

#### a. **Data Generator** (`data_generator.py`)

Generate sensor data dengan realistic patterns.

**Features:**

- Realistic pH drift (slow changes over time)
- TDS consumption (decreases as plants consume nutrients)
- Temperature & humidity variations
- Anomaly injection (random critical conditions)
- Action effects (add_nutrient → TDS increase, add_ph_down → pH decrease)

#### b. **LSTM Predictor** (`lstm_predictor.py`)

Prediksi kondisi sensor menggunakan LLM (bukan LSTM tradisional).

**Cara Kerja:**

1. Get historical data (7 hari terakhir)
2. Format data untuk LLM prompt
3. Ollama generate prediction
4. Cache prediction (15 menit)

**Output:**

- Trend analysis (pH naik/turun, TDS stabil/turun)
- Predictions (kondisi 24 jam ke depan)
- Recommendations (actions yang perlu dilakukan)

#### c. **Gamification Engine** (`gamification.py`)

Validate dan score user actions.

**Features:**

- Action validation (apakah action valid untuk kondisi saat ini)
- Improvement checking (apakah action membuat kondisi lebih baik)
- Achievement tracking (future: badges, leaderboards)

#### d. **Simulator Server** (`server.py`)

FastAPI server untuk simulator.

**Endpoints:**

- `GET /current`: Current sensor values
- `GET /history`: Historical data
- `POST /action`: Execute action (add_nutrient, etc)
- `GET /predict`: Get LSTM prediction
- `GET /insights`: Automated insights & alerts

**Port:** 3456

---

### 4. **WhatsApp Webhook** (`whatsapp-webhook/`)

Integration dengan WhatsApp menggunakan Baileys.

**File Utama:**

- `index.js`: Main webhook server
- `http_server.js`: HTTP server untuk simulator alerts

**Cara Kerja:**

1. **Startup**: Display QR code di terminal
2. **User scans**: Login ke WhatsApp Web
3. **Message received**:
   - Clean phone number
   - Check onboarding status
   - Route to onboarding atau chatbot
   - Get conversation history
   - Call FastAPI
   - Send response
4. **Conversation storage**: Save semua messages ke JSON files

**Features:**

- QR code login di terminal
- Session management (30 menit timeout)
- Conversation history tracking
- Typing indicator
- Alert handling dari simulator
- HTTP endpoint untuk simulator integration

**Port:** 3000

---

### 5. **Database** (`src/database/`)

SQLite database untuk persistent storage.

**Models:**

- `User`: user_id, name, onboarding_completed, last_active
- `Plant`: plant_id, user_id, plant_name, plant_type, growth_stage, planting_date
- `Message`: message_id, user_id, role, content, intent, timestamp
- `SensorReading`: reading_id, ph, tds, temperature, humidity, status, timestamp
- `Action`: action_id, user_id, action_type, ph_before, ph_after, improved_status
- `Prediction`: prediction_id, trend_analysis, predictions, recommendations

**Operations:**

- User CRUD
- Plant CRUD
- Message logging
- Sensor data tracking
- Action tracking
- Prediction storage

---

### 6. **RAG Dashboard** (via Streamlit + Ngrok)

Visualisasi proses RAG untuk transparency.

**Features:**

- Query input
- Top-k retrieved documents dengan similarity scores
- Document metadata (source, page, section)
- Generated answer
- Confidence score

**Access:** Via ngrok public URL (stored di `.ports.info`)

---

## 🔄 Cara Kerja Sistem

### Flow 1: User Bertanya via WhatsApp

```
1. User kirim pesan via WhatsApp
   ↓
2. WhatsApp Webhook terima message
   ↓
3. Clean phone number & check onboarding status
   ↓
4. Jika belum onboarding:
   - Route ke Onboarding Engine
   - Guided data collection
   - Save user & plant data
   ↓
5. Jika sudah onboarding:
   - Get conversation history
   - Extract sensor data (jika ada)
   - Call FastAPI /chat endpoint
   ↓
6. FastAPI → Hybrid Chatbot
   ↓
7. Hybrid Chatbot:
   - Detect intent (rag/rule_based/hybrid/action)
   - Execute appropriate engine(s)
   - Format response
   ↓
8. Response kembali ke WhatsApp Webhook
   ↓
9. WhatsApp Webhook kirim ke user
   ↓
10. Save conversation ke JSON & database
```

### Flow 2: RAG Engine Processing

```
1. User query masuk
   ↓
2. Enrich query dengan conversation history
   ↓
3. Embed query dengan E5 model
   ↓
4. Search di Qdrant vector database
   ↓
5. Retrieve top-k documents (default: 5)
   ↓
6. Score images berdasarkan relevance
   ↓
7. Build context dari documents
   ↓
8. Generate prompt untuk Ollama
   ↓
9. Ollama generate answer
   ↓
10. Clean markdown formatting
   ↓
11. Save RAG process untuk dashboard
   ↓
12. Return answer + metadata
```

### Flow 3: Simulator Data Generation

```
1. Background generator runs setiap 5 menit
   ↓
2. Generate next reading:
   - pH drift (±0.05 per reading)
   - TDS consumption (-5 to -15 ppm per reading)
   - Temperature variation (±0.5°C)
   - Humidity variation (±2%)
   ↓
3. Random anomaly injection (10% chance)
   ↓
4. Save reading ke database
   ↓
5. Check thresholds untuk alerts
   ↓
6. Jika critical/warning:
   - Generate alert
   - Send ke WhatsApp via HTTP endpoint
   ↓
7. Update current_state.json
```

### Flow 4: User Action Execution

```
1. User kirim action command (e.g., "tambah nutrisi")
   ↓
2. Hybrid Chatbot detect action intent
   ↓
3. Call Simulator API /action endpoint
   ↓
4. Simulator:
   - Validate action
   - Get current state (before)
   - Apply action effect:
     * add_nutrient: TDS +100-200 ppm
     * add_water: TDS -50-100 ppm
     * add_ph_down: pH -0.3 to -0.5
     * add_ph_up: pH +0.3 to +0.5
   - Get new state (after)
   - Check improvement
   - Save action to database
   ↓
5. Return before/after values
   ↓
6. Chatbot format response
   ↓
7. Send to user via WhatsApp
```

---

## 🔧 Prerequisites

### 1. Ollama (LLM)

```bash
# Install Ollama
brew install ollama  # macOS
# atau download dari https://ollama.ai

# Pull model
ollama pull qwen3:8b

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

### 3. Node.js & npm

```bash
# Install Node.js (v16+)
brew install node  # macOS

# Verify
node --version
npm --version
```

### 4. Python 3.9+

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
cd /Users/adrianalfajri/Projects/aeropon
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

### 3. Setup WhatsApp Webhook

```bash
cd whatsapp-webhook
npm install
cd ..
```

### 4. Setup Database

```bash
# Initialize database
python -c "from src.database.base import init_db; init_db()"
```

### 5. Download E5 Model (jika belum ada)

Model akan auto-download saat pertama kali digunakan. Atau download manual:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-base")
model.save("models/intfloat--multilingual-e5-base")
```

### 6. Populate Knowledge Base (jika belum ada)

```bash
# Run full pipeline
python src/utils/pipeline.py full
```

---

## 🚀 Menjalankan Sistem

### Quick Start (Semua Services)

```bash
./bin/startup/start-all.sh
```

Script ini akan:

1. Start Ollama (jika belum running)
2. Start Qdrant (jika belum running)
3. Start FastAPI server (port 8000)
4. Start IoT Simulator (port 3456)
5. Start WhatsApp Webhook (port 3000) - **QR code akan muncul di terminal**
6. Start Background Generator (simulator data)

**PENTING:** Scan QR code di terminal dengan WhatsApp untuk login.

### Manual Start (Per Service)

#### 1. FastAPI Server

```bash
cd api
python main.py
# atau
./start_server.sh
```

#### 2. IoT Simulator

```bash
cd simulator
python server.py
# atau
./start.sh
```

#### 3. WhatsApp Webhook

```bash
cd whatsapp-webhook
node index.js
# atau
./start.sh
```

#### 4. Background Generator (Simulator)

```bash
cd simulator
python background_generator.py
```

### Monitoring

#### Check Status

```bash
./bin/monitoring/status-all.sh
```

#### View Logs

```bash
./bin/monitoring/view-logs.sh
```

#### View Specific Log

```bash
tail -f logs/fastapi.log
tail -f logs/simulator.log
tail -f logs/whatsapp.log
```

### Shutdown

```bash
./bin/shutdown/stop-all.sh
```

---

## 📁 Struktur Project

```
aeropon/
├── api/                          # FastAPI application
│   ├── main.py                   # Main server
│   ├── test_client.py            # Test client
│   └── start_server.sh           # Startup script
│
├── src/                          # Source code utama
│   ├── core/                     # Core engines
│   │   ├── hybrid_chatbot.py     # Hybrid chatbot orchestrator
│   │   ├── rag_engine.py         # RAG engine
│   │   ├── rule_engine.py        # Rule-based diagnostics
│   │   ├── onboarding_engine.py  # User onboarding
│   │   ├── simulator_client.py   # Simulator API client
│   │   └── rag_storage.py        # RAG process storage
│   │
│   ├── database/                 # Database operations
│   │   ├── base.py               # Database setup
│   │   ├── models.py             # SQLAlchemy models
│   │   └── operations.py         # CRUD operations
│   │
│   ├── api/                      # API routes
│   │   └── onboarding_routes.py  # Onboarding endpoints
│   │
│   └── utils/                    # Utilities
│       └── pipeline.py           # Knowledge base pipeline
│
├── simulator/                    # IoT Simulator
│   ├── server.py                 # FastAPI server
│   ├── data_generator.py         # Sensor data generator
│   ├── lstm_predictor.py         # LLM-based predictor
│   ├── gamification.py           # Gamification engine
│   ├── database_integration.py   # Database ops
│   ├── background_generator.py   # Background data generation
│   └── config.json               # Configuration
│
├── whatsapp-webhook/             # WhatsApp integration
│   ├── index.js                  # Main webhook
│   ├── http_server.js            # HTTP server untuk alerts
│   ├── conversations/            # Conversation storage
│   └── auth_info/                # WhatsApp auth
│
├── bin/                          # Shell scripts
│   ├── startup/                  # Start scripts
│   │   └── start-all.sh          # Start all services
│   ├── shutdown/                 # Stop scripts
│   │   └── stop-all.sh           # Stop all services
│   ├── monitoring/               # Monitoring scripts
│   │   ├── status-all.sh         # Check status
│   │   └── view-logs.sh          # View logs
│   └── utils/                    # Utility scripts
│       ├── setup.sh              # Initial setup
│       └── reset-database.sh     # Reset database
│
├── scripts/                      # Python scripts
│   ├── testing/                  # Test scripts
│   ├── migration/                # Migration scripts
│   ├── admin/                    # Admin scripts
│   └── benchmarks/               # Benchmark scripts
│
├── docs/                         # Documentation
│   ├── presentation/             # Presentation materials
│   ├── technical/                # Technical docs
│   ├── testing/                  # Testing guides
│   └── guides/                   # User guides
│
├── data/                         # Data files
│   ├── raw/                      # Scraped data
│   ├── processed/                # Processed chunks
│   └── kb/                       # Knowledge base
│
├── logs/                         # Log files
│   ├── fastapi.log
│   ├── simulator.log
│   └── whatsapp.log
│
├── models/                       # ML models
│   └── intfloat--multilingual-e5-base/
│
├── qdrant_storage/               # Qdrant vector database
│
├── aeropon.db                    # SQLite database
├── requirements.txt              # Python dependencies
├── .ports.info                   # Port configuration
└── README.md                     # This file
```

---

## 🌐 API Endpoints

### FastAPI Server (Port 8000)

#### Chat Endpoints

**POST /chat**

```json
{
  "message": "pH saya 4.5, bagaimana?",
  "user_id": "628123456789",
  "language": "id",
  "include_images": true,
  "conversation_history": [
    { "role": "user", "message": "halo" },
    { "role": "assistant", "message": "Halo!" }
  ]
}
```

Response:

```json
{
  "success": true,
  "answer": "pH 4.5 terlalu rendah...",
  "intent": "hybrid",
  "confidence": 0.9,
  "has_sensor_data": true,
  "sensor_data": {...},
  "sources": ["UF IFAS Extension"],
  "images": ["path/to/image.png"],
  "rag_dashboard_url": "https://xxx.ngrok.io/?query_id=123"
}
```

**POST /diagnose**

```json
{
  "ph": 4.5,
  "tds": 1500,
  "temperature": 28,
  "humidity": 65,
  "growth_stage": "vegetative"
}
```

**POST /onboarding**

```json
{
  "user_id": "628123456789",
  "message": "Adrian"
}
```

#### User Endpoints

**GET /user/{user_id}**  
Get user profile dengan plants

**GET /user/{user_id}/onboarding-status**  
Check onboarding status

**GET /user/{user_id}/plants**  
Get user's plants

#### System Endpoints

**GET /health**  
Health check (chatbot, Qdrant, Ollama status)

**GET /stats**  
System statistics (vector count, models, etc)

---

### Simulator API (Port 3456)

**GET /current**  
Current sensor values

**GET /history?hours=24&insights=true**  
Historical data dengan optional insights

**POST /action**

```json
{
  "action_type": "add_nutrient",
  "amount": 1.0,
  "user_id": "628123456789"
}
```

**GET /predict?force_refresh=false**  
LSTM prediction

**GET /insights?hours=24**  
Automated insights & alerts

**GET /health**  
Simulator health check

**GET /stats**  
Simulator statistics

---

## 🧪 Testing

### Quick Test

```bash
# Test chatbot
python api/test_client.py

# Test onboarding
python scripts/testing/test-onboarding-interactive.py

# Test comprehensive
python scripts/testing/test-comprehensive.py
```

### Manual Testing via WhatsApp

1. Start all services
2. Scan QR code
3. Send message ke nomor WhatsApp yang di-scan
4. Test scenarios:
   - Greeting: "halo"
   - Onboarding: (jika user baru)
   - Knowledge query: "apa itu hidroponik?"
   - Sensor query: "pH saya 4.5, bagaimana?"
   - Action: "tambah nutrisi"

### Testing Workflow

Lihat `.agent/workflows/testing.md` untuk panduan lengkap.

```bash
# Run testing workflow
# Follow steps di workflow file
```

---

## 🐛 Troubleshooting

### 1. Ollama Not Running

```bash
# Check
curl http://localhost:11434/api/tags

# Start
ollama serve
```

### 2. Qdrant Not Running

```bash
# Check
curl http://localhost:6333/collections

# Start
docker run -p 6333:6333 qdrant/qdrant
```

### 3. WhatsApp QR Code Tidak Muncul

```bash
# Check logs
tail -f whatsapp-webhook/logs/webhook.log

# Restart
cd whatsapp-webhook
./start.sh
```

### 4. FastAPI Error: Chatbot Not Initialized

```bash
# Check Qdrant & Ollama
curl http://localhost:6333/collections
curl http://localhost:11434/api/tags

# Restart FastAPI
cd api
python main.py
```

### 5. Simulator Not Responding

```bash
# Check status
curl http://localhost:3456/health

# Restart
cd simulator
python server.py
```

### 6. Database Error

```bash
# Reset database
./bin/utils/reset-database.sh

# Atau manual
rm aeropon.db
python -c "from src.database.base import init_db; init_db()"
```

### 7. Port Already in Use

```bash
# Check ports
lsof -i :8000
lsof -i :3456
lsof -i :3000

# Kill process
kill -9 <PID>

# Atau gunakan stop-all.sh
./bin/shutdown/stop-all.sh
```

---

## 📚 Dokumentasi Tambahan

- **Quick Reference**: `QUICK_REFERENCE.md` - Navigasi cepat folder & files
- **Technical Documentation**: `docs/technical/TECHNICAL_DOCUMENTATION.md`
- **Testing Guide**: `docs/testing/TESTING_GUIDE.md`
- **Presentation**: `docs/presentation/PRESENTASI_AEROPON_SLIDES.md`

---

## 🔑 Port Configuration

Semua port disimpan di `.ports.info`:

```
FASTAPI_PORT=8000
SIMULATOR_PORT=3456
WHATSAPP_PORT=3000
DASHBOARD_PORT=8501
DB_VIEWER_PORT=8502
RAG_DASHBOARD_URL=https://xxx.ngrok-free.dev
```

---

## 🎯 Use Cases

### 1. User Baru - Onboarding

```
User: "halo"
Bot: "Halo! Selamat datang di Aeropon..."
     "Siapa nama kamu?"
User: "Adrian"
Bot: "Senang berkenalan dengan kamu, Adrian!"
     "Tanaman apa yang kamu tanam?"
User: "selada"
Bot: "Oke, selada! Tahap pertumbuhan apa saat ini?"
User: "vegetatif"
Bot: "Sempurna! Onboarding selesai..."
```

### 2. Knowledge Query

```
User: "apa kelebihan hidroponik?"
Bot: [RAG Engine]
     "Hidroponik memiliki beberapa kelebihan..."
     "📚 Sumber: UF IFAS Extension"
     "Lihat detail RAG: https://xxx.ngrok.io/?query_id=123"
```

### 3. Sensor Diagnostics

```
User: "pH saya 4.5, TDS 1500"
Bot: [Rule-Based Engine]
     "pH 4.5 terlalu rendah (kritis)..."
     "TDS 1500 ppm dalam range normal..."
     "Rekomendasi: Tambah pH Up (basa)"
```

### 4. Hybrid Query

```
User: "pH saya 4.5, bagaimana cara memperbaikinya?"
Bot: [Hybrid: RAG + Rule-Based]
     "Untuk menaikkan pH, kamu bisa..."
     [RAG answer dengan detailed steps]
     "Saya lihat pH kamu 4.5 (kritis)..."
     [Rule-based diagnostic]
```

### 5. Action Execution

```
User: "tambah pH up"
Bot: [Action Executor]
     "✅ Menambah pH Up Berhasil!"
     "Sebelum: pH 4.5, TDS 1500"
     "Sesudah: pH 5.2, TDS 1500"
     "🎉 Kondisi tanaman membaik!"
```

---

## 🎨 Customization

### Mengubah Thresholds

Edit `src/core/rule_engine.py`:

```python
THRESHOLDS = {
    'ph': {
        'optimal': (5.5, 6.5),
        'warning': (5.0, 7.0),
        'critical': (4.5, 7.5)
    },
    # ...
}
```

### Mengubah LLM Model

Edit `src/core/rag_engine.py`:

```python
ollama_model: str = "qwen3:8b"  # Ganti dengan model lain
```

### Mengubah Embedding Model

Edit `src/core/rag_engine.py`:

```python
model_name: str = "intfloat/multilingual-e5-base"  # Ganti
```

### Menambah Data Sources

Edit `src/scrapers/` dan tambah scraper baru, lalu:

```bash
python src/utils/pipeline.py full
```

---

## 📊 Monitoring & Analytics

### View Logs

```bash
# All logs
./bin/monitoring/view-logs.sh

# Specific service
tail -f logs/fastapi.log
tail -f logs/simulator.log
tail -f logs/whatsapp.log
```

### Database Viewer

```bash
# Start database viewer
./bin/startup/start-database-viewer.sh

# Access at http://localhost:8502
```

### RAG Dashboard

Access via ngrok URL di `.ports.info`:

```bash
cat .ports.info | grep RAG_DASHBOARD_URL
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set proper CORS origins di `api/main.py`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set environment variables untuk sensitive data
- [ ] Use process manager (PM2, systemd)
- [ ] Setup reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Setup monitoring (Prometheus, Grafana)
- [ ] Setup backup untuk database & conversations
- [ ] Rate limiting untuk API endpoints
- [ ] Authentication untuk admin endpoints

---

## 👨‍💻 Developer

**Adrian Alfajri**  
Project: Aeropon - Smart Hydroponic/Aquaponic Chatbot  
Last Updated: 2025-12-10

---

## 📄 License

Educational Use - Universitas Indonesia

---

**Selamat menggunakan Aeropon! 🌱**

Untuk pertanyaan atau issues, silakan buka issue di repository atau hubungi developer.
