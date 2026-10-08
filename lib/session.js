/* Session handling. The GitHub token is used once, at callback time, and discarded:
   we only ever need to know which handle is talking to us. */

export const COOKIE = 'wtk_session';

export function cookies(request) {
  const out = {};
  const raw = request.headers.get('cookie') || '';
  for (const part of raw.split(';')) {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}

export function setCookie(name, value, { maxAge = 0, clear = false } = {}) {
  const bits = [
    `${name}=${clear ? '' : encodeURIComponent(value)}`,
    'Path=/', 'HttpOnly', 'Secure', 'SameSite=Lax',
    `Max-Age=${clear ? 0 : maxAge}`,
  ];
  return bits.join('; ');
}

/** Resolve the caller, or null. Anonymous is the normal answer on this site. */
export async function getSession(request, env) {
  const id = cookies(request)[COOKIE];
  if (!id) return null;
  const raw = await env.SESSIONS.get(`session:${id}`);
  if (!raw) return null;
  try { return { id, ...JSON.parse(raw) }; } catch { return null; }
}

export const json = (body, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers },
  });
