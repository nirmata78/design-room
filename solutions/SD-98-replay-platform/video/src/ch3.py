from dsl import *
P = "[+]"

chapter(3, "Theory", 2, "What makes a replay worth trusting", [
 "C: The theory: what makes a replay worth trusting, in terms that outlive any product name. Five mechanisms, the options, and what will go wrong."])

S(plain("Theory · what it is", "A function from pinned inputs to outputs, run millions of times", cards(
  ("", "It is", "Running new code on recorded inputs as a pure function, so outputs can be reused and compared."),
  ("amb", "Not a batch cluster", "A batch cluster runs jobs; it does not promise that two runs agree."),
  ("amb", "Not CI tests", "Unit tests assert; a replay measures thousands of metrics and compares distributions."),
  ("amb", "Not production shadowing", "Shadowing sees today's traffic; replay asks what a new build would do on yesterday's."), cols=2)), [
 "C: What it is, and what it is not.", P,
 "V: Running new code on recorded inputs as a pure function, so outputs can be reused and compared.", P,
 "C: Not a batch cluster: a batch cluster runs jobs, it doesn't promise two runs agree.", P,
 "C: Not C-I tests: tests assert; a replay measures thousands of metrics and compares distributions.", P,
 "C: And not production shadowing, which sees today's traffic. Replay asks what a new build would have done on yesterday's."])

S(plain("Theory · properties", "Safety and liveness, stated separately", cards(
  ("red", "S1 · reproducible", "The same manifest gives the same outputs: bit for bit on CPU, within a declared tolerance on GPU."),
  ("red", "S2 · a hit is a recompute", "A cached output is exactly what recomputing would produce."),
  ("red", "S3 · no false pass", "A build never passes the gate with an unexplained regression."),
  ("grn", "L1 · the gate answers", "A release gate finishes within four hours."),
  ("grn", "L2 · nobody starves", "Every team's runs make progress, even on release day."), cols=3)), [
 "C: Safety first: what must never happen.", P,
 "V: S-one: the same manifest gives the same outputs. Bit for bit on C-P-U stages, within a declared tolerance on G-P-U stages.", P,
 "V: S-two: a cached output is exactly what recomputing would produce.", P,
 "V: S-three: a build never passes the gate with an unexplained regression.", P,
 "C: Liveness: L-one, the gate answers within four hours.", P,
 "C: L-two, every team's runs make progress, even on release day."])

S(plain("Theory · where randomness hides", "Six ways the same build gives two answers", table(["Source", "Example", "What removes it"], [
  ["Wall clock", "a timeout decides a branch", "simulated time; the call fails in the sandbox"],
  ["Thread order", "equal timestamps, either order", "one bus; order by (time, topic, sequence)"],
  ["Random numbers", "unseeded sampling", "seeds per scenario and stage, from the manifest"],
  ["GPU atomics", "a reduction sums in a new order", "deterministic kernels, or a declared tolerance"],
  ["Unpinned inputs", "“latest” model, a tag, a moving map", "digests and hashes only"],
  ["Hidden reads", "an environment variable, a file", "a hermetic sandbox"]], "bt xs mx")), [
 "C: Before the mechanisms, where randomness actually hides. Six places.", P,
 "C: The wall clock: a timeout that decides a branch. Removed by simulated time.", P,
 "C: Thread order: two messages with the same timestamp, delivered either way. Removed by one bus with a total order.", P,
 "C: Random numbers that nobody seeded. Removed by seeds from the manifest.", P,
 "C: G-P-U atomic adds, which sum in a different order every time. Removed by deterministic kernels, or a tolerance we declare.", P,
 "C: Unpinned inputs: a latest model, a tag, a map that moved. Removed by digests and hashes.", P,
 "C: And hidden reads: an environment variable, a file nobody declared. Removed by a hermetic sandbox. Setting a seed fixes exactly one of these six."])

