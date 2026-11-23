# SD-24 Distributed lock service: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A lock service sounds like a small problem. A key, an owner, an expiry. This question is not testing whether you can draw that. It is testing whether you notice what a lock cannot promise, and what you do about it.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design a distributed lock service that other teams use to make sure only one process does a thing at a time.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook. Holder A takes a lock and gets token forty-one. Then A freezes, for fifteen seconds. A garbage collection pause is enough.
C: At ten seconds the lease expires. The lock service is correct to expire it. Holder B asks, and gets token forty-two. B writes.
C: At fifteen seconds A wakes up. It has no idea time passed. It writes too. Two writers. The network was fine and no component misbehaved. The lock service's idea of who holds the lock and the resource's idea of who may write are different things, and nothing connects them.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes.
[reveal: v-005]
[pause: 0.45]
N: The weak signal on each is the same shape:
[reveal: v-006]
[pause: 0.45]
N: the happy path, drawn well.
[reveal: v-007]
[pause: 0.45]
N: The strong signal is what happens when the happy path fails.
[reveal: v-008]
[pause: 0.45]
C: I will keep that table in mind.
[reveal: v-009]
[pause: 0.45]
C: Correctness and operations are where I plan to spend the most time.
[pause: 1.0]

[slide: v-010]
[pause: 0.7]
V: A lock service says who should be working. Only the resource says who is allowed to write.
[pause: 1.0]
C: So my design has three layers. A lease, so a dead holder frees its lock. Consensus, so the record of who holds it survives failures and gives an order. And a fencing token, checked at the resource, which is what actually makes it safe.
[pause: 1.6]

[slide: v-011]
[pause: 0.6]
C: I'll go in this order.
C: Requirements and scope.
C: Then numbers.
C: Then a short theory chapter, because the design leans on it.
[reveal: v-012]
[pause: 0.45]
C: Then API and data, and a high-level design in three versions, each answering the objection to the one before.
[reveal: v-013]
[pause: 0.45]
C: Then the part I care most about: seven challenges that break the design, one at a time, where each fix creates the next question.
C: A build cost, because someone has to own this.
C: And a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: Before I draw anything, I want to ask six questions. Each answer will change the design.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: Who calls this, and for what?
I: Internal teams.
I: Background workers electing a leader.
I: Per-entity exclusion before a write.
I: And some run-this-job-once schedulers.
C: Three different uses.
C: Leader election wants a long hold.
C: Exclusion before a write wants a short one.
C: Run-once wants no waiting at all.
C: One API has to serve all three.
[pause: 0.6]

[slide: v-016]
[pause: 0.6]
C: What happens if two holders act at once?
I: It depends on the team.
I: For some it corrupts records.
I: For some it wastes an hour of compute.
I: I'd like you to tell me how you would find out.
C: That is the most important answer so far.
C: It splits locks into two kinds.
C: If a double hold only wastes work, I call it an efficiency lock.
C: If it corrupts data, it is a correctness lock.
C: They need very different designs, and I'll ask every team which one they have.
[pause: 0.6]

[slide: v-017]
[pause: 0.6]
C: And the scale?
I: About ten thousand acquisition attempts a second.
I: Around five thousand lock names.
I: Holds from a hundred milliseconds to thirty seconds.
I: Default lease, ten seconds.
C: Attempts, not grants.
C: I'll use that difference in the estimates.
[pause: 0.6]

[slide: v-018]
[pause: 0.6]
C: Latency, availability and failure?
I: p99 acquisition under twenty milliseconds.
I: It must survive the loss of a minority of nodes.
I: One region, three zones.
I: Multi-region is a later question.
C: Twenty milliseconds in one region is a quorum round trip, not a cross-region one.
C: That rules out stretching one group across regions.
[pause: 0.6]

[slide: v-019]
[pause: 0.6]
C: What are the resources being protected, and who calls?
I: Mostly SQL databases and an object store.
I: A few call partner H-T-T-P A-P-Is.
I: Callers are J-V-M services.
I: Assume stop-the-world pauses up to fifteen seconds in the tail.
I: That is a fact, not a tuning problem.
C: Good.
C: Two things.
C: The pause is now a requirement, so the design must be safe when a holder stops for fifteen seconds.
C: And partner A-P-Is are a problem I will come back to.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: Do callers need several locks at once, shared read locks, or strict order?
I: Several at once, some do.
I: Tell me what you'd say.
I: Shared mode, no.
I: Strict first-come order is not required.
C: I'll scope out shared mode.
C: I'll push back on several at once, and explain why in challenge six.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: Functionally, five things.
C: One, acquire an exclusive lock on a name, with a bounded wait.
[reveal: v-022]
[pause: 0.45]
C: Two, hold it and renew it, and find out fast if it is lost.
[reveal: v-023]
[pause: 0.45]
C: Three, release it, and have a dead holder's locks freed automatically.
[reveal: v-024]
[pause: 0.45]
C: Four, and this is the one people forget: every grant carries a strictly increasing token that the caller can hand to the resource.
[reveal: v-025]
[pause: 0.45]
C: And five, operators can inspect a name and force-revoke it, with an audit trail.
C: Each of these gets its own numbered flow later.
[pause: 0.8]

[slide: v-026]
[pause: 0.6]
C: The numbers.
C: They are initial targets, and I'll say so once for this chapter: none of these is a measurement.
C: Acquire p99 under twenty milliseconds, because a lock sits inside someone's request.
[reveal: v-027]
[pause: 0.45]
C: Availability of ninety-nine point nine nine percent, about four point three minutes a month.
[reveal: v-028]
[pause: 0.45]
C: A default lease of ten seconds, capped at sixty.
[reveal: v-029]
[pause: 0.45]
C: And survive the loss of two of five replicas without anyone being paged to fix it.
[pause: 0.8]

[slide: v-030]
[pause: 0.6]
C: Three promises that are not numbers.
C: If the service cannot decide, the protected operation does not proceed.
[reveal: v-031]
[pause: 0.45]
C: That is failing closed, and it is a choice I'm making now, not later.
C: A dead holder's name frees within one lease.
[reveal: v-032]
[pause: 0.45]
C: And tokens never go backwards, including after a disaster recovery.
C: That last one sounds obscure.
C: It will matter in challenge four.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: In scope: exclusive named leases with a bounded wait, sessions, tokens, operator tools, one region, and per-tenant quotas.
C: Out of scope, and I'm saying so on purpose. Shared and read-write modes: I'll add them behind the same A-P-I if someone needs them. Atomic multi-name acquire: that needs a transaction across groups, and I'll push back. Cross-region consensus: a quorum across regions cannot meet twenty milliseconds. And a general-purpose key-value store. That last one I'll write down as a non-goal, because it is how lock services get ruined.
[pause: 0.8]

[slide: v-034]
[pause: 0.6]
C: This split runs through everything that follows.
C: An efficiency lock avoids duplicate work.
C: If it fails once in a while, you waste some compute.
[reveal: v-035]
[pause: 0.45]
C: A correctness lock protects data.
C: If it fails, you corrupt something.
C: I treat them differently, and I ask every team which they have.
[reveal: v-036]
[pause: 0.45]
C: Many say correctness and mean efficiency.
C: Some say efficiency and mean correctness.
C: Most of what people call a lock problem is really an idempotency problem, and I'll come back to that.
[pause: 0.8]

[slide: v-037]
[pause: 0.7]
V: The core is four things. A lease that frees itself. A consensus-replicated record of who holds it. A token that orders the grants. And a check at the resource.
[pause: 0.8]
N: Notice what the candidate did in six minutes. They asked what a double hold costs, cut four things out loud, and attached numbers. That is the framing signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-038]
[pause: 1.2]
C: Now the numbers. Every one is arithmetic from the inputs, and carries a label: given, illustrative, or an initial target. Each one has to change a decision, or I'll drop it.
[pause: 1.8]

[slide: v-039]
[pause: 0.6]
C: Ten thousand attempts a second, given.
[reveal: v-040]
[pause: 0.45]
C: Multiply by a peak factor of three, which I'm assuming, because work tends to start at the top of the hour.
[reveal: v-041]
[pause: 0.45]
C: That is thirty thousand at peak.
[reveal: v-042]
[pause: 0.45]
C: Decision: I size for the peak, not the average.
[pause: 0.8]

[slide: v-043]
[pause: 1.0]
C: Here is a number the prompt hides.
C: One holder per name, around five thousand names.
[reveal: v-044]
[pause: 0.45]
C: So at most five thousand locks can be held at any instant.
C: With a mean hold of half a second, that caps grants at ten thousand a second, and only if every name is always held.
[reveal: v-045]
[pause: 0.45]
C: So most of the ten thousand attempts cannot succeed.
C: They fail, or wait.
[reveal: v-046]
[pause: 0.45]
C: Decision: the A-P-I needs a bounded wait and an explicit try-once, because failure is the normal case on a busy name.
[pause: 1.0]

[slide: v-047]
[pause: 1.0]
C: Assume forty percent of attempts succeed: four thousand grants a second.
[reveal: v-048]
[pause: 0.45]
C: Little's law says the number held at once is the arrival rate times the time held: four thousand times half a second, two thousand locks.
C: Split that.
[reveal: v-049]
[pause: 0.45]
C: Two percent of grants are long holds, about twenty seconds, think leader election: eighty a second times twenty is sixteen hundred.
C: The short ones are about four hundred.
[reveal: v-050]
[pause: 0.45]
C: Almost all the held locks are the long ones.
C: Remember that for renewals.
[pause: 1.0]

[slide: v-051]
[pause: 0.6]
C: Five thousand entries at about two hundred bytes each is one megabyte.
[reveal: v-052]
[pause: 0.45]
C: The whole state fits in memory and snapshots in milliseconds.
[reveal: v-053]
[pause: 0.45]
C: Decision, and a common mistake to avoid: we shard for write throughput and for blast radius.
[reveal: v-054]
[pause: 0.45]
C: We never shard because the data is big.
C: It is not.
[pause: 0.8]

[slide: v-055]
[pause: 1.0]
C: Each grant is one committed write, and so is each release.
C: Two times four thousand is eight thousand writes a second on average.
[reveal: v-056]
[pause: 0.45]
C: Times three is twenty-four thousand at peak.
[reveal: v-057]
[pause: 0.45]
C: Add waiter enqueues and expiries and I call it thirty thousand all-in.
C: Failed try-once attempts don't write.
[reveal: v-058]
[pause: 0.45]
C: The leader answers them from memory under its leader lease.
C: That is why the attempts number is so much larger than the writes number.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: One group's ceiling is the number I trust least, so it carries a label: fifteen thousand committed writes a second, with batched disk syncs, as an initial target I'll measure.
[reveal: v-060]
[pause: 0.45]
C: Thirty thousand divided by fifteen thousand times one half headroom is four groups.
[reveal: v-061]
[pause: 0.45]
C: I'll hash names into sixty-four slots, so I can move slots later.
[reveal: v-062]
[pause: 0.45]
C: One group nearly carries the average.
C: We shard for the peak, and so a bad group takes a quarter of the names, not all of them.
[pause: 1.0]

[slide: v-063]
[pause: 1.0]
C: Renewals.
C: A short hold, a hundred milliseconds, never renews, because the lease is ten seconds.
C: Only holds longer than a third of the lease do, about three point three seconds.
C: That is the sixteen hundred long-held locks.
[reveal: v-064]
[pause: 0.45]
C: Renewing each one every three point three seconds is about four hundred and eighty a second.
C: If instead each client process keeps one session alive, and locks hang off the session, with four hundred clients that is about a hundred and twenty.
[reveal: v-065]
[pause: 0.45]
C: And a dead client is one expiry, not fifty.
C: Decision: sessions.
[pause: 1.0]

