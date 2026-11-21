# SD-24 Distributed lock service: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.
     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: TTL=T-T-L TTLs=T-T-Ls SDK=S-D-K API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is FLP=F-L-P NTP=N-T-P SQL=S-Q-L FIFO=fifo GC=G-C gRPC=g-R-P-C CAS=C-A-S RPC=R-P-C fsync=F-sync fsyncs=F-syncs ppm=P-P-M HTTP=H-T-T-P JVM=J-V-M ZooKeeper=Zoo-keeper etcd=et-C-D Redis=Reddis ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C CP=C-P DR=D-R UUID=U-U-I-D -->


## 0 Cold open

[slide: v-001]
[pause: 1.0]
C: A lock service sounds like a small problem. A key, an owner, an expiry. This question is not testing whether you can draw that. It is testing whether you notice what a lock cannot promise, and what you do about it.

[slide: v-002]
I: Design a distributed lock service that other teams use to make sure only one process does a thing at a time.
[pause: 1.5]

[slide: v-003]
C: Here is the hook. Holder A takes a lock and gets token forty-one. Then A freezes, for fifteen seconds. A garbage collection pause is enough.
C: At ten seconds the lease expires. The lock service is correct to expire it. Holder B asks, and gets token forty-two. B writes.
C: At fifteen seconds A wakes up. It has no idea time passed. It writes too. Two writers. The network was fine and no component misbehaved. The lock service's idea of who holds the lock and the resource's idea of who may write are different things, and nothing connects them.

[slide: v-004]
N: Five axes. The weak signal on each is the same shape: the happy path, drawn well. The strong signal is what happens when the happy path fails.
C: I will keep that table in mind. Correctness and operations are where I plan to spend the most time.

[slide: v-005]
V: A lock service says who should be working. Only the resource says who is allowed to write.
[pause: 1.0]
C: So my design has three layers. A lease, so a dead holder frees its lock. Consensus, so the record of who holds it survives failures and gives an order. And a fencing token, checked at the resource, which is what actually makes it safe.

[slide: v-006]
C: I'll go in this order. Requirements and scope. Then numbers. Then a short theory chapter, because the design leans on it. Then API and data, and a high-level design in three versions, each answering the objection to the one before.
C: Then the part I care most about: seven challenges that break the design, one at a time, where each fix creates the next question. A build cost, because someone has to own this. And a recap.


## 1 Requirements and scope

[slide: v-007]
[pause: 1.0]
C: Before I draw anything, I want to ask six questions. Each answer will change the design.

[slide: v-008]
C: Who calls this, and for what?
I: Internal teams. Background workers electing a leader. Per-entity exclusion before a write. And some run-this-job-once schedulers.
C: Three different uses. Leader election wants a long hold. Exclusion before a write wants a short one. Run-once wants no waiting at all. One API has to serve all three.

[slide: v-009]
C: What happens if two holders act at once?
I: It depends on the team. For some it corrupts records. For some it wastes an hour of compute. I'd like you to tell me how you would find out.
C: That is the most important answer so far. It splits locks into two kinds. If a double hold only wastes work, I call it an efficiency lock. If it corrupts data, it is a correctness lock. They need very different designs, and I'll ask every team which one they have.

[slide: v-010]
C: And the scale?
I: About ten thousand acquisition attempts a second. Around five thousand lock names. Holds from a hundred milliseconds to thirty seconds. Default lease, ten seconds.
C: Attempts, not grants. I'll use that difference in the estimates.

[slide: v-011]
C: Latency, availability and failure?
I: p99 acquisition under twenty milliseconds. It must survive the loss of a minority of nodes. One region, three zones. Multi-region is a later question.
C: Twenty milliseconds in one region is a quorum round trip, not a cross-region one. That rules out stretching one group across regions.

[slide: v-012]
C: What are the resources being protected, and who calls?
I: Mostly SQL databases and an object store. A few call partner H-T-T-P A-P-Is. Callers are J-V-M services. Assume stop-the-world pauses up to fifteen seconds in the tail. That is a fact, not a tuning problem.
C: Good. Two things. The pause is now a requirement, so the design must be safe when a holder stops for fifteen seconds. And partner A-P-Is are a problem I will come back to.

[slide: v-013]
C: Do callers need several locks at once, shared read locks, or strict order?
I: Several at once, some do. Tell me what you'd say. Shared mode, no. Strict first-come order is not required.
C: I'll scope out shared mode. I'll push back on several at once, and explain why in challenge six.

[slide: v-014]
C: Functionally, five things. One, acquire an exclusive lock on a name, with a bounded wait. Two, hold it and renew it, and find out fast if it is lost. Three, release it, and have a dead holder's locks freed automatically.
C: Four, and this is the one people forget: every grant carries a strictly increasing token that the caller can hand to the resource. And five, operators can inspect a name and force-revoke it, with an audit trail. Each of these gets its own numbered flow later.

[slide: v-015]
C: The numbers. They are initial targets, and I'll say so once for this chapter: none of these is a measurement.
C: Acquire p99 under twenty milliseconds, because a lock sits inside someone's request. Availability of ninety-nine point nine nine percent, about four point three minutes a month. A default lease of ten seconds, capped at sixty. And survive the loss of two of five replicas without anyone being paged to fix it.

[slide: v-016]
C: Three promises that are not numbers. If the service cannot decide, the protected operation does not proceed. That is failing closed, and it is a choice I'm making now, not later.
C: A dead holder's name frees within one lease. And tokens never go backwards, including after a disaster recovery. That last one sounds obscure. It will matter in challenge four.

[slide: v-017]
C: In scope: exclusive named leases with a bounded wait, sessions, tokens, operator tools, one region, and per-tenant quotas.
C: Out of scope, and I'm saying so on purpose. Shared and read-write modes: I'll add them behind the same A-P-I if someone needs them. Atomic multi-name acquire: that needs a transaction across groups, and I'll push back. Cross-region consensus: a quorum across regions cannot meet twenty milliseconds. And a general-purpose key-value store. That last one I'll write down as a non-goal, because it is how lock services get ruined.

[slide: v-018]
C: This split runs through everything that follows. An efficiency lock avoids duplicate work. If it fails once in a while, you waste some compute. A correctness lock protects data. If it fails, you corrupt something.
C: I treat them differently, and I ask every team which they have. Many say correctness and mean efficiency. Some say efficiency and mean correctness. Most of what people call a lock problem is really an idempotency problem, and I'll come back to that.

[slide: v-019]
V: The core is four things. A lease that frees itself. A consensus-replicated record of who holds it. A token that orders the grants. And a check at the resource.
[pause: 0.8]
N: Notice what the candidate did in six minutes. They asked what a double hold costs, cut four things out loud, and attached numbers. That is the framing signal.


## 2 Estimates

[slide: v-020]
[pause: 1.0]
C: Now the numbers. Every one is arithmetic from the inputs, and carries a label: given, illustrative, or an initial target. Each one has to change a decision, or I'll drop it.

