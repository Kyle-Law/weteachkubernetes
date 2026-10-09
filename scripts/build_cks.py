#!/usr/bin/env python3
"""Render /cks/ - the published CKS curriculum mapped onto this roadmap.

Static HTML with no JavaScript, so the page works under script-src 'none' and is fully
indexable. Re-run after editing public/data/cks-curriculum.json.
"""
import html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUR = json.loads((ROOT / 'public/data/cks-curriculum.json').read_text())
ROAD = json.loads((ROOT / 'public/data/roadmap.json').read_text())
OUT = ROOT / 'public/cks/index.html'

CP, STAGE = {}, {}
for st in ROAD['stages']:
    for cp in st['checkpoints']:
        CP[cp['id']] = cp
        STAGE[cp['id']] = st

e = html.escape
WEIGHT = {'covered': 1.0, 'partial': 0.5, 'gap': 0.0}
LABEL = {'covered': 'written up', 'partial': 'partly covered', 'gap': 'not written yet'}


def article_for(cp_id):
    """The piece we wrote ourselves, if there is one."""
    for r in CP[cp_id]['resources']:
        if r.get('by'):
            return r
    return None


def score(domain):
    cs = domain['competencies']
    return sum(WEIGHT[c['status']] for c in cs) / len(cs)


total = sum(score(d) * d['weight'] for d in CUR['domains'])
comps = [c for d in CUR['domains'] for c in d['competencies']]
counts = {s: sum(1 for c in comps if c['status'] == s) for s in WEIGHT}

gaps = sorted(
    ((d, c) for d in CUR['domains'] for c in d['competencies'] if c['status'] == 'gap'),
    key=lambda dc: -dc[0]['weight'])


def links_for(comp):
    out = []
    for cid in comp.get('covers', []):
        cp, art = CP[cid], article_for(cid)
        bits = [f'<a class="cp" href="https://weteachkubernetes.com/#{cid}">{e(cp["title"])}</a>']
        if art:
            bits.append(f'<a class="art" href="{e(art["url"])}" target="_blank" '
                        f'rel="noopener">read it &rarr;</a>')
        out.append('<span class="lk">' + ' '.join(bits) + '</span>')
    return ''.join(out)


rows = []
for d in CUR['domains']:
    pct = round(100 * score(d))
    items = []
    for c in d['competencies']:
        extra = ''
        if c.get('covers'):
            extra += f'<div class="where">{links_for(c)}</div>'
        if c.get('missing'):
            extra += (f'<div class="miss"><b>Missing:</b> {e(c["missing"])}</div>')
        if c['status'] == 'gap':
            extra += ('<div class="where"><a class="write" '
                      'href="https://github.com/Kyle-Law/weteachkubernetes/issues/new'
                      f'?title={e("needs a write-up: " + c["text"][:60])}">'
                      'claim this one &rarr;</a></div>')
        items.append(f'''
      <li class="c {c['status']}">
        <span class="chip">{LABEL[c['status']]}</span>
        <div class="body"><p class="t">{e(c['text'])}</p>{extra}</div>
      </li>''')
    rows.append(f'''
  <section class="dom">
    <div class="dh">
      <h2>{e(d['title'])}</h2>
      <span class="wt">{d['weight']}% of the exam</span>
      <span class="sc">{pct}% written here</span>
    </div>
    <div class="bar"><i style="width:{pct}%"></i></div>
    <ul class="comps">{''.join(items)}</ul>
  </section>''')