[slide: v-066]
[pause: 1.3]
C: The latency budget. Twenty milliseconds at p99 is an initial target. Two milliseconds of network in. Three of batch wait. Four for the leader to sync its disk. Five for a follower round trip and its own sync. One to apply and reply. Two of network out.
C: That is seventeen, with three milliseconds spare. It only works because the quorum is in one region, across three zones. A cross-region quorum costs thirty to two hundred and fifty milliseconds by itself. Also: stage p99s don't add up to an end-to-end p99. This is a planning budget. I'd measure the whole path.
[pause: 1.1]

[slide: v-067]
[pause: 1.0]
C: Two numbers that settle arguments.
C: A fifteen-second pause beats a ten-second lease.
C: Raise the lease to sixty and a seventy-second migration still beats it, while every real crash now stalls its name for a minute.
C: Tuning the lease cannot fix this.
[reveal: v-068]
[pause: 0.45]
C: A token can.
C: And one name can grant at most one over the hold time: ten a second at a hundred milliseconds.
C: A name asked forty times a second is four times over, however many machines I add.
[pause: 1.0]

[slide: v-069]
[pause: 1.0]
C: Three more.
C: Clock drift of two hundred parts per million over a ten-second lease is two milliseconds.
C: The client will stop at seven seconds and the server waits ten, so there is a three-second gap.
[reveal: v-070]
[pause: 0.45]
C: Drift is not the risk.
C: Pauses are.
C: The availability target gives two hundred and fifty-nine seconds a month.
C: At two seconds an election, about a hundred and thirty elections a group spend all of it.
[reveal: v-071]
[pause: 0.45]
C: So elections per day becomes something I watch.
C: And a token is sixteen bits of epoch plus forty-eight bits of log index.
C: Forty-eight bits lasts about six hundred years at fifteen thousand a second.
C: All of these are labelled arithmetic, not measurements.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-072]
[pause: 1.2]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what a lock service is and is not, the two properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide in this chapter has a theory badge.
[pause: 1.8]

[slide: v-073]
[pause: 0.7]
V: A distributed lock service is a small, consensus-replicated store of named leases. It gives one holder at a time permission to act on a name, for a bounded time, together with a number that orders every grant on that name.
[pause: 1.0]
C: Every clause carries weight. Consensus-replicated, so a failover cannot forget a grant. Named, so locks are independent and can be sharded. Bounded time, because we cannot tell a dead holder from a slow one. And a number that orders, which is the part the resource needs.
[pause: 1.6]

[slide: v-074]
[pause: 0.6]
C: Three neighbours.
C: It is not a mutex.
C: A mutex lives in shared memory and can stop the holder.
C: A distributed lock cannot reach into a paused process and stop it.
[reveal: v-075]
[pause: 0.45]
C: It is not a queue: there is no payload and no ordering of work.
C: If a team wants one at a time per entity, in order, they want a single writer per partition.
C: And it is not a transaction.
[reveal: v-076]
[pause: 0.45]
C: It protects nothing on its own.
C: The resource has to take part.
C: Leader election is a use of a lock, not a different thing.
[pause: 0.8]

[slide: v-077]
[pause: 0.6]
V: Safety: two parties must never both act as the holder, with both effects taking hold at the resource.
[reveal: v-078]
[pause: 0.45]
V: Liveness: a free name is eventually granted, a dead holder's name is eventually freed, and a waiter is eventually served or told no.
[pause: 0.8]
C: A service that grants nothing is perfectly safe.
[reveal: v-079]
[pause: 0.45]
C: A service that grants everything is perfectly live.
C: The engineering is in getting enough of both.
C: From now on, every fix says which property it protects.
[pause: 0.8]

[slide: v-080]
[pause: 0.6]
C: There is a result from the nineteen-eighties, F-L-P.
C: In an asynchronous network, if even one process can fail, no protocol can both always agree and always finish.
[reveal: v-081]
[pause: 0.45]
C: Real systems add a timing assumption, usually a timeout, and then pick which property to give up.
C: Consensus systems keep safety unconditional and lose liveness during a partition.
[reveal: v-082]
[pause: 0.45]
C: A group without a majority stops, rather than risk two leaders.
C: That is my position as well, and I'll state it whenever it matters.
[pause: 0.8]

[slide: v-083]
[pause: 1.3]
C: Here is the tension everything comes from. When a holder goes quiet, the service cannot tell whether it crashed or is only slow. So the service does not try to detect death. It makes the grant expire.
C: Then the lease length is a trade. A short lease frees a crashed holder's name quickly, but expires slow holders that are still alive. A long lease does the opposite. The default is ten seconds. Our pause is fifteen. And no setting on this line removes the pause. Remember that.
[pause: 1.1]

[slide: v-084]
[pause: 0.6]
C: Mechanism one, the lease.
C: It protects liveness.
[reveal: v-085]
[pause: 0.45]
C: A grant is valid for a stated time, after which the service may reassign the name without asking.
[reveal: v-086]
[pause: 0.45]
C: That rules out a lock held forever by a dead holder.
[reveal: v-087]
[pause: 0.45]
C: It costs two things: a slow holder can lose its lock while alive, and a crash stalls that name for up to one lease.
[pause: 0.8]

[slide: v-088]
[pause: 0.6]
C: Mechanism two, a consensus-replicated record.
C: It protects the safety of the grant record.
[reveal: v-089]
[pause: 0.45]
C: Every grant is an entry committed by a majority, with one leader per term.
C: A stale leader cannot get a majority, so it cannot commit.
[reveal: v-090]
[pause: 0.45]
C: That rules out split brain, and a failover that forgets a grant.
[reveal: v-091]
[pause: 0.45]
C: It costs a quorum round trip on every write, an outage without a majority, and a cluster to run.
[pause: 0.8]

[slide: v-092]
[pause: 0.6]
C: Mechanism three, the fencing token.
C: This is the one that makes the design safe.
[reveal: v-093]
[pause: 0.45]
C: Each grant carries a number larger than every earlier grant for that name.
C: The resource remembers the highest number it has accepted and rejects anything smaller.
[reveal: v-094]
[pause: 0.45]
C: That rules out a paused holder's stale write.
C: It costs one number per protected row, and the resource has to take part.
[reveal: v-095]
[pause: 0.45]
C: Note the last cost: it orders writes, but it does not by itself make a multi-step read consistent.
C: Challenge one comes back to that.
[pause: 0.8]

[slide: v-096]
[pause: 0.6]
C: Mechanism four, clocks.
C: A wall clock can jump forwards or backwards.
[reveal: v-097]
[pause: 0.45]
C: A monotonic clock only measures elapsed time on one machine.
C: So the client times its lease from the moment it sent the request, on a monotonic clock, and gives up at seventy percent of the lease.
[reveal: v-098]
[pause: 0.45]
C: That rules out clock steps and skew.
[reveal: v-099]
[pause: 0.45]
C: It costs thirty percent of the lease, and it still assumes drift is bounded.
[pause: 0.8]

[slide: v-100]
[pause: 0.6]
C: Mechanism five, sessions.
[reveal: v-101]
[pause: 0.45]
C: A client keeps one session alive with one heartbeat, and its locks hang off the session.
C: When the session dies, all its locks free in one command.
[reveal: v-102]
[pause: 0.45]
C: That rules out renewal storms and fifty separate expiries.
[reveal: v-103]
[pause: 0.45]
C: It costs a coarser failure unit: one missed heartbeat drops every lock the client holds.
[pause: 0.8]

[slide: v-104]
[pause: 0.6]
C: Mechanism six, determinism.
[reveal: v-105]
[pause: 0.45]
C: Every replica applies the same entries in the same order.
[reveal: v-106]
[pause: 0.45]
C: If a replica read its own clock while applying, replicas would diverge, and a diverged lock service is an unrecoverable incident.
[reveal: v-107]
[pause: 0.45]
C: So the leader writes the time into the entry, and expiry is itself a replicated command.
C: It costs a little delay on expiry, and a new leader must work out which expiries are pending.
[pause: 0.8]

[slide: v-108]
[pause: 0.6]
C: Mechanism seven, bounded wait with directed hand-off.
[reveal: v-109]
[pause: 0.45]
C: Waiters queue per name with a cap.
C: A release grants directly to the head of the queue in the same committed step.
[reveal: v-110]
[pause: 0.45]
C: That rules out the herd, the unbounded queue, and polling.
[reveal: v-111]
[pause: 0.45]
C: It costs queue state in the replicated machine, and first-come ordering adds some tail latency.
[pause: 0.8]

[slide: v-112]
[pause: 1.0]
C: Now the options.
C: Six approaches, each with the failure that rules it out.
C: Three that look cheap first.
C: A, one cache node with set-if-absent and an expiry.
C: Replication is asynchronous, so the primary can acknowledge a grant and die before the copy arrives.
C: The new primary has no record and grants it again.
[reveal: v-113]
[pause: 0.45]
C: Fine for an efficiency lock.
C: Never claim it as a correctness lock.
C: B, a quorum of independent cache nodes.
C: It tries to fix that, but its safety rests on timing: a pause between acquiring and using, or one node's clock jumping, breaks it.
C: And it issues no token.
C: It is a well known debate, and I know it, but I would not propose it for correctness.
[reveal: v-114]
[pause: 0.45]
C: C, a relational row.
C: Underrated.
C: With synchronous commit it is safe, and a version column is a token.
C: It fails above a few thousand grants a second, or on a hot row.
C: And a plain row lock is tied to a connection, so it has no lease.
C: If the protected resource is in that same database, the lock and the work commit together, and the whole problem mostly disappears.
[pause: 1.0]

[slide: v-115]
[pause: 1.0]
C: Here are all six.
[reveal: v-116]
[pause: 0.45]
C: D is a consensus-backed coordination store, the ZooKeeper, etcd or Consul family.
[reveal: v-117]
[pause: 0.45]
C: It has leases, compare-and-set, and a revision number that is a ready-made token.
[reveal: v-118]
[pause: 0.45]
C: It fails when load exceeds one cluster, and then I shard.
C: Or when I need semantics it cannot express.
[reveal: v-119]
[pause: 0.45]
C: E, building my own consensus service, has the same safety and gives me full control, and it is far more expensive to run.
C: It fails if I cannot staff it.
[reveal: v-120]
[pause: 0.45]
C: F is no lock at all: a conditional write or an idempotency key at the resource.
C: It fails when the operation is not idempotent and the resource has no conditional write.
V: I pick D, after asking whether F applies.
[pause: 1.0]

[slide: v-121]
[pause: 0.6]
C: What the pick gives up, said plainly.
C: One cluster's write ceiling, so I'll shard in challenge five.
[reveal: v-122]
[pause: 0.45]
C: Fairness, priority and shared modes, which that store does not express.
C: Cross-region reach.
C: And the burden of running a consensus cluster, which is real.
[reveal: v-123]
[pause: 0.45]
C: What it buys: safety proven by someone else's consensus, leases and a revision number built in, and, behind my own A-P-I and S-D-K, the ability to swap the substrate later if evidence says I should.
C: And before any of it, I always ask whether row F applies.
[pause: 0.8]