[slide: v-021]
C: Ten thousand attempts a second, given. Multiply by a peak factor of three, which I'm assuming, because work tends to start at the top of the hour. That is thirty thousand at peak.
C: Decision: I size for the peak, not the average.

[slide: v-022]
C: Here is a number the prompt hides. One holder per name, around five thousand names. So at most five thousand locks can be held at any instant.
C: With a mean hold of half a second, that caps grants at ten thousand a second, and only if every name is always held. So most of the ten thousand attempts cannot succeed. They fail, or wait.
C: Decision: the A-P-I needs a bounded wait and an explicit try-once, because failure is the normal case on a busy name.

[slide: v-023]
C: Assume forty percent of attempts succeed: four thousand grants a second. Little's law says the number held at once is the arrival rate times the time held: four thousand times half a second, two thousand locks.
C: Split that. Two percent of grants are long holds, about twenty seconds, think leader election: eighty a second times twenty is sixteen hundred. The short ones are about four hundred. Almost all the held locks are the long ones. Remember that for renewals.

[slide: v-024]
C: Five thousand entries at about two hundred bytes each is one megabyte. The whole state fits in memory and snapshots in milliseconds.
C: Decision, and a common mistake to avoid: we shard for write throughput and for blast radius. We never shard because the data is big. It is not.

[slide: v-025]
C: Each grant is one committed write, and so is each release. Two times four thousand is eight thousand writes a second on average. Times three is twenty-four thousand at peak. Add waiter enqueues and expiries and I call it thirty thousand all-in.
C: Failed try-once attempts don't write. The leader answers them from memory under its leader lease. That is why the attempts number is so much larger than the writes number.

[slide: v-026]
C: One group's ceiling is the number I trust least, so it carries a label: fifteen thousand committed writes a second, with batched disk syncs, as an initial target I'll measure.
C: Thirty thousand divided by fifteen thousand times one half headroom is four groups. I'll hash names into sixty-four slots, so I can move slots later. One group nearly carries the average. We shard for the peak, and so a bad group takes a quarter of the names, not all of them.

[slide: v-027]
C: Renewals. A short hold, a hundred milliseconds, never renews, because the lease is ten seconds. Only holds longer than a third of the lease do, about three point three seconds.
C: That is the sixteen hundred long-held locks. Renewing each one every three point three seconds is about four hundred and eighty a second. If instead each client process keeps one session alive, and locks hang off the session, with four hundred clients that is about a hundred and twenty. And a dead client is one expiry, not fifty.
C: Decision: sessions.

[slide: v-028]
C: The latency budget. Twenty milliseconds at p99 is an initial target. Two milliseconds of network in. Three of batch wait. Four for the leader to sync its disk. Five for a follower round trip and its own sync. One to apply and reply. Two of network out.
C: That is seventeen, with three milliseconds spare. It only works because the quorum is in one region, across three zones. A cross-region quorum costs thirty to two hundred and fifty milliseconds by itself. Also: stage p99s don't add up to an end-to-end p99. This is a planning budget. I'd measure the whole path.

[slide: v-029]
C: Two numbers that settle arguments. A fifteen-second pause beats a ten-second lease. Raise the lease to sixty and a seventy-second migration still beats it, while every real crash now stalls its name for a minute. Tuning the lease cannot fix this. A token can.
C: And one name can grant at most one over the hold time: ten a second at a hundred milliseconds. A name asked forty times a second is four times over, however many machines I add.

[slide: v-030]
C: Three more. Clock drift of two hundred parts per million over a ten-second lease is two milliseconds. The client will stop at seven seconds and the server waits ten, so there is a three-second gap. Drift is not the risk. Pauses are.
C: The availability target gives two hundred and fifty-nine seconds a month. At two seconds an election, about a hundred and thirty elections a group spend all of it. So elections per day becomes something I watch.
C: And a token is sixteen bits of epoch plus forty-eight bits of log index. Forty-eight bits lasts about six hundred years at fifteen thousand a second. All of these are labelled arithmetic, not measurements.


## 3 Theory

[slide: v-031]
[pause: 1.0]
C: A short theory chapter before any design, so the design can lean on it. Six parts: what a lock service is and is not, the two properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide in this chapter has a theory badge.

[slide: v-032]
V: A distributed lock service is a small, consensus-replicated store of named leases. It gives one holder at a time permission to act on a name, for a bounded time, together with a number that orders every grant on that name.
[pause: 1.0]
C: Every clause carries weight. Consensus-replicated, so a failover cannot forget a grant. Named, so locks are independent and can be sharded. Bounded time, because we cannot tell a dead holder from a slow one. And a number that orders, which is the part the resource needs.

[slide: v-033]
C: Three neighbours. It is not a mutex. A mutex lives in shared memory and can stop the holder. A distributed lock cannot reach into a paused process and stop it. It is not a queue: there is no payload and no ordering of work. If a team wants one at a time per entity, in order, they want a single writer per partition.
C: And it is not a transaction. It protects nothing on its own. The resource has to take part. Leader election is a use of a lock, not a different thing.

[slide: v-034]
V: Safety: two parties must never both act as the holder, with both effects taking hold at the resource. Liveness: a free name is eventually granted, a dead holder's name is eventually freed, and a waiter is eventually served or told no.
[pause: 0.8]
C: A service that grants nothing is perfectly safe. A service that grants everything is perfectly live. The engineering is in getting enough of both. From now on, every fix says which property it protects.

[slide: v-035]
C: There is a result from the nineteen-eighties, F-L-P. In an asynchronous network, if even one process can fail, no protocol can both always agree and always finish. Real systems add a timing assumption, usually a timeout, and then pick which property to give up.
C: Consensus systems keep safety unconditional and lose liveness during a partition. A group without a majority stops, rather than risk two leaders. That is my position as well, and I'll state it whenever it matters.

[slide: v-036]
C: Here is the tension everything comes from. When a holder goes quiet, the service cannot tell whether it crashed or is only slow. So the service does not try to detect death. It makes the grant expire.
C: Then the lease length is a trade. A short lease frees a crashed holder's name quickly, but expires slow holders that are still alive. A long lease does the opposite. The default is ten seconds. Our pause is fifteen. And no setting on this line removes the pause. Remember that.

[slide: v-037]
C: Mechanism one, the lease. It protects liveness. A grant is valid for a stated time, after which the service may reassign the name without asking. That rules out a lock held forever by a dead holder. It costs two things: a slow holder can lose its lock while alive, and a crash stalls that name for up to one lease.

[slide: v-038]
C: Mechanism two, a consensus-replicated record. It protects the safety of the grant record. Every grant is an entry committed by a majority, with one leader per term. A stale leader cannot get a majority, so it cannot commit. That rules out split brain, and a failover that forgets a grant. It costs a quorum round trip on every write, an outage without a majority, and a cluster to run.

[slide: v-039]
C: Mechanism three, the fencing token. This is the one that makes the design safe. Each grant carries a number larger than every earlier grant for that name. The resource remembers the highest number it has accepted and rejects anything smaller. That rules out a paused holder's stale write. It costs one number per protected row, and the resource has to take part. Note the last cost: it orders writes, but it does not by itself make a multi-step read consistent. Challenge one comes back to that.

