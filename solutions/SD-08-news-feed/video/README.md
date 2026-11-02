# SD-08 news feed — mock-round video (v3, Staff L6/L7)

A narrated mock system-design round at the **Staff L6/L7** bar, **43:48 at 1080p, 23 chapters, 74 numbered slides** (AUX = EM layer, optional), in local
Kokoro voices (interviewer, candidate, candidate key lines spoken slower, coach) with burned-in captions and
chapters. Built with the `system-design-video` skill to `slide-video-kit/STANDARD.md`; content follows
`../../SD-08-news-feed.md`.

| File | Role |
|---|---|
| `feed-mock.script.md` | the spoken script: `[slide: v-NN]` / `[pause: s]` cues, `I:` / `C:` / `V:` (key line) / `N:` coach |
| `video-slides.html` + `video.css` + `deck.css` | 74 one-idea 16:9 slides; diagrams inlined from `svg/` |
| `diagrams.py` → `svg/` | C4 context, write-path and read-path container views, the feed-service component view, six sequences (outbox/CDC, publish, read, celebrity merge, delete on read, rebuild), push vs pull, the follower tail, a Chen conceptual ERD, the physical tables, wide-column partitions, the Redis key space and its writers, fan-out routing on `authorTier`, the fan-out tiers, the 48-hour delta, phasing, four follow-up diagrams |
| `build-video.sh` | diagrams → slides → `frames/` → `feed-mock.mp4` (`--frames` stops after the frames) |

Shape: requirements (the maximum follower count), the thesis ("push for most accounts, pull for celebrities"), four
numbers (the celebrity post is a hundred million writes; IDs not bodies, 4 TB vs 250 TB), API and cursor, stores, the
C4 walk, three deep dives (the celebrity threshold and crossing, deletes and blocks on the read path, a lost timeline
shard), the 48-hour catch-up as a mid-round delta, failures, freshness SLO, cost, phasing and teams, the close; then
four manager follow-ups: **(1)** the ranking team wants 300 ms; **(2)** a timeline cluster is lost on a Sunday
evening; **(3)** pure pull to hybrid in one quarter; **(4)** the timeline memory bill doubled. QA: Whisper excerpts
76–88% (homophones), a sync probe at 19:40, sampled frames; not watched end to end. The MP4 and `frames/` are
gitignored; rebuild with `video/build-video.sh` (about 15 minutes).

**v2 (2026-10-29)** adds, per `STANDARD.md` §1a: estimates as calculations (slides 9–12), wire formats for publish and the feed page with a signed cursor (14–16), the Redis key space and an ERD (17–18), three technology-vs-alternatives tables (20–22), fan-out worker and read-path pseudo-code (27, 29), the follower-threshold table (34), cost arithmetic (47), and a fifth technical follow-up, the power reader (59–60). Phasing and teams are AUX. QA: Whisper 72–89%, sync probe at 20:00, sampled frames; not watched end to end. v1 is in `.v1-em-2026-10-29/`.

**v3 (2026-10-29, the author's review of v2: "too quick to follow")** follows `STANDARD.md` §1b. New: a vocabulary
slide plus pictures for push vs pull and the follower tail (7–9); the ranking service's request and response (20);
the data model as a Chen conceptual ERD, then physical tables, a wide-column explainer, the Redis keys with arrows
between them, and who writes each key (21–26); outbox vs CDC and its sequence (32–33); fan-out routing on
`authorTier` (35); each path told as C4 → sequence → code, with the code split into two readable slides per path
(write 31–37, read 38–42). Every diagram is walked box by box or message by message. The script grew from 3,400 to
5,800 words. QA: Whisper excerpts 76–86% (all flagged words homophones: cache/cash, dedup), sync probe at 40:00, sampled frames; not watched end to end. Copied to Drive as `Interview videos/System design/SD-08-news-feed.mp4`. v2 is in `.v2-staff-2026-10-29/`.
