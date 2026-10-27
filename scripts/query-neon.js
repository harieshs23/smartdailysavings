require('dotenv').config();
const { createNeonClient } = require('@neon/sdk');
const { Client } = require('pg');

async function runQuery(sql) {
  const neon = createNeonClient({ apiKey: process.env.NEON_API_KEY });
  const { data: connStr, error } = await neon.postgres.connectionString({
    projectId: process.env.NEON_PROJECT_ID,
  });

  if (error) {
    throw error;
  }

  const client = new Client({
    connectionString: connStr,
    ssl: { rejectUnauthorized: false },
  });

  try {
    await client.connect();
    const result = await client.query(sql);
    console.log(JSON.stringify(result.rows, null, 2));
  } finally {
    await client.end();
  }
}

const sql = process.argv[2] || 'select * from playing_with_neon;';
runQuery(sql).catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
