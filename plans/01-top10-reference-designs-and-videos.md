# Plan 01 · Deep video rounds for the eleven most likely tasks

**Brief (private, read-only):** `private/01_Google_L6_SD_Top10_Tasks_and_Variants.md` — ten task
families plus a bonus, each with a spine answer, three variants, "expect" questions, the numbers that
steer the design, and study sources.
**Depth model (private, read-only):** `~/Profile/materials/system-design/Distributed_Lock_System_Design.md`
— a 16,000-word single-problem dossier. Each task reaches that depth **on video and in slide PDFs**,
not in a written booklet.
**Shared rules:** [`00-shared-rules-and-sources.md`](00-shared-rules-and-sources.md). Read it first.
**Theory course:** [`02-concepts-and-building-blocks-course.md`](02-concepts-and-building-blocks-course.md).
Shared theory is taught there once; these videos point at it (§4).
**Status file:** `plans/STATUS-01.md` (create it in the first session from the table in §2).
**Division of work:** the author writes every design sheet and every transcript; runners do the
mechanical subtasks of §5.3, about 30 minutes each.

## 1 · What gets built, and what changed in this revision

**No written reference design.** The 18–24k-word booklet of the first plan is gone, and step 1b of
the `system-design-video` skill ("reference design, always") is **overridden for this work**. Its
content moves into a longer video scenario and a richer slide deck: each task becomes a **series of
up to three episodes**, about three times the length of a single mock round, with every mechanism
explained in detail. The `STANDARD.md` limit of 45 minutes still holds **per episode**.

For each task, in `solutions/SD-NN-<slug>/`:

| Deliverable | File | Size | Standard |
|---|---|---|---|
| Design sheet | `design-sheet.md` | 800–1,200 words, tables and lists | §3.1. A working spine, not a document to read |
| Claims ledger | `claims.md` | one row per number | shared rules §5 |
| Diagram specifications | `video/diagrams/epN.md` → `video/diagrams.py` → `video/svg/` | 35–50 figures across the series | `theory/video/diagrams/README.md` |
| Episode 1 · The round | `video/src/ch01/*.txt` (segments, §5.1) → MP4 | 70–80 slides, 4,700–5,800 words, 35–43 min | `system-design-video` skill, `STANDARD.md` §1a and §1b |
| Episode 2 · Under the hood | `video/src/ch02/*.txt` → MP4 | 65–80 slides, 4,700–5,800 words, 35–43 min | §3.3 |
| Episode 3 · Under pressure | `video/src/ch03/*.txt` → MP4 | 55–75 slides, 4,000–5,800 words, 30–43 min | §3.4 |
| Slide PDFs | `<name>-Episode-0N-slides.pdf` in the series' output folder | one per episode | Written by `course.py frames` |
| Appendix deck (PDF only) | `video/src/ch09/*.txt` → PDF | 15–25 slides | §3.5. Not narrated |
| Study handout | `<name>-handout.pdf` in the output folder | every slide with its narration beneath, then the appendix | §3.6. Generated, never hand-written |
| Series settings | `video/series.json` | name, footer, unit, title, output folder | read by `theory/video/course.py --root` |
| Publish kit | `video/publish/` | for episode 1 only; the LinkedIn document is the episode-1 slide PDF | skill step 9. **Never upload** |
| Index rows | `solutions/VIDEOS.md`, `video/README.md` | one row per episode | skill steps 8–9 |

**Bar.** Staff L6/L7 depth as the skill defines it. The manager layer stays badged AUX. One of the
five follow-ups in episode 1 is the manager curveball; episode 3 carries the cost-to-build section,
also AUX.

**Total length.** Ten tasks at up to three episodes is up to about **20 hours** of video, plus one
supplement episode for ticket booking. That is by design: a task's series is watched around running
the same question in the simulator (episode 1 before or after a cold attempt, episodes 2 and 3 to
close the gaps the attempt showed). Episode 3 is built only **if needed** (§3.4 has the rule), so
the real total will be lower. The first wave (cache, rate limiter, denylist, aggregation) is up to
about eight hours.

## 2 · Tasks, order and starting state

Build plan 02's course first if both plans are being done: these videos cite its parts. Then do the
tasks in this order: shared ideas first, heavier machinery later.

| # | Task | Bank ID · folder | Starts from | Cue sheet |
|---|---|---|---|---|
| 1 | Distributed cache | SD-20 · `solutions/SD-20-distributed-cache/` | nothing | `questions/C-storage-data-consistency.md` `### SD-20` |
| 2 | Rate limiter and quota enforcement | SD-25 · `solutions/SD-25-rate-limiter/` | short solution `solutions/SD-25-rate-limiter.md`; a video at the older EM bar in `video/` | `questions/D-infrastructure-control-planes.md` `### SD-25` |
| 3 | Blocking / denylist distribution | **SD-95 (new)** · `solutions/SD-95-denylist-distribution/` | nothing; needs a bank row and a compact cue sheet (§7) | to be written in `questions/D-…` |
| 4 | Real-time aggregation: trending, top-K, counters, leaderboard | SD-02 · `solutions/SD-02-trending-top-k/` | nothing | `questions/A-streaming-analytics.md` `### SD-02` (read SD-01 and SD-03 too) |
| 5 | Fleet monitoring: metrics, logs, alerting | SD-04 · `solutions/SD-04-metrics-monitoring/` | nothing | `questions/A-…` `### SD-04` (read SD-05 for the logs variant) |
| 6 | Job scheduler / orchestrator | SD-28 · `solutions/SD-28-job-scheduler/` | nothing | `questions/D-…` `### SD-28` |
| 7 | Distributed lock, election and consensus service | SD-24 · `solutions/SD-24-distributed-lock/` | the private dossier, as technical input for the scripts | `questions/D-…` `### SD-24` |
| 8 | Key-value store / metadata database | SD-15 · `solutions/SD-15-distributed-kv-store/` | short solution `solutions/SD-15-distributed-kv-store.md`; an older-bar video in `video/` | `questions/C-…` `### SD-15` |
| 9 | Distributed file / blob storage | SD-16 · `solutions/SD-16-object-store/` | nothing | `questions/C-…` `### SD-16` (read SD-17 for the metadata variant) |
| 10 | Live data migration and cross-region replication | **SD-96 (new)** · `solutions/SD-96-live-data-migration/` | nothing; needs a bank row and a compact cue sheet (§7) | to be written in `questions/C-…`; read `### SD-22` |
| 11 | Ticket booking / reservation | SD-47 · `solutions/SD-47-ticket-booking/` | a **complete** written design and video. One supplement episode only (§6.11) | `questions/F-transactions-payments.md` `### SD-47` |

Before using an ID, confirm it is free: `grep -c 'SD-95\|SD-96' Question-Bank.md` must print `0`. If
not, take the next two free numbers and note it in the status file.