[slide: v-124]
[pause: 0.6]
C: If asked why not a row lock in a relational database.
C: No lease: the lock lives as long as the connection, so a paused client keeps it.
[reveal: v-125]
[pause: 0.45]
C: No token: nothing the resource can check later.
[reveal: v-126]
[pause: 0.45]
C: It is the right answer when the resource lives in the same database, so the lock and the work commit together, or when the load is under a few thousand a second.
C: Saying that is a better answer than reaching for a consensus cluster by reflex.
[pause: 0.8]

[slide: v-127]
[pause: 1.0]
C: Last part.
C: The failure catalogue, which becomes the challenge list.
C: F-one, a holder crashes.
C: The lease handles that, and the flows show it.
[reveal: v-128]
[pause: 0.45]
C: F-two, a holder pauses and resumes: challenge one.
[reveal: v-129]
[pause: 0.45]
C: F-three, the resource cannot check a token, or no lock is needed at all: challenge two.
[reveal: v-130]
[pause: 0.45]
C: F-four, clocks: challenge three.
[reveal: v-131]
[pause: 0.45]
C: F-five, the leader fails, a partition, or the whole group is lost: challenge four.
[pause: 1.0]

[slide: v-132]
[pause: 1.0]
C: F-six, duplicates, stale releases and delayed messages.
C: I design those out in the A-P-I, so they are not a challenge: release takes the token, and acquire carries a request id.
[reveal: v-133]
[pause: 0.45]
C: F-seven, a load peak: challenge five.
[reveal: v-134]
[pause: 0.45]
C: F-eight, a hot name, a herd or several locks: challenge six.
[reveal: v-135]
[pause: 0.45]
C: F-nine, a holder that is hung but alive: bounded leases and force revoke.
[reveal: v-136]
[pause: 0.45]
C: And F-ten, nobody notices: challenge seven.
C: Seven challenges, in that order.
[pause: 1.0]

[slide: v-137]
[pause: 1.0]
N: Good theory has a consequence for the design.
[reveal: v-138]
[pause: 0.45]
N: Look at this table:
[reveal: v-139]
[pause: 0.45]
N: every mechanism names the property it serves,
[reveal: v-140]
[pause: 0.45]
N: and where it will be used.
[reveal: v-141]
[pause: 0.45]
C: That is the vocabulary.
[reveal: v-142]
[pause: 0.45]
C: On to the design.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-143]
[pause: 1.2]
C: The A-P-I before the boxes. It is the contract, and it shows whether I've thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes.
[pause: 1.8]

[slide: v-144]
[pause: 1.0]
C: Session calls. OpenSession takes an owner name and a lease length, capped at sixty seconds, and returns a session id and the current epoch. It serves requirement two and writes a session entity.
C: Heartbeat is a stream, about every three point three seconds. The response has no timestamp that matters. The server time is for logs only. The client trusts nothing in the reply except that it was acknowledged, and measures its own deadline from when it sent the beat.
[pause: 1.0]

[slide: v-145]
[pause: 1.0]
C: Acquire. The name, the session, a request id, and a maximum wait. A wait of zero means try once. There is no way to wait forever, on purpose.
C: Four answers: granted with a token and a lease, queued with a position, timed out, or contended with a retry-after. The request id makes a retry safe. If the network duplicates the request, the service returns the same token and not a second one. That is how failure six, duplicates, is designed out.
[pause: 1.0]

[slide: v-146]
[pause: 1.0]
C: Release takes the token, not just the name.
C: If the token matches the current holder, the name is freed and handed to the head waiter.
C: If it does not, the call is rejected, because someone else holds it now.
C: Think about what that removes.
C: A holder whose lease expired, then wakes and calls release, cannot free the new holder's lock.
C: That failure is not guarded against.
C: It cannot be expressed.
[pause: 1.0]

[slide: v-147]
[pause: 1.0]
C: Two operator calls. Inspect shows who holds a name. It is documented as never to be used for a correctness decision, because the answer can be stale by the time you read it.
C: ForceRevoke is the break-glass call. Every lock service eventually needs one, usually at three in the morning. I'm designing it in now: it takes a reason and an operator, writes an audit entry, and alerts. The next grant gets a higher token, so the revoked holder is fenced like any other.
[pause: 1.0]

[slide: v-148]
[pause: 1.0]
C: This is not our A-P-I, but it is part of the contract, and I'll say it every time.
C: Every write to a protected resource carries the token, and the resource rejects it if the token is smaller than the highest it has accepted.
C: Here that is one conditional update.
C: Precision: equal is allowed.
C: The same holder may write several times with the same token.
C: Only smaller is rejected.
C: And pass the token as an explicit argument.
C: If it hides in a thread-local, it is lost the first time work moves to another thread pool, and silently.
[pause: 1.0]

[slide: v-149]
[pause: 0.6]
C: Reentrancy comes up, so I'll dismiss it aloud.
C: Yes, a holder may acquire a lock it already holds.
[reveal: v-150]
[pause: 0.45]
C: I'd do it as a hold count in the client library, keyed by session.
C: The server keeps one grant per name.
[reveal: v-151]
[pause: 0.45]
C: Doing it on the server would double the writes for nothing.
C: One subtlety: scope it to the session, not the process, or a client that reconnects with a new session deadlocks against its own old grant.
[pause: 0.8]

[slide: v-152]
[pause: 1.3]
C: The conceptual model. A tenant owns lock names. A session holds names, and the relationship carries the token and the expiry. A session waits for names, with a position. A lock name protects resource rows, and a row stores the highest token it has accepted, a derived attribute. And an audit event is a weak entity: it only exists in the context of a lock name.
C: One cardinality matters most: a name has at most one holder at a time. That one fact is why locks are independent per name, and so why this shards.
[pause: 1.1]

[slide: v-153]
[pause: 1.3]
C: Physically. The held table is keyed by name, with owner, session, token and an expiry that is in log time, not wall time. The waiter table is keyed by name and a sequence, capped in depth. The session table holds the lease and its names. The last heartbeat is volatile, not in the log.
C: Two things live outside the group. The epoch and a token floor per slot, durable, which challenge four and five use. And at the resource, the protected row carries a fence column. Everything in a group is keyed by name, and a name lives in exactly one group, so there are no cross-group transactions.
[pause: 1.1]

[slide: v-154]
[pause: 1.0]
C: The state machine is small enough to read whole.
C: Apply runs on every replica, in log order.
C: If the same owner retries, it returns the same grant.
C: If the name is held, it enqueues.
C: Otherwise it grants, and the token is the log index of this very entry.
C: Monotonic, and free.
C: Look at the time.
C: It is not read from a clock here.
C: It is a field in the entry, stamped by the leader before replication.
C: If each replica read its own clock, two replicas could disagree about whether a lease expired, and the group would diverge.
C: That is the most common bug in home-built replicated state machines.
[pause: 1.0]

[slide: v-155]
[pause: 1.3]
C: The token itself. Sixty-four bits. Sixteen for an epoch, forty-eight for the log index within a group. Compared as a number, so a bigger epoch always wins. The epoch changes only on a rebuild or a slot move, which is what makes tokens survive a disaster, in challenge four.
C: A timestamp is not a valid token, because clocks go backwards. A random identifier is not either, because it has no order.
[pause: 1.1]

[slide: v-156]
[pause: 1.0]
C: Four stores, and for each: can I lose it?
C: The replicated log survives losing a minority.
C: Losing all of it means starting empty.
[reveal: v-157]
[pause: 0.45]
C: Leader memory holds heartbeat times.
C: Losing it is harmless: a new leader treats every session as alive for one lease.
[reveal: v-158]
[pause: 0.45]
C: The epoch store must not be lost, or tokens could go backwards.
[reveal: v-159]
[pause: 0.45]
C: And the resource's own durability matters too: the token check is only as good as the store that keeps the highest token.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-160]
[pause: 1.2]
C: Three versions. Each one is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move.
[pause: 1.8]

[slide: v-161]
[pause: 1.3]
C: Version one.
C: An app with a lock library, and one lock server.
[reveal: v-162]
[pause: 0.45]
C: The server keeps a map from name to owner and expiry in memory.
C: Acquire checks the map.
C: A lease means a dead holder's name frees itself.
[reveal: v-163]
[pause: 0.45]
C: The app also writes to its resource, drawn on top.
C: No objection yet.
C: It is the simplest thing that works, and for an efficiency lock it might be enough.
[pause: 1.1]

[slide: v-164]
[pause: 1.0]
C: The objection.
[reveal: v-165]
[pause: 0.45]
C: The server restarts, and forgets who holds what.
C: A holds a lock.
[reveal: v-166]
[pause: 0.45]
C: The server crashes at four seconds and restarts at five with an empty map.
[reveal: v-167]
[pause: 0.45]
C: B asks, and is granted the same name.
[reveal: v-168]
[pause: 0.45]
C: A is still working.
C: Two holders, and the lock service caused it.
[reveal: v-169]
[pause: 0.45]
C: And one box is a single point of failure for every team.
[pause: 1.0]

[slide: v-170]
[pause: 1.3]
C: Version two answers that.
C: The single server becomes a consensus group of five replicas: one leader and four followers.
C: Every grant is a log entry, and it counts only once a majority of replicas have it.
[reveal: v-171]
[pause: 0.45]
C: If the leader dies, a follower that has the committed entries takes over, so no grant is forgotten.
C: And the token falls out of this for free.
C: It is the log index of the grant entry.
C: Increasing by construction, with no extra machinery.
[pause: 1.1]

[slide: v-172]
[pause: 0.6]
C: The group in one slide.
C: One leader per term.
C: All writes go to it.
[reveal: v-173]
[pause: 0.45]
C: A node that sees a higher term obeys it.
C: An entry commits when three of five replicas hold it, and any future leader must have been in that three, so it has the entry.
[reveal: v-174]
[pause: 0.45]
C: And with only two of five reachable, nothing commits.
C: Safety is kept, and availability is given up.
C: That is the trade I chose in the theory.
[pause: 0.8]

[slide: v-175]
[pause: 0.6]
C: The objection to version two.
C: The consensus group is right, but the caller still cannot tell when it has lost the lock.
C: A holder whose lease expired keeps working.
[reveal: v-176]
[pause: 0.45]
C: And every team would write its own heartbeat, its own clock arithmetic and its own retries, and each would get it subtly wrong.
[reveal: v-177]
[pause: 0.45]
C: Half the correctness lives in the client library, so the library is part of the product.
[pause: 0.8]

[slide: v-178]
[pause: 1.3]
C: Version three.
C: The lock library holds one session, with one heartbeat, the dashed purple arrow.
C: It tracks a local deadline on a monotonic clock, and calls back with LockLost the moment the deadline passes, so application code can stop.
[reveal: v-179]
[pause: 0.45]
C: A stateless gateway sits in front: it authenticates, applies tenant quotas, and routes to the group's leader.
C: The token comes back in the grant, and the app passes it to the resource, the grey box on top.
C: This is the baseline.
C: It stays on screen from here, and every later picture is a view of it.
[pause: 1.1]

[slide: v-180]
[pause: 1.0]
C: The library's heartbeat is short.
C: Note the time before sending, on a monotonic clock.
C: If the beat succeeds, move the deadline to that send time plus seventy percent of the lease.
C: If it fails and the deadline has passed, drop every lock, loudly.
C: Failing closed.
C: A warning I'll repeat.
C: A check-still-held call before a write narrows the window, and does not close it.
C: Between the check and the write the lease can still expire.
C: That is the next problem.
[pause: 1.0]

