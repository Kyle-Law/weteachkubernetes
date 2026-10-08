import { getSession, json } from '../../lib/session.js';
import { installationToken, gh } from '../../lib/github.js';

/* A dead-link report becomes an issue, with a name against it. */
export async function onRequestPost({ request, env }) {
  const s = await getSession(request, env);
  if (!s) return json({ error: 'sign in first' }, 401);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }
  const checkpoint = String(body.checkpoint || '').replace(/[^a-z0-9-]/g, '').slice(0, 64);
  if (!checkpoint) return json({ error: 'which checkpoint?' }, 400);

  const key = `report:${s.ghid}:${checkpoint}`;
  if (await env.SESSIONS.get(key)) return json({ ok: true, duplicate: true });

  try {
    const api = gh(await installationToken(env));
    const issue = await api.post(`/repos/${env.REPO_OWNER}/${env.REPO_NAME}/issues`, {
      title: `dead link reported on ${checkpoint}`,
      body: `Reported by @${s.handle} through the site.\n\nCheckpoint: \`${checkpoint}\``,
      labels: ['dead-link'],
    });
    await env.SESSIONS.put(key, '1', { expirationTtl: 30 * 86400 });
    return json({ ok: true, number: issue.number });
  } catch (err) {
    console.error('report failed', err?.message);
    return json({ error: 'could not file the report' }, 502);
  }
}
