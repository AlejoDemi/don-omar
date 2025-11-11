// Convert Airtable record fields into a public, PII-free skill object
function toPublicSkill(fields) {
  const linked = Array.isArray(fields['Name (from Skill)']) ? fields['Name (from Skill)'][0] : undefined;
  const skillName = linked || (typeof fields['Name'] === 'string' ? (fields['Name'].split(' - ')[0] || fields['Name']) : 'Unknown skill');
  const proficiency = fields['Proficiency'] || null;
  const categories = Array.isArray(fields['Categories (from Skill)']) ? fields['Categories (from Skill)'] : null;
  return {
    name: skillName,
    proficiency,
    categories,
  };
}

module.exports = {
  toPublicSkill,
};


