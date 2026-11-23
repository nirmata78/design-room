# SD-03 Event counting and billing rollups: reference solution (Staff L6/L7, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: SLO=S-L-O SLOs=S-L-Os SLI=S-L-I TTL=T-T-L API=A-P-I APIs=A-P-Is SDK=S-D-K SDKs=S-D-Ks TB=terabytes PB=petabytes MB=megabytes GB=gigabytes HTTP=H-T-T-P HTTPS=H-T-T-P-S SQL=S-Q-L ID=I-D IDs=I-Ds CPU=C-P-U p99=P-ninety-nine Kafka=Kahf-kah Kafka's=Kahf-kahs dedup=dee-dupe Flink=Flink ClickHouse=Click-House Iceberg=Iceberg GCS=G-C-S UUIDv7=U-U-I-D-version-seven RocksDB=Rocks-D-B HyperLogLog=Hyper-Log-Log CTR=click-through_rate ack=ack acks=acks EM=E-M -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: Counting clicks sounds like n equals n plus one. It is one of the most asked questions at Google and Meta, because at thirty million events a second the hard part is not counting fast. It is counting once, in the right hour, and being able to prove it.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Design the system that counts ad impressions and clicks. Advertisers watch their numbers live on a dashboard, and they are billed on the hourly totals.
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook, as one picture: the same hour of one campaign has three numbers.
C: Ten seconds in, the live number: fast and provisional, because duplicates and late events are still arriving. At forty-eight hours, the final number: exact, and invoiced. Nine days later fraud invalidates two percent, and a third number must become an adjustment, never an edit.
C: The whole design is about producing all three from one source, and saying which one you are looking at.
[pause: 1.1]

[slide: v-004]
[pause: 1.0]
N: Five axes, one at a time.
[reveal: v-005]
[pause: 0.45]
N: Requirements. Weak: one number for everything. Strong: which numbers are money, how late events arrive, who can take them back.
[reveal: v-006]
[pause: 0.45]
N: Correctness. Weak: n equals n plus one, or exactly-once as a name. Strong: an I-D minted at the source, event time, and numbers replaced rather than incremented.
[reveal: v-007]
[pause: 0.45]
N: Trade-offs. Reciting Lambda and Kappa is not one. Saying what you run twice, and what each run gives up, is.
[reveal: v-008]
[pause: 0.45]
N: Depth. Kafka and Flink are names; watermarks, keyed state and pinned re-runs are the level down.
[reveal: v-009]
[pause: 0.45]
N: Operations. Lag and C-P-U stay green while the count is wrong; conservation checks and canaries don't.
[reveal: v-010]
[pause: 0.45]
C: And the rule I'll keep for the whole round: the bill is the product. The dashboard is a preview of it, and must say so.
[pause: 1.0]

[slide: v-011]
[pause: 0.7]
V: Count once, from one log, with one piece of code run twice: fast and provisional for the dashboard, exact and pinned for the bill. Never increment a number you can recompute. Replace it.
[pause: 1.6]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-012]
[pause: 1.2]
C: The scale first, then six questions. Each answer moves the design.
[pause: 1.8]

[slide: v-013]
[pause: 0.6]
C: The interviewer gives me the scale, and I write it down first.
[reveal: v-014]
[pause: 0.45]
C: Twenty-five trillion impressions and two hundred and fifty billion clicks a month. A one percent click-through rate.
[reveal: v-015]
[pause: 0.45]
C: Raw events are kept six months, about a hundred and fifty trillion of them.
[reveal: v-016]
[pause: 0.45]
C: And the peak: thirty million events a second in the evening, three times the average. Inside it, one prime-time ad during a sports break takes two million impressions a second on its own.
[reveal: v-017]
[pause: 0.45]
C: Every number I use later starts from one of these three, and I'll say which.
[pause: 0.8]

[slide: v-018]
[pause: 0.6]
C: How fresh does the dashboard have to be, and the bill?
[reveal: v-019]
[pause: 0.45]
I: Within about ten seconds for the dashboard. The bill is hourly totals, final within two days.
C: So two clocks. And if someone asks for sub-second, I'd ask back: for one headline number, maybe; for slicing by country and hour, it costs a different system.
[pause: 0.6]

[slide: v-020]
[pause: 0.6]
C: Which numbers have to be exact?
[reveal: v-021]
[pause: 0.45]
I: The bill: exact, and auditable. The dashboard can be slightly off, but it has to converge to the bill.
C: That sentence is the design. One exact run for money, one fast run for people, and the fast one never disagrees for long.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: Can the same event arrive twice, or late?
[reveal: v-023]
[pause: 0.45]
I: Yes. S-D-Ks retry on network errors. Phones buffer offline for hours, sometimes days. And client clocks are skewed.
C: Duplicates mean an I-D per event. Late means event time, not arrival time. Skewed means I can't trust that time blindly. Three challenges.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: Who decides that a click was fraud, and when?
[reveal: v-025]
[pause: 0.45]
I: A separate system. It can invalidate events after the invoices have gone out.
C: So a closed hour can change. I need versions of an hour, and a way to bill the difference without editing an invoice.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: How long do we keep events and totals?
[reveal: v-027]
[pause: 0.45]
I: Raw events six months; the dispute window is ninety days. Aggregates seven years. And Finance wants a re-run of any day to give the same numbers.
C: Same numbers on a re-run means the aggregation is a pure function of inputs I can pin. I'll hold myself to that.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Four functional requirements.
[reveal: v-029]
[pause: 0.45]
C: One, record: accept the events, acknowledge only once they are durable, and a retry changes nothing.
[reveal: v-030]
[pause: 0.45]
C: Two, live: impressions, clicks, spend and an approximate unique reach per ad and campaign, within ten seconds.
[reveal: v-031]
[pause: 0.45]
C: Three, bill: exact hourly totals, final at a cutoff, versioned, and exported to invoicing.
[reveal: v-032]
[pause: 0.45]
C: Four, correct: late events and invalidations reach a closed hour as a new version and an adjustment line. A sent invoice is never edited. Each of these gets a sequence later.
[pause: 0.8]

[slide: v-033]
[pause: 0.6]
C: The numbers, and they are initial targets.
[reveal: v-034]
[pause: 0.45]
C: Thirty million events a second at peak, acknowledged within fifty milliseconds at the ninety-ninth percentile.
[reveal: v-035]
[pause: 0.45]
C: Live counts within ten seconds.
[reveal: v-036]
[pause: 0.45]
C: The bill final forty-eight hours after the hour, and reproducible bit for bit.
[reveal: v-037]
[pause: 0.45]
C: Four nines on ingest, because an event we drop is revenue we cannot bill.
[reveal: v-038]
[pause: 0.45]
C: And an acknowledged event survives losing a whole zone.
[pause: 0.8]

[slide: v-039]
[pause: 0.6]
C: In scope: ingest, dedup, live counts, approximate reach, the hourly billing totals with versions and corrections, an audit trail and reconciliation.
[reveal: v-040]
[pause: 0.45]
C: Out, on purpose: fraud detection itself, ad serving and the auction, budget pacing, invoicing and payment, and conversion attribution.
[reveal: v-041]
[pause: 0.45]
C: One of those I'd say aloud: budget pacing reads the live counts to stop a campaign that has spent its budget. That is why the live numbers must be fast, even though they are not the bill.
[pause: 0.8]

[slide: v-042]
[pause: 1.3]
C: Before any boxes inside it, the system in its context.
[reveal: v-043]
[pause: 0.45]
C: Ad clients: S-D-Ks in apps, browsers, and ad servers. They report every impression and click, in batches. Ninety-nine percent of the traffic.
[reveal: v-044]
[pause: 0.45]
C: In the middle, the system, one box for now: live counts and exact hourly totals.
[reveal: v-045]
[pause: 0.45]
C: Advertisers read dashboards and are billed.
[reveal: v-046]
[pause: 0.45]
C: A fraud system flags invalid traffic, and it can do that late, after the bill.
[reveal: v-047]
[pause: 0.45]
C: And invoicing turns our final hours into invoices. Nothing on the ingest path waits for any of them.
[pause: 1.1]

[slide: v-048]
[pause: 0.7]
V: The core is three things. An idempotent, durable intake. One aggregation, run twice. And versioned final hours, with a correction path.
[pause: 0.8]
N: Notice the candidate fixed the scale, named the core and drew the context before any internals. That is the scoping signal.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-049]
[pause: 1.2]
C: Numbers next. Each starts from the scale line, and each ends in a decision. They are illustrative, not anyone's real figures.
[pause: 1.8]

