const { Pool } = require("pg");
const BaseRepository = require("./BaseRepository");
const config = require("../config");

class PostgresRepository extends BaseRepository {
  constructor() {
    super();
    // Uses the clean config object instead of process.env
    this.pool = new Pool(config.db);
  }

  async saveMessage({ whatsapp_id, from_number, body, is_from_me, conversation_id, group_id }) {
    // We use a CTE (WITH clause) to ensure we get an ID even if the conflict occurs
    const query = `
        WITH inserted AS (
            INSERT INTO whatsapp_messages (whatsapp_id, from_number, body, is_from_me, conversation_id, group_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (whatsapp_id) DO NOTHING
            RETURNING id
        )
        SELECT id FROM inserted
        UNION ALL
        SELECT id FROM whatsapp_messages WHERE whatsapp_id = $1
        LIMIT 1;
    `;

    const values = [whatsapp_id, from_number, body, is_from_me, conversation_id, group_id];
    const result = await this.pool.query(query, values);

    // Return the ID of the record
    return result.rows[0]?.id;
  }

  async getChatHistory(from_number) {
    const query = `
            SELECT whatsapp_id, from_number, body, is_from_me, timestamp 
            FROM whatsapp_messages 
            WHERE from_number = $1 
            ORDER BY timestamp ASC;
        `;

    try {
      const result = await this.pool.query(query, [from_number]);

      return result.rows; // Returns an array of message objects
    } catch (error) {
      console.error(
        `❌ Error fetching chat history for ${from_number}:`,
        error.message
      );
      throw error;
    }
  }

  async getActiveWebhook() {
    const query = `
        SELECT url, retries, secret 
        FROM webhook_settings 
        WHERE is_active = TRUE 
        LIMIT 1;
    `;
    const result = await this.pool.query(query);
    return result.rows[0]; // Returns the dynamic config
  }
  /**
   * Inserts a new dynamic webhook configuration.
   */
  async insertWebhook({ url, retries, secret }) {
    const query = `
        INSERT INTO webhook_settings (url, retries, secret)
        VALUES ($1, $2, $3)
        RETURNING id, url, is_active;
    `;
    const result = await this.pool.query(query, [url, retries || 3, secret]);
    return result.rows[0];
  }
  async deleteWebhook(id) {
    const query = `
        DELETE FROM webhook_settings 
        WHERE id = $1 
        RETURNING id, url;
    `;
    const result = await this.pool.query(query, [id]);
    return result.rows[0]; // Returns the deleted record info or undefined if not found
  }
  /**
   * Fetches all webhooks (active and inactive).
   */
  async getAllWebhooks() {
    const query = `
        SELECT id, url, retries, secret, is_active, created_at 
        FROM webhook_settings 
        ORDER BY created_at DESC;
    `;
    const result = await this.pool.query(query);
    return result.rows;
  }
}
module.exports = PostgresRepository;
