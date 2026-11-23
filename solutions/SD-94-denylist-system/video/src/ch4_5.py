from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I before the boxes. It is the contract, and it shows whether I have thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes."])

def wire(l, r): return f'<div class="cols2"><pre class="wire">{l}</pre><pre class="wire">{r}</pre></div>'

S(plain("API · publish", "PublishChange", tr(("fr", "serves FR1"), ("api", "PublishChange"), ("ent", "writes ChangeSet · Rule"), ("nfr", "idempotent")) +
  wire('<span class="cm">// request</span>\nPublishChange {\n  list: "abuse",\n  ops: [{ op: "add",\n          key: "203.0.113.0/28",\n          kind: "range",\n          action: "deny",\n          reason: "ticket 7712",\n          source: "policy-tool",\n          expiresAt: "2026-12-01" }],\n  idempotencyKey: "c4f9…"\n}',
       '<span class="cm">// response</span>\n{ changeSetId: "cs-90113",\n  version: 8361004,\n  stage: 0 }\n\n<span class="cm">// a retry with the same key returns\n// the SAME version, never a second one\n// large or wide changes wait for a\n// second approver</span>')), [
 "C: Publish. A list name and a set of operations. Each carries the operation, the key, whether it is a single address or a range, the action, a reason, a source and an optional expiry. An idempotency key makes a retried publish harmless: the same key returns the same version, never a second one.",
 "C: The response is a change set id and the version it was given. Large or wide changes wait for a second approver. This call serves requirement one, and writes a change set and its rules."])

S(plain("API · distribution", "Manifest, delta, snapshot", tr(("fr", "serves FR2"), ("api", "manifest · delta · snapshot"), ("ent", "reads Version"), ("nfr", "immutable, cacheable")) +
  wire('<span class="cm">// the 10 s poll: about 100 bytes</span>\nGET /manifest?list=abuse&amp;have=8361000\n\n<span class="cm">// the artifacts: immutable, content-addressed</span>\nGET /delta?list=abuse&amp;from=8361000\nGET /snapshot/8361004',
       '<span class="cm">// manifest response</span>\n{ current: 8361004,\n  minDelta: 8274600,   <span class="cm">// window start</span>\n  deltaRef: "d/8361000-8361004",\n  snapshotRef: "s/8361004",\n  checksum: "9ab3…",\n  killed: false }      <span class="cm">// the kill flag</span>')), [
 "C: Distribution. The poll is a get on the manifest with the node's version. The response is tiny: the current version, where the delta window starts, references to the delta and snapshot, a checksum, and the kill flag. The delta and snapshot are immutable, content-addressed files, so any relay can cache them. The node reads minDelta: at or above it, fetch the delta, otherwise the snapshot. Never a file on a routine poll."])

S(plain("API · the check", "Check is not a network call", tr(("fr", "serves FR3"), ("api", "Check(key)"), ("ent", "reads the node's structure"), ("nfr", "< 10 µs")) +
  wire('<span class="cm">// in process, on the request path</span>\nverdict = agent.check(sourceAddress)\n\n<span class="cm">// returns</span>\n{ verdict: DENY | ALLOW | CHALLENGE,\n  ruleId: 4411,\n  version: 8361004 }',
       '<span class="cm">// order of evaluation</span>\n1. normalise (canonical CIDR, v6 forms)\n2. allowlist ranges: if match, ALLOW\n3. exact key\n4. longest-prefix range\n5. default ALLOW\n\n<span class="cm">// the version in the verdict is what\n// makes the decision log auditable</span>')), [
 "C: The check. Notice it is a library call in the serving process, not a network A-P-I. It returns a verdict, which may be deny, allow or challenge, the rule that decided, and the version of the list. The order matters: normalise the key, check the allowlist first, then the exact key, then the longest-prefix range, then allow by default.",
 "C: The allowlist goes first, so a protected range always wins over any deny. And the version in the verdict is what lets an auditor answer why a key was served on a given day."])

S(plain("API · fleet state and audit", "ReportApplied and Explain", tr(("fr", "serves FR4"), ("api", "ReportApplied · Explain"), ("ent", "writes NodeState · reads DecisionSample")) +
  wire('<span class="cm">// sent with each poll</span>\nReportApplied {\n  node: "z7-0412",\n  list: "abuse",\n  version: 8361004,\n  ageMs: 1800\n}',
       '<span class="cm">// for audit</span>\nExplain { key: "203.0.113.9",\n          at: "2026-11-03T14:05Z" }\n -> { verdict: DENY,\n      ruleId: 4411,\n      version: 8360990,\n      source: "policy-tool" }')), [
 "C: Fleet state and audit. Every poll carries a report: node, list, the version applied, and the age of that version. The control plane derives skew and lateness from these reports. A node never has to be asked.",
 "C: Explain is the audit call. Given a key and a time, it joins the sampled decision to the rule history by version, and answers: denied, by rule forty-four eleven, in version eight million three hundred sixty thousand nine hundred and ninety, from the policy tool."])

