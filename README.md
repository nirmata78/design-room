# design-room

**A system-design interviewer that will not help you.**

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://nirmata78.github.io/design-room/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![92 questions](https://img.shields.io/badge/questions-92-orange)
![6 levels](https://img.shields.io/badge/levels-Senior%20→%20Director-blue)
![Runs on Claude Code](https://img.shields.io/badge/runs%20on-Claude%20Code-8A2BE2)

`design-room` is a **Claude-Code-driven mock interview** for system-design loops from Senior and
Staff Engineer to Engineering Manager and Director. Claude plays the interviewer, holds the clock,
probes your decisions and scores you against a nine-dimension rubric **weighted for your target
level**. You design in `interview.md` and talk to it in chat. **Every attempt ends in a PDF report**:
scorecard with evidence, a retrospective, feedback, the delta against a strong answer, and your trend
over time.

It is not a chatbot that explains system design to you. It is a room with a stranger in it who will not
help, will not praise you, and will stop on time. **That is the point** — the failure modes it trains
away (not scoping, not managing the clock, not going deep, not talking about operations or cost) are
behavioural, and they only surface under those conditions.

---

## 1 · Start a session

You need [Claude Code](https://docs.claude.com/en/docs/claude-code/overview). Nothing else — no
install, no dependencies, no API key beyond the one Claude Code already uses.

```bash
git clone https://github.com/nirmata78/design-room.git
cd design-room
claude
```

Then say:

```
Run a system design mock.
```

That is the whole invocation. `CLAUDE.md` at the repository root is loaded automatically: it is the
interviewer's operating manual. Claude asks you the six setup questions once, creates `interview.md`
from the template, starts a real clock, and reads you a problem.

**To skip the setup questions**, specify what you want:

```
Mock me: SD-08, Google, em, full round, brutal.
Mock me as staff on something fintech.
Director round — surprise me.
Surprise me — pick my weakest archetype.
15-minute framing drill, three questions back to back.
```

**Optional — tell it who you are.** Copy `profile.example.md` to `profile.md` and fill it in: target
companies, track and level, target domains, your home domain (it probes you *harder* there), and any
confidentiality rules about your employer. `profile.md` is gitignored and never leaves your machine.

> **No Claude Code?** [`prompts/`](prompts/README.md) has a paste-into-any-chat version. It has no
> clock, no workspace and no memory between rounds, so it is a much weaker simulation — but it works
> anywhere.

---

## 2 · How a round actually goes

```
   YOU                                        CLAUDE (interviewer)
   ───                                        ────────────────────
                                              reads the prompt aloud, once
                                              starts the clock (real: `date`)
   write §1 Requirements in interview.md
   "requirements are up"            ────▶     reads §1 only, asks ONE probe
   answer in chat                              ◀──── "what did you deliberately leave out?"
   write §2 Estimation
   "done"                          ────▶      reads §2, probes the number
   ...                                        moves you on when a phase overruns
   write §4 the diagram
   "take a look"                   ────▶      "walk me through one request end to end"
   ...                                        deep dives: 3–4 probes, one curveball
   §8 four-sentence summary        ────▶      stops on time
                                              ─── drops the persona ───
   "how did that go?"              ◀────      retrospective: asks YOU first (4 questions)
                                              then feedback, the delta, the scorecard
   Start · Stop · Continue         ◀───▶      agreed together
                                              writes report.md → report.pdf, logs the round
```

### Every attempt ends in a report

When the debrief ends, Claude writes `sessions/<date>-SD-nn-slug/report.md` and renders it to
**`report.pdf`** with `scripts/build-report.sh` (pandoc plus any Chromium-family browser, WeasyPrint
or LaTeX). Three to five pages:

| Section | What's in it |
|---|---|
| **Verdict** | outcome at your target level, weighted score, apparent level, time outcome, help needed |
| **Scorecard** | nine dimensions × weight × score × evidence (a quote or a timestamp for every score) |
| **Where the time went** | budget vs actual per phase, hint rungs used |
| **Retrospective** | your own read (asked before any feedback), the interviewer's read, the **calibration gap** between them, Start · Stop · Continue |
| **Feedback** | two strengths and two improvements, each anchored to a moment |
| **The delta** | what a strong answer had that yours didn't (ranked by how much it mattered), what you raised beyond the sheet, the model design in brief |
| **Trend** | your previous rounds from `Progress-Log.md` — what's moving, what's stuck |
| **Next** | the one drill, what to study, the next recommended question |
| **Self-audit** | where the interviewer leaked or under-probed, so you know how far to trust the scores |

**See one:** [`examples/sample-report.pdf`](examples/sample-report.pdf) — a fictional Staff-level
fintech round ([source](examples/sample-report.md)).

Reports live under `sessions/`, which is **gitignored** (and so is every `*.pdf`). Re-render any time
with `report` in chat, or `scripts/build-report.sh --all`.

**Your side of the contract:** write in §1–§9 of `interview.md`, and say something in chat when you want
it looked at. Rough and fast beats neat and slow — nobody scores your ASCII art. Most of your reasoning
happens in chat, not in the file.

**Its side:** it reads only the sections the current phase covers, writes only to §10, asks one question
at a time, and does not help you.

### What it will not do

It won't name a component you haven't named, tell you whether an answer is right, say "good", complete
your diagram, or fill a silence. If you ask *"should I use Kafka here?"* you'll get *"which would you
pick, and why?"* All the teaching is held back for the debrief, where it's worth ten times more.

If you want it to teach mid-round, say **`coach mode`** — it breaks character, the clock stops, and the
round stops being scoreable. That's a deliberate trade, not a failure.

---

## 3 · Talking to it

| Say | What happens |
|---|---|
| `done` · `ready` · `look at §2` | Gate: it checks the clock, reads that section, probes |
| `time?` | Elapsed and remaining in this phase. Nothing else |
| `stuck` · `hint` | The hint ladder, starting at the weakest rung — and it records which rung you needed |
| `repeat the prompt` | Verbatim, no additions |
| `assume 50M users` | Accepted and written into §0 as an established fact for the round |
| `harder` · `easier` | Shifts the difficulty dial mid-round |
| `curveball` | Ask for one now, if you want the practice |
| `skip estimation` | Allowed — and it'll cost you at debrief |
| `pause` / `resume` | Stops and restarts the clock, excluding the gap |
| `debrief` · `stop` | Ends the round now and goes straight to feedback |
| `as staff` · `level director` · `domain crypto` | Sets the level or the domain filter for the session |
| `report` | Re-renders the latest session's PDF |
| `history` · `how am I doing?` | Trend by level, coverage gaps, standing weaknesses, drills not done |
| `coach mode` | Breaks character to teach. Round becomes unscoreable |

---

## 4 · The modes

| Mode | Time | Use it when |
|---|---|---|
| **full** | 75 min | The real thing. Full scorecard. Default |
| **framing** | 15 min | **The best value-per-minute drill.** Three prompts, scope + estimate only, no design. Trains the #1 failure mode |
| **hld** | 30 min | Through the diagram, stop before deep dives |
| **deep-dive** | untimed | One component, drilled to the bone |
| **grill** | untimed | Adversarial probing on a design you already have. 8+ probes, no mercy |
| **wrap** | 12 min | Failure modes, SLOs, cost and the four-sentence summary — the EM-bar phase alone |
| **review** | 20 min | **Inverted:** Claude presents a design, you critique it. Tests the skill an EM uses weekly |
| **loop** | — | Two or three rounds back to back with a cross-round pattern note |

If you have twenty minutes, run `framing`. If you have one hour, run `full`. If you have a loop next
week, run `loop` with the company's flagship questions.

---

## 5 · The question bank — 92 questions, sliced four ways

[`Question-Bank.md`](Question-Bank.md) is the index. **40 full cue sheets** (crux, clarification
numbers, checklist, phase-by-phase probes, curveball, weak/strong/exceptional, traps) and **52 compact
ones**, all runnable. Every question carries four tags:

- **Archetype** (A–K) — the technical family, i.e. what the round really tests.
- **Kind** — **Build** (design X) · **Review** (inverted: you critique an artifact with planted defects)
  · **Strategy** (decide, sequence, invest). Senior loops contain more Review and Strategy.
- **Domain** — `general` · `fintech` · `crypto` · `ai` · `social` · `commerce` · `media` · `search` ·
  `mobility` · `saas` · `infra` · `data`.
- **Levels** — where the question is most revealing: Senior · Staff · Principal · EM · Senior EM · Director.

| | Archetype | Qs | The recurring test |
|---|---|:-:|---|
| **A** | Ingest, streaming & real-time analytics | 7 | Durable buffer, event time, approximate vs exact |
| **B** | Social, feed & content | 7 | Fan-out — pay at write or read, and the outlier |
| **C** | Storage, data & consistency | 9 | Honesty about consistency |
| **D** | Infrastructure & control planes | 12 | Control plane vs data plane |
| **E** | Search, geo & ML | 8 | Precomputation under a latency budget |
| **F** | Transactions, payments & commerce — **incl. fintech** | 13 | Correctness under retry and partial failure; you are not the only ledger |
| **G** | Media & delivery | 4 | Moving bytes cheaply — egress dominates |
| **H** | **EM & senior-manager rounds** | 12 | Reviewing, sequencing, budgeting, SLOs, splitting work, org design |
| **I** | **AI & LLM systems** | 8 | Expensive, non-deterministic components; evaluation without ground truth |
| **J** | **Crypto & digital assets** | 6 | Irreversible value, key custody, chain reorganisations |
| **K** | **Staff+ technical-leadership rounds** | 6 | Strategy, API review, deprecation, diagnosis, arbitration — without authority |

**Archetypes H and K are the ones not to skip.** They hold the rounds that aren't "design X":
critique someone else's design or API, sequence an eighteen-month migration, take 30% out of an
infrastructure bill, find a p99 regression from dashboards, write a three-year technical strategy,
shape an org for a new product line. Six of them are **inverted** — Claude presents an artifact with
planted defects and you review it. Senior loops very often contain one of these, sometimes disguised
as a normal design round that turns into a review halfway through. **H is the manager track, K the
Staff+ IC track.**

**Company flagships**, if a loop is close — full table in the bank:

| Company class | Run these first |
|---|---|
| **Google** | SD-15 global KV · SD-36 crawler · SD-25 rate limiter · SD-19 collaborative editing · **SD-58 SLOs · SD-59 team split** (EM) · **SD-84 API review · SD-87 p99 hunt** (Staff) |
| **Meta** | SD-08 feed · SD-09 messaging · SD-20 cache · SD-41 recommendations · SD-68 moderation |
| **Amazon** | SD-48 inventory · SD-44 ledger · SD-47 booking · SD-28 workflows · SD-57 cost · SD-90 reliability program |
| **Fintech** | SD-44 ledger · SD-77 card authorisation · SD-79 reconciliation · SD-81 payouts · SD-80 FX |
| **Crypto** | SD-71 matching engine · SD-72 custody · SD-73 deposits & reorgs · SD-75 liquidations |
| **AI labs / platforms** | SD-42 inference · SD-63 LLM gateway · SD-64 agent platform · SD-66 GPU training |
| **Director loops** | SD-89 new product-line org · SD-91 annual planning · SD-92 cloud strategy · SD-62 build vs buy |

**No loop yet?** Go for coverage — one round in each archetype teaches more than ten rounds in the two
that feel comfortable.

### Levels — Staff Engineer is not the same round as Engineering Manager

| Track | Levels | The panel is asking… |
|---|---|---|
| **IC** | `senior` · `staff` · `principal` | Can they make the hardest technical calls — and go deep enough to be trusted with them? |
| **Manager** | `em` · `senior-em` · `director` | Can they own systems, operations, cost and the teams that run them — and, higher up, the portfolio? |

The same diagram can pass at one and fail at the other. So the interviewer changes **manner** by level
(who picks the deep dives, how vague the prompt is, what the curveball is) and the report **weights**
the nine dimensions by level — technical depth and trade-offs weigh most for Staff; operations and
leadership for EM; framing, cost and org/investment decisions for Director. Full ladder, weights and
outcome thresholds: [`levels.md`](levels.md). **Default: `em`.**

---

## 6 · Scoring

Nine dimensions, 1–4. **1** below bar · **2** approaching · **3** at bar (hire) · **4** above bar.
A strong round is mostly 3s with a couple of 2s and 4s.

1. Requirements & scoping
2. Estimation — did a number *change a decision*
3. High-level design
4. Technical depth — two levels deep when probed
5. Trade-off reasoning
6. **Operations, reliability & cost — the manager bar**
7. Communication & collaboration
8. Handling ambiguity & pushback
9. **Leadership signal** — *technical* leadership on the IC track, *org and delivery* on the manager track

Each score is against your **target level's** bar; the report combines them into a **weighted score**
using that level's weights and maps it to an outcome (strong hire · hire · lean no · no hire), plus an
**apparent level** — e.g. *"staff-level depth, senior-level framing"*.

Plus three things that often say more than the scores: **which hint rungs you needed**, **where the
time actually went**, and **how accurate your own self-assessment was.**

Every score comes with a quote or a timestamp. A dimension it never probed is left **unscored**, not
given a default. And it audits itself at the bottom of the sheet — leaks, missed probes, whether it
under-probed — because an inflated score is the one way this thing can actively hurt you.

Rubric: [`Scorecard-Template.md`](Scorecard-Template.md). It mirrors
[`guides/interviewer-guide.md`](guides/interviewer-guide.md) §7 — a guide written for a **human**
mock partner, even a non-technical one, with a printable grading sheet — so a peer running you
through it on paper scores you on the same axes.

---

## 7 · Files

```
design-room/
├── CLAUDE.md                the interviewer's operating manual — the engine. Read by Claude, not you
├── README.md                this file
├── Question-Bank.md         index of all 92 questions — by archetype, kind, domain and level
├── levels.md                six levels on two tracks: the bar, the weights, the outcome thresholds
├── questions/
│   ├── A-streaming-analytics.md           SD-01…07
│   ├── B-social-feed-content.md           SD-08…14
│   ├── C-storage-data-consistency.md      SD-15…23
│   ├── D-infrastructure-control-planes.md SD-24…35
│   ├── E-search-geo-ml.md                 SD-36…43
│   ├── F-transactions-payments.md         SD-44…50, SD-77…82 (fintech)
│   ├── G-media-delivery.md                SD-51…54
│   ├── H-em-specific-rounds.md            SD-55…62, SD-89…92 (senior EM / director)  ← inverted rounds + keys
│   ├── I-ai-llm-systems.md                SD-63…70
│   ├── J-crypto-digital-assets.md         SD-71…76
│   └── K-staff-technical-leadership.md    SD-83…88  ← inverted rounds + keys
├── templates/
│   ├── interview-template.md   copied to ./interview.md at session start
│   ├── report-template.md      the per-attempt report
│   └── report.css              its print styling
├── scripts/
│   └── build-report.sh      report.md → report.pdf
├── Scorecard-Template.md    the nine-dimension rubric
├── Cue-Sheet-Template.md    for running a prompt that isn't in the bank
├── Progress-Log.template.md copied to Progress-Log.md on first run
├── profile.example.md       copy to profile.md to calibrate the interviewer to you
├── guides/
│   ├── interviewer-guide.md the persona — also usable by a human mock partner
│   └── playbook.md          how to behave in the room; estimation number kit; phrasebook
├── prompts/                 paste-into-any-chat fallbacks (system design, behavioural, coding)
│
│   ── private, gitignored ──
├── profile.md               who you are and what you're targeting
├── Progress-Log.md          one row per round; drives "surprise me" and coverage tracking
├── interview.md             YOUR WORKSPACE — exists only during a session
└── sessions/                one directory per attempt: interview.md · scorecard.md · report.md · report.pdf
```

**Your rounds stay private.** `profile.md`, `Progress-Log.md`, `interview.md`, everything under
`sessions/` and every `*.pdf` are in `.gitignore`. If you fork this repository, your scores and designs will not be
pushed with it.

**Don't read `questions/*.md` before a round.** They contain the answer — the checklist, the probe
ladder, the model design, and for archetypes H and K the planted-defect keys. Reading the sheet turns a mock
into a recital. Read them *after*, at debrief, when Claude walks you through what you missed.

---

## 8 · The loop that builds skill

1. **Run a round.** Any mode. Don't pick the question yourself once you've done a few — `surprise me`
   reads `Progress-Log.md` and picks your weakest archetype.
2. **Take the retrospective seriously**, especially the first step where it asks how *you* think it went
   before saying anything — the report puts your read next to the evidence. Being able to grade yourself accurately is most of what separates people who improve from
   people who plateau.
3. **Do the one drill.** Exactly one thing, small enough to do this week. It's logged; if the same drill
   appears three times undone, it was too big — ask for a smaller one.
4. **Study the gap, not the question.** If depth on consistency was the weakness, read about
   consistency — not the model answer to the question you just did.
5. **Re-read the report before the next round** — the Next section names the question that loads your
   weak dimension.
6. **Re-run cold, weeks later.** Not the next day. The report's Trend section shows whether the habit
   changed.

**Cadence that works four weeks out:** week 1 coverage (one round per archetype relevant to your track — A–H for managers, A–G + I–K for Staff) · week 2 depth
(re-run the two weakest, `deep-dive` mode) · week 3 reps (daily `framing` drill + two `full` rounds at
`brutal`) · week 4 full `loop`s with company calibration.

**If you have one week:** the `framing` drill daily, plus two `full` rounds, plus one round from H (managers) or K (Staff+).

---

## 9 · Two things worth knowing

**Do it out loud where you can.** Typing a design and *narrating* one are different skills, and only
the second one transfers to the room. `pace: realtime` with the spoken answer in chat via voice is the
closest simulation; the default `typing-adjusted` (75 min instead of 50) exists so you're not penalised
for typing speed when working in the file.

**Your home turf is a risk.** If `profile.md` names a domain you work in professionally, the
interviewer probes you harder there and watches for the expert's failure mode: assuming the
interviewer shares your context and under-explaining. In a real loop the interviewer probably won't
be from your domain, and an expert who can't make a non-expert follow them scores badly on
Communication. Claude will ask you to define your own vocabulary. That's deliberate.

Also — session files persist. Nothing internal, confidential or identifiable goes into them; Claude is
instructed to generalise ("a large enterprise customer portfolio") rather than record real system
names, figures or ticket IDs — and the files are gitignored regardless.

---

## 10 · Contributing

New questions, sharper probes and better company calibration are all welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). The cue-sheet format is in
[`Cue-Sheet-Template.md`](Cue-Sheet-Template.md).

## License

[MIT](LICENSE).