[slide: v-050]
[pause: 1.0]
C: Traffic, from the monthly volumes.
[reveal: v-051]
[pause: 0.45]
C: Twenty-five trillion impressions over two point six million seconds is about ten million a second. Three times that in the evening: thirty million a second, one point eight billion a minute. No database takes a write per event at that rate, so a partitioned log it is.
[reveal: v-052]
[pause: 0.45]
C: Clicks are a hundredth of that: a hundred thousand a second, three hundred thousand at peak. They ride the same pipeline, and a billable click is keyed by the impression it came from, so a double-click bills once.
[reveal: v-053]
[pause: 0.45]
C: At two hundred bytes an event, the peak is six gigabytes a second, eighteen with three replicas. About a thousand partitions and eighty brokers. Illustrative, but it sets the order of magnitude.
[pause: 1.0]

[slide: v-054]
[pause: 1.0]
C: Where the bytes live.
[reveal: v-055]
[pause: 0.45]
C: Three days of log at the two-gigabyte average is five hundred and twenty terabytes; compressed and replicated, about three hundred and ninety. So brokers keep three days, and a replay older than that reads the lake.
[reveal: v-056]
[pause: 0.45]
C: The lake: twenty-five trillion events at about twenty-five bytes each, compressed in columns, is point six petabytes a month, three point eight for six months. Object storage, partitioned by the hour the event happened.
[reveal: v-057]
[pause: 0.45]
C: And dedup. Ten minutes of event I-Ds at the peak is eighteen billion I-Ds, about point seven terabytes. Spread over five hundred and twelve stream tasks that is about one point four gigabytes each. In one Redis set, it would be eighteen billion keys.
[pause: 1.0]

[slide: v-058]
[pause: 1.0]
C: Two numbers that decide the hard parts.
[reveal: v-059]
[pause: 0.45]
C: The hot ad: two million impressions a second on one key, against roughly three hundred thousand updates a second for one stream task. Keyed by ad, one task drowns. So I combine before the shuffle, and challenge three is about that.
[reveal: v-060]
[pause: 0.45]
C: And the money. If three tenths of a percent of click batches are retried, that's seven hundred and fifty million duplicate clicks a month. At fifty cents a click, about three hundred and seventy-five million dollars of overbilling. Illustrative, but it says dedup is the crux of this question, not an optimisation.
[pause: 1.0]

[slide: v-061]
[pause: 1.3]
C: The freshness budget, worst case. One second of batching in the S-D-K. Half a second through the collector and the log. Two seconds for the stream job's early results. A second to insert, a second to query. About five and a half seconds against ten.
C: The spare is for a slow minute, not for a synchronous call. And it says why the stream job emits early results every two seconds rather than waiting for a minute to close.
[pause: 1.1]

[pause: 1.4]

## 3 Theory

[slide: v-062]
[pause: 1.2]
C: Before any design, the theory: what makes this hard, in terms that will outlive any product name. Five mechanisms, then the options, then what will go wrong.
[pause: 1.8]

[slide: v-063]
[pause: 0.6]
C: What it is, and what it is not.
[reveal: v-064]
[pause: 0.45]
V: Counting events that are money: each one counted once, in the hour it happened, with every billed number reproducible and traceable to its events.
[reveal: v-065]
[pause: 0.45]
C: It is not monitoring. Metrics can be approximate and can drop a sample. A bill cannot.
[reveal: v-066]
[pause: 0.45]
C: It is not analytics uniques. Two percent off is fine for reach on a dashboard, never on an invoice.
[reveal: v-067]
[pause: 0.45]
C: And it is not a ledger. A ledger moves balances with double entry. We produce the counts that a ledger later charges.
[pause: 0.8]

[slide: v-068]
[pause: 0.6]
C: The properties, safety and liveness separately. Safety is what must never happen.
[reveal: v-069]
[pause: 0.45]
V: S-one: an accepted event is never lost, and never billed twice.
[reveal: v-070]
[pause: 0.45]
V: S-two: it is billed in the hour it happened, not at all once invalidated, and a sent invoice is never edited.
[reveal: v-071]
[pause: 0.45]
V: S-three: every billed number can be recomputed and traced to its events.
[reveal: v-072]
[pause: 0.45]
C: Liveness is what must eventually happen. L-one: every accepted event reaches a final hour, or an adjustment, within forty-eight hours plus the run.
[reveal: v-073]
[pause: 0.45]
C: L-two: the live counts reflect an event within ten seconds. Notice L-two is the only one with seconds in it. That's the tension.
[pause: 0.8]

[slide: v-074]
[pause: 0.6]
C: The tension, which the cold open drew as one hour with three numbers.
[reveal: v-075]
[pause: 0.45]
C: Answer sooner: count as events arrive. Fresh, but duplicates and late events are still coming, so the number is provisional.
[reveal: v-076]
[pause: 0.45]
C: Answer right: wait until the hour is complete, and count everything once. Exact, but two days late.
[reveal: v-077]
[pause: 0.45]
C: The way out is not to pick one. It is to do both from one immutable log, with the same code, so the fast number converges to the right one and any difference has a name.
[pause: 0.8]

[slide: v-078]
[pause: 0.6]
C: Mechanism one: idempotency by event I-D.
[reveal: v-079]
[pause: 0.45]
C: It protects S-one, counting once.
[reveal: v-080]
[pause: 0.45]
C: The S-D-K or the ad server mints an I-D at the moment the event happens, not when it is sent. Every later stage keeps the first copy of each I-D and drops the rest.
[reveal: v-081]
[pause: 0.45]
C: It rules out a retry, a redelivery or a replay being counted twice.
[reveal: v-082]
[pause: 0.45]
C: It costs an I-D minted upstream, which we do not control, and state per I-D for as long as the dedup window lasts. We sized that: point seven terabytes for ten minutes.
[pause: 0.8]

[slide: v-083]
[pause: 0.6]
C: Mechanism two: event time, with watermarks.
[reveal: v-084]
[pause: 0.45]
C: It protects S-two, the right hour, and with early results, L-two.
[reveal: v-085]
[pause: 0.45]
C: I count by the time in the event, not the time it arrived. A watermark is the job's claim that nothing older is still coming; a window's final result fires when it passes, early results before.
[reveal: v-086]
[pause: 0.45]
C: It rules out a late or replayed event landing in the hour it happened to arrive in.
[reveal: v-087]
[pause: 0.45]
C: It costs waiting, state for every window still open, and a cutoff. After the cutoff, a late event becomes a correction, not a count.
[pause: 0.8]

[slide: v-088]
[pause: 0.6]
C: Mechanism three, the one this whole design leans on: a deterministic re-run over an immutable log, where outputs replace, never increment.
[reveal: v-089]
[pause: 0.45]
C: It protects S-one under replay, and S-three, reproducibility.
[reveal: v-090]
[pause: 0.45]
C: The output is a pure function of pinned inputs, written as a replacement keyed by what it counts: this ad and minute, or this campaign, hour and version. Running it again writes the same row again.
[reveal: v-091]
[pause: 0.45]
C: It rules out a replay doubling a number, and an invoice nobody can reproduce.
[reveal: v-092]
[pause: 0.45]
C: It costs keeping raw events for the whole retention, and computing twice.
[pause: 0.8]

[slide: v-093]
[pause: 0.6]
C: Mechanism four: two-stage aggregation, which is the sharded counter idea applied in time.
[reveal: v-094]
[pause: 0.45]
C: It protects L-two when the load is skewed.
[reveal: v-095]
[pause: 0.45]
C: Each task sums the events it already has, for one second, and only then sends a partial sum to be merged by key. In the store, a hot counter is N shard rows, summed on read.
[reveal: v-096]
[pause: 0.45]
C: It rules out one hot key stalling one task, and with it the whole job.
[reveal: v-097]
[pause: 0.45]
C: It costs one more stage, a sum on every read, and a second of delay.
[pause: 0.8]

[slide: v-098]
[pause: 0.6]
C: Mechanism five, small but asked about: HyperLogLog, for unique reach.
[reveal: v-099]
[pause: 0.45]
C: It protects L-two for one number advertisers love: how many distinct people saw the ad.
[reveal: v-100]
[pause: 0.45]
C: Each user I-D is hashed into one of four thousand and ninety-six registers, each keeping the longest run of leading zeros it has seen. Sketches merge by taking the maximum per register, so minutes merge into hours.
[reveal: v-101]
[pause: 0.45]
C: It rules out exact distinct counts per campaign and minute, which would not fit in memory.
[reveal: v-102]
[pause: 0.45]
C: It costs about one point six percent error, and it cannot remove a user. So it is never on the bill.
[pause: 0.8]

