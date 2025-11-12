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
    
    // Validar que haya texto
    if (!userText || userText.length < 3) {
      await say({
        text: '👋 ¡Hola! Cuéntame qué tecnología o habilidad técnica quieres aprender.',
        thread_ts: event.ts
      });
      return;
    }

    try {
      const userInfo = await client.users.info({ user: event.user });
      const user = userInfo.user;
      const email = user.profile.email;

      const skillRecords = await getEmployeeByEmail(email);
      const payload = {
        objective: userText,
        skills: (skillRecords || []).map(toPublicSkill),
      };

      // Enviar mensaje de procesando
      const initialMsg = await say({
        text: '⏳ Procesando tu solicitud...',
        thread_ts: event.ts
      });

      // Array para guardar los timestamps de los mensajes de progreso
      const progressMessageTimestamps = [initialMsg.ts];

      try {
        // Callback de progreso para actualizar en Slack
        const progressCallback = async (message) => {
          try {
            const msg = await say({ text: message, thread_ts: event.ts });
            progressMessageTimestamps.push(msg.ts);
          } catch (err) {
            console.error('Error enviando mensaje de progreso:', err);
          }
        };

        const pythonOutput = await sendToPythonAgent(payload, progressCallback);
        console.log('[Agent] Raw output:', pythonOutput);
        const extracted = extractResponseFromAgentOutput(pythonOutput);
        console.log('[Agent] Extracted response:', extracted);
        const text = extracted || 'No pude generar respuesta.';
        
        // Borrar todos los mensajes de progreso
        for (const ts of progressMessageTimestamps) {
          try {
            await client.chat.delete({
              channel: event.channel,
              ts: ts
            });
          } catch (delErr) {
            console.error('Error borrando mensaje de progreso:', delErr);
          }
        }

        // Enviar respuesta final
        const chunks = splitIntoChunks(text, 3000);
        for (const chunk of chunks.length ? chunks : [text]) {
          await say({ text: chunk, thread_ts: event.ts });
        }
      } catch (err) {
        console.error('Error enviando al módulo de Python:', err);
        
        // Borrar mensajes de progreso incluso si hay error
        for (const ts of progressMessageTimestamps) {
          try {
            await client.chat.delete({
              channel: event.channel,
              ts: ts
            });
          } catch (delErr) {
            console.error('Error borrando mensaje de progreso:', delErr);
          }
        }
        
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
    
    const userText = (message.text || '').trim();
    
    // Validar que haya texto
    if (!userText || userText.length < 3) {
      await say('👋 ¡Hola! Cuéntame qué tecnología o habilidad técnica quieres aprender.');
      return;
    }

    try {
      const userInfo = await client.users.info({ user: message.user });
      const user = userInfo.user;
      const email = user.profile.email;

      const skillRecords = await getEmployeeByEmail(email);
      const payload = {
        objective: userText,
        skills: (skillRecords || []).map(toPublicSkill),
      };

      // Enviar mensaje de procesando
      const initialMsg = await say('⏳ Procesando tu solicitud...');

      // Array para guardar los timestamps de los mensajes de progreso
      const progressMessageTimestamps = [initialMsg.ts];

      try {
        // Callback de progreso para actualizar en Slack
        const progressCallback = async (message) => {
          try {
            const msg = await say(message);
            progressMessageTimestamps.push(msg.ts);
          } catch (err) {
            console.error('Error enviando mensaje de progreso:', err);
          }
        };

        const pythonOutput = await sendToPythonAgent(payload, progressCallback);
        console.log('[Agent] Raw output (DM):', pythonOutput);
        const extracted = extractResponseFromAgentOutput(pythonOutput);
        console.log('[Agent] Extracted response (DM):', extracted);
        const text = extracted || 'No pude generar respuesta.';
        
        // Borrar todos los mensajes de progreso
        for (const ts of progressMessageTimestamps) {
          try {
            await client.chat.delete({
              channel: message.channel,
              ts: ts
            });
          } catch (delErr) {
            console.error('Error borrando mensaje de progreso:', delErr);
          }
        }

        // Enviar respuesta final
        const chunks = splitIntoChunks(text, 3000);
        for (const chunk of chunks.length ? chunks : [text]) {
          await say(chunk);
        }
      } catch (err) {
        console.error('Error enviando al módulo de Python:', err);
        
        // Borrar mensajes de progreso incluso si hay error
        for (const ts of progressMessageTimestamps) {
          try {
            await client.chat.delete({
              channel: message.channel,
              ts: ts
            });
          } catch (delErr) {
            console.error('Error borrando mensaje de progreso:', delErr);
          }
        }
        
        await say('No pude enviar el objetivo al módulo de Python.');
      }
    } catch (err) {
      console.error('Error procesando DM:', err);
      await say('Hubo un error procesando tu DM.');
    }
  });
}

module.exports = { registerHandlers };


