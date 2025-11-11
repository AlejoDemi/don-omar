require('dotenv').config();
const { App } = require('@slack/bolt');
const { registerHandlers } = require('./src/slack/handlers');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  appToken: process.env.SLACK_APP_TOKEN,
  socketMode: true,
});

registerHandlers(app);

(async () => {
  await app.start();
  console.log('⚡️ Bot de Slack corriendo con Socket Mode');
})();