[slide: v-181]
[pause: 0.6]
C: What version three leaves open.
C: It has a correct record, a library that stops on loss, and a token in the caller's hand.
[reveal: v-182]
[pause: 0.45]
C: What it lacks: the resource accepts any write.
C: A paused holder that wakes after its lease expired still writes.
[reveal: v-183]
[pause: 0.45]
C: Safety is not here yet.
C: That is challenge one, and I'll get there after the flows.
[pause: 0.8]

[slide: v-184]
[pause: 1.3]
C: Requirement one, acquire.
[reveal: v-185]
[pause: 0.45]
C: Step one: the library sends Acquire with the name and a request id.
[reveal: v-186]
[pause: 0.45]
C: Step two: the gateway authenticates, checks the tenant's quota, hashes the name to a slot and routes to that group's leader.
[reveal: v-187]
[pause: 0.45]
C: Inside the box, which the next sequence shows: the leader appends the entry, a majority acknowledges, it commits, and apply grants with the log index as the token.
[reveal: v-188]
[pause: 0.45]
C: Step three: the token and lease come back to the gateway.
[reveal: v-189]
[pause: 0.45]
C: Step four: back to the library, which sets its deadline from when it sent the request.
[pause: 1.1]

[slide: v-190]
[pause: 1.3]
C: Requirement two.
[reveal: v-191]
[pause: 0.45]
C: Step one: a heartbeat, dashed purple because it is asynchronous, goes from the library to the gateway.
[reveal: v-192]
[pause: 0.45]
C: Step two: the gateway passes it to the leader as a session-alive note.
C: The leader keeps liveness in memory under its own leader lease, so a heartbeat is not a consensus write.
[reveal: v-193]
[pause: 0.45]
C: Only an actual expiry becomes a log entry.
C: When the beat is acknowledged, the library moves its deadline from the time it sent it.
[pause: 1.1]

[slide: v-194]
[pause: 1.3]
C: Requirement three, release.
[reveal: v-195]
[pause: 0.45]
C: The same four arrows.
[reveal: v-196]
[pause: 0.45]
C: One: Release with the name and the token.
[reveal: v-197]
[pause: 0.45]
C: Two: routed to the leader.
C: The leader commits, and apply compares the token, frees the name, and hands it to the head waiter in the same step.
[reveal: v-198]
[pause: 0.45]
C: Three and four: the answer comes back.
C: A dead holder uses no arrow at all.
[reveal: v-199]
[pause: 0.45]
C: Its heartbeats stop.
C: After one lease the leader proposes a single session-expired command, and every name that session held is freed at once.
[pause: 1.1]

[slide: v-200]
[pause: 1.3]
C: Requirement four, the most important arrow.
C: Step one: the application writes to the resource over the top path, with the token.
[reveal: v-201]
[pause: 0.45]
C: Step two: the resource compares it with the highest token it has stored for that row.
C: Not smaller: accept, and store it.
[reveal: v-202]
[pause: 0.45]
C: Smaller: reject with FencedOut, log both tokens, and alert.
C: This arrow does not touch the lock service at all.
[reveal: v-203]
[pause: 0.45]
C: That is the point.
C: The lock service issued an order.
C: The resource enforces it.
[pause: 1.1]

[slide: v-204]
[pause: 1.3]
C: Requirement five.
[reveal: v-205]
[pause: 0.45]
C: Step one: the operator console calls ForceRevoke with a reason.
[reveal: v-206]
[pause: 0.45]
C: Step two: the gateway checks the operator's identity and routes to the leader.
[reveal: v-207]
[pause: 0.45]
C: The leader commits a revoke entry and an audit entry.
C: Step three: the answer returns.
[reveal: v-208]
[pause: 0.45]
C: The old holder learns on its next heartbeat.
C: And even if it does not, its next write is fenced, because the next grant gets a higher token.
[pause: 1.1]

[slide: v-209]
[pause: 1.3]
C: The C4 context.
[reveal: v-210]
[pause: 0.45]
C: Application teams use the lock service and write to their own resources, with the token.
[reveal: v-211]
[pause: 0.45]
C: Operators inspect and break glass.
[reveal: v-212]
[pause: 0.45]
C: The lock service reports metrics to an observability platform.
[reveal: v-213]
[pause: 0.45]
C: Notice the arrow from the application team straight to the protected resources, not through the lock service.
C: That is deliberate.
[pause: 1.1]

[slide: v-214]
[pause: 1.3]
C: The containers.
[reveal: v-215]
[pause: 0.45]
C: Inside the lock service boundary:
[reveal: v-216]
[pause: 0.45]
C: the lock library, which runs inside the application, the gateway, the consensus groups, four of them, an epoch store, and an operator console.
[reveal: v-217]
[pause: 0.45]
C: The application calls the library in process.
[reveal: v-218]
[pause: 0.45]
C: The library talks g-R-P-C to the gateway, which proposes to the group leader.
[reveal: v-219]
[pause: 0.45]
C: The group reads and bumps the epoch only on a rebuild.
[reveal: v-220]
[pause: 0.45]
C: And the application writes to the resource directly, with the token.
[pause: 1.1]

[slide: v-221]
[pause: 1.3]
C: Acquire as a sequence.
[reveal: v-222]
[pause: 0.45]
C: One: the library sends Acquire.
[reveal: v-223]
[pause: 0.45]
C: Two: the gateway routes by hash of the name to the leader.
[reveal: v-224]
[pause: 0.45]
C: Three: the leader appends the entry to the followers.
[reveal: v-225]
[pause: 0.45]
C: Four: they acknowledge, and a majority makes the entry commit.
[reveal: v-226]
[pause: 0.45]
C: Then apply:
[reveal: v-227]
[pause: 0.45]
C: the name is free, so grant, token equals the log index, say nine thousand and one.
[reveal: v-228]
[pause: 0.45]
C: Back to the gateway, and to the library, which sets its deadline from its send time.
[pause: 1.1]

[slide: v-229]
[pause: 1.3]
C: The loss path.
[reveal: v-230]
[pause: 0.45]
C: One: heartbeat.
C: The ack moves the deadline.
[reveal: v-231]
[pause: 0.45]
C: Then the network drops.
[reveal: v-232]
[pause: 0.45]
C: No reply, and no beat reaches the leader.
C: Two: at the deadline, seven seconds after the last send, the library tells the application LockLost, and the application stops before its next side effect.
[reveal: v-233]
[pause: 0.45]
C: Three: later, the leader sees no beat for a full lease and proposes SessionExpired.
[reveal: v-234]
[pause: 0.45]
C: Four: that commit frees the names, and the head waiter is granted, with a higher token.
[reveal: v-235]
[pause: 0.45]
C: The client stopped first, by design.
[pause: 1.1]

[slide: v-236]
[pause: 1.3]
C: Release.
C: One: holder A releases with token forty-one.
[reveal: v-237]
[pause: 0.45]
C: Two: the leader commits, and apply sees the token matches, so it frees the name.
[reveal: v-238]
[pause: 0.45]
C: Three, in the same step: the head of the queue is B, so grant, token forty-two.
[reveal: v-239]
[pause: 0.45]
C: Four: A gets its answer.
[reveal: v-240]
[pause: 0.45]
C: Five: B is told it was granted.
[reveal: v-241]
[pause: 0.45]
C: One committed write, one waiter woken, no polling.
[pause: 1.1]

[slide: v-242]
[pause: 1.3]
C: The check at the resource.
[reveal: v-243]
[pause: 0.45]
C: The current holder writes with token forty-two.
[reveal: v-244]
[pause: 0.45]
C: The stored maximum is forty-one, forty-two is not smaller, so accept and store forty-two.
[reveal: v-245]
[pause: 0.45]
C: Later a stale holder writes with forty-one.
[reveal: v-246]
[pause: 0.45]
C: The stored maximum is forty-two.
[reveal: v-247]
[pause: 0.45]
C: Forty-one is smaller, so reject, log both tokens, and alert.
[pause: 1.1]

[slide: v-248]
[pause: 1.0]
C: Last in the design, what a correct caller looks like. The wait is bounded. If the lock is not granted, no side effect happens. The check-still-held call narrows the window. Then the token goes to both protected resources, the payment call and the database write, because both must check. And a LockLost exception aborts safely. It never continues anyway.
[pause: 1.0]

[slide: v-249]
[pause: 1.0]
C: Mechanism before brand.
C: What must the substrate give me?
C: Leases that expire.
[reveal: v-250]
[pause: 0.45]
C: An atomic compare-and-set.
[reveal: v-251]
[pause: 0.45]
C: A monotonic number per change, my token.
[reveal: v-252]
[pause: 0.45]
C: And ordered, resumable watches so waiters wake in order.
[reveal: v-253]
[pause: 0.45]
C: A coordination store in the ZooKeeper or etcd family has all four.
C: If the store I'm offered lacks one of them, it is the wrong store.
[pause: 1.0]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-254]
[pause: 1.2]
C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-255]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-256]
[pause: 0.45]
C: The path between them..
[reveal: v-257]
[pause: 0.45]
C: Lock SDK is Library in the app.
[reveal: v-258]
[pause: 0.45]
C: Gateway is Go, gRPC, stateless.
[reveal: v-259]
[pause: 0.45]
C: Operator console is CLI + API.
[reveal: v-260]
[pause: 0.45]
C: Consensus groups is etcd-class, 4 times 5.
[reveal: v-261]
[pause: 0.45]
C: Epoch store is 3-replica counter.
[reveal: v-262]
[pause: 0.45]
C: Protected resource is Conditional write.
[pause: 1.1]

[slide: v-263]
[pause: 1.0]
C: Writes go to the leader, are appended to a log, replicated and committed on a majority. A lease is an object with a time to live that keys attach to; when it expires the keys vanish. Acquire is one transaction: if the name does not exist, create it and attach the lease, else say who holds it. Every name lives in exactly one group, chosen by hash, so there are no cross-group transactions. Reads that must be fresh confirm leadership first.
[reveal: v-264]
[pause: 0.45]
C: Why etcd-class store, 4 groups times 5 replicas, one name in one group: A lock needs a replicated record that survives losing a minority, an order for every change, leases that expire and an atomic set-if-absent. Its per-key revision is a ready-made fencing token.
[reveal: v-265]
[pause: 0.45]
C: Rejected: One cache node, set if absent with expiry. Replication is asynchronous: the primary grants the lock and dies before the copy arrives, and the new primary grants it again.
[reveal: v-266]
[pause: 0.45]
C: A quorum of independent cache nodes. Safety rests on timing: a pause between acquire and use lets a second client assemble a majority. And it produces no token.
[reveal: v-267]
[pause: 0.45]
C: A relational row with select for update. A row lock lives as long as the connection: no lease, no token. Right when the resource is in the same database.
[pause: 1.0]

[slide: v-268]
[pause: 1.0]
C: The library opens a session and sends a heartbeat about every third of the lease, which is 3.3 seconds for a ten-second lease. It keeps a local deadline shorter than the lease. If the heartbeat cannot get through and the local deadline passes, it raises LockLost to the application, which must stop. The library never reuses a token after expiry.
[reveal: v-269]
[pause: 0.45]
C: Why JVM and Go libraries; a heartbeat every third of the lease: The holder must stop on its own when it cannot prove it still holds the lock. That logic has to live in the process that does the work.
[reveal: v-270]
[pause: 0.45]
C: Rejected: A thin client that only calls acquire. The application would have to build the heartbeat and the deadline itself, and every team would get it slightly wrong.
[reveal: v-271]
[pause: 0.45]
C: A sidecar process per host. One more process that can pause independently of the application, which is the failure we are guarding against.
[pause: 1.0]

