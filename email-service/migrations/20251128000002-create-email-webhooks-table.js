'use strict';

module.exports = {
    async up(queryInterface, Sequelize) {
        await queryInterface.sequelize.query(`
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      CREATE TABLE IF NOT EXISTS email_webhooks (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          url TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `);
    },

    async down(queryInterface, Sequelize) {
        await queryInterface.sequelize.query('DROP TABLE IF EXISTS email_webhooks;');
    }
};
