# SD-44 · Payment processing and the double-entry ledger: reference-solution video

Staff bar (L6/L7), **compact cut** (GUIDELINES §3.4). **Length 1:22:26**, 9 chapters plus 6 challenge sub-chapters and 5.1 / 5.2, **138 numbered slides** in **549 reveal frames**,
**9,737 spoken words** (candidate 86.2 %, interviewer 2.9 %, key line 6.5 %, coach 4.4 %). Rebuilt 2026-11-22 from the earlier
retrofit; a few minutes over the 80-minute compact target because of the material added on request (partition key, runtime, gateway
or processor, Debezium alternatives). Scripted walkthrough with synthetic voices; numbers are illustrative, not any company's figures;
not legal, accounting or compliance advice. **The technical content has not been reviewed by a person, and the video has not been
watched end to end.**

Output: `payments-ledger-reference.mp4` with `payments-ledger-reference.srt` and `.vtt` beside it (local only; no subtitle stream).
Written companion: `../SD-44_Payments_Ledger_Reference_Design.md` (PDF beside it, 41 pages). Publish kit: `publish/`. Plan: `OUTLINE.md`.

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:39 | 1 Requirements and scope |
| 08:29 | 2 Estimates |
| 13:03 | 3 Theory |
| 22:46 | 4 API and entities |
| 28:04 | 5 High-level design |
| 36:20 | 5.1 Components and technologies |
| 46:44 | 5.2 When you don't need all this |
| 48:26 | 6 Bridge |
| 49:23 | 7 Challenges |
| 49:42 | 7.1 Challenge 1: The bank timed out |
| 54:30 | 7.2 Challenge 2: Three retries at once |
| 59:18 | 7.3 Challenge 3: A crash between the ledger and the event |
| 63:43 | 7.4 Challenge 4: The hot merchant, and a million one-time accounts |
| 69:26 | 7.5 Challenge 5: 999,998 against 1,000,000 |
| 74:06 | 7.6 Challenge 6: How would you know before finance does? |
| 78:47 | 8 Recap |

## The six challenges

| # | Challenge | The fix, one level down | Rejected |
|---|---|---|---|
| 1 | The bank timed out | attempt row before the call; UNKNOWN by conditional update; inquiry by our reference; breaker, never fail over an unknown | treating a timeout as a decline |
| 2 | Three retries at once | unique insert of the key with a request hash in the payment's transaction; 409 / stored / 422 | check, then insert |
| 3 | A crash between the ledger and the event | outbox row in the transaction; Debezium reads the log through a slot, commit order, at least once | publish after the commit |
| 4 | The hot merchant, and a million one-time accounts (V4) | insert-only entries, projector, payout writer; an account is a row, not a partition | one balance row per payment |
| 5 | 999,998 against 1,000,000 | expectations by reference, line-by-line match, owned breaks; a spike is an incident (reversing entries) | matching on amount and time |
| 6 | How would you know before finance does? | approval rate by segment, UNKNOWN age, slot lag, unmatched by age, zero-sum, a probe | alerting on the error rate |

## Answers to the author's review of 2026-11-22

| Question | Where |
|---|---|
| Why partition by account? A million one-time accounts? | it is **not** partitioned by account: slide "The partition key" (chapter 5), estimates, challenge 4 second push; booklet "The partition key" and 6.4 |
| State machine appears piece by piece | chapter 4, 12 steps (`diagrams.py`, `states`) |
| ERD appears piece by piece | chapter 4, both models build up entity by entity (`order=`) |
| Why Go; against Python, Java, WebFlux, Quarkus, Rust | 5.1 "Why Go" table and narration; booklet "Runtime" and the `runtime` entry of `stack.json` |
| Fastest ledger for a small business | booklet "Building a payment ledger for your own business: the ladder"; TigerBeetle in challenge 4 and `payments-db` |
| Gateway or processor; why gateways | 5.1 table with the break-even; 5.2; booklet "Gateway or processor" |
| Why Debezium; alternatives | `outbox-log` technology slide (polling relay, own decoding consumer, managed capture); challenge 3 second push; booklet detail |

## Canon check

See `OUTLINE.md`. Covered: keys, double entry, UNKNOWN and inquiry, outbox, reconciliation, hot accounts and the partition key, refunds
and chargebacks as new transactions, PCI scope, gateway against processor. Dismissed aloud: FX, fraud scoring, payouts, KYC.

## Rebuild

```bash
solutions/SD-44-payments-ledger/video/build-video.sh            # diagrams -> slides + script -> layout gate -> frames -> payments-ledger-reference.mp4
solutions/SD-44-payments-ledger/video/build-video.sh --frames   # stop after the frames
solutions/SD-44-payments-ledger/build-sd-booklet.sh SD-44_Payments_Ledger_Reference_Design   # the written reference design (PDF)
```

Slides and script are generated together from `video/src/*.py`: edit the sources, not `video-slides.html` or the script. Technologies
are edited in `../stack.json` only (`stack.py sync` regenerates the booklet's and outline's marked regions). The booklet's Markdown
is now the source (the old `booklet-src/` was removed).

## QA done

- Layout gate: **0 failures**, 7 warnings (`dense`: slides 4, 53, 64–69 carry 100–126 words against the cap of 95; every one is a table or
  a technology slide whose content is the point). No `redraw` warnings.
- ffprobe: H.264 + AAC, 1920 × 1080, 9 chapters plus 6 challenge sub-chapters and 5.1 / 5.2 plus 6 sub-chapters, no subtitle stream, 82:16.
- Captions: 1,117 cues; first cue at 0:01 (the card's lead pause), last ends about 3 s before the end (the closing pause); no line over 42
  characters or more than 2 lines; every VTT cue carries a `<v Name>` voice span.
- Contact sheets: the last step of all 138 slides read as images before rendering; eight frames sampled across the finished video.
- Audio intelligibility (faster-whisper, 22 excerpts of 30 s, 6 of them in 5.1 and the challenges): 10 suspect words, all Whisper
  noise (an, and, timeout and, owned, hot/hard, writer/rider); no technology name (Debezium, Kafka, PostgreSQL, Go, WebFlux) flagged.
- Sync probe at 75:14 (challenge 6 trace): each row appears with its own sentence. The first render had a defect found by this probe
  (a helper that auto-prepended a marker moved 15 slides one sentence early); it was removed and every one of those slides re-marked by hand.
