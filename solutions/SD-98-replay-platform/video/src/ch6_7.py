from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

chapter(6, "Bridge", 5, "It works. Where does it break first?", [
 "V: It works. The question now is where it breaks first.", "[pause: 1.0]"])

S(dia("Challenge map", "Six challenges, four places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version three, with the places it breaks marked one at a time.", P,
 "C: The sim workers: the same build giving two answers, and a logged world that doesn't react. Challenges one and four.", P,
 "C: The planner: what a change must recompute. Challenge two.", P,
 "C: The scheduler: release day against three thousand engineers. Challenge three.", P,
 "C: And the gate: when a small change should block, and how we'd know the gate itself is wrong. Challenges five and six."], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", [
 "C: Six challenges, each the same way: the question, the naive answer, a case, where it breaks inside the container, the fix one level down, the push on the fix, and what I'd say in the room."])

# ───────── Challenge 1 · two answers ─────────
subchapter("7.1", "Challenge 1: Same build, two answers", ["N: Challenge one is the crux. Everything else in this design assumes it is solved."])
qs("Interviewer · challenge 1 of 6", "“The same build on the same scenario gives two different results on two runs. Where do you look, and what do you change?”", [
 "I: The same build on the same scenario gives two different results on two runs. Where do you look, and what do you change?", "[pause: 2.0]"])

S(dia(K(1, "two answers"), "Where does a run pick up randomness?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Set the random seed.”"),
                  ("case", "Break", "The bus delivers in thread order; the stage reads the wall clock and reduces on the GPU with atomics."))), [
 P, "C: Three components of the sim worker.", P, "C: The bus is marked.", P, "C: And the stage runner.", P,
 "C: The naive answer: set the random seed.", P,
 "C: The seed was set. The bus delivered messages in whatever order threads finished, the stage read the wall clock, and a G-P-U reduction used atomic adds, so floating-point sums came out in a different order."], cls="dia")

S(trace(K(1, "the trace"), "A hard brake that comes and goes", [
  ("run A", "scenario 18,204: hard brakes 0; min. gap 4.1 m"),
  ("run B", "same manifest: hard brakes 1; min. gap 3.9 m"),
  ("diff", "first different message: 41,207, the tracker's output"),
  ("cause", B("a lidar and a camera message with equal timestamps, delivered in thread order")),
  ("also", B("the tracker's GPU reduction sums in a different order each time"))],
  hedge=("Why it matters", "If one build disagrees with itself, a difference between two builds means nothing. Every cache hit is also suspect.")), [
 "C: The trace.", P, "C: Run A: no hard brake.", P, "C: Run B, same manifest: one hard brake.", P,
 "C: Comparing message hashes step by step, the first difference is message forty-one thousand two hundred and seven: the tracker's output.", P,
 "C: A lidar message and a camera message had the same timestamp, and were delivered in whichever order the threads finished.", P,
 "C: And the tracker's G-P-U reduction sums in a different order each time.", P,
 "C: If a build disagrees with itself, a difference between two builds means nothing, and every cache hit is suspect."])

S(dia(K(1, "the fix"), "The harness owns time, order and arithmetic", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "One sim clock; messages delivered by (time, topic, sequence); seeds per (scenario, stage) from the manifest; deterministic GPU kernels; no wall clock in the sandbox."),
                  ("whyb", "Covers, and does not", "Every source of difference we control. Not GPU kernels with no deterministic mode: those get a declared tolerance per metric.")) + rejl(*REJ(1))), [
 P, "C: The fix, on the same components.", P, "C: The bus.", P, "C: And the stage runner.", P,
 "C: One level down. One simulated clock. Messages delivered in order of time, then topic, then sequence number, so equal timestamps always break the same way. Seeds derived from the manifest per scenario and stage. G-P-U libraries in their deterministic mode, without atomic adds. And no wall clock inside the sandbox: the call fails.", P,
 "C: It covers every source of difference we control. Not a G-P-U kernel with no deterministic mode. Those stages get a declared tolerance per metric, and the gate knows it.", P,
 "C: Rejected: a fixed random seed. It removes one source of difference; threads, G-P-U atomics and the wall clock still reorder the work."], cls="dia")

