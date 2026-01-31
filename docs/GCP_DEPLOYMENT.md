# Deployment Canopya ke GCP

## 📋 Status Deployment

### ✅ Production Ready

**VM Instance:**
- Instance: `canopya-chatbot-server`
- Zone: `asia-southeast2-a` (Jakarta)
- Machine: `e2-medium` (2 vCPU, 4GB RAM) - **Optimized untuk cost efficiency**
- External IP: `34.128.116.35`
- Internal IP: `10.184.0.2`
- OS: Ubuntu 22.04 LTS

**Services Running:**

1. **Cloudflare Tunnel** (Auto-start via systemd)
   - Tunnel: `canopya-gcp`
   - Status: Active
   - Domains:
     - `app.canopya.cloud` → FastAPI (port 8000)
     - `rag.canopya.cloud` → RAG Dashboard (port 3000)
     - `test.canopya.cloud` → Chat Tester (port 3001)

2. **FastAPI Server** (port 8000)
   - Endpoint: https://app.canopya.cloud
   - Docs: https://app.canopya.cloud/docs
   - Health: https://app.canopya.cloud/health

3. **RAG Dashboard** (port 3000)
   - URL: https://rag.canopya.cloud
   - Features: RAG process visualization, document retrieval

4. **Chat Tester** (port 3001)
   - URL: https://test.canopya.cloud
   - Features: Interactive chat testing, quick questions

5. **Qdrant** (port 6333)
   - 2245 vectors
   - Collection: `aquaponics_knowledge`
   - Embeddings: `intfloat/multilingual-e5-base`

6. **Ollama** (port 11434)
   - Model: `ministral-3:3b` (lightweight, efficient)
   - Local inference

**Configuration:**
```env
QDRANT_URL=http://localhost:6333
OLLAMA_BASE_URL=http://localhost:11434
HOST=0.0.0.0
PORT=8000
```

**Performance:**
- Memory usage: ~2GB / 4GB (50%)
- CPU usage: ~30-40% during inference
- Response time: ~3-7s (end-to-end)
- Concurrent users: 2-3 (optimal for current setup)

**Cost:**
- VM: ~$30/month (e2-medium)
- Disk: ~$5/month (50GB)
- Network: ~$5/month (egress)
- **Total: ~$40/month**

---

## 🏗️ Arsitektur Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet Users                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare (DNS + Tunnel)                      │
│  - app.canopya.cloud  → 34.128.116.35:8000                  │
│  - rag.canopya.cloud  → 34.128.116.35:3000                  │
│  - test.canopya.cloud → 34.128.116.35:3001                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           GCP VM (e2-medium, asia-southeast2-a)             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Cloudflared Tunnel (systemd service)                  │ │
│  │  - Auto-start on boot                                  │ │
│  │  - Routes traffic to localhost services                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI (port 8000)                                   │ │
│  │  - Hybrid Chatbot Engine                               │ │
│  │  - RAG + Rule-Based                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RAG Dashboard (port 3000)                             │ │
│  │  - Streamlit app                                       │ │
│  │  - RAG process visualization                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Chat Tester (port 3001)                               │ │
│  │  - Streamlit app                                       │ │
│  │  - Interactive chat interface                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Qdrant (port 6333)                                    │ │
│  │  - Vector database                                     │ │
│  │  - 2245 vectors                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Ollama (port 11434)                                   │ │
│  │  - LLM inference engine                                │ │
│  │  - Model: ministral-3:3b                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SQLite Database (aeropon.db)                          │ │
│  │  - User data, messages, RAG processes                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup Guide

### 1. Prerequisites

**Local Machine:**
- gcloud CLI installed
- SSH access ke GCP VM

**GCP VM:**
- Ubuntu 22.04 LTS
- Python 3.10+
- Docker (untuk Qdrant)
- Ollama
- Cloudflared

### 2. Initial Setup (One-time)

#### a. Create GCP VM

```bash
gcloud compute instances create canopya-chatbot-server \
  --zone=asia-southeast2-a \
  --machine-type=e2-medium \
  --boot-disk-size=50GB \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=http-server,https-server
```

#### b. SSH ke VM

```bash
gcloud compute ssh canopya-chatbot-server --zone=asia-southeast2-a
```

#### c. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3-pip python3-venv -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull ministral-3:3b

# Install Cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

#### d. Clone Repository

```bash
git clone https://github.com/AlphaJr1/canopya.git
cd canopya
```

#### e. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### f. Start Qdrant

