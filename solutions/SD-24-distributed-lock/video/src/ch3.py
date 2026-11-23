from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before any design, so the design can lean on it. Six parts: what a lock service is and is not, the two properties, the central tension, seven mechanisms, an options matrix, and the failure catalogue. Every slide in this chapter has a theory badge."]); th()

key("Theory · 1 of 6 · what it is", "A small, consensus-replicated store of <em>named leases</em>: one holder at a time, for bounded time, with a number that orders every grant.", [
 "V: A distributed lock service is a small, consensus-replicated store of named leases. It gives one holder at a time permission to act on a name, for a bounded time, together with a number that orders every grant on that name.", "[pause: 1.0]",
 "C: Every clause carries weight. Consensus-replicated, so a failover cannot forget a grant. Named, so locks are independent and can be sharded. Bounded time, because we cannot tell a dead holder from a slow one. And a number that orders, which is the part the resource needs."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Three things it is confused with", '<div class="cards c3">'
  '<div class="cd"><h3>Not a mutex</h3><p>A mutex lives in shared memory and can stop the holder. A distributed lock cannot reach into a paused process.</p></div>'
  '<div class="cd"><h3>Not a queue</h3><p>No payload, no work ordering. “One at a time per entity, in order” wants a single writer per partition.</p></div>'
  '<div class="cd red"><h3>Not a transaction</h3><p>It protects nothing by itself. The resource has to take part.</p></div></div>'), [
 "C: Three neighbours. It is not a mutex. A mutex lives in shared memory and can stop the holder. A distributed lock cannot reach into a paused process and stop it. It is not a queue: there is no payload and no ordering of work. If a team wants one at a time per entity, in order, they want a single writer per partition.",
 "C: And it is not a transaction. It protects nothing on its own. The resource has to take part. Leader election is a use of a lock, not a different thing."], cls="theory")

S(plain("Theory · 2 of 6 · the two properties", "State safety and liveness separately", 
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p>Two parties both act as the holder of a name, and both effects take hold at the resource.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p>A free name is granted. A dead holder\'s name frees within one lease. A waiter is served, or told no, within its wait budget.</p></div>'
  '<div class="whyb"><b class="t">Why separate them</b>A lock service that never grants anything is perfectly safe. One that grants everything immediately is perfectly live. Every fix later says which one it serves.</div>'), [
 "V: Safety: two parties must never both act as the holder, with both effects taking hold at the resource. Liveness: a free name is eventually granted, a dead holder's name is eventually freed, and a waiter is eventually served or told no.", "[pause: 0.8]",
 "C: A service that grants nothing is perfectly safe. A service that grants everything is perfectly live. The engineering is in getting enough of both. From now on, every fix says which property it protects."], cls="theory")

