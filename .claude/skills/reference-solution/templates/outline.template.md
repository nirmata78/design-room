# SD-NN · <Question> — reference-solution outline (six-chapter, C4-first format)

Target level: staff (manager layer as one recap row) · Target length: __ min (40–60) · Word budget: __ (5,500–7,500)
Worked example: `solutions/SD-03-ad-click-aggregation/video/OUTLINE.md`. Format: `.claude/skills/reference-solution/GUIDELINES.md`.

## Thesis and hook

- **Thesis** (one sentence, key-line voice):
- **Hook** (why it is harder than it looks, as one picture):

## Scale line (GUIDELINES §3.1)

Volume per month: · Total over the retention period: · Peak and its cause:
(every number below names which of these it starts from)

## 1 · Prompt, clarifying Q&A and C4 context

- **What this question grades** (weak · strong): Requirements · Correctness · Trade-offs · Depth · Operations
- **Clarifying questions** (4–6) and the interviewer's answers, each with what it moves in the design:
- **FR1 …** :
- **NFRs** with numbers (initial targets):
- **Properties** — safety `S1-<slug>` …, liveness `L1-<slug>` …:
- **IN / OUT** of scope:
- **C4 context (L1)**: actors and external systems; which boundaries are `[HTTPS]`, which `[Event]` / `[Batch]`:
- **The core is N things**:

## 2 · Back-of-the-envelope

| Number | From (scale line) | Arithmetic | Label | The constraint it forces (rules out · requires) |
|---|---|---|---|---|

Budget bar (latency or freshness): stages and the spare.

## 3 · API contracts and the data model

| Endpoint / event | Serves | Idempotency key · status codes | What the response says |
|---|---|---|---|

Physical tables (key, partition key, indexes), in build order: · Lifecycle (state machine), if the core entity has one:

## 4 · The design, driven by challenges

**V1** (the C4 container view, technologies on the boxes): the boxes, and why this is the simplest correct design:
Happy-path flow on V1 (numbered arrows):
Technology cards shown with V1 (from `stack.json`):

### Challenges

Each: the interviewer's question · the case (trace) · the break (container view or component zoom, `views.json` key) · the
mechanism (property protected → how → rules out → costs) · the fix one level down (what is written, what it covers and does not,
why this tool and not the one under it) · the Rejected line · the version it produces (V2, V3 … or "zoom only") · the push and the
second fix · "if asked, I'd say" · the bridge to the next.

#### Challenge 1 · <title>
#### Challenge 2 · <title>
#### Challenge 3 · <title>
#### Challenge 4 · <title>
#### Challenge 5 · <title>
#### Challenge 6 · How would you know it is broken?   (observability, always last)

## 5 · When you don't need all this

The simpler design (its own view, ALTERNATE) · what it gives up · the crossover number from chapter 2:

## 6 · Recap

Final view badges (alias → mechanism) · the mistakes table · follow-up questions with where each is answered · the close:

## C4 plan (`workspace.dsl` + `views.json`)

| View key | From | Overlays | Used on |
|---|---|---|---|
| c4-context | exported | steps | ch1 |
| containers | exported (master, `video: false`) | — | — |
| v1, flow-v1, v2 … | containers | hide / new / flow / breaks | ch4 |
| comp-<container> | exported (grid, grouped steps) | — | ch4, the first time a challenge enters it |
| <zoom keys> | comp-<container> | keep + breaks / fix (rest dimmed) | ch4, via zoom() |
| recap | containers | badges | ch6 |
| alt | exported | alternate | ch5 |

## Canon check

| Point the standard treatments make | Covered where (slide) / dismissed why |
|---|---|

## Budget

| Chapter | Minutes | Words | Logical slides |
|---|---|---|---|
| 1 · Prompt + context | 4–6 | | |
| 2 · Estimates | 4–5 | | |
| 3 · API + data | 4–5 | | |
| 4 · Design + challenges | 22–32 | | |
| 5 · Alternate | 2–3 | | |
| 6 · Recap | 3–4 | | |