```bash
docker run -d -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant
```

#### g. Setup Cloudflare Tunnel

**Di Cloudflare Dashboard:**
1. Login: https://dash.cloudflare.com
2. Zero Trust → Networks → Tunnels → Create Tunnel
3. Nama: `canopya-gcp`
4. Copy token

**Di VM:**
```bash
# Install as service
sudo cloudflared service install <TOKEN>

# Start service
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

**Configure Public Hostname:**
1. Di Cloudflare Dashboard → Tunnel → Public Hostname
2. Add routes:
   - `app.canopya.cloud` → `http://localhost:8000`
   - `rag.canopya.cloud` → `http://localhost:3000`
   - `test.canopya.cloud` → `http://localhost:3001`

---

## 🔧 Daily Operations

### VM Management (dari Local)

**Start VM:**
```bash
gcloud compute instances start canopya-chatbot-server --zone=asia-southeast2-a
```

**Stop VM:**
```bash
gcloud compute instances stop canopya-chatbot-server --zone=asia-southeast2-a
```

**Check Status:**
```bash
gcloud compute instances describe canopya-chatbot-server \
  --zone=asia-southeast2-a \
  --format="get(status)"
```

**SSH ke VM:**
```bash
gcloud compute ssh canopya-chatbot-server --zone=asia-southeast2-a
```

### Service Management (di VM)

**Start All Services:**
```bash
cd canopya

# FastAPI
./bin/startup/start-fastapi-gcp.sh

# RAG Dashboard
./bin/startup/start-rag-dashboard-gcp.sh

# Chat Tester
./bin/startup/start-chat-tester-gcp.sh
```

**Stop All Services:**
```bash
./bin/shutdown/stop-fastapi-gcp.sh
./bin/shutdown/stop-rag-dashboard-gcp.sh
./bin/shutdown/stop-chat-tester-gcp.sh
```

**Check Status:**
```bash
# All services
ps aux | grep -E "fastapi|streamlit|cloudflared" | grep -v grep

# FastAPI
curl http://localhost:8000/health

# RAG Dashboard
curl http://localhost:3000

# Chat Tester
curl http://localhost:3001

# Qdrant
curl http://localhost:6333/collections/aquaponics_knowledge

# Ollama
curl http://localhost:11434/api/tags
```

**View Logs:**
```bash
# FastAPI
tail -f .run/logs/fastapi.log

# RAG Dashboard
tail -f .run/logs/rag-dashboard.log

# Chat Tester
tail -f .run/logs/chat-tester.log

# Cloudflared
sudo journalctl -u cloudflared -f
```

---

## 📊 Monitoring

### Health Checks

**FastAPI:**
```bash
curl https://app.canopya.cloud/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "chatbot_ready": true,
  "qdrant_status": "healthy",
  "ollama_status": "healthy",
  "timestamp": "2026-01-31T09:00:00"
}
```

### Resource Usage

**Memory:**
```bash
free -h
```

**CPU:**
```bash
top
```

**Disk:**
```bash
df -h
```

**Network:**
```bash
sudo netstat -tulpn | grep -E "8000|3000|3001|6333|11434"
```

---

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Kill process on port
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:3000 | xargs kill -9
sudo lsof -ti:3001 | xargs kill -9
```

### Qdrant Not Running

```bash
# Check Docker
docker ps

# Start Qdrant
docker start qdrant

# Restart Qdrant
docker restart qdrant
```

### Ollama Not Responding

```bash
# Check Ollama
ollama list

# Restart Ollama
sudo systemctl restart ollama
```

### Cloudflare Tunnel Down

```bash
# Check status
sudo systemctl status cloudflared

# Restart tunnel
sudo systemctl restart cloudflared

# View logs
sudo journalctl -u cloudflared -n 50
```

### Out of Memory

```bash
# Check memory
free -h

# Kill heavy processes
ps aux --sort=-%mem | head -10

# Consider upgrading VM to e2-standard-2 (8GB RAM)
```

### Service Won't Start

```bash
# Check logs
tail -100 .run/logs/fastapi.log

# Check Python environment
source venv/bin/activate
which python

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 🔄 Updates & Maintenance

### Update Code

