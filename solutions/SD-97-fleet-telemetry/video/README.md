# SD-97 · Device telemetry & live location map — reference-solution video (compact cut)

**Length:** 60:14 · 134 logical slides, 502 frames · 6781 spoken words · 1080p, sidecar captions.
**Format:** the compact cut (GUIDELINES §3.4): 6 challenges, no drill interlude, no build-cost chapter.
**Files (local, gitignored):** `fleet-telemetry-reference.mp4`, `.srt` (upload to YouTube), `.vtt`. Booklet: `../SD-97_*_Reference_Design.pdf`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 0 Cold open |
| 3:30 | 1 Requirements and scope |
| 7:25 | 2 Estimates |
| 9:59 | 3 Theory |
| 16:15 | 4 API and entities |
| 19:02 | 5 High-level design |
| 24:08 | 5.1 Components and technologies |
| 29:42 | 5.2 When you don't need all this |
| 30:52 | 6 Bridge |
| 31:37 | 7 Challenges |
| 31:56 | 7.1 Challenge 1: Out of the tunnel |
| 36:09 | 7.2 Challenge 2: Downtown at six |
| 40:02 | 7.3 Challenge 3: Five thousand viewers |
| 43:36 | 7.4 Challenge 4: A city comes back |
| 47:46 | 7.5 Challenge 5: One vehicle, one hour |
| 52:57 | 7.6 Challenge 6: Forty seconds stale |
| 57:57 | 8 Recap |

## Challenges

1. Out of the tunnel (crux): (epoch, seq) filter; live overwrites only with newer; history takes all, deduplicated.
2. Downtown at six: log keyed by vehicle; cells indexed at 9 with counts at 6 and 7; hot-cell split.
3. Five thousand viewers: cell subscriptions and a per-pod change feed; snapshot on pan.
4. A city comes back: three lanes on the vehicle; capped backfill to history only.
5. One vehicle, one hour: day × 256 buckets sorted by (vehicle, seq); pinned snapshot; ~10 s.
6. Forty seconds stale (observability): V4 freshness probe with canary vehicles through every map pod.

## Rebuild

```bash
solutions/SD-97-fleet-telemetry/video/build-video.sh
solutions/SD-97-fleet-telemetry/build-sd-booklet.sh SD-97_<Title>_Reference_Design
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-97-fleet-telemetry/video/publish/meta.json
```

## QA done (2026-11-22)

- Layout gate: 134 slides, 0 failures, 0 warnings (min text 22 px, min diagram label 18 px at 1080p).
- ffprobe: H.264 + AAC, 1920 × 1080, 17 chapters, no subtitle stream, 60.2 min.
- Captions: 807 VTT cues, each with a `<v Name>` span; 0 SRT lines over 42 characters.
- Eight frames sampled across the length; Whisper check on 20 excerpts (6 suspect substitutions, read by hand).
- Not watched end to end by a person.

## Canon check

See `OUTLINE.md` § Canon check.
