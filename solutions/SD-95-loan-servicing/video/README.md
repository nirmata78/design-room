# SD-95 · Instalment loan servicing: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 75:13**, 18 chapters, **162 numbered slides**, **9,238 spoken words**
(candidate 88.4 %, interviewer 4.3 %, key line 4.3 %, coach 3.0 %). Built 2026-11-21 in the SD-94 reference format; it replaces
problem 2 of the 2026-11-20 fintech mock series, which has been retired. Scripted walkthrough with synthetic voices; numbers are
illustrative, not any company's figures; bank-debit return rules checked against public rule summaries in November 2026; not legal,
accounting or compliance advice. **The technical content has not been reviewed by a person, and the video has not been watched end
to end.**

Output: `loan-servicing-reference.mp4` (local only, gitignored). Written companion: `../SD-95_Loan_Servicing_Reference_Design.md`
(PDF beside it, 34 pages, about 15k words). Publish kit: `publish/` (YouTube title, description with chapters, tags, thumbnail,
LinkedIn post). Plan: `OUTLINE.md`.

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:11 | 1 Requirements and scope |
| 08:24 | 2 Estimates |
| 12:49 | 3 Theory |
| 22:58 | 4 API and entities |
| 28:25 | 5 High-level design |
| 36:16 | 6 Bridge |
| 37:01 | 7 Challenges |
| 37:19 | 7.1 Challenge 1: The processor timed out |
| 41:42 | 7.2 Challenge 2: The morning of the 1st |
| 46:07 | 7.3 Challenge 3: It settled, then it came back |
| 50:32 | 7.4 Challenge 4: A refund in the middle of the loan |
| 54:31 | 7.5 Challenge 5: Paying off with a debit in flight |
| 58:37 | 7.6 Challenge 6: Four hundred dollars more than the bank |
| 62:45 | 7.7 Challenge 7: The card processor is down on the 1st |
| 66:14 | 7.8 Challenge 8: How would you know before month-end? |
| 70:01 | 8 Build cost (AUX) |
| 72:30 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The processor timed out | UNKNOWN; the resolver queries by the same key; same attempt, same key; the settlement file is the arbiter |
| 2 | The morning of the 1st | 42/s is nothing; a day plan back from the 14:00 cut-off; token bucket per rail; claim with SKIP LOCKED |
| 3 | It settled, then it came back | RETURNED; a reversal dated the day it arrives; return codes as policy (R01 re-present ≤ 2, R10 never) |
| 4 | A refund mid-loan | A transaction plus a new schedule version; re-amortise or shorten per the terms; allocation waterfall |
| 5 | Payoff with a debit in flight | The quote lists what is in flight; PAID_PENDING until nothing can come back; customer payable |
| 6 | $400 more than the bank | Three-way match by reference; typed, owned, aged breaks; never by totals |
| 7 | Card processor down on the 1st | Pause the rail, resolve unknowns first, no late fees for our outage, resume at 50/s |
| 8 | How would you know? | The money funnel per rail, file acknowledgement by 11:00, returns by reason code, nightly invariants, symptom pairs |

## Rebuild

```bash
solutions/SD-95-loan-servicing/video/build-video.sh            # diagrams -> slides + script -> frames -> loan-servicing-reference.mp4
solutions/SD-95-loan-servicing/video/build-video.sh --frames   # stop after the frames
cat solutions/SD-95-loan-servicing/booklet-src/*.md > solutions/SD-95-loan-servicing/SD-95_Loan_Servicing_Reference_Design.md
solutions/SD-95-loan-servicing/build-sd-booklet.sh SD-95_Loan_Servicing_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-95-loan-servicing/video/publish/meta.json
```

Slides and script are generated together from `video/src/*.py` (DSL copied from SD-44/SD-94): edit the sources, not
`video-slides.html` or the script.

## QA done

- `ffprobe`: H.264 1920x1080, AAC, a chapter data stream (18 chapters); no subtitle stream. Duration 1:15:13.
- Audio intelligibility (`check_audio.py`, 20 excerpts of 45 s across the length): Whisper confidence -0.14 to -0.33; 13 suspect
  substitutions, all near-homophones or function words ("your call" / "you're cool", "cents" / "sense", "ingest" / "and jest",
  "diff" / "dip"). No term re-voiced.
- Sync probe at 66:40: the burned caption matches the narration Whisper hears.
- Frames: all 162 slides read on contact sheets before the build (fixed: overflowing code comments, fix strips that shrank the
  baseline, baseline label collisions, Chen ERD overlaps, day-plan axis). Eight frames sampled from the MP4.
- Booklet: built clean (missing ≈ ≠ ≥ glyphs replaced), 34 pages tiled and read; page 22 read zoomed.
- **Not watched end to end.**

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Double-entry ledger, immutable lines | cue sheet; standard ledger treatments | M1; ch. 4 worked entries and posting SQL; C3, C4 |
| "Never store a balance" | common prep | Corrected aloud: a projection in the same commit, provable, checked nightly (M1) |
| Idempotency keys | all | M3 (three layers); C1 |
| Payment state machine; UNKNOWN; RETURNED | cue sheet (crux) | M2; ch. 4 states; C1; C3 |
| Scheduler / cron at scale; "thundering herd" | common prep; cue sheet trap | Estimates 1–2; M4, M5; C2 |
| A message broker for the work queue | common prep | Options row B; theory pick note: optional, for other consumers |
| Dunning / failed-payment retries; late fees | billing treatments | M6; C3 rules table; C7 (no fees for our outage) |
| Refunds, proration, re-amortisation | cue sheet | C4; allocation waterfall |
| Early payoff; interest accrual | cue sheet | C5; estimate 8 (accrue by calculation) |
| Bank-debit return codes and windows | cue sheet; public rule summaries | C3 (R01 two banking days, re-present at most twice; unauthorised up to 60 days, never retried) |
| Business days and holidays | billing treatments | Ch. 4 money-and-dates slide |
| Three-way reconciliation | cue sheet | M7; C6 |
| Event sourcing | some treatments | Options row C, rejected as the core |
| Buy a servicing platform | build-vs-buy treatments | Options row E; build cost V0 |
| Instant payment rails (since 2023) | then-and-now | Theory 3, one line: removes some pending states, not returns or reconciliation |
