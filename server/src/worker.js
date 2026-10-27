// Offload capture inbox.
// Siri (or any client) POSTs text here with a private capture key.
// The app pulls pending items with the same key, saves them on the device, then deletes them here.
// The server only ever stores a SHA-256 hash of the key, never the key itself.

const MAX_TEXT = 4000;      // characters per capture
const MAX_PENDING = 500;    // unsynced items per key

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    if (url.pathname === '/' && req.method === 'GET') return text('Offload capture inbox is running.');

    const key = readKey(req, url);
    if (!key) return text('Missing or invalid capture key. Copy it again from Offload → Settings → Siri.', 401);
    const inbox = await sha256(key);

    try {
      if (url.pathname === '/capture' && req.method === 'POST') {
        const body = (await readText(req)).trim().slice(0, MAX_TEXT);
        if (!body) return text("I didn't catch anything to save.", 400);
        const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM captures WHERE inbox = ?').bind(inbox).first();
        if (n >= MAX_PENDING) return text('Your Offload inbox is full. Open the app to sync, then try again.', 429);
        await env.DB.prepare('INSERT INTO captures (id, inbox, body, source, created) VALUES (?, ?, ?, ?, ?)')
          .bind(crypto.randomUUID(), inbox, body, (url.searchParams.get('source') || 'siri').slice(0, 20), Date.now()).run();
        return text('Saved to Offload.');
      }

      if (url.pathname === '/inbox' && req.method === 'GET') {
        const { results } = await env.DB.prepare(
          'SELECT id, body AS text, source, created FROM captures WHERE inbox = ? ORDER BY created LIMIT 200'
        ).bind(inbox).all();
        return json({ items: results });
      }

      if (url.pathname === '/inbox' && req.method === 'DELETE') {
        const { ids } = await req.json().catch(() => ({}));
        if (!Array.isArray(ids) || !ids.length) return json({ deleted: 0 });
        const list = ids.slice(0, 200).map(String);
        const marks = list.map(() => '?').join(',');
        const r = await env.DB.prepare(`DELETE FROM captures WHERE inbox = ? AND id IN (${marks})`).bind(inbox, ...list).run();
        return json({ deleted: r.meta.changes });
      }

      return text('Not found.', 404);
    } catch (err) {
      return text('Offload could not save that right now. Try again in a moment.', 500);
    }
  },
};

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Max-Age': '86400',
};
const text = (s, status = 200) => new Response(s, { status, headers: { ...CORS, 'Content-Type': 'text/plain; charset=utf-8' } });
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });

function readKey(req, url) {
  const h = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '').trim();
  const k = h || url.searchParams.get('key') || '';
  return /^[A-Za-z0-9_-]{24,64}$/.test(k) ? k : null;
}

// Accepts JSON {"text": "..."}, a form field "text", or a plain-text body.
async function readText(req) {
  const type = req.headers.get('Content-Type') || '';
  if (type.includes('application/json')) {
    const b = await req.json().catch(() => ({}));
    return String(b.text ?? b.Text ?? b.body ?? '');
  }
  if (type.includes('form')) {
    const f = await req.formData();
    return String(f.get('text') || '');
  }
  return await req.text();
}

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}