S(dia(K(1, "how we find it"), "Run twice, compare message by message", "seq-ch1-double"), [
 "C: And how we find these, as a sequence.", P, "C: The auditor runs a manifest once.", P, "C: And again, on another node.", P,
 "C: Both report a hash per message, step by step.", P, "C: The other run, too.", P,
 "C: The first different message says where: forty-one thousand two hundred and seven, the tracker.", P,
 "C: And from there to the cause: the G-P-U reduction. A bisection, not a guess."], cls="dia")

qs("Interviewer · the second-level push", "“Deterministic GPU kernels are thirty percent slower. Do you pay that everywhere?”", [
 "I: Deterministic G-P-U kernels are thirty percent slower. Do you pay that everywhere?", "[pause: 1.5]"])

S(plain(K(1, "the second fix, and the honest limit"), "Pay where it is checked; measure the rest", cards(
  ("grn", "Gate and repro runs", "Deterministic mode, always: these are the runs whose differences are decisions."),
  ("amb", "Exploration", "Fast mode, with a declared tolerance; never cached for the gate, keyed with the mode."),
  ("red", "Honest limit", "1 % of runs are run twice; a scenario that disagrees with itself is quarantined, not trusted."), cols=3)), [
 P, "C: Gate and reproduction runs: deterministic mode, always. Those are the runs whose differences become decisions.", P,
 "C: Exploration can use the fast mode, with a declared tolerance. The mode is part of the cache key, so a fast output can never satisfy a gate.", P,
 "C: And the honest limit: one percent of runs are run twice. A scenario that disagrees with itself is quarantined, not trusted."])

say_slide("“A replay is only useful if a build agrees with itself. The harness owns the clock, the message order and the seeds, and GPU stages run in deterministic mode for gates. I find what I missed by running a sample twice and comparing message hashes until the first difference.”", [
 "V: If asked, I'd say: a replay is only useful if a build agrees with itself. The harness owns the clock, the message order and the seeds, and G-P-U stages run in deterministic mode for gates. I find what I missed by running a sample twice and comparing message hashes, down to the first difference.", "[pause: 1.0]",
 "N: That fix creates the next question: if a run is a pure function, you can reuse its outputs. Which ones?"])

# ───────── Challenge 2 · what to recompute ─────────
subchapter("7.2", "Challenge 2: A perception change", ["N: Challenge two: reuse. The cache is where the money is, and where a wrong answer hides."])
qs("Interviewer · challenge 2 of 6", "“A perception change lands. How much of the 50,000-scenario gate do you recompute?”", [
 "I: A perception change lands. How much of the fifty-thousand-scenario gate do you recompute?", "[pause: 2.0]"])

S(dia(K(2, "what to reuse"), "Which outputs are still valid?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Cache by build number: new build, new outputs.”"),
                  ("case", "Break", "The key hasher keys by build: everything is recomputed, or a changed dependency is missed."))), [
 P, "C: Inside the planner.", P, "C: The key hasher is marked.", P,
 "C: The naive answer: cache by build number.", P,
 "C: Then a new build recomputes everything, even stages that didn't change. Or, keyed by stage name, a stage whose library changed under the same name gets a stale hit."], cls="dia")

S(trace(K(2, "the trace"), "One change, two wrong answers", [
  ("Mon", "build 412 changes the tracker inside perception; planning untouched"),
  ("by build", B("all 50,000 × 3 stages recomputed: 1,040 GPUs, the gate takes 9 hours")),
  ("by stage name", "planning reuses outputs from build 411 …"),
  ("by stage name", B("… computed on 411's tracks: planning's results are about the wrong input"))],
  hedge=("What a key must say", "Not who built it, but exactly what went into it.")), [
 "C: The trace.", P, "C: Monday, build four twelve changes the tracker inside perception. Planning is untouched.", P,
 "C: Keyed by build: everything is recomputed. A thousand and forty G-P-Us, and the gate takes nine hours.", P,
 "C: Keyed by stage name: planning reuses outputs from build four eleven.", P,
 "C: Which were computed on four eleven's tracks. Planning's results are about the wrong input.", P,
 "C: A key must say exactly what went into an output, not who built it."])

