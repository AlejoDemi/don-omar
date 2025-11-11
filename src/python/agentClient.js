const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function safeParseJson(text) {
  try {
    return JSON.parse(text);
  } catch (_) {
    try {
      const m = String(text || '').match(/\{[\s\S]*\}/);
      if (m && m[0]) {
        return JSON.parse(m[0]);
      }
    } catch (_) {}
  }
  return null;
}

function extractJsonStringValue(raw, key) {
  const s = String(raw || '');
  const needle = `"${key}"`;
  let idx = s.indexOf(needle);
  if (idx === -1) return null;
  // Find first quote after colon
  idx = s.indexOf(':', idx);
  if (idx === -1) return null;
  // Skip whitespace
  while (idx + 1 < s.length && /\s/.test(s[idx + 1])) idx++;
  if (s[idx + 1] !== '"') return null;
  let i = idx + 2;
  let escaped = false;
  let buf = '';
  while (i < s.length) {
    const ch = s[i];
    if (escaped) {
      buf += ch;
      escaped = false;
    } else if (ch === '\\\\') {
      escaped = true;
    } else if (ch === '"') {
      // end of string
      try {
        return JSON.parse('"' + buf + '"');
      } catch (_) {
        return buf;
      }
    } else {
      buf += ch;
    }
    i++;
  }
  return null;
}

function extractResponseFromAgentOutput(output) {
  try {
    const data = typeof output === 'string' ? safeParseJson(output) : output;
    // Unified contract: prefer 'response'
    if (data && typeof data.response === 'string') return data.response.trim();
    if (data && data.result && typeof data.result.response === 'string') return data.result.response.trim();
    if (data && data.received && typeof data.received.response === 'string') return data.received.response.trim();
  } catch (_) {}
  // Regex fallback
  try {
    const text = String(output || '');
    const val = extractJsonStringValue(text, 'response') ||
                extractJsonStringValue(text, 'smart_objective') ||
                extractJsonStringValue(text, 'summary');
    if (typeof val === 'string') return val.trim();
  } catch (_) {}
  return null;
}

async function sendToPythonAgent(payload) {
  const agentUrl = process.env.PY_AGENT_URL || 'http://127.0.0.1:8000/agent';
  try {
    const axios = require('axios');
    const res = await axios.post(agentUrl, payload, { timeout: 15000 });
    return JSON.stringify(res && res.data);
  } catch (httpErr) {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(__dirname, '../../python', 'agent.py');
      const projectRoot = path.join(__dirname, '..', '..');
      const venvPython = process.env.PYTHON_BIN || path.join(projectRoot, '.venv', 'bin', 'python');
      const pythonExec = fs.existsSync(venvPython) ? venvPython : 'python3';
      console.log(`[Agent] Spawning Python: ${pythonExec} ${scriptPath}`);
      const py = spawn(pythonExec, [scriptPath], { stdio: ['pipe', 'pipe', 'pipe'] });

      let stdout = '';
      let stderr = '';

      py.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      py.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      py.on('close', (code) => {
        if (code === 0) {
          resolve(stdout.trim());
        } else {
          reject(new Error(`Python exited with code ${code}: ${stderr}`));
        }
      });

      try {
        py.stdin.write(JSON.stringify(payload));
        py.stdin.end();
      } catch (err) {
        reject(err);
      }
    });
  }
}

module.exports = {
  sendToPythonAgent,
  extractResponseFromAgentOutput,
};