[slide: v-272]
[pause: 1.0]
C: The gateway authenticates the caller, applies a per-tenant quota, maps the name to its group with the slot map and forwards to the cached leader of that group. On a not-leader answer it refreshes the leader and retries once. It holds no lock state, so losing a gateway loses nothing but in-flight calls.
[reveal: v-273]
[pause: 0.45]
C: Why Go service on Kubernetes, gRPC, three zones: Clients should not know which group owns a name or who leads it. A stateless layer keeps that knowledge and can be restarted at will.
[reveal: v-274]
[pause: 0.45]
C: Rejected: Clients talking to the groups directly. Every client library would carry the slot map and leader changes, and a rebalance would need a client release.
[reveal: v-275]
[pause: 0.45]
C: A shared layer-7 proxy. Leader routing is application knowledge; a generic proxy would round-robin onto followers.
[pause: 1.0]

[slide: v-276]
[pause: 1.0]
C: The epoch sits in the top sixteen bits of every token, and the log index in the low forty-eight. It is read at group start and bumped only on a rebuild or a slot move, a handful of times a year. The store is itself replicated, three replicas across zones, and is written with a conditional update.
[reveal: v-277]
[pause: 0.45]
C: Why A three-replica strongly consistent store, outside the groups: If every group were lost, tokens would restart from zero and go backwards. The epoch is the one number that must survive, so it lives somewhere else.
[reveal: v-278]
[pause: 0.45]
C: Rejected: Keep the epoch inside the groups. The failure it protects against is losing the groups. It must not share their fate.
[reveal: v-279]
[pause: 0.45]
C: A clock-derived epoch. A wall-clock epoch depends on clocks agreeing across a rebuild; a bad clock gives a smaller number.
[pause: 1.0]

[slide: v-280]
[pause: 1.0]
C: Where the resource supports it, the token is the generation, version or entity tag, and the write is conditional on it: a SQL update where the stored token is at most mine, or a write-if-generation-matches. Where the resource is a partner API with no such primitive, a validating proxy keeps the highest token per resource in a consistent store and forwards only fresh calls. It fails closed.
[reveal: v-281]
[pause: 0.45]
C: Why A conditional write at the resource; a validating proxy where it cannot: The lock service cannot stop a stale write; only the resource can, and only if the check and the write are one atomic step.
[reveal: v-282]
[pause: 0.45]
C: Rejected: A check in the application before the write. Two steps, and the pause lands between them. That is exactly the failure.
[reveal: v-283]
[pause: 0.45]
C: An idempotency key alone. Cheapest, and the right answer when the operation allows it. It does not help when the second write is a different, valid operation.
[pause: 1.0]

[slide: v-284]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Consensus groups: etcd-class, 4 times 5 replicas.
C: Not Cache node; Redlock; SQL row.
C: Safety without timing; a revision as token.
[reveal: v-285]
[pause: 0.45]
C: Lock SDK: Library, local deadline.
C: Not Thin client; sidecar.
C: Stop on our own.
[reveal: v-286]
[pause: 0.45]
C: Gateway: Go, gRPC, stateless.
C: Not Direct clients; generic proxy.
C: Routing knowledge in one place.
[reveal: v-287]
[pause: 0.45]
C: Epoch store: 3-replica durable counter.
C: Not In the groups; clock epoch.
C: Survives losing every group.
[reveal: v-288]
[pause: 0.45]
C: Resource check: Conditional write; proxy.
C: Not App-side check.
C: Atomic with the write.
[reveal: v-289]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-290]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-291]
[pause: 1.0]
N: Here is where interviewers usually go.
I: The leader of a group dies mid-acquire.
I: Can two clients both be told they hold the name?
[pause: 1.2]
N: No.
N: A grant commits only on a majority, and the new leader has every committed entry.
[reveal: v-292]
[pause: 0.45]
N: A client that never saw the answer retries and learns the truth.
N: The trap is a read from a follower that has not caught up.
I: The application's thread pauses for forty seconds with a ten-second lease.
I: What stops the stale write?
[pause: 1.2]
[reveal: v-293]
[pause: 0.45]
N: Nothing in the library can, since the whole process is paused.
N: That is why the token exists: the resource rejects the stale write because a newer token has been seen.
I: Every group is lost in a disaster.
I: How do you restart without issuing a token an old holder could beat?
[pause: 1.2]
N: Bump the epoch in the epoch store, start the groups empty, seed the token floor above the old maximum, and wait one maximum lease before granting.
[reveal: v-294]
[pause: 0.45]
N: Every new token exceeds every old one.
I: The resource is a partner HTTP API with no conditional write.
I: Where does the check go?
[pause: 1.2]
N: In a validating proxy that keeps the highest token seen per resource in a consistent store and rejects lower ones, failing closed.
[reveal: v-295]
[pause: 0.45]
N: The proxy's step is itself a conditional update.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 6 Bridge

[slide: v-296]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-297]
[pause: 1.3]
C: Here is the baseline with seven attack points.
C: A paused holder, at the resource.
C: A resource that cannot check tokens.
C: Clocks, in the library.
[reveal: v-298]
[pause: 0.45]
C: The leader and the partition, in the group.
C: Peak load, at the gateway and the group.
C: A hot name, in the group.
C: And finally: how would we know any of it was broken?
C: I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-299]
[pause: 1.2]
C: Seven challenges. Each one runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room.
[pause: 1.8]


## 7.1 Challenge 1: The paused holder

[slide: v-300]
[pause: 0.6]
I: A holder is stopped by a fifteen-second garbage collection pause. Its lease expires, another process acquires, and then the first one wakes up. Both now write. What saves you?
[pause: 2.0]

[slide: v-301]
[pause: 1.3]
C: The first answer most people give: make the lease longer, and check the lease is valid just before writing.
[reveal: v-302]
[pause: 0.45]
C: Look where it breaks.
[reveal: v-303]
[pause: 0.45]
C: The red arrow, from the client to the resource.
[reveal: v-304]
[pause: 0.45]
C: The lock service did everything right, and the resource still accepts both writes.
C: A check before a write is not atomic with the write.
[reveal: v-305]
[pause: 0.45]
C: Between them, the lease can expire.
C: That is the pause, exactly.
[pause: 1.1]

[slide: v-306]
[pause: 1.0]
C: The trace with numbers.
[reveal: v-307]
[pause: 0.45]
C: A gets token forty-one at zero, reads, checks that it still holds the lock, and pauses at point three.
[reveal: v-308]
[pause: 0.45]
C: The lease expires at ten.
C: B acquires at ten point four, token forty-two, and writes at ten point five.
[reveal: v-309]
[pause: 0.45]
C: At fifteen point three A resumes and writes.
[reveal: v-310]
[pause: 0.45]
C: It checked.
[reveal: v-311]
[pause: 0.45]
C: It was right to check.
[reveal: v-312]
[pause: 0.45]
C: It was just too early.
[reveal: v-313]
[pause: 0.45]
C: Raising the lease to sixty seconds moves the line, and a seventy-second pause still beats it, while every real crash stalls its name for a minute.
C: These numbers are illustrative.
C: The shape is what matters.
[pause: 1.0]

[slide: v-314]
[pause: 1.3]
C: The fix is the fencing token, checked at the resource.
[reveal: v-315]
[pause: 0.45]
C: The new green box is the check.
[reveal: v-316]
[pause: 0.45]
C: The grant already carries a token, which is the log index.
[reveal: v-317]
[pause: 0.45]
C: The resource keeps the highest token it has accepted for that row, and rejects any write that carries a smaller one.
[reveal: v-318]
[pause: 0.45]
C: Rejected: A lease with no token.
[reveal: v-319]
[pause: 0.45]
C: A paused holder wakes after expiry with no idea, and writes; only a token the resource checks can reject it.
[pause: 1.1]

[slide: v-320]
[pause: 1.3]
C: Replay it. A holds forty-one and pauses. B gets forty-two and writes: accepted, the resource stores forty-two. A wakes at fifteen point three and writes with forty-one. Forty-one is smaller than forty-two. Rejected. Notice what did not change: the pause, the lease, the lock service. Only the resource became safe.
[pause: 1.1]

[slide: v-321]
[pause: 1.3]
C: As a sequence.
[reveal: v-322]
[pause: 0.45]
C: A acquires and gets forty-one.
[reveal: v-323]
[pause: 0.45]
C: A pauses fifteen seconds.
[reveal: v-324]
[pause: 0.45]
C: B acquires after the lease expired and gets forty-two.
[reveal: v-325]
[pause: 0.45]
C: B writes with forty-two, accepted.
[reveal: v-326]
[pause: 0.45]
C: A resumes and writes with forty-one at fifteen point three,
[reveal: v-327]
[pause: 0.45]
C: and the resource rejects it:
[reveal: v-328]
[pause: 0.45]
C: forty-one is smaller than forty-two.
[pause: 1.1]

[slide: v-329]
[pause: 1.0]
C: In code, on a database row it is one conditional update.
C: Set the amount and the fence, where the fence is less than or equal to the token.
C: Zero rows updated means fenced out: log both tokens and alert.
C: On an object store, the object's generation number is the token, and the write is conditional on it.
C: Why it works, as a property: safety, enforced where the effect happens.
C: Consensus gives a correct order.
C: The resource, the only place that can check and write in one atomic step, enforces it.
C: And precisely: equal tokens pass, because one holder may write several times.
C: Only smaller is rejected.
[pause: 1.0]

[slide: v-330]
[pause: 0.6]
I: A's stale write arrives before B's first write. The resource has only seen forty-one, so it accepts A. Then B, who read the old row, writes forty-two on top. Is that fenced?
[pause: 2.0]

[slide: v-331]
[pause: 1.0]
C: No, and that is the honest limit.
C: Fencing rejects stale writes after a newer token has been seen.
[reveal: v-332]
[pause: 0.45]
C: Here A's write lands first, when the resource has only seen forty-one.
[reveal: v-333]
[pause: 0.45]
C: It is accepted.
[reveal: v-334]
[pause: 0.45]
C: Then B, working from an older read, writes on top of it, and A's update is lost.
[reveal: v-335]
[pause: 0.45]
C: Two ways to close it.
C: One: make B's critical section a single conditional write against the version it read, so the token is the version.
[reveal: v-336]
[pause: 0.45]
C: Two: B claims its token at the resource before it reads.
C: After that, any write from A is rejected.
C: The cost is one extra round trip, or a critical section that fits in one conditional write.
[pause: 1.0]

[slide: v-337]
[pause: 1.3]
C: The claim as a sequence.
[reveal: v-338]
[pause: 0.45]
C: B claims token forty-two at the resource before reading.
[reveal: v-339]
[pause: 0.45]
C: The resource now stores forty-two.
[reveal: v-340]
[pause: 0.45]
C: A, the stale holder, writes with forty-one: rejected.
[reveal: v-341]
[pause: 0.45]
C: Then B reads the row and writes with forty-two,
[reveal: v-342]
[pause: 0.45]
C: conditional on the version it read.
[reveal: v-343]
[pause: 0.45]
C: The window is closed.
[pause: 1.1]

[slide: v-344]
[pause: 0.7]
V: If asked, I'd say: a lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock when its write lands. So the grant carries a token that only increases, and the resource rejects anything older than it has accepted. Safety lives at the resource. The lock service only has to give a correct order.
[pause: 1.0]
N: That fix creates the next question: what if the resource cannot check?
[pause: 1.6]


## 7.2 Challenge 2: The resource cannot check

