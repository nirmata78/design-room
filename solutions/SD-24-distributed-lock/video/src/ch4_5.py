from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract first. It forces the semantics into the open.", [
 "C: The A-P-I before the boxes. It is the contract, and it shows whether I've thought about failure. Every call carries a tag: which requirement it serves, and which entity it reads or writes."])

def wire(l, r): return f'<div class="cols2"><pre class="wire">{l}</pre><pre class="wire">{r}</pre></div>'

S(plain("API · sessions", "OpenSession and Heartbeat", tr(("fr", "serves FR2"), ("api", "OpenSession · Heartbeat"), ("ent", "writes Session"), ("nfr", "lease ≤ 60 s")) +
  wire('<span class="cm">// request</span>\nOpenSession {\n  owner: "billing-worker-7",\n  ttlMs: 10000\n}\n\n<span class="cm">// heartbeat, a stream, every ~3.3 s</span>\nHeartbeat { sessionId: 88123 }',
       '<span class="cm">// response</span>\nOpenSession -> {\n  sessionId: 88123,\n  epoch: 6,\n  serverTimeMs: 1731400000000   <span class="cm">// logging only</span>\n}\n\nHeartbeat -> { ok: true }\n<span class="cm">// the client trusts nothing but "ok"</span>')), [
 "C: Session calls. OpenSession takes an owner name and a lease length, capped at sixty seconds, and returns a session id and the current epoch. It serves requirement two and writes a session entity.",
 "C: Heartbeat is a stream, about every three point three seconds. The response has no timestamp that matters. The server time is for logs only. The client trusts nothing in the reply except that it was acknowledged, and measures its own deadline from when it sent the beat."])

S(plain("API · acquire", "Acquire returns a token or an honest no", tr(("fr", "serves FR1, FR4"), ("api", "Acquire"), ("ent", "writes Lock · Waiter"), ("nfr", "bounded wait")) +
  wire('<span class="cm">// request</span>\nAcquire {\n  name: "invoice:17",\n  sessionId: 88123,\n  requestId: "9f1c…",   <span class="cm">// retries are idempotent</span>\n  maxWaitMs: 2000      <span class="cm">// 0 = try once</span>\n}',
       '<span class="cm">// responses</span>\ngranted   { token: 9001, ttlMs: 10000 }\nqueued    { position: 2 }\ntimeout   { }\ncontended { retryAfterMs: 200 }\n\n<span class="cm">// a duplicate requestId returns\n// the SAME token, never a new one</span>')), [
 "C: Acquire. The name, the session, a request id, and a maximum wait. A wait of zero means try once. There is no way to wait forever, on purpose.",
 "C: Four answers: granted with a token and a lease, queued with a position, timed out, or contended with a retry-after. The request id makes a retry safe. If the network duplicates the request, the service returns the same token and not a second one. That is how failure six, duplicates, is designed out."])

S(plain("API · release", "Release takes the token, not the name", tr(("fr", "serves FR3"), ("api", "Release"), ("ent", "writes Lock")) +
  wire('<span class="cm">// request</span>\nRelease {\n  name: "invoice:17",\n  token: 9001\n}',
       '<span class="cm">// apply, inside the state machine</span>\nif held[name].token == token:\n    free it, hand off to head waiter\nelse:\n    reject   <span class="cm">// someone else holds it now</span>') +
  line("Releasing someone else's lock cannot even be expressed. Failure six is designed out, not guarded against.")), [
 "C: Release takes the token, not just the name. If the token matches the current holder, the name is freed and handed to the head waiter. If it does not, the call is rejected, because someone else holds it now.",
 "C: Think about what that removes. A holder whose lease expired, then wakes and calls release, cannot free the new holder's lock. That failure is not guarded against. It cannot be expressed."])