[slide: v-103]
[pause: 1.0]
C: Five ways to do it.
[reveal: v-104]
[pause: 0.45]
C: A, a counter per event in a database: thirty million writes a second, hot rows, and every retry counts.
[reveal: v-105]
[pause: 0.45]
C: B, batch only: exact, but the dashboard is a day behind.
[reveal: v-106]
[pause: 0.45]
C: C, stream only, where the stream's result is the bill: a late event past the state's lifetime is lost, and a bug fix means replaying months.
[reveal: v-107]
[pause: 0.45]
C: D, Lambda, written twice: it works until the two implementations drift.
[reveal: v-108]
[pause: 0.45]
C: E, which I pick: one aggregation code, run twice. Streaming for the dashboard, then the same operators in batch mode over each closed hour.
[reveal: v-109]
[pause: 0.45]
V: Kappa in code, Lambda in time. I give up computing twice, and a bill that waits forty-eight hours.
[pause: 1.0]

[slide: v-110]
[pause: 1.0]
C: Where each one will live. I'll draw the system once, in the design chapter, and these labels come back on it at the end.
[reveal: v-111]
[pause: 0.45]
C: M-one, the event I-D: minted in the S-D-K, dropped if seen, for ten minutes on the live path and for the whole hour on the billing run.
[reveal: v-112]
[pause: 0.45]
C: M-two, event time: a watermark two minutes behind the latest event, and a billing cutoff at forty-eight hours.
[reveal: v-113]
[pause: 0.45]
C: M-three, replace, never increment: in the live store and the billing tables, rows keyed by what they count, with a version.
[reveal: v-114]
[pause: 0.45]
C: M-four, two-stage sums: five hundred and twelve partial sums a second, and shard rows summed on read.
[reveal: v-115]
[pause: 0.45]
C: M-five, sketches: reach per campaign and minute, merged when the dashboard asks.
[pause: 1.0]

[slide: v-116]
[pause: 1.3]
C: Mechanism two at protocol level: one window, ad seventy-seven, the minute starting at fourteen hundred, fed by two partitions.
[reveal: v-117]
[pause: 0.45]
C: Partition one delivers an impression with event time fourteen hundred and fifty-eight seconds.
[reveal: v-118]
[pause: 0.45]
C: Partition two, one at fourteen oh one thirty.
[reveal: v-119]
[pause: 0.45]
C: The watermark is the minimum over partitions of the latest time minus two minutes: thirteen fifty-eight fifty-eight. The minute is still open.
[reveal: v-120]
[pause: 0.45]
C: But the dashboard should not wait, so the window emits an early result: twelve hundred and twelve, version one.
[reveal: v-121]
[pause: 0.45]
C: Later events arrive, from both partitions.
[reveal: v-122]
[pause: 0.45]
C: Now the watermark is fourteen oh one oh five. It has passed the end of the minute.
[reveal: v-123]
[pause: 0.45]
C: So the on-time result fires: thirteen eighteen, version two, and it replaces version one. It does not add to it.
[reveal: v-124]
[pause: 0.45]
C: Then a late event for that minute, within the allowed hour.
[reveal: v-125]
[pause: 0.45]
C: Version three, thirteen nineteen. No lock and no wall clock: event times, a minimum, and a version.
[pause: 1.1]

[slide: v-126]
[pause: 1.0]
C: The failure catalogue. It becomes the challenge list.
[reveal: v-127]
[pause: 0.45]
C: One: the same event arrives three times.
[reveal: v-128]
[pause: 0.45]
C: Two: events arrive a day late, with skewed clocks.
[reveal: v-129]
[pause: 0.45]
C: Three: one ad takes two million impressions a second.
[reveal: v-130]
[pause: 0.45]
C: Four: a job crashes, or a bug forces a four-hour replay.
[reveal: v-131]
[pause: 0.45]
C: Five: fraud invalidates clicks after the invoice.
[reveal: v-132]
[pause: 0.45]
C: And six: a number is wrong, and nobody notices. I'll come back to each.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-133]
[pause: 1.2]
C: The A-P-I next, then the data. Every endpoint is tagged with the requirement it serves.
[pause: 1.8]

[slide: v-134]
[pause: 1.0]
C: One write endpoint, and it serves F-R-one. A batch of up to five hundred events.
C: Three fields matter. The event I-D is a U-U-I-D version seven, minted by the S-D-K at the moment the event happens, not when it is sent, so a retry carries the same I-D. A click names the impression it came from, so a double-click is two click events but one billable click. And the client time is kept as the client said it; we decide later how much to trust it.
C: The answer is two-oh-two, and only after the log has acknowledged the batch. The I-D makes retries harmless, and the impression I-D makes clicks billable once.
[pause: 1.0]

[slide: v-135]
[pause: 1.0]
C: Three more endpoints.
[reveal: v-136]
[pause: 0.45]
C: The live read, for F-R-two. Every response carries an as-of time and the word provisional. The dashboard says what it is.
[reveal: v-137]
[pause: 0.45]
C: The billing read, for F-R-three: each hour with its version and the I-D of the manifest that produced it. That I-D is how we answer a dispute.
[reveal: v-138]
[pause: 0.45]
C: And corrections, for F-R-four: the fraud system posts invalidated event I-Ds with their hours, a reason and the version of the rule that flagged them. Append only.
[pause: 1.0]

[slide: v-139]
[pause: 1.3]
C: The conceptual model, entity by entity.
[reveal: v-140]
[pause: 0.45]
C: An advertiser.
[reveal: v-141]
[pause: 0.45]
C: An advertiser runs many campaigns.
[reveal: v-142]
[pause: 0.45]
C: A campaign has many ads.
[reveal: v-143]
[pause: 0.45]
C: An ad receives many events, each with its event I-D, its event time and, for a click, the impression it came from.
[reveal: v-144]
[pause: 0.45]
C: Events are counted in an hour total. The hour total is a weak entity: it exists only for a campaign, and its key includes the hour and a version, because a correction creates a new version rather than changing the old one.
[reveal: v-145]
[pause: 0.45]
C: And an invalidation voids an event, with a reason.
[reveal: v-146]
[pause: 0.45]
C: An hour is never edited. That one rule removes a whole class of disputes.
[pause: 1.1]

[slide: v-147]
[pause: 1.3]
C: The physical tables, one at a time.
[reveal: v-148]
[pause: 0.45]
C: Events, in an Iceberg table on object storage, partitioned by event hour. Point six petabytes a month.
[reveal: v-149]
[pause: 0.45]
C: Billing hour: the primary key is campaign, ad, hour and version. A correction adds a row; none is updated. It points to a manifest.
[reveal: v-150]
[pause: 0.45]
C: The manifest records what one billing run read: the events snapshot, the rate-card version, the invalidation snapshot, and the job's image digest.
[reveal: v-151]
[pause: 0.45]
C: Live minute, in ClickHouse: keyed by campaign, ad, minute and a shard number, with a version column. A newer version replaces an older one.
[reveal: v-152]
[pause: 0.45]
C: Invalidations, append only.
[reveal: v-153]
[pause: 0.45]
C: And adjustments: per campaign, hour and version, the difference that invoicing applies.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-154]
[pause: 1.2]
C: The design in three versions. Each answers the objection to the one before, and it is one picture from here to the end: later slides only show what changes on it.
[pause: 1.8]

[slide: v-155]
[pause: 1.3]
C: Version one is the simplest thing that is exact, and I'll draw it in the order an event travels.
[reveal: v-156]
[pause: 0.45]
C: Ad clients send batches of events.
[reveal: v-157]
[pause: 0.45]
C: A collector validates them, stamps the server time, and appends them.
[reveal: v-158]
[pause: 0.45]
C: To a partitioned, replicated event log. This is the one copy everything else is derived from.
[reveal: v-159]
[pause: 0.45]
C: Every five minutes the log is landed as files in an event lake, partitioned by the hour the event happened.
[reveal: v-160]
[pause: 0.45]
C: A billing job reads one closed hour, removes duplicates and counts.
[reveal: v-161]
[pause: 0.45]
C: And writes billing tables.
[reveal: v-162]
[pause: 0.45]
C: A reporting A-P-I serves them.
[reveal: v-163]
[pause: 0.45]
C: To the advertiser. It is exact and replayable. The objection: the dashboard is an hour or a day behind, and budget pacing can't run on that.
[pause: 1.1]

[slide: v-164]
[pause: 1.3]
C: Version two answers that.
[reveal: v-165]
[pause: 0.45]
C: Everything from version one stays where it was.
[reveal: v-166]
[pause: 0.45]
C: New, a live aggregator: a stream job on the same log, with the same aggregation code. It counts by the minute and emits early results.
[reveal: v-167]
[pause: 0.45]
C: New, a live store, which holds the live minutes, and also gets the final hours loaded from the billing job. So the A-P-I now reads one store for both. The objection: a bill has to be final, yet late events and fraud corrections keep arriving after the hour.
[pause: 1.1]