[slide: v-345]
[pause: 0.6]
I: The thing you are protecting is a partner's H-T-T-P A-P-I, or a cron job. There is no conditional write. Now what?
[pause: 2.0]

[slide: v-346]
[pause: 1.3]
C: The naive answer: use a long lease, trust the library, and call it correct.
[reveal: v-347]
[pause: 0.45]
C: It is not.
[reveal: v-348]
[pause: 0.45]
C: Here is a payment call to a partner with no idempotency key.
[reveal: v-349]
[pause: 0.45]
C: The holder pauses after its lock check, and the call happens twice.
[reveal: v-350]
[pause: 0.45]
C: The grey box has nowhere to put a fence.
[pause: 1.1]

[slide: v-351]
[pause: 1.0]
C: Before building, sort the callers.
C: An illustrative survey of a hundred.
C: Fifty-five only want to avoid duplicate work: that is an efficiency lock, and no token is needed.
[reveal: v-352]
[pause: 0.45]
C: Thirty write to a store with a conditional write or a version column: the resource's own version is the token, and the lock service is just an optimisation.
[reveal: v-353]
[pause: 0.45]
C: Ten call something with neither: for those I build a validating proxy.
[reveal: v-354]
[pause: 0.45]
C: And five are truly non-idempotent, with no check possible.
[reveal: v-355]
[pause: 0.45]
C: For those, no lock can make them safe.
C: The answer is to change the contract, or accept the risk in writing, with a named owner.
[pause: 1.0]

[slide: v-356]
[pause: 0.6]
C: So the order of questions.
C: One: is the operation idempotent?
C: If so, give it a key, the lock name plus the job instance, and a double hold becomes harmless.
[reveal: v-357]
[pause: 0.45]
C: Two: does the resource have a conditional write?
C: Use its version as the token.
[reveal: v-358]
[pause: 0.45]
C: Three: otherwise put a validating proxy in front of it.
[reveal: v-359]
[pause: 0.45]
C: Four: if none of these fit, ship an efficiency lock, and say so plainly in the contract.
C: Each option moves safety to a place that can check and act atomically.
[pause: 0.8]

[slide: v-360]
[pause: 1.3]
C: The proxy, for the ten.
[reveal: v-361]
[pause: 0.45]
C: It sits in front of the partner's A-P-I and keeps the highest token per resource in a consistent store.
[reveal: v-362]
[pause: 0.45]
C: A call with a fresh token is forwarded.
[reveal: v-363]
[pause: 0.45]
C: A stale one is rejected, and the partner never sees it.
[reveal: v-364]
[pause: 0.45]
C: The property: safety, moved to a place where a check can be made atomic.
[reveal: v-365]
[pause: 0.45]
C: Rejected: Checking the token in the application.
C: Two steps, and the pause lands between them; the check must be atomic with the write.
[pause: 1.1]

[slide: v-366]
[pause: 1.3]
C: As a sequence.
[reveal: v-367]
[pause: 0.45]
C: The app calls through the proxy with token forty-two.
[reveal: v-368]
[pause: 0.45]
C: The proxy sets the maximum to forty-two with a conditional update,
[reveal: v-369]
[pause: 0.45]
C: which applies, then forwards the call, and the response comes back.
[reveal: v-370]
[pause: 0.45]
C: A stale holder calls with forty-one.
[reveal: v-371]
[pause: 0.45]
C: The conditional update does not apply,
[reveal: v-372]
[pause: 0.45]
C: because the maximum is forty-two,
[reveal: v-373]
[pause: 0.45]
C: so the proxy rejects it,
[reveal: v-374]
[pause: 0.45]
C: and the partner never sees the call.
[pause: 1.1]

[slide: v-375]
[pause: 0.6]
I: The proxy is now a single point of failure, and a new thing that must itself be consistent. And your idempotency records: how long do you keep them?
[pause: 2.0]

[slide: v-376]
[pause: 0.6]
C: The proxy fails closed, keeps its table in a consensus-backed store, and is scoped per resource class, so one failure does not take everyone.
[reveal: v-377]
[pause: 0.45]
C: Idempotency records live at least as long as the maximum lease plus the maximum pause plus the retry horizon.
C: For a sixty-second lease, an illustrative twenty-four hours.
[reveal: v-378]
[pause: 0.45]
C: And the honest limit.
C: A non-idempotent call to a system with no check cannot be made safe by any lock.
C: The answer is to change the contract, or accept the risk with an owner.
[pause: 0.8]

[slide: v-379]
[pause: 0.7]
V: If asked, I'd say: before I build a lock for a team I ask what a double hold costs, and whether the operation can be made idempotent. If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I only claim a correctness lock where something downstream checks the token.
[pause: 1.0]
N: Next: if safety rests on the token, how much does it rest on the lease clock?
[pause: 1.6]


## 7.3 Challenge 3: Clocks and leases

[slide: v-380]
[pause: 0.6]
I: A client's clock is five seconds slow. Or time is stepped back eight seconds in the middle of a lease. What happens to the lease?
[pause: 2.0]

[slide: v-381]
[pause: 1.3]
C: The naive design:
[reveal: v-382]
[pause: 0.45]
C: the server returns an expiry timestamp,
[reveal: v-383]
[pause: 0.45]
C: and the client compares it with its own clock.
[reveal: v-384]
[pause: 0.45]
C: Look at the box under attack, the library.
[reveal: v-385]
[pause: 0.45]
C: It trusts a time from a machine whose clock it has no reason to trust.
[pause: 1.1]

[slide: v-386]
[pause: 1.3]
C: The case. The server grants at its time zero, expiry at ten. The client's clock is five seconds slow, so it believes it holds until its own ten, which is server time fifteen. From server time ten to fifteen, B has been granted the name and A still believes it holds it. Two holders, for five seconds. A fast clock is merely wasteful. A step back of eight seconds mid-lease does the same to a perfectly good client. And a timestamp is no good as the token either, for the same reason.
[pause: 1.1]

[slide: v-387]
[pause: 1.0]
C: The discipline is to use each kind of time for one job.
C: A wall clock can jump either way: clock steps, leap seconds, virtual machine migration.
C: Never use it for a lease.
[reveal: v-388]
[pause: 0.45]
C: A monotonic clock never goes backwards on one machine, but means nothing across machines.
C: Use it for durations.
[reveal: v-389]
[pause: 0.45]
C: And logical order, the log index and the term, says nothing about duration but is totally ordered.
[reveal: v-390]
[pause: 0.45]
C: Use it for the token.
[pause: 1.0]

[slide: v-391]
[pause: 1.3]
C: The fix.
[reveal: v-392]
[pause: 0.45]
C: The library measures its deadline as the monotonic time when it sent the request, plus seventy percent of the lease.
[reveal: v-393]
[pause: 0.45]
C: The server counts the lease from its own commit, on its own monotonic clock.
[reveal: v-394]
[pause: 0.45]
C: And inside the replicated machine, the leader writes the apply time into the log entry, so replicas never read their own clocks.
[reveal: v-395]
[pause: 0.45]
C: No timestamp crosses the wire.
[reveal: v-396]
[pause: 0.45]
C: Rejected: A quorum of cache nodes for the lock.
C: Its safety rests on timing assumptions, and it issues no token.
[pause: 1.1]

[slide: v-397]
[pause: 1.3]
C: Replay it. The client counts from when it sent: seven seconds. At seven it stops. The server waits the full ten. Between them, a three-second margin. The client always stops first, so there is never a window where it believes it holds a lock the server has given away. And drift? Two hundred parts per million over ten seconds is two milliseconds. The margin is for round trips and scheduling, not for drift.
[pause: 1.1]

[slide: v-398]
[pause: 0.6]
I: What if the process pauses between reading the monotonic clock and doing the write? Or drift is far above your assumption, as on a throttled virtual machine?
[pause: 2.0]

[slide: v-399]
[pause: 0.6]
C: Two honest answers.
C: A pause between the clock read and the write: the margin cannot see it.
C: That is challenge one again, and the token is the backstop.
[reveal: v-400]
[pause: 0.45]
C: And drift beyond the assumption: bounded drift is an assumption, and I'll say so.
C: But once fencing is in, it is no longer load-bearing for safety.
C: It only affects how often a holder is fenced.
C: So I monitor clock health and the rate of missed deadlines, and keep the margin configurable per tenant.
[pause: 0.8]

[slide: v-401]
[pause: 0.7]
V: If asked, I'd say: I use monotonic clocks for durations and logical order for correctness. The client gives up before the server does, so there is never a window where it believes it holds a lock the server has given away. And because that still assumes bounded drift, the token at the resource is what the safety argument rests on.
[pause: 1.0]
N: So far, every failure was at the edges. What if the middle fails?
[pause: 1.6]


## 7.4 Challenge 4: Leader loss, partition, group loss

[slide: v-402]
[pause: 0.6]
I: The leader dies mid-grant, and a partition leaves two of the five replicas talking to some clients. What do those clients see?
[pause: 2.0]

[slide: v-403]
[pause: 1.3]
C: The naive answer:
[reveal: v-404]
[pause: 0.45]
C: promote a follower fast,
[reveal: v-405]
[pause: 0.45]
C: and let the minority side keep serving, to stay available.
[reveal: v-406]
[pause: 0.45]
C: Look where it breaks, the consensus group.
[reveal: v-407]
[pause: 0.45]
C: Serving on the small side means two sides can each grant the same name.
[pause: 1.1]

[slide: v-408]
[pause: 1.3]
C: The case. Replicas one to five. R-one leads in term seven. A partition isolates R-one and R-two from R-three, four and five. The big side hears no leader for a second and a half and elects R-three in term eight. R-one still believes it leads, but it can reach only one other replica out of five. It cannot get a majority. So it cannot commit, and cannot grant.
[pause: 1.1]

[slide: v-409]
[pause: 1.3]
C: As a sequence.
[reveal: v-410]
[pause: 0.45]
C: Client Y, on the majority side, asks for x.
[reveal: v-411]
[pause: 0.45]
C: R-three commits it with a majority: granted, token nine thousand and one.
[reveal: v-412]
[pause: 0.45]
C: Client X, on the minority side, asks R-one for x.
[reveal: v-413]
[pause: 0.45]
C: R-one cannot reach a majority, so it answers unavailable.
[reveal: v-414]
[pause: 0.45]
C: No grant.
[reveal: v-415]
[pause: 0.45]
C: When the partition heals, R-one sees term eight, steps down, and discards anything uncommitted.
[reveal: v-416]
[pause: 0.45]
C: The small side got an honest no.
[pause: 1.1]

[slide: v-417]
[pause: 1.3]
C: The fix is mostly what version two already had, plus two details.
[reveal: v-418]
[pause: 0.45]
C: Only the majority side commits.
[reveal: v-419]
[pause: 0.45]
C: A stale leader steps down when it sees a higher term.
C: Heartbeats are answered by the leader under a short leader lease, so no log entry per beat.
[reveal: v-420]
[pause: 0.45]
C: And a new leader treats every session as alive for one full lease after election, called a grace period.
[reveal: v-421]
[pause: 0.45]
C: Otherwise a failover would see every heartbeat gap as a death and evict every lock at once.
[reveal: v-422]
[pause: 0.45]
C: Rejected: Restoring the groups from a backup.
C: The backup predates later grants, so tokens would go backwards; start empty with a higher epoch.
[pause: 1.1]

