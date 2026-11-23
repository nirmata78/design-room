---
title: "SD-98 · A Reproducible Replay and Regression-Gate Platform"
subtitle: "A reference solution for a system design round at the Staff bar: new builds run on petabytes of recorded logs as pure functions of pinned manifests, unchanged work reused by content, and a release gate that compares pairs under versioned rules and proves it can fail"
author: "design-room reference solution · practise with the simulator first"
date: "22 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: gblueink
urlcolor: gblueink
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-98`** in
[design-room](https://github.com/nirmata78/design-room), and the written companion to its reference-solution video (the
**compact cut**: about an hour, six challenges). It shows how a strong Staff candidate (L6/L7) runs the round, and the **why**
behind every line.

**One question, many names.** Autonomous-driving companies ask it as *"a deterministic simulation and log-and-replay
platform"*; others ask for *traffic replay against a new service version* or *offline evaluation of a new model on recorded
inputs*. The bank keeps the generic form. Its neighbours: SD-32 (build caching by content hash), SD-28 (DAG execution), SD-66
(GPU scheduling), SD-97 (ingesting the logs this platform replays).

**Three layers.** Part I explains the system in pictures. Part II is the round, stage by stage; the video's six challenges
are Stage 6. Part III is the internals: deterministic harnesses, Merkle keys, Kueue, paired statistics.

::: {.key title="Top-3 number"}
One of the back-of-the-envelope numbers worth computing out loud in the round.
:::

::: why
Explains a term or a decision in plain words. For you, not for the interviewer.
:::

> Words you can say in the room, nearly verbatim.

::: warn
A trap: something weak candidates do, or a claim that breaks under a follow-up question.
:::

::: load
What this part of the system sees at peak, with numbers.
:::

**Practise in three passes.** Read Parts I and II; run the simulator cold
(`Read CLAUDE.md. Mock me: SD-98, Google, staff, full round.`); debrief against Stage 12.

**About the numbers.** The scale is the cue sheet's. Everything else is arithmetic with labelled assumptions (bytes per
log-minute, GPU-minutes per log-minute, price per GPU-hour). None is a measurement or any company's real figure, and this is
not any company's actual design.

**The prompt:** *"Thousands of engineers want to run new builds against petabytes of recorded logs, and get results they can
trust before a release. Design the platform."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Make every run a pure function of a pinned manifest,** so outputs can be cached by content and differences mean something;
**then gate on paired statistics under a versioned policy.**
:::

::: why
**Why this sentence.** Determinism is not a nicety here; it is what makes the other two parts possible. A cache hit is only
safe if recomputing would give the same answer, and a difference between two builds only means something if a build agrees
with itself. Everything after it defends one of those three clauses.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

| Term | Plain meaning | Where it lives |
|---|---|---|
| **Log chunk** | One minute of recorded sensor and vehicle data, immutable, named by its hash | the log store |
| **Scenario** | A slice of log worth replaying: 2–20 minutes around an event | the catalog |
| **Scenario set** | A versioned list of scenarios; a version never changes | the catalog |
| **Stage** | One step of the replay: scenario loading, perception, planning, metrics | the stage graph |
| **Manifest** | Everything a run reads, by content: chunks, image digests, model hashes, map, seeds, mode | the catalog |
| **Stage key** | A hash of a stage's code, parameters, seed, mode and its inputs' keys | the planner |
| **Artifact** | A stage's output, stored under its key | the artifact cache |
| **Open loop / closed loop** | Other road users replayed as logged / simulated as reacting agents | the harness |
| **Divergence** | How far the new build's vehicle has drifted from the logged one | the harness |
| **Baseline** | The last released build's run on the same set version | the gate |
| **Gate policy** | Versioned rules: which metrics block, at what interval | a reviewed repository |

## What one run experiences

1. **Asked.** An engineer submits build `7f3c` (images by digest) on set `left-rain@1`, seed 42.
2. **Pinned.** The planner writes manifest `m-9921`: the set's 9,200 chunk hashes, every image digest, model hashes, map
   version 31, the agent models, seed and mode.
3. **Keyed.** For each scenario it builds the stage graph and chains keys: loader, perception, planning, metrics.
4. **Looked up.** Perception's keys all hit (it did not change); planning's all miss.
5. **Scheduled.** 1,840 planning jobs go to the team's queue.
6. **Replayed.** A worker reads perception's outputs from the cache and the needed log topics by byte range, replays them
   in a harness that owns the clock and the message order, and writes planning's output (blob first, then the index row).
7. **Measured.** Metrics land in the results store as run 9921, with the manifest attached.

## The whole design on one page

![Version 4, with the mechanisms on it.](diagrams/video-recap.pdf){width=100%}

## Where the load lands

::: load
**Gate day:** 50,000 scenarios × 5 log-minutes = 250 TB read in four hours (≈ 17 GB/s); ≈ 1,040 GPUs if perception must be
recomputed, ≈ 1,040 CPU cores if only planning changed. **A month:** 6 M scenario-runs, 30 M log-minutes, ≈ 500,000 GPU-hours
uncached (≈ $1 M at $2 an hour). **Cache:** ≈ 100 TB. **Metrics:** 6 B rows a month. **Logs:** 20 PB, +1 PB a month.
:::

\newpage

# Part II: The round, stage by stage

| Stage | Minutes (of 60) | What you produce |
|---|---|---|
| 1 Clarify | 0–6 | The scale line; five questions; four FRs; IN and OUT |
| 2 Estimates | 6–11 | Gate bytes and GPUs; monthly cost; cache and metric volume |
| 3 API and data | 11–16 | Sets, runs, gates; the manifest |
| 4 High-level design | 16–28 | V1, V2, V3; two flows; four sequences |
| 6 Deep dives | 28–52 | Two to four of the six challenges |
| 8–9 Failures, SLOs, cost | 52–57 | Two minutes each |
| 11 Close | 57–60 | Four sentences |

# Stage 1: Clarify requirements

**The scale line** (given): 1 PB of new logs and about 6 M scenario-runs a month; 20 PB kept; 3,000 engineers; on release-cut
day, a 50,000-scenario gate due within four hours.

| Question | Answer | What it changes |
|---|---|---|
| What is a scenario, and what does it cost? | 2–20 log-minutes, avg 5; ~1 GB a log-minute; ~1 GPU-min per log-minute for perception | compute is the bill; reuse matters |
| How reproducible? | An incident replay reproduces a year later | every input pinned by content |
| Open loop or closed? | Mostly log replay; agents for some sets | divergence must be measured |
| Who blocks a release? | The safety team's rules; overrides need an approver | policy as versioned data |
| Where does it run? | Company Kubernetes, GPUs shared with training | quotas, priority, preemption |

**FRs:** FR1 *Find* (versioned sets) · FR2 *Run* (reuse what is unchanged) · FR3 *Reproduce* (from a manifest) · FR4 *Gate*.
**NFRs** (initial targets): gate p95 4 h; bit for bit on CPU stages, a declared tolerance on GPU stages; an engineer's 1,000-
scenario run in 15 minutes; zero unexplained passes. **Out:** fleet ingestion, simulator physics, training, the release
pipeline itself.

![C4 level 1.](diagrams/video-c4-context.pdf){width=90%}

# Stage 2: Back-of-the-envelope

::: {.key title="Top-3 number 1: the gate's GPUs"}
50,000 × 5 log-minutes = 250,000 GPU-minutes ≈ 4,170 GPU-hours; in four hours, **≈ 1,040 GPUs**. *What it means:* a gate that
recomputes perception every time cannot be reserved for; reuse is not an optimisation. *Say:* "Reuse is the difference between
possible and not."
:::

::: {.key title="Top-3 number 2: the monthly bill"}
6 M runs × 5 log-minutes = 30 M GPU-minutes = 500,000 GPU-hours ≈ **$1 M a month** at $2. *What it means:* every ten points of
cache hit rate is about $100 k a month. *Say:* "The cache's hit rate is a line on the budget."
:::

::: {.key title="Top-3 number 3: copies"}
6 M runs × 5 GB = **30 PB a month** if each job copied its logs: more than the archive. *What it means:* workers read in place,
by byte range, near the data. *Say:* "Nothing is copied; chunks are read where they live."
:::

| Number | Arithmetic | Decides |
|---|---|---|
| Gate reads | 250 TB ÷ 14,400 s ≈ 17 GB/s | parallel byte-range reads |
| Gate, perception cached | ≈ 4,170 CPU-hours ≈ 1,040 cores for 4 h | planning changes are cheap |
| Cache | 100 MB × 50,000 × 20 versions ≈ 100 TB | blob store + index |
| Metrics | 6 M × 1,000 ≈ 6 B rows a month | columnar store |
| One engineer | 5,000 log-min ÷ 15 min ≈ 330 cores, or 330 GPUs on a miss | quotas |

![The gate budget.](diagrams/video-budget.pdf){width=95%}

# Stage 3: API and data

```json
POST /v1/runs
{"build": "7f3c",
 "images": {"perception": "sha256:91ab...",
            "planning": "sha256:4c07..."},
 "set": "left-rain@1",
 "seed": 42}

