# Shared rules and sources for the two video-kit plans

Read this file first, in every session, before `01-…` or `02-…`. It holds what both plans share: how to
work, what may be published, which sources to anchor on, and how to keep the technical content honest.

| Plan | Builds | From |
|---|---|---|
| [`01-top10-reference-designs-and-videos.md`](01-top10-reference-designs-and-videos.md) | For eleven tasks, a video series of up to three episodes each, with slide PDFs and a study handout. No written reference design | `private/01_Google_L6_SD_Top10_Tasks_and_Variants.md` |
| [`02-concepts-and-building-blocks-course.md`](02-concepts-and-building-blocks-course.md) | A seventeen-part narrated theory course at Staff depth (195 concepts, about seven hours), a chapter-level reading plan, an index that plan 01 cites, and a written companion | `private/02_Google_L6_SD_Concepts_and_Building_Blocks.md` |

Build the course (plan 02) first if both are being done: plan 01's videos do not re-teach shared
theory, they point at the course's parts through `theory/video/INDEX.md` and reuse its diagrams and
wording. Either plan also works alone; plan 01 then cites part numbers from plan 02's table.

---

## 1 · You are not the interviewer in these sessions

`CLAUDE.md` at the repo root turns Claude into a mock interviewer. **It does not apply to this work.**
These sessions produce study material, so explain, teach, name technologies and write files freely.
Three things from `CLAUDE.md` still hold: nothing private goes into a tracked file (§3 below), numbers
are never invented, and `interview.md`, `sessions/`, `Progress-Log.md` and `profile.md` are not touched.

## 2 · How to work

1. **One subtask per session, about 30 minutes.** Both plans are cut into subtask cards (plan 02 §5,
   plan 01 §5.3). The author writes all content: transcripts, design sheets, diagram specifications.
   A runner session does one mechanical card: draw figures from a specification, re-run arithmetic,
   render frames, build and check a video, merge. Small pieces are built first and merged upward:
   segments into an episode or part, parts into the course, episodes into a series. Stop at the
   card's "done when" list, update the status file, and end the session.
2. **Read before writing.** Every unit lists the files to read. Read them fully; do not work from
   their names. The skills are binding:
   - `~/.claude/skills/slide-video-kit/STANDARD.md` (picture, sound, captions, QA; §1a depth, §1b pacing)
   - `~/.claude/skills/system-design-video/SKILL.md` (plan 01). **Its step 1b, the written reference
     design, is overridden: plan 01 builds no booklet.** Read `REFERENCE-DESIGN.md` only for its list
     of what the race hunt found in SD-09
   - `~/.claude/skills/audio-version/reference/writing-for-the-ear.md` (all narration)
3. **Status file.** Each plan names one (`plans/STATUS-01.md`, `plans/STATUS-02.md`). One row per unit:
   state (`todo` · `sheet and diagrams done` · `frames checked` · `built` · `QA done`), word and slide counts,
   real duration, open questions for the author, anything you corrected. Update it at the end of every
   session; the next session starts by reading it.
4. **Branch and commits.** Work on the branch the author names (this plan was written on
   `feature/google-l6-video-kit-plans`). One commit per finished unit, message in the repo's style
   (`SD-20: design sheet and diagrams`, `SD-20: episode 2`, `Course part 3: consensus`). **Never push unless the author asks
   for it in so many words, never open a pull request, never upload or post anything.** MP4s, frames, audio and PDFs are gitignored; do not
   force-add them.
5. **Look at what you render.** Tile every frame and every PDF page and read the sheets
   (`~/.claude/skills/slide-video-kit/scripts/tile_frames.sh`). Overflow and overlap show only in pixels.
6. **Word budget before synthesis.** Count spoken words before building; the build's time guard fires
   only after ten minutes of synthesis. About 0.43 s per spoken word plus pauses.
7. **Report honestly.** Each session ends with: what was built, the real length, the QA that was run,
   what was not checked, and "not watched end to end". The technical content is a model's reasoning
   and has not been reviewed by a person; say so.
8. **When blocked,** write the question into the status file and carry on with the parts that do not
   depend on it. Do not guess a fact about a real system to get unblocked (§5).

## 3 · What is private and what is public

design-room is a **public repository**. Everything under `solutions/`, `theory/`, `questions/` and
`Question-Bank.md` is published.