[slide: v-040]
C: Mechanism four, clocks. A wall clock can jump forwards or backwards. A monotonic clock only measures elapsed time on one machine. So the client times its lease from the moment it sent the request, on a monotonic clock, and gives up at seventy percent of the lease. That rules out clock steps and skew. It costs thirty percent of the lease, and it still assumes drift is bounded.

[slide: v-041]
C: Mechanism five, sessions. A client keeps one session alive with one heartbeat, and its locks hang off the session. When the session dies, all its locks free in one command. That rules out renewal storms and fifty separate expiries. It costs a coarser failure unit: one missed heartbeat drops every lock the client holds.

[slide: v-042]
C: Mechanism six, determinism. Every replica applies the same entries in the same order. If a replica read its own clock while applying, replicas would diverge, and a diverged lock service is an unrecoverable incident. So the leader writes the time into the entry, and expiry is itself a replicated command. It costs a little delay on expiry, and a new leader must work out which expiries are pending.

[slide: v-043]
C: Mechanism seven, bounded wait with directed hand-off. Waiters queue per name with a cap. A release grants directly to the head of the queue in the same committed step. That rules out the herd, the unbounded queue, and polling. It costs queue state in the replicated machine, and first-come ordering adds some tail latency.

[slide: v-044]
C: Now the options. Six approaches, each with the failure that rules it out. Three that look cheap first.
C: A, one cache node with set-if-absent and an expiry. Replication is asynchronous, so the primary can acknowledge a grant and die before the copy arrives. The new primary has no record and grants it again. Fine for an efficiency lock. Never claim it as a correctness lock.
C: B, a quorum of independent cache nodes. It tries to fix that, but its safety rests on timing: a pause between acquiring and using, or one node's clock jumping, breaks it. And it issues no token. It is a well known debate, and I know it, but I would not propose it for correctness.
C: C, a relational row. Underrated. With synchronous commit it is safe, and a version column is a token. It fails above a few thousand grants a second, or on a hot row. And a plain row lock is tied to a connection, so it has no lease. If the protected resource is in that same database, the lock and the work commit together, and the whole problem mostly disappears.

[slide: v-045]
C: Here are all six. D is a consensus-backed coordination store, the ZooKeeper, etcd or Consul family. It has leases, compare-and-set, and a revision number that is a ready-made token. It fails when load exceeds one cluster, and then I shard. Or when I need semantics it cannot express.
C: E, building my own consensus service, has the same safety and gives me full control, and it is far more expensive to run. It fails if I cannot staff it. F is no lock at all: a conditional write or an idempotency key at the resource. It fails when the operation is not idempotent and the resource has no conditional write.
V: I pick D, after asking whether F applies.
[pause: 0.8]

[slide: v-046]
C: What the pick gives up, said plainly. One cluster's write ceiling, so I'll shard in challenge five. Fairness, priority and shared modes, which that store does not express. Cross-region reach. And the burden of running a consensus cluster, which is real.
C: What it buys: safety proven by someone else's consensus, leases and a revision number built in, and, behind my own A-P-I and S-D-K, the ability to swap the substrate later if evidence says I should. And before any of it, I always ask whether row F applies.

[slide: v-047]
C: If asked why not a row lock in a relational database. No lease: the lock lives as long as the connection, so a paused client keeps it. No token: nothing the resource can check later. It is the right answer when the resource lives in the same database, so the lock and the work commit together, or when the load is under a few thousand a second. Saying that is a better answer than reaching for a consensus cluster by reflex.

[slide: v-048]
C: Last part. The failure catalogue, which becomes the challenge list. F-one, a holder crashes. The lease handles that, and the flows show it. F-two, a holder pauses and resumes: challenge one. F-three, the resource cannot check a token, or no lock is needed at all: challenge two. F-four, clocks: challenge three. F-five, the leader fails, a partition, or the whole group is lost: challenge four.

[slide: v-049]
C: F-six, duplicates, stale releases and delayed messages. I design those out in the A-P-I, so they are not a challenge: release takes the token, and acquire carries a request id. F-seven, a load peak: challenge five. F-eight, a hot name, a herd or several locks: challenge six. F-nine, a holder that is hung but alive: bounded leases and force revoke. And F-ten, nobody notices: challenge seven. Seven challenges, in that order.

[slide: v-050]
N: Good theory has a consequence for the design. Look at this table: every mechanism names the property it serves, and where it will be used.
C: That is the vocabulary. On to the design.


## 4 API and entities

[slide: v-051]
[pause: 1.0]
C: The A-P-I before the boxes. It is the contract, and it shows whether I've thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes.

[slide: v-052]
C: Session calls. OpenSession takes an owner name and a lease length, capped at sixty seconds, and returns a session id and the current epoch. It serves requirement two and writes a session entity.
C: Heartbeat is a stream, about every three point three seconds. The response has no timestamp that matters. The server time is for logs only. The client trusts nothing in the reply except that it was acknowledged, and measures its own deadline from when it sent the beat.

[slide: v-053]
C: Acquire. The name, the session, a request id, and a maximum wait. A wait of zero means try once. There is no way to wait forever, on purpose.
C: Four answers: granted with a token and a lease, queued with a position, timed out, or contended with a retry-after. The request id makes a retry safe. If the network duplicates the request, the service returns the same token and not a second one. That is how failure six, duplicates, is designed out.

[slide: v-054]
C: Release takes the token, not just the name. If the token matches the current holder, the name is freed and handed to the head waiter. If it does not, the call is rejected, because someone else holds it now.
C: Think about what that removes. A holder whose lease expired, then wakes and calls release, cannot free the new holder's lock. That failure is not guarded against. It cannot be expressed.

[slide: v-055]
C: Two operator calls. Inspect shows who holds a name. It is documented as never to be used for a correctness decision, because the answer can be stale by the time you read it.
C: ForceRevoke is the break-glass call. Every lock service eventually needs one, usually at three in the morning. I'm designing it in now: it takes a reason and an operator, writes an audit entry, and alerts. The next grant gets a higher token, so the revoked holder is fenced like any other.

[slide: v-056]
C: This is not our A-P-I, but it is part of the contract, and I'll say it every time. Every write to a protected resource carries the token, and the resource rejects it if the token is smaller than the highest it has accepted. Here that is one conditional update.
C: Precision: equal is allowed. The same holder may write several times with the same token. Only smaller is rejected. And pass the token as an explicit argument. If it hides in a thread-local, it is lost the first time work moves to another thread pool, and silently.

[slide: v-057]
C: Reentrancy comes up, so I'll dismiss it aloud. Yes, a holder may acquire a lock it already holds. I'd do it as a hold count in the client library, keyed by session. The server keeps one grant per name. Doing it on the server would double the writes for nothing. One subtlety: scope it to the session, not the process, or a client that reconnects with a new session deadlocks against its own old grant.

