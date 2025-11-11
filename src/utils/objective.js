// Extract objective from free text in the form "objetivo: <texto>"
function extractObjective(text) {
  if (!text) return null;
  const match = text.match(/objetivo\s*:\s*(.+)/i);
  return match ? match[1].trim() : null;
}

module.exports = {
  extractObjective,
};


