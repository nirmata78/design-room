# SD-94 Blocking / denylist system: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: denylist=deny-list CIDR=C-I-D-R IPv4=I-P-v-four IPv6=I-P-v-six IP=I-P IPs=I-P-s SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S gRPC=g-R-P-C SQL=S-Q-L CDN=C-D-N NAT=nat DDoS=dee-dos TLS=T-L-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C DR=D-R UUID=U-U-I-D xDS=x-D-S Redis=Reddis fsync=F-sync ppm=P-P-M JVM=J-V-M LB=load_balancer -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A denylist sounds like the easy question. A set of banned addresses and a lookup. Anyone can write that lookup in an afternoon. This question is not testing the lookup. It is testing what happens around it: how a ban reaches a hundred thousand servers, what a server does when it cannot hear about new bans, and what stops one wrong line from taking everyone offline.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design a distributed system that stops requests from banned sources, such as I-P addresses, from being served, on every one of our servers.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. An operator means to ban a small range and types a wide one. The change compiles in three seconds, crosses two tiers of relays, and by about eighteen seconds every server in the fleet is running it. Eight percent of real requests are now denied.
C: No deployment failed. Every component did what it was told. The pipeline that can deliver an urgent ban in ten seconds delivers a mistake in the same ten seconds. The lookup was never the hard part. The pipe, and what it is allowed to carry, is.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes. The weak signal is always the same shape: a fast lookup, drawn well. The strong signal is what the candidate says about the distance between the list and the lookup.
C: I'll keep two failures in mind the whole way. A ban that is missing, and a block that should not exist. Most designs worry about the first and forget the second.
[pause: 1.0]

[slide: v-005]
[pause: 0.7]
V: The check must be local and the list cannot be. So the design is the distance between them: a version every node can verify, a stated bound on how stale a node may be, and the discipline of a release.
[pause: 1.0]
C: Concretely, a check in the server's own memory with no network call. A list compiled once, versioned, and copied everywhere through a path that can be verified and resumed. And pushes treated as carefully as a binary.
[pause: 1.6]

[slide: v-006]
[pause: 0.6]
C: The order I'll follow. Requirements and scope, then numbers, then a short theory chapter that the design can lean on. Then the A-P-I and data, and a high-level design in three versions, each answering the objection to the one before.
C: Then the part I care about most: seven challenges that break the design, where each fix creates the next question. A build cost, because someone has to own this. And a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-007]
[pause: 1.2]
C: Before I draw anything I want to ask six questions. Each answer will change the design.
[pause: 1.8]

[slide: v-008]
[pause: 0.6]
C: Who owns the list, and who calls the check?
I: A policy team, security and legal, owns the content. The platform team owns the mechanism. The check runs on every serving node, on the request path. About a hundred thousand nodes in twenty regions.
C: Two owners. That matters later, because the contract between them has to be a number. And the check is on the request path of a hundred thousand servers, so it cannot be slow and it cannot depend on much.
[pause: 0.6]

[slide: v-009]
[pause: 0.6]
C: What exactly is banned?
I: Network addresses first. Single I-P-v-four and I-P-v-six addresses, and ranges, written as C-I-D-R blocks. A second key type, a user I-D, will come later. Do not design it out.
C: Ranges change the data structure, because a range needs longest-prefix matching and a single address does not. And a second key type means the key kind must be a field, not an assumption.
[pause: 0.6]

[slide: v-010]
[pause: 0.6]
C: How big, and how fast does it change?
I: Ten million entries today, perhaps a hundred million later. About five changes a second on average, fifty in a burst. A million requests a second at peak, across the whole fleet.
C: The list is large but changes slowly. A million requests against five changes. That ratio is the whole shape of the design: read everywhere, write rarely.
[pause: 0.6]

[slide: v-011]
[pause: 0.6]
C: How fast must a new ban take effect?
I: Within thirty seconds, for ninety-nine point nine percent of nodes. Removals follow the same rule.
C: Thirty seconds is generous enough to avoid a constant stream and tight enough to rule out a once-a-minute timer. And it is stated as a share of nodes, which tells me some nodes are allowed to be late. I'll have to say what happens to those.
[pause: 0.6]

[slide: v-012]
[pause: 0.6]
C: What should a node do if it cannot get updates?
I: That is yours to propose. I will decide who signs it.
C: That answer is the second half of this question. Failing open and failing closed are both bad for a denylist, and the choice belongs to the policy owner, not to me. I'll make it explicit and bring it back in challenge four.
[pause: 0.6]

[slide: v-013]
[pause: 0.6]
C: And where does the list come from?
I: Mostly an internal tool. One list is mirrored from an external authority that publishes a daily bulk file. A variant has only a slow lookup A-P-I. Tell me what you would say.
C: Two sources with different speeds. I'll treat the bulk file as an input to the same pipeline, and I'll answer the slow lookup in challenge six.
[pause: 0.6]

[slide: v-014]
[pause: 0.6]
C: Functionally, five things. One, publish a change: add or remove a key or range, with a reason, a source and an optional expiry, validated and audited. Two, distribute: every change reaches every node within the bound, and a node that was offline catches up without help.
C: Three, enforce: a verdict for each request, in the request path, in microseconds. Four, inspect and explain: which version each node runs and how old it is, and why a key was denied or served on a given day. Five, roll back and stop: halt a rollout, kill a list, revert, with an emergency path. Each of these gets a numbered flow later.
[pause: 0.8]

[slide: v-015]
[pause: 0.6]
C: The numbers. They are initial targets, and I'll say so once for this chapter: none is a measurement.
C: The check takes under ten microseconds at the ninety-ninth percentile, in process, with no network call. A new version reaches ninety-nine point nine percent of nodes in thirty seconds, which means about a hundred of a hundred thousand may be late, and each of those must be listed, not silent. And every decision carries the version of the list that made it, so an auditor can reconstruct a verdict.
[pause: 0.8]

[slide: v-016]
[pause: 0.6]
C: Three promises that are not numbers. A node keeps enforcing its last known list through any outage of the distribution plane. Stale does not mean open.
C: The staleness bound is signed: every list has a maximum age and an action when it is exceeded, chosen by its owner. And a bad push is caught by the pipeline itself, not by customers. Notice the pair of failures again: the first two promises are about a missing ban, the third is about a block that should not exist.
[pause: 0.8]

[slide: v-017]
[pause: 0.6]
C: One definition, stated once, because it is easy to misread. Every ten seconds a node asks the manifest, about a hundred bytes: the current version, the delta window and a checksum. If current, that is the whole exchange. If behind, inside the window, it fetches deltas. A full snapshot only to bootstrap, after falling outside the window, or when verification fails. Never on a routine poll.
[pause: 0.8]

[slide: v-018]
[pause: 0.6]
C: In scope: single addresses and ranges in both address families, a second key type as an extension, an allowlist of ranges never blocked, internal and mirrored sources, staged rollout, audit and a console.
C: Out of scope, on purpose. Detecting abuse, which is a different question about models. Rate limiting, which has counters and windows. Absorbing a volumetric attack, which happens upstream. Content rules inside requests. And an appeals product, which needs an owner and a workflow: I'll name it, not draw it.
[pause: 0.8]

[slide: v-019]
[pause: 0.6]
C: Something to say aloud. An address is not a person. Many users share one address behind a carrier-grade translator. One wrong range blocks thousands of legitimate people at once.
C: That is why I want an allowlist that always wins, why removals matter as much as additions, and why the action on a match is part of the rule: deny, challenge or log only. It is also why a block that should not exist belongs next to a ban that is missing.
[pause: 0.8]

[slide: v-020]
[pause: 0.7]
V: The core is four things. A versioned list, compiled in one place. A distribution path that can be verified and resumed. A local check with no network call. And a release discipline that treats the list as code.
[pause: 0.8]
N: Notice what the candidate did in six minutes. They asked who owns the failure policy, cut five things out loud, and said an address is not a person. That is the framing signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-021]
[pause: 1.2]
C: Now the numbers. Every one is arithmetic from the inputs and carries a label: given, illustrative, derived or an initial target. Each has to change a decision, or I drop it.
[pause: 1.8]

