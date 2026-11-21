# SD-NN · <Question> — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: __ min (75–100) · Word budget: __ (≈ minutes × 120) · Reveal steps: __

## Thesis and definition

- **Thesis** (one sentence, key-line voice):
- **Definition to say aloud** (what the system is, every clause load-bearing):
- **Hook** (why it is harder than it looks):

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

| Number | Arithmetic | Label (illustrative · target · measured) | Decision it drives |
|---|---|---|---|

## 3 · Theory

1. Is / is not:
2. Safety (must never happen): · Liveness (must eventually happen):
3. Central tension (and the picture for it):
4. Mechanisms — property → how → failure ruled out → cost:
   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
5. Options matrix (rows = approaches, columns = deciding properties, last column = fails when). Pick: · Gives up:
   Mechanisms at work: the container view labelled by mechanism; 1–2 sequences at protocol level (which mechanism, which messages):
6. Failure catalogue (becomes the challenge list):

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
C4 containers (right after V3): one line per container, what the narration says about it:
Flows and sequences, one of each per functional requirement (numbered steps):

## 5.1 · Components and technologies

C4 component view per in-scope service (components, library or mechanism, timeouts):

| Container | Choice | How it is built (one level down) | Rejected (≥ 2) and why | Theory part |
|---|---|---|---|---|

## 7 · Challenges

One block per challenge, 6–8 in total. The last is observability.

### Challenge N · <short name>

- Q (interviewer):
- Naive answer:
- Case (IDs, times, numbers):
- Break (which box):
- Fix (mechanism) · sequence? code?:
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
