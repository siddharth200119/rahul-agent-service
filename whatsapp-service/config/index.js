// config/index.js
require("dotenv").config();

const config = {
  db: {
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASS,
    port: parseInt(process.env.DB_PORT) || 5432,
  },
  hosts: {
    backend: process.env.BACKEND_HOST || "http://192.168.1.62:3000",
    agent: process.env.AGENT_HOST || "http://127.0.0.1:3033",
  },
  minio: {
    endPoint: process.env.MINIO_ENDPOINT || 'localhost',
    port: parseInt(process.env.MINIO_PORT || '9000'),
    useSSL: false,
    accessKey: process.env.MINIO_ROOT_USER || 'minioadmin',
    secretKey: process.env.MINIO_ROOT_PASSWORD || 'minioadmin',
    bucket: process.env.MINIO_WHATSAPP_BUCKET || 'whatsapp-attachments',
  },
  isProduction: process.env.NODE_ENV === "production",
};

// Freeze the object so it can't be modified at runtime
module.exports = Object.freeze(config);
