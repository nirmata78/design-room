# Episode 11 · Distributed consensus for critical state

Reader transcript generated from `src/ch11.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 11 of 16 · Priority 1 — Distributed consensus for critical state   `[th]`
> Why leader election, locks and configuration all reduce to agreement, and what an operator must know to run it.
**COACH:** Episode eleven. This is the most technical episode in the series, and one of the most useful. Its claim is that many problems that look different are one problem: getting several machines to agree. We follow the argument from three failures that agreement would have prevented, through the patterns built on it, then inside Paxos itself, to the operational choices: how many replicas, where, and what to watch.
**SAY THIS:** If two machines can both believe they are in charge, one day they will.
*[pause: 0.8]*


## 11.0 Why this decides interviews

### Slide 2 · The opening story — Case study one: the split brain   `[dia]`
*Diagram:* `svg/e11-split-brain.svg`
**COACH:** Start with a service that stores files on pairs of file servers in different racks. One is the leader, the other a follower, and they must never both accept writes, because that corrupts data. They send each other heartbeats. If the leader goes quiet, the follower takes over, and, to be safe, sends a command to power the old leader off. Now the network gets slow. Heartbeats time out.
**COACH:** Each server decides the other is dead, each sends the power-off command, and some are lost. Both now believe they are the leader, and both accept writes. A mechanism designed to prevent two leaders produced two leaders. It is worth saying plainly: this approach is an industry standard way of reducing split brain, and it is conceptually unsound.

### Slide 3 · What this episode covers — Distributed consensus for reliability   `[panel · note]`
> Managing critical state with distributed consensus. This episode is the operator's view, plus a working tour of the Paxos algorithm. The design-room course parts three and four teach the algorithms and coordination services in full.
**COACH:** This episode covers distributed consensus for reliability. In the design-room course, parts three and four teach the algorithms and the coordination services in depth. This episode is the operator's view: why you need consensus, how Paxos works inside, and what running it is like.


## 11.1 Three failures, one cause

### Slide 4 · Three case studies — Coordination failures   `[cards · c3]`
> red Split brain :: Two nodes both believe they lead. Data corruption, possibly unrecoverable.
> red Failover that needs a human :: The system avoids split brain by stopping and paging a person. Safe, but slow, and humans do not scale.
> red Faulty group membership :: Nodes disagree about who is alive. A node that is wrongly elected accepts writes and deletes it should not.
> > Each is the same problem: deciding one answer that everyone accepts, despite failures.
**COACH:** Three case studies. Split brain: two nodes both believe they lead, and corrupt data. Failover that needs a human: the system avoids split brain by stopping and paging a person, which is safe, but slow, and humans do not scale. And faulty group membership: the nodes disagree about who is alive, and one that is wrongly elected accepts writes it should not. The insight is that all three are the same problem, deciding one answer that everyone accepts, despite failures. It is the consensus problem.

### Slide 5 · The theory the operator needs — Two facts and what they imply   `[table · sm]`
> Fact | Meaning | What you do
> Impossibility: no asynchronous algorithm can guarantee progress with an unreliable network | You cannot have both certainty and guaranteed speed | Aim for progress most of the time, and never give up safety
> Quorum: decisions need a majority | Two majorities of the same group always overlap | One side of a partition can proceed, the other cannot
> > Backoff with randomised delays stops contenders from fighting forever.
**COACH:** Two facts the operator needs. First, the impossibility result: no asynchronous algorithm can guarantee progress when the network is unreliable. In practice that means aim for progress most of the time, with enough healthy replicas and connectivity, but never give up safety. Second, decisions need a majority, called a quorum, and two majorities of the same group always overlap. So in a partition, at most one side can proceed, and the other side must wait. Randomised backoff stops contenders from fighting forever.

### Slide 6 · The line to say — Consensus lets a group of machines agree on one history, even while some of them fail.   `[th]`
**SAY THIS:** Consensus means a group agrees on one ordered history, as long as a majority can talk to each other. Safety never depends on timing. Progress does.
*[pause: 0.8]*


## 11.2 The patterns built on it

### Slide 7 · The core pattern — A replicated state machine   `[dia]`
*Diagram:* `svg/e11-rsm.svg`
**COACH:** The core pattern is the replicated state machine. Several processes execute the same operations in the same order. The consensus algorithm agrees on the sequence, and the state machine on each replica applies the operations in that order. If the program is deterministic, every replica ends in the same state. Any deterministic program can be turned into a highly available service this way.
**COACH:** Clients talk to a leader, which proposes the operation, the replicas record it, and when a majority has, the operation is committed and applied. Everything else in this episode is a use of this.

### Slide 8 · One level down — Five uses of one mechanism   `[table · sm]`
> Pattern | What agrees | Example outcome
> Replicated state machine | The order of commands | A service that survives machine loss
> Replicated datastore or config store | The value of a key, in order | Configuration that every node reads the same way
> Leader election | Who leads, for a term | One primary, and a safe failover
> Locks and leases | Who holds the lock | Mutual exclusion that survives a crash
> Reliable queue | The order of messages | No message lost, none out of order
> > In leader election the consensus step is not on the data path, so it is cheap.
**COACH:** One level down: five uses of the one mechanism. A replicated state machine, where the order of commands is agreed. A replicated datastore or configuration store, where the value of a key is agreed in order. Leader election, where who leads for a term is agreed, giving one primary and a safe failover. Locks and leases, where who holds the lock is agreed. And reliable queues, where the order of messages is agreed. There is a useful note about leader election.
**COACH:** The consensus step is used to choose the leader, and not on the path of every operation, so the cost is small.

### Slide 9 · The trap — A lock is not safe just because it is distributed   `[panel · trap]`
> A client that holds a lock can pause, for garbage collection or a stall, and keep acting after the lock expired.
> The fix is to make the resource check a number that only grows, issued with each grant: a fencing token.
> The design-room course part on coordination covers this. Say it in any answer that involves a lock.
**ASIDE:** A trap that comes up in every lock question. A client that holds a lock can pause, for garbage collection or any other stall, and keep acting after the lock has expired. The fix is to make the resource check a number that only grows, issued with each grant, which is called a fencing token. The design-room course covers it in the part on coordination. Say it in any answer that involves a lock.


## 11.3 Inside Paxos

### Slide 10 · Paxos · The roles — Three jobs, usually played by the same machines   `[cards · c3]`
> Proposer :: Wants a value chosen. Picks a proposal number that is unique and always growing, and drives the two phases.
> Acceptor :: The voter. Keeps three things on disk: the highest number it promised, and the number and value it last accepted.
> Learner :: Finds out what was chosen and applies it. In practice, every replica.
> > Safety needs only the acceptors, on stable storage, and a majority of them alive.
**COACH:** So far this episode has treated consensus as a black box. Now open it. Paxos, from a famous paper of the late nineteen nineties, is the classic algorithm, and many of the systems you will meet descend from it. It has three roles, and one machine usually plays all three. A proposer wants a value chosen, and picks a proposal number that is unique and only ever grows.
**COACH:** An acceptor is a voter. It keeps three things on disk: the highest number it has promised, and the number and value of the last proposal it accepted. A learner finds out what was chosen and applies it. Safety needs only the acceptors, on stable storage, and a majority of them alive.

### Slide 11 · Paxos · One decision — Two phases: ask for a promise, then ask for acceptance   `[dia]`
*Diagram:* `svg/e11-paxos-phases.svg`
**COACH:** Here is one decision, with a proposer and three acceptors. Phase one. The proposer picks number one and sends a prepare message to every acceptor. An acceptor that has not promised anything higher replies with a promise: I will ignore any proposal numbered below one, and the last value I accepted is none. Phase two. The proposer has promises from a majority, so it sends accept, number one, value X.
**COACH:** Each acceptor accepts unless it has since promised a higher number, and tells the proposer. Acceptor three is slow, but two of three is a majority, so the value X is chosen. Notice that choosing it needed no clock, only a majority and a disk.

### Slide 12 · Paxos · The rules — Three rules carry the whole safety argument   `[table · sm]`
> Who | Rule | Why it matters
> Acceptor, on prepare(n) | If n is higher than any promise so far, persist the promise, then reply with the last accepted number and value | Old proposals are fenced out, and the proposer learns what may already be chosen
> Acceptor, on accept(n, v) | Accept, unless it has promised a number higher than n | A proposal that lost the race cannot sneak in
> Proposer, after a majority of promises | Propose the value of the highest-numbered accepted proposal in the replies. Only if there is none, propose your own | A value that may be chosen is never replaced
**COACH:** Three rules carry the whole safety argument. On a prepare with number n, an acceptor that has not promised anything higher writes the promise to disk, then replies with the last proposal it accepted, if any. On an accept, it accepts unless it has promised something higher. And the proposer's rule, the one people forget.
**COACH:** After a majority of promises, it must propose the value from the highest numbered accepted proposal in the replies. Only if every reply is empty may it propose its own value. That rule is the heart of Paxos, because it is what stops a late proposer from overwriting a decision.

### Slide 13 · Paxos · Why a chosen value survives — A later proposer is forced to repeat it   `[dia]`
*Diagram:* `svg/e11-paxos-recovery.svg`
**COACH:** See it work. Later, a second proposer wants value Y, and has no idea that X was chosen. It sends prepare, number two, to acceptors two and three. Acceptor two replies with its promise, and adds: I already accepted number one, value X. Acceptor three has nothing to report. That is a majority, and one reply carries a value, so the proposer must propose X, not Y.
**COACH:** It sends accept, number two, value X, and the decision stays X. Why does this always work? Any two majorities share at least one acceptor, so any later majority of promises must include someone who saw the earlier decision.

### Slide 14 · Paxos · The traps — Where real implementations bite   `[panel · trap]`
> Duelling proposers: two proposers keep raising numbers and invalidating each other's phase one, and nothing is ever chosen. Safety holds, liveness does not. The fix is one stable leader, or randomised backoff.
> Forgetting to persist: an acceptor that replies to a prepare before the promise is on disk, then restarts, can break its own promise. Write first, reply second.
> One run decides one value: a real service needs a sequence of decisions.
> > Safety never depends on timing. Progress does.
**ASIDE:** Where real implementations bite. First, duelling proposers. Two proposers keep raising their numbers and killing each other's phase one, so nothing is ever chosen. Safety still holds, but liveness does not, which is the impossibility result from earlier, seen in practice. The fix is a single stable leader, or randomised backoff. Second, persistence. An acceptor that replies before the promise reaches disk, and then restarts, can break its own promise, so write first and reply second. Third, one run decides one value, and a service needs a sequence of decisions.

### Slide 15 · Paxos · A log of decisions — Multi-Paxos: elect once, then one round trip per slot   `[dia]`
*Diagram:* `svg/e11-paxos-slots.svg`
**COACH:** A real service needs a sequence, which is a replicated log, and that is Multi-Paxos. Each log position is its own Paxos decision, called a slot. Running phase one for every slot would double the cost, so a leader runs phase one once, for all future slots at the same time. Then each command needs only phase two: one round trip to a majority. That is exactly the replicated state machine from the last section. If the leader dies, the new leader runs phase one, learns what any majority has accepted, fills any empty slots with no-ops, and carries on.

### Slide 16 · Paxos · And Raft — The same ideas, packaged to be understood   `[table · sm]`
> Idea | Paxos | Raft
> Who proposes | Any proposer with a higher number | One leader per term, elected by majority vote
> Ordering | Proposal numbers, slot by slot | A single log, with a term and index on every entry
> Gaps in the log | Allowed, and filled with no-ops | Not allowed: the log is contiguous
> Membership change | Not part of the basic protocol | Specified in the paper
> > Different packaging, same two ingredients: majority overlap and promises written to disk.
**COACH:** How does this relate to Raft? Raft was designed to be easier to teach and to implement. It has one leader per term, elected by majority vote. It keeps a single contiguous log with a term and an index on every entry, so there are no gaps to fill. And it specifies how membership changes. Paxos allows any proposer, and leaves membership to the implementer. Under the packaging they share the same two ingredients: majorities always overlap, and a promise is written to disk before anyone relies on it.

### Slide 17 · Paxos · Beyond the paper — Why implementing it is harder than understanding it   `[panel · key]`
> Engineers who built Paxos into a production system reported that the gap between the algorithm and a real system was large: disk corruption, membership changes, snapshots to truncate the log, and leases so a leader can serve reads.
> That is why you operate a consensus library and test it with fault injection, rather than write one.
> > Understand the two phases. Do not write your own.
**COACH:** One last point on why you use a library. The engineers who built Paxos into a real system, in a paper called Paxos Made Live, reported that the gap between the algorithm and the system was large. Disk corruption. Changing the set of replicas. Snapshots to truncate the log. Leases, so that a leader can serve reads safely. So understand the two phases well enough to reason about failures, and then run a battle tested library instead of writing your own.

### Slide 18 · The line to say — Two phases, one rule: promise to ignore the old, and repeat what may already be chosen.   `[th]`
**SAY THIS:** Paxos in one breath. Promise to ignore older proposals, and if anything may already be chosen, repeat it. Everything else is making that survive crashes, and repeating it for every slot.
*[pause: 0.8]*


## 11.4 Performance and deployment

### Slide 19 · The line to say — Commit time is the round trip to the nearest majority.   `[th]`
**SAY THIS:** Commit latency is the round trip to the nearest majority, plus the disk write. Place the replicas with that in mind.
*[pause: 0.8]*

### Slide 20 · Latency — Commit waits for the nearest majority   `[dia]`
*Diagram:* `svg/e11-write-latency.svg`
**COACH:** Now the operator's questions. First, performance. In the common design a leader gets a command, writes it to its own log, sends it to the others, and waits for a majority. So the time to commit is set by the round trip to the nearest majority, plus the cost of writing to disk. Look at the picture, with illustrative numbers. Five replicas in three regions: two in the leader's region, two in a second region thirty milliseconds away, one in a third region eighty away.
**COACH:** The leader needs three of five, so itself, its local peer, and one remote acknowledgement. The nearest remote is thirty milliseconds, so commits cost about thirty. The far region is not on the critical path.

### Slide 21 · One level down — What to know about performance   `[table · sm]`
> Technique | What it does | Cost or condition
> Stable leader | One leader handles many commands without re-electing | Leader failure costs an election
> Batching | Many commands per round trip and per disk write | A little added latency
> Disk behaviour | Each commit must reach stable storage before acknowledging | Disk latency joins the critical path
> Read scaling | Serve reads from followers, or with leases | Reads may lag, or need extra coordination
> > The consensus system's latency is dominated by network round trips and disk writes.
**COACH:** One level down, performance. A stable leader handles many commands without a new election, but its failure costs an election. Batching puts many commands in one round trip and one disk write, at the cost of a little latency. Each commit must reach stable storage before it is acknowledged, so disk latency sits on the critical path. And to scale reads you serve them from followers or with leases, accepting that they may lag, or need extra coordination. In short, latency is dominated by network round trips and disk writes.

### Slide 22 · The line to say — Four is no better than three.   `[th]`
**SAY THIS:** Four replicas tolerate one failure, the same as three. Five tolerate two, which lets you survive a failure during maintenance.
*[pause: 0.8]*

### Slide 23 · Deployment — How many replicas, and where   `[table · sm]`
> Replicas | Majority | Failures tolerated | Note
> 3 | 2 | 1 | The usual minimum for fault tolerance
> 4 | 3 | 1 | No better than 3, and costs more
> 5 | 3 | 2 | Survives one failure during maintenance of another
> 7 | 4 | 3 | Slower commits: more acknowledgements
> > Tolerated failures = floor of (N minus 1) divided by 2. Spread replicas across failure domains; distance buys safety and costs latency.
**COACH:** Deployment. How many replicas? Three replicas need a majority of two, and tolerate one failure. Four need three, and still tolerate only one, so four is no better than three and costs more. Five need three and tolerate two, which means you can survive a failure while another replica is down for maintenance. Seven tolerate three, with slower commits. The rule is the floor of N minus one over two. And where? Spread replicas across failure domains, such as racks, datacenters and regions.
**COACH:** Here is the trade-off: as distance grows, so does the failure you can survive, and also the latency of every operation.

### Slide 24 · The alternative and the price — Consensus or something weaker   `[table · sm]`
> Option | Gives | Gives up
> Consensus group | One agreed order, safe failover | Latency, a quorum to keep, operational care
> Single primary with async replicas | Low latency, simple | Failover can lose acknowledged writes or split the brain
> Leaderless with quorums | High availability, tunable | No single order. Conflicts to resolve
> No coordination | Fastest | Everything that needs agreement is at risk
> > Use consensus for the small amount of state that must be right. Do not put the bulk data through it.
**COACH:** The alternatives and their price. A consensus group gives one agreed order and safe failover, at the cost of latency and the care of keeping a quorum. A single primary with asynchronous replicas is fast and simple, but failover can lose acknowledged writes or split the brain. Leaderless quorums give high availability, with no single order and conflicts to resolve. No coordination is fastest, and leaves everything that needs agreement at risk. The practical rule: use consensus for the small amount of state that must be right, and do not put the bulk data through it.


## 11.5 Operating it

### Slide 25 · The line to say — Consensus for the small state that must be right.   `[th]`
**SAY THIS:** Use consensus for the small state that must be right, such as leaders, locks and metadata. Never put the bulk data through it.
*[pause: 0.8]*

### Slide 26 · Monitoring — What to watch on a consensus system   `[list]`
> ~ The list follows from quorums, stable leaders and disk writes.
> - Number of healthy replicas and whether a quorum exists
> - Is there a leader, and how often does it change
> - Commit latency and the time to apply
> - Replica lag, and disk latency
> - Slow or flapping network links between replicas
**COACH:** What to watch. The number of healthy replicas, and whether a quorum exists. Whether there is a leader, and how often it changes, because frequent changes mean trouble. Commit latency and the time to apply. Replica lag and disk latency. And slow or flapping network links between the replicas. The list follows from what we said about quorums, stable leaders and disk writes.

### Slide 27 · The trap — Losing the quorum without noticing   `[panel · trap]`
> Rolling maintenance that takes down two of three replicas is an outage, even if every step looked safe.
> Plan for one failure plus one maintenance. That is why five is the common choice for the most critical systems.
> Alert on loss of redundancy, not only on loss of service.
**ASIDE:** The trap is losing the quorum without noticing. A rolling maintenance that takes down two of three replicas is an outage, even if each step looked safe. Plan for one failure plus one maintenance, which is why five replicas is a common choice for the most critical systems. And alert on loss of redundancy, not only on loss of service. By the time service is lost, you have no margin left.


## 11.6 Then and now

### Slide 28 · Since 2016 — Consensus became a commodity you run   `[panel · now]`
> Raft is the teachable default, and it sits inside widely used coordination stores and many databases. You are far more likely to operate one than to write one.
> Databases now shard data into many small consensus groups, each with its own leader, and run transactions across them.
> Managed services offer consensus-backed storage, and some use bounded clock uncertainty to give strong guarantees across regions.
> Independent testing of real systems has repeatedly found safety bugs in implementations. Run a fault-injection test before you trust one.
**ASIDE:** What has changed? Consensus became a commodity you run, not a paper you implement. Raft is the teachable default, and it sits inside widely used coordination stores and many databases. You are far more likely to operate one than to write one. Databases now divide data into many small consensus groups, each with its own leader, and run transactions across them. Managed services offer consensus-backed storage, and some use bounded clock uncertainty to give strong guarantees across regions. And independent testing has found safety bugs in implementations again and again, so run a fault injection test before you trust one.


## 11.7 Probe drills

### Slide 29 · Interviewer probe — Why not just use a primary and a hot standby?   `[probe]`
**INTERVIEWER:** Why not just use a primary and a hot standby?
*A strong answer on screen:*
> - A failure detector is not accurate: a slow primary looks dead
> - Promoting while the old primary lives gives two primaries: split brain
> - Consensus makes the decision to promote safe: at most one leader per term
**CANDIDATE:** Because a hot standby relies on a failure detector, and in a network where delay is unbounded, a slow primary looks exactly like a dead one. If the standby promotes itself while the old primary is alive, there are two primaries. Consensus makes the decision to promote safe: a leader is chosen by a majority, for a term, so at most one can win, and the old one finds out when it tries to commit.

### Slide 30 · Interviewer probe — A network partition splits a five-node cluster into two and three. What happens?   `[probe]`
**INTERVIEWER:** A network partition splits a five-node cluster into two and three. What happens?
*A strong answer on screen:*
> - The three side has a quorum: it elects a leader and continues
> - The two side has no quorum: it cannot commit, so it rejects or waits
> - On heal, the two side catches up from the leader
> - Clients on the two side see errors or timeouts: that is the price of safety
**CANDIDATE:** The side with three nodes has a majority, so it elects a leader if needed and keeps going. The side with two cannot reach a majority, so it cannot commit writes, and clients there see errors or timeouts. That is the price of safety, and it is what prevents split brain. When the partition heals, the two nodes catch up from the leader's log.

### Slide 31 · Interviewer probe — You need to replace a dead replica in a three-node group. How, safely?   `[probe]`
**INTERVIEWER:** You need to replace a dead replica in a three-node group. How, safely?
*A strong answer on screen:*
> - Add the new node as a non-voting learner, and let it catch up
> - Then promote it: four voters
> - Then remove the dead one: three voters
> - Never remove first: with two left, one more failure stops the group
**CANDIDATE:** I add the new node as a non-voting learner, so it can catch up from a snapshot and the log without affecting the quorum. When it has caught up, I promote it, which makes four voters. Then I remove the dead one, back to three. The order matters. If I removed first, I would be down to two, and one more failure would stop the whole group.

### Slide 32 · Interviewer probe — Where in your design does consensus not belong?   `[probe]`
**INTERVIEWER:** Where in your design does consensus not belong?
*A strong answer on screen:*
> - On the bulk data path: put the data elsewhere, and keep pointers and metadata under consensus
> - In latency-sensitive paths that do not need agreement
> - Where eventual consistency is acceptable and conflicts are rare
**CANDIDATE:** On the bulk data path. Consensus is expensive in latency and throughput, so I keep it for the small amount of state that must be right, such as who is the leader, where each piece of data lives, and the configuration. The data itself goes to a store designed for bulk. And I would not use it in latency-sensitive paths, or where eventual consistency is acceptable and conflicts are rare.

### Slide 33 · Interviewer probe — Why must an acceptor write its promise to disk before it replies?   `[probe]`
**INTERVIEWER:** Why must an acceptor write its promise to disk before it replies?
*A strong answer on screen:*
> - A promise is a commitment that must survive a restart
> - If it forgets, it can accept an older proposal it had promised to ignore
> - Then two proposers can each believe a different value was chosen: safety is broken
**CANDIDATE:** Because a promise is a commitment, and a commitment that disappears on restart is not one. Suppose the acceptor promises to ignore proposals below five, replies, crashes and restarts having forgotten. It can now accept proposal three. Meanwhile the proposer that got the promise assumed three could no longer win. Two proposers can end up believing different values were chosen, and that is the one thing consensus must never allow. So persist the promise first, and reply second.

### Slide 34 · Interviewer probe — A proposer gets promises from a majority, and one reply carries an accepted value. What may it propose?   `[probe]`
**INTERVIEWER:** A proposer gets promises from a majority, and one reply carries an accepted value. What may it propose?
*A strong answer on screen:*
> - Only the value of the highest-numbered accepted proposal in the replies
> - Its own value only if every reply is empty
> - That rule is what stops a chosen value from ever being replaced
**CANDIDATE:** It must propose the value from the highest numbered accepted proposal among the replies, even though it wanted something else. It may use its own value only if every reply is empty. The reason is that a value that a majority accepted might already be chosen, and any later majority of promises must include at least one acceptor that saw it. Repeating it keeps the decision stable, and the proposer's own value simply loses this round.


## 11.8 Where this shows up

### Slide 35 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 3 teaches consensus, and part 4 teaches coordination services built on it.
> - Episode 12: distributed cron uses a replicated state machine
> - Episode 13: data integrity, where agreement meets storage
> - Google's SRE books: the chapter on distributed consensus, and the Chubby paper
> - Papers: the Raft paper, and "Paxos Made Live"
**COACH:** Next steps. Part three of the design-room course teaches consensus, and part four teaches coordination services built on it. Episode twelve shows distributed cron, which uses a replicated state machine, and episode thirteen is about data integrity. The Chubby paper, the Raft paper and Paxos Made Live are the best companions.