Where an older video exists (SD-25, SD-15), move its sources into `video/.v1-em/` before starting, as
`STANDARD.md` §5 says. Do not delete them. The short `solutions/SD-NN-*.md` files are inputs and are
not changed.

## 3 · The series: what each piece contains

### 3.1 · The design sheet (the spine, not a booklet)

Three episodes drift apart unless one file fixes the design. That file is
`design-sheet.md`: 800–1,200 words, tables and lists only, no prose explanation. It is the single
source of names and numbers for all slides and scripts.

- The prompt in one sentence; functional and non-functional requirements with numbers; the cuts.
- The thesis and the central contrast (from §6).
- Estimates: each as inputs → arithmetic → result → the decision it forces.
- API: the calls with their request and response fields. Data model: entities, keys, the partition key.
- Components: one line each, what it owns.
- Decisions: chosen · rejected · the condition that flips it. One row per major decision.
- Invariants and guarantees: one line each, with the mechanism that upholds it.
- The three variants: which is in the round, which is the mid-round requirement, and for each the
  delta (what changes, what does not, what it costs, which seam absorbs it).
- The episode outlines: per episode the chapter list with a slide count, and for each chapter the
  course references it uses (§4).
- **Brief checklist**: every "pin down first" item, every "number that steers the design", every
  spine step, every variant bullet and every "Expect" question of the brief's section, each mapped
  to an episode and chapter. Nothing in the brief may be left unmapped.

If a later session has to change the sheet, it changes the sheet first, then the slides, and lists
the change in the status file. Episodes already built that carry the old value are rebuilt or the
difference is listed for the author.

### 3.2 · Episode 1 · The round

The mock round exactly as the `system-design-video` skill defines it. Task-specific choices:

| Part of the round | Content |
|---|---|
| Requirements | The brief's "pin down first" as Q&A; the interviewer's answers come from the cue sheet |
| Thesis (`V`, dark slide) | The task's thesis from §6, said once after scoping and again at the close |
| Vocabulary slide and central-contrast picture | The task's own terms; the contrast named in §6 |
| Estimates | The brief's numbers, as calculations with their consequence |
| Deep dive | The variant marked **in round** in §6: C4 container → the pattern → sequence → code |
| Mid-round requirement | The variant marked **mid-round** in §6, answered as a delta |
| Five follow-ups | Listed in §6: at least three technical; one manager curveball, badged AUX. `[pause: 2.0]` after each question |
| Debrief | What a weak answer missed, in the coach's voice, and what episodes 2 and 3 open up |

Episode 1 must stand alone: someone who watches only this one has seen a complete Staff-level round.

### 3.3 · Episode 2 · Under the hood

Coach-led (`N`), with the candidate's voice (`C`, `V`) for what to say in a round and the
interviewer (`I`) for probes. No round framing; this is the explanation the round had no time for.

| Chapter | Content | Share |
|---|---|---|
| What is really being graded | Four to six signals an interviewer listens for on this problem, and the one question that exposes a weak design | 5% |
| The theory this problem owns | The "taught here" items of §6, each from the failure it prevents to the mechanism, with a worked example in numbers and a figure. Shared theory is **recalled, not taught** (§4) | 20% |
| Options, compared honestly | Every serious way to build the core mechanism, five to eight options, one or two slides each: how it works, what it guarantees, **the named failure where it breaks**, cost, verdict. Include "do not build it" and "reuse the platform". End on one comparison matrix | 20% |
| The two other variants as full deep dives | For each: the requirement that selects it → the risk → the mechanism → a sequence diagram → the failure case → code or arithmetic where that is the mechanism → the line to say (`V`) → what a weak answer says | 40% |
| Internals | Wire formats, storage layouts, the state machines, the code listings the round only pointed at | 10% |
| The bug a first draft has | The findings of the race hunt (shared rules §5.4), each as a two-slide before and after | 5% |

### 3.4 · Episode 3 · Under pressure

| Chapter | Content | Share |
|---|---|---|
| The follow-up bank | Every "Expect" question of the brief not already answered in episodes 1 and 2, 10–14 of them, reworded. Each: the question (`I`, big quote), `[pause: 2.0]`, a reference answer of 120–200 spoken words on a diagram or table that starts with the claim and ends with what it costs, then the `V` line | 50% |
| Two incidents, minute by minute | Two failures from the task's hunt list walked on a timeline: what the dashboards show, what the system does unaided, what the on-call does, what is lost, what changes afterwards | 20% |
| Shipping it | Rollout stages with gates and rollback; the migration from whatever exists today; the SLOs and the alerts that defend them | 10% |
| What it costs to build (AUX) | V1 proves the risky part, V2 hardens, V3 scales, with scope cuts; team shape along the seams; build, reuse or do not; the risk register with how each risk is retired early; what to cut at half the team. Every figure in people or months is labelled an assumption | 10% |
| Rapid recall | Twenty flashcards: the question on screen, `[pause: 1.5]`, the one-line answer. Then a practice plan that names the simulator commands (`mock me SD-NN`, `practice SD-NN`, `grill`) | 10% |

**"If needed" rule.** After the design sheet is written, count the material for episodes 2 and 3
from the brief checklist. If the two together would be under about 6,500 spoken words, build one
combined episode 2 (keep every chapter, shorten the flashcards to ten) and record the decision in
the status file. Do not pad an episode to reach three, and do not cut a mechanism to stay at two.

### 3.5 · The appendix deck (PDF only)

Slides that are for reading, not for narration. They may be denser than video slides (up to about
60 words or a table of ten rows), but still one idea each: the glossary · the full options matrix
on one or two slides · the estimates as one table · the API and schema as reference · the decision
log (chosen, rejected, flip condition) · the invariants and what upholds each · the flashcards, two
per slide · **the course map for this task**: every course reference used, as concept → part →
section (§4) · the reading list ordered by value for this problem, by chapter.

### 3.6 · The study handout

One PDF per task that replaces the booklet for reading and printing: each slide's frame, the
narration for that slide beneath it with speaker labels, two slides to a page, episode by episode
with a contents page; then the appendix deck.

It is generated by `solutions/_tools/handout.py`, written once in subtask T-S1 (§5.3) and reused by
every task: it reads each episode's compiled script and frames, writes markdown with one image and
its text per slide, and builds the PDF with `pandoc` and `xelatex`. Captions come from the script, so the handout and the video cannot differ.
PDFs are build outputs: gitignored, kept beside the MP4s in the local output folder (no Google Drive copy).

### 3.7 · Rules for every episode

- `STANDARD.md` §1a and §1b bind, per episode: one idea per slide, every term defined on first use,
  every diagram walked element by element with 40–70 spoken words, arithmetic shown, wire formats,
  technology against alternatives, readable `pre.code`. **Explain in a lot of detail**: when in
  doubt between a slide that asserts and three slides that show, show.
- **Mechanism first, product second.** The reported bar is building the component from first
  principles. Name a product only after the mechanism, and give Google's name beside the open-source
  one where the second private report's building-block table has both.
