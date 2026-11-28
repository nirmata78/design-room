# Runbook · practice (learning) session

Read [`README.md`](README.md) first, then `CLAUDE.md` §16. This file is the order of events.

A practice round is a full round with a coach. **No clock**, help on purpose, and the candidate
still does the reasoning. The numbers are varied here too — practising on the solution's figures
teaches the figures, not the method.

---

## Step 1 · Setup

1. Read `CLAUDE.md`, `guides/interviewer-guide.md`, `levels.md`, `profile.md`.
2. Generate the card:
   ```bash
   scripts/scenario.py new SD-nn --session practice --mode full --difficulty standard
   ```
   (`--difficulty gentle` gives every fact precisely and drops the curveball — use it for a first
   attempt at an archetype.)
3. Read the cue sheet section. Find the reference solution's stages:
   `ls solutions/ | grep SD-nn` then `grep -n '^# Stage\|^## ' <file>`. **Do not read it yet.**
4. `interview.md` from the template; §0 with `Session: practice`, help dial, `Numbers: varied · seed N`.
5. Frame per `CLAUDE.md` §16.1, read the card's prompt verbatim, write it into §0.
6. Log `date +%H:%M:%S` as `START`.

## Step 2 · Each phase

For each phase, in order (P1 → P5):

1. Read **only that phase's stage** of the reference solution (`Read` with offset/limit).
2. Decide the one or two things this phase must produce: the cue-sheet items that matter, and the
   **one number that drives a decision**. Compute that number **with the card's figures**, not the
   reference's. Write it in §10 as `KEY: …` so you can check their work.
3. Send the two-channel message (`CLAUDE.md` §16.2):

```
**Interviewer:** <the probe, clean: no components they have not named, no praise, one question>

**Coach:**
- *Testing:* <what the probe is after>
- *Hint:* <a consideration, or a choice between two named options>
- *Scaffold:* <a stem with ___ blanks — every number and every "why" is a blank>
- *Your move:* <what to write, and where: "§2, three rows">
```

4. When they answer, coach for real: right and why · wrong and why · the one thing a strong answer
   adds. Check the arithmetic properly against your `KEY`. One correction round, then move on.
5. Log independence: **U** unaided · **H** hint · **S** scaffold · **W** worked (`show me`).
6. Fade the help: two U/H steps in a row → one level less help, and say so. Two stuck steps → one
   level more.

### Scaffolds with varied numbers — examples

The reference solution says *"2M applications a month, 10× Saturday peak ≈ 8/s, so one relational
primary is plenty"*. The card says 20M and 30×. The scaffold is:

> `avg = ___ applications ÷ ___ seconds per month = ___/s · peak = avg × ___ = ___/s → one primary
> can / cannot absorb that because ___ → so the store is ___`

Not: *"20M a month is about 8 a second on average and 230 at peak, so one primary is still fine."*
That is the worked answer; it is `show me` only.

**If the varied scale changes the reference's conclusion**, the coach says so as a question, never as
the answer: *"The reference design was sized for a tenth of this. Which of its decisions would you
re-check?"*

### Using the reference without leaking its numbers

| The reference has | The coach uses |
|---|---|
| A figure (8/s, $2M/month, 40 TB) | The **unit chain** that produced it, as a scaffold with blanks |
| A conclusion ("one primary is enough") | A **decision to make**, with the threshold as a question |
| A named mechanism (outbox, saga, breaker) | Two options to choose between, in the coach channel only |
| A diagram | A skeleton with half the boxes, labels blank |

## Step 3 · Curveball, wrap, summary

Even with no clock: throw the card's curveball (coached), run the wrap and the four-sentence summary.
These are the parts that get practised least.

## Step 4 · Debrief and archive

`CLAUDE.md` §16.6 then §12, plus README §7. In the report's *Next*, name the reference stages to
re-read — and suggest a certifying `blitz` of the **same question no sooner than three days later**,
which will draw different numbers.
