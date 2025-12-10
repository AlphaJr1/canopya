# Aeropon WhatsApp Webhook

Webhook WhatsApp menggunakan Baileys yang terintegrasi dengan FastAPI Aeropon Chatbot.

## 🎯 Fitur

- ✅ **Auto-connect** ke WhatsApp Web menggunakan Baileys
- ✅ **QR Code Login** - QR code ditampilkan di file log
- ✅ **Logging Lengkap** - Semua aktivitas tercatat di `logs/webhook.log`
- ✅ **Simpan Percakapan** - Setiap percakapan disimpan dalam JSON di folder `conversations/`
- ✅ **Integrasi FastAPI** - Otomatis memanggil chatbot API
- ✅ **Session Management** - Tracking session per user
- ✅ **Auto Reconnect** - Otomatis reconnect jika terputus
- ✅ **No Terminal Logs** - Semua log hanya di file

## 📁 Struktur Folder

```
whatsapp-webhook/
├── index.js              # Main webhook bot
├── package.json          # Dependencies
├── logs/
│   └── webhook.log       # Log file (termasuk QR code)
├── conversations/        # Percakapan tersimpan (JSON)
│   ├── user_628xxx_2025-12-08.json
│   └── user_628yyy_2025-12-08.json
└── auth_info/           # WhatsApp auth session
    └── creds.json
```

## 🚀 Cara Menggunakan

### 1. Install Dependencies

```bash
cd whatsapp-webhook
npm install
```

### 2. Pastikan FastAPI Server Berjalan

```bash
# Di terminal lain
cd ../api
./start_server.sh
```

Server harus berjalan di `http://localhost:8000`

### 3. Jalankan Webhook Bot

```bash
npm start
```

### 4. Login WhatsApp

1. Buka file `logs/webhook.log`
2. Cari QR code (akan tampil sebagai ASCII art)
3. Scan QR code dengan WhatsApp di HP Anda
4. Setelah tersambung, bot siap menerima pesan!

## 📋 Cara Kerja

1. **User mengirim pesan** ke nomor WhatsApp bot
2. **Bot menerima pesan** dan log ke file
3. **Bot memanggil FastAPI** `/chat` endpoint dengan pesan user
4. **FastAPI memproses** dengan hybrid chatbot (RAG + Rule-based)
5. **Bot menerima response** dari API
6. **Bot mengirim balasan** ke user
7. **Percakapan disimpan** dalam JSON untuk evaluasi

## 📊 Format Percakapan JSON

File: `conversations/user_628xxx_2025-12-08.json`

```json
{
  "session_id": "user_628xxx_2025-12-08",
  "phone_number": "628xxx@s.whatsapp.net",
  "last_activity": "2025-12-08T01:30:00.000Z",
  "messages": [
    {
      "timestamp": "2025-12-08T01:25:00.000Z",
      "role": "user",
      "message": "pH saya 4.5, bagaimana cara memperbaikinya?"
    },
    {
      "timestamp": "2025-12-08T01:25:05.000Z",
      "role": "assistant",
      "message": "Berdasarkan bacaan sensor pH 4.5...",
      "intent": "hybrid",
      "confidence": 0.9,
      "has_sensor_data": true,
      "sensor_data": {
        "ph": 4.5
      }
    }
  ]
}
```

## 📝 Monitoring Logs

### Melihat Log Real-time

```bash
tail -f logs/webhook.log
```

### Mencari QR Code di Log

```bash
grep -A 20 "QR CODE" logs/webhook.log
```

### Melihat Pesan Masuk

```bash
grep "📨 Pesan masuk" logs/webhook.log
```

### Melihat Error

```bash
grep "ERROR" logs/webhook.log
```

## 🔧 Konfigurasi

Edit di `index.js`:

```javascript
const CONFIG = {
    FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
    LOG_FILE: path.join(__dirname, 'logs', 'webhook.log'),
    CONVERSATIONS_DIR: path.join(__dirname, 'conversations'),
    AUTH_DIR: path.join(__dirname, 'auth_info'),
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 menit
};
```

### Environment Variables

```bash
# Custom FastAPI URL
export FASTAPI_URL=http://your-server:8000
npm start
```

## 🛡️ Session Management

- **Session ID Format**: `user_<phone>_<date>`
- **Session Timeout**: 30 menit inaktivitas
- **Auto Cleanup**: Setiap 10 menit
- **Persistent Storage**: Semua percakapan tersimpan di JSON

## 🔄 Auto Reconnect

Bot akan otomatis reconnect jika:
- Koneksi internet terputus
- WhatsApp Web logout (kecuali manual logout)
- Server restart

## 📱 Testing

### Test dengan WhatsApp

1. Kirim pesan ke nomor bot: "Halo"
2. Bot akan balas dengan greeting dari chatbot
3. Coba kirim: "pH saya 4.5, bagaimana?"
4. Bot akan balas dengan analisis sensor

### Cek Log

```bash
cat logs/webhook.log
```

### Cek Percakapan Tersimpan

```bash
ls -la conversations/
cat conversations/user_*.json
```

## ⚠️ Troubleshooting

### QR Code tidak muncul di log

```bash
# Hapus auth lama dan restart
rm -rf auth_info/
npm start
```

### FastAPI tidak terhubung

```bash
# Cek FastAPI health
curl http://localhost:8000/health

# Pastikan server running
cd ../api
./start_server.sh
```

### Bot tidak merespon

```bash
# Cek log untuk error
grep "ERROR" logs/webhook.log

# Restart bot
npm start
```

### Percakapan tidak tersimpan

```bash
# Cek permissions folder
ls -la conversations/

# Cek log untuk error save
grep "💾 Pesan disimpan" logs/webhook.log
```

## 🎯 Production Tips

1. **Gunakan PM2** untuk auto-restart:
   ```bash
   npm install -g pm2
   pm2 start index.js --name aeropon-wa-bot
   pm2 save
   pm2 startup
   ```

2. **Log Rotation**:
   ```bash
   # Install logrotate
   sudo nano /etc/logrotate.d/aeropon-webhook
   ```
   
   ```
   /path/to/whatsapp-webhook/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       notifempty
       create 0640 user user
   }
   ```

3. **Backup Percakapan**:
   ```bash
   # Backup harian
   tar -czf conversations-backup-$(date +%Y%m%d).tar.gz conversations/
   ```

4. **Monitor dengan PM2**:
   ```bash
   pm2 monit
   pm2 logs aeropon-wa-bot
   ```

## 📊 Metrics

Log mencatat:
- ✅ Setiap pesan masuk/keluar
- ✅ API call ke FastAPI
- ✅ Response time
- ✅ Error dan stack trace
- ✅ Connection status
- ✅ QR code events
- ✅ Session cleanup

## 🔐 Security Notes

- `auth_info/` berisi credentials WhatsApp - **JANGAN commit ke Git**
- `conversations/` berisi data user - **Pastikan privacy**
- Gunakan HTTPS untuk production FastAPI
- Implementasi rate limiting jika perlu

## 📞 Support

Jika ada masalah:
1. Cek `logs/webhook.log` untuk error
2. Pastikan FastAPI running (`curl http://localhost:8000/health`)
3. Cek koneksi internet
4. Restart bot jika perlu

---

**Ready to use!** 🚀

Jalankan `npm start` dan scan QR code di `logs/webhook.log`
