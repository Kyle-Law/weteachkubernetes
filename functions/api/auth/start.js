import { setCookie } from '../../../lib/session.js';

/* The authorize URL carries an EMPTY scope on purpose: GitHub's consent screen then asks
   for public profile data and nothing else. No repository access, no write access. */
export function onRequestGet({ request, env }) {
  const state = crypto.randomUUID();
  const back = new URL(request.url).searchParams.get('next') || '/';
  const url = new URL('https://github.com/login/oauth/authorize');
  url.searchParams.set('client_id', env.GITHUB_CLIENT_ID);
  url.searchParams.set('redirect_uri', new URL('/api/auth/callback', request.url).toString());
  url.searchParams.set('scope', '');
  url.searchParams.set('state', state);

  const headers = new Headers({ Location: url.toString() });
  headers.append('Set-Cookie', setCookie('wtk_state', state, { maxAge: 600 }));
  headers.append('Set-Cookie', setCookie('wtk_next', back.startsWith('/') ? back : '/', { maxAge: 600 }));
  return new Response(null, { status: 302, headers });
}
