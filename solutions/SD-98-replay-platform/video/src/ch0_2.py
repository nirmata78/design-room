from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Replay recorded logs against new builds, and trust the answer", [
 "C: Replaying recorded logs against a new build sounds like a batch job. It is asked at autonomous-driving companies and wherever a release must be tested on recorded reality, because a replay is only worth running if the same inputs give the same answer, and a gate is only worth having if it can fail for the right reason."])

qs("Interviewer · the prompt", "“Thousands of engineers want to run new builds against petabytes of recorded logs, and get results they can trust before a release. Design the platform.”", [
 "I: Thousands of engineers want to run new builds against petabytes of recorded logs, and get results they can trust before a release. Design the platform.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Recompute for trust, or reuse for speed", "tension",
      chip=chips("trustworthy", "affordable", "both, if every input is in the key")), [
 "C: Here is the hook as one picture. Recomputing everything for every build is trustworthy, and costs about a thousand G-P-Us for each four-hour release gate.",
 "C: Reusing yesterday's outputs by build name is cheap, and silently wrong the day a dependency changes. The design lives in the third box: reuse by content, where a cached output is keyed by a hash of everything that produced it. Then a hit equals a recompute, but only if the computation is deterministic and nothing it reads is missing from the key."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Run simulations at scale”", "Asks what must be reproducible, how fast a gate must answer, who decides a block"],
  ["<b>Correctness</b>", "“Set the random seed”", "A pinned manifest, simulated time, ordered delivery, hermetic stages"],
  ["<b>Trade-offs</b>", "Cache everything, or nothing", "Content keys; what a hit costs to trust; closed loop against open loop"],
  ["<b>Depth</b>", "Stops at “Kubernetes jobs”", "Merkle keys per stage, quotas and preemption, paired statistics"],
  ["<b>Operations</b>", "Job success rate", "Double-run agreement, cache audits, a known-bad build that must fail"]], "bt xs sig") +
  grade("A difference must mean the build changed, never that the run did.")), [
 "N: Five axes, one at a time.", P,
 "N: Requirements. Weak: run simulations at scale. Strong: what must be reproducible, how fast the gate must answer, and who decides a block.", P,
 "N: Correctness. Weak: set the random seed. Strong: a pinned manifest, simulated time, ordered delivery, and stages that can read nothing else.", P,
 "N: Trade-offs. Weak: cache everything or nothing. Strong: content keys, what it costs to trust a hit, and closed loop against open loop.", P,
 "N: Depth: Merkle keys per stage, quotas with preemption, paired statistics.", P,
 "N: Operations: not the job success rate, but double-run agreement, cache audits, and a known-bad build that must fail the gate.", P,
 "C: And the rule for the whole round: a difference must mean the build changed, never that the run did."])

key("The thesis", "Make every run a <em>pure function of a pinned manifest</em>, so outputs can be <em>cached by content</em> and differences <em>mean something</em>; then gate on <em>paired statistics</em> under a <em>versioned policy</em>.", [
 "V: Make every run a pure function of a pinned manifest, so outputs can be cached by content and differences mean something. Then gate on paired statistics, under a versioned policy.", "[pause: 1.0]"])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "The scale first, then five questions", [
 "C: The scale first, then five questions. Each answer moves the design."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>1 PB · 6 M</b><span>new logs · scenario-runs a month</span></div>'
  '<div class="tile"><b>20 PB</b><span>of logs kept today; 3,000 engineers</span></div>'
  '<div class="tile red"><b>50,000 in 4 h</b><span>the release gate, on release-cut day</span></div></div>' +
  line("Every number later in this video starts from one of these three.", "a")), [
 "C: The scale, written down first.", P,
 "C: A petabyte of new logs a month, and about six million scenario-runs a month from three thousand engineers.", P,
 "C: Twenty petabytes of logs kept today.", P,
 "C: And the peak: on the day a release is cut, a gate of fifty thousand scenarios must answer within four hours, on top of everyone else's runs.", P,
 "C: Every number I use later starts from one of these."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "What is a scenario, and what does it cost?", "2–20 minutes of log, about 5 on average; ~1 GB a log-minute; perception needs ~1 GPU-minute per log-minute.",
     "What is a scenario, and what does replaying one cost?", "Two to twenty minutes of log, five on average. About a gigabyte per log-minute, and the perception stages need about a G-P-U-minute per log-minute.",
     "So compute is the bill, and perception is most of it. Whatever avoids recomputing perception is worth building.")
clar(2, "How reproducible?", "An incident replay must give the same answer a year later. Same inputs, same outputs.",
     "How reproducible does a run have to be?", "An incident replay must give the same answer a year later. Same inputs, same outputs.",
     "Then a run is defined by its inputs, and every input must be pinned: logs, code, model weights, maps, seeds.")
