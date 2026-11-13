# Plan 02 · System-design theory and building blocks: a narrated course at Staff depth

**Brief (private, read-only):** `private/02_Google_L6_SD_Concepts_and_Building_Blocks.md` — 244
concepts in 20 groups with a "be able to say" line and a tier each (Part B), 28 building blocks
(Part C), a task-to-group matrix (Part D), a module list (Part E), a reading list (Part F).
**Shared rules:** [`00-shared-rules-and-sources.md`](00-shared-rules-and-sources.md). Read it first.
**Format model:** the ten-part course in `~/Projects/gcp-ace-simulator/theory/video/` (one source file
per part, slides and narration together; `course.py` compiles, renders, builds and merges). Read its
`README.md`, `course.py` and one `src/ch04.txt` before anything else.
**Status file:** `plans/STATUS-02.md`.

## 1 · What gets built, and what changed in this revision

A course in `theory/video/` that teaches the concepts a Staff-level design round is certain to
touch, each deep enough to survive three "why?" in a row. Three decisions shape it:

1. **Fewer concepts.** 49 of the brief's 244 concepts (20%) and 6 of its 28 blocks are out (§2.1):
   everything in Tier C, the search group, and the Tier B items that only rare problems use.
2. **Staff depth on what remains** (§3): mechanism, the second level down, the alternative and its
   price, the failure, the line to say. No concept is a definition and a sentence.
3. **Books carry what books do well** (§2.3). Where a chapter of the SRE book, the SRE workbook or
   DDIA already teaches a topic thoroughly, the course does not retell it: the author reads the
   chapter, and the course spends its time on applying it under interview probing.