def mech(n, name, prot, how, rules, cost, say):
    S(plain(f"Theory · mechanism M{n}", name, cards(("", "Protects", prot), ("grn", "How it works", how), ("red", "Rules out", rules), ("amb", "Costs", cost), cols=2)), say)

mech(1, "A pinned manifest", "S1.", "A run names every input by content: log-chunk hashes, image digests, model weights, map version, seeds.",
     "“It worked last week” with nothing to compare against.", "Every input must be addressable; nothing may be read by name at run time.", [
 "C: Mechanism one: a pinned manifest.", P, "C: It protects S-one.", P,
 "C: A run names every input by content: the hashes of its log chunks, the digests of its container images, the hashes of its model weights, the map version, and its seeds.", P,
 "C: It rules out a result that nobody can reproduce or compare.", P,
 "C: It costs discipline: every input must be addressable, and nothing may be read by name at run time."])

mech(2, "Simulated time and ordered delivery", "S1.", "The harness owns the clock. Messages are delivered in (time, topic, sequence) order, one at a time.",
     "Results that depend on thread timing or the wall clock.", "Less parallelism inside one scenario; parallelism comes from many scenarios.", [
 "C: Mechanism two: simulated time and ordered delivery.", P, "C: It also protects S-one.", P,
 "C: The harness owns the clock: no component may read the wall clock. Messages between components are delivered in the order of time, topic, and sequence number, one at a time.", P,
 "C: It rules out results that depend on which thread happened to run first.", P,
 "C: It costs parallelism inside one scenario. We get it back across fifty thousand scenarios."])

mech(3, "Content-addressed memoisation", "S2, L1.", "Each stage's key is the hash of its code, parameters, seed and the keys of its inputs: a Merkle chain.",
     "Recomputing what did not change; reusing what did.", "Hermetic stages; an index; storage for outputs.", [
 "C: Mechanism three: content-addressed memoisation.", P, "C: It protects S-two, and makes L-one affordable.", P,
 "C: Each stage's output is stored under a key that hashes the stage's code, its parameters, its seed and the keys of its inputs. Keys chain, like a Merkle tree: change perception, and every key downstream changes with it.", P,
 "C: It rules out both recomputing what didn't change and reusing what did.", P,
 "C: It costs hermetic stages, an index, and storage for outputs."])

mech(4, "Paired comparison under a versioned policy", "S3.", "Candidate and baseline on the same scenarios; per-metric differences; an interval, not a point; rules as versioned data.",
     "Blocking on noise; passing on luck; decisions nobody can explain later.", "Two runs per question; statistics people must trust.", [
 "C: Mechanism four: paired comparison under a versioned policy.", P, "C: It protects S-three.", P,
 "C: Run the candidate and the baseline on the same scenarios, take per-scenario differences per metric, and compute an interval, not a single number. The rules that turn intervals into pass or block are versioned data.", P,
 "C: It rules out blocking on noise, passing on luck, and decisions nobody can explain later.", P,
 "C: It costs two runs per question, and statistics people must learn to trust."])

mech(5, "Quotas, priority and preemption", "L1, L2.", "A reserved queue for gates; teams share and borrow idle quota; exploratory jobs are preemptible at stage boundaries.",
     "The gate waiting behind exploration; one team filling the cluster.", "Preempted work is redone, up to one stage.", [
 "C: Mechanism five: quotas, priority and preemption.", P, "C: It protects both liveness properties.", P,
 "C: Gates run in a reserved, high-priority queue. Teams share a pool and borrow each other's idle quota. Exploratory jobs can be preempted, at stage boundaries.", P,
 "C: It rules out the gate waiting behind exploration, and one team filling the cluster.", P,
 "C: It costs redone work: up to one stage per preemption."])

