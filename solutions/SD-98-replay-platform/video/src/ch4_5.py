from dsl import *
from stack import TECH, STACK, SUMMARY, SUMMARY_SAY, say_text
import re
P = "[+]"

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "What a run is, on the wire and on disk", [
 "C: The A-P-I next, then the data. Every endpoint is tagged with the requirement it serves."])

S(plain("API · start a run (FR2)", "A run is a build, a set version, and nothing implicit",
  chips("serves FR2", "writes MANIFEST, RUN", "returns the manifest id") +
  code('POST /v1/runs\n{"build": "7f3c",\n "images": {"perception": "sha256:91ab…",\n            "planning": "sha256:4c07…"},\n "set": "left-rain@1",\n "seed": 42}\n\n201 Created\n{"run_id": 9921, "manifest_id": "m-9921",\n "cache": {"hit": 0.71}}', "json", hl=(3, 5, 6))), [
 "C: Starting a run, for F-R-two. A run is a build, given as image digests rather than tags, a scenario set with its version, and a seed. Nothing is implicit: there is no latest.",
 "C: The answer is a run I-D and a manifest I-D, and how much of the run the cache already had: seventy-one percent here."])

S(plain("API · find, reproduce, gate", "Three more endpoints, each tagged", table(["Endpoint", "Serves", "Touches", "What the response says"], [
  ["<code>POST /v1/sets</code> {query, name}", "FR1", "SCENARIO SET", "<code>name@version</code>, the chunk hashes"],
  ["<code>POST /v1/runs</code> {from_manifest}", "FR3", "MANIFEST, RUN", "the same keys; <code>verify=true</code> re-executes"],
  ["<code>POST /v1/gates</code> {build}", "FR4", "GATE DECISION", "<code>pass</code> or <code>block</code>, reasons, policy version"]], "bt xs mx")), [
 "C: Three more.", P,
 "C: Sets, for F-R-one: a query and a name, and back comes a versioned set with its chunk hashes. A version never changes.", P,
 "C: Reproduce, for F-R-three: a run from an existing manifest. Verify equals true re-executes instead of trusting the cache.", P,
 "C: And gates, for F-R-four: a build in, a verdict out, with its reasons and the policy version."])

S(plain("Data · the manifest in full", "Everything a run read, by content",
  code('{"manifest_id": "m-9921",\n "set": "left-rain@1",\n "chunks": "sha256:5e1d… (list of 9,200)",\n "images": {"perception": "sha256:91ab…",\n            "planning": "sha256:4c07…"},\n "models": {"tracker": "sha256:aa30…"},\n "map_version": 31, "agents": "sha256:0f2e…",\n "seed": 42, "mode": "deterministic"}', "json", hl=(3, 4, 6, 8))), [
 "C: The manifest in full, because it is the core object of this design. The scenario set and its version. The hash of the list of nine thousand two hundred log chunks. Every image by digest. Every model's weights by hash. The map version and the agent models. The seed, and the mode: deterministic or fast.",
 "C: Nothing in it is a name that can move. Given this record and the stored blobs, anyone can rerun the run, next week or next year, and get the same answer. And because it's immutable, a manifest I-D is a fine thing to put in an incident report."])

S(dia("Data · conceptual model", "Runs are pinned by manifests; gates compare two runs", "erd-chen"), [
 "C: The conceptual model, a piece at a time.", P,
 "C: A scenario set lists scenarios, many to many.", P, "C: A scenario spans log chunks, named by their hash.", P,
 "C: A run replays scenarios.", P, "C: Every run is pinned by exactly one manifest; a manifest can pin many runs.", P,
 "C: A run produces artifacts, each under its key.", P,
 "C: And a gate decision compares two runs: the candidate and the baseline."], cls="dia")

S(dia("Data · physical model", "Where each entity lives, and its key", "erd-physical"), [
 "C: The physical tables.", P, "C: The manifest: image digests, model hashes, map version, seed. Immutable once written.", P,
 "C: The run points to its manifest.", P, "C: The artifact index, in Bigtable: key to blob, producer and size. The blob is written first.", P,
 "C: Metrics in ClickHouse: run, scenario, name, value. Six billion rows a month.", P,
 "C: Gate decisions: candidate, baseline, policy version and verdict. Append only.", P,
 "C: And scenario sets: a name and version, and a list that never changes."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions on one picture, then every path", [
 "C: The design in three versions, each answering the objection to the one before, on one picture that only changes by deltas."])

S(dia("Design · version 1", "The simplest thing that is reproducible: pinned runs on a batch pool", "base-v1", vtag="V1"), [
 "C: Version one, the simplest thing that is reproducible, in the order a run travels.", P,
 "C: Log ingest delivers chunks.", P, "C: Into a log store, immutable, named by hash.", P,
 "C: An engineer asks for a run.", P, "C: The run A-P-I writes a manifest.", P,
 "C: It resolves the scenario set from the catalog.", P,
 "C: It sends every stage of every scenario to a batch scheduler.", P,
 "C: Sim workers fetch chunks by byte range and replay them in a deterministic harness.", P,
 "C: Metrics land in a results store. The objection: every build recomputes everything, a thousand G-P-Us per gate."], cls="dia")

