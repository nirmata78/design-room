# design-room

**A system-design interviewer that will not help you.**

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://nirmata78.github.io/design-room/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![62 questions](https://img.shields.io/badge/questions-62-orange)
![Runs on Claude Code](https://img.shields.io/badge/runs%20on-Claude%20Code-8A2BE2)

`design-room` is a **Claude-Code-driven mock interview** for senior, staff and Engineering-Manager
system-design loops. Claude plays a FAANG interviewer, holds the clock, probes your
decisions, and scores you against a nine-dimension rubric. You design in `interview.md` and talk to it
in chat.

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
Mock me: SD-08, Google, L6, full round, brutal.
Surprise me — pick my weakest archetype.
15-minute framing drill, three questions back to back.
```

**Optional — tell it who you are.** Copy `profile.example.md` to `profile.md` and fill it in: target
companies and level, your home domain (it probes you *harder* there), and any confidentiality rules
about your employer. `profile.md` is gitignored and never leaves your machine.

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
   "how did that go?"              ◀────      asks YOU first, then the debrief
                                              writes the scorecard, archives the session
```

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

## 5 · The question bank — 62 questions

[`Question-Bank.md`](Question-Bank.md) is the index. Eight archetypes, 29 with full cue sheets (crux,
clarification numbers, checklist, phase-by-phase probes, curveball, weak/strong/exceptional, traps) and
33 compact ones, all runnable.

| | Archetype | Qs | The recurring test |
|---|---|:-:|---|
| **A** | Ingest, streaming & real-time analytics | 7 | Durable buffer, event time, approximate vs exact |
| **B** | Social, feed & content | 7 | Fan-out — pay at write or read, and the outlier |
| **C** | Storage, data & consistency | 9 | Honesty about consistency |
| **D** | Infrastructure & control planes | 12 | Control plane vs data plane |
| **E** | Search, geo & ML | 8 | Precomputation under a latency budget |
| **F** | Transactions, payments & commerce | 7 | Correctness under retry and partial failure |
| **G** | Media & delivery | 4 | Moving bytes cheaply — egress dominates |
| **H** | **EM-specific rounds** | 8 | Reviewing, sequencing, budgeting, SLOs, splitting work |

**Archetype H is the one to not skip.** It holds the rounds that aren't "design X": critique someone
else's design, sequence an eighteen-month migration, take 30% out of an infrastructure bill, fix a
service with 1,200 alerts and an exhausted team, split a system across five teams. Four of them are
**inverted** — Claude presents an artifact (a design doc, a bill, an incident timeline) with planted
defects, and you review it. An L6 EM loop very often contains one of these, sometimes disguised as a
normal design round that turns into a review halfway through.

**Company flagships**, if a loop is close:

| Company | Run these first |
|---|---|
| **Google L6 EM** | SD-15 global KV · SD-36 crawler · SD-02 top-K · SD-25 rate limiter · SD-19 collaborative editing · SD-32 CI/CD · **SD-58 SLOs · SD-59 team split** |
| **Meta E6 EM** | SD-08 feed · SD-09 messaging · SD-20 cache · SD-41 recommendations · SD-10 live comments |
| **Amazon L6/L7** | SD-48 inventory · SD-44 ledger · SD-47 booking · SD-28 workflows · SD-56 migration · SD-57 cost · SD-61 incident |
| **Microsoft** | SD-23 multi-tenancy · SD-19 collaborative editing · SD-09 messaging · SD-34 secrets · SD-59 team split |
| **Netflix** | SD-51 video · SD-52 live · SD-41 recommendations · SD-35 rollout · SD-57 cost |

**No loop yet?** Go for coverage — one round in each of A–H teaches more than eight rounds in the two
archetypes that feel comfortable.

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
9. **Leadership signal (EM)**

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
├── Question-Bank.md         index of all 62 questions
├── questions/
│   ├── A-streaming-analytics.md           SD-01…07
│   ├── B-social-feed-content.md           SD-08…14
│   ├── C-storage-data-consistency.md      SD-15…23
│   ├── D-infrastructure-control-planes.md SD-24…35
│   ├── E-search-geo-ml.md                 SD-36…43
│   ├── F-transactions-payments.md         SD-44…50
│   ├── G-media-delivery.md                SD-51…54
│   └── H-em-specific-rounds.md            SD-55…62  ← includes the inverted rounds + answer keys
├── templates/
│   └── interview-template.md   copied to ./interview.md at session start
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
└── sessions/                archived rounds: interview.md + scorecard.md + debrief.md
```

**Your rounds stay private.** `profile.md`, `Progress-Log.md`, `interview.md` and everything under
`sessions/` are in `.gitignore`. If you fork this repository, your scores and designs will not be
pushed with it.

**Don't read `questions/*.md` before a round.** They contain the answer — the checklist, the probe
ladder, the model design, and for archetype H the planted-defect keys. Reading the sheet turns a mock
into a recital. Read them *after*, at debrief, when Claude walks you through what you missed.

---

## 8 · The loop that builds skill

1. **Run a round.** Any mode. Don't pick the question yourself once you've done a few — `surprise me`
   reads `Progress-Log.md` and picks your weakest archetype.
2. **Take the debrief seriously**, especially step 1 where it asks how *you* think it went before saying
   anything. Being able to grade yourself accurately is most of what separates people who improve from
   people who plateau.
3. **Do the one drill.** Exactly one thing, small enough to do this week. It's logged; if the same drill
   appears three times undone, it was too big — ask for a smaller one.
4. **Study the gap, not the question.** If depth on consistency was the weakness, read about
   consistency — not the model answer to the question you just did.
5. **Re-run cold, weeks later.** Not the next day.

**Cadence that works four weeks out:** week 1 coverage (one round per archetype, A–H) · week 2 depth
(re-run the two weakest, `deep-dive` mode) · week 3 reps (daily `framing` drill + two `full` rounds at
`brutal`) · week 4 full `loop`s with company calibration.

**If you have one week:** the `framing` drill daily, plus two `full` rounds, plus one archetype-H round.

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