S(plain("API · operators", "Inspect, and break glass", tr(("fr", "serves FR5"), ("api", "Inspect · ForceRevoke"), ("ent", "reads Lock · writes Audit")) +
  wire('<span class="cm">// never used for correctness</span>\nInspect { name: "invoice:17" } ->\n  { owner, token: 9001,\n    acquiredAt, expiresAt,\n    waiters: 2 }',
       '<span class="cm">// audited, alerting, awkward on purpose</span>\nForceRevoke {\n  name: "invoice:17",\n  reason: "holder hung, ticket 4411",\n  operator: "alice"\n}')), [
 "C: Two operator calls. Inspect shows who holds a name. It is documented as never to be used for a correctness decision, because the answer can be stale by the time you read it.",
 "C: ForceRevoke is the break-glass call. Every lock service eventually needs one, usually at three in the morning. I'm designing it in now: it takes a reason and an operator, writes an audit entry, and alerts. The next grant gets a higher token, so the revoked holder is fenced like any other."])

S(plain("API · the resource's side of the contract", "The resource must take the token", tr(("fr", "serves FR4"), ("api", "Write(..., token)"), ("ent", "writes the resource row"), ("nfr", "reject if smaller")) +
  '<pre class="code"><span class="cm">-- reject if the token is SMALLER than the highest accepted. Equal is allowed.</span>\n'
  '<span class="kw">UPDATE</span> invoice\n   <span class="kw">SET</span> amount = :amount, fence = :token\n <span class="kw">WHERE</span> id = :id <span class="kw">AND</span> fence &lt;= :token;\n'
  '<span class="cm">-- 0 rows updated: FencedOut. Log both tokens. Alert.</span></pre>' +
  line("Pass the token as an explicit argument. Never in a thread-local: it is lost silently when work moves threads.", "r")), [
 "C: This is not our A-P-I, but it is part of the contract, and I'll say it every time. Every write to a protected resource carries the token, and the resource rejects it if the token is smaller than the highest it has accepted. Here that is one conditional update.",
 "C: Precision: equal is allowed. The same holder may write several times with the same token. Only smaller is rejected. And pass the token as an explicit argument. If it hides in a thread-local, it is lost the first time work moves to another thread pool, and silently."])

S(plain("API · a question to dismiss aloud", "Reentrancy", '<div class="cards c2"><div class="cd amb"><h3>The question</h3><p>Can a holder acquire a lock it already holds?</p></div>'
  '<div class="cd grn"><h3>My answer</h3><p>Yes, as a hold count in the S-D-K, keyed by session. The server keeps one grant per name. Doing it server-side doubles writes for no gain.</p></div></div>' +
  line("Scope it to a session, not a process, or a reconnecting client deadlocks against its own stale grant.", "a")), [
 "C: Reentrancy comes up, so I'll dismiss it aloud. Yes, a holder may acquire a lock it already holds. I'd do it as a hold count in the client library, keyed by session. The server keeps one grant per name. Doing it on the server would double the writes for nothing. One subtlety: scope it to the session, not the process, or a client that reconnects with a new session deadlocks against its own old grant."])

S(dia("Data · conceptual model", "Entities and relationships, in Chen notation", "erd-chen"), [
 "C: The conceptual model. A tenant owns lock names. A session holds names, and the relationship carries the token and the expiry. A session waits for names, with a position. A lock name protects resource rows, and a row stores the highest token it has accepted, a derived attribute. And an audit event is a weak entity: it only exists in the context of a lock name.",
 "C: One cardinality matters most: a name has at most one holder at a time. That one fact is why locks are independent per name, and so why this shards."], cls="dia")

S(dia("Data · physical model", "What is stored, and where", "erd-physical"), [
 "C: Physically. The held table is keyed by name, with owner, session, token and an expiry that is in log time, not wall time. The waiter table is keyed by name and a sequence, capped in depth. The session table holds the lease and its names. The last heartbeat is volatile, not in the log.",
 "C: Two things live outside the group. The epoch and a token floor per slot, durable, which challenge four and five use. And at the resource, the protected row carries a fence column. Everything in a group is keyed by name, and a name lives in exactly one group, so there are no cross-group transactions."], cls="dia")

