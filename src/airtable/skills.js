const AIRTABLE_API = 'https://api.airtable.com/v0';

// Lookup employee skills by email in Airtable
async function getEmployeeByEmail(email) {
  try {
    const escapedEmail = email.replace(/'/g, "\\'");
    const formula = `{Email (from Assignee)}='${escapedEmail}'`;

    const res = await fetch(
      `${AIRTABLE_API}/${process.env.AIRTABLE_BASE_ID}/${process.env.AIRTABLE_TABLE_ID}/listRecords`,
      {
        headers: {
          Authorization: `Bearer ${process.env.AIRTABLE_TOKEN}`,
          'Content-Type': 'application/json',
        },
        method: 'POST',
        body: JSON.stringify({
          fields: ['Name', 'Name (from Skill)', 'Proficiency', 'Email (from Assignee)', 'Categories (from Skill)'],
          filterByFormula: formula,
        }),
      }
    );

    const { records } = await res.json();
    if (records && records.length > 0) {
      return records.map((record) => record.fields);
    }
    return null;
  } catch (error) {
    console.error('Error fetching from Airtable:', error);
    return null;
  }
}

module.exports = {
  getEmployeeByEmail,
};


