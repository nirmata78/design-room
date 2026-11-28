# Reference solution — expectations and guidelines

The standard for every design-room **reference solution**: one question from the bank, worked from the prompt to the recap the way a
candidate would present it in a real round, as **one narrated video and one generated Markdown design**. Decided with the author on
2026-11-12 and revised several times since; **rewritten 2026-11-28 (issue #5)** into the **six-chapter, C4-first, challenge-driven
format**: the design starts as a C4 container view (V1) and evolves only because an interviewer challenges it; theory, component
views and technology choices appear at the moment a challenge needs them, never in a separate lecture. The pilot is
`solutions/SD-03-ad-click-aggregation/`. The workflow is `SKILL.md` in this folder.

What changed on 2026-11-28, and why: the old ten-chapter shape walked the same architecture three or four times (a theory chapter
before any design, V1 → V3 and then a C4 container walk of the same boxes, a 5.1 technology tour of the same boxes again, then the
challenges). A real round never does that. The old pipeline also used three diagram generators (PlantUML, hand-placed `c4svg`,
`basesvg`), kept a hand-written booklet beside the video sources, and left PDFs, frames and HTML behind. All of that is gone.

## 1 · What it is for

The viewer is preparing for a system-design round and wants to know **what the interviewer expects to hear**, and what comes after
the first answer, when the interviewer goes one level down on a box. A reference solution must:

1. **Follow the shape interviewers recognise**: scope → numbers → API and data → a simple design → break it → fix it → recap.
2. **Cover the canon** for the question: the points every well-known treatment makes. Missing one reads as a gap.
3. **Go past the canon** on failure and implementation: which property each mechanism protects, what it costs, and which concrete
   technology carries it, against which named alternative, and why.
4. **Look like a candidate thinking at a whiteboard**: nothing appears before it is spoken about.

Content, clarity and learning come before length. Never rush a diagram to save minutes.

## 2 · The references, and what each one contributes

| Reference | What it is | Take from it | Do not take |
|---|---|---|---|
| 01 Batch inference walkthrough (66 min) | One evolving canvas, 3 baseline versions, 7 challenges | The challenge grammar, the carried baseline, V1 → V2 → V3, worked cases with numbers, the "if asked, I'd say" closer, symptom-pair diagnosis | One unbroken voice, no captions, sponsor blocks |
| 02 URL shortener walkthrough (39 min) | Framework-driven, one flow per requirement | The stage ribbon, IN/OUT scope pair, requirement → API → entity tags, numbered-arrow flows, colour by role | Asserted technology, no failure or cost |
| 03 URL shortener book chapter (older) | The four-step written canon | The clarifying dialogue, the estimate chain, the two-option comparison table, the wrap-up list | Its depth: it stops before failure and operations. Check its arithmetic |
| Distributed-lock dossier (the author's own) | A single-problem theory dossier | Safety and liveness, the options matrix with a pick, "what is graded", common mistakes | Dossier length; this is a video |
| Building-blocks course (`theory/video/src/`, the author's own) | 17 parts of mechanisms with "one level down" panels | The grounding for every technology card: cite the part and section | Its length; cite, don't repeat |

## 3 · The shape: six chapters, fixed order

Target **40–60 minutes** (the upper end is soft: clarity wins over the clock — never cut a component view or a card slide to save a minute); hard limit 90. About **5,500–7,500 spoken words**. Each logical slide is shown as several reveal frames.

| # | Chapter | Min | What must be on screen |
|:-:|---|:-:|---|
| 1 | **Prompt, clarifying Q&A and C4 context** | 4–6 | Cold-open hook; the *what this question grades* table (weak against strong signal); the thesis; **the scale line** (§3.1); 4–6 clarifying questions asked aloud and answered by the interviewer; numbered FRs; quantified NFRs; the **properties** (safety and liveness, each with a slug, §4.3); IN/OUT scope; the **C4 system context (L1)** with synchronous `[HTTPS]` and asynchronous `[Event]`/`[Batch]` boundaries drawn distinctly; "the core is N things" |
| 2 | **Back-of-the-envelope** | 4–5 | Every number as arithmetic **from the scale line**, with a label (illustrative, initial target, measured) and **the constraint it forces**: what it rules out and what it requires; the latency or freshness budget as one bar |
| 3 | **API contracts and the data model** | 4–5 | Wire formats (`code()`/`wire()`) for each FR endpoint or event, with idempotency keys, headers and status codes, each tagged with the FR it serves; the physical ERD built table by table (`erdsvg`); a state machine where the core entity has a lifecycle (`statesvg`) |
| 4 | **The design, driven by challenges** | 22–32 | **V1 is the C4 container view** (L2, c4-structurizr), the simplest design that satisfies the happy path, technologies on the boxes; its happy path walked once as a numbered flow; then **5–6 interviewer challenges** (§5), each a sub-chapter 4.1 … 4.6 that breaks the design and fixes it with a C4 delta (V2, V3, V4 …) or a C4 component zoom (L3), introducing the mechanism and the technology card **at that moment** |
| 5 | **When you don't need all this** | 2–3 | The simpler design at 10–100× lower scale, marked ALTERNATE (§3.2); what it gives up; **the crossover number** from chapter 2 |
| 6 | **Recap, trade-offs and follow-ups** | 3–4 | The final container view with mechanism badges; the stack against its rivals (from `stack.json`); the common mistakes; the follow-up questions an interviewer asks next (`followups()`); the thesis again |

**What no longer exists**, on purpose: a theory chapter before the design; a C4 container walk after V3; a 5.1 technology tour; a
drill interlude; a bridge chapter with a challenge map; a build-cost chapter. Their content moves into chapter 4 at the moment a
challenge motivates it, or into the recap. A question that would have been a follow-up becomes a challenge or a recap row.

### 3.1 · The scale line

The first numbers the viewer hears, said once in chapter 1 and shown on one slide: the volume per month, the total over the
retention period, and the peak with its cause (SD-03: 25 T impressions and 250 B clicks a month, 6 months kept, 30 M events a second
in the evening with one ad at 2 M/s). **Every later number is arithmetic that starts from one of these**, and the narration says
which one. A number in chapter 2 or a challenge that does not trace back to the scale line is a defect.

### 3.2 · The alternate path: "when you don't need all this"

One short chapter shows the simpler design that is correct at a smaller scale (SD-03: one ClickHouse cluster as buffer, truth and
dashboard). It shows the simpler design as its own C4 view marked ALTERNATE (`alternate:` in `views.json`); **what it gives up**,
named precisely; and **the number at which the full design becomes necessary**, from chapter 2. Said as a judgment, not an apology:
"below N, I would ship this."

### 3.3 · Challenges reach the mechanism, one level down

A challenge is not answered by naming a component. The fix must say, at the level an interviewer drills to: **what exactly is
written or appended** (the record, the key and the condition of the write), **which failure it covers and which it does not**,
**why this tool and not the one under it**, and **when the simpler option is acceptable**. Status codes and protocol edges count as
mechanisms too. The component the fix lives in is shown in a C4 component zoom (L3) of its container.

## 4 · Mechanisms, components and technologies: just in time

### 4.1 · A mechanism appears inside the challenge that needs it

`mech_slide(n, total, name, protects, how, rules_out, costs, say)`: four blocks, *property it protects → how it works → the failure it
rules out → what it costs*. Mechanism first, product name second. If the mechanism is best seen at protocol level, the sequence
follows **on its own slide** (`stage()` or `dia()`; a sequence inside the half-width infographic is too small for 1080p). Choose the
picture type per mechanism: a sequence for protocols and races, a state machine for lifecycles, a C4 zoom for placement, an ERD for
keys and invariants.

### 4.2 · Options belong to the challenge that forces the choice

The serious approaches (3–6) are compared where the choice is made, usually the first challenge: a matrix with a pick and the
rest greyed, and one sentence on what the pick gives up. `option_slide()` exists for an option worth its own infographic.

### 4.3 · Properties carry descriptive slugs

`props(S1="count-once", …)` once in `gen.py`; `pid("S1")` on slides prints `[S1-count-once]`; `ps("S1")` in narration says "S-one,
count once"; the Markdown prints `` `[S1-count-once]` ``. A bare `S1`/`L2` on a slide or in speech fails `gen.py` (`lint_props`) and
`md_github.py`. Slugs: 2–4 lower-case words that state the property. Write "layer-4", not "L4".

### 4.4 · Technology cards, from one file

Each in-scope container's choice is a technology card (`tech(**ST.tech(id))`, narration `ST.say(id)`) shown **when that container
is built or challenged**: *how it is built* one level down, the pick with its deciding reason, and **at least two named rejected
alternatives, each with the property or failure that rules it out**; cite the building-blocks course part. The recap repeats the
stack as one table (`ST.summary()`). **`stack.json` is the only place a technology choice is written** (the kit's `stack.py` reads
it); the container technology lines on the C4 boxes live in `workspace.dsl`. A choice changed in one place only is a defect.

Rules: a product is named only after its mechanism has been explained; prefer the boring, operable choice and say so; the rejected
alternative is the one an interviewer will actually name.

## 5 · The challenge grammar

Each challenge is a sub-chapter (`challenge(n, total, title, question)`) of 3–6 minutes:

| Beat | Speaker | Slide | Content |
|---|---|---|---|
| 1 Question | Interviewer | `qs`, opened by `challenge()` | A concrete failure, scale bottleneck, race, hot key, crash or replay, late data, or observability gap, against the current design |
| 2 Case | Candidate | `trace()`: one event per reveal | Concrete IDs, times and numbers that break the naive answer |
| 3 Break | Candidate | the **C4 container view** marked BREAKS (`breaks:`), or a **C4 component zoom** of the container involved (`keep:` + `breaks:` on the full component view, the rest dimmed), drawn with `zoom()`: the picture full frame, then the naive answer and the break as cards on their own slide | Where it breaks, one level down |
| 4 Mechanism | Candidate | `mech_slide()`, then its sequence on its own slide if it has one | The property protected, how it works, what it rules out, what it costs |
| 5 Fix | Candidate | the **C4 delta**: the next version with NEW boxes (`new:`), or the zoom with FIX marks (`fix:`, via `zoom()`); the version tag (`vtag="V2"`) when the container view changes | One named mechanism on one named technology, **one level down (§3.3)**, its coverage and limit as strips, and **one Rejected line** (`rejl(*ST.rej(n))`). Pseudocode when the steps are the mechanism (§7.7); the technology card if this is where the container first matters |
| 6 Push | Interviewer | `push("…")` | "What if the fix fails?": restart, replay, 10× load, a quiet partition, the checker itself wrong |
| 7 Second fix | Candidate | a zoom, a sequence or cards | The next mechanism, or an honest limit and what it costs |
| 8 "If asked, I'd say" | Key-line voice | `say_slide()` | The 2–4 sentence answer for the real round; then the coach's one-line bridge: "that fix creates the next question" |

Choosing the challenges: ordered so each fix creates the next question; at least one each of correctness, overload, failure
recovery and observability; **the last is always "how would you know it is broken?"**; the crux gets the most depth. Five or six.

**Versions follow the challenges.** V1 is the first container view. Each challenge whose fix adds a container carries the design
forward as the next version (V2, V3 …), drawn as a delta on the same master layout (boxes never move: `views.json` cuts versions
from one exported view and locks the viewBox). A challenge answered inside one container changes no version; it zooms into that
container's component view instead: the **first** time a challenge enters a container, show its whole component view on a `stage()`
slide (revealed in a few grouped steps), then every zoom of that container is the same picture with the boxes in play marked and
the rest dimmed. The recap shows the last version.

**Ad-hoc box sketches are not used.** Every architecture picture is a view of `workspace.dsl`.

## 6 · Voices

| Voice | Share | Role |
|---|---|---|
| Candidate (`C`) | about 80–85 % | Drives the whole walkthrough |
| Interviewer (`I`) | under 10 % | Answers clarifying questions; opens each challenge; pushes one level deeper. Neutral, never praises |
| Key line (`V`) | under 8 % | The thesis, the properties, each "if asked, I'd say", the close. Slower |
| Coach (`N`) | under 7 % | "What is graded here", challenge intros and bridges, the mistakes. Never explains the design |

Write narration with written forms (`API`, `202`, `ClickHouse`); the pronunciation map (`META["say"]`, `theory/video/say.py`)
respells them for the voice, captions keep the written form, and the Markdown reverses any respelling (`say_to_prose()`).

## 7 · Picture

### 7.1 Style: clean, light, Google colours and Google Fonts

Full tokens: **`DESIGN-TOKENS.md`**. Every slide is a white card in a thin frame (a #202124 band with a yellow and a grey wedge);
chapter and challenge cards use the four-colour frame with diagonal corner stripes and a large centred title (§7.1 of the tokens:
learned from two author decks, recoloured to Google). Generous margins, one idea per slide. **Plus Jakarta Sans** for titles and
statements, **Inter** for prose, tables, captions and diagram labels, **Roboto Mono** only for code and wire formats. Tables are
booktabs; cards are hairline boxes with a coloured left rule. **Colour means role**: Google Blue for what is in scope and "in focus", Green
**only** for a fix, Yellow for NEW, cache and cost, Red **only** for failure, grey for external systems. In a C4 diagram the role
of a box is its **shape** (person, cylinder, log, bucket, `>_`, component icon), not its colour. The
kit's `video.css` + `google-theme.css` and c4-structurizr's native renderer (`c4draw.py`) implement all of this; do not restyle per
question (a view may only set its `box` size and `grid`). The SD-03 diagrams are the approved look (2026-11-28);
`.claude/skills/c4-structurizr/tests/test_golden_sd03.py` fails if the renderer drifts from them.

### 7.2 Progressive disclosure: nothing appears before it is spoken about

- Tables reveal one row at a time; traces one event at a time; cards, tiles, strips and lines are each a step.
- **C4 views** reveal in request order (`steps` in `views.json` for a first drawing); a **version** shows carried boxes at once and
  reveals each NEW box with its arrows; a **flow** reveals one numbered arrow per sentence; a **break/fix zoom** reveals each
  BREAKS/FIX pill; the **recap** reveals one mechanism badge at a time. Sequences add one message per step; ERDs one table per step;
  state machines one state or transition per step.
- Narration places the steps with `[+]`, `[+N]`, `[+*]`; `gen.py` refuses a slide that leaves anything unrevealed
  (`REVEAL_REPORT=1 python3 gen.py` lists every mismatch at once). A slide with more than ~12 steps is two slides.
- Statement slides (thesis, "if asked", chapter cards, interviewer questions) are shown whole.

### 7.3 Captions are files, never pixels

No caption band and nothing burned in. The build writes `NAME.srt` (cues ≤ 2 lines of ≤ 42 characters, the speaker named on a
change) and `NAME.vtt` (`<v Name>` voice spans) beside the MP4; the MP4 has no subtitle stream. Upload the `.srt` to YouTube.

### 7.4 C4 diagrams: one workspace, every view derived (c4-structurizr)

Every architecture picture comes from **`<solution>/workspace.dsl`** rendered by `.claude/skills/c4-structurizr` with
**`<solution>/views.json`**:

| Need | `views.json` |
|---|---|
| the context (L1) | the exported `systemContext` view, `"slot": "stage"`, a cross-shaped `grid` (the system in the middle), `steps` in narration order |
| the master container view | the exported `container` view containing every container that ever appears, with a `grid` designed so V1 sits in the middle and later versions fill the edges |
| a component view (L3) | the exported `component` view, `"slot": "stage"`, a `grid` of ≤ 4 columns × 3 rows (or 5 × 4 with one-line descriptions), grouped `steps`: shown whole the first time a challenge enters the container |
| V1, V2 … | `"from": "containers"` + `"hide": [...]` for boxes not built yet + `"new": [...]` for this version's boxes — the viewBox is locked to the master, so **boxes never move** |
| a numbered flow | `"from"` + `"flow": ["a->b", …]` |
| a break or fix on the container view | `"breaks": [...]`, `"fix": [...]`, `"focus": [...]` |
| a component zoom | `"from": "comp-x"` + `"keep": [2–4 components]` + `"breaks"`/`"fix"`: the rest of the component view dims, nothing moves (no `crop`) |
| mechanism badges | `"badges": {"alias": "M1 · Dedup"}` |
| the alternate path | its own exported view + `"alternate": [...]` |

Rules (c4-structurizr's native renderer, 2026-11-28 — c4model.com look, Google palette): `!identifiers hierarchical` and
`!impliedRelationships false`; arrows in **C4 "uses" direction** (from the reader to what it reads); every relationship has a
**technology** (`a -> b "Reads hour H" "Kafka"`, drawn as `[Kafka]`); shapes by tag (`Database`, `Queue`, `Bucket`, `App`, `External`);
a box description is one short line (≈ 20–28 characters) and a technology one or two words, because the `[Container: …]` line and
the description are 18–19 px on the frame; every exported view has a `grid` in `views.json` (externals outside the block of
containers or components in scope; neighbours that talk adjacent); the master container view ≤ 11 elements in ≤ 3 rows × 5 columns.
Non-C4 pictures (sequences, ERDs, state machines, budget bars, figures) come from `video/diagrams.py` with the kit's `seqsvg`,
`erdsvg`, `statesvg` and `figsvg`. **No PlantUML anywhere.**

### 7.5 Fit and readability at 1080p (measured, not eyeballed)

- **Minimum text on the frame**: 22 px for slide text, **18 px for diagram labels**. Two gates measure it: c4-structurizr's at
  render time (per view and slot: `stage` 1800 × 860, `full` 1704 × 780) and `check_layout.py` on the whole deck before any frame.
- **Caps per slide**: about 95 words on screen, 7 table rows, 12 reveal steps, a figure plus at most two strips and the Rejected line.
- The layout gate **fails the build** on overflow, overlapping text, a label wider than its box, small text or long code; dense
  slides and full redraws of one canonical picture are warnings to act on. Fix the slide or the view; never lower a limit to pass.
- A C4 view goes on a **`stage()`** slide (diagram only, one-line header; `stage()` refuses a header that would wrap). A zoom with
  explanation uses **`zoom()`**: the picture on a stage slide, then its cards (naive answer, break, mechanism, coverage, Rejected)
  at reading size on the next slide, the narration split where the figure's steps end. Never put a C4 view above a strip of cards:
  it lands under 14 px. Sequences go on `stage()` when they are tall.
- Tables reveal row by row and an unrevealed row takes no space (no empty ruled rows on screen).

### 7.6 Devices

Question titles on challenge slides; chip strips under titles that carry numbers; the stage ribbon on chapter cards; traceability
tags on API slides; the budget as one bar; the symptom-pair table in the observability challenge.

### 7.7 Code on slides

**Pseudocode by default** (`pseudo()`); a real language only when its idiom is the lesson; wire formats as they are on the wire.
At most **56 characters a line and 12 lines**; the lines the narration is about marked (`hl=`). Google tokens only; no red or green.

## 8 · Language

- **Precision statements.** Name the guarantee exactly ("at-least-once delivery plus dedup on an ID minted at the source").
- **Label every number**: illustrative, initial target, or measured.
- **Mechanism before brand, then the brand**, against the rejected alternatives.
- **Bridges are spoken**: "that fix creates the next question".
- Write for the ear: short sentences, one idea each. Walk every diagram element by element, in reveal order.

## 9 · One source: the video and the Markdown design

`video/src/*.py` is the only authored text. `gen.py` writes three things from it: the deck and the narration script (build
intermediates, deleted after the video) and **`SD-NN_<Title>_Reference_Design.md`** (tracked) via `dsl.write_reference_markdown()`:

- GitHub Pages front matter (`layout: reference-solution`, `title`, `description`, `question_id`, `level`, `tags`) — no LaTeX or
  Pandoc keys;
- every chapter and sub-chapter as a heading; every slide as a section with its visual — tables, code blocks, `$$` formulas and
  figures embedded straight from `video/svg/` (no copies) — and the narration beneath it: the candidate as prose, the interviewer as
  quotes, "If asked, I'd say" as `> [!TIP]`, the coach as `> [!IMPORTANT]`;
- an **Implementation Lab & Reproducible Workspace** section linking `workspace.dsl`, `views.json`, `stack.json` and `video/src/`.

Nothing in the Markdown is edited by hand; `md_github.py` lints it (figures exist, no bare property codes, no Pandoc keys).

## 10 · The canon check

Before the outline is final, list the points the standard treatments of this question make. Each is either **covered**, with the
slide where, or **dismissed aloud**, with the reason. The list goes in the video's README, not on screen.

## 11 · The deliverables, and nothing else

```
solutions/SD-NN-<slug>/
├── SD-NN_<Title>_Reference_Design.md   generated, tracked
├── stack.json                          tracked: technologies, rejected rivals, challenge rejections
├── workspace.dsl                       tracked: the one Structurizr workspace
├── views.json                          tracked: every derived view
└── video/
    ├── OUTLINE.md  README.md            tracked
    ├── build-video.sh                   tracked: calls scripts/ref_solution.py
    ├── diagrams.py                      tracked: sequences, ERDs, state machines, figures
    ├── svg/                             tracked: every SVG with its .steps.json and .meta.json (shared by video and Markdown)
    ├── src/                             tracked: gen.py and the chapter files
    ├── publish/                         tracked: meta.json, youtube.md, youtube-description.txt, thumbnail.png, linkedin.md
    └── <slug>-reference.mp4 · .srt · .vtt   local only (gitignored)
```

No PDF, no booklet sources, no `diagrams/` copies of the video's SVGs, no slides HTML, frames, scripts or layout reports after the
build (`ref_solution.py clean`; `--keep-intermediates` keeps them for debugging), no `.v*-retrofit-*` snapshots (git keeps history).

## 12 · Acceptance checklist

A reference solution is not done until every line holds.

- [ ] Six chapters in order; the ribbon shows the current one on every chapter card; 40–60 minutes, 5,500–7,500 words
- [ ] "What this question grades" near the start; the scale line opens chapter 1 and every number traces back to it
- [ ] Properties stated as safety and liveness with slugs; every mechanism names the property it protects
- [ ] C4 context (L1) in chapter 1 with sync and async boundaries drawn distinctly
- [ ] Chapter 2: every number has arithmetic, a label and the constraint it forces
- [ ] Chapter 3: wire formats tagged by FR; the physical model built table by table; the lifecycle as a state machine where one exists
- [ ] V1 is the C4 container view with technologies; its happy path is one numbered flow
- [ ] 5–6 challenges, every beat of §5; each fix one level down with a Rejected line; the last is observability; each ends with "if asked, I'd say"
- [ ] Versions V2, V3 … are deltas of one master layout (0 px shift); each container a challenge enters is shown as its whole component view once, and its zooms dim that same picture; no ad-hoc sketches, no PlantUML
- [ ] Mechanisms, options and technology cards appear inside the challenge that needs them; no separate theory chapter or technology tour
- [ ] The alternate path is shown, marked ALTERNATE, with what it gives up and the crossover number
- [ ] The recap shows the final view with mechanism badges, the stack table from `stack.json`, the mistakes and the follow-ups
- [ ] `ref_solution.py diagrams` exits ok (c4-structurizr gate, no unknown alias); `deck` reports **0 failures** and no redraw warning
- [ ] `ref_solution.py markdown` exits ok; the Markdown is generated, not edited, and renders on GitHub
- [ ] Every table, trace and diagram is revealed step by step in request order
- [ ] `.srt` and `.vtt` beside the MP4; no subtitle stream; cues ≤ 2 × 42 characters
- [ ] Nothing in §11's "no" list is left in the solution folder after the build
- [ ] Third-party material: nothing copied; ideas and structure only, in our own words and drawings