S(plain("Theory · the options", "Five ways to build it, one picked", table(["Approach", "Reproducible", "Affordable", "Fails when"], [
  ["A · scripts on copied logs, per engineer", "no", "no", "nobody can rerun a result; copies cost more than compute"],
  ["B · recompute everything, every build", "yes", "no", "1,040 GPUs per gate; exploration starves"],
  ["C · reuse outputs by build name", "no", "yes", "a changed dependency serves a stale hit"],
  ["D · shadow in production only", "partly", "yes", "no counterfactual before release"],
  ("pick", ["<b>E · pinned manifests, content-keyed stages, a deterministic harness</b>", "yes", "yes", "every input must be hashed; hermeticity is enforced"])], "bt xs mx") +
  line("Pay for determinism once; it buys both caching and meaningful differences.", "a")), [
 "C: Five ways to build it.", P,
 "C: A, scripts on copied logs: nobody can rerun a result, and the copies cost more than the compute.", P,
 "C: B, recompute everything every time: trustworthy, a thousand G-P-Us per gate.", P,
 "C: C, reuse outputs by build name: cheap, until a changed dependency serves a stale hit.", P,
 "C: D, shadowing in production only: there's no counterfactual before the release.", P,
 "C: E, which I pick: pinned manifests, stages keyed by content, and a deterministic harness.", P,
 "V: Pay for determinism once. It buys both caching and differences that mean something.", "[pause: 0.8]"])

S(plain("Theory · the mechanisms at work", "Where each mechanism will live", table(["Mechanism", "Where", "In one clause"], [
  ["M1 · manifest", "run API, planner, log store", "chunks named by hash; a manifest per run"],
  ["M2 · simulated time", "sim workers", "the harness owns the clock and the order"],
  ["M3 · memoisation", "planner, artifact cache", "keys chain stage to stage; blob first, index after"],
  ["M4 · paired policy", "gate service", "intervals per metric; rules versioned"],
  ["M5 · quotas", "scheduler", "a reserved gate queue; preemption at stage ends"]], "bt xs mx")), [
 "C: Where each one lives. I'll draw the system once, in the design chapter; these labels come back on it at the end.", P,
 "C: M-one, the manifest: in the run A-P-I, the planner, and the log store whose chunks are named by hash.", P,
 "C: M-two, simulated time: in the sim workers.", P,
 "C: M-three, memoisation: in the planner and the artifact cache.", P,
 "C: M-four, the paired policy: in the gate service.", P,
 "C: M-five, quotas: in the scheduler."])

S(dia("Theory · mechanism M3 at work", "Two keys, one hit, one miss", "seq-th-keys"), [
 "C: Mechanism three at protocol level.", P,
 "C: The planner computes the perception key: a hash of the perception image digest, the chunk hashes and the parameters.", P,
 "C: Then the planning key, which includes the perception key, the map version and the seed. That's the chain.", P,
 "C: It asks the cache index for both.", P, "C: Perception hits; planning misses, because only planning changed.", P,
 "C: So only planning runs, reading perception's cached output.", P,
 "C: And the worker writes the blob first, then the index row. A reader that finds the row always finds a complete blob."], cls="dia")

S(plain("Theory · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "Property at risk"], [
  ["1", "The same build gives two different results", "S1"],
  ["2", "A perception change: what must be recomputed?", "S2, L1"],
  ["3", "Release day: the gate against 3,000 engineers", "L1, L2"],
  ["4", "The new planner acts differently; the log does not react", "S3"],
  ["5", "A 0.3 % change in a safety metric: block?", "S3"],
  ["6", "The gate passes, and the field regresses", "all of them"]], "bt sm")), [
 "C: The failure catalogue, which becomes the challenges.", P, "C: One: the same build gives two different results.", P,
 "C: Two: perception changes; what must be recomputed?", P, "C: Three: release day, the gate against three thousand engineers.", P,
 "C: Four: the new planner acts differently, and the logged world doesn't react.", P,
 "C: Five: a small change in a safety metric. Block?", P, "C: Six: the gate passes, and the field regresses."])
