# System design: building blocks and concepts, a narrated course

Seventeen parts, about 7¾ hours, at Staff depth: 195 concepts and 22 building blocks, each explained
far enough to survive three "why?" in a row. Every part is one source file with slides and narration
together. `course.py` compiles it, renders the slides, voices it with Kokoro, and builds a 1080p MP4
with burned captions and chapters.

The videos are not in the repository. They are built into `~/Movies/SD-Building-Blocks-course/`
and stay there; they are not copied to Google Drive or anywhere else.

## The parts

| Part | Title | Length | Chapters | Concepts |
|---|---|---|---|---|
| 1 | Estimation that changes the design | 27:23 | 15 | 11 |
| 2 | Consistency, time and failure | 31:55 | 19 | 15 |
| 3 | Consensus | 20:12 | 14 | 8 |
| 4 | Coordination services | 23:19 | 11 | 6 |
| 5 | Replication | 32:16 | 18 | 14 |
| 6 | Partitioning and placement | 26:48 | 15 | 11 |
| 7 | Storage engines and blob storage | 32:40 | 19 | 15 |
| 8 | Transactions and concurrency control | 28:04 | 14 | 10 |
| 9 | Caching | 27:13 | 15 | 11 |
| 10 | Logs, queues, streams and sketches | 35:04 | 21 | 17 |
| 11 | Networking, the edge and API contracts | 35:15 | 20 | 16 |
| 12 | Rate limiting and overload control | 21:52 | 13 | 9 |
| 13 | Reliability patterns | 30:25 | 18 | 14 |
| 14 | Observability and time-series storage | 22:17 | 15 | 11 |
| 15 | Scheduling and control planes | 20:38 | 13 | 9 |
| 16 | Security, operating and evolving systems, the manager layer | 34:10 | 22 | 18 |
| 17 | The building blocks | 15:35 | 11 | 22 |
| | **Full course** (`SD-Full-Course.mp4`, 273 chapters) | **7:45:15** | | **217** |

`INDEX.md` lists every concept with its part, section and timestamp. Task videos cite those rows
instead of teaching a concept again.

## Files

| Path | What it is |
|---|---|
| `src/chNN.txt` | The source of part NN: slides (`= type flags \| kicker \| title`), concept markers (`@ ID`), narration (`N:` narrator, `V:` the line to say, `I:` interviewer, `C:` candidate) |
| `concepts.tsv` | The concept register: `id · name · tier · part · form`. Drives `coverage` and `INDEX.md` |
| `diagrams/pNN.md` | Figure specifications, one section per figure |
| `diagrams_pNN.py`, `dg.py` | The figures as code (shared helpers in `dg.py`) → `svg/pN-*.svg`. Part 17 reuses figures from earlier parts |
| `course.py` | The builder (commands below) |
| `build_cached.py`, `say.py`, `render_check.py` | Voice cache, spoken-only respellings, frame render with an overflow check |
| `sd.css`, `deck.css`, `video.css` | Slide styles |
| `claims/pNN.md` | The arithmetic ledger of each part: every derived number with its expression, recomputed by `claims_check.py` |
| `claims_dump.py` | Prints the slides of a part that carry numbers, as input for a ledger |
| `companion/SD-Building-Blocks-Companion.md` | The written companion, extracted from the sources by `course.py companion`; `build-sd-booklet.sh` turns it into a PDF (the PDF is gitignored) |
| `tests/` | `test_course.py`, the sample part `sample.txt` and its golden output |
| `INDEX.md` | Generated: concept → part → section → timestamp |

## Commands

```bash
cd theory/video
./course.py compile [NN…]      # lint and counts; writes ~/.cache/sd-course/build/chNN/
./course.py frames  [NN…]      # 1080p frames, overflow check, SD-Part-NN-slides.pdf
./course.py video   [NN…] -j3  # MP4s; only changed narration lines are re-voiced
./course.py coverage           # every concept homed exactly once, in its part
./course.py merge              # SD-Full-Course.mp4, chapters combined
./course.py index              # INDEX.md, with timestamps once the MP4s exist
./course.py companion [NN…]    # companion/SD-Building-Blocks-Companion.md
(cd companion && ./build-sd-booklet.sh SD-Building-Blocks-Companion)   # companion PDF
./claims_check.py [NN…] --write   # recompute every derived number in claims/
python3 -m unittest discover tests  # builder tests (from theory/video)
```

To fix a mispronounced term, add a respelling to `say.py` (never respell in a transcript), rebuild
the parts that speak it, then `merge` and `index` again.

## The reading plan

The course assumes some chapters have been read and does not retell them. Chapter numbers and
titles were checked against the books' online tables of contents on 2026-11-12. DDIA is the first
edition (2017). "Must" means assumed read.

| Source | Must read | Read when the part needs more |
|---|---|---|
| **Site Reliability Engineering** (free at `sre.google/sre-book`) | ch. 3 Embracing Risk · ch. 4 Service Level Objectives · ch. 6 Monitoring Distributed Systems · ch. 19 Load Balancing at the Frontend · ch. 20 Load Balancing in the Datacenter · **ch. 21 Handling Overload** · **ch. 22 Addressing Cascading Failures** · ch. 23 Managing Critical State · ch. 24 Distributed Periodic Scheduling with Cron · ch. 26 Data Integrity | ch. 2 The Production Environment at Google · ch. 17 Testing for Reliability · ch. 25 Data Processing Pipelines · ch. 27 Reliable Product Launches at Scale |
| **The Site Reliability Workbook** (free at `sre.google/workbook`) | ch. 2 Implementing SLOs · ch. 5 Alerting on SLOs · **ch. 12 Introducing Non-Abstract Large System Design** (read it twice) · ch. 16 Canarying Releases | ch. 11 Managing Load · ch. 14 Configuration Design and Best Practices · ch. 17 Identifying and Recovering from Overload |
| **Designing Data-Intensive Applications** (1st ed.) | ch. 5 Replication · ch. 6 Partitioning · ch. 7 Transactions · ch. 8 The Trouble with Distributed Systems · ch. 9 Consistency and Consensus · ch. 11 Stream Processing | ch. 3 Storage and Retrieval · ch. 1 (percentiles, load) · ch. 4 Encoding and Evolution · ch. 12 (end-to-end argument, request IDs) |
| **Software Engineering at Google** (free at `abseil.io/resources/swe-book`) | — | ch. 15 Deprecation · ch. 22 Large-Scale Changes · ch. 14 Larger Testing · ch. 1 (Hyrum's Law) |
| **Papers** | Raft (extended, sections 5 and 8) · "The Chubby Lock Service" · Spanner (sections 3 and 4) · "The Tail at Scale" · "Scaling Memcache at Facebook" (section 3) | Bigtable · Dynamo · GFS and the Colossus posts · Borg · Monarch · "The Dataflow Model" · "Paxos Made Live" · Kleppmann, "How to do distributed locking" |

## How it was checked

- Every frame of every part looked at on contact sheets; zero lint and zero overflow.
- Every derived number recomputed (`claims/`, 360 rows, none off); wording notes for the author are
  at the end of each ledger.
- Pronunciation: every respelled key and every acronym-like term in the narration was voiced and
  transcribed with Whisper; the terms it misheard got respellings and their parts were rebuilt.
- Each MP4: 1920×1080, AAC, chapters equal to the part's sections, no subtitle stream, a sync probe
  near the end. **Nobody has watched the course end to end.**
- Not yet re-checked: the Google Cloud product roles in part 17 against the Architecture Center.