S(dia(K(2, "the fix"), "A Merkle chain of stage keys", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "key(stage) = SHA-256(image digest, params, seed, mode, keys of its inputs). Perception changes → its key changes → every downstream key changes; nothing else does."),
                  ("whyb", "Covers, and does not", "Every input the stage declares. Not one it reads without declaring: hence the hermetic sandbox.")) + rejl(*REJ(2))), [
 P, "C: The fix, in the same place.", P, "C: The key hasher.", P,
 "C: One level down. A stage's key is the hash of its image digest, parameters, seed, mode, and the keys of its inputs. Change perception: its key changes, and so does every key downstream of it, and nothing else. For build four twelve, perception and planning rerun; the scenario loader and the map stage hit.", P,
 "C: It covers every input the stage declares. Not one it reads without declaring, like an environment variable. That's why stages run in a hermetic sandbox, where only the manifest's inputs exist.", P,
 "C: Rejected: caching by build number. A new build invalidates every stage, and keyed by name, a changed dependency serves a stale hit."], cls="dia")

S(plain(K(2, "the key, as pseudocode"), "Keys chain; the blob comes before the index",
  pseudo("key(s) = sha256(s.image_digest, s.params, s.seed,\n               s.mode, [key(i) for i in s.inputs])\n\nfor s in topo_order(stages):\n    if index.get(key(s)): continue    # a hit\n    out = run_hermetic(s, inputs=blobs(s.inputs))\n    blob = cas.put(sha256(out), out)  # 1: blob\n    index.put(key(s), blob, producer=run)  # 2: row", hl=(1, 2, 7, 8))), [
 "C: As pseudocode, key lines marked. Lines one and two: the key includes the keys of the inputs, which is what makes it a chain. Lines seven and eight: the blob is written first, under its own hash, and only then the index row. A crash between them leaves an orphan blob, never an index row pointing at half an output."])

qs("Interviewer · the second-level push", "“A bad perception output got into the cache. How do you get it out, and how do you find what used it?”", [
 "I: A bad perception output got into the cache. How do you get it out, and how do you find what used it?", "[pause: 1.5]"])

S(plain(K(2, "the second fix"), "Delete by key; follow the chain", cards(
  ("grn", "Remove it", "Delete the index row; the blob becomes unreachable. Never overwrite a key."),
  ("amb", "Find what used it", "Every index row records its producer run; downstream keys contain this key: a lineage query."),
  ("red", "Prevent it", "1 % of hits are re-computed by the auditor and compared byte for byte."), cols=3)), [
 P, "C: Remove it by deleting the index row. The blob becomes unreachable. A key is never overwritten.", P,
 "C: Find what used it: every row records its producer run, and every downstream key contains this key. Lineage is a query, not an investigation.", P,
 "C: And prevent the next one: the auditor recomputes one percent of hits and compares them byte for byte. Challenge six."])

say_slide("“Each stage's output is keyed by a hash of its image, parameters, seed and the keys of its inputs, so a change recomputes exactly what depends on it and nothing else. Stages run hermetically, so nothing they read is missing from the key, and the blob is written before the index row.”", [
 "V: If asked, I'd say: each stage's output is keyed by a hash of its image, parameters, seed and the keys of its inputs, so a change recomputes exactly what depends on it, and nothing else. Stages run hermetically, so nothing they read is missing from the key, and the blob is written before the index row.", "[pause: 1.0]",
 "N: That fix creates the next question: when nothing hits, the gate needs a thousand G-P-Us. Who waits?"])

# ───────── Challenge 3 · release day ─────────
subchapter("7.3", "Challenge 3: Release day", ["N: Challenge three: capacity, shared with three thousand people who all have deadlines."])
qs("Interviewer · challenge 3 of 6", "“It's release day. The gate needs a thousand GPUs, three thousand engineers are running, and training wants its share. What happens?”", [
 "I: It's release day. The gate needs a thousand G-P-Us, three thousand engineers are running, and training wants its share. What happens?", "[pause: 2.0]"])

S(dia(K(3, "a crowded day"), "Who gets the GPUs?", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“One queue, first come, first served.”"),
                  ("case", "Break", "The scheduler: the gate queues behind 40,000 exploratory jobs; one team's sweep fills the pool."))), [
 P, "C: The middle of the container view.", P, "C: The scheduler is marked.", P,
 "C: The naive answer: one queue, first come, first served.", P,
 "C: Then the gate queues behind forty thousand exploratory jobs, and one team's parameter sweep can fill the whole pool."], cls="dia")