S(plain("API · rollout control", "Rollout, Halt, Rollback, KillSwitch", tr(("fr", "serves FR5"), ("api", "Rollout · Halt · Rollback · KillSwitch"), ("ent", "writes Version stage · Audit")) +
  wire('<span class="cm">// stages: 5 % → 25 % → 100 %</span>\nRollout { version: 8361004, stage: 1 }\nHalt    { version: 8361004, reason: "gate" }\n\n<span class="cm">// a rollback is a NEW, HIGHER version</span>\nRollback { to: 8360990 }\n -> publishes that content as 8361005',
       '<span class="cm">// the kill flag lives in the manifest</span>\nKillSwitch { list: "abuse", on: true }\n\n<span class="cm">// every call is audited, two-person\n// approved above a size, and alerting\n// versions never move backwards</span>') +
  line("A rollback that reuses a version number would make a node ignore it. Versions only go forward.", "r")), [
 "C: Rollout control. Rollout moves a version to a stage. Halt freezes it. Rollback takes the version number you want to return to, and publishes that content as a new, higher version. Never an old number: a node ignores anything not newer than what it has.",
 "C: KillSwitch sets a flag in the manifest itself, so nodes see it within one poll on a channel that does not depend on a new snapshot. Every call is audited, two-person approved above a size, and it alerts."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model. A list contains rules. A rule is published in a version. A version is applied by nodes: each node's state records the version it runs. An allow range protects rules from any deny. An audit event is a weak entity, logged against a list: it only exists in the context of one.",
 "C: One fact matters most: a key has at most one live state per list, and the version of its last change decides it. That is what makes merging safe, in challenge two."], cls="dia")

S(dia("Data · physical model", "What is stored, and where", "erd-physical"), [
 "C: Physically. The rule table is keyed by list and key, with the version it was added in and, if removed, the version it was removed in. A removed row stays for the delta window: a tombstone. The version table holds a number assigned in the same transaction as the rules, a checksum, and the previous checksum.",
 "C: Node state is soft, rebuilt from reports. The allow ranges are kept apart and checked twice, at compile time and at enforcement. On the node, the sorted array, the prefix trie and the filter live in memory, with the current and previous snapshot on disk. The rule store must not be lost or rewound, because version numbers would be reused."], cls="dia")

S(plain("Data · the apply step", "Applying a delta is a merge, not an overwrite",
  '<pre class="code"><span class="cm">// runs on every node, for each change in a delta</span>\n<span class="kw">apply</span>(change c):\n  cur = state[c.key]              <span class="cm">// last version that touched this key</span>\n  <span class="kw">if</span> c.version &lt;= cur.version: <span class="kw">return</span>   <span class="cm">// late, duplicate: no-op</span>\n  state[c.key] = { c.version, c.op, c.action }\n\n<span class="cm">// then build the structure beside the old one,\n// verify the checksum chain, swap one pointer</span></pre>' +
  grade("Naming the per-key version unprompted is a depth signal: arrival order is not intent order. The merge is idempotent and order-independent.")), [
 "C: The apply step is small enough to read whole. For each change in a delta, look at the last version that touched this key. If the change's version is not higher, it is a late or duplicate message: do nothing. Otherwise record it. Then build the structure beside the old one, verify the checksum chain, and swap one pointer.",
 "C: That per-key version is the quiet hero. It makes the merge idempotent and independent of order, which challenge two depends on."])

S(dia("Data · the version chain", "A checksum that covers the one before", "chain"), [
 "C: The version chain. Each version's checksum covers its own content and the checksum of the version before. A node that holds version N-1 and receives the delta to N can verify the chain end to end before applying anything. The shaded band is the delta window: twenty-four hours of deltas. Inside it, a node takes small deltas. Outside it, or when a check fails, one full snapshot."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Simple first. Each version answers the objection to the one before.", [
 "C: Three versions. Each is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("one list file", "every node downloads it", "swap and check locally")), [
 "C: Version one. A policy tool writes one list file into object storage. Every node downloads it every minute, builds a set, swaps it in, and checks each request against it locally. Requests come in at the top, verdicts go out. No objection yet: it is the simplest thing that works, and for a short list that rarely changes it might be enough."], cls="dia")