| Private: read, never copy into a tracked file | Why |
|---|---|
| `private/01_…md`, `private/02_…md` | The ranking evidence, the "reported as" lines, the names and counts of question banks, and every second-person remark ("your SD-47") stay private. The **technical content** (cruxes, spines, numbers, variants, the concept wording) is generic and may be used |
| `profile.md`, `Progress-Log.md`, `sessions/`, `private/<company>/` | Not needed for this work. Do not open them |
| `~/Profile/materials/system-design/*.md` | The author's private dossiers. Use their technical content as input where a plan says so. Never copy their front matter, career framing or company-specific prep notes |

Rules for what you publish:

- Generic content only: no personal career claims, no employer systems, no profile data.
- The private reports number tasks `T01`–`T56`. **Public files use bank IDs (`SD-NN`) and plain names**,
  never `T-` numbers. Concept IDs (`CON-13`, `BLK-07`) may appear in the course's coverage table; they
  are a generic taxonomy.
- Do not state how often a company asks a question, and do not present any design as a company's real
  internal design. "Published in the Spanner paper" is fine; "this is how Google does it" is not.
- Use they/them for people in examples.

## 4 · Source anchors

Three families of sources, in this order of preference. Every part and every design names the ones it
used, by chapter or section title.

### 4.1 Kleppmann, *Designing Data-Intensive Applications*

Cite the **first edition (2017)** by chapter number and section title, never by page. The author has a
local copy (a 613-page PDF in `~/Downloads`; `pdftotext -f N -l M` reads a page range). **Open the
section and check an example before using it**; do not rely on memory for its details. Paraphrase and
attribute ("the on-call doctors example, DDIA ch. 7"); never reproduce a paragraph or redraw a figure
line for line. A second edition exists; if the local copy of it is incomplete, do not cite it.

| Ch. | Title | Examples worth using (verify each in the text) | Concept groups |
|---|---|---|---|
| 1 | Reliable, Scalable, and Maintainable Applications | The home-timeline fan-out as a load description; percentiles and tail-latency amplification; faults versus failures | EST REL MSG-10 |
| 2 | Data Models and Query Languages | Relational versus document versus graph by access pattern | STO-14 |
| 3 | Storage and Retrieval | The append-only log with a hash index; SSTables and LSM-trees; B-trees and the write-ahead log; comparing the two; column-oriented storage | STO DS-01 |
| 4 | Encoding and Evolution | Schema evolution in Protocol Buffers and Avro; forward and backward compatibility during rolling upgrades; the problems with RPC | MSG-15 API OPS-03 |
| 5 | Replication | Synchronous versus asynchronous followers; setting up a new follower; failover hazards and split brain; the three lag anomalies and their guarantees; multi-leader conflicts; leaderless quorums, sloppy quorums and hinted handoff; version vectors and the shopping-cart merge | REP FND-12 |
| 6 | Partitioning | Key range versus hash; skew and the celebrity hot key; local versus global secondary indexes; rebalancing strategies; request routing | PAR |
| 7 | Transactions | Read committed and snapshot isolation; lost updates; **write skew with the on-call doctors**; phantoms with meeting-room booking and username claims; serial execution, two-phase locking, serializable snapshot isolation | TXN STO-05 |
| 8 | The Trouble with Distributed Systems | Timeouts and unbounded delays; clock skew and last-write-wins losing data; **process pauses and the fencing-token figure**; the majority decides; system models | FND-05–09 FND-13 |
| 9 | Consistency and Consensus | Linearizability and where it is needed (locks, uniqueness, cross-channel timing); the cost of linearizability; Lamport timestamps and total order broadcast; two-phase commit and coordinator failure; consensus and epoch numbers; membership and coordination services | FND-01–04 CON TXN-05 |
| 10 | Batch Processing | MapReduce, joins, skewed keys; building search indexes and key-value stores as batch output | MSG-14 SRCH-01 |
| 11 | Stream Processing | Message brokers versus logs; change data capture and event sourcing; event time versus processing time, windows, straggler events; stream joins; checkpoints, idempotence and atomic commit for fault tolerance | MSG REP-08 FND-10 |
| 12 | The Future of Data Systems | Derived data and unbundling the database; the end-to-end argument and request IDs; timeliness versus integrity; auditing | FND-17 REL-11 TXN-09 |

### 4.2 Google's published architectures ("blueprints")

Two kinds. **Papers and book chapters** describe how a Google system was built at the time of writing.
**Google Cloud Architecture Center** pages describe how to assemble Google Cloud products. Use the
first for mechanisms and the second for the "what would I draw on Google Cloud" slide.

