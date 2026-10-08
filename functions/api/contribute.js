import { getSession, json } from '../../lib/session.js';
import { installationToken, gh, decodeB64, encodeB64 } from '../../lib/github.js';

const FILE = 'public/data/roadmap.json';
const PEOPLE = 'public/data/contributors.json';
const KINDS = new Set(['article', 'video', 'lab', 'repo']);
const OPEN_PR_LIMIT = 5;

const clean = (s, max) => String(s ?? '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, max);

export async function onRequestPost({ request, env }) {
  const s = await getSession(request, env);
  if (!s) return json({ error: 'sign in first' }, 401);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }

  const checkpoint = clean(body.checkpoint, 64);
  const r = body.resource || {};
  const type = KINDS.has(r.type) ? r.type : null;
  const title = clean(r.title, 90);
  const url = clean(r.url, 300);
  const minutes = Number(r.minutes);

  if (!type) return json({ error: 'type must be article, video, lab or repo' }, 400);
  if (title.length < 6) return json({ error: 'title too short' }, 400);
  if (!/^https:\/\/[^\s]+\.[^\s]+$/.test(url)) return json({ error: 'url must be https' }, 400);
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 600) {
    return json({ error: 'minutes must be 1-600' }, 400);
  }

  /* A link nobody can open is not a tutorial. Some hosts dislike HEAD, so fall back to GET. */
  const reachable = await probe(url);
  if (!reachable) return json({ error: 'that link did not respond' }, 422);

  /* Rate limit per account, not per IP: an account is the cost of entry here. */
  const rlKey = `prs:${s.ghid}`;
  const open = Number((await env.SESSIONS.get(rlKey)) || 0);
  if (open >= OPEN_PR_LIMIT) {
    return json({ error: `you already have ${open} submissions waiting for review` }, 429);
  }

  const token = await installationToken(env);
  const api = gh(token);
  const repo = `/repos/${env.REPO_OWNER}/${env.REPO_NAME}`;
  const branch = `tutorial/${checkpoint}-${s.handle}-${Date.now().toString(36)}`;

  try {
    const base = await api.get(`${repo}/git/ref/heads/${env.REPO_BRANCH || 'main'}`);
    await api.post(`${repo}/git/refs`, { ref: `refs/heads/${branch}`, sha: base.object.sha });

    /* The trailer is what puts this on the contributor's own GitHub profile. The noreply
       address is derived from their numeric id, so we never ask for or store an email. */
    const author = { name: s.name, email: `${s.ghid}+${s.handle}@users.noreply.github.com` };
    const trailer = `\n\nCo-authored-by: ${author.name} <${author.email}>`;

    const road = await api.get(`${repo}/contents/${encodeURIComponent(FILE)}?ref=${branch}`);
    const data = JSON.parse(decodeB64(road.content));
    const cp = data.stages.flatMap((st) => st.checkpoints).find((c) => c.id === checkpoint);
    if (!cp) return json({ error: 'no such checkpoint' }, 404);
    if (cp.resources.some((x) => x.url === url)) {
      return json({ error: 'that link is already on this checkpoint' }, 409);
    }
    cp.resources.push({
      type, title, url, by: s.handle, minutes,
      added: new Date().toISOString().slice(0, 10),
    });

    await api.put(`${repo}/contents/${encodeURIComponent(FILE)}`, {
      message: `tutorial: ${checkpoint}${trailer}`,
      content: encodeB64(`${JSON.stringify(data, null, 2)}\n`),
      sha: road.sha, branch, author, committer: author,
    });

    if (body.contributor) {
      const pf = await api.get(`${repo}/contents/${encodeURIComponent(PEOPLE)}?ref=${branch}`);
      const people = JSON.parse(decodeB64(pf.content));
      if (!people.people.some((p) => p.handle === s.handle)) {
        people.people.push({
          handle: s.handle,
          name: clean(body.contributor.name, 60) || s.name,
          title: clean(body.contributor.title, 60) || 'Contributor',
          location: clean(body.contributor.location, 60) || null,
          tz: clean(body.contributor.tz, 12) || null,
          photo: null,
          github: `https://github.com/${s.handle}`,
          linkedin: /^https:\/\/(www\.)?linkedin\.com\//.test(body.contributor.linkedin || '')
            ? body.contributor.linkedin : null,
          certs: [], teaches: [],
          joined: new Date().toISOString().slice(0, 10),
        });
        people.people.sort((a, b) => a.handle.localeCompare(b.handle));
        await api.put(`${repo}/contents/${encodeURIComponent(PEOPLE)}`, {
          message: `contributor: ${s.handle}${trailer}`,
          content: encodeB64(`${JSON.stringify(people, null, 2)}\n`),
          sha: pf.sha, branch, author, committer: author,
        });
      }
    }

    const pr = await api.post(`${repo}/pulls`, {
      title: `tutorial: ${checkpoint}`,
      head: branch,
      base: env.REPO_BRANCH || 'main',
      maintainer_can_modify: true,
      body: [
        `Submitted through the site form by @${s.handle}.`,
        '',
        `- **Checkpoint:** \`${checkpoint}\``,
        `- **Kind:** ${type} · ${minutes} min`,
        `- **Link:** ${url}`,
        '',
        'The submitter confirmed this links to free public material and contains no exam content.',
      ].join('\n'),
    });

    await env.SESSIONS.put(rlKey, String(open + 1), { expirationTtl: 14 * 86400 });
    return json({ ok: true, number: pr.number, url: pr.html_url });
  } catch (err) {
    /* Never leak a token or an internal path to the browser. */
    console.error('contribute failed', err?.message);
    return json({ error: 'could not open the pull request' }, 502);
  }
}

async function probe(url) {
  for (const method of ['HEAD', 'GET']) {
    try {
      const r = await fetch(url, { method, redirect: 'follow' });
      if (r.ok) return true;
    } catch { /* try the next method */ }
  }
  return false;
}
