# SD-98 Reproducible replay and regression-gate platform: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I SDK=S-D-K TB=terabytes PB=petabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds CPU=C-P-U CPUs=C-P-Us GPU=G-P-U GPUs=G-P-Us Kafka=Kahf-kah ClickHouse=Click-House GCS=G-C-S MCAP=M-cap SHA-256=shaw-two-fifty-six DAG=dag Kueue=queue Bigtable=Big-table CI=C-I EM=E-M -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Replaying recorded logs against a new build sounds like a batch job. It is asked at autonomous-driving companies and wherever a release must be tested on recorded reality, because a replay is only worth running if the same inputs give the same answer, and a gate is only worth having if it can fail for the right reason.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Thousands of engineers want to run new builds against petabytes of recorded logs, and get results they can trust before a release. Design the platform.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook as one picture. Recomputing everything for every build is trustworthy, and costs about a thousand G-P-Us for each four-hour release gate.
C: Reusing yesterday's outputs by build name is cheap, and silently wrong the day a dependency changes. The design lives in the third box: reuse by content, where a cached output is keyed by a hash of everything that produced it. Then a hit equals a recompute, but only if the computation is deterministic and nothing it reads is missing from the key.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes, one at a time.
[reveal: v-005]
[pause: 0.45]
N: Requirements. Weak: run simulations at scale. Strong: what must be reproducible, how fast the gate must answer, and who decides a block.
[reveal: v-006]
[pause: 0.45]
N: Correctness. Weak: set the random seed. Strong: a pinned manifest, simulated time, ordered delivery, and stages that can read nothing else.
[reveal: v-007]
[pause: 0.45]
N: Trade-offs. Weak: cache everything or nothing. Strong: content keys, what it costs to trust a hit, and closed loop against open loop.
[reveal: v-008]
[pause: 0.45]
N: Depth: Merkle keys per stage, quotas with preemption, paired statistics.
[reveal: v-009]
[pause: 0.45]
N: Operations: not the job success rate, but double-run agreement, cache audits, and a known-bad build that must fail the gate.
[reveal: v-010]
[pause: 0.45]
C: And the rule for the whole round: a difference must mean the build changed, never that the run did.
[pause: 1.0]

[slide: v-011]
[pause: 0.7]
V: Make every run a pure function of a pinned manifest, so outputs can be cached by content and differences mean something. Then gate on paired statistics, under a versioned policy.
[pause: 1.6]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-012]
[pause: 1.2]
C: The scale first, then five questions. Each answer moves the design.
[pause: 1.8]

[slide: v-013]
[pause: 0.6]
C: The scale, written down first.
[reveal: v-014]
[pause: 0.45]
C: A petabyte of new logs a month, and about six million scenario-runs a month from three thousand engineers.
[reveal: v-015]
[pause: 0.45]
C: Twenty petabytes of logs kept today.
[reveal: v-016]
[pause: 0.45]
C: And the peak: on the day a release is cut, a gate of fifty thousand scenarios must answer within four hours, on top of everyone else's runs.
[reveal: v-017]
[pause: 0.45]
C: Every number I use later starts from one of these.
[pause: 0.8]

[slide: v-018]
[pause: 0.6]
C: What is a scenario, and what does replaying one cost?
[reveal: v-019]
[pause: 0.45]
I: Two to twenty minutes of log, five on average. About a gigabyte per log-minute, and the perception stages need about a G-P-U-minute per log-minute.
C: So compute is the bill, and perception is most of it. Whatever avoids recomputing perception is worth building.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: How reproducible does a run have to be?
[reveal: v-021]
[pause: 0.45]
I: An incident replay must give the same answer a year later. Same inputs, same outputs.
C: Then a run is defined by its inputs, and every input must be pinned: logs, code, model weights, maps, seeds.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: Do the other road users react to the new build, or do we replay them as logged?
[reveal: v-023]
[pause: 0.45]
I: Mostly log replay. Reactive agent models exist for some scenarios.
C: Log replay stops being true once the new build acts differently. I'll need to know when that happens. Challenge four.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: Who decides that a result blocks a release?
[reveal: v-025]
[pause: 0.45]
I: The safety team owns the rules. The gate applies them. Overrides need a named approver.
C: So the rules are versioned data, not code buried in a script, and every decision records which version it used.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: Where does the compute come from?
[reveal: v-027]
[pause: 0.45]
I: The company's Kubernetes clusters, sharing G-P-Us with model training.
C: Shared means quotas and preemption. The gate can't wait behind training, and exploration can't starve.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-029]
[pause: 0.45]
C: One, find: select scenarios by tags, and save them as an immutable, versioned set.
[reveal: v-030]
[pause: 0.45]
C: Two, run a build on a set, with results per scenario and metric, reusing whatever didn't change.
[reveal: v-031]
[pause: 0.45]
C: Three, reproduce any past run from its manifest, with the same outputs.
[reveal: v-032]
[pause: 0.45]
C: Four, gate: compare a release candidate with the last release, on the gate set, and answer pass or block. Each gets a sequence later.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: The numbers, initial targets.
[reveal: v-034]
[pause: 0.45]
C: A fifty-thousand-scenario gate within four hours.
[reveal: v-035]
[pause: 0.45]
C: Bit-for-bit reproducible on C-P-U stages, and within a declared tolerance on G-P-U stages.
[reveal: v-036]
[pause: 0.45]
C: An engineer's thousand-scenario run within fifteen minutes, so people iterate.
[reveal: v-037]
[pause: 0.45]
C: And no unexplained pass.
[reveal: v-038]
[pause: 0.45]
C: A gate that can't answer is a release that waits. A gate that answers wrong is a release that ships.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: In scope: scenario sets, manifests, the replay harness, caching, scheduling, results, the release gate and its audit.
[reveal: v-040]
[pause: 0.45]
C: Out, on purpose: ingesting logs from the fleet, the simulator's physics, model training, and the release pipeline itself.
[reveal: v-041]
[pause: 0.45]
C: One thing I'd say aloud: ingestion is out, but its output is my input. I need log chunks I can name by their hash.
[pause: 0.8]

[slide: v-042]
[pause: 1.3]
C: The system in its context.
[reveal: v-043]
[pause: 0.45]
C: Engineers, three thousand of them, run builds against recorded logs and read results.
[reveal: v-044]
[pause: 0.45]
C: The replay platform, one box for now.
[reveal: v-045]
[pause: 0.45]
C: The release pipeline asks it whether a build may ship.
[reveal: v-046]
[pause: 0.45]
C: Log ingest delivers fleet logs, a petabyte a month.
[reveal: v-047]
[pause: 0.45]
C: And the compute cluster runs our pods, shared with training.
[pause: 1.1]

[slide: v-048]
[pause: 0.7]
V: The core is three things. Runs defined by pinned manifests. Outputs cached by the hash of what made them. And a gate that compares pairs, under a versioned policy.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-049]
[pause: 1.2]
C: Numbers next, each from the scale line, each ending in a decision. Illustrative, not anyone's real figures.
[pause: 1.8]

[slide: v-050]
[pause: 1.0]
C: The gate first.
[reveal: v-051]
[pause: 0.45]
C: Fifty thousand scenarios times five log-minutes times a gigabyte is two hundred and fifty terabytes, seventeen gigabytes a second over four hours. Object storage serves that by byte range, if nothing is copied.
[reveal: v-052]
[pause: 0.45]
C: Perception at a G-P-U-minute per log-minute is four thousand one hundred and seventy G-P-U-hours: about a thousand and forty G-P-Us for four hours. Too many to reserve for one gate.
[reveal: v-053]
[pause: 0.45]
C: But if only planning changed and perception's outputs are reused, it's about a thousand C-P-U cores for four hours. Reuse is the difference between possible and not.
[pause: 1.0]

