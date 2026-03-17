const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const nodemailer = require('nodemailer');
const imaps = require('imap-simple');
const simpleParser = require('mailparser').simpleParser;
const axios = require('axios');
const Minio = require('minio');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });

const app = express();
app.use(express.json());

const port = process.env.EMAIL_SERVICE_PORT || 3001;

// Database Connection
const sequelize = new Sequelize(
    process.env.APP_DB_NAME,
    process.env.APP_DB_UNAME,
    process.env.APP_DB_PASS,
    {
        host: process.env.APP_DB_HOST,
        port: process.env.APP_DB_PORT,
        dialect: 'postgres',
        logging: false,
    }
);

// Models
const Email = sequelize.define('Email', {
    id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
    message_id: { type: DataTypes.TEXT, unique: true },
    thread_id: DataTypes.TEXT,
    subject: DataTypes.TEXT,
    sender_email: { type: DataTypes.TEXT, allowNull: false },
    receiver_email: { type: DataTypes.TEXT, allowNull: false },
    sender_role: { type: DataTypes.STRING, allowNull: false }, // 'user' or 'assistant'
    timestamp: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
    in_reply_to: DataTypes.UUID,
    attachments: DataTypes.ARRAY(DataTypes.TEXT),
    content: DataTypes.TEXT,
    content_type: DataTypes.STRING,
}, { tableName: 'emails', underscored: true });

const Webhook = sequelize.define('Webhook', {
    id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
    url: { type: DataTypes.TEXT, allowNull: false },
}, { tableName: 'email_webhooks', underscored: true, updatedAt: false });

// MinIO Client
const minioClient = new Minio.Client({
    endPoint: process.env.MINIO_ENDPOINT || 'minio',
    port: parseInt(process.env.MINIO_PORT || '9000'),
    useSSL: false,
    accessKey: process.env.MINIO_ROOT_USER || 'admin',
    secretKey: process.env.MINIO_ROOT_PASSWORD || 'admin123',
});

const BUCKET_NAME = process.env.EMAIL_BUCKET || 'email-attachments';

async function ensureBucket() {
    try {
        const exists = await minioClient.bucketExists(BUCKET_NAME);
        if (!exists) {
            await minioClient.makeBucket(BUCKET_NAME, 'us-east-1');
            console.log(`Bucket ${BUCKET_NAME} created.`);
        }
    } catch (err) {
        console.error('Error ensuring MinIO bucket:', err);
    }
}

// SMTP Transporter
const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT,
    secure: process.env.SMTP_SECURE === 'true',
    auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
    },
    tls: {
        rejectUnauthorized: false
    }
});

// IMAP Configuration
const imapConfig = {
    imap: {
        user: process.env.IMAP_USER,
        password: process.env.IMAP_PASSWORD,
        host: process.env.IMAP_HOST,
        port: process.env.IMAP_PORT,
        tls: process.env.IMAP_TLS === 'true',
        tlsOptions: {
            rejectUnauthorized: false
        },
        authTimeout: 3000,
    },
};

// Helper to upload to MinIO
async function uploadToMinio(filename, buffer, mimetype) {
    const objectName = `${uuidv4()}-${filename}`;
    await minioClient.putObject(BUCKET_NAME, objectName, buffer, buffer.length, { 'Content-Type': mimetype });
    // Return a URL or path. Since it's internal MinIO, we might just return the object name or a constructable URL.
    // For now, let's return the object name, or a full URL if we have a public endpoint.
    // Assuming internal access mostly, but let's store the object name.
    // Or better, store a relative path that can be served.
    return objectName;
}

// IMAP Listener
let fetchTimeout = null;
let isFetching = false;

async function startImapListener() {
    try {
        const connection = await imaps.connect(imapConfig);
        console.log('IMAP connected');

        await connection.openBox('INBOX');
        console.log('INBOX opened successfully');

        // Listen for new emails
        // imap-simple doesn't have a direct 'mail' event listener like node-imap, 
        // but it exposes the underlying node-imap connection.
        connection.imap.on('mail', async (numNewMsgs) => {
            console.log(`New email notification received! (${numNewMsgs} new messages)`);

            // Debounce: wait 2 seconds before fetching to batch multiple notifications
            if (fetchTimeout) {
                clearTimeout(fetchTimeout);
            }

            fetchTimeout = setTimeout(() => {
                fetchNewEmails(connection);
            }, 2000);
        });

        // Initial fetch of unread emails
        console.log('Performing initial fetch of UNSEEN emails...');
        fetchNewEmails(connection);

        connection.imap.on('error', (err) => {
            console.error('IMAP error:', err);
            // Reconnect logic could go here
        });

        connection.imap.on('end', () => {
            console.log('IMAP connection ended');
        });

    } catch (err) {
        console.error('Error connecting to IMAP:', err);
        setTimeout(startImapListener, 10000); // Retry after 10s
    }
}

