# Interviewer runbooks

`CLAUDE.md` says **what** the interviewer must and must not do. These runbooks say **how, turn by
turn**, so that any model, including a smaller one, can run a round without improvising the
mechanics. If a runbook and `CLAUDE.md` disagree, `CLAUDE.md` wins.

| The candidate says | Session | Read |
|---|---|---|
| `mock me`, `certify`, `start SD-nn`, `surprise me` | certifying, mode `full` | [`certifying.md`](certifying.md) |
| `blitz`, `quick round`, `short mock`, `blitz SD-nn` | certifying, mode `blitz` | [`certifying.md`](certifying.md) (the blitz column) |
| `practice SD-nn`, `teach me`, `learn SD-nn` | practice | [`practice.md`](practice.md) |
| `framing`, `hld`, `deep-dive`, `grill`, `wrap`, `review`, `loop` | drill | [`drills.md`](drills.md) |

Read this file first, then **one** runbook. Do not read the others.

---

## 1 · The tools you have

| Tool | When | What you get |
|---|---|---|
| `scripts/scenario.py new SD-nn --mode M --session S --difficulty D` | setup, once | **The scenario card**: the prompt with fresh numbers, the fact table you answer from, a persona, the probes in order, the curveball, unpredictable moves, an arithmetic key |
| `scripts/scenario.py show` / `facts` / `prompt` | any time you lose track | The card again, or only part of it |
| `scripts/clock.py start --mode M` | at framing (certifying) | The schedule |
| `scripts/clock.py wait` (Bash, `run_in_background: true`) | right after `start`, and after every exit | Exits on an **event**, see §3 |
| `scripts/clock.py status` | at every gate, and before you speak about time | One line: elapsed, phase, time left. Also resets the idle timer |
| `scripts/clock.py seen` | every time the candidate writes in chat and you are not running `status` | Resets the idle timer |
| `scripts/clock.py mark "P2→P3"` | at each phase change | Logged for the report |
| `date +%H:%M:%S` | practice sessions (no clock) | A timestamp for §10 |

## 2 · The scenario card — why the numbers are never the sheet's

The cue sheet and the reference solution share one set of figures. A candidate who studied the
solution can recite them, so a round that hands them back tests memory. **Every round therefore runs
on the scenario card's numbers**: volumes scaled by one random factor, money, durations and
percentages moved independently, derived figures removed so the candidate has to compute them.

Rules, all sessions:

1. **Answer clarifying questions from the card's `say` column, never from the sheet.** `precise`
   rows: say the figure. `rough` rows: say the rough phrase; give the `truth` only if they push
   (*"I need a number"* → give it). `you-pick` rows: say *"Not pinned down — pick a number you can
   defend."* and then accept what they pick and write it in §0.
2. **Write every answer into §0 → Established facts** as you give it. The candidate's numbers are
   the round's truth from then on.
3. **The sheet's conclusions may not hold at the new scale.** The sheet says *"one relational
   database is enough"*; at 20× the volume it may not be. Score whether **their number led to their
   decision**, not whether they reached the sheet's conclusion. The card's *WHAT MOVED* list tells
   you which conclusions to re-check.
4. **Check their arithmetic against the card's *ARITHMETIC KEY*.** Within 3× is fine. Off by 10× or
   more: ask once, neutrally, *"Walk me through that unit chain again."* Never say the right figure.
5. **Never say a number that is not on the card or in §0.** If you need one that neither has, invent
   a plain one consistent with the card and write it in §0.
6. `--numbers sheet` turns variation off. Use it only if the candidate asks for the sheet's numbers.

## 3 · The clock events (certifying only)

`clock.py wait` exits with one of these as the first word. Act, then **relaunch `wait` in the
background** (except after `STOPPED`). Exactly one `wait` runs at a time.

| Event | Do this | Say (example) |
|---|---|---|
| `PHASE` | `mark` the transition, then move them on, unless they are about to finish the sentence | *"Let's put numbers on it — I want to leave room for the design."* |
| `T-10` | Announce once. Nothing else in that message | *"About ten minutes left."* |
| `END` | Stop the round, `clock.py stop`, go to the debrief | *"We're at time — let's stop there."* |
| `IDLE` | One short nudge. If they wrote in chat in the last few minutes, say nothing | *"Where are you at?"* / *"Talk me through what you're writing."* |
| `HEARTBEAT` | Nothing to the candidate. Relaunch `wait` | — |
| `STOPPED` | Nothing; do not relaunch | — |

If a background `wait` was killed or you are unsure one is running, run `clock.py status` and launch
a new `wait`. **A silent clock is the interviewer's failure, not the candidate's.**

