# SD-39 · Nearby drivers & ride matching — reference-solution video (compact cut)

**Length:** 60:47 · 131 logical slides, 469 frames · 6855 spoken words · 1080p, sidecar captions.
**Format:** the compact cut (GUIDELINES §3.4): 6 challenges, no drill interlude, no build-cost chapter.
**Files (local, gitignored):** `ride-matching-reference.mp4`, `.srt` (upload to YouTube), `.vtt`. Booklet: `../SD-39_*_Reference_Design.pdf`. Publish kit: `publish/`.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | 0 Cold open |
| 2:40 | 1 Requirements and scope |
| 6:34 | 2 Estimates |
| 9:39 | 3 Theory |
| 17:21 | 4 API and entities |
| 20:24 | 5 High-level design |
| 26:30 | 5.1 Components and technologies |
| 31:54 | 5.2 When you don't need all this |
| 33:07 | 6 Bridge |
| 33:52 | 7 Challenges |
| 34:05 | 7.1 Challenge 1: Two riders, one driver |
| 37:43 | 7.2 Challenge 2: The driver who vanishes |
| 42:09 | 7.3 Challenge 3: Boundaries and hot cells |
| 45:46 | 7.4 Challenge 4: A shard dies |
| 50:13 | 7.5 Challenge 5: Nearest is not closest |
| 54:28 | 7.6 Challenge 6: “No drivers” next to idle drivers |
| 58:29 | 8 Recap |

## Challenges

1. Two riders, one driver (crux): one matcher per city under an etcd lease; one conditional, fenced `UPDATE`.
2. The driver who vanishes: offer expiry, heartbeat leases on trips, idempotent accept by offer ID.
3. Boundaries and hot cells: expanding k-rings to 20 candidates; resolution 9 for crowded cells.
4. A shard dies: no replicas; refill from the next 4 s of reports; sequence numbers drop old positions.
5. Nearest is not closest: shortlist by distance, one ETA matrix per tick, min-cost batch assignment.
6. “No drivers” next to idle drivers (observability): V4 probe riders; idle-next-to-no; stale share; SLIs.

## Rebuild

```bash
solutions/SD-39-ride-matching/video/build-video.sh
solutions/SD-39-ride-matching/build-sd-booklet.sh SD-39_<Title>_Reference_Design
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-39-ride-matching/video/publish/meta.json
```

## QA done (2026-11-22)

- Layout gate: 131 slides, 0 failures, 2 warnings (min text 22 px, min diagram label 18 px at 1080p).
- ffprobe: H.264 + AAC, 1920 × 1080, 17 chapters, no subtitle stream, 60.8 min.
- Captions: 818 VTT cues, each with a `<v Name>` span; 0 SRT lines over 42 characters.
- Eight frames sampled across the length; Whisper check on 20 excerpts (9 suspect substitutions, read by hand).
- Not watched end to end by a person.

## Canon check

See `OUTLINE.md` § Canon check.
