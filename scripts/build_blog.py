#!/usr/bin/env python3
"""Render blog.weteachkubernetes.com from the article data in blog_content.py.

One HTML file per roadmap checkpoint, plus an index and a sitemap. Articles are plain
static HTML with no JavaScript at all, so the CSP can be script-src 'none'.
"""
import html, json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from blog_content import ARTICLES              # noqa: E402

SITE = 'https://blog.weteachkubernetes.com'
MAIN = 'https://weteachkubernetes.com'
AUTHOR = 'Kyle Law'
AUTHOR_GH = 'https://github.com/Kyle-Law'
REPO = 'https://github.com/Kyle-Law/weteachkubernetes'
CERTS = {'KCNA', 'CKAD', 'CKA', 'CKS', 'KCSA', 'CKNE'}

road = json.load(open(os.path.join(ROOT, 'public/data/roadmap.json')))
CP, STAGE = {}, {}
for st in road['stages']:
    for cp in st['checkpoints']:
        CP[cp['id']] = cp
        STAGE[cp['id']] = st

e = html.escape


def hl(code):
    """Comment and string highlighting only - enough to read, no tokeniser to go wrong."""
    out = []
    for line in e(code).split('\n'):
        m = re.match(r'^(\s*)(#.*)$', line)
        if m:
            out.append(f'{m.group(1)}<span class="c">{m.group(2)}</span>')
            continue
        line = re.sub(r'(\s)(#\s.*)$', r'\1<span class="c">\2</span>', line)
        out.append(line)
    return '\n'.join(out)


def blocks(bs):
    o = []
    for b in bs:
        kind = b[0]
        if kind == 'h2':
            o.append(f'<h2>{e(b[1])}</h2>')
        elif kind == 'p':
            o.append(f'<p>{b[1]}</p>')
        elif kind == 'code':
            o.append(f'<pre><code>{hl(b[1])}</code></pre>')
        elif kind == 'ul':
            items = ''.join(f'<li>{i}</li>' for i in b[1])
            o.append(f'<ul>{items}</ul>')
        elif kind == 'ol':
            items = ''.join(f'<li>{i}</li>' for i in b[1])
            o.append(f'<ol>{items}</ol>')
        elif kind == 'note':
            o.append(f'<div class="note">{b[1]}</div>')
        elif kind == 'gotcha':
            o.append(f'<div class="gotcha">{b[1]}</div>')
        else:
            raise SystemExit(f'unknown block: {kind}')
    return '\n      '.join(o)


HEAD = '''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<link rel="stylesheet" href="{css}">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="{ogtype}">
</head>
<body>

<div class="site"><div class="wrap wide">
  <a class="logo" href="/">we<i>teach</i>kubernetes <span style="color:#8795AE;font-weight:400">/ blog</span></a>
  <nav>
    <a href="/">All articles</a>
    <a href="{main}/">The roadmap</a>
    <a href="{repo}">GitHub</a>
  </nav>
</div></div>
'''

FOOT = '''
<footer><div class="wrap wide">
  Written for <a href="{main}/">weteachkubernetes.com</a> &mdash; a Kubernetes roadmap taught by the
  people who walked it. No exam content: the Linux Foundation NDA covers CKA, CKAD, CKS, KCNA, KCSA
  and CKNE, so these articles teach the subject and never the questions.
</div></footer>
</body>
</html>
'''


