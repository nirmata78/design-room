# Reference-solution video — expectations and guidelines

The standard for every design-room **reference solution video**: one question from the bank, worked from the
prompt to the recap, as a candidate would present it to an interviewer. Decided with the author on 2026-11-12.
It builds on three analysed references (`references/video-examples/`) and on the house video rules
(`~/.claude/skills/slide-video-kit/STANDARD.md`); the workflow is `SKILL.md` in this folder. Where this file and STANDARD.md disagree on shape or length,
this file wins for reference-solution videos; picture, sound, caption and QA rules stay as STANDARD.md has them.

## 1 · What the video is for

The viewer is preparing for a system-design round and wants to know **what the interviewer expects to hear**.
Interviewers calibrate on the same public material candidates study, so a reference solution must do three things:

1. **Follow the shape interviewers recognise**: scope → numbers → simple design → break it → fix it → recap.
2. **Cover the canon** for the question: the points every well-known treatment makes. Missing one reads as a gap.
3. **Go past the canon** on theory and failure: say which property each mechanism protects, and what it costs.

Content, clarity and learning come before length. Never rush a diagram to save minutes.

## 2 · The three references, and what each one contributes

| Reference | What it is | Take from it | Do not take |
|---|---|---|---|
| 01 Batch inference walkthrough (66 min) | One evolving canvas, 3 baseline versions, 7 challenges | The challenge grammar, the carried baseline, V1 → V2 → V3, worked cases with numbers, the "if asked, I'd say" closer, symptom-pair diagnosis, precision statements | One unbroken voice, no captions, sponsor blocks |
| 02 URL shortener walkthrough (39 min) | Framework-driven, one flow per requirement, 3 deep dives | The stage ribbon, IN/OUT scope pair, requirement → API → entity tags, numbered-arrow flows, colour by role, "every solution creates the next question" | Asserted technology, no failure or cost |
| 03 URL shortener book chapter (older) | The four-step written canon | The clarifying dialogue, the estimate chain, a worked example with real values, the two-option comparison table, the wrap-up list | Its depth: it stops before failure, operations and cost. Check its arithmetic |
| Distributed-lock dossier (the author's own) | A single-problem theory dossier | Theory before design, safety and liveness, the options matrix with a pick, "what is graded", common mistakes, build cost | Dossier length; this is a video |

## 3 · The shape (fixed order)

Target **60–90 minutes**; hard limit **180**. One video, not parts. About 8,000–12,000 spoken words and
150–220 slides at the house pace. Minutes below are a guide for a 90-minute video, not a quota.

| # | Chapter | Min | What must be on screen |
|---|---|---|---|
| 0 | **Cold open** | 3 | The hook (why the question is harder than it looks), the "what this question grades" table (weak signal against strong signal), the stage ribbon |
| 1 | **Requirements and scope** | 6 | Clarifying questions asked aloud and answered by the interviewer; numbered functional requirements; non-functional requirements with numbers; the IN/OUT pair; "the core is N things" |
| 2 | **Estimates** | 5 | Each number as arithmetic with its consequence; a tag on every number: illustrative, initial target or measured |
| 3 | **Theory** | 8–12 | See §4. Every slide carries the THEORY badge |
| 4 | **API and entities** | 6 | Wire formats; each API tagged with the requirement it serves and the entity it reads or writes; conceptual then physical data model |
| 5 | **High-level design** | 12 | V1 → V2 → V3 on the carried baseline, each version answering the objection to the one before; one numbered-arrow flow per functional requirement; then the C4 container view and one sequence per core flow |
| 6 | **Bridge** | 1 | "It works. Where does it break first?" and the challenge map: the baseline with the 6–8 attack points listed |
| 7 | **Challenges** (6–8) | 36–45 | See §5. The last one is always "how would you know it is broken?" |
| 8 | **Build cost** (AUX) | 4 | V1, V2, V3 scope; people and months; buy against build; the top risks. Marked AUX as the manager layer |
| 9 | **Recap** | 4 | One clean final diagram; one bar per path with one sentence; the common mistakes in this round; the thesis |

There is **no separate follow-up section**. A question that would have been a follow-up becomes a challenge.

## 4 · The theory chapter

It comes after the estimates and before any design, so the design can refer back to it. It answers one question:
*what makes this problem hard, in terms that outlive any product name?* Six parts, in this order:

1. **What it is, and what it is not.** One definition sentence to say aloud, then 2–3 neighbours it is confused
   with (a lock is not a mutex, a queue is not a log).
2. **Properties, stated separately.** Safety: what must never happen. Liveness: what must eventually happen.
   One sentence each, specific to this problem. Every later fix says which one it serves.
3. **The central tension.** The trade this problem forces (consistency against availability per workflow,
   latency against throughput, freshness against cost), drawn as one picture.
4. **The mechanisms.** The 4–7 mechanisms the design will use. For each, one slide in a fixed form:
   *property it protects → how it works → the failure it rules out → what it costs.* Mechanism first, product
   name second.
5. **The options matrix.** 3–6 serious approaches as rows; the properties that decide as columns; the failure
   that rules each one out. One row picked, the rest greyed and kept visible. Say what the pick gives up.
6. **The failure catalogue.** The list of things that will go wrong. It becomes the challenge list.

Rules: define every term on first use; no theory slide without a consequence for this design; if a part has
nothing to say for this problem, say so in one line and move on.

## 5 · The challenge grammar

Each challenge runs 5–6 minutes on the carried baseline and follows the same nine beats. One beat is one or
more slides; one idea per slide still holds.

| Beat | Speaker | Slide | Content |
|---|---|---|---|
| 1 Question | Interviewer | `.qs` with the pause marker | The challenge as a question. Then a 2-second pause |
| 2 Naive answer | Candidate | challenge slide, red strip | The first answer most people give, said fairly |
| 3 Case | Candidate | state trace | Concrete IDs, times and numbers that break the naive answer |
| 4 Break | Candidate | baseline, box outlined dashed red | Where it breaks in the system |
| 5 Fix | Candidate | baseline, fix outlined green | One named mechanism. Then its sequence diagram, and code if the code is the mechanism |
| 6 Why it works | Candidate | blue strip | The theory beat: which property, and why this mechanism guarantees it |
| 7 "What if the fix fails?" | Interviewer | `.qs` | The second-level push |
| 8 Second fix | Candidate | baseline | The next mechanism, or an honest limit and what it costs |
| 9 "If asked, I'd say" | Key-line voice | dark `.th.say` | The 2–4 sentence answer to give in the real round, spoken slowly |

Choosing the challenges: take them from the failure catalogue; order them so each one's fix creates the next
one's question; include at least one each of correctness, overload, failure recovery and observability; the
crux of the question gets two.

## 6 · Voices

| Voice | Share | Role |
|---|---|---|
| Candidate (`C`) | about 80% | Drives the whole walkthrough as a continuous explanation |
| Interviewer (`I`) | under 10% | Answers clarifying questions; opens each challenge; pushes "what if the fix fails?". Neutral, never praises |
| Key line (`V`) | under 5% | The thesis, the definition sentence, each "if asked, I'd say", the close. Slower |
| Coach (`N`) | under 5% | "What is graded here" notes, 1–2 sentences, at chapter boundaries only. Never explains the design |

## 7 · Picture

House light slides stay, with C4, sequence and ERD diagrams. Added for this format:

- **One carried baseline.** The system is declared once (`basesvg.Baseline`) and every later picture is a view
  of it: version builds, numbered flows, challenge overlays. Boxes never move. A challenge dims the rest; it
  never redraws.
- **Colour means role, in every video**: client blue, edge darker blue, service purple, data store green,
  cache yellow, queue or log orange, external grey. Red is only failure; green outline is only a fix; blue
  outline is only "new in this step".
- **Arrows**: request solid dark, response dashed green, asynchronous dashed purple. In a flow view the arrows
  are numbered and the narration uses the numbers.
- **Question titles** on challenge slides; **chip strip** under titles that carry numbers; **stage ribbon** on
  every chapter card; **traceability tags** on API and flow slides.
- **State traces** for failures: one line per event, time first, the broken line in red.
- **Latency budget** as one bar that sums to the target with the spare drawn (`basesvg.budget_bar`).
- **Symptom-pair table** in the observability challenge: two metrics, one conclusion.
- The C4 container view and the sequences use the kit's existing generators and palette; the baseline is the
  map, C4 and sequences are the detail.

## 8 · Language

- **Precision statements.** Name the guarantee exactly ("at-least-once delivery with idempotent handlers, not
  exactly-once"). Separate near-synonyms when both appear.
- **Label every number**: illustrative, initial target, or measured. Say so aloud once per chapter.
- **Mechanism before brand.** Then name a product against its rejected alternatives, with the failure that
  rules each out.
- **Bridges are spoken.** "It works; where does it break first?" between design and challenges; "that fix
  creates the next question" between challenges.
- Write for the ear: short sentences, one idea each. Walk every diagram element by element.

## 9 · The canon check

Before the outline is final, list the points the standard treatments of this question make (the book chapter
if one exists, the widely watched walkthroughs, the question's cue sheet). Each one is either **covered**, with
the slide where, or **dismissed aloud**, with the reason. Older sources get a "what changed since" line.
The list goes in the video's README, not on screen.

## 10 · Acceptance checklist

A video is not done until every line holds.

- [ ] Chapters 0–9 present, in order; the ribbon shows the current one on every chapter card
- [ ] "What this question grades" table near the start; common mistakes in the recap
- [ ] Theory chapter has all six parts; safety and liveness are stated separately; the matrix has a pick and a stated cost
- [ ] V1 → V2 → V3, each version introduced by the objection it answers
- [ ] One numbered flow per functional requirement; narration uses the numbers
- [ ] 6–8 challenges, all nine beats each; every one drawn on the carried baseline; the last is observability
- [ ] Every challenge ends with "if asked, I'd say" in the key-line voice
- [ ] Every number carries arithmetic and a label; every mechanism names the property it protects
- [ ] Build-cost chapter marked AUX
- [ ] Canon check written in the video README
- [ ] Third-party material: nothing copied from the references; ideas and structure only, in our own words and drawings
- [ ] STANDARD.md picture, sound, caption and QA rules met; length under 180 minutes, reported with the word count