[slide: v-022]
[pause: 1.0]
C: A million requests a second over a hundred thousand nodes is ten a second per node. So CPU is not the argument for a local check. The argument is latency and independence.
C: A remote check adds about a millisecond to every request, and makes one service answer a million lookups a second. And availability multiplies: a list service at four nines on the request path of a service at four nines gives about three point nine nines. Decision: the check is local, with no network call.
[pause: 1.0]

[slide: v-023]
[pause: 1.3]
C: Memory. Ten million single I-P-v-four addresses at four bytes is forty megabytes as a sorted array. Two million ranges in a prefix trie is about eighty. All of that fits on every node. Now a hundred million I-P-v-six prefixes at seventeen bytes: one point seven gigabytes, over a budget of five hundred and twelve megabytes. A filter at ten bits an entry is a hundred and twenty-five. Challenge five will deal with it.
C: Now the later case: a hundred million I-P-v-six prefixes. Seventeen bytes each is one point seven gigabytes, over a budget of five hundred and twelve megabytes. A filter at ten bits an entry is a hundred and twenty-five. Decision: ten million fits exactly, a hundred million does not, and challenge five will deal with it.
[pause: 1.1]

[slide: v-024]
[pause: 1.0]
C: The check itself. Binary search over ten million entries is about twenty-four comparisons: under a microsecond even with cache misses. A prefix trie is a little more. Against a budget of ten microseconds, the lookup has room to spare. Both numbers are illustrative, and I'd measure them.
C: Decision: I will not spend design effort making the lookup faster. The risk is in getting the list there and in what it contains.
[pause: 1.0]

[slide: v-025]
[pause: 1.0]
C: Change volume. Fifty changes a second at about thirty bytes is one and a half kilobytes a second. A node that was offline for two hours misses about eleven megabytes of deltas, against a forty megabyte snapshot. So catching up by deltas wins.
C: The break-even is when the deltas would exceed a snapshot: about seven and a half hours at the burst rate. So I keep twenty-four hours of deltas, about a hundred and thirty megabytes. Decision: a delta window of twenty-four hours. A node older than that takes a snapshot.
[pause: 1.0]

[slide: v-026]
[pause: 1.3]
C: Fan-out. If every node pulled a forty megabyte snapshot from one origin, that is a hundred thousand times forty megabytes: four terabytes. So I build a relay tree. The origin serves twenty regional relays, each serves ten zone relays, each zone relay serves five hundred nodes. The origin now serves twenty snapshots: eight hundred megabytes.
C: Snapshots are immutable and addressed by content, so a zone relay caches them forever: five hundred nodes cost one fetch. Decision: the tree is not optional, and it also bounds the load on the origin.
[pause: 1.1]

[slide: v-027]
[pause: 1.0]
C: Polling. A hundred thousand nodes every ten seconds is ten thousand manifest polls a second. Each is about a hundred bytes: one megabyte a second across the fleet, and fifty a second on each zone relay. Trivial.
C: And to repeat the definition: a poll fetches the manifest and nothing else, unless the manifest shows the node is behind. Decision: a ten-second poll is cheap enough to be the backstop to push, and by itself it is a valid first release.
[pause: 1.0]

[slide: v-028]
[pause: 1.3]
C: The propagation budget. Compile, three seconds. Origin to regional, two. Regional to zone, two. The node's own poll, up to ten seconds of waiting: the worst case with no push. Verify and apply, one. Eighteen seconds against thirty, twelve spare. Pull alone meets the target. Push shortens the wait to about one second. And a sixty-second poll would not work: sixty-eight. Decision: a ten-second poll, and a measured propagation number to alert on.
[pause: 1.1]

[slide: v-029]
[pause: 1.0]
C: The variant with a slow external source. Say twenty thousand first-seen addresses a second at peak, against a limit of a hundred calls a second. Two hundred times over. Even running all day, a hundred calls a second buys eight point six million lookups, against about fifty million distinct addresses: seventeen percent.
C: Decision: that lookup can never sit on the request path, and it cannot give full coverage. It can feed a cache for the highest-volume addresses, and I'll ask for a bulk list. Challenge six.
[pause: 1.0]

[slide: v-030]
[pause: 1.0]
C: Blast radius. Without gates, all hundred thousand nodes run a pushed change within eighteen seconds. A bad range blocking eight percent of traffic would show in a single ten-second metrics window on a canary of five thousand nodes.
C: So a planned push goes five percent, twenty-five percent, then everyone, with a five-minute bake each: about ten minutes. An urgent ban can use a shorter path. Decision: speed is not free. It is a setting, and different pushes get different settings.
[pause: 1.0]

[slide: v-031]
[pause: 1.0]
C: Last. Ninety-nine point nine percent of a hundred thousand nodes allows a hundred late nodes. Each late node is listed with its age, never hidden. The service level indicator is the share of nodes on the current version, per region.
N: A hundred nodes of slack is the kind of arithmetic that turns an abstract target into a pager rule.
C: That is the numbers. Next, theory.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-032]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what a denylist is and is not, the properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide here has a theory badge.
[pause: 1.8]

[slide: v-033]
[pause: 0.7]
V: A distributed denylist is a versioned set of banned keys, compiled once, copied to every enforcement node, and checked inside the request path without a network call. A change takes effect everywhere within a stated bound, and every decision can be traced to the rule version that made it.
[pause: 1.0]
C: Each clause is load-bearing. Versioned, so a node can prove what it holds and catch up. Copied to every node, so the check is local. Without a network call, so the list's availability does not multiply into every request's. A stated bound, so staleness is a number someone signed. Traced to a version, so there is an audit.
[pause: 1.6]

[slide: v-034]
[pause: 0.6]
C: Four neighbours. It is not a rate limiter: no counters, no window. It is not a cache: a cache can be wrong by design and refills on a miss, but a denylist must hold the whole set, because a miss means allow. It is not a feature-flag service: same push mechanics, but a wrong flag changes a behaviour while a wrong block drops a customer. And it is not a firewall, which decides on content.
[pause: 0.8]

[slide: v-035]
[pause: 0.6]
V: Safety: a banned key is never served by a node whose list is newer than the ban plus the bound, and a legitimate key is never denied because of a bad or partial list. Liveness: every node applies every version, ninety-nine point nine percent within thirty seconds, and a node that cannot update is detected and handled.
[pause: 0.8]
C: Notice there are two safety properties, because there are two ways to be wrong. S-one is the missing ban. S-two is the wrong block. Every fix from here says which property it serves.
[pause: 0.8]

[slide: v-036]
[pause: 1.3]
C: Here is the central tension. The faster a change reaches every node, the faster a mistake does. And every safeguard that checks a push costs time. On the left, no gates: eighteen seconds to everyone. On the right, a routine push in stages, about ten minutes. In between, an urgent ban: one region first, a short bake.
C: The pipeline cannot tell a ban from a mistake. So the position on this line is a decision, made per push, by its owner. Hold on to that picture. Challenge three lives on it.
[pause: 1.1]

[slide: v-037]
[pause: 0.6]
C: Mechanism one, the in-process check. It protects latency and independence. A sorted array or hash set for single keys and a prefix trie for ranges, in the server's own memory. It rules out a network call on every request, and the list service joining every request's availability. It costs the whole set in memory on every node, and it turns staleness from a non-issue into a design parameter.
[pause: 0.8]

[slide: v-038]
[pause: 0.6]
C: Mechanism two, versions with checksums. It protects convergence and integrity. One writer assigns a strictly increasing version. Every version has a snapshot and a delta from the one before, and each checksum covers its content and the previous checksum, so they form a chain. It rules out a node that cannot say what it holds, partial or corrupt state, and a full download per change. It costs a compile step, a delta log to retain, and two kinds of artifact to store.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: Mechanism three, a relay tree with push and a pull backstop. It protects propagation speed and resilience. The origin serves a few relays, each relay serves more, and artifacts are immutable so every tier can cache them. A push says a version exists, and a ten-second manifest poll is the backstop. It rules out an overloaded origin and a missed push that leaves a node behind forever. It costs extra hops of latency and two paths to run.
[pause: 0.8]