| System | Source | Use it for |
|---|---|---|
| GFS, Colossus | "The Google File System" (SOSP 2003); Cloud blog "A peek behind Colossus" (2021), "Colossus under the hood" (2025) | Single master and why it stopped scaling; metadata in Bigtable, Curators, D servers, Custodians |
| Bigtable | OSDI 2006 | Tablets, SSTables, compactions, the lock service's role |
| Spanner, F1 | Spanner (OSDI 2012); "Online, Asynchronous Schema Change in F1" (VLDB 2013) | Paxos per shard, TrueTime and commit wait, two-phase commit across groups, intermediate schema states |
| Chubby, Paxos | "The Chubby Lock Service" (OSDI 2006); "Paxos Made Live" (PODC 2007) | Sessions, leases, sequencers, the grace period; what production consensus needs beyond the paper |
| Borg, Omega, Kubernetes | Borg (EuroSys 2015); Omega (EuroSys 2013); "Borg, Omega, and Kubernetes" (ACM Queue 2016) | Priority, quota, scoring, shared-state scheduling, reconciliation |
| Monarch, Dapper | Monarch (VLDB 2020); Dapper (2010) | Zonal in-memory time series with global query; trace context and sampling |
| MillWheel, Dataflow, Dremel, Mesa | MillWheel (VLDB 2013); "The Dataflow Model" (VLDB 2015); Dremel (VLDB 2010) | Watermarks, exactly-once effect, windows and triggers, columnar scans |
| Maglev, Slicer, Zanzibar | Maglev (NSDI 2016); Slicer (OSDI 2016); Zanzibar (USENIX ATC 2019) | Consistent hashing for a load balancer; auto-sharding; relationship tuples and the "new enemy" problem |
| The SRE books | *Site Reliability Engineering*: ch. 2 The Production Environment at Google, from the Viewpoint of an SRE; 3 Embracing Risk; 4 Service Level Objectives; 6 Monitoring Distributed Systems; 8 Release Engineering; 17 Testing for Reliability; 19 Load Balancing at the Frontend; 20 Load Balancing in the Datacenter; 21 Handling Overload; 22 Addressing Cascading Failures; 23 Managing Critical State: Distributed Consensus for Reliability; 24 Distributed Periodic Scheduling with Cron; 25 Data Processing Pipelines; 26 Data Integrity: What You Read Is What You Wrote; 27 Reliable Product Launches at Scale. *The Site Reliability Workbook*: ch. 2 Implementing SLOs; 4 Monitoring; 5 Alerting on SLOs; 11 Managing Load; 12 Introducing Non-Abstract Large System Design; 14 Configuration Design and Best Practices; 16 Canarying Releases; 17 Identifying and Recovering from Overload | Operations, overload, rollout, alerting, a worked design in Google's style. Plan 02 §2.3 says which are must-reads |
| Google Cloud Architecture Center | The Well-Architected Framework (reliability, operational excellence, cost, performance, security pillars); the enterprise foundations blueprint; the disaster-recovery planning guide; reference architectures for multi-regional deployment, global load balancing and data pipelines | The "on Google Cloud" slide; RPO and RTO vocabulary; product names beside mechanisms |
| Google API design | The API Improvement Proposals at aip.dev (pagination, long-running operations, request identification for idempotency, etags, errors, backwards compatibility) | Every API contract slide |

**Fetch before citing.** The chapter numbers and titles of the two SRE books and of *Software
Engineering at Google* (ch. 14 Larger Testing, 15 Deprecation, 22 Large-Scale Changes) were checked
against their online tables of contents on 2026-11-12; what each chapter **contains** was not, so
open a chapter before leaving a topic to it. AIP numbers, product limits and Architecture Center page
titles come from memory and can be wrong or out of date. Check each one you use against
`sre.google`, `aip.dev`, `cloud.google.com/architecture` or the paper itself, and write the title as
the source gives it. If a page cannot be fetched, cite the source by name without a number.

The second private report ends with a full reading list (Part F) and three exact product facts with
their check date. Those facts were checked in November 2026; reuse them as written, with the date.

### 4.3 Google software-engineering practice

From *Software Engineering at Google* (Winters, Manshreck, Wright; free at `abseil.io/resources/swe-book`)
and the SRE books. It applies in two places.

