from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Six parts: what a denylist is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here has a theory badge."]); th()

key("Theory · 1 of 6 · what it is", "A <em>versioned</em> set of banned keys, copied to every node, checked <em>without a network call</em>, changed under a <em>release discipline</em>.", [
 "V: A distributed denylist is a versioned set of banned keys, compiled once, copied to every enforcement node, and checked inside the request path without a network call. A change takes effect everywhere within a stated bound, and every decision can be traced to the rule version that made it.", "[pause: 1.0]",
 "C: Each clause is load-bearing. Versioned, so a node can prove what it holds and catch up. Copied to every node, so the check is local. Without a network call, so the list's availability does not multiply into every request's. A stated bound, so staleness is a number someone signed. Traced to a version, so there is an audit."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a rate limiter</h3><p>No counters, no window. The verdict depends on the key alone.</p></div>'
  '<div class="cd"><h3>Not a cache</h3><p>A cache may be wrong by design and refills on a miss. A denylist must hold the whole set.</p></div>'
  '<div class="cd amb"><h3>Not a feature-flag service</h3><p>Same push mechanics. But a wrong flag changes behaviour, and a wrong block drops a customer.</p></div>'
  '<div class="cd red"><h3>Not a firewall</h3><p>It decides on identity, not on content.</p></div></div>'), [
 "C: Four neighbours. It is not a rate limiter: no counters, no window. It is not a cache: a cache can be wrong by design and refills on a miss, but a denylist must hold the whole set, because a miss means allow. It is not a feature-flag service: same push mechanics, but a wrong flag changes a behaviour while a wrong block drops a customer. And it is not a firewall, which decides on content."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> A banned key is served by a node whose list is newer than that ban plus the bound.<br><b>S2</b> An allowlisted or legitimate key is denied because a bad, partial or mis-merged list was applied.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every node applies every published version.<br><b>L2</b> 99.9 % of nodes do so within 30 s.<br><b>L3</b> A node that cannot update is detected, reported and handled by the stale policy.</p></div>'
  '<div class="whyb"><b class="t">Why two safety properties</b>A denylist can be wrong in both directions. Most designs defend S1 and forget S2.</div>'), [
 "V: Safety: a banned key is never served by a node whose list is newer than the ban plus the bound, and a legitimate key is never denied because of a bad or partial list. Liveness: every node applies every version, ninety-nine point nine percent within thirty seconds, and a node that cannot update is detected and handled.", "[pause: 0.8]",
 "C: Notice there are two safety properties, because there are two ways to be wrong. S-one is the missing ban. S-two is the wrong block. Every fix from here says which property it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Freshness against blast radius", "tension"), [
 "C: Here is the central tension. The faster a change reaches every node, the faster a mistake does. And every safeguard that checks a push costs time. On the left, no gates: eighteen seconds to everyone. On the right, a routine push in stages, about ten minutes. In between, an urgent ban: one region first, a short bake.",
 "C: The pipeline cannot tell a ban from a mistake. So the position on this line is a decision, made per push, by its owner. Hold on to that picture. Challenge three lives on it."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "An in-process check on a compact structure", "Latency and independence.", "A sorted array or hash set for single keys, a prefix trie for ranges, held in the server's memory. The request never leaves the process.",
     "A network call on every request, and the list service becoming part of every request's availability.", "The whole set in RAM on every node. Staleness becomes a design parameter instead of a non-issue.", [
 "C: Mechanism one, the in-process check. It protects latency and independence. A sorted array or hash set for single keys and a prefix trie for ranges, in the server's own memory. It rules out a network call on every request, and the list service joining every request's availability. It costs the whole set in memory on every node, and it turns staleness from a non-issue into a design parameter."])
mech(2, "Versioned snapshots and deltas, with checksums", "Convergence and integrity: S1, S2, L1.", "One writer assigns a strictly increasing version. Each version has a snapshot and a delta from the previous one. Each checksum covers its content and the checksum before it.",
     "A node unable to say what it holds, partial or corrupt state, out-of-order application, a full download per change.", "A compile step, a delta log to retain, and two artifact kinds to store.", [
 "C: Mechanism two, versions with checksums. It protects convergence and integrity. One writer assigns a strictly increasing version. Every version has a snapshot and a delta from the one before, and each checksum covers its content and the previous checksum, so they form a chain. It rules out a node that cannot say what it holds, partial or corrupt state, and a full download per change. It costs a compile step, a delta log to retain, and two kinds of artifact to store."], live=False)
mech(3, "A relay tree, push plus a pull backstop", "Propagation speed and resilience: L1, L2.", "Origin, regional relays, zone relays, nodes. A push says a version exists. A ten-second manifest poll is the backstop. Artifacts are immutable and cacheable.",
     "Origin overload, and a missed push leaving a node behind forever.", "More hops add latency. Two paths to build, operate and test.", [
 "C: Mechanism three, a relay tree with push and a pull backstop. It protects propagation speed and resilience. The origin serves a few relays, each relay serves more, and artifacts are immutable so every tier can cache them. A push says a version exists, and a ten-second manifest poll is the backstop. It rules out an overloaded origin and a missed push that leaves a node behind forever. It costs extra hops of latency and two paths to run."])
mech(4, "Atomic swap and a last known good copy on disk", "Safety of the node's serving state: S2.", "Build the new structure beside the old, verify, swap one pointer. Write the verified snapshot and version to disk.",
     "A half-applied list, an empty list after a restart, a crash during an update.", "Two copies in memory briefly. A startup path that must work with no network at all.", [
 "C: Mechanism four, atomic swap and a last known good copy. It protects the node's serving state. Build beside, verify, swap one pointer, and write the verified list to disk. It rules out a half-applied list, an empty list after a restart, and a crash in the middle of an update. It costs two copies in memory for a moment, and a startup path that has to work with no network."], live=False)
mech(5, "Release discipline: gates, a kill flag, rollback", "Safety against bad content: S2.", "Limits and an allowlist at ingest. Stages gated automatically on block rate. A flag in the manifest nodes honour within one poll. A rollback publishes the old content as a higher version.",
     "One mistaken rule reaching the whole fleet at once.", "Minutes of delay for a routine push. An emergency fast path with fewer gates. A gate that must be trusted.", [
 "C: Mechanism five, release discipline. It protects against bad content, which is the over-block. Limits and an allowlist at ingest. Stages gated automatically on the block rate. A kill flag in the manifest that nodes honour within one poll. And a rollback that publishes the old content as a new, higher version. It rules out one mistaken rule reaching everyone at once. It costs minutes of delay on a routine push, and an emergency path with fewer gates."], live=False)
mech(6, "A staleness bound with an explicit action", "Liveness made visible: L3.", "Each list has a maximum age and an action when exceeded, signed by its owner: alert, or drain the node, with a cap.",
     "Silent drift: every node quietly serving an old list for days.", "A policy someone must sign. Capacity lost when nodes drain.", [
 "C: Mechanism six, the staleness bound. It protects liveness by making it visible. Each list has a maximum age and an action when it is exceeded, signed by its owner: alert, or drain the node, with a cap. It rules out silent drift, every node quietly serving an old list for days. It costs a policy someone must sign, and capacity when nodes drain."])
mech(7, "A filter in front, an exact check behind; allow beats deny", "Correct verdicts at scale: S2.", "A compact filter answers “definitely not listed”. A maybe is confirmed by an exact tier. An allowlist range overrides any deny.",
     "A false positive blocking a real user. A wrong range overriding a protected one.", "A second tier for confirmation. Precedence rules to explain and to test.", [
 "C: Mechanism seven, a filter in front and an exact check behind, with allow beating deny. It protects correct verdicts at scale. A compact filter answers definitely not listed. A maybe is confirmed by an exact tier. And an allowlist range overrides any deny. It rules out a false positive blocking a real user, and a wrong range overriding a protected one. It costs a second tier for confirmation, and precedence rules to explain and test."], live=False)

S(plain("Theory · 5 of 6 · the options, part one", "Three ways that look cheap", table(["Approach", "Latency", "Independent of the list service?", "Fails when"], [
  ("rej", ["A · A central lookup per request: a shared cache or database on the path", "~1 ms", "no", "the store is down, or 1 M lookups a second arrive; every request pays the trip"]),
  ("rej", ["B · Each node downloads the whole list on a timer", "µs", "yes", "100,000 full downloads (4 TB); a partial or corrupt file; one bad file reaches everyone; no versions"]),
  ("rej", ["C · A push-only stream of changes: pub/sub", "µs", "yes", "a node misses messages with no way to catch up; ordering and duplicates; no integrity check"])], "bt sm mx")), [
 "C: Now the options. Six approaches, each with the failure that rules it out. Three that look cheap first.",
 "C: A, a central lookup on every request: always fresh, but a millisecond on every call, the list service in everyone's availability, and a million lookups a second. B, each node downloads the whole list on a timer: four terabytes at this scale, and a corrupt file looks like a good one.",
 "C: C, a push-only stream. Fast and cheap. But a node that misses messages has no way to catch up, ordering and duplicates are your problem, and there is no integrity check."], cls="theory")

S(plain("Theory · 5 of 6 · the options matrix", "Six approaches, one pick", table(["Approach", "Latency", "Freshness", "Independent?", "Ops", "Fails when"], [
  ("rej", ["A · Central lookup per request", "~1 ms", "instant", "no", "low", "store down; 1 M lookups/s"]),
  ("rej", ["B · Whole list on a timer", "µs", "interval", "yes", "very low", "4 TB; corrupt file; no versions"]),
  ("rej", ["C · Push-only stream", "µs", "seconds", "yes", "medium", "missed message, no catch-up"]),
  ("pick", ["D · Versioned snapshots + deltas, relay tree, push + pull, local check, staged rollout", "µs", "seconds to ~18 s", "yes", "medium to high", "set no longer fits; a wrong rule that validates"]),
  ("rej", ["E · Local filter + remote check on a hit", "µs miss, ~1 ms hit", "as D", "partly", "high", "high hit rate (an attack); tier down"]),
  ("rej", ["F · The edge provider's own IP-set feature", "µs", "provider-defined", "yes", "very low", "entry limits; key types; layers; audit; unmeasurable propagation"])], "bt sm mx")), [
 "C: Here are all six. D is a versioned snapshot plus deltas, a relay tree, push with a pull backstop, a local check and a staged rollout. It fails when the set no longer fits on a node, which adds row E, and when a wrong rule passes validation, which is challenge three.",
 "C: E is a local filter with a remote check on a hit. It fails when the hit rate is high, as in an attack. F is the edge or C-D-N provider's own I-P-set feature: almost no work, and it fails on entry limits, key types, layered rules, audit detail, and propagation I cannot measure.",
 "V: I pick D, after checking whether F is enough.", "[pause: 0.8]"], cls="theory")

S(plain("Theory · 5 of 6 · the pick, and what it gives up", "D, with F checked first and E held in reserve", '<div class="cards c2">'
  '<div class="cd grn"><h3>What the pick buys</h3><p>Auditable verdicts, layered rules, extra key types, a propagation number I can measure, and a design that needs nothing from the request path.</p></div>'
  '<div class="cd red"><h3>What it gives up</h3><p>Instant effect: a bounded delay instead. Memory on every node. And a distribution plane to build and run.</p></div></div>' +
  line("Check F first: if the provider's feature fits the limits, buy it and build only the audit.", "a")), [
 "C: What the pick gives up, said plainly. Instant effect: a bounded, measured delay instead. Memory on every node. And a distribution plane to build, run and be paged for. What it buys: auditable verdicts, layered rules, extra key types, a propagation number I can measure, and a request path that depends on nothing else.",
 "C: And before any of it I check row F. If the provider's feature fits my limits and my propagation needs, I buy it and build only the audit around it."], cls="theory")

S(plain("Theory · 5 of 6 · row F, honestly", "Is the provider's feature enough?", '<div class="cards c3">'
  '<div class="cd grn"><h3>Ask these</h3><p>Entry limit against our 10 M. IPv6 and ranges. How fast a change lands, and can we measure it. A second key type.</p></div>'
  '<div class="cd amb"><h3>Often missing</h3><p>Per-decision audit with a version. Layered regional rules. A staged rollout we control. An allowlist that always wins.</p></div>'
  '<div class="cd"><h3>The honest answer</h3><p>If every answer fits, buy. Build only the rule store, the audit and the gates around it.</p></div></div>'), [
 "C: Row F deserves a straight answer, because candidates skip it. Ask four things: does the entry limit cover ten million, and a hundred million later? Does it handle ranges and I-P-v-six? How fast does a change land, and can I measure it? Can it carry a second key type?",
 "C: What is often missing: a per-decision audit with a version, layered regional rules, a staged rollout I control, and an allowlist that always wins. If everything fits, I buy it and build the rule store, the audit and the gates around it. If not, I build D."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue, part one", "What will go wrong", table(["#", "Failure", "Becomes"], [
  ["F1", "A node is offline or behind; an update is corrupt or truncated", "<b>Challenge 1</b>"],
  ["F2", "Add and remove arrive out of order or twice; ranges overlap", "<b>Challenge 2</b>"],
  ["F3", "A bad rule: a too-wide range, a typo, a wrong merge", "<b>Challenge 3</b>"],
  ["F4", "The distribution plane is down, or a node is partitioned", "<b>Challenge 4</b>"]], "bt sm")), [
 "C: Last part, the failure catalogue, which becomes the challenge list. F-one, a node is offline or behind, or an update is corrupt: challenge one. F-two, add and remove arrive out of order or twice, or ranges overlap: challenge two. F-three, a bad rule: challenge three. F-four, the distribution plane is down or a node is partitioned: challenge four."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue, part two", "What will go wrong, continued", table(["#", "Failure", "Becomes"], [
  ["F5", "The list outgrows a node; IPv6; a filter's false positive; a hit storm", "<b>Challenge 5</b>"],
  ["F6", "The source is a slow, rate-limited authority; a new /16 against cached verdicts", "<b>Challenge 6</b>"],
  ["F7", "Nobody notices a ban that did not land, or a block that should not exist", "<b>Challenge 7</b>"],
  ["F8", "An operator mistake in the console", "two-person approval and audit, on the API slides"],
  ["F9", "A restart with no network", "last known good on disk, in the flows"]], "bt sm")), [
 "C: F-five, the list outgrows a node: challenge five. F-six, the source is a slow authority: challenge six. F-seven, nobody notices: challenge seven. F-eight, an operator mistake in the console, I handle with two-person approval and an audit trail, on the A-P-I slides. F-nine, a restart with no network, is last known good on disk, in the flows. Seven challenges, in that order."], cls="theory")

S(plain("Theory · what each mechanism serves", "Safety or liveness, never both unnamed", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 In-process check", "latency, independence", "flows, challenge 5"],
  ["M2 Versions + checksums", "<b>S1, S2, L1</b>", "challenges 1 and 2"],
  ["M3 Relay tree, push + pull", "L1, L2", "challenges 1 and 7"],
  ["M4 Atomic swap, last known good", "S2", "challenges 1 and 4"],
  ["M5 Release discipline", "<b>S2</b>", "challenge 3"],
  ["M6 Staleness bound", "L3", "challenge 4"],
  ["M7 Filter + exact + allow wins", "S2", "challenges 5 and 6"]], "bt sm") +
  grade("Every mechanism must name the property it protects. A mechanism with no stated property is decoration.")), [
 "N: Good theory has a consequence for the design. Look at this table: every mechanism names the property it serves, and where it will be used.",
 "C: That is the vocabulary. On to the design."], cls="theory")