[slide: v-054]
[pause: 1.0]
C: A month.
[reveal: v-055]
[pause: 0.45]
C: Six million runs of five log-minutes is thirty million G-P-U-minutes, five hundred thousand G-P-U-hours. At two dollars an hour, about a million dollars a month. Every ten points of cache hit rate is a hundred thousand dollars a month.
[reveal: v-056]
[pause: 0.45]
C: The cache: a perception output is about a hundred megabytes per scenario. Twenty versions of the gate set is about a hundred terabytes. A blob store with an index, not memory.
[reveal: v-057]
[pause: 0.45]
C: And metrics: a thousand per run is six billion rows a month. A columnar store.
[pause: 1.0]

[slide: v-058]
[pause: 1.0]
C: Storage and reads.
[reveal: v-059]
[pause: 0.45]
C: Twenty petabytes of logs today, a petabyte more a month, about a gigabyte per log-minute. Immutable chunks in object storage.
[reveal: v-060]
[pause: 0.45]
C: A gate reads two hundred and fifty terabytes in four hours: seventeen gigabytes a second, spread over thousands of chunks. Object storage serves that in parallel, by byte range, if the workers run in the region that holds the data.
[reveal: v-061]
[pause: 0.45]
C: And if every job copied its logs first: six million runs times five gigabytes is thirty petabytes moved a month, more than the whole archive. So nothing is copied. Workers read in place.
[pause: 1.0]

[slide: v-062]
[pause: 1.0]
C: And one engineer's run, the thing people do all day.
[reveal: v-063]
[pause: 0.45]
C: A thousand scenarios is five thousand log-minutes.
[reveal: v-064]
[pause: 0.45]
C: If perception hits, planning needs about five thousand C-P-U-minutes. In fifteen minutes that's three hundred and thirty cores, easy from a shared pool.
[reveal: v-065]
[pause: 0.45]
C: If perception misses, it's three hundred and thirty G-P-Us for fifteen minutes: one engineer asking for a third of a gate. That's why quotas exist, and why most people should only change the stages they own.
[pause: 1.0]

[slide: v-066]
[pause: 1.3]
C: The gate budget. Ten minutes to plan and look up keys. About two hours fifty to compute the misses. Ten minutes to pair the results and apply the policy. And about fifty minutes of margin.
C: The margin is for a gate whose perception changed, when nothing hits. That case is challenge three.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-067]
[pause: 1.2]
C: The theory: what makes a replay worth trusting, in terms that outlive any product name. Five mechanisms, the options, and what will go wrong.
[pause: 1.8]

[slide: v-068]
[pause: 0.6]
C: What it is, and what it is not.
[reveal: v-069]
[pause: 0.45]
V: Running new code on recorded inputs as a pure function, so outputs can be reused and compared.
[reveal: v-070]
[pause: 0.45]
C: Not a batch cluster: a batch cluster runs jobs, it doesn't promise two runs agree.
[reveal: v-071]
[pause: 0.45]
C: Not C-I tests: tests assert; a replay measures thousands of metrics and compares distributions.
[reveal: v-072]
[pause: 0.45]
C: And not production shadowing, which sees today's traffic. Replay asks what a new build would have done on yesterday's.
[pause: 0.8]

[slide: v-073]
[pause: 0.6]
C: Safety first: what must never happen.
[reveal: v-074]
[pause: 0.45]
V: S-one: the same manifest gives the same outputs. Bit for bit on C-P-U stages, within a declared tolerance on G-P-U stages.
[reveal: v-075]
[pause: 0.45]
V: S-two: a cached output is exactly what recomputing would produce.
[reveal: v-076]
[pause: 0.45]
V: S-three: a build never passes the gate with an unexplained regression.
[reveal: v-077]
[pause: 0.45]
C: Liveness: L-one, the gate answers within four hours.
[reveal: v-078]
[pause: 0.45]
C: L-two, every team's runs make progress, even on release day.
[pause: 0.8]

[slide: v-079]
[pause: 1.0]
C: Before the mechanisms, where randomness actually hides. Six places.
[reveal: v-080]
[pause: 0.45]
C: The wall clock: a timeout that decides a branch. Removed by simulated time.
[reveal: v-081]
[pause: 0.45]
C: Thread order: two messages with the same timestamp, delivered either way. Removed by one bus with a total order.
[reveal: v-082]
[pause: 0.45]
C: Random numbers that nobody seeded. Removed by seeds from the manifest.
[reveal: v-083]
[pause: 0.45]
C: G-P-U atomic adds, which sum in a different order every time. Removed by deterministic kernels, or a tolerance we declare.
[reveal: v-084]
[pause: 0.45]
C: Unpinned inputs: a latest model, a tag, a map that moved. Removed by digests and hashes.
[reveal: v-085]
[pause: 0.45]
C: And hidden reads: an environment variable, a file nobody declared. Removed by a hermetic sandbox. Setting a seed fixes exactly one of these six.
[pause: 1.0]

[slide: v-086]
[pause: 0.6]
C: Mechanism one: a pinned manifest.
[reveal: v-087]
[pause: 0.45]
C: It protects S-one.
[reveal: v-088]
[pause: 0.45]
C: A run names every input by content: the hashes of its log chunks, the digests of its container images, the hashes of its model weights, the map version, and its seeds.
[reveal: v-089]
[pause: 0.45]
C: It rules out a result that nobody can reproduce or compare.
[reveal: v-090]
[pause: 0.45]
C: It costs discipline: every input must be addressable, and nothing may be read by name at run time.
[pause: 0.8]

[slide: v-091]
[pause: 0.6]
C: Mechanism two: simulated time and ordered delivery.
[reveal: v-092]
[pause: 0.45]
C: It also protects S-one.
[reveal: v-093]
[pause: 0.45]
C: The harness owns the clock: no component may read the wall clock. Messages between components are delivered in the order of time, topic, and sequence number, one at a time.
[reveal: v-094]
[pause: 0.45]
C: It rules out results that depend on which thread happened to run first.
[reveal: v-095]
[pause: 0.45]
C: It costs parallelism inside one scenario. We get it back across fifty thousand scenarios.
[pause: 0.8]

[slide: v-096]
[pause: 0.6]
C: Mechanism three: content-addressed memoisation.
[reveal: v-097]
[pause: 0.45]
C: It protects S-two, and makes L-one affordable.
[reveal: v-098]
[pause: 0.45]
C: Each stage's output is stored under a key that hashes the stage's code, its parameters, its seed and the keys of its inputs. Keys chain, like a Merkle tree: change perception, and every key downstream changes with it.
[reveal: v-099]
[pause: 0.45]
C: It rules out both recomputing what didn't change and reusing what did.
[reveal: v-100]
[pause: 0.45]
C: It costs hermetic stages, an index, and storage for outputs.
[pause: 0.8]

[slide: v-101]
[pause: 0.6]
C: Mechanism four: paired comparison under a versioned policy.
[reveal: v-102]
[pause: 0.45]
C: It protects S-three.
[reveal: v-103]
[pause: 0.45]
C: Run the candidate and the baseline on the same scenarios, take per-scenario differences per metric, and compute an interval, not a single number. The rules that turn intervals into pass or block are versioned data.
[reveal: v-104]
[pause: 0.45]
C: It rules out blocking on noise, passing on luck, and decisions nobody can explain later.
[reveal: v-105]
[pause: 0.45]
C: It costs two runs per question, and statistics people must learn to trust.
[pause: 0.8]

[slide: v-106]
[pause: 0.6]
C: Mechanism five: quotas, priority and preemption.
[reveal: v-107]
[pause: 0.45]
C: It protects both liveness properties.
[reveal: v-108]
[pause: 0.45]
C: Gates run in a reserved, high-priority queue. Teams share a pool and borrow each other's idle quota. Exploratory jobs can be preempted, at stage boundaries.
[reveal: v-109]
[pause: 0.45]
C: It rules out the gate waiting behind exploration, and one team filling the cluster.
[reveal: v-110]
[pause: 0.45]
C: It costs redone work: up to one stage per preemption.
[pause: 0.8]