S(plain("Data · the state machine", "Apply is deterministic", 
  '<pre class="code"><span class="cm">// runs on every replica, in log order</span>\n<span class="kw">apply</span>(Acquire a, index, timeFromEntry):\n  cur = held[a.name]\n  <span class="cm">// same owner retrying: return the same grant</span>\n  <span class="kw">if</span> cur live <span class="kw">and</span> cur.owner == a.owner: <span class="kw">return</span> cur\n  <span class="kw">if</span> cur live: enqueue(a); <span class="kw">return</span> queued\n  <span class="cm">// token is the log index: monotonic, free</span>\n  held[a.name] = {a.owner, token: index,\n                  expires: timeFromEntry + a.ttl}\n  <span class="kw">return</span> granted(index)</pre>' +
  grade("Naming this unprompted is a depth signal: never read the clock inside apply. The leader stamps the time into the entry.")), [
 "C: The state machine is small enough to read whole. Apply runs on every replica, in log order. If the same owner retries, it returns the same grant. If the name is held, it enqueues. Otherwise it grants, and the token is the log index of this very entry. Monotonic, and free.",
 "C: Look at the time. It is not read from a clock here. It is a field in the entry, stamped by the leader before replication. If each replica read its own clock, two replicas could disagree about whether a lease expired, and the group would diverge. That is the most common bug in home-built replicated state machines."])

S(dia("Data · the token", "A token is a number: epoch and index", "token-bits"), [
 "C: The token itself. Sixty-four bits. Sixteen for an epoch, forty-eight for the log index within a group. Compared as a number, so a bigger epoch always wins. The epoch changes only on a rebuild or a slot move, which is what makes tokens survive a disaster, in challenge four.",
 "C: A timestamp is not a valid token, because clocks go backwards. A random identifier is not either, because it has no order."], cls="dia")

S(plain("Data · which stores, and can you lose them", "Four stores, four answers", table(["Store", "Holds", "If lost"], [
  ["Replicated log + snapshot", "grants, sessions, queues", "survives a minority loss. Total loss: start empty (challenge 4)"],
  ["Leader memory", "last heartbeat per session", "a new leader treats all sessions as alive for one lease"],
  ["Epoch store", "epoch and slot floors", "<b>must not be lost</b>: tokens would go backwards"],
  ["The resource", "highest token per row", "its own durability. The check is only as good as its store"]], "bt sm")), [
 "C: Four stores, and for each: can I lose it? The replicated log survives losing a minority. Losing all of it means starting empty. Leader memory holds heartbeat times. Losing it is harmless: a new leader treats every session as alive for one lease.",
 "C: The epoch store must not be lost, or tokens could go backwards. And the resource's own durability matters too: the token check is only as good as the store that keeps the highest token."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Simple first. Each version answers the objection to the one before.", [
 "C: Three versions. Each one is introduced by the objection it answers. The system stays on screen from here, and later pictures are views of it. Boxes never move."])

S(dia("High-level design · version 1 of 3", "The simplest thing that works", "base-v1", vtag="V1",
      chip=chips("one server", "a map of name to owner and expiry", "a lease, so a dead holder frees its name")), [
 "C: Version one. An app with a lock library, and one lock server. The server keeps a map from name to owner and expiry in memory. Acquire checks the map. A lease means a dead holder's name frees itself. The app also writes to its resource, drawn on top. No objection yet. It is the simplest thing that works, and for an efficiency lock it might be enough."], cls="dia")

S(plain("V1 · the objection", "The server restarts, and forgets who holds what", trace("", "", "").replace('<div class="k"></div><h1 class="q"></h1>', "") if False else
  '<pre class="trace"><span class="t">t = 0 s    </span>A acquires invoice-17 (lease 10 s)\n<span class="t">t = 4 s    </span><span class="bad">lock server crashes, memory lost</span>\n<span class="t">t = 5 s    </span>server restarts, map is empty\n<span class="t">t = 6 s    </span>B acquires invoice-17: <span class="bad">granted</span>\n<span class="t">t = 7 s    </span>A is still working. <span class="bad">Two holders.</span></pre>' +
  '<div class="hedge"><b class="t">Also</b>One box is a single point of failure for every team that uses it.</div>', red=True), [
 "C: The objection. The server restarts, and forgets who holds what. A holds a lock. The server crashes at four seconds and restarts at five with an empty map. B asks, and is granted the same name. A is still working. Two holders, and the lock service caused it. And one box is a single point of failure for every team."], cls="")

