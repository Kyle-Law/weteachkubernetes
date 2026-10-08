import { COOKIE, cookies, setCookie, json } from '../../../lib/session.js';

export async function onRequestPost({ request, env }) {
  const sid = cookies(request)[COOKIE];
  if (sid) await env.SESSIONS.delete(`session:${sid}`);
  return json({ ok: true }, 200, { 'set-cookie': setCookie(COOKIE, '', { clear: true }) });
}
