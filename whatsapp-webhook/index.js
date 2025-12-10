import makeWASocket, { 
    DisconnectReason, 
    useMultiFileAuthState,
    fetchLatestBaileysVersion,
    makeCacheableSignalKeyStore
} from '@whiskeysockets/baileys';
import axios from 'axios';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { createHTTPServer } from './http_server.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CONFIG = {
    FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
    HTTP_PORT: parseInt(process.env.WHATSAPP_HTTP_PORT) || 3000,
    LOG_FILE: path.join(__dirname, 'logs', 'webhook.log'),
    CONVERSATIONS_DIR: path.join(__dirname, 'conversations'),
    AUTH_DIR: path.join(__dirname, 'auth_info'),
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 menit
};

await fs.ensureDir(path.dirname(CONFIG.LOG_FILE));
await fs.ensureDir(CONFIG.CONVERSATIONS_DIR);
await fs.ensureDir(CONFIG.AUTH_DIR);

class Logger {
    constructor(logFile) {
        this.logFile = logFile;
        this.logStream = fs.createWriteStream(logFile, { flags: 'a' });
    }

    _formatMessage(level, message, data = null) {
        const timestamp = new Date().toISOString();
        let logEntry = `[${timestamp}] [${level}] ${message}`;
        if (data) {
            logEntry += `\n${JSON.stringify(data, null, 2)}`;
        }
        return logEntry + '\n';
    }

    trace(message, data = null) {
        // Trace level - very detailed, optional logging
        // Don't write to file to avoid clutter
    }

    debug(message, data = null) {
        // Debug level - optional logging
        // Don't write to file to avoid clutter
    }

    info(message, data = null) {
        const formatted = this._formatMessage('INFO', message, data);
        this.logStream.write(formatted);
    }

    error(message, data = null) {
        const formatted = this._formatMessage('ERROR', message, data);
        this.logStream.write(formatted);
    }

    warn(message, data = null) {
        const formatted = this._formatMessage('WARN', message, data);
        this.logStream.write(formatted);
    }

    qr(qrCode) {
        const timestamp = new Date().toISOString();
        const qrEntry = `\n${'='.repeat(80)}\n[${timestamp}] [QR CODE]\n${qrCode}\n${'='.repeat(80)}\n\n`;
        this.logStream.write(qrEntry);
    }

    close() {
        this.logStream.end();
    }
}

const logger = new Logger(CONFIG.LOG_FILE);

class ConversationManager {
    constructor(conversationsDir) {
        this.conversationsDir = conversationsDir;
        this.sessions = new Map(); // session_id -> { messages: [], lastActivity: timestamp }
    }

    async saveMessage(phoneNumber, role, message, metadata = {}) {
        const sessionId = this._getSessionId(phoneNumber);
        const conversationFile = path.join(this.conversationsDir, `${sessionId}.json`);

        // Load existing conversation
        let conversation = { session_id: sessionId, phone_number: phoneNumber, messages: [] };
        if (await fs.pathExists(conversationFile)) {
            conversation = await fs.readJson(conversationFile);
        }

        // Add new message
        const messageEntry = {
            timestamp: new Date().toISOString(),
            role, // 'user' or 'assistant'
            message,
            ...metadata
        };
        conversation.messages.push(messageEntry);

        // Update last activity
        conversation.last_activity = new Date().toISOString();

        // Save to file
        await fs.writeJson(conversationFile, conversation, { spaces: 2 });

        // Update in-memory session
        this.sessions.set(sessionId, {
            messages: conversation.messages,
            lastActivity: Date.now()
        });

        logger.info(`💾 Pesan disimpan untuk ${phoneNumber}`, { role, message: message.substring(0, 100) });
    }

    _getSessionId(phoneNumber) {
        // Format: user_<phone>_<date>
        const cleanPhone = phoneNumber.replace(/[^0-9]/g, '');
        const date = new Date().toISOString().split('T')[0];
        return `user_${cleanPhone}_${date}`;
    }