[slide: v-040]
[pause: 0.6]
C: Mechanism four, atomic swap and a last known good copy. It protects the node's serving state. Build beside, verify, swap one pointer, and write the verified list to disk. It rules out a half-applied list, an empty list after a restart, and a crash in the middle of an update. It costs two copies in memory for a moment, and a startup path that has to work with no network.
[pause: 0.8]

[slide: v-041]
[pause: 0.6]
C: Mechanism five, release discipline. It protects against bad content, which is the over-block. Limits and an allowlist at ingest. Stages gated automatically on the block rate. A kill flag in the manifest that nodes honour within one poll. And a rollback that publishes the old content as a new, higher version. It rules out one mistaken rule reaching everyone at once. It costs minutes of delay on a routine push, and an emergency path with fewer gates.
[pause: 0.8]

[slide: v-042]
[pause: 0.6]
C: Mechanism six, the staleness bound. It protects liveness by making it visible. Each list has a maximum age and an action when it is exceeded, signed by its owner: alert, or drain the node, with a cap. It rules out silent drift, every node quietly serving an old list for days. It costs a policy someone must sign, and capacity when nodes drain.
[pause: 0.8]

[slide: v-043]
[pause: 0.6]
C: Mechanism seven, a filter in front and an exact check behind, with allow beating deny. It protects correct verdicts at scale. A compact filter answers definitely not listed. A maybe is confirmed by an exact tier. And an allowlist range overrides any deny. It rules out a false positive blocking a real user, and a wrong range overriding a protected one. It costs a second tier for confirmation, and precedence rules to explain and test.
[pause: 0.8]

[slide: v-044]
[pause: 1.0]
C: Now the options. Six approaches, each with the failure that rules it out. Three that look cheap first.
C: A, a central lookup on every request: always fresh, but a millisecond on every call, the list service in everyone's availability, and a million lookups a second. B, each node downloads the whole list on a timer: four terabytes at this scale, and a corrupt file looks like a good one.
C: C, a push-only stream. Fast and cheap. But a node that misses messages has no way to catch up, ordering and duplicates are your problem, and there is no integrity check.
[pause: 1.0]

[slide: v-045]
[pause: 1.0]
C: Here are all six. D is a versioned snapshot plus deltas, a relay tree, push with a pull backstop, a local check and a staged rollout. It fails when the set no longer fits on a node, which adds row E, and when a wrong rule passes validation, which is challenge three.
C: E is a local filter with a remote check on a hit. It fails when the hit rate is high, as in an attack. F is the edge or C-D-N provider's own I-P-set feature: almost no work, and it fails on entry limits, key types, layered rules, audit detail, and propagation I cannot measure.
V: I pick D, after checking whether F is enough.
[pause: 1.0]

[slide: v-046]
[pause: 0.6]
C: What the pick gives up, said plainly. Instant effect: a bounded, measured delay instead. Memory on every node. And a distribution plane to build, run and be paged for. What it buys: auditable verdicts, layered rules, extra key types, a propagation number I can measure, and a request path that depends on nothing else.
C: And before any of it I check row F. If the provider's feature fits my limits and my propagation needs, I buy it and build only the audit around it.
[pause: 0.8]

[slide: v-047]
[pause: 0.6]
C: Row F deserves a straight answer, because candidates skip it. Ask four things: does the entry limit cover ten million, and a hundred million later? Does it handle ranges and I-P-v-six? How fast does a change land, and can I measure it? Can it carry a second key type?
C: What is often missing: a per-decision audit with a version, layered regional rules, a staged rollout I control, and an allowlist that always wins. If everything fits, I buy it and build the rule store, the audit and the gates around it. If not, I build D.
[pause: 0.8]

[slide: v-048]
[pause: 1.0]
C: Last part, the failure catalogue, which becomes the challenge list. F-one, a node is offline or behind, or an update is corrupt: challenge one. F-two, add and remove arrive out of order or twice, or ranges overlap: challenge two. F-three, a bad rule: challenge three. F-four, the distribution plane is down or a node is partitioned: challenge four.
[pause: 1.0]

[slide: v-049]
[pause: 1.0]
C: F-five, the list outgrows a node: challenge five. F-six, the source is a slow authority: challenge six. F-seven, nobody notices: challenge seven. F-eight, an operator mistake in the console, I handle with two-person approval and an audit trail, on the A-P-I slides. F-nine, a restart with no network, is last known good on disk, in the flows. Seven challenges, in that order.
[pause: 1.0]

[slide: v-050]
[pause: 1.0]
N: Good theory has a consequence for the design. Look at this table: every mechanism names the property it serves, and where it will be used.
C: That is the vocabulary. On to the design.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-051]
[pause: 1.2]
C: The A-P-I before the boxes. It is the contract, and it shows whether I have thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes.
[pause: 1.8]

[slide: v-052]
[pause: 1.0]
C: Publish. A list name and a set of operations. Each carries the operation, the key, whether it is a single address or a range, the action, a reason, a source and an optional expiry. An idempotency key makes a retried publish harmless: the same key returns the same version, never a second one.
C: The response is a change set id and the version it was given. Large or wide changes wait for a second approver. This call serves requirement one, and writes a change set and its rules.
[pause: 1.0]

[slide: v-053]
[pause: 1.0]
C: Distribution. The poll is a get on the manifest with the node's version. The response is tiny: the current version, where the delta window starts, references to the delta and snapshot, a checksum, and the kill flag. The delta and snapshot are immutable, content-addressed files, so any relay can cache them. The node reads minDelta: at or above it, fetch the delta, otherwise the snapshot. Never a file on a routine poll.
[pause: 1.0]

[slide: v-054]
[pause: 1.0]
C: The check. Notice it is a library call in the serving process, not a network A-P-I. It returns a verdict, which may be deny, allow or challenge, the rule that decided, and the version of the list. The order matters: normalise the key, check the allowlist first, then the exact key, then the longest-prefix range, then allow by default.
C: The allowlist goes first, so a protected range always wins over any deny. And the version in the verdict is what lets an auditor answer why a key was served on a given day.
[pause: 1.0]

[slide: v-055]
[pause: 1.0]
C: Fleet state and audit. Every poll carries a report: node, list, the version applied, and the age of that version. The control plane derives skew and lateness from these reports. A node never has to be asked.
C: Explain is the audit call. Given a key and a time, it joins the sampled decision to the rule history by version, and answers: denied, by rule forty-four eleven, in version eight million three hundred sixty thousand nine hundred and ninety, from the policy tool.
[pause: 1.0]

[slide: v-056]
[pause: 1.0]
C: Rollout control. Rollout moves a version to a stage. Halt freezes it. Rollback takes the version number you want to return to, and publishes that content as a new, higher version. Never an old number: a node ignores anything not newer than what it has.
C: KillSwitch sets a flag in the manifest itself, so nodes see it within one poll on a channel that does not depend on a new snapshot. Every call is audited, two-person approved above a size, and it alerts.
[pause: 1.0]

[slide: v-057]
[pause: 1.3]
C: The conceptual model. A list contains rules. A rule is published in a version. A version is applied by nodes: each node's state records the version it runs. An allow range protects rules from any deny. An audit event is a weak entity, logged against a list: it only exists in the context of one.
C: One fact matters most: a key has at most one live state per list, and the version of its last change decides it. That is what makes merging safe, in challenge two.
[pause: 1.1]

[slide: v-058]
[pause: 1.3]
C: Physically. The rule table is keyed by list and key, with the version it was added in and, if removed, the version it was removed in. A removed row stays for the delta window: a tombstone. The version table holds a number assigned in the same transaction as the rules, a checksum, and the previous checksum.
C: Node state is soft, rebuilt from reports. The allow ranges are kept apart and checked twice, at compile time and at enforcement. On the node, the sorted array, the prefix trie and the filter live in memory, with the current and previous snapshot on disk. The rule store must not be lost or rewound, because version numbers would be reused.
[pause: 1.1]

[slide: v-059]
[pause: 1.0]
C: The apply step is small enough to read whole. For each change in a delta, look at the last version that touched this key. If the change's version is not higher, it is a late or duplicate message: do nothing. Otherwise record it. Then build the structure beside the old one, verify the checksum chain, and swap one pointer.
C: That per-key version is the quiet hero. It makes the merge idempotent and independent of order, which challenge two depends on.
[pause: 1.0]

