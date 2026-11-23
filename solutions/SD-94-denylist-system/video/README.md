# SD-94 · Blocking / denylist system: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 92:53** (re-cut 2026-11-20 with the course-builder pacing; v1 was 82:15), 17 chapters, **175 numbered slides**, **11,880 spoken words** (candidate 87.6 %, interviewer 4.3 %, key line 6.6 %, coach 1.6 %). Scripted walkthrough with synthetic voices; figures are illustrative, not any company's numbers. **The technical content has not been reviewed by a person, and the video has not been watched end to end.**

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:04 | 1 Requirements and scope |
| 10:44 | 2 Estimates |
| 18:01 | 3 Theory |
| 29:34 | 4 API and entities |
| 35:40 | 5 High-level design |
| 48:11 | 5.1 Components and technologies |
| 58:19 | 6 Bridge |
| 59:02 | 7 Challenges |
| 59:22 | 7.1 Challenge 1: The node that was offline |
| 1:04:15 | 7.2 Challenge 2: Order, duplicates, overlap |
| 1:09:37 | 7.3 Challenge 3: The bad push |
| 1:16:03 | 7.4 Challenge 4: Stale or no control plane |
| 1:21:45 | 7.5 Challenge 5: The list does not fit |
| 1:27:24 | 7.6 Challenge 6: A slow external source |
| 1:32:18 | 7.7 Challenge 7: How would you know? |
| 1:37:35 | 8 Build cost |
| 1:42:22 | 9 Recap |

## Re-cut 2026-11-20

Pacing from the course builder (`theory/video/course.py`), ported into `src/dsl.py`: silence and a title card before
every chapter and each of the seven challenges (new: 7 challenge cards with a one-sentence spoken intro), a beat after a
slide appears (longer for figures and tables) and after it ends (longer after key lines), and sentence beats inside
each line (`theory/video/build_cached.py`, which also caches voice lines). Monospace traces are now two-column
timeline tables in the body font; code and wire formats are larger and labelled. The v1 MP4, script and slides are in
`.v1-2026-11-12/`. QA: ffprobe (H.264/AAC 1080p, 17 chapters); Whisper on 4 excerpts, confidence −0.13 to −0.31,
3 substitutions, all homophones (trie/try); sampled frames. **Not watched end to end.**

## The seven challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The node that was offline | Manifest, delta window, snapshot fallback, chained checksums |
| 2 | Order, duplicates and overlap | One total order and per-key versions |
| 3 | The bad push | Treat the list like code |
| 4 | Stale, partitioned, or no control plane | A bound and an action, signed by the owner |
| 5 | The list does not fit | Filter in front, authoritative check behind, positive cache, and a smaller exact core |
| 6 | A slow external source | Prefer a bulk list; otherwise a verdict cache with a bound, a budget and a stated policy |
| 7 | How would you know it is broken? | Measure the promise, not the machine |

## Rebuild

```bash
solutions/SD-94-denylist-system/video/build-video.sh            # diagrams -> slides + script -> frames -> denylist-reference.mp4
solutions/SD-94-denylist-system/video/build-video.sh --frames   # stop after the frames
solutions/SD-94-denylist-system/build-sd-booklet.sh SD-94_Denylist_System_Reference_Design   # the written reference design (PDF)
```

The slides and the script are generated together from `video/src/*.py`: edit the sources, not `video-slides.html` or the script. Every frame has exactly one cue. Needs the slide-video-kit, Kokoro TTS, pandoc, xelatex, plantuml, rsvg-convert.

## QA done

- `ffprobe`: H.264 1920x1080, AAC, a chapter data stream; no subtitle stream, no `.srt` beside the MP4.
- Audio intelligibility (`check_audio.py`, 8 excerpts of 60 s across the length): Whisper confidence -0.15 to -0.23; 5 differences, all homophones or splits (pushed/push, skew, cached, seen). The first build had "denylist" heard as "dentalist"; respelled as `deny-list` in the script's `say:` list and rebuilt, and the difference is gone.
- Sync probe at 75:00: the transcribed audio ("The best question is which of these we are asked for ...") matches the burned caption on the frame 2 s later.
- Frames: all 168 slides read on contact sheets before the build (seven fixed: two overlong mechanism titles, a doubled escape in a chip, two lines past the right edge, a figure label overlap); six more sampled from the finished MP4.
- **Not watched end to end.**

## Canon check

The points the standard treatments of this question make, and where this video covers them (or why it dismisses them).

For the video README, not for the screen. The source map is kept outside the tracked files.

| Canonical point | Covered at (chapter / slide) or dismissed because |
| --- | --- |
| No network call on the request path; a local structure sized with arithmetic | Ch. 2 estimates; ch. 3 M1; options matrix rows A and D |
| Exact structures: sorted array or hash set for keys, radix trie for prefixes | Ch. 2; ch. 3 M1; ch. 4 physical model; **C2** |
| A Bloom filter says "definitely not listed", a hit needs confirmation | Ch. 2; **C5**. what changed since: hash-prefix lists are now one of several shapes; the principle (confirm a hit) is unchanged |
| Versioned snapshots plus incremental updates with a checksum | Ch. 3 M2; **C1** |
| Push plus pull backstop; relay tree; fan-out arithmetic | Ch. 2 fan-out; ch. 3 M3; V2 |
| Staged rollout, canary, kill switch, rollback of a bad configuration | Ch. 3 M5; **C3** |
| Staleness bound and fail-open against fail-closed | Ch. 3 M6; **C4**; the owner signs it |
| Ordering of add and remove; idempotent merge; tombstones | **C2** |
| An allowlist of ranges that must never be blocked | Ch. 1; ch. 3 M5 and M7; **C3** |
| A slow external source: mirror, cache with TTL, coalescing, budget, breaker, first-seen policy | **C6** |
| Audit: why was X served on day D | FR4; API `Explain`; **C7** |
| Propagation SLO as the contract between policy and platform owners | Ch. 1; ch. 8 |
| Layered rules: global plus regional | Ch. 1 IN scope; ch. 8 R2; dismissed from the walk-through: same pipeline, per-region artifact; one slide in ch. 5 |
| Per-entity enforcement point (IP at the edge, user id after authentication) | **C5** |
| Shared and rotating addresses; an address is not a person | Ch. 1 hook; **C5** |
| Rate limiting, abuse detection, volumetric attack scrubbing | Dismissed aloud in ch. 1 (OUT) with pointers to SD-25 and SD-43 |
| Buy against build against don't, people and months | Ch. 8 |

## Retrofit, 2026-11-22

Brought to the current standard by `RETROFIT.md`: the Google theme (`video.css`, `google-theme.css`), progressive reveal (every table row,
card, trace event and figure step appears as it is spoken), sidecar captions (`.srt` and `.vtt` beside the MP4, nothing burned in), the
technology chapter **5.1** generated from `../stack.json` (container view with technologies, one slide per technology with its rejected
alternatives, the stack on one slide, the drill interlude) and a **Rejected** line on every challenge's fix slide.

**116 of the 186 slides were written before reveal markers existed; their markers were placed automatically** (`dsl.META["automark"]`:
the narration is cut at sentences and dealt to the reveal units by word overlap). Watch those slides and move a marker by hand where one
lands badly. Not done in this pass: the C4 context moved to the end of chapter 1, a mechanism map in the theory chapter, extra sequences per
requirement, component views. The previous sources are kept in `.v1-retrofit-2026-11-22/` until the author has watched this version.
