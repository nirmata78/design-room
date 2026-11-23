# Reference solution — expectations and guidelines

The standard for every design-room **reference solution**: one question from the bank, worked from the prompt to the recap, as
a candidate would present it to an interviewer, as a video and a written booklet. Decided with the author on 2026-11-12;
**revised 2026-11-21** (progressive disclosure, light style, captions as files, C4 earlier and deeper, every component one
level down with concrete technologies and rejected alternatives); **restyled 2026-11-22** to Google colours and Google Fonts (`DESIGN-TOKENS.md`); **revised again 2026-11-22** after the SD-96 / SD-08 review (scale line §3.1, alternate path §3.2, challenges one level down and versions past V3 §3.3 and §5, one canonical diagram per level §7.5, the measured layout gate §7.6, code §7.7). It builds on three analysed references
(`references/video-examples/`) and on the house video rules (`~/.claude/skills/slide-video-kit/STANDARD.md`); the workflow is
`SKILL.md` in this folder. Where this file and STANDARD.md disagree, this file wins for reference solutions.

## 1 · What it is for

The viewer is preparing for a system-design round and wants to know **what the interviewer expects to hear**, and what comes
after the first answer, when the interviewer goes one level down on a box. A reference solution must:

1. **Follow the shape interviewers recognise**: scope → numbers → simple design → break it → fix it → recap.
2. **Cover the canon** for the question: the points every well-known treatment makes. Missing one reads as a gap.
3. **Go past the canon** on theory, failure and implementation: say which property each mechanism protects, what it costs, and
   which concrete technology carries it, against which named alternative, and why.
4. **Look like a candidate thinking at a whiteboard**: nothing appears before it is spoken about.

Content, clarity and learning come before length. Never rush a diagram to save minutes.

## 2 · The references, and what each one contributes

