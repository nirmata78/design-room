# RETROFIT — bring an older solution to the current standard, by delta

**Temporary.** Delete this file, and its line in `SKILL.md`, when every solution in the table below is marked done.
Written 2026-11-21, after SD-96 became the model. The aim is to spend tokens only on what the standard added, not to redo
work that still meets it: the outline, the booklet's prose, the estimates, the challenges and most narration stay.

## Status, 2026-11-22

Eight solutions done in one pass with **`dsl.META["automark"]`** (markers placed by sentence/overlap, so delta 5 cost no tokens), **`ch5_1.py` + `stack.json`**
(deltas 9 and 10: the 5.1 slides, the stack and drill slides and the fix-slide Rejected lines are generated from one file; `how` is
spoken, so it carries no code) and `c4svg.Diagram.OVERRIDE` (the container view redrawn with technologies). **Not done**, per delta:
6 (C4 context to the end of chapter 1), 7 (mechanism map and theory sequences), 8 (extra sequences per requirement), the component views of 9,
and hand-placed markers (the README of each solution says how many slides were automarked). Their snapshots are in `video/.v1-retrofit-2026-11-22/`;
delete them, and this file, when the author has watched the videos. SD-09 (full run needed) is still open; SD-15 and SD-25 too.

## Which path

| Solution | Sources | Path | Done |
|---|---|---|---|
| SD-08 news feed | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-24 distributed lock | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-44 payments ledger | `video/src/` (older DSL) | this file | ✓ full `/reference-solution` run 2026-11-22 (compact cut; model for the next ones) |
| SD-47 ticket booking | `video/src/` (older DSL) | this file (it has uncommitted author edits: commit or ask first) | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-77 card authorisation | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-82 credit decisioning | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-94 denylist system | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-95 loan servicing | `video/src/` (older DSL) | this file | ✓ 2026-11-22 (deltas 1–5, 9, 10, 11, 12 partly, 13; automarked) |
| SD-09 chat, SD-15 KV store, SD-25 rate limiter | no `src/` (mock-round videos) | a full `/reference-solution SD-NN` run, not a retrofit | |
| SD-96 URL shortener | current (2026-11-21 format) | the model; next edition planned below (published video kept) | ✓ |

Run solutions one at a time, in one thread; only the final video render goes to the background.

## What changed since the older format

The delta, in the order to apply it. Each line names the SD-96 file to copy the pattern from (`M = solutions/SD-96-url-shortener`).

| # | Delta | Cost | Pattern |
|---|---|---|---|
| 1 | New engine: `dsl.py` from the kit template (reveal units, `steps=False`, `tech`, `rejl`, `cards`, `trace`; keeps `timeline`, `tex`, `code`) | copy | `$KIT/templates/reference-solution/dsl.py` |
| 2 | Scientific style: `video.css` from the template, `--qid` set | copy + 1 line | `$KIT/templates/reference-solution/video.css` |
| 3 | Captions as files: `--captions sidecar --reveal-fade 0.6 --max-minutes 180`; `stack.py sync` first | edit `build-video.sh` | `M/video/build-video.sh` |
| 4 | Reveal plans: rerun `diagrams.py` (the kit now writes `<name>.steps.json`); add `order=` where left-to-right is not the request flow | small | `M/video/diagrams.py` (`C4_ORDER`, `restep`) |
| 5 | Reveal markers in the narration | **the main cost** | see below |
| 6 | C4 context closes chapter 1; the container view right after V3, walked one container per step (~45 words each) | move + split | `M/video/src/ch0_2.py`, `ch4_5.py` |
| 7 | Theory: a mechanism map (`containers()` labelled M1…Mn) and 1–2 sequences of a mechanism at protocol level | 3 slides | `M/video/diagrams.py` (`th-map`, `seq-th-*`), `ch3.py` |
| 8 | One sequence per functional requirement (most older solutions miss one or two) | 0–2 diagrams | `seq-count` in `M` |
| 9 | `stack.json` + sub-chapter 5.1: technologies on the container view, a component view per in-scope service, one `tech()` slide per container, the stack slide, the drill interlude | **new content** (~16–20 min) | `M/stack.json`, `ch4_5.py` from `subchapter("5.1"` |
| 10 | A `rejl(*REJ(n))` line on every challenge's fix slide, with one candidate sentence | 8 lines | `M/video/src/ch6_7a.py` |
| 11 | Booklet: replace the technology part of the design stage with the two `stack:` marker regions; add the component views and theory sequences as figures | edit | `M/SD-96_…md` Stage 5 |
| 12 | Outline: a revision section, the `stack:outline` region, the measured budget | edit | `M/video/OUTLINE.md` (end) |
| 13 | Publish kit: captions upload step (automatic once a `.srt` exists); README, `solutions/VIDEOS.md` | regenerate | `M/video/publish/` |

