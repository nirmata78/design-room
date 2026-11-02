# Global key-value store mock round (video)

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png.
     Speakers: I interviewer · C candidate · V candidate, key line (slower) · N coach. [pause: s] = silence.
     Content follows ../../SD-15-distributed-kv-store.md. Level: em (L6 / M1), per levels.md.
     The four follow-ups and their diagrams (svg/fu-*.svg) are new for this video. Target ~27 min. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: commitTs=commit_timestamp CRDT=C-R-D-T LSM=L-S-M RPO=R-P-O -->

## Before you start

[slide: v-01]
N: This is a mock system design round, for an engineering manager loop at level six. The prompt is a globally distributed key-value store. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. After the design, four manager follow-ups. Listen once, straight through. On the second pass, pause after every question, and answer it yourself first.

[slide: v-02]
N: Know what's being weighed. At this level, operations and cost count most, then leadership. Depth once: here, the network partition, second by second. And expect the manager's curveball. Build or buy. A lost region. A team that wants strong consistency everywhere. A transfer bill.

## Requirements

[slide: v-03]
I: Design a key-value store that serves reads and writes from five regions on three continents.

C: Some numbers first, then the questions that decide the design.

[slide: v-04]
C: Which regions?

I: Two in the US, one in Europe, two in Asia.

C: Three continents, so any global quorum pays a cross-continent round trip. How much data?

I: About a hundred terabytes, ten billion keys, a kilobyte on average.

C: Traffic?

I: A million reads a second, a hundred thousand writes, spread globally.

C: Ten to one, read-heavy. So local reads are the big win. And read latency?

I: Under ten milliseconds at p ninety-nine, locally.

C: Then reads must be served in-region.

[slide: v-05]
C: Write latency. What do you need?

I: You tell me. What can you promise?

C: That's the real question, and I'll answer with a number in a minute. Consistency?

I: Tell me what you can offer, and what each option costs.

C: Then I'll offer tiers, not one answer. Durability?

I: Survive losing a whole region.

C: And one more. Are most keys written mostly from one region?

I: Yes, mostly.

C: That's what lets me put each key's home near its writers.

N: "Who writes a key?" looks like a detail. It's the question that makes the whole design possible.

[slide: v-06]
C: Before designing, I'll put the impossibility on the table.

V: Strong, local and fast, in five regions. You can pick two.

[pause: 1.0]

C: Under a partition, I either refuse writes or accept divergence. And even without a partition, a quorum across continents costs a cross-continent round trip.

[slide: v-07]
C: So here's the framing.

V: Consistency is a per-operation choice. And I'll say what each one costs.

[pause: 1.0]

C: Each key range has a home region, with a consensus group for linearizable writes. Every region serves local reads, with a stated staleness. Callers who need more ask for it, and pay for it.

[slide: v-08]
C: In scope: get, put, delete and compare-and-set, placement, failover and residency. Out of scope, said aloud: multi-key transactions, which I'll mention as an extension, secondary indexes and a query language. Targets: local reads under ten milliseconds, zero data loss for strong writes on a zone failure, and eventual reads always available.

## Back of the envelope

[slide: v-09]
C: Write latency first, because it decides the architecture. A majority of five regions, across continents, is a hundred to two hundred milliseconds per write. A majority of three zones in one region is two to five. So a strong write from a client in Singapore, to a key homed in us-east, costs about two hundred and twenty milliseconds. I'd rather say that number now than have you find it.

I: And is that acceptable?

C: For the keys written near their home, writes are a few milliseconds. For the rest, it's honest, and the caller can choose a weaker tier.

[slide: v-10]
C: Storage. A hundred terabytes, three replicas in the home region, and one follower in each of the four other regions. That's a replication factor of seven, about seven hundred terabytes. Replication factor is a cost dial, and I'd set it per table. At about ten gigabytes a range, that's ten thousand ranges, each its own consensus group. Reads are about two hundred thousand a second per region, served by local followers.

N: The two-twenty milliseconds, said aloud and then dealt with. That's the moment this round turns.

