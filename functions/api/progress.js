import { getSession, json } from '../../lib/session.js';

const MAX = 500;   // the roadmap is nowhere near this big; the cap is for the storage, not the user

export async function onRequestPut({ request, env }) {
  const s = await getSession(request, env);
  if (!s) return json({ error: 'sign in first' }, 401);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }
  if (!Array.isArray(body?.done)) return json({ error: 'done must be an array' }, 400);

  const done = [...new Set(body.done)]
    .filter((x) => typeof x === 'string' && /^[a-z0-9-]{1,64}$/.test(x))
    .slice(0, MAX);

  await env.SESSIONS.put(`progress:${s.ghid}`, JSON.stringify(done));
  return json({ ok: true, count: done.length });
}

/* Deleting an account's progress has to be possible without emailing anyone. */
export async function onRequestDelete({ request, env }) {
  const s = await getSession(request, env);
  if (!s) return json({ error: 'sign in first' }, 401);
  await env.SESSIONS.delete(`progress:${s.ghid}`);
  return json({ ok: true });
}