[slide: v-168]
[pause: 1.3]
C: Version three answers that.
[reveal: v-169]
[pause: 0.45]
C: Version two, carried as it was.
[reveal: v-170]
[pause: 0.45]
C: New, the fraud system. Its invalidations arrive on an append-only topic, and the billing job re-runs the affected hours as new versions.
[reveal: v-171]
[pause: 0.45]
C: New, invoicing, which receives final hours and, when a version changes after an invoice, an adjustment line. This is the baseline. From here it only changes by deltas.
[pause: 1.1]

[slide: v-172]
[pause: 1.0]
C: The containers, one line each, in the order an event meets them.
[reveal: v-173]
[pause: 0.45]
C: The collector: validation, the server time and the append. No I-Ds, no dedup, so it stays stateless at thirty million a second. Go on Kubernetes, with a disk spool if the log is unreachable.
[reveal: v-174]
[pause: 0.45]
C: The event log: the one copy, keyed by event I-D, for three days.
[reveal: v-175]
[pause: 0.45]
C: The live aggregator: dedup for ten minutes, partial sums, minute windows and reach.
[reveal: v-176]
[pause: 0.45]
C: The live store: live minutes, and a copy of the final hours.
[reveal: v-177]
[pause: 0.45]
C: The event lake: every event for six months, by event hour.
[reveal: v-178]
[pause: 0.45]
C: The billing job and its tables: the exact hour, as versions, each with a manifest.
[reveal: v-179]
[pause: 0.45]
C: And the reporting A-P-I, which always says provisional or final. On the ingest path: the collector and the log. Nothing else.
[pause: 1.0]

[slide: v-180]
[pause: 1.3]
C: The live path, numbered.
[reveal: v-181]
[pause: 0.45]
C: One: the S-D-K posts a batch to the collector.
[reveal: v-182]
[pause: 0.45]
C: Two: the collector appends it with all replicas acknowledging, then answers two-oh-two.
[reveal: v-183]
[pause: 0.45]
C: Three: the live aggregator consumes it.
[reveal: v-184]
[pause: 0.45]
C: Four: it writes minute rows, early every two seconds, final when the watermark passes.
[reveal: v-185]
[pause: 0.45]
C: Five: the advertiser opens a dashboard.
[reveal: v-186]
[pause: 0.45]
C: Six: the A-P-I queries the live store. About five seconds end to end.
[pause: 1.1]

[slide: v-187]
[pause: 1.3]
C: The billing path, numbered.
[reveal: v-188]
[pause: 0.45]
C: One: the log lands files in the lake every five minutes, in the partition of each event's hour.
[reveal: v-189]
[pause: 0.45]
C: Two: at forty-eight hours, the billing job reads that hour at a snapshot.
[reveal: v-190]
[pause: 0.45]
C: Three: it replaces the hour in the billing tables as the next version.
[reveal: v-191]
[pause: 0.45]
C: Four: it loads the final hour into the live store, so the dashboard switches from provisional to final.
[reveal: v-192]
[pause: 0.45]
C: Five: invoicing receives the final hour.
[pause: 1.1]

[slide: v-193]
[pause: 1.3]
C: Record, as a sequence.
[reveal: v-194]
[pause: 0.45]
C: The S-D-K posts five hundred events, each with its I-D minted at creation.
[reveal: v-195]
[pause: 0.45]
C: The collector validates, stamps the server time, and clamps a client time that is too far off.
[reveal: v-196]
[pause: 0.45]
C: It produces to Kafka keyed by event I-D, with acks equals all.
[reveal: v-197]
[pause: 0.45]
C: Two of three replicas have it.
[reveal: v-198]
[pause: 0.45]
C: Only now: two-oh-two.
[reveal: v-199]
[pause: 0.45]
C: If that answer is lost, the S-D-K retries the same batch with the same I-Ds. That's challenge one.
[pause: 1.1]

[slide: v-200]
[pause: 1.3]
C: Live, as a sequence.
[reveal: v-201]
[pause: 0.45]
C: Flink consumes events, partitioned by event I-D.
[reveal: v-202]
[pause: 0.45]
C: It drops any I-D it has seen in ten minutes, and sums per ad per second.
[reveal: v-203]
[pause: 0.45]
C: Each ad-and-minute window emits an early result every two seconds.
[reveal: v-204]
[pause: 0.45]
C: As rows with a version into ClickHouse.
[reveal: v-205]
[pause: 0.45]
C: The advertiser asks for campaign forty-two, by minute.
[reveal: v-206]
[pause: 0.45]
C: The A-P-I takes the latest version of each row and sums the shards.
[reveal: v-207]
[pause: 0.45]
C: Sixty rows back.
[reveal: v-208]
[pause: 0.45]
C: As of fourteen oh five and seven seconds, marked provisional.
[pause: 1.1]

[slide: v-209]
[pause: 1.3]
C: The bill, as a sequence.
[reveal: v-210]
[pause: 0.45]
C: The hour starting at fourteen hundred closes forty-eight hours later.
[reveal: v-211]
[pause: 0.45]
C: The closer asks the lake for a snapshot of that hour as of the cutoff.
[reveal: v-212]
[pause: 0.45]
C: Snapshot seven million three hundred and forty-two thousand.
[reveal: v-213]
[pause: 0.45]
C: It starts the run with a manifest: that snapshot, rate card eighteen, invalidation list nine-oh-three, and the job's image.
[reveal: v-214]
[pause: 0.45]
C: The job removes every duplicate, drops invalid events, prices in integer micro-dollars and sums.
[reveal: v-215]
[pause: 0.45]
C: It replaces the hour as version one, with its manifest.
[reveal: v-216]
[pause: 0.45]
C: And the final hour goes to invoicing.
[pause: 1.1]

[slide: v-217]
[pause: 1.3]
C: Correct, as a sequence.
[reveal: v-218]
[pause: 0.45]
C: The fraud system invalidates three point one million clicks from botnet seventeen, with their hours.
[reveal: v-219]
[pause: 0.45]
C: The hours are marked dirty.
[reveal: v-220]
[pause: 0.45]
C: The closer re-runs each one with a new manifest.
[reveal: v-221]
[pause: 0.45]
C: Version two of each hour is written. Version one stays.
[reveal: v-222]
[pause: 0.45]
C: The difference to what was invoiced: minus one point five five million dollars.
[reveal: v-223]
[pause: 0.45]
C: It goes on the next invoice as adjustment lines. Challenge five drills into this.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-224]
[pause: 1.2]
C: Now one level down. The same picture with what each box runs on, the two containers that matter most opened up, and for each choice, what I rejected and why.
[pause: 1.8]

[slide: v-225]
[pause: 1.3]
C: The same container view; only the type lines changed. The seven boxes in scope, one at a time.
[reveal: v-226]
[pause: 0.45]
C: The collector: Go on Kubernetes, acks equals all, with a disk spool.
[reveal: v-227]
[pause: 0.45]
C: The event log: Kafka, a thousand and twenty-four partitions, keyed by event I-D.
[reveal: v-228]
[pause: 0.45]
C: The live aggregator: Flink, streaming.
[reveal: v-229]
[pause: 0.45]
C: The live store: ClickHouse, replacing rows by version.
[reveal: v-230]
[pause: 0.45]
C: The event lake: Iceberg tables on Google Cloud Storage, Parquet by event hour.
[reveal: v-231]
[pause: 0.45]
C: The billing job: Flink again, in batch mode. The same code, at the close.
[reveal: v-232]
[pause: 0.45]
C: And the billing tables: Iceberg, versioned, hour by campaign by version.
[pause: 1.1]

[slide: v-233]
[pause: 1.3]
C: Inside the live aggregator, in the order an event meets it.
[reveal: v-234]
[pause: 0.45]
C: The event log feeds it.
[reveal: v-235]
[pause: 0.45]
C: A Kafka source: one per partition range, its offsets saved in the checkpoint.
[reveal: v-236]
[pause: 0.45]
C: The time assigner: it clamps a skewed client time, and emits the watermark.
[reveal: v-237]
[pause: 0.45]
C: The deduplicator: state keyed by event I-D, ten-minute lifetime, in Rocks-D-B.
[reveal: v-238]
[pause: 0.45]
C: The combiner: partial sums per task, flushed every second.
[reveal: v-239]
[pause: 0.45]
C: The window counter: ad by minute, by event time.
[reveal: v-240]
[pause: 0.45]
C: Reach sketches hang off it.
[reveal: v-241]
[pause: 0.45]
C: And a late output, which counts events past the allowed lateness instead of adding them.
[reveal: v-242]
[pause: 0.45]
C: The store sink writes rows with a version.
[reveal: v-243]
[pause: 0.45]
C: Into ClickHouse.
[reveal: v-244]
[pause: 0.45]
C: And checkpoints: state and offsets together, every thirty seconds. Challenges one to four all happen in this picture.
[pause: 1.1]

