# Deployment Canopya ke GCP

## Status Deployment

### ✅ Yang Sudah Selesai

**VM Instance:**
- Instance: `canopya-chatbot-server`
- Zone: `asia-southeast2-a` (Jakarta)
- Machine: `e2-standard-4` (4 vCPU, 16GB RAM)
- IP: `34.128.116.35`

**Services Running:**
1. **Qdrant** (port 6333)
   - 2245 vectors (synced dari local)
   - Collection: `aquaponics_knowledge`

2. **Ollama** (port 11434)
   - Local: `ministral-3:3b`
   - Cloud: `gpt-oss:120b` (ACTIVE)

3. **FastAPI** (port 8000)
   - Endpoint: `http://34.128.116.35:8000`
   - Docs: `http://34.128.116.35:8000/docs`

**Configuration:**
```env
QDRANT_URL=http://localhost:6333
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CLOUD_API_KEY=4d3dafbda8e94538bc09203300fc6e0f.33W44AW9LTk-doBm5ykYqEAT
OLLAMA_MODE=cloud
HOST=0.0.0.0
PORT=8000
```

**Scripts:**
- `bin/startup/start-fastapi-gcp.sh` - Start FastAPI
- `bin/shutdown/stop-fastapi-gcp.sh` - Stop FastAPI
- Logs: `.run/logs/fastapi.log`

**Performance:**
- Response time: ~5-20s (dengan Ollama Cloud)
- 9x lebih cepat dari local Ollama

---

## ⏳ Next Steps

### 1. Setup Cloudflare Tunnel (PRIORITAS)

**Di Cloudflare Dashboard:**
1. Login: https://dash.cloudflare.com
2. Zero Trust → Tunnels → Create Tunnel
3. Nama: `canopya-gcp`
4. Copy credentials ke `~/.cloudflared/credentials.json`
5. Setup DNS:
   - `app.canopya.cloud` → tunnel
   - `rag.canopya.cloud` → tunnel

**Di GCP VM:**
```bash
# Start tunnel
cloudflared tunnel run canopya-gcp
```

### 2. Setup Systemd Service

Buat auto-restart untuk:
- FastAPI
- Qdrant
- Ollama
- Cloudflare Tunnel

### 3. Setup Database

Buat database untuk user management (SQLite sudah ada tapi perlu init).

### 4. Monitoring & Logging

Setup log rotation dan monitoring dashboard.

---

## Commands Penting

### VM Management (dari Local)

**Start VM:**
```bash
gcloud compute instances start canopya-chatbot-server --zone=asia-southeast2-a
# Tunggu ~30 detik, lalu SSH
gcloud compute ssh canopya-chatbot-server --zone=asia-southeast2-a
```

**Stop VM:**
```bash
gcloud compute instances stop canopya-chatbot-server --zone=asia-southeast2-a
```

**Check Status:**
```bash
gcloud compute instances describe canopya-chatbot-server --zone=asia-southeast2-a --format="get(status)"
```

### Service Management (di VM)

**Start Services:**
```bash
# FastAPI
./bin/startup/start-fastapi-gcp.sh

# Lihat logs
tail -f .run/logs/fastapi.log
```

**Stop Services:**
```bash
./bin/shutdown/stop-fastapi-gcp.sh
```

**Check Status:**
```bash
# FastAPI
ps aux | grep uvicorn

# Qdrant
curl http://localhost:6333/collections/aquaponics_knowledge

# Ollama
curl http://localhost:11434/api/tags
```

---

## Troubleshooting

**Port 8000 sudah dipakai:**
```bash
pkill -f uvicorn
```

**Qdrant tidak running:**
```bash
docker start qdrant
```

**Model cache error:**
```bash
# Cek symlink
ls -la models/
```
