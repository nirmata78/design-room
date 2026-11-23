# SD-98 · Reproducible replay & regression-gate platform — reference-solution video outline

Target level: staff · **Compact cut** (GUIDELINES §3.4): ≈ 61 min, ≈ 7,100 words, 6 challenges, no build-cost chapter, no drill.
Generic form of "deterministic simulation and log-and-replay platform" (autonomous driving), traffic replay for a new service
version, and offline evaluation of a model on recorded inputs.

## Thesis and definition

- **Thesis:** make every run a pure function of a pinned manifest, so outputs can be cached by content and differences mean
  something; then gate on paired statistics under a versioned policy.
- **Definition:** a platform that runs new builds against recorded logs as pure functions, reuses unchanged stage outputs by
  content, and answers "may this build ship?" by comparing it with the last release under versioned rules.
- **Hook:** recompute everything (trustworthy, ≈ 1,040 GPUs per gate) or reuse by name (cheap, silently stale); content keys
  give both, only if the computation is deterministic and hermetic.

## Scale line (GUIDELINES §3.1)

Volume per month: **1 PB of new logs, 6 M scenario-runs** · Total: **20 PB** of logs kept; 3,000 engineers · Peak: **release
cut**: a 50,000-scenario gate due within 4 hours, on top of the day's runs.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | "Run simulations at scale" | What must be reproducible, how fast the gate answers, who decides a block |
| Correctness | "Set the random seed" | Pinned manifest, simulated time, ordered delivery, hermetic stages |
| Trade-offs | Cache everything or nothing | Content keys; open loop against closed loop |
| Depth | "Kubernetes jobs" | Merkle stage keys, quotas and preemption, paired statistics |
| Operations | Job success rate | Double-run agreement, cache audits, a known-bad build that must fail |

## 1 · Requirements and scope

Clarifying answers: a scenario is 2–20 log-minutes (avg 5), ~1 GB per log-minute, ~1 GPU-minute per log-minute for perception ·
an incident replay must reproduce a year later · mostly open-loop replay, reactive agents for some sets · the safety team owns
the rules, overrides need a named approver · compute is the company's Kubernetes, GPUs shared with training.

FR1 Find (versioned scenario sets) · FR2 Run (a build on a set; reuse what is unchanged) · FR3 Reproduce (from a manifest) ·
FR4 Gate (candidate against the last release: pass or block).
NFR (initial targets): gate p95 4 h · bit-for-bit on CPU stages, declared tolerance on GPU stages · an engineer's 1,000-scenario
run in 15 min · zero unexplained passes.
IN: sets, manifests, harness, caching, scheduling, results, gate, audit. OUT: fleet ingestion, simulator physics, training, the
release pipeline. Core: runs defined by pinned manifests; outputs cached by content; a gate comparing pairs under versioned rules.

## 2 · Estimates

| Number | From | Arithmetic | Label | Decides |
|---|---|---|---|---|
| Gate bytes | peak | 50,000 × 5 × 1 GB = 250 TB; ÷ 14,400 s ≈ 17 GB/s | illustrative | byte-range reads, no copies |
| Gate GPUs, nothing cached | peak | 250,000 GPU-min = 4,170 GPU-h; ÷ 4 h ≈ 1,040 GPUs | illustrative | reuse is required |
| Gate, perception cached | peak | ≈ 4,170 CPU-h ≈ 1,040 cores for 4 h | illustrative | planning changes are cheap |
| Monthly compute | monthly runs | 6 M × 5 = 30 M GPU-min = 500,000 GPU-h ≈ $1 M at $2 | illustrative | 10 points of hit rate ≈ $100 k a month |
| Cache | gate set | 100 MB × 50,000 × 20 versions ≈ 100 TB | illustrative | blob store + index |
| Metrics | monthly runs | 6 M × 1,000 = 6 B rows a month | illustrative | columnar store |
| Copies | monthly runs | 6 M × 5 GB = 30 PB a month | illustrative | read in place |
| One engineer's run | NFR | 5,000 log-min ÷ 15 min ≈ 330 cores, or 330 GPUs if perception misses | illustrative | quotas |
| Gate budget | NFR | 15 min plan + 165 min compute + 15 min decide + margin | target | pre-warm the cache |