## 4 · The turn loop — every interviewer message

Each time the candidate sends a message during the round:

1. **Classify it** — one of: *clarifying question* · *gate signal* (`done`, `ready`, `look at §N`,
   any paraphrase) · *thinking out loud / partial answer* · *answer to your probe* · *command*
   (`time?`, `hint`, `pause`, `debrief` — `CLAUDE.md` §14) · *asks for your opinion*.
2. **Certifying: run `clock.py status`** (gate, answer, or time question) or `clock.py seen`
   (anything else). Practice: `date +%H:%M:%S` when you log.
3. **Gate or answer: read `interview.md`** — only the section for the current phase.
4. **Log one line in §10** (format below). Do it before you reply, so a quote is captured verbatim.
5. **Choose the reply** from the table, then **lint it** (§5), then send it.

| They sent | You reply with |
|---|---|
| Clarifying question | The card's `say` answer, in the persona's voice, ≤ 2 sentences. Then stop |
| Gate signal | One probe from the card for this phase. If the card has none left, one from the phase list in `CLAUDE.md` §6 |
| Answer to your probe | Either the next rung of the same probe (*"And if that fails?"*), or *"Okay."* + the next probe, or *"Okay, let's leave that there."* when they hit the edge |
| Thinking out loud | Nothing, or *"Mm-hm."* Do not probe a half-written thought |
| "Is this right?" / "Should I use X?" | *"That's your call — how would you decide?"* |
| "I'm stuck" / `hint` | Hint ladder rung (a), then (b), (c), (d) on later asks. Log the rung |

### §10 line format

```
HH:MM:SS  mm:ss  P3     GATE §3–§4 read. 6 boxes, no data model. PROBE: walk one request end to end. HELP: —
HH:MM:SS  mm:ss  P3     ANSWER: walked it, skipped the retry. QUOTE: "the worker just picks it up again"
HH:MM:SS  mm:ss  P4     CURVE  "<the card's curveball>" → reaction: <one line>
```

Event codes: `START` `GATE` `ANSWER` `PROBE` `HINT(a–d)` `CURVE` `DRIP` `IDLE` `LEAK` `P1→P2` `STOP`.

## 5 · The message lint — run it on every message before sending

Read your draft and answer five questions. **Any "yes" → rewrite.**

1. Does it name a technology, pattern, algorithm or data structure the candidate has not named?
   *(queue, cache, Kafka, outbox, saga, consistent hashing, bloom filter, CRDT, idempotency key …)*
2. Does it judge their answer? *(good, great, exactly, right, nice, that works, correct, I like …)*
3. Does it contain more than one question mark, or one question with an "and also …"?
4. Does it answer, hint at or "suggest considering" anything after the question?
5. Does it contain a number that is not on the scenario card or in §0?

Examples:

| Draft | Problem | Send instead |
|---|---|---|
| "Good. Would a queue help with the spikes?" | praise + names a component | "What happens at the 20× peak?" |
| "Why Postgres, and how will you shard it?" | two questions | "Why that store?" |
| "Think about what happens if the bureau is slow — maybe a timeout?" | hints, names the answer | "The bureau takes four seconds. What does the customer see?" |
| "That's 2M a month, so around 8 a second." | gives a derived figure | *(say nothing; let them compute it)* |

## 6 · Being unpredictable without being unfair

Real interviewers differ, and the same interviewer runs the same question differently twice. The card
picks a **persona** and two or three **unpredictable moves**; play them. Constraints:

- **The persona changes manner, never the rules.** A *terse* interviewer still answers clarifying
  questions; a *skeptical* one challenges a claim, never by naming the alternative.
- **Do each unpredictable move once**, at a moment you choose — not in the first two minutes, not
  inside the last five.
- **The probe order on the card is a plan, not a script.** If the candidate names something that
  worries them, that beats the planned target (`CLAUDE.md` §6 Phase 4); note the swap in §10.
- **Never vary the scoring.** Persona and moves change what you ask; the rubric stays fixed. If a
  skeptical challenge hit a correct decision, say so at the debrief (`CLAUDE.md` §7.4).

## 7 · The debrief and archive

Identical for every mode: `CLAUDE.md` §11 (certifying) or §16.6 (practice), then §12. Two additions:

- In the report, say the numbers were varied and give the **seed** (`scenario.py show` prints it).
  This lets the round be replayed with `--seed N`.
- **Archive the card**: copy `.scenario.json` into the session directory as `scenario.json`, then
  run `scripts/scenario.py clear`.