S(dia("High-level design · version 2 of 3", "Replace the box with a consensus group", "base-v2", vtag="V2",
      chip=chips("5 replicas", "majority commit", "token = log index")), [
 "C: Version two answers that. The single server becomes a consensus group of five replicas: one leader and four followers. Every grant is a log entry, and it counts only once a majority of replicas have it. If the leader dies, a follower that has the committed entries takes over, so no grant is forgotten.",
 "C: And the token falls out of this for free. It is the log index of the grant entry. Increasing by construction, with no extra machinery."], cls="dia")

S(plain("V2 · how the group works, in one slide", "Leader, term, majority", '<div class="cards c3">'
  '<div class="cd"><h3>One leader per term</h3><p>All writes go to the leader. A new election starts a higher term. A node with an old term is ignored.</p></div>'
  '<div class="cd grn"><h3>Commit = majority</h3><p>3 of 5 replicas hold the entry. Any later leader must have been among them, so it has the entry.</p></div>'
  '<div class="cd red"><h3>No majority, no service</h3><p>With 2 of 5, nothing commits. Safety is kept. Availability is not.</p></div></div>'), [
 "C: The group in one slide. One leader per term. All writes go to it. A node that sees a higher term obeys it. An entry commits when three of five replicas hold it, and any future leader must have been in that three, so it has the entry. And with only two of five reachable, nothing commits. Safety is kept, and availability is given up. That is the trade I chose in the theory."])

S(plain("V2 · the objection", "Nobody is told when the lock is lost", '<div class="cards c2">'
  '<div class="cd red"><h3>The caller cannot tell</h3><p>A holder that loses its lease keeps working. Nothing tells it to stop.</p></div>'
  '<div class="cd amb"><h3>Renewal is hand-rolled</h3><p>Every team writes its own heartbeat, clock arithmetic and retries, and gets it subtly wrong.</p></div></div>' +
  line("Half the correctness lives in the client library. So the library is part of the product.", "a")), [
 "C: The objection to version two. The consensus group is right, but the caller still cannot tell when it has lost the lock. A holder whose lease expired keeps working. And every team would write its own heartbeat, its own clock arithmetic and its own retries, and each would get it subtly wrong. Half the correctness lives in the client library, so the library is part of the product."])

S(dia("High-level design · version 3 of 3", "A client library with sessions, and a gateway", "base-v3", vtag="V3",
      chip=chips("sessions", "monotonic local deadline", "LockLost callback")), [
 "C: Version three. The lock library holds one session, with one heartbeat, the dashed purple arrow. It tracks a local deadline on a monotonic clock, and calls back with LockLost the moment the deadline passes, so application code can stop. A stateless gateway sits in front: it authenticates, applies tenant quotas, and routes to the group's leader.",
 "C: The token comes back in the grant, and the app passes it to the resource, the grey box on top. This is the baseline. It stays on screen from here, and every later picture is a view of it."], cls="dia")

S(plain("V3 · what the library does", "Lease timing in eight lines", 
  '<pre class="code"><span class="cm">// every ~3.3 s, on a background thread</span>\nsentAt = monotonicNow()\n<span class="kw">try</span> { heartbeat(sessionId)\n       <span class="cm">// measured from SEND time: the conservative choice</span>\n       deadline = sentAt + 0.7 * ttl }\n<span class="kw">catch</span> (e) {\n  <span class="kw">if</span> (monotonicNow() &gt; deadline) loseAllLocks(e)  <span class="cm">// fail closed</span>\n}</pre>' +
  line("Check-still-held narrows the window. It does not close it. The token does.", "r")), [
 "C: The library's heartbeat is short. Note the time before sending, on a monotonic clock. If the beat succeeds, move the deadline to that send time plus seventy percent of the lease. If it fails and the deadline has passed, drop every lock, loudly. Failing closed.",
 "C: A warning I'll repeat. A check-still-held call before a write narrows the window, and does not close it. Between the check and the write the lease can still expire. That is the next problem."])