[slide: v-423]
[pause: 0.6]
C: Why it works.
C: Safety is kept: two replicas cannot commit, so a partition cannot create two holders.
[reveal: v-424]
[pause: 0.45]
C: Liveness is given up, on the small side only.
C: A failover costs about two seconds.
C: And tokens stay monotonic across terms, because they are log indexes.
[reveal: v-425]
[pause: 0.45]
C: There is no clever third option here, and I won't pretend there is.
C: I'd rather say the position plainly: for a correctness lock, unavailability of the lock service must become unavailability of the protected operation.
C: If the business cannot accept that, the requirement is really an efficiency lock, and I'd make the resource idempotent.
[pause: 0.8]

[slide: v-426]
[pause: 0.6]
I: Three of the five replicas are gone. Or someone restores last night's snapshot. What happens to the tokens?
[pause: 2.0]

[slide: v-427]
[pause: 1.0]
C: Without a majority, the service fails closed: libraries reach their local deadlines, get LockLost, and stop.
[reveal: v-428]
[pause: 0.45]
C: That part is fine.
[reveal: v-429]
[pause: 0.45]
C: The dangerous part is the restore.
C: Restore Monday's snapshot, and the log index goes back.
[reveal: v-430]
[pause: 0.45]
C: The next grant of that name reuses a token that was already issued.
[reveal: v-431]
[pause: 0.45]
C: The resource has stored a much higher number, so it rejects every new holder as stale.
[reveal: v-432]
[pause: 0.45]
C: And in the other direction, a stale holder from before the loss could slip through.
C: Tokens must never go backwards, even across a disaster.
[pause: 1.0]

[slide: v-433]
[pause: 1.3]
C: So disaster recovery is not restore.
[reveal: v-434]
[pause: 0.45]
C: It is start empty with a higher epoch.
[reveal: v-435]
[pause: 0.45]
C: One: the operator bumps the durable epoch, six to seven, in the epoch store.
[reveal: v-436]
[pause: 0.45]
C: Two: the new group starts empty, with its token floor at epoch seven, shifted left forty-eight bits.
[reveal: v-437]
[pause: 0.45]
C: Three: a quiet period of one maximum lease, sixty seconds, in which the group refuses grants, so every old holder has stopped on its own deadline.
[reveal: v-438]
[pause: 0.45]
C: Four: libraries open sessions again, and grants resume with tokens above everything ever issued.
[pause: 1.1]

[slide: v-439]
[pause: 0.6]
C: The cost is a minute of outage during a rebuild.
C: The quiet period equals the longest lease we allow.
[reveal: v-440]
[pause: 0.45]
C: The epoch is sixteen bits, so sixty-five thousand rebuilds, far more than will ever happen.
[reveal: v-441]
[pause: 0.45]
C: All of that is derived, not measured.
[reveal: v-442]
[pause: 0.45]
C: A minute of outage is cheap, next to the alternative of two holders.
[pause: 0.8]

[slide: v-443]
[pause: 0.7]
V: If asked, I'd say: under partition I choose safety. The minority side refuses, it does not guess. After the loss of a whole group I start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible lease before granting. The outage is a minute. The alternative is two holders.
[pause: 1.0]
N: Now the failure is not a fault. It is success: too much traffic.
[pause: 1.6]


## 7.5 Challenge 5: The top of the hour

[slide: v-444]
[pause: 0.6]
I: At the top of the hour traffic triples, and two thousand clients retry at once after a network blip. What happens, and what do you do?
[pause: 2.0]

[slide: v-445]
[pause: 1.3]
C: The naive answers: add replicas, or shorten the lease.
[reveal: v-446]
[pause: 0.45]
C: Neither touches the problem.
[reveal: v-447]
[pause: 0.45]
C: One group carries about fifteen thousand committed writes a second,
[reveal: v-448]
[pause: 0.45]
C: and the peak is thirty thousand.
[reveal: v-449]
[pause: 0.45]
C: The group box is the bottleneck.
[pause: 1.1]

[slide: v-450]
[pause: 1.0]
C: Trace it.
C: Thirty thousand writes a second arrive and the group commits fifteen.
[reveal: v-451]
[pause: 0.45]
C: The backlog grows by fifteen thousand a second.
[reveal: v-452]
[pause: 0.45]
C: After ten seconds it is a hundred and fifty thousand deep, and latency is longer than the ten-second lease itself.
[reveal: v-453]
[pause: 0.45]
C: Grants that were in flight have already expired.
C: Clients retry, which adds load.
[reveal: v-454]
[pause: 0.45]
C: A metastable collapse: the system cannot recover even if the peak passes.
C: And more replicas do not help.
[reveal: v-455]
[pause: 0.45]
C: Every write must reach a majority.
C: Replicas add fault tolerance, not write throughput.
C: These figures are illustrative, from the estimates.
[pause: 1.0]

[slide: v-456]
[pause: 1.3]
C: The fix.
[reveal: v-457]
[pause: 0.45]
C: Hash the name into sixty-four slots, and map slots to four groups.
C: Thirty thousand over fifteen thousand times half is four.
[reveal: v-458]
[pause: 0.45]
C: The gateway applies per-tenant quotas, and answers overloaded with a retry-after, instead of queueing.
C: The library retries with jittered backoff.
[reveal: v-459]
[pause: 0.45]
C: Sessions keep renewal at about a hundred and twenty a second, not four hundred and eighty.
C: And the leader batches many entries into one disk sync.
[reveal: v-460]
[pause: 0.45]
C: This works because locks are independent per name.
C: There are no cross-group transactions, so the partition is free.
[reveal: v-461]
[pause: 0.45]
C: Rejected: Every waiter polling the same name.
C: A thundering herd at expiry; a watch wakes one waiter in order.
[pause: 1.1]

[slide: v-462]
[pause: 1.3]
C: As a sequence.
[reveal: v-463]
[pause: 0.45]
C: The library asks.
[reveal: v-464]
[pause: 0.45]
C: The gateway sees the tenant over quota,
[reveal: v-465]
[pause: 0.45]
C: or the group's queue deep, and answers overloaded, retry after two hundred milliseconds.
[reveal: v-466]
[pause: 0.45]
C: The library waits that long plus a random jitter,
[reveal: v-467]
[pause: 0.45]
C: so two thousand clients do not return in the same instant.
[reveal: v-468]
[pause: 0.45]
C: It retries, and this time it is admitted, routed to the leader, and granted.
[pause: 1.1]

[slide: v-469]
[pause: 0.6]
I: One group goes bad. Or you need to move a slot while its locks are held.
[pause: 2.0]

[slide: v-470]
[pause: 1.3]
C: A bad group takes a quarter of the names with it and fails closed. The other three are untouched. That is the blast radius, and it is why I shard even though the data is tiny. Moving a slot is the dangerous part. A name moving while it is held is a correctness hazard. So: freeze the slot, drain its held locks, which takes at most one maximum lease, bump the slot's epoch so the new group's token floor sits above the old group's, then unfreeze in the new group.
C: Skip the epoch bump and a name that moves to a group with a lower log index would see its tokens go backwards. Same rule as before: tokens never go back.
[pause: 1.1]

[slide: v-471]
[pause: 0.7]
V: If asked, I'd say: I size for the peak. Thirty thousand writes a second against a fifteen thousand ceiling means four groups with headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back off with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the names.
[pause: 1.0]
N: Spreading across groups does not help one name.
[pause: 1.6]


## 7.6 Challenge 6: A hot name, several locks

[slide: v-472]
[pause: 0.6]
I: One name gets forty attempts a second, and each hold lasts a hundred milliseconds. What happens?
[pause: 2.0]

[slide: v-473]
[pause: 1.3]
C: The naive answers:
[reveal: v-474]
[pause: 0.45]
C: everyone polls until they get it, or we keep a queue that just grows.
[reveal: v-475]
[pause: 0.45]
C: The pain lands on one box:
[reveal: v-476]
[pause: 0.45]
C: the leader of the one group that owns this name.
[reveal: v-477]
[pause: 0.45]
C: Sharding does not help, because one name lives in one group.
[pause: 1.1]

[slide: v-478]
[pause: 1.3]
C: The arithmetic. A hold of a hundred milliseconds means this name can grant at most ten a second. Forty attempts a second is four times over. If waiters poll every fifty milliseconds, thirty waiters make six hundred polls a second on this one name. Each release wakes all of them and twenty-nine lose: a herd. With an unbounded queue, it grows by thirty a second. After ten seconds a new waiter is three hundred deep and waits about thirty seconds, longer than its own lease. Illustrative numbers, but the shape is real.
[pause: 1.1]

[slide: v-479]
[pause: 1.3]
C: The fix.
[reveal: v-480]
[pause: 0.45]
C: The new orange box: a waiter queue per name, with a cap, scoped to sessions so a dead waiter is reaped.
[reveal: v-481]
[pause: 0.45]
C: A release grants directly to the head waiter in the same committed step.
[reveal: v-482]
[pause: 0.45]
C: One write, one waiter woken.
C: Beyond the cap, or the wait budget, the answer is contended with a retry-after.
[reveal: v-483]
[pause: 0.45]
C: Waiting costs no writes.
C: The herd is gone.
[reveal: v-484]
[pause: 0.45]
C: Every wait is bounded.
C: Rejected: One global lock for a whole resource family.
C: It makes one group the bottleneck for everything; split the name and keep one name in one group.
[pause: 1.1]

[slide: v-485]
[pause: 1.3]
C: As a sequence.
[reveal: v-486]
[pause: 0.45]
C: Waiter one asks and is queued at position one.
[reveal: v-487]
[pause: 0.45]
C: Waiter two asks and is queued at position two.
[reveal: v-488]
[pause: 0.45]
C: Holder A releases with token seven.
[reveal: v-489]
[pause: 0.45]
C: The leader commits, and the same step grants to waiter one, token eight.
[reveal: v-490]
[pause: 0.45]
C: Waiter two keeps waiting,
[reveal: v-491]
[pause: 0.45]
C: and if the cap or its maximum wait is exceeded, it gets contended with a retry-after instead of waiting forever.
[pause: 1.1]

[slide: v-492]
[pause: 0.6]
I: A team now asks to acquire three locks atomically.
[pause: 2.0]

[slide: v-493]
[pause: 1.0]
C: First I push back.
C: Acquiring several names atomically across groups is a distributed transaction, and I would not offer it.
[reveal: v-494]
[pause: 0.45]
C: If it must be done: a canonical order, with the library sorting names and acquiring in that order, so two callers cannot wait on each other in a cycle.
[reveal: v-495]
[pause: 0.45]
C: Try with a timeout and release everything on failure.
[reveal: v-496]
[pause: 0.45]
C: And bounded leases mean any deadlock that still happens heals within one lease.
[reveal: v-497]
[pause: 0.45]
C: Building a wait-for graph to detect cycles is rarely worth it, and saying so is a better answer than describing the algorithm.
[pause: 1.0]

[slide: v-498]
[pause: 0.6]
C: And an honest limit.
C: A lock serialises.
C: A name can grant at most one over the hold time, and no design makes that bigger.
[reveal: v-499]
[pause: 0.45]
C: If one name is asked forty times a second, the caller does not want a lock.
C: They want a queue, or a single writer per partition.
C: That is a conversation to have with the team, not a feature to add.
[pause: 0.8]

[slide: v-500]
[pause: 0.7]
V: If asked, I'd say: a lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock directly to the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks I fix the order, bound every wait, and rely on leases so a deadlock heals in one lease. I would not offer atomic multi-lock.
[pause: 1.0]
N: Everything so far assumed we would notice a failure. Would we?
[pause: 1.6]


## 7.7 Challenge 7: How would you know?

