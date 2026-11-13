---
title: System design · building blocks and concepts
subtitle: Written companion to the 17-part course
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
---

# The reading plan

Chapter numbers and titles of the two SRE books and of *Software Engineering at Google* were
checked against their online tables of contents on 2026-11-12. DDIA is the first edition (2017).
"Must" means the course assumes it has been read and does not retell it.

| Source | Must read | Read when the part needs more |
|---|---|---|
| **Site Reliability Engineering** (free at `sre.google/sre-book`) | ch. 3 Embracing Risk · ch. 4 Service Level Objectives · ch. 6 Monitoring Distributed Systems · ch. 19 Load Balancing at the Frontend · ch. 20 Load Balancing in the Datacenter · **ch. 21 Handling Overload** · **ch. 22 Addressing Cascading Failures** · ch. 23 Managing Critical State: Distributed Consensus for Reliability · ch. 24 Distributed Periodic Scheduling with Cron · ch. 26 Data Integrity: What You Read Is What You Wrote | ch. 2 The Production Environment at Google (the vocabulary of Borg, Colossus, Chubby in ten pages) · ch. 17 Testing for Reliability · ch. 25 Data Processing Pipelines · ch. 27 Reliable Product Launches at Scale |
| **The Site Reliability Workbook** (free at `sre.google/workbook`) | ch. 2 Implementing SLOs · ch. 5 Alerting on SLOs · **ch. 12 Introducing Non-Abstract Large System Design** (a worked design round in Google's own style: read it twice) · ch. 16 Canarying Releases | ch. 11 Managing Load · ch. 14 Configuration Design and Best Practices · ch. 17 Identifying and Recovering from Overload |
| **Designing Data-Intensive Applications** (1st ed.) | ch. 5 Replication · ch. 6 Partitioning · ch. 7 Transactions · ch. 8 The Trouble with Distributed Systems · ch. 9 Consistency and Consensus · ch. 11 Stream Processing | ch. 3 Storage and Retrieval (must for the key-value and blob problems) · ch. 1 (percentiles, load) · ch. 4 Encoding and Evolution · ch. 12 (end-to-end argument, request IDs) |
| **Software Engineering at Google** (free at `abseil.io/resources/swe-book`) | — | ch. 15 Deprecation · ch. 22 Large-Scale Changes · ch. 14 Larger Testing · ch. 1 (Hyrum's Law; confirm the location) |
| **Papers** | Raft (extended version, sections 5 and 8) · "The Chubby Lock Service" · Spanner (sections 3 and 4) · "The Tail at Scale" · "Scaling Memcache at Facebook" (section 3) | Bigtable · Dynamo · GFS and the two Colossus posts · Borg · Monarch · "The Dataflow Model" · "Paxos Made Live" · Kleppmann, "How to do distributed locking" |

# Part 1 · Estimation that changes the design

**Assumed reading.**

- The SRE workbook, chapter 12, *Introducing Non-Abstract Large System Design*, walks one design from a single machine to a planet-wide system with numbers at every step. Read it twice.
- The SRE book, chapter 3, *Embracing Risk*, is where the availability targets in this part come from.

**Read next.**

- *Designing Data-Intensive Applications*, chapter 1: describing load and describing performance, including why percentiles and not averages.
- Dean and Barroso, *The Tail at Scale*: where the fan-out arithmetic comes from, and what to do about it.
- The SRE workbook, chapter 12, again, now with a pencil: redo its numbers before reading its answers.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| EST-01 | Time and size constants | A | A day is about ten to the fifth seconds, so a million a day is roughly ten a second. I am rounding down by about a seventh, which is fine for sizing. | 1.1 Time and size constants |
| EST-02 | Load shape | A | The average is about a thousand a second. I will assume a peak of three times that and size serving for it. Storage follows the average. And for a ten times burst, I will say what queues and what is shed. | 1.2 Load shape |
| EST-03 | Storage sizing | A | Records times bytes times retention gives the logical size. Then I multiply by replication and index overhead and divide by a fill factor, and I state the result twice: in terabytes, and in machines. | 1.3 Storage sizing |
| EST-04 | Machine envelope | A | One node handles on the order of a hundred thousand simple operations a second, and holds a few terabytes. I size the cluster by data and by load, take the larger, and say which resource is the binding one. | 1.4 The machine envelope |
| EST-05 | Latency ladder | A | Memory is nanoseconds, flash is microseconds, a datacentre round trip is half a millisecond, and an ocean is over a hundred. So I count wide-area round trips on the common path first. | 1.5 The latency ladder |
| EST-06 | Availability maths | A | Dependencies in series multiply their availabilities, so five at three nines give me two and a half. Redundant copies multiply their unavailabilities, but only if they fail independently. So I look for what they share. | 1.6 Availability |
| EST-08 | Queueing intuition | A | Time in the system is service time over one minus utilisation, so at ninety percent a request takes ten times longer. I size for about seventy percent at peak, and I bound every queue. | 1.7 Queueing |
| EST-09 | Fan-out and tail latency | B | The chance that any of N parallel calls is slow is one minus the chance that all are fast. For a hundred leaves at one percent, that is sixty-three percent. So I care about the leaves' extreme tail, and I will hedge or drop the slowest. | 1.8 Fan-out and tail latency |
| EST-10 | Bandwidth and transfer time | B | Transfer time is bytes times eight over the link rate. A hundred petabytes over a hundred gigabits a second is about three months. So the copy is a project, and the change log has to outlive it. | 1.9 Bandwidth and transfer time |
| EST-07 | Durability maths | B | At one to two percent a year, a fleet of seventy-five thousand disks loses about three a day. Whether that loses data depends on how fast I repair, how many simultaneous losses the encoding survives, and whether the copies can fail together. | 1.10 Durability |
| EST-12 | Cost modelling | B | The biggest line in this design is storage. Three copies cost three times the logical size, an erasure code about one and a half. So for cold data I would encode, and I would tier by age. | 1.11 Cost |

## Figures

![A system sized for the average falls over every evening](diagrams/video-p1-load-curve.pdf){width=100%}

![Six rungs, each about ten times the one below](diagrams/video-p1-latency-ladder.pdf){width=100%}

![Three good dependencies make one mediocre service](diagrams/video-p1-series-parallel.pdf){width=100%}

![Latency does not rise in a straight line](diagrams/video-p1-utilisation-curve.pdf){width=100%}

![One request, a hundred leaves, and the slowest one sets the time](diagrams/video-p1-fanout.pdf){width=100%}

## Traps and easy confusions

**Easy to confuse · Precision is not rigour.** Working to three significant figures costs time and adds no information: the inputs are guesses. Rounding to a power of ten is fast, but hides a factor of three. When a result lands near a boundary, such as "fits in memory, just", redo that one number carefully.

**Trap · The number most candidates stop at is five times too small.** Logical data: **73 TB**. Provisioned: **344 TB**. The factor between them is 4.7. Stopping at the logical figure gives nine machines instead of forty-three.

## Probe drills

**1. Your cache hit ratio falls from 99 percent to 95. What happens to the database?**

- Misses go from **1% to 5%** of reads: database load is **five times** higher
- At 1 M reads a second: 10,000 /s becomes 50,000 /s
- If the database was at 30% utilisation, it is now past saturation
- *A four-point drop in hit ratio is a fivefold rise in backend load.*

> The database sees the misses, so I look at the miss ratio. It goes from one percent to five percent, which is five times the load. At a million reads a second, that is ten thousand a second becoming fifty thousand. If the database was running at thirty percent, it is now beyond saturation, and from the queueing curve, latency there is no longer bounded.

**2. Which number would you alarm on?**

- The **miss rate in requests per second** reaching the database, against its known capacity
- Not the hit ratio: 99% and 98% look alike on a chart and differ by 2×

> I would alarm on the absolute miss rate reaching the database, in requests a second, compared with the capacity I measured for it. I would not alarm on the hit ratio itself. Ninety-nine and ninety-eight look the same on a chart, and they are a factor of two apart in backend load.

**3. This service calls five others on every request. What is its availability?**

- If all five are hard dependencies at 99.9%: 0.999^5^ $\approx$ **99.5%**, about 44 hours a year
- Its own failures come on top
- To promise 99.9%, each dependency needs about 99.98%, or some must become soft

> If all five are hard dependencies at three nines each, they multiply. That is ninety-nine point five percent before my own failures, about forty-four hours a year. So I cannot promise three nines on top of five three-nine dependencies. Either each one has to be nearer ninety-nine point nine eight, or I make some of them soft, with a default or a stale answer when they fail.

**4. And if two of those five share one database?**

- Their failures are no longer independent: when the database is down, both are
- That **helps** the serial sum slightly, since it is one failure instead of two
- It **breaks** any redundancy between them: a fallback from one to the other is worth nothing

> Then those two fail together. For the serial sum that is slightly better, since it is one failure instead of two. But it breaks any redundancy I was counting on. If my plan was to fall back from one to the other, the fallback is worth nothing, because the event that takes the first away takes the second with it. So I would ask what else is shared: the database, the configuration, the release train.

**5. You may ask me for one number. Which one?**

- The **peak rate of the dominant operation**, with its size
- It sets the machine count, shows whether memory or disk binds, and whether one node is enough
- Second choice: the latency target, because it decides how many wide-area round trips are allowed

> The peak rate of the dominant operation, with the size of one item. From that I get the machine count, I see which resource binds, and I learn whether this is a one machine problem that I am over-thinking. If I am allowed a second number, it is the latency target, because that tells me how many wide-area round trips the common path may contain.

**6. You sized forty-three nodes. I give you a budget for twenty. What changes?**

- Find the largest multiplier in the chain: **replication at 3×**
- Erasure-code data older than a month: about 1.5× on most of the bytes
- Or cut retention on the hot tier and roll old data up
- Say what is given up: slower reads and repairs of old data

> I go back to the chain and find the largest multiplier, which is replication at three times. Most of the bytes are old and rarely read, so I would erasure-code everything older than about a month, which brings that data down to one and a half times. If that is not enough, I shorten retention on the hot tier and keep roll-ups. And I would say what we give up: reads and repairs of old data get slower.

# Part 2 · Consistency, time and failure

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 8, *The Trouble with Distributed Systems*: unreliable networks, unreliable clocks, process pauses.
- Chapter 9, *Consistency and Consensus*: what linearizability is, where it is needed, and what it costs.
- This part assumes both and works the cases an interviewer asks about.

**Read next.**

- The Spanner paper, sections 3 and 4: TrueTime and how commit wait gives external consistency.
- *Designing Data-Intensive Applications*, chapter 5, the section on the limits of quorum consistency.
- Kleppmann, *How to do distributed locking*: the pause, the fencing token, and when a best-effort lock is enough.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| FND-01 | CAP, stated correctly | A | During a partition, each operation keeps either linearizability or availability, and I will say which for each. When there is no partition, CAP tells me nothing, and the trade-off is about latency. | 2.1 CAP, stated correctly |
| FND-02 | PACELC | A | In a partition I trade availability against consistency. The rest of the time I trade latency against consistency, and that is the cost I pay on every request. So I choose per operation which ones wait for a majority. | 2.2 PACELC |
| FND-03 | Consistency-model ladder | A | I choose consistency per operation, not per system. Checkout is linearizable. The user's own profile is read-your-writes. The feed is bounded-stale, a few seconds old at most. | 2.3 The consistency ladder |
| FND-04 | Linearizability vs serializability | A | Linearizability is about single operations in real-time order. Serializability is about whole transactions being equivalent to some serial order. They are independent, and strict serializability is both together. | 2.4 Linearizability and serializability |
| FND-12 | Quorums | A | R plus W greater than N guarantees that a read set and a write set overlap. It does not give linearizability on its own, because of concurrent writes, sloppy quorums and partial failures. | 2.5 Quorums |
| FND-07 | Physical clocks | A | Clock synchronisation gives millisecond skew with no hard bound. So I use a monotonic clock for durations, and I never order events across machines by wall clock alone. Order comes from a version. | 2.6 Physical clocks |
| FND-08 | Logical clocks | B | Lamport timestamps give a total order that respects causality. Version vectors go further and detect that two updates were concurrent, which is what I need before I can merge instead of overwrite. | 2.7 Logical clocks |
| FND-09 | Hybrid and bounded clocks | B | A hybrid logical clock is physical time plus a logical counter. A bounded clock exposes its uncertainty as an interval, and the transaction waits that interval out before it reports the commit. That wait buys real-time order. | 2.8 Hybrid and bounded clocks |
| FND-11 | Ordering guarantees | A | Total order needs a single log or consensus group. Per-key order needs only partitioning by key, with a version the receiver checks. So first I ask which one the product actually needs. | 2.9 Ordering guarantees |
| FND-10 | Idempotency and "exactly-once" | A | Exactly-once delivery does not exist. What I can build is exactly-once effect: at-least-once delivery, plus processing that is idempotent or deduplicated, with the key stored in the same transaction as the effect. | 2.10 Idempotency and exactly-once |
| FND-13 | Leases and fencing tokens | A | A lease is ownership with a time limit, and it only needs bounded clock drift. A fencing token is a number that only grows, checked by the resource, and it makes a paused or partitioned former owner harmless. | 2.11 Leases and fencing tokens |
| FND-05 | Safety vs liveness; FLP | B | Real consensus protocols keep safety always, and get liveness under partial synchrony by using timeouts. So a bad timeout can stall the system, and it can never make two nodes disagree. | 2.12 Safety, liveness and FLP |
| FND-06 | Failure models | B | I assume crash-recovery: a node can return with stale state, so it must be fenced. And I assume grey failure, where a node passes health checks and serves badly, so I detect it from the caller's side. | 2.13 Failure models |
| FND-15 | Failure detection | B | A heartbeat timeout trades detection time against false positives. And a single observer cannot tell a dead node from its own partition, so the decision to act belongs to a quorum. | 2.14 Failure detection |
| FND-16 | Gossip dissemination | B | Gossip reaches all nodes in a logarithmic number of rounds with no coordinator, and it converges eventually. So I use it for membership and soft state, and never for anything that needs an order. | 2.15 Gossip |

## Figures

![A partition forces a choice on the minority side](diagrams/video-p2-partition.pdf){width=100%}

![The two session anomalies that users actually report](diagrams/video-p2-session-anomalies.pdf){width=100%}

![Two different guarantees that sound alike](diagrams/video-p2-lin-vs-ser.pdf){width=100%}

![Overlap is not linearizability](diagrams/video-p2-stale-quorum.pdf){width=100%}

![Last writer wins, and the later write loses](diagrams/video-p2-lww-skew.pdf){width=100%}

![Version vectors tell "after" from "at the same time"](diagrams/video-p2-version-vector.pdf){width=100%}

![Commit wait: sit out the uncertainty](diagrams/video-p2-commit-wait.pdf){width=100%}

![The reply is lost, the client retries, the customer pays twice](diagrams/video-p2-lost-reply.pdf){width=100%}

![Deliver at least once, apply at most once](diagrams/video-p2-dedup.pdf){width=100%}

![A paused holder writes after its lease has gone](diagrams/video-p2-pause.pdf){width=100%}

![The resource checks a number that only grows](diagrams/video-p2-fencing.pdf){width=100%}

![Each round, everyone who knows tells someone at random](diagrams/video-p2-gossip.pdf){width=100%}

## Traps and easy confusions

**Trap · "Strongly consistent", over an arrow labelled "async".** A candidate draws a primary database and two replicas, labels the arrows between them **async**, sends reads to the replicas, and writes in the requirements: *strongly consistent*. The interviewer asks one question: "A user saves, and reloads. What do they see?"

**Trap · Why "CA" is not on the menu, and what a "CP" system really does.** You cannot choose to have no partitions: a network of more than one machine can always lose messages. So "CA" describes a single node, or a wish. A consistent system does not go wholly dark in a partition. **The majority side keeps working.** Only nodes on the minority side refuse. Say which requests fail, and for whom.

**Trap · Per-key order is lost in three ordinary ways.** **A retry overtakes**: message 1 fails, message 2 succeeds, message 1 is retried and lands second. **The partition count changes**: the key now hashes elsewhere, and old and new partitions are read in parallel. **Parallel consumers** inside one partition process two events for one key at once.

**Trap · The token must be checked where the write lands.** A lock service that hands out tokens which the storage never checks protects nothing. If the resource cannot check a token, say so, and say what bounds the damage instead.

## Probe drills

**1. Is R plus W greater than N linearizable?**

- **No.** It guarantees overlap, not real-time order
- A write in flight can be seen by one reader and then missed by a later one
- Sloppy quorums and partly failed writes break it too

> No. It guarantees that a read set overlaps a write set, and that is all. A write still in flight can be seen by one reader and missed by a later reader, which violates real-time order. A sloppy quorum can put the write on nodes the reader never asks. And a write that failed part-way is not rolled back.

**2. What would make it linearizable, and at what cost?**

- The reader **writes back** the newest value to a quorum before returning: one more round per read
- Or replace it with a **consensus log** and read through the leader
- Either way, "any node accepts a write during a partition" is gone

> Two options. The reader repairs before returning: it writes the newest value it saw back to a quorum, which costs a second round on every read. Or I replace bare quorums with a consensus log and read through the leader. Either way I give up the property that any node accepts writes during a partition, so I would only do it for the operations that need it.

**3. Two events happened on two machines. Which came first?**

- From wall clocks: **unknown** if the stamps are closer than the clock error
- If both went through one log: the log position decides
- If they carry version vectors: one precedes the other, or they are concurrent

> From wall-clock timestamps alone, I cannot say, if the stamps are closer together than the clock error, and that error has no hard bound. If both events went through one log, the log position decides. If they carry version vectors, I can tell that one came before the other, or that they were concurrent. Concurrent is a real answer, and it means I have to merge.

**4. And if the two clocks are 200 milliseconds apart?**

- Any two events within 200 ms may be ordered wrongly
- With last-writer-wins, the later write can be silently discarded
- So: issue versions from one place, or use a clock with a bounded interval and wait it out

> Then any two events within two hundred milliseconds of each other may be ordered wrongly, and with last writer wins, the later write can be silently discarded. So I would not let wall time decide. Either a single authority issues the version, or I use a clock that exposes its uncertainty and wait that uncertainty out before acknowledging.

**5. What does your system do during a partition?**

- Answer **per operation**, and for **each side**
- Writes that need an invariant: majority side continues, minority side returns an error
- Reads that tolerate staleness: both sides answer, marked with their age
- Say how the minority catches up when the partition heals

> I answer per operation and for each side of the split. Writes that protect an invariant continue on the majority side and fail fast on the minority side. Reads that tolerate staleness are served on both sides, with their age. And when the partition heals, the minority replays the log from its last position. Nothing has to be merged, because it accepted no writes.

**6. Why not use synchronised time for a lease?**

- A lease needs a **duration**, not a time of day: use each machine's monotonic clock
- It assumes bounded drift, which is realistic, not bounded offset, which is not
- And a pause can outlast any lease, so the resource checks a fencing token

> A lease needs a duration, not a time of day. Each side measures it on its own monotonic clock, the holder stopping slightly early. That assumes only bounded drift between two clocks over ten seconds, which is realistic. It does not assume the clocks agree on what time it is. And because a pause can outlast any lease, the resource still checks a fencing token.

# Part 3 · Consensus

**Assumed reading.**

- The Raft paper, extended version: section 5 (the algorithm) and section 8 (client interaction). Read them with the figures.
- The SRE book, chapter 23, *Managing Critical State*: what to build on consensus and how to deploy it.
- This part walks the algorithm as one trace and then goes to what the paper leaves to implementers.

**Read next.**

- Chandra, Griesemer and Redstone, *Paxos Made Live*: the gap between an algorithm and a service.
- *Designing Data-Intensive Applications*, chapter 9: total order broadcast, epoch numbers and quorums, and the limits of consensus.
- The Raft paper, section 6 (membership) and section 7 (log compaction), once sections 5 and 8 are solid.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| FND-14 | State-machine replication | B | A replicated log, applied deterministically in order, gives identical replicas. So consensus is really agreement on a log, and everything else is a state machine on top. | 3.1 State-machine replication |
| CON-03 | Raft core | A | Raft has terms with at most one leader each. The leader appends, and followers accept only if the previous entry matches. An entry of the leader's own term is committed once a majority stores it. And a server only votes for a candidate whose log is at least as up to date, so a new leader always holds every committed entry. | 3.2 Raft: the election |
| CON-04 | Raft in production | B | Beyond the paper's core, a production system needs membership change one server at a time, snapshots to bound the log, pre-vote against disruptive rejoiners, non-voting learners for new replicas, and leadership transfer for maintenance. | 3.5 Raft in production |
| CON-05 | Linearizable reads | B | Reading from a leader is not enough. Either the leader confirms it still leads with a heartbeat round to a majority, or it relies on a leader lease, which is a clock-drift assumption I should state. | 3.6 Linearizable reads |
| CON-01 | Paxos, single decree | B | Single-decree Paxos has two phases: prepare and promise, then accept and accepted. Ballot numbers order the attempts, any two majorities intersect, and a value is chosen once a majority accepts it. | 3.7 Paxos, single decree |
| CON-02 | Multi-Paxos | B | In Multi-Paxos a stable leader runs phase one once and then needs one round trip per log slot. A production implementation adds snapshots, membership change, leader leases and checks against disk corruption. | 3.8 Multi-Paxos |
| CON-06 | Multi-Raft | B | A large store runs one consensus group per shard. The costs are heartbeats per group, which I coalesce per node pair, many logs, which share one write-ahead log, and rebalancing, which is a membership change per moved replica. | 3.9 Many groups at once |
| CON-14 | Quorum placement across regions | B | I place three or five voters over at least three failure domains. Commit latency is about the round trip from the leader to the nearest majority, so where the leader lives decides who pays. | 3.10 Quorums across regions |

## Figures

![The same log, applied in the same order, gives the same state](diagrams/video-p3-smr.pdf){width=100%}

![A follower times out, raises the term and asks for votes](diagrams/video-p3-election.pdf){width=100%}

![Append, check the previous entry, commit on a majority](diagrams/video-p3-append.pdf){width=100%}

![An old-term entry on a majority is still not safe](diagrams/video-p3-figure8.pdf){width=100%}

![The leader must prove it still leads before it answers a read](diagrams/video-p3-readindex.pdf){width=100%}

![Two phases, and a proposer that must adopt what it finds](diagrams/video-p3-paxos-duel.pdf){width=100%}

![Commit latency is the round trip to the nearest majority](diagrams/video-p3-placement.pdf){width=100%}

## Traps and easy confusions

**Trap · Two leaders, each sure it leads.** A leader is cut off from its followers. It does not know. It keeps accepting writes. On the other side, the followers time out and elect a new leader, which also accepts writes. The interviewer asks: "A client wrote to the old leader during those ten seconds. Where is that write now?"

**Trap · A leader commits by counting replicas only for entries of its own term.** The leader of term four must first get an entry **of term four** onto a majority. Now server five can no longer win: its log is behind. The old term-two entry becomes committed at that moment, **indirectly**, because it precedes a committed entry. In practice a new leader appends an empty entry as soon as it is elected, exactly for this.

**Easy to confuse · Raft and Multi-Paxos, side by side.** Both: a leader, a replicated log, majorities, one round trip per write in the steady state. Raft requires the new leader to **already hold** every committed entry; logs have no gaps. Multi-Paxos lets any node lead and **recover** missing entries during phase one; slots may be decided out of order. For a design round they are the same building block. Say "a consensus log" and name whichever your store uses.

## Probe drills

**1. A partitioned leader still accepts a write. What happens to it?**

- It appends locally but **cannot reach a majority**, so the entry never commits
- The client gets no success: a timeout
- On rejoining, it sees a higher term, steps down, and the entry is **overwritten**

> The old leader appends the entry to its own log, but it cannot reach a majority, so the entry is never committed and the client never gets a success. When the partition heals, the old leader sees a higher term and steps down. The log-matching check then overwrites that entry with the new leader's log.

**2. And what does the client that sent it do?**

- It saw a timeout: the outcome is **unknown**, not failed
- It retries against the new leader **with the same request ID**
- The state machine deduplicates, so the command applies at most once

> The client saw a timeout, which means unknown, not failed. In another interleaving the entry could have committed just before the reply was lost. So it retries against the new leader with the same request identifier, and the state machine remembers recent identifiers per client. The command is applied at most once, whichever way it went.

**3. Can followers serve reads?**

- **Stale** reads: yes, immediately, with no guarantee
- **Linearizable** reads: yes, if the follower gets a read index from the leader and waits to apply it
- **Bounded-stale** reads: yes, at a timestamp the follower knows it has fully applied

> Yes, in three ways. A follower can answer immediately from its own state, and that read may be stale. It can ask the leader for a read index, wait until it has applied that far, and answer: that is linearizable, and costs one round trip to the leader. Or it can serve at a timestamp it knows it has fully applied, which gives bounded staleness with no round trip.

**4. One of three replicas has died for good. Replace it safely.**

- Add the new node as a **learner**; it receives a snapshot, then the log
- When caught up, **promote** it: now four voters, quorum three
- **Remove** the dead one: three voters, quorum two
- Never remove first: two voters need both, and one more failure stops everything

> I add the new node as a non-voting learner. It gets a snapshot and then the log. When it has caught up, I promote it, which makes four voters with a quorum of three. Then I remove the dead node, back to three voters. The order matters. If I removed the dead node first, I would have two voters that both must be up, and one more failure stops all writes.

**5. Five replicas in three regions. What is the write latency?**

- The round trip from the leader to the **nearest majority**
- Layout 2 + 2 + 1, leader in a region with two: one local, one remote → the nearer remote region's round trip
- Add the client's distance to the leader

> It is the round trip from the leader to the nearest majority. With two, two and one, and the leader in a region with two voters, it has two local acknowledgements and needs one remote, so the cost is the round trip to the nearer other region. Then I add the client's own distance to the leader, which for a far client can be the larger part.

**6. Move the leader to follow the traffic. Who pays now?**

- Clients near the new leader gain; the others lose the same amount
- If the new region has **one** voter, the quorum is further away: commits get slower for everyone
- Moving costs a brief pause; do it by leadership transfer, not by killing the leader

> The clients near the new leader gain, and the others lose about the same. But there is a second effect. If the new region has only one voter, the leader needs two remote acknowledgements, so every commit gets slower. And the move itself should be a leadership transfer to a caught-up follower, which takes a moment, not a kill, which costs an election timeout.

# Part 4 · Coordination services

**Assumed reading.**

- Burrows, *The Chubby Lock Service for Loosely-Coupled Distributed Systems*: read it whole, it is short.
- Part 2 of this course: leases and fencing tokens. Part 3: the consensus log underneath.
- This part leaves the paper's design rationale and usage statistics to the paper, and goes to the timeline, the primitives and the patterns.

**Read next.**

- Kleppmann, *How to do distributed locking*: the timing argument and fencing, in full.
- *Designing Data-Intensive Applications*, chapter 9: membership and coordination services.
- *The Site Reliability Workbook*, chapter 14, *Configuration Design and Best Practices*.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| CON-07 | Chubby model | B | In the Chubby model a session is a lease renewed by KeepAlives. When the client's own, shorter copy of the lease expires, it stops trusting its cache and waits through a grace period. If the master does not answer by then, the session and all its locks are gone. And for correctness, the holder passes a sequencer to whatever it writes to. | 4.1 The Chubby model |
| CON-09 | etcd primitives | B | etcd gives me four primitives on one revision counter: leases with a time to live that delete their keys, compare and swap transactions, and watches that resume from a revision so I never miss a change. Everything else, election, locks, membership, is built from those. | 4.2 etcd primitives |
| CON-10 | Leader election as a pattern | A | I elect with a compare and swap on a key that carries a lease. The winner's epoch comes from the store's revision, every side effect carries it, and every receiver rejects a lower one. So a paused former leader can wake up, and do no harm. | 4.3 Leader election as a pattern |
| CON-11 | Locks: efficiency vs correctness | A | First I say whether this lock is for efficiency or for correctness. For efficiency, a single cache node with an expiry is fine. For correctness I need a consensus-backed lock, a fencing token, and a resource that checks the token on every write. Without the check, no lock is safe against a pause. | 4.4 Locks: for efficiency, or for correctness |
| CON-12 | Membership and service discovery | A | Members register under a lease, so a dead member disappears on its own. Clients watch for changes and also drop a member on their own errors. And because any client cache can be stale, every request carries the shard and epoch it expects, and the server refuses a request meant for someone else. | 4.5 Membership and service discovery |
| CON-13 | Configuration distribution | A | I treat configuration like code. Every change is a version, delivered by push with a periodic pull as a backstop, checked by checksum before it applies, rolled out in stages with health checks, with last known good as the fallback. And each server reports the version it is running, so I can see who has not caught up. | 4.6 Configuration distribution |

## Figures

![A session is a lease, renewed by KeepAlives, with a grace period on top](diagrams/video-p4-chubby-session.pdf){width=100%}

![Two nodes both act as leader for a few seconds](diagrams/video-p2-pause.pdf){width=100%}

![Win with a compare-and-swap; carry the epoch on everything you do](diagrams/video-p4-election-epoch.pdf){width=100%}

![A majority of independent nodes, and a clock that jumps](diagrams/video-p4-redlock-clock.pdf){width=100%}

![A thousand clients wait on one lock](diagrams/video-p4-herd.pdf){width=100%}

![A client sends traffic to an address that now belongs to someone else](diagrams/video-p4-stale-discovery.pdf){width=100%}

![Register with a lease, publish by watch, verify on connect](diagrams/video-p4-registry.pdf){width=100%}

![One bad config value, everywhere, within a minute](diagrams/video-p4-config-push.pdf){width=100%}

![Versioned snapshots, deltas, push with a pull backstop, staged rollout](diagrams/video-p4-config-flow.pdf){width=100%}

## Traps and easy confusions

**Trap · A lock that works until the holder pauses.** A batch job takes a lock so that only one copy rewrites a report. It has worked for a year. One night the holder stalls in garbage collection for twenty seconds. Its lock expires. A second copy starts. The first wakes up, still certain it holds the lock, and both write the same file.

**Trap · "Failover takes fifteen seconds. Make it one.".** Shorten the lease, and every garbage-collection pause or slow disk now causes a **false failover**, each one an outage of its own. Better: keep the lease, and make the **leaderless interval cheap**. Workers continue the work they already have; only new decisions wait. If decisions truly cannot wait, move them into a consensus group whose leader change is already sub-second, and fence with its term.

**Trap · "The registry is down. What breaks?".** Nothing that is already running should break. Clients keep serving from their **last known member list**. What stops: joins, leaves and ownership changes. A new server cannot take traffic; a dead one is removed only by client-side errors. Design so the registry is **not on the request path**. If every request reads the registry, its outage is your outage.

**Trap · The config service must not be needed to start.** If a server cannot start without reaching the config service, then a config-service outage plus a restart wave is a full outage. Each server **persists its last known good config locally** and starts from it, then catches up. The same holds for the coordination service: a cold start of everything at once must not need it in the critical path.

## Probe drills

**1. Why is a lock on a cache cluster not enough here?**

- It assumes **bounded pauses, drift and delay**; any one violated gives two holders
- It hands out **no fencing token**, so the resource cannot reject a late holder
- For correctness: a consensus store, a token, and a check at the resource

> Because it rests on timing assumptions: that a client never pauses longer than the expiry, that clocks do not jump, and that messages arrive in bounded time. Break any one, and two clients hold the lock. And it gives no fencing token, so the resource has no way to reject the late holder. For a correctness lock I want a consensus-backed store, a fencing token, and the check done by the resource on every write.

**2. Then when is it enough?**

- When the lock is for **efficiency**: a double holder only repeats work
- When every write is **idempotent or conditional** anyway, so the lock is an optimisation
- Then even **one node** is enough; five buys little

> It is enough when the lock is for efficiency. If two holders only means some work is done twice, a cheap lock is the right choice. It is also enough when the writes are already safe on their own, idempotent or conditional on a version, so the lock just reduces wasted work. And in that case even a single node is fine. Five independent nodes buy very little, because the cost of failure was already acceptable.

**3. A thousand clients wait on one lock. What happens on release?**

- Naive: all wake, one wins, the rest retry: a **herd** on every release
- Fix: a queue of keys ordered by revision; each waiter **watches only its predecessor**
- And ask why: a thousand waiters is usually a **work queue** in disguise

> Done naively, every waiter watches the lock key, so each release wakes all of them, one wins and the rest fail and watch again. That is a herd on every release. Instead, each waiter creates its own key in a queue, ordered by revision, and watches only the key just before it. A release wakes exactly one client. And I would ask why a thousand clients wait on one lock. That is usually a work queue that should be a queue.

**4. A node was offline for two hours. How does its config catch up?**

- It reconnects with **its version**; the service sends deltas, or a **full snapshot** if they no longer reach back
- It validates the checksum, applies, and resumes the stream
- Until then it serves from **last known good**, persisted on its disk

> It reconnects and sends the version it has. If the service still holds deltas back that far, it sends them. If not, it sends a full snapshot at the current version. The node checks the checksum, applies it, and resumes the stream. Until then it runs on its last known good configuration, which it kept on local disk, so it could start even while the config service was unreachable.

**5. And how do you know it did?**

- Each node reports the **version applied** and a **hash** of the running config
- A dashboard of **version spread**; an alert on any node behind by more than a few minutes
- The hash catches a node that claims the version but parsed it differently

> Each node reports the version it has applied, and a hash of the configuration it is actually running. I watch the spread of versions across the fleet and alert when any node has been behind for more than a few minutes. The hash matters because a node can claim the right version and still be running something different, for example after a parse error it silently ignored.

**6. Your leader election fails over in fifteen seconds. Is that acceptable?**

- Ask what stops during it: **new decisions**, or the **data path**?
- Keep the lease long enough to ride out pauses; make the leaderless interval **cheap**
- If the data path stops, move it out from behind the leader

> It depends on what stops in those fifteen seconds. If only new decisions wait, scheduling or rebalancing, it is usually fine, and a shorter lease would bring false failovers on every long pause. If the data path stops, the problem is not the lease length, it is that the data path depends on the leader. I would move it out from behind the leader, so workers keep serving what they already own.

# Part 5 · Replication

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 5, **whole**.
- Part 2 of this course: session guarantees on the consistency ladder, quorums, last-writer-wins and version vectors. Part 3: consensus.
- The chapter's survey of topologies and the history of conflict resolution stay in the chapter. This part goes to failover, the outbox, repair and the numbers.

**Read next.**

- DeCandia et al., *Dynamo*: sloppy quorums, hinted handoff, Merkle trees, vector clocks, in one paper.
- Ghemawat et al., *The Google File System*: leases, primaries and chunk version numbers.
- *Designing Data-Intensive Applications*, chapter 11: change data capture and event sourcing.
- *Site Reliability Engineering*, chapter 26, *Data Integrity*. The Google Cloud disaster-recovery planning guide for RPO and RTO.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| REP-01 | Single-leader replication | A | With asynchronous replication, failover loses whatever was not yet shipped, so my recovery point is the lag. Semi-synchronous loses nothing if the follower that acknowledged is the one promoted. And in every case, failover means detect, choose the most advanced follower, fence the old leader, repoint clients, and reconcile the tail it left behind. | 5.1 Single-leader replication |
| REP-06 | Primary–backup with leases | B | Primary and backup with leases: the master grants one replica a time-bounded lease to order writes, and raises a version number with each lease, so a replica that missed writes is detected as stale. Failover waits out the lease. | 5.2 Primary–backup with leases |
| REP-07 | Log shipping | B | Physical log shipping gives a byte-identical follower on the same version. A logical log of row changes by key can feed a different version, or a different system entirely, which is how I upgrade without downtime and how change data capture works. | 5.3 Log shipping |
| REP-10 | Replication lag | A | I measure replication lag in seconds, with a heartbeat row, and I treat it as a distribution with causes, not one number. For read your writes and monotonic reads, the session carries a log position, and a replica serves the read only if it has applied that far. | 5.4 Replication lag |
| REP-08 | Change data capture and the outbox | A | I never write to the database and the log as two separate steps. The event goes into an outbox table in the same transaction, a relay ships it from the database in commit order, and because the relay can publish twice, every consumer deduplicates by event identifier. | 5.5 Change data capture and the outbox |
| REP-02 | Multi-leader replication | B | Multi-leader replication gives local writes in every region and keeps working through a partition, and it pays with conflicts found after both writers were told they succeeded. Where I can, I home each entity to one region, so each entity has one leader. | 5.6 Multi-leader replication |
| REP-09 | Conflict resolution | B | For conflicts I choose by what I can afford to lose. Last writer wins is acceptable only where losing a concurrent write is harmless. Otherwise version vectors detect concurrency and keep both for a merge, or I use a CRDT, whose merge is correct by construction. | 5.7 Conflict resolution |
| REP-03 | Leaderless (Dynamo-style) | B | In a leaderless store every replica takes writes. I wait for W of N on writes and R on reads, concurrent versions come back to the client to merge, and a sloppy quorum with hinted handoff keeps writes available at the cost of reads that can miss them for a while. | 5.8 Leaderless replication |
| REP-04 | Read repair and anti-entropy | B | Replicas converge two ways: read repair fixes keys as they are read, and background anti-entropy compares replicas and fixes everything else. Anti-entropy has a deadline: it must finish within the tombstone grace period. | 5.9 Read repair and anti-entropy |
| DS-04 | Merkle tree | B | For anti-entropy I keep a Merkle tree per key range: hashes of buckets, then hashes of hashes. Two replicas compare roots, descend only where they differ, and exchange a few kilobytes to find a difference that a full scan would need gigabytes for. | 5.10 Merkle trees |
| REP-14 | Tombstones | B | A delete is a tombstone, kept for a grace period longer than the longest outage plus repair. A replica that was away longer than that is rebuilt from scratch, or it will resurrect deleted data. | 5.11 Tombstones |
| REP-11 | Geo topologies | A | For multiple regions I decide three things in advance: where each type of data is written, what a reader in another region sees, and what is lost when a region goes. Usually that means consensus for money, entities homed to a region for user data, and followers for read-mostly data. | 5.12 Geo topologies |
| REP-12 | Snapshot plus log catch-up | B | A new or lagging replica loads a snapshot taken at a known log position and replays from there, which needs the log retained back that far. I compare replay time, which is backlog over replay rate minus arrival rate, with rebuild time, and past a point the rebuild wins. | 5.13 Snapshot plus log catch-up |
| REP-13 | RPO, RTO and failover orchestration | A | I agree the recovery point and recovery time with the business before the incident, each with its price. Node and zone failover is automated. A regional failover that may lose data is a named person's decision, against a threshold written in the runbook. And with asynchronous replication, my recovery point is at least the lag. | 5.14 RPO, RTO and failover orchestration |

## Figures

![Asynchronous replication loses the tail on failover](diagrams/video-p5-async-tail.pdf){width=100%}

![Lag is usually milliseconds, and sometimes minutes](diagrams/video-p5-lag-curve.pdf){width=100%}

![Two writes, two systems, no atomicity](diagrams/video-p5-dual-write.pdf){width=100%}

![Write the event in the same transaction; ship it from the database](diagrams/video-p5-outbox.pdf){width=100%}

![Each region accepts writes; conflicts appear after the fact](diagrams/video-p5-multi-leader.pdf){width=100%}

![Write to N, wait for W; read from N, wait for R](diagrams/video-p5-sloppy.pdf){width=100%}

![Compare two replicas by comparing hashes, and descend only where they differ](diagrams/video-p5-merkle.pdf){width=100%}

![A deleted value comes back from a replica that was away](diagrams/video-p5-tombstone.pdf){width=100%}

![A new replica copies a snapshot, then replays the log from the snapshot's position](diagrams/video-p5-seed.pdf){width=100%}

## Traps and easy confusions

**Trap · The follower that was one second behind.** A database primary fails at peak. Automation promotes a follower within thirty seconds. Everyone is pleased. The follower was **one second** behind. At five thousand writes a second, five thousand acknowledged writes are gone. Worse: some of them had already been copied into a cache and a search index, which now hold data the database never had.

**Trap · The old leader comes back and accepts writes.** Without step 3, a leader that was only partitioned keeps serving clients that can still reach it. Now two leaders take writes, and the histories diverge. Detection by timeout **cannot** tell dead from partitioned. Only fencing makes the difference harmless. This is the same lesson as part 2's fencing token, applied to a whole database.

**Easy to confuse · What the lease costs, and what it relies on.** After a primary disappears, the master **waits out the lease** before granting a new one: up to 60 seconds without writes to that chunk. It relies on bounded clock drift, like every lease. Writes from a former primary are rejected by the version check.

**Easy to confuse · Read from the leader, or carry a position.** Reading from the leader is simple, and sends your read load back to one machine. Fine for a few seconds after a write; not for every read. Carrying a position costs a token in the session, and a wait or a redirect when the replica is behind. A **bound** is the product decision: "stale by at most 5 seconds, or served by the leader".

**Easy to confuse · Repair must finish inside the tombstone grace period.** A replica that misses a delete must be repaired before tombstones are discarded, or the deleted data returns (section 5.11). So the repair schedule is a **correctness** requirement, not a tuning knob.

**Easy to confuse · Choose per data type, not per system.** Most systems mix them: **account balance** on consensus, **user profile** homed, **counters and likes** multi-leader with a CRDT, **catalogue** one leader with followers everywhere. The price of mixing is that a single request may touch data with different guarantees. Say which data each screen shows.

**Trap · A regional failover nobody had the authority to start.** The primary region is degraded, not down. Writes succeed slowly, some fail. Failing over would lose the replication lag, about 4 seconds of payments. Not failing over keeps a third of requests failing. Two teams argue for forty minutes about whose decision it is.

## Probe drills

**1. The same key is updated in two regions within 100 ms. Which write survives?**

- With **last writer wins**: the higher timestamp; the other is lost **silently**
- With **version vectors**: both, as concurrent versions, until a merge
- Better: **home** the entity, so the second region forwards its write

> It depends on the resolution rule, and I would rather not need one. With last writer wins, the higher timestamp survives and the other is silently lost, even if it was really later, under clock skew. With version vectors both survive as concurrent versions until something merges them. My preferred answer is to home the entity to one region, so the second region forwards the write and there is no conflict.

**2. And who is told?**

- Last writer wins: **nobody**; both users saw success
- With a merge: the application, or the user, sees both and resolves
- If someone must be told, the write needed **one leader**; say so in the design

> With last writer wins, nobody. Both users were told their write succeeded, and one of them was lost. With version vectors, the application or the user sees both and resolves them, like a conflicting edit dialog. And if the business needs someone to be told before success is reported, then this data needed a single leader, or consensus, and the design should say that.

**3. A replica is two days behind. Catch up or rebuild?**

- Catch-up time is **backlog over replay rate minus arrival rate**
- Two days at 5k a second, replay at 20k: **about 16 hours**
- A 2 TB snapshot at 200 MB a second: **under 3 hours**. Rebuild

> I compare the two. Catch-up time is the backlog divided by the replay rate minus the arrival rate. Two days at five thousand writes a second, replayed at twenty thousand, is about sixteen hours. Copying a fresh two terabyte snapshot at two hundred megabytes a second takes under three hours, plus a short replay. So I rebuild. And if the log was not retained for two days, catch-up was never an option.

**4. A deleted item comes back. What happened?**

- A replica **missed the delete** and returned after the tombstone was purged
- Or a stale copy elsewhere, a cache or an index, was written back
- Fix: grace period longer than outage plus repair; rebuild long-absent replicas

> Most likely a replica missed the delete, was away longer than the tombstone grace period, and on return repair treated its old value as data the others were missing. The other common cause is a stale copy outside the store, a cache or a search index, being written back. The fixes: a grace period longer than any outage plus repair, rebuilding replicas that were away longer, and never writing derived copies back to the source.

**5. A user writes, then reads from another region. What do they see?**

- From a follower: possibly **not their write**, for the lag
- Fix: carry the write's **log position**; the far replica waits, or forwards to the home region
- Or route the user's reads home for a few seconds after a write

> If the far region serves the read from a follower, they may not see their own write until the lag passes. To fix it, the session carries the log position of the user's last write. The far replica serves the read only once it has applied that position, and otherwise waits briefly or forwards the read to the home region. A simpler version routes the user's reads home for a few seconds after any write.

**6. The primary fails at peak. What did you lose, exactly?**

- Async: **the lag at that moment**, in writes: lag times write rate
- Plus anything copied to caches or indexes but not to the new leader
- Saved from the old leader's tail and reconciled, not discarded

> With asynchronous replication, I lost the lag at that moment, times the write rate. One second at five thousand writes a second is five thousand acknowledged writes. Plus a subtler loss: anything that reached a cache or an index from the old leader but never reached the new one. I save the old leader's unshipped tail, compare it with the new leader, replay what is safe, and report the rest.

# Part 6 · Partitioning and placement

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 6.
- The chapter's comparison of rebalancing strategies across products stays there. This part does the arithmetic, the protocols and the failure cases.

**Read next.**

- Chang et al., *Bigtable*: tablets, splits and the location hierarchy.
- Adya et al., *Slicer: Auto-Sharding for Datacenter Applications*: a directory that moves load, not keys.
- DeCandia et al., *Dynamo*: the ring with virtual nodes and preference lists.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| PAR-01 | Hash vs range partitioning | A | Range partitioning keeps keys in order, so scans are cheap and time-ordered keys go hot. Hash partitioning spreads load and turns every range query into scatter and gather. Usually I use a compound key: hash the entity to pick the partition, and sort by time inside it. | 6.1 Hash versus range partitioning |
| PAR-02 | Consistent hashing with virtual nodes | A | With hash modulo N, adding one node moves almost every key. With consistent hashing, it moves about one over N, the minimum. I give each node a hundred or more virtual nodes, so shares are within about ten percent and a failed node's load spreads over many neighbours. | 6.2 Consistent hashing with virtual nodes |
| PAR-04 | Dynamic splitting and merging | B | Ranges split by size or by load. A split is first a metadata change in a versioned shard map, with no data copied. Clients cache the map, and a server rejects a request for a range it no longer owns, so a stale client pays one round trip, never a wrong answer. | 6.3 Dynamic splitting and merging |
| PAR-05 | Rebalancing while serving | B | To move a range while serving: copy a snapshot under a throttle, stream the writes that arrived meanwhile, then switch ownership with a short write pause and a new map version, and delete the old copy later. In a consensus store the same thing is a membership change. | 6.4 Rebalancing while serving |
| PAR-06 | Hot keys and hot partitions | A | Partitioning spreads keys, never a single key. I detect hot keys per shard with a sketch, and then match the cure to the traffic: cache or replicate hot reads, split commutative writes into sub-keys summed on read, salt a timeline by time bucket, or rate limit abuse. | 6.5 Hot keys and hot partitions |
| PAR-07 | Request routing | A | Routing can live in any node, a proxy tier, or the client, trading an extra hop against copies of the shard map. Whichever I choose, the owner checks every request and answers with a redirect, so a stale map costs a round trip, never a wrong write. | 6.6 Request routing |
| PAR-08 | Secondary indexes | B | A local secondary index keeps writes on one shard and makes every query scatter to all shards. A global index, partitioned by the indexed value, answers from one place, and is usually maintained asynchronously, so it can lag behind the data. | 6.7 Secondary indexes |
| PAR-09 | Cross-shard operations | B | I choose the partition key so that every operation that must be atomic touches one shard, co-locating children under their parent. Cross-shard transactions and sagas are the fallback, with their price stated. | 6.8 Cross-shard operations |
| PAR-10 | Failure-domain-aware placement | A | I place the replicas of each range in distinct failure domains, at the level I must survive, usually three zones. And I spread each node's partners widely, so a failed node is rebuilt from many peers in parallel, in minutes rather than hours. | 6.9 Failure-domain-aware placement |
| PAR-11 | Multi-tenant partitioning | B | For tenants I choose between pooled, siloed and shuffle-sharded. Shuffle sharding gives each tenant a random few nodes out of many, so a bad tenant fully overlaps almost nobody, at close to the cost of a pool. The largest tenants may still get a silo. | 6.10 Multi-tenant partitioning |
| DS-11 | ID schemes | A | For identifiers I use time, worker and sequence in sixty-four bits, or a time-ordered UUID: unique, roughly ordered, no coordination per insert. I lease the worker identifier, refuse to run when the clock steps back, and never make a time-ordered identifier the leading key of a range-partitioned table. | 6.11 ID schemes |

## Figures

![Range keeps neighbours together; hash scatters them](diagrams/video-p6-hash-range.pdf){width=100%}

![Hash modulo N moves almost everything when N changes](diagrams/video-p6-mod-n.pdf){width=100%}

![A ring of hash space; each node owns the arc before it](diagrams/video-p6-ring.pdf){width=100%}

![A range splits at its middle key when it grows too big or too busy](diagrams/video-p6-split.pdf){width=100%}

![Copy, catch up, switch, clean up](diagrams/video-p6-move.pdf){width=100%}

![Three places the shard map can live](diagrams/video-p6-routing.pdf){width=100%}

![Index local to each shard, or partitioned by the indexed value](diagrams/video-p6-indexes.pdf){width=100%}

![Three replicas, one rack](diagrams/video-p6-domains.pdf){width=100%}

## Traps and easy confusions

**Trap · Timestamps as keys, and one shard taking every write.** An event store is range-partitioned by key, and the key is the event's timestamp. Twenty shards, nicely balanced on old data. Every new event has the latest timestamp, so every write lands on the **last range**. One shard at 100%, nineteen idle. Adding shards changes nothing: the newest range is still one range.

**Easy to confuse · When range wins, and what it costs.** Range wins when the main query is a **scan**: time series per device, alphabetical listings, a key prefix. It costs **hot-spot management**: automatic splitting by load, and a key design that does not start with time. Hash wins for **point reads and writes** at even load, and costs every range query a scatter-gather.

**Trap · "Paginate a range scan across hash shards.".** Each shard returns its next page **in key order**; the router **merges** them and keeps a cursor per shard. The cursor the client gets encodes **every shard's position**, not one offset. Cost: every page asks every shard. If that is the common query, the partition key is wrong.

**Trap · "Grow from 20 to 40 nodes. What moves, how fast, and the cache?".** **Half** of all keys move: each new node takes its share from the old ones. At 10 TB total and 50 MB a second of throttled copy per new node: 5 TB over 20 receivers is 250 GB each, **about 1.4 hours**. The cache for half the keys is **cold**. Grow in steps of a few nodes, and warm before you switch.

**Easy to confuse · The one moment of unavailability, and the throttle.** Writes to the range pause **only during the switch**: drain the last writes and commit the new map version. Typically **tens to a few hundred milliseconds**. If the store is replicated by consensus, a move is instead a **membership change**: add a learner, catch up, transfer leadership, remove the old replica (part 3). No pause beyond a leadership transfer. The copy is throttled; too fast and the move itself is the outage.

**Easy to confuse · What splitting a key costs.** Reads now fan out to **N sub-keys**: with N = 16, one read becomes 16. Do it only for detected hot keys. A split counter is **not linearizable** for a read-then-check, such as "stop at 100 units". That needs escrow (part 8). Caching a hot key makes it **stale by the cache TTL**; say the bound.

**Easy to confuse · Global indexes are usually asynchronous.** Updating a global index **in the same transaction** needs a cross-shard commit (part 8) on every write. So most stores update it **asynchronously**: a read just after a write may not find the product by colour. Say which index the query uses, and how stale it may be.

**Easy to confuse · What spreading costs.** Spreading across **zones** adds cross-zone latency to every quorum write (about 1 to 2 ms) and cross-zone network charges. Spreading **partners** widely means a correlated failure of **any three nodes** loses some range. Narrow partner sets (copysets) make that rarer and repair slower. It is a real trade: frequency of loss against size of loss and repair time.

**Trap · An auto-increment ID on a sharded store.** One database sequence hands out IDs for every shard: **a single point of coordination** on every insert. Use a sequence per shard instead, and IDs collide across shards. Use random 128-bit UUIDs, and inserts scatter across a B-tree index: page splits, cache misses, no order by time.

**Easy to confuse · Time-ordered IDs and range partitions.** A time-ordered ID as the leading key of a **range-partitioned** table is the opening story again: every insert goes to the last range. Fix: lead the key with something spread out (the tenant, or a hash), or **reverse the bits** of the sequence, or use hash partitioning. B-tree **locality** is good for a single database; for a range-sharded one it is a hot spot.

## Probe drills

**1. Grow from 20 to 40 nodes. What moves, and how fast?**

- **Half** the data moves: the new nodes must end up with half
- 10 TB total, 5 TB moved, 250 GB per new node at 50 MB/s: **about 1.4 h**
- Caches for half the keys go cold: grow in steps, warm first

> Half the data moves, because twenty new nodes must end up holding half of it. With ten terabytes in total, five terabytes move, about two hundred and fifty gigabytes to each new node. Throttled at fifty megabytes a second, that is under an hour and a half in parallel. And half the keys change owner, so any per-node cache misses on them. I would add nodes in a few steps, warming each before switching traffic.

**2. One partition takes a fifth of all traffic.**

- Is it **one key** or **many keys** in one range?
- Many keys: **split** the range and move a half
- One key: **cache, split, salt or limit** by traffic type

> First I find out whether it is one key or many keys in one range. If many keys, I split the range by load and move one half to another node. If it is one key, splitting ranges cannot help. Then I match the traffic: reads get a per-key cache or replicas, commutative writes get split into sub-keys, a timeline gets salted by time bucket, and abuse gets rate limited.

**3. Paginate a range scan across shards.**

- Each shard returns its next page **in order**; the router **merges**
- The cursor holds **one position per shard**
- If this is the common query, the partition key is wrong

> Each shard returns its next page in key order, and the router merges them, keeping one position per shard. The cursor handed to the client encodes all of those positions, so the next page resumes on every shard exactly where it stopped. Every page touches every shard, though. If this is the main query, I would rather partition by range on that key, or keep a derived table that is.

**4. Two clients disagree about the topology. What happens?**

- Each request carries the **map version** or expected range
- The server **checks ownership** and redirects the stale one
- Neither can write to a range its target does not own

> Nothing bad, if the server checks. Each request carries the map version, or the range it expects. A server that does not own the key under the current map answers with a redirect or a stale-version error, the client updates that range and retries. So the stale client pays one extra round trip, and neither client can write somewhere the data does not live.

**5. Your ID is time first. Is that a problem?**

- On **one database**: no, inserts stay at the right edge of the index
- On a **range-partitioned** store: every insert hits the last range
- Fix: lead with tenant or hash, or hash-partition

> On a single database, no. Inserts land at the right edge of the index, which stays in memory. On a range-partitioned store it is the opening story: every insert goes to the last range, one shard takes all writes. I would lead the key with something that spreads, the tenant or a hash of the entity, and keep the time-ordered part second.

# Part 7 · Storage engines and blob storage

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 3.
- The chapter's build-up from an append-only file, and the basics of B-trees, stay in the chapter. This part goes to the trace, the arithmetic and the failure cases.

**Read next.**

- Chang et al., *Bigtable*: memtables, SSTables, compactions and Bloom filters in production.
- Ghemawat et al., *The Google File System*, and the Colossus posts on the Google Cloud blog.
- Huang et al., *Erasure Coding in Windows Azure Storage*: local reconstruction codes.
- *Designing Data-Intensive Applications*, chapter 7, on implementing snapshot isolation. *Site Reliability Engineering*, chapter 26.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| STO-01 | Write-ahead log and fsync | A | A write is durable only when its log record has been fsynced, on enough nodes to survive what I promised to survive. The log is sequential, and group commit lets many writers share one sync, so durability costs latency, not throughput. | 7.1 Write-ahead log and fsync |
| STO-02 | B-tree engines | B | A B-tree keeps sorted pages and updates them in place, with the change logged first and the page written back at a checkpoint. Point reads and range scans are cheap. Its weakness is random writes, once the working set no longer fits in memory. | 7.2 B-tree engines |
| DS-07 | Skip list / sorted set | B | A skip list is a sorted linked list with randomly chosen express lanes. Search and insert take log time, inserts are local and easy to make concurrent, and iteration is in order. That is why it is the memtable of an LSM tree, and the core of a sorted set. | 7.3 Skip lists |
| STO-03 | LSM-tree engines | A | An LSM tree makes every write a log append plus a memory insert. Sorted immutable tables are flushed and merged in the background. Writes are sequential and cheap, and the price is compaction: levelled compaction rewrites each byte ten to thirty times, and that competes with reads. | 7.4 LSM-tree engines |
| STO-04 | LSM read path | B | An LSM point read goes from the memtable down through the tables, newest first, and Bloom filters skip almost every table that cannot hold the key. So a read costs about one disk read, as long as filters and sparse indexes fit in memory, which I size: about ten bits a key, plus one index entry per block. | 7.5 The LSM read path |
| DS-01 | Bloom / cuckoo filter | A | A Bloom filter answers definitely not, or maybe. With about ten bits per key and seven hashes I get about one percent false positives, and each extra five bits per key cuts that by ten. It cannot delete. When I need deletes, a cuckoo filter. | 7.6 Bloom and cuckoo filters |
| STO-05 | Multi-version storage (MVCC) | B | With multi-version storage, every write adds a version stamped with its timestamp, and each reader sees the newest version at or below its snapshot, with no locks. Versions are collected only below the oldest open snapshot, so I bound transaction age. | 7.7 Multi-version storage |
| STO-14 | Choosing a data model | A | I choose the data model from the access patterns, each written down with its key, rate, result size and freshness. I keep one system of record, add derived stores only for patterns it cannot serve, and say the number at which the first store stops being enough. | 7.8 Choosing a data model |
| STO-15 | Indexing basics | A | A composite index serves queries on a prefix of its columns, in order, and a covering index answers without touching the table. Every index is one more write on every insert, so I add one only for a query that needs it at a rate that matters. | 7.9 Indexing basics |
| STO-08 | Blob layout | B | A blob store is two systems: a strongly consistent metadata store mapping names to chunk lists, and immutable chunks spread over many servers. Chunks are written first and the metadata row last, so an object becomes visible atomically, all of it or none. | 7.10 Blob layout |
| STO-09 | Erasure coding | B | Erasure coding with Reed-Solomon six and three stores one and a half times the data and survives any three lost fragments, against three times for replicas. The cost is repair: rebuilding one fragment reads six, so after a rack loss the repair traffic is six times the data lost. Local reconstruction codes cut that. | 7.11 Erasure coding |
| STO-10 | Integrity | B | I protect integrity end to end: a checksum computed by the client, verified at every hop and on every read, per block, plus a scrubber that reads every byte on a fixed schedule, so silent corruption is found while other copies still exist. | 7.12 Integrity |
| STO-11 | Repair and reconstruction | B | Repair is prioritised by how close each stripe is to data loss. Stripes one failure away from loss go first, at full speed. Stripes that are still safe wait a short delay, because most failures are reboots, and are then repaired under a throttle. | 7.13 Repair and reconstruction |
| STO-13 | Garbage collection of orphans | B | Orphaned chunks are found by comparing what the chunk servers hold with what metadata references, and deleted only when older than a grace period that covers any upload still in flight. So space after a delete comes back in days. | 7.14 Garbage collection of orphans |
| STO-16 | Backups and snapshots | B | Backups are a full snapshot, incrementals, and an archived log for point-in-time recovery, because replicas copy mistakes. I size the restore time against the recovery objective, test restores on a schedule, and keep one copy out of reach of the same credentials. | 7.15 Backups and snapshots |

## Figures

![Where a write actually is, at each moment](diagrams/video-p7-write-path.pdf){width=100%}

![Update a page in place, log it first](diagrams/video-p7-btree.pdf){width=100%}

![A sorted linked list with express lanes](diagrams/video-p7-skiplist.pdf){width=100%}

![A B-tree at a hundred thousand random writes a second](diagrams/video-p7-random-writes.pdf){width=100%}

![The write path: log, memtable, flush, levels](diagrams/video-p7-lsm-write.pdf){width=100%}

![A point read, newest first](diagrams/video-p7-lsm-read.pdf){width=100%}

![Looking for a key that is not there](diagrams/video-p7-bloom.pdf){width=100%}

![Every write adds a version; a reader picks by its snapshot](diagrams/video-p7-mvcc.pdf){width=100%}

![Metadata in one place, immutable chunks in another](diagrams/video-p7-blob-layout.pdf){width=100%}

![Reed–Solomon (6, 3): six data fragments, three parity, any six rebuild the rest](diagrams/video-p7-rs63.pdf){width=100%}

![Chunks with no metadata row, and a grace period](diagrams/video-p7-orphans.pdf){width=100%}

## Traps and easy confusions

**Trap · "Durable", acknowledged before the log reached the disk.** A service acknowledges each write after `write()` returns. The data is in the operating system's page cache, not on the disk. A power cut. Ten seconds of acknowledged writes are gone, on every replica in the same rack at once. Nothing in the code was wrong except the meaning of the word "written".

**Trap · "Your disk says fsync took 0.01 ms.".** Then something is **lying**: a drive write cache without power-loss protection, or a virtual disk that acknowledges from memory. Ask what the device guarantees. Test it: pull the power under load, and count what is lost.

**Trap · "p99 read latency spikes during compaction. What do you do?".** **Throttle compaction** I/O to a rate, and accept more tables per read and more space for a while. Give compaction its own **priority class** on the device; keep foreground reads ahead. If compaction cannot keep up at all, the engine **stalls writes**. The real fix is capacity, or size-tiered compaction for this workload.

**Easy to confuse · Where else the filter earns its memory.** **A cache in front of a database**: keep keys that **cannot exist** from reaching it (part 9). **A crawler**: "seen this URL?" for billions of URLs, accepting a few skipped pages. **A join**: send a filter of one side's keys to the other side, and ship only rows that may match. Its price is a known, tunable rate of **false maybes**, never a false no.

**Easy to confuse · Old versions, and the transaction that holds them.** A version can be deleted only when **no active snapshot** can still see it: below the **oldest running transaction**. One analytics query open for six hours keeps **six hours** of versions of every changed row. Tables bloat, scans slow down. Bound transaction age, and run long reads against a replica or a snapshot copy.

**Easy to confuse · One store for everything, or several.** **One relational store** is the right first answer far more often than it sounds: it scales to tens of thousands of writes a second and terabytes. **Several stores** each fit one pattern, and each adds a copy to keep consistent, a schema to evolve, and an on-call surface. Say what would make you add the second store: a number.

**Easy to confuse · Index, denormalise, or derive.** **Another index**: cheapest for a query on the same store; costs every write. **A denormalised column** or summary row: one read, and a second write you must keep consistent. **A derived store** fed by change data capture: no cost on the write path; reads are stale by the lag.

**Easy to confuse · What scrubbing costs, and why the schedule is a durability number.** A 20 PB cluster scrubbed every 14 days reads about **17 GB a second**, continuously. That is real disk time, throttled below foreground load. The scrub interval is how long a silent corruption can sit next to a failure: it enters the durability arithmetic of part 1.

**Easy to confuse · So space is freed late, by design.** After a delete, space returns only after **the grace period plus the next collection run**: days, not seconds. The listing of chunks and of metadata must be taken carefully: a chunk listed before its metadata commits must not look orphaned. The grace period covers that race.

**Trap · A backup that has never been restored is a hope.** **Restore time** is the real number: 50 TB at 500 MB a second is **28 hours**. Is that within the recovery time objective? Test restores on a schedule, into a scratch environment, and verify the data, not only that the job finished. Keep at least one copy where the same credentials, and the same bug, cannot delete it.

## Probe drills

**1. p99 read latency spikes during compaction. What do you throttle?**

- **Compaction I/O**, to a rate, with lower device priority
- Give up: **more tables per read** and **more space** while it lags
- If it cannot keep up, writes stall: add capacity or change compaction style

> I throttle compaction's I/O to a byte rate and give it lower priority than foreground reads. What I give up is read amplification and space for a while: more tables per read, more old versions on disk. If compaction can never catch up, level zero fills and the engine stalls writes, and then the fix is capacity, or a compaction style with less write amplification for this workload.

**2. How much RAM to index 1 PB of 1 KB records?**

- 10^12 records; filters at 10 bits a key: **1.25 TB**
- Sparse index, 16 KB blocks, 32 B an entry: **2 TB**
- About **3.2 TB** across the cluster; per node with 500 nodes, about **6.5 GB**

> A petabyte of one kilobyte records is a trillion records. Bloom filters at ten bits a key are ten trillion bits, one and a quarter terabytes. A sparse index with one thirty-two byte entry per sixteen kilobyte block is two terabytes. So about three and a quarter terabytes of memory across the cluster, or about six and a half gigabytes per node on five hundred nodes. Comfortable, and it keeps every read to about one disk read.

**3. A rack dies. Walk me through the next hour.**

- Stripes **one loss from data loss** repaired first, at full speed
- Safe stripes wait a short delay, since most failures are reboots
- Then throttled repair from many sources; RS (6, 3) reads six times the lost data

> First, the system finds stripes that are now one loss away from losing data and repairs them at full speed. Stripes that are still safe wait about fifteen minutes, because most failures are reboots. Then repair proceeds under a throttle, reading from many sources in parallel. With Reed-Solomon six and three, it reads six times the data lost, so a petabyte rack means about six petabytes of repair reads, roughly half a day.

**4. After a delete, when is the space actually free?**

- The metadata row goes **at once**; the object is invisible
- Chunks become **orphans**, deleted after the **grace period** plus the next run
- In an LSM store, the tombstone must reach the bottom level first

> The metadata row is removed at once, so the object is invisible immediately. Its chunks become orphans, and the collector deletes them only after the grace period, plus however long until its next run, so days. In an LSM-based store the same holds for a deleted key: its tombstone must be compacted down to the bottom level before the old value's space is reclaimed.

**5. Your write is acknowledged in 0.2 ms. Is it durable?**

- Ask **where it is**: page cache, device cache, or fsynced
- 0.2 ms is plausible for **NVMe with power-loss protection**, not for network disks
- Durable against what: one node, a rack, a zone?

> I would ask where the write is at that moment. Two tenths of a millisecond is plausible for an fsync on local NVMe with power-loss protection, and implausible on network block storage, where a sync is about a millisecond. And durable against what? One node's power loss, or a rack, or a zone? That decides whether one local sync is enough or I need a quorum.

# Part 8 · Transactions and concurrency control

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 7.
- The chapter's taxonomy of isolation levels and the history of their names stay there. This part does the traces and the choices.
- Part 2 of this course: idempotency and exactly-once, with the deduplication sequence. Part 7: multi-version storage.

**Read next.**

- *Designing Data-Intensive Applications*, chapter 9 (atomic commit and two-phase commit) and chapter 12 (end-to-end request IDs).
- Corbett et al., *Spanner*: two-phase commit over Paxos groups, and commit wait.
- Garcia-Molina and Salem, *Sagas*. Helland, *Life beyond Distributed Transactions*.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| TXN-01 | Isolation levels and anomalies | A | I name the anomaly my design must rule out, then the cheapest mechanism that does. An atomic update or a version check for lost updates. A lock on the rows the decision read, or serializable isolation, for write skew. And I say what the database's default level actually permits, because it is usually weaker than its name. | 8.1 Isolation levels and anomalies |
| TXN-02 | Optimistic concurrency / conditional writes | A | Optimistic concurrency writes on condition that the version has not changed, checked atomically by the store. It is the right default when conflicts are rare. Under heavy contention its retries grow quadratically, and then I use an atomic conditional statement, or a lock. | 8.2 Optimistic concurrency and conditional writes |
| TXN-03 | Pessimistic locking | A | Pessimistic locking locks the rows a decision reads, until commit. I lock in one global order to avoid deadlock, set a lock timeout, never hold a lock across a network call, and remember that one hot row can take at most one over the lock hold time per second. | 8.3 Pessimistic locking |
| TXN-04 | Snapshot reads | B | Read-only work runs as a snapshot read at one timestamp: consistent across every shard, no locks, after waiting for each shard's safe time. For read-write work, snapshot isolation stops lost updates, and serializable snapshot isolation also catches write skew, by aborting one of the two. | 8.4 Snapshot reads |
| TXN-05 | Two-phase commit | A | Two-phase commit has participants prepare durably and vote, and the coordinator's logged decision is the commit point. Its weakness is that a prepared participant cannot decide alone, so if the coordinator dies after prepare, locks are held until it returns. I avoid it by co-locating data, or I run it over consensus groups. | 8.5 Two-phase commit |
| TXN-06 | Two-phase commit over consensus groups | B | Running two-phase commit where every participant and the coordinator is a consensus group removes the single point of blocking. A new coordinator leader reads the decision from its log. The price is two consensus rounds per commit, across regions if the groups span them. | 8.6 Two-phase commit over consensus groups |
| TXN-08 | Sagas | A | Across services I use a saga: a sequence of local steps, each with an idempotent compensation, run by an orchestrator that records its progress durably. It has no isolation, so I design the visible pending state, put irreversible steps last, and retry compensations until they succeed. | 8.7 Sagas |
| TXN-09 | Idempotency keys and dedup tables | A | An idempotency key is claimed with a unique insert before any work starts, so a concurrent duplicate sees in progress and does not repeat the effect. The response is stored in the same transaction as the effect and replayed on retry. I keep keys longer than the longest client retry, and pass the key to any downstream provider. | 8.8 Idempotency keys and dedup tables |
| TXN-10 | Reservation pattern | A | For anything scarce across two systems I use a reservation. A conditional write creates a hold with an expiry. The payment uses the hold as its idempotency key. The confirm is conditional on the hold still being mine, and if it is not, the system refunds automatically. Expired holds release themselves. | 8.9 The reservation pattern |
| TXN-12 | Escrow / split counters | B | For a hot global limit I use escrow: the budget is split into allowances that each shard spends locally, and a central ledger refills them without ever granting more than remains. Near the end I shrink the allowances and route the last units centrally. | 8.10 Escrow and split counters |

## Figures

![Lost update: two read-modify-writes on one counter](diagrams/video-p8-lost-update.pdf){width=100%}

![Two editors, one document, the second save wins silently](diagrams/video-p8-two-editors.pdf){width=100%}

![Two transactions, two rows, opposite order](diagrams/video-p8-deadlock.pdf){width=100%}

![Money leaves one shard and never arrives at the other](diagrams/video-p8-partial-commit.pdf){width=100%}

![Prepare, vote, decide, commit](diagrams/video-p8-2pc.pdf){width=100%}

![The coordinator dies after prepare](diagrams/video-p8-2pc-blocked.pdf){width=100%}

![Every participant and the coordinator is a replicated group](diagrams/video-p8-2pc-paxos.pdf){width=100%}

![Three services, no shared transaction, and a failure halfway](diagrams/video-p8-saga-fail.pdf){width=100%}

![Steps, each with a compensation, run by an orchestrator](diagrams/video-p8-saga.pdf){width=100%}

![The double-click: the second request arrives during the first](diagrams/video-p8-double-click.pdf){width=100%}

![Charge first or reserve first, and both are wrong without a hold](diagrams/video-p8-oversell.pdf){width=100%}

![Hold with an expiry, then confirm or cancel](diagrams/video-p8-reservation.pdf){width=100%}

![A budget split into per-shard allowances](diagrams/video-p8-escrow.pdf){width=100%}

## Traps and easy confusions

**Trap · Two doctors both go off call. Each checked first..** A hospital rule: at least one doctor must be on call. Alice and Bob are both on call, and both feel unwell. Each opens the app at the same moment. Each transaction checks: "is anyone else on call?" Yes, one other. Each sets itself off call, and commits. Both transactions were correct on their own. Now nobody is on call. The database raised no error.

**Trap · "Fix the doctors.".** **Option 1**: `SELECT … FROM doctors WHERE on_call AND shift = 7 FOR UPDATE`. Both transactions lock the same rows; the second waits, re-reads, sees one doctor, and refuses. **Option 2**: run at **serializable**; one of the two aborts, and its retry refuses. **Option 3**: a constraint the database checks, if it can express "at least one".

**Easy to confuse · Snapshot isolation, and making it serializable.** Snapshot isolation for **read-write** transactions: read at the start timestamp, and abort if another transaction **wrote the same row** first. Lost updates: gone. Write skew: still possible. **Serializable snapshot isolation** also tracks what each transaction **read**, and aborts one of two transactions where each read what the other wrote: the doctors. Price: more aborts under contention; no blocking.

**Easy to confuse · Two consensus writes, plus the commit wait.** Latency: a consensus round on every participant to prepare, then one on the coordinator to commit. Within a region, a few milliseconds; across regions, two cross-region rounds. Spanner adds a **commit wait** for its timestamp (part 2). Blocking is still possible, but only when a **majority** of a group is lost.

**Easy to confuse · How long to remember a key.** Keep keys **longer than any client retries**: if clients retry for up to 24 hours, keep them for more than 24. Storage: 10 million payments a day x 1 KB per key x 1 day = **10 GB**. Cheap. An **in-progress** row left by a crashed worker needs a timeout and a recovery path that **checks the effect** before retrying.

**Easy to confuse · Stranded budget, and the end game.** Near the end, units are **stranded**: one shard has 40 left that it cannot use, another is refused. Fix: as the remainder falls, **shrink the allowances**, and finally route the last units through the central ledger. Lowering the limit while allowances are out is bounded by **what has already been granted**. Part 12 uses the same arithmetic for leased rate-limit capacity.

## Probe drills

**1. The user double-clicks Pay. The second request arrives during the first.**

- Both carry the **same idempotency key**
- The first **inserts the key** as in progress; the second's insert fails on the unique key
- The second gets **409**, or waits and receives the stored response

> Both requests carry the same idempotency key, generated by the client when the page loaded. The first inserts the key with state in progress. The second's insert fails on the unique constraint, so it never starts the charge. It either answers conflict, or waits briefly and then returns the first request's stored response. The card is charged once, and I also pass the key to the payment provider so it deduplicates too.

**2. Payment succeeds after the hold expired.**

- The confirm is **conditional** on the hold; it changes **zero rows**
- So the system **refunds automatically**, idempotently, and tells the user
- Make it rare: holds longer than authorisation, **extended** when payment starts

> The confirm only succeeds if the seat is still held by this hold. If the hold expired and the seat was resold, it changes nothing, and the system refunds the payment automatically, keyed by the hold so the refund happens once, and tells the user. To make it rare, the hold is longer than the slowest payment authorisation and is extended when payment begins.

**3. A hundred parallel requests target the last unit.**

- One atomic **conditional decrement**: stock above zero
- Exactly one succeeds; ninety-nine get zero rows and a sold-out answer
- No read-modify-write, no retries, no application lock

> I make it one statement: decrement where stock is greater than zero. The database applies those one at a time under the row lock, held for microseconds. Exactly one request changes a row, and ninety-nine change nothing and get a sold-out answer. No read in the application followed by a write, which would lose updates, and no optimistic retry storm.

**4. Name the anomaly your design must rule out, and the cheapest level that rules it out.**

- For "at least one on call": **write skew**
- Snapshot isolation does **not** rule it out
- Lock the rows read with **FOR UPDATE**, or run that one transaction **serializable**

> For a rule like at least one doctor on call, the anomaly is write skew: two transactions read the same facts and update different rows. Snapshot isolation does not prevent it. The cheapest fixes are to lock the rows the decision read, with select for update, or to run just that transaction at serializable and retry on abort. Everything else can stay at the default level.

**5. The coordinator dies after prepare. What happens to the participants?**

- They are **in doubt**: they cannot commit or abort alone
- They **hold locks** until the coordinator, or its log, returns
- Fix: run the coordinator as a **consensus group**, so a new leader reads the decision

> The participants are in doubt. They promised to commit if told to, so they cannot abort, and they do not know the decision, so they cannot commit. They hold their locks until the coordinator recovers and tells them. Everything touching those rows waits. The fix is to make the coordinator a consensus group, so a new leader reads the decision from the replicated log and completes it.

# Part 9 · Caching

**Assumed reading.**

- Nishtala et al., *Scaling Memcache at Facebook*, **section 3**: leases, pools, gutter servers.
- The paper's regional and cross-region story stays in the paper. This part does the mechanisms on one key, with the arithmetic.

**Read next.**

- Nishtala et al., *Scaling Memcache at Facebook*, after section 3: regions and consistency across them.
- *Designing Data-Intensive Applications*, chapter 5 (reading your own writes) and chapter 11 (keeping derived data in sync from a change stream).
- Einziger, Friedman and Manes, *TinyLFU: A Highly Efficient Cache Admission Policy*.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| CAC-01 | Caching patterns | A | My default is cache-aside: read the cache, on a miss load from the store and add with a time to live, and on a write update the store and delete the key, never set it. Write-through when the cache must be current. Write-behind only for data I can afford to lose, with the window said aloud. | 9.1 Caching patterns |
| CAC-10 | Hit-ratio maths | A | I size the database from the miss ratio, not the hit ratio. Backend load is misses times traffic, so a fall from ninety-nine to ninety percent hits is ten times the load. If the database cannot take the miss rate a failure would cause, the cache is load-bearing, and I design and alert for that. | 9.2 Hit-ratio maths |
| CAC-02 | Eviction policies | A | Least recently used adapts fast and is flushed by a single scan. I add frequency-based admission, a small Count-Min Sketch with decay, so a new key only evicts a less popular one. And I choose the policy by replaying a real trace at several cache sizes, not by opinion. | 9.3 Eviction policies |
| CAC-03 | Expiry | A | Every time to live gets random jitter, so keys loaded together do not expire together. I choose the TTL per type of data as the worst-case staleness I can accept if invalidation fails, and I remember it sets a floor of one miss per hot key per TTL. | 9.4 Expiry |
| CAC-04 | Invalidation | A | I state the staleness I guarantee, with the mechanism behind it. Invalidation from the database's change stream bounds staleness by the stream's lag and survives writer crashes. A writer deleting after commit is usually fresh, with the time to live as the backstop. And the TTL alone is the worst case. | 9.5 Invalidation |
| CAC-06 | Stale-set race and leases | B | The stale-set race lets a slow reader write an old value after the invalidation. Leases fix it: the cache hands a token with each miss, a delete voids outstanding tokens, and a set is accepted only with a valid token. The same lease also limits how many readers load a key at once. | 9.6 The stale-set race and leases |
| CAC-05 | Stampede control | A | On a hot key's expiry, I make sure there is one rebuild, not thousands. Single flight inside each process, a lease across processes for the hottest keys, probabilistic early refresh so the rebuild happens before expiry, or serving the stale value briefly while one refresh runs. | 9.7 Stampede control |
| CAC-07 | Hot keys and big values | B | A single hot key beyond one node's capacity gets a short-lived in-process copy, or replicas under suffixes read at random. A big value gets split, compressed, or replaced by the smaller projection the reader needs, because the network card saturates before the processor. | 9.8 Hot keys and big values |
| CAC-08 | Multi-tier caching | B | I stack an in-process tier for the hottest keys, with a time to live of seconds because it is hard to invalidate, over a remote cache for the working set, over the store. Each tier's hit ratio multiplies down the load on the next. | 9.9 Multi-tier caching |
| CAC-09 | Negative caching and penetration | B | Keys that do not exist go straight through a cache. I cache not found with a short time to live, cleared on create, and put a Bloom filter of existing keys in front, so random lookups are refused before they reach the database. | 9.10 Negative caching and penetration |
| CAC-11 | Cold start and node loss | B | An empty cache is a database outage waiting to happen. I warm a cold tier from a warm peer, cover a lost node with a small gutter pool rather than rehashing its keys onto live nodes, and keep an admission limit in front of the database so it never sees the full miss rate. | 9.11 Cold start and node loss |

## Figures

![The backend load curve as the hit ratio falls](diagrams/video-p9-hit-curve.pdf){width=100%}

![Ten thousand keys set at the same second expire at the same second](diagrams/video-p9-ttl-sync.pdf){width=100%}

![The writer committed, then crashed before deleting the key](diagrams/video-p9-lost-invalidation.pdf){width=100%}

![A slow reader writes an old value after the delete](diagrams/video-p9-stale-set.pdf){width=100%}

![A lease token on a miss; a delete invalidates it](diagrams/video-p9-lease.pdf){width=100%}

![In-process first, then remote, then the store](diagrams/video-p9-tiers.pdf){width=100%}

![Keys that do not exist go straight through the cache](diagrams/video-p9-penetration.pdf){width=100%}

## Traps and easy confusions

**Trap · The cache restarts cold at peak, and the database follows it down.** A cache tier serves 99% of a million reads a second. The database sees ten thousand, and is sized for twenty. A bad deploy restarts every cache node at noon. The hit ratio drops to zero. The database receives a **million** reads a second, falls over, and the cache cannot refill from a database that is down.

**Easy to confuse · Which pattern, when.** **Cache-aside** for most reads: simple, the cache can fail without data loss. **Write-through** when reads right after writes dominate and the cache must be current. **Write-behind** only for data you can lose or rebuild: counters, view tallies, with a stated loss window. **Refresh-ahead** for a small set of very hot keys whose miss would hurt.

**Easy to confuse · Buy hit ratio with memory, or protect the database another way.** More memory moves along a curve of **diminishing returns**: doubling the cache might take 95% to 97%. Sometimes cheaper: **size the database for the miss rate you will actually see in a failure**, or add a load-shedding limit in front of it (part 12). Treat the cache as **load-bearing**: alert on hit ratio per family, and on database load per hit-ratio point.

**Easy to confuse · How to choose, and measure, for your workload.** **Replay a trace**: record a day of key requests, run it through simulators of each policy at several cache sizes, and plot hit ratio against size. In production, a **shadow** policy can track keys it would hold, without serving, and report its hit ratio. The price of a smarter policy: a few bytes per key for the sketch, and CPU per request.

**Easy to confuse · Long TTL with invalidation, or short TTL alone.** **Short TTL alone**: simple, bounded staleness; a floor of misses, and stale reads up to the TTL. **Long TTL with invalidation**: fewer misses, usually fresh; the TTL only covers lost invalidations, and the invalidation path must be built and monitored.

**Easy to confuse · What the change stream costs.** A log consumer to run, monitor and scale: its **lag is now your staleness**, so alert on it. The consumer must map a row change to **every cache key derived from it**: a product row feeds a product page, a search result and a category list. That mapping is the hard part, and the usual source of "we invalidated the wrong key".

**Easy to confuse · What each defence costs.** **Single-flight** per process still sends one load per **process**: a thousand servers, a thousand loads. Use it, and add a lease or a lock across servers for the hottest keys. **Stale-while-revalidate** serves data past its TTL: say by how much. **Early refresh** does a little extra work on hot keys, all the time.

**Easy to confuse · The in-process tier is the hard one to invalidate.** There may be **a thousand** in-process caches. A delete must reach all of them, by broadcast, or not at all. So give it a **short TTL**, seconds, and accept that staleness; or subscribe each process to an invalidation channel and accept a fan-out on every write. Never put per-user, must-be-fresh data in the in-process tier.

**Easy to confuse · A short TTL, and a filter to keep current.** A negative entry must be **short-lived**, and deleted when the key is created, or a new product is invisible for its TTL. Random keys defeat negative caching (each is new), so the **filter** is what stops an attack. It must be rebuilt or updated as keys are created.

## Probe drills

**1. State the staleness you guarantee.**

- Normally: the **change stream's lag**, under a second
- If the stream stalls: the **TTL**, here five minutes, as the hard bound
- For the user's own writes: read from the store, or carry a version

> Normally the staleness is the lag of the change stream that drives invalidation, under a second, and I alert when that lag rises. If the stream stalls completely, the time to live is the hard bound, here five minutes. And for a user's own writes, where they will notice, the read after a write goes to the store or carries the version it must see.

**2. And what breaks it?**

- The **stale-set race**, unless sets carry a lease token
- A **wrong key mapping**: the row changed, a different derived key was cached
- The **in-process tier**, which only the TTL covers

> Three things. The stale-set race, where a slow reader writes an old value after the delete, unless sets require a lease token. A wrong mapping from rows to keys, where the row changed and a derived key nobody listed stays stale until its time to live. And the in-process tier, which invalidation may not reach, so only its own short time to live bounds it.

**3. One key takes 500,000 requests a second.**

- Beyond one node: **local copies** for a few seconds on each app server
- Or **replicas** under suffixes, read at random
- Detect it with a **sketch** first; and fix the stampede on its expiry

> That is beyond one cache node, so I spread it. Each application server keeps a local copy for a second or two, which removes almost all the remote load at a staleness of seconds. Or I store it under sixteen suffixes on different nodes and read one at random. I detect such keys with a frequency sketch rather than guessing, and I make sure its expiry triggers one rebuild, with a lease or early refresh.

**4. LRU or LFU for this workload, and how would you measure it?**

- Scans or one-off reads in the mix: **frequency-based admission** wins
- Fast-shifting popularity: **LRU** or a large window
- Measure: **replay a trace** at several sizes, or run a **shadow** policy

> If the traffic mixes popular keys with scans or one-off reads, frequency-based admission wins, because it stops one-time keys from evicting popular ones. If popularity shifts fast, recency matters more. But I would not decide by argument. I would replay a day's trace through simulators of each policy at several cache sizes and compare hit ratios, or run a shadow policy in production.

**5. The cache tier restarts at peak. What happens?**

- Hit ratio near **zero**: the database sees the **full read rate**
- Defence: **warm from a peer**, admission limit on the database, staggered restarts
- Design: say the cache is **load-bearing**, and size or protect for it

> The hit ratio goes to nearly zero, so the database sees the full read rate, likely many times its capacity. The defences: restart nodes in stages, never all at once; warm a cold tier from a warm peer; and keep an admission limit in front of the database, so excess misses are shed rather than taking it down. And in the design I would say plainly that the cache is load-bearing.

# Part 10 · Logs, queues, streams and sketches

**Assumed reading.**

- *Designing Data-Intensive Applications*, chapter 11.
- Part 2 of this course: idempotency and exactly-once, ordering guarantees. Part 5: change data capture and the outbox.
- The chapter's stream joins and its survey of brokers stay there.

**Read next.**

- Akidau et al., *The Dataflow Model*: event time, windows, watermarks and triggers.
- Kreps, Narkhede and Rao, *Kafka: a Distributed Messaging System for Log Processing*, and the Kafka replication design documentation.
- *Designing Data-Intensive Applications*, chapter 4 (schema evolution). *Site Reliability Engineering*, chapter 25, *Data Processing Pipelines*. The Pub/Sub documentation.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| MSG-01 | Queue vs log | A | A queue tracks each message and deletes it once acknowledged, which suits tasks done once each. A log keeps messages for a retention period and each consumer group tracks its own offset, which suits events that several consumers need in order, and allows replay. | 10.1 Queue versus log |
| MSG-02 | Partitioned log internals | B | Each partition is an append-only sequence of segment files with a sparse index from offset to file position. Retention deletes whole segments by age or size, and a compacted topic keeps only the latest value per key, so it doubles as a table. | 10.2 Inside a partitioned log |
| MSG-03 | Log replication | B | For durability, the producer waits for all in-sync replicas with a minimum of two in sync, and consumers read only up to the high watermark. If the last in-sync replica dies, I would rather be unavailable than elect an out-of-date leader and lose acknowledged messages. | 10.3 Log replication |
| MSG-04 | Consumer groups | B | A consumer group gives each partition to one consumer, so the partition count caps parallelism and I choose it for peak. A rebalance pauses work and replays from the last committed offset, so I use cooperative rebalancing and commit often enough that the replay is small. | 10.4 Consumer groups |
| MSG-05 | Delivery semantics | A | When I say exactly once, I mean effectively once: at-least-once delivery, plus a sink that makes a duplicate harmless, either by committing the offset in the same transaction as the result, or by an upsert or a unique constraint on a stable event identifier. Broker transactions only cover topic to topic. | 10.5 Delivery semantics |
| MSG-06 | Ordering | A | A log gives order only within a partition, so I get order per key, and I choose the key as the smallest unit that needs it. I keep it across retries with an idempotent producer, never resize an ordered topic in place, and where I can, I put a version on events so consumers can ignore stale ones and need no ordering at all. | 10.6 Ordering |
| MSG-07 | Ack deadlines, redelivery, dead letters | A | Each message is leased with an acknowledgement deadline that a working consumer extends, redelivered with growing backoff, and moved to a dead-letter topic after a set number of attempts, so one poison message cannot block the rest. The dead-letter topic has an owner, an alert and a replay tool. | 10.7 Ack deadlines, redelivery, dead letters |
| MSG-08 | Backpressure and lag | A | I measure consumer lag in seconds, not messages, and alert on it. Catch-up time is the backlog divided by capacity minus the arrival rate, and the retention period is my outage budget before data is lost. For each edge I decide whether to buffer, push back, or shed. | 10.8 Backpressure and lag |
| MSG-09 | Delayed and priority delivery | B | For delayed delivery I use one topic per fixed delay, or a timer store for arbitrary times. For priority, separate queues consumed with weights, never strict priority, so the lower class is never starved. | 10.9 Delayed and priority delivery |
| MSG-10 | Fan-out | A | Fan-out on write makes reads cheap and pays per follower at post time. Fan-out on read makes posts cheap and pays on every read. I use a hybrid: push for ordinary authors, pull and merge the few huge accounts at read time, with the threshold set from the write and read arithmetic. | 10.10 Fan-out |
| MSG-11 | Event time, windows, watermarks | B | I window by event time. The watermark is the minimum progress across input partitions, and it decides when a window is emitted, so an idle partition must be detected or it stalls everything. Late events within an allowed lateness update the result, and later ones go to a side output. | 10.11 Event time, windows and watermarks |
| MSG-12 | Stateful stream processing | B | A stateful stream processor keeps keyed state locally and checkpoints it together with the input offsets. On failure it restores the checkpoint and rewinds the input, so state is exactly once, and outputs are recomputed, which the sink must make harmless. | 10.12 Stateful stream processing |
| MSG-13 | Lambda vs Kappa | B | I prefer one replayable stream path, and reprocess by running a new version of the job over the retained log beside the old one, then switching. I keep a separate batch path only when history is far bigger than any log retention. | 10.13 Lambda versus Kappa |
| MSG-15 | Schema evolution | B | Topic schemas evolve under a compatibility rule, at least backward, so consumers upgrade first. I only add optional fields with defaults, never reuse or retype a field, and a schema registry rejects any version that breaks the rule. | 10.14 Schema evolution |
| DS-02 | HyperLogLog | B | For distinct counts at scale I use HyperLogLog: about twelve kilobytes per counter for under one percent error, and sketches merge across shards and time by taking the maximum per register. | 10.15 HyperLogLog |
| DS-03 | Count-Min Sketch and heavy hitters | B | A Count-Min Sketch estimates frequencies in a few tens of kilobytes. It never underestimates and overestimates by at most epsilon times the total, with width e over epsilon and depth log of one over delta. With a small heap on top it finds heavy hitters, and sketches merge by adding counters. | 10.16 Count-Min Sketch and heavy hitters |
| DS-10 | Quantile sketches | B | For percentiles over a stream I use a mergeable quantile sketch, such as DDSketch for a relative error guarantee, or a fixed histogram with edges around the threshold. I merge sketches across hosts and never average percentiles. | 10.17 Quantile sketches |

## Figures

![Delete on acknowledgement, or keep and track a position](diagrams/video-p10-queue-log.pdf){width=100%}

![Segments, offsets, a sparse index, and retention by whole files](diagrams/video-p10-segments.pdf){width=100%}

![Followers fetch; the high watermark is what all in-sync replicas hold](diagrams/video-p10-isr.pdf){width=100%}

![Partitions are divided among the consumers of a group](diagrams/video-p10-group.pdf){width=100%}

![The duplicate dies in the sink's transaction](diagrams/video-p10-sink-txn.pdf){width=100%}

![Order lost by a retry, and by a change of partition count](diagrams/video-p10-reorder.pdf){width=100%}

![One message that always crashes the consumer](diagrams/video-p10-poison.pdf){width=100%}

![A slow consumer, and a lag nobody measured in time](diagrams/video-p10-lag.pdf){width=100%}

![Push to inboxes on write, or pull and merge on read](diagrams/video-p10-fanout.pdf){width=100%}

![Count by when it happened, not when it arrived](diagrams/video-p10-watermark.pdf){width=100%}

![Local state, checkpointed with the input offsets](diagrams/video-p10-checkpoint.pdf){width=100%}

## Traps and easy confusions

**Trap · The consumer crashed between two lines of code.** A consumer reads a batch of payments from the log, writes each one into the ledger, then commits its position. It crashes after the ledger write and before the commit. On restart it reads from the last committed position, and writes the same payments **again**. The broker did exactly what it promised.

**Easy to confuse · What a rebalance costs.** In the classic protocol, a rebalance **stops every consumer** in the group, revokes all partitions, and reassigns them. Each partition then restarts from its **last committed offset**: work since then is redone. Cooperative rebalancing moves only the partitions that change owner; static membership avoids a rebalance on a quick restart.

**Easy to confuse · Global order, or none.** **Global order**: one partition. Throughput of one consumer, no parallelism. Almost never needed. **No order**: free parallelism; consumers must tolerate reordering, with a **version** on each event and "ignore older than what I have". That last trick often removes the need for ordering at all.

**Easy to confuse · A dead-letter topic is a queue with no consumer.** Every dead letter is a **request someone did not get served**. It needs an owner, an alert on its depth, and a **replay tool** to send fixed messages back. Retries that are too fast make a dependency outage worse; retries that are too few dead-letter healthy messages during a short outage.

**Easy to confuse · Buffer, push back, or shed.** **Buffer** costs storage and **freshness**: work is late, not lost. Fine for analytics, wrong for a fraud check. **Push back** keeps the system honest and moves the problem to the caller, who must handle a rejection. **Shed** drops work deliberately, cheapest first (part 12). Say which work is cheapest.

**Easy to confuse · Starvation, and a queue that is really a timeline.** **Strict** priority starves the lower class under sustained load; weights prevent it. A delay tier with a slow consumer delivers late by the **lag**: alert on it as for any consumer.

**Easy to confuse · What each shape costs.** **On write**: storage for every inbox entry; wasted work for inactive followers; a backlog after a big post. **On read**: latency and load on every read; the merge must be fast across hundreds of sources. **Hybrid**: two code paths, and a threshold to tune; a follower of a celebrity sees their post via the merge, so the merge must be cached.

**Easy to confuse · Replay time, and the sink.** Recovery replays everything since the last checkpoint: checkpoint every **minute**, replay up to a minute, plus state restore time, which grows with state size. Inside the processor, state is exactly once. **Outputs** are recomputed, so the sink must be transactional with the checkpoint or idempotent (10.5).

**Easy to confuse · Fixed histograms, the cheap alternative.** A **fixed-bucket histogram** also merges by adding counts, and is cheapest. Its error depends on bucket edges: choose them around the SLO threshold. A sketch adapts to the data, at a few KB per series.

## Probe drills

**1. Exactly once: what do you actually mean?**

- **At-least-once delivery**, plus a sink that makes duplicates harmless
- Broker transactions cover **topic to topic** only
- External effects need **dedup at the sink**, by a stable ID

> I mean effectively once. Delivery is at least once, because a consumer can always crash between doing the work and recording that it did. Broker transactions make topic to topic processing exactly once, and nothing beyond. So for any external effect, the sink makes a repeated message harmless, by committing the offset with the result, or by an upsert or unique constraint on a stable event identifier.

**2. Show me where the duplicate dies.**

- In the **ledger's transaction**: payments and the offset commit together
- Or by **unique constraint** on the event ID in the ledger
- Restart reads the offset **from the sink**, not the broker

> In the ledger's own transaction. The consumer writes the batch of payments and its new offset into the same database, in one transaction. On restart it reads its offset from the ledger, not from the broker, so either the payments and the offset are both there, or neither is. As a second guard, the ledger has a unique constraint on the event identifier, so even a bug in offset handling cannot post a payment twice.

**3. One key is ten percent of all events.**

- Its partition, and its **one consumer**, carry ten percent: a hot partition
- Does it **need order**? If not, salt the key and spread it
- If it does: a faster consumer per key, or **pre-aggregate** before the ordered step

> That key's partition, and the one consumer that owns it, carry ten percent of everything, while other partitions are nearly idle. First question: does that key really need order? If not, I salt it into sub-keys and spread it over partitions. If it does, I make that one consumer faster, or I pre-aggregate the key's events upstream, so the ordered step sees far fewer of them.

**4. Events arrive two hours late.**

- Window by **event time**; the watermark has long passed
- Within allowed lateness: **update** the result. Beyond: **side output**
- Two hours is a product decision: correct later, or count in the arrival window

> I window by event time, so these belong to windows the watermark closed long ago. If two hours is within the allowed lateness, the result for those windows is updated and re-emitted, and downstream must accept updates. If not, they go to a side output, and a correction job folds them in later. Which one is a product question: whether a late correction is worth more than a stable number.

**5. A consumer is slow. What happens upstream?**

- On a **log**: nothing until retention; lag grows, in seconds
- Catch-up is **backlog over capacity minus arrivals**
- On a bounded queue: producers are blocked or rejected: **backpressure**

> On a log, producers are unaffected, the log absorbs it, and lag grows. I alert on lag in seconds, and the retention period is my budget before data is lost. When the consumer is fixed, catch-up time is the backlog divided by its capacity minus the arrival rate. On a bounded queue, the queue fills and then producers are blocked or rejected, and that pressure travels to their callers, so I decide in advance which work to shed.

# Part 11 · Networking, the edge and API contracts

**Assumed reading.**

- *Site Reliability Engineering*, chapter 19, *Load Balancing at the Frontend*, and chapter 20, *Load Balancing in the Datacenter*.
- The chapters' account of DNS and virtual-IP balancing, subsetting and weighted round robin stays there. This part keeps one picture and the probe for each, then goes to RPC and the API contract.

**Read next.**

- Eisenbud et al., *Maglev: A Fast and Reliable Software Network Load Balancer*.
- The API Improvement Proposals at aip.dev: pagination, long-running operations, request identification, etags.
- *Designing Data-Intensive Applications*, chapter 4: the problems with remote procedure calls.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| NET-01 | DNS, GeoDNS, anycast | A | DNS failover takes at least the record's time to live, plus clients that cache longer, so records I may move get short TTLs. For fast regional failover I put an anycast front end at the edge: every site announces one address, and failover is a route withdrawal that converges in seconds. | 11.1 DNS, geo-routing and anycast |
| NET-02 | L4 vs L7 load balancing | A | A layer four balancer places connections, fast and protocol-blind; a layer seven balancer places each request and can route, retry and observe. With long-lived multiplexed connections, I balance at layer seven, or cap connection lifetime. | 11.2 L4 versus L7 load balancing |
| NET-03 | Health checks and draining | A | Health checks eject outliers, using both probes and real error rates. A planned stop fails readiness first, waits for the balancer, finishes in-flight requests, then exits. And past a panic threshold the balancer sends traffic to every backend, because a health check that fails everywhere is usually the check that is wrong. | 11.3 Health checks and draining |
| NET-04 | API gateway / reverse proxy | A | My gateway does only what every request needs: TLS, authentication, per-client limits, routing, deadlines and request identifiers. Business logic and orchestration live in services. Because every request crosses it, its config rolls out in stages and it fails static on last known good. | 11.4 The API gateway |
| NET-07 | RPC semantics | A | Between services I pass an absolute deadline and cancellation down the whole chain, so no hop starts work it cannot finish and nobody works for a caller who has gone. I retry only idempotent calls, from one layer. And a timeout means unknown, so non-idempotent calls carry an idempotency key. | 11.5 RPC semantics |
| NET-08 | Polling, long polling, SSE, WebSocket | A | I choose the transport by direction and rate. Polling only for rare updates at small scale. Server-sent events for a one-way stream such as a streamed model answer, because it is plain HTTP and resumes from the last event. WebSocket when the client sends often too. Every push transport costs a connection per online client. | 11.6 Polling, long polling, SSE and WebSocket |
| NET-09 | Persistent-connection tiers | B | A persistent-connection tier only holds sockets. Each gateway registers its users in a routing table under a lease, a dispatcher looks users up to deliver, and clients reconnect with randomised backoff so that losing a gateway does not become a handshake storm on the others. | 11.7 Persistent-connection tiers |
| API-01 | API style | A | My default is a resource model with standard methods, get, list, create, update and delete, and custom methods for actions, defined once and served over gRPC between services and HTTP at the edge. GraphQL when many screens share one graph, with query cost limits. | 11.8 API style |
| API-02 | Pagination | A | I paginate with an opaque cursor that encodes the last row's unique sort key, plus a version and the query it belongs to. It is stable under inserts and deletes and costs an index seek at any depth. Offsets only for small static lists. | 11.9 Pagination |
| API-03 | Idempotent writes | A | A create that may be retried carries an idempotency key chosen by the client once per intent and persisted with it. The server replays the stored response for any retry within the key's lifetime, answers conflict while the first is in progress, and keeps keys longer than any client can retry. | 11.10 Idempotent writes |
| API-04 | Versioning and compatibility | B | Within an API version I only make additive changes. A breaking change becomes a new major version running beside the old, with a deprecation date and per-client usage measured, so the old one can actually be turned off. | 11.11 Versioning and compatibility |
| API-05 | Long-running operations | B | For work longer than a request I return a long-running operation: a durable name the client can poll, wait on with a deadline, or cancel, created by an idempotent start call. A dropped connection or a deploy then loses nothing. | 11.12 Long-running operations |
| API-06 | Resumable and multipart upload | B | Large uploads go through a resumable session or a multipart upload. After a failure, the client asks the server how many bytes it holds and continues from there, parts expire if never completed, and the whole object's checksum is verified at the end. | 11.13 Resumable and multipart upload |
| API-07 | Conditional requests | B | Every resource carries an entity tag. Clients revalidate cheaply with if-none-match, and update safely with if-match, getting precondition failed if someone else wrote first. It is optimistic concurrency, on the wire. | 11.14 Conditional requests |
| API-08 | Error and throttling contract | A | My error contract tells clients what to do. Bad requests are never retried. Four twenty-nine means this client is over its limit, with retry-after and rate limit headers. Five oh three means the service is overloaded, retried with backoff and jitter inside a retry budget. And the body is structured, so programs can switch on the reason. | 11.15 The error and throttling contract |
| DS-05 | Trie / radix tree / FST | B | For longest-prefix match, routes, IP ranges or autocomplete, I use a trie or a radix tree: a lookup costs the length of the key, not the size of the table. When a term dictionary must be compact, a finite-state transducer shares suffixes as well as prefixes. | 11.16 Tries, radix trees and FSTs |

## Figures

![Three ways to send a user to the nearest healthy site](diagrams/video-p11-dns-anycast.pdf){width=100%}

![Packets, or requests](diagrams/video-p11-l4-l7.pdf){width=100%}

![Healthy, half alive, or dead, and the panic threshold](diagrams/video-p11-health.pdf){width=100%}

![A gateway that grew business logic](diagrams/video-p11-gateway-bloat.pdf){width=100%}

![The caller gave up; the callee did not](diagrams/video-p11-orphan-work.pdf){width=100%}

![Pass a deadline, not a timeout](diagrams/video-p11-deadline.pdf){width=100%}

![Gateways hold connections; a routing table says where each user is](diagrams/video-p11-conn-tier.pdf){width=100%}

![Offset pagination under inserts](diagrams/video-p11-offset.pdf){width=100%}

![Start a session, send chunks, resume from the last byte the server has](diagrams/video-p11-resumable.pdf){width=100%}

![Longest-prefix match for routes and IP ranges](diagrams/video-p11-trie.pdf){width=100%}

## Traps and easy confusions

**Trap · A failover that took as long as the DNS TTL.** A region fails. The team changes the DNS record to point at the healthy region, in thirty seconds. The record's TTL was **one hour**. Resolvers and clients keep the old address for up to an hour; some clients ignore the TTL and keep it longer. The failover was quick. The outage lasted an hour.

**Trap · "One backend gets all the traffic over a few long connections.".** A **layer 4** balancer balances **connections**. A client with one HTTP/2 or gRPC connection sends every request to one backend. Fix: balance at **layer 7**, per request; or have clients open several connections and rotate them; or cap a connection's lifetime so it reconnects elsewhere.

**Trap · "A deploy drops in-flight requests.".** The process was killed **before** the balancer stopped sending to it. Order matters: 1. fail **readiness**; 2. wait for the balancer to notice, a few probe intervals; 3. finish in-flight work, bounded by a deadline; 4. exit. And never let a health check depend on a shared dependency: when the database blips, **every** backend fails, and everyone is ejected.

**Easy to confuse · Gateway, sidecar mesh, or library.** **Edge gateway**: one place for edge policy. Bottleneck risk if it grows logic. **Service mesh** with a sidecar proxy per service: retries, mutual TLS and metrics for **east-west** calls, at the price of a proxy hop and a control plane to run. **A shared client library**: no hop, and every language and version must be upgraded to change policy.

**Easy to confuse · Push costs a connection per client.** Any push transport holds **one open connection per online client**. A million online users is a million connections, with memory, file descriptors and heartbeats (next section). And a mobile app in the background cannot hold one: it needs a platform push service, which is part of the notification task.

**Easy to confuse · What each style costs you later.** **REST** without discipline drifts into inconsistent verbs in URLs. **gRPC** needs a proxy or a transcoding layer for browsers. **GraphQL** needs **query cost limits**, depth limits and persisted queries, or one client can take down the backend with one request.

**Trap · "Why not GraphQL here?".** Answer with the **consumers**: how many client screens, how different their shapes, and who controls them. One mobile app and one web app, owned by the same team: a backend-for-frontend with plain methods is simpler. Dozens of independent clients over one graph: GraphQL earns its cost-control machinery.

**Easy to confuse · What cursors cannot do.** No **jump to page 50**, and no exact **total count** for free. If the product needs them, compute an approximate count separately, and limit how deep jumps go. Offsets are fine for small, static lists: an admin table of 200 rows.

**Trap · "For how long do you remember the key?".** Longer than the **longest retry window** of any client, including offline mobile clients that retry on reconnect: perhaps **days**, not minutes. After expiry, a late retry **would** create a duplicate. So either keep keys longer than any retry, or reject requests whose client timestamp is older than the key retention.

**Easy to confuse · The operation is a durable record.** Operations must be **stored**, with an owner and an expiry, and survive the server that created them. Make the start call **idempotent** too, with a key, or a retried start launches the job twice. Offer a **callback** or event for clients that should not poll.

**Easy to confuse · Sessions expire, and parts must be cleaned up.** A session holds state on the server: give it an **expiry**, a week for example. Parts uploaded and never completed are **orphans** (part 7): a lifecycle rule deletes them. Verify a **checksum** of the whole object on completion.

**Trap · Errors that clients cannot act on.** A service returns **500** for "you sent a bad field", for "you are over your quota" and for "the database is down". Clients cannot tell which to retry. So they retry **all** of them, including the bad requests, forever, and the quota rejections at full speed. The overload makes itself worse because the error carried no instruction.

**Easy to confuse · 429 or 503, and why the difference matters.** **429** says "slow down, you": the client should back off, and others are unaffected. **503** says "we are hurting": every client should back off, and the server may shed by criticality (part 12). Sending 503 for a per-client limit makes **innocent clients** back off; sending 429 for overload makes nobody back off enough.

## Probe drills

**1. Server push for a streamed response: which transport, and why?**

- **Server-sent events**: one direction, plain HTTP, resumes from the last event ID
- Passes proxies and multiplexes over HTTP/2
- WebSocket only if the client sends often during the stream

> Server-sent events. The flow is one direction, the server streams tokens to a client that already sent its request. It is plain HTTP, so it works through proxies and load balancers and multiplexes over HTTP two, and it resumes from the last event identifier after a drop. I would choose WebSocket only if the client also sent frequently during the stream, which this does not.

**2. Make this POST safe to retry.**

- Client sends an **Idempotency-Key**, generated once per intent
- Server claims it with a **unique insert**, stores the response with the effect
- Retries get the **same response**; in progress gets 409

> The client generates an idempotency key once per user action and sends it in a header on every attempt. The server claims the key with a unique insert before doing anything, performs the effect and stores the response in the same transaction, and replays that response on any retry. A retry that arrives during the first gets conflict, and the same key with a different body is rejected.

**3. For how long do you remember the key?**

- Longer than the **longest client retry**, including offline mobile clients
- So **days**, scoped to the caller
- Or reject requests older than the retention

> Longer than any client could retry, including a phone that was offline and replays its queue on reconnect. So days, not minutes, and scoped to the caller so keys cannot collide across customers. If that is too expensive, I reject requests whose client timestamp is older than my key retention, so a late retry fails safely instead of duplicating.

**4. A deploy drops in-flight requests. Why, and the fix?**

- The process exited **before** the balancer stopped sending
- Fail **readiness**, wait a few probe intervals, finish in-flight, then exit
- Bound the drain with a deadline

> The process exited before the load balancer had stopped sending it requests. The fix is the drain order: fail the readiness check, wait a few probe intervals until the balancer has noticed, let in-flight requests finish up to a deadline, then exit. For long-lived connections, also tell clients to reconnect, so they move gracefully rather than all at once.

**5. Ten million open connections reconnect at once.**

- 10 million TLS handshakes is a **self-inflicted outage**
- Clients use **randomised exponential backoff**; servers can hint a delay
- Shed handshakes beyond capacity early and cheaply

> That is a self-inflicted outage, because TLS handshakes are expensive and the gateways cannot do ten million in a few seconds. Clients must reconnect with randomised exponential backoff, so the wave spreads over tens of seconds. The servers can send a reconnect delay hint when they shut down, and refuse handshakes beyond capacity cheaply and early, rather than accepting them and timing out.

# Part 12 · Rate limiting and overload control

**Assumed reading.**

- *Site Reliability Engineering*, chapter 21, *Handling Overload*.
- The chapter's criticality classes, per-customer limits, the derivation of client-side throttling and its utilisation signals stay there.
- Part 8 of this course: reservations and escrow, for quotas that are money.

**Read next.**

- *The Site Reliability Workbook*, chapter 11, *Managing Load*, and chapter 17, *Identifying and Recovering from Overload*.
- The Doorman design (Google's global distributed client-side rate limiter): rate shares and leases.
- *Designing Data-Intensive Applications*, chapter 7: preventing lost updates, the atomic check-and-decrement.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| RL-01 | Token bucket | A | A token bucket keeps tokens and a last refill time per key and refills lazily on each request, so the rate sets the average and the capacity sets the burst. The check and decrement are one atomic operation, and time comes from the store, not from the callers. | 12.1 The token bucket |
| RL-03 | Window counters | A | A fixed window counter allows up to twice the limit across a boundary. A sliding log is exact and costs a timestamp per request. The sliding-window counter weights the previous window by how much of it still overlaps, and is nearly exact with two counters per key. | 12.2 Window counters |
| RL-04 | Distributed enforcement | A | For a global limit across many nodes I lease capacity from a central store and spend it locally. Over-admission is bounded by nodes times lease size, a lowered limit takes effect within one lease duration, and I pick the lease size to trade that bound against traffic to the store. | 12.3 Distributed enforcement |
| RL-05 | Concurrency limits | B | Besides rate limits, each server has a concurrency limit, sized by Little's law as throughput times latency, and ideally adaptive: increase while latency is flat, cut sharply when it rises. It reacts to slowness instantly, with no clock. | 12.4 Concurrency limits |
| RL-06 | Load shedding and criticality | A | Under overload I shed by a criticality carried on every request and propagated downstream, batch first, checkout last. I reject as early and cheaply as possible, because if a rejection costs a tenth of the work, the server serves nothing at ten times overload. | 12.5 Load shedding and criticality |
| RL-07 | Client-side adaptive throttling | B | Clients throttle themselves: each tracks recent requests and accepts and drops locally with probability requests minus K times accepts, over requests plus one, with K about two. Rejected work never reaches the overloaded backend. | 12.6 Client-side adaptive throttling |
| RL-08 | Fairness | B | For fairness I use max-min allocation, with weights where plans differ, enforced by per-tenant quotas at the gateway and per-tenant queues inside servers, so a noisy tenant waits behind its own burst. | 12.7 Fairness |
| RL-09 | Fail-open vs fail-closed | A | For every limit I decide, with its owner, whether it fails open or closed when the store is unreachable. Product limits usually fail open to a bounded local fallback, security limits fail closed. The behaviour is explicit, with a short timeout, and tested by blocking the store. | 12.8 Fail-open versus fail-closed |
| RL-10 | Admission control and queue discipline | B | Every queue is bounded, a request whose deadline has passed is dropped when it reaches the front, and under overload I serve newest first or let CoDel drop when the minimum delay stays above target. For a known spike, a waiting room in front. | 12.9 Admission control and queue discipline |

## Figures

![Twice the limit across a window boundary](diagrams/video-p12-boundary.pdf){width=100%}

![Fifty gateways, each enforcing the limit locally](diagrams/video-p12-local-limit.pdf){width=100%}

![A bounded queue, deadlines checked at dequeue, newest first under overload](diagrams/video-p12-queue.pdf){width=100%}

## Traps and easy confusions

**Trap · A limiter that failed closed and took the product down.** Every request checks a central rate-limit store. One afternoon the store's primary fails over, and is unreachable for forty seconds. The limiter's code treats "no answer" as "over the limit". **Every request is rejected**. For forty seconds the product was down, protected perfectly from traffic it could easily have served.

**Easy to confuse · Token bucket or leaky bucket.** **Token bucket** allows bursts up to b, then the rate r. Two knobs: the average and the burst. **Leaky bucket** as a queue: requests drain at a constant rate. Smooths output perfectly, and **adds latency** to bursts; suits shaping traffic to a fragile downstream.

**Easy to confuse · Windows or buckets.** **Windows** state a limit the way contracts do: "1,000 requests per hour". Easy to explain, easy to bill. **Buckets** state a rate and a burst, and are better at protecting a server. Many systems use both: a bucket per second for protection, a window per day for the commercial quota.

**Easy to confuse · Exact and slow, or bounded and fast.** **Central counter** when the limit is small and money-like, and a millisecond per request is affordable. **Leases** for high-volume protection limits: a few percent over, almost no added latency. Google's **Doorman** works this way, with rate shares and leases. **Gossip** where any central store is unacceptable and rough is fine.

**Trap · "Two gateways race for the last token.".** With a **central counter**: the decrement is atomic, so exactly one wins. With **leases**: they cannot race for the same token, because tokens are partitioned among nodes in advance. The cost is that the last few tokens may sit unused on another node.

**Easy to confuse · What it protects, and what it does not.** It protects **this server** from its own slowness. It says nothing about fairness between clients. An adaptive limit needs a clean latency signal: if latency is dominated by a slow dependency, the limit shrinks to protect the dependency, which may be exactly right.

**Trap · "Where exactly do you reject, and what do you drop first?".** **Where**: as early and as cheaply as possible: before parsing the body, before authentication if you can, ideally at the client (12.6). **What first**: by criticality carried on the request: batch and prefetch before user-facing, user-facing before the critical few, such as checkout. And **propagate** criticality to downstream calls, so a backend sheds the same way.

**Easy to confuse · Why K is 2 and not 1.** With K = 1 the client would send only what was accepted, and could never **discover** that the backend has recovered. K above 1 keeps sending some excess, which probes for capacity, at the cost of some wasted rejections at the backend.

**Easy to confuse · Removing the dependency instead.** If the limiter must never be a single point of failure, keep the store **off the request path**: leased capacity (12.3) keeps working for one lease duration when the store dies. The price is the bounded overshoot, which you already accepted.

## Probe drills

**1. State the worst-case over-admission.**

- With leased capacity: **N x L**
- 50 gateways, leases of 20: up to **1,000** extra in the worst moment
- With a central counter: zero, for a round trip per request

> With leased capacity it is the number of nodes times the lease size, because in the worst moment every node has just received a full lease as the global budget runs out. Fifty gateways with leases of twenty tokens can over-admit by up to a thousand requests. With a central atomic counter it would be zero, at the cost of a round trip to the store on every request.

**2. Halve it. What does it cost?**

- Halve **L**: 500 extra
- **Twice** the lease requests to the central store
- Or fewer nodes per limit: route a tenant to a **subset** of gateways

> Halving the lease size halves the bound to five hundred, and doubles the traffic to the central store, since each node renews twice as often. Alternatively, reduce N for a given limit: route each tenant to a subset of gateways, so only those hold leases for it. That also improves locality, at the cost of a routing rule.

**3. The limiter's store is down.**

- Each limit **fails as decided**: product limits open to a **local fallback**, security limits closed
- Leases keep working for **one lease duration**
- Alert, and the runbook names the owner of each choice

> Each limit does what we decided in advance. Nodes keep spending their current leases for one lease duration, then fall back. Product limits fail open to a local per-node bucket, the global limit divided by the node count, so we are generous but bounded. Login and other security limits fail closed. We alert at once, and the runbook says who owns each of those choices.

**4. Two gateways race for the last token.**

- **Central counter**: an atomic decrement; exactly one wins
- **Leases**: no race; tokens are partitioned in advance
- The price of leases: a few tokens stranded on another node

> With a central counter, the decrement is atomic, so exactly one of them gets it and the other is told to retry after. With leases there is no race at all, because the tokens were split among nodes in advance. The price is the opposite problem: near the end, a few tokens can sit unused on a node that does not need them.

**5. A limit is lowered. When does it bite?**

- At the next **lease renewal**: within one **lease duration**
- Overshoot meanwhile at most **N x L**
- For an emergency cut: **revoke** by version

> Leases already granted are spent at the old terms, so the new limit bites as each node renews, within one lease duration, with an overshoot of at most N times L in the meantime. If that is too slow, for an emergency, nodes check a limit version on each decision and drop leases older than the new version, so the cut is immediate.

# Part 13 · Reliability patterns

**Assumed reading.**

- *Site Reliability Engineering*, chapter 22, *Addressing Cascading Failures*.
- The chapter's anatomy of a cascade, queue management, testing advice and immediate steps during an incident stay there.
- Part 11: deadlines passed down a call chain. Part 12: shedding and client-side throttling.

**Read next.**

- Dean and Barroso, *The Tail at Scale*: hedged and tied requests, micro-partitions.
- *Site Reliability Engineering*, chapter 26, *Data Integrity*. *Designing Data-Intensive Applications*, chapter 1 (faults and failures) and chapter 8 (timeouts).
- The reliability pillar of the Google Cloud Well-Architected Framework.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| REL-01 | Timeouts and deadlines | A | I set each per-attempt timeout from the dependency's p99.9 latency, cap it by what remains of the caller's deadline, and keep retries inside that deadline. A timeout is a capacity decision: it bounds how long a failing dependency can hold my threads. | 13.1 Timeouts and deadlines |
| REL-02 | Retries | A | I retry at exactly one layer, with at most three attempts, inside a retry budget of about ten percent of requests, using exponential backoff with full jitter. Every other layer fails fast, because three layers each retrying three times multiply load by twenty-seven exactly when the bottom is weakest. | 13.2 Retries |
| REL-03 | Circuit breaker | A | A circuit breaker around each dependency trips open when the failure rate passes a threshold over a minimum number of calls, fails fast for a cool-down, then lets trial calls through half-open. It needs a fallback for the open state, and it suits dependencies that fail completely. | 13.3 Circuit breaker |
| REL-04 | Bulkheads and cells | A | Inside a process, each dependency gets its own bounded pool, so a slow one cannot take every thread. Across the fleet I use cells: full copies of the stack serving fixed customer slices behind a very simple router, deployed one cell at a time, so a bad change or poison input reaches one slice. | 13.4 Bulkheads and cells |
| REL-05 | Hedged requests | B | For fan-out reads where the tail decides latency, I hedge: after the p95, send a second copy to another replica and take the first answer. It costs a few percent more requests and cuts the tail sharply, and I use it only for idempotent reads and turn it off under overload. | 13.5 Hedged requests |
| REL-06 | Graceful degradation | A | My design lists every dependency as hard or soft, with what the user sees when each fails. Soft calls run in parallel with short timeouts and tested fallbacks, and each fallback served is counted, so a failing extra never takes down the core path. | 13.6 Graceful degradation |
| REL-07 | Static stability | A | I design for static stability: if the control plane is down, the data plane keeps serving from last known good state, and capacity to survive a zone loss is already running, not launched during the event. The price is idle headroom and no changes until the control plane returns. | 13.7 Static stability |
| REL-08 | Redundancy and failure domains | A | I count redundancy in the unit that fails, usually a zone. Surviving the loss of one of three zones at peak needs each zone to carry half the peak, one and a half times in total, running before the failure. With four zones it is one point three three, which is one reason to prefer more, smaller failure domains. | 13.8 Redundancy and failure domains |
| REL-09 | Cascading and metastable failures | B | A metastable failure is a sustaining loop: latency causes timeouts, timeouts cause retries, retries cause load, and it survives after the trigger is gone. I break it by shedding hard, dropping expired work and cutting retries, then restoring traffic in steps. | 13.9 Cascading and metastable failures |
| REL-10 | Thundering herds | A | Thundering herds come from synchronisation: the same schedule, the same fixed delay. I give every scheduled job a random offset, every retry full jitter, and every reconnect a random delay, and the server ramps admission after a recovery. | 13.10 Thundering herds |
| REL-11 | Reconciliation and invariant audits | A | As the net under every other mechanism, I reconcile systems that should agree and audit invariants that must always hold, independently of the code paths that maintain them, partitioned so differences narrow fast, with an owner and an idempotent repair for each class of difference. | 13.11 Reconciliation and invariant audits |
| REL-12 | Dependency hygiene | B | I classify each dependency as hard or soft, keep the hard chain short because availability multiplies along it, forbid cycles among hard dependencies, and test a full cold start so a cycle is found in a drill, not an outage. | 13.12 Dependency hygiene |
| REL-13 | Capacity and autoscaling | B | Autoscaling only keeps up with slow growth, because launch and warm-up take minutes, so I keep headroom for spikes and a zone loss. Scale-down is the risky direction: it is slow, has floors tied to expected traffic, and pauses during incidents. | 13.13 Capacity and autoscaling |
| REL-14 | Disaster recovery | B | My disaster recovery plan lists scenarios, each with its recovery point and time, runbook and decision owner, and I only trust it once it has been exercised, ideally in production where safe, with restores tested on a schedule. | 13.14 Disaster recovery |

## Figures

![Calling a dependency that is certainly down](diagrams/video-p13-no-breaker.pdf){width=100%}

![Closed, open, half-open](diagrams/video-p13-breaker.pdf){width=100%}

![One slow dependency takes every thread](diagrams/video-p13-shared-pool.pdf){width=100%}

![Separate pools inside a process; separate cells across the fleet](diagrams/video-p13-cells.pdf){width=100%}

![The control plane fails, and the data plane stops with it](diagrams/video-p13-static.pdf){width=100%}

![The loop that holds a system down](diagrams/video-p13-metastable.pdf){width=100%}

![Hard, soft, and the cycle that prevents a cold start](diagrams/video-p13-cycle.pdf){width=100%}

## Traps and easy confusions

**Trap · The trigger is gone, and the system is still down.** A database has a ten-minute slowdown during a backup. Latency rises; clients time out; every layer retries three times. The backup finishes. The database is healthy again. The system stays down for an hour, because the **retries alone** are now three to twenty-seven times the normal load, and every response is too late to count.

**Trap · The default timeout was thirty seconds.** A dependency normally answers in 20 ms, at p99 in 80 ms. The client library's default timeout is **30 seconds**. The dependency hangs. Each calling thread now waits 30 s. A server with 200 threads serving 2,000 requests a second runs out of threads in **one tenth of a second**. The caller is down, though its own code is fine.

**Trap · "Where exactly do retries happen in your design, and who may not retry?".** Name the **one layer** that retries: usually the one closest to the user that knows the request is idempotent. **Not allowed to retry**: anything non-idempotent without a key (part 11); any layer below the chosen one; and any call whose deadline has passed. **Retry on** unavailable and 503; **never on** 400s or on DEADLINE_EXCEEDED from below, which means the budget is spent.

**Easy to confuse · Breaker, retry budget, or adaptive throttling.** **Retry budget** limits extra load from retries, and still sends every first attempt. **Client-side throttling** (part 12) rejects in proportion to the failure rate, smoothly. **A breaker** is all or nothing: it stops all calls, and recovers in steps. It suits a dependency that fails **completely**, not one that is merely slow for some calls.

**Easy to confuse · Only for idempotent reads, and never under overload.** Hedge only **idempotent** requests: a hedged write may apply twice. Under overload, hedging **adds** load at the worst moment: disable it when the dependency is shedding, or count hedges against the retry budget.

**Trap · Recommendations are down, so the product page shows an error.** The product page calls six services. One of them, recommendations, fails. The page handler treats any failed call as a failed page, and returns an error. Users cannot buy anything, because a box of "you might also like" could not load.

**Easy to confuse · Degrade the product, or degrade the quality.** Some systems degrade **quality** under load rather than features: fewer search results scored, a cheaper model, lower video bitrate. Both need a **product owner's decision** in advance: which feature or quality is cut first. That is a requirement, not an implementation detail.

**Easy to confuse · What it costs, and what it gives up.** **Cost**: idle capacity, here 50% over peak, and caches of state that can be stale. **Gives up**: changes during the outage. No new deploys, no config changes, no scaling. That is acceptable for minutes to hours, and the trade must be stated.

**Easy to confuse · Pay for N+1 across zones, or accept a degraded mode.** N+1 by zone costs **50%** more capacity with three zones. Some systems instead **shed** to the critical traffic when a zone is lost (part 12), and size only for that. The decision is a cost against an availability target, made with numbers, not by habit.

**Trap · "Load is back to normal and latency is not. Why, and what do you do?".** The **work** has not returned to normal: retries, queued requests that are already past their deadline, and cold caches still add load. Break the loop: **shed** load hard, drop queued work past its deadline, **cut retries** (budget to zero), and warm caches before restoring full traffic. Then let traffic back **in steps**.

**Easy to confuse · Spread, or provision for the peak.** Provisioning for the synchronised peak, 10x normal for one minute a night, is expensive and rarely necessary. The price of jitter is **latency**: a job runs up to 30 minutes later, a retry waits longer. State it.

**Trap · A bug that every mechanism above let through.** A payment is marked **paid** in your ledger. The card network never received the charge: a bug in an error path. Retries, idempotency and transactions all worked as designed. The bug was in the logic they protected. Six weeks later finance finds 1,400 orders shipped without payment.

**Easy to confuse · Cheaper than any prevention for unknown bugs.** It costs a job, read capacity on both systems, and a team that answers the alerts. It is the only defence against bugs nobody predicted, and Google's data-integrity practice, in SRE chapter 26, treats it as mandatory for important data.

**Trap · Why scaling down is the dangerous direction.** An upstream outage drops your traffic to near zero. The autoscaler, correctly by its rules, **removes 80% of capacity**. The upstream recovers, and full traffic returns in seconds, onto a fleet that needs minutes to grow back. Fix: **minimum floors** tied to expected traffic, slow scale-down, and no scale-down while an incident is open.

**Easy to confuse · An exercise finds what documents hide.** Every exercise finds something: a runbook step that no longer exists, a credential only one person holds, a dependency nobody listed. That is the point, and the price is the risk and effort of running it. Start in test environments; widen as confidence grows.

## Probe drills

**1. Where exactly do retries happen in your design?**

- At **one layer**: the edge service, which knows the call is idempotent
- At most **3 attempts**, within the deadline, budget **10%**, full jitter
- Every other layer **fails fast**

> At one layer only, the edge service, because it knows which calls are idempotent and holds the user's deadline. At most three attempts, all inside that deadline, with a retry budget of about ten percent of requests and full jitter on backoff. Every layer below fails fast and returns the error upward, because three layers each retrying three times would multiply load by twenty-seven.

**2. And who is not allowed to retry?**

- Any layer **below** the chosen one
- Any **non-idempotent** call without an idempotency key
- Any call whose **deadline has passed**, or that got a 400

> Every layer below the one I chose. Any non-idempotent call without an idempotency key, because a retry would repeat the effect. Any call after its deadline has passed, since nobody is waiting for the answer. And nothing that failed with a client error, because it will fail the same way again.

**3. What does the user see when this dependency fails?**

- Look it up in the **degraded-mode table**: hard or soft
- Soft: the fallback, within a **short timeout**, counted by a metric
- Hard: a clear error, and that dependency gets the most redundancy

> I would look it up in the design's degraded-mode table. If it is soft, like recommendations, the user sees the fallback, best-sellers, within a short timeout, and we count each fallback served. If it is hard, like price and stock, the user sees a clear error, and that is why hard dependencies get the most redundancy and the shortest list.

**4. A zone is lost at peak. Walk me through the next five minutes.**

- Seconds: balancers **eject** it; other zones absorb with **N+1** sizing
- Within a minute: leaders in the zone **fail over**
- Nothing launched on the critical path; then repair replicas by risk

> Within seconds, the balancers eject the zone's backends and the other two zones take its traffic, which they can absorb because each is sized for half the peak. Within a minute, leaders that lived in the zone fail over: consensus groups re-elect, asynchronous primaries are promoted, with their lag as the loss. Nothing needs to be launched to survive. Afterwards, data that lost a replica is repaired, most at-risk first.

**5. The load is back to normal and latency is not. Why?**

- A **metastable loop**: retries and expired queued work keep load high
- **Shed** hard, drop expired work, **cut retries** to zero
- Warm caches, then restore traffic **in steps**

> The offered load is normal, but the work is not: retries, queued requests already past their deadlines, and cold caches keep the system above capacity, and its own timeouts keep generating more retries. I would shed load hard, drop queued work past its deadline, set the retry budget to zero for a while, warm the caches, and then let traffic back in steps.

# Part 14 · Observability and time-series storage

**Assumed reading.**

- *Site Reliability Engineering*, chapter 4 (*Service Level Objectives*) and chapter 6 (*Monitoring Distributed Systems*).
- *The Site Reliability Workbook*, chapter 2 (*Implementing SLOs*) and chapter 5 (*Alerting on SLOs*).
- How to choose SLIs, the burn-rate derivation and its table of windows, and alert hygiene stay in those chapters.

**Read next.**

- Adams et al., *Monarch: Google's Planet-Scale In-Memory Time Series Database*.
- Pelkonen et al., *Gorilla: A Fast, Scalable, In-Memory Time Series Database*.
- *Designing Data-Intensive Applications*, chapter 3: column-oriented storage.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| OBS-09 | Golden signals | A | For any user-facing service I watch latency, split by success and failure, traffic, errors, and saturation of the tightest resource, and I measure at the edge and from outside probes as well as in the server, because the worst failures never reach it. | 14.1 The four golden signals |
| OBS-08 | SLI, SLO, error budget | A | My indicator is good requests over valid requests, the objective is a target for it over thirty days, and the error budget, a tenth of a percent, forty-three minutes a month, is spent on launches and failures alike. A written policy says what happens when it is gone: launches stop until reliability recovers. | 14.2 SLI, SLO and error budget |
| OBS-01 | Metric model and cardinality | B | The number of series is the product of each label's distinct values, so labels must be few and bounded. Per-user detail goes into logs, traces and exemplars, and the store enforces a series limit per metric. | 14.3 The metric model and cardinality |
| OBS-02 | Percentiles and sketches | A | I never average percentiles. Each host keeps a histogram or a mergeable sketch, the fleet's distribution is their sum, and the p99 is read from that sum. And I put a bucket edge exactly at the objective's threshold, so the indicator is exact. | 14.4 Percentiles and sketches |
| OBS-03 | Push vs pull collection | B | Pull collection notices a dead target and paces itself. Push suits short-lived jobs and many networks, and detects a dead target only against an expected set from the registry, with pushes rate-limited. | 14.5 Push versus pull collection |
| OBS-04 | Roll-ups and retention | B | I keep raw samples for a couple of weeks and roll-ups for months and years, each roll-up storing min, max, sum, count and histogram buckets, so spikes, rates and percentiles all survive the loss of resolution. | 14.6 Roll-ups and retention |
| OBS-06 | Logging pipelines | B | Logs go from an agent with a local buffer through a queue into an index, and age into object storage. Under pressure the pipeline drops in a stated order, debug first, never errors or audit records, and it never blocks the application. | 14.7 Logging pipelines |
| OBS-05 | Alerting | A | I alert on error-budget burn rate, with a long and a short window, paging at fourteen point four over an hour and six over six hours, and ticketing at one over three days. Detection time is scrape, evaluation, hold and notification added up, and I shorten it only for the few indicators that justify the cost and the false alarms. | 14.8 Alerting |
| STO-06 | Columnar storage | B | For analytical scans I use columnar storage: each column stored together, so a query reads only the columns it needs, compressed by dictionary, run-length and bit-packing, often ten times. The price is slow single-row writes and lookups, so it is fed in batches. | 14.9 Columnar storage |
| STO-07 | Time-series compression | B | Time-series stores encode timestamps as deltas of deltas and values as XOR with the previous value, about one point four bytes a sample. The binding limit is memory per active series, a few kilobytes each, so ten million series is tens of gigabytes. | 14.10 Time-series compression |
| DS-06 | Inverted index | B | The time-series store finds series through an inverted index: each label value maps to a sorted postings list, and a query intersects the lists, shortest first. Search engines use the same structure for words. | 14.11 The inverted index from label to series |

## Figures

![Aggregate distributions, then read the percentile](diagrams/video-p14-histograms.pdf){width=100%}

![Agent, buffer, queue, index; drop the cheapest first](diagrams/video-p14-logs.pdf){width=100%}

![Store each column together, read only the columns you need](diagrams/video-p14-columnar.pdf){width=100%}

![Each label value lists its series; a query intersects the lists](diagrams/video-p14-postings.pdf){width=100%}

## Traps and easy confusions

**Trap · Someone adds a user ID as a label.** A latency metric has labels for method, status, endpoint and instance: about **half a million** series. An engineer adds `user_id` to debug one customer. There are a million active users. The metric now has up to **five hundred billion** possible series. The monitoring system runs out of memory, and the company is blind during the incident the label was meant to help with.

**Trap · "Your error rate is flat and users are complaining.".** Look for errors the server cannot see: **clients timing out** before the server answers, requests that never arrived because of DNS or the load balancer, **wrong answers** returned as 200. So measure at the edge and from probes outside, not only in the server.

**Trap · "Why not 100%?".** Because users cannot tell 99.99% from 100% through their own networks and devices, and every extra nine costs about **ten times** more. And because a budget is what lets you **ship**: a 100% target means no risky change is ever allowed. Set the SLO a little **below** what the system achieves, so it alerts before users suffer, not after.

**Easy to confuse · Histograms, sketches, or raw samples.** **Fixed histogram**: cheapest, mergeable, error set by edges. **Quantile sketch** (part 10): adapts, mergeable, a few KB per series. **Raw samples**: exact, and impossible at scale; acceptable only for traces of sampled requests. **Precomputed percentiles** per host: cheap and **not mergeable**. Avoid them for anything aggregated.

**Trap · "p99 across 10,000 hosts.".** Each host exports a **histogram** with shared bucket edges, or a sketch. The query **sums bucket counts** across hosts, then computes the p99 once. Cost: buckets x hosts series, so keep buckets to a few dozen, and pre-aggregate by region in a recording rule.

**Easy to confuse · What a roll-up loses.** A 30-second spike disappears inside a 5-minute average; the **max** keeps it. Percentiles **cannot** be rolled up from percentiles; only from buckets. Queries spanning tiers must switch resolution at the boundary, and say so on the graph.

**Trap · "Who monitors the monitor?".** The alerting path must **not depend on what it watches**: separate infrastructure, another region or another provider. A **dead man's switch**: an alert that **always fires**, received by an external service that pages when it **stops** arriving. And a second, small, independent monitor that checks the main one from outside.

**Easy to confuse · Long lists and negative matches.** A label with few values, such as `status="200"`, has a list covering most series: intersect **shortest first**. A negative or regular-expression match, `endpoint=~"/api/.*"`, must merge many lists: expensive. Each new series adds an entry to every one of its labels' lists: cardinality costs index too.

## Probe drills

**1. p99 latency across 10,000 hosts.**

- Hosts export **histograms** with shared edges, or mergeable sketches
- **Sum** bucket counts, then compute the p99 once
- Pre-aggregate by region; keep an edge at the SLO threshold

> Every host exports a latency histogram with the same bucket edges, or a mergeable sketch. The query sums bucket counts across all hosts and reads the p99 from the sum. Averaging per-host p99s would be wrong. To keep it cheap I pre-aggregate per region with a recording rule, and I put a bucket edge exactly at the objective's threshold so the indicator is exact.

**2. Who monitors the monitor?**

- Alerting runs on **independent** infrastructure
- A **dead man's switch**: an always-firing alert, paged on silence
- An external probe of the monitoring system itself

> The alerting path runs on infrastructure that does not share failure with what it watches, in another region or with another provider. A dead man's switch sends an alert that always fires to an external service, which pages if it stops arriving. And a small independent monitor probes the main monitoring system from outside, so its outage is itself noticed.

**3. Cut detection time from two minutes to fifteen seconds.**

- Detection is **scrape + evaluate + for + notify**
- Shorten scrape and evaluation to 5 s, drop the for window
- Cost: **6x** samples, and more false pages; only for a few critical SLIs

> Detection time is the sum of the scrape interval, the evaluation interval, the for window and notification, here about two minutes. To reach fifteen seconds I scrape and evaluate every five seconds and remove the for window. That costs six times the samples for those series, and pages on short blips. So I would do it only for the few indicators where fifteen seconds matters.

**4. And what false-alarm rate do you accept?**

- Set by **on-call load**: at most a couple of pages a shift
- Every page must be **actionable**; a false one is a cost, tracked
- Measure precision of each alert, and retune or delete the noisy ones

> That is set by what on-call can sustain, roughly no more than a couple of pages per shift, every one actionable. I would track each alert's precision, the fraction of its pages that needed action, and retune or delete alerts that fall below, say, half. A fast alert that pages falsely every night is worse than a slower one people trust.

**5. Someone added a user ID as a label. What now?**

- **Cardinality** explodes: product of label values
- Drop the label at ingestion; enforce a **per-metric series limit**
- Per-user detail goes to logs, traces or **exemplars**

> The series count multiplies by the number of users, and the store runs out of memory. Immediately, I drop that label at ingestion with a relabelling rule. Permanently, a per-metric series limit refuses new series past a ceiling and alerts the owner. And the per-user question is answered by logs and traces, indexed by identifier, or exemplars that link a metric bucket to one trace.

# Part 15 · Scheduling and control planes

**Assumed reading.**

- *Site Reliability Engineering*, chapter 24, *Distributed Periodic Scheduling with Cron*.
- The chapter's design history of the cron service and its handling of large installations stay there.
- Part 3 (consensus), part 2 (fencing), part 13 (static stability).

**Read next.**

- Verma et al., *Large-scale cluster management at Google with Borg*.
- Burns et al., *Borg, Omega, and Kubernetes*.
- *Site Reliability Engineering*, chapter 2, *The Production Environment at Google*. *Designing Data-Intensive Applications*, chapter 8 (fencing).

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| OPS-04 | Control plane vs data plane | A | I separate the control plane, which decides and pushes versioned state, from the data plane, which serves every request from local state. Nothing on the request path calls the control plane, so the product's availability is the data plane's, and a control-plane outage only delays changes. | 15.1 Control plane versus data plane |
| SCH-01 | Desired state and reconciliation | A | My control plane keeps desired state in a consistent store and runs level-triggered reconcile loops: compare desired with observed, take one idempotent action per difference, on every event and periodically. A missed event, a restart or a failover is then harmless, because the next pass sees the difference. | 15.2 Desired state and reconciliation |
| SCH-02 | Placement | B | The scheduler filters out nodes that cannot run the task, scores the rest, and binds with a conditional write in the store. I spread replicas of one service across failure domains as a hard rule, and pack different services by score to save machines. | 15.3 Placement |
| SCH-03 | Priority, quota, preemption | B | Priority decides who may evict whom, quota caps how much any team can claim, and preemption picks the lowest-priority victims with the least work lost, giving them a grace period to checkpoint. Batch work is designed to be evicted. | 15.4 Priority, quota and preemption |
| SCH-05 | Node liveness and eviction | B | A silent node is presumed dead only after a timeout, evictions are rate-limited, and if a large share of a zone goes silent at once eviction stops, because it is a partition. Cut-off nodes keep running their tasks, and replacements run with a new epoch so the old copies cannot write. | 15.5 Node liveness and eviction |
| SCH-06 | Timers at scale | B | For timers at scale I key them by due-time bucket and shard, so each scheduler shard reads one small range ahead of time into an in-memory timing wheel. Each job has a misfire policy, and fixed times like midnight are spread over a window with a stable random offset. | 15.6 Timers at scale |
| DS-08 | Heaps and timing wheels | B | For a few thousand timers a heap is enough. For millions, a hierarchical timing wheel gives constant-time insert and cancel, fires at tick resolution, and cascades long timers down as they approach. | 15.7 Heaps and timing wheels |
| SCH-07 | Task leasing | A | The scheduler writes a launch record through consensus before any side effect and the outcome after. Workers pull tasks under leases renewed by heartbeat, results are tagged with the attempt identifier, which downstream uses as a fencing token, and each job declares whether a run that started and never finished is retried or held for a check. | 15.8 Task leasing |
| SCH-08 | Durable workflows | B | For long multi-step processes I use a durable workflow engine: each step's result is recorded in a history, and after a crash the code replays deterministically, skipping completed steps, and resumes. The rules are determinism, explicit versioning and bounded history. | 15.9 Durable workflows |

## Figures

![Decide slowly and centrally; serve fast and locally](diagrams/video-p15-planes.pdf){width=100%}

![An edge-triggered controller misses one event](diagrams/video-p15-edge.pdf){width=100%}

![A high-priority task arrives on a full cluster](diagrams/video-p15-preempt.pdf){width=100%}

![A partition makes healthy nodes look dead](diagrams/video-p15-partition.pdf){width=100%}

![Due-time buckets, sharded, loaded into an in-memory wheel](diagrams/video-p15-timers.pdf){width=100%}

![The scheduler starts a job and dies before recording it](diagrams/video-p15-launch-gap.pdf){width=100%}

![Record the intent, lease the task, record the outcome, tag results with the attempt](diagrams/video-p15-lease.pdf){width=100%}

![The workflow's code is replayed from an event history](diagrams/video-p15-workflow.pdf){width=100%}

## Traps and easy confusions

**Trap · The control plane goes down. Does anything else notice?.** A cluster manager's control plane is unavailable for an hour: no new scheduling, no rescheduling, no config pushes. In a well-built system, **every running service keeps serving**. Users notice nothing. In a badly built one, nodes that cannot reach it **kill their workloads**, and the whole fleet goes dark within minutes.

**Easy to confuse · What separation costs.** **Staleness**: the data plane acts on decisions up to a refresh interval old, or longer during an outage. **Two systems** to build and to test, including the case where they disagree. The alternative, one combined system, is simpler and fails all at once.

**Easy to confuse · What the loop costs.** Every pass lists desired and observed state: at 100,000 objects, use **watches plus a periodic full resync** rather than a full list every second. A loop can **fight** another controller, or a human, that changes the same field: give each field one owner.

**Easy to confuse · Bin-packing against spreading.** **Bin-packing** uses fewer machines and frees whole nodes for big tasks, and puts many replicas in one failure domain unless spread is a filter. **Spreading** survives failures and leaves capacity fragmented: a task needing 64 GB finds no node with 64 GB free. Usual answer: **spread replicas** of one service as a hard rule, **pack** different services by score.

**Easy to confuse · Resolution and memory.** A wheel fires at **tick resolution**: one-second ticks mean up to a second late. A wheel of 3,600 one-second slots holds an hour; anything later belongs in an outer wheel, or in the durable store until its bucket loads.

**Easy to confuse · Determinism, versioning and history size.** Workflow code must be **deterministic**: no local clock, randomness or direct I/O; those go through recorded steps. Changing workflow code while old instances are running needs **versioning**, or replay diverges. History grows with steps: very long workflows **continue as new** with a fresh history.

## Probe drills

**1. The scheduler dies after starting a job and before recording it.**

- Prevent it: write a **launch record through consensus first**, state starting
- New leader finds **starting, no result**: apply the job's declared policy
- Idempotent: retry as **attempt 2**; otherwise mark **unknown** and check

> I would not let that state exist silently. The leader writes a launch record through consensus before starting anything. A new leader that finds a record in starting with no result applies the job's declared policy. If the job is idempotent, it launches attempt two, and attempt one's late results are refused by attempt number. If not, like billing, it marks the run unknown and resolves it through the job's own idempotency key, or a person.

**2. A million jobs at midnight.**

- Timers keyed by **due bucket and shard**, read ahead into **in-memory wheels**
- **Spread** over a window with a stable random offset per job
- Downstream sees about **550 a second**, not a million at once

> Timers are stored under their due-time bucket and a shard, so at a minute to midnight each scheduler shard reads its own small range into an in-memory timing wheel, with no table scan. And I ask whether they need exactly midnight. Most do not, so each job gets a fixed random offset in a half-hour window, and downstream services see about five hundred and fifty launches a second instead of a million at once.

**3. A high-priority job arrives. Who is evicted, and how cleanly?**

- Only **lower** priority, never the same band; the team must be within **quota**
- Cheapest victims: least work lost, fewest tasks
- Signal, **grace period**, then kill; batch checkpoints and requeues

> Only tasks of lower priority, never the same band, and only if the arriving job's team is within its quota. Among candidates, I choose those that lose the least work, and the fewest of them, on one node. They get a termination signal and a grace period, say thirty seconds, to checkpoint and exit, then a kill, and they go back in the queue to run elsewhere.

**4. The control plane is down for an hour. What happens?**

- The data plane **keeps serving** on last known good
- No new placements, no rescheduling, no config changes
- Nodes **do not** kill workloads because the control plane is silent

> Everything that is running keeps running, from last known good state, so users notice nothing. What stops is change: no new placements, no rescheduling after failures, no config pushes. Crucially, nodes do not kill their workloads because they cannot reach the control plane. That would turn a control-plane outage into a total one.

# Part 16 · Security, operating and evolving systems, the manager layer

**Assumed reading.**

- *The Site Reliability Workbook*, chapter 16, *Canarying Releases*.
- Canary evaluation and metric selection stay in the chapter.

**Read next.**

- *Site Reliability Engineering*, chapter 17 (*Testing for Reliability*) and chapter 27 (*Reliable Product Launches at Scale*).
- Rae et al., *Online, Asynchronous Schema Change in F1*.
- *Software Engineering at Google*, chapter 14 (*Larger Testing*), chapter 15 (*Deprecation*), chapter 22 (*Large-Scale Changes*).
- *Designing Data-Intensive Applications*, chapter 4 (rolling upgrades). The operational-excellence pillar of the Google Cloud Well-Architected Framework.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| SEC-01 | Authentication | A | Users get short-lived signed access tokens, verified locally, plus an opaque refresh token the auth service can revoke at once, so a stolen token is useful for minutes. Services authenticate each other with mutual TLS and automatically rotated workload identities, and authorisation of a specific resource happens in the service that owns it. | 16.1 Authentication |
| SEC-04 | Tenant isolation | A | I isolate tenants in three ways: data, by a tenant identifier taken from the authenticated identity and enforced below application code; performance, by quotas and fair queues; and faults, by cells or shuffle sharding. And a test tries every endpoint across tenants. | 16.2 Tenant isolation |
| SEC-07 | Abuse resistance | B | Against abuse I layer defences: rate limits at the edge, friction scaled by risk at signup, reputation and anomaly detection on behaviour, and product limits that bound the damage a new account can do, while measuring what each costs legitimate users. | 16.3 Abuse resistance |
| OPS-01 | Progressive rollout | A | Every change, binary, configuration or data, rolls out in stages: canary, zone, region, then the rest, with bake time sized so the canary can actually detect a regression, automated health gates and automatic rollback, and never to two regions at once. | 16.4 Progressive rollout |
| OPS-02 | Online migration | A | I migrate online: expand the new system, capture every new write into it, backfill history, verify with shadow reads until differences are zero, switch reads, then writes, and contract much later. After the write switch, reverse replication keeps the old system current, so rollback loses nothing until a point of no return I declare in advance. | 16.5 Online migration |
| OPS-03 | Version skew | B | Every format or protocol change follows the two-release rule: first ship a version that reads both, then, once it is everywhere, start writing the new format, often by flipping a flag. Any single release can then be rolled back safely. | 16.6 Version skew |
| OPS-05 | Background vs foreground work | A | All background work, backfills, compaction, repair, runs under a controller that slows it whenever foreground latency approaches its objective, with a hard ceiling and lower I/O priority. The price is time, so I put that time in the project plan rather than in users' latency. | 16.7 Background versus foreground work |
| OPS-07 | Kill switches and safe limits | A | Every automation that changes production is bounded: a rate, a maximum fraction of the fleet, a human gate above a threshold, and a kill switch checked locally on every action, which fails safe and is tested in production. | 16.8 Kill switches and safe limits |
| OPS-08 | Testing distributed systems | B | I test the distributed behaviour, not only the code: fault injection, consistency checks under faults, deterministic simulation for rare interleavings, and scheduled failovers in production, because a failover path that has not run recently does not work. | 16.9 Testing distributed systems |
| OPS-09 | Multi-region operation | A | Multiple regions only help if they fail independently, so each region has its own data plane, every change goes region by region with bake time, the others can absorb a lost region's peak, and data is placed per type. I prefer active-active, so failover is a traffic shift exercised every week. | 16.10 Multi-region operation |
| OPS-10 | Cost and efficiency ownership | B | I state the cost as a unit cost, such as dollars per thousand requests, name the biggest line item, and pull its lever, utilisation or replication factor, without eating the headroom a zone loss requires. | 16.11 Cost and efficiency ownership |
| EM-01 | Scope and phases | A | I phase the work: first the thinnest end-to-end path that real users can try, with the riskiest assumption tested before anything is built around it, and each phase ends on a number, not a date. | 16.12 Scope and phases |
| EM-02 | Team shape | A | I cut teams along the design's contracts, not its layers, fix each contract before teams split, put the riskiest component with the most experienced team, and make every team own its part in production. | 16.13 Team shape |
| EM-03 | Build, reuse or buy | A | I build what differentiates us and buy or reuse the rest when it meets the requirements in numbers, comparing three-year cost, including the people to run what we build, and keeping bought products behind our own interface. | 16.14 Build, reuse or buy |
| EM-04 | Risk register | A | I keep a risk register where every risk has a likelihood, an impact, a mitigation, an owner and a trigger to act, reviewed every two weeks, and the riskiest rows decide what goes into the first phase. | 16.15 The risk register |
| EM-05 | SLOs as a contract | A | Between teams I write the objective as a contract: what is promised, what the caller must do in return, what happens when the promise is missed, and where it is measured. And I check that my own objective is achievable given my dependencies' objectives. | 16.16 SLOs as a contract |
| EM-06 | Client adoption and migration | B | To migrate clients I measure usage per client, make moving cheap with guides, shims and automated changes, make the new API the default, announce a deadline, budget for the long tail, and then remove the old path. | 16.17 Client adoption and migration |
| EM-07 | Operational readiness | A | Before launch I check observability with paging alerts, a load test at two to three times the forecast, a staged rollout with rehearsed rollback and a kill switch, tested degraded modes, and runbooks with a trained on-call. Anything missing is a recorded exception with an owner. | 16.18 Operational readiness |

## Figures

![One timeline: expand, capture, backfill, verify, switch reads, switch writes, contract](diagrams/video-p16-migration.pdf){width=100%}

## Traps and easy confusions

**Trap · A correct design, shipped to every region at once.** A configuration change was reviewed, tested and correct for every case anyone had thought of. It was pushed to **every region in the same five minutes**. One field was parsed differently by an older binary still running in a third of the fleet. A third of the world's traffic failed at once, with no region left untouched to fail over to.

**Easy to confuse · What each choice costs.** **Opaque everywhere**: instant revocation, and the auth service on every request path: its outage is yours. **Long self-contained tokens**: no dependency, and no revocation: the opening story. **Short access plus refresh**: a refresh call every few minutes per client, and exposure bounded by minutes.

**Trap · One query without a tenant filter.** A reporting endpoint builds its query by hand and forgets `WHERE tenant_id = :t` in one branch. A customer downloads a report containing **every customer's** invoices. Every other control worked. Isolation depended on every engineer remembering one clause in every query.

**Easy to confuse · Pooled with enforcement, or a database per tenant.** **A database per tenant** makes leaks across tenants nearly impossible and costs per-tenant operations, migrations and idle capacity. **Pooled with enforcement below the application** is cheaper, and the enforcement layer must be the only path to data. Many platforms do both: pooled for small tenants, siloed for the largest or most regulated.

**Easy to confuse · Every defence costs good users something.** Friction loses real signups; false positives block real customers. Measure both, and give a **path to appeal**. Abusers adapt: defences are a **program** with an owner, not a feature shipped once.

**Trap · "Rollout applies to what, exactly?".** **Binaries, configuration and data** alike: the opening story was a config change. Stages: one canary, one zone, one region, then the rest, with **bake time** and an automated health gate at each, and **automatic rollback** on a failed gate. **Never two regions at once** until the change has baked in one.

**Trap · A migration with a weekend of downtime, then a rollback that loses data.** The plan: stop writes Friday night, copy 8 TB, switch Sunday. The copy took longer than planned. The switch happened Monday morning, under load, and failed. Rolling back meant **discarding** six hours of writes made to the new system.

**Easy to confuse · Online or offline.** **Online** costs weeks, a capture path, a verifier and reverse replication, and has no downtime and a safe way back at every step. **Offline** costs a maintenance window and a rollback that may lose data; acceptable for small data and tolerant users.

**Trap · "Roll back after two days of writes.".** With reverse replication running: **switch back**; the old system has every write. Without it: rollback means **replaying two days of writes** into the old schema, if they can be expressed there, or **no rollback**, which should have been said before the switch.

**Easy to confuse · Separate hardware for background work.** Run heavy background work on **replicas** or a **copy**, not on the serving primary: costs a replica, removes the contention. Not always possible: compaction and repair must run where the data is.

**Trap · An automation that did exactly what it was told.** A tool drains servers that fail a health check, so they can be repaired. A bad health-check change marks **every** server unhealthy. The tool, correctly, drains them all, in four minutes. Nobody had told it that draining 90% of a cluster is never a repair.

**Easy to confuse · Limits slow down good days.** A rate limit on drains slows a real repair wave after a bad batch of disks; the human gate costs a page. That is the trade: slightly slower good days for **bounded** bad days. State the limits as numbers.

**Trap · "How would you know your failover works?".** Because it **ran recently**, on purpose: a scheduled failover in production, during business hours, with the on-call watching. A failover path that has not run in six months **does not work**; something it depends on has changed.

**Easy to confuse · What multi-region costs.** Roughly **1.5x** capacity for N+1 with three regions, cross-region replication traffic, and slower, staged releases. Ask whether the availability target needs it: a 99.9% internal tool may be fine in one region with good zone redundancy.

**Easy to confuse · Efficiency spends headroom.** Higher utilisation spends **headroom** you may need for a zone loss (part 13): compute the floor first. Erasure coding raises **repair** cost and read latency for that data.

**Easy to confuse · What phasing costs.** Some throwaway work: a v1 that is replaced; scaffolding for a partial system. And discipline: saying **no** to features until the path works. That is the job.

**Easy to confuse · "Deliver this with half the team.".** Cut **scope**, not quality: the MVP path only, one region, fewer features. **Reuse** or buy (16.14) for anything that is not the differentiator. Say what is **deferred** and what risk that carries, and keep on-call sustainable: a team of three cannot run a 24-hour rotation.

**Easy to confuse · "What would you not build?".** Everything that is not the differentiator and has a product that fits: identity, the message queue, metrics, the workflow engine. Say it with the requirement that the product meets, and the condition under which you would revisit.

**Easy to confuse · A register costs an hour every two weeks.** The alternative is to discover risks when they happen. The price of a register is small; the cost of the surprise is usually a re-plan.

**Easy to confuse · Contracts take negotiation.** Agreeing an SLO with another team costs meetings and sometimes their roadmap. The alternative is an implicit promise that is discovered in an incident.

**Easy to confuse · The long tail.** The last 10% of clients take as long as the first 90%. Budget for it, or the old system runs for ever, and you pay for two.

**Trap · "Who says no to a launch?".** The **owning team's lead**, against the written checklist, with an SRE or production reviewer as a second signature for critical systems. A launch that fails the list goes ahead only as an **explicit, recorded exception**, with an owner and a date to close it.

## Probe drills

**1. A bad push is blocking a continent. Stop it.**

- **Halt** the rollout: the pipeline's stop, or the **kill switch**
- **Roll back** the affected regions to last known good, region by region
- Then find out why the health gate did not catch it

> First, stop the bleeding without debugging: halt the rollout so it reaches no further regions, and if the change is behind a flag, flip the kill switch. Then roll the affected regions back to last known good, one at a time, watching recovery. Only after that, find out why the health gate let it through, whether the bake time was too short to detect it or the gate measured the wrong thing.

**2. Roll back after two days of writes.**

- With **reverse replication** running: switch back, nothing lost
- Without it: replay two days into the old schema, if expressible, or **no rollback**
- Decided and written down **before** the write switch

> If reverse replication from the new system to the old has been running since the write switch, I switch back and nothing is lost. If not, rollback means replaying two days of writes into the old schema, which may not be able to express them, or it means no rollback and a fix forward. Which of those it is should have been decided and written down before writes moved.

**3. How would you deliver this with half the team?**

- Cut **scope**: the MVP path, one region, fewer features; keep quality
- **Buy or reuse** everything that is not the differentiator
- State what is deferred, the risk it carries, and keep on-call sustainable

> I would cut scope, not quality: the thinnest end-to-end path, one region, the features that matter for the first users. I would buy or reuse everything that is not the differentiator, identity, queues, metrics. I would say exactly what is deferred and what risk that carries, and I would make sure the smaller team can still run a sustainable on-call.

**4. What would you not build?**

- Not the **differentiator**? Then reuse or buy, if it meets the numbers
- Identity, the queue, metrics, the workflow engine
- With the condition under which you would revisit

> Anything that is not why customers choose us and has a product that meets the requirements in numbers: identity, the message queue, metrics, the workflow engine. I would build the part that differentiates us, here the core data path. And I would state when I would revisit each, for instance if the bought queue's cost per message became the biggest line item at ten times the volume.

# Part 17 · The building blocks

**Assumed reading.**

- *Site Reliability Engineering*, chapter 2, *The Production Environment at Google, from the Viewpoint of an SRE*.
- Each block's mechanism is in the part named on its card. This part only says when to draw it.

**Read next.**

- The Google Cloud Architecture Center: reference architectures that assemble these blocks.
- Each system's own paper: Chubby, Bigtable, Spanner, GFS and Colossus, Dremel, MillWheel, Dataflow, Monarch, Borg, Maglev, Dapper.

## Concepts

| ID | Name | Tier | The line to say | Section |
|--------|------------------|----|--------------------------------------------------------|--------------|
| BLK-01 | DNS and anycast front door | block |  | 17.1 The front door |
| BLK-02 | L4 load balancer | block |  | 17.1 The front door |
| BLK-03 | L7 proxy / API gateway | block |  | 17.1 The front door |
| BLK-05 | Real-time gateway | block |  | 17.1 The front door |
| BLK-06 | Relational database | block |  | 17.2 Databases and stores |
| BLK-07 | Distributed SQL | block |  | 17.2 Databases and stores |
| BLK-08 | Wide-column store | block |  | 17.2 Databases and stores |
| BLK-09 | Leaderless key-value store | block |  | 17.2 Databases and stores |
| BLK-10 | Embedded storage engine | block |  | 17.2 Databases and stores |
| BLK-11 | Object / blob store | block |  | 17.2 Databases and stores |
| BLK-12 | In-memory cache | block |  | 17.3 Memory and coordination |
| BLK-13 | Coordination service | block |  | 17.3 Memory and coordination |
| BLK-14 | Partitioned log | block |  | 17.4 Messaging and processing |
| BLK-15 | Message queue / pub-sub service | block |  | 17.4 Messaging and processing |
| BLK-16 | Stream processor | block |  | 17.4 Messaging and processing |
| BLK-17 | Batch processor | block |  | 17.4 Messaging and processing |
| BLK-18 | Columnar warehouse / OLAP | block |  | 17.4 Messaging and processing |
| BLK-20 | Time-series database | block |  | 17.5 Platforms and backends |
| BLK-21 | Workflow engine | block |  | 17.5 Platforms and backends |
| BLK-22 | Cluster manager | block |  | 17.5 Platforms and backends |
| BLK-24 | Config / feature-flag service | block |  | 17.5 Platforms and backends |
| BLK-26 | Tracing and logging backends | block |  | 17.5 Platforms and backends |

## Figures

![What is inside: packets, then requests](diagrams/video-p11-l4-l7.pdf){width=100%}

![What is inside: a log, a memory table, sorted files](diagrams/video-p7-lsm-write.pdf){width=100%}

![What is inside: register under a lease, watch, check on every request](diagrams/video-p4-registry.pdf){width=100%}

![What is inside: segments, offsets, retention](diagrams/video-p10-segments.pdf){width=100%}

![What is inside: a control plane that decides, a data plane that serves](diagrams/video-p15-planes.pdf){width=100%}

## Traps and easy confusions

**Trap · "Open that up.".** The candidate draws a box labelled **Kafka** and moves on. The interviewer points at it: "Open that up. What decides ordering, and what happens to a consumer when the group rebalances?" A name without a mechanism is a Depth miss. A mechanism without a name is fine.

## Probe drills

**1. Why a wide-column store and not a relational database here?**

- The **write rate** exceeds one primary, and access is by **row-key range**
- No multi-row transactions or ad hoc joins are needed
- If they were, distributed SQL, at a latency price

> Because the write rate is beyond what one relational primary can take, and every query is a scan by row-key range, which the wide-column store serves directly from its sorted tablets. We do not need multi-row transactions or ad hoc joins. If we did, I would choose distributed SQL instead, and pay a consensus round trip per write.

**2. Why a log and not a queue?**

- **Several consumers** need the same events, and replay after a bug
- **Order per key** matters
- Tasks of varying cost done once each would favour a queue

> Because several consumers need the same events independently, and we must be able to replay a week after a bug, which a queue cannot do once messages are acknowledged. And we need order per key. If the messages were tasks of varying cost, each done once, with redelivery and dead letters, I would choose a queue.

**3. Why a coordination service and not the cache for this lock?**

- It is a **correctness** lock: overlap corrupts data
- Needs consensus and a **fencing token** the resource checks
- A cache lock is fine only for **efficiency**

> Because this lock protects correctness: two holders would corrupt the ledger file. That needs a consensus-backed lock that survives a node failure and issues a fencing token, which the storage checks on every write. A lock in a cache is fine when two holders only means repeated work, which is not the case here.

**4. "Do not use the managed product. Build it." Which part do you open?**

- Name the **mechanisms** the product provides, then the part for each
- A cache: parts 6 and 9; a scheduler: 3, 4 and 15; a blob store: 5, 6 and 7
- Build the differentiating mechanism in depth; keep the rest as boxes

> I would name the mechanisms the product provides and open the part for each. For a cache, partitioning and caching, parts six and nine. For a scheduler, consensus, coordination and part fifteen. For a blob store, replication, partitioning and storage, parts five to seven. And I would go deep on the mechanism the question is really about, keeping the rest as clearly labelled boxes.

