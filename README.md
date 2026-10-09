# weteachkubernetes.com

A Kubernetes learning roadmap organised by problem rather than by exam syllabus, with one
article per checkpoint — and a structure where anyone can add theirs.

- **Roadmap:** <https://weteachkubernetes.com>
- **Articles:** <https://blog.weteachkubernetes.com>

## The idea

Certifications are tags on this roadmap, not sections of it. Selecting `CKS` highlights the
checkpoints that exam happens to cover; the checkpoints stay exactly where they are for someone
who will never sit one — which is most people working on inference and GPUs, since no exam
covers that yet.

The site is a renderer. The content is two JSON files, and both take pull requests.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: find the checkpoint your tutorial
belongs to, append one object to its `resources` array in
[`public/data/roadmap.json`](public/data/roadmap.json), and add yourself to
[`public/data/contributors.json`](public/data/contributors.json) if it is your first time.

**One rule that gets a pull request closed: no exam content.** The Linux Foundation NDA covers
what appears in CKA, CKAD, CKS, KCNA, KCSA and CKNE. Teach the subject, never the questions.

## Layout

```
public/              the roadmap site, deployed to weteachkubernetes.com
  index.html         one page; the data below is inlined at build time
  cks/index.html     the published CKS curriculum mapped onto the roadmap, gaps included
  data/roadmap.json  stages, checkpoints, tags, and every resource
  data/contributors.json      contributors; handle plus anything GitHub cannot know
  data/cks-curriculum.json    the CKS mapping, and the source it came from
blog/                generated article pages, deployed to blog.weteachkubernetes.com
functions/           Cloudflare Pages Functions: sign-in, progress, contribution API
lib/                 session handling and a small GitHub App client
scripts/
  blog_content.py    the prose for every article - edit here, not in blog/
  build_blog.py      renders blog/ from blog_content.py
  validate.mjs       the data check CI runs on every pull request
  build_cks.py       renders public/cks/ from the curriculum mapping
  sync_contributors.py  pulls names and avatars from the GitHub API
  add-dns.sh         attaches the custom domains
k8s-ai-roadmap.json  an earlier, unused draft of a Kubernetes-for-AI graph, kept for reference
```

## Running it

```sh
npm install
npm run check          # validate the data files
npm run dev            # serve public/ with functions, at localhost:8788
python3 scripts/build_blog.py        # regenerate blog/ after editing article prose
python3 scripts/build_cks.py         # regenerate public/cks/ after editing the mapping
python3 scripts/sync_contributors.py # refresh profiles and avatars from GitHub
```

## Deploying

See [DEPLOY.md](DEPLOY.md). Two Cloudflare Pages projects, no build step, no server. Secrets
live as Pages secrets and never in this repo.

## Licence

Code — everything in `functions/`, `lib/`, `scripts/` and the page templates — is
[MIT](LICENSE). The article prose and roadmap text are
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): reuse it, change it, credit the
author named on the piece.

Contributors keep authorship of what they write and are credited on the checkpoint and in the
contributors list. By opening a pull request you agree to those terms for your contribution.
