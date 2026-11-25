# SD-59 · Multi-team decomposition and API contracts — outline (compact cut, 2026-11-25)

Standard: `.claude/skills/reference-solution/GUIDELINES.md` (§3.4 compact cut, §4b the 2026-11-25 rules). Subject: the SD-95 loan-servicing platform.

**Thesis.** Cut along domain seams, put a versioned contract on every seam, give shared things one owner, integrate end to end by week four, and keep the contracts, the dependency graph and the milestones yourself.
**Definition.** A division of the work into teams that can ship alone, joined by explicit contracts, with one owner for everything shared, and a way to see early that the cut is wrong.
**The scale line.** 40 engineers · 5 teams · 3 time zones · 6 months (240 engineer-months) · 2 external consumers.
**What it grades.** Seams · contracts · unblocking · integration · what the manager owns.

## Clarifying answers
Optimise for independent delivery · two teams know the domain, three do not · structure may change once · three time zones, pairs overlap ~2 h · two external consumers (events in, breaks out).

## FRs and NFRs
FR1 seams (≤ 2 teams per feature) · FR2 contracts (agreed by week 2) · FR3 unblocked (idle ≤ 2 days) · FR4 integrate (green by week 4) · FR5 detect (signal by month 2). NFR: release in 6 months; contract changes announced 2 weeks ahead; cross-zone seams most stable.

## Estimates (all from the scale line)
240 engineer-months; −25 % overhead = ~180; 36 per team · 10 team pairs, design for 4–5 · one cross-team change ≈ 1 week; a 4-team feature = 3–4 weeks · integration at month 5 against week 4 ≈ 10× dearer.

## Theory (five parts, theory rendered first; no failure catalogue)
Properties: `[S1-no-silent-break]` `[S2-one-owner-each]` `[L1-no-team-waits]` `[L2-integrated-by-week-4]` `[L3-wrong-split-seen-early]`.
Mechanisms, each with its diagram type: M1 seams by domain (C4) · M2 contracts first (ERD) · M3 consumer-driven tests and mocks (sequence) · M4 one owner (C4) · M5 skeleton first (C4) · M6 leading indicators, one re-cut (state machine).
Options, one infographic each (pros, cons, C4, red pitfalls): A by layer · B by domain (pick) · C feature teams, shared everything · D twelve services · E platform plus stream teams. Matrix as summary; pick and its cost.

## Contracts and entities
An event contract with an additive v2; a call contract with its policy; the ownership ERD (team, component, contract, dependency).

## HLD (C4 container deltas) and objections (sequences)
V1 by layer → objection: a partial refund crosses four teams → V2 by domain → objection: incompatible changes to one table, integration in month 5 → V3 contract hub and skeleton environment. One sequence per FR. Events (dashed blue) versus calls (solid) drawn distinctly.
Components and technologies: contract format and registry · consumer-driven tests · decision record and dashboard (each with two rejected alternatives).
Alternate path: one team of eight, a modular monolith; split at ~12 engineers or three hot modules.

## Challenges (6, all nine beats; each fix one level down with a Rejected line)
1 critical path (contract + mock in week 2) · 2 a dependency two months late (consumer tests in the provider's CI) · 3 two teams, one table (owner, versioned views, expand-migrate-contract) · 4 a contract dispute (decision record, clock, named decider) · 5 lose a team at month 3 (pause, freeze, cut scope) · 6 observability: three leading indicators, thresholds in advance, own failure mode.

## Recap and follow-ups
Five paths; what I own; common mistakes; four sentences; six follow-up questions with pointers.

## Canon check
Conway's law (M1) · domain over layer (A) · contracts before code, additive, sunset (M2) · consumer-driven tests, mocks (M3) · shared-component ownership (M4, ch. 3) · skeleton first (M5) · sequencing against skills (Q2) · time-zone seams (Q4) · manager's owned list (recap) · leading indicators and own failure mode (ch. 6) · not over-decomposing (D) · reorg curveball (ch. 5). Third-party material: none copied.

## Budget (compact cut)
Chapters 0–8; 117 logical slides, ~6,000 spoken words (below the 7,800–8,800 compact target: the video will be about 50–55 minutes; a longer cut would add worked cases to challenges 2 and 4).
