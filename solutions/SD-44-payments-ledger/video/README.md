# SD-44 · Payment processing and the double-entry ledger: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 73:56**, 18 chapters, **160 numbered slides**, **8,977 spoken words**
(candidate 85.1 %, interviewer 4.0 %, key line 7.6 %, coach 3.4 %). Built 2026-11-20 in the SD-94 reference format; it replaces
the earlier 26-minute mock round, which has been retired. Scripted walkthrough
with synthetic voices; numbers are illustrative, not any company's figures; not legal, accounting or compliance advice.
**The technical content has not been reviewed by a person, and the video has not been watched end to end.**

Output: `payments-ledger-reference.mp4` (local only). Written companion: `../SD-44_Payments_Ledger_Reference_Design.md` (PDF beside it, 31 pages).
Publish kit: `publish/` (YouTube title, description with chapters, tags, thumbnail, LinkedIn post). Plan: `OUTLINE.md`.

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:00 | 1 Requirements and scope |
| 07:43 | 2 Estimates |
| 12:18 | 3 Theory |
| 21:53 | 4 API and entities |
| 27:36 | 5 High-level design |
| 36:46 | 6 Bridge |
| 37:28 | 7 Challenges |
| 37:47 | 7.1 Challenge 1: The bank timed out |
| 42:24 | 7.2 Challenge 2: Three retries at once |
| 46:38 | 7.3 Challenge 3: A crash between the ledger and the event |
| 49:57 | 7.4 Challenge 4: The hot merchant |
| 53:24 | 7.5 Challenge 5: Refunds, and a chargeback months later |
| 57:10 | 7.6 Challenge 6: 999,998 against 1,000,000 |
| 60:57 | 7.7 Challenge 7: A bug double-posted forty thousand entries |
| 64:39 | 7.8 Challenge 8: How would you know before finance does? |
| 68:35 | 8 Build cost (AUX) |
| 71:08 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The bank timed out | Attempt committed before the call; UNKNOWN; inquiry and reversal by our reference; settlement file as arbiter |
| 2 | Three retries at once | Idempotency key inserted first, unique, with a request hash; 409 / stored response / 422 |
| 3 | A crash between the ledger and the event | Transactional outbox, at-least-once relay, de-duplication by event ID |
| 4 | The hot merchant | Append entries, derived balance; sub-accounts or one writer for the rare checked operation |
| 5 | Refunds and a late chargeback | New transactions dated now; the refund limit as one conditional update |
| 6 | 999,998 against 1,000,000 | Expectations from the ledger, line-by-line match, owned and aged breaks |
| 7 | 40,000 double-posted entries | Kill switch, payout hold, reversing entries tagged with the incident, receivables; a (payment, type) constraint |
| 8 | How would you know? | Approval rate per segment, UNKNOWN age, zero-sum ledger page, synthetic payments, symptom pairs |

## Rebuild

```bash
solutions/SD-44-payments-ledger/video/build-video.sh            # diagrams -> slides + script -> frames -> payments-ledger-reference.mp4
solutions/SD-44-payments-ledger/video/build-video.sh --frames   # stop after the frames
solutions/SD-44-payments-ledger/build-sd-booklet.sh SD-44_Payments_Ledger_Reference_Design   # the written reference design (PDF)
```

Slides and script are generated together from `video/src/*.py` (copied DSL from SD-94): edit the sources, not `video-slides.html` or
the script. The booklet is assembled from `booklet-src/*.md` (`cat booklet-src/*.md > SD-44_Payments_Ledger_Reference_Design.md`).

## QA done

- `ffprobe`: H.264 1920x1080, AAC, a chapter data stream (18 chapters); no subtitle stream. Duration 1:13:56.
- Audio intelligibility (`check_audio.py`, 8 excerpts of 60 s across the length): Whisper confidence -0.17 to -0.30; 5 suspect
  substitutions, four of them function words (an/and, in/and, "your call" heard as "you're cool"); one real: "auth" in "auth pending"
  heard as "off". Not re-voiced.
- Sync probe at 66:40 and 58:20: the burned caption matches the slide's narration.
- Frames: all 160 slides read on contact sheets before the build (fixed: baseline compressed vertically so it reads larger, budget-bar
  label clipped, idempotency box text overflow, row-four boxes clipped in short views, ERD edges and legend). Eight frames sampled from the MP4.
- Booklet: built clean (no missing glyphs after replacing the approximately sign), 31 pages tiled and read; pages 9 and 22 read zoomed.
- **Not watched end to end.**

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Pay-in flow through a payment service and an external processor | standard treatments; cue sheet | Ch. 5 V1–V3; FR1 flow |
| Hosted payment page / tokenisation to keep card data out of scope | standard treatments | Ch. 1 OUT; ch. 8 V1 |
| Double-entry ledger | all | M3; ch. 4 worked example; C5 |
| Idempotency keys; exactly-once as at-least-once + idempotent effect | all | M1; precision statement in theory 1; C2 |
| Retry with backoff; dead-letter for failures | standard treatments | C1 (retries carry the reference); C3 (webhooks with backoff); dead-letter = break or aged UNKNOWN |
| Reconciliation with settlement files | all | M6; C6 |
| Handling a PSP timeout / unknown outcome | cue sheet (crux) | C1 |
| Sagas and compensations | cue sheet | Options matrix row C; C1 reversal; dismissed as the core model because compensation can itself be unknown |
| Outbox | cue sheet | M4; C3 |
| Hot account | cue sheet | C4 |
| Wallet / stored balance product | some treatments | Dismissed aloud: a different product (stored value) with its own regulation; the same journal underneath |
| Payouts to merchants | some treatments | OUT (SD-81); payout checks in C4 and C7 |
| Fraud | all | OUT (SD-43), one call in the latency budget |
| Multi-currency | cue sheet | Ch. 4 (currency on every amount); C5 second fix |
| What changed since older treatments | — | Network tokens and processor idempotency keys are now common, which makes M5 easier; the UNKNOWN state is still needed |


