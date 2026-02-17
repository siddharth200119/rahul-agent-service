// app.js
const express = require("express");
const morgan = require("morgan");
const logger = require("./middleware/logger");
const bodyParser = require("body-parser");

const MessagingProvider = require("./providers/WebJSProvider");
const MessageRepository = require("./repositories/PostgresRepository");
const llmService = require("./services/WebhookService");

// Controllers
const MessageController = require("./controllers/MessageController");
const WebhookController = require("./controllers/WebhookController");
const messageRoutes = require("./routes/messageRoutes");
const axios = require("axios");
const config = require("./config");

const messenger = new MessagingProvider();
const db = new MessageRepository();

// Initialize Controllers
const messageCtrl = new MessageController(messenger, db);
const webhookCtrl = new WebhookController(db);

const app = express();

// app.use(morgan("dev"));
app.use(logger);

app.use(bodyParser.json());

// --- ROUTES ---
app.use("/", messageRoutes(messageCtrl, webhookCtrl));

// --- EVENT LISTENERS ---

messenger.onMessage(async (msg) => {
  console.log(`📩 Incoming message from ${msg.from}`);
  try {
    // 1. Clean the incoming number (e.g., "917229091491@c.us" -> "7229091491")
    const contact = await msg.getContact();
    const rawNumber = contact.number;
    const mobileNumber =
      rawNumber.length > 10 ? rawNumber.slice(-10) : rawNumber;

    const isGroup = msg.from.endsWith("@g.us");
    const allowedGroups = process.env.ALLOWED_GROUP_IDS
      ? process.env.ALLOWED_GROUP_IDS.split(",").map((id) => id.trim())
      : [];

    // 🚫 If message is from group but NOT in allowed list → ignore
    if (isGroup && !allowedGroups.includes(msg.from)) {
      console.log(`🚫 Message from unauthorized group ${msg.from}. Ignoring.`);
      return;
    }
    console.log(`🔍 Looking up POC for mobile: ${mobileNumber}`);

    // 2. Map phone number to user using the filter payload
    let userId;
    try {
      const adminResponse = await axios.post(
        `${config.hosts.backend}/v1/admin-service/poc-details/list`,
        {
          filter: [
            {
              field: "mobile_number",
              operator: "equals",
              value: mobileNumber,
            },
          ],
        }
      );

      const pocs = adminResponse.data?.data?.pocs;
      if (!pocs || pocs.length === 0) {
        console.warn(`⚠️ No POC found for number: ${mobileNumber}.`);
        return;
      } else {
        userId = pocs[0].id;
        console.log(`✅ Found POC: ${pocs[0].name} (ID: ${userId})`);
      }
    } catch (e) {
      console.error(
        `❌ Admin service error: ${e.message}. Defaulting to user 1.`
      );
      // userId = 1; // Fallback
      return;
    }

    let conversation;

    // 3. Check for existing conversation (Agent Host)
    console.log(
      `🕵️ Checking existing conversations for user ${userId} at ${config.hosts.agent}`
    );
    try {
      const convListResponse = await axios.get(
        `${config.hosts.agent}/api/conversations`,
        {
          params: { user_id: userId, limit: 1 },
        }
      );

      const existingConversations = convListResponse.data.data;

      if (existingConversations && existingConversations.length > 0) {
        conversation = existingConversations[0];
        console.log(
          `💬 Found existing conversation: ${conversation.id} (Agent: ${conversation.agent})`
        );

        // If the agent is not "inquiry", maybe we should update it?
        if (conversation.agent !== "inquiry") {
          console.log(
            `🔄 Updating conversation ${conversation.id} agent to 'inquiry'`
          );
          const updateResponse = await axios.put(
            `${config.hosts.agent}/api/conversations/${conversation.id}`,
            { agent: "inquiry" }
          );
          conversation = updateResponse.data.data;
        }
      } else {
        // 4. Create conversation if it doesn't exist
        console.log(`🆕 Creating new inquiry conversation for user ${userId}`);
        const createResponse = await axios.post(
          `${config.hosts.agent}/api/conversations`,
          {
            user_id: parseInt(userId),
            agent: "inquiry",
            title: "WhatsApp Inquiry",
          }
        );
        conversation = createResponse.data?.data;
      }
    } catch (e) {
      console.error(`❌ Agent service error: ${e.message}`);
      return;
    }

    // 5. Save message and trigger services
    console.log(
      `💾 Saving message to database for conversation ${conversation.id} (Group: ${isGroup})`
    );

    const messageData = {
      whatsapp_id: msg.id.id,
      from_number: mobileNumber,
      group_id: isGroup ? msg.from : null,
      body: msg.body,
      is_from_me: false,
      conversation_id: conversation.id,
      user_id: userId,
    };

    const id = await db.saveMessage(messageData);
    console.log(`✅ Message saved with ID: ${id}. Triggering LLM...`);

    // if (msg.body.toLowerCase() === "hi") {
    //   await messenger.sendMessage(
    //     msg.from,
    //     `Hello! I'm your Inquiry Agent. How can I help you today?`
    //   );
    // }

    await llmService.triggerLLMService(id, db);
    console.log(`🚀 LLM Service triggered for message ${id}`);
  } catch (error) {
    console.error("❌ Workflow Error:", error.response?.data || error.message);
  }
});

app.listen(8080, () => console.log("Service running on port 8080"));