201 Created
{"run_id": 9921, "manifest_id": "m-9921", "cache": {"hit": 0.71}}
```

`POST /v1/sets` (FR1) saves a query as `name@version`. `POST /v1/runs` with `from_manifest` (FR3) reproduces; `verify=true`
re-executes and compares output hashes. `POST /v1/gates` (FR4) answers pass or block with reasons and the policy version.

::: why
**Why digests, not tags.** A tag (`perception:latest`) can move; a digest cannot. A run that names a tag cannot be reproduced,
and its cache key would be a lie.
:::

![Conceptual model.](diagrams/video-erd-chen.pdf){width=95%}

![Physical model.](diagrams/video-erd-physical.pdf){width=95%}

# Stage 4: High-level design

![V1: pinned runs on a batch pool. Reproducible; every build recomputes everything.](diagrams/video-base-v1.pdf){width=100%}

![V2: a DAG planner and an artifact cache. Reuse by content.](diagrams/video-base-v2.pdf){width=100%}

![V3: the gate service and the release pipeline. Paired verdicts.](diagrams/video-base-v3.pdf){width=100%}

![FR2: a run, numbered.](diagrams/video-flow-run.pdf){width=100%}

![FR4: a gate, numbered.](diagrams/video-flow-gate.pdf){width=100%}

![FR1, find.](diagrams/video-seq-find.pdf){width=80%}

![FR2, run.](diagrams/video-seq-run.pdf){width=85%}

![FR3, reproduce.](diagrams/video-seq-repro.pdf){width=80%}

![FR4, gate.](diagrams/video-seq-gate.pdf){width=85%}

# Stage 5: Components and technologies

![The sim worker.](diagrams/video-c4-comp-worker.pdf){width=100%}

![The DAG planner.](diagrams/video-c4-comp-planner.pdf){width=100%}

![The gate service.](diagrams/video-c4-comp-gate.pdf){width=100%}

![The container view with technologies.](diagrams/video-c4-containers-tech.pdf){width=100%}

<!-- stack:sections -->

## Log store: MCAP chunks on object storage

*How it is built.* Logs are cut into one-minute MCAP chunks with a per-topic index, each named by its SHA-256. Workers read by byte range and verify the hash. About 1 GB a log-minute (compressed camera, lidar and radar subsets, illustrative). 20 PB today, plus 1 PB a month; cold chunks move to an archive class after 90 days unless a scenario set references them. A release gate reads about 250 TB in four hours, about 17 GB/s, spread over thousands of chunks: object storage serves that in parallel; the scheduler places workers in the region that holds the chunks.

*Why MCAP files on GCS, one-minute chunks:* Hashed chunks make a manifest a list of hashes; byte-range reads fetch one topic without a copy.

*Rejected:*

- **HDFS or a shared file system**: Another 20 PB system to run, and a copy per job.
- **Logs in a database**: Frames are blobs: more cost, a second truth, no byte ranges.

*Course:* building-blocks course, part 7 §7.10–7.12 (blob layout, integrity).

*Drill.* "A chunk is re-uploaded after a fix to the logger. What happens to old results?" Nothing changes under them: the fixed chunk has a new hash, so it is a new input. Old manifests still name the old hash, so old runs stay reproducible; a new scenario-set version picks up the new chunk.

## Artifact cache: a content-addressed store with an index

*How it is built.* Key = SHA-256(image digest, params, seed, mode, input keys). The blob is written first, then the index row, so a row always finds a whole blob. About 100 TB of perception outputs for 20 versions of the gate set, plus exploratory outputs evicted by last access after 30 days. Bigtable rows are tiny (≈ 200 bytes); lookups are batched per scenario. 1 % of hits are re-computed by the auditor and compared byte for byte (challenge 6).

*Why CAS blobs on GCS + a Bigtable index:* A key that hashes everything a stage read hits only when recomputing would give the same output.

*Rejected:*

- **Redis**: 100 TB does not belong in memory, and silent eviction loses cited results.
- **A Bazel remote cache**: A near-equal for build actions; small outputs, eviction not tied to gate sets.

*Course:* building-blocks course, part 7 §7.12 (integrity) and part 9 §9.1 (caching patterns).

*Drill.* "A stage reads an environment variable that is not in its key. What breaks?" The cache returns an output computed under a different value: a poisoned hit that no key comparison can see. The fix is hermeticity: stages run in a sandbox where only the manifest's inputs exist, so anything a stage can read is in its key.

## Scheduler: Kubernetes with Kueue

*How it is built.* Gates run in a reserved, top-priority queue; teams share a cohort and borrow idle quota. Exploratory jobs are preemptible at stage boundaries. GPU pools by type; gang admission for multi-GPU stages. Fair share by team over a rolling day. A gate needs ≈ 1,040 GPUs for four hours if nothing is cached, ≈ 300 with the usual hit rate; the reserved queue holds 400 and borrows the rest.

*Why Kubernetes + Kueue, a ClusterQueue per team:* Admission by quota with borrowing, priority and preemption, on the cluster we already run.

*Rejected:*

- **One FIFO queue**: The gate waits behind exploration; one team fills the pool.
- **Slurm**: Strong at fair share; a separate world from our Kubernetes images.

*Course:* building-blocks course, part 15 §15.4 (priority, quota and preemption) and §15.8 (task leasing).

## Results store and catalog: ClickHouse and PostgreSQL

*How it is built.* `metric(run, scenario, name, value)` in ClickHouse, ordered by (scenario, name, run). Manifests, sets and verdicts in PostgreSQL, immutable once written. A gate decision compares 50,000 scenarios × ~1,000 metrics for two runs: 100 M values, a few seconds in a columnar store. Manifests are rows with content hashes; a scenario set is a versioned list of (chunk range, tags).

*Why ClickHouse for metrics; PostgreSQL for manifests:* Six billion metric rows a month are scanned by column; manifests and verdicts must be transactional.

*Rejected:*

- **PostgreSQL for metrics**: Six billion narrow rows a month: every comparison is a slow scan.
- **Elasticsearch**: Search over text, not paired numbers across 50,000 scenarios.

*Course:* building-blocks course, part 14 §14.9 (columnar storage) and part 8 §8.1 (isolation).

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Log store | MCAP chunks on GCS | HDFS, a database | immutable, hashed, read by range |
| Artifact cache | CAS on GCS + Bigtable | Redis, Bazel cache | key = hash of everything read |
| Scheduler | Kubernetes + Kueue | FIFO queue, Slurm | quota, borrowing, preemption |
| Results, catalog | ClickHouse; PostgreSQL | Postgres for metrics, Elasticsearch | columns for metrics, rows for manifests |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | A fixed random seed | it removes one source of difference; threads, GPU atomic adds and the wall clock still reorder the computation. |
| 6.2 | Caching by build number | a new build invalidates every stage, and a stage whose dependency changed under the same name serves a stale hit. |
| 6.3 | One FIFO queue | the release gate waits behind exploration, and one team can fill the cluster. |
| 6.4 | Frame-by-frame comparison with the log | after the ego diverges, the log no longer shows what the other road users would have done. |
| 6.5 | A fixed threshold against yesterday's run | noise moves it, the baseline drifts, and nobody can say later why a build passed. |
| 6.6 | Pass-rate dashboards | a gate that cannot fail looks exactly like a gate that is passing. |

<!-- /stack:summary -->

## When you don't need all this (the alternate path)

![ALTERNATE: no planner, no cache; a nightly recompute.](diagrams/video-alt.pdf){width=100%}

A nightly job runs every scenario on the release branch in the same deterministic harness and compares with the previous
night by fixed rules. It gives up per-change answers (engineers wait a night), reuse, and a cost that does not grow with
builds × scenarios. A 1,000-scenario gate is 83 GPU-hours (21 GPUs for four hours); at 50,000 it is 1,040. **Below about 5,000
scenarios (≈ 100 GPUs), ship the nightly recompute** and build the deterministic harness anyway: the cache needs it later.

# Stage 6: Deep dives

## 6.1 Same build, two answers (the crux)

**The case.** Scenario 18,204 gives no hard brake on run A and one on run B, from the same manifest. Comparing message hashes
step by step, the first difference is message 41,207, the tracker's output: a lidar and a camera message with equal timestamps
were delivered in thread order, and a GPU reduction used atomic adds.

| Source | Example | What removes it |
|---|---|---|
| Wall clock | a timeout decides a branch | simulated time; the call fails in the sandbox |
| Thread order | equal timestamps, either order | one bus; order by (time, topic, sequence) |
| Random numbers | unseeded sampling | seeds per scenario and stage, from the manifest |
| GPU atomics | a reduction sums in a new order | deterministic kernels, or a declared tolerance |
| Unpinned inputs | "latest" model, a moving map | digests and hashes only |
| Hidden reads | an environment variable, a file | a hermetic sandbox |

![Finding non-determinism: run twice, compare message hashes to the first difference.](diagrams/video-seq-ch1-double.pdf){width=80%}

::: warn
**"Set the random seed."** It removes one of six sources. Threads, GPU atomics, the wall clock, unpinned inputs and hidden
reads remain. An interviewer who hears only the seed will ask about threads next.
:::

**Cost and limit.** Deterministic GPU kernels can be ~30 % slower (illustrative). Gate and reproduction runs always use them;
exploration may use a fast mode, which is part of the cache key so a fast output can never satisfy a gate. One percent of runs
are run twice; a scenario that disagrees with itself is quarantined.

> A replay is only useful if a build agrees with itself. The harness owns the clock, the message order and the seeds; GPU stages
> run deterministically for gates; and a sample run twice finds what I missed.

## 6.2 A perception change

**The case.** Build 412 changes the tracker inside perception. Keyed by build, everything recomputes (1,040 GPUs, a nine-hour
gate). Keyed by stage name, planning reuses outputs computed on build 411's tracks.

```
key(s) = sha256(s.image_digest, s.params, s.seed,
               s.mode, [key(i) for i in s.inputs])