[slide: v-058]
C: The conceptual model. A tenant owns lock names. A session holds names, and the relationship carries the token and the expiry. A session waits for names, with a position. A lock name protects resource rows, and a row stores the highest token it has accepted, a derived attribute. And an audit event is a weak entity: it only exists in the context of a lock name.
C: One cardinality matters most: a name has at most one holder at a time. That one fact is why locks are independent per name, and so why this shards.

[slide: v-059]
C: Physically. The held table is keyed by name, with owner, session, token and an expiry that is in log time, not wall time. The waiter table is keyed by name and a sequence, capped in depth. The session table holds the lease and its names. The last heartbeat is volatile, not in the log.
C: Two things live outside the group. The epoch and a token floor per slot, durable, which challenge four and five use. And at the resource, the protected row carries a fence column. Everything in a group is keyed by name, and a name lives in exactly one group, so there are no cross-group transactions.

[slide: v-060]
C: The state machine is small enough to read whole. Apply runs on every replica, in log order. If the same owner retries, it returns the same grant. If the name is held, it enqueues. Otherwise it grants, and the token is the log index of this very entry. Monotonic, and free.
C: Look at the time. It is not read from a clock here. It is a field in the entry, stamped by the leader before replication. If each replica read its own clock, two replicas could disagree about whether a lease expired, and the group would diverge. That is the most common bug in home-built replicated state machines.

[slide: v-061]
C: The token itself. Sixty-four bits. Sixteen for an epoch, forty-eight for the log index within a group. Compared as a number, so a bigger epoch always wins. The epoch changes only on a rebuild or a slot move, which is what makes tokens survive a disaster, in challenge four.
C: A timestamp is not a valid token, because clocks go backwards. A random identifier is not either, because it has no order.

[slide: v-062]
C: Four stores, and for each: can I lose it? The replicated log survives losing a minority. Losing all of it means starting empty. Leader memory holds heartbeat times. Losing it is harmless: a new leader treats every session as alive for one lease.
C: The epoch store must not be lost, or tokens could go backwards. And the resource's own durability matters too: the token check is only as good as the store that keeps the highest token.


## 5 High-level design

[slide: v-063]
[pause: 1.0]
C: Three versions. Each one is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move.

[slide: v-064]
C: Version one. An app with a lock library, and one lock server. The server keeps a map from name to owner and expiry in memory. Acquire checks the map. A lease means a dead holder's name frees itself. The app also writes to its resource, drawn on top. No objection yet. It is the simplest thing that works, and for an efficiency lock it might be enough.

[slide: v-065]
C: The objection. The server restarts, and forgets who holds what. A holds a lock. The server crashes at four seconds and restarts at five with an empty map. B asks, and is granted the same name. A is still working. Two holders, and the lock service caused it. And one box is a single point of failure for every team.

[slide: v-066]
C: Version two answers that. The single server becomes a consensus group of five replicas: one leader and four followers. Every grant is a log entry, and it counts only once a majority of replicas have it. If the leader dies, a follower that has the committed entries takes over, so no grant is forgotten.
C: And the token falls out of this for free. It is the log index of the grant entry. Increasing by construction, with no extra machinery.

[slide: v-067]
C: The group in one slide. One leader per term. All writes go to it. A node that sees a higher term obeys it. An entry commits when three of five replicas hold it, and any future leader must have been in that three, so it has the entry. And with only two of five reachable, nothing commits. Safety is kept, and availability is given up. That is the trade I chose in the theory.

[slide: v-068]
C: The objection to version two. The consensus group is right, but the caller still cannot tell when it has lost the lock. A holder whose lease expired keeps working. And every team would write its own heartbeat, its own clock arithmetic and its own retries, and each would get it subtly wrong. Half the correctness lives in the client library, so the library is part of the product.

[slide: v-069]
C: Version three. The lock library holds one session, with one heartbeat, the dashed purple arrow. It tracks a local deadline on a monotonic clock, and calls back with LockLost the moment the deadline passes, so application code can stop. A stateless gateway sits in front: it authenticates, applies tenant quotas, and routes to the group's leader.
C: The token comes back in the grant, and the app passes it to the resource, the grey box on top. This is the baseline. It stays on screen from here, and every later picture is a view of it.

[slide: v-070]
C: The library's heartbeat is short. Note the time before sending, on a monotonic clock. If the beat succeeds, move the deadline to that send time plus seventy percent of the lease. If it fails and the deadline has passed, drop every lock, loudly. Failing closed.
C: A warning I'll repeat. A check-still-held call before a write narrows the window, and does not close it. Between the check and the write the lease can still expire. That is the next problem.

[slide: v-071]
C: What version three leaves open. It has a correct record, a library that stops on loss, and a token in the caller's hand. What it lacks: the resource accepts any write. A paused holder that wakes after its lease expired still writes. Safety is not here yet. That is challenge one, and I'll get there after the flows.

[slide: v-072]
C: Requirement one, acquire. Step one: the library sends Acquire with the name and a request id. Step two: the gateway authenticates, checks the tenant's quota, hashes the name to a slot and routes to that group's leader.
C: Inside the box, which the next sequence shows: the leader appends the entry, a majority acknowledges, it commits, and apply grants with the log index as the token. Step three: the token and lease come back to the gateway. Step four: back to the library, which sets its deadline from when it sent the request.

[slide: v-073]
C: Requirement two. Step one: a heartbeat, dashed purple because it is asynchronous, goes from the library to the gateway. Step two: the gateway passes it to the leader as a session-alive note.
C: The leader keeps liveness in memory under its own leader lease, so a heartbeat is not a consensus write. Only an actual expiry becomes a log entry. When the beat is acknowledged, the library moves its deadline from the time it sent it.

[slide: v-074]
C: Requirement three, release. The same four arrows. One: Release with the name and the token. Two: routed to the leader. The leader commits, and apply compares the token, frees the name, and hands it to the head waiter in the same step. Three and four: the answer comes back.
C: A dead holder uses no arrow at all. Its heartbeats stop. After one lease the leader proposes a single session-expired command, and every name that session held is freed at once.

[slide: v-075]
C: Requirement four, the most important arrow. Step one: the application writes to the resource over the top path, with the token. Step two: the resource compares it with the highest token it has stored for that row. Not smaller: accept, and store it. Smaller: reject with FencedOut, log both tokens, and alert.
C: This arrow does not touch the lock service at all. That is the point. The lock service issued an order. The resource enforces it.

[slide: v-076]
C: Requirement five. Step one: the operator console calls ForceRevoke with a reason. Step two: the gateway checks the operator's identity and routes to the leader. The leader commits a revoke entry and an audit entry. Step three: the answer returns.
C: The old holder learns on its next heartbeat. And even if it does not, its next write is fenced, because the next grant gets a higher token.

[slide: v-077]
C: The C4 context. Application teams use the lock service and write to their own resources, with the token. Operators inspect and break glass. The lock service reports metrics to an observability platform. Notice the arrow from the application team straight to the protected resources, not through the lock service. That is deliberate.

[slide: v-078]
C: The containers. Inside the lock service boundary: the lock library, which runs inside the application, the gateway, the consensus groups, four of them, an epoch store, and an operator console. The application calls the library in process. The library talks g-R-P-C to the gateway, which proposes to the group leader. The group reads and bumps the epoch only on a rebuild. And the application writes to the resource directly, with the token.