S(plain("V3 · what it leaves open", "Nothing checks the token", '<div class="cards c2">'
  '<div class="cd red"><h3>What V3 has</h3><p>A correct grant record. A library that stops when it loses the lease. A token handed to the caller.</p></div>'
  '<div class="cd red"><h3>What V3 lacks</h3><p>The resource accepts any write. A paused holder that wakes up after the lease expired still writes.</p></div></div>' +
  line("Safety is not here yet. That is challenge one.", "r")), [
 "C: What version three leaves open. It has a correct record, a library that stops on loss, and a token in the caller's hand. What it lacks: the resource accepts any write. A paused holder that wakes after its lease expired still writes. Safety is not here yet. That is challenge one, and I'll get there after the flows."])

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "acquire", "FR1: one acquire, in four numbered steps", "flow-fr1",
     [("fr", "serves FR1, FR4"), ("api", "Acquire"), ("ent", "writes Lock"), ("nfr", "p99 < 20 ms")], [
 "C: Requirement one, acquire. Step one: the library sends Acquire with the name and a request id. Step two: the gateway authenticates, checks the tenant's quota, hashes the name to a slot and routes to that group's leader.",
 "C: Inside the box, which the next sequence shows: the leader appends the entry, a majority acknowledges, it commits, and apply grants with the log index as the token. Step three: the token and lease come back to the gateway. Step four: back to the library, which sets its deadline from when it sent the request."])
flow(2, "hold and renew", "FR2: one heartbeat keeps every lock alive", "flow-fr2",
     [("fr", "serves FR2"), ("api", "Heartbeat"), ("ent", "touches Session"), ("nfr", "every ~3.3 s")], [
 "C: Requirement two. Step one: a heartbeat, dashed purple because it is asynchronous, goes from the library to the gateway. Step two: the gateway passes it to the leader as a session-alive note.",
 "C: The leader keeps liveness in memory under its own leader lease, so a heartbeat is not a consensus write. Only an actual expiry becomes a log entry. When the beat is acknowledged, the library moves its deadline from the time it sent it."])
flow(3, "release and expiry", "FR3: release by token, or expire by silence", "flow-fr3",
     [("fr", "serves FR3"), ("api", "Release"), ("ent", "writes Lock"), ("nfr", "hand-off in one step")], [
 "C: Requirement three, release. The same four arrows. One: Release with the name and the token. Two: routed to the leader. The leader commits, and apply compares the token, frees the name, and hands it to the head waiter in the same step. Three and four: the answer comes back.",
 "C: A dead holder uses no arrow at all. Its heartbeats stop. After one lease the leader proposes a single session-expired command, and every name that session held is freed at once."])
flow(4, "fence", "FR4: the write carries the token, and the resource compares", "flow-fr4",
     [("fr", "serves FR4"), ("api", "Write(..., token)"), ("ent", "writes the resource row"), ("nfr", "reject if smaller")], [
 "C: Requirement four, the most important arrow. Step one: the application writes to the resource over the top path, with the token. Step two: the resource compares it with the highest token it has stored for that row. Not smaller: accept, and store it. Smaller: reject with FencedOut, log both tokens, and alert.",
 "C: This arrow does not touch the lock service at all. That is the point. The lock service issued an order. The resource enforces it."])
flow(5, "inspect and revoke", "FR5: an operator breaks glass, audited", "flow-fr5",
     [("fr", "serves FR5"), ("api", "ForceRevoke"), ("ent", "writes Lock · Audit"), ("nfr", "alerts")], [
 "C: Requirement five. Step one: the operator console calls ForceRevoke with a reason. Step two: the gateway checks the operator's identity and routes to the leader. The leader commits a revoke entry and an audit entry. Step three: the answer returns.",
 "C: The old holder learns on its next heartbeat. And even if it does not, its next write is fenced, because the next grant gets a higher token."])

S(dia("Design · C4 level 1", "The system in its context", "c4-context"), [
 "C: The C4 context. Application teams use the lock service and write to their own resources, with the token. Operators inspect and break glass. The lock service reports metrics to an observability platform. Notice the arrow from the application team straight to the protected resources, not through the lock service. That is deliberate."], cls="dia")
