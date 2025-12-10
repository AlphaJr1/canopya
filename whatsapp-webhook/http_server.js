import express from 'express';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Membuat HTTP server untuk menerima alerts dari simulator
 * Server ini akan memanggil sock.sendAlert() dan sock.sendSensorUpdate()
 */
export function createHTTPServer(sock, logger, port = 3000) {
    const app = express();
    app.use(express.json());

    // Health check
    app.get('/health', (req, res) => {
        res.json({
            status: 'healthy',
            whatsapp_connected: sock.user ? true : false,
            timestamp: new Date().toISOString()
        });
    });

    // Send alert endpoint
    app.post('/send-alert', async (req, res) => {
        try {
            const { phone_number, alert, buttons } = req.body;

            if (!phone_number || !alert) {
                return res.status(400).json({
                    success: false,
                    error: 'Missing phone_number or alert'
                });
            }

            logger.info('📥 Received alert request from simulator', {
                phone: phone_number,
                alert_type: alert.type
            });

            const success = await sock.sendAlert(phone_number, alert, buttons);

            res.json({
                success,
                message: success ? 'Alert sent successfully' : 'Failed to send alert'
            });

        } catch (error) {
            logger.error('❌ Error in /send-alert endpoint', { error: error.message });
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });

    // Send message endpoint
    app.post('/send-message', async (req, res) => {
        try {
            const { phone_number, message, sensor_data } = req.body;

            if (!phone_number || !message) {
                return res.status(400).json({
                    success: false,
                    error: 'Missing phone_number or message'
                });
            }

            const success = await sock.sendSensorUpdate(phone_number, message, sensor_data);

            res.json({
                success,
                message: success ? 'Message sent successfully' : 'Failed to send message'
            });

        } catch (error) {
            logger.error('❌ Error in /send-message endpoint', { error: error.message });
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });

    // Start server
    const server = app.listen(port, () => {
        logger.info(`🌐 HTTP server listening on port ${port}`);
        logger.info(`   - Health: http://localhost:${port}/health`);
        logger.info(`   - Send Alert: POST http://localhost:${port}/send-alert`);
        logger.info(`   - Send Message: POST http://localhost:${port}/send-message`);
    });

    return server;
}