## Step by step

0. **Snapshot** as SKILL step 0.2 (`$V/.vN-<date>/`). Check `git status` for the solution first: author edits in flight
   (SD-47 today) are committed or asked about before anything is overwritten. Never run a solution's `diagrams.py` before the
   snapshot: it rewrites every SVG in place.
1. **Engine and style** (deltas 1–3). Copy `dsl.py` over the old one; diff the old one first and carry any helper the chapter
   files call that the template lacks (grep the chapter files for `def`-less calls). Port the old `gen.py`'s `META`/heading
   and the say-map into `dsl.META` as in `M/video/src/gen.py`. Copy `video.css`, set `--qid`.
2. **Diagrams** (delta 4). `python3 diagrams.py`, then list the plans: `for f in svg/*.steps.json; do echo $f; cat $f; done`.
   Fix the order of every C4 view and baseline build to client → edge → service → cache → store, then side paths.
3. **The marker report** (delta 5):
   ```bash
   REVEAL_REPORT=1 python3 $V/src/gen.py      # every slide that needs markers: file:line, units, reveals, spoken lines
   ```
   SD-08's dry run: 107 of 164 slides, because the older narration is usually **one paragraph per slide**. Work through the
   list top to bottom:
   - **A table** (units = rows): split the paragraph into one sentence per row; a `[+]` before each.
   - **A diagram** (units from `steps.json`): read the plan, split the narration at each element in that order; where the
     narration covers two elements in one sentence, use `[+2]`. A long build may end with `[+*]`.
   - **Cards, strips, lines, grading notes**: a `[+]` before the sentence that discusses each.
   - **A statement slide** (thesis, "if asked", an interviewer question): `steps=False`, no markers.
   - Words stay as they are unless a split forces a new sentence. Do not rewrite narration that already reads well.
   Rerun the report until it prints `0 of N slides`. Then `gen.py` normally.
4. **New content** (deltas 6–10). Write `stack.json` first (from the old technology slides, the booklet and the outline, plus
   the rejected alternatives the standard requires), then the 5.1 slides by copying `M/video/src/ch4_5.py` from
   `subchapter("5.1"` and replacing the narration. Copy the drill interlude's shape; pick 4–5 boxes. Add the `rejl` lines.
5. **Booklet and outline** (deltas 11–12): insert the marker regions, `python3 $V/src/stack.py sync`, then
   `./build-sd-booklet.sh <Name>`; read the Stage pages as images.
6. **Check frames only for what changed.** `build-video.sh --frames`, then tile the last step of: every 5.1 slide, every fix
   slide, every slide the marker report listed with a figure, and every slide moved in delta 6. Unchanged slides were read
   when the older version was accepted; read a 16-slide sample of them, not all.
7. **Render** in the background; QA per SKILL step 5 (streams, captions, 20 audio excerpts, 6 of them in 5.1, one sync probe).
8. **Retire** the snapshot and the old MP4/script as SKILL step 7; update the row above; report as SKILL step 7.

## Layout and fit checklist (2026-11-22) — rework an old video against the layout gate

The kit's generators changed on 2026-11-22 (larger secondary labels, C4 viewBox trimmed to content, delta views cropped to their
focus, ERD build-up plans, sized badges, highlighted code). Re-running an old solution's `diagrams.py` therefore changes its SVGs:
do it on purpose, then work this list until the gate prints **0 failures**. Never re-render a video the author has published
unless asked; fixing its sources for the next edition is fine.

1. Copy the kit's `dsl.py`, `video.css` (keep `--qid`) and `ch5_1.py`; add the gate step to `build-video.sh` (as in SD-08's).
2. `python3 diagrams.py && python3 src/gen.py`. `gen.py` now refuses code wider than 56 characters or longer than 12 lines:
   rewrite as `pseudo(…, hl=…)` unless the idiom is the lesson; split long wire formats into short lines.
3. `$PY $KIT/scripts/check_layout.py --html video-slides.html > layout-report.txt`, then by kind:
   - `overflow`: shorten cells and strips (the narration keeps the words); `bt xs` for 4–5 column tables; a technology slide's
     `how` to two or three sentences, the rest into `stack.json` `detail`; a two-line title to one; drop captions under big figures.
   - `small` (diagram): canvas wider than tall for the 16:9 figure area; box titles `size=` 24–28; legend into a free column
     (`vertical=True`, Chen `rows=`); a challenge view with `keep=` (cropped) and at most one strip under it.
   - `overlap` / `box`: move the label (`at=`), widen the box, or let the generator size the badge.
   - `code`: as step 2.
   - `redraw` (warning): turn the second drawing into a delta (`new=`, `badges=`, `keep=`), or say in the README why it stays.
   - `dense` (warning): split, or move detail to the narration.