[slide: v-060]
[pause: 1.3]
C: The version chain. Each version's checksum covers its own content and the checksum of the version before. A node that holds version N-1 and receives the delta to N can verify the chain end to end before applying anything. The shaded band is the delta window: twenty-four hours of deltas. Inside it, a node takes small deltas. Outside it, or when a check fails, one full snapshot.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-061]
[pause: 1.2]
C: Three versions. Each is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move.
[pause: 1.8]

[slide: v-062]
[pause: 1.3]
C: Version one. A policy tool writes one list file into object storage. Every node downloads it every minute, builds a set, swaps it in, and checks each request against it locally. Requests come in at the top, verdicts go out. No objection yet: it is the simplest thing that works, and for a short list that rarely changes it might be enough.
[pause: 1.1]

[slide: v-063]
[pause: 1.0]
C: The objection. Every minute, a hundred thousand nodes each pull forty megabytes: four terabytes from one place. A node can read a file while it is still being written, and load half a list without knowing. A bad file reaches every node. And there is no version, so an auditor asking what was in force at two o'clock cannot be answered.
[pause: 1.0]

[slide: v-064]
[pause: 1.3]
C: Version two answers that. A rule store assigns versions in a single transaction, so there is exactly one order. A compiler turns each version into an immutable snapshot and a delta, with chained checksums, in the origin store. The origin feeds a relay tree. Nodes poll the manifest every ten seconds, the dashed push arrow says a version exists, and the green arrow carries the delta.
C: Now a node can say what it holds, verify what it gets, catch up by small deltas, and never download the whole list on a routine poll.
[pause: 1.1]

[slide: v-065]
[pause: 0.6]
C: The three arrows between a relay and a node, because they are easy to confuse. Poll: every ten seconds the node asks the manifest. It always works. Push: the relay tells the node a version exists, and the node immediately runs the same manifest step. The push carries no data. And the delta: the small, immutable file, fetched only when the node is behind.
C: Push shortens the wait and the poll guarantees arrival, and the node's logic is the same for both. That is why I can leave push out in the first release.
[pause: 0.8]

[slide: v-066]
[pause: 0.6]
C: The objection to version two. The distribution is right, and it is fast, and nothing checks the content. A typo travels as quickly as a ban. And a node that cannot update does something, and nobody chose what. Distribution is correct. Release discipline is missing.
[pause: 0.8]

[slide: v-067]
[pause: 1.3]
C: Version three. The new box is a control plane. It reads every node's applied version and age, the dashed arrow back, and it gates each stage of a rollout through the origin. Inside the rule store, ingest now validates against an allowlist and size limits. On the node, the swap is atomic, the last known good copy is on disk, and a staleness bound has an action.
C: This is the baseline. It stays on screen, and every later picture is a view of it.
[pause: 1.1]

[slide: v-068]
[pause: 1.0]
C: The node's loop is short. Ask the manifest. If the kill flag is set, honour it. If already current, do nothing: the common case. Otherwise fetch a delta if inside the window, a snapshot if not. Verify the checksum chain: on failure, discard and report. Build the new structure beside the old, swap, persist to disk, report.
C: Every branch ends with the node serving a good list. A failure never leaves it worse off than before the poll.
[pause: 1.0]

[slide: v-069]
[pause: 0.6]
C: What version three leaves open. It has one order, verified distribution, atomic apply, a controller with gates and a stated stale policy. It has not been tested against a node two hours behind, changes out of order, a plausible but wrong rule, a lost control plane, a list that does not fit, a slow authority, or a silent failure. Those are the seven challenges, after the flows.
[pause: 0.8]

[slide: v-070]
[pause: 1.3]
C: Requirement one, publish. Step one: an operator sends PublishChange. Step two: ingest normalises every key into a canonical form, so the same range always looks the same. Step three, on the validate box: size limits, a cap on how much address space one change may cover, and a check against the allowlist.
C: A large change waits for a second person. Then one transaction in the rule store writes the rules and takes the next version number, so there is exactly one order, and an audit event is written. The compiler picks it up from there.
[pause: 1.1]

[slide: v-071]
[pause: 1.3]
C: Requirement two, distribute. One: the origin fans artifacts out through the relay tree. Two: a push says the new version exists. Three: the node polls the manifest. Four: the delta comes back; the node verifies the chain, builds beside, swaps, writes to disk and reports. A node that never hears the push takes the same steps at its next poll, and so does a node that was offline.
[pause: 1.1]

[slide: v-072]
[pause: 1.3]
C: Requirement three, enforce. Step one: the request arrives with a source address. Step two: the agent in the serving process normalises it and checks. The allowlist first, then the exact key, then the longest-prefix range. No network call, no lock, nothing shared.
C: The verdict returns with the rule and the version, and the decision is sampled to a log off the hot path. The request carries on or is refused.
[pause: 1.1]

[slide: v-073]
[pause: 1.3]
C: Requirement four. Step one: every poll carries the version applied and its age. Step two: the control plane computes version skew and the list of late nodes. Step three: the metrics box turns it into the propagation SLI per region.
C: And for audit: an operator asks Explain with a key and a day, and the sampled decision is joined to the rule history by version. The answer names the rule and the list version in force.
[pause: 1.1]

[slide: v-074]
[pause: 1.3]
C: Requirement five. Step one: an operator, or a gate, halts the stage, so regions not yet reached never receive the bad version. Step two: the control plane tells the origin. A rollback publishes the old content as a new, higher version, and normal distribution carries it.
C: The kill flag is the lighter lever: a field in the manifest that every node reads on its next poll. It is for when a push is bad and the rollback itself needs a minute. Everything is audited.
[pause: 1.1]

[slide: v-075]
[pause: 1.3]
C: The C4 context. A policy owner publishes changes. A platform operator handles rollouts, halts and rollbacks. An external authority supplies a bulk list or a lookup. And the serving fleet, a hundred thousand nodes, receives versions and manifests. Notice who owns what: policy owns content, platform owns the pipe. The contract between them is the propagation target.
[pause: 1.1]

[slide: v-076]
[pause: 1.3]
C: The containers. A policy tool. An ingest service with the rule store. A compiler with the origin storage. The relay tree. A control plane. And, inside each serving process, an enforcement agent: a library that holds the structure, applies updates and answers Check in process. The external authority feeds the rule store by mirror. The serving process calls the agent, with no network between them.
[pause: 1.1]

[slide: v-077]
[pause: 1.3]
C: Publish as a sequence. One: the operator sends the change with an idempotency key. The ingest service normalises, checks limits and the allowlist, and asks for approval if it is large. Two: one transaction writes the rules and takes version N. Three: the compiler is told N exists, and builds the snapshot and the delta with a checksum chained to N minus one. The operator hears accepted, with the version and rollout stage zero.
[pause: 1.1]

[slide: v-078]
[pause: 1.3]
C: Distribute as a sequence. The relay pushes that version N exists. The node asks the manifest with N minus one. The relay replies: inside the window, here is the delta and its checksum. The node verifies the chain and builds beside the old structure. It swaps one pointer: the old list until that instant, the new one after. It writes the snapshot and version to disk, and reports applied with its next poll.
[pause: 1.1]

[slide: v-079]
[pause: 1.3]
C: Enforce. A request arrives with an address. The agent normalises it and checks the allowlist: not allowlisted. Exact lookup, then the longest-prefix range lookup. Verdict: deny, rule forty-four eleven, version eight million three hundred sixty-one thousand and four. And, off the hot path, a sample goes to the decision log.
[pause: 1.1]

[slide: v-080]
[pause: 1.3]
C: Rollback. A gate sees the canary's block rate eight points over baseline, and halts version N: later stages do not receive it. The operator calls rollback to M. The control plane publishes M's content as version N plus one: higher, never reused. The normal path carries it, and the canary nodes' block rate returns to baseline. Nothing about this needed a special channel, except the kill flag for the first seconds.
[pause: 1.1]

[slide: v-081]
[pause: 1.0]
C: Last in the design, what the serving code looks like. At start, the agent loads its last known good copy from disk, so a restart with no network still enforces. On every request, one in-process call and a switch on the verdict. The decision is sampled with its version. And the health endpoint reports the list age, which the load balancer reads. That endpoint is how the staleness bound gets an action.
[pause: 1.0]

