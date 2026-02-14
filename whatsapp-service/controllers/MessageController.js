// controllers/MessageController.js
class MessageController {
  constructor(messenger, db) {
    this.messenger = messenger;
    this.db = db;
  }

  sendMessage = async (req, res) => {
    // console.log(`Send message is called ${req}`);

    const { number, message, is_reply } = req.body;
    try {
      const result = await this.messenger.sendMessage(number, message);

      if (!is_reply) {
        await this.db.saveMessage({
          whatsapp_id: result.response.id.id,
          from_number: result.response.id.remote,
          body: message,
          is_from_me: true,
        });
      }

      res.json({ status: "sent" });
    } catch (error) {
      res.status(500).json({ error: "Failed to send message" });
    }
  };

  getWebhooks = async (req, res) => {
    try {
      const webhooks = await this.db.getAllWebhooks();
      res.status(200).json(webhooks);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch webhooks" });
    }
  };

  registerWebhook = async (req, res) => {
    const { url, retries, secret } = req.body;
    if (!url) return res.status(400).json({ error: "Webhook URL is required" });

    try {
      const newWebhook = await this.db.insertWebhook({ url, retries, secret });
      res.status(201).json({
        message: "Webhook registered successfully",
        webhook: newWebhook,
      });
    } catch (error) {
      res.status(500).json({ error: "Failed to register webhook" });
    }
  };

  deleteWebhook = async (req, res) => {
    const { id } = req.params;
    try {
      const deletedWebhook = await this.db.deleteWebhook(id);
      if (!deletedWebhook)
        return res.status(404).json({ error: "Webhook not found" });
      res.status(200).json({
        message: "Webhook deleted successfully",
        deleted: deletedWebhook,
      });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete webhook" });
    }
  };
}

module.exports = MessageController;
