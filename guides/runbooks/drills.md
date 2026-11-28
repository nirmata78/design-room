# Runbook · drills (`framing`, `hld`, `deep-dive`, `grill`, `wrap`, `review`, `loop`)

Read [`README.md`](README.md) first. Every drill uses the scenario card for numbers:
`scripts/scenario.py new SD-nn --mode <drill>`. Setup, lint, logging and archive are as in the README.

| Drill | Clock | Card | Steps |
|---|---|---|---|
| **framing** | `--mode framing` (3 × 5 min) | one card per prompt: run `new` three times, three different questions | For each: read the card's prompt → answer clarifying questions from the card → at their gate, one probe: *"What does that number tell you about the design?"* → at the `PHASE` event, next prompt. No design. Score Requirements and Estimation only |
| **hld** | `--mode hld` (30 min) | `--mode hld` | P1–P3 as in `certifying.md`; stop at the end of P3. Mandatory walk-through. Score dimensions 1, 2, 3, 7 |
| **deep-dive** | off | `--mode deep-dive` (4 targets) | They state a design in §4. You climb the four-rung ladder on each card target until the edge. Log the rung where the edge was. Score 4 and 5 |
| **grill** | off | `--mode grill` (8 probes, persona skeptical) | Rapid probes on a finished design, each harder. No teaching, no hints. At least one challenge to a *correct* decision. Score 4, 5, 8 |
| **wrap** | `--mode wrap` (12 min) | `--mode wrap` | The four wrap questions, one at a time, then the four-sentence summary. Score 6 and 9 |
| **review** | `--mode review` (20 min) | `--mode review` | Present the cue sheet's *Weak* band as a design, with the card's numbers. They critique; you answer questions about it as its author would. Score 4, 5, 6, 9 |
| **loop** | per round | a new card per round | Two or three certifying rounds (`full` or `blitz`), different archetypes, one scorecard each, then one cross-round pattern note |

Numbers in a drill follow the same rule as a round: **only the card's figures**, and their derived
figures are theirs to compute.
