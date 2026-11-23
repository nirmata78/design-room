# SD-08 · News feed / home timeline: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 1:31:59**, 19 chapters, **176 numbered slides** in **586 reveal frames**, **10,915 spoken words**
(candidate 83.1 %, interviewer 4.1 %, key line 6.6 %, coach 6.2 %). Built 2026-11-20 in the SD-94 reference format. Scripted
walkthrough with synthetic voices; figures are illustrative, not any company's numbers. **The technical content has not been
reviewed by a person, and the video has not been watched end to end.** It replaces the earlier mock-round videos, which have
been retired.

Written companion: [`../SD-08_News_Feed_Reference_Design.md`](../SD-08_News_Feed_Reference_Design.md) (PDF built locally, 30 pages,
about 10,900 words). Outline and budget: [`OUTLINE.md`](OUTLINE.md).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:11 | 1 Requirements and scope |
| 08:13 | 2 Estimates |
| 13:50 | 3 Theory |
| 23:05 | 4 API and entities |
| 26:44 | 5 High-level design |
| 37:33 | 5.1 Components and technologies |
| 51:27 | 6 Bridge |
| 52:08 | 7 Challenges |
| 52:27 | 7.1 Challenge 1: The celebrity post |
| 56:59 | 7.2 Challenge 2: Where is the line, and who crosses it? |
| 1:01:49 | 7.3 Challenge 3: Delete, block, unfollow |
| 1:05:44 | 7.4 Challenge 4: Twice, or never |
| 1:09:36 | 7.5 Challenge 5: A timeline shard is gone |
| 1:14:20 | 7.6 Challenge 6: The ranker takes 300 ms |
| 1:18:32 | 7.7 Challenge 7: Catch up on the last 48 hours |
| 1:22:22 | 7.8 Challenge 8: How would you know the feed got worse? |
| 1:26:42 | 8 Build cost |
| 1:28:57 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | The celebrity post | Pull it: one write to the author's recent list; priority lanes for bursts |
| 2 | Where is the line, and who crosses it? | Three tiers from both sides of the arithmetic, hysteresis, no backfill; power readers precomputed |
| 3 | Delete, block, unfollow | Correctness on the read path; cleanup is cosmetic; a recently-removed set as backstop |
| 4 | Twice, or never | A set keyed by post ID; a (score, ID) cursor; the session's ranked list |
| 5 | A timeline shard is gone | Rebuild by pull, coalesced, rate-limited, degraded beyond the limit |
| 6 | The ranker takes 300 ms | A hard deadline, a counted fallback, an owner for the fallback rate |
| 7 | Catch up on the last 48 hours | The source of truth through the rebuild path, cached; a view only if it earns it |
| 8 | How would you know it got worse? | Synthetic probes per tier, quality metrics, symptom pairs, the memory lever |

## Rebuild

```bash
solutions/SD-08-news-feed/video/build-video.sh            # diagrams -> slides + script -> frames -> news-feed-reference.mp4
solutions/SD-08-news-feed/video/build-video.sh --frames   # stop after the frames
solutions/SD-08-news-feed/build-sd-booklet.sh SD-08_News_Feed_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-08-news-feed/video/publish/meta.json
```

The slides and the script are generated together from `video/src/*.py` (the SD-94 DSL, plus KaTeX formulas and highlighted
code with a language flag): edit the sources, not `video-slides.html` or the script. Every frame has exactly one cue.

## QA done

- ffprobe: H.264 1920×1080 + AAC, 18 chapters, no subtitle stream; 73:52.
- Every one of the 164 frames read on contact sheets before the voice build (fixed: an overflowing code slide, a shrunken
  baseline, sequence widths); every SVG checked on sheets.
- Whisper (faster-whisper base.en) on 20 excerpts of 45 s: confidence −0.14 to −0.28; 21 suspect substitutions, all
  homophones or near-homophones (write/right, cache/cash, waits/weights, bill/build), none a mispronounced term.
- Eight frames sampled across the length with their burned captions: slide and caption agree, including at 73:00 (sync).
- **Not watched end to end.**

## Canon check

| Canonical point | Source | Covered at, or dismissed because |
|---|---|---|
| Feed publishing and feed retrieval as two flows | book ch. 11; cue sheet | FR1, FR2 flows; V2 |
| Fan-out on write against fan-out on read, pros and cons | book; all | Theory 3 and 5; C1 |
| Hybrid: push for most, pull for celebrities | book; cue sheet | Pick E; C1, C2 |
| Inactive users: don't fan out to them | book (as a pull advantage); cue sheet | Ch. 2; M3; ch. 8 lever |
| Graph store for follow relations; filter by mute settings | book | Ch. 4; FR4; C3 |
| News feed cache stores IDs, not objects | book; cue sheet | M4; ch. 2 (4 TB against 250 TB) |
| Five cache tiers (feed, content with hot set, graph, action, counters) | book | Ch. 4 physical; counters dismissed aloud as a separate service |
| Message queue between post and fan-out | book | M7; V2 (outbox + log) |
| Ranking as a separate stage with a budget | cue sheet | M6; C6 |
| Cursor pagination | cue sheet | C4 |
| Celebrity threshold and its transition | cue sheet (crux) | C2 |
| Deletes and blocks | cue sheet | C3 |
| Cache loss and rebuild | cue sheet | C5 |
| 48-hour catch-up curveball | cue sheet | C7 |
| Rate limiting, authentication, CDN for media | book (wrap-up) | Dismissed aloud in ch. 1 OUT: standard edge concerns, not this question's grade |
| What changed since the book | — | Ranked feeds with a candidate-generation stage are now the default; "chronological only" is a user setting, which C7 covers |

## Retrofit, 2026-11-22

Brought to the current standard by `RETROFIT.md`: the Google theme (`video.css`, `google-theme.css`), progressive reveal (every table row,
card, trace event and figure step appears as it is spoken), sidecar captions (`.srt` and `.vtt` beside the MP4, nothing burned in), the
technology chapter **5.1** generated from `../stack.json` (container view with technologies, one slide per technology with its rejected
alternatives, the stack on one slide, the drill interlude) and a **Rejected** line on every challenge's fix slide.

**109 of the 176 slides were written before reveal markers existed; their markers were placed automatically** (`dsl.META["automark"]`:
the narration is cut at sentences and dealt to the reveal units by word overlap). Watch those slides and move a marker by hand where one
lands badly. Not done in this pass: the C4 context moved to the end of chapter 1, a mechanism map in the theory chapter, extra sequences per
requirement, component views. The previous sources are kept in `.v1-retrofit-2026-11-22/` until the author has watched this version.