| Deliverable | Where | Notes |
|---|---|---|
| 17 part sources | `theory/video/src/chNN.txt` | The single source of slides and narration for a part |
| Diagrams | `theory/video/diagrams_pNN.py` → `theory/video/svg/pNN-*.svg` | About 170; one file per part so sessions do not collide |
| Builder | `theory/video/course.py`, `build_cached.py`, `say.py`, `render_check.py`, CSS | Ported from the model course (§4) |
| Concept register | `theory/video/concepts.tsv` | `id · name · tier · part · form`; 195 concepts and 22 blocks; drives the coverage check |
| **Course index** | `theory/video/INDEX.md` (generated) | Concept → part → section title → chapter timestamp. **Plan 01's videos point at these rows instead of re-teaching** |
| Claims ledger | `theory/video/claims/pNN.md` | Shared rules §5 |
| 17 part videos + merged course | `~/Movies/SD-Building-Blocks-course/` (not in the repo) | 1080p, burned captions, chapters. Stays local: no copy to Google Drive (author's decision, 2026-11-13) |
| Slide PDFs | same folder, `SD-Part-NN-slides.pdf` | Written by the frame render; one per part |
| Written companion | `theory/video/companion/SD-Building-Blocks-Companion.md` → PDF | Generated from the sources: per part the reading list, the concept table with the lines to say, the diagrams, traps, probe drills with answers |
| README | `theory/video/README.md` | Files, commands, part list with real durations, the reading plan, how to rebuild |

No publish kit and no upload.

## 2 · Scope, length and reading

### 2.1 · What is out

Dropped concepts are not taught, not listed "for awareness" and not in `concepts.tsv`. If a design
problem in plan 01 needs one, that problem's video teaches it there (plan 01 marks these "taught
here").

| Group | Dropped | Why |
|---|---|---|
| All of Tier C (21) | FND-17 · CON-15, CON-16 · REP-05 · PAR-03, PAR-12 · TXN-07, TXN-13 · CAC-13 · NET-10, NET-11, NET-12, NET-14 · API-09 · RL-11 · DS-12, DS-13, DS-14 · SCH-04, SCH-10, SCH-12 | "Know that it exists" items; none decides a round |
| Search (7) | SRCH-01–07 | Used only by search, typeahead and crawler problems, none of them in the priority set |
| Rare Tier B (21) | EST-11 · CON-08 · STO-12, STO-17 · TXN-11 · CAC-12 · MSG-14, MSG-16 · NET-05, NET-06, NET-13 · RL-02 · OBS-07 · DS-09 · SCH-09, SCH-11 · SEC-02, SEC-03, SEC-05, SEC-06 · OPS-06 | Each serves problems outside the priority set, or a neighbour that stays already covers it (SCH-09 by RL-08, SCH-11 by REL-13, OPS-06 by REL-12, RL-02 by RL-01, CON-08 by CON-07 and CON-09) |
| Blocks (6) | BLK-04 CDN · BLK-19 search index · BLK-23 authorisation service · BLK-25 key management · BLK-27 vector index · BLK-28 model serving | Their open-up concepts were dropped |

Remaining: **195 concepts (100 Tier A, 95 Tier B) and 22 blocks.** The data-structure group no
longer has its own part: each structure is taught in the part that uses it (Bloom filters and skip
lists with storage engines, Merkle trees with replication, timing wheels with scheduling, and so on).

If the author later wants a dropped item back, add its row to `concepts.tsv` and a section to its
part; nothing else depends on the list.

### 2.2 · Length

About **6 h 50 min** in 17 parts, about 55,000 spoken words. That is longer than the first plan's
core cut because every remaining concept now gets Staff depth, and it is the price of "own it":
at 0.45 s a word, a Tier A concept at this depth is about two minutes. There is one cut; the
earlier core/full split is gone.

Budget per concept form (§3): **full Tier A** about 2.1 min · **Tier B** about 1.1 min ·
**read-first** (the chapter teaches it; §2.3) about 0.8 min · plus about five minutes a part for
the opening, recap, drills and reading slide. Parts 3 and 7 get extra time for one long trace each.

| Part | Title | Concepts (home) | A · B | Min |
|---|---|---|---|---|
| 1 | Estimation that changes the design | EST-01–10, EST-12 | 7 · 4 | 24 |
| 2 | Consistency, time and failure | FND-01–13, FND-15, FND-16 | 9 · 6 | 31 |
| 3 | Consensus | CON-01–06, CON-14, FND-14 | 1 · 7 | 22 |
| 4 | Coordination services: locks, election, membership, config push | CON-07, CON-09–13 | 4 · 2 | 16 |
| 5 | Replication | REP-01–04, REP-06–14, DS-04 | 5 · 9 | 25 |
| 6 | Partitioning and placement | PAR-01, PAR-02, PAR-04–11, DS-11 | 6 · 5 | 23 |
| 7 | Storage engines and blob storage | STO-01–05, STO-08–11, STO-13–16, DS-01, DS-07 | 5 · 10 | 30 |
| 8 | Transactions and concurrency control | TXN-01–06, TXN-08–10, TXN-12 | 7 · 3 | 23 |
| 9 | Caching | CAC-01–11 | 6 · 5 | 23 |
| 10 | Logs, queues, streams and sketches | MSG-01–13, MSG-15, DS-02, DS-03, DS-10 | 6 · 11 | 30 |
| 11 | Networking, the edge and API contracts | NET-01–04, NET-07–09, API-01–08, DS-05 | 10 · 6 | 30 |
| 12 | Rate limiting and overload control | RL-01, RL-03–10 | 5 · 4 | 18 |
| 13 | Reliability patterns | REL-01–14 | 9 · 5 | 28 |
| 14 | Observability and time-series storage | OBS-01–06, OBS-08, OBS-09, STO-06, STO-07, DS-06 | 4 · 7 | 17 |
| 15 | Scheduling and control planes | SCH-01–03, SCH-05–08, OPS-04, DS-08 | 3 · 6 | 18 |
| 16 | Security, operating and evolving systems, the manager layer | SEC-01, SEC-04, SEC-07, OPS-01–03, OPS-05, OPS-07–10, EM-01–07 | 13 · 5 | 35 |
| 17 | The building blocks: which box, when, and what is inside | 22 blocks, the problem matrix | blocks | 19 |
| | | **195 concepts + 22 blocks** | **100 · 95** | **~412** |

The assignment was checked by script against the brief: every kept ID has exactly one home and the
tier counts are 100 and 95. Recount when you write `concepts.tsv`; if your counts differ, stop and
record it.

A part may run 15% over if the lint and the look-through are clean. Beyond that, shorten Tier B
narration before Tier A. No part may exceed 45 minutes.

### 2.3 · The reading plan (for the author; also printed in the README and the companion)

Chapter numbers and titles of the two SRE books and of *Software Engineering at Google* were
checked against their online tables of contents on 2026-11-12. DDIA is the first edition (2017).
"Must" means the course assumes it has been read and does not retell it.

| Source | Must read | Read when the part needs more |
|---|---|---|
| **Site Reliability Engineering** (free at `sre.google/sre-book`) | ch. 3 Embracing Risk · ch. 4 Service Level Objectives · ch. 6 Monitoring Distributed Systems · ch. 19 Load Balancing at the Frontend · ch. 20 Load Balancing in the Datacenter · **ch. 21 Handling Overload** · **ch. 22 Addressing Cascading Failures** · ch. 23 Managing Critical State: Distributed Consensus for Reliability · ch. 24 Distributed Periodic Scheduling with Cron · ch. 26 Data Integrity: What You Read Is What You Wrote | ch. 2 The Production Environment at Google (the vocabulary of Borg, Colossus, Chubby in ten pages) · ch. 17 Testing for Reliability · ch. 25 Data Processing Pipelines · ch. 27 Reliable Product Launches at Scale |
| **The Site Reliability Workbook** (free at `sre.google/workbook`) | ch. 2 Implementing SLOs · ch. 5 Alerting on SLOs · **ch. 12 Introducing Non-Abstract Large System Design** (a worked design round in Google's own style: read it twice) · ch. 16 Canarying Releases | ch. 11 Managing Load · ch. 14 Configuration Design and Best Practices · ch. 17 Identifying and Recovering from Overload |
| **Designing Data-Intensive Applications** (1st ed.) | ch. 5 Replication · ch. 6 Partitioning · ch. 7 Transactions · ch. 8 The Trouble with Distributed Systems · ch. 9 Consistency and Consensus · ch. 11 Stream Processing | ch. 3 Storage and Retrieval (must for the key-value and blob problems) · ch. 1 (percentiles, load) · ch. 4 Encoding and Evolution · ch. 12 (end-to-end argument, request IDs) |
| **Software Engineering at Google** (free at `abseil.io/resources/swe-book`) | — | ch. 15 Deprecation · ch. 22 Large-Scale Changes · ch. 14 Larger Testing · ch. 1 (Hyrum's Law; confirm the location) |
| **Papers** | Raft (extended version, sections 5 and 8) · "The Chubby Lock Service" · Spanner (sections 3 and 4) · "The Tail at Scale" · "Scaling Memcache at Facebook" (section 3) | Bigtable · Dynamo · GFS and the two Colossus posts · Borg · Monarch · "The Dataflow Model" · "Paxos Made Live" · Kleppmann, "How to do distributed locking" |

Each part's brief in §6 repeats the rows that belong to it under **Read first** and **Go deeper**,
and names what the narration leaves to the chapter.

**How "read-first" changes a concept.** A concept whose base explanation is a must-read chapter is
marked `read` in `concepts.tsv`. The course does not re-derive it. It gets the short form of §3.3:
one picture that fixes the idea, the number or formula worth knowing by heart, the probe that the
chapter does not answer, and the line to say. Read-first concepts: RL-06, RL-07, REL-02, REL-09,
NET-02, NET-03, OBS-05, OBS-08, OBS-09, OPS-01, OPS-08, EM-07. The part's opening says which
chapter is assumed, on screen and aloud.

## 3 · How a part is laid out

| Section | Content | Slides |
|---|---|---|
| `Opening` | Dark title slide; why this part decides rounds (one concrete failure story); **what is assumed read** (the must chapters); a map of the part. About 75 seconds | 3–4 |
| `<topic>` × 4–8 | The concepts, grouped by idea, in dependency order, Tier A and B mixed where the idea needs both | per §3.1–3.3 |
| `Recap` | One slide listing the part's Tier A ideas by name; the narrator says what to be able to explain without notes | 1 |
| `Probe drills` | Four interviewer probes at Staff level, each a chain: question, `[pause: 2.0]`, answer, then the follow-up a strong answer invites, and its answer | 12–16 |
| `Where this shows up` | Which design problems lean on this part, by plain name, and what each takes from it | 1–2 |
| `Read next` | The Go-deeper chapters and papers | 1 |

### 3.1 · Tier A at Staff depth (five to six slides, 260–320 spoken words)

1. **The failure first.** What goes wrong in a real system without this idea, as a picture or a
   small trace with times or values. Never start from the definition.
2. **The mechanism,** on a diagram or as worked arithmetic. Walk every element: each box, each
   numbered message, each line of the calculation, with concrete numbers.
3. **One level down.** The detail an interviewer reaches on the second "why?": the data structure
   behind the box, the invariant, what is persisted before what, the wire format or state machine,
   the constant that sets the cost. This slide is the difference between knowing the name and
   owning the idea, and it is not optional.
4. **The alternative and the price.** What else could do this job, the condition under which it
   wins, and what the chosen mechanism costs in latency, availability, money or operational load.
   A number wherever one exists.
5. **The line to say.** The brief's "be able to say" sentence, reworded for the ear, as a `V` line
   on a dark slide. Mechanism first, product name second.
6. **The trap or the probe.** The follow-up that breaks a shallow answer, and the answer. May be
   merged into slide 3 or 4 when it is the same point.

### 3.2 · Tier B at Staff depth (three slides, 140–180 words)

The mechanism in one picture or table with a worked case · one level down **or** the alternative
and its price, whichever an interviewer would ask · the line to say with where it is used.

### 3.3 · Read-first concepts (two slides, 100–130 words)

The one picture or formula worth carrying, with the number · the probe the chapter does not answer,
answered · the line to say. The slide's footer names the chapter ("Assumes SRE book ch. 21").

### 3.4 · Rules for all slides and narration

- `STANDARD.md` binds: one idea per slide, at most one diagram or one table of six rows or about 25
  words of body; 40–70 spoken words on every diagram slide; every term of art defined on first use,
  on screen and aloud; code in `pre.code`, 16 lines at most.
- The kicker of each slide carries the concept ID and tier (`FND-13 · Tier A`), so a viewer can
  find it in the companion and plan 01's videos can point at it.
- **Section titles are reference targets.** Plan 01's videos cite "course part 2, Leases and
  fencing". Use the concept's name from the brief as the section or slide title, and do not rename
  a section after its part is built without regenerating `INDEX.md` and noting it in the status file.
- **Teach the concept once, in general form.** Use a small neutral example, not a full design
  problem: the problem-specific treatment belongs to plan 01. Do not walk a whole design here.
- Every part uses at least **three examples from DDIA and two Google sources** from the shared
  rules' §4, named on the slide and in `Read next`. Open each before using it.
- Google's name for a block appears beside the open-source one wherever the brief's Part C gives
  both, after the mechanism has been explained.
- Narration is written for the ear. No symbols in spoken lines (the compiler lints `→ · ≥ % ~` and
  others); spell numbers the voice would mangle; add respellings to `say.py`.
- Numbers on screen and in speech match, and each has a row in the part's claims file.

### 3.5 · A sample in the source format

Shape only. The real format is whatever the ported `course.py` accepts; `@` lines are the concept
markers (§4).

```
## Leases and fencing tokens

= dia | FND-13 · Tier A · The failure | A paused holder writes after its lease has gone
@ FND-13
p2-pause
N: Follow the picture from the left. Client A takes the lock, with a ten second lease. Then its process stops. Not a crash: a pause. A garbage collection, or the hypervisor moving the machine. On the middle line, the lease runs out at ten seconds, and the service, correctly, gives the lock to client B. B starts writing. At fifteen seconds A wakes up. Nothing told it that time has passed. It still believes it holds the lock, and it writes. Two writers, at the same instant, and the lock service did nothing wrong.

= dia | FND-13 · Tier A · The mechanism | The resource checks a number that only grows
p2-fencing
N: The repair is on the resource, not in the lock. Every grant carries a fencing token, a number that only goes up. A got thirty-three. B got thirty-four. The storage service remembers the highest token it has accepted. B writes with thirty-four, and that is accepted. A arrives late with thirty-three. Thirty-three is lower than thirty-four, so the write is refused. The pause no longer matters, however long it was.

= code | FND-13 · Tier A · One level down | The check and the write are one conditional operation
UPDATE objects
   SET body = :body, token = :token
 WHERE id = :id AND token <= :token;   -- zero rows changed: a newer owner exists
N: One level down. The check must be atomic with the write. Here it is a single conditional update: write only if the stored token is not greater than mine. Check first and write second, as two steps, and a late owner slips between them. And the token must come from the same ordered log that granted the lease, so that a new leader of the lock service can never hand out a smaller number.

= table | FND-13 · Tier A · The alternative and the price | A lease alone, a lease with fencing, or no lock at all
…three rows: what each assumes about clocks, what a pause can break, what it costs the resource…
N: …

= th | FND-13 · the line to say | A lease is time-bounded ownership. A fencing token makes a late owner harmless.
V: A lease is ownership with a time limit, and it only needs bounded clock drift. A fencing token is a number that only grows, checked by the resource, and it makes a paused or partitioned former owner harmless.
[pause: 0.8]

= panel trap | FND-13 · Tier A | The token must be checked where the write lands
A lock service that hands out tokens which the storage never checks protects nothing.
If the resource cannot check a token, say so, and say what bounds the damage instead.
> Source: the fencing figure in DDIA ch. 8; sequencers in the Chubby paper.
N: Here is the trap. The token only helps if the thing being written to checks it. If the storage cannot compare tokens, the lock is advisory, and you should say that aloud, and say what limits the damage.
```

## 4 · Who does what

The work is split so that a weaker model never has to decide what to teach.

| Role | Does | Never does |
|---|---|---|
| **Author** (the strongest model, with the author present) | Writes every transcript (`src/chNN.txt`: slides and narration, complete), every diagram specification (`diagrams/pNN.md`), `concepts.tsv`, and the builder | Renders video |
| **Runner** (Sonnet or similar, one subtask per session, about 30 minutes) | Draws diagrams from the specifications, re-runs the arithmetic, renders frames, fixes layout overflow, synthesises voice, builds and checks video, merges | Writes or rewrites teaching content, changes a number, adds or drops a slide's meaning |

**Already done by the author** (do not redo):

- The builder is ported to `theory/video/`: `course.py` (`compile`, `frames`, `video`, `merge`,
  `stats`, plus the new `coverage` and `index`), `build_cached.py`, `render_check.py`, `say.py`,
  `sd.css`. New in the port: `= probe` slides, `@ ID` concept markers, a part as a folder of segment
  files (`src/chNN/*.txt`, joined in name order), slide PDFs copied to the output folder, and
  `--root DIR` so plan 01's episode series build with the same tool.
- `concepts.tsv`: 195 concepts and 22 blocks with tier, home part and form.
- `diagrams/README.md`: the drawing rules for every figure.

**Transcript status** (the author updates this table; a runner subtask for a part may start only
when its row says "written"):

| Part | Transcript `src/chNN.txt` | Diagram spec `diagrams/pNN.md` | Compiles clean | Slides · words · est. min |
|---|---|---|---|---|
| 1 Estimation | written | written (5 figures) | yes | 66 · 4,341 · 31 |
| 2 Consistency, time and failure | written | written (12 figures) | yes | 81 · 4,863 · 35 |
| 3 Consensus | written | written (7 figures) | yes | 49 · 3,154 · 23 |
| 4 Coordination services | written | written (8 figures; reuses `p2-pause`) | yes | 61 · 3,701 · 27 |
| 5 Replication | written | written (9 figures) | yes | 90 · 4,895 · 36 |
| 6 Partitioning and placement | written | written (8 figures) | yes | 78 · 4,155 · 30 |
| 7 Storage engines and blob storage | written | written (11 figures) | yes | 94 · 5,022 · 37 |
| 8 Transactions and concurrency control | written | written (13 figures) | yes | 76 · 4,160 · 30 |
| 9 Caching | written | written (7 figures) | yes | 77 · 4,154 · 30 |
| 10 Logs, queues, streams and sketches | written | written (11 figures) | yes | 101 · 5,248 · 38 |
| 11 Networking, the edge and API contracts | written | written (10 figures) | yes | 99 · 5,112 · 37 |
| 12 Rate limiting and overload control | written | written (3 figures) | yes | 67 · 3,286 · 24 |
| 13 Reliability patterns | written | written (7 figures) | yes | 92 · 4,449 · 32 |
| 14 Observability and time-series storage | written | written (4 figures) | yes | 69 · 3,174 · 23 |
| 15 Scheduling and control planes | written | written (8 figures) | yes | 62 · 3,035 · 22 |
| 16 Security, operating and evolving systems, the manager layer | written | written (1 figure) | yes | 110 · 4,999 · 36 |
| 17 The building blocks | written | no new figures; reuses five (see `p17.md`) | yes | 58 · 2,177 · 16 |

All 217 IDs (195 concepts, 22 blocks) have exactly one home; `INDEX.md` has no "not written" rows.
Total: about 70,000 spoken words, 124 figures to draw, about 8.5 hours by the compiler's estimate.
Real lengths come from `course.py compile`; the budget in §2.2 was a plan. Part 4 onwards reuse
some figures across parts; draw each figure once, in the part that first names it.

**Checked since (2026-11-13):** every derived number, in `claims/pNN.md` (360 rows, none off).
**Not yet checked by anyone but the author:** the technical claims against the cited chapters and
papers beyond the arithmetic, the Google Cloud product
roles in part 17's assemblies (verify against the Architecture Center before rendering), and the
exact product facts, which were taken from the research brief's November 2026 check.

### 4.1 · What a runner may change in a transcript

A transcript is finished text. A runner changes it only in these cases, and lists every change in
the status file with the slide title and the before and after:

1. **Lint** reported by `course.py compile` (a symbol in a spoken line, a spoken line over 110
   words): replace the symbol with the word, or split the line at a sentence end. Wording otherwise
   untouched.
2. **Overflow** reported by `course.py frames`, fixed by the first of these that works:
   a. add the `sm` flag to a table slide (`= table sm | …`);
   b. shorten on-screen text of that slide without changing a number, a name or the meaning (the
      narration is not touched);
   c. split the slide in two at a natural row or line, and split its narration at a sentence end so
      each half is spoken over its own slide.
3. **Pronunciation**: add a respelling to `say.py`. Never respell inside the transcript.
4. **A wrong number** found by the claims subtask: **do not fix it.** Record it under "For the
   author" in the status file, with the arithmetic, and carry on. The author corrects transcripts.

## 5 · Subtasks

Every subtask is one session of about 30 minutes. Each card says what it needs, what to do, what it
leaves behind and when it is done. Start every session by reading the shared rules (§1–§3 and §6
are enough for a runner), this file's §4.1, and the card. End it by updating `plans/STATUS-02.md`
(one row per subtask: ID, state, counts, changes made, items for the author) and committing.

IDs: `C-S*` setup, `C-NN-*` part NN, `C-M*` merge. Order: setup once; then for each part
`D → K → F → V`; `D` and `K` of one part can run in parallel sessions; parts are independent of
each other; `C-M*` last.

**Kick-off prompt** (change the ID):

```
Read plans/00-shared-rules-and-sources.md §1–§3 and §6, then plans/02-concepts-and-building-blocks-course.md §4.1
and the card for subtask C-03-F in §5. Do exactly that subtask. You are a runner: do not write or rewrite
teaching content. CLAUDE.md's interviewer rules do not apply to this work.
Stop when the card's "done when" list is true, update plans/STATUS-02.md, commit, and report.
```

### 5.1 · Setup subtasks (once)

**C-S1 · Smoke build** (30 min)
- *Needs:* nothing.
- *Do:* 1) `cd theory/video && ./course.py compile 1` — expect no lint and a line of counts.
  2) Write `tests/sample.txt`: a twelve-slide part with one slide of every type (`th table cards
  tiles list dia code panel probe`), an `@` marker, a `[pause]`, and lines for all four speakers
  `N V I C`; for the `dia` slide draw a trivial `svg/sample-box.svg`. Copy it to `src/ch99.txt`.
  3) `./course.py frames 99` then `./course.py video 99`. 4) `ffprobe` the MP4: one video stream
  1920×1080, one audio stream, chapters, no subtitle stream. 5) Look at four frames. 6) Delete
  `src/ch99.txt` and the MP4.
