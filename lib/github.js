/* Minimal GitHub App client. An installation token is scoped to one repo, expires in an
   hour and is revocable without touching anyone's personal account - which is why this
   uses an App rather than a personal access token. */

const API = 'https://api.github.com';
const UA = { 'user-agent': 'weteachkubernetes-site', accept: 'application/vnd.github+json' };

const b64url = (buf) =>
  btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

/** Sign a short-lived App JWT (RS256) with WebCrypto. */
async function appJwt(env) {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(new TextEncoder().encode(JSON.stringify({ alg: 'RS256', typ: 'JWT' })));
  const claims = b64url(new TextEncoder().encode(JSON.stringify({
    iat: now - 60, exp: now + 540, iss: env.GITHUB_APP_ID,
  })));
  const pem = env.GITHUB_APP_PRIVATE_KEY
    .replace(/-----(BEGIN|END) (RSA )?PRIVATE KEY-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey(
    'pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key,
    new TextEncoder().encode(`${header}.${claims}`));
  return `${header}.${claims}.${b64url(sig)}`;
}

export async function installationToken(env) {
  const jwt = await appJwt(env);
  const r = await fetch(`${API}/app/installations/${env.GITHUB_INSTALLATION_ID}/access_tokens`, {
    method: 'POST', headers: { ...UA, authorization: `Bearer ${jwt}` },
  });
  if (!r.ok) throw new Error(`installation token: ${r.status} ${await r.text()}`);
  return (await r.json()).token;
}

export function gh(token) {
  const call = async (method, path, body) => {
    const r = await fetch(`${API}${path}`, {
      method,
      headers: { ...UA, authorization: `Bearer ${token}`, 'content-type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await r.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON error body */ }
    if (!r.ok) throw new Error(`${method} ${path} -> ${r.status} ${data?.message || text.slice(0, 200)}`);
    return data;
  };
  return {
    get: (p) => call('GET', p),
    post: (p, b) => call('POST', p, b),
    put: (p, b) => call('PUT', p, b),
  };
}

/* Workers have no Buffer, and btoa/atob are latin1 only, so round-trip through UTF-8
   explicitly or any non-ASCII character in a title corrupts the file. */
export const decodeB64 = (s) =>
  new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, '')), (c) => c.charCodeAt(0)));
export const encodeB64 = (s) =>
  btoa(String.fromCharCode(...new TextEncoder().encode(s)));