S(plain("Theory · 2 of 6 · honesty about impossibility", "You cannot have both, unconditionally", 
  '<div class="cards c2"><div class="cd"><h3>The result</h3><p>In an asynchronous network, with even one process allowed to fail, no protocol guarantees agreement and always finishes. This is the F-L-P result.</p></div>'
  '<div class="cd amb"><h3>What real systems do</h3><p>Add a timing assumption, such as a failure detector with a timeout. They keep safety unconditional and lose liveness while a partition lasts.</p></div></div>' +
  line("Our position: safety unconditional. The minority side of a partition gets “unavailable”, never a second grant.", "r")), [
 "C: There is a result from the nineteen-eighties, F-L-P. In an asynchronous network, if even one process can fail, no protocol can both always agree and always finish. Real systems add a timing assumption, usually a timeout, and then pick which property to give up.",
 "C: Consensus systems keep safety unconditional and lose liveness during a partition. A group without a majority stops, rather than risk two leaders. That is my position as well, and I'll state it whenever it matters."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "You cannot tell a dead holder from a slow one", "ttl-slider"), [
 "C: Here is the tension everything comes from. When a holder goes quiet, the service cannot tell whether it crashed or is only slow. So the service does not try to detect death. It makes the grant expire.",
 "C: Then the lease length is a trade. A short lease frees a crashed holder's name quickly, but expires slow holders that are still alive. A long lease does the opposite. The default is ten seconds. Our pause is fifteen. And no setting on this line removes the pause. Remember that."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 7", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "A lease with a TTL", "Liveness.", "A grant is valid for a stated time. When it ends, the service may give the name to someone else without asking the holder.",
     "A lock held forever by a dead holder, and manual cleanup.", "A slow holder can be expired while alive. A crash stalls its name for up to one lease.", [
 "C: Mechanism one, the lease. It protects liveness. A grant is valid for a stated time, after which the service may reassign the name without asking. That rules out a lock held forever by a dead holder. It costs two things: a slow holder can lose its lock while alive, and a crash stalls that name for up to one lease."])
mech(2, "A consensus-replicated record", "Safety of the grant record.", "Every grant is a log entry committed by a majority of replicas. One leader per term. A stale leader cannot commit.",
     "Split brain, and a failover that forgets a grant.", "A quorum round trip on every write. No majority, no service. A cluster to run.", [
 "C: Mechanism two, a consensus-replicated record. It protects the safety of the grant record. Every grant is an entry committed by a majority, with one leader per term. A stale leader cannot get a majority, so it cannot commit. That rules out split brain, and a failover that forgets a grant. It costs a quorum round trip on every write, an outage without a majority, and a cluster to run."], )
mech(3, "A fencing token, checked at the resource", "Safety at the resource.", "Each grant carries a number larger than every earlier one for that name. The resource remembers the highest it accepted and rejects anything smaller.",
     "A paused holder's stale write landing after a newer holder's.", "The resource must check. One number per protected row. It orders writes: it does not make a multi-step read consistent by itself.", [
 "C: Mechanism three, the fencing token. This is the one that makes the design safe. Each grant carries a number larger than every earlier grant for that name. The resource remembers the highest number it has accepted and rejects anything smaller. That rules out a paused holder's stale write. It costs one number per protected row, and the resource has to take part. Note the last cost: it orders writes, but it does not by itself make a multi-step read consistent. Challenge one comes back to that."], live=False)
mech(4, "Monotonic clocks, and a conservative client deadline", "Safety of the lease arithmetic.", "Durations are measured on a monotonic clock. The client measures from when it sent the request and gives up at 0.7 of the lease.",
     "Wall-clock steps and skew that make the client believe it holds a lock it lost.", "The client gives up early: 30% of the lease is wasted. It still assumes bounded drift.", [
 "C: Mechanism four, clocks. A wall clock can jump forwards or backwards. A monotonic clock only measures elapsed time on one machine. So the client times its lease from the moment it sent the request, on a monotonic clock, and gives up at seventy percent of the lease. That rules out clock steps and skew. It costs thirty percent of the lease, and it still assumes drift is bounded."], live=False)
mech(5, "Sessions", "Liveness and throughput.", "A client holds one session, kept alive by one heartbeat. Locks hang off the session. When it dies, all its locks are freed in one command.",
     "Per-lock renewal storms, and many separate expiries for one dead client.", "A coarser failure unit: one missed heartbeat drops every lock that client holds.", [
 "C: Mechanism five, sessions. A client keeps one session alive with one heartbeat, and its locks hang off the session. When the session dies, all its locks free in one command. That rules out renewal storms and fifty separate expiries. It costs a coarser failure unit: one missed heartbeat drops every lock the client holds."])
mech(6, "A deterministic replicated state machine", "Safety across replicas.", "Every replica applies the same entries in the same order. The time used is written into the entry by the leader. Expiry is a command, not a background sweep.",
     "Replicas that disagree about who holds a lock, or a follower expiring a lease on its own clock.", "Expiry waits for the leader's timer. A new leader must re-derive pending expiries.", [
 "C: Mechanism six, determinism. Every replica applies the same entries in the same order. If a replica read its own clock while applying, replicas would diverge, and a diverged lock service is an unrecoverable incident. So the leader writes the time into the entry, and expiry is itself a replicated command. It costs a little delay on expiry, and a new leader must work out which expiries are pending."], live=False)
mech(7, "Bounded wait with directed hand-off", "Liveness under contention.", "Waiters queue per name, with a depth cap and a wait budget. Release grants to the head waiter in the same step.",
     "A thundering herd on release, an unbounded queue, and polling that burns consensus.", "Queue state in the replicated machine. First-come order adds tail latency.", [
 "C: Mechanism seven, bounded wait with directed hand-off. Waiters queue per name with a cap. A release grants directly to the head of the queue in the same committed step. That rules out the herd, the unbounded queue, and polling. It costs queue state in the replicated machine, and first-come ordering adds some tail latency."])

S(plain("Theory · 5 of 6 · the options, part one", "Three ways that look cheap", table(["Approach", "Safe without fencing?", "Token", "Fails when"], [
  ("rej", ["A · One cache node, set-if-absent with an expiry", "no", "bolt-on counter, not atomic with the grant", "the primary dies before replicating the grant; the new primary grants it again"]),
  ("rej", ["B · A quorum of independent cache nodes", "disputed", "none", "a pause between acquire and use; a node's clock jumps and its key expires early; no token to reject a stale holder"]),
  ("rej", ["C · A relational row: conditional update or row lock", "yes, with synchronous commit", "a version column", "above a few thousand grants a second, or on a hot row; a row lock tied to a connection has no lease"])], "bt sm mx")), [
 "C: Now the options. Six approaches, each with the failure that rules it out. Three that look cheap first.",
 "C: A, one cache node with set-if-absent and an expiry. Replication is asynchronous, so the primary can acknowledge a grant and die before the copy arrives. The new primary has no record and grants it again. Fine for an efficiency lock. Never claim it as a correctness lock.",
 "C: B, a quorum of independent cache nodes. It tries to fix that, but its safety rests on timing: a pause between acquiring and using, or one node's clock jumping, breaks it. And it issues no token. It is a well known debate, and I know it, but I would not propose it for correctness.",
 "C: C, a relational row. Underrated. With synchronous commit it is safe, and a version column is a token. It fails above a few thousand grants a second, or on a hot row. And a plain row lock is tied to a connection, so it has no lease. If the protected resource is in that same database, the lock and the work commit together, and the whole problem mostly disappears."], cls="theory")

S(plain("Theory · 5 of 6 · the options matrix", "Six approaches, one pick", table(["Approach", "Safe w/o fencing?", "Token", "Throughput", "Ops", "Fails when"], [
  ("rej", ["A · One cache node", "no", "bolt-on", "very high", "very low", "primary dies before replicating"]),
  ("rej", ["B · Quorum of caches", "disputed", "none", "high", "medium", "pause, clock jump, no token"]),
  ("rej", ["C · Relational row", "yes (sync)", "version", "low to medium", "very low", "over a few thousand grants/s, hot row"]),
  ("pick", ["D · Consensus coordination store: lease + compare-and-set + revision", "yes", "store revision", "10–30k writes/s a cluster", "medium", "load beyond a cluster; exotic semantics"]),
  ("rej", ["E · Custom consensus service", "yes", "log index", "high, sharded", "very high", "you cannot staff it"]),
  ("rej", ["F · No lock: conditional write or idempotency key", "yes, at the resource", "the resource's version", "n/a", "lowest", "non-idempotent and no conditional write"])], "bt sm mx")), [
 "C: Here are all six. D is a consensus-backed coordination store, the ZooKeeper, etcd or Consul family. It has leases, compare-and-set, and a revision number that is a ready-made token. It fails when load exceeds one cluster, and then I shard. Or when I need semantics it cannot express.",
 "C: E, building my own consensus service, has the same safety and gives me full control, and it is far more expensive to run. It fails if I cannot staff it. F is no lock at all: a conditional write or an idempotency key at the resource. It fails when the operation is not idempotent and the resource has no conditional write.",
 "V: I pick D, after asking whether F applies.", "[pause: 0.8]"], cls="theory")

S(plain("Theory · 5 of 6 · the pick, and what it gives up", "D, behind our own API", '<div class="cards c2">'
  '<div class="cd grn"><h3>What the pick buys</h3><p>Safety proven by someone else\'s consensus. Leases and a revision number built in. One place to enforce rules, behind our A-P-I and S-D-K, so we can swap the substrate later.</p></div>'
  '<div class="cd red"><h3>What it gives up</h3><p>One cluster\'s write ceiling, so we shard. Fairness, priority and shared modes. Cross-region reach. And the operating burden of a consensus cluster.</p></div></div>' +
  line("Always ask first: does the resource support a conditional write? If it does, that is row F, and it is cheaper.", "a")), [
 "C: What the pick gives up, said plainly. One cluster's write ceiling, so I'll shard in challenge five. Fairness, priority and shared modes, which that store does not express. Cross-region reach. And the burden of running a consensus cluster, which is real.",
 "C: What it buys: safety proven by someone else's consensus, leases and a revision number built in, and, behind my own A-P-I and S-D-K, the ability to swap the substrate later if evidence says I should. And before any of it, I always ask whether row F applies."], cls="theory")

S(plain("Theory · 5 of 6 · a probe you may get", "“Why not SELECT FOR UPDATE on a Postgres row?”", '<div class="cards c3">'
  '<div class="cd amb"><h3>No lease</h3><p>A row lock lives as long as the connection. A paused client keeps it. A dead one drops it only when the database notices.</p></div>'
  '<div class="cd amb"><h3>No token</h3><p>A held lock hands out no number the resource can check later.</p></div>'
  '<div class="cd grn"><h3>When it is right</h3><p>The resource is in the same database, so lock and work commit together. Or load is under a few thousand a second.</p></div></div>'), [
 "C: If asked why not a row lock in a relational database. No lease: the lock lives as long as the connection, so a paused client keeps it. No token: nothing the resource can check later. It is the right answer when the resource lives in the same database, so the lock and the work commit together, or when the load is under a few thousand a second. Saying that is a better answer than reaching for a consensus cluster by reflex."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue, part one", "What will go wrong", table(["#", "Failure", "Becomes"], [
  ["F1", "A holder crashes", "the lease (M1). Covered in the flows"],
  ["F2", "A holder pauses, then resumes", "<b>Challenge 1</b>"],
  ["F3", "The resource cannot check tokens, or no lock is needed", "<b>Challenge 2</b>"],
  ["F4", "Clocks skew, jump or drift", "<b>Challenge 3</b>"],
  ["F5", "Leader fails, partition, whole group lost", "<b>Challenge 4</b>"]], "bt sm")), [
 "C: Last part. The failure catalogue, which becomes the challenge list. F-one, a holder crashes. The lease handles that, and the flows show it. F-two, a holder pauses and resumes: challenge one. F-three, the resource cannot check a token, or no lock is needed at all: challenge two. F-four, clocks: challenge three. F-five, the leader fails, a partition, or the whole group is lost: challenge four."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue, part two", "What will go wrong, continued", table(["#", "Failure", "Becomes"], [
  ["F6", "Duplicate acquire, stale release, delayed message", "designed out in the A-P-I: release takes the token; acquire carries a request id"],
  ["F7", "A load peak, renewal storm, retry storm", "<b>Challenge 5</b>"],
  ["F8", "A hot name, a herd, several locks at once", "<b>Challenge 6</b>"],
  ["F9", "A holder hung but alive", "bounded lease, and force revoke (FR5)"],
  ["F10", "Nobody notices", "<b>Challenge 7</b>"]], "bt sm")), [
 "C: F-six, duplicates, stale releases and delayed messages. I design those out in the A-P-I, so they are not a challenge: release takes the token, and acquire carries a request id. F-seven, a load peak: challenge five. F-eight, a hot name, a herd or several locks: challenge six. F-nine, a holder that is hung but alive: bounded leases and force revoke. And F-ten, nobody notices: challenge seven. Seven challenges, in that order."], cls="theory")

S(plain("Theory · what each mechanism serves", "Safety or liveness, never both unnamed", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 Lease", "liveness", "flows, challenge 3"],
  ["M2 Consensus record", "safety", "challenge 4"],
  ["M3 Fencing token", "<b>safety, at the resource</b>", "challenges 1 and 2"],
  ["M4 Monotonic clocks", "safety of the lease arithmetic", "challenge 3"],
  ["M5 Sessions", "liveness, throughput", "challenge 5"],
  ["M6 Deterministic machine", "safety across replicas", "challenges 3 and 4"],
  ["M7 Hand-off queue", "liveness under contention", "challenge 6"]], "bt sm") +
  grade("Every mechanism must name the property it protects. A mechanism with no stated property is decoration.")), [
 "N: Good theory has a consequence for the design. Look at this table: every mechanism names the property it serves, and where it will be used.",
 "C: That is the vocabulary. On to the design."], cls="theory")