[slide: v-245]
[pause: 1.3]
C: Inside the billing job.
[reveal: v-246]
[pause: 0.45]
C: It reads the event lake.
[reveal: v-247]
[pause: 0.45]
C: The hour closer decides when: at forty-eight hours, or when an hour is marked dirty. It pins a manifest.
[reveal: v-248]
[pause: 0.45]
C: The reader reads that hour at the pinned snapshot.
[reveal: v-249]
[pause: 0.45]
C: Exact dedup: the first row per I-D, over the whole hour.
[reveal: v-250]
[pause: 0.45]
C: Invalidations arrive on an append-only topic, and the invalid filter is an anti-join against a pinned snapshot of them.
[reveal: v-251]
[pause: 0.45]
C: Rate cards are versioned. Price and sum, in integer micro-dollars, so the sum is the same in any order.
[reveal: v-252]
[pause: 0.45]
C: The writer commits the hour as the next version.
[reveal: v-253]
[pause: 0.45]
C: Into the billing tables.
[reveal: v-254]
[pause: 0.45]
C: The adjuster takes the new version minus what was invoiced.
[reveal: v-255]
[pause: 0.45]
C: And sends it to invoicing.
[pause: 1.1]

[slide: v-256]
[pause: 1.0]
C: Topic events.raw: partition = hash(event ID) mod 1,024, RF 3 over three zones, min.insync.replicas=2. Brokers keep three days.
[reveal: v-257]
[pause: 0.45]
C: Why: A replayable log is the one copy everything is derived from.
[reveal: v-258]
[pause: 0.45]
C: Rejected: Google Pub/Sub. An honest equal on Google Cloud.
[reveal: v-259]
[pause: 0.45]
C: Amazon Kinesis. 1 MB/s a shard.
[pause: 1.0]

[slide: v-260]
[pause: 1.0]
C: Dedup keyed by event ID (TTL 10 min), a per-subtask combiner flushed every second, then ad times minute windows: early results every 2 s, final on the watermark. Checkpoints every 30 s.
[reveal: v-261]
[pause: 0.45]
C: Why: Keyed state with a TTL, event-time windows, and checkpoints that hold state and offsets together.
[reveal: v-262]
[pause: 0.45]
C: Rejected: Kafka Streams. Re-keying to the ad writes a repartition topic.
[reveal: v-263]
[pause: 0.45]
C: Spark Structured Streaming. A near-equal.
[pause: 1.0]

[slide: v-264]
[pause: 1.0]
C: live_minute ORDER BY (campaign_id, ad_id, minute, shard) with a version column, inserted in batches. Reads take the latest version per key and sum the shards.
[reveal: v-265]
[pause: 0.45]
C: Why: Columnar scans answer a dashboard in milliseconds.
[reveal: v-266]
[pause: 0.45]
C: Rejected: Apache Druid or Pinot. Honest equals.
[reveal: v-267]
[pause: 0.45]
C: Redis counters. An increment is not replay-safe, and history does not fit in memory.
[pause: 1.0]

[slide: v-268]
[pause: 1.0]
C: events partitioned by event hour, 0.6 PB a month. billing_hour keyed by (campaign, ad, hour, version); each run commits version n + 1 with its manifest.
[reveal: v-269]
[pause: 0.45]
C: Why: Each commit is a snapshot with an ID, so a run pins what it read, and replacing an hour is atomic.
[reveal: v-270]
[pause: 0.45]
C: Rejected: Plain Parquet folders. No atomic overwrite and no snapshot.
[reveal: v-271]
[pause: 0.45]
C: Delta Lake. An honest equal.
[pause: 1.0]

[slide: v-272]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
[reveal: v-273]
[pause: 0.45]
C: Collector: Go, stateless, disk spool. Not warehouse streaming inserts. The ack means the log has it.
[reveal: v-274]
[pause: 0.45]
C: Event log: Kafka, keyed by event ID. Not Pub/Sub (equal), Kinesis. Replayable; even load; retries co-located.
[reveal: v-275]
[pause: 0.45]
C: Live aggregator: Flink, event time. Not Kafka Streams, Spark. State TTL, watermarks, one engine for both runs.
[reveal: v-276]
[pause: 0.45]
C: Live store: ClickHouse. Not Druid/Pinot (equal), Redis. Replace by version; columnar slice-and-dice.
[reveal: v-277]
[pause: 0.45]
C: Lake + billing: Iceberg on GCS. Not Hive folders, Delta (equal). Snapshots to pin; atomic overwrite.
[reveal: v-278]
[pause: 0.45]
N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-279]
[pause: 1.2]
C: Before I break it: a much smaller design is correct at a smaller scale, and I should say where the line is.
[pause: 1.8]

[slide: v-280]
[pause: 1.3]
C: The alternate path. The ingest boxes stay.
[reveal: v-281]
[pause: 0.45]
C: What goes away is marked. The event lake.
[reveal: v-282]
[pause: 0.45]
C: The separate billing job.
[reveal: v-283]
[pause: 0.45]
C: And the billing tables as their own store.
[reveal: v-284]
[pause: 0.45]
C: Instead, one ClickHouse cluster. Collectors insert batches with an insert dedup token. A materialised view keeps minute rollups for the dashboard. And a nightly query bills each hour from the events table, deduplicated by event I-D.
[reveal: v-285]
[pause: 0.45]
C: What it gives up, precisely: there is no independent log to replay, because the table is the only copy. A heavy query slows ingest. A correction is a mutation. And dedup happens on merges, so it is eventual.
[pause: 1.1]

[slide: v-286]
[pause: 0.7]
C: Where is the line? A cluster of about twenty ClickHouse nodes takes on the order of one to two million rows a second. Our average, from the scale line, is ten million. We are past it by an order of magnitude.
V: Below about two hundred thousand events a second, with room to spare, I'd ship the one-box version, and I'd say out loud when I'd switch.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-287]
[pause: 1.2]
V: It works. The question now is where it breaks first.
[pause: 1.8]

[slide: v-288]
[pause: 1.3]
C: Version three, with the places it will break marked one at a time.
[reveal: v-289]
[pause: 0.45]
C: The collector, where a retry arrives as a second copy. Challenge one.
[reveal: v-290]
[pause: 0.45]
C: The live aggregator: late events and skewed clocks, one ad at two million a second, and a crash with a replay. Challenges two, three and four.
[reveal: v-291]
[pause: 0.45]
C: The billing job, where the hour has to close at the right moment and re-run safely.
[reveal: v-292]
[pause: 0.45]
C: The billing tables, when fraud changes its mind after the invoice. Challenge five.
[reveal: v-293]
[pause: 0.45]
C: And the reporting A-P-I, where an advertiser says our number is wrong. Challenge six: how would we know first?
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-294]
[pause: 1.2]
C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: The same click, three times

[slide: v-295]
[pause: 1.2]
N: Challenge one is the crux of this question: a retry. Most answers name a guarantee here. The grade is for the mechanism.
[pause: 1.8]

[slide: v-296]
[pause: 0.6]
I: A retrying client sends the same click three times, two seconds apart. Walk me through it.
[pause: 2.0]

[slide: v-297]
[pause: 1.3]
C: The live aggregator, opened up.
[reveal: v-298]
[pause: 0.45]
C: Marked: where a deduplicator should be, and in the naive design there isn't one.
[reveal: v-299]
[pause: 0.45]
C: The naive answer: Kafka is exactly-once, so duplicates can't happen.
[reveal: v-300]
[pause: 0.45]
C: But the duplicates were made before Kafka. Three copies arrive, and nothing remembers an I-D, so three are counted, on the dashboard and on the bill.
[pause: 1.1]

[slide: v-301]
[pause: 1.0]
C: The trace.
[reveal: v-302]
[pause: 0.45]
C: At ten o'clock the S-D-K sends batch B-seventeen, with click e-seven-f-three.
[reveal: v-303]
[pause: 0.45]
C: Forty milliseconds later it is at offset eighty-one thousand two hundred and twenty, acknowledged.
[reveal: v-304]
[pause: 0.45]
C: The two-oh-two is lost on the cell network.
[reveal: v-305]
[pause: 0.45]
C: Two seconds later the S-D-K retries: a second copy.
[reveal: v-306]
[pause: 0.45]
C: And again: a third.
[reveal: v-307]
[pause: 0.45]
C: Nobody did anything wrong. And at three tenths of a percent of batches, it's three hundred and seventy-five million dollars a month, billed twice.
[pause: 1.0]