S(plain("V1 · the objection", "A hundred thousand full downloads, and no way to verify any of them",
  '<pre class="trace"><span class="t">every minute  </span>100,000 nodes × 40 MB = <span class="bad">4 TB</span> from one place\n<span class="t">14:02:11      </span>a node is reading a file that is still being written\n<span class="t">14:02:12      </span><span class="bad">it loads half a list, with no way to know</span>\n<span class="t">14:03:00      </span>a bad file is published: <span class="bad">every node loads it</span>\n<span class="t">next day      </span>auditor: "what was in force at 14:02?" <span class="bad">no version, no answer</span></pre>' +
  '<div class="hedge"><b class="t">Also</b>No catch-up story, no staleness bound, nothing to tell a node what it holds.</div>', red=True), [
 "C: The objection. Every minute, a hundred thousand nodes each pull forty megabytes: four terabytes from one place. A node can read a file while it is still being written, and load half a list without knowing. A bad file reaches every node. And there is no version, so an auditor asking what was in force at two o'clock cannot be answered."], cls="")

S(dia("High-level design · version 2 of 3", "Versions, a rule store, and a relay tree", "base-v2", vtag="V2",
      chip=chips("one version order", "snapshots + deltas", "relay tree", "push + 10 s manifest poll")), [
 "C: Version two answers that. A rule store assigns versions in a single transaction, so there is exactly one order. A compiler turns each version into an immutable snapshot and a delta, with chained checksums, in the origin store. The origin feeds a relay tree. Nodes poll the manifest every ten seconds, the dashed push arrow says a version exists, and the green arrow carries the delta.",
 "C: Now a node can say what it holds, verify what it gets, catch up by small deltas, and never download the whole list on a routine poll."], cls="dia")

S(plain("V2 · how the three arrows between a relay and a node work", "Poll, push, delta", '<div class="cards c3">'
  '<div class="cd"><h3>Poll · every 10 s</h3><p>The node asks the manifest with its version. About 100 bytes. The backstop that always works.</p></div>'
  '<div class="cd amb"><h3>Push · optional</h3><p>The relay says “version N exists”. The node then does the same manifest step at once. It carries no data.</p></div>'
  '<div class="cd grn"><h3>Delta · when behind</h3><p>Small, immutable, verified, applied. A snapshot only to bootstrap or beyond the window.</p></div></div>' +
  line("Push shortens the wait. Poll guarantees arrival. The node's logic is the same for both.", "a")), [
 "C: The three arrows between a relay and a node, because they are easy to confuse. Poll: every ten seconds the node asks the manifest. It always works. Push: the relay tells the node a version exists, and the node immediately runs the same manifest step. The push carries no data. And the delta: the small, immutable file, fetched only when the node is behind.",
 "C: Push shortens the wait and the poll guarantees arrival, and the node's logic is the same for both. That is why I can leave push out in the first release."])

S(plain("V2 · the objection", "One bad version reaches everyone in eighteen seconds", '<div class="cards c2">'
  '<div class="cd red"><h3>Nothing checks the content</h3><p>A typo is as fast as a ban. The pipeline cannot tell them apart.</p></div>'
  '<div class="cd amb"><h3>Nobody decided what stale means</h3><p>A node that cannot update does something, and nobody chose it.</p></div></div>' +
  line("The distribution is correct. The release discipline is missing. That is version three.", "a")), [
 "C: The objection to version two. The distribution is right, and it is fast, and nothing checks the content. A typo travels as quickly as a ban. And a node that cannot update does something, and nobody chose what. Distribution is correct. Release discipline is missing."])

S(dia("High-level design · version 3 of 3", "Safe enforcement: a controller, gates, and a stated policy", "base-v3", vtag="V3",
      chip=chips("atomic swap", "last known good", "staged rollout", "staleness bound")), [
 "C: Version three. The new box is a control plane. It reads every node's applied version and age, the dashed arrow back, and it gates each stage of a rollout through the origin. Inside the rule store, ingest now validates against an allowlist and size limits. On the node, the swap is atomic, the last known good copy is on disk, and a staleness bound has an action.",
 "C: This is the baseline. It stays on screen, and every later picture is a view of it."], cls="dia")

