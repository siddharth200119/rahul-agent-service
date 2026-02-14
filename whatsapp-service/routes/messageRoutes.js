// routes/messageRoutes.js
const express = require("express");
const router = express.Router();

module.exports = (messageCtrl, webhookCtrl) => {
  // Message Endpoints
  router.post("/send", messageCtrl.sendMessage);

  // Webhook Management Endpoints
  router.get("/webhooks", webhookCtrl.getWebhooks);
  router.post("/webhooks", webhookCtrl.registerWebhook);
  router.delete("/webhooks/:id", webhookCtrl.deleteWebhook);
  
  return router;
};