[slide: v-111]
[pause: 1.0]
C: Five ways to build it.
[reveal: v-112]
[pause: 0.45]
C: A, scripts on copied logs: nobody can rerun a result, and the copies cost more than the compute.
[reveal: v-113]
[pause: 0.45]
C: B, recompute everything every time: trustworthy, a thousand G-P-Us per gate.
[reveal: v-114]
[pause: 0.45]
C: C, reuse outputs by build name: cheap, until a changed dependency serves a stale hit.
[reveal: v-115]
[pause: 0.45]
C: D, shadowing in production only: there's no counterfactual before the release.
[reveal: v-116]
[pause: 0.45]
C: E, which I pick: pinned manifests, stages keyed by content, and a deterministic harness.
[reveal: v-117]
[pause: 0.45]
V: Pay for determinism once. It buys both caching and differences that mean something.
[pause: 1.0]

[slide: v-118]
[pause: 1.0]
C: Where each one lives. I'll draw the system once, in the design chapter; these labels come back on it at the end.
[reveal: v-119]
[pause: 0.45]
C: M-one, the manifest: in the run A-P-I, the planner, and the log store whose chunks are named by hash.
[reveal: v-120]
[pause: 0.45]
C: M-two, simulated time: in the sim workers.
[reveal: v-121]
[pause: 0.45]
C: M-three, memoisation: in the planner and the artifact cache.
[reveal: v-122]
[pause: 0.45]
C: M-four, the paired policy: in the gate service.
[reveal: v-123]
[pause: 0.45]
C: M-five, quotas: in the scheduler.
[pause: 1.0]

[slide: v-124]
[pause: 1.3]
C: Mechanism three at protocol level.
[reveal: v-125]
[pause: 0.45]
C: The planner computes the perception key: a hash of the perception image digest, the chunk hashes and the parameters.
[reveal: v-126]
[pause: 0.45]
C: Then the planning key, which includes the perception key, the map version and the seed. That's the chain.
[reveal: v-127]
[pause: 0.45]
C: It asks the cache index for both.
[reveal: v-128]
[pause: 0.45]
C: Perception hits; planning misses, because only planning changed.
[reveal: v-129]
[pause: 0.45]
C: So only planning runs, reading perception's cached output.
[reveal: v-130]
[pause: 0.45]
C: And the worker writes the blob first, then the index row. A reader that finds the row always finds a complete blob.
[pause: 1.1]

[slide: v-131]
[pause: 1.0]
C: The failure catalogue, which becomes the challenges.
[reveal: v-132]
[pause: 0.45]
C: One: the same build gives two different results.
[reveal: v-133]
[pause: 0.45]
C: Two: perception changes; what must be recomputed?
[reveal: v-134]
[pause: 0.45]
C: Three: release day, the gate against three thousand engineers.
[reveal: v-135]
[pause: 0.45]
C: Four: the new planner acts differently, and the logged world doesn't react.
[reveal: v-136]
[pause: 0.45]
C: Five: a small change in a safety metric. Block?
[reveal: v-137]
[pause: 0.45]
C: Six: the gate passes, and the field regresses.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-138]
[pause: 1.2]
C: The A-P-I next, then the data. Every endpoint is tagged with the requirement it serves.
[pause: 1.8]

[slide: v-139]
[pause: 1.0]
C: Starting a run, for F-R-two. A run is a build, given as image digests rather than tags, a scenario set with its version, and a seed. Nothing is implicit: there is no latest.
C: The answer is a run I-D and a manifest I-D, and how much of the run the cache already had: seventy-one percent here.
[pause: 1.0]

[slide: v-140]
[pause: 1.0]
C: Three more.
[reveal: v-141]
[pause: 0.45]
C: Sets, for F-R-one: a query and a name, and back comes a versioned set with its chunk hashes. A version never changes.
[reveal: v-142]
[pause: 0.45]
C: Reproduce, for F-R-three: a run from an existing manifest. Verify equals true re-executes instead of trusting the cache.
[reveal: v-143]
[pause: 0.45]
C: And gates, for F-R-four: a build in, a verdict out, with its reasons and the policy version.
[pause: 1.0]

[slide: v-144]
[pause: 1.0]
C: The manifest in full, because it is the core object of this design. The scenario set and its version. The hash of the list of nine thousand two hundred log chunks. Every image by digest. Every model's weights by hash. The map version and the agent models. The seed, and the mode: deterministic or fast.
C: Nothing in it is a name that can move. Given this record and the stored blobs, anyone can rerun the run, next week or next year, and get the same answer. And because it's immutable, a manifest I-D is a fine thing to put in an incident report.
[pause: 1.0]

[slide: v-145]
[pause: 1.3]
C: The conceptual model, a piece at a time.
[reveal: v-146]
[pause: 0.45]
C: A scenario set lists scenarios, many to many.
[reveal: v-147]
[pause: 0.45]
C: A scenario spans log chunks, named by their hash.
[reveal: v-148]
[pause: 0.45]
C: A run replays scenarios.
[reveal: v-149]
[pause: 0.45]
C: Every run is pinned by exactly one manifest; a manifest can pin many runs.
[reveal: v-150]
[pause: 0.45]
C: A run produces artifacts, each under its key.
[reveal: v-151]
[pause: 0.45]
C: And a gate decision compares two runs: the candidate and the baseline.
[pause: 1.1]

[slide: v-152]
[pause: 1.3]
C: The physical tables.
[reveal: v-153]
[pause: 0.45]
C: The manifest: image digests, model hashes, map version, seed. Immutable once written.
[reveal: v-154]
[pause: 0.45]
C: The run points to its manifest.
[reveal: v-155]
[pause: 0.45]
C: The artifact index, in Bigtable: key to blob, producer and size. The blob is written first.
[reveal: v-156]
[pause: 0.45]
C: Metrics in ClickHouse: run, scenario, name, value. Six billion rows a month.
[reveal: v-157]
[pause: 0.45]
C: Gate decisions: candidate, baseline, policy version and verdict. Append only.
[reveal: v-158]
[pause: 0.45]
C: And scenario sets: a name and version, and a list that never changes.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-159]
[pause: 1.2]
C: The design in three versions, each answering the objection to the one before, on one picture that only changes by deltas.
[pause: 1.8]

[slide: v-160]
[pause: 1.3]
C: Version one, the simplest thing that is reproducible, in the order a run travels.
[reveal: v-161]
[pause: 0.45]
C: Log ingest delivers chunks.
[reveal: v-162]
[pause: 0.45]
C: Into a log store, immutable, named by hash.
[reveal: v-163]
[pause: 0.45]
C: An engineer asks for a run.
[reveal: v-164]
[pause: 0.45]
C: The run A-P-I writes a manifest.
[reveal: v-165]
[pause: 0.45]
C: It resolves the scenario set from the catalog.
[reveal: v-166]
[pause: 0.45]
C: It sends every stage of every scenario to a batch scheduler.
[reveal: v-167]
[pause: 0.45]
C: Sim workers fetch chunks by byte range and replay them in a deterministic harness.
[reveal: v-168]
[pause: 0.45]
C: Metrics land in a results store. The objection: every build recomputes everything, a thousand G-P-Us per gate.
[pause: 1.1]

[slide: v-169]
[pause: 1.3]
C: Version two answers that.
[reveal: v-170]
[pause: 0.45]
C: Version one, carried.
[reveal: v-171]
[pause: 0.45]
C: New, a DAG planner: it turns a run into stages, computes a content key per stage, and sends only the misses.
[reveal: v-172]
[pause: 0.45]
C: New, an artifact cache: outputs by key, a blob store with an index. Workers read hits and write misses. The objection: who decides that a difference blocks a release, and against what?
[pause: 1.1]