## 3 · Theory

1. Is: new code on recorded inputs as a pure function. Not a batch cluster, not CI tests, not production shadowing.
2. S1 reproducible (bitwise CPU; tolerance GPU) · S2 a hit equals a recompute · S3 no false pass · L1 gate in 4 h · L2 no starvation.
3. Tension: recompute for trust, reuse for speed (figure `tension`). Where randomness hides: wall clock, thread order, seeds, GPU
   atomics, unpinned inputs, hidden reads.
4. Mechanisms: M1 pinned manifest · M2 simulated time and ordered delivery · M3 content-addressed memoisation (Merkle keys) ·
   M4 paired comparison under a versioned policy · M5 quotas, priority, preemption.
5. Options: A scripts on copied logs · B recompute everything · C reuse by build name · D shadow only · **E pinned manifests,
   content-keyed stages, deterministic harness** (gives up: every input hashed; hermeticity enforced). One sequence: `seq-th-keys`.
6. Failure catalogue → the six challenges.

## 4 · API and entities

`POST /v1/sets` (FR1) · `POST /v1/runs` (FR2; `from_manifest` + `verify` for FR3) · `POST /v1/gates` (FR4). Entities: SCENARIO SET,
SCENARIO, LOG CHUNK, MANIFEST, RUN, ARTIFACT, GATE DECISION. Physical: `manifest`, `run`, `artifact_index` (Bigtable),
`metric` (ClickHouse), `gate_decision`, `scenario_set`.

## 5 · High-level design

| Version | Adds | Answers | Leaves |
|---|---|---|---|
| V1 | log store, catalog, run API, scheduler, sim workers, results | reproducible runs | every build recomputes everything |
| V2 | DAG planner, artifact cache | reuse by content | who decides a block |
| V3 | gate service, release pipeline | paired verdicts | is the gate itself right? |
| V4 (ch. 6) | gate auditor | the gate proves it can fail | — |

Canonical diagram plan: containers drawn once (`base-v1`), then `new=2,3,4`; flows `flow-run`, `flow-gate`; technologies
`focus=`; map `attack=`; challenges on component views (worker: 1, 4; planner: 2; gate: 5) or the container view (3, 6); recap
`badges=`. Sequences: `seq-find`, `seq-run`, `seq-repro`, `seq-gate`.

## 5.1 · Components and technologies

Component views: sim worker, DAG planner, gate service.

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Log store | MCAP files on GCS, one-minute chunks | Logs are cut into one-minute MCAP chunks with a per-topic index, each named by its SHA-256 | HDFS or a shared file system; Logs in a database | 7 §7.10–7.12 |
| Artifact cache | CAS blobs on GCS + a Bigtable index | Key = SHA-256(image digest, params, seed, mode, input keys) | Redis; A Bazel remote cache | 7 §7.12, 9 §9.1 |
| Scheduler | Kubernetes + Kueue, a ClusterQueue per team | Gates run in a reserved, top-priority queue; teams share a cohort and borrow idle quota | One FIFO queue; Slurm | 15 §15.4, 15.8 |
| Results store and catalog | ClickHouse for metrics; PostgreSQL for manifests | `metric(run, scenario, name, value)` in ClickHouse, ordered by (scenario, name, run) | PostgreSQL for metrics; Elasticsearch | 14 §14.9, 8 §8.1 |

Fix-slide rejections: 1: A fixed random seed; 2: Caching by build number; 3: One FIFO queue; 4: Frame-by-frame comparison with the log; 5: A fixed threshold against yesterday's run; 6: Pass-rate dashboards.

<!-- /stack:outline -->

## 5.2 · Alternate path

Nightly recompute of every scenario on the release branch, no planner, no cache. Gives up: cost ∝ builds × scenarios, a night's
wait, no reuse. Line: 1,000 scenarios ≈ 21 GPUs for 4 h; 50,000 ≈ 1,040; below ≈ 5,000 scenarios (≈ 100 GPUs), ship the nightly.