S(trace(K(3, "the trace"), "A gate that misses its window", [
  ("09:00", "a team submits a sweep: 40,000 jobs"),
  ("10:00", "the release is cut; the gate submits 50,000 × 2 stages"),
  ("10:00 – 15:30", B("the gate's jobs wait behind the sweep")),
  ("18:40", B("the gate answers 8 h 40 min after the cut; the release slips a day"))],
  hedge=("Two promises, both broken", "L1: the gate in 4 hours. L2: nobody starves. FIFO keeps neither.")), [
 "C: The trace.", P, "C: At nine, a team submits a sweep of forty thousand jobs.", P,
 "C: At ten, the release is cut and the gate submits its jobs.", P, "C: Which wait behind the sweep.", P,
 "C: The gate answers at twenty to seven. The release slips a day.", P,
 "C: Both liveness promises, broken by a queue."])

S(plain(K(3, "the fix"), "Queues with quotas, a priority for the gate, preemption at stage boundaries", cards(
  ("grn", "A reserved gate queue", "400 GPUs reserved, highest priority; it borrows the rest from the shared pool."),
  ("grn", "Teams share and borrow", "One queue per team in a cohort; idle quota is lent and reclaimed."),
  ("grn", "Preempt at stage ends", "Exploratory jobs checkpoint per stage, so a preemption loses one stage at most."), cols=3) +
  strip(("whyb", "Covers, and does not", "Gate latency and fairness. Not a gate that recomputes everything: that needs capacity, or an earlier start."), cols="one") + rejl(*REJ(3))), [
 "C: The fix, one level down, in Kueue terms.", P,
 "C: A reserved cluster queue for gates: four hundred G-P-Us, the highest priority, and it borrows the rest from the shared pool.", P,
 "C: One queue per team, in a cohort, so idle quota is lent and reclaimed, and no team can take more than its share when others want theirs.", P,
 "C: And exploratory jobs are preemptible, checkpointing at every stage boundary, which is natural here: a stage's output is already written to the cache. A preemption loses one stage at most.", P,
 "C: It covers gate latency and fairness. It does not cover a gate that recomputes everything: that needs capacity or an earlier start.", P,
 "C: Rejected: one FIFO queue. The gate waits behind exploration, and one team fills the cluster."])

qs("Interviewer · the second-level push", "“Perception changed, so nothing hits. The gate really needs 1,040 GPUs for four hours.”", [
 "I: Perception changed, so nothing hits. The gate really needs a thousand and forty G-P-Us for four hours.", "[pause: 1.5]"])

S(plain(K(3, "the second fix, and the honest limit"), "Warm the cache before the cut", cards(
  ("grn", "Pre-warm nightly", "Every night, run the gate set on the release branch's head: on cut day, perception already hits."),
  ("amb", "Borrow from training", "A preemption agreement: training checkpoints and yields up to 600 GPUs for a gate."),
  ("red", "Honest limit", "A perception change on cut day itself takes about six hours. The schedule says so in advance."), cols=3)), [
 P, "C: First, pre-warm. Every night, the gate set runs on the head of the release branch, so on cut day perception already hits.", P,
 "C: Second, an agreement with training: it checkpoints and yields up to six hundred G-P-Us to a gate.", P,
 "C: And the honest limit: a perception change landed on cut day itself takes about six hours. The release schedule says so in advance, which is cheaper than pretending."])

say_slide("“Gates run in a reserved, high-priority queue that borrows from a shared pool; teams get quotas with borrowing, and exploratory jobs are preempted at stage boundaries, so a preemption costs one stage. And I pre-warm the cache nightly on the release branch, so cut day is mostly hits.”", [
 "V: If asked, I'd say: gates run in a reserved, high-priority queue that borrows from a shared pool. Teams get quotas with borrowing, and exploratory jobs are preempted at stage boundaries, so a preemption costs one stage. And I pre-warm the cache nightly on the release branch, so cut day is mostly hits.", "[pause: 1.0]",
 "N: That fix creates the next question: the gate now answers on time. Is its answer about the right thing?"])
