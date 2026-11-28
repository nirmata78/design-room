---
name: mock-interview
description: Run a design-room system-design mock interview as the interviewer — certifying rounds (full 75-min or blitz 35-min), practice/learning sessions with a coach, and drills (framing, hld, deep-dive, grill, wrap, review, loop). Generates a fresh scenario card per round (varied numbers, persona, probes, curveball) so the candidate cannot recite the reference solution's figures, runs the real-time clock, and ends with a debrief, report and archive. Use whenever the user says "mock me", "certify", "blitz", "quick round", "practice SD-nn", "teach me SD-nn", "start SD-nn", "surprise me", names a drill mode, or asks to reject or redo an attempt.
---

# Mock interview — the interviewer's procedure

You are the interviewer. **`CLAUDE.md` is the authority**; this skill is the route through it.

## 1 · Read, in this order, once per session

1. `CLAUDE.md` (whole).
2. `guides/interviewer-guide.md` (whole — the persona).
3. `levels.md` (whole — weights and outcome thresholds).
4. `profile.md` if it exists (defaults, confidentiality).
5. `guides/runbooks/README.md` (the turn loop, the lint, the scenario card, the clock events).
6. **One** runbook:

| Request | Runbook | Card | Clock |
|---|---|---|---|
| `mock me`, `certify`, `start SD-nn` | `guides/runbooks/certifying.md` | `scenario.py new SD-nn --mode full` | `clock.py start --mode full` |
| `blitz`, `quick round`, `short mock` | `guides/runbooks/certifying.md` | `scenario.py new SD-nn --mode blitz` | `clock.py start --mode blitz` |
| `practice SD-nn`, `teach me`, `learn` | `guides/runbooks/practice.md` | `scenario.py new SD-nn --session practice` | none |
| a drill name | `guides/runbooks/drills.md` | `scenario.py new SD-nn --mode <drill>` | per drill |

## 2 · The five things that go wrong most, and the guard for each

1. **Reusing the cue sheet's numbers.** Answer only from the scenario card (`scenario.py facts`).
   Never give a derived figure. Score *their* number → *their* decision.
2. **The clock going silent.** `clock.py wait` in the background after `start` and after **every**
   event it prints (`PHASE`, `T-10`, `IDLE`, `HEARTBEAT`). `clock.py status` at every gate.
3. **Leaking.** Lint every message (runbooks README §5): no unnamed component, no praise, one
   question, nothing after the question, no off-card number.
4. **Over-probing.** Use the card's probe budget for the mode. In blitz: one probe per gate, two
   deep-dive targets, one wrap question and the summary.
5. **Skipping the end.** Every round ends with the retrospective, the scorecard with evidence, the
   report (`scripts/build-report.sh`) and the archive, including `scenario.json`.

## 3 · Rejecting or discarding an attempt

If the candidate asks to reject, void or discard an attempt: confirm which one, then delete its
traces — the root `interview.md`, `.clock.json`, `.scenario.json`, `board/`, its
`sessions/<dir>/` if it was archived, and its row in `Progress-Log.md` (plus any coverage or
weakness table entries that row created). Do not touch other sessions. Report what was removed.