- *Leaves:* `tests/sample.txt`, `svg/sample-box.svg`.
- *Done when:* the sample built and passed the probe; any failure of the toolchain is written into
  the status file with the exact error. Do not repair the builder beyond a path or a typo; larger
  faults go to the author.

**C-S2 · Tests for the builder** (30 min)
- *Needs:* C-S1.
- *Do:* write `tests/test_course.py` (stdlib `unittest`): a golden-file test that compiling
  `tests/sample.txt` gives the stored HTML and script (`tests/golden/`); a test that a concept
  declared in two slides fails `coverage`; a test that an ID missing from `concepts.tsv` fails it;
  a test that a folder of segment files compiles to the same output as the joined file.
- *Done when:* `python3 -m unittest discover theory/video/tests` passes, and fails when one
  character of the golden HTML is changed (try it, then restore).

**C-S3 · Pronunciation check** (30 min)
- *Needs:* C-S1.
- *Do:* 1) Collect the terms: every key of `say.py`, plus every word in `src/*.txt` spoken lines
  that contains a capital after the first letter, a digit, or a hyphenated acronym
  (`grep -ohE "\b[A-Za-z0-9/+-]*[A-Z0-9][A-Za-z0-9/+-]*\b"` over lines starting `N: V: C: I:`).
  2) Build a one-minute clip that speaks each in a short sentence (a `src/ch98.txt` of `list`
  slides). 3) Run `~/.claude/skills/audio-version/scripts/check_audio.py` on its audio against the
  text. 4) For each flagged term add or correct a respelling in `say.py`; rebuild; repeat once.
  5) Delete `src/ch98.txt`.