[slide: v-079]
C: Acquire as a sequence. One: the library sends Acquire. Two: the gateway routes by hash of the name to the leader. Three: the leader appends the entry to the followers. Four: they acknowledge, and a majority makes the entry commit. Then apply: the name is free, so grant, token equals the log index, say nine thousand and one. Back to the gateway, and to the library, which sets its deadline from its send time.

[slide: v-080]
C: The loss path. One: heartbeat. The ack moves the deadline. Then the network drops. No reply, and no beat reaches the leader. Two: at the deadline, seven seconds after the last send, the library tells the application LockLost, and the application stops before its next side effect. Three: later, the leader sees no beat for a full lease and proposes SessionExpired. Four: that commit frees the names, and the head waiter is granted, with a higher token. The client stopped first, by design.

[slide: v-081]
C: Release. One: holder A releases with token forty-one. Two: the leader commits, and apply sees the token matches, so it frees the name. Three, in the same step: the head of the queue is B, so grant, token forty-two. Four: A gets its answer. Five: B is told it was granted. One committed write, one waiter woken, no polling.

[slide: v-082]
C: The check at the resource. The current holder writes with token forty-two. The stored maximum is forty-one, forty-two is not smaller, so accept and store forty-two. Later a stale holder writes with forty-one. The stored maximum is forty-two. Forty-one is smaller, so reject, log both tokens, and alert.

[slide: v-083]
C: Last in the design, what a correct caller looks like. The wait is bounded. If the lock is not granted, no side effect happens. The check-still-held call narrows the window. Then the token goes to both protected resources, the payment call and the database write, because both must check. And a LockLost exception aborts safely. It never continues anyway.

[slide: v-084]
C: Mechanism before brand. What must the substrate give me? Leases that expire. An atomic compare-and-set. A monotonic number per change, my token. And ordered, resumable watches so waiters wake in order. A coordination store in the ZooKeeper or etcd family has all four. If the store I'm offered lacks one of them, it is the wrong store.


## 6 Bridge

[slide: v-085]
[pause: 1.0]
V: It works. The question now is where it breaks first.
[pause: 1.0]

[slide: v-086]
C: Here is the baseline with seven attack points. A paused holder, at the resource. A resource that cannot check tokens. Clocks, in the library. The leader and the partition, in the group. Peak load, at the gateway and the group. A hot name, in the group. And finally: how would we know any of it was broken? I'll take them in an order where each fix creates the next question.


## 7 Challenges

[slide: v-087]
[pause: 1.0]
C: Seven challenges. Each one runs the same way: the question, the naive answer, a case with numbers, where it breaks, the fix, why it works, then the interviewer pushes on the fix itself, and I answer what I'd say in the room.


## 7.1 Challenge 1: The paused holder

[slide: v-088]
I: A holder is stopped by a fifteen-second garbage collection pause. Its lease expires, another process acquires, and then the first one wakes up. Both now write. What saves you?
[pause: 2.0]

[slide: v-089]
C: The first answer most people give: make the lease longer, and check the lease is valid just before writing. Look where it breaks. The red arrow, from the client to the resource. The lock service did everything right, and the resource still accepts both writes. A check before a write is not atomic with the write. Between them, the lease can expire. That is the pause, exactly.

[slide: v-090]
C: The trace with numbers. A gets token forty-one at zero, reads, checks that it still holds the lock, and pauses at point three. The lease expires at ten. B acquires at ten point four, token forty-two, and writes at ten point five. At fifteen point three A resumes and writes. It checked. It was right to check. It was just too early.
C: Raising the lease to sixty seconds moves the line, and a seventy-second pause still beats it, while every real crash stalls its name for a minute. These numbers are illustrative. The shape is what matters.

[slide: v-091]
C: The fix is the fencing token, checked at the resource. The new green box is the check. The grant already carries a token, which is the log index. The resource keeps the highest token it has accepted for that row, and rejects any write that carries a smaller one.

[slide: v-092]
C: Replay it. A holds forty-one and pauses. B gets forty-two and writes: accepted, the resource stores forty-two. A wakes at fifteen point three and writes with forty-one. Forty-one is smaller than forty-two. Rejected. Notice what did not change: the pause, the lease, the lock service. Only the resource became safe.

[slide: v-093]
C: As a sequence. A acquires and gets forty-one. A pauses fifteen seconds. B acquires after the lease expired and gets forty-two. B writes with forty-two, accepted. A resumes and writes with forty-one at fifteen point three, and the resource rejects it: forty-one is smaller than forty-two.

[slide: v-094]
C: In code, on a database row it is one conditional update. Set the amount and the fence, where the fence is less than or equal to the token. Zero rows updated means fenced out: log both tokens and alert. On an object store, the object's generation number is the token, and the write is conditional on it.
C: Why it works, as a property: safety, enforced where the effect happens. Consensus gives a correct order. The resource, the only place that can check and write in one atomic step, enforces it. And precisely: equal tokens pass, because one holder may write several times. Only smaller is rejected.

[slide: v-095]
I: A's stale write arrives before B's first write. The resource has only seen forty-one, so it accepts A. Then B, who read the old row, writes forty-two on top. Is that fenced?
[pause: 2.0]

[slide: v-096]
C: No, and that is the honest limit. Fencing rejects stale writes after a newer token has been seen. Here A's write lands first, when the resource has only seen forty-one. It is accepted. Then B, working from an older read, writes on top of it, and A's update is lost.
C: Two ways to close it. One: make B's critical section a single conditional write against the version it read, so the token is the version. Two: B claims its token at the resource before it reads. After that, any write from A is rejected. The cost is one extra round trip, or a critical section that fits in one conditional write.

[slide: v-097]
C: The claim as a sequence. B claims token forty-two at the resource before reading. The resource now stores forty-two. A, the stale holder, writes with forty-one: rejected. Then B reads the row and writes with forty-two, conditional on the version it read. The window is closed.

[slide: v-098]
V: If asked, I'd say: a lease cannot guarantee exclusion at the resource, because the holder cannot know it still holds the lock when its write lands. So the grant carries a token that only increases, and the resource rejects anything older than it has accepted. Safety lives at the resource. The lock service only has to give a correct order.
[pause: 1.0]
N: That fix creates the next question: what if the resource cannot check?


## 7.2 Challenge 2: The resource cannot check

[slide: v-099]
I: The thing you are protecting is a partner's H-T-T-P A-P-I, or a cron job. There is no conditional write. Now what?
[pause: 2.0]

[slide: v-100]
C: The naive answer: use a long lease, trust the library, and call it correct. It is not. Here is a payment call to a partner with no idempotency key. The holder pauses after its lock check, and the call happens twice. The grey box has nowhere to put a fence.

[slide: v-101]
C: Before building, sort the callers. An illustrative survey of a hundred. Fifty-five only want to avoid duplicate work: that is an efficiency lock, and no token is needed. Thirty write to a store with a conditional write or a version column: the resource's own version is the token, and the lock service is just an optimisation.
C: Ten call something with neither: for those I build a validating proxy. And five are truly non-idempotent, with no check possible. For those, no lock can make them safe. The answer is to change the contract, or accept the risk in writing, with a named owner.