    getSession(phoneNumber) {
        const sessionId = this._getSessionId(phoneNumber);
        return this.sessions.get(sessionId);
    }

    cleanupOldSessions() {
        const now = Date.now();
        for (const [sessionId, session] of this.sessions.entries()) {
            if (now - session.lastActivity > CONFIG.SESSION_TIMEOUT) {
                this.sessions.delete(sessionId);
                logger.info(`🧹 Session dibersihkan: ${sessionId}`);
            }
        }
    }
}

const conversationManager = new ConversationManager(CONFIG.CONVERSATIONS_DIR);

// Cleanup old sessions setiap 10 menit
setInterval(() => conversationManager.cleanupOldSessions(), 10 * 60 * 1000);

/**
 * Membersihkan nomor WhatsApp dari format @s.whatsapp.net
 * Contoh: 628123456789@s.whatsapp.net -> 628123456789
 */
function cleanPhoneNumber(whatsappId) {
    // Hapus @s.whatsapp.net atau @c.us atau format lainnya
    return whatsappId.split('@')[0];
}

class FastAPIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async chat(message, sessionId, conversationHistory = [], language = 'id', includeImages = false) {
        try {
            logger.info(`📤 Mengirim ke FastAPI: ${message.substring(0, 100)}...`);
            
            const response = await axios.post(`${this.baseUrl}/chat`, {
                message,
                session_id: sessionId,
                language,
                include_images: includeImages,
                conversation_history: conversationHistory
            }, {
                timeout: 60000 // 60 detik timeout (increased for Ollama)
            });

            logger.info('📥 Response dari FastAPI diterima', {
                intent: response.data.intent,
                confidence: response.data.confidence,
                has_sensor_data: response.data.has_sensor_data
            });

            return response.data;
        } catch (error) {
            logger.error('❌ Error saat memanggil FastAPI', {
                error: error.message,
                stack: error.stack
            });
            throw error;
        }
    }

    async healthCheck() {
        try {
            const response = await axios.get(`${this.baseUrl}/health`, { timeout: 5000 });
            return response.data;
        } catch (error) {
            logger.error('❌ FastAPI health check gagal', { error: error.message });
            return null;
        }
    }
}

const fastapiClient = new FastAPIClient(CONFIG.FASTAPI_URL);