- *Done when:* no flagged term remains, or the remaining ones are listed for the author. Rerun this
  card after every five new transcripts.

**C-S4 · The companion command** (30 min)
- *Needs:* C-S2.
- *Do:* add `course.py companion` (and a test): for each part write to
  `companion/SD-Building-Blocks-Companion.md` — the part title; the "Assumed reading" and "Read
  next" panel texts; a table of the part's concepts (ID, name, tier, the text of the concept's
  `V:` line, the section title); each `dia` slide's figure with its title; each `trap` and `watch`
  panel's text; each probe with its answer bullets and its `C:` line. The reading plan of §2.3 goes
  at the front. Pure extraction from the sources: no new prose.
- *Done when:* the command runs on part 1 and its output contains 11 concept rows, 5 figures and
  6 probes; tests pass.

### 5.2 · Per-part subtasks (for each part NN whose transcript is "written")

**C-NN-D1, C-NN-D2, … · Diagrams from the specification** (30 min each, at most five figures a session)
- *Needs:* `diagrams/pNN.md`, `diagrams/README.md`.
- *Do:* 1) Read the rules, then the first five undrawn figures of the specification. 2) Write or
  extend `diagrams_pNN.py`, one function per figure, and run it. 3) Render each SVG to PNG and
  look at each one. 4) Compare with the specification label by label and number by number.
  5) Fix and re-render until clean. Next session: the next five.
- *Leaves:* `diagrams_pNN.py`, `svg/pN-*.svg`.
- *Done when:* `./course.py compile NN` no longer lists those figures as "not drawn yet"; every
  figure was looked at; nothing overlaps or is cut; every label of the specification is present.

**C-NN-K · Check the arithmetic** (30 min)
- *Needs:* the transcript.
- *Do:* 1) List every number in the part that is the result of a calculation (on a slide or
  spoken), with its inputs. 2) Recompute each with `python3 -c`. 3) Write `claims/pNN.md`: one row
  per claim — the claim, its kind (`derived` with the expression and result · `published` with the
  source named on the slide · `assumption`), the slide title. 4) Check that every number spoken
  matches the number on its slide.
- *Done when:* every derived number is in the ledger with a recomputed value; every mismatch
  larger than rounding is listed under "For the author" (§4.1 rule 4). Nothing in the transcript
  was changed.

**C-NN-F · Frames and layout** (30 min)
- *Needs:* all C-NN-D* done.
- *Do:* 1) `./course.py compile NN`: fix lint per §4.1 rule 1. 2) `./course.py coverage NN`: must
  be clean; a problem here goes to the author. 3) `./course.py frames NN`: fix each reported
  overflow per §4.1 rule 2, re-run until zero. 4) Tile all frames eight to a sheet
  (`~/.claude/skills/slide-video-kit/scripts/tile_frames.sh`) and look at every sheet: text cut
  off, a figure too small to read, a table that touches the footer. Fix as in rule 2.
- *Leaves:* frames in `~/.cache/sd-course/build/chNN/frames/`, the slide PDF in the output folder.
- *Done when:* zero lint, zero overflow, every sheet looked at, every change listed in the status
  file.

**C-NN-V · Voice, video and checks** (30 min; the build runs in the background)
- *Needs:* C-NN-F, C-S3.
- *Do:* 1) `./course.py video NN` in the background (about a third of the part's length). 2) While
  it runs: `./course.py index`. 3) When it finishes: `ffprobe` streams and chapters (1920×1080,
  audio, chapters equal to the part's `##` sections, no subtitle stream). 4) Extract the audio and
  run `check_audio.py` against the script in `~/.cache/sd-course/build/chNN/`; for each flagged
  word add a respelling to `say.py` and rebuild (only changed lines are re-voiced). 5) Sync probe:
  grab a frame at about 90% of the duration and check its caption belongs to that slide. 6) Look
  at six frames spread over the video.
