# Reference solution — expectations and guidelines

The standard for every design-room **reference solution**: one question from the bank, worked from the prompt to the recap, as
a candidate would present it to an interviewer, as a video and a written booklet. Decided with the author on 2026-11-12;
**revised 2026-11-21** (progressive disclosure, scientific style, captions as files, C4 earlier and deeper, every component one
level down with concrete technologies and rejected alternatives). It builds on three analysed references
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
| 1 | **Requirements and scope** | 7 | Clarifying questions asked aloud, answered by the interviewer; numbered FRs; NFRs with numbers; the IN/OUT pair; **the C4 context view (level 1)**; "the core is N things" |
| 2 | **Estimates** | 5 | Each number as arithmetic with its consequence; a label on every number: illustrative, initial target or measured |
| 3 | **Theory** | 11–14 | See §4. Every slide carries the THEORY badge |
| 4 | **API and entities** | 5 | Wire formats; each API tagged with the requirement it serves and the entity it touches; conceptual then physical model |
| 5 | **High-level design** | 16–20 | V1 → V2 → V3 on the carried baseline, each answering the objection to the one before; **the C4 container view straight after V3, walked container by container** (≥ 40 spoken words each); one numbered flow **and one sequence diagram per functional requirement** (every core read and write path) |
| 5.1 | **Components and technologies** | 10–14 | See §4a: containers with technologies; a C4 component view of every in-scope service; one technology slide per in-scope container; the stack on one slide |
| 6 | **Bridge** | 1 | "It works. Where does it break first?" and the challenge map: the baseline with the attack points marked one by one |
| 7 | **Challenges** (6–8) | 36–45 | See §5. The last one is always "how would you know it is broken?" |
| 8 | **Build cost** (AUX) | 4 | V1/V2/V3 scope; people and months; buy against build; the top risks. Marked AUX as the manager layer |
| 9 | **Recap** | 4 | The final diagram drawn once more; one sentence per path; the common mistakes in this round; the thesis |

There is **no separate follow-up section**. A question that would have been a follow-up becomes a challenge.

## 4 · The theory chapter

It comes after the estimates and before any design, so the design can refer back to it. It answers one question:
*what makes this problem hard, in terms that outlive any product name?* Six parts, in this order:

1. **What it is, and what it is not.** One definition sentence to say aloud, then 2–4 neighbours it is confused with.
2. **Properties, stated separately.** Safety: what must never happen. Liveness: what must eventually happen.
3. **The central tension.** The trade this problem forces, drawn as one picture.
4. **The mechanisms.** The 4–7 mechanisms the design will use, one slide each in a fixed form: *property it protects → how it
   works → the failure it rules out → what it costs.* Mechanism first, product name second.
   **Then the mechanisms at work (2–3 slides):** a C4 container view labelled by mechanism (where each one will live), and one or
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
| 4 Break | Candidate | baseline, box outlined dashed red | Where it breaks in the system |
| 5 Fix | Candidate | baseline, fix outlined green | One named mechanism, on the named technology. Then its sequence diagram, and code if the code is the mechanism (real client API where one exists) |
| 6 Why it works | Candidate | blue strip | Which property, and why this mechanism guarantees it |
| 7 "What if the fix fails?" | Interviewer | `.qs` | The second-level push |
| 8 Second fix | Candidate | baseline or cards | The next mechanism, or an honest limit and what it costs |
| 9 "If asked, I'd say" | Key-line voice | `.th.say` | The 2–4 sentence answer for the real round, spoken slowly |

Choosing the challenges: from the failure catalogue; ordered so each fix creates the next question; at least one each of
correctness, overload, failure recovery and observability; the crux gets two.

## 6 · Voices

| Voice | Share | Role |
|---|---|---|
| Candidate (`C`) | about 80–88% | Drives the whole walkthrough |
| Interviewer (`I`) | under 10% | Answers clarifying questions; opens each challenge; pushes "what if the fix fails?". Neutral, never praises |
| Key line (`V`) | under 6% | The thesis, the definition, the properties, each "if asked, I'd say", the close. Slower |
| Coach (`N`) | under 5% | "What is graded here", 1–2 sentences, at chapter boundaries only. Never explains the design |

## 7 · Picture

### 7.1 Style: clean and scientific

- **White page**, generous margins, one idea per slide. **Serif** (Charter, then STIX Two Text) for titles, statements and prose;
  **Inter small caps** for kickers, labels and table headers; monospace only for code, keys and wire formats.
- **Tables are booktabs**: a heavy rule above and below, a light rule under the header, no vertical lines, no fills except the
  pick (green) and the row just revealed (a pale tint).
- **Cards are hairline boxes** with a thin coloured left rule; statement slides (chapter cards, thesis, "if asked") are light
  paper with a serif statement, not dark full-bleed blocks.
- **Figures carry a caption** (`Figure 5.1 — …`) where the picture needs one sentence of context.
- **Colour means role, in every video**: client blue, edge darker blue, service purple, data store green, cache yellow, queue or
  log orange, external grey. Red is only failure; green outline is only a fix; blue outline is only "new in this step".
- The slide number sits small in a corner and is the same on every reveal step of one slide.
- The kit's `video.css` (copied from the current model solution) implements all of this; do not restyle per question.

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
- **Keep each step short.** A step is one to three sentences. A slide with more than ~12 steps is two slides.
- Statement slides (thesis, "if asked", chapter cards, interviewer questions) are shown whole.

### 7.3 Captions are files, never pixels

No caption band, no speaker chip, nothing burned into the picture. The build writes `NAME.srt` and `NAME.vtt` beside the MP4
(`--captions sidecar`): cues of at most two 42-character lines, the speaker named when the speaker changes. Upload the `.srt`
to YouTube as the English track, so viewers can turn captions on and off and auto-translate them. The MP4 carries no subtitle
stream.

### 7.4 Devices

- **One carried baseline** (`basesvg.Baseline`): every later picture is a view of it; boxes never move.
- **Arrows**: request solid dark, response dashed green, asynchronous dashed purple; numbered in flow views.
- **C4 views**: context (level 1) in chapter 1; containers (level 2) right after V3; components (level 3) in 5.1.
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
- [ ] One technology slide per in-scope container: how it is built, the pick, ≥ 2 named rejected alternatives with reasons, a theory citation; the stack on one slide; the choices are used consistently in challenges, build cost, recap and booklet
- [ ] 6–8 challenges, all nine beats each; every one drawn on the carried baseline; the last is observability; each ends with "if asked, I'd say"
- [ ] Every table, trace and diagram is revealed step by step in request-flow order (generator check passes; contact sheets read)
- [ ] No burned-in captions or speaker chip; `.srt` and `.vtt` beside the MP4; no subtitle stream in the MP4
- [ ] Every number carries arithmetic and a label; every mechanism names the property it protects
- [ ] Build-cost chapter marked AUX; canon check in the video README
- [ ] Third-party material: nothing copied; ideas and structure only, in our own words and drawings
- [ ] STANDARD.md sound and QA rules met; length reported with the word count and frame count; under 180 minutes