| Reference | What it is | Take from it | Do not take |
|---|---|---|---|
| 01 Batch inference walkthrough (66 min) | One evolving canvas, 3 baseline versions, 7 challenges | The challenge grammar, the carried baseline, V1 → V2 → V3, worked cases with numbers, the "if asked, I'd say" closer, symptom-pair diagnosis, precision statements | One unbroken voice, no captions, sponsor blocks |
| 02 URL shortener walkthrough (39 min) | Framework-driven, one flow per requirement, 3 deep dives | The stage ribbon, IN/OUT scope pair, requirement → API → entity tags, numbered-arrow flows, colour by role, "every solution creates the next question" | Asserted technology, no failure or cost |
| 03 URL shortener book chapter (older) | The four-step written canon | The clarifying dialogue, the estimate chain, a worked example with real values, the two-option comparison table, the wrap-up list | Its depth: it stops before failure, operations and cost. Check its arithmetic |
| Distributed-lock dossier (the author's own) | A single-problem theory dossier | Theory before design, safety and liveness, the options matrix with a pick, "what is graded", common mistakes, build cost | Dossier length; this is a video |
| Building-blocks course (`theory/video/src/`, the author's own) | 17 parts of mechanisms with "one level down" panels | The grounding for every technology slide: cite the part and section | Its length; cite, don't repeat |

## 3 · The shape (fixed order)

Target **75–100 minutes**; hard limit **180**. One video, not parts. About 10,000–12,500 spoken words and 150–190 logical slides
(each shown as several reveal frames). Minutes below are a guide, not a quota.

| # | Chapter | Min | What must be on screen |
|---|---|---|---|
| 0 | **Cold open** | 3 | The hook, the "what this question grades" table (weak against strong signal), the stage ribbon |
| 1 | **Requirements and scope** | 7 | **The scale line first** (§3.1); clarifying questions asked aloud, answered by the interviewer; numbered FRs; NFRs with numbers; the IN/OUT pair; **the C4 context view (level 1)**; "the core is N things" |
| 2 | **Estimates** | 5 | Each number as arithmetic **from the scale line**, with its consequence; a label on every number: illustrative, initial target or measured |
| 3 | **Theory** | 11–14 | See §4. Every slide carries the THEORY badge |
| 4 | **API and entities** | 5 | Wire formats; each API tagged with the requirement it serves and the entity it touches; conceptual then physical model |
| 5 | **High-level design** | 16–20 | V1 → V2 → V3 on the carried baseline, each answering the objection to the one before; **the C4 container view straight after V3, walked container by container** (≥ 40 spoken words each); one numbered flow **and one sequence diagram per functional requirement** (every core read and write path) |
| 5.1 | **Components and technologies** | 10–14 | See §4a: containers with technologies; a C4 component view of every in-scope service; one technology slide per in-scope container; the stack on one slide |
| 5.2 | **When you don't need all this** (alternate path) | 3–4 | §3.2: the simpler design, what it gives up, the scale at which the full design becomes necessary. Marked ALTERNATE, never the baseline |
| 6 | **Bridge** | 1 | "It works. Where does it break first?" and the challenge map: the canonical view with the attack points marked one by one |
| 7 | **Challenges** (6–10) | 36–50 | See §5. Each fix that changes the design carries the baseline forward: V3 → V4 → V5 …, as many versions as the challenges need. The last one is always "how would you know it is broken?" |
| 8 | **Build cost** (AUX) | 4 | V1/V2/V3 scope; people and months; buy against build; the top risks. Marked AUX as the manager layer |
| 9 | **Recap** | 4 | The final diagram drawn once more; one sentence per path; the common mistakes in this round; the thesis |

There is **no separate follow-up section**. A question that would have been a follow-up becomes a challenge.

### 3.1 · The scale line (from the SD-96 review, 2026-11-22)

The first numbers the viewer hears, said once in the framing and shown on one slide: the volume per month, the total over the
retention period, and the peak with its cause (SD-96: 100 M new links a month, 10 B redirects a month, a viral link at 40,000
clicks a second). **Every later estimate is arithmetic that starts from one of these numbers**, and the narration says which one.
A number in chapter 2 or a challenge that does not trace back to the scale line is a defect.

### 3.2 · The alternate path: "when you don't need all this"

After the design (5 and 5.1) and before the bridge, one short segment shows the simpler design that is correct at a smaller
scale. Example (SD-96): a PostgreSQL sequence replaces the consensus-backed range allocator. It shows: the one box that changes,
drawn as a delta on the canonical view (§7.5) and labelled ALTERNATE; **what it gives up**, named precisely (a single writer is the
bottleneck; failover leaves a gap or a reuse window); and **the number at which the full design becomes necessary**, from the
scale line. It is said as a judgment, not an apology: "below N, I would ship this."

### 3.3 · Challenges reach the mechanism, one level down

A challenge is not answered by naming a component. The fix must say, at the level an interviewer drills to: **what exactly is
written or appended** (the record in the log, the key and the condition of the write), **which failure it covers and which it
does not** (fencing stops a stale holder's writes from landing; it does not stop a partition from delaying them), **why this tool
and not the one under it** (etcd as a consensus log we rent, against running our own Raft), and **when the simpler option is
acceptable** (pure random codes against allocated ranges). Status codes and protocol edges count as mechanisms too (410 Gone for an
expired or deleted link, and what makes a crawler stop asking). A component the narration leans on (an encoder, an allocator)
gets its own box in a component view with its inputs, outputs and invariants, before a challenge drills into it.

### 3.4 · The compact cut: 60–80 minutes (from the SD-03 run, 2026-11-22)

The full shape runs 100–110 minutes in practice (SD-96, SD-08). When the author asks for a shorter video, or for any question
where the round's value is concentrated in a few mechanisms, use the **compact cut**. Same chapter order and the same rules
everywhere else; only these change:

| Part | Full | Compact |
|---|---|---|
| Length · words · logical slides | 75–100 min · 10,000–12,500 · 150–190 | **60–80 min · 7,800–8,800 · 110–130** (≈ 0.5 s a word all-in, measured on SD-08 and SD-96) |
| Theory | 4–7 mechanisms, 1–2 sequences | **4–5 mechanisms**, one slide each; **one** protocol-level sequence; the matrix and the catalogue as tables |
| Flows | a numbered flow and a sequence per FR | a sequence per FR; numbered flows for the **two core paths** only |
| 5.1 | a tech slide per in-scope container; drill interlude | tech slides for the containers the challenges drill (3–5), narration reads only the first clause of each rejection; **no drill interlude** (the booklet keeps the probes); component views only for the 2–3 containers the challenges open |
| Challenges | 6–10, 5–6 min each | **6**, about 4 min each (the crux still gets two); all nine beats, but beats 7–8 are one `qs` and one cards slide |
| Build cost (AUX) | chapter 8 | **dropped**: the recap becomes chapter 8 (`dsl.META["chapters"] = 8`, `dsl.STAGES` without "Cost") |
| Booklet | 15–22 k words | 8–10 k words, the same stages; Stage 10 says it is dropped |

Every chapter must last at least 10 seconds before the next one starts (YouTube drops the whole chapter list otherwise;
`publish_kit.py` refuses it): a chapter card followed at once by a sub-chapter card needs ~25 spoken words.
Cut words, not pictures: shorten narration per step before removing a diagram, and never drop the scale line, the alternate
path, the component views a challenge is drawn on, or the observability challenge.

## 4 · The theory chapter

It comes after the estimates and before any design, so the design can refer back to it. It answers one question:
*what makes this problem hard, in terms that outlive any product name?* Six parts, in this order:

1. **What it is, and what it is not.** One definition sentence to say aloud, then 2–4 neighbours it is confused with.
2. **Properties, stated separately.** Safety: what must never happen. Liveness: what must eventually happen.
3. **The central tension.** The trade this problem forces, drawn as one picture.
4. **The mechanisms.** The 4–7 mechanisms the design will use, one slide each in a fixed form: *property it protects → how it
   works → the failure it rules out → what it costs.* Mechanism first, product name second.
   **Then the mechanisms at work (2–3 slides):** where each mechanism will live, as a table (mechanism · container · one clause),
   not as a drawing of the system: the system is drawn once, in chapter 5 (§7.5). The mechanism labels come back later as
   badges on the canonical container view (`badges=`). Then one or
   two sequence diagrams that show the hardest mechanism operating at protocol level (a compare-and-set through a consensus log;
   cache-aside with single flight and a lifetime as the backstop). The viewer must see the mechanism, not only its name.
5. **The options matrix.** 3–6 serious approaches as rows; the deciding properties as columns; the failure that rules each out.
   One row picked, the rest greyed and kept visible. Say what the pick gives up.
6. **The failure catalogue.** It becomes the challenge list.

Rules: define every term on first use; no theory slide without a consequence for this design; if a part has nothing to say, say
so in one line and move on.

## 4a · Components and technologies (sub-chapter 5.1)

The interviewer's next move after the container view is "you said X; how does X actually work?". This sub-chapter answers it
ahead of time, **even where it goes past what a 45-minute round has time for**: it prepares the viewer for the deep-dive follow-up.

1. **Containers with technologies**: the same C4 container view, the type line naming the product (`Redis Cluster`,
   `etcd, 3 nodes, Raft`, `PostgreSQL, sharded by code`).
2. **A C4 component view (level 3) of every in-scope service** — the components inside it, each named with its library or
   mechanism (`ristretto, TinyLFU`, `singleflight`, `pgx pool`, `etcd client`), and the timeouts on every miss path.
3. **One technology slide per in-scope container** (`tech()` in the DSL): *how it is built* one level down (keys, partitions,
   replication, the exact conditional write, the eviction policy, the configuration that matters), the pick with its deciding
   reason, and **at least two named rejected alternatives, each with the property or failure that rules it out**. Honest equals
   are said to be equals. Cite the building-blocks course part that explains the mechanism (`theory/video/src/chNN.txt`).
4. **The stack on one slide**: container · choice · rejected · the deciding reason.
5. **The drill interlude** (~2 minutes): the coach hands the viewer the interviewer's seat ("which box would you drill, and
   what is your one question?", a pause), then 4–5 boxes, each with the probe an interviewer asks one level down and what a
   strong answer names, read as interviewer probe then coach answer. It turns 5.1 from a lecture into practice.

**One source.** Every technology fact on these slides, in the booklet's technology stage, in the outline's 5.1 table, on the
container view with technologies and on the fix slides' "Rejected" lines comes from `<solution>/stack.json` (SKILL step 2a).
A choice changed in one place only is a defect.

Rules: a product is named only after its mechanism has been explained; the choice must be consistent everywhere else (challenges,
booklet, build cost, recap); prefer the boring, operable choice and say so; the rejected alternative is the one an interviewer
will actually name (Cassandra, DynamoDB, ZooKeeper, Memcached, Hazelcast, RabbitMQ …).

## 5 · The challenge grammar

Each challenge runs 5–6 minutes on the carried baseline and follows the same nine beats.

| Beat | Speaker | Slide | Content |
|---|---|---|---|
| 1 Question | Interviewer | `.qs` with the pause marker | The challenge as a question. Then a 2-second pause |
| 2 Naive answer | Candidate | challenge slide, red strip | The first answer most people give, said fairly |
| 3 Case | Candidate | state trace, one event per reveal | Concrete IDs, times and numbers that break the naive answer |
| 4 Break | Candidate | **C4 component view** of the container involved, the component under attack marked BREAKS (`attack=`), the rest dimmed (`keep=`) | Where it breaks, inside the container, one level down |
| 5 Fix | Candidate | the same component view, fix marked FIX (`fix=`) or a new component marked NEW; the version tag (V4, V5 …) when the design changes | One named mechanism, on the named technology, **one level down (§3.3)**, and **one "Rejected" line**: the tool an interviewer would name instead and the property that rules it out (`rejl()`, from `stack.json`). Then its sequence diagram, and pseudocode if the steps are the mechanism (§7.7) |
| 6 Why it works | Candidate | blue strip | Which property, and why this mechanism guarantees it |
| 7 "What if the fix fails?" | Interviewer | `.qs` | The second-level push |
| 8 Second fix | Candidate | baseline or cards | The next mechanism, or an honest limit and what it costs |
| 9 "If asked, I'd say" | Key-line voice | `.th.say` | The 2–4 sentence answer for the real round, spoken slowly |

Choosing the challenges: from the failure catalogue; ordered so each fix creates the next question; at least one each of
correctness, overload, failure recovery and observability; the crux gets two. Six to ten, as the question needs.

**Versions follow the challenges.** V1 → V2 → V3 build the design; each challenge whose fix adds or changes a box carries the
baseline forward as the next version (V4, V5 …), shown as a delta on the canonical view (`new=`) with its version tag. A
challenge answered inside one component (a new condition on a write) changes no version. The recap shows the last version.

**Ad-hoc box sketches are not used in challenges.** The visual is always a view of a canonical diagram: the container view for
a cross-container problem, the container's component view otherwise.

## 6 · Voices

| Voice | Share | Role |
|---|---|---|
| Candidate (`C`) | about 80–88% | Drives the whole walkthrough |
| Interviewer (`I`) | under 10% | Answers clarifying questions; opens each challenge; pushes "what if the fix fails?". Neutral, never praises |
| Key line (`V`) | under 6% | The thesis, the definition, the properties, each "if asked, I'd say", the close. Slower |
| Coach (`N`) | under 6% | "What is graded here", 1–2 sentences, at chapter boundaries; the answers in the 5.1 drill interlude. Never explains the design elsewhere |

## 7 · Picture

### 7.1 Style: clean, light, Google colours and Google Fonts

Full tokens, sizes and per-renderer font loading: **`DESIGN-TOKENS.md`**. In short:

- **White page** (`#FFFFFF`, statement slides `#F8F9FA`), generous margins, one idea per slide. **Plus Jakarta Sans** (700/600) for titles
  and statements, **Inter** (400/500, labels 650) for prose, tables, captions and diagram labels, **Roboto Mono** only for code, keys and
  wire formats. No serif, no system face.
- **Tables are booktabs**: a heavy rule above and below, a light rule under the header, no vertical lines, no fills except the
  pick (green tint) and the row just revealed (a pale yellow tint).
- **Cards are hairline boxes** with a thin coloured left rule; statement slides (chapter cards, thesis, "if asked") are light
  `#F8F9FA` with a display-face statement, not dark full-bleed blocks.
- **Figures carry a caption** (`Figure 5.1 — …`) where the picture needs one sentence of context.
- **Colour means role, in every video**: Google Blue `#4285F4` for client, edge, service and "new in this step"; Google Green `#34A853` for
  data stores and **only** for a fix; Google Yellow `#FBBC05` for cache, hedge and cost; Google Red `#EA4335` **only** for failure; grey for
  external and for a queue or log. No purple or orange. Small coloured text uses the 700/800 shade (`#1967D2`, `#C5221F`, `#188038`,
  `#B06000`) so it stays legible; fills, rules and strokes use the brand hex.
- The slide number sits small in a corner and is the same on every reveal step of one slide.
- The kit's `video.css` + `google-theme.css` implement all of this; do not restyle per question.

### 7.2 Progressive disclosure: nothing appears before it is spoken about

- **Tables are revealed one row at a time**, each row with the sentence that discusses it; the header is visible from the start.
  Traces are revealed one event at a time. Cards, tiles, strips, takeaway lines and grading notes are each a step.
- **Diagrams are drawn 1–2 elements at a time, following the request flow** (left to right: client → edge → service → cache →
  store; then the side paths), as a candidate draws at a whiteboard. A version build shows what is carried, then adds each new
  box with its arrows. A numbered flow shows the picture, then adds one numbered arrow per sentence. A sequence diagram adds one
  message per step; a participant appears with its first message. A challenge overlay shows the picture, then the BREAKS / FIX
  marks, then the note.
- The default reveal order comes from the generators (`<name>.steps.json` beside each SVG); `order=` in `diagrams.py` sets the
  request-flow order where left-to-right is not it. Narration places the steps with `[+]`, `[+N]`, `[+*]`; the generator refuses a
  slide that leaves anything unrevealed.
- **Data models build up too.** A conceptual (Chen) model adds one entity, with its attributes, per step, and each relationship
  as its own step once both ends are drawn; a physical model adds one table per step, each relation with its second table
  (`erdsvg` writes the plan; `order=` sets it). A model that appears whole is a defect.
- **Keep each step short.** A step is one to three sentences. A slide with more than ~12 steps is two slides (`gen.py` warns).
- Statement slides (thesis, "if asked", chapter cards, interviewer questions) are shown whole.

### 7.3 Captions are files, never pixels

No caption band, no speaker chip, nothing burned into the picture. The build writes `NAME.srt` and `NAME.vtt` beside the MP4
(`--captions sidecar`): cues of at most two 42-character lines. The `.srt` names the speaker in the text when the speaker
changes (`Coach: …`), inside the 42-character budget; the `.vtt` names it as a WebVTT voice span on every cue (`<v Coach>…`),
which web players can style, with text-only lines. YouTube shows no voice spans, so upload the `.srt`
to YouTube as the English track, so viewers can turn captions on and off and auto-translate them. The MP4 carries no subtitle
stream.

### 7.4 Devices

- **One carried baseline**: every later picture is a view of it; boxes never move. New questions draw it **as the C4 container
  view** (`c4svg` with `since=` per box and edge), so the V1 → V3 build and the container walk are the same picture (§7.5).
  `basesvg.Baseline` stays for older solutions.
- **Arrows**: request solid dark, response dashed green, asynchronous dashed deep blue; numbered in flow views.
- **C4 views**: context (level 1) in chapter 1; containers (level 2) built V1 → V3 and walked; components (level 3) in 5.1, and
  again as the visual of every challenge about that container.

### 7.5 One canonical diagram per level, then deltas (from the SD-96 and SD-08 review, 2026-11-22)

Each level of the design is **drawn in full once**: the context view, the container view (built V1 → V3), and one component view
per in-scope container. After that the picture is only ever shown **as a delta on top of itself**, never redrawn:

| Need | View of the canonical diagram |
|---|---|
| a new version (V2, V4 …) | carried boxes at once, then only the new ones, marked NEW (`new=`) |
| the technologies (5.1) | the same boxes with product type lines (`OVERRIDE`) or product badges (`badges=`), introduced as "the same picture, one level down" |
| where the theory's mechanisms live | badges M1 … Mn on the container view (`badges=`), not a second system drawing in the theory chapter |
| a flow | the boxes, then one numbered arrow per step (`flow=`) |
| a challenge | the boxes involved, the rest dimmed and cropped away (`keep=`), BREAKS / FIX / IN FOCUS marks (`attack=`, `fix=`, `focus=`) |
| the alternate path | the one box that changes, marked ALTERNATE (`alt=` in `basesvg` and `c4svg`, added 2026-11-22) |
| the recap | the last version with one path highlighted at a time, not a fresh build |

The generators write `<name>.meta.json` (`canon`, `full`); the layout check warns on every second full drawing of one canon.

### 7.6 Fit and readability at 1080p (measured, not eyeballed)

- **Minimum text on the frame**: 22 px for slide text (`DESIGN-TOKENS.md` §2), **18 px for diagram labels** (type lines,
  edge labels, legends, badges). Dimmed context in a delta view (opacity under 0.5) is exempt; nothing else is.
- **Caps per slide**: about 95 words on screen (diagram labels not counted), 7 table rows, 12 reveal steps, a figure plus at most
  one strip and the Rejected line on a challenge slide; strips one or two lines each (the narration carries the rest). A
  technology slide's `how` is two or three sentences; the rest goes in `stack.json`'s `detail` (booklet only).
- **The layout gate**: `check_layout.py` measures every slide in Chromium before any frame is rendered and **fails the build** on
  overflow (past the content area, clipped in a cell, over the slide number), overlapping text (HTML or diagram labels), a
  label wider than its box, text under the minimum, or code past the limits below. Dense slides and full redraws are warnings
  to act on. Fix the slide (shorter text, `bt xs`, split, re-lay out the diagram); never lower a limit to pass.
- Diagrams are drawn for a 16:9 figure area (about 1736 × 770 frame px under a title): a canvas wider than tall, a legend in a
  free column, `size=` 24–28 for box titles. A delta view is cropped to what it is about, so its boxes grow.

### 7.7 Code on slides

- **Pseudocode by default** (`pseudo()`); a real language (`code(src, "go")`) only when its idiom is the lesson: the exact client
  call, the conditional write, the header that matters. Wire formats (`http`, `json`) are shown as they are on the wire.
- At most **56 characters a line and 12 lines** (`code()` refuses more); comments short; the lines the narration is about
  marked as key lines (`hl=(2, 3)`: a yellow tint and bar, the rest muted).
- Highlighting uses the Google tokens only: blue ink keywords, deep blue types, yellow ink strings and numbers, grey italic
  comments. No red or green in code: they mean failure and fix.
- Question titles on challenge slides; chip strip under titles that carry numbers; stage ribbon on chapter cards; traceability
  tags on API and flow slides; latency budget as one bar; symptom-pair table in the observability challenge.

## 8 · Language

- **Precision statements.** Name the guarantee exactly ("at-least-once delivery with idempotent handlers, not exactly-once").
- **Label every number**: illustrative, initial target, or measured. Say so aloud once per chapter.
- **Mechanism before brand, then the brand.** Explain the mechanism, then name the concrete product that carries it, against the
  rejected alternatives, with the failure that rules each out. Unnamed "a store" is not acceptable after chapter 5.1.
- **Bridges are spoken.** "It works; where does it break first?"; "that fix creates the next question".
- Write for the ear: short sentences, one idea each. Walk every diagram element by element, in reveal order.

## 9 · The canon check

Before the outline is final, list the points the standard treatments of this question make. Each one is either **covered**, with
the slide where, or **dismissed aloud**, with the reason. The list goes in the video's README, not on screen.

## 10 · Acceptance checklist

A reference solution is not done until every line holds.

- [ ] Chapters 0–9 (and 5.1) present, in order; the ribbon shows the current one on every chapter card
- [ ] "What this question grades" table near the start; common mistakes in the recap
- [ ] C4 context in chapter 1; C4 containers right after V3, walked container by container; a C4 component view per in-scope service
- [ ] Theory chapter has all six parts, plus a mechanism map and 1–2 mechanism sequences; safety and liveness separately; the matrix has a pick and a stated cost
- [ ] V1 → V2 → V3, each version introduced by the objection it answers
- [ ] One numbered flow **and one sequence diagram** per functional requirement; narration uses the numbers
- [ ] One technology slide per in-scope container: how it is built, the pick, ≥ 2 named rejected alternatives with reasons, a theory citation; the stack on one slide; the drill interlude; the choices are used consistently in challenges, build cost, recap and booklet
- [ ] `stack.json` is the only place a technology is written: `stack.py sync` reports "up to date" after the build, and `grep` finds no hand-written copy of the stack table
- [ ] Every challenge's fix slide ends with a "Rejected" line naming a tool and the property that rules it out
- [ ] 6–8 challenges (exactly 6 in the compact cut, §3.4), all nine beats each; every one drawn on the carried baseline; the last is observability; each ends with "if asked, I'd say"
- [ ] Every table, trace and diagram is revealed step by step in request-flow order (generator check passes; contact sheets read); data models build up entity by entity
- [ ] The scale line opens chapter 1 and every estimate traces back to it; the alternate path (5.2) is shown, marked ALTERNATE, with its limit and the crossover number
- [ ] Every challenge fix reaches the mechanism one level down (§3.3); versions follow the challenges (V4, V5 …); challenge visuals are C4 component or container views, never ad-hoc sketches
- [ ] Each level is drawn in full once; everything after is a delta (`check_layout.py` shows no `redraw` warning, or each one is justified in the README)
- [ ] `check_layout.py`: **0 failures** (overflow, overlap, label-in-box, minimum 22 px text and 18 px diagram labels, code ≤ 56 × 12); warnings read and acted on
- [ ] Code is pseudocode unless the idiom is the lesson; key lines marked
- [ ] No burned-in captions or speaker chip; `.srt` and `.vtt` beside the MP4; no subtitle stream in the MP4; SRT lines ≤ 42 characters; VTT cues carry `<v Name>`
- [ ] Every number carries arithmetic and a label; every mechanism names the property it protects
- [ ] Build-cost chapter marked AUX (absent in the compact cut); canon check in the video README
- [ ] Third-party material: nothing copied; ideas and structure only, in our own words and drawings
- [ ] STANDARD.md sound and QA rules met; length reported with the word count and frame count; under 180 minutes