- *Leaves:* `SD-Part-NN-….mp4` and `SD-Part-NN-slides.pdf` in `~/Movies/SD-Building-Blocks-course/`.
- *Done when:* all checks pass or the failures are listed; real duration is in the status file;
  the part is under 45 minutes (if not: report it to the author; do not cut).

### 5.3 · Merge subtasks (after all parts)

**C-M1 · Merge and index** (30 min)
- *Do:* `./course.py coverage` (195 of 195, no problems) · `./course.py merge` · `ffprobe` the
  merged file: duration equals the sum of the parts, chapters combined · `./course.py index`
  (now with timestamps) · commit `INDEX.md`.

**C-M2 · Companion PDF** (30 min)
- *Needs:* C-S4, C-M1.
- *Do:* `./course.py companion`; build the PDF with the booklet kit
  (`~/.claude/skills/slide-video-kit/templates/reference-design/build-sd-booklet.sh`); read the
  build output for missing glyphs; tile the pages and look at them.

**C-M3 · Final check and hand-over** (30 min)
- *Do:* grep the claims ledgers for one quantity with two values across parts; list differences ·
  write `theory/video/README.md` (files, commands, the part table with real durations, the reading
  plan of §2.3) · add one line to `theory/README.md` · do **not** copy anything to Google Drive (author's decision, 2026-11-13) · run the privacy grep of §7 · report per shared rules §2.7.

## 6 · Part briefs (the author's agenda for each transcript)

These briefs are what the author writes each transcript from; a runner does not need them. For each part: the concepts are in §2.2. "Worked" lists what must be shown as a trace or a
calculation, not asserted. "Level down" names the second-"why?" details that must have a slide.
"Read first" is assumed read and not retold; "Leave to the chapter" says what the narration skips.
"Probes" are the drill chains (reword freely). Check every detail of a source before it goes on a
slide.

### Part 1 · Estimation that changes the design
- **Opening story.** Two candidates produce the same numbers; one stops, the other says "so it fits
  in memory on every node, and the hot path needs no network call". Every estimate ends in "so".
- **Worked.** The constants as tiles (10⁵ seconds a day, 1 M a day is about 12 a second) · load
  shape: peak against average, and which one you build for · a storage sizing from records to
  machines · the machine envelope: what one node does in requests, RAM, disk and network · the
  latency ladder on a log scale, with a request budget spent on it · availability: three 99.9%
  dependencies in series, two 99% replicas in parallel · queueing: why latency bends upward past
  70–80% utilisation · fan-out: 100 leaves at 1% slow gives 63% · transfer time for 100 PB ·
  durability from failure rate and repair time · cost per GB-month under replication and under
  erasure coding.
- **Level down.** Where each constant comes from, so it can be rebuilt · the M/M/1 waiting-time
  formula behind the utilisation curve, with two points computed · why availability maths assumes
  independence, and what a shared dependency does to it.
- **Read first.** SRE workbook ch. 12 (Non-Abstract Large System Design). SRE book ch. 3.
  **Leave to the chapter:** the full worked design; the course teaches the moves and sends the
  viewer to the chapter for a complete example.
- **Go deeper.** DDIA ch. 1 (describing load, describing performance). "The Tail at Scale".
- **Probes.** Hit ratio falls from 99% to 95%: what happens to the database → and which number
  would you alarm on · this service calls five others: what is its availability → and if two of
  them share a database · you have one number to ask the interviewer for: which.

### Part 2 · Consistency, time and failure
- **Opening story.** A design that says "strongly consistent" over an arrow labelled "async".
- **Worked.** CAP stated correctly, and why "CA" is not a choice · PACELC with two systems placed on
  it · the consistency ladder with one operation per rung · linearizable versus serializable on two
  timelines, and strict serializability as both · a quorum with R + W > N that still returns a stale
  value · exactly-once as an effect: at-least-once delivery plus a dedup key · total, per-key and
  causal order · wall clocks: last-writer-wins dropping a write under skew · Lamport timestamps and a
  version-vector conflict · hybrid clocks and commit wait on a timeline · leases and fencing (the
  sample in §3.5) · safety versus liveness and what FLP does and does not say · failure models and
  grey failure · heartbeat timeouts, phi-accrual, gossip reaching N nodes in about log N rounds.
- **Level down.** How a linearizability checker thinks: one total order consistent with real time ·
  the lease-safety inequality with drift (the holder gives up before the grantor re-grants) · where
  the dedup key is stored and for how long · the three interleavings that make a quorum read stale
  (a concurrent write, a sloppy quorum, a failed write that partly landed).
- **Read first.** DDIA ch. 8 and ch. 9. **Leave to the chapter:** the survey of system models and
  the long discussion of what linearizability is not; the course works the cases.
- **Go deeper.** Spanner sections 3 and 4 (TrueTime, commit wait). DDIA ch. 5 (limits of quorum
  consistency).
- **Probes.** Is R + W > N linearizable → what would make it so, and at what cost · order two events
  from two machines → and if the clocks are 200 ms apart · what does your system do during a
  partition, per operation · why not use NTP time for a lease → what bound do you need instead.

### Part 3 · Consensus
- **Opening story.** Two leaders, each sure it leads.
- **Worked.** State-machine replication: a log plus deterministic apply · **Raft as one continuous
  trace on five nodes**: an election with terms and randomised timeouts; replication with the
  log-matching check; the commit rule and why a leader commits only entries of its own term by
  counting replicas (the scenario from the Raft paper); the election restriction · production Raft:
  membership change, snapshots, pre-vote, learners, leadership transfer · linearizable reads: a
  heartbeat round versus a leader lease · single-decree Paxos with two competing proposers · what
  Multi-Paxos skips, and what "Paxos Made Live" adds · multi-Raft: one group per shard, coalesced
  heartbeats, the arithmetic for 400,000 ranges · quorum placement over three regions with a commit
  latency worked out from round-trip times.
- **Level down.** What is on disk before a vote or an append is answered (term, vote, log) and why ·
  the write path's cost: one fsync and one majority round trip, and how batching hides it · why a
  membership change moves one server at a time or through a joint configuration · what a snapshot
  must contain for a new replica to be safe.
- **Read first.** Raft, extended version, sections 5 and 8. SRE book ch. 23. **Leave to the
  chapter:** the patterns built on consensus (queues, barriers) and the deployment advice; the
  course does the algorithm.
- **Go deeper.** "Paxos Made Live". DDIA ch. 9 (total order broadcast, epoch numbers and quorums).
- **Probes.** A partitioned leader still accepts a write: what happens to it → and to the client
  that sent it · can followers serve reads → how stale, and how would you bound it · replace a dead
  replica safely · five replicas in three regions: the write latency → move the leader: who pays now.
- **Note.** This is the group most likely to be drilled to the bottom. Spend the budget on the trace.

### Part 4 · Coordination services
- **Opening story.** A lock that "works" until the holder pauses.
- **Worked.** The Chubby model: sessions, KeepAlives, the master lease, the grace period on failover,
  sequencers, client caches with invalidation · etcd as the open counterpart: revisions, leases with
  a TTL, compare-and-swap transactions, watch from a revision · leader election as a pattern, with
  the epoch carried on every side effect · efficiency locks versus correctness locks, and the
  critique of a multi-node Redis lock · membership and discovery with stale client caches ·
  configuration push: versioned snapshots plus deltas, a push stream with pull as a backstop,
  checksums, staged rollout, last-known-good.
- **Level down.** The session timeline in numbers: lease length, the client's shortened local view,
  the grace period, and when a client must treat its locks as lost · waiting on a lock without a
  herd (each waiter watches only its predecessor) · why the service is used for coarse locks and
  small metadata, with the write-rate arithmetic that makes it a bad database.
- **Read first.** "The Chubby Lock Service". **Leave to the paper:** the design rationale and usage
  statistics.
- **Go deeper.** Kleppmann, "How to do distributed locking". DDIA ch. 9 (membership and coordination
  services). SRE workbook ch. 14.
- **Probes.** Why is a Redis lock not enough → when is it enough · 1,000 waiters on one lock · a node
  was offline for two hours: how does its config catch up → and how do you know it did.

### Part 5 · Replication
- **Opening story.** A failover that promoted a follower missing the last second of writes.
- **Worked.** Single leader: synchronous, semi-synchronous, asynchronous, and what failover loses ·
  split brain and fencing · the three lag anomalies and the guarantee that fixes each ·
  multi-leader conflicts, and homing an entity to one leader · leaderless: N, R, W, a sloppy quorum
  and hinted handoff, concurrent versions returned to the client · read repair and a Merkle-tree
  comparison descending into one differing range · primary–backup with leases and version numbers ·
  physical versus logical log shipping · change data capture and the transactional outbox against
  the dual-write race · conflict resolution: last-writer-wins, version vectors with a merge, CRDTs ·
  geo topologies · seeding a replica from a snapshot plus the log · RPO and RTO, and who decides to
  fail over · tombstones outliving the longest outage.
- **Level down.** Failover step by step: detect, choose the most advanced follower, fence the old
  leader, repoint clients, and the writes that are lost or must be reconciled · how the outbox is
  drained (poll or log tailing) and why the consumer must still dedup · the size and depth of a
  Merkle tree over 10⁹ keys and what one comparison transfers.
- **Read first.** DDIA ch. 5, whole. **Leave to the chapter:** the survey of topologies and the
  history of conflict-resolution approaches (verify the failover incident it describes before
  citing it).
- **Go deeper.** Dynamo. GFS. DDIA ch. 11 (change data capture). SRE book ch. 26. The Google Cloud
  disaster-recovery planning guide for RPO and RTO vocabulary.
- **Probes.** The same key is updated in two regions within 100 ms → which write survives, and who
  is told · a replica is two days behind: catch up or rebuild · a deleted item comes back · a user
  writes, then reads from another region.

### Part 6 · Partitioning and placement
- **Opening story.** Timestamps as keys, and one shard taking every write.
- **Worked.** Hash versus range on the same data set · consistent hashing: add a node to a ring of
  four, count the keys that move; virtual nodes · split and merge by size or load with a versioned
  shard map · rebalancing while serving: copy, catch up, switch, throttle · hot keys: detect,
  then salt, split, cache or limit · three ways to route a request · local versus global secondary
  indexes · avoiding cross-shard operations by co-location · failure-domain placement · tenants:
  pooled, siloed, and shuffle sharding with the combinatorics · ID schemes with their bit layouts:
  time plus worker plus sequence, time-ordered UUIDs, leased ranges.
- **Level down.** What a client does with a stale shard map (the redirect or the rejected epoch) ·
  the load variance virtual nodes buy, in numbers · the range-move protocol's one moment of
  unavailability and how long it is · why a time-ordered ID makes a range-partitioned store hot,
  and the fix.
- **Read first.** DDIA ch. 6. **Leave to the chapter:** the comparison of rebalancing strategies
  across products.
- **Go deeper.** Bigtable (tablets and splits). Slicer. Dynamo.
- **Probes.** Grow from 20 to 40 nodes → what moves, how fast, what does it do to the cache · one
  partition takes 20% of traffic · paginate a range scan across shards · two clients disagree about
  the topology.

### Part 7 · Storage engines and blob storage
- **Opening story.** "Durable" that was acknowledged before the log reached the disk.
- **Worked.** The write-ahead log, fsync and group commit · a B-tree page update with its log record ·
  **the LSM write and read paths as a trace**: memtable (a skip list), flush, levels, Bloom filters
  sized from the formula, the sparse index, the block cache; levelled versus size-tiered compaction
  and the three amplifications · MVCC: versions by timestamp and garbage collection below the oldest
  snapshot · choosing a data model by access pattern · primary-key order, composite and covering
  indexes, and every index as a write cost · blob layout: chunks, stripes, immutable objects,
  content addressing · Reed–Solomon (6,3): overhead, losses survived, and what repairing one
  fragment reads; local reconstruction codes · checksums end to end and scrubbing · repair priority
  and throttling · garbage collection of orphans with a grace period · snapshots, incrementals,
  point-in-time recovery, and the restore test.
- **Level down.** fsync latency against group-commit batch size, with the throughput it yields ·
  the worst-case point read in a levelled LSM (one table per level after the filters) and the RAM
  for filters and index over 1 PB of 1 KB records · write amplification of levelled compaction as
  a number and what it does to SSD life and p99 · why erasure-coded repair reads k fragments to
  rebuild one, and what that means for repair bandwidth after a rack loss.
- **Read first.** DDIA ch. 3. **Leave to the chapter:** the build-up from an append-only file and
  the B-tree basics.
- **Go deeper.** Bigtable. GFS and the Colossus posts. "Erasure Coding in Windows Azure Storage".
  DDIA ch. 7 (implementing snapshot isolation). SRE book ch. 26.
- **Probes.** p99 read latency spikes during compaction → what do you throttle, and what do you
  give up · how much RAM to index 1 PB of 1 KB records · a rack dies: the next hour · after a
  delete, when is the space free.

### Part 8 · Transactions and concurrency control
- **Opening story.** Two doctors both go off call. Each checked first.
- **Worked.** Isolation levels by the anomaly each allows: dirty read, lost update, write skew,
  phantom, each as a two-transaction trace · optimistic concurrency with a version check ·
  pessimistic locks, `SELECT … FOR UPDATE`, `SKIP LOCKED` as a queue, deadlocks and lock ordering ·
  snapshot reads and serializable snapshot isolation · two-phase commit on a timeline, with the
  coordinator dying after prepare · two-phase commit where each participant is a consensus group ·
  a saga with compensations and a visible intermediate state · the idempotency key stored in the
  same transaction as the effect · hold, then confirm or cancel, with an expiry · escrow: a budget
  split into per-shard allowances.
- **Level down.** What a database's default isolation level actually permits (name the level, show
  the anomaly) · why a participant that has prepared cannot decide alone, and how long locks stay
  held · the dedup table: key, stored response, expiry, and the request that arrives while the
  first is still running · optimistic against pessimistic by contention: the retry arithmetic at
  100 buyers for one unit.
