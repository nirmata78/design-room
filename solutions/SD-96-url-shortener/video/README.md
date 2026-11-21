# SD-96 · URL shortener: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 71:02**, 18 chapters, **153 numbered slides**, **8,764 spoken
words** (candidate 83.7 %, interviewer 4.1 %, key line 8.1 %, coach 4.2 %). Scripted walkthrough with synthetic voices;
figures are illustrative, not any company's numbers. **The technical content has not been reviewed by a person, and the
video has not been watched end to end.** It replaces an earlier 20-minute mock round (retired) as the
reference for this question. Written companion: `../SD-96_URL_Shortener_Reference_Design.md` (and PDF).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 02:28 | 1 Requirements and scope |
| 06:57 | 2 Estimates |
| 11:37 | 3 Theory |
| 20:25 | 4 API and entities |
| 24:04 | 5 High-level design |
| 32:41 | 6 Bridge |
| 33:28 | 7 Challenges |
| 33:46 | 7.1 Two servers, one code |
| 38:56 | 7.2 Codes in order |
| 42:57 | 7.3 One link at 40,000 clicks a second |
| 47:10 | 7.4 301 or 302? |
| 50:38 | 7.5 Dead everywhere in five minutes |
| 55:07 | 7.6 Counting without slowing the redirect |
| 58:39 | 7.7 A region goes dark |
| 62:18 | 7.8 How would you know it is broken? |
| 65:54 | 8 Build cost (AUX) |
| 68:11 | 9 Recap |

## The eight challenges

| # | Challenge | The fix |
|---|---|---|
| 1 | Two servers, one code | Leased ID ranges; the unique constraint decides; aliases of 8+ characters |
| 2 | Codes in order | A keyed permutation (Feistel, cycle walking); a 404 rate limit |
| 3 | One viral link | In-process cache on every server; single flight; negative caching |
| 4 | 301 or 302 | 302 by default; edge caches 60 s and can be purged; 301 opt-in |
| 5 | Takedown in five minutes | Status, direct shared-cache delete, invalidation, purge; lifetimes that sum to about 2 min |
| 6 | Counting | After the answer: buffer, log, aggregator; event IDs and de-duplication if billed |
| 7 | A region goes dark | Regional replicas; a slice of the ID space per region |
| 8 | How would you know | Create-then-follow probes, an hourly synthetic takedown, symptom pairs |

## Rebuild

```bash
solutions/SD-96-url-shortener/video/build-video.sh            # diagrams -> slides + script -> frames -> url-shortener-reference.mp4
solutions/SD-96-url-shortener/video/build-video.sh --frames   # stop after the frames
solutions/SD-96-url-shortener/build-sd-booklet.sh SD-96_URL_Shortener_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-96-url-shortener/video/publish/meta.json
```

Slides and script are generated together from `src/*.py` (the SD-94 DSL): edit the sources, not `video-slides.html` or
the script. Every frame has exactly one cue. The MP4 stays local; never copy it to a cloud folder.

## QA done

- ffprobe: H.264 1920×1080 + AAC + chapter data, no subtitle stream, 18 chapters, 71:02.
- All 153 frames read on contact sheets; fixed: two challenge slides whose diagram shrank (strips moved to chips), the
  physical ERD (became a table), a code label (now "python" / "wire format"), an overlong closing card.
- Audio (faster-whisper, 6 × 45 s excerpts): confidence −0.16 to −0.30, 8 substitutions, all homophones
  (phishing/fishing, cache/cash, poll/pull, aloud/allowed).
- Sync probe at 60:12: the transcribed line and the burned caption 8 s later match.
- Eight frames sampled across the length, captions and slides correct.
- Booklet: 26 pages, 9.6k words, built clean (≈ glyph fixed), no leaked fences; all pages tiled and looked at, two zoomed.

## Canon check

| Canonical point | Covered at, or dismissed because |
|---|---|
| Read:write ratio and capacity over the service's life | Ch. 1 Q1–2; ch. 2 |
| Code length from capacity over a 62-character alphabet | Ch. 2 (six against seven, with headroom) |
| Hash-and-truncate against counter + base-62 | Ch. 3 options matrix rows A, C, D; C1 |
| 301 against 302, tied to analytics and load | C4 |
| Cache in front of the store | V2; C3 |
| Unique IDs in a distributed deployment | M1; C1; C7 (regional slices) |
| Unique constraint as the final authority; alias race | M3; C1 |
| Analytics off the critical path | M5; C6 |
| Bloom filter to test whether a code exists | Dismissed: the constraint answers it on insert; a filter adds a second truth |
| Rate limiting the create API | API slide (per-key limit) |
| Database scaling, replication, multi-region | C7 |
| Hot key / viral link | C3 (beyond the standard treatments) |
| Takedown through every cache layer | C5 (beyond the standard treatments) |
| Enumeration of sequential codes | C2 |
| What changed since older treatments | Edge platforms expose purge APIs in seconds; browser caching of 301 unchanged |

## Publish kit

`publish/`: YouTube title (89/100), description with chapters (2,991/5,000), tags, thumbnail (checked), LinkedIn post
(hook 85 characters) and first comment. Not uploaded, not posted.