## 7 · Challenges

### Challenge 1 · Same build, two answers (crux)
Naive: set the seed. Case: scenario 18,204, message 41,207, equal timestamps in thread order, GPU atomics. Fix: one sim clock,
(time, topic, sequence) delivery, seeds per scenario and stage, deterministic kernels, no wall clock in the sandbox; double runs
find the rest (`seq-ch1-double`). Push: deterministic kernels cost 30 % → gates and repro deterministic, exploration fast with the
mode in the key; 1 % double runs; quarantine. Version: no change. Rejected: a fixed random seed.

### Challenge 2 · A perception change
Naive: cache by build. Case: build 412 changes the tracker. Fix: key = SHA-256(image, params, seed, mode, input keys); blob before
index; hermetic sandbox (pseudocode). Push: a poisoned entry → delete the row, lineage by producer and keys, 1 % hit audit.
Version: no change. Rejected: caching by build number.

### Challenge 3 · Release day
Naive: one FIFO queue. Case: a 40,000-job sweep; gate answers 8 h 40 min after the cut. Fix: Kueue: reserved gate queue (400 GPUs,
borrows), team queues in a cohort, preemption at stage ends. Push: nothing hits → nightly pre-warm, a training yield agreement;
honest limit ≈ 6 h for a cut-day perception change. Version: no change. Rejected: one FIFO queue.

### Challenge 4 · The log does not react
Naive: a collision is a collision. Case: brakes at 5.4 s instead of 7.0 s; divergence > 1 m at 6.2 s; the logged follower hits us.
Fix: measure divergence each step, score up to it; closed loop with pinned agent models for interactive sets (figure
`divergence`). Push: safety sets diverge early → closed loop by default; agents validated. Version: no change.
Rejected: frame-by-frame comparison with the log.

### Challenge 5 · Block or pass?
Naive: threshold against yesterday. Case: false block (+0.3 % noise) and false pass (+0.4 % against the release). Fix: baseline
= last release on the same set version; per-scenario differences; bootstrap interval; versioned policy; recorded verdict
(pseudocode). Push: an override → named approver, reason, expiry; reviewed. Version: no change. Rejected: fixed threshold vs yesterday.

### Challenge 6 · The gate passed (observability)
Naive: pass rate and job success. Case: an undeclared config read; planning hits stale outputs; the gate compares old with old.
Fix: **V4** gate auditor: a weekly planted regression that must be blocked, 1 % double runs, 1 % cache audit, coverage against
field miles; symptom pairs; SLIs. Rejected: pass-rate dashboards.

## 8 · Recap

V4 with badges; mistakes table; thesis.

## Canon check

| Canonical point | Covered at, or dismissed because |
|---|---|
| Determinism: seeds, time, ordering, GPU non-determinism | theory "where randomness hides", challenge 1 |
| Versioned inputs: logs, models, maps | manifest (M1), API "manifest in full" |
| Caching intermediate outputs by (input hash, code version) | M3, challenge 2 |
| DAG orchestration on Kubernetes / Borg | planner, scheduler, challenge 3 |
| Open loop against closed loop simulation | challenge 4 |
| Golden-baseline diffing and release gates | M4, challenge 5 |
| Flaky scenarios | challenge 1 push, gate flake list |
| Coverage of the scenario set | challenge 6 |
| Simulator physics and sensor simulation | dismissed: out of scope |
| Log ingestion from the fleet | dismissed: out of scope (SD-97 is its generic question) |
| Build cost and team | dismissed: compact cut |

## Budget (measured)

| Chapter | Words |
|---|---|
| 0 Cold open | 320 |
| 1 Requirements | 561 |
| 2 Estimates | 421 |
| 3 Theory | 920 |
| 4 API and data | 368 |
| 5 Design, 5.1, 5.2 | 1,444 |
| 6 Bridge | 83 |
| 7 Challenges | 2,766 |
| 8 Recap | 239 |
| **Total** | **7,122 (≈ 61 min)** |
