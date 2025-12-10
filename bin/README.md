# Folder `bin/` - Script Shell Aeropon

Folder ini berisi semua script shell untuk mengelola sistem Aeropon.

## Struktur Folder

### 📂 `startup/`
Script untuk memulai berbagai service:
- `start-all.sh` - Memulai semua service (FastAPI, WhatsApp, Simulator, Dashboard, Database Viewer)
- `start-db-manager.sh` - Memulai database manager
- `start-database-viewer.sh` - Memulai database viewer
- `start-ngrok.sh` - Memulai ngrok tunnel

### 📂 `shutdown/`
Script untuk menghentikan service:
- `stop-all.sh` - Menghentikan semua service yang berjalan
- `stop-database-viewer.sh` - Menghentikan database viewer

### 📂 `monitoring/`
Script untuk monitoring dan viewing:
- `status-all.sh` - Cek status semua service
- `view-logs.sh` - Melihat log dari berbagai service
- `view-database-logs.sh` - Melihat log database viewer
- `view-database.sh` - Membuka database viewer

### 📂 `utils/`
Script utility dan helper:
- `find-free-port.sh` - Mencari port yang tersedia
- `reset-database.sh` - Reset database ke kondisi awal
- `restart-db-manager.sh` - Restart database manager
- `setup.sh` - Setup awal project
- `setup-dependencies.sh` - Install dependencies
- `test-onboarding.sh` - Test onboarding flow
- `test-quick.sh` - Quick test untuk sistem
- `commands.sh` - Kumpulan command utility

## Cara Penggunaan

### Memulai Sistem
```bash
./bin/startup/start-all.sh
```

### Menghentikan Sistem
```bash
./bin/shutdown/stop-all.sh
```

### Cek Status
```bash
./bin/monitoring/status-all.sh
```

### Melihat Logs
```bash
./bin/monitoring/view-logs.sh
```