[slide: v-173]
[pause: 1.3]
C: Version three answers that.
[reveal: v-174]
[pause: 0.45]
C: Version two, carried.
[reveal: v-175]
[pause: 0.45]
C: New, the release pipeline, which asks for a verdict.
[reveal: v-176]
[pause: 0.45]
C: New, the gate service: it submits the gate set, pairs the candidate's results with the last release's, applies a versioned policy, and answers pass or block. This is the baseline.
[pause: 1.1]

[slide: v-177]
[pause: 1.0]
C: The containers, one line each.
[reveal: v-178]
[pause: 0.45]
C: The log store: immutable chunks named by hash. Twenty petabytes.
[reveal: v-179]
[pause: 0.45]
C: The catalog: versioned sets, manifests and decisions. Small and transactional.
[reveal: v-180]
[pause: 0.45]
C: The run A-P-I and planner: manifests, stage keys, lookups, and only the misses go on.
[reveal: v-181]
[pause: 0.45]
C: The artifact cache: outputs by key, a hundred terabytes.
[reveal: v-182]
[pause: 0.45]
C: The scheduler: quotas, priority and preemption, around a thousand G-P-Us on gate day.
[reveal: v-183]
[pause: 0.45]
C: The sim workers: the deterministic harness, reading seventeen gigabytes a second at a gate.
[reveal: v-184]
[pause: 0.45]
C: And results with the gate: metrics, pairs and verdicts. Nothing on the run path waits for a person.
[pause: 1.0]

[slide: v-185]
[pause: 1.3]
C: A run, numbered.
[reveal: v-186]
[pause: 0.45]
C: One: the engineer submits build and set.
[reveal: v-187]
[pause: 0.45]
C: Two: the A-P-I writes the manifest and hands it to the planner.
[reveal: v-188]
[pause: 0.45]
C: Three: the planner resolves the set version from the catalog.
[reveal: v-189]
[pause: 0.45]
C: Four: it looks up every stage key in the cache.
[reveal: v-190]
[pause: 0.45]
C: Five: only the misses go to the scheduler.
[reveal: v-191]
[pause: 0.45]
C: Six: pods start on the workers.
[reveal: v-192]
[pause: 0.45]
C: Seven: workers read chunks by byte range.
[reveal: v-193]
[pause: 0.45]
C: Eight: metrics land in the results store.
[pause: 1.1]

[slide: v-194]
[pause: 1.3]
C: A gate, numbered.
[reveal: v-195]
[pause: 0.45]
C: One: the release pipeline asks about a build.
[reveal: v-196]
[pause: 0.45]
C: Two: the gate submits the gate set.
[reveal: v-197]
[pause: 0.45]
C: Three: the A-P-I hands it to the planner.
[reveal: v-198]
[pause: 0.45]
C: Four: misses go to the scheduler, in the reserved queue.
[reveal: v-199]
[pause: 0.45]
C: Five: workers run them.
[reveal: v-200]
[pause: 0.45]
C: Six: metrics land.
[reveal: v-201]
[pause: 0.45]
C: Seven: the gate pairs them with the last release.
[reveal: v-202]
[pause: 0.45]
C: Eight: pass or block, back to the pipeline.
[pause: 1.1]

[slide: v-203]
[pause: 1.3]
C: Find, as a sequence.
[reveal: v-204]
[pause: 0.45]
C: An engineer asks for unprotected left turns in rain.
[reveal: v-205]
[pause: 0.45]
C: The catalog is queried by tags and chunk ranges.
[reveal: v-206]
[pause: 0.45]
C: Eighteen hundred and forty scenarios.
[reveal: v-207]
[pause: 0.45]
C: Saved as left-rain, version one.
[reveal: v-208]
[pause: 0.45]
C: Which is a list of chunk hashes. It will mean the same thing in a year.
[pause: 1.1]

[slide: v-209]
[pause: 1.3]
C: Run, as a sequence.
[reveal: v-210]
[pause: 0.45]
C: Build seven-f-three on left-rain version one.
[reveal: v-211]
[pause: 0.45]
C: The planner writes the manifest: digests, set version, seeds.
[reveal: v-212]
[pause: 0.45]
C: It looks up three stage keys per scenario.
[reveal: v-213]
[pause: 0.45]
C: Perception all hit; planning all miss.
[reveal: v-214]
[pause: 0.45]
C: Eighteen hundred and forty planning jobs go to the scheduler.
[reveal: v-215]
[pause: 0.45]
C: Pods start within the team's quota.
[reveal: v-216]
[pause: 0.45]
C: Metrics land as run ninety-nine twenty-one.
[pause: 1.1]

[slide: v-217]
[pause: 1.3]
C: Reproduce, as a sequence.
[reveal: v-218]
[pause: 0.45]
C: An engineer reproduces run forty-four ten, from an incident in March.
[reveal: v-219]
[pause: 0.45]
C: The planner loads its manifest. Same inputs, so the same keys.
[reveal: v-220]
[pause: 0.45]
C: It looks them up.
[reveal: v-221]
[pause: 0.45]
C: All hit: identical outputs, in seconds.
[reveal: v-222]
[pause: 0.45]
C: To be sure, verify re-executes without the cache.
[reveal: v-223]
[pause: 0.45]
C: And the output hashes equal March's. That's S-one, checked.
[pause: 1.1]

[slide: v-224]
[pause: 1.3]
C: The gate, as a sequence.
[reveal: v-225]
[pause: 0.45]
C: The pipeline asks about build seven-f-three.
[reveal: v-226]
[pause: 0.45]
C: The gate runs gate-set version fifty-seven on it.
[reveal: v-227]
[pause: 0.45]
C: Fifty thousand scenarios; seventy percent of stages hit.
[reveal: v-228]
[pause: 0.45]
C: Metrics land as run ninety-nine thirty.
[reveal: v-229]
[pause: 0.45]
C: The gate pairs it with the released run, ninety-eight eleven.
[reveal: v-230]
[pause: 0.45]
C: Intervals per metric, under policy fourteen.
[reveal: v-231]
[pause: 0.45]
C: Block: the hard-braking rate is up four tenths of a percent, and the interval excludes zero.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-232]
[pause: 1.2]
C: One level down: the same picture with what each box runs on, the three containers the challenges open, and for each choice what I rejected.
[pause: 1.8]

[slide: v-233]
[pause: 1.3]
C: The same container view; only the type lines changed.
[reveal: v-234]
[pause: 0.45]
C: The log store: MCAP files on Google Cloud Storage, one-minute chunks, hashed.
[reveal: v-235]
[pause: 0.45]
C: The catalog: PostgreSQL.
[reveal: v-236]
[pause: 0.45]
C: The planner: a Go service.
[reveal: v-237]
[pause: 0.45]
C: The artifact cache: blobs on G-C-S with a Bigtable index.
[reveal: v-238]
[pause: 0.45]
C: The scheduler: Kubernetes with Kueue.
[reveal: v-239]
[pause: 0.45]
C: The workers: G-P-U and C-P-U pods running the harness.
[reveal: v-240]
[pause: 0.45]
C: Results: ClickHouse.
[reveal: v-241]
[pause: 0.45]
C: And the gate: a Go service, with its policy as code.
[pause: 1.1]

[slide: v-242]
[pause: 1.3]
C: Inside a sim worker.
[reveal: v-243]
[pause: 0.45]
C: The log store.
[reveal: v-244]
[pause: 0.45]
C: The chunk fetcher reads byte ranges and checks each chunk's hash.
[reveal: v-245]
[pause: 0.45]
C: The sim clock and bus: one clock, and delivery in order of time, topic and sequence.
[reveal: v-246]
[pause: 0.45]
C: Agent models, for road users that react.
[reveal: v-247]
[pause: 0.45]
C: The stage runner runs pinned images in a sandbox.
[reveal: v-248]
[pause: 0.45]
C: Before each stage, the cache client asks for the key; after it, it writes the output.
[reveal: v-249]
[pause: 0.45]
C: Into the artifact cache.
[reveal: v-250]
[pause: 0.45]
C: The metric extractor, per scenario.
[reveal: v-251]
[pause: 0.45]
C: The result writer, with the manifest attached.
[reveal: v-252]
[pause: 0.45]
C: Into the results store. Challenges one and four happen in this picture.
[pause: 1.1]

