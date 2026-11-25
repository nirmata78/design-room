# SD-NN · <Question> — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: __ min (75–100) · Word budget: __ (≈ minutes × 120) · Reveal steps: __

## Thesis and definition

- **Thesis** (one sentence, key-line voice):
- **Definition to say aloud** (what the system is, every clause load-bearing):
- **Hook** (why it is harder than it looks):

## Scale line (GUIDELINES §3.1)

Volume per month: · Total over the retention period: · Peak and its cause:
(every estimate below names which of these it starts from)

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | | |
| Correctness | | |
| Trade-offs | | |
| Depth | | |
| Operations | | |

## 1 · Requirements and scope

- Clarifying questions and the interviewer's answers:
- Functional requirements (FR1 …):
- Non-functional requirements, with numbers:
- IN scope / OUT of scope:
- "The core is N things":

## 2 · Estimates

| Number | From (scale line) | Arithmetic | Label (illustrative · target · measured) | Decision it drives |
|---|---|---|---|---|

## 3 · Theory

1. Is / is not:
2. Safety (must never happen): · Liveness (must eventually happen):
3. Central tension (and the picture for it):
4. Mechanisms — property (slug: `[S1-…]`, never a bare code) → how → failure ruled out → cost; diagram type per mechanism (c4 · seq · erd · state):
   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
5. Options: one infographic per option (pros · cons · C4 view · red pitfall boxes), then the matrix (rows = approaches, columns = deciding properties, last column = fails when). Pick: · Gives up:
   Mechanisms at work: the container view labelled by mechanism; 1–2 sequences at protocol level (which mechanism, which messages):
6. Failure list — outline only, no theory slide; it becomes the challenge map (ch. 6) and the follow-up questions (ch. 9):

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|

Entities (conceptual), then physical tables and keys:

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | | (none: simplest thing that works) | |
| V2 | | | |
| V3 | | | |

Baseline spine, left to right (this is also the reveal order):
C4 context (chapter 1): actors and external systems:
C4 containers = the carried baseline, built V1 → V3 (`since=`); one line per container, what the narration says about it:

Canonical diagram plan (GUIDELINES §7.5): each level drawn in full once; every later slide that shows it, and its delta:

| Slide | Canonical diagram | Delta (new= · badges= · flow= · keep=/attack=/fix=/focus= · OVERRIDE) |
|---|---|---|
Flows and sequences, one of each per functional requirement (numbered steps):

## 5.1 · Components and technologies

C4 component view per in-scope service (components, library or mechanism, timeouts):

Write the choices into `../stack.json` (SKILL step 2a), not here: `stack.py sync` fills the region below.

<!-- stack:outline -->
<!-- /stack:outline -->

Drill interlude: which 4–5 boxes, each with its probe (the `drill` field in `stack.json`).

## 5.2 · When you don't need all this (alternate path)

Simpler design (the one box that changes): · How it works, one level down: · What it gives up: · Crossover number (from the
scale line) and why: · What the narration says when it would switch:

## 7 · Challenges

One block per challenge, 6–10 in total. The last is observability. Versions follow the challenges: V4, V5 … for each fix that
changes the design.

### Challenge N · <short name>

- Q (interviewer):
- Naive answer:
- Case (IDs, times, numbers):
- Break (which component, inside which container; the C4 component view it is drawn on):
- Fix (mechanism) · sequence? pseudocode (key lines)?:
- One level down (what is written or appended; which failure it covers and which it does not; why this tool and not the one under it; when the simpler option is fine):
- Version after the fix (V4, V5 … or "no change"):
- Rejected on the fix slide (tool · why; `challenges` in `stack.json`):
- Why it works (property):
- "What if the fix fails?":
- Second fix or honest limit:
- If asked, I'd say:

## 8 · Build cost (AUX)

V1 / V2 / V3 scope · people and months · buy against build · top risks:

## 9 · Recap

Final diagram · one sentence per path · common mistakes in this round · closing line:

## Canon check

| Canonical point | Source | Covered at (chapter / slide) or dismissed because |
|---|---|---|

## Budget

| Chapter | Minutes | Words | Slides |
|---|---|---|---|
