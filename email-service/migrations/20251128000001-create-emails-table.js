'use strict';

module.exports = {
    async up(queryInterface, Sequelize) {
        await queryInterface.sequelize.query(`
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      CREATE TABLE IF NOT EXISTS emails (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          message_id TEXT UNIQUE,
          thread_id TEXT,
          subject TEXT,
          sender_email TEXT NOT NULL,
          receiver_email TEXT NOT NULL,
          sender_role VARCHAR(255) NOT NULL,
          timestamp TIMESTAMPTZ DEFAULT NOW(),
          in_reply_to UUID,
          attachments TEXT[],
          content TEXT,
          content_type VARCHAR(255),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `);
    },

    async down(queryInterface, Sequelize) {
        await queryInterface.sequelize.query('DROP TABLE IF EXISTS emails;');
    }
};