[slide: v-308]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-309]
[pause: 0.45]
C: The deduplicator.
[reveal: v-310]
[pause: 0.45]
C: And the checkpoints that keep its state.
[reveal: v-311]
[pause: 0.45]
C: One level down: state keyed by event I-D, in Rocks-D-B, with a ten-minute lifetime. A record whose I-D is already there is dropped. The state is checkpointed with the Kafka offsets, and the billing run keeps the first row per I-D over the whole hour. The log is keyed by event I-D, so all three copies meet the same state.
[reveal: v-312]
[pause: 0.45]
C: It covers every retry, redelivery and replay of one event. Not a client that mints a new I-D per click: that's fraud's job.
[reveal: v-313]
[pause: 0.45]
C: Rejected: Kafka's exactly-once, with transactions. It removes a producer's own retry inside one session. An S-D-K retry over H-T-T-P-S is a new request, and only dedup on the event I-D removes it.
[pause: 1.1]

[slide: v-314]
[pause: 1.3]
C: As a sequence.
[reveal: v-315]
[pause: 0.45]
C: Batch B-seventeen.
[reveal: v-316]
[pause: 0.45]
C: Appended.
[reveal: v-317]
[pause: 0.45]
C: Acknowledged.
[reveal: v-318]
[pause: 0.45]
C: The answer is lost.
[reveal: v-319]
[pause: 0.45]
C: The retry, same I-Ds.
[reveal: v-320]
[pause: 0.45]
C: Appended again, on the same partition.
[reveal: v-321]
[pause: 0.45]
C: Both reach the deduplicator.
[reveal: v-322]
[pause: 0.45]
C: e-seven-f-three is in state: the second is dropped.
[reveal: v-323]
[pause: 0.45]
C: And the billing run keeps the first row per I-D in the hour. Once, by construction.
[pause: 1.1]

[slide: v-324]
[pause: 0.6]
I: The job restarts and loses its state. Or the retry comes eleven minutes later.
[pause: 1.5]

[slide: v-325]
[pause: 0.6]
C: Three answers.
[reveal: v-326]
[pause: 0.45]
C: A restart doesn't lose state. It is restored from the checkpoint, together with the offsets it matches, so a record read again meets the state that already saw it.
[reveal: v-327]
[pause: 0.45]
C: A retry eleven minutes later passes the live path, and the live view is two clicks high until the hour closes. The bill isn't: its dedup covers the whole hour, and the final hour replaces the live one.
[reveal: v-328]
[pause: 0.45]
C: And why ten minutes: S-D-K retries stop after five, ten is twice that, and the reconciler counts late duplicates, so the window is a measured choice, not a guess.
[pause: 0.8]

[slide: v-329]
[pause: 0.7]
V: If asked, I'd say: every event carries an I-D minted where it happened, so a retry is recognisable. The live path drops repeats in keyed state for ten minutes, and the billing run drops them over the whole hour. Exactly-once isn't a broker setting. It's at-least-once delivery plus that dedup.
[pause: 1.0]
N: That fix creates the next question: the I-D says which event it is. It doesn't say when it happened.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: Yesterday's events at 6 a.m.

[slide: v-330]
[pause: 1.2]
N: Challenge two: time. Which clock decides the hour an event is billed in?
[pause: 1.8]

[slide: v-331]
[pause: 0.6]
I: A phone was offline overnight. Three hundred impressions from Tuesday evening arrive on Wednesday at six. Which hour gets billed?
[pause: 2.0]

[slide: v-332]
[pause: 1.3]
C: Three components of the live aggregator.
[reveal: v-333]
[pause: 0.45]
C: The time assigner is marked.
[reveal: v-334]
[pause: 0.45]
C: The naive answer: count them when they arrive.
[reveal: v-335]
[pause: 0.45]
C: Then the time assigner uses arrival time. Tuesday's hours come up short, and Wednesday six o'clock is over.
[pause: 1.1]

[slide: v-336]
[pause: 1.0]
C: The trace.
[reveal: v-337]
[pause: 0.45]
C: Tuesday evening, three hundred impressions on a phone with no signal.
[reveal: v-338]
[pause: 0.45]
C: At midnight the campaign's flight ends.
[reveal: v-339]
[pause: 0.45]
C: At six on Wednesday the phone reconnects.
[reveal: v-340]
[pause: 0.45]
C: Counted at arrival, those impressions are billed after the campaign ended.
[reveal: v-341]
[pause: 0.45]
C: And another phone says its clock is in twenty thirty-one. Trust that, and an hour opens that never closes.
[reveal: v-342]
[pause: 0.45]
C: So I need event time, and I can't trust it blindly.
[pause: 1.0]

[slide: v-343]
[pause: 1.3]
C: The fix, on the same components.
[reveal: v-344]
[pause: 0.45]
C: The time assigner.
[reveal: v-345]
[pause: 0.45]
C: And the window counter.
[reveal: v-346]
[pause: 0.45]
C: One level down. The event time is the client's time if it lies between seventy-two hours before and five minutes after the server's time. Otherwise it's the server time, and the event is flagged as clamped. The watermark is the minimum, over partitions, of the latest event time minus two minutes. And a minute window accepts an hour of lateness after that.
[reveal: v-347]
[pause: 0.45]
C: It covers late and skewed events up to the billing cutoff. After the cutoff, an event changes a closed hour, and that's challenge five.
[reveal: v-348]
[pause: 0.45]
C: Rejected: processing-time windows. They bill a phone's Tuesday evening in Wednesday's six a.m. hour.
[pause: 1.1]

[slide: v-349]
[pause: 1.0]
C: As pseudocode. The key lines are marked.
C: Line two: a client time outside the window is replaced by the server time. Line six: the watermark is a minimum over active partitions, two minutes behind. Line eight: a late event inside the hour of allowed lateness updates its window, which is emitted again with a higher version. Anything later is only counted as late. The lake still has it, so the bill still will.
C: Why it works: a minimum means one fast partition can't close a minute that a slow one is still filling, and the clamp bounds what a bad clock can do.
[pause: 1.0]

[slide: v-350]
[pause: 1.3]
C: The live view is one half. The bill is the other, inside the billing job.
[reveal: v-351]
[pause: 0.45]
C: The hour closer.
[reveal: v-352]
[pause: 0.45]
C: At forty-eight hours it pins a snapshot of that hour's partition: every file landed so far, the late ones included, because files are partitioned by event hour, not by arrival. The run reads exactly that snapshot, and nothing that lands later.
[reveal: v-353]
[pause: 0.45]
C: Why forty-eight hours: it's an initial target, to be measured. If ninety-nine point nine nine percent of events arrive within thirty-six hours, the rest become a version two, at the cost of one adjustment.
[pause: 1.1]

[slide: v-354]
[pause: 0.6]
I: One partition goes quiet. Or a bad S-D-K release sends every clock a day off.
[pause: 1.5]

[slide: v-355]
[pause: 0.6]
C: A quiet partition would hold the minimum back forever, so it is excluded from the watermark after thirty seconds of silence.
[reveal: v-356]
[pause: 0.45]
C: A bad S-D-K clock is clamped to server time and flagged, and an alert fires when the clamped share passes a tenth of a percent, broken down by S-D-K version, so the release is found in minutes.
[reveal: v-357]
[pause: 0.45]
C: And the honest limit: an event past the cutoff does change a closed hour. It becomes version two and an adjustment, never a silent edit.
[pause: 0.8]

[slide: v-358]
[pause: 0.7]
V: If asked, I'd say: the event's own time decides its hour, clamped against server time so a broken or hostile clock can't move it far. The dashboard waits two minutes and accepts an hour of lateness. The bill closes at forty-eight hours from a snapshot of everything that landed for that hour, and anything later becomes a new version.
[pause: 1.0]
N: That fix creates the next question: the windows are keyed by ad. What if one ad is the whole stream?
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: One ad at 2 million a second

[slide: v-359]
[pause: 1.2]
N: Challenge three: overload, but not the kind more machines fix.
[pause: 1.8]

[slide: v-360]
[pause: 0.6]
I: A sports break puts one ad on every screen: two million impressions a second. What happens to your job?
[pause: 2.0]

[slide: v-361]
[pause: 1.3]
C: The middle of the live aggregator.
[reveal: v-362]
[pause: 0.45]
C: The window counter is marked.
[reveal: v-363]
[pause: 0.45]
C: The naive answer: key by ad, and add machines.
[reveal: v-364]
[pause: 0.45]
C: But a key lives on exactly one task. Machines don't help it. That one task gets all two million a second, and its backpressure slows every partition.
[pause: 1.1]

[slide: v-365]
[pause: 1.0]
C: The trace.
[reveal: v-366]
[pause: 0.45]
C: At twenty fourteen, ad seventy-seven goes from three thousand to two million impressions a second.
[reveal: v-367]
[pause: 0.45]
C: Five seconds later, the one window task holding it is at a hundred percent.
[reveal: v-368]
[pause: 0.45]
C: Backpressure. Every source slows, and lag grows on all thousand and twenty-four partitions.
[reveal: v-369]
[pause: 0.45]
C: Ninety seconds later every advertiser's dashboard is stale, and budget pacing is flying blind, not just for ad seventy-seven.
[reveal: v-370]
[pause: 0.45]
C: Note what is not hot: the log is keyed by event I-D, so its partitions are even. The hot spot is one thread.
[pause: 1.0]

