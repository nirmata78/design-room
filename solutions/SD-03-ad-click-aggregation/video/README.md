# SD-03 · Event counting & billing rollups — reference-solution video (compact cut)

**Length:** 71:41 · 125 logical slides, 482 frames · 8,492 spoken words (candidate 85 %) · 1080p, sidecar captions.
**Format:** the compact cut (GUIDELINES §3.4): 6 challenges, no drill interlude, no build-cost chapter.
**Files (local, gitignored):** `ad-click-aggregation-reference.mp4`, `.srt` (upload to YouTube), `.vtt`. Booklet: `../SD-03_Ad_Click_Aggregation_Reference_Design.pdf`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 0 Cold open |
| 2:30 | 1 Requirements and scope |
| 8:22 | 2 Estimates |
| 11:49 | 3 Theory |
| 21:36 | 4 API and entities |
| 25:05 | 5 High-level design |
| 32:31 | 5.1 Components and technologies |
| 39:25 | 5.2 When you don't need all this |
| 41:00 | 6 Bridge |
| 41:55 | 7 Challenges |
| 42:14 | 7.1 Challenge 1: The same click, three times |
| 46:52 | 7.2 Challenge 2: Yesterday's events at 6 a.m. |
| 52:00 | 7.3 Challenge 3: One ad at 2 million a second |
| 55:59 | 7.4 Challenge 4: Replay four hours |
| 60:26 | 7.5 Challenge 5: Fraud after the invoice |
| 64:52 | 7.6 Challenge 6: “Your numbers are 3 % high” |
| 69:21 | 8 Recap |

## Challenges

1. The same click, three times (correctness, crux): event IDs minted at the source; keyed dedup state; billing dedup over the hour.
2. Yesterday's events at 6 a.m. (correctness): event time clamped; watermark − 2 min; 1 h lateness; the bill closes at H + 48 h.
3. One ad at 2 million a second (overload): combine per subtask, merge 512 partials; shard rows summed on read.
4. Replay four hours (failure recovery, crux): replace by key and version; a billing run is a pure function of its manifest.
5. Fraud after the invoice (correctness): versions and adjustment lines; nothing billed is edited.
6. "Your numbers are 3 % high" (observability): V4 reconciler: conservation per hop, live against final, canaries, audit trail.

## Rebuild

```bash
solutions/SD-03-ad-click-aggregation/video/build-video.sh            # sources → slides → layout gate → frames → MP4
solutions/SD-03-ad-click-aggregation/video/build-video.sh --frames   # stop after the frames
solutions/SD-03-ad-click-aggregation/build-sd-booklet.sh SD-03_Ad_Click_Aggregation_Reference_Design
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-03-ad-click-aggregation/video/publish/meta.json
```

## QA done (2026-11-22)

- Layout gate: 125 slides, **0 failures**, 7 warnings (dense: the four technology slides and the options matrix, 96–116 words; kept, the tables are the content).
- ffprobe: H.264 + AAC, 1920 × 1080, 17 chapters, no subtitle stream, 71.7 min.
- Captions: SRT and VTT, 945 cues, no SRT line over 42 characters, every VTT cue with a `<v Name>` span.
- Eight frames sampled across the length (mid-reveal states, nothing drawn over the slide).
- Whisper check on 20 excerpts twice; "Kafka" respelled after the first pass; the rest are homophones (ad/add) and number formatting.
- Not watched end to end by a person.

## Canon check

See `OUTLINE.md` § Canon check: durable log, idempotency keys, event time and watermarks, Lambda against Kappa, exactly-once
unpacked, hot keys and sharded counters, HyperLogLog, reconciliation, retroactive invalidation and reproducible history are
covered; fraud detection, ad serving and build cost are dismissed aloud.
