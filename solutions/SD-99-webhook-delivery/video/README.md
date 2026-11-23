# SD-99 · Outbound webhooks and partner event delivery: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 1:29:02**, 19 chapters, **158 numbered slides** in **549 reveal frames**,
**10,573 spoken words** (candidate 85.9 %, interviewer 4.0 %, key line 4.0 %, coach 6.0 %). Built 2026-11-22 with
`/reference-solution`, set in the world of SD-82 and SD-95 (a point-of-sale lender's loan and payment events to merchants and a partner bank);
the build-cost chapter and challenge 6 carry the SD-59 overlay (team seams, contracts, API governance). Scripted walkthrough with
synthetic voices; numbers and prices are illustrative. **The technical content has not been reviewed by a person, and the video has not
been watched end to end.**

Output: `webhook-delivery-reference.mp4` with `.srt` and `.vtt` beside it (local only, gitignored). Written companion:
`../SD-99_Webhook_Delivery_Reference_Design.md` (and PDF). Technologies: `../stack.json`. Plan: `OUTLINE.md`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:28 | 1 Requirements and scope |
| 08:51 | 2 Estimates |
| 11:46 | 3 Theory |
| 21:08 | 4 API and entities |
| 24:00 | 5 High-level design |
| 32:14 | 5.1 Components and technologies |
| 46:56 | 5.2 When you don't need all this |
| 48:47 | 6 Bridge |
| 49:30 | 7 Challenges |
| 49:48 | 7.1 Challenge 1: Why not publish after the commit? |
| 54:05 | 7.2 Challenge 2: One slow endpoint |
| 58:48 | 7.3 Challenge 3: Down for two days, then back |
| 1:04:17 | 7.4 Challenge 4: Twice, and out of order |
| 1:08:19 | 7.5 Challenge 5: Hostile URLs and forged calls |
| 1:14:11 | 7.6 Challenge 6: A producer changes the payload |
| 1:19:27 | 7.7 Challenge 7: “You never sent it” |
| 1:23:37 | 8 Build cost |
| 1:26:30 | 9 Recap |

## The seven challenges

| # | Challenge | The fix | Version |
|---|---|---|---|
| 1 | Why not publish after the commit? | Outbox row in the commit; relay publishes, waits for acks, then marks sent; consumers de-duplicate | — |
| 2 | One slow endpoint | Claim only where in-flight < cap (Little's law); tier pools; breaker; batching for the bank | — |
| 3 | Down for two days, then back | Full jitter capped at 1 h for 72 h; breaker pauses; probe and ramp; disable and email; latest-per-loan replay | V4 |
| 4 | Twice, and out of order | Event ID kept 7 days; per-loan sequence from the producer's commit; thin events; ordered mode costs throughput | — |
| 5 | Hostile URLs and forged calls | Egress proxy checks the address it connects to; HMAC over id.timestamp.body, 5 min; rotation with overlap | V5 |
| 6 | A producer changes the payload | Pinned dated versions; renderer; golden examples fail the producer's build; integrations team owns the seam | V6 |
| 7 | "You never sent it" | Attempts in the merchant's dashboard; health emails; SLIs we own; symptom pairs | — |

## Rebuild

```bash
solutions/SD-99-webhook-delivery/video/build-video.sh            # sources → slides → frames → MP4 (TTS cached)
solutions/SD-99-webhook-delivery/build-sd-booklet.sh SD-99_Webhook_Delivery_Reference_Design
```

## QA done

- `check_layout.py`: 0 failures; 12 warnings (dense technology and drill slides generated from `stack.json`; the recap is a numbered flow on the final view).
- `ffprobe`: H.264 + AAC, 1920×1080, 19 chapters, no subtitle stream. Captions: no line over 42 characters, no cue over two lines, every VTT cue with a voice span.
- Whisper on 24 excerpts: "endpoint" was heard as "in point"; respelled in `theory/video/say.py` and re-rendered; the remaining substitutions are transcription noise.
- Contact sheets of the last step of all 158 slides and eight frames sampled from the MP4, read as images.
- Not watched end to end.

## Canon check

See `OUTLINE.md` (covered: queue, backoff with jitter, idempotency, signatures and rotation, dead letters and disabling, isolation,
replay, ordering, SSRF, customer logs, payload versioning, buy; dismissed aloud: multi-region, booklet Stage 7).
