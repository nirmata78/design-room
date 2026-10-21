---
title: "SD-79 · Reconciliation & settlement engine"
subtitle: "Fintech · staff (IC track) · full · standard · domain: fintech"
date: "2026-10-21 · attempt 1 on this question · round 6 overall · fictional sample candidate"
---

# Verdict

| Outcome at the target level | Weighted score | Apparent level | Time outcome | Help needed |
|---|:-:|---|---|---|
| **Hire** (borderline) | **2.81 / 4** | staff-level depth on matching; senior-level framing | rushed the end — wrap took 4 of 9 min | (a) × 2 · (c) × 1 |

**Headline.** The matching design was genuinely strong — multi-pass, partitioned, with a clear story
for corrected files — but the round treated reconciliation as *two lists that don't line up* rather
than *expectations the ledger failed to meet*. That framing cost the fee/FX explanation at 00:41 and
is the single change that moves this from a borderline hire to a clear one.

# Scorecard

*Scored against the **staff** bar. Weights from `levels.md` §2 (staff): H = 1.5, N = 1.0, L = 0.5.*

| # | Dimension | Weight | Score | Evidence |
|:--|:--------------------|:--:|:--:|:------------------------------------------------|
| 1 | Requirements & scoping | N 1.0 | 3 | 00:06 asked who the users were before writing anything; cut real-time rails explicitly |
| 2 | Estimation | N 1.0 | 3 | 00:14 "15M × 15M is a cross product — partition by date, account, processor first" → drove the design |
| 3 | High-level design | N 1.0 | 3 | clean raw → canonical → match → exceptions pipeline; walk-through at 00:22 without hesitation |
| 4 | Technical depth | **H 1.5** | 3 | many-to-one settlement matching and idempotent re-runs on corrected files, both two levels deep |
| 5 | Trade-off reasoning | **H 1.5** | 3 | 00:31 rule-based vs ML matching: "rules first, because finance must explain every match" |
| 6 | Operations, reliability & cost | N 1.0 | 2 | silent format change at 00:47 needed rung (a); no metric for unreconciled balance by age |
| 7 | Communication & collaboration | N 1.0 | 3 | narrated continuously; defined "break" when asked, without condescension |
| 8 | Handling ambiguity & pushback | H 1.5 | 3 | curveball (real-time rail) handled calmly; correctly said the core was batch-shaped |
| 9 | Leadership signal (technical) | N 1.0 | 2 | ops-headcount question at 00:52 answered with "more automation" — no auto-match target, no sequencing |

**Weighted score** = (3+3+3+4.5+4.5+2+3+4.5+2) ÷ 10.5 = 29.5 ÷ 10.5 = **2.81** → *hire* (2.75–3.24).
No High-weight dimension at 1, so no cap applies. Dimension 6 is slightly contaminated by one
interviewer leak (see self-audit) — read its 2 as "2, possibly generous", not as a reason to adjust
the number.

# Where the time went

| Phase | Budget | Actual | Note |
|:--------------------|:--:|:--:|:----------------------------------------|
| Requirements & scope | 12 | 10 | efficient; good clarifying questions |
| Estimation | 9 | 6 | short, but the one number mattered |
| High-level design | 18 | 17 | on budget |
| Deep dives | 22 | 29 | 7 min on matching rules after the point was made |
| Wrap: failure, scale, cost, summary | 9 | 4 | four-sentence summary was three sentences and trailed off |

**Hint rungs used:** (a) × 2 — format-change detection, ageing metric · (c) × 1 — "there's a tension
between what you expect and what arrives" at 00:41.

# Retrospective

## Your read — asked before any feedback

> "Matching felt solid. I think I lost time in the rules and didn't land the ops story. I'd give
> myself a 3. The fee question surprised me — I hadn't thought about the settlement being net."

## The interviewer's read

Agree on matching and on time. The fee question was not a surprise to the design so much as a
symptom: without ledger-generated expectations there is nowhere for fees, FX and chargebacks to live.

## Calibration gap

