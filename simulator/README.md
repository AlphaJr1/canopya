# Simulator pH & TDS - Aeropon

Simulator 24/7 untuk generate data pH dan TDS secara realistis untuk sistem hidroponik NFT (Nutrient Film Technique). Dilengkapi dengan gamification via WhatsApp dan LLM-based predictor.

## 🎯 Features

- ✅ **Realistic Data Generation**: Generate pH/TDS dengan pola NFT realistis (drift, diurnal variation, noise)
- ✅ **Gamification**: User dapat melakukan aksi (tambah nutrisi, air, pH up/down) via WhatsApp buttons
- ✅ **LLM Predictor**: Prediksi pH/TDS 6 jam ke depan dengan rekomendasi aksi menggunakan Qwen2.5:7b-instruct
- ✅ **REST API**: 8 endpoints untuk integrasi dengan chatbot dan IoT
- ✅ **Database Integration**: Menyimpan historical data, user actions, dan predictions
- ✅ **Automated Insights**: Analisis trend, anomaly detection, dan alert generation
- ✅ **24/7 Operation**: Background scheduler untuk generate data otomatis

## 📁 Struktur Folder

```
simulator/
├── config.json                 # Konfigurasi (interval, range, port, dll)
├── data_generator.py           # Core generator dengan pola NFT
├── database_integration.py     # CRUD operations dan insights
├── gamification.py             # Action validation dan alert generation
├── lstm_predictor.py           # LLM-based predictor (Qwen2.5)
├── server.py                   # FastAPI REST API
├── background_generator.py     # Background scheduler
├── start.sh                    # Startup script
├── stop.sh                     # Shutdown script
├── requirements.txt            # Python dependencies
├── logs/                       # Log files
│   └── simulator.log
└── data/                       # Runtime data
    ├── current_state.json
    └── *.pid
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd simulator
pip3 install -r requirements.txt
```

### 2. Pastikan Ollama Running

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Jika belum running, jalankan:
ollama serve

# Pastikan model sudah di-pull
ollama pull qwen2.5:7b-instruct
```

### 3. Start Simulator

```bash
./start.sh
```

Server akan running di `http://localhost:3456`

### 4. Stop Simulator

```bash
./stop.sh
```

## 📡 API Endpoints

### General

- `GET /` - Root endpoint
- `GET /health` - Health check (database, Ollama status)

### Sensor Data

- `GET /current` - Get current pH/TDS values
- `GET /history?hours=24&insights=true` - Get historical data

### Gamification

- `POST /action` - Perform user action
  ```json
  {
    "action_type": "add_nutrient",
    "amount": 1.0,
    "user_id": "6281234567890"
  }
  ```

### Prediction & Analysis

- `GET /predict?force_refresh=false` - Get LLM prediction
- `GET /insights?hours=24` - Get automated insights
- `GET /stats` - Get statistics

### Development

- `POST /generate` - Manually trigger reading generation

## 🎮 Gamification Actions

| Action | Effect | Use Case |
|--------|--------|----------|
| `add_nutrient` | TDS +150, pH -0.1 | TDS terlalu rendah |
| `add_water` | TDS -100, pH +0.05 | TDS terlalu tinggi |
| `add_ph_down` | pH -0.5, TDS +10 | pH terlalu tinggi |
| `add_ph_up` | pH +0.5, TDS +10 | pH terlalu rendah |

## 🔧 Configuration

Edit `config.json` untuk customize:

- **Interval update**: `data_generation.interval_seconds` (default: 180 detik / 3 menit)
- **Port server**: `server.port` (default: 3456)
- **Range pH/TDS**: `sensor_ranges.*`
- **LLM model**: `llm.model` (default: qwen2.5:7b-instruct)
- **Cache duration**: `llm.cache_duration_minutes` (default: 30 menit)

## 📊 Database Schema

### SimulatorReading
- `reading_id`, `ph`, `tds`, `temperature`, `status`, `source`, `anomaly_injected`, `metadata`, `created_at`

### UserAction
- `action_id`, `user_id`, `action_type`, `amount`, `ph_before`, `ph_after`, `tds_before`, `tds_after`, `improved_status`, `context`, `created_at`

### Prediction
- `prediction_id`, `predicted_ph`, `predicted_tds`, `prediction_horizon_hours`, `confidence`, `recommendation`, `recommended_action`, `llm_response`, `llm_model`, `historical_data`, `created_at`, `expires_at`

## 🧪 Testing

### Test Data Generator

```bash
cd simulator
python3 data_generator.py
```

### Test Database Integration

```bash
python3 database_integration.py
```

### Test LLM Predictor

```bash
python3 lstm_predictor.py
```

### Test API Endpoints

```bash
# Get current values
curl http://localhost:3456/current

# Get history
curl http://localhost:3456/history?hours=24

# Perform action
curl -X POST http://localhost:3456/action \
  -H "Content-Type: application/json" \
  -d '{"action_type": "add_nutrient", "amount": 1.0}'

# Get prediction
curl http://localhost:3456/predict

# Health check
curl http://localhost:3456/health
```

## 📝 Logs

Semua logs tersimpan di `logs/simulator.log` dengan format:

```
2025-12-08 16:30:00 - data_generator - INFO - Generated reading: pH=6.2, TDS=1150, Status=optimal
```

View logs real-time:

```bash
tail -f logs/simulator.log
```

## 🔗 Integrasi dengan Chatbot

Chatbot dapat polling simulator API untuk mendapatkan kondisi terkini:

```python
import requests

# Get current state
response = requests.get('http://localhost:3456/current')
data = response.json()
print(f"pH: {data['ph']}, TDS: {data['tds']}, Status: {data['status']}")

# Get insights
response = requests.get('http://localhost:3456/insights?hours=24')
insights = response.json()

# Check for alerts
if insights.get('alerts'):
    for alert in insights['alerts']:
        print(f"Alert: {alert['message']}")
        # Send to WhatsApp
```

## 🔗 Integrasi dengan IoT

IoT device dapat menggantikan simulator dengan hit endpoint yang sama:

```python
# IoT device sends real sensor data
import requests

sensor_data = {
    'ph': 6.5,
    'tds': 1200,
    'temperature': 26.0,
    'source': 'iot'
}

# POST ke endpoint (akan ditambahkan nanti)
response = requests.post('http://localhost:3456/iot/reading', json=sensor_data)
```

## 🐛 Troubleshooting

### Simulator tidak start

1. Check dependencies: `pip3 list | grep fastapi`
2. Check Ollama: `curl http://localhost:11434/api/tags`
3. Check logs: `cat logs/simulator.log`

### LLM predictor error

1. Pastikan Ollama running: `ollama serve`
2. Pastikan model sudah di-pull: `ollama pull qwen2.5:7b-instruct`
3. Check Ollama logs: `ollama list`

### Database error

1. Check PostgreSQL running
2. Check connection string di `config.json`
3. Run migration: `python3 -c "from database_integration import SimulatorDatabase; SimulatorDatabase()"`

## 📚 API Documentation

Akses interactive API docs di:
- Swagger UI: `http://localhost:3456/docs`
- ReDoc: `http://localhost:3456/redoc`

## 🎯 Roadmap

- [ ] WhatsApp integration (send alerts dengan buttons)
- [ ] Chatbot integration (context awareness)
- [ ] IoT endpoint untuk real sensor data
- [ ] Dashboard UI (Streamlit/React)
- [ ] Historical data export (CSV/JSON)
- [ ] Advanced analytics (correlation, forecasting)

## 📄 License

MIT License - Aeropon Project
