# SD-29 · Device-fleet control plane (IoT) — reference-solution video (compact cut)

**Length:** 61:56 · 131 logical slides, 481 frames · 6798 spoken words · 1080p, sidecar captions.
**Format:** the compact cut (GUIDELINES §3.4): 6 challenges, no drill interlude, no build-cost chapter.
**Files (local, gitignored):** `device-fleet-reference.mp4`, `.srt` (upload to YouTube), `.vtt`. Booklet: `../SD-29_*_Reference_Design.pdf`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 0 Cold open |
| 2:52 | 1 Requirements and scope |
| 7:13 | 2 Estimates |
| 9:44 | 3 Theory |
| 16:57 | 4 API and entities |
| 19:36 | 5 High-level design |
| 25:41 | 5.1 Components and technologies |
| 31:48 | 5.2 When you don't need all this |
| 32:57 | 6 Bridge |
| 33:46 | 7 Challenges |
| 34:05 | 7.1 Challenge 1: A config that crashes the device |
| 38:48 | 7.2 Challenge 2: The rare revision |
| 43:35 | 7.3 Challenge 3: Six weeks offline |
| 47:18 | 7.4 Challenge 4: The reconnect storm |
| 51:44 | 7.5 Challenge 5: Telemetry, twice |
| 55:40 | 7.6 Challenge 6: Connected is not converged |
| 59:42 | 8 Recap |

## Challenges

1. A config that crashes the device (crux): pending until confirmed by a full round trip; three tries; last known good.
2. The rare revision: waves by strata, per-cell controls, automatic interval halts.
3. Six weeks offline: latest desired document, prerequisites first, level-triggered loop.
4. The reconnect storm: full jitter, per-node admission, a version-compare cache.
5. Telemetry, twice: (epoch, seq) dedup; cohort labels, never device IDs.
6. Connected is not converged (observability): V4 fleet census; convergence; blocked/rejected; SLIs.

## Rebuild

```bash
solutions/SD-29-device-fleet/video/build-video.sh
solutions/SD-29-device-fleet/build-sd-booklet.sh SD-29_<Title>_Reference_Design
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-29-device-fleet/video/publish/meta.json
```

## QA done (2026-11-22)

- Layout gate: 131 slides, 0 failures, 0 warnings (min text 22 px, min diagram label 18 px at 1080p).
- ffprobe: H.264 + AAC, 1920 × 1080, 17 chapters, no subtitle stream, 61.9 min.
- Captions: 837 VTT cues, each with a `<v Name>` span; 0 SRT lines over 42 characters.
- Eight frames sampled across the length; Whisper check on 20 excerpts (7 suspect substitutions, read by hand).
- Not watched end to end by a person.

## Canon check

See `OUTLINE.md` § Canon check.