[slide: v-253]
[pause: 1.3]
C: Inside the planner.
[reveal: v-254]
[pause: 0.45]
C: A run request arrives.
[reveal: v-255]
[pause: 0.45]
C: The manifest builder pins the set version from the catalog, and every digest.
[reveal: v-256]
[pause: 0.45]
C: The stage graph comes from the build, with images resolved by digest.
[reveal: v-257]
[pause: 0.45]
C: The key hasher chains stage keys.
[reveal: v-258]
[pause: 0.45]
C: The index lookup, batched per scenario, against the cache index.
[reveal: v-259]
[pause: 0.45]
C: The job emitter sends only the misses.
[reveal: v-260]
[pause: 0.45]
C: To the scheduler. Challenge two lives here.
[pause: 1.1]

[slide: v-261]
[pause: 1.3]
C: Inside the gate.
[reveal: v-262]
[pause: 0.45]
C: The release pipeline asks.
[reveal: v-263]
[pause: 0.45]
C: A gate request: build and set version.
[reveal: v-264]
[pause: 0.45]
C: The baseline resolver finds the last released run on the same set.
[reveal: v-265]
[pause: 0.45]
C: The paired differ reads both runs' metrics per scenario.
[reveal: v-266]
[pause: 0.45]
C: A flake list removes scenarios that disagree with themselves.
[reveal: v-267]
[pause: 0.45]
C: Statistics: an interval per metric, not a point.
[reveal: v-268]
[pause: 0.45]
C: The policy evaluator applies versioned rules from a reviewed repository.
[reveal: v-269]
[pause: 0.45]
C: And every decision is recorded. Challenge five lives here.
[pause: 1.1]

[slide: v-270]
[pause: 1.0]
C: Logs are cut into one-minute MCAP chunks with a per-topic index, each named by its SHA-256. Workers read by byte range and verify the hash.
[reveal: v-271]
[pause: 0.45]
C: Why: Hashed chunks make a manifest a list of hashes.
[reveal: v-272]
[pause: 0.45]
C: Rejected: HDFS or a shared file system. Another 20 PB system to run, and a copy per job.
[reveal: v-273]
[pause: 0.45]
C: Logs in a database. Frames are blobs.
[pause: 1.0]

[slide: v-274]
[pause: 1.0]
C: Key = SHA-256(image digest, params, seed, mode, input keys). The blob is written first, then the index row, so a row always finds a whole blob.
[reveal: v-275]
[pause: 0.45]
C: Why: A key that hashes everything a stage read hits only when recomputing would give the same output.
[reveal: v-276]
[pause: 0.45]
C: Rejected: Redis. 100 TB does not belong in memory, and silent eviction loses cited results.
[reveal: v-277]
[pause: 0.45]
C: A Bazel remote cache. A near-equal for build actions.
[pause: 1.0]

[slide: v-278]
[pause: 1.0]
C: Gates run in a reserved, top-priority queue; teams share a cohort and borrow idle quota. Exploratory jobs are preemptible at stage boundaries.
[reveal: v-279]
[pause: 0.45]
C: Why: Admission by quota with borrowing, priority and preemption, on the cluster we already run.
[reveal: v-280]
[pause: 0.45]
C: Rejected: One FIFO queue. The gate waits behind exploration.
[reveal: v-281]
[pause: 0.45]
C: Slurm. Strong at fair share.
[pause: 1.0]

[slide: v-282]
[pause: 1.0]
C: metric(run, scenario, name, value) in ClickHouse, ordered by (scenario, name, run). Manifests, sets and verdicts in PostgreSQL, immutable once written.
[reveal: v-283]
[pause: 0.45]
C: Why: Six billion metric rows a month are scanned by column.
[reveal: v-284]
[pause: 0.45]
C: Rejected: PostgreSQL for metrics. Six billion narrow rows a month.
[reveal: v-285]
[pause: 0.45]
C: Elasticsearch. Search over text, not paired numbers across 50,000 scenarios.
[pause: 1.0]

[slide: v-286]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-287]
[pause: 0.45]
C: Log store: MCAP chunks on GCS. Not HDFS, a database. Immutable, hashed, read by range.
[reveal: v-288]
[pause: 0.45]
C: Artifact cache: CAS on GCS + Bigtable. Not Redis, Bazel cache. Key = hash of everything read.
[reveal: v-289]
[pause: 0.45]
C: Scheduler: Kubernetes + Kueue. Not FIFO queue, Slurm. Quota, borrowing, preemption.
[reveal: v-290]
[pause: 0.45]
C: Results, catalog: ClickHouse; PostgreSQL. Not Postgres for metrics, Elasticsearch. Columns for metrics, rows for manifests.
[reveal: v-291]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-292]
[pause: 1.2]
C: Before I break it: at a smaller scale, a much simpler design is right, and I should say where the line is.
[pause: 1.8]

[slide: v-293]
[pause: 1.3]
C: The alternate path, on version two.
[reveal: v-294]
[pause: 0.45]
C: The planner goes away.
[reveal: v-295]
[pause: 0.45]
C: And the cache.
[reveal: v-296]
[pause: 0.45]
C: Instead, a nightly job runs every scenario on the release branch, in the same deterministic harness, and compares with last night by fixed rules.
[reveal: v-297]
[pause: 0.45]
C: What it gives up: cost grows with builds times scenarios, engineers wait a night for an answer, and nothing is reused.
[pause: 1.1]

[slide: v-298]
[pause: 0.7]
C: Where is the line? A thousand scenarios is eighty-three G-P-U-hours: twenty-one G-P-Us for four hours, easy. Fifty thousand is a thousand and forty.
V: Below about five thousand scenarios, about a hundred G-P-Us, I'd ship the nightly recompute, and say when I'd switch. The determinism I'd build anyway: the cache needs it later.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-299]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-300]
[pause: 1.3]
C: Version three, with the places it breaks marked one at a time.
[reveal: v-301]
[pause: 0.45]
C: The sim workers: the same build giving two answers, and a logged world that doesn't react. Challenges one and four.
[reveal: v-302]
[pause: 0.45]
C: The planner: what a change must recompute. Challenge two.
[reveal: v-303]
[pause: 0.45]
C: The scheduler: release day against three thousand engineers. Challenge three.
[reveal: v-304]
[pause: 0.45]
C: And the gate: when a small change should block, and how we'd know the gate itself is wrong. Challenges five and six.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-305]
[pause: 1.2]
C: Six challenges, each the same way: the question, the naive answer, a case, where it breaks inside the container, the fix one level down, the push on the fix, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Same build, two answers

[slide: v-306]
[pause: 1.2]
N: Challenge one is the crux. Everything else in this design assumes it is solved.
[pause: 1.8]

[slide: v-307]
[pause: 0.6]
I: The same build on the same scenario gives two different results on two runs. Where do you look, and what do you change?
[pause: 2.0]

[slide: v-308]
[pause: 1.3]
C: Three components of the sim worker.
[reveal: v-309]
[pause: 0.45]
C: The bus is marked.
[reveal: v-310]
[pause: 0.45]
C: And the stage runner.
[reveal: v-311]
[pause: 0.45]
C: The naive answer: set the random seed.
[reveal: v-312]
[pause: 0.45]
C: The seed was set. The bus delivered messages in whatever order threads finished, the stage read the wall clock, and a G-P-U reduction used atomic adds, so floating-point sums came out in a different order.
[pause: 1.1]