async function fetchNewEmails(connection) {
    // Prevent concurrent fetches
    if (isFetching) {
        console.log('Skipping fetch - already fetching emails');
        return;
    }

    isFetching = true;

    try {
        console.log('🔍 Searching for UNSEEN emails...');
        const searchCriteria = ['UNSEEN'];
        const fetchOptions = {
            bodies: ['HEADER', 'TEXT', ''],
            markSeen: true,  // Mark as seen after fetching
            struct: true
        };

        const messages = await connection.search(searchCriteria, fetchOptions);

        console.log(`Found ${messages.length} UNSEEN email(s)`);

        for (const item of messages) {
            const all = item.parts.find(part => part.which === '');
            const id = item.attributes.uid;
            const idHeader = "Imap-Id: " + id + "\r\n";

            const simple = await simpleParser(idHeader + all.body);

            const sender = simple.from.value[0].address;
            const receiver = simple.to.value[0].address; // Might be array
            const subject = simple.subject;
            const text = simple.text;
            const html = simple.html;
            const rawMessageId = simple.messageId || '';
            const cleanMessageId = rawMessageId
                .replace(/^<|>$/g, '')   // remove < >
                .split('@')[0];          // remove domain

            const messageId = cleanMessageId;

            const rawInReplyTo = simple.inReplyTo || '';
            const cleanInReplyTo = rawInReplyTo
                .replace(/^<|>$/g, '')
                .split('@')[0];
            const inReplyTo = simple.inReplyTo;
            const references = simple.references;

            // Handle attachments
            const attachmentLinks = [];
            if (simple.attachments) {
                for (const att of simple.attachments) {
                    try {
                        const link = await uploadToMinio(att.filename, att.content, att.contentType);
                        attachmentLinks.push(link);
                    } catch (uploadErr) {
                        console.error(`Failed to upload attachment "${att.filename}" to MinIO:`, uploadErr.message);
                        // Continue processing — email still gets stored and webhook still fires
                    }
                }
            }

            let parentEmail = null;

            if (inReplyTo) {
                parentEmail = await Email.findOne({
                    where: { message_id: inReplyTo }
                });
            }

            let threadId;
            if (parentEmail) {
                threadId = parentEmail.thread_id || parentEmail.id;
            } else {
                threadId = messageId; // new thread fallback
            }

            // Store in DB
            const emailRecord = await Email.create({
                sender_email: sender,
                receiver_email: receiver,
                sender_role: 'user',
                message_id: messageId,
                subject: subject,
                in_reply_to: parentEmail?.id || null,
                content: text || html,
                content_type: html ? 'text/html' : 'text/plain',
                attachments: attachmentLinks,
                thread_id: threadId, // Use the calculated stable threadId
            });

            console.log(`Stored email from ${sender}`);

            // Trigger Webhooks — route by subject
            // Emails whose subject contains "approval" (case-insensitive) go to
            // approval webhooks only; all other emails go to non-approval webhooks.
            const webhooks = await Webhook.findAll();
            const isApprovalEmail = subject && subject.toLowerCase().includes('approval');

            console.log(`Triggering webhooks for email (isApproval=${isApprovalEmail}) subject="${subject}"...`);

            for (const hook of webhooks) {
                const hookIsApproval = hook.url.toLowerCase().includes('approval');

                // Only fire the webhook if its type matches the email type
                if (hookIsApproval !== isApprovalEmail) {
                    console.log(`Skipping webhook ${hook.url} (subject mismatch)`);
                    continue;
                }

                try {
                    await axios.post(hook.url, {
                        event: 'new_email',
                        data: emailRecord
                    });
                    console.log(`Triggered webhook: ${hook.url}`);
                } catch (err) {
                    console.error(`Failed to trigger webhook ${hook.url}:`, err.message);
                }
            }
        }
    } catch (err) {
        console.error('Error fetching emails:', err);
    } finally {
        isFetching = false;  // Release lock
    }
}

// API Endpoints

// Send Email
app.post('/send', async (req, res) => {
    const { to, subject, text, html, attachments, thread_id } = req.body; // attachments: array of { filename, content (base64) or path }

    if (!to || (!text && !html)) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        const mailOptions = {
            from: process.env.SMTP_USER,
            to,
            subject,
            text,
            html,
            attachments: attachments // Nodemailer format
        };

        const info = await transporter.sendMail(mailOptions);

        // Clean "<id@gmail.com>" -> "id"
        const rawMessageId = info.messageId || '';
        const cleanMessageId = rawMessageId
            .replace(/^<|>$/g, '')   // remove < >
            .split('@')[0];          // remove domain


        console.log("DB CONFIG:", {
            host: process.env.APP_DB_HOST,
            port: process.env.APP_DB_PORT,
            db: process.env.APP_DB_NAME
        });

        // Store sent email in DB
        const emailRecord = await Email.create({
            sender_email: process.env.SMTP_USER,
            receiver_email: to,
            sender_role: 'assistant',
            message_id: cleanMessageId,
            subject: subject,
            content: text || html,
            content_type: html ? 'text/html' : 'text/plain',
            thread_id: thread_id,
            // attachments: ... handle outgoing attachments storage if needed
        });

        console.log(`Stored email from ${process.env.SMTP_USER} successfully to the database ${process.env.APP_DB_NAME} on host ${process.env.APP_DB_HOST}`);

        res.json({ success: true, messageId: info.messageId });
    } catch (err) {
        console.error('Error sending email:', err);
        res.status(500).json({ error: 'Failed to send email' });
    }
});

// Webhooks
app.post('/webhooks', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL is required' });
    try {
        const hook = await Webhook.create({ url });
        res.status(201).json(hook);
    } catch (err) {
        res.status(500).json({ error: 'Failed to create webhook' });
    }
});

app.get('/webhooks', async (req, res) => {
    const hooks = await Webhook.findAll();
    res.json(hooks);
});

app.delete('/webhooks/:id', async (req, res) => {
    const { id } = req.params;
    await Webhook.destroy({ where: { id } });
    res.json({ success: true });
});

// Start Server
app.listen(port, async () => {
    console.log(`Email service listening on port ${port}`);
    await ensureBucket();
    startImapListener();
});