def article_page(a):
    cp = CP[a['node']]
    st = STAGE[a['node']]
    tags = ''.join(
        f'<span class="m {"tag" if t in CERTS else "topic"}">{e(t)}</span>' for t in cp['tags'])
    return (HEAD.format(title=f"{a['title']} — We Teach Kubernetes",
                        ogtitle=a['title'], desc=e(a['dek']),
                        canon=f"{SITE}/{a['slug']}/", css='../style.css',
                        ogtype='article', main=MAIN, repo=REPO)
            + f'''
<article><div class="wrap">
  <div class="kicker">{e(st['title'])}</div>
  <h1>{e(a['title'])}</h1>
  <p class="dek">{e(a['dek'])}</p>
  <div class="meta">
    {tags}
    <span class="m">{a['minutes']} min read</span>
    <span class="byline">by <a href="{AUTHOR_GH}">{AUTHOR}</a> · {a['added']}</span>
  </div>
  <div class="body">
      {blocks(a['body'])}
  </div>
  <div class="back">
    <b>This article covers one checkpoint on the roadmap.</b>
    <a href="{MAIN}/#{a['node']}">Open <strong>{e(cp['title'])}</strong> on the roadmap &rarr;</a>
    — it lists what this depends on and everything else written about it.
  </div>
  <p class="fix">Something wrong or out of date?
    <a href="{REPO}/issues/new?title=blog%3A%20{a['slug']}">Open an issue</a> — corrections are
    welcome and get credited.</p>
</div></article>
''' + FOOT.format(main=MAIN))


def index_page():
    total_min = sum(a['minutes'] for a in ARTICLES)
    out = [HEAD.format(title='Articles — We Teach Kubernetes',
                       ogtitle='We Teach Kubernetes — articles',
                       desc='One article for every checkpoint on the Kubernetes roadmap.',
                       canon=f'{SITE}/', css='style.css', ogtype='website',
                       main=MAIN, repo=REPO)]
    out.append(f'''
<div class="hero"><div class="wrap wide">
  <h1>One article for every <i>checkpoint</i></h1>
  <p>The roadmap says what to learn and in what order. These say how the thing actually behaves,
  including the parts that only show up once you run it.</p>
  <div class="stats">
    <div><b>{len(ARTICLES)}</b>articles</div>
    <div><b>{total_min}</b>minutes</div>
    <div><b>{len(road['stages'])}</b>stages</div>
  </div>
</div></div>

<div class="wrap wide">''')
    by_node = {a['node']: a for a in ARTICLES}
    for st in road['stages']:
        out.append(f'''
  <section class="stage">
    <h2>{e(st['title'])}</h2>
    <p class="blurb">{e(st['blurb'])}</p>''')
        for cp in st['checkpoints']:
            a = by_node.get(cp['id'])
            if not a:
                continue
            tags = ''.join(
                f'<span class="m {"tag" if t in CERTS else "topic"}">{e(t)}</span>'
                for t in cp['tags'])
            out.append(f'''
    <a class="post" href="/{a['slug']}/">
      <h3>{e(a['title'])}</h3>
      <p>{e(a['dek'])}</p>
      <div class="row">{tags}<span class="m">{a['minutes']} min</span></div>
    </a>''')
        out.append('  </section>')
    out.append('</div>')
    out.append(FOOT.format(main=MAIN))
    return '\n'.join(out)


def sitemap():
    urls = [f'{SITE}/'] + [f"{SITE}/{a['slug']}/" for a in ARTICLES]
    today = datetime.date.today().isoformat()
    body = ''.join(
        f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'{body}</urlset>\n')


def main():
    seen = set()
    for a in ARTICLES:
        if a['node'] not in CP:
            raise SystemExit(f"no such checkpoint: {a['node']}")
        if a['node'] in seen:
            raise SystemExit(f"two articles for {a['node']}")
        seen.add(a['node'])
        d = os.path.join(ROOT, 'blog', a['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w').write(article_page(a))

    open(os.path.join(ROOT, 'blog/index.html'), 'w').write(index_page())
    open(os.path.join(ROOT, 'blog/sitemap.xml'), 'w').write(sitemap())

    missing = [c for c in CP if c not in seen]
    print(f'built {len(ARTICLES)} articles + index + sitemap')
    print('checkpoints with no article:', ', '.join(missing) if missing else 'none')
    if missing:
        sys.exit(1)


if __name__ == '__main__':
    main()