[slide: v-313]
[pause: 1.0]
C: The trace.
[reveal: v-314]
[pause: 0.45]
C: Run A: no hard brake.
[reveal: v-315]
[pause: 0.45]
C: Run B, same manifest: one hard brake.
[reveal: v-316]
[pause: 0.45]
C: Comparing message hashes step by step, the first difference is message forty-one thousand two hundred and seven: the tracker's output.
[reveal: v-317]
[pause: 0.45]
C: A lidar message and a camera message had the same timestamp, and were delivered in whichever order the threads finished.
[reveal: v-318]
[pause: 0.45]
C: And the tracker's G-P-U reduction sums in a different order each time.
[reveal: v-319]
[pause: 0.45]
C: If a build disagrees with itself, a difference between two builds means nothing, and every cache hit is suspect.
[pause: 1.0]

[slide: v-320]
[pause: 1.3]
C: The fix, on the same components.
[reveal: v-321]
[pause: 0.45]
C: The bus.
[reveal: v-322]
[pause: 0.45]
C: And the stage runner.
[reveal: v-323]
[pause: 0.45]
C: One level down. One simulated clock. Messages delivered in order of time, then topic, then sequence number, so equal timestamps always break the same way. Seeds derived from the manifest per scenario and stage. G-P-U libraries in their deterministic mode, without atomic adds. And no wall clock inside the sandbox: the call fails.
[reveal: v-324]
[pause: 0.45]
C: It covers every source of difference we control. Not a G-P-U kernel with no deterministic mode. Those stages get a declared tolerance per metric, and the gate knows it.
[reveal: v-325]
[pause: 0.45]
C: Rejected: a fixed random seed. It removes one source of difference; threads, G-P-U atomics and the wall clock still reorder the work.
[pause: 1.1]

[slide: v-326]
[pause: 1.3]
C: And how we find these, as a sequence.
[reveal: v-327]
[pause: 0.45]
C: The auditor runs a manifest once.
[reveal: v-328]
[pause: 0.45]
C: And again, on another node.
[reveal: v-329]
[pause: 0.45]
C: Both report a hash per message, step by step.
[reveal: v-330]
[pause: 0.45]
C: The other run, too.
[reveal: v-331]
[pause: 0.45]
C: The first different message says where: forty-one thousand two hundred and seven, the tracker.
[reveal: v-332]
[pause: 0.45]
C: And from there to the cause: the G-P-U reduction. A bisection, not a guess.
[pause: 1.1]

[slide: v-333]
[pause: 0.6]
I: Deterministic G-P-U kernels are thirty percent slower. Do you pay that everywhere?
[pause: 1.5]

[slide: v-334]
[pause: 0.6]
C: Gate and reproduction runs: deterministic mode, always. Those are the runs whose differences become decisions.
[reveal: v-335]
[pause: 0.45]
C: Exploration can use the fast mode, with a declared tolerance. The mode is part of the cache key, so a fast output can never satisfy a gate.
[reveal: v-336]
[pause: 0.45]
C: And the honest limit: one percent of runs are run twice. A scenario that disagrees with itself is quarantined, not trusted.
[pause: 0.8]

[slide: v-337]
[pause: 0.7]
V: If asked, I'd say: a replay is only useful if a build agrees with itself. The harness owns the clock, the message order and the seeds, and G-P-U stages run in deterministic mode for gates. I find what I missed by running a sample twice and comparing message hashes, down to the first difference.
[pause: 1.0]
N: That fix creates the next question: if a run is a pure function, you can reuse its outputs. Which ones?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: A perception change

[slide: v-338]
[pause: 1.2]
N: Challenge two: reuse. The cache is where the money is, and where a wrong answer hides.
[pause: 1.8]

[slide: v-339]
[pause: 0.6]
I: A perception change lands. How much of the fifty-thousand-scenario gate do you recompute?
[pause: 2.0]

[slide: v-340]
[pause: 1.3]
C: Inside the planner.
[reveal: v-341]
[pause: 0.45]
C: The key hasher is marked.
[reveal: v-342]
[pause: 0.45]
C: The naive answer: cache by build number.
[reveal: v-343]
[pause: 0.45]
C: Then a new build recomputes everything, even stages that didn't change. Or, keyed by stage name, a stage whose library changed under the same name gets a stale hit.
[pause: 1.1]

[slide: v-344]
[pause: 1.0]
C: The trace.
[reveal: v-345]
[pause: 0.45]
C: Monday, build four twelve changes the tracker inside perception. Planning is untouched.
[reveal: v-346]
[pause: 0.45]
C: Keyed by build: everything is recomputed. A thousand and forty G-P-Us, and the gate takes nine hours.
[reveal: v-347]
[pause: 0.45]
C: Keyed by stage name: planning reuses outputs from build four eleven.
[reveal: v-348]
[pause: 0.45]
C: Which were computed on four eleven's tracks. Planning's results are about the wrong input.
[reveal: v-349]
[pause: 0.45]
C: A key must say exactly what went into an output, not who built it.
[pause: 1.0]

[slide: v-350]
[pause: 1.3]
C: The fix, in the same place.
[reveal: v-351]
[pause: 0.45]
C: The key hasher.
[reveal: v-352]
[pause: 0.45]
C: One level down. A stage's key is the hash of its image digest, parameters, seed, mode, and the keys of its inputs. Change perception: its key changes, and so does every key downstream of it, and nothing else. For build four twelve, perception and planning rerun; the scenario loader and the map stage hit.
[reveal: v-353]
[pause: 0.45]
C: It covers every input the stage declares. Not one it reads without declaring, like an environment variable. That's why stages run in a hermetic sandbox, where only the manifest's inputs exist.
[reveal: v-354]
[pause: 0.45]
C: Rejected: caching by build number. A new build invalidates every stage, and keyed by name, a changed dependency serves a stale hit.
[pause: 1.1]

[slide: v-355]
[pause: 1.0]
C: As pseudocode, key lines marked. Lines one and two: the key includes the keys of the inputs, which is what makes it a chain. Lines seven and eight: the blob is written first, under its own hash, and only then the index row. A crash between them leaves an orphan blob, never an index row pointing at half an output.
[pause: 1.0]

[slide: v-356]
[pause: 0.6]
I: A bad perception output got into the cache. How do you get it out, and how do you find what used it?
[pause: 1.5]

[slide: v-357]
[pause: 0.6]
C: Remove it by deleting the index row. The blob becomes unreachable. A key is never overwritten.
[reveal: v-358]
[pause: 0.45]
C: Find what used it: every row records its producer run, and every downstream key contains this key. Lineage is a query, not an investigation.
[reveal: v-359]
[pause: 0.45]
C: And prevent the next one: the auditor recomputes one percent of hits and compares them byte for byte. Challenge six.
[pause: 0.8]

[slide: v-360]
[pause: 0.7]
V: If asked, I'd say: each stage's output is keyed by a hash of its image, parameters, seed and the keys of its inputs, so a change recomputes exactly what depends on it, and nothing else. Stages run hermetically, so nothing they read is missing from the key, and the blob is written before the index row.
[pause: 1.0]
N: That fix creates the next question: when nothing hits, the gate needs a thousand G-P-Us. Who waits?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Release day

[slide: v-361]
[pause: 1.2]
N: Challenge three: capacity, shared with three thousand people who all have deadlines.
[pause: 1.8]

[slide: v-362]
[pause: 0.6]
I: It's release day. The gate needs a thousand G-P-Us, three thousand engineers are running, and training wants its share. What happens?
[pause: 2.0]

[slide: v-363]
[pause: 1.3]
C: The middle of the container view.
[reveal: v-364]
[pause: 0.45]
C: The scheduler is marked.
[reveal: v-365]
[pause: 0.45]
C: The naive answer: one queue, first come, first served.
[reveal: v-366]
[pause: 0.45]
C: Then the gate queues behind forty thousand exploratory jobs, and one team's parameter sweep can fill the whole pool.
[pause: 1.1]

