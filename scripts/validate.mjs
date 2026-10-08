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
    if (!handles.has(r.by)) fail.push(`${cp.id}: "${r.title}" credits @${r.by}, who is not in contributors.json`);
    if (!/^https:\/\//.test(r.url)) fail.push(`${cp.id}: "${r.title}" has a non-https url`);
    if (!['article', 'video', 'lab', 'repo'].includes(r.type)) fail.push(`${cp.id}: bad type "${r.type}"`);
    if (!Number.isInteger(r.minutes) || r.minutes < 1) fail.push(`${cp.id}: "${r.title}" has bad minutes`);
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
console.log(`ok: ${checkpoints.length} checkpoints, ${res.length} tutorials, ${people.people.length} contributors`);