[slide: v-371]
[pause: 1.3]
C: The fix, in the middle of the job.
[reveal: v-372]
[pause: 0.45]
C: The combiner.
[reveal: v-373]
[pause: 0.45]
C: And the window counter, which now merges partial sums.
[reveal: v-374]
[pause: 0.45]
C: One level down. Each of the five hundred and twelve subtasks sums its own events per ad and minute for one second, then sends one partial sum. The window task for ad seventy-seven now sees five hundred and twelve updates a second instead of two million. And the store keeps up to sixteen shard rows per ad and minute, summed when the dashboard reads. That's the sharded counter.
[reveal: v-375]
[pause: 0.45]
C: It covers any number of hot ads, because the cost now follows active keys, not events. It adds a second of delay, inside the ten-second budget.
[reveal: v-376]
[pause: 0.45]
C: Rejected: Redis increment-by on one counter key. One key is one shard's thread, about a hundred thousand operations a second against two million. And a replay increments again.
[pause: 1.1]

[slide: v-377]
[pause: 0.6]
I: Now five hundred ads are hot at once, in every break.
[pause: 1.5]

[slide: v-378]
[pause: 0.6]
C: Five hundred hot ads.
[reveal: v-379]
[pause: 0.45]
C: Each subtask's partial map holds one entry per active ad and minute: five hundred entries, flushed every second. Small.
[reveal: v-380]
[pause: 0.45]
C: The merge stage sees five hundred ads times five hundred and twelve partials: about two hundred and fifty-six thousand updates a second, spread over its subtasks by key. That scales with machines, because now there are many keys.
[reveal: v-381]
[pause: 0.45]
C: The honest limit: every count arrives a second later. The budget has the room.
[pause: 0.8]

[slide: v-382]
[pause: 0.7]
V: If asked, I'd say: a hot key is a hot thread, not a hot partition, because my log is keyed by event I-D. So I sum where the events already are, once a second, and merge five hundred and twelve partial sums instead of two million updates. On the read side, a hot counter is sixteen shard rows, summed on read.
[pause: 1.0]
N: That fix creates the next question: the job holds a lot of state now. What happens when it crashes, or when you have to run it again?
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Replay four hours

[slide: v-383]
[pause: 1.2]
N: Challenge four is the second half of the crux: running the same thing twice.
[pause: 1.8]

[slide: v-384]
[pause: 0.6]
I: You find a bug, redeploy the stream job and replay from ten o'clock, four hours back. Is anyone billed twice?
[pause: 2.0]

[slide: v-385]
[pause: 1.3]
C: The end of the live aggregator: the window, the sink, the store, the checkpoints.
[reveal: v-386]
[pause: 0.45]
C: The store sink is marked.
[reveal: v-387]
[pause: 0.45]
C: The naive answer: Flink is exactly-once.
[reveal: v-388]
[pause: 0.45]
C: Inside one run, it is. But if the sink adds each partial sum to what's in the store, a replay adds the same four hours on top of the first run.
[pause: 1.1]

[slide: v-389]
[pause: 1.0]
C: The trace.
[reveal: v-390]
[pause: 0.45]
C: At fourteen oh two, a bug: reach was merged per subtask instead of per campaign.
[reveal: v-391]
[pause: 0.45]
C: The fix is deployed, and the offsets rewound to ten o'clock.
[reveal: v-392]
[pause: 0.45]
C: Four hours are recomputed and written again.
[reveal: v-393]
[pause: 0.45]
C: With an adding sink, the dashboard shows those four hours doubled, and budget pacing stops forty campaigns that haven't spent anything extra.
[reveal: v-394]
[pause: 0.45]
C: And a billing job written the same way would double the invoice.
[reveal: v-395]
[pause: 0.45]
C: The engine's exactly-once is about one run. This question is about two.
[pause: 1.0]

[slide: v-396]
[pause: 1.3]
C: The fix, on the same view.
[reveal: v-397]
[pause: 0.45]
C: The store sink.
[reveal: v-398]
[pause: 0.45]
C: And the live store.
[reveal: v-399]
[pause: 0.45]
C: One level down. A live row is keyed by ad, minute and shard, with a version, and ClickHouse keeps the highest version per key. So a re-emitted minute replaces the old row; it never adds. A billing hour is committed as a whole partition, a pure function of its manifest.
[reveal: v-400]
[pause: 0.45]
C: It covers replays, restarts and re-runs with new code. It doesn't make a buggy run right. It makes the next run safe.
[reveal: v-401]
[pause: 0.45]
C: Rejected: Flink's two-phase-commit sink on its own. It makes one run's output atomic. A second run from four hours earlier still adds on top, unless the write replaces by key.
[pause: 1.1]

[slide: v-402]
[pause: 1.3]
C: The same replay, with replacing writes.
[reveal: v-403]
[pause: 0.45]
C: On-call redeploys and rewinds to ten.
[reveal: v-404]
[pause: 0.45]
C: Flink writes the four hours again, with higher versions.
[reveal: v-405]
[pause: 0.45]
C: Same keys, higher versions: they replace, they don't add.
[reveal: v-406]
[pause: 0.45]
C: For the bill, on-call re-runs the hour starting at ten with its manifest.
[reveal: v-407]
[pause: 0.45]
C: The rows are identical, so the commit changes nothing. A replay is a no-op on the bill.
[pause: 1.1]

[slide: v-408]
[pause: 0.6]
I: Finance wants last March re-run, bit for bit, two years from now.
[pause: 1.5]

[slide: v-409]
[pause: 1.3]
C: Inside the billing job.
[reveal: v-410]
[pause: 0.45]
C: The hour closer, which writes the manifest.
[reveal: v-411]
[pause: 0.45]
C: And the writer, which stores it beside every hour.
[reveal: v-412]
[pause: 0.45]
C: The manifest pins four things: the events snapshot, the rate-card version, the invalidation snapshot, and the job's image digest. The job reads no wall clock, sums integer micro-dollars and sorts before it reduces. Run that image over those snapshots in two years, and March comes out bit for bit. The honest limit: raw events live six months, so after that March is reproducible from its billing rows, not from events.
[pause: 1.1]

[slide: v-413]
[pause: 0.7]
V: If asked, I'd say: I never increment a number I can recompute. Live minutes and billing hours are written as replacements keyed by what they count, with a version, so a replay rewrites the same rows. A billing run is a pure function of a pinned manifest, which is also how I re-run March two years from now.
[pause: 1.0]
N: That fix creates the next question: if an hour can be re-run, what happens when its inputs change after it was billed?
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Fraud after the invoice

[slide: v-414]
[pause: 1.2]
N: Challenge five: the past changes. How you record that is the grade.
[pause: 1.8]

[slide: v-415]
[pause: 0.6]
I: Nine days after the invoices go out, fraud invalidates two percent of October's clicks for one advertiser. What happens?
[pause: 2.0]

[slide: v-416]
[pause: 1.3]
C: Inside the billing job: the invalidations, the filter, the writer, the billing tables, invoicing.
[reveal: v-417]
[pause: 0.45]
C: The writer is marked.
[reveal: v-418]
[pause: 0.45]
C: The naive answer: delete the invalid rows and re-send the invoice.
[reveal: v-419]
[pause: 0.45]
C: Then the writer edits hours that were billed, and the invoice already sent matches nothing we have stored.
[pause: 1.1]

[slide: v-420]
[pause: 1.0]
C: The trace.
[reveal: v-421]
[pause: 0.45]
C: On the first of November, advertiser A is invoiced: a hundred and fifty-five million clicks, seventy-seven and a half million dollars.
[reveal: v-422]
[pause: 0.45]
C: On the ninth, fraud flags botnet seventeen: three point one million of those clicks, two percent.
[reveal: v-423]
[pause: 0.45]
C: The naive fix updates the billed rows in place.
[reveal: v-424]
[pause: 0.45]
C: A week later A disputes a line, and we have no stored version that matches the invoice in their hand.
[reveal: v-425]
[pause: 0.45]
C: So I need two things at once: a credit for the invalid clicks, and an untouched record of what was invoiced.
[pause: 1.0]

