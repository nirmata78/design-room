# SD-96 · URL shortener: reference-solution video

Staff bar (L6/L7), manager layer marked AUX. **Length 1:45:45**, 19 chapters, **171 logical slides shown as 643 reveal
frames**, **12,719 spoken words** (candidate 85.6 %, interviewer 3.4 %, key line 5.6 %, coach 5.4 %). Rebuilt 2026-11-21 to
the revised standard (`.claude/skills/reference-solution/GUIDELINES.md`): progressive disclosure (tables row by row, diagrams
drawn in request-flow order), the Google visual style (Google colours; Plus Jakarta Sans, Inter, Roboto Mono; see `.claude/skills/reference-solution/DESIGN-TOKENS.md`), **no burned-in captions** (`url-shortener-reference.srt` / `.vtt`
beside the MP4), C4 context in chapter 1, the container view right after V3, a sequence for every flow, and a new sub-chapter
5.1 with C4 component views, a technology slide per container and a drill interlude. Every technology fact comes from
`../stack.json` (slides, C4 labels, booklet Stage 5, outline); every challenge's fix slide names the tool it rejects. Scripted walkthrough with synthetic voices; figures are
illustrative, not any company's numbers. **The technical content has not been reviewed by a person, and the video has not
been watched end to end.** Written companion: `../SD-96_URL_Shortener_Reference_Design.md` (and PDF).

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | 0 Cold open |
| 03:17 | 1 Requirements and scope (C4 context) |
| 09:02 | 2 Estimates |
| 13:49 | 3 Theory (mechanisms at work: a lease through Raft, cache-aside with single flight) |
| 27:31 | 4 API and entities |
| 31:29 | 5 High-level design (V1–V3, C4 containers, four flows and four sequences) |
| 43:19 | 5.1 Components and technologies (ends with the drill interlude) |
| 62:01 | 6 Bridge |
| 63:04 | 7 Challenges |
| 63:22 | 7.1 Two servers, one code |
| 69:20 | 7.2 Codes in order |
| 74:09 | 7.3 One link at 40,000 clicks a second |
| 78:55 | 7.4 301 or 302? |
| 82:44 | 7.5 Dead everywhere in five minutes |
| 87:37 | 7.6 Counting without slowing the redirect |
| 91:35 | 7.7 A region goes dark |
| 95:48 | 7.8 How would you know it is broken? |
| 100:02 | 8 Build cost (AUX) |
| 102:34 | 9 Recap |

## The stack (sub-chapter 5.1)

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Link store | PostgreSQL, 16 shards per region, a primary per region's slice | Cassandra/Scylla, DynamoDB, one big PostgreSQL | PK is the uniqueness authority; no last-writer-wins across regions |
| Allocator | etcd, 3 members per region (Raft), Txn on ModRevision | ZooKeeper (honest equal), Redis INCRBY, Cassandra counter, PostgreSQL sequence | linearizable CAS; asynchronous replication can reissue a range |
| Shared cache | Redis Cluster, 6 + 6 per region, allkeys-lfu | Memcached (honest equal), Hazelcast, none | a replica per shard: no cold slice |
| In-process | ristretto + singleflight (Caffeine in Java) | plain LRU, sidecar, none | TinyLFU admission survives scans |
| Click log | Kafka, 32 partitions by code, pre-aggregated per second | RabbitMQ, Kinesis/Pub-Sub (equals on that cloud), direct writes | replay to recount |
| Counting | Flink (1-min event-time windows) → ClickHouse SummingMergeTree | Spark (equal), nightly batch, Cassandra counters, PostgreSQL table | idempotent, windowed, columnar |
| Invalidation | Kafka topic + CDN surrogate-key purge | Redis Pub/Sub, polling, purge by URL | a reconnecting server replays |
| Services | Go on Kubernetes, 3 zones | Java (equal), serverless, own edge | 20 ms p99, predictable pauses |

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
solutions/SD-96-url-shortener/video/build-video.sh            # diagrams -> slides + script -> frames -> MP4 + .srt + .vtt
solutions/SD-96-url-shortener/video/build-video.sh --frames   # stop after the frames
solutions/SD-96-url-shortener/build-sd-booklet.sh SD-96_URL_Shortener_Reference_Design   # the written reference design (PDF)
python3 ~/.claude/skills/slide-video-kit/scripts/publish_kit.py solutions/SD-96-url-shortener/video/publish/meta.json
```

Slides and script are generated together from `src/*.py`: edit the sources, not `video-slides.html` or the script.
`gen.py` refuses a slide whose `[+]` markers do not reveal exactly its units. The MP4 and captions stay local.

## QA done (2026-11-21)

- `gen.py`: every slide's reveal markers match its units (two miscounts caught by the check and fixed).
- ffprobe: H.264 1920×1080 + AAC + chapter track, **no subtitle stream**, 19 chapters, 1:45:45.
- Captions: 1,423 cues, 00:00:01.2 to 01:45:42, at most two lines of ≤ 42 characters (SRT including the `Name: ` prefix);
  every VTT cue carries a `<v Name>` voice span. Eight over-long cues from the first render were re-cut with the kit's new
  `cue_groups()` (the kit fix applies to the next render).
- Frames: the last step of all 169 slides read on contact sheets (16 per sheet), plus the step sequences of the smoke-test table,
  sequence and baseline; fixed: three technology slides and the options matrix overflowing (compact `xs` tables, one row cut),
  edge labels overlapping in the component views, a sequence note contradicting the narration (region prefix → inverse permutation).
- Eight frames sampled from the MP4 across the length, including mid-crossfade: nothing drawn over the slide.
- Audio (faster-whisper, 20 × 45 s excerpts, 6 of them in 5.1): confidence −0.12 to −0.36; 18 substitutions, all homophones
  (cache/cash, writes/rights, Redis/"reddies"); "etcd" voiced as et-see-dee.
- Sync probe at 61:34: caption and the just-revealed strip match.
- Booklet: 33 pages, built clean; Stage 5 generated from `stack.json`, its four pages read as images.
- Second pass (same day): drill interlude, fix-slide rejections and the alias home-region rule. Last step of the drill slide
  and all eight fix slides read; Whisper on the drill and six rejection lines (3.7 min): only homophones (Redis/"reddy's");
  sync probes at 60:20 (drill, first row only) and 89:20 (challenge 6, the rejected line shown).

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