[slide: v-102]
C: So the order of questions. One: is the operation idempotent? If so, give it a key, the lock name plus the job instance, and a double hold becomes harmless. Two: does the resource have a conditional write? Use its version as the token. Three: otherwise put a validating proxy in front of it. Four: if none of these fit, ship an efficiency lock, and say so plainly in the contract. Each option moves safety to a place that can check and act atomically.

[slide: v-103]
C: The proxy, for the ten. It sits in front of the partner's A-P-I and keeps the highest token per resource in a consistent store. A call with a fresh token is forwarded. A stale one is rejected, and the partner never sees it. The property: safety, moved to a place where a check can be made atomic.

[slide: v-104]
C: As a sequence. The app calls through the proxy with token forty-two. The proxy sets the maximum to forty-two with a conditional update, which applies, then forwards the call, and the response comes back. A stale holder calls with forty-one. The conditional update does not apply, because the maximum is forty-two, so the proxy rejects it, and the partner never sees the call.

[slide: v-105]
I: The proxy is now a single point of failure, and a new thing that must itself be consistent. And your idempotency records: how long do you keep them?
[pause: 2.0]

[slide: v-106]
C: The proxy fails closed, keeps its table in a consensus-backed store, and is scoped per resource class, so one failure does not take everyone. Idempotency records live at least as long as the maximum lease plus the maximum pause plus the retry horizon. For a sixty-second lease, an illustrative twenty-four hours.
C: And the honest limit. A non-idempotent call to a system with no check cannot be made safe by any lock. The answer is to change the contract, or accept the risk with an owner.

[slide: v-107]
V: If asked, I'd say: before I build a lock for a team I ask what a double hold costs, and whether the operation can be made idempotent. If the resource supports a conditional write, the resource enforces exclusion and the lock is an optimisation. I only claim a correctness lock where something downstream checks the token.
[pause: 1.0]
N: Next: if safety rests on the token, how much does it rest on the lease clock?


## 7.3 Challenge 3: Clocks and leases

[slide: v-108]
I: A client's clock is five seconds slow. Or time is stepped back eight seconds in the middle of a lease. What happens to the lease?
[pause: 2.0]

[slide: v-109]
C: The naive design: the server returns an expiry timestamp, and the client compares it with its own clock. Look at the box under attack, the library. It trusts a time from a machine whose clock it has no reason to trust.

[slide: v-110]
C: The case. The server grants at its time zero, expiry at ten. The client's clock is five seconds slow, so it believes it holds until its own ten, which is server time fifteen. From server time ten to fifteen, B has been granted the name and A still believes it holds it. Two holders, for five seconds. A fast clock is merely wasteful. A step back of eight seconds mid-lease does the same to a perfectly good client. And a timestamp is no good as the token either, for the same reason.

[slide: v-111]
C: The discipline is to use each kind of time for one job. A wall clock can jump either way: clock steps, leap seconds, virtual machine migration. Never use it for a lease. A monotonic clock never goes backwards on one machine, but means nothing across machines. Use it for durations. And logical order, the log index and the term, says nothing about duration but is totally ordered. Use it for the token.

[slide: v-112]
C: The fix. The library measures its deadline as the monotonic time when it sent the request, plus seventy percent of the lease. The server counts the lease from its own commit, on its own monotonic clock. And inside the replicated machine, the leader writes the apply time into the log entry, so replicas never read their own clocks. No timestamp crosses the wire.

[slide: v-113]
C: Replay it. The client counts from when it sent: seven seconds. At seven it stops. The server waits the full ten. Between them, a three-second margin. The client always stops first, so there is never a window where it believes it holds a lock the server has given away. And drift? Two hundred parts per million over ten seconds is two milliseconds. The margin is for round trips and scheduling, not for drift.

[slide: v-114]
I: What if the process pauses between reading the monotonic clock and doing the write? Or drift is far above your assumption, as on a throttled virtual machine?
[pause: 2.0]

[slide: v-115]
C: Two honest answers. A pause between the clock read and the write: the margin cannot see it. That is challenge one again, and the token is the backstop. And drift beyond the assumption: bounded drift is an assumption, and I'll say so. But once fencing is in, it is no longer load-bearing for safety. It only affects how often a holder is fenced. So I monitor clock health and the rate of missed deadlines, and keep the margin configurable per tenant.

[slide: v-116]
V: If asked, I'd say: I use monotonic clocks for durations and logical order for correctness. The client gives up before the server does, so there is never a window where it believes it holds a lock the server has given away. And because that still assumes bounded drift, the token at the resource is what the safety argument rests on.
[pause: 1.0]
N: So far, every failure was at the edges. What if the middle fails?


## 7.4 Challenge 4: Leader loss, partition, group loss

[slide: v-117]
I: The leader dies mid-grant, and a partition leaves two of the five replicas talking to some clients. What do those clients see?
[pause: 2.0]

[slide: v-118]
C: The naive answer: promote a follower fast, and let the minority side keep serving, to stay available. Look where it breaks, the consensus group. Serving on the small side means two sides can each grant the same name.

[slide: v-119]
C: The case. Replicas one to five. R-one leads in term seven. A partition isolates R-one and R-two from R-three, four and five. The big side hears no leader for a second and a half and elects R-three in term eight. R-one still believes it leads, but it can reach only one other replica out of five. It cannot get a majority. So it cannot commit, and cannot grant.

[slide: v-120]
C: As a sequence. Client Y, on the majority side, asks for x. R-three commits it with a majority: granted, token nine thousand and one. Client X, on the minority side, asks R-one for x. R-one cannot reach a majority, so it answers unavailable. No grant. When the partition heals, R-one sees term eight, steps down, and discards anything uncommitted. The small side got an honest no.

[slide: v-121]
C: The fix is mostly what version two already had, plus two details. Only the majority side commits. A stale leader steps down when it sees a higher term. Heartbeats are answered by the leader under a short leader lease, so no log entry per beat. And a new leader treats every session as alive for one full lease after election, called a grace period. Otherwise a failover would see every heartbeat gap as a death and evict every lock at once.

[slide: v-122]
C: Why it works. Safety is kept: two replicas cannot commit, so a partition cannot create two holders. Liveness is given up, on the small side only. A failover costs about two seconds. And tokens stay monotonic across terms, because they are log indexes.
C: There is no clever third option here, and I won't pretend there is. I'd rather say the position plainly: for a correctness lock, unavailability of the lock service must become unavailability of the protected operation. If the business cannot accept that, the requirement is really an efficiency lock, and I'd make the resource idempotent.

[slide: v-123]
I: Three of the five replicas are gone. Or someone restores last night's snapshot. What happens to the tokens?
[pause: 2.0]