## The A-P-I

[slide: v-11]
C: Consistency is a parameter. Put takes strong or eventual, and an optional expected version. It returns the version and a commit timestamp. Get takes strong, bounded staleness, session, or eventual. Compare-and-set uses the version. And the session token is just the commit timestamp of your last write. Show it on a read anywhere, and you'll read your own writes.

[slide: v-12]
C: So four tiers. Strong reads at the leader: linearizable, with the cross-continent cost. Bounded: local, unless the follower lags past the bound. Session: read your own writes anywhere. Eventual: any follower, always available, under ten milliseconds. Each tier gets its own S-L-O.

## High-level design

[slide: v-13]
C: The context. Application services in five regions call the store through an S-D-K. Platform S-R-E owns placement and failover. And the inter-region network sets the price of everything.

[slide: v-14]
C: Inside. The client S-D-K caches placement from a directory, a small consensus group that maps each range to its home region, replicas and leader. A strong write goes to the home-region Raft group. A local read goes to the nearest async follower. A placement controller splits, merges and re-homes ranges, and enforces residency. Every node runs an L-S-M storage engine, with versions and hybrid logical clock timestamps.

[slide: v-15]
C: One range, deployed. Range R1 is homed in us-east, with a Raft group of three replicas in three zones. A majority of three inside one region: two to five milliseconds, and it survives a zone loss. Every other region has an async follower for local reads, a hundred to three hundred milliseconds behind.

[slide: v-16]
C: A strong write from Tokyo. The client sends to the nearest node, which forwards to R1's leader in us-east: about a hundred and fifty milliseconds round trip. The leader appends, replicates to two zones in about two milliseconds, commits, and acknowledges with a version and commit timestamp. Total, about two hundred and twenty. Then the followers apply the log, asynchronously.

[slide: v-17]
C: Reads in Tokyo. Eventual is served by the local follower, maybe stale, under ten milliseconds. Bounded checks the follower's applied timestamp. If it's within five seconds, serve. If not, forward, or wait briefly. And strong goes to the leader, and pays the trip.

[slide: v-18]
C: Technology, with the alternatives. Range partitioning with a directory, because it can express a home region and residency per range. A consistent-hash ring can't. Raft per range at home, plus async followers. Global Raft would cost every write a hundred to two hundred milliseconds. Leaderless quorums would give no single order and need conflict resolution. An L-S-M engine for a hundred thousand writes a second. Hybrid logical clocks, because wall clocks can't order events. And the directory as a small consensus group.

[slide: v-19]
C: Inside a storage node: an R-P-C server, a range replica manager running Raft with terms, commit index and leases, an applied-timestamp tracker that serves bounded and session reads, the L-S-M engine, a snapshot sender to bootstrap followers, and a fencing check that rejects writes from a stale term.

## Deep dive one: the partition

[slide: v-20]
I: The link between Europe and the US drops for thirty seconds. What happens, second by second?

[slide: v-21]
C: Split it by where each key is homed. On the US side, writes to US-homed keys are normal, because their quorum is local. Strong writes to EU-homed keys fail or time out: their leader is unreachable. The EU side is the mirror image. Eventual reads keep working on both sides, and their staleness grows to thirty seconds.

[slide: v-22]
C: Bounded reads at five seconds work for local homes. For keys across the cut, they forward, and after five seconds, they fail. Session reads work if the token's timestamp was already applied locally. When the link heals, the followers catch up from the leaders' logs. There are no conflicts, because every key had exactly one writer.

[slide: v-23]
V: That's the C in CAP, chosen deliberately, and only for the cross-homed fraction of traffic.

[pause: 1.0]

N: Second by second, by home region, and the cost named as a fraction. That's the depth this round wants.

[slide: v-24]
I: What if a team wants writes to succeed everywhere, partition or not?

C: For designated tables, an eventual write mode: accepted in any region, replicated asynchronously, and merged with C-R-D-T semantics. Counters, sets, presence, shopping carts. What I won't do is silently apply last-write-wins to data that matters. Clocks skew, and last-write-wins drops writes.

