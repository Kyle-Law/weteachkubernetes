# Contributing

Two files take contributions. Everything else is machinery.

## Adding a tutorial

1. Open the roadmap and find the checkpoint it belongs to. Its id is shown in the detail panel
   and in the page URL — `https://weteachkubernetes.com/#network-policy`.
2. In [`public/data/roadmap.json`](public/data/roadmap.json), append one object to that
   checkpoint's `resources` array. Append; do not re-sort, so two pull requests on the same day
   do not conflict.

   ```json
   {
     "type": "video",
     "title": "Debugging a dropped packet with Hubble",
     "url": "https://youtu.be/...",
     "by": "your-github-handle",
     "minutes": 18,
     "added": "2026-10-09"
   }
   ```

   `type` is one of `article`, `video`, `lab`, `repo`. `minutes` is honest reading or watching
   time, not aspirational.

3. If this is your first contribution, add yourself to
   [`public/data/contributors.json`](public/data/contributors.json). `handle` must be your
   GitHub username — it is the join key between the two files. `photo` and `linkedin` can both
   stay `null`; a portrait is generated from your handle.

4. Open the pull request, titled `tutorial: <checkpoint-id>`. One checkpoint per pull request
   keeps review quick.

CI will reject an unknown `by` handle, a tag that is not in the registry, a non-https URL, a
bad `type`, or a duplicate checkpoint id. Run it yourself first:

```sh
npm run check
```

## Adding or changing a checkpoint

Structural changes reshape everyone's path, so they are reviewed more slowly. Open an issue
first describing what is missing and where it belongs. Adding a tutorial to an existing
checkpoint is far more likely to be merged than proposing a new checkpoint.

## Fixing an article

Article prose lives in [`scripts/blog_content.py`](scripts/blog_content.py), not in the
generated HTML under `blog/`. Edit it there, then:

```sh
python3 scripts/build_blog.py
```

Corrections are genuinely welcome and get credited. If you would rather just report the problem,
open an issue — that is useful too.

## The one rule

**No exam content.** The Linux Foundation NDA covers what appears in CKA, CKAD, CKS, KCNA, KCSA
and CKNE. Describing a topic is fine and is the whole point. Restating exam tasks, questions or
scenarios is not, and the pull request will be closed.

## Tone

Two things make a tutorial here worth linking:

- **It says what actually goes wrong.** The default that bites, the error message that misleads,
  the thing that looks like a GPU problem and is 64 MB of `/dev/shm`.
- **It is honest about cost.** What a mesh takes from you, what a limit throttles, what an idle
  accelerator bills.

Nobody needs another restatement of the official documentation. Link that instead and write the
part it leaves out.