- **Each major decision is a design-doc entry on a slide**: chosen, rejected, the condition that
  flips it. Goals, non-goals, alternatives considered, rollout and monitoring all appear somewhere
  in the series; that is the Google practice the viewer is expected to show.
- Episodes 2 and 3 open with a thirty-second recap of the design (one C4 slide from episode 1) and
  say which episode a viewer should have seen. They never re-run the round.
- No slide and no explanation appears twice in a series. A later episode that needs an earlier
  picture shows it for one slide with "from episode 1" in the kicker.
- Count words before building each episode; the hard limit is 45 minutes each.

## 4 · Cross-references to the theory course

Plan 02's course teaches each shared concept once. These videos **do not teach it again.**

1. **Two lists per task** (§6): *From the course* (recalled) and *Taught here* (owned by this task).
   If a concept is on the first list, the series may not spend more than one slide on explaining it.
2. **The recall slide.** A shared concept is brought in with one slide: kicker `From the course ·
   Part N · <section title>`, the concept's line to say as the title, the course's own diagram for
   it (reuse the SVG from `theory/video/svg/` when it exists), and at most 45 spoken words that end
   with what this problem does with it. Then go straight to the problem-specific use. At most eight
   recall slides an episode.
3. **Where the reference comes from.** Read `theory/video/INDEX.md` (concept → part → section →
   timestamp). If the course is not built yet, take the part number from plan 02 §2.2 and the
   concept's name as the section title, and list the references in the status file so they can be
   checked once `INDEX.md` exists.
4. **Same words, same numbers.** Use the course's term and its line to say. If this task needs a
   different number for the same thing (a different lease length, say), state that it differs and why.
5. **Concepts the course dropped** (plan 02 §2.1) have no home there. If this task needs one, it is
   on the task's *Taught here* list and is taught in full, in episode 2.
6. **The course map** for the task goes into the appendix deck (§3.5) and into the description
   field of the publish kit as "watch first".
7. The debrief of episode 1 names the two or three course parts that matter most for this problem.

## 5 · Who does what, and the subtasks

### 5.1 · Roles

| Role | Does | Never does |
|---|---|---|
| **Author** (the strongest model, with the author present) | Writes, per task: `design-sheet.md`, the new cue sheet where §7 needs one, every episode's complete transcript as segment files, every diagram specification, the appendix deck's source, `publish/meta.json`, and the brief checklist | Renders video |
| **Runner** (Sonnet or similar, one subtask per session, about 30 minutes) | Draws diagrams from specifications, re-runs arithmetic, renders frames, fixes layout overflow, synthesises voice, builds and checks video, builds the PDFs, files the index rows | Writes or rewrites design or teaching content, changes a number, a name or a decision |

Episodes are written in the **same single-source format as the theory course** and built with the
same tool (`theory/video/course.py --root solutions/SD-NN-<slug>/video`). Hand-written slide HTML
and a separate script file, as the skill describes them, are not used: the tool generates both.
Plan 02 §4.1 (what a runner may change in a transcript) applies here word for word.

**Small pieces first, merged upward.** An episode is a folder of segment files, one per chapter of
the episode, each three to eight minutes of video. The tool joins them in name order. Segments
merge into an episode, episodes into the task's series, the series into the study handout:

```
solutions/SD-20-distributed-cache/
├── design-sheet.md                      author
├── claims.md                            runner (T-K)
└── video/
    ├── series.json                      author: name, footer, unit "Episode", title, out folder, teacher "COACH"
    ├── src/ch01/01-requirements.txt     author: episode 1, segment 1
    ├── src/ch01/02-estimates.txt        …
    ├── src/ch02/…                       episode 2
    ├── src/ch03/…                       episode 3
    ├── src/ch09/…                       the appendix deck (slides only, no speech; never built to video)
    ├── diagrams/ep1.md … ep3.md         author: figure specifications
    ├── diagrams.py → svg/               runner (T-D)
    └── publish/meta.json                author
```

**Transcript status** (the author updates it; a runner subtask may start only when its inputs say
"written"). Nothing is written yet for plan 01: the course transcripts come first, because these
episodes cite them.

| Task | Design sheet | Ep 1 segments | Ep 2 segments | Ep 3 segments | Diagram specs | Appendix | `meta.json` |
|---|---|---|---|---|---|---|---|
| SD-20 … SD-96, SD-47 supplement | pending (author) | pending | pending | pending | pending | pending | pending |

### 5.2 · The author's agenda per task (for the record; a runner skips this)

1. Read the brief's section, the cue sheet, the sources of §6, the private input if one is named,
   and `theory/video/INDEX.md`.
2. For a new bank entry, do §7.
3. Write `design-sheet.md` (§3.1) with the brief checklist and the episode outlines; apply the "if
   needed" rule of §3.4.
4. Run the race hunt (shared rules §5.4) over the sheet's guarantees and the hunt list of §6.
5. Write episode 1 segment by segment in round order: `01-frame-and-requirements`, `02-thesis-and-
   estimates`, `03-api-and-data`, `04-architecture`, `05-deep-dive`, `06-mid-round-requirement`,
   `07-operations`, `08-manager-layer-and-close`, `09-follow-ups`, `10-debrief`. Compile after each
   segment; keep the running word count inside 4,700–5,800.
6. Write episode 2 (`01-what-is-graded`, `02-theory-taught-here`, `03-options`, `04-variant-…`,
   `05-variant-…`, `06-internals`, `07-first-draft-bugs`) and episode 3 (`01-follow-up-bank-a`,
   `02-follow-up-bank-b`, `03-incident-…`, `04-incident-…`, `05-shipping-it`, `06-cost-to-build`,
   `07-rapid-recall`) the same way.
7. Write the diagram specifications as the transcripts call for figures, in the format of
   `theory/video/diagrams/README.md`.
8. Write the appendix deck source (§3.5) and `publish/meta.json`.
9. Tick the brief checklist; set the status row to "written".

### 5.3 · Runner subtasks

One session each, about 30 minutes. Start by reading the shared rules §1–§3 and §6, plan 02 §4.1,
and the card. End by updating `plans/STATUS-01.md` (ID, state, counts, changes made, items for the
author) and committing. Per task the order is `T-D* → T-K → (T-En-F → T-En-V) for each episode →
T-A → T-H → T-X`; `T-D*` and `T-K` can run in parallel sessions; tasks are independent of each other.
In the IDs, `SD-NN` is the task and `n` the episode.

**Kick-off prompt** (change the ID):

```
Read plans/00-shared-rules-and-sources.md §1–§3 and §6, plans/02-concepts-and-building-blocks-course.md §4.1,
then the card for subtask SD-20/T-E1-F in plans/01-top10-reference-designs-and-videos.md §5.3. Do exactly that
subtask. You are a runner: do not write or rewrite content. CLAUDE.md's interviewer rules do not apply.
Stop when the card's "done when" list is true, update plans/STATUS-01.md, commit, and report.
```

