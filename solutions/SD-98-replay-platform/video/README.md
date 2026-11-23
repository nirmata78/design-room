# SD-98 · Reproducible replay & regression-gate platform — reference-solution video (compact cut)

**Length:** 62:45 · 126 logical slides, 473 frames · 7,122 spoken words · 1080p, sidecar captions.
**Format:** the compact cut (GUIDELINES §3.4): 6 challenges, no drill interlude, no build-cost chapter.
**Files (local, gitignored):** `replay-platform-reference.mp4`, `.srt` (upload to YouTube), `.vtt`. Booklet: `../SD-98_Replay_Platform_Reference_Design.pdf`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 0 Cold open |
| 2:37 | 1 Requirements and scope |
| 7:28 | 2 Estimates |
| 11:02 | 3 Theory |
| 19:16 | 4 API and entities |
| 22:26 | 5 High-level design |
| 28:30 | 5.1 Components and technologies |
| 34:56 | 5.2 When you don't need all this |
| 36:10 | 6 Bridge |
| 36:56 | 7 Challenges |
| 37:13 | 7.1 Challenge 1: Same build, two answers |
| 41:37 | 7.2 Challenge 2: A perception change |
| 45:38 | 7.3 Challenge 3: Release day |
| 49:02 | 7.4 Challenge 4: The log does not react |
| 52:40 | 7.5 Challenge 5: Block or pass? |
| 56:33 | 7.6 Challenge 6: The gate passed |
| 60:39 | 8 Recap |

## Challenges

1. Same build, two answers (crux): simulated clock, (time, topic, sequence) delivery, seeds from the manifest, deterministic GPU kernels; double runs.
2. A perception change: Merkle stage keys; blob before index; hermetic sandbox.
3. Release day: Kueue: a reserved gate queue, team quotas with borrowing, preemption at stage ends; nightly pre-warm.
4. The log does not react: divergence scoring; closed loop with pinned agent models.
5. Block or pass?: paired differences against the last release, bootstrap intervals, a versioned policy, recorded overrides.
6. The gate passed (observability): V4 gate auditor: a planted regression, double runs, cache audit, coverage; SLIs.

## Rebuild

```bash
solutions/SD-98-replay-platform/video/build-video.sh
solutions/SD-98-replay-platform/build-sd-booklet.sh SD-98_Replay_Platform_Reference_Design
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-98-replay-platform/video/publish/meta.json
```

## QA done (2026-11-22)

- Layout gate: 126 slides, **0 failures**, 3 warnings (dense technology slides, 96–108 words).
- ffprobe: H.264 + AAC, 1920 × 1080, 17 chapters, no subtitle stream, 62.8 min.
- Captions: 836 cues, no SRT line over 42 characters, every VTT cue with a `<v Name>` span.
- Eight frames sampled; Whisper check on 20 excerpts: only homophones (cache/cash, Merkle/markle).
- Not watched end to end by a person.

## Canon check

See `OUTLINE.md` § Canon check.