4. `--only <slides> --shots DIR` and look at every slide you touched; then the full reveal sequence of one ERD (it builds up now).
5. Record in the solution's README: the gate result and the slides changed.

Done: **SD-08** (2026-11-22, 0 failures, 15 warnings; sources only, video not re-rendered). Open: every other solution.

## SD-96 next edition (planned 2026-11-22; the published video stays as it is)

The author's review of the published video. Apply in the next `/reference-solution SD-96` run, outline first.

**Content (GUIDELINES §3.1–3.3, §5):**
- Scale line in chapter 1: 100 M new links a month, 10 B redirects a month, a viral-link peak of 40,000 clicks a second; re-derive
  every estimate from it.
- 5.2 alternate path: a PostgreSQL sequence (`nextval`, cached per connection) instead of the etcd range allocator. Gives up: one
  writer for every create (the sequence's primary), and a failover gap (cached values lost, so gaps; an async replica promoted
  late can reissue values unless the sequence is advanced past the old maximum). Crossover: when creates need more than one
  region's primary, or the allocator's availability must exceed one primary's. Marked ALTERNATE.
- Challenges, each one level down, versions carried V3 → V4 → … as the fixes need:
  1. *Fencing*: what a fencing token (the range lease's revision) covers — a paused or partitioned holder whose stale write is
     rejected by the store — and what it does not: a valid holder's slow write, or a store that does not check the token.
  2. *etcd against our own Raft*: etcd is used only as a small linearizable key with compare-and-set (`Txn` on `mod_revision`),
     about 0.4 writes a second; our own Raft is building and operating a consensus system for one counter.
  3. *The lease*: a range is `[next, next + 1000)` of the key `/alloc/{region}/next`; handing one out is one `Txn` whose `Put` is
     appended to the Raft log and committed by a majority; a crashed holder's range is never returned (a gap, not a collision).
  4. *Random against allocated*: random 7-character codes with `INSERT … ON CONFLICT` and a retry are simpler (no allocator) and
     fine while the space is sparse (0.34 % collision probability at year ten); ranges win when one write per create, no retry
     tail and per-region slices matter.
  5. *`GET /{code}` for expired or deleted links*: 410 Gone (permanent), cached briefly at the edge; crawlers treat 410 as
     removal and drop the URL faster than after a 404.
  6. *Vacuum* on the small hot table [?: confirm which table the review meant, "128-row"]: what vacuum reclaims (dead row
     versions after UPDATE/DELETE), and when it hurts (a few rows updated constantly, a long transaction holding back the
     horizon, bloat and latency).
  7. *Analytics: Flink against ClickHouse*: Flink keeps windowed, de-duplicated state (event IDs, late data, bot filter) and emits
     per-minute counts; ClickHouse stores and serves them columnar. The boundary: ClickHouse materialized views alone suffice when
     no de-duplication or late-data window is needed.
  8. *The encoder as its own component*: input a 42-bit ID from the range and the secret key; output 7 base-62 characters;
     invariants: a bijection below 62⁷ (cycle-walking), deterministic, unpredictable without the key.

**Picture (GUIDELINES §7.5–7.7)** — the layout gate on the current sources, with the 2026-11-22 kit (scratch copy, 49 failures,
19 warnings; it was 89 with the old generators): overflow on slides 4, 34, 45, 46, 68, 69, 74, 76, 78, 109, 127; overlap 42, 48;
small diagram labels 17, 37, 47, 53, 54, 61, 65, 66, 67, 86, 146, 155; code 89 (Go, 69 columns), 99 (Python → pseudocode).
Redraws: `c4-containers` (54) and `c4-containers-tech` (65) after `th-map` (37), and `base-final` (167): draw the container view
once as the carried baseline, show the mechanism map and the technologies as badges or type lines on it, and the recap as
highlighted paths. The ERD (47) builds up entity by entity once its slide has markers. Challenge visuals become component views.

## Known traps (from SD-96)

- `table(..., "bt xs")` for anything with four columns or `code`; the `.cite` line and the last table row overflow first.
- C4 component views: no edge labels where boxes are close; the labels overlap.
- Words the voice gets wrong: add respellings to `dsl.META["say"]` (etcd, PostgreSQL, ClickHouse, Kubernetes, Feistel …).
- The booklet font lacks `≈`: write "about".
- `[+N]` counts include both strips on a fix slide, and the `rejl` line is the last unit.
- A design fact said in a drill or a rejected line must exist in the design (SD-96 had to state where an alias's home region is
  before its drill could ask about it).