**T-S1 · The handout tool** (once for all tasks; 30 min)
- *Needs:* plan 02's C-S1 and C-S2 done (the builder is proven).
- *Do:* write `solutions/_tools/handout.py` (stdlib only) and a test. Input: a series root. For
  each episode it reads the compiled script (`[slide: v-NN]` cues, speaker lines) and the frames
  folder from `~/.cache/sd-course/build/<name>/chNN/`, and writes markdown: a contents page, then
  per slide the frame image and the lines spoken over it with speaker labels, two slides to a page;
  then the appendix deck's frames, one to a page. It builds the PDF with `pandoc` and `xelatex`
  into the series' output folder as `<name>-handout.pdf`.
- *Done when:* the test passes on a three-slide sample; a real run on the course's part 1
  (`--root theory/video`, unit "Part") produces a readable PDF that was looked at.

**T-D1, T-D2, … · Diagrams from the specification** (30 min each, at most five figures a session)
- *Needs:* `video/diagrams/epN.md`; `theory/video/diagrams/README.md`.
- *Do:* as plan 02's C-NN-D card, writing `video/diagrams.py` → `video/svg/`. A figure that a
  specification marks "reuse from the course" is copied from `theory/video/svg/`, not redrawn.
- *Done when:* compiling the episode no longer lists those figures as "not drawn yet"; every
  figure was looked at and matches its specification label by label.

**T-K · Check the arithmetic** (30 min; a series with three episodes may need two sessions)
- *Needs:* the design sheet and the transcripts.
- *Do:* as plan 02's C-NN-K card, writing `claims.md` in the task folder. In addition: check that
  every number and every component name in the three episodes equals the design sheet's.
- *Done when:* every derived number is recomputed and in the ledger; every mismatch with the
  design sheet or between episodes is listed for the author; no transcript was changed.

**T-En-F · Frames and layout for episode n** (30 min)
- *Needs:* the episode's figures drawn.
- *Do:* 1) `theory/video/course.py --root solutions/SD-NN-<slug>/video compile n`: fix lint per
  plan 02 §4.1. Word count must be within the range in §1; if not, report to the author and stop.
  2) `… frames n`: fix overflow per §4.1 rule 2 until zero. 3) Tile all frames eight to a sheet
  and look at every sheet. 4) Count recall slides (kicker starts "From the course"): at most eight;
  each names a part and section that exists in `theory/video/INDEX.md`. A mismatch goes to the author.
- *Done when:* zero lint, zero overflow, every sheet looked at, the recall check done, every
  change listed.

**T-En-V · Voice, video and checks for episode n** (30 min; the build runs in the background)
- *Needs:* T-En-F; plan 02's C-S3.
- *Do:* 1) `… video n` in the background. 2) When it finishes: `ffprobe` (1920×1080, audio,
  chapters equal to the episode's `##` sections, no subtitle stream); duration under 45 minutes.
  3) `check_audio.py` against the compiled script; add respellings to `theory/video/say.py` for
  flagged words and rebuild. 4) Sync probe at about 90% of the duration. 5) Look at six frames.
  6) Add the episode's row to `solutions/VIDEOS.md` and `video/README.md` (length, chapters, the
  rebuild command).
- *Leaves:* `<name>-Episode-0n-….mp4` and `<name>-Episode-0n-slides.pdf` in the series' output folder.
- *Done when:* all checks pass or failures are listed; the real duration is in the status file.

**T-A · Appendix deck** (30 min)
- *Needs:* `src/ch09/`.
- *Do:* `… frames 9`; fix overflow per §4.1 rule 2 (the appendix may use `sm` tables freely); tile
  and look at every sheet. Do **not** run `video 9`.
- *Done when:* `<name>-Episode-09-slides.pdf` exists and every page was looked at.

**T-H · Handout and series merge** (30 min)
- *Needs:* all T-En-V, T-A, T-S1.
- *Do:* 1) `solutions/_tools/handout.py solutions/SD-NN-<slug>/video`; tile the handout's pages and
  look at them. 2) Optional single file for offline viewing: `… merge` joins the episodes with
  combined chapters (`<name>-Full.mp4`).
- *Done when:* the handout PDF exists, was looked at, and its slide count equals the sum of the
  episodes' slides plus the appendix.

**T-X · Publish kit, delivery, close-out** (30 min)
- *Needs:* T-H; `publish/meta.json`.
- *Do:* 1) `~/.claude/skills/slide-video-kit/scripts/publish_kit.py video/publish/meta.json` for
  episode 1, with the episode-1 slide PDF as the LinkedIn document; look at the thumbnail.
  **Upload nothing.** 2) Leave MP4s, slide PDFs and the handout in the local output folder and list their
  paths; do not copy them to Google Drive (author's decision, 2026-11-13). 3) Run the privacy grep of §8 on the diff.
  4) `git status`: no frame, audio, PDF or MP4 is tracked. 5) Go through §8 and tick it in the
  status file.
- *Done when:* §8 is true for the task, or each open item is listed for the author.

## 6 · Task briefs

Each brief adds direction to the private report's section; it does not replace it. "From the
course" items get a recall slide only (§4); the number is the course part. "Taught here" is this
task's own theory and gets full treatment in episode 2. "Hunt" lists the races and false claims a
first draft usually misses. Check every source detail before using it.

### 6.1 · SD-20 Distributed cache

- **Thesis.** A cache is a bet that the backend survives without it. The design is about what happens
  to the backend when the cache changes shape: a node lost, a resize, a cold start, a hot key expiring.
- **Central contrast.** Memory sizes the cluster; the miss ratio sizes the backend.
- **In round:** cluster behaviour (rebalancing and failover). **Mid-round:** consistency with the
  source of truth.
- **Follow-ups (episode 1).** Make `get()` scale across 64 cores · one key at 500k requests a second ·
  the tier restarts cold at peak · a write in one region and a read in another 50 ms later · AUX:
  running it as a platform with per-tenant quotas.
- **From the course.** Consistent hashing with virtual nodes, hot keys, request routing (6) · caching
  patterns, eviction, expiry, invalidation, stampede control, the stale-set race and its lease,
  hit-ratio maths, cold start (9) · reading your own writes, change data capture (5) · static
  stability (13).
- **Taught here.** What doubling the cluster does in numbers and how to stage it · warm-up by
  reading through the previous owner · a spare pool that absorbs a dead node's load · client-side
  sharding against a slot map with redirects against a proxy tier · invalidation across regions and
  its ordering · the node's memory layout: hash table, eviction list, size classes (the course
  dropped this) · load-based auto-sharding (dropped there too).
- **Options matrix.** No cache (read replicas, a bigger database) · in-process cache · client-side
  sharding over independent nodes · fixed slots with a slot map and redirects · a routing proxy tier ·
  load-based auto-sharding · a replicated cache. Verdict per workload.