[slide: v-501]
[pause: 0.6]
I: It is three in the morning. A team says duplicates are happening, and your dashboard is green. How would you have known?
[pause: 2.0]

[slide: v-502]
[pause: 1.3]
C: The naive answer: watch the service's CPU, memory and uptime.
[reveal: v-503]
[pause: 0.45]
C: Here is the case.
[reveal: v-504]
[pause: 0.45]
C: Availability is ninety-nine point nine nine percent, p99 is eight milliseconds.
[reveal: v-505]
[pause: 0.45]
C: Everything is green.
[reveal: v-506]
[pause: 0.45]
C: And yet one service has twelve fenced-out rejections a minute, its renewal failures are rising, and on one name the hold time went from half a second to nine.
C: The dashboard watches the machine.
C: The promise is broken somewhere it does not look.
[pause: 1.1]

[slide: v-507]
[pause: 1.0]
C: So measure the guarantee.
[reveal: v-508]
[pause: 0.45]
C: Acquire availability and latency, the headline contract.
[reveal: v-509]
[pause: 0.45]
C: Session-loss rate, because every loss may abort someone's work.
[reveal: v-510]
[pause: 0.45]
C: Fenced-out writes: alert on any.
C: A fenced-out write means a stale holder reached a resource.
[reveal: v-511]
[pause: 0.45]
C: It is either the safety net working, or the first symptom of a real problem, and I want to know which.
C: Elections per group per day, under one.
[reveal: v-512]
[pause: 0.45]
C: Time to a new leader under two seconds.
C: All initial targets.
[pause: 1.0]

[slide: v-513]
[pause: 1.0]
C: Read metrics in pairs, so each page names a cause.
C: Fenced-out writes rising together with one client's renewal failures: that client is pausing.
C: The safety net worked.
[reveal: v-514]
[pause: 0.45]
C: Fix the client.
C: Elections rising with acquire p99: an unhealthy group or its disk.
[reveal: v-515]
[pause: 0.45]
C: Hold-time tail up with waiter depth up: someone is holding a lock across a network call, or it is a hot name.
[reveal: v-516]
[pause: 0.45]
C: Token gaps growing with attempts: a retry storm.
[reveal: v-517]
[pause: 0.45]
C: One metric tells you something is wrong.
C: Two tell you where.
[pause: 1.0]

[slide: v-518]
[pause: 1.3]
C: The fix: a metrics and canary box fed by the groups and the resource checks.
[reveal: v-519]
[pause: 0.45]
C: A canary lock acquired continuously, so a quiet failure still shows up as a missed acquire.
[reveal: v-520]
[pause: 0.45]
C: And an offline checker that replays the grant log for overlapping holds.
[reveal: v-521]
[pause: 0.45]
C: The property: it turns the safety argument into something you can watch.
[reveal: v-522]
[pause: 0.45]
C: Rejected: Alerting on whether the service is up.
[reveal: v-523]
[pause: 0.45]
C: It can be up while grants miss their budget; measure acquire latency and token monotonicity.
[pause: 1.1]

[slide: v-524]
[pause: 1.3]
C: And turn the target into a constraint. Ninety-nine point nine nine percent of a thirty-day month is two hundred and fifty-nine seconds. At about two seconds an election, roughly a hundred and thirty elections a group a month spend all of it. So elections per day is an SLI with a target under one. A constraint like that is what a manager uses to decide what to fix first.
[pause: 1.1]

[slide: v-525]
[pause: 0.6]
I: Fenced-out is zero this week. Does that mean you are safe?
[pause: 2.0]

[slide: v-526]
[pause: 0.6]
C: No.
C: Zero fenced-out writes could just mean nobody is sending tokens.
C: So I track coverage: the share of protected writes that carry a token, and a counter of writes that arrive without one.
[reveal: v-527]
[pause: 0.45]
C: And a double hold that causes no stale write is invisible to the resource.
C: The log audit finds overlapping holds from the server's durations.
[reveal: v-528]
[pause: 0.45]
C: The honest limit: you can observe a violation after the fact, and you can alarm on its precursors.
C: You cannot observe an absence of risk.
[pause: 0.8]

[slide: v-529]
[pause: 0.7]
V: If asked, I'd say: I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or the first sign of a problem. I read metrics in pairs so each page names a cause. I track how many protected writes carry a token at all, and I audit the grant log for overlapping holds. A green dashboard about the service says nothing about the promise.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-530]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: A distributed lock service is not one project. It is three, and they differ by an order of magnitude.
[pause: 1.8]

[slide: v-531]
[pause: 1.0]
C: Three releases, called R-zero, R-one and R-two so nobody confuses them with design versions.
[reveal: v-532]
[pause: 0.45]
C: A prototype to prove the model: about a month.
[reveal: v-533]
[pause: 0.45]
C: Production in one region for one or two teams: four engineers for five or six months, twenty to twenty-four engineer-months.
[reveal: v-534]
[pause: 0.45]
C: A company platform: seventy to a hundred and forty.
[reveal: v-535]
[pause: 0.45]
C: The best question available is: which of these are we actually being asked for, and who is the first customer?
[pause: 1.0]

[slide: v-536]
[pause: 1.0]
C: R-one, in detail.
C: A tech lead for protocol correctness.
[reveal: v-537]
[pause: 0.45]
C: A senior and a mid backend engineer.
[reveal: v-538]
[pause: 0.45]
C: A full-time S-R-E, because half of an infrastructure service is operations.
[reveal: v-539]
[pause: 0.45]
C: Plus fractions of a manager and a programme manager.
[reveal: v-540]
[pause: 0.45]
C: Phases: three weeks of discovery, four for a walking skeleton, six for correctness, including a linearizability test harness under injected faults, six for hardening, four for operations, and three for the first customer, in shadow mode and then cutover.
C: One assumption to state: if there is no committed first customer, the right decision is not to build.
[pause: 1.0]

[slide: v-541]
[pause: 0.6]
C: Ownership.
C: Twenty-four engineer-months to build.
[reveal: v-542]
[pause: 0.45]
C: Then about one and three-quarter people for five years, which is a hundred and five.
[reveal: v-543]
[pause: 0.45]
C: A hundred and twenty-nine in total, about eleven engineer-years, and infrastructure is about a tenth of it.
C: All illustrative.
[reveal: v-544]
[pause: 0.45]
C: People dominate.
C: And infrastructure services do not become free after launch: a service with no owner becomes an incident with no owner.
[pause: 0.8]

[slide: v-545]
[pause: 1.0]
C: Build, adopt, buy, or don't.
C: Don't: make the resource idempotent or use its conditional write.
C: Two weeks per resource.
[reveal: v-546]
[pause: 0.45]
C: Check first, every time.
C: Buy a managed transactional store: about four weeks.
[reveal: v-547]
[pause: 0.45]
C: Adopt a coordination store behind our own A-P-I: about ten weeks.
C: That is my R-one pick.
[reveal: v-548]
[pause: 0.45]
C: Build a custom service: about a hundred and twenty-nine engineer-months, justified only by a semantic nothing else gives, or very large scale.
C: I would write the buy-versus-build memo before any code, with the first customer's commitment in it.
C: And because the A-P-I is ours from day one, replacing the substrate later is a project, not a migration.
[pause: 1.0]

[slide: v-549]
[pause: 0.6]
C: What I would never cut: fencing end to end, the conservative client deadline, the linearizability harness, and the runbook with a qualified on-call.
[reveal: v-550]
[pause: 0.45]
C: What I'd cut first: multi-region, shared modes, first-come fairness, extra-language libraries, the admin console.
C: Top risks.
C: Fencing cannot be enforced at a key resource: descope that caller to an efficiency lock in writing.
[reveal: v-551]
[pause: 0.45]
C: Adoption fails: a named pilot before any code.
C: Scope creep into a general key-value store, which is what happened to the best-known lock service: written non-goals, with quotas enforced in code.
C: A key person who knows the protocol: pair, write design docs, two people on-call before launch.
C: And a split-brain incident: consensus, fencing, a harness in the pipeline, game days.
[pause: 0.8]

[slide: v-552]
[pause: 0.6]
C: Staffing.
C: Start small, because design by committee is slow.
C: Grow in the middle where the work parallelises.
[reveal: v-553]
[pause: 0.45]
C: Do not add people while stabilising.
C: Share the on-call rotation with a sibling team, so four people do not carry a twenty-four-seven pager.
V: The question I ask before saying yes: what happens if two of you hold this at once, and could the operation be made idempotent?
[pause: 1.0]

[pause: 1.4]

## 9 Recap

[slide: v-554]
[pause: 1.2]
C: Four minutes to close. One picture, one sentence per path, the mistakes to avoid, and the thesis.
[pause: 1.8]

[slide: v-555]
[pause: 1.3]
C: The final picture.
[reveal: v-556]
[pause: 0.45]
C: The library with sessions and a local deadline.
[reveal: v-557]
[pause: 0.45]
C: The gateway with quotas and the slot map.
[reveal: v-558]
[pause: 0.45]
C: Four consensus groups with leaders and a waiter queue.
[reveal: v-559]
[pause: 0.45]
C: The epoch store.
[reveal: v-560]
[pause: 0.45]
C: Metrics and a canary.
[reveal: v-561]
[pause: 0.45]
C: And at the resource,
[reveal: v-562]
[pause: 0.45]
C: the token check,
[reveal: v-563]
[pause: 0.45]
C: with a proxy where a resource cannot check.
[reveal: v-564]
[pause: 0.45]
C: Every box on it was added to answer one question the design raised.
[pause: 1.1]

[slide: v-565]
[pause: 1.0]
C: Five paths, one sentence each.
C: Acquire: one committed write and a token out.
[reveal: v-566]
[pause: 0.45]
C: Renew: one heartbeat per client, measured from send time.
[reveal: v-567]
[pause: 0.45]
C: Release and expiry: compare by token, hand off to the head waiter, and a dead session is one command.
[reveal: v-568]
[pause: 0.45]
C: Fence: the resource rejects anything older than it has seen.
[reveal: v-569]
[pause: 0.45]
C: Revoke: audited, and the next token is higher.
[pause: 1.0]

[slide: v-570]
[pause: 0.6]
C: If asked about multi-region.
C: Preferred: region-local lock services over region-owned resources, so there is no cross-region consensus at all.
[reveal: v-571]
[pause: 0.45]
C: Sparingly: a global lock for rare, coarse locks, accepting the latency.
[reveal: v-572]
[pause: 0.45]
C: Never: asynchronous replication of lock state.
C: That is split brain with extra steps.
C: A cross-region quorum costs thirty to two hundred and fifty milliseconds, which breaks the twenty-millisecond target.
[pause: 0.8]

[slide: v-573]
[pause: 0.6]
C: Ten mistakes in this round.
C: In the design: a cache key with an expiry presented as a correctness lock.
C: Tune the lease as the answer to a pause.
C: No token, or a token nobody checks.
C: Timestamps compared across machines.
C: Failing open without saying so.
[reveal: v-574]
[pause: 0.45]
C: In judgment: a beautiful consensus group and no word about the resource.
C: Never asking whether a lock is needed.
C: Offering atomic multi-lock.
C: Restoring an old snapshot.
C: And hiding the token in a thread-local.
[pause: 0.8]

[slide: v-575]
[pause: 0.7]
V: The lock service decides who should be working. The resource decides who is allowed to write. Everything I built is there so that those two answers can disagree safely.
[pause: 1.2]
C: Thank you. I'll stop there.
[pause: 1.6]