[slide: v-082]
[pause: 0.6]
C: Layered rules, in one slide, because it comes up. A global list and a regional list, each with its own versions. A node reads the global one and the list for its own region, and the precedence is fixed: allow beats deny, and a more specific range beats a wider one. It is the same compiler, the same relays and the same gates. Only the artifact's name and its audience differ.
[pause: 0.8]

[pause: 1.4]

## 6 Bridge

[slide: v-083]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-084]
[pause: 1.3]
C: Here is the baseline with seven attack points. A node that fell behind, on the relay-to-node arrow. Changes out of order and overlapping, in the node's apply step. A wrong rule, from the rule store onward. No updates at all. A list too big for a node. A slow external source, at the rule store. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-085]
[pause: 1.2]
C: Seven challenges. Each runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The node that was offline

[slide: v-086]
[pause: 1.2]
N: Challenge one. A node comes back after two hours offline: what should it fetch, and how do we prove it got all of it?
[pause: 1.8]

[slide: v-087]
[pause: 0.6]
I: A node was offline for two hours. How does it catch up? And how do you know all one hundred thousand nodes run version N?
[pause: 2.0]

[slide: v-088]
[pause: 1.3]
C: The first answer most people give: on reconnect, download the whole list again, and check each node's file somehow. Look at the red arrows between the relay and the node. Nothing says what the node should fetch, and nothing proves that what it received is whole. And the file is forty megabytes.
[pause: 1.1]

[slide: v-089]
[pause: 1.0]
C: The trace. A node applied version eight million at two o'clock and lost its uplink. By four the list is at eight million three hundred sixty thousand: three hundred sixty thousand changes missed, about eleven megabytes. Fifty nodes in the zone reconnect together: fifty times forty megabytes, two gigabytes from one relay. And a power cut in the middle of a download leaves a truncated file that the node might load.
C: These numbers are illustrative. The shape is the point: a small difference, a large naive transfer, and no integrity check.
[pause: 1.0]

[slide: v-090]
[pause: 1.3]
C: The fix. The new green box is the manifest. The node sends the version it has. The manifest answers: you are inside the window, take the delta, or you are not, take the snapshot. Every artifact is verified against the chained checksum before anything is applied, and the apply is the atomic swap from before.
[pause: 1.1]

[slide: v-091]
[pause: 1.3]
C: As a sequence. The node, offline for two hours, asks the manifest with its version. The relay answers: current is eight million three hundred sixty thousand, you are inside the window, deltas, about eleven megabytes. Suppose the checksum fails on the last delta. The node discards it and asks again, this time for the snapshot, which the zone relay serves from its cache, one origin fetch for fifty nodes. It verifies, builds beside, swaps, and reports the applied version.
[pause: 1.1]

[slide: v-092]
[pause: 1.0]
C: In code, three branches. Current: nothing to do. Inside the window: take the delta. Outside, or bootstrapping: take the snapshot. If verification fails, discard and try the snapshot, and if that fails too, keep the last good list and report apply-failed. The property is convergence and integrity. And I know the fleet runs version N because every node reports the version it runs. Skew is a metric, not a hope.
[pause: 1.0]

[slide: v-093]
[pause: 0.6]
I: The delta window is twenty-four hours and the node was down for three days. Or the checksum fails again on the snapshot.
[pause: 2.0]

[slide: v-094]
[pause: 0.6]
C: Beyond the window, the manifest simply points to the snapshot, whatever the node's age, and the zone relay's cache makes fifty nodes cost one origin fetch. A checksum that keeps failing means a corrupt artifact at the origin. The node keeps its last known good list, reports apply-failed, and the control plane halts that version.
C: The honest limit: a node that cannot reach anything keeps an old list. That is challenge four.
[pause: 0.8]

[slide: v-095]
[pause: 0.7]
V: If asked, I'd say: every version has a number and a checksum chained to the one before. A node says what it has, and the manifest says whether a small delta or a full snapshot gets it to the present. It verifies before it applies and swaps atomically, so it never serves a half-built list. And I know the fleet is converged because every node reports the version it runs.
[pause: 1.0]
N: That fix creates the next question: in what order do changes apply?
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Order, duplicates, overlap

[slide: v-096]
[pause: 1.2]
N: Challenge two. Changes arrive late, twice, and overlapping each other: how does every node still end at the same answer?
[pause: 1.8]

[slide: v-097]
[pause: 0.6]
I: An add and a remove for the same key arrive in the wrong order. Or the same delta arrives twice. And an operator adds a slash sixteen, and allows a slash twenty-six inside it.
[pause: 2.0]

[slide: v-098]
[pause: 1.3]
C: The naive answer: apply changes in the order they arrive, because the network is mostly in order. Mostly. Look at the node: its apply step believes that arrival order is intent order. Through two relay tiers, with a push and a poll both delivering, that is not true.
[pause: 1.1]

[slide: v-099]
[pause: 1.0]
C: The trace. Version one hundred adds a key by mistake. Version one hundred and one removes it, the correction. The node receives one-oh-one first and one hundred second, by two paths. Applied in arrival order: remove, then add. The final state is banned, though the last intent was remove.
C: Overlap is the second half. Version ninety denies a slash sixteen. Version ninety-seven allows a partner's slash twenty-six inside it. A node that stops at the first range it finds says deny. And two sources can disagree about one key: that needs a written precedence.
[pause: 1.0]

[slide: v-100]
[pause: 1.3]
C: The fix lives in the same node box, outlined green. One: the rule store's transaction assigns the version, so there is a single order to begin with. Two: each key remembers the version of its last change, and a change applies only if its version is higher. A late message, or a duplicate, is a no-op. The result depends on the set of changes, not their order or number.
[pause: 1.1]

[slide: v-101]
[pause: 1.3]
C: As a sequence. Version one-oh-one, remove, arrives first. The node records the key as removed at one-oh-one. Version one hundred, add, arrives late: one hundred is not higher than one-oh-one, ignore. The final state is removed. Version one-oh-one arrives again, a duplicate: not higher than itself, a no-op. The node converges to the intended state whatever the arrival order.
[pause: 1.1]

[slide: v-102]
[pause: 1.0]
C: Precedence, as rules the compiler enforces. An exact entry beats a range. A longer prefix beats a shorter one. At equal specificity, allow beats deny. An allowlist range matches first and always wins. And when two sources disagree, an unexpired manual entry beats a feed. In the example, the partner's slash twenty-six is more specific than the slash sixteen, so the verdict is allow.
C: One detail: the compiler expands an exception inside a range into explicit entries, so the node needs no special case. The node stays simple, and the complexity is in one place that can be tested.
[pause: 1.0]

[slide: v-103]
[pause: 0.6]
I: Tombstones grow forever. And what if the version counter itself is lost or reset after a restore?
[pause: 2.0]

[slide: v-104]
[pause: 0.6]
C: Tombstones are kept only for the delta window. A node older than the window takes a snapshot, which has none, so nothing is resurrected. The version counter lives in the rule store's transaction log, and a restore that would rewind it is refused. After a rebuild, start with a higher epoch. Never reuse a number.
C: One more decision belongs here. Expiry is a command, not a node-side clock. A ban with an expiry becomes an explicit remove, issued by the compiler at that time with its own version. So every node sees the same history, and none depends on its own wall clock.
[pause: 0.8]

[slide: v-105]
[pause: 0.7]
V: If asked, I'd say: I do not trust arrival order. One writer assigns versions, and each key remembers the version of its last change, so a late or duplicate message is ignored. Ranges resolve by longest prefix, and an exception beats a deny. The merge is idempotent, so the same history gives the same list in any order.
[pause: 1.0]
N: Now the content itself: what if the change is wrong?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: The bad push

[slide: v-106]
[pause: 1.2]
N: Challenge three. A correct pipeline delivers a wrong rule to every node in seconds: how do we stop our own speed from hurting us?
[pause: 1.8]

[slide: v-107]
[pause: 0.6]
I: Someone publishes a range that covers a large part of Europe. How fast does it break, and how do you stop it?
[pause: 2.0]