for s in topo_order(stages):
    if index.get(key(s)): continue    # a hit
    out = run_hermetic(s, inputs=blobs(s.inputs))
    blob = cas.put(sha256(out), out)  # 1: blob
    index.put(key(s), blob, producer=run)  # 2: row
```

![Mechanism M3 at protocol level: two keys, one hit, one miss.](diagrams/video-seq-th-keys.pdf){width=80%}

::: why
**Why a chain.** Including the input keys in a stage's key means a change upstream changes every key downstream of it, and
nothing else. Writing the blob before the index row means a crash leaves an orphan blob, never a row pointing at half an output.
:::

**A poisoned entry.** Delete its index row (never overwrite a key); find what used it by producer run and by downstream keys that
contain it; prevent the next by recomputing 1 % of hits (6.6).

## 6.3 Release day

**The case.** A 40,000-job sweep at 09:00; the release is cut at 10:00; in one FIFO queue the gate answers at 18:40.

**The mechanism (Kueue).** A reserved, highest-priority ClusterQueue for gates (400 GPUs) that borrows from the shared cohort;
one ClusterQueue per team in the cohort, lending idle quota; exploratory jobs preemptible, checkpointing at stage boundaries
(their outputs are already in the cache), so a preemption loses at most one stage. **When nothing hits:** pre-warm the gate set
nightly on the head of the release branch; a training yield agreement for up to 600 GPUs; and an honest limit of about six
hours for a perception change landed on cut day itself.

## 6.4 The log does not react

![Open-loop replay after divergence.](diagrams/video-divergence.pdf){width=95%}

**The mechanism.** The harness measures divergence (position and heading against the log) every step; metrics are scored up to
the first divergence above 1 m and the scenario reports where it was. Interactive sets run closed loop: other road users are
agent models, pinned in the manifest and validated on their own (an agent that never yields fails its validation). Closed
loop answers *what if*, not *what happened*, so results carry the agents' version.

## 6.5 Block or pass?

**The case.** Week one: +0.3 % hard brakes against yesterday, above a 0.25 % threshold: block, and a rerun shows +0.1 %. Week
two: +0.2 %, a pass, while yesterday already carried +0.2 %: +0.4 % against the release ships.

```
base = last_release_run(set_version)
for m in policy.metrics:
    d = [cand[s][m] - base[s][m] for s in scenarios
         if s not in flaky]
    lo, hi = bootstrap_interval(d, 0.95)
    if lo > policy.limit[m]: block(m, lo, hi)