S(dia("Design · version 2", "Reuse: a DAG planner and an artifact cache", "base-v2", vtag="V2"), [
 "C: Version two answers that.", P, "C: Version one, carried.", P,
 "C: New, a DAG planner: it turns a run into stages, computes a content key per stage, and sends only the misses.", P,
 "C: New, an artifact cache: outputs by key, a blob store with an index. Workers read hits and write misses. The objection: who decides that a difference blocks a release, and against what?"], cls="dia")

S(dia("Design · version 3", "The gate: pairs, a policy, a verdict", "base-v3", vtag="V3"), [
 "C: Version three answers that.", P, "C: Version two, carried.", P,
 "C: New, the release pipeline, which asks for a verdict.", P,
 "C: New, the gate service: it submits the gate set, pairs the candidate's results with the last release's, applies a versioned policy, and answers pass or block. This is the baseline."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Log store", "Immutable chunks, named by hash", "20 PB; +1 PB a month"],
  ["Scenario catalog", "Versioned sets, manifests, decisions", "small, transactional"],
  ["Run API + planner", "Manifests; stage keys; lookups; misses only", "6 M runs a month"],
  ["Artifact cache", "Outputs by key, blob then index", "100 TB"],
  ["Scheduler", "Quotas, priority, preemption", "~1,000 GPUs at a gate"],
  ["Sim workers", "The deterministic harness", "17 GB/s of reads at a gate"],
  ["Results + gate", "Metrics; pairs; verdicts", "6 B rows a month"]], "bt xs mx")), [
 "C: The containers, one line each.", P, "C: The log store: immutable chunks named by hash. Twenty petabytes.", P,
 "C: The catalog: versioned sets, manifests and decisions. Small and transactional.", P,
 "C: The run A-P-I and planner: manifests, stage keys, lookups, and only the misses go on.", P,
 "C: The artifact cache: outputs by key, a hundred terabytes.", P,
 "C: The scheduler: quotas, priority and preemption, around a thousand G-P-Us on gate day.", P,
 "C: The sim workers: the deterministic harness, reading seventeen gigabytes a second at a gate.", P,
 "C: And results with the gate: metrics, pairs and verdicts. Nothing on the run path waits for a person."])

S(dia("Flow · FR2", "A run, from the engineer to the metrics", "flow-run"), [
 P, "C: A run, numbered.", P, "C: One: the engineer submits build and set.", P, "C: Two: the A-P-I writes the manifest and hands it to the planner.", P,
 "C: Three: the planner resolves the set version from the catalog.", P, "C: Four: it looks up every stage key in the cache.", P,
 "C: Five: only the misses go to the scheduler.", P, "C: Six: pods start on the workers.", P,
 "C: Seven: workers read chunks by byte range.", P, "C: Eight: metrics land in the results store."], cls="dia")

S(dia("Flow · FR4", "A gate, from the release pipeline to the verdict", "flow-gate"), [
 P, "C: A gate, numbered.", P, "C: One: the release pipeline asks about a build.", P, "C: Two: the gate submits the gate set.", P,
 "C: Three: the A-P-I hands it to the planner.", P, "C: Four: misses go to the scheduler, in the reserved queue.", P,
 "C: Five: workers run them.", P, "C: Six: metrics land.", P, "C: Seven: the gate pairs them with the last release.", P,
 "C: Eight: pass or block, back to the pipeline."], cls="dia")

S(dia("Sequence · FR1 find", "A query becomes a set that never changes", "seq-find"), [
 "C: Find, as a sequence.", P, "C: An engineer asks for unprotected left turns in rain.", P,
 "C: The catalog is queried by tags and chunk ranges.", P, "C: Eighteen hundred and forty scenarios.", P,
 "C: Saved as left-rain, version one.", P, "C: Which is a list of chunk hashes. It will mean the same thing in a year."], cls="dia")

S(dia("Sequence · FR2 run", "Hits are read, misses are run", "seq-run"), [
 "C: Run, as a sequence.", P, "C: Build seven-f-three on left-rain version one.", P,
 "C: The planner writes the manifest: digests, set version, seeds.", P, "C: It looks up three stage keys per scenario.", P,
 "C: Perception all hit; planning all miss.", P, "C: Eighteen hundred and forty planning jobs go to the scheduler.", P,
 "C: Pods start within the team's quota.", P, "C: Metrics land as run ninety-nine twenty-one."], cls="dia")

S(dia("Sequence · FR3 reproduce", "An incident from March, again", "seq-repro"), [
 "C: Reproduce, as a sequence.", P, "C: An engineer reproduces run forty-four ten, from an incident in March.", P,
 "C: The planner loads its manifest. Same inputs, so the same keys.", P, "C: It looks them up.", P,
 "C: All hit: identical outputs, in seconds.", P, "C: To be sure, verify re-executes without the cache.", P,
 "C: And the output hashes equal March's. That's S-one, checked."], cls="dia")