[slide: v-108]
[pause: 1.3]
C: The naive answer: review the change before it goes out, and fix it quickly if it is wrong. Look at the arrows from the rule store through the origin to the relays, all red. Nothing between the author's keystroke and every node asks whether the content is plausible. The pipeline is working perfectly.
[pause: 1.1]

[slide: v-109]
[pause: 1.0]
C: The trace. At two o'clock an operator means a slash twenty-eight and types a slash eight. One line, reviewed by one person, who saw one line added. Three seconds to compile. Twelve to reach the relays. At twenty-one seconds every node serves it. At thirty, eight percent of requests are denied. At forty the on-call is paged, and the fix is another version that takes another eighteen seconds.
C: Illustrative timings, and the share depends on the range. The structure holds: fast in, fast out, and a human in the loop.
[pause: 1.0]

[slide: v-110]
[pause: 0.6]
C: The first line of defence is at ingest. Limits: shape and size, and a cap on how much address space one change may cover, with a second approver above it. An allowlist of ranges that must never be blocked, the company's own, key partners, health checks, checked at compile time and again at enforcement, so it works even if a bad version gets through. And a review that sees the effect, not just the line: this change covers sixteen million addresses.
[pause: 0.8]

[slide: v-111]
[pause: 1.3]
C: The fix. The new green boxes are the validation step, the controller doing staged rollout, and the kill flag carried by the manifest. A stage goes to five percent of nodes, then twenty-five, then everyone, with a five-minute bake each. The controller compares each node's block rate to its own baseline, and a rise of more than a few points trips the gate, freezes the stage and alerts. Rollback is a new, higher version.
[pause: 1.1]

[slide: v-112]
[pause: 1.3]
C: Replay it. Top row, without gates: eighteen seconds to everyone, then eight percent denied for as long as it takes someone to act. Bottom row, with a canary: only five thousand nodes see the bad version. The gate trips within one metrics window, the stage freezes, and a rollback lands as a new version. The exposure is five thousand nodes for about a minute, not a hundred thousand for however long the on-call takes.
[pause: 1.1]

[slide: v-113]
[pause: 1.0]
C: What exactly trips the gate? Block rate per node in a ten-second window against its baseline: more than three points on the canary freezes the stage and alerts. A region's block rate doubling halts and pages. Any checksum failure halts that version. An urgent ban uses a fast path, one region and a sixty-second bake, logged as an exception. Initial targets: the gate is a number, not a person watching a graph.
[pause: 1.0]

[slide: v-114]
[pause: 0.6]
C: One more tool. The action is part of the rule: log only, challenge, or deny. A new or widened rule can ship in shadow mode: nodes record that they would have denied, with the rule id, and no user is affected. The owner reads the counts and promotes it to deny, which is itself a version. For shared addresses, a challenge is a softer answer than a hard block.
[pause: 0.8]

[slide: v-115]
[pause: 0.6]
I: The rule is legitimate-looking and wrong: a real customer's range. The block rate does not move. Or the kill switch rides the same pipe that is broken.
[pause: 2.0]

[slide: v-116]
[pause: 0.6]
C: Two answers. Nodes protect themselves: if a node's block rate jumps by a multiple of its own baseline right after an update, it reverts to the previous version on its own, reports, and pages. And the kill flag is a separate, tiny channel: one field in the manifest that every poll reads, not a new snapshot, so it works even when the artifact path is the broken part.
C: The honest limit: a precise, plausible, wrong rule, such as a real customer's range added by mistake, cannot be found by statistics. It is found by the allowlist, by review of high-impact changes, by the audit trail and a fast removal path. Policy, not mechanism, owns that risk, and I say so.
[pause: 0.8]

[slide: v-117]
[pause: 0.7]
V: If asked, I'd say: the same pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the same discipline as a binary. Validation, an allowlist that always wins, a canary gated on block rate, a kill flag on its own channel, and a rollback that is just a new version. Nodes also protect themselves: if the block rate jumps right after an update, they revert on their own.
[pause: 1.0]
N: So far, updates arrived. What if they stop arriving?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Stale or no control plane

[slide: v-118]
[pause: 1.2]
N: Challenge four. The control plane is stale, partitioned or gone: what does a node do, and who decided that?
[pause: 1.8]

[slide: v-119]
[pause: 0.6]
I: A node cannot reach any relay for three hours. Or the whole distribution plane is down. What does the node do, and who decided?
[pause: 2.0]

[slide: v-120]
[pause: 1.3]
C: The naive answer is a binary: fail closed, deny everything if the list is old, or fail open, serve everything. Look at the node under attack. It has stopped hearing from the relays, and its staleness clock has no action attached to it. Nobody chose what happens. Both defaults are bad, in opposite directions.
[pause: 1.1]

[slide: v-121]
[pause: 1.0]
C: The trace. A node applied its last update at nine and lost all relays. By noon it has missed fifty-four thousand changes, including one ban the policy team called urgent. Fail closed would refuse a hundred and eight thousand legitimate requests from this node alone, and if the whole plane is down, every node fails closed together: a global outage caused by the system built to protect you. Fail open serves everything, including the ban it never heard about.
C: Illustrative numbers. The point is that neither default is a policy. Both are what happens when nobody decided.
[pause: 1.0]

[slide: v-122]
[pause: 1.3]
C: The first move is to separate two things people merge. Stale is not open. A node with an old list keeps blocking every ban it knew about. Only the newest bans are missing. So the question is never block everything or allow everything. It is what to do about the missing new bans, and how long that is acceptable. On the line: fresh, then past a bound an alert, then past a longer bound a stronger action.
[pause: 1.1]

[slide: v-123]
[pause: 1.3]
C: The fix. The node persists its last known good copy, so a restart with no network still enforces. It exposes its list age on its health endpoint, and the load balancer reads it. Each list has a maximum age and an action, chosen by the policy owner. The action is either alert and keep serving, or drain the node out of the load-balancer rotation. Drain, instead of failing each request. The node keeps its last list while it waits for the plane to return.
[pause: 1.1]

[slide: v-124]
[pause: 1.0]
C: Who signs what. Per list class, a bound, an action and an owner, agreed before the incident. Abuse bans: fifteen minutes, alert and keep serving, owned by security. The general list: sixty minutes, drain the node, capped. A legal list: whatever the legal term says, drain and escalate. A node with no list on disk stays out of rotation until it bootstraps. This table is what the interviewer signs.
[pause: 1.0]

[slide: v-125]
[pause: 1.3]
C: As a sequence. The node sees fifteen minutes with no update, past the bound for the abuse list. It reports stale, with its age, to the load balancer. The balancer checks its drain budget, five percent per region, not used up. The node is taken out of rotation but keeps enforcing its last list. When the node reaches a relay again, it applies the delta, reports current, and goes back into rotation.
[pause: 1.1]

[slide: v-126]
[pause: 0.6]
I: Every node passes the bound at once because the control plane is down. You just drained the fleet.
[pause: 2.0]

[slide: v-127]
[pause: 0.6]
C: A drain budget. Automatic draining never removes more than a fixed share of the fleet, say five percent per region. Past that, nodes keep serving and the page goes to a human. The cost is stated: while the plane is down beyond the bound, some nodes serve a stale list, and the owner of the list accepts that in writing.
C: The honest limit: nothing makes a partitioned node learn a ban it cannot hear. The cures are a plane that is not a single point of failure, and a bound short enough to matter. That is a staffing and design question, not something a node can solve alone.
[pause: 0.8]

[slide: v-128]
[pause: 0.7]
V: If asked, I'd say: stale is not open. A node keeps enforcing what it has. For each list, the owner signs a maximum age and an action: alert and keep serving, or pull the node out of rotation. Automatic draining has a cap, so a control-plane outage cannot become a fleet outage. The risk of a late ban is a named decision, not an accident.
[pause: 1.0]
N: Next: what if the list no longer fits on a node?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: The list does not fit

[slide: v-129]
[pause: 1.2]
N: Challenge five. The list grows past a node's memory: what do we keep locally, and what does a false positive cost?
[pause: 1.8]

[slide: v-130]
[pause: 0.6]
I: A hundred million I-P-v-six prefixes. Why not one shared cache lookup per request? And a Bloom filter says maybe. Then what?
[pause: 2.0]

