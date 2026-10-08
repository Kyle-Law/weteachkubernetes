/* The check CI runs on every pull request. Nothing fancy: the four things that have
   actually gone wrong before. */
import { readFileSync } from 'node:fs';

const road = JSON.parse(readFileSync('public/data/roadmap.json', 'utf8'));
const people = JSON.parse(readFileSync('public/data/contributors.json', 'utf8'));
const handles = new Set(people.people.map((p) => p.handle));
const tags = new Set(road.tags.map((t) => t.id));
const checkpoints = road.stages.flatMap((s) => s.checkpoints);
const fail = [];

const ids = checkpoints.map((c) => c.id);
ids.filter((x, i) => ids.indexOf(x) !== i).forEach((x) => fail.push(`duplicate checkpoint id: ${x}`));

for (const cp of checkpoints) {
  for (const t of cp.tags) if (!tags.has(t)) fail.push(`${cp.id}: tag "${t}" is not in the registry`);
  for (const r of cp.resources) {
    const where = `${cp.id}: "${r.title}"`;

    // A resource is either written by a contributor who opted in, or a curated link to
    // somebody else's material. Claiming both would imply a membership nobody agreed to.
    if (r.by && r.source) fail.push(`${where} has both "by" and "source" - pick one`);
    if (!r.by && !r.source) fail.push(`${where} needs either "by" or "source"`);

    if (r.by && !handles.has(r.by)) {
      fail.push(`${where} credits @${r.by}, who is not in contributors.json`);
    }
    if (r.source) {
      if (!r.source.name) fail.push(`${where} has a source with no name`);
      if (!/^https:\/\//.test(r.source.url || '')) fail.push(`${where} source url must be https`);
      if (r.minutes !== undefined) {
        fail.push(`${where} is a curated link; leave out "minutes" rather than estimating `
          + `someone else's reading time`);
      }
    } else if (!Number.isInteger(r.minutes) || r.minutes < 1) {
      fail.push(`${where} has bad minutes`);
    }

    if (!/^https:\/\//.test(r.url)) fail.push(`${where} has a non-https url`);
    if (!['article', 'video', 'lab', 'repo'].includes(r.type)) fail.push(`${cp.id}: bad type "${r.type}"`);
  }
}
for (const p of people.people) {
  if (!/^[A-Za-z0-9-]{1,39}$/.test(p.handle)) fail.push(`bad handle: ${p.handle}`);
  if (p.linkedin && !/^https:\/\/(www\.)?linkedin\.com\//.test(p.linkedin)) {
    fail.push(`${p.handle}: linkedin must be a linkedin.com url or null`);
  }
}

const res = checkpoints.flatMap((c) => c.resources);
if (fail.length) {
  console.error(`\n${fail.length} problem(s):`);
  fail.forEach((f) => console.error(`  - ${f}`));
  process.exit(1);
}
const own = res.filter((r) => r.by).length;
const curated = res.length - own;
console.log(`ok: ${checkpoints.length} checkpoints, ${own} contributed + ${curated} curated `
  + `= ${res.length} resources, ${people.people.length} contributors`);