S(dia("Sequence · FR4 gate", "Pairs, intervals, a verdict", "seq-gate"), [
 "C: The gate, as a sequence.", P, "C: The pipeline asks about build seven-f-three.", P,
 "C: The gate runs gate-set version fifty-seven on it.", P, "C: Fifty thousand scenarios; seventy percent of stages hit.", P,
 "C: Metrics land as run ninety-nine thirty.", P, "C: The gate pairs it with the released run, ninety-eight eleven.", P,
 "C: Intervals per metric, under policy fourteen.", P,
 "C: Block: the hard-braking rate is up four tenths of a percent, and the interval excludes zero."], cls="dia")

# ───────────────────────── 5.1 · components and technologies ─────────────────────────
subchapter("5.1", "Components and technologies", ["C: One level down: the same picture with what each box runs on, the three containers the challenges open, and for each choice what I rejected."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 P, "C: The same container view; only the type lines changed.", P,
 "C: The log store: MCAP files on Google Cloud Storage, one-minute chunks, hashed.", P, "C: The catalog: PostgreSQL.", P,
 "C: The planner: a Go service.", P, "C: The artifact cache: blobs on G-C-S with a Bigtable index.", P,
 "C: The scheduler: Kubernetes with Kueue.", P, "C: The workers: G-P-U and C-P-U pods running the harness.", P,
 "C: Results: ClickHouse.", P, "C: And the gate: a Go service, with its policy as code."], cls="dia")

S(dia("Architecture · C4 components · sim worker", "Inside a sim worker, in the order a chunk meets it", "c4-comp-worker"), [
 "C: Inside a sim worker.", P, "C: The log store.", P, "C: The chunk fetcher reads byte ranges and checks each chunk's hash.", P,
 "C: The sim clock and bus: one clock, and delivery in order of time, topic and sequence.", P,
 "C: Agent models, for road users that react.", P, "C: The stage runner runs pinned images in a sandbox.", P,
 "C: Before each stage, the cache client asks for the key; after it, it writes the output.", P, "C: Into the artifact cache.", P,
 "C: The metric extractor, per scenario.", P, "C: The result writer, with the manifest attached.", P,
 "C: Into the results store. Challenges one and four happen in this picture."], cls="dia")

S(dia("Architecture · C4 components · DAG planner", "Inside the planner: from a request to the misses", "c4-comp-planner"), [
 "C: Inside the planner.", P, "C: A run request arrives.", P,
 "C: The manifest builder pins the set version from the catalog, and every digest.", P,
 "C: The stage graph comes from the build, with images resolved by digest.", P,
 "C: The key hasher chains stage keys.", P, "C: The index lookup, batched per scenario, against the cache index.", P,
 "C: The job emitter sends only the misses.", P, "C: To the scheduler. Challenge two lives here."], cls="dia")

S(dia("Architecture · C4 components · gate service", "Inside the gate: from a build to a verdict", "c4-comp-gate"), [
 "C: Inside the gate.", P, "C: The release pipeline asks.", P, "C: A gate request: build and set version.", P,
 "C: The baseline resolver finds the last released run on the same set.", P,
 "C: The paired differ reads both runs' metrics per scenario.", P, "C: A flake list removes scenarios that disagree with themselves.", P,
 "C: Statistics: an interval per metric, not a point.", P, "C: The policy evaluator applies versioned rules from a reviewed repository.", P,
 "C: And every decision is recorded. Challenge five lives here."], cls="dia")

def tsay(_id):
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
for _id in ("logs", "cache", "sched", "res"):
    S(tech(**TECH(_id)), tsay(_id))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

# ───────────────────────── 5.2 · when you don't need all this ─────────────────────────
subchapter("5.2", "When you don't need all this", ["C: Before I break it: at a smaller scale, a much simpler design is right, and I should say where the line is."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "No planner, no cache: recompute every night", "alt",
      extra=strip(("fixb", "How it works", "A nightly job runs every scenario on the release branch in the same deterministic harness; results compared with last night's by fixed rules."),
                  ("case", "What it gives up", "Cost grows with builds × scenarios; no fast per-change answer; reuse is impossible."))), [
 P, "C: The alternate path, on version two.", P, "C: The planner goes away.", P, "C: And the cache.", P,
 "C: Instead, a nightly job runs every scenario on the release branch, in the same deterministic harness, and compares with last night by fixed rules.", P,
 "C: What it gives up: cost grows with builds times scenarios, engineers wait a night for an answer, and nothing is reused."], cls="dia")

key("ALTERNATE · the line", "A gate of <em>1,000 scenarios</em> is 83 GPU-hours: about <em>21 GPUs</em> for four hours. At <em>50,000</em> it is 1,040. Below about <em>5,000 scenarios</em>, I'd ship the nightly recompute.", [
 "C: Where is the line? A thousand scenarios is eighty-three G-P-U-hours: twenty-one G-P-Us for four hours, easy. Fifty thousand is a thousand and forty.",
 "V: Below about five thousand scenarios, about a hundred G-P-Us, I'd ship the nightly recompute, and say when I'd switch. The determinism I'd build anyway: the cache needs it later.", "[pause: 0.8]"])