clar(3, "Open loop or closed loop?", "Mostly log replay. Reactive agents exist for some scenarios.",
     "Do the other road users react to the new build, or do we replay them as logged?", "Mostly log replay. Reactive agent models exist for some scenarios.",
     "Log replay stops being true once the new build acts differently. I'll need to know when that happens. Challenge four.")
clar(4, "Who decides a release is blocked?", "The safety team owns the rules; the gate applies them; overrides need a named approver.",
     "Who decides that a result blocks a release?", "The safety team owns the rules. The gate applies them. Overrides need a named approver.",
     "So the rules are versioned data, not code buried in a script, and every decision records which version it used.")
clar(5, "Where does it run?", "On the company's Kubernetes clusters, sharing GPUs with model training.",
     "Where does the compute come from?", "The company's Kubernetes clusters, sharing G-P-Us with model training.",
     "Shared means quotas and preemption. The gate can't wait behind training, and exploration can't starve.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Find", "Select scenarios by tags and save them as an immutable, versioned set."),
  ("grn", "FR2 · Run", "Run a build on a set; results per scenario and metric, reusing whatever is unchanged."),
  ("amb", "FR3 · Reproduce", "Re-run any past run from its manifest and get the same outputs."),
  ("red", "FR4 · Gate", "Compare a release candidate with the last release on the gate set and answer pass or block."))), [
 "C: Four functional requirements.", P,
 "C: One, find: select scenarios by tags, and save them as an immutable, versioned set.", P,
 "C: Two, run a build on a set, with results per scenario and metric, reusing whatever didn't change.", P,
 "C: Three, reproduce any past run from its manifest, with the same outputs.", P,
 "C: Four, gate: compare a release candidate with the last release, on the gate set, and answer pass or block. Each gets a sequence later."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets</p><div class="tiles" style="--n:4">'
  '<div class="tile blue"><b>4 h</b><span>a 50,000-scenario gate, p95</span></div>'
  '<div class="tile blue"><b>100 %</b><span>reproducible on CPU stages; declared tolerance on GPU</span></div>'
  '<div class="tile"><b>15 min</b><span>an engineer’s 1,000-scenario run</span></div>'
  '<div class="tile red"><b>0</b><span>unexplained passes: no false pass</span></div></div>' +
  line("A gate that cannot answer is a release that waits; a gate that answers wrong is a release that ships.", "a")), [
 "C: The numbers, initial targets.", P, "C: A fifty-thousand-scenario gate within four hours.", P,
 "C: Bit-for-bit reproducible on C-P-U stages, and within a declared tolerance on G-P-U stages.", P,
 "C: An engineer's thousand-scenario run within fifteen minutes, so people iterate.", P,
 "C: And no unexplained pass.", P,
 "C: A gate that can't answer is a release that waits. A gate that answers wrong is a release that ships."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Scenario sets, manifests, the replay harness, caching, scheduling, results, the release gate, its audit."),
  ("red", "Out, on purpose", "Log ingestion from the fleet. Building the simulator's physics. Model training. The release pipeline itself.")) +
  line("Ingestion is out, but its output is my input: chunks I can name by hash.", "")), [
 P, "C: In scope: scenario sets, manifests, the replay harness, caching, scheduling, results, the release gate and its audit.", P,
 "C: Out, on purpose: ingesting logs from the fleet, the simulator's physics, model training, and the release pipeline itself.", P,
 "C: One thing I'd say aloud: ingestion is out, but its output is my input. I need log chunks I can name by their hash."])

S(dia("Architecture · C4 level 1 · context", "The system in its context", "c4-context",
      cap="Figure 1.1 — C4 system context: who runs builds, who asks for a verdict, where logs and compute come from"), [
 "C: The system in its context.", P,
 "C: Engineers, three thousand of them, run builds against recorded logs and read results.", P,
 "C: The replay platform, one box for now.", P,
 "C: The release pipeline asks it whether a build may ship.", P,
 "C: Log ingest delivers fleet logs, a petabyte a month.", P,
 "C: And the compute cluster runs our pods, shared with training."], cls="dia")

key("The core", "The core is three things: <em>runs defined by pinned manifests</em>, <em>outputs cached by the hash of what made them</em>, and a <em>gate that compares pairs under a versioned policy</em>.", [
 "V: The core is three things. Runs defined by pinned manifests. Outputs cached by the hash of what made them. And a gate that compares pairs, under a versioned policy.", "[pause: 0.8]"])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", [
 "C: Numbers next, each from the scale line, each ending in a decision. Illustrative, not anyone's real figures."])