S(dia("Design · C4 level 2", "The containers", "c4-containers"), [
 "C: The containers. Inside the lock service boundary: the lock library, which runs inside the application, the gateway, the consensus groups, four of them, an epoch store, and an operator console. The application calls the library in process. The library talks g-R-P-C to the gateway, which proposes to the group leader. The group reads and bumps the epoch only on a rebuild. And the application writes to the resource directly, with the token."], cls="dia")
S(dia("Design · sequence · acquire", "Acquire, message by message", "seq-acquire"), [
 "C: Acquire as a sequence. One: the library sends Acquire. Two: the gateway routes by hash of the name to the leader. Three: the leader appends the entry to the followers. Four: they acknowledge, and a majority makes the entry commit. Then apply: the name is free, so grant, token equals the log index, say nine thousand and one. Back to the gateway, and to the library, which sets its deadline from its send time."], cls="dia")
S(dia("Design · sequence · losing the lease", "Heartbeat, silence, LockLost, expiry", "seq-heartbeat-loss"), [
 "C: The loss path. One: heartbeat. The ack moves the deadline. Then the network drops. No reply, and no beat reaches the leader. Two: at the deadline, seven seconds after the last send, the library tells the application LockLost, and the application stops before its next side effect. Three: later, the leader sees no beat for a full lease and proposes SessionExpired. Four: that commit frees the names, and the head waiter is granted, with a higher token. The client stopped first, by design."], cls="dia")
S(dia("Design · sequence · release", "Release with a direct hand-off", "seq-release-handoff"), [
 "C: Release. One: holder A releases with token forty-one. Two: the leader commits, and apply sees the token matches, so it frees the name. Three, in the same step: the head of the queue is B, so grant, token forty-two. Four: A gets its answer. Five: B is told it was granted. One committed write, one waiter woken, no polling."], cls="dia")
S(dia("Design · sequence · the resource check", "Accept, and reject", "seq-fence-write"), [
 "C: The check at the resource. The current holder writes with token forty-two. The stored maximum is forty-one, forty-two is not smaller, so accept and store forty-two. Later a stale holder writes with forty-one. The stored maximum is forty-two. Forty-one is smaller, so reject, log both tokens, and alert."], cls="dia")
S(plain("Design · what correct caller code looks like", "The whole pattern, from the caller's side", 
  '<pre class="code"><span class="kw">try</span> {\n  g = session.acquire(<span class="str">"invoice:"</span> + id, ttl, maxWait: 2s)   <span class="cm">// bounded</span>\n  <span class="kw">if</span> (g.empty) <span class="kw">return</span> retryLater()                  <span class="cm">// no side effect</span>\n  <span class="kw">var</span> inv = repo.load(id)\n  session.checkStillHeld(g)                    <span class="cm">// narrows the window</span>\n  payments.execute(inv, g.token)               <span class="cm">// the token makes it safe</span>\n  repo.markPaid(id, g.token)                   <span class="cm">// both resources check</span>\n  session.release(g)\n} <span class="kw">catch</span> (LockLost e) { <span class="kw">return</span> abortedSafely() }  <span class="cm">// never "continue anyway"</span></pre>'), [
 "C: Last in the design, what a correct caller looks like. The wait is bounded. If the lock is not granted, no side effect happens. The check-still-held call narrows the window. Then the token goes to both protected resources, the payment call and the database write, because both must check. And a LockLost exception aborts safely. It never continues anyway."])
S(plain("Design · mechanism before brand", "What the pick must provide", table(["Needed", "Why", "A consensus coordination store gives"], [
  ["Leases that expire", "liveness", "lease grant and keep-alive"],
  ["Atomic compare-and-set", "one grant at a time", "a transaction with an if-absent condition"],
  ["A monotonic number per change", "the token", "the key's revision"],
  ["Ordered, resumable watches", "waiters wake in order", "watch from a revision"]], "bt sm") + line("Mechanism first, product second. If the store lacks one of these four, it is the wrong store.", "a")), [
 "C: Mechanism before brand. What must the substrate give me? Leases that expire. An atomic compare-and-set. A monotonic number per change, my token. And ordered, resumable watches so waiters wake in order. A coordination store in the ZooKeeper or etcd family has all four. If the store I'm offered lacks one of them, it is the wrong store."])
