# SD-47 · Ticket / seat booking under contention: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 86:46**, 18 chapters, **169 numbered slides**, **11,198 spoken words** (candidate 86.9 %, interviewer 3.0 %, key line 6.3 %, coach 3.8 %). Scripted walkthrough with synthetic voices; figures are illustrative, not any company's numbers. **The technical content has not been reviewed by a person, and the video has not been watched end to end.** Reworked 2026-11-21 from the 38-minute mock-round video (v2) into the reference-solution format; the written companion is [`../SD-47_Ticket_Booking_Reference_Design.md`](../SD-47_Ticket_Booking_Reference_Design.md).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:11 | 1 Requirements and scope |
| 08:09 | 2 Estimates |
| 14:44 | 3 Theory |
| 23:53 | 4 API and entities |
| 30:42 | 5 High-level design |
| 40:44 | 5.1 Components and technologies |
| 53:42 | 6 Bridge |
| 54:27 | 7 Challenges |
| 54:47 | 7.1 Challenge 1: Two fans, one seat |
| 59:17 | 7.2 Challenge 2: The hold that outlives its owner |
| 1:04:07 | 7.3 Challenge 3: The hold expires, then the payment succeeds |
| 1:10:36 | 7.4 Challenge 4: A million at the door |
| 1:16:40 | 7.5 Challenge 5: A fair line, and the bots |
| 1:21:23 | 7.6 Challenge 6: The seat map for ten thousand shoppers |
| 1:26:07 | 7.7 Challenge 7: Requirements that arrive mid-sale |
| 1:32:07 | 7.8 Challenge 8: How would you know it is broken? |
| 1:37:40 | 8 Build cost |
| 1:40:12 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | Two fans, one seat | One conditional update (the check and the change), rows locked in order, all or nothing; a unique ticket constraint as the second guard |
| 2 | The hold that outlives its owner | Lazy expiry inside the claim plus a sweeper; a dead sweeper costs staleness, not oversell |
| 3 | The hold expires, then the payment succeeds | Freeze before the call, authorize then capture, unknown is not failed, a reconciler; the residual case is owned |
| 4 | A million at the door | A waiting room admitting at a rate from shop capacity (Little's law), a controller driven by health, one cached answer for everyone |
| 5 | A fair line, and the bots | A lottery among everyone present at the start, signed tokens, verified accounts, limits per card; a product decision |
| 6 | The seat map for ten thousand shoppers | An immutable layout on the edge, a versioned bitmap from the event log, a 304 when nothing changed |
| 7 | Requirements that arrive mid-sale | New rows and a layout version, a waitlist as a consumer, an allocator, cells for a tour; say what changes and what does not |
| 8 | How would you know it is broken? | Indicators tied to promises, a synthetic fan, a load test, a plan to degrade |

## Rebuild

```bash
solutions/SD-47-ticket-booking/video/build-video.sh            # diagrams -> slides + script -> frames -> ticket-reference.mp4
solutions/SD-47-ticket-booking/video/build-video.sh --frames   # stop after the frames
solutions/SD-47-ticket-booking/build-sd-booklet.sh SD-47_Ticket_Booking_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-47-ticket-booking/video/publish/meta.json   # the publish kit
```

The slides and the script are generated together from `video/src/*.py`: edit the sources, not `video-slides.html` or the script. Every frame has exactly one cue. `video/OUTLINE.md` is the outline the sources follow. Needs the slide-video-kit, Kokoro TTS, pandoc, xelatex, plantuml, rsvg-convert. The MP4, `frames/` and the booklet PDF are gitignored.

## QA done

- `ffprobe`: H.264 1920x1080, AAC, a chapter data stream (18 chapters); no subtitle stream, no `.srt` beside the MP4. Length 86:46, under the 90-minute target.
- Audio intelligibility (`check_audio.py`, 22 excerpts of 45 s across the length): Whisper confidence -0.14 to -0.31; 26 differences, all homophones or splits (write/right, writer/rider, queue/Q, trace/trays, bot/bought, cached/cashed, Redis heard as a possessive); nothing mangled enough to respell.
- Sync probe at 78:20: the transcribed audio ("Map version lag rising with hold latency flat. The pipeline, which is staleness...") is followed, 2 s after the clip ends, by the next scripted line on the burned caption, as it should be.
- Frames: all slides read on contact sheets before the build (fixed: wire-format badge overlapping the first comment line, dimmed nodes leaking below a cropped figure, two code lines past the right edge, a tiny V1 picture, a truncated note); the slide added afterwards (challenge 7's trace) and eight frames sampled from the finished MP4 were checked.
- Booklet: `build-sd-booklet.sh` builds (62 pages); three pages spread across it read as images (theory options matrix, V3 and a flow, challenge 3 with its figure).
- **Not watched end to end.**

## Canon check

For the video README, not for the screen.

| Canonical point | Covered at (chapter / slide) or dismissed because |
| --- | --- |
| Three-state seat, atomic conditional claim (not read-then-write) | Ch. 3 mechanism 1 and the options matrix; V2; **C1** |
| A hold with a TTL, not a lock through checkout | Ch. 1 question 3; ch. 3 mechanism 2; **C1, C2** |
| A virtual waiting room admitting at a serviceable rate; the queue as a product (position, estimate) | Ch. 2 estimates 2 to 5; V3; **C4** |
| Sweeper plus lazy expiry | **C2** |
| Hold expired, payment succeeded: take a position | **C3** (freeze, authorize then capture, unknown, residual) |
| Seat-map read path split; a stale click is acceptable and graceful | Ch. 2 estimate 6; **C6** |
| Fairness discussed explicitly, including bots; a lottery over strict first-come | Ch. 1 question 4; **C5**. What changed since older write-ups: strict first-come at the start is now widely seen as bot-friendly; verified-fan registration is standard for flagship events |
| Idempotent purchase | Ch. 4 (idempotency key on holds and orders); **C3** |
| Adjacent seats ("best available") | **C7** (an allocator that hands different fans different seats) |
| A pre-event load test and an SLO for the opening | **C8**; ch. 8 |
| A distributed lock per seat (a cache key with a lease) | **Dismissed aloud** in the options matrix: a second system to run, and a lease can expire mid-transaction |
| Optimistic locking with a version column | In the options matrix; a multi-seat claim ends in one conditional update anyway |
| "Exactly-once" payment | Corrected in **C3**: at-least-once with idempotent effects, by key |
| Multi-region | **C7**: each event homed in one region with a single writer; no multi-master writes on seats |

## Retrofit, 2026-11-22

Brought to the current standard by `RETROFIT.md`: the Google theme (`video.css`, `google-theme.css`), progressive reveal (every table row,
card, trace event and figure step appears as it is spoken), sidecar captions (`.srt` and `.vtt` beside the MP4, nothing burned in), the
technology chapter **5.1** generated from `../stack.json` (container view with technologies, one slide per technology with its rejected
alternatives, the stack on one slide, the drill interlude) and a **Rejected** line on every challenge's fix slide.

**109 of the 182 slides were written before reveal markers existed; their markers were placed automatically** (`dsl.META["automark"]`:
the narration is cut at sentences and dealt to the reveal units by word overlap). Watch those slides and move a marker by hand where one
lands badly. Not done in this pass: the C4 context moved to the end of chapter 1, a mechanism map in the theory chapter, extra sequences per
requirement, component views. The previous sources are kept in `.v1-retrofit-2026-11-22/` until the author has watched this version.