[slide: v-367]
[pause: 1.0]
C: The trace.
[reveal: v-368]
[pause: 0.45]
C: At nine, a team submits a sweep of forty thousand jobs.
[reveal: v-369]
[pause: 0.45]
C: At ten, the release is cut and the gate submits its jobs.
[reveal: v-370]
[pause: 0.45]
C: Which wait behind the sweep.
[reveal: v-371]
[pause: 0.45]
C: The gate answers at twenty to seven. The release slips a day.
[reveal: v-372]
[pause: 0.45]
C: Both liveness promises, broken by a queue.
[pause: 1.0]

[slide: v-373]
[pause: 0.6]
C: The fix, one level down, in Kueue terms.
[reveal: v-374]
[pause: 0.45]
C: A reserved cluster queue for gates: four hundred G-P-Us, the highest priority, and it borrows the rest from the shared pool.
[reveal: v-375]
[pause: 0.45]
C: One queue per team, in a cohort, so idle quota is lent and reclaimed, and no team can take more than its share when others want theirs.
[reveal: v-376]
[pause: 0.45]
C: And exploratory jobs are preemptible, checkpointing at every stage boundary, which is natural here: a stage's output is already written to the cache. A preemption loses one stage at most.
[reveal: v-377]
[pause: 0.45]
C: It covers gate latency and fairness. It does not cover a gate that recomputes everything: that needs capacity or an earlier start.
[reveal: v-378]
[pause: 0.45]
C: Rejected: one FIFO queue. The gate waits behind exploration, and one team fills the cluster.
[pause: 0.8]

[slide: v-379]
[pause: 0.6]
I: Perception changed, so nothing hits. The gate really needs a thousand and forty G-P-Us for four hours.
[pause: 1.5]

[slide: v-380]
[pause: 0.6]
C: First, pre-warm. Every night, the gate set runs on the head of the release branch, so on cut day perception already hits.
[reveal: v-381]
[pause: 0.45]
C: Second, an agreement with training: it checkpoints and yields up to six hundred G-P-Us to a gate.
[reveal: v-382]
[pause: 0.45]
C: And the honest limit: a perception change landed on cut day itself takes about six hours. The release schedule says so in advance, which is cheaper than pretending.
[pause: 0.8]

[slide: v-383]
[pause: 0.7]
V: If asked, I'd say: gates run in a reserved, high-priority queue that borrows from a shared pool. Teams get quotas with borrowing, and exploratory jobs are preempted at stage boundaries, so a preemption costs one stage. And I pre-warm the cache nightly on the release branch, so cut day is mostly hits.
[pause: 1.0]
N: That fix creates the next question: the gate now answers on time. Is its answer about the right thing?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: The log does not react

[slide: v-384]
[pause: 1.2]
N: Challenge four is about what a replay can and cannot tell you.
[pause: 1.8]

[slide: v-385]
[pause: 0.6]
I: The new planner brakes earlier than the logged one. The replay now shows the car behind hitting us. Is that a regression?
[pause: 2.0]

[slide: v-386]
[pause: 1.3]
C: Inside the worker: the bus, the stage runner, the metric extractor.
[reveal: v-387]
[pause: 0.45]
C: The metric extractor is marked.
[reveal: v-388]
[pause: 0.45]
C: The naive answer: a collision is a collision, block it.
[reveal: v-389]
[pause: 0.45]
C: But the extractor scored the whole scenario, including the part after the logged world stopped being what would have happened.
[pause: 1.1]

[slide: v-390]
[pause: 1.3]
C: The picture. The logged ego braked at seven seconds. The new planner brakes at five point four. By six point two seconds the two positions differ by more than a metre: they have diverged.
C: The car behind is replayed as logged, so it keeps its speed and hits us. The real driver behind would have reacted to our brake lights. The collision is an artefact of open-loop replay, not of the planner. Score up to the divergence, or replace the follower with an agent that reacts.
[pause: 1.1]

[slide: v-391]
[pause: 1.3]
C: The fix, in the worker.
[reveal: v-392]
[pause: 0.45]
C: The agent models, which make the other road users react.
[pause: 1.1]

[slide: v-393]
[pause: 0.6]
C: One level down. Every simulated step, the harness measures how far the ego has diverged from the log, in position and heading. Metrics are scored up to the first divergence above one metre, and the scenario reports where that was. For scenario sets flagged as interactive, the other road users are agent models that react, so the scenario stays valid after divergence.
[reveal: v-394]
[pause: 0.45]
C: It covers false regressions caused by logged actors. It doesn't cover the agents' own mistakes: agent models are pinned in the manifest like any model, and validated on their own.
[reveal: v-395]
[pause: 0.45]
C: Rejected: frame-by-frame comparison with the log. After the ego diverges, the log no longer shows what the others would have done.
[pause: 0.8]

[slide: v-396]
[pause: 0.6]
I: Most of your safety-relevant scenarios diverge early. Truncating them leaves nothing to score.
[pause: 1.5]

[slide: v-397]
[pause: 0.6]
C: Safety-relevant scenario sets run closed loop by default. Truncation is for the rest.
[reveal: v-398]
[pause: 0.45]
C: The agents are scored too: an agent that never yields, or always does, fails its own validation before it's allowed into a gate set.
[reveal: v-399]
[pause: 0.45]
C: And the honest limit: closed loop answers what if, not what happened. A reactive agent is a model, so every result carries the agent's version.
[pause: 0.8]

[slide: v-400]
[pause: 0.7]
V: If asked, I'd say: open-loop replay is only valid until the new build acts differently. I measure divergence every step, score metrics up to it, and run safety-relevant scenarios closed loop with versioned agent models, so a collision with a logged car that would have braked isn't a regression.
[pause: 1.0]
N: That fix creates the next question: the metrics are now about the right thing. Which differences should block a release?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Block or pass?

[slide: v-401]
[pause: 1.2]
N: Challenge five: the decision. Who decides, on what evidence, and can you explain it next year?
[pause: 1.8]

[slide: v-402]
[pause: 0.6]
I: A candidate's hard-braking rate is up three tenths of a percent on the gate set. Does it ship?
[pause: 2.0]

[slide: v-403]
[pause: 1.3]
C: Inside the gate service.
[reveal: v-404]
[pause: 0.45]
C: The policy evaluator is marked.
[reveal: v-405]
[pause: 0.45]
C: The naive answer: compare with yesterday's run, and block above a fixed threshold.
[reveal: v-406]
[pause: 0.45]
C: That's one noisy number, against a baseline that moves every day, with a threshold nobody can defend.
[pause: 1.1]

[slide: v-407]
[pause: 1.0]
C: The trace.
[reveal: v-408]
[pause: 0.45]
C: Week one: three tenths up against yesterday, above a quarter-percent threshold. Block.
[reveal: v-409]
[pause: 0.45]
C: Rerun: one tenth. It was noise, and a day was lost.
[reveal: v-410]
[pause: 0.45]
C: Week two: two tenths up, under the threshold. Pass. But yesterday's run already carried two tenths.
[reveal: v-411]
[pause: 0.45]
C: So the release shipped four tenths up against the last release.
[reveal: v-412]
[pause: 0.45]
C: A false block and a false pass, both from the method, not the build.
[pause: 1.0]

[slide: v-413]
[pause: 1.3]
C: The fix, on the same components.
[reveal: v-414]
[pause: 0.45]
C: Statistics.
[reveal: v-415]
[pause: 0.45]
C: And the policy evaluator.
[reveal: v-416]
[pause: 0.45]
C: One level down. The baseline is the last released build on the same set version, never yesterday. For each scenario, candidate minus baseline, so scenario difficulty cancels. A bootstrap over scenarios gives an interval per metric. The policy says which metrics block and at what interval; it lives in a repository the safety team reviews, and every decision records its version.
[reveal: v-417]
[pause: 0.45]
C: It covers noise and a drifting baseline. Not a gate set that misses the situation that regresses. That's coverage, and challenge six.
[reveal: v-418]
[pause: 0.45]
C: Rejected: a fixed threshold against yesterday's run. Noise moves it, the baseline drifts, and nobody can say later why a build passed.
[pause: 1.1]