[slide: v-131]
[pause: 1.3]
C: The naive answers. Put everything in a shared cache and call it from every node, or use a Bloom filter and block on a yes. Look at the node box and the request arrow. The exact set no longer fits in memory, and a filter used alone turns its error into a block.
[pause: 1.1]

[slide: v-132]
[pause: 1.0]
C: The numbers. The exact set is a hundred million times seventeen bytes: one point seven gigabytes, against a budget of five hundred and twelve megabytes. A shared lookup is a hard dependency on every request. And a filter used alone, at one percent false positives, blocks ten thousand real users every second at a million requests a second. The filter itself, at ten bits an entry, is a hundred and twenty-five megabytes: it fits.
C: The false-positive rate is a property of the filter's size, a design parameter I choose. It is not something I measure.
[pause: 1.0]

[slide: v-133]
[pause: 1.3]
C: The shape of the fix. A request goes to the local filter. For about ninety-nine percent of traffic it says definitely not listed: allow, with no network call. For the rest, a maybe, the request goes to an exact lookup tier, sharded by key prefix, which returns the verdict. Listed: deny. Not listed, which is a false positive: allow, and cache the answer. Used this way, a false positive costs a lookup, not a wrong block.
[pause: 1.1]

[slide: v-134]
[pause: 1.3]
C: The fix, on the baseline. The new box is the lookup tier. The node's filter answers not listed locally. A maybe goes to the tier, and the answer is cached on the node with a lifetime no longer than the staleness bound. I'd also keep the hottest, most-matched ranges exact and local, so the busiest keys never leave the node. Memory stays within budget, and the path stays local for nearly all traffic.
[pause: 1.1]

[slide: v-135]
[pause: 1.3]
C: As a sequence. A check for an I-P-v-six address arrives. The local filter says maybe. The agent asks the exact tier, and identical concurrent requests are coalesced into one lookup. The answer: not listed, a false positive. Allow, and cache it for sixty seconds. And a per-node lookup budget protects the tier during an attack, which is the next question.
[pause: 1.1]

[slide: v-136]
[pause: 1.0]
C: Where each key is enforced. An address or a range is known at the connection, so the edge enforces it, with a sorted array and a trie. A user I-D is known only after authentication, so it is enforced in the application layer, with the same agent library. A user who arrives from a new address on every request is not a denylist problem: that needs an identity key or an abuse model.
[pause: 1.0]

[slide: v-137]
[pause: 0.6]
I: During an attack nearly every request is a true hit, so every request goes to the lookup tier. What now?
[pause: 2.0]

[slide: v-138]
[pause: 0.6]
C: Three moves. Cache the positive verdict on the node, so repeated hits from one source cost one lookup. Coalesce concurrent lookups for one key, and shard the tier by prefix. And cap lookups per node: past the cap, a node uses cached verdicts and, for an unknown key, its stated policy, so the tier cannot be flooded by the attack it exists to stop.
C: The honest limit: a very large list costs a tier on the request path for hits. We pay that cost only for keys that are likely to be banned, and the rest of the traffic stays fully local.
[pause: 0.8]

[slide: v-139]
[pause: 0.7]
V: If asked, I'd say: a shared lookup per request puts the list service in everyone's availability, and a millisecond on every call. When the set does not fit, I keep a filter locally, which can say definitely not listed, and confirm a maybe with an exact tier, because a false positive blocks a real user. I cache the verdicts, coalesce lookups, and cap the load per node, so an attack does not take down the confirmation tier.
[pause: 1.0]
N: One more source of trouble: when the list comes from someone slow.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A slow external source

[slide: v-140]
[pause: 1.2]
N: Challenge six. One verdict depends on a slow outside source: how do we answer fast without lying about what we know?
[pause: 1.8]

[slide: v-141]
[pause: 0.6]
I: The authority gives you only a lookup A-P-I: one second a call, a hundred calls a second. It is down for two days. And a new ban covers a slash sixteen you already cached verdicts for.
[pause: 2.0]

[slide: v-142]
[pause: 1.3]
C: The naive answer: call the A-P-I on each new address and cache the answer. Look at the adapter and the authority, outlined red. The adapter cannot keep up, and a cache of per-address answers will outlive a wider ban.
[pause: 1.1]

[slide: v-143]
[pause: 1.3]
C: The case. Twenty thousand first-seen addresses a second against a limit of a hundred calls a second. Two hundred times over. Even running all day, a hundred a second gives eight point six million lookups against about fifty million distinct addresses: seventeen percent. These are illustrative numbers. And a request cannot wait a second on a call that is rate limited anyway.
[pause: 1.1]

[slide: v-144]
[pause: 1.0]
C: The cache that lies. An address is checked and allowed, and cached for a day as an address verdict. Later the authority bans the whole slash sixteen that contains it. An hour on, that address is served from the cache: allowed, for another twenty-three hours. The fix is to cache by the rule the authority returns, as a range rule with a version, so a wider ban supersedes address verdicts by version.
[pause: 1.0]

[slide: v-145]
[pause: 1.3]
C: The fix, on the baseline. The new adapter box mirrors into the rule store. First: if there is any bulk list or change feed, mirror it and use the same pipeline as every other list, and use the lookup only to verify. Second, with only a lookup: a cache keyed by range, with a lifetime no longer than the allowed staleness or the legal grace period. Single-flight lookups per key. And a token bucket of a hundred a second, spent on the highest-volume addresses first.
[pause: 1.1]

[slide: v-146]
[pause: 1.3]
C: As a sequence. The agent asks for a verdict on an address. The adapter has no entry, has tokens in its budget, and sends one lookup. The authority answers: banned, covers the slash sixteen, valid for twenty-four hours. The adapter stores a range rule with a version, which supersedes any address verdicts. The agent gets deny. And if the authority is down, the adapter serves expired entries inside a grace period, flags the decisions it made on expired data, and alerts.
[pause: 1.1]

[slide: v-147]
[pause: 0.6]
I: The API is down for two days, and your cache lifetime is one day.
[pause: 2.0]

[slide: v-148]
[pause: 0.6]
C: A grace period. Serve expired verdicts for a stated number of days, flag every decision made on expired data in the log, and alert. The legal owner decides how many days. The exposure is first-seen addresses during the outage, which I reduce by spending the budget on the highest-volume ones first and by asking for a bulk feed.
C: The honest limit: with only a slow lookup, full coverage is not possible. I say so, and I ask for a better source.
[pause: 0.8]

[slide: v-149]
[pause: 0.7]
V: If asked, I'd say: I never call a slow authority on the request path. If there is a bulk list, I mirror it. If there is only a lookup, I cache verdicts for no longer than the allowed staleness, coalesce lookups, spend the rate budget on the highest-volume addresses, and write down what happens on a first-seen address and on an outage. Full coverage is not possible, so I say how much we have, and I ask for a better feed.
[pause: 1.0]
N: Last question: how would you know?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: How would you know?

[slide: v-150]
[pause: 1.2]
N: Challenge seven. Every machine is green and the promise is broken: how would we know?
[pause: 1.8]

[slide: v-151]
[pause: 0.6]
I: A ban was published an hour ago and one region is still serving the banned source. The dashboard is green. How would you have known?
[pause: 2.0]

[slide: v-152]
[pause: 1.3]
C: The naive answer: watch the C-P-U and the error rate of the relays. Look at the picture: the relay box is outlined, and it is the box the dashboard watches. It is green. The promise is broken somewhere that dashboard does not look.
[pause: 1.1]

[slide: v-153]
[pause: 1.0]
C: The case. The relays report a hundred percent healthy, origin latency forty milliseconds: green. But in one region, four percent of nodes are a version behind. The push to one zone fails quietly, and polls hit a relay cache that is stale. Meanwhile the block rate in that region is point two percent against point five elsewhere. A ban did not land.
C: Illustrative numbers. The shape holds: every machine metric is fine, and one pair of numbers says otherwise.
[pause: 1.0]

[slide: v-154]
[pause: 1.3]
C: The fix: a metrics and probe box fed by the controller. The service level indicators describe the promise, not the machines. And a synthetic probe: a banned key published on a schedule, with a request sent through the real path to check that it is denied within thirty seconds, in every region. Decisions are logged with their rule version, so an audit has an answer.
[pause: 1.1]