async function startWhatsAppBot() {
    logger.info('🚀 Memulai WhatsApp Bot...');

    // Check FastAPI health
    const health = await fastapiClient.healthCheck();
    if (health) {
        logger.info('✅ FastAPI server terhubung', health);
    } else {
        logger.warn('⚠️  FastAPI server tidak dapat dijangkau, bot tetap berjalan...');
    }

    // Load auth state
    const { state, saveCreds } = await useMultiFileAuthState(CONFIG.AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    logger.info(`📱 Menggunakan Baileys versi: ${version.join('.')}`);

    // Create socket
    const sock = makeWASocket({
        version,
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys, logger),
        },
        browser: ['Aeropon Bot', 'Chrome', '1.0.0'],
        getMessage: async (key) => {
            return { conversation: '' };
        }
    });

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n' + '='.repeat(60));
            console.log('📱 QR CODE - SCAN DENGAN WHATSAPP ANDA');
            console.log('='.repeat(60) + '\n');
            
            // Import qrcode-terminal
            const QRCode = (await import('qrcode-terminal')).default;
            
            // Generate QR code di terminal
            QRCode.generate(qr, { small: true }, (qrCode) => {
                console.log(qrCode);
                console.log('\n' + '='.repeat(60));
                console.log('CARA SCAN:');
                console.log('1. Buka WhatsApp di HP');
                console.log('2. Tap Menu (⋮) > Linked Devices');
                console.log('3. Tap "Link a Device"');
                console.log('4. Scan QR code di atas');
                console.log('='.repeat(60) + '\n');
            });
            
            logger.info('📱 QR Code ditampilkan di terminal, silakan scan dengan WhatsApp');
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            logger.warn('⚠️  Koneksi terputus', {
                reason: lastDisconnect?.error?.message,
                shouldReconnect
            });

            if (shouldReconnect) {
                logger.info('🔄 Mencoba reconnect...');
                setTimeout(() => startWhatsAppBot(), 5000);
            }
        } else if (connection === 'open') {
            logger.info('✅ WhatsApp terhubung!');
            
            // Start HTTP server untuk simulator
            if (!sock.httpServer) {
                sock.httpServer = createHTTPServer(sock, logger, CONFIG.HTTP_PORT);
                logger.info(`🌐 HTTP server untuk simulator started on port ${CONFIG.HTTP_PORT}`);
            }
        }

    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.update', async (updates) => {
        for (const update of updates) {
            try {
                // Check if this is a button response
                if (update.update?.pollUpdates || update.update?.reactionMessage) {
                    continue; // Skip polls and reactions
                }
                
                // Handle button responses
                const message = update.key;
                if (message && update.update?.message?.buttonsResponseMessage) {
                    const buttonResponse = update.update.message.buttonsResponseMessage;
                    const selectedButtonId = buttonResponse.selectedButtonId;
                    const phoneNumber = message.remoteJid;
                    
                    logger.info(`🔘 Button clicked: ${selectedButtonId} from ${phoneNumber}`);
                    
                    // Parse button ID (format: action_<action_type>)
                    if (selectedButtonId.startsWith('action_')) {
                        const actionType = selectedButtonId.replace('action_', '');
                        
                        // Handle different actions
                        if (actionType === 'check_guide') {
                            // Send guide link or info
                            await sock.sendMessage(phoneNumber, {
                                text: '📖 *Panduan Hidroponik*\\n\\nUntuk panduan lengkap, tanyakan ke chatbot dengan mengetik:\\n• \"bagaimana cara mengatur pH?\"\\n• \"cara menambah nutrisi\"\\n• \"panduan hidroponik\"'
                            });
                        } else if (actionType === 'ignore') {
                            // User chose to ignore
                            await sock.sendMessage(phoneNumber, {
                                text: 'Baik, alert diabaikan. Jika kondisi memburuk, saya akan mengingatkan lagi.'
                            });
                        } else {
                            // Execute simulator action
                            try {
                                const response = await axios.post('http://localhost:3456/action', {
                                    action_type: actionType,
                                    amount: 1.0
                                }, { timeout: 30000 }); // Increased timeout
                                
                                if (response.data.success) {
                                    const { before, after, improved } = response.data;
                                    
                                    let message = `✅ *Aksi Berhasil!*\\n\\n`;
                                    message += `**Sebelum:**\\n`;
                                    message += `• pH: ${before.ph}\\n`;
                                    message += `• TDS: ${before.tds} ppm\\n\\n`;
                                    message += `**Sesudah:**\\n`;
                                    message += `• pH: ${after.ph}\\n`;
                                    message += `• TDS: ${after.tds} ppm\\n`;
                                    
                                    if (improved) {
                                        message += `\\n🎉 Kondisi tanaman membaik!`;
                                    }
                                    
                                    await sock.sendMessage(phoneNumber, { text: message });
                                } else {
                                    await sock.sendMessage(phoneNumber, {
                                        text: `❌ Gagal melakukan aksi: ${response.data.message}`
                                    });
                                }
                            } catch (error) {
                                logger.error('Error executing action from button', { error: error.message });
                                await sock.sendMessage(phoneNumber, {
                                    text: '❌ Terjadi kesalahan saat melakukan aksi. Silakan coba lagi atau hubungi chatbot.'
                                });
                            }
                        }
                    }
                }
            } catch (error) {
                logger.error('Error handling button update', { error: error.message });
            }
        }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            let typingStarted = false;
            
            try {
                // Skip jika pesan dari bot sendiri
                if (msg.key.fromMe) continue;

                // Extract info
                const rawPhoneNumber = msg.key.remoteJid;
                const phoneNumber = cleanPhoneNumber(rawPhoneNumber); // Bersihkan nomor dari @s.whatsapp.net
                const messageText = msg.message?.conversation || 
                                  msg.message?.extendedTextMessage?.text || '';

                if (!messageText) continue;

                logger.info('📨 Pesan masuk', {
                    from: phoneNumber,
                    raw: rawPhoneNumber,
                    message: messageText.substring(0, 100)
                });

                // Save user message
                await conversationManager.saveMessage(phoneNumber, 'user', messageText);

                // Get session ID
                const sessionId = conversationManager._getSessionId(phoneNumber);

                // START typing indicator (gunakan rawPhoneNumber untuk WhatsApp API)
                await sock.sendPresenceUpdate('composing', rawPhoneNumber);
                typingStarted = true;

                // Check onboarding status
                let botResponse;
                let responseMetadata = {};
                
                try {
                    // Check if user needs onboarding (gunakan phoneNumber yang sudah dibersihkan)
                    const onboardingCheckResponse = await axios.get(
                        `${CONFIG.FASTAPI_URL}/user/${phoneNumber}/onboarding-status`,
                        { timeout: 5000 }
                    );

                    
                    const needsOnboarding = !onboardingCheckResponse.data.completed;
                    
                    if (needsOnboarding) {
                        // Route to onboarding
                        logger.info(`🎯 Routing to onboarding for ${phoneNumber}`);
                        
                        const onboardingResponse = await axios.post(
                            `${CONFIG.FASTAPI_URL}/onboarding`,
                            {
                                user_id: phoneNumber,
                                message: messageText
                            },
                            { timeout: 60000 } // Increased for Ollama
                        );
                        
                        botResponse = onboardingResponse.data.answer;
                        responseMetadata = {
                            onboarding: true,
                            onboarding_step: onboardingResponse.data.current_step,
                            onboarding_completed: onboardingResponse.data.onboarding_completed
                        };
                        
                    } else {
                        // Route to normal chatbot
                        logger.info(`💬 Routing to chatbot for ${phoneNumber}`);
                        
                        // Get conversation history
                        const session = conversationManager.getSession(phoneNumber);
                        const conversationHistory = session?.messages || [];
                        
                        // Format conversation history for API (last 10 messages)
                        const formattedHistory = conversationHistory
                            .slice(-10)
                            .map(msg => ({
                                role: msg.role,
                                message: msg.message
                            }));
                        
                        const apiResponse = await fastapiClient.chat(messageText, sessionId, formattedHistory);
                        botResponse = apiResponse.answer;
                        responseMetadata = {
                            intent: apiResponse.intent,
                            confidence: apiResponse.confidence,
                            has_sensor_data: apiResponse.has_sensor_data,
                            sensor_data: apiResponse.sensor_data
                        };
                    }

                    // Save bot response with metadata
                    await conversationManager.saveMessage(phoneNumber, 'assistant', botResponse, responseMetadata);

                } catch (apiError) {
                    // API error - log but don't send to user
                    logger.error('❌ API Error', {
                        error: apiError.message,
                        stack: apiError.stack,
                        phone: phoneNumber
                    });
                    
                    // STOP typing on error
                    if (typingStarted) {
                        await sock.sendPresenceUpdate('paused', rawPhoneNumber);
                        typingStarted = false;
                    }
                    
                    // Don't send error message to user, just log
                    // User will think bot is not responding, which is better than showing error
                    continue;
                }

                // STOP typing before sending message
                if (typingStarted) {
                    await sock.sendPresenceUpdate('paused', rawPhoneNumber);
                    typingStarted = false;
                }
                
                // Send response (gunakan rawPhoneNumber untuk WhatsApp API)
                await sock.sendMessage(rawPhoneNumber, { text: botResponse });

                logger.info('📤 Pesan terkirim', {
                    to: phoneNumber,
                    message: botResponse.substring(0, 100)
                });

            } catch (error) {
                // General error - log and stop typing
                logger.error('❌ Error saat memproses pesan', {
                    error: error.message,
                    stack: error.stack
                });
                
                // STOP typing on error
                if (typingStarted) {
                    try {
                        await sock.sendPresenceUpdate('paused', rawPhoneNumber);
                    } catch (e) {
                        logger.error('Failed to stop typing indicator', { error: e.message });
                    }
                }
                
                // Don't send error to user
            }
        }
    });

    
    /**
     * Endpoint untuk menerima alert dari simulator
     * POST /send-alert
     * Body: { phone_number, alert: {type, severity, message, recommended_action}, buttons: [{id, text}] }
     */
    sock.sendAlert = async (phoneNumber, alert, buttons = []) => {
        try {
            logger.info(`📢 Sending alert to ${phoneNumber}`, { type: alert.type, severity: alert.severity });
            
            // Format message
            const severityEmoji = {
                'critical': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️'
            };
            
            const emoji = severityEmoji[alert.severity] || 'ℹ️';
            let messageText = `${emoji} *Alert: ${alert.message}*\n\n`;
            
            if (alert.recommended_action) {
                const actionLabels = {
                    'add_nutrient': 'Tambah Nutrisi',
                    'add_water': 'Tambah Air',
                    'add_ph_down': 'Tambah pH Down (Asam)',
                    'add_ph_up': 'Tambah pH Up (Basa)',
                    'monitor': 'Monitor Terus'
                };
                const actionLabel = actionLabels[alert.recommended_action] || alert.recommended_action;
                messageText += `💡 Rekomendasi: ${actionLabel}\n`;
            }
            
            // Send message with buttons if available
            if (buttons && buttons.length > 0) {
                // Baileys buttons format
                const buttonMessage = {
                    text: messageText,
                    footer: 'Aeropon - Smart Hydroponics',
                    buttons: buttons.map(btn => ({
                        buttonId: btn.id,
                        buttonText: { displayText: btn.text },
                        type: 1
                    })),
                    headerType: 1
                };
                
                await sock.sendMessage(phoneNumber, buttonMessage);
            } else {
                // Send plain text if no buttons
                await sock.sendMessage(phoneNumber, { text: messageText });
            }
            
            logger.info(`✅ Alert sent to ${phoneNumber}`);
            
            // Save to conversation
            await conversationManager.saveMessage(phoneNumber, 'assistant', messageText, {
                alert_type: alert.type,
                severity: alert.severity,
                recommended_action: alert.recommended_action
            });
            
            return true;
        } catch (error) {
            logger.error(`❌ Error sending alert to ${phoneNumber}`, { error: error.message });
            return false;
        }
    };
    
    /**
     * Endpoint untuk mengirim sensor update
     * POST /send-message
     * Body: { phone_number, message, sensor_data }
     */
    sock.sendSensorUpdate = async (phoneNumber, message, sensorData = null) => {
        try {
            await sock.sendMessage(phoneNumber, { text: message });
            
            await conversationManager.saveMessage(phoneNumber, 'assistant', message, {
                sensor_data: sensorData,
                message_type: 'sensor_update'
            });
            
            logger.info(`📊 Sensor update sent to ${phoneNumber}`);
            return true;
        } catch (error) {
            logger.error(`❌ Error sending sensor update`, { error: error.message });
            return false;
        }
    };

    return sock;
}

process.on('SIGINT', () => {
    logger.info('🛑 Menerima SIGINT, shutting down...');
    logger.close();
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('🛑 Menerima SIGTERM, shutting down...');
    logger.close();
    process.exit(0);
});

logger.info('=' .repeat(80));
logger.info('🤖 AEROPON WHATSAPP WEBHOOK BOT');
logger.info('=' .repeat(80));
logger.info('Konfigurasi:', CONFIG);

startWhatsAppBot().catch((error) => {
    logger.error('❌ Fatal error saat start bot', {
        error: error.message,
        stack: error.stack
    });
    process.exit(1);
});
