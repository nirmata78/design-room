# SD-24 · Distributed lock / coordination service: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 78:16**, 17 chapters, **166 numbered slides**, **11,073 spoken words** (candidate 88.5 %, interviewer 4.2 %, key line 5.8 %, coach 1.5 %). Scripted walkthrough with synthetic voices; figures are illustrative, not any company's numbers. **The technical content has not been reviewed by a person, and the video has not been watched end to end.**

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:22 | 1 Requirements and scope |
| 08:16 | 2 Estimates |
| 14:04 | 3 Theory |
| 25:08 | 4 API and entities |
| 31:53 | 5 High-level design |
| 42:18 | 6 Bridge |
| 42:49 | 7 Challenges |
| 43:05 | 7.1 Challenge 1: The paused holder |
| 48:07 | 7.2 Challenge 2: The resource cannot check |
| 52:00 | 7.3 Challenge 3: Clocks and leases |
| 55:41 | 7.4 Challenge 4: Leader loss, partition, group loss |
| 60:40 | 7.5 Challenge 5: The top of the hour |
| 64:13 | 7.6 Challenge 6: A hot name, several locks |
| 67:52 | 7.7 Challenge 7: How would you know? |
| 71:40 | 8 Build cost |
| 75:53 | 9 Recap |

## The seven challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The paused holder | Fencing token checked at the resource |
| 2 | The resource cannot check | Ask first; then pick the cheapest place to enforce |
| 3 | Time | Durations, not timestamps |
| 4 | Leader loss, partition, and losing the group | Majority commit and terms, plus a leader lease and a grace period |
| 5 | The top of the hour | Partition by name, admit at the edge, retry with jitter |
| 6 | One hot name, and several locks at once | Bounded wait with directed hand-off |
| 7 | How would you know it is broken? | Measure the guarantee, not the machine |

## Rebuild

```bash
solutions/SD-24-distributed-lock/video/build-video.sh            # diagrams -> slides + script -> frames -> distributed-lock-reference.mp4
solutions/SD-24-distributed-lock/video/build-video.sh --frames   # stop after the frames
solutions/SD-24-distributed-lock/build-sd-booklet.sh SD-24_Distributed_Lock_Reference_Design   # the written reference design (PDF)
```

The slides and the script are generated together from `video/src/*.py`: edit the sources, not `video-slides.html` or the script. Every frame has exactly one cue. Needs the slide-video-kit, Kokoro TTS, pandoc, xelatex, plantuml, rsvg-convert.

## QA done

- `ffprobe`: H.264 1920x1080, AAC, a chapter data stream; no subtitle stream, no `.srt` beside the MP4.
- Audio intelligibility (`check_audio.py`, 6 excerpts of 60 s across the length): Whisper confidence -0.16 to -0.22; 11 differences, all homophones or splits (weight, right, be), none a mangled term.
- Sync probe at 75:00: the transcribed audio ("creep into a general key-value store ...") matches the burned caption on the frame 2 s later.
- Frames: all 166 slides read on contact sheets before the build; four more sampled from the finished MP4 (minutes 5, 20, 38, 55).
- **Not watched end to end.**

## Canon check

The points the standard treatments of this question make, and where this video covers them (or why it dismisses them).

For the video README, not for the screen. The source map is kept outside the tracked files.

| Canonical point | Covered at (chapter / slide) or dismissed because |
| --- | --- |
| A lock alone cannot make a system safe; a paused holder writes after expiry | Ch. 0 hook; ch. 3 mechanism M3; **C1** |
| Fencing tokens: monotonic, validated by the resource, equal vs smaller | **C1** (precision statement); API slide "Resource contract" |
| Leases with a TTL, not locks held until release | Ch. 3 M1, M5; FR2 flow |
| Consensus-backed replicated state; single cache node and a database row are not equivalent | Ch. 3 options matrix rows A, C, D; V2 |
| Quorum-of-caches debate: probabilistic safety, no token | Ch. 3 matrix row B; spoken in the matrix slide; **older source: "what changed since"**: conditional writes in object stores now make resource-side checks natural |
| Clock discipline: monotonic durations, conservative client deadline | Ch. 3 M4; **C3** |
| Safety against liveness, FLP-honest, fail closed | Ch. 3 part 2 and 3; **C4** |
| What the minority side of a partition sees | **C4** |
| Client that loses its lease mid-operation must stop | V3 SDK; FR2 flow step 5; **C1** |
| Do you even need a lock (idempotency, single-writer) | Ch. 0, **C2**, ch. 8 closing question |
| `SELECT FOR UPDATE` on a database row | Ch. 3 matrix row C: no lease, no token, tied to a connection; fine when the resource is in the same database |
| Reentrancy | Dismissed aloud on the API slide: a hold count in the SDK keyed by session, not server state; doubling writes for no gain |
| FIFO fairness, herd, deadlock, lock ordering | **C6** |
| Sharding by name, hot keys | **C5**, **C6** |
| Session heartbeats, grace period on failover | Ch. 3 M5; **C4** |
| Token continuity after restore or rebuild (epoch) | **C4** second fix |
| Observability, SLOs, error budget | **C7** |
| Multi-region | Out of scope in ch. 1; one slide in ch. 9; reason: cross-region quorum breaks the 20 ms target |
| Shared / read-write locks, watch API | Dismissed in ch. 1 (OUT): add behind the same API; no requirement |
| Build against adopt against don't, people and months | Ch. 8 |