record(build, cand, base, policy.version, verdict)
```

::: why
**Why pairs.** Scenario difficulty varies far more than a build's effect. Differencing on the same scenario removes it; a
bootstrap over scenarios gives an honest interval without assuming a distribution.
:::

**Overrides.** Allowed with a named approver from the safety team, a reason and an expiry, recorded with the verdict, and
reviewed: either the policy changes or the override was wrong.

## 6.6 The gate passed (observability)

**The case.** A stage starts reading an undeclared config file; its key misses it; planning keeps hitting stale outputs; the gate
compares old planning with old planning and passes; the field regresses.

![V4: a gate auditor.](diagrams/video-base-v4.pdf){width=100%}

| Check | What it catches |
|---|---|
| A weekly planted regression that must be blocked | a gate that cannot fail |
| 1 % of runs twice | non-determinism |
| 1 % of cache hits recomputed | inputs missing from keys |
| Gate-set situations against field miles | coverage gaps |

| Symptom | Paired with | Means |
|---|---|---|
| Cache audit mismatch | double runs agree | an input missing from a key |
| Double runs disagree | cache audit clean | non-determinism in a stage |
| Known-bad build passes | — | the gate cannot fail: stop releases |
| Pass rate 100 % for weeks | few policy changes | check coverage |
| Gate time up | hit rate down | a change upstream of most stages |

# Stage 8–9: Failures, SLOs, cost

| Failure | What happens | Recovery |
|---|---|---|
| A worker dies mid-stage | the stage reruns; earlier stages hit | automatic |
| The index is unavailable | runs proceed as all-miss (slower, correct) | degrade, page |
| The log store is slow in one region | the scheduler places work where chunks are | placement |
| A poisoned artifact | audit mismatch pages | delete row, rerun descendants |

**SLIs:** known-bad blocked 100 %; double-run agreement ≥ 99.9 % of scenarios; cache-audit mismatches 0; gates within 4 h for 95 %;
hit rate ≈ 70 %, watched for drops. **Cost:** compute dominates (≈ $1 M a month uncached); the levers are hit rate, pre-warming,
preemptible capacity for exploration, and smaller gate sets chosen by coverage.

# Stage 10: The EM layer (dropped in the compact cut)

In a manager round: V1 (manifests and the deterministic harness) is the first quarter and pays for itself in reproducible
incidents; the cache and planner follow; the gate and its auditor come with the safety team as co-owner.

# Stage 11: The close

> **What:** runs as pure functions of pinned manifests, cached by content, gated on paired intervals. **Trade-off:** determinism
> work and hermetic stages, for reuse and differences that mean something. **Risk:** a gate that cannot fail; hence planted
> regressions and audits. **Next:** measure coverage against field miles.

# Stage 12: Self-check

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Determinism | "set the seed" | harness owns time and order | finds residual non-determinism by double runs |
| Reuse | cache by build | content keys per stage | Merkle chain, hermeticity, blob-then-index |
| Capacity | one queue | quotas and priority | preemption at stage ends; pre-warming |
| Validity | scores everything | knows open loop diverges | divergence scoring, versioned agents |
| Decisions | threshold vs yesterday | paired against the release | intervals, versioned policy, recorded overrides |
| Operations | job success | double runs | a gate that proves it can fail |

\newpage

# Part III: The internals

## Appendix A: A deterministic harness

The harness is a discrete-event simulator. It keeps a priority queue of messages ordered by (simulated time, topic, sequence
number) and delivers one at a time to the component that subscribes; components may only learn the time from the harness. The
sandbox (no network, a read-only filesystem holding only the manifest's inputs, no clock syscall) makes hidden reads fail loudly.
GPU frameworks offer deterministic modes that avoid atomic reductions; where none exists, a stage declares a tolerance per output.

## Appendix B: Content-addressed storage and Merkle keys

A content-addressed store names a blob by the hash of its bytes, so a blob is immutable and self-verifying. A stage key hashes
the stage's identity and its inputs' keys, forming a Merkle DAG: two runs that share a prefix of inputs share the keys of every
stage in that prefix. An index maps stage keys to blob hashes; writing the blob before the row makes the row a commit point.

## Appendix C: Kueue in one page

Kueue admits Kubernetes Jobs into ClusterQueues by quota. ClusterQueues in one cohort can borrow each other's unused quota, and
reclaim it, preempting borrowers if needed; priority classes order admission and preemption. Jobs are suspended until admitted,
so the default scheduler only places pods that already have quota.

## Appendix D: Paired bootstrap

For each scenario s, d_s = candidate_s − baseline_s. Resample the scenarios with replacement many times, compute the mean of d each
time, and take the 2.5th and 97.5th percentiles as a 95 % interval. Block when the whole interval is past the limit. Flaky
scenarios (that disagree with themselves) are excluded and listed.

\newpage

# One-page cheat card

- **Scale:** 1 PB logs and 6 M runs a month; 20 PB kept; a 50,000-scenario gate in 4 h.
- **Numbers:** 250 TB and ≈ 1,040 GPUs per uncached gate; ≈ $1 M a month uncached; 100 TB cache; 6 B metric rows a month.
- **Thesis:** pure functions of pinned manifests; cache by content; gate on pairs under a versioned policy.
- **Mechanisms:** M1 manifest · M2 simulated time and ordered delivery · M3 Merkle stage keys · M4 paired intervals · M5 quotas.
- **Stack:** MCAP chunks on GCS · CAS + Bigtable index · Kubernetes + Kueue · ClickHouse + PostgreSQL.
- **Challenges:** two answers · a perception change · release day · the log does not react · block or pass · the gate passed.
- **Alternate:** a nightly recompute below ~5,000 scenarios.