[slide: v-124]
C: Without a majority, the service fails closed: libraries reach their local deadlines, get LockLost, and stop. That part is fine. The dangerous part is the restore. Restore Monday's snapshot, and the log index goes back. The next grant of that name reuses a token that was already issued. The resource has stored a much higher number, so it rejects every new holder as stale. And in the other direction, a stale holder from before the loss could slip through. Tokens must never go backwards, even across a disaster.

[slide: v-125]
C: So disaster recovery is not restore. It is start empty with a higher epoch. One: the operator bumps the durable epoch, six to seven, in the epoch store. Two: the new group starts empty, with its token floor at epoch seven, shifted left forty-eight bits. Three: a quiet period of one maximum lease, sixty seconds, in which the group refuses grants, so every old holder has stopped on its own deadline. Four: libraries open sessions again, and grants resume with tokens above everything ever issued.

[slide: v-126]
C: The cost is a minute of outage during a rebuild. The quiet period equals the longest lease we allow. The epoch is sixteen bits, so sixty-five thousand rebuilds, far more than will ever happen. All of that is derived, not measured. A minute of outage is cheap, next to the alternative of two holders.

[slide: v-127]
V: If asked, I'd say: under partition I choose safety. The minority side refuses, it does not guess. After the loss of a whole group I start empty with a higher epoch, so every new token exceeds every old one, and I wait out the longest possible lease before granting. The outage is a minute. The alternative is two holders.
[pause: 1.0]
N: Now the failure is not a fault. It is success: too much traffic.


## 7.5 Challenge 5: The top of the hour

[slide: v-128]
I: At the top of the hour traffic triples, and two thousand clients retry at once after a network blip. What happens, and what do you do?
[pause: 2.0]

[slide: v-129]
C: The naive answers: add replicas, or shorten the lease. Neither touches the problem. One group carries about fifteen thousand committed writes a second, and the peak is thirty thousand. The group box is the bottleneck.

[slide: v-130]
C: Trace it. Thirty thousand writes a second arrive and the group commits fifteen. The backlog grows by fifteen thousand a second. After ten seconds it is a hundred and fifty thousand deep, and latency is longer than the ten-second lease itself. Grants that were in flight have already expired. Clients retry, which adds load. A metastable collapse: the system cannot recover even if the peak passes.
C: And more replicas do not help. Every write must reach a majority. Replicas add fault tolerance, not write throughput. These figures are illustrative, from the estimates.

[slide: v-131]
C: The fix. Hash the name into sixty-four slots, and map slots to four groups. Thirty thousand over fifteen thousand times half is four. The gateway applies per-tenant quotas, and answers overloaded with a retry-after, instead of queueing. The library retries with jittered backoff. Sessions keep renewal at about a hundred and twenty a second, not four hundred and eighty. And the leader batches many entries into one disk sync.
C: This works because locks are independent per name. There are no cross-group transactions, so the partition is free.

[slide: v-132]
C: As a sequence. The library asks. The gateway sees the tenant over quota, or the group's queue deep, and answers overloaded, retry after two hundred milliseconds. The library waits that long plus a random jitter, so two thousand clients do not return in the same instant. It retries, and this time it is admitted, routed to the leader, and granted.

[slide: v-133]
I: One group goes bad. Or you need to move a slot while its locks are held.
[pause: 2.0]

[slide: v-134]
C: A bad group takes a quarter of the names with it and fails closed. The other three are untouched. That is the blast radius, and it is why I shard even though the data is tiny. Moving a slot is the dangerous part. A name moving while it is held is a correctness hazard. So: freeze the slot, drain its held locks, which takes at most one maximum lease, bump the slot's epoch so the new group's token floor sits above the old group's, then unfreeze in the new group.
C: Skip the epoch bump and a name that moves to a group with a lower log index would see its tokens go backwards. Same rule as before: tokens never go back.

[slide: v-135]
V: If asked, I'd say: I size for the peak. Thirty thousand writes a second against a fifteen thousand ceiling means four groups with headroom. Replicas do not add write throughput. I shed load at the gateway with a retry-after, make clients back off with jitter, and shard by name because locks are independent. A bad shard fails closed for a quarter of the names.
[pause: 1.0]
N: Spreading across groups does not help one name.


## 7.6 Challenge 6: A hot name, several locks

[slide: v-136]
I: One name gets forty attempts a second, and each hold lasts a hundred milliseconds. What happens?
[pause: 2.0]

[slide: v-137]
C: The naive answers: everyone polls until they get it, or we keep a queue that just grows. The pain lands on one box: the leader of the one group that owns this name. Sharding does not help, because one name lives in one group.

[slide: v-138]
C: The arithmetic. A hold of a hundred milliseconds means this name can grant at most ten a second. Forty attempts a second is four times over. If waiters poll every fifty milliseconds, thirty waiters make six hundred polls a second on this one name. Each release wakes all of them and twenty-nine lose: a herd. With an unbounded queue, it grows by thirty a second. After ten seconds a new waiter is three hundred deep and waits about thirty seconds, longer than its own lease. Illustrative numbers, but the shape is real.

[slide: v-139]
C: The fix. The new orange box: a waiter queue per name, with a cap, scoped to sessions so a dead waiter is reaped. A release grants directly to the head waiter in the same committed step. One write, one waiter woken. Beyond the cap, or the wait budget, the answer is contended with a retry-after. Waiting costs no writes. The herd is gone. Every wait is bounded.

[slide: v-140]
C: As a sequence. Waiter one asks and is queued at position one. Waiter two asks and is queued at position two. Holder A releases with token seven. The leader commits, and the same step grants to waiter one, token eight. Waiter two keeps waiting, and if the cap or its maximum wait is exceeded, it gets contended with a retry-after instead of waiting forever.

[slide: v-141]
I: A team now asks to acquire three locks atomically.
[pause: 2.0]

[slide: v-142]
C: First I push back. Acquiring several names atomically across groups is a distributed transaction, and I would not offer it. If it must be done: a canonical order, with the library sorting names and acquiring in that order, so two callers cannot wait on each other in a cycle. Try with a timeout and release everything on failure. And bounded leases mean any deadlock that still happens heals within one lease. Building a wait-for graph to detect cycles is rarely worth it, and saying so is a better answer than describing the algorithm.

[slide: v-143]
C: And an honest limit. A lock serialises. A name can grant at most one over the hold time, and no design makes that bigger. If one name is asked forty times a second, the caller does not want a lock. They want a queue, or a single writer per partition. That is a conversation to have with the team, not a feature to add.

[slide: v-144]
V: If asked, I'd say: a lock serialises. If the name is hot, the lock is the wrong tool. I bound the queue, hand the lock directly to the next waiter so a release is one write, and return an explicit rejection beyond the limit. For several locks I fix the order, bound every wait, and rely on leases so a deadlock heals in one lease. I would not offer atomic multi-lock.
[pause: 1.0]
N: Everything so far assumed we would notice a failure. Would we?


## 7.7 Challenge 7: How would you know?

[slide: v-145]
I: It is three in the morning. A team says duplicates are happening, and your dashboard is green. How would you have known?
[pause: 2.0]