- **Figures.** The ring before and after adding a node; the miss-storm arithmetic (1 M reads/s at 99%
  hits is 10k/s to the database; losing one node of 20 adds about 5% misses); the stale-set race as a
  sequence with two clients; single-flight on a hot key; warm-up through the previous owner; the
  node's memory layout; who writes each key.
- **Hunt.** A node returns after ten minutes with entries that were invalidated meanwhile · two clients
  with different shard maps, so a delete reaches one owner and a read the other · a cache filled from a
  lagging replica just after an invalidation · TTLs that expire together · "replicate everything"
  doubling the RAM bill for a contract that already allows loss.
- **Sources.** "Scaling Memcache at Facebook" (leases, gutter pools, regional invalidation,
  cold-cluster warm-up). DDIA ch. 6 (rebalancing, request routing), ch. 5, ch. 11. TinyLFU and the
  Caffeine design notes. Slicer.

### 6.2 · SD-25 Rate limiter and quota enforcement

- **Thesis.** A shared counter on the hot path cannot be accurate, fast and available at once. For a
  rate limit, decide locally and reconcile, with a stated bound on over-admission. For a quota that is
  money, reserve, then commit or release.
- **Central contrast.** A rate (refills with time) versus a quota (a budget that is consumed).
- **In round:** latency first, with capacity leased to local buckets. **Mid-round:** a hard billing
  quota.
- **Follow-ups (episode 1).** Two gateways race for the last token · the allocator is unreachable · a
  limit is lowered: when does it bite · 100 parallel uploads with 1 GB left · AUX: shadow mode before
  a new limit rejects anything.
- **From the course.** Token bucket, window counters, distributed enforcement, load shedding,
  client-side throttling, fairness, fail-open versus fail-closed (12) · lost updates and conditional
  writes, the reservation pattern, escrow, idempotency keys (8) · physical clocks, leases (2) · the
  429 contract (11).
- **Taught here.** The allocator's lease protocol: grant, renew, shrink, expire · the over-admission
  bound for this design as a formula and a number · how a changed limit reaches the fleet and when
  it bites · the quota's reserve → commit / release state machine with expiry and a late commit ·
  escrow rebalancing between shards · the one-timestamp bucket (GCRA; the course dropped it) as an
  option.
- **Options matrix.** In-process only · a central store with an atomic script · a central store with
  local batching · leased capacity from an allocator · gossip-synchronised local buckets · client-side
  adaptive throttling · a strongly consistent counter per account · escrow split across shards.
- **Figures.** Lease grant and renewal sequence; the worst-case over-admission arithmetic; the
  limit-change timeline; the reservation state machine; escrow rebalancing; the 429 response on the
  wire with `Retry-After`.
- **Hunt.** Check-then-decrement that is not atomic · time taken from callers instead of the store ·
  leases still outstanding when a limit is lowered · a commit that arrives after its reservation
  expired · a retry that double-charges because the idempotency key is not stored with the effect · a
  refill computed with a clock that stepped backwards · the limiter failing closed and taking the
  product down with it.
- **Sources.** SRE book ch. 21 and ch. 22; workbook ch. 11. Doorman. O'Neil, "The Escrow
  Transactional Method". DDIA ch. 7, ch. 8. Private input:
  `~/Profile/materials/system-design/SysDesign_Q06_Rate_Limiter.md`.
- **Existing material.** `solutions/SD-25-rate-limiter.md` and the older video: keep their numbers
  unless wrong; list every correction.

### 6.3 · SD-95 Blocking / denylist distribution (new bank entry)

- **Thesis.** The check is a memory lookup. The system is the pipeline that gets a correct, versioned
  list into every process's memory, proves it arrived, and can take it back.
- **Central contrast.** Data plane (a microsecond check, never a network call) versus control plane
  (slow, versioned, staged, allowed to be down).
- **In round:** propagation within N seconds. **Mid-round:** the source becomes a slow, rate-limited
  external lookup API.
- **Follow-ups (episode 1).** A bad push blocks a continent: stop it · a node was offline for two
  hours · a new ban covers a /16 while per-address verdicts are cached · the filter says "maybe" ·
  AUX: the policy owner is not the mechanism owner; the propagation SLO is the contract.
- **From the course.** Configuration distribution (4) · snapshot plus log catch-up (5) · static
  stability (13) · fail-open versus fail-closed (12) · Bloom filters (7) · tries and longest-prefix
  match (11) · control plane versus data plane (15) · progressive rollout, kill switches (16) ·
  negative caching (9).
