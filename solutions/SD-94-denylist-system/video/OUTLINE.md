- [x] outline approved  - [x] design  - [x] diagrams  - [x] slides  - [x] script  - [x] video  - [x] publish

# SD-94 · Blocking / denylist system — reference-solution video outline

Target level: staff (manager layer AUX) · Target length: 86 min (75–90) · Word budget: 11,437 (≈ minutes × 133)

Generic content only: no employer, vendor, product or currency. Costs are in engineer-months with an illustrative loading. Every number
below is arithmetic from stated inputs and carries a label.

## Thesis and definition

- **Thesis** (one sentence, key-line voice): *The check must be local and the list cannot be, so the design is the distance
  between them: a version that every node can verify, a stated bound on how stale a node may be, and a push discipline that treats a
  bad rule as the outage.*
- **Definition to say aloud**: *A distributed denylist is a versioned set of banned keys, compiled once, copied to every enforcement
  node, and checked inside the request path without a network call. A change takes effect everywhere within a stated bound, and
  every decision can be traced to the rule version that made it.* Load-bearing clauses: **versioned** (so a node can prove what
  it holds and catch up), **copied to every node** (the check is local), **without a network call** (the list's availability must
  not multiply into every request's), **a stated bound** (staleness is a number someone signed), **traced to a version** (audit).
- **Hook** (why it is harder than it looks): The lookup is a hash set; anyone can write it in an afternoon. What is hard is
  everything around it. The same pipe that delivers a ban to 100,000 nodes in ten seconds delivers a mistake to 100,000 nodes in
  ten seconds. A wrong rule is a fleet-wide outage with no failed deployment to blame. And the list has two ways to be wrong: a ban
  that is missing, and a block that should not exist. The question tests whether you separate the microsecond check from the slow,
  partly broken distribution path, and whether you say the staleness bound and the failure policy out loud.

## 0 · What this question grades

| Axis | Weak signal | Strong signal |
|---|---|---|
| Requirements | Starts with "a table of IPs and a cache"; never asks who owns the list, what a late ban costs, or what a wrong block costs | Asks how fast a change must apply, what is enforced where, who decides the failure policy; separates **missing ban** from **wrong block** before drawing |
| Correctness | One shared store queried per request; no versions; "eventually consistent" with no number | States the staleness bound, gives every update a version and a checksum, handles out-of-order add and remove, explains why a filter's hit must be confirmed |
| Trade-offs | Names a product and a protocol | Options matrix with the failure that rules each row out; picks and says what the pick gives up; asks whether the edge provider's own feature is enough |
| Depth | Stops at "push the list to the nodes" | Two levels down: delta log retention against snapshot size, why versions only move forward even on rollback, per-key versions and tombstones, longest-prefix match, memory arithmetic for IPv6 |
| Operations | Watches CPU and error rate | Propagation lag and version skew as the SLI, a synthetic banned probe per region, block-rate anomaly as the halt signal, staged pushes, a kill switch, a named owner for the policy and another for the mechanism |

## 1 · Requirements and scope

- **Clarifying questions and the interviewer's answers** (asked aloud, six):
  1. *Who owns the list, and who calls the check?* — A policy team (security, legal) owns the content; the platform team owns the
     mechanism. The check runs on every serving node: about 100,000 nodes in 20 regions, on the request path.
  2. *What is banned?* — Network addresses first: single IPv4 and IPv6 addresses and ranges (CIDR). "A second key type, a user id,
     will come; do not design it out."
  3. *How big, how fast does it change?* — 10 million entries today, perhaps 100 million later; about 5 changes a second on
     average, 50 a second in a burst. 1 million requests a second at peak across the fleet.
  4. *How fast must a ban take effect?* — "Within 30 seconds for 99.9 % of nodes." Removals follow the same rule.
  5. *What if a node cannot get updates?* — "That is yours to propose. I will decide who signs it." (This seeds the staleness
     policy and challenge 4.)
  6. *Where does the list come from?* — Mostly an internal tool; one list is mirrored from an external authority that publishes a
     daily bulk file. "A variant has only a slow lookup API. Tell me what you would say." (Seeds challenge 6.)
- **Functional requirements** (each gets a numbered flow later):
  - FR1 · **Publish** a change (add or remove a key or range, with a reason, a source and an optional expiry), validated, audited. Sources: the
    policy tool, a detection system's fast path, and a mirrored external list; conflicts between sources resolve by a stated precedence.
  - FR2 · **Distribute** every change to every node within the bound; a node that was offline catches up on its own.
  - FR3 · **Enforce**: a verdict (allow or deny) for each request, inside the request path, in microseconds.
  - FR4 · **Inspect and explain**: which version each node runs and how old; why was key X denied or served on day D.
  - FR5 · **Roll back and stop**: halt a rollout, kill a list, revert to the previous version, with an emergency fast path. Audited.
- **Non-functional requirements, with numbers** (all initial targets, not measurements):
  - Check: p99 under 10 µs in-process; **no network call** on the request path.
  - Propagation: 99.9 % of nodes on a new version within 30 s of publish; the remaining 0.1 % flagged, not silent.
  **Poll semantics, stated once and kept:** every 10 s a node asks the **manifest** (about 100 bytes: current version, delta window, checksum).
  If it is already current, that is the whole exchange. If it is behind and inside the retention window it fetches **deltas**. It fetches a
  **full snapshot only to bootstrap or after falling outside the window**, never on a routine poll.
  - A node keeps enforcing its last known list through any outage of the distribution plane.
  - Staleness is **bounded and signed**: a per-list maximum age, after which a stated action fires.
  - Every change and every decision carries a version; an auditor can reconstruct a verdict.
  - A bad push is caught by the pipeline, not by customers.
- **IN scope / OUT of scope**:
  - IN: address and range keys (v4 and v6), a second key type as an extension, global and regional layers, an allowlist of ranges that
    must never be blocked, ingest from an internal tool and an external mirror, staged rollout, audit, operator console.
  - OUT, on purpose: detecting abuse (a model or rules engine; that is a different question, SD-43); rate limiting (SD-25);
    absorbing a volumetric attack (network scrubbing upstream); content rules inside requests (a web firewall); an appeals product
    for blocked users (an owner and a workflow, named, not drawn).
  - Said aloud: **an address is not a person.** A shared or carrier-grade-NAT address can hold thousands of legitimate users; one
    wrong range blocks all of them. This is why there is an allowlist and why removals matter as much as adds.
- **"The core is 4 things"**: a *versioned list* compiled in one place, a *distribution path* that can be verified and resumed, a
  *local check* with no network call, and a *rollout discipline* that treats the list as code.

## 2 · Estimates

Every number is arithmetic from the stated inputs, and carries a label.

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Request rate per node | 1,000,000/s ÷ 100,000 nodes = 10/s average per node | given | The check is not a CPU problem; the reason to keep it local is latency and **independence**, not throughput |
| A remote check on the path | Each request waits ~1 ms for a network round trip; 1 M/s becomes **1 M lookups/s** on one service; availability 99.99 % × 99.99 % ≈ 99.98 % | illustrative | Rules out "one shared lookup per request": it makes the list service the biggest dependency in the company |
| One exact lookup | Sorted array of 10 M: log₂(10⁷) ≈ 24 comparisons ≈ **0.3–1 µs** with cache misses | illustrative, **to be measured** | The check fits inside a 10 µs budget with room to spare |
| Exact IPv4, memory | 10 M × 4 B = **40 MB** sorted array; a hash set at 8 B and 1.5× load ≈ 120 MB | derived | The whole list fits in RAM on every node |
| Filter, if used | 10 M × 10 bits = 12.5 MB for ~1 % false positives | derived | Not needed at 10 M (the exact set is only 40 MB). It matters at 100 M (below) |
| Ranges (prefix trie) | ~2 M ranges × ~40 B ≈ **80 MB** | illustrative | Longest-prefix match is a different structure from exact keys |
| 100 M IPv6 entries | 100 M × (16 B address + 1 B length) = **1.7 GB** exact; Bloom at 10 bits = **125 MB** | derived | The exact set no longer fits the memory budget (say 512 MB); a filter does, and a hit needs an authoritative check. Challenge 5 |
| Change volume | 50/s × 30 B ≈ **1.5 KB/s** of deltas; 2 hours offline = 7,200 s × 50 × 30 B ≈ **11 MB** | illustrative | A delta is far smaller than a snapshot, so catch-up by deltas wins |
| Delta against snapshot | Break-even 40 MB ÷ 30 B ≈ 1.33 M changes ≈ 7.4 h at the 50/s burst rate; keep **24 h** of deltas: 86,400 × 50 × 30 B ≈ **130 MB** | illustrative | Retention window for the delta log; beyond it a node takes a full snapshot |
| Fan-out | 100,000 nodes × 40 MB snapshot = **4 TB** if every node pulls from the origin. Relay tree: origin → 20 regional → 200 zone relays (500 nodes each): the origin serves 20 × 40 MB = 800 MB | derived | The tree is not optional; it also bounds the load on the origin |
| Poll load | 100,000 nodes ÷ 10 s = **10,000 manifest polls/s**; a "no change" answer is ~100 B ≈ 1 MB/s; 50 polls/s on each zone relay. A poll never downloads the list: deltas only when behind inside the window, a snapshot only to bootstrap or beyond the window | illustrative | Polling every 10 s is cheap enough to be the backstop, and is itself a valid phase-1 design |
| Propagation budget (30 s) | compile 3 s + origin→regional 2 s + regional→zone 2 s + push 1 s + verify and apply 1 s = **9 s** with push; with pull only, worst case adds a 10 s poll: **18 s**; spare 12 s | initial target | Pull-only already meets the SLO; push buys margin. A 60 s poll would not (68 s) |
| Memory swap | Build the new structure beside the old, then swap one pointer: 2 × 40 MB = 80 MB briefly | derived | Atomic swap; no half-applied list |
| External lookup API | 20,000 first-seen addresses/s at peak against a 100 calls/s limit = **200× over**; 100/s × 86,400 = 8.6 M lookups a day against ~50 M distinct addresses a day = **17 %** coverage | illustrative | The API cannot be the path; it can feed a cache for the highest-volume addresses. Challenge 6 |
| Blast radius of a bad push | All 100,000 nodes apply within 18 s. A rule that blocks 8 % of traffic is visible within one 10 s metrics window on a 5 % canary: 5,000 nodes | illustrative | Gate on block rate per node against baseline; staged push: 5 % → 25 % → 100 %, 5 min bake each ≈ 10 min planned |
| Propagation SLO as a budget | 99.9 % of 100,000 nodes = 99,900; **100 nodes** may be late; each late node is listed with its age | initial target | The SLI is the fraction on the current version, per region |

## 3 · Theory

1. **Is / is not.**
   - Is: a versioned set of banned keys, copied to every enforcement node, checked locally, changed under a rollout discipline.
   - Is not a **rate limiter** (it has no counters and no window; the verdict depends on the key only), not a **cache** (a cache can
     be wrong by design and refills on a miss; the denylist must hold the whole set), not a **feature flag service** (the same
     push mechanics, but a wrong flag changes a behaviour; a wrong block drops a customer), not a **firewall** (it decides on
     identity, not on content). It is a **replicated read-mostly dataset** with a safety-critical rollout.
   - Two ways to be wrong run through the video: a **missing ban** (under-block) and a **wrong block** (over-block).
2. **Safety (must never happen):** S1 · a request from a banned key is served by a node whose list is newer than that ban plus the
   bound. S2 · a request from an allowlisted or legitimate key is denied because a bad, partial or mis-merged list was applied.
   **Liveness (must eventually happen):** L1 · every node applies every published version, in order or by snapshot. L2 · 99.9 % of
   nodes do so within 30 s. L3 · a node that cannot update is detected, reported and handled by the stale policy. Each later fix is
   tagged with the property it serves.
3. **Central tension:** **freshness against blast radius.** The faster a change reaches every node, the faster a mistake does, and a
   safeguard that checks a push costs time. Picture: one timeline: publish, canary bake, wider bake, all nodes; with a slider that
   trades speed for the detection window. An emergency ban and a routine cleanup deserve different positions on it.
4. **Mechanisms** (7). Form per slide: property → how → failure ruled out → cost.

   | Mechanism | Protects | Rules out | Costs |
   |---|---|---|---|
   | **M1 In-process check on a compact structure** (sorted array or hash set for keys, prefix trie for ranges) | Latency and independence | A network call on every request; the list service becoming part of every request's availability | The whole set in RAM per node; staleness is now a design parameter |
   | **M2 Versioned immutable snapshots plus ordered deltas, with checksums** | Convergence and integrity (S1, S2, L1) | A node unable to say what it holds; partial, corrupt or out-of-order state; a full re-download per change | A compile step; delta retention; two artifact kinds to store |
   | **M3 Relay tree with push and a pull backstop** | Propagation speed and resilience (L1, L2) | Origin overload; a missed push leaving a node behind forever | More hops add latency; two paths to operate and test |
   | **M4 Atomic swap and last-known-good on disk** | Safety of the node's serving state (S2) | A half-applied list; an empty list after a restart; a crash during update | Two copies in memory briefly; disk and a startup path that must work with no network |
   | **M5 Validation, staged rollout, kill switch and one-step rollback** | Safety against bad content (S2) | A mistaken rule reaching the whole fleet at once | Minutes of delay for routine pushes (an emergency fast path with fewer gates); a human or an automated gate in the loop |
   | **M6 Staleness bound with an explicit action** | Liveness made visible (L3) | Silent drift; every node quietly serving an old list for days | A policy someone must sign; draining capacity when a node exceeds the bound |
   | **M7 Filter in front, exact check behind; allow beats deny** | Correct verdicts at large scale (S2) | A false positive blocking a real user; a wrong range overriding a protected one | A second tier for confirmation; precedence rules to explain and test |

5. **Options matrix** (rows = approaches; columns = deciding properties; last column = fails when).

   | Approach | Check latency | Freshness | Independent of the list service? | Ops burden | Fails when |
   |---|---|---|---|---|---|
   | A · Central lookup per request (shared cache or database on the path) | ~1 ms | Instant | No | Low | The store is down, or 1 M lookups/s arrive; every request pays the round trip |
   | B · Each node downloads the whole list on a timer | µs | Interval | Yes | Very low | 100,000 full downloads (4 TB); a corrupt or partial file; one bad file reaches everyone; no versions |
   | C · Push-only stream of changes (pub/sub) | µs | Seconds | Yes | Medium | A node misses messages with no way to catch up; ordering and duplicates; no integrity check |
   | **D · Versioned snapshot plus deltas, relay tree, push with pull backstop, local check, staged rollout** | µs | Seconds to ~18 s | Yes | Medium to high | The set no longer fits on a node (then add row E); a wrong rule that passes validation |
   | E · Local filter plus a remote authoritative check on a hit | µs on a miss, ~1 ms on a hit | As D | Partly | High | The hit rate is high (an attack makes every request a hit); the remote tier is down |
   | F · The edge or CDN provider's own IP-set feature | µs | Provider-defined | Yes | Very low | Entry limits; key types it lacks; layered regional rules; audit detail; propagation you cannot measure |

   **Pick: D**, after checking **F** (buy before build); **E** is an extension for the very large case, not a start. Rows A, B, C, E,
   F stay on screen, greyed, with their failures.
   **Gives up:** instant effect (a bounded, measured delay), memory on every node, and a distribution plane to build and run. The
   pick of D over F buys auditability, key types and layering, and costs a platform team.
6. **Failure catalogue** (becomes the challenge list):
   - F1 node offline or behind, a corrupt or truncated update → **C1**
   - F2 add and remove out of order or duplicated; overlapping ranges → **C2**
   - F3 a bad rule: a too-wide range, a typo, a wrongly merged list → **C3** (crux, part 1)
   - F4 the distribution plane is down or a node is partitioned → **C4** (crux, part 2)
   - F5 the list outgrows a node; IPv6; a filter's false positive; a hit storm → **C5**
   - F6 the source is a slow, rate-limited authority; a new /16 against cached verdicts → **C6**
   - F7 nobody notices a ban that did not land, or a block that should not exist → **C7**
   - F8 an operator error in the console: covered by audit and two-person approval on the API slides, not a challenge
   - F9 a restart with no network: last-known-good on disk (M4), covered in flows

## 4 · API and entities

| API | Serves | Reads / writes | Wire-format notes |
|---|---|---|---|
| `PublishChange(list, ops[{op, key, kind, reason, source, expiresAt}], idempotencyKey)` → `{changeSetId}` | FR1 | writes **ChangeSet**, **Rule** | `op` is add or remove; the idempotency key makes a retried publish harmless; two-person approval above a size threshold |
| `GET /manifest?list&have=V` → `{current, minDelta, deltaRef?, snapshotRef, checksum}` | FR2 | reads **Version** | Tiny, cacheable for a second; says whether `V` is still inside the delta window |
| `GET /delta?list&from=V` and `GET /snapshot/{version}` | FR2 | reads **Version** artifacts | Immutable and content-addressed, so every relay can cache them forever; delta ops carry a per-key version |
| In-process `Check(key)` → `{verdict, ruleId, version}` | FR3 | reads the node's structure | **Not a network API.** The version is returned so the decision log can say which list decided |
| `ReportApplied(node, list, version, ageMs)` | FR4 | writes **NodeState** | Sent with the poll; the control plane derives skew and lag from it |
| `Explain(key, atTime)` | FR4 | reads **DecisionSample**, **Rule** history | For audit; answers "was this key denied on day D, by which version" |
| `Rollout(version, stage)`, `Halt(version)`, `Rollback(toVersion)`, `KillSwitch(list)` | FR5 | writes **Version** stage, **AuditEvent** | A rollback publishes the old content as a **new, higher** version; versions never move backwards |

**Conceptual model** (Chen view): **List** 1—N **Rule** (key, kind, action, reason, source, expiry); **ChangeSet** 1—N **Rule**
change; **Version** 1—1 **Snapshot** and 1—1 **Delta**, each with a checksum chained to the previous version; **Node** 1—N
**NodeState** (applied version, age); **AllowRange** protects keys from any deny; **AuditEvent** records publishes, rollouts and
rollbacks; **DecisionSample** records a sampled verdict with its version.

**Physical** (rule store: relational with transactional writes; artifacts in object storage; node structures in memory):

- `rule(list_id, key_bytes, kind, action, added_version, removed_version NULL, reason, source, expires_at)`; key `(list_id, key_bytes)`.
- `version(list_id, n, checksum, prev_checksum, snapshot_ref, delta_ref, stage, created_at)`; key `(list_id, n)`; `n` is a 64-bit counter,
  assigned by the rule store's transaction, so there is one order.
- `node_state(node_id, list_id, version, applied_at)`: soft state, rebuilt from reports.
- On the node: a sorted array and a prefix trie in memory; on disk the current and previous snapshot and a small `version` file.
- Tombstones: a removed key keeps its row for at least the delta window so a late delta cannot resurrect it.

## 5 · High-level design

| Version | Adds | Objection it answers | Objection it leaves |
|---|---|---|---|
| V1 | The policy tool writes one list file to object storage; each node downloads it every minute, builds a set, swaps it in, and checks locally | (none: simplest thing that works) | 100,000 full downloads a minute (4 TB); a node cannot tell a corrupt or partial file from a good one; no version, so no catch-up and no audit; one bad file reaches everyone |
| V2 | **Versions and distribution**: a rule store assigns versions; a compiler produces immutable snapshots and ordered deltas with chained checksums; a relay tree (origin, regional, zone); push notification with a 10 s **manifest** poll as backstop (deltas inside the window, a snapshot only to bootstrap); nodes report the applied version | "A full download per node per change is 4 TB, and a node cannot verify what it got or catch up after an outage" | One bad version reaches every node in 18 s; nothing validates content; a node that cannot update has no policy; a restart with no network has nothing to serve |
| V3 | **Safe enforcement**: atomic swap, last-known-good on disk, validation with an allowlist, staged rollout with gates, kill switch, rollback by new version, a staleness bound with an action, a decision log | "A wrong rule goes everywhere at once, and a stale node does something nobody chose" | The details: the catch-up edge cases, ordering and overlap, a legitimately formed but wrong rule, a very large list, a slow external source. These are challenges 1–7 |

Baseline spine, left to right: **Policy tool → Ingest and validate → Rule store → Compiler → Origin store → Regional relay → Zone relay →
Enforcement node (local structure)**, with the **Request** entering the node on the right and a **Control plane** (rollout, gates,
fleet state) along the bottom that observes the nodes and drives the stage. Boxes that appear only in a challenge carry a tag: `ch1`
manifest and snapshot fallback; `ch2` per-key versions and tombstones; `ch3` validation, allowlist, canary, kill switch; `ch4`
last-known-good and the drain action; `ch5` filter and authoritative lookup tier; `ch6` external authority adapter and verdict cache;
`ch7` metrics, probes and the decision log. Colours by role as in GUIDELINES §7.

Flows, one per functional requirement (numbered arrows, narration uses the numbers):

- **FR1 Publish:** 1 operator `PublishChange` · 2 ingest normalises (canonical CIDR, v6 forms) · 3 validate: size limit, allowlist, schema ·
  4 approval above a threshold · 5 commit rows and assign version N in one transaction · 6 audit event.
- **FR2 Distribute:** 1 compiler builds snapshot N and delta N-1→N, with checksum · 2 upload to origin · 3 rollout stage allows region
  group · 4 push "N exists" to relays and nodes · 5 node asks the manifest with `have=N-1` · 6 fetches the delta from its zone relay ·
  7 verifies the checksum chain · 8 builds the new structure beside the old · 9 swaps one pointer · 10 writes the `version` file and
  reports applied N. Backstop: the same steps start from a 10 s manifest poll; the poll fetches nothing else unless the manifest shows the node is behind.
- **FR3 Enforce:** 1 request arrives with a source address · 2 normalise · 3 check the allowlist first · 4 exact lookup · 5 range
  lookup (longest prefix) · 6 verdict and version returned · 7 decision sampled to the log, off the hot path.
- **FR4 Inspect and explain:** 1 node reports `(version, age)` with each poll · 2 control plane computes skew and the late list ·
  3 operator asks `Explain(key, day)` · 4 decision sample and rule history joined by version · 5 answer names the rule and the version.
- **FR5 Roll back and stop:** 1 gate trips or operator calls `Halt` · 2 stage frozen; unfinished regions do not receive N · 3
  `Rollback(to M)` publishes M's content as version N+1 · 4 normal distribution carries it · 5 kill switch: a flag in the manifest
  itself that nodes honour within one poll · 6 audit.

C4 and sequence views that follow: context; container (policy tool, ingest, rule store, compiler, origin, relays, enforcement node,
control plane); sequences for publish, distribute-and-apply, enforce, and rollback. Challenge sequences are added in each challenge.

## 6 · Bridge and challenge map

*It works. Where does it break first?* The carried baseline with seven attack points marked: a node behind (C1), changes out of
order and overlapping (C2), a wrong rule (C3), no updates at all (C4), a list too big for a node (C5), a slow external source
(C6), and the silent failure (C7). Spoken line: "every fix creates the next question."

## 7 · Challenges

Seven, ordered so that each fix creates the next question. Correctness: C2, C3. Failure recovery: C1, C4. Overload and scale: C5,
C6. Observability: C7. The crux (the staleness bound and the failure policy, and the bad push) gets two: C3 and C4.

### Challenge 1 · The node that was offline  *(failure recovery)*

- Q (interviewer): "A node was offline for two hours. How does it catch up? And how do you know all one hundred thousand nodes run
  version N?"
- Naive answer: "On reconnect it downloads the whole list again, and we check each node's file."
- Case (IDs, times, numbers): Node `z7-0412` last applied version 8,000,000 at 02:00; at 04:00 the list is at 8,360,000. A full
  download is 40 MB; the 360,000 changes in between are ≈ 11 MB. Fifty nodes in the zone reconnect together: 50 × 40 MB = 2 GB from
  one relay at once. And a truncated download, a power cut mid-write, leaves a half-file the node would load.
- Break (which box): the arrow from the zone relay to the node, dashed red: nothing says what the node should fetch or whether what it
  got is whole.
- Fix (mechanism) · sequence? code?: **Manifest, delta window, snapshot fallback, chained checksums.** The node sends `have=V`; the
  manifest says "inside the window: take the delta" or "outside: take snapshot N". Each version's checksum covers its content and the
  previous checksum, so a node verifies **before** applying, and on mismatch discards and takes a full snapshot. The new structure is
  built beside the old and swapped. Sequence: reconnect, manifest, delta, verify, swap, report.
- Why it works (property): **Convergence (L1) and integrity (S2).** A node can always reach the current version: by a small delta
  if it is recent, by a snapshot if it is not. It never serves a state it has not verified.
- "What if the fix fails?": "The delta window is 24 hours and the node was down for three days. Or the checksum fails again on the
  snapshot."
- Second fix or honest limit: Beyond the window the manifest returns the snapshot and the node, whatever its age, takes it (zone relays
  cache it so fifty nodes cost one origin fetch). A repeatedly failing checksum means a corrupt artifact at the origin: the node
  keeps its last known good, reports `apply_failed`, and the control plane halts that version. Honest limit: a node that cannot reach
  anything keeps an old list, and that is **challenge 4**. The fleet answer to "is everyone on N" is the reported applied version,
  not a hope: skew is a metric.
- If asked, I'd say: "Every version has a number and a checksum chained to the one before. A node says what it has; the manifest says
  whether a small delta or a full snapshot gets it to the present. It verifies before it applies and swaps atomically, so it never
  serves a half-built list. And I know the fleet is converged because every node reports the version it runs."

### Challenge 2 · Order, duplicates and overlap  *(correctness)*

- Q (interviewer): "An add and a remove for the same key arrive in the wrong order. Or the same delta arrives twice. And an
  operator adds a /16 and removes one /24 inside it."
- Naive answer: "Apply changes in the order they arrive; hope the network is in order."
- Case (IDs, times, numbers): Key `203.0.113.9`: version 100 add, version 101 remove (the ban was a mistake). The node, through two
  relays, sees 101 and then 100: the final state is **banned**, though the last intent was **removed**. A duplicate of 100 after 101
  does the same. Separately: at version 90 add deny `198.51.0.0/16`; at 97 add allow `198.51.100.64/26` (a partner's range inside it). What is the verdict for
  `198.51.100.70`? A node that stops at the first range it finds says deny. Two sources disagree about one key: the precedence is written down (an operator's
  allow beats an automated deny; an unexpired manual entry beats a feed).
- Break (which box): the node's apply step, dashed red: it believes arrival order is intent order.
- Fix (mechanism) · sequence? code?: **One total order and per-key versions.** The rule store's transaction assigns the version, so
  there is one order. Each rule carries `added_version` and `removed_version`; applying a change is "set this key's state if the change's
  version is **greater** than the version the key last had". Replays and reordering become no-ops. Tombstones keep removed keys
  for the delta window. For ranges: longest-prefix match decides; **allow beats deny at equal specificity**; and the compiler
  expands an exception inside a range into explicit entries so the node needs no special case. Code: the apply function, ten lines.
- Also decided here: **expiry is a command, not a node-side clock.** A ban with `expiresAt` is turned into an explicit remove by the compiler at that time,
  with its own version, so every node sees the same history and none depends on its own wall clock.
- Why it works (property): **Convergence to the intended state (L1, S1, S2).** The result depends only on the set of changes, not on
  their order or count: an idempotent, commutative merge.
- "What if the fix fails?": "Tombstones grow forever. And what if the version counter itself is lost or reset after a restore?"
- Second fix or honest limit: Tombstones are kept only for the delta window; a node older than the window takes a snapshot, which
  contains no tombstones, so nothing is resurrected. The version counter lives in the rule store's transaction log; a restore that
  would rewind it is refused, the same lesson as a fencing token that must not go backwards: **never reuse a version number**, and
  start a higher epoch if the store is rebuilt.
- If asked, I'd say: "I do not trust arrival order. There is one writer that assigns versions, and each key remembers the version of its
  last change, so a late or duplicate message is ignored. Ranges resolve by longest prefix, and an exception beats a deny. The merge is
  idempotent, so applying the same history in any order gives the same list."

### Challenge 3 · The bad push  *(crux, part 1; correctness and operations)*

- Q (interviewer): "Someone publishes a range that covers a large part of Europe. How fast does it break, and how do you stop it?"
- Naive answer: "Review the change before it goes out, and fix it quickly if it is wrong."
- Case (IDs, times, numbers): 14:00:00 an operator adds `/8` instead of `/28` (a typo). 14:00:03 compiled as version 8,361,001.
  14:00:12 the push reaches the relays; **14:00:21 all 100,000 nodes serve the new list**. 14:00:30 eight percent of requests are
  denied. The change was reviewed by one person who saw "one line added". The next fix is a new version; the nodes take 18 s to
  get it. Total exposure ~40 s, or longer if the on-call has to wake up.
- Break (which box): the arrow from the compiler to the fleet, dashed red: nothing between the author's keystroke and every node
  asks whether the content is plausible.
- Fix (mechanism) · sequence? code?: **Treat the list like code.** (1) **Validation at ingest:** size and shape limits, a maximum
  share of the address space a single change may cover, and an **allowlist of ranges that must never be blocked**, checked at
  compile time **and again at enforcement** (allow beats deny). (2) **Two-person approval** above a threshold. (3) **Staged
  rollout:** 5 % (one region) → 25 % → 100 %, 5 minutes of bake each, **gated automatically on block rate per node against its baseline**;
  a gate trips on a rise of more than a few points, freezes the stage and alerts. (4) **Kill switch:** a flag in the manifest that nodes honour
  within one poll. (5) **Rollback is a new, higher version** with the previous content. (6) **Shadow mode:** a new or widened rule can ship as *log-only* first; nodes record "would have denied" with
  the rule id, and the owner promotes it to enforce after reading the counts. The action is part of the rule: deny, challenge (for a shared address,
  a softer response than a hard block) or log-only. An emergency ban uses a fast path (one
  region first, 60 s bake), logged as such. Sequence: stage, gate, halt, rollback.
- Why it works (property): **Safety against over-block (S2), at the cost of time.** The blast radius of a mistake becomes the canary:
  5,000 nodes for about a minute instead of 100,000 for however long the on-call takes. The allowlist is a second, independent
  line of defence that does not depend on review.
- "What if the fix fails?": "The rule is legitimate-looking and wrong: a real customer's range. Block rate does not move. Or the
  kill switch rides the same pipe that is broken."
- Second fix or honest limit: Two answers. A node runs a local **circuit breaker**: if its block rate exceeds a multiple of its baseline for
  N seconds right after a new version, it reverts itself to the previous version, reports, and pages; it does not wait for a central
  decision. The kill switch is a **separate, tiny channel** (one flag in the manifest every poll reads), not a new snapshot. Honest
  limit: a precise, plausible, wrong rule cannot be found by statistics. It is found by the allowlist for protected ranges, by the
  review of high-impact changes, and by an audit trail and a fast removal path. Policy, not mechanism, owns that risk.
- If asked, I'd say: "The same pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the same
  discipline as a binary: validation, an allowlist that always wins, a canary gated on block rate, a kill switch on its own channel,
  and a rollback that is just a new version. Nodes also protect themselves: if the block rate jumps right after an update, they
  revert on their own."

### Challenge 4 · Stale, partitioned, or no control plane  *(crux, part 2; failure recovery)*

- Q (interviewer): "A node cannot reach any relay for three hours. Or the whole distribution plane is down. What does the node do,
  and who decided?"
- Naive answer: "Fail closed: deny everything if the list is old. Or fail open: serve everything."
- Case (IDs, times, numbers): Node `eu-3-0099` last updated at 09:00; by 12:00 it has missed 3 h × 3,600 × 5/s = 54,000 changes. Fail
  closed would refuse everything this node serves: 10 requests/s × 10,800 s = 108,000 legitimate requests, and if the *whole fleet* loses the
  plane, every node fails closed together: a global outage caused by the system built to protect you. Fail open serves everything: the 54,000
  changes it missed include a ban the policy team called urgent.
- Break (which box): the node's staleness clock and the box that decides what to do when it expires, outlined dashed red: nobody chose.
- Fix (mechanism) · sequence? code?: **A bound and an action, signed by the owner.** First: **stale is not open.** A node keeps enforcing
  its last known list; only the *new* bans are missing. Per list class the policy owner sets a bound (for example 15 min for abuse bans, 1
  hour for the general list) and an action: **alert and keep serving**, or for a class with a legal deadline, **drain the node out of the
  load-balancer rotation** instead of failing each request. The node exposes its age; the load balancer reads it. Last-known-good on
  disk means a restart with no network still enforces. Sequence: bound passes, node reports `stale`, balancer drains, node recovers,
  re-checks, returns.
- Why it works (property): **Liveness made visible (L3) without trading safety for a global outage.** The decision is a number and an
  action chosen before the incident, by the people who own the consequence.
- "What if the fix fails?": "Every node passes the bound at once because the control plane is down. You just drained the fleet."
- Second fix or honest limit: A **drain budget**: automatic draining never removes more than a fixed share of the fleet (say 5 % per region);
  past that the node keeps serving and the page goes to a human. The cost is stated: while the plane is down beyond the bound, some
  nodes serve a stale list, and that risk is accepted in writing by the owner of the list. Honest limit: nothing makes a partitioned
  node learn a ban it cannot hear; the cure is a plane that is not a single point, and a bound short enough to matter.
- If asked, I'd say: "Stale is not open: a node keeps enforcing what it has. For each list, the owner signs a maximum age and an
  action: alert and keep serving, or pull the node out of rotation. Automatic draining has a cap so that a control-plane outage
  cannot become a fleet outage. The risk of a late ban is a named decision, not an accident."

### Challenge 5 · The list does not fit  *(scale)*

- Q (interviewer): "A hundred million IPv6 prefixes. Why not one shared cache lookup per request? And a Bloom filter says maybe. Then
  what?"
- Naive answer: "Put it all in a shared cache and call it from every node; or use a Bloom filter and block on 'yes'."
- Case (IDs, times, numbers): 100 M × 17 B = 1.7 GB per node exact; the budget is 512 MB. A shared lookup at 1 M/s adds ~1 ms to every
  request and a hard dependency. A Bloom filter at 1 % false positives, used alone: 1 M/s × 1 % = **10,000 legitimate requests a second
  blocked**. The filter can only say "definitely not listed"; "maybe" is not a verdict.
- Break (which box): the node's local structure, dashed red: the exact set no longer fits; the naive filter turns its error into a block.
- Fix (mechanism) · sequence? code?: **Filter in front, authoritative check behind, positive cache, and a smaller exact core.** The local Bloom
  filter (125 MB) answers "not listed" for 99 % of traffic with no network call. A "maybe" goes to a **regional lookup tier**
  (sharded by key prefix, exact structure) that returns the verdict, and the node caches it with a TTL bounded by the staleness bound. Keep
  the hottest, most-matched ranges exact and local. Per-entity enforcement point: addresses at the edge, user ids after authentication.
  Sequence: miss, maybe, lookup, cache.
- Why it works (property): **Correct verdicts at scale (S2).** The filter's error is one-sided, so a false positive costs a lookup, not a
  wrong block. Memory is within budget; the path stays local for nearly all traffic.
- "What if the fix fails?": "During an attack nearly every request is a true hit, so every request goes to the lookup tier. And the
  user changes address on every request."
- Second fix or honest limit: Cache positive verdicts, **coalesce** concurrent lookups for the same key, shard the tier and size it for the
  hit rate it will see, and put a **per-node budget** on lookups: past the budget, a node uses its cached verdicts and, for an unknown key, its
  stated policy. The rotating-address user is not a denylist problem: that is an identity key (the user id, after authentication) or an
  abuse model (SD-43). Honest limit: a very large list costs a tier that sits on the path for hits; we pay that only for the keys that
  are actually likely banned.
- If asked, I'd say: "A shared lookup per request puts the list service in everyone's availability, and 1 ms on every call. When the set
  does not fit, I keep a filter locally, which can say 'definitely not listed', and I confirm a 'maybe' with an exact tier, because a
  false positive blocks a real user. I cache the verdicts, coalesce lookups, and cap the load per node, so an attack does not take
  down the confirmation tier."

### Challenge 6 · A slow external source  *(overload; the source variant)*

- Q (interviewer): "The authority only gives you a lookup API: one second per call, a hundred calls a second. The API is down for two
  days. A new ban covers a /16 that you already cached verdicts for."
- Naive answer: "Call the API on each new address and cache the answer."
- Case (IDs, times, numbers): 20,000 first-seen addresses a second against 100 calls a second: 200× over. Even async, only 100/s × 86,400 ≈ 8.6 M of
  ~50 M distinct addresses a day are ever checked: 17 %. A cached *per-address* verdict (24 h) for `192.0.2.7` stays "allowed" for a day after
  the authority bans `192.0.2.0/16`.
- Break (which box): the adapter to the external authority, dashed red, and the verdict cache that stores keys instead of rules.
- Fix (mechanism) · sequence? code?: **Prefer a bulk list; otherwise a verdict cache with a bound, a budget and a stated policy.** (1) If any
  bulk file or change feed exists, mirror it and keep the same distribution; the API is only used to verify. (2) With only the API: a
  **verdict cache** keyed by range when the authority returns a range, with a TTL no longer than the allowed staleness or the legal grace period;
  **single-flight** lookups per key; a **token-bucket budget** (100/s) shared by priority (highest request volume first); asynchronous refresh;
  a policy for first-seen addresses (serve and verify, or hold briefly) chosen by the owner; a **circuit breaker** with an explicit,
  fleet-wide rule for an API outage. A /16 ban from the authority is applied as a range rule, which supersedes cached per-address verdicts by version.
- Why it works (property): **Bounded exposure instead of unbounded wait (L2, S1).** The request path never waits for the authority; the
  exposure is a number (the TTL and the coverage), and the budget makes a limit into a priority.
- "What if the fix fails?": "The API is down for two days and the cache TTL is one day."
- Second fix or honest limit: Extend a **grace period**: serve expired verdicts for a stated number of days, flag the decisions made on
  expired data in the log, and alert; the legal owner decides how many days. First-seen addresses in the outage window are the
  exposure; reduce it by prioritising by volume and by asking the authority for a bulk file. Honest limit: with only a slow lookup API
  full coverage is not possible, and the video says so and asks for a feed.
- If asked, I'd say: "I never call a slow authority on the request path. If there is a bulk list I mirror it. If there is only a
  lookup, I cache verdicts for no longer than the allowed staleness, coalesce lookups, spend the rate budget on the highest-volume
  addresses, and write down what happens on a first-seen address and on an outage. Full coverage is not possible, so I say how much we
  have and ask for a better feed."

### Challenge 7 · How would you know it is broken?  *(observability)*

- Q (interviewer): "A ban was published an hour ago and one region is still serving the banned source. The dashboard is green. How
  would you have known?"
- Naive answer: "Watch the CPU and the error rate of the relays."
- Case (IDs, times, numbers): Relay health 100 %, origin latency 40 ms: green. But region `ap-2` has 4 % of its nodes on version
  8,360,990 and the rest on 8,361,004; the push from the regional relay to one zone silently fails; polls are answered by a relay cache that
  is stale. Meanwhile block rate in that region is 0.2 % against 0.5 % elsewhere.
- Break (which box): the whole baseline dimmed, with the metrics, probes and decision log (tag `ch7`) as the only boxes outlined.
- Fix (mechanism) · sequence? code?: **Measure the promise, not the machine.** SLIs and targets (initial): **version skew**: share of nodes on the
  current version within 30 s ≥ 99.9 % per region; **propagation lag** p99.9; snapshot age per node against the bound; apply failures; block
  rate against baseline per version; lookup-tier hit rate. And an **end-to-end probe**: a synthetic banned key per region, published
  on a schedule, with a request sent through the real path to confirm a deny within 30 s. **Symptom pairs**:
  - skew up **and** one zone's relay cache age up → a stale relay cache, not the nodes
  - block rate down in one region **and** that region's applied version behind → a ban that did not land
  - block rate up **and** a new version applied → a bad rule: the gate, not the relay
  - apply failures up **and** checksum mismatches up → a corrupt artifact at the origin
  The decision log carries the version, so "why was X served on day D" has an answer.
- Why it works (property): **It turns the propagation promise into something you can watch.** The probe checks the whole chain every
  time, and each pair names a cause and an owner.
- "What if the fix fails?": "The probe passes and a real ban is still missing. Or the block rate is flat because traffic bypasses the
  enforcement point."
- Second fix or honest limit: Probes can pass while a different key fails, so skew is measured per node from reports, not only from
  probes. **Coverage** is a metric: the share of traffic that passes through an enforcement point, and a counter of requests that
  skipped the check. Honest limit: we can detect a late ban after the fact and alarm on its precursors; we cannot observe an absence of risk.
- If asked, I'd say: "I alert on the promise: the share of nodes on the current version within thirty seconds, per region, plus a
  synthetic banned key sent through the real path. I read metrics in pairs so each page names a cause, and every decision logs the
  rule version so an auditor gets an answer. A green relay dashboard says nothing about whether a ban landed."

## 8 · Build cost (AUX)

**Marked AUX: the manager layer.** Three releases (called R0, R1, R2 so they are not confused with design versions V1–V3):

| Release | R0 · Prototype | R1 · Production, one platform | R2 · Platform |
|---|---|---|---|
| Goal | Prove the model with one list | One or two lists, the full fleet, safe to depend on | Several key types, regional layers, very large lists, streaming push |
| Scope | Rule store, compiler, snapshot to object storage, 10 s manifest poll, atomic swap | Versions and deltas, relay tree, checksums, validation and allowlist, staged rollout and gates, kill switch, reports, decision log, console, audit | Push streams, layered regional rules, filter plus lookup tier, an external mirror adapter, per-key-type enforcement points |
| SLO, on-call | None | Propagation 99.9 % in 30 s, business-hours on-call | Error budgets, 24/7, shared rotation |
| Effort (engineer-months) | 1–2 | 18–24 (4 engineers, 5–6 months) | 50–90 (5–7 engineers, 10–14 months) |

- **People and months, R1:** tech lead 1.0, senior backend 1.0, backend (agent, library) 1.0, SRE 1.0 (the rollout and gates are
  operations), manager 0.3, security or policy liaison 0.2. Phases: discovery and RFC with the policy owner (3 weeks), walking skeleton (4),
  correctness: versioning, ordering, a convergence test harness under injected faults (6), safety: validation, canary, kill switch (5),
  operations: SLIs, probes, runbooks, game day (4), shadow on one region then cutover (4).
- **Total cost of ownership, illustrative:** 22 engineer-months to build, then ~1.5 people for five years (1.5 × 60 = 90) ≈ **112 engineer-months
  ≈ 9 engineer-years**; infrastructure is a small share (relays and storage). People dominate.
- **Buy against build against don't:**

  | Option | Effort to a pilot | Five-year cost, engineer-months (illustrative) | When it wins |
  |---|---|---|---|
  | Don't: an edge provider's managed IP-set feature | ~2 weeks | ~15 | The limits fit (entries, key types, regions) and you can live with its propagation time. **Check first, every time** |
  | Adopt: an existing configuration-distribution protocol and its control plane for transport, with our own compiler and gates | ~8 weeks | ~70 | A distribution fabric is already run for other configuration |
  | Build: this design, end to end | ~5 months, 4 people | ~112 | Lists beyond the managed limits, custom key types, audit and layering requirements |
  | Hybrid: build the compiler, gates and audit; buy the transport | ~3 months | ~85 | Our pick for R1 if a transport exists |

- **Never cut:** versions with checksums, staged rollout with a gate, the allowlist, a kill switch, last-known-good on disk, the version in the
  decision log. **Cut first:** push streams (the 10 s manifest poll meets the SLO), regional layers, the second key type, the lookup tier, the console UI.
- **Top risks:** (1) a bad rule: the gates, the allowlist and a game day that practises one; (2) owner ambiguity: policy writes the list,
  platform owns the pipe, and the **propagation SLO is the contract between them** ("99.9 % of nodes within 30 s"); (3) the control plane
  becomes a single point: a drain budget and nodes that work with no control plane; (4) adoption: a named first list and its owner before code;
  (5) scope creep into a general configuration platform: written non-goals.
- **Staffing:** small first; grow in the middle where the work parallelises (agent, compiler, console); do not add people in stabilisation;
  share the on-call with the team that runs the sibling rollout system.
- **The question to ask the requesting team before saying yes:** "What does a wrong block cost, who decides, and how fast must a ban land?"
- **Phases:** Phase 1 a 10 s manifest poll with deltas inside the window and a snapshot only to bootstrap or beyond it; Phase 2 streaming push and regional layers; Phase 3 the large-list tier.

## 9 · Recap

- **Final diagram:** the full carried baseline, all tags visible and green: policy tool, validation and allowlist, rule store with
  one version order, compiler, relay tree with push and pull, nodes with atomic swap, last-known-good, filter and lookup tier, rollout
  gates with a kill switch, metrics, probes and the decision log.
- **One sentence per path:** *Publish:* validate, approve, one version. *Distribute:* manifest, delta or snapshot, verify, swap. *Enforce:*
  allowlist, exact, longest prefix, version in the verdict. *Explain:* the version joins the rule history. *Roll back:* a new, higher version, and
  a kill switch on its own channel.
- **If asked: a second key type (user id).** The same pipeline; a different enforcement point after authentication; a different bound.
- **Common mistakes in this round:** a lookup per request on the path; "eventually consistent" with no number; no versions or checksums;
  trusting arrival order; a full download per node per change; failing closed for the whole fleet or failing open silently; never asking
  who owns the failure policy; a Bloom filter used as a verdict; one big push with no canary; no allowlist; rollback that reuses a version
  number; green relay dashboards as proof; ignoring the shared-address user.
- **Closing line (key-line voice):** "The check is local because it has to be fast and independent. The list cannot be local, so I give
  it versions, a bound on how old it may be, and the discipline of a release. Everything I built is there so that a ban lands
  quickly and a mistake does not."

## Canon check

For the video README, not for the screen. The source map is kept outside the tracked files.

| Canonical point | Covered at (chapter / slide) or dismissed because |
| --- | --- |
| No network call on the request path; a local structure sized with arithmetic | Ch. 2 estimates; ch. 3 M1; options matrix rows A and D |
| Exact structures: sorted array or hash set for keys, radix trie for prefixes | Ch. 2; ch. 3 M1; ch. 4 physical model; **C2** |
| A Bloom filter says "definitely not listed", a hit needs confirmation | Ch. 2; **C5**. what changed since: hash-prefix lists are now one of several shapes; the principle (confirm a hit) is unchanged |
| Versioned snapshots plus incremental updates with a checksum | Ch. 3 M2; **C1** |
| Push plus pull backstop; relay tree; fan-out arithmetic | Ch. 2 fan-out; ch. 3 M3; V2 |
| Staged rollout, canary, kill switch, rollback of a bad configuration | Ch. 3 M5; **C3** |
| Staleness bound and fail-open against fail-closed | Ch. 3 M6; **C4**; the owner signs it |
| Ordering of add and remove; idempotent merge; tombstones | **C2** |
| An allowlist of ranges that must never be blocked | Ch. 1; ch. 3 M5 and M7; **C3** |
| A slow external source: mirror, cache with TTL, coalescing, budget, breaker, first-seen policy | **C6** |
| Audit: why was X served on day D | FR4; API `Explain`; **C7** |
| Propagation SLO as the contract between policy and platform owners | Ch. 1; ch. 8 |
| Layered rules: global plus regional | Ch. 1 IN scope; ch. 8 R2; dismissed from the walk-through: same pipeline, per-region artifact; one slide in ch. 5 |
| Per-entity enforcement point (IP at the edge, user id after authentication) | **C5** |
| Shared and rotating addresses; an address is not a person | Ch. 1 hook; **C5** |
| Rate limiting, abuse detection, volumetric attack scrubbing | Dismissed aloud in ch. 1 (OUT) with pointers to SD-25 and SD-43 |
| Buy against build against don't, people and months | Ch. 8 |

## Budget

Planned: 86 minutes, 11,437 words, 181 slides. **Actual (script, after the build): 11,736 words, 168 slides**, about 0.44 s a word. Voice mix: candidate about 88 %, interviewer 4 %, key line 6.5 %, coach 1.6 %.

| Chapter | Words (actual) | Slides (actual) |
|---|---|---|
| 0 Cold open | 396 | 6 |
| 1 Requirements and scope | 1,008 | 14 |
| 2 Estimates | 881 | 11 |
| 3 Theory | 1,468 | 19 |
| 4 API and entities | 802 | 10 |
| 5 High-level design | 1,537 | 22 |
| 6 Bridge | 89 | 2 |
| 7 Challenges | 41 | 1 |
| 7.1 Challenge 1: The node that was offline | 548 | 9 |
| 7.2 Challenge 2: Order, duplicates, overlap | 591 | 9 |
| 7.3 Challenge 3: The bad push | 767 | 11 |
| 7.4 Challenge 4: Stale or no control plane | 679 | 10 |
| 7.5 Challenge 5: The list does not fit | 662 | 10 |
| 7.6 Challenge 6: A slow external source | 557 | 9 |
| 7.7 Challenge 7: How would you know? | 606 | 10 |
| 8 Build cost | 575 | 7 |
| 9 Recap | 529 | 8 |
| **Total** | **11,736** | **168** |