| Where you thought | Where the evidence put it | Why it matters |
|---|---|---|
| Overall ≈ 3 | 2.81 — borderline hire | close; slightly generous on ops |
| Lost time "in the rules" | yes, and it is what squeezed the wrap | the wrap is where dimensions 6 and 9 are earned |
| Fees were an edge case | fees, FX and chargebacks are the *normal* case for settlement | it is the crux of this question |

## Start · Stop · Continue

| Start | Stop | Continue |
|---|---|---|
| Framing reconciliation as **expected vs actual** from the first minute | Elaborating a point after the interviewer has nodded it through | Asking who the users are before designing |
| Naming one ops metric per pipeline stage | Leaving the four-sentence summary to the last 60 seconds | Letting one estimate drive the partitioning decision |

# Feedback

## Strengths

1. **Estimation that changed the design** — at 00:14, the cross-product observation immediately
   produced the partitioning scheme. Exactly the shape the bar asks for.
2. **Corrected files handled as first-class** — 00:35, "raw files are immutable, a resend is a new
   version, matches are recomputed for affected partitions." Most candidates never get here.

## Improvements

1. **The expectations model** — 00:41, a $3,400 shortfall had no explanation path. A strong answer has
   the ledger emit *expected settlements net of fees*, so the break is self-describing.
2. **The ops and people story** — 00:52, "more automation" for 25 ops staff. A Staff answer gives an
   auto-match target, the break taxonomy that drives upstream fixes, and the sequence.

## Moments worth remembering

| Time | Quote | Read |
|:----|:----------------------------------------|:-------------|
| 00:14 | "15M by 15M is a cross product — I'm not doing that." | altitude |
| 00:31 | "Rules first, because finance must be able to explain every match." | strong trade-off |
| 00:47 | "We'd… notice when totals don't match?" | needed rung (a) |

# The delta against a strong answer

## What a strong answer contained that this one didn't

1. **Ledger-generated expectations** including fees, FX and chargebacks — *mattered most*.
2. **Unreconciled balance by age** as the headline metric — mattered.
3. **Schema-change detection that fails loudly** — mattered; silent parse success is the classic
   incident.
4. Maker-checker on write-offs — checklist noise at this level; mentioned in passing is enough.

## What you raised that the cue sheet doesn't have

- Per-processor **confidence calibration** of fuzzy matches, sampled weekly by the ops team — a good
  idea worth a 4 on trade-offs had the rest been there.

## The model design, in brief

Immutable raw files → canonical records → **expectations generated by the ledger** (amount, date,
counterparty, net of known fees) → multi-pass matching (exact → rules → many-to-one) → breaks as a
categorised, aged, owned workflow → net settlement under maker-checker. It hinges on one decision:
**reconcile against expectations, not between two lists.**

# Trend

| Date | ID | Level | Weighted | Weakest dimension | Drill done? |
|---|---|---|:-:|---|:-:|
| 2026-09-30 | SD-44 | staff | 2.62 | Ops (2) | yes |
| 2026-10-07 | SD-71 | staff | 2.95 | Leadership (2) | partly |
| 2026-10-14 | SD-84 | staff | 3.10 | Time (rushed) | yes |
| 2026-10-21 | SD-79 | staff | 2.81 | Ops (2), Leadership (2) | — |

**Pattern:** depth and trade-offs are reliably at the Staff bar. **Operations and the technical-
leadership close are the standing weakness** — three of four rounds, and both are earned in the wrap,
which keeps getting squeezed.

# Next

**The one drill.** Run `wrap` mode three times this week on designs you already have, hard-stopping
deep dives at their budget. Success = a crisp four-sentence summary and one named metric per stage.

**Study the gap.** Expected-vs-actual reconciliation; operational metrics for financial pipelines;
how break taxonomies feed upstream fixes.

**Next round.** SD-81 *Payouts* at `staff` — it loads operations (ambiguous rail outcomes, returns)
and rewards the expectations framing you're building.

# Interviewer self-audit

One leak at 00:44: I said "net settlement" before the candidate did — dimension 6 slightly
contaminated, flagged above rather than adjusted. Under-probed estimation (one probe only). Confidence in this
scorecard: **medium-high**.
