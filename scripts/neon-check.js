require('dotenv').config();
const { createNeonClient } = require('@neon/sdk');

async function main() {
  const apiKey = process.env.NEON_API_KEY;
  const projectId = process.env.NEON_PROJECT_ID;

  if (!apiKey) {
    throw new Error('Set NEON_API_KEY in .env');
  }

  if (!projectId) {
    throw new Error('Set NEON_PROJECT_ID in .env');
  }

  const neon = createNeonClient({ apiKey });
  const { data, error } = await neon.projects.get({ projectId });

  if (error) {
    throw error;
  }

  console.log('Neon project details:');
  console.log(JSON.stringify({
    id: data.id,
    name: data.name,
    region_id: data.region_id,
    pg_version: data.pg_version,
    created_at: data.created_at,
    owner: data.owner,
  }, null, 2));
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