[slide: v-146]
C: The naive answer: watch the service's CPU, memory and uptime. Here is the case. Availability is ninety-nine point nine nine percent, p99 is eight milliseconds. Everything is green. And yet one service has twelve fenced-out rejections a minute, its renewal failures are rising, and on one name the hold time went from half a second to nine. The dashboard watches the machine. The promise is broken somewhere it does not look.

[slide: v-147]
C: So measure the guarantee. Acquire availability and latency, the headline contract. Session-loss rate, because every loss may abort someone's work. Fenced-out writes: alert on any. A fenced-out write means a stale holder reached a resource. It is either the safety net working, or the first symptom of a real problem, and I want to know which. Elections per group per day, under one. Time to a new leader under two seconds. All initial targets.

[slide: v-148]
C: Read metrics in pairs, so each page names a cause. Fenced-out writes rising together with one client's renewal failures: that client is pausing. The safety net worked. Fix the client. Elections rising with acquire p99: an unhealthy group or its disk. Hold-time tail up with waiter depth up: someone is holding a lock across a network call, or it is a hot name. Token gaps growing with attempts: a retry storm. One metric tells you something is wrong. Two tell you where.

[slide: v-149]
C: The fix: a metrics and canary box fed by the groups and the resource checks. A canary lock acquired continuously, so a quiet failure still shows up as a missed acquire. And an offline checker that replays the grant log for overlapping holds. The property: it turns the safety argument into something you can watch.

[slide: v-150]
C: And turn the target into a constraint. Ninety-nine point nine nine percent of a thirty-day month is two hundred and fifty-nine seconds. At about two seconds an election, roughly a hundred and thirty elections a group a month spend all of it. So elections per day is an SLI with a target under one. A constraint like that is what a manager uses to decide what to fix first.

[slide: v-151]
I: Fenced-out is zero this week. Does that mean you are safe?
[pause: 2.0]

[slide: v-152]
C: No. Zero fenced-out writes could just mean nobody is sending tokens. So I track coverage: the share of protected writes that carry a token, and a counter of writes that arrive without one. And a double hold that causes no stale write is invisible to the resource. The log audit finds overlapping holds from the server's durations.
C: The honest limit: you can observe a violation after the fact, and you can alarm on its precursors. You cannot observe an absence of risk.

[slide: v-153]
V: If asked, I'd say: I alert on the guarantee. Any fenced-out write pages someone, because it is either the safety net working or the first sign of a problem. I read metrics in pairs so each page names a cause. I track how many protected writes carry a token at all, and I audit the grant log for overlapping holds. A green dashboard about the service says nothing about the promise.


## 8 Build cost

[slide: v-154]
[pause: 1.0]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round.
C: A distributed lock service is not one project. It is three, and they differ by an order of magnitude.

[slide: v-155]
C: Three releases, called R-zero, R-one and R-two so nobody confuses them with design versions. A prototype to prove the model: about a month. Production in one region for one or two teams: four engineers for five or six months, twenty to twenty-four engineer-months. A company platform: seventy to a hundred and forty. The best question available is: which of these are we actually being asked for, and who is the first customer?

[slide: v-156]
C: R-one, in detail. A tech lead for protocol correctness. A senior and a mid backend engineer. A full-time S-R-E, because half of an infrastructure service is operations. Plus fractions of a manager and a programme manager. Phases: three weeks of discovery, four for a walking skeleton, six for correctness, including a linearizability test harness under injected faults, six for hardening, four for operations, and three for the first customer, in shadow mode and then cutover.
C: One assumption to state: if there is no committed first customer, the right decision is not to build.

[slide: v-157]
C: Ownership. Twenty-four engineer-months to build. Then about one and three-quarter people for five years, which is a hundred and five. A hundred and twenty-nine in total, about eleven engineer-years, and infrastructure is about a tenth of it. All illustrative. People dominate. And infrastructure services do not become free after launch: a service with no owner becomes an incident with no owner.

[slide: v-158]
C: Build, adopt, buy, or don't. Don't: make the resource idempotent or use its conditional write. Two weeks per resource. Check first, every time. Buy a managed transactional store: about four weeks. Adopt a coordination store behind our own A-P-I: about ten weeks. That is my R-one pick. Build a custom service: about a hundred and twenty-nine engineer-months, justified only by a semantic nothing else gives, or very large scale. I would write the buy-versus-build memo before any code, with the first customer's commitment in it. And because the A-P-I is ours from day one, replacing the substrate later is a project, not a migration.

[slide: v-159]
C: What I would never cut: fencing end to end, the conservative client deadline, the linearizability harness, and the runbook with a qualified on-call. What I'd cut first: multi-region, shared modes, first-come fairness, extra-language libraries, the admin console.
C: Top risks. Fencing cannot be enforced at a key resource: descope that caller to an efficiency lock in writing. Adoption fails: a named pilot before any code. Scope creep into a general key-value store, which is what happened to the best-known lock service: written non-goals, with quotas enforced in code. A key person who knows the protocol: pair, write design docs, two people on-call before launch. And a split-brain incident: consensus, fencing, a harness in the pipeline, game days.

[slide: v-160]
C: Staffing. Start small, because design by committee is slow. Grow in the middle where the work parallelises. Do not add people while stabilising. Share the on-call rotation with a sibling team, so four people do not carry a twenty-four-seven pager.
V: The question I ask before saying yes: what happens if two of you hold this at once, and could the operation be made idempotent?
[pause: 1.0]


## 9 Recap

[slide: v-161]
[pause: 1.0]
C: Four minutes to close. One picture, one sentence per path, the mistakes to avoid, and the thesis.

[slide: v-162]
C: The final picture. The library with sessions and a local deadline. The gateway with quotas and the slot map. Four consensus groups with leaders and a waiter queue. The epoch store. Metrics and a canary. And at the resource, the token check, with a proxy where a resource cannot check. Every box on it was added to answer one question the design raised.

[slide: v-163]
C: Five paths, one sentence each. Acquire: one committed write and a token out. Renew: one heartbeat per client, measured from send time. Release and expiry: compare by token, hand off to the head waiter, and a dead session is one command. Fence: the resource rejects anything older than it has seen. Revoke: audited, and the next token is higher.

[slide: v-164]
C: If asked about multi-region. Preferred: region-local lock services over region-owned resources, so there is no cross-region consensus at all. Sparingly: a global lock for rare, coarse locks, accepting the latency. Never: asynchronous replication of lock state. That is split brain with extra steps. A cross-region quorum costs thirty to two hundred and fifty milliseconds, which breaks the twenty-millisecond target.

[slide: v-165]
C: Ten mistakes in this round. In the design: a cache key with an expiry presented as a correctness lock. Tune the lease as the answer to a pause. No token, or a token nobody checks. Timestamps compared across machines. Failing open without saying so.
C: In judgment: a beautiful consensus group and no word about the resource. Never asking whether a lock is needed. Offering atomic multi-lock. Restoring an old snapshot. And hiding the token in a thread-local.

[slide: v-166]
V: The lock service decides who should be working. The resource decides who is allowed to write. Everything I built is there so that those two answers can disagree safely.
[pause: 1.2]
C: Thank you. I'll stop there.