[slide: v-155]
[pause: 1.0]
C: The indicators, on the promise. Version skew: the share of nodes on the current version within thirty seconds, at least ninety-nine point nine percent per region. Propagation lag, at the ninety-nine point ninth percentile. List age per node against its bound. Apply failures and checksum mismatches, near zero. Block rate against its baseline, per version. And the lookup tier's hit rate. All initial targets.
[pause: 1.0]

[slide: v-156]
[pause: 1.0]
C: Read metrics in pairs, so each page names a cause. Skew up with one zone's relay cache age up: a stale relay cache. Block rate down in one region with that region's version behind: a ban that did not land, tonight's case. Block rate up with a new version: a bad rule, so the gate, not the relay. Apply failures with checksum mismatches: a corrupt artifact at the origin. One metric says something is wrong. Two say where.
[pause: 1.0]

[slide: v-157]
[pause: 1.3]
C: The probe as a sequence. Every five minutes the probe publishes a synthetic banned key as a new version. Normal distribution carries it. Then the probe sends a request from the synthetic key through the real path, in each region. In a healthy region the answer is deny within thirty seconds. If a region still allows it after thirty seconds, the probe pages, with that node's applied version attached. This tests the whole chain every time, not each part.
[pause: 1.1]

[slide: v-158]
[pause: 0.6]
I: The probe passes and a real ban is still missing. Or the block rate is flat because traffic bypasses the enforcement point.
[pause: 2.0]

[slide: v-159]
[pause: 0.6]
C: Two answers. Skew is measured per node, from reports, not only from probes: a node that is behind shows up even when the probe's key got through. And coverage is a metric: the share of traffic that passes through an enforcement point, and a counter of requests that skipped the check, so a flat block rate cannot hide a bypass.
C: The honest limit: we can detect a late ban after the fact and alarm on its precursors. We cannot observe an absence of risk.
[pause: 0.8]

[slide: v-160]
[pause: 0.7]
V: If asked, I'd say: I alert on the promise. The share of nodes on the current version within thirty seconds, per region, plus a synthetic banned key sent through the real path. I read metrics in pairs so each page names a cause, and every decision logs the rule version so an auditor gets an answer. A green relay dashboard says nothing about whether a ban landed.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-161]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: A denylist system is not one project. It is three, and they differ by an order of magnitude.
[pause: 1.8]

[slide: v-162]
[pause: 1.0]
C: Three releases, called R-zero, R-one and R-two so nobody confuses them with design versions. A prototype with one list: a rule store, a compiler, a snapshot in object storage, a ten-second manifest poll and an atomic swap. About a month or two.
C: Production is R-one: versions and deltas, the relay tree, checksums, validation, staged rollout, a kill flag, reports, a console and audit. Four engineers for five or six months: eighteen to twenty-four engineer-months. A platform is R-two: push streams, layered rules, the lookup tier. Fifty to ninety. The best question is which of these we are asked for, and who owns the first list.
[pause: 1.0]

[slide: v-163]
[pause: 1.0]
C: R-one in detail. A tech lead for the version model and the merge. A senior backend engineer for the rule store, compiler and relays. A backend engineer for the agent, the console and the first migration. A full-time S-R-E, because the rollout is operations. Phases: three weeks of design review with the policy owner, four for a walking skeleton, six for correctness with a convergence harness under injected faults, five for safety, four for operations, and four for shadow mode, then cutover.
C: One assumption to state: if there is no named owner and first list, the right decision is not to build.
[pause: 1.0]

[slide: v-164]
[pause: 0.6]
C: Ownership. Twenty-two engineer-months to build. Then about one and a half people for five years, which is ninety. A hundred and twelve in total, about nine engineer-years, and infrastructure is a small share of it. All illustrative. People dominate. And a pipeline with no owner becomes an incident with no owner.
[pause: 0.8]

[slide: v-165]
[pause: 1.0]
C: Build, adopt, buy, or don't. Don't: use the edge provider's managed I-P sets. Two weeks to a pilot. Check first, every time. Adopt a configuration-distribution fabric for transport, with our own compiler, gates and audit: about eight weeks. The hybrid, build the compiler, the gates and the audit and buy the transport, is my R-one pick if a transport exists. Build everything: about a hundred and twelve engineer-months, justified for lists beyond managed limits, custom keys, layered rules and audit.
C: I would write the buy-versus-build memo before any code, with the first list owner's commitment in it.
[pause: 1.0]

[slide: v-166]
[pause: 0.6]
C: What I would never cut: versions with checksums, a staged rollout with a gate, the allowlist, a kill flag, last known good on disk, and the version in the decision log. What I'd cut first: push streams, because the ten-second poll meets the target, regional layers, the second key type, the lookup tier and the console.
C: Top risks. A bad rule: gates, the allowlist, and a game day that practises one. Owner ambiguity: policy writes the list, platform owns the pipe, and the propagation target is the contract between them. The control plane as a single point: a drain budget, and nodes that work without it. No adopter: a named first list before any code. And scope creep into a general configuration platform.
[pause: 0.8]

[slide: v-167]
[pause: 0.6]
C: Staffing. Start small, because design by committee is slow. Grow in the middle where the work parallelises: the agent, the compiler and the console. Do not add people while stabilising. Share the on-call with the team that runs the sibling rollout system.
V: The question I ask before saying yes: what does a wrong block cost, who decides, and how fast must a ban land?
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-168]
[pause: 1.2]
C: Four minutes to close. One picture, one sentence per path, the contract between the owners, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-169]
[pause: 1.3]
C: The final picture. The policy tool, and ingest with validation and an allowlist. The rule store with one version order. The origin and the relay tree with push and a ten-second manifest poll. The enforcement node with an atomic swap, a last known good copy and a lookup tier behind a filter. A controller with gates and a kill flag, a load balancer that drains stale nodes, a mirror for a slow source, and metrics with probes. Every box was added to answer one question the design raised.
[pause: 1.1]

[slide: v-170]
[pause: 1.0]
C: Five paths, one sentence each. Publish: validate, approve, one transaction, one version. Distribute: manifest, then a delta or a snapshot, verify the chain, swap one pointer. Enforce: allowlist, exact key, longest prefix, with the version in the verdict. Explain: the version joins the rule history. Roll back: a new, higher version, and a kill flag on its own channel.
[pause: 1.0]

[slide: v-171]
[pause: 1.0]
C: Seven fixes, each naming the property it protects. One: manifest, window and chained checksums, for convergence and integrity. Two: one version order and a per-key version, for the intended state. Three: validation, the allowlist, canary gates, the kill flag and a local breaker, for safety against the wrong block. Four: a signed bound and an action. Five: a filter, an exact tier and a cache. Six: a mirror, a range cache and a stated policy. Seven: skew, probes and coverage.
[pause: 1.0]

[slide: v-172]
[pause: 0.6]
C: Two owners, and a contract. Policy owns what is listed, the reason, the allowlist, the action on a match, the signed staleness bound, and the risk of a late ban. Platform owns the pipeline, the versions, the gates, the indicators, and the propagation target: ninety-nine point nine percent of nodes within thirty seconds. That number is the contract between them.
C: And a bad denylist is a global outage, so a push gets the same discipline as a binary.
[pause: 0.8]

[slide: v-173]
[pause: 0.6]
C: If asked about a second key type, a user I-D. Same pipeline: the rule store, compiler, relays, gates and audit, with the key kind as a field. A different enforcement point: after authentication, in the application layer, with the same agent library. And possibly a different bound, which the owner signs. Nothing about the design had to change, which is why I did not design it out.
[pause: 0.8]

[slide: v-174]
[pause: 0.6]
C: Ten mistakes in this round. In the design: a lookup per request on the path. Eventually consistent with no number. No versions or checksums. Trusting arrival order. A full download per node per change.
C: In judgment: failing closed fleet-wide, or open without saying so. Never asking who owns the failure policy. A Bloom filter used as a verdict. One big push with no canary and no allowlist. And a green relay dashboard as proof that a ban landed.
[pause: 0.8]

[slide: v-175]
[pause: 0.7]
V: The check is local because it has to be fast and independent. The list cannot be local, so I gave it versions, a bound on how old it may be, and the discipline of a release. Everything I built is there so that a ban lands quickly and a mistake does not.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
