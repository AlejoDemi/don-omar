const { extractObjective } = require('../utils/objective');
const { toPublicSkill } = require('../utils/skills');
const { getEmployeeByEmail } = require('../airtable/skills');
const { sendToPythonAgent, extractResponseFromAgentOutput } = require('../python/agentClient');

function splitIntoChunks(text, maxLen = 3000) {
  if (!text) return [];
  const parts = [];
  const paragraphs = String(text).split(/\n{2,}/g);
  let buffer = '';
  for (const p of paragraphs) {
    const para = buffer ? `\n\n${p}` : p;
    if ((buffer + para).length <= maxLen) {
      buffer += para;
    } else {
      if (buffer) parts.push(buffer);
      if (para.length <= maxLen) {
        buffer = para;
      } else {
        // hard split long paragraph
        let i = 0;
        while (i < para.length) {
          parts.push(para.slice(i, i + maxLen));
          i += maxLen;
        }
        buffer = '';
      }
    }
  }
  if (buffer) parts.push(buffer);
  return parts;
}

function registerHandlers(app) {
  // Mentions
  app.event('app_mention', async ({ event, say, client }) => {
    const userText = event.text.replace(/<@[^>]+>/, '').trim();
    try {
      const userInfo = await client.users.info({ user: event.user });
      const user = userInfo.user;
      const email = user.profile.email;

      const objective = extractObjective(userText);
      if (!objective) {
        await say({
          text: `Hola ${user.real_name} 👋. Para procesar tu solicitud, envía: "objetivo: <tu objetivo técnico>".`,
          thread_ts: event.ts
        });
        return;
      }

      const skillRecords = await getEmployeeByEmail(email);
      const payload = {
        objective,
        skills: (skillRecords || []).map(toPublicSkill),
      };

      try {
        const pythonOutput = await sendToPythonAgent(payload);
        console.log('[Agent] Raw output:', pythonOutput);
        const extracted = extractResponseFromAgentOutput(pythonOutput);
        console.log('[Agent] Extracted response:', extracted);
        const text = extracted || 'No pude generar respuesta.';
        const chunks = splitIntoChunks(text, 3000);
        for (const chunk of chunks.length ? chunks : [text]) {
          await say({ text: chunk, thread_ts: event.ts });
        }
      } catch (err) {
        console.error('Error enviando al módulo de Python:', err);
        await say({ text: 'No pude enviar el objetivo al módulo de Python.', thread_ts: event.ts });
      }
    } catch (error) {
      console.error('Error obteniendo info del usuario:', error);
      await say({ text: 'Hubo un error procesando tu solicitud.', thread_ts: event.ts });
    }
  });

  // DMs
  app.message(async ({ message, say, client }) => {
    if (message.channel_type !== 'im') return;
    try {
      const userInfo = await client.users.info({ user: message.user });
      const user = userInfo.user;
      const email = user.profile.email;

      const objective = extractObjective(message.text || '');
      if (!objective) {
        await say('Para procesar tu solicitud, envía: "objetivo: <tu objetivo técnico>".');
        return;
      }

      const skillRecords = await getEmployeeByEmail(email);
      const payload = {
        objective,
        skills: (skillRecords || []).map(toPublicSkill),
      };

      try {
        const pythonOutput = await sendToPythonAgent(payload);
        console.log('[Agent] Raw output (DM):', pythonOutput);
        const extracted = extractResponseFromAgentOutput(pythonOutput);
        console.log('[Agent] Extracted response (DM):', extracted);
        const text = extracted || 'No pude generar respuesta.';
        const chunks = splitIntoChunks(text, 3000);
        for (const chunk of chunks.length ? chunks : [text]) {
          await say(chunk);
        }
      } catch (err) {
        console.error('Error enviando al módulo de Python:', err);
        await say('No pude enviar el objetivo al módulo de Python.');
      }
    } catch (err) {
      console.error('Error procesando DM:', err);
      await say('Hubo un error procesando tu DM.');
    }
  });
}

module.exports = { registerHandlers };