## Deep dive two: read-your-writes

[slide: v-25]
I: A user writes in us-east, then reads in Europe. Do they see their own write?

C: Yes, with the session token. The write returns commit timestamp T. The read in Europe carries T. The follower checks whether it has applied up to T. If not, it waits, usually a hundred to three hundred milliseconds, or forwards to the leader. So no stale read of your own write, without making every read strong.

## Deep dive three: losing a region

[slide: v-26]
I: us-east is gone. Not the link. The whole region.

[slide: v-27]
C: Strong writes to ranges homed in us-east are unavailable until failover. The placement controller re-homes each range to the most up-to-date follower region, starts a new Raft group there, and updates the directory. Clients pick up the new placement.

[slide: v-28]
C: But I have to be honest about one thing.

V: Async followers mean the R-P-O is above zero.

[pause: 0.8]

C: The last few hundred milliseconds of acknowledged writes can be lost. If that's unacceptable for a table, that table gets a cross-region quorum: two replicas at home and one in a nearby region, a majority of three across two regions. Writes cost ten to seventy milliseconds, for that table only. And when the lost region comes back, it catches up from the logs, and serves reads only once it's within the staleness bound.

## Deep dive four: the hot key

[slide: v-29]
I: One key gets a hundred thousand writes a second.

C: A single linearizable key has a single-leader ceiling, by design, and I'd say so. Then the options. Push back on the access pattern: it's almost always a counter. Split it into sub-keys and sum on read. Use a C-R-D-T counter in eventual mode. Or batch writes at the leader into one log entry.

[slide: v-30]
I: And adding a sixth region?

C: Without downtime, one range at a time. New followers bootstrap from snapshots and logs, throttled to protect the leaders. They serve reads once caught up, and the directory is updated per range. Later, ranges whose writers moved can be re-homed, with a leadership transfer and a membership change.

## A requirement added mid-round

[slide: v-31]
I: EU users' data must stay in the EU. But the key space stays globally addressable.

[slide: v-32]
C: Range placement makes this a policy, not a rewrite. Ranges holding EU-resident data, by key prefix or an attribute, are homed in eu-west, with every replica in EU regions. No followers outside the EU. A client outside the EU reading those keys is forwarded to the EU, and pays the latency. It's never served from a local copy. This is exactly what a consistent-hash ring can't do, because it places by hash, not by policy.

N: The early choice of range partitioning just paid for itself. Good candidates connect the two out loud.

## Failures and operations

[slide: v-33]
C: The failures. A zone lost in a home region: nothing visible, two of three replicas remain. A home region lost: the failover runbook, the R-P-O stated, quorum tables for zero loss. A leader pause that risks two leaders: Raft terms, fencing at the storage layer, and leases with bounded clock skew. The directory down: clients use cached placement. A replication lag spike: bounded reads forward or fail, and lag alerts per region.

[slide: v-34]
C: For S-L-Os, the honest view is a matrix. Local read latency per region. Strong write latency by client region and home region, because an average would hide the two-twenty. And replication lag per region, because it drives the bounded-read S-L-O.

[slide: v-35]
C: Cost. Seven hundred terabytes at replication factor seven. And replication egress: a hundred thousand writes a second, a kilobyte each, to four remote regions, is about thirty-five terabytes a day. Both have dials per table: the replication factor, and the number of follower regions.

N: An S-L-O matrix instead of an average, and cost dials per table. That's the operations signal for a manager.

## The manager layer

[slide: v-36]
I: How would you build it?

C: First question: should we? Managed global databases cover most of this. I'd buy first, and build only if placement control or cost demands it. If we build: the core first, single-region Raft ranges, the directory and the S-D-K. Then global: followers, tiers, failover and residency. The one-way doors are the partitioning scheme and the consistency contract in the A-P-I. Those get the most review.

[slide: v-37]
C: Three teams. Storage and replication, who own the R-P-O. Placement and directory, who own failover tooling and residency. And the client S-D-K and A-P-I, who own the consistency contract. Each tier's S-L-O has an owner.