- **Read first.** DDIA ch. 7. **Leave to the chapter:** the taxonomy of isolation levels and their
  naming history; the course does the traces and the choices.
- **Go deeper.** DDIA ch. 9 (atomic commit), ch. 12 (request IDs). Spanner. Garcia-Molina and Salem,
  "Sagas". Helland, "Life beyond Distributed Transactions".
- **Probes.** The user double-clicks Pay → the second request arrives during the first · payment
  succeeds after the hold expired · 100 parallel requests against the last unit · name the anomaly
  your design must rule out, and the cheapest level that rules it out.

### Part 9 · Caching
- **Opening story.** The cache tier restarts cold at peak and the database follows it down.
- **Worked.** Five caching patterns in one table: who populates, who invalidates, what happens on
  failure · eviction: LRU, LFU, CLOCK and sampled LRU, admission by a frequency sketch · TTL with
  jitter; lazy plus sampled expiry · invalidation three ways, with the staleness bound stated ·
  stampede control: single-flight, leases, early refresh, stale-while-revalidate · **the stale-set
  race as a sequence, and the lease token that closes it** · hot keys and big values · tiers: in
  process and remote · negative caching and a filter against keys that cannot exist · the hit-ratio
  arithmetic · cold start and node loss.
- **Level down.** What a cache node is inside: a hash table, an eviction list, per-item overhead in
  bytes, and what that does to "64 GB of cache" · invalidation from the change stream against
  invalidation by the writer: the ordering each can and cannot guarantee · the backend load curve
  as the hit ratio moves from 99% to 90%.
