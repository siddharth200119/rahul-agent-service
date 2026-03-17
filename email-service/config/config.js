require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

module.exports = {
    development: {
        username: process.env.APP_DB_UNAME,
        password: process.env.APP_DB_PASS,
        database: process.env.APP_DB_NAME,
        host: process.env.APP_DB_HOST,
        port: process.env.APP_DB_PORT,
        dialect: 'postgres',
    },
    test: {
        username: process.env.APP_DB_UNAME,
        password: process.env.APP_DB_PASS,
        database: process.env.APP_DB_NAME,
        host: process.env.APP_DB_HOST,
        port: process.env.APP_DB_PORT,
        dialect: 'postgres',
    },
    production: {
        username: process.env.APP_DB_UNAME,
        password: process.env.APP_DB_PASS,
        database: process.env.APP_DB_NAME,
        host: process.env.APP_DB_HOST,
        port: process.env.APP_DB_PORT,
        dialect: 'postgres',
    }
};