gap_rows = ''.join(
    f'<tr><td class="w">{d["weight"]}%</td><td>{e(d["title"])}</td>'
    f'<td>{e(c["text"])}</td></tr>' for d, c in gaps)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(f'''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CKS curriculum, mapped — We Teach Kubernetes</title>
<meta name="description" content="Every competency in the published CKS curriculum, mapped to a
  checkpoint on this roadmap - including the {counts['gap']} that nothing covers yet.">
<link rel="canonical" href="https://weteachkubernetes.com/cks/">
<meta property="og:title" content="CKS curriculum, mapped to a roadmap">
<meta property="og:description" content="26 competencies, 6 domains, and an honest list of what is
  not written up yet.">
<meta property="og:url" content="https://weteachkubernetes.com/cks/">
<style>
:root{{
  color-scheme:light;
  --brand:#326CE5; --brand-d:#2457C5; --brand-l:#E8EFFD;
  --teal:#0F8F86; --teal-l:#E0F5F2;
  --warm:#C2761A; --warm-l:#FBF1E2;
  --rose:#B3456B; --rose-l:#FBEBF0;
  --ok:#17795E; --ok-l:#E4F4EC; --ok-b:#8FCBB4;
  --ink:#10203A; --muted:#566480; --faint:#8795AE;
  --bg:#FFFFFF; --bg-2:#F5F8FD; --line:#DCE5F2;
  --hero:#0E1E38; --hero-muted:#A8B8D4; --hero-accent:#7AA7F5;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}}
*{{box-sizing:border-box}}
html,body{{margin:0}}
body{{font-family:var(--sans); color:var(--ink); background:var(--bg-2); line-height:1.6}}
.wrap{{max-width:900px; margin:0 auto; padding:0 24px}}
h1,h2,h3{{line-height:1.22; margin:0 0 .4em; letter-spacing:-.015em}}
a{{color:var(--brand)}}

.site{{background:var(--bg); border-bottom:1px solid var(--line)}}
.site .wrap{{display:flex; align-items:center; gap:16px; padding-block:13px}}
.logo{{font-weight:700; font-size:15px; text-decoration:none; color:var(--ink)}}
.logo i{{color:var(--brand); font-style:normal}}
.site nav{{display:flex; gap:16px; font-size:13.5px; margin-left:auto}}
.site nav a{{color:var(--muted); text-decoration:none}}
.site nav a:hover{{color:var(--brand)}}

header.h{{background:var(--hero); color:#fff; padding:46px 0 40px}}
header.h .kick{{font-family:var(--mono); font-size:11px; letter-spacing:.09em; text-transform:uppercase;
  color:var(--hero-accent); margin-bottom:12px}}
header.h h1{{font-size:clamp(1.7rem,4.4vw,2.5rem)}}
header.h h1 i{{color:var(--hero-accent); font-style:normal}}
header.h p{{color:var(--hero-muted); max-width:66ch; margin:13px 0 0}}
.stats{{display:flex; flex-wrap:wrap; margin-top:26px}}
.stats div{{padding:0 20px; border-left:1px solid rgba(255,255,255,.16); color:#9FAABD;
  font-size:11.5px; letter-spacing:.05em; text-transform:uppercase}}
.stats div:first-child{{border-left:0; padding-left:0}}
.stats b{{display:block; font-family:var(--mono); font-size:23px; color:#fff; text-transform:none}}

.src{{background:var(--brand-l); border-left:3px solid var(--brand); padding:14px 17px;
  border-radius:0 9px 9px 0; font-size:14px; color:var(--brand-d); margin:22px 0}}
.src b{{color:var(--ink)}}
.src a{{color:var(--brand-d)}}
.caveat{{border-left:3px solid var(--warm); background:var(--warm-l); padding:13px 16px;
  border-radius:0 9px 9px 0; font-size:14px; color:#5E4413; margin:0 0 22px}}
.caveat b{{color:#3F2D08}}

.dom{{background:var(--bg); border:1px solid var(--line); border-radius:13px; margin:0 0 18px;
  overflow:hidden}}
.dh{{display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; padding:16px 20px 12px}}
.dh h2{{font-size:1.08rem; margin:0}}
.dh .wt{{font-family:var(--mono); font-size:11.5px; color:var(--faint)}}
.dh .sc{{font-family:var(--mono); font-size:11.5px; color:var(--brand-d); margin-left:auto;
  background:var(--brand-l); border-radius:99px; padding:2px 9px}}
.bar{{height:4px; background:var(--line)}}
.bar i{{display:block; height:100%; background:var(--brand)}}
ul.comps{{list-style:none; margin:0; padding:0}}
li.c{{display:flex; gap:12px; padding:14px 20px; border-top:1px solid var(--line)}}
li.c .chip{{font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.05em;
  padding:3px 8px; border-radius:99px; height:fit-content; white-space:nowrap; flex:none;
  min-width:112px; text-align:center}}
li.covered .chip{{background:var(--ok-l); color:var(--ok)}}
li.partial .chip{{background:var(--warm-l); color:var(--warm)}}
li.gap .chip{{background:var(--rose-l); color:var(--rose)}}
li.c .body{{flex:1; min-width:0}}
li.c p.t{{margin:0; font-size:14.5px}}
li.gap p.t{{font-weight:600}}
.where{{margin-top:8px; display:flex; gap:10px; flex-wrap:wrap}}
.lk{{display:inline-flex; gap:8px; align-items:center; font-size:13px}}
a.cp{{text-decoration:none; background:var(--bg-2); border:1px solid var(--line); border-radius:7px;
  padding:3px 9px}}
a.cp:hover{{border-color:var(--brand); background:var(--brand-l)}}
a.art{{font-family:var(--mono); font-size:11.5px; text-decoration:none}}
a.art:hover{{text-decoration:underline}}
a.write{{font-family:var(--mono); font-size:11.5px; color:var(--rose); text-decoration:none;
  border:1px dashed var(--rose); border-radius:7px; padding:3px 9px}}
a.write:hover{{background:var(--rose-l)}}
.miss{{margin-top:7px; font-size:13px; color:var(--muted)}}
.miss b{{color:var(--ink); font-weight:600}}

.next{{background:var(--bg); border:1px solid var(--line); border-radius:13px; padding:20px;
  margin:26px 0}}
.next h2{{font-size:1.08rem}}
.next p{{font-size:14px; color:var(--muted); margin:0 0 14px}}
table{{width:100%; border-collapse:collapse; font-size:13.5px}}
th,td{{text-align:left; padding:9px 10px; border-bottom:1px solid var(--line)}}
th{{font-family:var(--mono); font-size:10.5px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--faint)}}
td.w{{font-family:var(--mono); color:var(--rose); white-space:nowrap; width:1%}}
tr:last-child td{{border-bottom:0}}
footer{{border-top:1px solid var(--line); background:var(--bg); padding:26px 0 48px;
  color:var(--faint); font-size:12.5px}}
@media(max-width:620px){{
  li.c{{flex-direction:column; gap:8px}} li.c .chip{{min-width:0}}
  .dh .sc{{margin-left:0}} .stats div{{padding:0 14px}}
}}
</style>
</head>
<body>

<div class="site"><div class="wrap">
  <a class="logo" href="/">we<i>teach</i>kubernetes</a>
  <nav>
    <a href="/">Roadmap</a>
    <a href="/cks/">CKS</a>
    <a href="https://blog.weteachkubernetes.com/">Articles</a>
    <a href="https://github.com/Kyle-Law/weteachkubernetes">GitHub</a>
  </nav>
</div></div>

<header class="h"><div class="wrap">
  <div class="kick">Certified Kubernetes Security Specialist</div>
  <h1>The CKS curriculum, <i>mapped</i></h1>
  <p>Every competency the Linux Foundation publishes for the CKS, against what this roadmap
  actually covers — including the {counts['gap']} that nothing covers yet. The gaps are the
  useful part: they are the writing backlog.</p>
  <div class="stats">
    <div><b>{len(comps)}</b>competencies</div>
    <div><b>{counts['covered']}</b>written up</div>
    <div><b>{counts['partial']}</b>partial</div>
    <div><b>{counts['gap']}</b>gaps</div>
    <div><b>{total:.0f}%</b>weighted coverage</div>
  </div>
</div></header>

<div class="wrap">

  <div class="src"><b>Where this comes from.</b> The domains, weights and competency wording are the
  Linux Foundation's published curriculum, mirrored in the
  <a href="{CUR['_source']['url']}" target="_blank" rel="noopener">CNCF curriculum repository</a> and
  on the <a href="{CUR['_source']['also']}" target="_blank" rel="noopener">certification page</a>.
  That is the public syllabus, not exam content — the NDA covers what appears in the exam, and
  nothing here restates a task or a question. Check the official source for the current version
  before relying on this; curricula change.</div>

  <div class="caveat"><b>The percentage is a rough weighting, not a readiness score.</b> A fully
  written competency counts 1, a partial counts 0.5, and the judgement of which is which is my
  reading of the wording rather than an official mapping. It tells you what is missing from this
  roadmap. It does not tell you whether you would pass.</div>

{''.join(rows)}

  <div class="next">
    <h2>What to write next</h2>
    <p>The {counts['gap']} outright gaps, ordered by how much of the exam their domain is worth.
    Each one is also the most useful pull request available right now.</p>
    <table>
      <tr><th>Domain weight</th><th>Domain</th><th>Nothing covers this yet</th></tr>
      {gap_rows}
    </table>
  </div>

</div>

<footer><div class="wrap">
  Generated from <code>public/data/cks-curriculum.json</code> by <code>scripts/build_cks.py</code>.
  Corrections to the mapping are welcome —
  <a href="https://github.com/Kyle-Law/weteachkubernetes/issues/new?title=cks%20mapping">open an
  issue</a>.
</div></footer>

</body>
</html>
''')
print(f'wrote {OUT.relative_to(ROOT)}')
print(f'  {len(comps)} competencies · {counts["covered"]} covered · {counts["partial"]} partial · '
      f'{counts["gap"]} gaps · {total:.1f}% weighted')