[slide: v-419]
[pause: 1.0]
C: As pseudocode, key lines marked. Line one: the baseline is the last release on the same set version. Line five: an interval from a bootstrap over the paired differences, without flaky scenarios. Line six: block only when the whole interval is past the limit. Line seven: every verdict is recorded with both runs and the policy version, so next year's question has an answer.
[pause: 1.0]

[slide: v-420]
[pause: 0.6]
I: The gate blocks, and the release manager wants to ship anyway.
[pause: 1.5]

[slide: v-421]
[pause: 0.6]
C: An override is allowed, and it's a decision too: an approver from the safety team, a reason, and an expiry, recorded with the verdict.
[reveal: v-422]
[pause: 0.45]
C: And every override is reviewed afterwards. Either the policy was wrong, and a new version fixes it, or the override was.
[pause: 0.8]

[slide: v-423]
[pause: 0.7]
V: If asked, I'd say: I compare the candidate with the last release on the same scenario-set version, scenario by scenario, and block on a bootstrap interval, not a point. The rules are versioned data owned by the safety team, and every verdict, and every override, is recorded with both runs and the policy version.
[pause: 1.0]
N: That fix creates the last question: how would you know the gate itself is wrong?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: The gate passed

[slide: v-424]
[pause: 1.2]
N: Challenge six is observability, and here the thing to observe is the gate itself.
[pause: 1.8]

[slide: v-425]
[pause: 0.6]
I: The gate passed a build, and the field regressed. How would you have known the gate was wrong?
[pause: 2.0]

[slide: v-426]
[pause: 1.3]
C: The release pipeline, the gate, the results.
[reveal: v-427]
[pause: 0.45]
C: The gate is marked.
[reveal: v-428]
[pause: 0.45]
C: The naive answer: pass rate, job success and queue time are all green.
[reveal: v-429]
[pause: 0.45]
C: They were. A poisoned cache entry made every run reuse old planning outputs, so candidate and baseline looked the same.
[pause: 1.1]

[slide: v-430]
[pause: 1.0]
C: The trace.
[reveal: v-431]
[pause: 0.45]
C: Tuesday, a stage starts reading a config file it never declared, so its key doesn't include it.
[reveal: v-432]
[pause: 0.45]
C: The config changes, and planning keeps hitting old outputs.
[reveal: v-433]
[pause: 0.45]
C: Friday the gate compares old planning with old planning, and passes.
[reveal: v-434]
[pause: 0.45]
C: The next week, the field sees the regression the gate never ran.
[reveal: v-435]
[pause: 0.45]
C: A healthy gate with a hundred percent pass rate is exactly what a broken gate looks like.
[pause: 1.0]

[slide: v-436]
[pause: 1.3]
C: The fix changes the design: version four. Version three, carried.
[reveal: v-437]
[pause: 0.45]
C: New: a gate auditor. It submits its own runs through the scheduler and reads the results store.
[pause: 1.1]

[slide: v-438]
[pause: 0.6]
C: One level down, four checks on the gate itself.
[reveal: v-439]
[pause: 0.45]
C: A known-bad build: every week the auditor submits a build with a planted regression, and the gate must block it. A gate that can't fail fails this.
[reveal: v-440]
[pause: 0.45]
C: Double runs: one percent of runs are run twice, and the agreement rate is a service level indicator.
[reveal: v-441]
[pause: 0.45]
C: A cache audit: one percent of hits are recomputed and compared byte for byte. That would have caught Tuesday's undeclared config by Wednesday.
[reveal: v-442]
[pause: 0.45]
C: Coverage: the situations in the gate set against what the fleet actually drives, per release.
[reveal: v-443]
[pause: 0.45]
C: Rejected: pass-rate dashboards. A gate that can't fail looks exactly like one that's passing.
[pause: 0.8]

[slide: v-444]
[pause: 1.0]
C: And read them in pairs.
[reveal: v-445]
[pause: 0.45]
C: A cache-audit mismatch while double runs agree: an input missing from a key. Our case.
[reveal: v-446]
[pause: 0.45]
C: Double runs disagreeing while the cache audit is clean: non-determinism in a stage.
[reveal: v-447]
[pause: 0.45]
C: A known-bad build passing: the gate can't fail. Stop releases until it can.
[reveal: v-448]
[pause: 0.45]
C: A hundred percent pass rate for weeks: check coverage before celebrating.
[reveal: v-449]
[pause: 0.45]
C: And gate time up with the hit rate down: a change upstream of most stages.
[pause: 1.0]

[slide: v-450]
[pause: 1.0]
C: And the gate's own service levels, so its health is a number, not a feeling.
[reveal: v-451]
[pause: 0.45]
C: Known-bad builds blocked: a hundred percent. One miss stops releases.
[reveal: v-452]
[pause: 0.45]
C: Double-run agreement: at least ninety-nine point nine percent of scenarios.
[reveal: v-453]
[pause: 0.45]
C: Cache-audit mismatches: zero. One is an incident.
[reveal: v-454]
[pause: 0.45]
C: Gates answered within four hours: ninety-five percent.
[reveal: v-455]
[pause: 0.45]
C: And the cache hit rate, around seventy percent, watched for sudden drops, which usually mean a change upstream of most stages.
[pause: 1.0]

[slide: v-456]
[pause: 0.7]
V: If asked, I'd say: I'd make the gate prove it can fail. A planted regression every week that it must block, one percent of runs done twice, one percent of cache hits recomputed, and coverage against what the fleet drives. A gate with a perfect pass rate is a symptom until those say otherwise.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-457]
[pause: 1.2]
C: The recap: one picture, the mechanisms on it, and the mistakes that cost most.
[pause: 1.8]

[slide: v-458]
[pause: 1.3]
C: Version four, the final design: version one's picture with three boxes more. The labels from the theory chapter come back.
[reveal: v-459]
[pause: 0.45]
C: The log store: chunks named by hash, the base of every manifest.
[reveal: v-460]
[pause: 0.45]
C: The planner: manifests and Merkle keys.
[reveal: v-461]
[pause: 0.45]
C: The artifact cache: outputs by content.
[reveal: v-462]
[pause: 0.45]
C: The scheduler: a reserved gate queue, quotas and preemption.
[reveal: v-463]
[pause: 0.45]
C: The workers: the harness that owns time and order.
[reveal: v-464]
[pause: 0.45]
C: The gate: paired intervals under a versioned policy.
[reveal: v-465]
[pause: 0.45]
C: And the auditor: the gate's own canaries.
[pause: 1.1]

[slide: v-466]
[pause: 1.0]
N: The mistakes that cost most in this round.
[reveal: v-467]
[pause: 0.45]
N: Set the seed as the whole answer to determinism. Instead, the harness owns the clock, the order and the arithmetic.
[reveal: v-468]
[pause: 0.45]
N: Caching by build or name. Instead, keys that hash every input, and hermetic stages.
[reveal: v-469]
[pause: 0.45]
N: One queue for everything. Instead, a reserved gate queue, quotas and preemption.
[reveal: v-470]
[pause: 0.45]
N: Scoring open-loop replays after divergence. Instead, score up to it, with reactive agents where it matters.
[reveal: v-471]
[pause: 0.45]
N: A threshold against yesterday. Instead, paired intervals against the last release, under versioned rules.
[reveal: v-472]
[pause: 0.45]
N: And trusting a gate that never fails. Instead, a planted regression it must block.
[pause: 1.0]

[slide: v-473]
[pause: 0.7]
V: Make every run a pure function of a pinned manifest. Then outputs can be reused by content, differences mean the build changed, and a gate can be trusted, once it has proved it can fail.
[pause: 1.0]
C: Thanks for watching. The written design, with the internals of each tool, is linked below.
[pause: 1.6]