[slide: v-38]
C: To close.

V: The cross-continent cost appears only when a caller asks for it.

[pause: 0.8]

C: It's a range-partitioned store. Each range has a home region running a three-zone Raft group for fast linearizable writes, and async followers everywhere else for local reads. Callers choose strong, bounded, session or eventual. Under a partition, each side keeps serving its own keys, and stale reads for the rest. Next, I'd add cross-region quorums for zero-loss tables, and residency-aware placement.

I: Thanks. Some questions on the management side.

## Follow-up 1: build or buy

[slide: v-39]
I: Your C-T-O wants us to build this in-house. A managed global database covers most of it. What do you recommend?

[slide: v-40]
C: I'd write down the must-haves first: residency, the consistency tiers, the R-P-O, the scale. Then the total cost over three years: the managed bill, against roughly a team of engineers, forever. Then the exit cost: how locked in we'd be, how we'd export data and migrate. Engineering effort is a cost too. A home-grown database is a decade-long commitment.

V: I'd recommend buying, with a named trigger to revisit it.

[pause: 0.8]

C: For example: if the bill passes a stated number, or a placement requirement appears that the product can't meet. And I'd bring this to the C-T-O as a document, so we disagree about facts, not instincts.

N: A recommendation, its cost, and the condition that would change it. That's how a manager disagrees upward.

## Follow-up 2: the region goes dark

[slide: v-41]
I: Saturday night, us-east goes dark. Failing over loses the last few hundred milliseconds of writes. Do you?

[slide: v-42]
C: First, it shouldn't be decided at two in the morning for the first time. The runbook names who decides, and on what. Detect: write availability by home region pages on-call. Then decide: if the region looks like it'll be back in minutes, waiting may lose nothing. If not, failing over trades a small, known data loss for availability. That trade is pre-agreed per table, and zero-loss tables don't lose anything anyway.

V: Writes to Europe-homed keys never stopped. Only strong writes homed in us-east waited.

[pause: 0.8]

C: Afterwards, we reconcile: report exactly what was in the lost tail, to the table owners. And a game day, before the next one.

N: A pre-agreed decision with a named owner. Not a reflex, and not a debate during the outage.

## Follow-up 3: strong everywhere

[slide: v-43]
I: The payments team says eventual consistency is dangerous. They want strong to be the default, for everyone.

[slide: v-44]
C: They're right to worry, and wrong about the fix. Strong for everyone would put the cross-continent cost on every team, including those who don't need it. I'd propose session consistency as the default: read-your-writes, local and fast, which removes the surprises people actually hit. Strong is opt-in per table, and the S-D-K shows its latency by client and home region, so nobody chooses it blind. And every quarter, we review which tables pay for strong, and why.

V: A safe default with a visible price beats a blanket rule.

[pause: 0.8]

N: You took the concern seriously, and kept the choice with the team that owns the data.

## Follow-up 4: the transfer bill

[slide: v-45]
I: Last one. The inter-region transfer bill is now the biggest line on our cloud invoice.

[slide: v-46]
C: Slice by table: who replicates to how many regions, and who actually reads there? Often a table has followers in regions that never read it. Remove those: follower regions are a dial per table. Then batch and compress replication. And charge the cost back to the table owners, so it's visible where decisions are made. I'd report cost per million writes, so growth doesn't hide the trend.

N: The diagnosis order is the answer. And none of these levers touches the consistency contract.

## Debrief

[slide: v-47]
N: Here's where the round lands. Strong candidates name CAP. Exceptional ones add latency, and say the two-twenty milliseconds out loud. Strong ones say replication. Exceptional ones say Raft at home, async followers, and a directory. Strong ones offer strong or eventual. Exceptional ones offer four tiers, each with a cost and an S-L-O. And on region loss, exceptional ones name the R-P-O honestly.

[slide: v-48]
N: Five checks, before the real round. The impossibility, on the table first. A number for a cross-continent strong write. Consistency per operation, with its price. The partition, second by second. And R-P-O on region loss, said honestly. Good luck.