S(plain("Estimates · the gate", "Fifty thousand scenarios in four hours", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Bytes read", "the gate", "50,000 × 5 log-min × 1 GB = <b>250 TB</b>; ÷ 14,400 s ≈ 17 GB/s", "Byte-range reads from object storage; no copies"],
  ["GPU, nothing cached", "the gate", "250,000 log-min × 1 GPU-min = 4,170 GPU-h; ÷ 4 h ≈ <b>1,040 GPUs</b>", "Too many to reserve: reuse is required"],
  ["GPU, perception cached", "the gate", "planning only: ≈ 4,170 CPU-h ≈ <b>1,040 cores</b> for 4 h", "A planning change is cheap if perception hits"]])), [
 "C: The gate first.", P,
 "C: Fifty thousand scenarios times five log-minutes times a gigabyte is two hundred and fifty terabytes, seventeen gigabytes a second over four hours. Object storage serves that by byte range, if nothing is copied.", P,
 "C: Perception at a G-P-U-minute per log-minute is four thousand one hundred and seventy G-P-U-hours: about a thousand and forty G-P-Us for four hours. Too many to reserve for one gate.", P,
 "C: But if only planning changed and perception's outputs are reused, it's about a thousand C-P-U cores for four hours. Reuse is the difference between possible and not."])

S(plain("Estimates · a month, and what it holds", "Six million runs a month, and where the money goes", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Compute", "6 M runs", "6 M × 5 log-min = 30 M GPU-min = 500,000 GPU-h ≈ <b>$1 M</b> at $2", "A 70 % hit rate saves ≈ $700 k a month"],
  ["Cache", "the gate set", "100 MB per scenario × 50,000 × 20 versions ≈ <b>100 TB</b>", "Blob store + index, not memory"],
  ["Metrics", "6 M runs", "6 M × ~1,000 metrics = <b>6 B rows</b> a month", "A columnar store"]])), [
 "C: A month.", P,
 "C: Six million runs of five log-minutes is thirty million G-P-U-minutes, five hundred thousand G-P-U-hours. At two dollars an hour, about a million dollars a month. Every ten points of cache hit rate is a hundred thousand dollars a month.", P,
 "C: The cache: a perception output is about a hundred megabytes per scenario. Twenty versions of the gate set is about a hundred terabytes. A blob store with an index, not memory.", P,
 "C: And metrics: a thousand per run is six billion rows a month. A columnar store."])

S(plain("Estimates · storage and reads", "Twenty petabytes, read by range, never copied", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Logs", "the scale line", "20 PB + 1 PB a month; ~1 GB per log-minute", "Immutable chunks in object storage"],
  ["Gate reads", "the gate", "250 TB in 4 h ≈ <b>17 GB/s</b> over thousands of chunks", "Parallel byte-range reads, near the data"],
  ["A copy per job", "6 M runs", "6 M × 5 GB = <b>30 PB</b> moved a month", "Copies are ruled out: read in place"]])), [
 "C: Storage and reads.", P,
 "C: Twenty petabytes of logs today, a petabyte more a month, about a gigabyte per log-minute. Immutable chunks in object storage.", P,
 "C: A gate reads two hundred and fifty terabytes in four hours: seventeen gigabytes a second, spread over thousands of chunks. Object storage serves that in parallel, by byte range, if the workers run in the region that holds the data.", P,
 "C: And if every job copied its logs first: six million runs times five gigabytes is thirty petabytes moved a month, more than the whole archive. So nothing is copied. Workers read in place."])

S(plain("Estimates · one engineer's run", "Fifteen minutes for a thousand scenarios, only if perception hits", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Log-minutes", "1,000 scenarios", "1,000 × 5 = 5,000 log-minutes", "The unit of work"],
  ["Perception hits", "the NFR", "5,000 CPU-min ÷ 15 min ≈ <b>330 cores</b>", "Easy, from a shared pool"],
  ["Perception misses", "the NFR", "5,000 GPU-min ÷ 15 min ≈ <b>330 GPUs</b>", "One engineer, a third of the gate: a quota question"]])), [
 "C: And one engineer's run, the thing people do all day.", P,
 "C: A thousand scenarios is five thousand log-minutes.", P,
 "C: If perception hits, planning needs about five thousand C-P-U-minutes. In fifteen minutes that's three hundred and thirty cores, easy from a shared pool.", P,
 "C: If perception misses, it's three hundred and thirty G-P-Us for fifteen minutes: one engineer asking for a third of a gate. That's why quotas exist, and why most people should only change the stages they own."])

S(dia("Estimates · the gate budget", "Four hours, from the request to the verdict", "budget", chip=chips("initial target")), [
 "C: The gate budget. Ten minutes to plan and look up keys. About two hours fifty to compute the misses. Ten minutes to pair the results and apply the policy. And about fifty minutes of margin.",
 "C: The margin is for a gate whose perception changed, when nothing hits. That case is challenge three."], cls="dia")