- **Read first.** "Scaling Memcache at Facebook", section 3. **Leave to the paper:** the regional
  and cross-region deployment story.
- **Go deeper.** DDIA ch. 5 (reading your own writes), ch. 11 (derived data kept in sync from a
  change stream). TinyLFU.
- **Probes.** State the staleness you guarantee → and what breaks it · one key takes 500k requests a
  second · LRU or LFU for this workload, and how would you measure it.
- **Note.** The cache as a whole system (cluster behaviour, resize, failover) belongs to plan 01's
  cache videos. Teach the concepts here on one node and one key.

### Part 10 · Logs, queues, streams and sketches
- **Opening story.** A consumer crashes after writing its result and before saving its position.
- **Worked.** Queue versus log · inside a partitioned log: segments, offsets, the sparse index,
  retention, compaction by key · log replication: in-sync replicas and the high watermark ·
  consumer groups and what a rebalance costs · the three delivery semantics · ordering per key and
  its price · acknowledgement deadlines, redelivery, dead letters (use the brief's exact product
  facts, with their check date) · backpressure and lag measured in time · delayed and priority
  delivery · fan-out on write versus on read · event time, windows, watermarks, late data ·
  checkpointed state and replay · batch plus stream versus one replayable stream · schema
  evolution · HyperLogLog, Count-Min Sketch and quantile sketches, each with its error bound and
  why it merges.
- **Level down.** The crash between the sink write and the offset commit, in both correct
  constructions (dedup in the sink's transaction; or replay from a checkpoint into a sink that
  overwrites) · what an acknowledged write means under each replication setting, and the data loss
  when the last in-sync replica dies · how a watermark is computed from partition progress and why
  one idle partition stalls it · Count-Min width and depth from ε and δ, worked.
- **Read first.** DDIA ch. 11. **Leave to the chapter:** stream joins and the broker survey.
- **Go deeper.** "The Dataflow Model". The Kafka paper and its replication design notes. DDIA ch. 4
  (schema evolution). SRE book ch. 25. Pub/Sub documentation.
- **Probes.** Exactly-once: what do you actually mean → show me where the duplicate dies · one key
  is 10% of all events · events arrive two hours late · a consumer is slow: what happens upstream.

### Part 11 · Networking, the edge and API contracts
- **Opening story.** A failover that took as long as the DNS TTL.
- **Worked.** DNS, geo-routing and anycast · L4 versus L7 balancing and the balancing policies
  (read-first) · health checks, outlier ejection, draining, and never ejecting everyone
  (read-first) · the gateway tier and what stays out of it · RPC: deadlines passed downstream,
  cancellation, subsetting, retries only when idempotent · polling, long polling, SSE and WebSocket
  in one table · a persistent-connection tier: the user-to-gateway routing table, heartbeats,
  reconnect storms · the API contract: style, cursors, idempotent writes, compatibility,
  long-running operations, resumable upload, conditional requests, the 429 contract on the wire ·
  tries and longest-prefix match for routing tables and IP ranges.
- **Level down.** What a cursor encodes and why offsets break under inserts · the deadline budget
  across three hops, with the arithmetic · memory and file descriptors for ten million open
  connections, and the reconnect rate after a gateway dies · an idempotent POST on the wire: the
  header, the stored response, the replay.
- **Read first.** SRE book ch. 19 and ch. 20. **Leave to the chapters:** how DNS and virtual-IP
  balancing work, subsetting, and weighted round robin; the course keeps one picture and the probe.
- **Go deeper.** Maglev. The API Improvement Proposals for pagination, long-running operations,
  request identification and etags (check each number at aip.dev). DDIA ch. 4 (the problems with RPC).
- **Probes.** Server push for a streamed response: which transport and why · make this POST safe to
  retry → for how long do you remember the key · a deploy drops in-flight requests · ten million
  open connections reconnect at once.

### Part 12 · Rate limiting and overload control
- **Opening story.** A limiter that failed closed and took the product down with it.
- **Worked.** Token bucket state and refill on read · fixed window, sliding log, sliding-window
  counter with the formula and the boundary burst · three ways to enforce across nodes (a central
  atomic counter, local buckets with leased capacity, gossip) and how each bounds over-admission ·
  concurrency limits that adapt · shedding by criticality, and a cheap reject (read-first) · the
  client-side throttling formula (read-first) · fairness: quotas, weighted fair queuing, max–min ·
  fail-open versus fail-closed, and who owns the decision · bounded queues, deadlines checked at
  dequeue, LIFO and CoDel.
- **Level down.** The atomic check-and-decrement and where time comes from · worst-case
  over-admission with leased capacity as a formula in lease size and node count · what lowering a
  limit does while leases are outstanding · the cost of a reject against the cost of serving, and
  why that ratio decides whether shedding can save you.
- **Read first.** SRE book ch. 21. **Leave to the chapter:** criticality classes, per-customer
  limits, the derivation of client-side throttling and the utilisation signals.
- **Go deeper.** SRE workbook ch. 11 and ch. 17. Doorman. DDIA ch. 7 (preventing lost updates).
- **Probes.** State the worst-case over-admission → halve it: what does it cost · the limiter's
  store is down · two gateways race for the last token · a limit is lowered: when does it bite.
- **Note.** The quota that is money (reserve, commit, release) is taught in part 8 as the
  reservation pattern and escrow; point to it, do not repeat it.

### Part 13 · Reliability patterns
- **Opening story.** The trigger is gone and the system is still down: retries are holding it there.
- **Worked.** Deadlines as a budget passed down · retries: backoff with jitter, a retry budget, and
  the amplification arithmetic when three layers each retry three times (read-first) · the circuit
  breaker state machine · bulkheads and cells · hedged requests · degraded modes decided in the
  design · static stability · redundancy across zones: can you lose one at peak · cascading and
  metastable failure (read-first) · thundering herds · reconciliation and invariant audits as the
  safety net · hard and soft dependencies, no cycles, cold start · headroom and the risky direction
  of autoscaling · disaster recovery that has been exercised.
- **Level down.** N+1 and N+2 at peak as arithmetic across three zones, and what it costs ·
  the hedging threshold (send the second request at the 95th percentile) and the extra load it
  adds · what a cell is made of and how a request is pinned to one · the sustaining loop of a
  metastable failure drawn as a cycle, and the two ways to break it (shed load, cut retries).
- **Read first.** SRE book ch. 22. **Leave to the chapter:** the anatomy of a cascading failure,
  queue management, the testing advice and the immediate steps during an incident.