**In the content** (operations stages, the EM layer, the course's last part):

| Practice | Where it appears in the material |
|---|---|
| Design documents with goals, non-goals and alternatives considered | Every task's design sheet and decision slides follow it: each major decision has a rejected alternative and the condition that would flip it |
| Hyrum's Law: every observable behaviour of an interface gets depended on | API contracts, version skew, why migrations have a long tail |
| Deprecation as planned work; large-scale changes done by one team with tooling | Migration, client adoption, switching off the old system |
| Testing sizes (small, medium, large), the Beyoncé rule ("if you liked it, put a test on it"), shifting left | Correctness evidence: fault injection, linearizability checks, load tests as launch gates |
| Small changes, code review, readability | Rollout safety: change size as blast radius |
| Progressive rollout, canary analysis, error budgets, blameless postmortems | Operations stages; every incident follow-up |
| Build, reuse or buy; one-version dependencies | "What I would actually build" sections |

Verify where a topic sits in the book before naming a chapter for it (Hyrum's Law is believed to be
in ch. 1; confirm).

**In how you work:**

- Small, reviewable commits: one unit each, with a message that says what and why.
- Any change to build tooling (plan 02 ports a builder) gets a test: a golden-file check that a sample
  source compiles to the expected HTML and script, run before each commit.
- Lint is a gate, not advice: the course compiler's lint list and the PDF builds' warnings must be
  empty before a unit is marked done.
- Python follows the style of the file being edited; no new dependencies.
- Keep generated files out of the repository and keep sources deterministic, so a rebuild reproduces
  the output.

## 5 · Keeping the content correct

A weaker draft fails in predictable ways. Guard against each.

1. **A ledger of claims.** Keep `claims.md` beside each unit's sources (tracked). One row per number or
   factual claim that appears on a slide or in a `key` box: the claim, its kind (`given` from the brief ·
   `derived`, with the arithmetic · `published`, with the source and section · `assumption`), and where
   it is used. A claim with no row does not ship. Planning figures say they are assumptions.
2. **Arithmetic is shown and re-run.** Recompute every estimate with a calculator call (`python3 -c`),
   not in your head. A slide and its narration must give the same number.
3. **Real systems.** State only what the source states, in its tense ("the 2012 paper describes").
   Product limits change; give the check date or leave the number out.
4. **Hunt the race.** For every guarantee a design claims, write down: the interleaving that would
   break it, the failure that would break it, and what happens when it meets the neighbouring mechanism.
   Run each code listing by hand against a duplicate request and against a crash between two lines.
   `REFERENCE-DESIGN.md` lists what this found in SD-09.
5. **Never "exactly-once delivery", never "CA system", never "R + W > N means linearizable".** The
   private report's FND group has the correct wording; use it.
6. **Terms.** Define each term of art on first use, on screen and aloud. One name per thing throughout
   a unit ("lease" and "TTL lock" are not synonyms).
7. **Agreement across the kit.** A concept explained in the course and recalled in a task video uses
   the same words and the same numbers, and is explained only in the course (plan 01 §4). The existing `theory/*.md` chapters and `guides/tool-depth-crib.md`
   are the baseline; where you find one of them wrong, list it in the status file rather than silently
   diverging.

## 6 · Tooling at a glance

| Need | Tool |
|---|---|
| C4, sequence, ERD diagrams | `~/.claude/skills/slide-video-kit/scripts/c4svg.py`, `seqsvg.py`, `erdsvg.py`; worked sources in `solutions/SD-09-chat-messaging/video/diagrams.py` and `pdf-kit/examples/notification-platform/video/diagrams.py` |
| Slides to frames | `pdf-kit/.venv/bin/python ~/.claude/skills/slide-video-kit/scripts/render_slides.py …` |
| Script to MP4 | `~/.claude/skills/slide-video-kit/scripts/build_video.py … --gap-scale 1.3 --max-minutes 45` |
| Audio check | `~/.claude/skills/audio-version/scripts/check_audio.py` |
| Slide PDF | Written by `render_slides.py --html` beside the HTML file; copy it to the unit's `pdf/` folder |
| Study handout (plan 01) | `solutions/_tools/handout.py`, written in plan 01's first session: slide frames plus narration → PDF with `pandoc` and `xelatex` |
| Companion PDF (plan 02) | `build-sd-booklet.sh` from `~/.claude/skills/slide-video-kit/templates/reference-design/` (needs `pandoc`, `xelatex`, `plantuml`, `rsvg-convert`; all installed) |
| Publish kit (local text and thumbnail only) | `~/.claude/skills/slide-video-kit/scripts/publish_kit.py` |
| Delivery | Finished MP4s and PDFs stay in their local output folders. **No copy to Google Drive** or any cloud folder (author's decision, 2026-11-13) |

Voices are Kokoro through the `audio-version` skill. Never macOS `say`.