```bash
# SSH ke VM
gcloud compute ssh canopya-chatbot-server --zone=asia-southeast2-a

# Stop services
cd canopya
./bin/shutdown/stop-fastapi-gcp.sh
./bin/shutdown/stop-rag-dashboard-gcp.sh
./bin/shutdown/stop-chat-tester-gcp.sh

# Pull latest code
git pull origin main

# Update dependencies (if needed)
source venv/bin/activate
pip install -r requirements.txt

# Restart services
./bin/startup/start-fastapi-gcp.sh
./bin/startup/start-rag-dashboard-gcp.sh
./bin/startup/start-chat-tester-gcp.sh
```

### Backup Database

```bash
# Backup SQLite database
cp aeropon.db aeropon.db.backup.$(date +%Y%m%d)

# Backup Qdrant data
tar -czf qdrant_storage.backup.$(date +%Y%m%d).tar.gz qdrant_storage/
```

### Restore Database

```bash
# Restore SQLite
cp aeropon.db.backup.20260131 aeropon.db

# Restore Qdrant
tar -xzf qdrant_storage.backup.20260131.tar.gz
docker restart qdrant
```

---

## 💰 Cost Optimization

### Current Setup (e2-medium)

- **VM**: ~$30/month
- **Disk**: ~$5/month
- **Network**: ~$5/month
- **Total**: ~$40/month

### Optimization Tips

1. **Stop VM when not in use:**
   ```bash
   gcloud compute instances stop canopya-chatbot-server --zone=asia-southeast2-a
   ```
   Saves ~$1/day

2. **Use Preemptible VM** (for development):
   - 80% cheaper
   - Can be terminated anytime
   - Not recommended for production

3. **Downgrade if traffic is low:**
   - e2-micro (0.25 vCPU, 1GB RAM): ~$7/month
   - Only for very light usage

4. **Upgrade if needed:**
   - e2-standard-2 (2 vCPU, 8GB RAM): ~$60/month
   - For higher traffic (5-10 concurrent users)

### Change Machine Type

```bash
# Stop VM
gcloud compute instances stop canopya-chatbot-server --zone=asia-southeast2-a

# Change machine type
gcloud compute instances set-machine-type canopya-chatbot-server \
  --zone=asia-southeast2-a \
  --machine-type=e2-standard-2

# Start VM
gcloud compute instances start canopya-chatbot-server --zone=asia-southeast2-a
```

---

## 🔐 Security

### Firewall Rules

**Current Setup:**
- All traffic goes through Cloudflare Tunnel
- No direct port exposure needed
- Cloudflare provides DDoS protection

**Recommended:**
```bash
# Block direct access to ports (optional)
gcloud compute firewall-rules create block-direct-access \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=DENY \
  --rules=tcp:8000,tcp:3000,tcp:3001 \
  --source-ranges=0.0.0.0/0
```

### SSH Access

**Restrict SSH to specific IPs:**
```bash
gcloud compute firewall-rules update default-allow-ssh \
  --source-ranges=YOUR_IP/32
```

---

## 📝 Scripts Reference

### Startup Scripts

- `bin/startup/start-fastapi-gcp.sh` - Start FastAPI server
- `bin/startup/start-rag-dashboard-gcp.sh` - Start RAG Dashboard
- `bin/startup/start-chat-tester-gcp.sh` - Start Chat Tester

### Shutdown Scripts

- `bin/shutdown/stop-fastapi-gcp.sh` - Stop FastAPI server
- `bin/shutdown/stop-rag-dashboard-gcp.sh` - Stop RAG Dashboard
- `bin/shutdown/stop-chat-tester-gcp.sh` - Stop Chat Tester

### Log Files

- `.run/logs/fastapi.log` - FastAPI logs
- `.run/logs/rag-dashboard.log` - RAG Dashboard logs
- `.run/logs/chat-tester.log` - Chat Tester logs

---

## 🎯 Next Steps (Optional)

### 1. Setup Systemd Services

Create systemd services untuk auto-restart on boot:
- FastAPI
- RAG Dashboard
- Chat Tester

### 2. Setup Log Rotation

Prevent logs from filling disk:
```bash
sudo apt install logrotate
```

### 3. Setup Monitoring

- Google Cloud Monitoring
- Uptime checks
- Alert notifications

### 4. Setup CI/CD

- GitHub Actions untuk auto-deploy
- Automated testing
- Rolling updates

---

## 📞 Support

**Issues:**
- GitHub: https://github.com/AlphaJr1/canopya/issues

**Documentation:**
- README: https://github.com/AlphaJr1/canopya/blob/main/README.md

---

**Last Updated:** 2026-01-31  
**VM Status:** Running  
**Services:** All operational  
**Deployment:** Production ready ✅
