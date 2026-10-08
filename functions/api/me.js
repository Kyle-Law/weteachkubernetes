import { getSession, json } from '../../lib/session.js';

export async function onRequestGet({ request, env }) {
  const s = await getSession(request, env);
  if (!s) return json({ handle: null }, 200);
  const raw = await env.SESSIONS.get(`progress:${s.ghid}`);
  let done = [];
  try { done = raw ? JSON.parse(raw) : []; } catch { done = []; }
  return json({ handle: s.handle, name: s.name, id: s.ghid, done });
}