- **Go deeper.** "The Tail at Scale". SRE book ch. 26. DDIA ch. 1 (faults and failures), ch. 8
  (timeouts). The reliability pillar of the Well-Architected Framework.
- **Probes.** Where exactly do retries happen in your design → and who is not allowed to retry ·
  what does the user see when this dependency fails · a zone is lost at peak: walk me through the
  next five minutes · the load is back to normal and latency is not: why.

### Part 14 · Observability and time-series storage
- **Opening story.** Someone adds a user ID as a label.
- **Worked.** A series is a name plus a label set; the cardinality arithmetic · why percentiles
  cannot be averaged, with numbers, and what to aggregate instead (histograms, sketches) · push
  versus pull · roll-ups and retention tiers · alerting on symptoms and on error-budget burn over
  several windows (read-first; take the thresholds from the workbook chapter, verified) · the
  logging pipeline and what is dropped first · SLI, SLO, error budget and what happens when it is
  spent (read-first) · the four golden signals (read-first) · columnar storage and its encodings ·
  timestamp and value compression on four real samples · the inverted index from label to series.
- **Level down.** The detection-time formula: scrape interval, evaluation interval, the `for`
  window, notification delay, and which term to cut first · memory per active series in the head
  block and what 10⁷ series cost · why the alerting path must not depend on what it watches, and
  the dead-man's switch.
- **Read first.** SRE book ch. 4 and ch. 6. SRE workbook ch. 2 and ch. 5. **Leave to the
  chapters:** how to choose SLIs, the burn-rate derivation and the table of windows, alert hygiene.
- **Go deeper.** Monarch. Gorilla. DDIA ch. 3 (column-oriented storage).
- **Probes.** p99 across 10,000 hosts · who monitors the monitor · cut detection time from two
  minutes to fifteen seconds: what does it cost → and what false-alarm rate do you accept.

### Part 15 · Scheduling and control planes
- **Opening story.** The control plane goes down, and the question is whether anything else notices.
- **Worked.** Control plane versus data plane · desired state, observed state, and a level-triggered
  reconcile loop · placement: filter, then score; bin-packing versus spreading · priority, quota and
  preemption with graceful termination · node liveness, and rate-limited eviction during a
  partition · timers at scale: due-time buckets, shards, an in-memory hierarchical timing wheel, a
  heap for next-due, the misfire policy · task leasing: pull, lease, heartbeat, expiry, results
  tagged with the attempt · durable workflows resumed by replaying an event history.
- **Level down.** Why level-triggered beats edge-triggered after a missed event · the launch record
  written through consensus before and after the side effect, and what a new leader does with a
  launch that started and never finished (skip or double, chosen per job) · the attempt ID as a
  fencing token on results.
- **Read first.** SRE book ch. 24. **Leave to the chapter:** the cron service's design history and
  its handling of large installations.
- **Go deeper.** Borg. "Borg, Omega, and Kubernetes". SRE book ch. 2. DDIA ch. 8 (fencing).
- **Probes.** The scheduler dies after starting a job and before recording it · a million jobs at
  midnight · a high-priority job arrives: who is evicted, and how cleanly.

### Part 16 · Security, operating and evolving systems, the manager layer
- **Opening story.** A correct design, shipped to every region at once.
- **Worked.** Authentication for users and for services; opaque tokens versus self-contained ones,
  and revocation · tenant isolation of data, performance and faults · abuse resistance ·
  progressive rollout with bake time, health gates and automatic rollback, for binaries, config and
  data alike (read-first) · **online migration as one timeline**: expand, capture or dual-write,
  backfill, verify, switch reads, switch writes, contract · version skew and feature flags ·
  background work throttled by foreground targets · kill switches and safe limits on automation ·
  testing distributed systems (read-first) · multi-region operation · unit cost and its biggest
  lever · the manager layer: phases, team seams, build or reuse, the risk register, SLOs as a
  contract, client adoption, operational readiness (read-first).
- **Level down.** Why a rollout is a statistics problem: canary size, bake time and the smallest
  regression it can detect · the two-release rule for a schema or protocol change (read new, then
  write new) · rollback after writes have reached the new system: reverse replication or no
  rollback, said in advance · what bounds an automation's blast radius (a rate, a fraction, a
  human gate).
- **Read first.** SRE workbook ch. 16. **Leave to the chapter:** canary evaluation and metric
  selection.
- **Go deeper.** SRE book ch. 17 and ch. 27. "Online, Asynchronous Schema Change in F1". *Software
  Engineering at Google* ch. 15, ch. 22 and ch. 14. DDIA ch. 4 (rolling upgrades). The
  Well-Architected Framework's operational-excellence pillar.
- **Probes.** A bad push blocks a continent: stop it · roll back after two days of writes · how
  would you deliver this with half the team · what would you not build.
- **Note.** The manager-layer slides carry the AUX badge of `STANDARD.md` §1a; the coach says once
  what it means.

### Part 17 · The building blocks
- **Opening story.** An interviewer points at a box and says "open that up".
- **Layout.** One card slide per kept block, about 30 seconds: draw it for · not for · the concepts
  to open up, **with the part and section that taught them** · Google's name beside the
  open-source and cloud ones. Each section opens with one "what is inside" picture reused from the
  part that taught the mechanism. Five sections: the front door (BLK-01–03, 05) · databases and
  stores (06–11) · memory and coordination (12, 13) · messaging and processing (14–18) · platforms
  and backends (20–22, 24, 26).
- **Then.** The brief's three exact product facts, with their check date · the group-by-problem
  matrix (the brief's Part D) redrawn with plain problem names and part numbers · three short
  assemblies: pick the blocks for a cache tier, a job scheduler and a blob store, saying for each
  box what it owns and what would replace it on Google Cloud (take product roles from the
  Architecture Center, verified).
- **Read first.** SRE book ch. 2. **Go deeper.** The Google Cloud Architecture Center; each
  system's paper from the shared rules' §4.2.
- **Probes.** Why this store and not that one, for three pairs · the interviewer says "do not use
  the managed product: build it" → which part of this course do you open.

## 7 · Done means

- [ ] Setup: the sample builds; tests pass; `concepts.tsv` has 195 + 22 rows and no dropped ID.
- [ ] Every transcript was written by the author; runners changed only what §4.1 allows, and every
      such change is listed in the status file.
- [ ] Every part: lint empty; no slide overflow; every frame looked at; coverage clean; claims file
      complete; at least three DDIA examples and two Google sources, each opened and named.
- [ ] Every Tier A concept has the elements of §3.1, including a level-down slide and an
      alternative with its price. Every Tier B concept has three slides. Every read-first concept
      names its chapter and adds something the chapter does not say.
- [ ] Every part's opening states what is assumed read; `Read next` lists the Go-deeper sources;
      every chapter cited was opened in the session.
- [ ] No part walks a whole design problem; problem-specific material is left to plan 01.
- [ ] No part over 45 minutes. The real course length is reported; if it is over eight and a half
      hours, the author decides what to tighten.
- [ ] QA of `STANDARD.md` §4 done on every part; flagged words reviewed.
- [ ] `INDEX.md` committed with timestamps; companion PDF builds clean and was looked at.
- [ ] Nothing private in tracked files: no "reported" evidence, no source-bank names, no second-person
      remarks from the brief, no task numbers of the form `T01`.
- [ ] Nothing uploaded, nothing copied to Google Drive; pushed only when the author asks. Status file complete.