S(plain("V3 · what the node does", "One loop, with a safe failure at every step",
  '<pre class="code"><span class="cm">// every ~10 s, with jitter</span>\nm = manifest(have = version)                     <span class="cm">// ~100 bytes</span>\n<span class="kw">if</span> m.killed: enterKillMode()                   <span class="cm">// honoured in one poll</span>\n<span class="kw">if</span> m.current == version: <span class="kw">return</span>              <span class="cm">// the common case: nothing</span>\nart = (version &gt;= m.minDelta) ? delta(version) : snapshot(m.current)\n<span class="kw">if</span> !verifyChain(art, m.checksum): discard(); report(apply_failed); <span class="kw">return</span>\nnew = buildBeside(current, art)                  <span class="cm">// old list still serving</span>\nswap(new); persist(new); report(applied, age = 0)</pre>' +
  line("Every branch ends serving a good list. A failure never leaves the node worse off.", "a")), [
 "C: The node's loop is short. Ask the manifest. If the kill flag is set, honour it. If already current, do nothing: the common case. Otherwise fetch a delta if inside the window, a snapshot if not. Verify the checksum chain: on failure, discard and report. Build the new structure beside the old, swap, persist to disk, report.",
 "C: Every branch ends with the node serving a good list. A failure never leaves it worse off than before the poll."])

