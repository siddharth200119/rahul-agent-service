const http = require('http');
const axios = require('axios');

// Configuration
const EMAIL_SERVICE_URL = "http://localhost:3001";
const WEBHOOK_PORT = 5000;
// If running in docker, host.docker.internal, else localhost
const WEBHOOK_URL_LOCAL = `http://host.docker.internal:${WEBHOOK_PORT}/webhook`;

// Webhook Server
const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/webhook') {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            console.log('\n[Webhook Received]', JSON.parse(body));
            res.writeHead(200);
            res.end();
        });
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(WEBHOOK_PORT, async () => {
    console.log(`Webhook server listening on port ${WEBHOOK_PORT}`);

    // Wait a bit for server to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    await testEmailService();

    // Keep alive for a bit to receive webhooks
    setTimeout(() => {
        console.log('Test finished. Closing server.');
        server.close();
        process.exit(0);
    }, 5000);
});

async function testEmailService() {
    console.log("Testing Email Service...");

    // 1. Register Webhook
    console.log("\n1. Registering Webhook...");
    try {
        const res = await axios.post(`${EMAIL_SERVICE_URL}/webhooks`, { url: WEBHOOK_URL_LOCAL });
        console.log("Register Webhook Response:", res.status, res.data);
    } catch (e) {
        console.error("Failed to register webhook:", e.message);
    }

    // 2. Send Email
    console.log("\n2. Sending Email...");
    try {
        const payload = {
            to: "test@example.com",
            subject: "Test Email from Agent",
            text: "This is a test email sent via the email service API."
        };
        const res = await axios.post(`${EMAIL_SERVICE_URL}/send`, payload);
        console.log("Send Email Response:", res.status, res.data);
    } catch (e) {
        console.error("Failed to send email:", e.message);
    }

    // 3. List Webhooks
    console.log("\n3. Listing Webhooks...");
    try {
        const res = await axios.get(`${EMAIL_SERVICE_URL}/webhooks`);
        console.log("List Webhooks Response:", res.status, res.data);
    } catch (e) {
        console.error("Failed to list webhooks:", e.message);
    }

    console.log("\nRequests completed. Waiting for webhook...");
}