- **Taught here.** The version chain with checksums and what a node does on a gap · the apply loop ·
  the relay fan-out tree and its propagation-time arithmetic · the memory arithmetic for the list ·
  **measuring** propagation rather than claiming it (the fleet's version histogram) · a never-block
  range validated at ingest and on the node · the slow external source: a local replica, a verdict
  cache with range-aware invalidation, and a request budget.
- **Options matrix.** A remote lookup per request · a shared cache lookup per request · periodic full
  snapshots pulled · snapshot plus streamed deltas · a filter in front of a sharded lookup service ·
  enforcement at L4, at the L7 gateway, in the application.
- **Figures.** Control and data plane as C4; the version chain; the relay tree; the node's apply loop
  as code (verify version n+1, apply, checksum the result, atomic pointer swap, persist); the memory
  arithmetic (10 M IPv4 addresses as a sorted array is 40 MB; a filter at 1% is about 12 MB; work
  out 100 M IPv6 prefixes and show it); a radix trie; the staleness timeline against the SLO; the
  version histogram; canary → region → all with a kill switch.
- **Hunt.** An add and a remove for one key arriving out of order · a delta applied to the wrong base ·
  a node booting with no list at all · a never-block range that a bad rule covers · a filter false
  positive blocking a legitimate user · cached per-address verdicts outliving a range ban · "all
  nodes run version N" claimed without a measurement.
- **Sources.** Safe Browsing Update API documentation. "Holistic Configuration Management at
  Facebook". Envoy xDS. SRE workbook ch. 14 and ch. 16; SRE book ch. 8. DDIA ch. 5, ch. 11. Private
  input: `~/Profile/materials/system-design/SysDesign_Q04_Feature_Flags.md` for the config-push parts.

### 6.4 · SD-02 Real-time aggregation: trending, top-K, counters, leaderboard

- **Thesis.** First decide which numbers are money and which are heuristics. An exact count is a
  replayable log, a dedup and an idempotent write. An approximate one is a sketch with an error bound
  you can state.
- **Central contrast.** Event time versus processing time.
- **In round:** exact counts with exactly-once effect. **Mid-round:** approximate top-K over a sliding
  24 hours.
- **Follow-ups (episode 1).** The rank of one player among 10⁸ in 10 ms · one video is 10% of all
  events · mobile clients upload two hours late · a bot farm pushes a hashtag · AUX: agreeing with
  product what "correct" means, because it moves the cost by an order of magnitude.
- **From the course.** Queue versus log, delivery semantics, ordering, event time and watermarks,
  stateful processing with checkpoints, batch plus stream, HyperLogLog, Count-Min Sketch, quantile
  sketches (10) · idempotency and exactly-once as an effect (2) · hot keys (6) · skip lists (7) ·
  idempotency keys and dedup tables (8).
- **Taught here.** The exact-count path end to end in both correct constructions · two-stage
  aggregation with salted keys · a ring of per-minute sketches for a sliding window, with the memory
  arithmetic · why merging per-partition top-K lists is wrong and what makes it right · publishing a
  window and correcting it later · the leaderboard: exact head, bucketed tail, rank by counting ·
  the batch recomputation path (the course dropped batch processing).
- **Options matrix.** A database counter per event · batch only · stream only with replay · batch plus
  stream · sketches in the stream processor · a pre-aggregating OLAP store · a sorted set in memory.
- **Figures.** The pipeline as C4; a late event against a closed window; the crash between sink write
  and checkpoint as a sequence, twice; salting; the sketch arithmetic (width e/ε, depth ln(1/δ), about
  1.9 M counters and 15 MB a window at the brief's parameters, error at most 600 in 60 M events); the
  ring of sketches; the leaderboard's bucketed tail.
- **Hunt.** Increments re-applied on replay · dedup state that expires before the lateness horizon ·
  a global top-K computed by merging per-partition top-K lists · a sketch over-count putting a false
  heavy hitter in the heap · a window closed and published, then a correction · a weekly reset "at
  midnight" across time zones.
- **Sources.** DDIA ch. 11, ch. 10. "The Dataflow Model". MillWheel. SRE book ch. 25. Count-Min
  Sketch (2005). "HyperLogLog in Practice".

### 6.5 · SD-04 Fleet monitoring: metrics, logs, alerting

- **Thesis.** Cardinality is the cost, and the monitor must work when what it watches does not. So
  series are budgeted, recent data lives in memory in each zone, and nothing on the alerting path
  depends on the systems being monitored.
- **Central contrast.** 1,000 hosts fit on one machine; say so, then ask what grows.
- **In round:** the metrics store and its query path. **Mid-round:** detection time cut from two
  minutes to fifteen seconds.
- **Follow-ups (episode 1).** Someone adds a user ID as a label · p99 across 10,000 hosts · the
  monitoring region is cut off, and who monitors the monitor · a service starts logging 100 times
  more · AUX: every team is a tenant, so cardinality budgets and self-service.
- **From the course.** Metric model and cardinality, percentiles and sketches, push versus pull,
  roll-ups, alerting, logging pipelines, SLOs, golden signals, time-series compression, columnar
  storage, the inverted index (14) · the write-ahead log and LSM engines (7) · static stability,
  dependency hygiene (13) · failure detection (2) · tenant isolation (16).
- **Taught here.** The zonal in-memory store with a global query layer · head block, log and
  immutable blocks for this workload · query fan-out with aggregation pushed down · the
  detection-time budget for this design, term by term · the alert pipeline: evaluate, group,
  deduplicate, route · the dead-man's switch and the out-of-band path · per-tenant series budgets
  and what happens at the limit · the logs variant: three index choices priced · trace sampling
  (the course dropped tracing) in one slide if a follow-up needs it.
- **Options matrix.** One node · pull scrapers with local storage per zone · a push pipeline through a
  durable log · in-memory zonal stores with a global query layer · a columnar store for everything ·
  for logs: a full-text index, a label index over compressed chunks, a columnar store.
- **Figures.** Agent to store as C4 (collection and query as two views); the arithmetic (10⁸ samples a
  second, 138 TB a day raw at 16 bytes, about 12 TB at 1.4 bytes); the write path's blocks; query
  fan-out; the detection-time timeline; group → deduplicate → route; a multi-window burn-rate alert
  applied to this system; the dead-man's switch.
- **Hunt.** Missing data read as zero · a dead host versus a partitioned observer · replicas that
  disagree at query time · out-of-order samples · roll-ups that averaged a percentile · an alert
  evaluator that needs the service it alerts on · a rack failure paging forty times.
- **Sources.** Monarch. Gorilla. SRE book ch. 6; workbook ch. 4 and ch. 5. DDIA ch. 1, ch. 3. Private
  input: `~/Profile/materials/system-design/Observability_Platform_System_Design.md`.

### 6.6 · SD-28 Job scheduler / orchestrator

- **Thesis.** Exactly-once execution does not exist. Choose per job between skipping a run and doubling
  it, record the intent through consensus before acting, and name each launch by its scheduled time so
  that a new leader can see it and a repeat is harmless.
- **Central contrast.** A job definition versus a job run; firing on time versus placing on capacity.
- **In round:** time-based scheduling (cron and delayed jobs). **Mid-round:** opaque long-running GPU
  jobs that need placement.
- **Follow-ups (episode 1).** The scheduler dies after starting a job and before recording it · a
  million jobs at 00:00:00 · a 64-GPU job never fits although 200 are free · one worker is ten times
  slower than the rest · AUX: a scheduler bug launches everything twice; blast radius and the kill
  switch.
- **From the course.** Leases and fencing (2) · leader election (4) · desired state and
  reconciliation, placement, priority and preemption, node liveness, timers at scale, task leasing,
  durable workflows, timing wheels (15) · `SKIP LOCKED` as a queue, idempotency keys (8) · delayed
  delivery (10) · thundering herds (13).
- **Taught here.** The launch log: launch-started and launch-finished around the side effect, and
  the takeover · shard ownership of time buckets by lease · spreading the midnight herd · the run
  state machine with overlapping runs and misfires · time zones and daylight saving · all-or-nothing
  placement for multi-GPU jobs, fragmentation and how to defragment (the course dropped gang
  scheduling) · fair sharing between tenants (dropped there) · scheduler architectures in one slide.
- **Options matrix.** Cron on one host · a database table polled with `SKIP LOCKED` · a delayed queue ·
  leader per time-bucket shard with a consensus-tracked launch log · a durable workflow engine with
  event histories · a cluster manager with declarative state.
- **Figures.** The run state machine; the due-time bucket index and the wheel; shard ownership by
  lease; the launch log and the takeover sequence; attempt-ID fencing for workers; the arithmetic
  (10⁸ jobs a day is about 1,200 a second on average, with hundredfold bursts on the hour; 10⁶ tests
  of 30 s in 600 s need 50,000 cores); filter and score; gang placement and fragmentation.
- **Hunt.** A paused worker finishing after its lease expired · two shards owning one bucket · a clock
  ahead firing early · a run still going when the next is due · daylight-saving and time zones ·
  retries synchronising into a herd · a partition evicting a whole zone at once.
- **Sources.** SRE book ch. 24. Borg. Omega. "Borg, Omega, and Kubernetes". DDIA ch. 8, ch. 9. Private
  input: `~/Profile/materials/system-design/SysDesign_Q07_Workflow_Orchestrator.md`.

### 6.7 · SD-24 Distributed lock, election and consensus service

- **Input.** The private dossier already has the depth. Use its technical content to write the design
  sheet and the three scripts; redraw its figures with `c4svg` and `seqsvg` (its TikZ does not build
  here); drop its front matter, preface framing and companion-lab references; check every claim into
  `claims.md`. Read `SysDesign_Q01_Distributed_Lock.md` in the same folder for extra follow-ups.
  Nothing is copied into the repo as a document.
- **Thesis.** A lock alone protects nothing. A lease is safe only within its clock assumptions, and
  only a fencing token checked by the resource makes a paused ex-holder harmless.
- **Central contrast.** A lock for efficiency versus a lock for correctness.
- **In round:** correctness first (sessions, leases, fencing through a leader change). **Mid-round:**
  100,000 acquisitions a second.
- **Follow-ups (episode 1).** The holder pauses for 30 seconds · a partitioned leader still thinks it
  leads · five replicas in three regions: the write latency · why not write your own Paxos · AUX:
  publishing limits so the service is not used as a database.
- **From the course.** Leases and fencing, physical clocks, linearizability, failure detection (2) ·
  state-machine replication, Raft, linearizable reads, quorum placement, single-decree Paxos (3) ·
  the Chubby model, etcd primitives, election as a pattern, efficiency versus correctness locks,
  membership (4).
- **Taught here.** This service's own API and session protocol, message by message · failover with
  the old leader's longest lease waited out, on a timeline with numbers · what the client library
  must do (the shortened local lease, the "in doubt" state, re-acquire) · scaling to 100,000
  acquisitions a second: many consensus groups, batching, client-held leases, and what each costs ·
  waiting without a herd · the resource side: how three kinds of resource check a token, and what
  to say when one cannot · the limits the service publishes.
- **Options matrix.** A database row lock · a single cache node with a TTL key · a multi-node cache
  lock · a consensus-backed lease service · leases inside the resource's own store · no lock:
  idempotent or conditional writes instead.
- **Hunt.** A token checked by the lock service but not by the resource · a new leader granting before
  the old leader's longest lease has run out · a client trusting the full lease length instead of a
  shortened one · a session "in doubt" treated as held.
- **Sources.** Chubby. Raft. "Paxos Made Live". SRE book ch. 23. Kleppmann, "How to do distributed
  locking". DDIA ch. 8 and ch. 9.

### 6.8 · SD-15 Key-value store / metadata database

- **Thesis.** Consistency is chosen per operation, and every level has a price in latency or
  availability. The promise you make must match the mechanism you drew.
- **Central contrast.** Leaderless quorums versus one consensus group per range.
- **In round:** consistency first (ordered ranges, a consensus group each, leader leases, splits).
  **Mid-round:** an always-writable multi-region mode.
- **Follow-ups (episode 1).** Is R + W > N linearizable · the transaction coordinator dies after
  prepare · p99 read latency spikes during compaction · a deleted item comes back · AUX: "use the
  existing platform" said first, then what was asked is built.
- **From the course.** The consistency ladder, quorums, hybrid clocks, leases (2) · Raft, multi-Raft,
  linearizable reads, quorum placement (3) · replication modes, leaderless replication, read repair,
  Merkle trees, conflict resolution, tombstones (5) · range partitioning, splits, routing, secondary
  indexes, cross-shard operations (6) · the write-ahead log, LSM engines, MVCC, Bloom filters (7) ·
  two-phase commit, also over consensus groups, snapshot reads (8).
- **Taught here.** The three layers assembled into one read and one write, hop by hop with a latency
  budget · a range split by snapshot and log catch-up, with a transaction in flight · a two-range
  transaction end to end, including the coordinator's death · commit wait in this design, with the
  uncertainty bound as a number · the always-writable mode as a delta: what the API can no longer
  promise · the node-count and index arithmetic · a timestamp service (the course dropped it) as an
  option against bounded-uncertainty clocks.
- **Options matrix.** Single leader with asynchronous followers · leaderless quorums with repair ·
  consensus per range with hybrid logical clocks · consensus per range with bounded-uncertainty clocks ·
  B-tree versus LSM engines under each.
- **Figures.** The arithmetic (100 TB over 2 TB nodes with three replicas is 150 nodes; 400,000 ranges
  of 256 MB, about 8,000 replicas a node; the index of 1 PB of 1 KB records re-derived); one read and
  one write through the layers; a range split; a two-range transaction; commit wait on a timeline;
  the ring with a sloppy quorum and hinted handoff; a version-vector conflict; quorum placement
  across three regions with the commit latency.
- **Hunt.** A stale leader serving a read · last-writer-wins dropping a write under clock skew ·
  tombstones collected before a long-dead replica returns · a split in the middle of a transaction ·
  a global uniqueness check done in two groups · monotonic keys creating a hot range.
- **Sources.** DDIA ch. 3, 5, 6, 7, 9 (this task uses the book more than any other). Dynamo. Bigtable.
  Spanner. Raft.
- **Existing material.** `solutions/SD-15-distributed-kv-store.md` and the older video.

### 6.9 · SD-16 Distributed file / blob storage

- **Thesis.** Two problems. Metadata is a database that must be consistent and must scale. The data
  plane treats failure as the steady state, so repair is a permanent workload with a budget.
- **Central contrast.** Replication versus erasure coding: overhead against repair cost.
- **In round:** the data path, durability and repair. **Mid-round:** the namespace at 100 billion
  files.
- **Follow-ups (episode 1).** A rack dies: walk through the next hour · find silent corruption ·
  rename a directory holding a billion files · after a delete, when is the space free · AUX:
  justifying the durability target with evidence.
- **From the course.** Blob layout, erasure coding, integrity and scrubbing, repair, garbage
  collection of orphans, backups (7) · failure-domain placement (6) · primary–backup with leases (5) ·
  durability maths, bandwidth, cost modelling (1) · resumable upload, conditional requests (11) ·
  hedged requests, background against foreground work (13, 16) · control plane versus data plane (15).
- **Taught here.** The metadata service at 100 billion files: row keys, sharding, what a listing
  costs · placing one stripe across racks and zones · the repair scheduler: priority by remaining
  redundancy, throttling against foreground reads · the hour after a rack dies, in numbers · the
  write path with a lease and a generation number · renaming a huge directory · a durability model
  that admits correlated failure · tiering by temperature, signed URLs and disk-versus-flash
  behaviour (all three dropped from the course), one or two slides each.
- **Options matrix.** One master with chunk servers · sharded metadata in a consistent database ·
  3× replication · RS(6,3) · local reconstruction codes · replicate first and encode later · for the
  product shape: flat key space versus a hierarchical namespace.
- **Figures.** Client → metadata → storage servers with the data path bypassing metadata; the
  arithmetic (1 EB logical at 1.5× is 75,000 disks of 20 TB; at 1–2% annual failures, two to four
  die a day; 100 billion files at 200 bytes is 20 TB of metadata); a stripe across racks and zones;
  repair priority; a hedged and a reconstructed read; multipart upload; the write path with a lease
  and a version; mark-and-sweep with a grace period; namespace row keys.
- **Hunt.** Durability maths that assumes independent failures when a rack fails together · garbage
  collection racing an upload in flight · a stale writer after its lease · orphan parts of abandoned
  uploads · repair traffic starving foreground reads · eleven nines quoted with no model behind it.
- **Sources.** "The Google File System". The two Colossus posts on the Google Cloud blog. Tectonic.
  "Erasure Coding in Windows Azure Storage". SRE book ch. 26. DDIA ch. 5 and ch. 6. Private input:
  `~/Profile/materials/system-design/SysDesign_Q03_Object_Storage_Control_Plane.md`.

### 6.10 · SD-96 Live data migration and cross-region replication (new bank entry)

- **Thesis.** A migration is done when you can prove the two sides are equal and can still go back.
  That takes an ordered change stream, an idempotent version-checked apply, continuous verification,
  and a cutover with one writer per key.
- **Central contrast.** Application dual-writes versus change capture from the commit log.
- **In round:** zero-downtime migration to a new backend. **Mid-round:** keep both regions live
  afterwards (continuous replication).
- **Follow-ups (episode 1).** The write succeeds in the old store and fails in the new · prove the
  copy is identical while writes continue · roll back after two days of writes to the new system ·
  moving 100 PB: the arithmetic and the alternative · AUX: the last tenth of clients take most of
  the calendar; who owns the tail.
- **From the course.** Change data capture and the outbox, log shipping, snapshot plus log catch-up,
  multi-leader replication, conflict resolution, geo topologies, RPO and RTO, Merkle trees (5) ·
  online migration, version skew, progressive rollout (16) · leases and fencing, idempotency (2) ·
  conditional writes (8) · schema evolution (10) · bandwidth and transfer time (1) ·
  reconciliation and invariant audits (13).
- **Taught here.** A chunked snapshot interleaved with the live stream between two watermarks · the
  apply function and why it converges · verification against a moving target · the per-shard
  cutover with a fence, and its seconds of unavailability · reverse replication without loops ·
  what to do about a feature the new store lacks · home region per entity as conflict avoidance ·
  the long tail of clients as engineering work (AUX) · inter-region link limits (the course dropped
  them) in the 100 PB arithmetic.
- **Options matrix.** Stop the world · dual-write from the application · change capture plus backfill ·
  a proxy that shadows traffic · physical shipment for bulk · for the afterlife: active–passive,
  home region per entity, active–active with merge.
- **Figures.** The phases on one timeline (shadow-write, backfill, shadow-read and compare, canary
  reads, switch writes, reverse-replicate, decommission) with a rollback arrow from each; the
  dual-write failure as a sequence; the watermarked snapshot; the apply function as code;
  verification by range checksum; the cutover with a fence; the arithmetic (100 PB over 100 Gb/s is
  about 93 days; 1 PB at 1 GB/s about 12 days, so the change stream is kept at least that long).
- **Hunt.** A backfill row overwriting a newer captured write · a delete that the backfill resurrects ·
  a schema change in month three of six · two writers during the switch · "verified" against a moving
  target · reverse replication looping its own writes back · a feature the old store had and the new
  one lacks (secondary index, TTL, a transaction).
- **Sources.** "Online, Asynchronous Schema Change in F1". DBLog. Dynamo (anti-entropy). Shapiro et
  al. on CRDTs. DDIA ch. 4, ch. 5, ch. 11. SRE book ch. 26. *Software Engineering at Google* ch. 15
  (Deprecation) and ch. 22 (Large-Scale Changes).

### 6.11 · SD-47 Ticket booking / reservation (one supplement episode)

The written design and the round video exist and are not rebuilt. The author writes a short design sheet and one episode's segments; the runner subtasks of §5.3 then apply with one episode:

1. Read the existing design and script. List which of the brief's three variants and "Expect"
   questions they already answer (correctness and the on-sale surge are expected to be covered;
   time-slot capacity is expected to be missing). The list goes into a short `design-sheet.md`
   that holds only the additions.
2. Build **one supplement episode**, 30–43 minutes, in the shape of §3.3 and §3.4 combined: a deep
   dive on capacity per time bucket (a reservation spanning buckets decrements all of them
   atomically; overstay; an offline gate that syncs later), then the follow-up bank for every
   unanswered "Expect" question, two incidents, ten flashcards.
3. **From the course.** Isolation levels and anomalies, optimistic and pessimistic concurrency, the
   reservation pattern, idempotency keys, sagas (8) · admission control and queues (12) · hot
   partitions (6).
4. Slide PDF and handout for the supplement. Leave the existing design, its PDF and the first video
   untouched; note in the status file anything in them the supplement had to correct.

## 7 · The two new bank entries (SD-95, SD-96)

The author does this before the design sheet.

1. Read `Cue-Sheet-Template.md`, `CONTRIBUTING.md` and one Tier-2 sheet as a model (for example
   `### SD-26` in `questions/D-infrastructure-control-planes.md`).
2. Write a **Tier-2 compact sheet**: a prompt of two or three sentences in your own words, deliberately
   under-specified; clarification numbers; the checklist; five probes; weak / strong / exceptional
   bands. Append it to archetype D (SD-95) or C (SD-96).
3. Add the row to `Question-Bank.md` in the matching table, with kind `Build`, the domain, the levels
   and what it loads. Leave the company-frequency column modest and generic; do not copy counts from
   the private report.
4. The prompt must not quote any reported interview question.

## 8 · Done means

Per task, all true:

- [ ] `design-sheet.md` is within 1,200 words and its brief checklist has no unmapped item; every
      ticked item was found on a slide.
- [ ] No reference-design booklet was written.
- [ ] `claims.md` covers every number; every estimate was recomputed.
- [ ] The race hunt ran; its findings are in episode 2.
- [ ] Each episode: 1920×1080, under 45 minutes, no subtitle stream, chapters present;
      `check_audio.py` flags reviewed; sync probe passed; six frames looked at; every frame was
      tiled and looked at before the build.
- [ ] Episode 1 stands alone as a complete round. Episodes 2 and 3 repeat nothing from it beyond
      the recap slide. If episodes 2 and 3 were merged, the status file says why.
- [ ] Every *From the course* concept has at most one recall slide, with the part and section in
      its kicker; every *Taught here* item has a full treatment in episode 2; the course map is in
      the appendix deck.
- [ ] All episodes carry the same numbers and names as the design sheet.
- [ ] Slide PDFs, appendix PDF and the handout were built and looked at.
- [ ] Nothing private in tracked files (`git diff --stat` reviewed; grep the diff for `T0`, `T1`,
      "reported", and the question-bank names listed in the private report).
- [ ] Index rows added; publish kit written for episode 1; MP4s and PDFs left local, not copied to Drive; nothing
      uploaded; nothing pushed.
- [ ] Status file updated with counts, durations, corrections and open questions.