S(plain("V3 · what it leaves open", "The details are where it breaks", '<div class="cards c2">'
  '<div class="cd red"><h3>What V3 has</h3><p>One version order, verified distribution, atomic apply, a controller with gates, a stated stale policy.</p></div>'
  '<div class="cd red"><h3>What it has not been tested against</h3><p>A node two hours behind. Changes out of order. A plausible but wrong rule. No control plane. A list that does not fit. A slow authority. A silent failure.</p></div></div>' +
  line("Seven questions. Each fix creates the next. These are the challenges.", "r")), [
 "C: What version three leaves open. It has one order, verified distribution, atomic apply, a controller with gates and a stated stale policy. It has not been tested against a node two hours behind, changes out of order, a plausible but wrong rule, a lost control plane, a list that does not fit, a slow authority, or a silent failure. Those are the seven challenges, after the flows."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "publish", "FR1: a change becomes a version", "flow-fr1",
     [("fr", "serves FR1"), ("api", "PublishChange"), ("ent", "writes ChangeSet · Rule"), ("nfr", "idempotent")], [
 "C: Requirement one, publish. Step one: an operator sends PublishChange. Step two: ingest normalises every key into a canonical form, so the same range always looks the same. Step three, on the validate box: size limits, a cap on how much address space one change may cover, and a check against the allowlist.",
 "C: A large change waits for a second person. Then one transaction in the rule store writes the rules and takes the next version number, so there is exactly one order, and an audit event is written. The compiler picks it up from there."])
flow(2, "distribute", "FR2: from the origin to every node", "flow-fr2",
     [("fr", "serves FR2"), ("api", "manifest · delta · snapshot"), ("ent", "reads Version"), ("nfr", "30 s for 99.9 %")], [
 "C: Requirement two, distribute. One: the origin fans artifacts out through the relay tree. Two: a push says the new version exists. Three: the node polls the manifest. Four: the delta comes back; the node verifies the chain, builds beside, swaps, writes to disk and reports. A node that never hears the push takes the same steps at its next poll, and so does a node that was offline."])
flow(3, "enforce", "FR3: every request, in microseconds", "flow-fr3",
     [("fr", "serves FR3"), ("api", "Check(key)"), ("ent", "reads the node's structure"), ("nfr", "< 10 µs")], [
 "C: Requirement three, enforce. Step one: the request arrives with a source address. Step two: the agent in the serving process normalises it and checks. The allowlist first, then the exact key, then the longest-prefix range. No network call, no lock, nothing shared.",
 "C: The verdict returns with the rule and the version, and the decision is sampled to a log off the hot path. The request carries on or is refused."])
flow(4, "inspect and explain", "FR4: what is every node running, and why was X denied", "flow-fr4",
     [("fr", "serves FR4"), ("api", "ReportApplied · Explain"), ("ent", "writes NodeState"), ("nfr", "late nodes listed")], [
 "C: Requirement four. Step one: every poll carries the version applied and its age. Step two: the control plane computes version skew and the list of late nodes. Step three: the metrics box turns it into the propagation SLI per region.",
 "C: And for audit: an operator asks Explain with a key and a day, and the sampled decision is joined to the rule history by version. The answer names the rule and the list version in force."])
flow(5, "roll back and stop", "FR5: halt, kill, or revert", "flow-fr5",
     [("fr", "serves FR5"), ("api", "Halt · Rollback · KillSwitch"), ("ent", "writes Version stage · Audit"), ("nfr", "audited")], [
 "C: Requirement five. Step one: an operator, or a gate, halts the stage, so regions not yet reached never receive the bad version. Step two: the control plane tells the origin. A rollback publishes the old content as a new, higher version, and normal distribution carries it.",
 "C: The kill flag is the lighter lever: a field in the manifest that every node reads on its next poll. It is for when a push is bad and the rollback itself needs a minute. Everything is audited."])

S(dia("Design · C4 level 1", "The system in its context", "c4-context"), [
 "C: The C4 context. A policy owner publishes changes. A platform operator handles rollouts, halts and rollbacks. An external authority supplies a bulk list or a lookup. And the serving fleet, a hundred thousand nodes, receives versions and manifests. Notice who owns what: policy owns content, platform owns the pipe. The contract between them is the propagation target."], cls="dia")
S(dia("Design · C4 level 2", "The containers", "c4-containers"), [
 "C: The containers. A policy tool. An ingest service with the rule store. A compiler with the origin storage. The relay tree. A control plane. And, inside each serving process, an enforcement agent: a library that holds the structure, applies updates and answers Check in process. The external authority feeds the rule store by mirror. The serving process calls the agent, with no network between them."], cls="dia")
S(dia("Design · sequence · publish", "From operator to a compiled version", "seq-publish"), [
 "C: Publish as a sequence. One: the operator sends the change with an idempotency key. The ingest service normalises, checks limits and the allowlist, and asks for approval if it is large. Two: one transaction writes the rules and takes version N. Three: the compiler is told N exists, and builds the snapshot and the delta with a checksum chained to N minus one. The operator hears accepted, with the version and rollout stage zero."], cls="dia")
S(dia("Design · sequence · distribute and apply", "Push, manifest, delta, verify, swap", "seq-distribute"), [
 "C: Distribute as a sequence. The relay pushes that version N exists. The node asks the manifest with N minus one. The relay replies: inside the window, here is the delta and its checksum. The node verifies the chain and builds beside the old structure. It swaps one pointer: the old list until that instant, the new one after. It writes the snapshot and version to disk, and reports applied with its next poll."], cls="dia")
S(dia("Design · sequence · enforce", "One request, one verdict", "seq-enforce"), [
 "C: Enforce. A request arrives with an address. The agent normalises it and checks the allowlist: not allowlisted. Exact lookup, then the longest-prefix range lookup. Verdict: deny, rule forty-four eleven, version eight million three hundred sixty-one thousand and four. And, off the hot path, a sample goes to the decision log."], cls="dia")
S(dia("Design · sequence · rollback", "Gate trips, halt, a new higher version", "seq-rollback"), [
 "C: Rollback. A gate sees the canary's block rate eight points over baseline, and halts version N: later stages do not receive it. The operator calls rollback to M. The control plane publishes M's content as version N plus one: higher, never reused. The normal path carries it, and the canary nodes' block rate returns to baseline. Nothing about this needed a special channel, except the kill flag for the first seconds."], cls="dia")

S(plain("Design · what the serving code looks like", "The whole pattern, from the serving side",
  '<pre class="code"><span class="cm">// at server start</span>\nagent = DenyAgent.start(lists = ["abuse", "legal"])\n\n<span class="cm">// on every request, in process</span>\nv = agent.check(request.sourceAddress)\n<span class="kw">switch</span> v.verdict {\n  DENY:      <span class="kw">return</span> refuse(403, v.ruleId)\n  CHALLENGE: <span class="kw">return</span> challenge()\n  ALLOW:     <span class="kw">return</span> next()\n}\nlog.sample(v)                                       <span class="cm">// carries the version</span>\n\n<span class="cm">// and the health endpoint the balancer reads</span>\nhealth = { listAge: agent.ageMs(), ok: agent.age &lt; bound }</pre>'), [
 "C: Last in the design, what the serving code looks like. At start, the agent loads its last known good copy from disk, so a restart with no network still enforces. On every request, one in-process call and a switch on the verdict. The decision is sampled with its version. And the health endpoint reports the list age, which the load balancer reads. That endpoint is how the staleness bound gets an action."])

S(plain("Design · layered rules, in one slide", "Global and regional lists, one pipeline", '<div class="cards c3">'
  '<div class="cd"><h3>One list per layer</h3><p>A global list and a regional list, each with its own versions.</p></div>'
  '<div class="cd amb"><h3>The node holds both</h3><p>A node reads the global list and its own region\'s list. Precedence is fixed: allow beats deny; a more specific range beats a wider one.</p></div>'
  '<div class="cd grn"><h3>Same pipe</h3><p>The same compiler, relays and gates. Only the artifact name and the audience differ.</p></div></div>'), [
 "C: Layered rules, in one slide, because it comes up. A global list and a regional list, each with its own versions. A node reads the global one and the list for its own region, and the precedence is fixed: allow beats deny, and a more specific range beats a wider one. It is the same compiler, the same relays and the same gates. Only the artifact's name and its audience differ."])