[slide: v-426]
[pause: 1.3]
C: The fix, at the end of the billing job: the writer only ever adds a version, and the adjuster sits between it and invoicing.
[reveal: v-427]
[pause: 0.45]
C: The adjuster.
[reveal: v-428]
[pause: 0.45]
C: One level down. The fraud system appends invalidations, each with its event's hour. The closer marks those hours dirty and re-runs each as the next version, with a manifest pinning the new invalidation snapshot. Version one stays. The adjuster sends the new version minus what was invoiced as a credit line: minus one point five five million dollars.
[reveal: v-429]
[pause: 0.45]
C: One path covers fraud, events past the cutoff, and rate-card fixes. And because the invoiced version is never touched, every invoice line still matches a stored row.
[reveal: v-430]
[pause: 0.45]
C: Rejected: updating billed rows in place. The invoice then matches no stored version, and the audit trail ends at the edit.
[pause: 1.1]

[slide: v-431]
[pause: 1.0]
C: As pseudocode, key lines marked.
C: Line three: a new manifest pins the new invalidation snapshot. Line six: the commit writes version v, and version v minus one stays. Line nine: any difference from what was invoiced becomes an adjustment.
C: Why it works: a correction is the billing job with a newer manifest. There's no second code path, so a correction can't be computed differently from a bill.
[pause: 1.0]

[slide: v-432]
[pause: 0.6]
I: Fraud invalidates an event from seven months ago.
[pause: 1.5]

[slide: v-433]
[pause: 0.6]
C: Seven months is past the raw retention. Events are kept six months and the dispute window is ninety days, so an older invalidation is refused, and the refusal is logged. That's a contract, not a mechanism, and I'd say so.
[reveal: v-434]
[pause: 0.45]
C: Inside the window: any hour, any number of versions, and the adjustment is always computed against what was actually invoiced.
[reveal: v-435]
[pause: 0.45]
C: And only the fraud system may invalidate, with a rule version on every record, so a manifest can say which rules a version used.
[pause: 0.8]

[slide: v-436]
[pause: 0.7]
V: If asked, I'd say: nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference from what was invoiced becomes an adjustment line on the next invoice. The same path carries fraud, events past the cutoff and rate-card fixes, so every invoice still matches a stored version.
[pause: 1.0]
N: That fix creates the last question. Every part can now be right. How would you know when one of them isn't?
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: “Your numbers are 3 % high”

[slide: v-437]
[pause: 1.2]
N: Challenge six is observability, and in this question it is about a wrong number, not a down server.
[pause: 1.8]

[slide: v-438]
[pause: 0.6]
I: An advertiser says our clicks are three percent higher than their own logs. What do you do, and how would you have known first?
[pause: 2.0]

[slide: v-439]
[pause: 1.3]
C: Back to the container view, version three.
[reveal: v-440]
[pause: 0.45]
C: The reporting A-P-I is marked: that's where the advertiser sees the number.
[reveal: v-441]
[pause: 0.45]
C: The naive answer: lag, C-P-U and error rate are all green.
[reveal: v-442]
[pause: 0.45]
C: And they are. Every container is healthy, and the number is wrong.
[pause: 1.1]

[slide: v-443]
[pause: 1.0]
C: The trace.
[reveal: v-444]
[pause: 0.45]
C: Monday at nine, a config push sets the dedup lifetime to ten seconds instead of ten minutes. A units typo.
[reveal: v-445]
[pause: 0.45]
C: Lag, C-P-U and errors stay green. Live clicks run three percent above their usual ratio to impressions, and nothing watches that.
[reveal: v-446]
[pause: 0.45]
C: On Wednesday Monday's final hours are right, because the billing run deduplicates the whole hour.
[reveal: v-447]
[pause: 0.45]
C: On Thursday an advertiser compares their screenshots with their logs and calls.
[reveal: v-448]
[pause: 0.45]
C: Every system was healthy. One number was wrong for three days.
[pause: 1.0]

[slide: v-449]
[pause: 1.3]
C: The fix changes the design, so this is version four. Version three, carried.
[reveal: v-450]
[pause: 0.45]
C: New: a reconciler. It reads the collectors' accepted counts and the live store, where the final hours also land.
[pause: 1.1]

[slide: v-451]
[pause: 0.6]
C: One level down, three checks on the numbers themselves.
[reveal: v-452]
[pause: 0.45]
C: Conservation at every hop, per minute: accepted equals appended equals landed, minus duplicates.
[reveal: v-453]
[pause: 0.45]
C: Live against final for every closed hour, alerting above half a percent. That one would have fired on Wednesday.
[reveal: v-454]
[pause: 0.45]
C: And canary events with known I-Ds every minute, each expected exactly once in the live store and in the final hour.
[reveal: v-455]
[pause: 0.45]
C: And to answer the advertiser: the invoice line points to an hour version, the version to its manifest, the manifest to the event I-Ds. We can export the I-Ds behind their line and compare.
[reveal: v-456]
[pause: 0.45]
C: Rejected: lag and C-P-U dashboards. They stay green while the pipeline counts wrong. Only conservation checks and canaries see a wrong number.
[pause: 0.8]

[slide: v-457]
[pause: 1.0]
C: One more habit: read symptoms in pairs. A number alone is not a diagnosis.
[reveal: v-458]
[pause: 0.45]
C: Live clicks up three percent while the final for the same hour is flat: duplicates on the live path. Our case.
[reveal: v-459]
[pause: 0.45]
C: Live and final both up, with impressions up too: real traffic. Nobody gets paged.
[reveal: v-460]
[pause: 0.45]
C: Accepted above landed, while log lag is flat: the lake sink is losing files.
[reveal: v-461]
[pause: 0.45]
C: A canary seen twice: a duplicate path, wherever it is.
[reveal: v-462]
[pause: 0.45]
C: And a clamped share above a tenth of a percent, all from one S-D-K version: a client clock bug.
[pause: 1.0]

[slide: v-463]
[pause: 0.6]
I: And if the reconciler itself is wrong?
[pause: 1.5]

[slide: v-464]
[pause: 0.6]
C: The canaries check the checker. A known number of them a minute, so the reconciler must count exactly that many, or it pages about itself.
[reveal: v-465]
[pause: 0.45]
C: And silence is a failure. If no comparison has run for fifteen minutes, that pages too. An alert that cannot fire is not an alert.
[pause: 0.8]

[slide: v-466]
[pause: 0.7]
V: If asked, I'd say: I'd answer the advertiser with the event I-Ds behind their line: invoice line, hour version, manifest, events. And I'd want to have seen it first: conservation at every hop, live against final every hour, and canary events whose count I know, so a wrong number pages even when every system is healthy.
[pause: 1.6]

[pause: 1.4]

## 8 Recap

[slide: v-467]
[pause: 1.2]
C: The recap. One picture, the mechanisms on it, and the mistakes that cost most.
[pause: 1.8]

[slide: v-468]
[pause: 1.3]
C: Version four, the final design. The same picture as version one, with four boxes more. The labels from the theory chapter come back on it.
[reveal: v-469]
[pause: 0.45]
C: The collector keeps the I-D the S-D-K minted. It never makes one up.
[reveal: v-470]
[pause: 0.45]
C: The live aggregator runs four of the five mechanisms: the I-D, event time, two-stage sums and the reach sketches. Record, then live, within ten seconds.
[reveal: v-471]
[pause: 0.45]
C: The live store replaces by version. It never increments.
[reveal: v-472]
[pause: 0.45]
C: The billing job runs the same code at the close, over a pinned snapshot: the I-D, event time and replacement.
[reveal: v-473]
[pause: 0.45]
C: The billing tables hold versions, so a correction is a new row and an adjustment, never an edit.
[reveal: v-474]
[pause: 0.45]
C: And the reconciler checks the numbers themselves, with canaries whose count it knows.
[pause: 1.1]

[slide: v-475]
[pause: 1.0]
N: The mistakes that cost most in this round.
[reveal: v-476]
[pause: 0.45]
N: n equals n plus one, per event, in a database. Instead, a log first, and counts derived from it.
[reveal: v-477]
[pause: 0.45]
N: Exactly-once said as a name. Instead, at-least-once plus dedup on an I-D minted at the source.
[reveal: v-478]
[pause: 0.45]
N: Counting by arrival time. Instead, event time, clamped, with a watermark and a cutoff.
[reveal: v-479]
[pause: 0.45]
N: One run for both the dashboard and the bill. Instead, one code, run twice.
[reveal: v-480]
[pause: 0.45]
N: Editing billed rows. Instead, versions and adjustment lines.
[reveal: v-481]
[pause: 0.45]
N: And no way to show the events behind an invoice line. Instead, a manifest per hour, canaries and conservation checks.
[pause: 1.0]

[slide: v-482]
[pause: 0.7]
V: Count once, from one log, with one piece of code run twice. Never increment what you can recompute. Replace it, and keep every version you billed.
[pause: 1.0]
C: Thanks for watching. The written design, with every number and the internals of each tool, is linked below.
[pause: 1.6]
