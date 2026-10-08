import { COOKIE, cookies, setCookie, json } from '../../../lib/session.js';

const SESSION_DAYS = 30;

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const jar = cookies(request);

  /* Without this check, any site could walk a visitor through our sign-in. */
  if (!code || !state || state !== jar.wtk_state) {
    return json({ error: 'bad state' }, 400);
  }

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { accept: 'application/json', 'content-type': 'application/json' },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,   // a Worker secret; never sent to a browser
      code,
    }),
  });
  const tok = await tokenRes.json().catch(() => ({}));
  if (!tok.access_token) return json({ error: 'token exchange failed' }, 502);

  const who = await fetch('https://api.github.com/user', {
    headers: {
      authorization: `Bearer ${tok.access_token}`,
      accept: 'application/vnd.github+json',
      'user-agent': 'weteachkubernetes-site',
    },
  }).then((r) => (r.ok ? r.json() : null));
  if (!who?.login) return json({ error: 'could not read profile' }, 502);

  /* We needed the token for exactly one call. Keep the identity, drop the token. */
  const sid = crypto.randomUUID();
  await env.SESSIONS.put(
    `session:${sid}`,
    JSON.stringify({ handle: who.login, ghid: who.id, name: who.name || who.login }),
    { expirationTtl: SESSION_DAYS * 86400 },
  );

  const headers = new Headers({ Location: jar.wtk_next || '/' });
  headers.append('Set-Cookie', setCookie(COOKIE, sid, { maxAge: SESSION_DAYS * 86400 }));
  headers.append('Set-Cookie', setCookie('wtk_state', '', { clear: true }));
  headers.append('Set-Cookie', setCookie('wtk_next', '', { clear: true }));
  return new Response(null, { status: 302, headers });
}
