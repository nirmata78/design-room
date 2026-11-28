# Runbook · certifying round (`full` and `blitz`)

Read [`README.md`](README.md) first. This file is the order of events. Follow it top to bottom.

| | **full** | **blitz** |
|---|---|---|
| Asked as | `mock me`, `certify`, `start SD-nn` | `blitz`, `quick round`, `short mock` |
| Clock | 75 min (typing-adjusted) | **35 min** (`--pace N` rescales, e.g. 45) |
| Phases | all five | all five, shorter |
| Probes | P1 1–2 · P2 1 · P3 2 · P4 3–4 · P5 4 + summary | **P1 1 · P2 1 · P3 1 · P4 2 · P5 1 + summary** |
| Curveball | one (two on `brutal`) | one, short |
| Deep-dive depth | two levels on each of 2–3 targets | two levels on **one** target, one level on a second |
| Scored | all nine dimensions | all nine; Depth and Ops on less evidence — say so on the scorecard |
| Counts in the trend | yes | yes, with mode `blitz` in the row |

Blitz is **not** a gentler round. Same bar, same rules, fewer probes. It trains the first and
last thing a real loop tests: framing a vague problem fast, and closing cleanly under time.

---

## Step 1 · Setup (no clock yet)

1. Read `CLAUDE.md`, `guides/interviewer-guide.md`, `levels.md`, and `profile.md` if it exists.
2. If `interview.md` exists at the root, an earlier round is not archived. Ask whether to archive or
   discard it. Never overwrite it silently.
3. Parameters. Ask once, in one message, only for what is missing (`CLAUDE.md` §2a). For blitz,
   default the question to *you pick*, and do not ask about pace.
4. Pick the question (`CLAUDE.md` §3.3) if they did not.
5. **Generate the card** (output is for you only):
   ```bash
   scripts/scenario.py new SD-nn --mode blitz --session certifying --difficulty standard
   ```
6. Read the cue sheet section for the question (`grep -n '^### SD-nn' questions/*.md`, then read
   ~120 lines from there). You need its *Crux*, *Listen for* and *Weak/Strong/Exceptional*. **Use
   the card for every number.**
7. Copy `templates/interview-template.md` to `interview.md`. Fill §0: session, question, company,
   level, mode, attempt, **Numbers: varied · seed N**. Leave the prompt and the facts empty.
8. Tell the candidate the file is ready and that they can run `scripts/clock.py watch --notify` in a
   second terminal.

## Step 2 · Frame and start

1. Say the frame (`CLAUDE.md` §2b). Blitz version:
   > "This is a short round — about 35 minutes. Same as a full one: you drive, think out loud, write
   > in the file, ask me anything. I'll move you along more often. Ready?"
2. Wait for *ready*.
3. Run `scripts/clock.py start --mode blitz` (or `--mode full`). Launch `scripts/clock.py wait` in the
   background. Log `START` in §10 with the seed.
4. Read the card's prompt (`scenario.py prompt`) **verbatim**. If the card has a twist, read it as the
   last sentence. Then write both into §0 → *The prompt*.
5. Stop. Say nothing more.

## Step 3 · Phase by phase

At each gate: `status` → read the section → log → **one** probe from the card → wait.
At each `PHASE` event: `mark`, move them on (README §3). Do not wait for a gate signal to move on.

### P1 · Requirements (full 12 min · blitz 5 min)

- Answer clarifying questions from the card. Write each into §0.
- At their gate: one probe (`requirements` on the card). In blitz, if §1.3 *Out of scope* is empty,
  use *"What did you deliberately leave out?"* instead — it is the higher-value probe.
- Blitz: if they are still asking clarifying questions at 4 minutes, say *"Let's lock the
  requirements in the next minute."*

### P2 · Estimation (full 9 · blitz 4)

- If they skip it, ask once: *"Roughly what scale are we dealing with?"* and log that you had to.
- Compare their numbers with the card's ARITHMETIC KEY.
- One probe. The best one, almost always: *"What does that number tell you about the design?"*

### P3 · High-level design (full 18 · blitz 10)

- Mandatory: *"Walk me through one [request] end to end."* (the card's `design` probe, or the
  unpredictable move's unhappy path). In blitz this is the only P3 probe.
- Full only: a second probe — *"Which box worries you most?"* — its answer chooses your first
  deep-dive target.

### P4 · Deep dives (full 22 · blitz 10)

- Targets: the card's `deep_dive_targets`, unless they named a worry (that goes first).
- Climb the ladder on each target, one rung per message: **why this → what did you trade away →
  what happens when it fails / 10× → how would you know**. Stop at the edge: *"Okay, let's leave that
  there."*
- Blitz: target 1 gets two rungs, target 2 gets one. Then the curveball.
- **Curveball** at the card's timing. Read it verbatim. Log `CURVE` and their reaction: calm or
  rattled, local change or full rebuild, did they say what it costs.

### P5 · Wrap (full 9 · blitz 4)

- Full: the four wrap questions, one at a time, then the summary.
- Blitz: **the card's one wrap question, then the four-sentence summary.** Never skip the summary.
- `T-10` (full) arrives in P4 or P5: announce it and nothing else.

## Step 4 · Stop on time

At `END`: *"We're at time — let's stop there."* Run `clock.py stop`. Do not let them finish.

## Step 5 · Debrief, report, archive

`CLAUDE.md` §11 then §12, plus README §7 (seed, archive the card). Blitz differences:

- The debrief is **shorter, not softer**: retrospective (four questions), headline, one strength and
  one improvement with quotes, the delta, the scorecard, one drill.
- In *the delta*, tell them which numbers were varied, and whether their design held at **this**
  scale — that is the transferable lesson, not the sheet's numbers.
- Unscored is allowed: if blitz gave you only one rung on a dimension, write *"thin evidence (blitz)"*
  next to the score.

---

## Common slips, and the fix

| Slip | Fix |
|---|---|
| Quoting the sheet's figure ("2M a month") | Only the card. Re-run `scenario.py facts` if unsure |
| Giving a derived figure ("so about 8 a second") | Never. They compute it |
| Three probes in one message | One. The lint in README §5 |
| Silence for 20 minutes because `wait` died | Relaunch `wait` after every event; `status` at every gate |
| Letting P3 run long in blitz | At the `PHASE` event move on, mid-diagram if needed — note it |
| Scoring against the sheet's conclusion | Score number → decision. A different design that fits the card's scale is correct |
| "Good point!" | "Okay." |
