# SD-99 Outbound webhook and partner event-delivery platform: reference solution (Staff L6/L7)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is HTTP=H-T-T-P SQL=S-Q-L ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E UUID=U-U-I-D ACH=A-C-H NSF=N-S-F BNPL=B-N-P-L APR=A-P-R TB=terabytes GB=gigabytes MB=megabytes KB=kilobytes UNKNOWN=unknown RETURNED=returned SETTLED=settled PENDING=pending PAID_PENDING=paid-pending SFTP=S-F-T-P HMAC=H-MAC SHA256=SHA-two-fifty-six SSRF=S-S-R-F POS=P-O-S ERP=E-R-P DNS=D-N-S URL=U-R-L URLs=U-R-Ls IP=I-P IPs=I-Ps KMS=K-M-S mTLS=mutual-T-L-S TLS=T-L-S DLQ=D-L-Q CI=C-I JSON=jason p99=P-ninety-nine p95=P-ninety-five SDK=S-D-K SDKs=S-D-Ks -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: A point-of-sale lender approves a loan at a merchant's counter. The merchant's till has to hear about it in seconds, their accounting system has to hear about the refund a month later, and the partner bank wants every payment, loan by loan. The first version of that is one line of code: a POST to the merchant's URL, inside the booking request. It fails the first time a merchant's server takes thirty seconds to answer.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: Merchants and partners subscribe to our loan and payment events: approved, booked, funded, refunded, paid. Design the platform that delivers them as webhooks.
[pause: 1.5]

[slide: v-003]
[pause: 1.0]
N: Five axes.
[reveal: v-004]
[pause: 0.45]
N: The weak answer is a queue with retries.
[reveal: v-005]
[pause: 0.45]
N: The strong answer isolates every endpoint,
[reveal: v-006]
[pause: 0.45]
N: says at-least-once and means it, and treats the payload as a public contract.
[reveal: v-007]
[pause: 0.45]
C: One sentence I'll keep in front of everything:
[reveal: v-008]
[pause: 0.45]
C: one bad endpoint must never spend another endpoint's capacity.
[pause: 1.0]

[slide: v-009]
[pause: 0.7]
V: We promise at-least-once delivery, and we give every endpoint its own failure budget. Exactly-once is the consumer's job, and the contract that makes it possible is the product.
[pause: 1.0]
C: Concretely: an outbox, so no event exists without its commit. A delivery row per endpoint, so a slow endpoint queues in its own rows. Backoff with jitter and a slow ramp, so a recovering endpoint is not knocked over again. Signatures, an egress proxy and a versioned contract, so merchants can trust and keep parsing what we send.
[pause: 1.6]

[slide: v-010]
[pause: 0.6]
C: The order.
C: Requirements, numbers from one scale line, and a short theory chapter.
[reveal: v-011]
[pause: 0.45]
C: Then the A-P-I, the data, and a design in three versions, with a simpler alternative and the number where it stops being enough.
[reveal: v-012]
[pause: 0.45]
C: Most of the time goes to seven challenges, each one carrying the design forward, to version six.
C: Then the build cost, with the team seams and the contracts between them, and a recap.
[pause: 0.8]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-013]
[pause: 1.2]
C: Before I draw anything, one scale line and six questions. Each answer changes the design.
[pause: 1.8]

[slide: v-014]
[pause: 1.0]
C: The scale line, said once.
[reveal: v-015]
[pause: 0.45]
C: Sixty million events a month, from origination, funding and servicing. Each matches about three subscriptions, so a hundred and eighty million deliveries a month. That's about seventy a second on average.
[reveal: v-016]
[pause: 0.45]
C: Over thirty days of retention: about two hundred and sixteen million attempt rows, at one point two attempts per delivery, and about a hundred and twenty gigabytes of payloads, one per event.
[reveal: v-017]
[pause: 0.45]
C: The peak has a cause. On the morning after a collection day, the bank's settlement file posts four hundred and eighty thousand payments in about ten minutes. That's eight hundred events a second, and two thousand four hundred deliveries a second: thirty-four times the average.
[reveal: v-018]
[pause: 0.45]
C: And twenty thousand endpoints, of which about three percent are failing at any moment: six hundred.
[reveal: v-019]
[pause: 0.45]
C: All illustrative. Every number from here starts from one of these rows.
[pause: 1.0]

[slide: v-020]
[pause: 0.6]
C: Who subscribes, and what do they do with an event?
I: Merchant tills and accounting systems, which register their own URLs.
I: And the partner bank, by contract.
C: So a merchant may release goods on an approval event.
C: That makes a forged event a fraud problem, not a nuisance.
C: And self-service URLs mean the URL is untrusted input that my servers will call.
[pause: 0.6]

[slide: v-021]
[pause: 0.6]
C: Must events for one loan arrive in order?
I: We don't promise it.
I: Merchants can always fetch the loan's current state.
C: Good.
C: Then I'll give them what they need to order it themselves, a sequence per loan, rather than promise something a retry will break.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: How fast must the first attempt go, and how long do we keep trying?
I: First attempt within five seconds at the ninety-ninth percentile, for a healthy endpoint.
I: Retry for seventy-two hours.
C: Seventy-two hours means a backlog of days has to live somewhere durable, not in memory.
[pause: 0.6]

[slide: v-023]
[pause: 0.6]
C: Do we promise exactly once?
I: At least once.
I: Say it in the contract.
C: Then the event I-D is part of the product: merchants de-duplicate by it.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: Payload size, and how many regions?
I: About two kilobytes.
I: One region to start.
C: Small payloads: storage is not the problem.
C: I'll name the second region as an extension, not design for it now.
[pause: 0.6]

[slide: v-025]
[pause: 0.6]
C: Who owns what goes inside an event?
I: The producing teams own their events.
I: Merchants must not break when those teams change things.
C: Then the public contract cannot be the internal event.
C: That will be a challenge on its own, and a team seam.
[pause: 0.6]

[slide: v-026]
[pause: 1.0]
C: Four functional requirements.
[reveal: v-027]
[pause: 0.45]
C: F-R-one: register an endpoint and subscribe it to event types. The URL is verified, a signing secret is shown once, and the endpoint is pinned to an A-P-I version.
[reveal: v-028]
[pause: 0.45]
C: F-R-two: emit an event atomically with the state change. No event without its commit, and none for a change that rolled back.
[reveal: v-029]
[pause: 0.45]
C: F-R-three: deliver to every matching endpoint, signed, with retries for seventy-two hours, and then dead, visibly.
[reveal: v-030]
[pause: 0.45]
C: F-R-four: see every attempt, and redeliver one delivery or replay everything since a time, at a rate the merchant chooses.
[pause: 1.0]

[slide: v-031]
[pause: 1.0]
C: The non-functional requirements, all initial targets.
[reveal: v-032]
[pause: 0.45]
C: Zero events lost after commit: a lost approval stops a sale.
[reveal: v-033]
[pause: 0.45]
C: The first attempt to a healthy endpoint within five seconds at p ninety-nine, because a till is waiting.
[reveal: v-034]
[pause: 0.45]
C: One endpoint's failure adds less than a second to anyone else's p ninety-nine. That's the isolation requirement, written as a number.
[reveal: v-035]
[pause: 0.45]
C: Seventy-two hours of retries, then dead and visible: long enough for a weekend outage at a merchant.
[reveal: v-036]
[pause: 0.45]
C: Ingest at ninety-nine point nine five percent, because producers must never block on us.
[reveal: v-037]
[pause: 0.45]
C: And never a call to a private address.
[pause: 1.0]

[slide: v-038]
[pause: 0.6]
C: In scope: the outbox and relay, fan-out, delivery with retries, signing, egress control, the attempt log, replay, and the public contract with its versions.
[reveal: v-039]
[pause: 0.45]
C: Out, on purpose: partner-side S-D-Ks, a schema design tool, webhooks we receive from others, push notifications to customers' phones, and a second region, which I'll name as an extension.
[pause: 0.8]

[slide: v-040]
[pause: 0.7]
V: The core is three things. A durable event before any delivery. Isolation per endpoint. And the consumer contract: I-Ds, a sequence, a signature, and versions.
[pause: 1.6]

[slide: v-041]
[pause: 1.3]
C: The context.
[reveal: v-042]
[pause: 0.45]
C: Origination produces loan events.
[reveal: v-043]
[pause: 0.45]
C: The servicing system adds the payments and refunds.
[reveal: v-044]
[pause: 0.45]
C: The webhook platform sits in the middle.
[reveal: v-045]
[pause: 0.45]
C: It sends signed POSTs to twenty thousand merchant tills and accounting systems,
[reveal: v-046]
[pause: 0.45]
C: and loan-level events to the partner bank, over mutual T-L-S.
[reveal: v-047]
[pause: 0.45]
C: Merchant developers register endpoints and replay deliveries.
[reveal: v-048]
[pause: 0.45]
C: And a key service holds the signing secrets.
[pause: 1.1]

[pause: 1.4]

## 2 Estimates

[slide: v-049]
[pause: 1.2]
C: Five numbers, each from the scale line, each with the decision it drives. All illustrative.
[pause: 1.8]

[slide: v-050]
[pause: 1.0]
C: Estimate one, from the peak.
[reveal: v-051]
[pause: 0.45]
C: Two thousand four hundred deliveries a second, times a quarter of a second for a typical answer: about six hundred calls in flight, by Little's law.
[reveal: v-052]
[pause: 0.45]
C: That's a small fleet.
C: Raw capacity is not the risk.
C: What happens when one endpoint stops answering in a quarter of a second is.
[pause: 1.0]

[slide: v-053]
[pause: 1.0]
C: Estimate two.
C: One till vendor gets five percent of the deliveries: a hundred and twenty a second at the peak.
[reveal: v-054]
[pause: 0.45]
C: If its server slows to our ten-second timeout, it needs twelve hundred calls in flight.
C: Twice the whole fleet.
[reveal: v-055]
[pause: 0.45]
C: So a cap on in-flight calls per endpoint, and separate pools per tier, are mandatory.
C: Not tuning.
[pause: 1.0]

[slide: v-056]
[pause: 1.0]
C: Estimate three.
C: An accounting system that takes two percent of deliveries, one point four a second, is down for two days.
[reveal: v-057]
[pause: 0.45]
C: That's two hundred and forty thousand deliveries, about half a gigabyte.
[reveal: v-058]
[pause: 0.45]
C: The backlog lives in durable rows, not in memory.
C: And when it comes back, sending all of it at our peak rate would be seventeen hundred times its normal load.
C: So recovery has to be ramped.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: Estimate four, storage.
[reveal: v-060]
[pause: 0.45]
C: The attempt log: a hundred and eighty million deliveries, times one point two attempts, times five hundred bytes: about a hundred and eight gigabytes a month, in daily partitions we drop after thirty days.
[reveal: v-061]
[pause: 0.45]
C: Payloads: sixty million events times two kilobytes: a hundred and twenty gigabytes a month, stored once per event. Stored per delivery it would be three times that.
[reveal: v-062]
[pause: 0.45]
C: And delivery writes at the peak: about four writes per delivery, insert, claim, finish and the attempt, so about ten thousand a second. Four PostgreSQL shards by endpoint carry it with headroom.
[pause: 1.0]

[slide: v-063]
[pause: 1.0]
C: Estimate five, the latency budget for the first attempt.
[reveal: v-064]
[pause: 0.45]
C: Half a second for the relay to poll,
[reveal: v-065]
[pause: 0.45]
C: half a second through the log and fan-out, half a second for a dispatcher to claim, up to two seconds for a healthy endpoint to answer, and a second and a half spare.
[reveal: v-066]
[pause: 0.45]
C: Polling intervals are the dial.
[reveal: v-067]
[pause: 0.45]
C: If the five-second promise tightens, I shorten the polls before I add machinery.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-068]
[pause: 1.2]
C: A short theory chapter before any design, in five parts: what this system is and is not, its properties, the central tension, six mechanisms each with the picture that fits it, and the options, one slide each. The failures come later, as the challenges.
[pause: 1.8]

[slide: v-069]
[pause: 0.7]
V: A webhook platform turns committed state changes into signed H-T-T-P calls to endpoints we do not control, retries them for days, and never lets one endpoint take capacity from another.
[pause: 0.8]
C: Every clause does work. Committed: the event exists only if the change does. Signed: the receiver can tell it is us. Endpoints we do not control: they are slow, down, wrong, or hostile. For days: the backlog is durable. And capacity: isolation is the product.
[pause: 1.6]

[slide: v-070]
[pause: 0.6]
C: Four confusions.
C: It is not a message broker: a broker lets consumers pull at their own pace.
C: Here we push into servers that give no back-pressure at all.
[reveal: v-071]
[pause: 0.45]
C: It is not push notifications to our own app, which go to a platform we trust.
[reveal: v-072]
[pause: 0.45]
C: It is not webhooks we receive, which is about verifying others.
[reveal: v-073]
[pause: 0.45]
C: And it is not exactly-once: into a system we don't control, the honest promise is at-least-once, plus an I-D.
[pause: 0.8]

[slide: v-074]
[pause: 0.6]
C: Three safety properties. S-one, no event lost: no event lost after its commit, and none for a change that rolled back. S-two, no private address: no call to a private address. S-three, signed no replay: no unsigned call, and none a third party could replay.
[reveal: v-075]
[pause: 0.45]
C: Three liveness properties. L-one, delivered or dead 72h: every event delivered, or visibly dead, within seventy-two hours. L-two, healthy stays fast: a healthy endpoint is served within its p ninety-nine while others fail. L-three, recovery no relapse: a recovered endpoint drains its backlog without falling over again.
C: Every fix from here names the tag of the property it serves.
[pause: 0.8]

[slide: v-076]
[pause: 1.0]
C: The central tension is reliability against isolation.
C: Retrying hard for one endpoint spends workers and sockets the healthy endpoints need.
[reveal: v-077]
[pause: 0.45]
C: A hard cap per endpoint keeps everyone else safe, but a failing endpoint drains slower.
[reveal: v-078]
[pause: 0.45]
C: And recovery wants to send the backlog now, which knocks the endpoint over again.
[reveal: v-079]
[pause: 0.45]
C: The resolution is a budget per endpoint: its own concurrency, its own retries, its own ramp.
C: Everything else in the design serves that.
[pause: 1.0]

[slide: v-080]
[pause: 1.3]
C: Mechanism one, the transactional outbox, as a message sequence.
[reveal: v-081]
[pause: 0.45]
C: It protects S-one, no event lost.
[reveal: v-082]
[pause: 0.45]
C: The event is a row written in the same transaction as the change, and a relay publishes unsent rows, marking them sent only after the log acknowledges.
[reveal: v-083]
[pause: 0.45]
C: It rules out the lost event, and the event for a rolled-back change.
[reveal: v-084]
[pause: 0.45]
C: It costs a table and a relay per producer, and it publishes at least once.
[reveal: v-085]
[pause: 0.45]
C: The producer writes the loan row and the outbox row in one transaction.
[reveal: v-086]
[pause: 0.45]
C: The commit succeeds, or neither exists.
[reveal: v-087]
[pause: 0.45]
C: The relay reads the unsent rows.
[reveal: v-088]
[pause: 0.45]
C: It publishes each one to the log, keyed by loan.
[reveal: v-089]
[pause: 0.45]
C: The log acknowledges.
[reveal: v-090]
[pause: 0.45]
C: Only then does the relay mark the row sent. A crash before that republishes it, which is safe, because the event I-D travels with it.
[pause: 1.1]

[slide: v-091]
[pause: 1.3]
C: Mechanism two, a durable, replayable log, drawn as who reads it.
[reveal: v-092]
[pause: 0.45]
C: It protects S-one, no event lost and L-one, delivered or dead 72h.
[reveal: v-093]
[pause: 0.45]
C: Events are appended once, keyed by loan, kept for days, and read by many consumer groups, each with its own offset. A bad deploy can rewind.
[reveal: v-094]
[pause: 0.45]
C: It rules out one consumer's bug losing events for everyone.
[reveal: v-095]
[pause: 0.45]
C: It costs a cluster to run, and ordering only within a key.
[reveal: v-096]
[pause: 0.45]
C: The relay appends once.
[reveal: v-097]
[pause: 0.45]
C: The log keeps it, keyed by loan, for seven days.
[reveal: v-098]
[pause: 0.45]
C: The fan-out group reads at its own offset.
[reveal: v-099]
[pause: 0.45]
C: And so does the audit group, without disturbing the first.
[pause: 1.1]

[slide: v-100]
[pause: 1.3]
C: Mechanism three, a queue per endpoint with a concurrency cap, drawn as the tables and their keys.
[reveal: v-101]
[pause: 0.45]
C: It protects L-two, healthy stays fast.
[reveal: v-102]
[pause: 0.45]
C: Deliveries are rows keyed by endpoint, and a worker claims only for endpoints below their in-flight cap. Pools are split by tier, like bulkheads in a ship.
[reveal: v-103]
[pause: 0.45]
C: It rules out head-of-line blocking, and one slow endpoint holding every worker.
[reveal: v-104]
[pause: 0.45]
C: It costs a failing endpoint draining slower, and caps to tune.
[reveal: v-105]
[pause: 0.45]
C: The endpoint holds its tier, its cap and its state.
[reveal: v-106]
[pause: 0.45]
C: A delivery row belongs to one endpoint, with its next attempt time and a lease. That row is the queue.
[reveal: v-107]
[pause: 0.45]
C: Every try is an attempt row.
[pause: 1.1]

[slide: v-108]
[pause: 1.3]
C: Mechanism four, backoff with full jitter, a breaker and a ramp, drawn as a state machine of one endpoint.
[reveal: v-109]
[pause: 0.45]
C: It protects L-three, recovery no relapse.
[reveal: v-110]
[pause: 0.45]
C: A retry goes at a random time below a ceiling that doubles each attempt, up to an hour. After five failures the breaker opens, and we probe once a minute. On success the rate doubles each minute up to the cap.
[reveal: v-111]
[pause: 0.45]
C: It rules out a retry storm, and synchronised retries knocking a recovering endpoint over.
[reveal: v-112]
[pause: 0.45]
C: It costs slower recovery for an endpoint that was only down for a moment.
[reveal: v-113]
[pause: 0.45]
C: An endpoint starts closed: deliveries flow.
[reveal: v-114]
[pause: 0.45]
C: Five failures open the breaker.
[reveal: v-115]
[pause: 0.45]
C: One probe a minute decides. A failed probe stays open.
[reveal: v-116]
[pause: 0.45]
C: A success starts the ramp: the rate doubles each minute, and more failures reopen it, until the cap is reached.
[pause: 1.1]

[slide: v-117]
[pause: 1.3]
C: Mechanism five, the consumer contract, as the conversation with the merchant.
[reveal: v-118]
[pause: 0.45]
C: It protects S-three, signed no replay, and correctness on the merchant's side.
[reveal: v-119]
[pause: 0.45]
C: Every call carries an event I-D, a sequence number per loan, a timestamp and an H-MAC signature. Events are versioned, and thin enough to say: fetch current state.
[reveal: v-120]
[pause: 0.45]
C: It rules out double-processing a retry, an old state overwriting a newer one, and a forged approval.
[reveal: v-121]
[pause: 0.45]
C: It costs merchants work: they store I-Ds and verify signatures, so we owe them documentation and S-D-Ks.
[reveal: v-122]
[pause: 0.45]
C: We send event ninety-one, sequence seven, signed.
[reveal: v-123]
[pause: 0.45]
C: The merchant verifies the signature and the timestamp.
[reveal: v-124]
[pause: 0.45]
C: It answers two hundred: processed.
[reveal: v-125]
[pause: 0.45]
C: We retry with the same I-D.
[reveal: v-126]
[pause: 0.45]
C: It answers two hundred again, because it has seen that I-D: not applied twice.
[reveal: v-127]
[pause: 0.45]
C: Event six arrives late.
[reveal: v-128]
[pause: 0.45]
C: It is older than the stored state, so it is ignored, and still answered two hundred.
[pause: 1.1]

[slide: v-129]
[pause: 1.3]
C: Mechanism six, an egress proxy, drawn as the path out.
[reveal: v-130]
[pause: 0.45]
C: It protects S-two, no private address.
[reveal: v-131]
[pause: 0.45]
C: Every call leaves through one proxy that resolves the name itself, refuses private address ranges, and connects to exactly the address it checked.
[reveal: v-132]
[pause: 0.45]
C: It rules out server-side request forgery, including a name that changes its address after we validated it.
[reveal: v-133]
[pause: 0.45]
C: It costs one more hop to run.
[reveal: v-134]
[pause: 0.45]
C: The dispatcher hands over a signed request.
[reveal: v-135]
[pause: 0.45]
C: The proxy resolves the name itself.
[reveal: v-136]
[pause: 0.45]
C: A range check refuses private addresses.
[reveal: v-137]
[pause: 0.45]
C: And it connects to that address, never to a second lookup.
[pause: 1.1]

[slide: v-138]
[pause: 1.3]
C: Option A, the first thing most people draw: call the merchant's U-R-L inside the booking request.
[reveal: v-139]
[pause: 0.45]
C: It has no moving parts.
[reveal: v-140]
[pause: 0.45]
C: But the booking waits for the till.
[reveal: v-141]
[pause: 0.45]
C: The pitfall: a till takes thirty seconds and holds a worker.
[reveal: v-142]
[pause: 0.45]
C: And a crash loses the event, while a rollback still sends it.
[reveal: v-143]
[pause: 0.45]
C: The booking request holds a worker.
[reveal: v-144]
[pause: 0.45]
C: While it waits on a merchant's till.
[pause: 1.1]

[slide: v-145]
[pause: 1.3]
C: Option B, one shared queue and a pool of workers.
[reveal: v-146]
[pause: 0.45]
C: It is simple to build.
[reveal: v-147]
[pause: 0.45]
C: And cheap.
[reveal: v-148]
[pause: 0.45]
C: But it has no isolation.
[reveal: v-149]
[pause: 0.45]
C: And no replay.
[reveal: v-150]
[pause: 0.45]
C: The pitfall: one slow endpoint holds the whole pool.
[reveal: v-151]
[pause: 0.45]
C: And events for healthy merchants wait behind it.
[reveal: v-152]
[pause: 0.45]
C: Producers enqueue into one queue.
[reveal: v-153]
[pause: 0.45]
C: All workers get stuck on the slow endpoint.
[reveal: v-154]
[pause: 0.45]
C: While the healthy one waits behind it.
[pause: 1.1]

[slide: v-155]
[pause: 1.3]
C: Option C, a topic, or a retry topic per delay, for each endpoint.
[reveal: v-156]
[pause: 0.45]
C: It is replayable.
[reveal: v-157]
[pause: 0.45]
C: And familiar.
[reveal: v-158]
[pause: 0.45]
C: But retries come in fixed steps.
[reveal: v-159]
[pause: 0.45]
C: And isolation is only partial.
[reveal: v-160]
[pause: 0.45]
C: The pitfall: head-of-line blocking inside a partition.
[reveal: v-161]
[pause: 0.45]
C: And the number of topics grows with the number of endpoints.
[reveal: v-162]
[pause: 0.45]
C: Producers publish.
[reveal: v-163]
[pause: 0.45]
C: To topics partitioned by endpoint, with retry topics by delay.
[reveal: v-164]
[pause: 0.45]
C: Consumers work them in fixed steps.
[pause: 1.1]

[slide: v-165]
[pause: 1.3]
C: Option D, the pick: a log for events, then delivery rows keyed by endpoint, claimed under a cap.
[reveal: v-166]
[pause: 0.45]
C: Isolation per endpoint, with any delay.
[reveal: v-167]
[pause: 0.45]
C: And replay, with an audit trail.
[reveal: v-168]
[pause: 0.45]
C: It costs about four writes per delivery.
[reveal: v-169]
[pause: 0.45]
C: And a few shards to run.
[reveal: v-170]
[pause: 0.45]
C: The pitfall: a claim without a lease strands rows.
[reveal: v-171]
[pause: 0.45]
C: And caps must be tuned per tier.
[reveal: v-172]
[pause: 0.45]
C: The log holds events, replayable.
[reveal: v-173]
[pause: 0.45]
C: Fan-out writes rows by endpoint.
[reveal: v-174]
[pause: 0.45]
C: The delivery rows are the queue.
[reveal: v-175]
[pause: 0.45]
C: And the dispatcher claims under the cap.
[pause: 1.1]

[slide: v-176]
[pause: 1.3]
C: Option E, managed publish-subscribe with push subscriptions.
[reveal: v-177]
[pause: 0.45]
C: There is nothing to run.
[reveal: v-178]
[pause: 0.45]
C: But no per-endpoint caps.
[reveal: v-179]
[pause: 0.45]
C: And no control of signing or the egress check.
[reveal: v-180]
[pause: 0.45]
C: The pitfall: a slow endpoint still piles up.
[reveal: v-181]
[pause: 0.45]
C: And private addresses cannot be refused.
[reveal: v-182]
[pause: 0.45]
C: Producers publish.
[reveal: v-183]
[pause: 0.45]
C: The service pushes to the merchant.
[reveal: v-184]
[pause: 0.45]
C: On its own terms.
[pause: 1.1]

[slide: v-185]
[pause: 1.3]
C: Option F, buy a webhook service. It works.
[reveal: v-186]
[pause: 0.45]
C: It is the fastest to production.
[reveal: v-187]
[pause: 0.45]
C: And isolation and replay come included.
[reveal: v-188]
[pause: 0.45]
C: But the data leaves our boundary.
[reveal: v-189]
[pause: 0.45]
C: And there is a cost per message.
[reveal: v-190]
[pause: 0.45]
C: The pitfall: their retry policy, not ours.
[reveal: v-191]
[pause: 0.45]
C: And lock-in on payload shapes.
[reveal: v-192]
[pause: 0.45]
C: Producers emit events.
[reveal: v-193]
[pause: 0.45]
C: To a vendor.
[reveal: v-194]
[pause: 0.45]
C: Who delivers to the merchants.
[pause: 1.1]

[slide: v-195]
[pause: 1.0]
C: The six side by side, as a summary only.
[reveal: v-196]
[pause: 0.45]
C: A fails the first time a till takes thirty seconds.
[reveal: v-197]
[pause: 0.45]
C: B fails when one slow endpoint holds the pool.
[reveal: v-198]
[pause: 0.45]
C: C has head-of-line blocking inside a partition.
[reveal: v-199]
[pause: 0.45]
V: D is the pick. What it gives up: about four writes per delivery, and a few shards to run.
[reveal: v-200]
[pause: 0.45]
C: E has no per-endpoint caps, no signing and no egress control.
[reveal: v-201]
[pause: 0.45]
C: And F, buy a service, is the honest equal. I come back to it as the alternate path.
[pause: 1.0]

[pause: 1.4]

## 4 API and entities

[slide: v-202]
[pause: 1.2]
C: The A-P-I next, then the data. Each endpoint is tagged with the requirement it serves and the entity it touches.
[pause: 1.8]

[slide: v-203]
[pause: 1.0]
C: Register.
C: A U-R-L, the event types, and an A-P-I version, which is pinned at creation.
C: The answer carries the endpoint I-D and the signing secret, shown once.
C: Before the endpoint is active, we send a verification ping it must answer.
C: F-R-one; it writes the endpoint and its subscriptions.
[pause: 1.0]

[slide: v-204]
[pause: 1.0]
C: The delivery itself, the most important contract in the system.
C: Three headers: the event I-D, a timestamp, and a signature over both and the body.
C: The body carries the type, the loan, a sequence number for that loan, the pinned version, and the data.
C: The answer codes are part of the contract too: any two hundred means done, four ten means stop sending, and anything else, including a timeout, means we retry.
C: F-R-three.
[pause: 1.0]

[slide: v-205]
[pause: 1.0]
C: Logs and replay.
C: The merchant lists deliveries by endpoint and state, with every attempt.
C: They can redeliver one, or replay everything since a time, at a rate they choose.
C: Replay is just a write to the same rows the dispatcher already claims, so it needs no second delivery path.
C: F-R-four.
[pause: 1.0]

[slide: v-206]
[pause: 1.3]
C: The conceptual model.
[reveal: v-207]
[pause: 0.45]
C: A merchant
[reveal: v-208]
[pause: 0.45]
C: owns endpoints.
[reveal: v-209]
[pause: 0.45]
C: An endpoint
[reveal: v-210]
[pause: 0.45]
C: listens to subscriptions, one per event type.
[reveal: v-211]
[pause: 0.45]
C: An event
[reveal: v-212]
[pause: 0.45]
C: fans out to deliveries:
[reveal: v-213]
[pause: 0.45]
C: one delivery is one event to one endpoint,
[reveal: v-214]
[pause: 0.45]
C: going to that endpoint,
[reveal: v-215]
[pause: 0.45]
C: and tried by attempts.
[reveal: v-216]
[pause: 0.45]
C: The delivery,
[reveal: v-217]
[pause: 0.45]
C: not the event, is the unit of state.
[pause: 1.1]

[slide: v-218]
[pause: 1.3]
C: The physical model.
[reveal: v-219]
[pause: 0.45]
C: The endpoint: U-R-L, pinned version, tier and cap, and its state.
[reveal: v-220]
[pause: 0.45]
C: The secret lives in the key service, not here.
[reveal: v-221]
[pause: 0.45]
C: The event payload, stored once per event, with the loan and its sequence.
[reveal: v-222]
[pause: 0.45]
C: Subscriptions, cached in fan-out.
C: The delivery: sharded by endpoint, unique on endpoint and event, with its state, attempt number, next attempt time and lease.
[reveal: v-223]
[pause: 0.45]
C: The attempt table, partitioned by day.
C: And the note: the timer is a column, with a partial index on the next attempt time for pending rows.
[pause: 1.1]

[slide: v-224]
[pause: 1.3]
C: One picture to settle the boundary.
[reveal: v-225]
[pause: 0.45]
C: A dashed blue line is an event, a solid line is a synchronous call over H-T-T-P-S.
[reveal: v-226]
[pause: 0.45]
C: The merchant's developer registers an endpoint with an H-T-T-P-S call: it needs an answer now.
[reveal: v-227]
[pause: 0.45]
C: The producer commits the loan and an outbox row together, then the relay appends loan booked to the log.
[reveal: v-228]
[pause: 0.45]
C: An event, inside our boundary.
C: Then the outbox row goes to the relay.
[reveal: v-229]
[pause: 0.45]
C: The relay publishes loan booked to the durable log.
C: Still an event.
[reveal: v-230]
[pause: 0.45]
C: Fan-out consumes it, and writes one delivery row per matching endpoint.
C: The dispatcher claims a row and signs it.
[reveal: v-231]
[pause: 0.45]
C: And only at the very edge does it become an H-T-T-P-S call, to a server we do not control.
C: The boundary is where our guarantees end and a stranger's begin.
[pause: 1.1]

[slide: v-232]
[pause: 1.0]
C: What the merchant's server receives.
C: An event I-D, a sequence number per loan, and a signature that carries its own timestamp and covers the body.
C: The payload is thin: a type and a loan I-D.
[reveal: v-233]
[pause: 0.45]
C: What we do with its answer.
C: Any two-hundred is delivered.
C: A client error, a server error or a timeout means retry with backoff.
C: And four-ten gone tells us to pause the endpoint.
[pause: 1.0]

[pause: 1.4]

## 5 High-level design

[slide: v-234]
[pause: 1.2]
C: Now the design, in three versions, each introduced by the objection to the one before. The boxes never move: every later picture is a view of the same baseline.
[pause: 1.8]

[slide: v-235]
[pause: 1.3]
C: Version one.
[reveal: v-236]
[pause: 0.45]
C: The producer, say origination, books the loan, and in the same request it POSTs to every subscribed merchant U-R-L.
C: It is the simplest thing that works, and for a handful of merchants on a good day, it does.
[pause: 1.1]

[slide: v-237]
[pause: 1.3]
I: Walk me through how version one breaks.
[reveal: v-238]
[pause: 0.45]
C: The booking request POSTs the loan booked event to the merchant's till.
[reveal: v-239]
[pause: 0.45]
C: The till answers after thirty seconds, and the booking request held a worker for all of it.
[reveal: v-240]
[pause: 0.45]
C: A retry inside the request.
[reveal: v-241]
[pause: 0.45]
C: And a deploy restarts the process.
[reveal: v-242]
[pause: 0.45]
C: The loan exists, and the event is gone.
[reveal: v-243]
[pause: 0.45]
C: And another booking POSTs first and then rolls back: the merchant hears of a loan that does not exist.
[pause: 1.1]

[slide: v-244]
[pause: 1.3]
C: Version two answers that. The producer writes an outbox row in the same transaction as the loan.
[reveal: v-245]
[pause: 0.45]
C: An outbox relay publishes the rows to the event log, keyed by loan,
[reveal: v-246]
[pause: 0.45]
C: and the log keeps them for seven days.
[reveal: v-247]
[pause: 0.45]
C: Dispatcher workers consume the log and POST to the merchants, retrying in process on failure. The booking request no longer waits for anyone.
[pause: 1.1]

[slide: v-248]
[pause: 1.3]
I: Version two is correct at the source.
[reveal: v-249]
[pause: 0.45]
I: What is still missing?
[reveal: v-250]
[pause: 0.45]
C: A hundred and twenty calls a second to one slow till at ten seconds each hold twelve hundred workers, and we have six hundred.
[reveal: v-251]
[pause: 0.45]
C: Events for healthy merchants queue behind the slow one in the same partition.
C: Retries live in memory, so a restart forgets them, and a two-day outage cannot live in a process.
[reveal: v-252]
[pause: 0.45]
C: And there is no record of what was sent, so when a merchant says we never sent it, we cannot answer.
C: That is version three.
[pause: 1.1]

[slide: v-253]
[pause: 1.3]
C: Version three keeps everything from version two.
[reveal: v-254]
[pause: 0.45]
C: Fan-out consumes the log and matches each event to its subscriptions.
[reveal: v-255]
[pause: 0.45]
C: It writes one row per delivery into the delivery store, keyed by endpoint. That row is the queue, and its next-attempt column is the timer.
C: The dispatcher now claims rows, only for endpoints below their in-flight cap, under a lease.
[reveal: v-256]
[pause: 0.45]
C: Every attempt goes to the attempt log,
[reveal: v-257]
[pause: 0.45]
C: and the webhooks A-P-I reads that log and replays by writing rows.
C: This is the baseline. Every picture from here is a view of it.
[pause: 1.1]

[slide: v-258]
[pause: 1.0]
C: The claim, in S-Q-L. Pending rows whose next attempt time has passed, only for endpoints whose in-flight count is under their cap, two hundred at a time, with skip locked so two dispatchers never take the same row. They move to in-flight with a thirty-second lease.
C: The lease is the lock. If a dispatcher dies, the lease expires and another one claims the row. That resend is safe because the event I-D travels with it.
[pause: 1.0]

[slide: v-259]
[pause: 1.3]
C: Requirement two, emit, by the numbers.
[reveal: v-260]
[pause: 0.45]
C: One: the producer commits the loan and the outbox row together.
[reveal: v-261]
[pause: 0.45]
C: Two: the relay publishes the row to the log, keyed by loan.
[reveal: v-262]
[pause: 0.45]
C: Three: fan-out consumes it.
[reveal: v-263]
[pause: 0.45]
C: Four: fan-out writes one delivery row per matching endpoint. The event now exists durably, three times over: the outbox, the log, and the rows.
[pause: 1.1]

[slide: v-264]
[pause: 1.3]
C: Requirement three, deliver.
[reveal: v-265]
[pause: 0.45]
C: One: fan-out writes the row.
[reveal: v-266]
[pause: 0.45]
C: Two: the dispatcher claims it, under the endpoint's cap.
[reveal: v-267]
[pause: 0.45]
C: Three: it signs and sends through the egress proxy, which arrives in version five.
[reveal: v-268]
[pause: 0.45]
C: Four: the proxy POSTs to the merchant's checked address.
[reveal: v-269]
[pause: 0.45]
C: Five: the attempt, success or failure, goes to the attempt log.
[pause: 1.1]

[slide: v-270]
[pause: 1.3]
C: Requirement one, register, as a sequence.
[reveal: v-271]
[pause: 0.45]
C: The developer POSTs the endpoint, its event types and its version.
[reveal: v-272]
[pause: 0.45]
C: The A-P-I sends a verification ping with a challenge,
[reveal: v-273]
[pause: 0.45]
C: through the egress proxy, which checks the address is public.
[reveal: v-274]
[pause: 0.45]
C: The endpoint echoes the challenge.
[reveal: v-275]
[pause: 0.45]
C: Only then is it active, and the secret is shown, once.
[pause: 1.1]

[slide: v-276]
[pause: 1.3]
C: Requirement two.
[reveal: v-277]
[pause: 0.45]
C: One transaction: book the loan, insert the outbox row, commit.
[reveal: v-278]
[pause: 0.45]
C: The relay reads unsent rows in I-D order,
[reveal: v-279]
[pause: 0.45]
C: publishes each, keyed by loan,
[reveal: v-280]
[pause: 0.45]
C: waits for the log's acknowledgement,
[reveal: v-281]
[pause: 0.45]
C: and only then marks the row sent. A crash in between publishes it twice, never zero times.
[pause: 1.1]

[slide: v-282]
[pause: 1.3]
C: Requirement three.
[reveal: v-283]
[pause: 0.45]
C: Fan-out inserts the delivery, unique on endpoint and event, so a repeated batch is absorbed.
[reveal: v-284]
[pause: 0.45]
C: The dispatcher claims it under the cap, with a lease.
[reveal: v-285]
[pause: 0.45]
C: It sends the signed POST to the proxy,
[reveal: v-286]
[pause: 0.45]
C: which forwards it to the checked address.
[reveal: v-287]
[pause: 0.45]
C: Two hundred, in a hundred and eighty milliseconds.
[reveal: v-288]
[pause: 0.45]
C: The row is delivered, and the attempt is written.
[pause: 1.1]

[slide: v-289]
[pause: 1.3]
C: Requirement four.
[reveal: v-290]
[pause: 0.45]
C: The developer asks to replay everything since nine on the second, at twenty a second.
[reveal: v-291]
[pause: 0.45]
C: The A-P-I turns those dead rows back to pending, oldest first.
[reveal: v-292]
[pause: 0.45]
C: It sets a rate limit on the endpoint until the replay drains.
[reveal: v-293]
[pause: 0.45]
C: The dispatcher claims as usual, under the cap and the rate.
[reveal: v-294]
[pause: 0.45]
C: And the developer gets a replay I-D for two hundred and forty thousand deliveries.
[pause: 1.1]

[slide: v-295]
[pause: 1.3]
C: The C4 container view of version three, one container at a time.
[reveal: v-296]
[pause: 0.45]
C: The outbox relay is a small worker per producer database. It drains outbox rows in I-D order into the log, and holds a lease so only one copy drains each database.
[reveal: v-297]
[pause: 0.45]
C: The event log holds domain events keyed by loan for seven days. Funding, servicing and analytics read it too; webhooks are one more consumer group.
[reveal: v-298]
[pause: 0.45]
C: Fan-out turns an order by loan into isolation by endpoint. It matches subscriptions from a cache and writes delivery rows in batches, committing its offset only after the write.
[reveal: v-299]
[pause: 0.45]
C: The delivery store holds one row per delivery, sharded by endpoint. The row is the queue, the next-attempt column is the timer, and the lease is the lock.
[reveal: v-300]
[pause: 0.45]
C: The dispatcher is a pool of workers that claim rows under each endpoint's cap, sign each call, send it with hard timeouts, and write the result.
[reveal: v-301]
[pause: 0.45]
C: The merchant endpoints are outside our control: tills, accounting systems and the partner bank. We assume any of them is slow, down, or hostile.
[reveal: v-302]
[pause: 0.45]
C: The attempt log keeps every try, with its status, latency and the first bytes of the answer, for thirty days in daily partitions.
[reveal: v-303]
[pause: 0.45]
C: And the webhooks A-P-I is where merchants register endpoints, read the log, and replay. It is the only container a merchant ever touches directly.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-304]
[pause: 1.2]
C: Now one level down. Every container with the technology I would run it on, including the three the challenges will add, and for each choice, the alternatives I rejected and why.
[pause: 1.8]

[slide: v-305]
[pause: 1.3]
C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide.
[reveal: v-306]
[pause: 0.45]
C: Outbox relay is Go poller; Event log is Kafka, by loan; Fan-out is Go consumer group; Dispatcher is Go, bulkheads; Delivery store is PostgreSQL, by endpoint; Webhooks API is Go, PostgreSQL; Attempt log is PostgreSQL by day.
[reveal: v-307]
[pause: 0.45]
C: Contract renderer is schema registry.
[reveal: v-308]
[pause: 0.45]
C: Egress proxy is Smokescreen.
[reveal: v-309]
[pause: 0.45]
C: Endpoint health is Go control loop.
[pause: 1.1]

[slide: v-310]
[pause: 1.3]
C: One level further down, inside the dispatcher, the box challenges two, three and five will open.
[reveal: v-311]
[pause: 0.45]
C: Due rows come from the delivery store.
[reveal: v-312]
[pause: 0.45]
C: The claimer takes them with skip locked and a lease, and only for endpoints under their cap.
[reveal: v-313]
[pause: 0.45]
C: Tier pools are bulkheads: the partner bank, large merchants and the long tail never share workers.
[reveal: v-314]
[pause: 0.45]
C: The endpoint limiter is a semaphore per endpoint: ten calls in flight by default.
[reveal: v-315]
[pause: 0.45]
C: A breaker per endpoint opens after five failures in a row.
[reveal: v-316]
[pause: 0.45]
C: The H-T-T-P client has a two-second connect timeout, a ten-second total, keep-alive, and reads at most four kilobytes of any answer.
[reveal: v-317]
[pause: 0.45]
C: The signer computes an H-MAC over the event I-D, the timestamp and the body,
[reveal: v-318]
[pause: 0.45]
C: with the endpoint's secret from the key service, cached for five minutes.
[reveal: v-319]
[pause: 0.45]
C: Every call leaves through the egress proxy.
[reveal: v-320]
[pause: 0.45]
C: The result writer marks the row delivered, or writes its next attempt time,
[reveal: v-321]
[pause: 0.45]
C: and reports the outcome to the endpoint health loop.
[pause: 1.1]

[slide: v-322]
[pause: 1.3]
C: And inside fan-out, which challenges four and six open.
[reveal: v-323]
[pause: 0.45]
C: Events arrive from the log, ordered by loan.
[reveal: v-324]
[pause: 0.45]
C: The log consumer commits its offset only after its batch is written, so a crash repeats a batch.
[reveal: v-325]
[pause: 0.45]
C: Subscription changes come from the webhooks A-P-I,
[reveal: v-326]
[pause: 0.45]
C: into an in-memory cache.
[reveal: v-327]
[pause: 0.45]
C: The matcher turns one event into N endpoints by type and merchant.
[reveal: v-328]
[pause: 0.45]
C: The renderer turns the internal event into each endpoint's pinned public version,
[reveal: v-329]
[pause: 0.45]
C: from the schema registry, which arrives in version six.
[reveal: v-330]
[pause: 0.45]
C: The payload writer stores each event once, not once per delivery.
[reveal: v-331]
[pause: 0.45]
C: The sequence check carries the producer's sequence number for the loan.
[reveal: v-332]
[pause: 0.45]
C: The delivery writer inserts rows in batches, unique on endpoint and event, so a repeated batch is absorbed,
[reveal: v-333]
[pause: 0.45]
C: into the delivery store.
[pause: 1.1]

[slide: v-334]
[pause: 1.0]
C: The producer inserts the outbox row in the same transaction as the change. The relay publishes unsent rows in ID order, keyed by loan, and marks them sent only after the log acknowledges.
[reveal: v-335]
[pause: 0.45]
C: Why An outbox table in each producer's PostgreSQL, drained by a Go poller in ID order: Only one transaction can make “the loan was booked” and “the world will hear about it” a single fact.
[reveal: v-336]
[pause: 0.45]
C: Rejected: A dual write: commit, then publish to Kafka. A crash between the two loses the event, or publishes one for a change that rolled back.
[reveal: v-337]
[pause: 0.45]
C: Change data capture with Debezium. An honest equal: no polling and no extra table, but one more system to run.
[pause: 1.0]

[slide: v-338]
[pause: 1.0]
C: One topic per domain, keyed by loan ID, so one loan's events stay in commit order. Seven days of retention; webhooks are one more consumer group, and its lag is our first indicator.
[reveal: v-339]
[pause: 0.45]
C: Why Kafka, domain topics keyed by loan ID, seven days of retention: Funding, servicing and analytics already read these events. Webhooks are one more consumer group, with their own offsets.
[reveal: v-340]
[pause: 0.45]
C: Rejected: Amazon SQS as the backbone. No replay after a message is consumed, and no per-key ordering shared by many consumer groups.
[reveal: v-341]
[pause: 0.45]
C: RabbitMQ. Replay and a backlog of days are not what it is built for; each consumer needs its own queue copy.
[pause: 1.0]

[slide: v-342]
[pause: 1.0]
C: Each consumer matches events to subscriptions from an in-memory cache and inserts one delivery row per match, in batches, unique on event and endpoint. The log offset is committed only after the batch is written.
[reveal: v-343]
[pause: 0.45]
C: Why A Go consumer group with an in-memory subscription cache, writing delivery rows in batches: The event log is ordered by loan; delivery must be isolated by endpoint. Fan-out is where one becomes the other.
[reveal: v-344]
[pause: 0.45]
C: Rejected: One Kafka topic per endpoint. Twenty thousand topics, created and deleted by self-service registration.
[reveal: v-345]
[pause: 0.45]
C: Filtering inside every dispatcher. Every worker reads every event; isolation by endpoint is lost before it starts.
[pause: 1.0]

[slide: v-346]
[pause: 1.0]
C: A row per delivery, on the shard that owns its endpoint, with its state, next attempt time and lease. Workers claim due rows with skip locked; an expired lease makes a row claimable again.
[reveal: v-347]
[pause: 0.45]
C: Why PostgreSQL sharded by endpoint ID; claim with SKIP LOCKED and a lease; next_attempt_at is the timer: Each endpoint needs its own queue, its own delay and its own state for days. Rows in a table give all three without twenty thousand queues.
[reveal: v-348]
[pause: 0.45]
C: Rejected: Kafka retry topics. Fixed delays, and head-of-line blocking within each partition: one slow endpoint delays everything behind it.
[reveal: v-349]
[pause: 0.45]
C: An SQS queue per endpoint. Twenty thousand queues to manage, and a fifteen-minute ceiling on message delay.
[pause: 1.0]

[slide: v-350]
[pause: 1.0]
C: Workers claim only for endpoints under their in-flight cap, ten by default, in pools split by merchant tier. Every call has a 2 s connect and a 10 s total timeout, is signed, and leaves through the egress proxy.
[reveal: v-351]
[pause: 0.45]
C: Why Go workers: a concurrency cap per endpoint, pools per merchant tier, a breaker per endpoint: One slow endpoint must never spend the capacity another endpoint needs. The cap is the whole design.
[reveal: v-352]
[pause: 0.45]
C: Rejected: One shared worker pool with retries. A slow endpoint holds every worker: at ten seconds a call, 120 calls a second need 1,200 sockets.
[reveal: v-353]
[pause: 0.45]
C: A thread pool per endpoint. Twenty thousand pools, almost all idle; a cap on in-flight calls gives the same isolation for free.
[pause: 1.0]

[slide: v-354]
[pause: 1.0]
C: The proxy resolves the name itself, refuses private, loopback, link-local and metadata addresses, and connects to the address it checked. Dispatchers have no other route out.
[reveal: v-355]
[pause: 0.45]
C: Why Smokescreen, an open-source egress proxy, in front of every dispatcher: A customer-supplied URL is untrusted input that our servers will call. The check must happen on the address actually connected to.
[reveal: v-356]
[pause: 0.45]
C: Rejected: Checking the URL at registration only. DNS rebinding: the name resolves to a public address at registration and to a private one at send time.
[reveal: v-357]
[pause: 0.45]
C: A firewall allow-list of merchant addresses. Twenty thousand self-served endpoints on cloud hosts whose addresses change.
[pause: 1.0]

[slide: v-358]
[pause: 1.0]
C: One row per attempt: status, latency, the first bytes of the answer, the error class. Daily partitions, copied to object storage and dropped after thirty days.
[reveal: v-359]
[pause: 0.45]
C: Why PostgreSQL partitioned by day, then object storage; read by the merchant dashboard: Support, the merchant and on-call ask the same question: what did we send, when, and what did they answer?
[reveal: v-360]
[pause: 0.45]
C: Rejected: Elasticsearch. Full-text search is not the question asked; an append-only daily table is cheaper to run.
[reveal: v-361]
[pause: 0.45]
C: ClickHouse. An honest equal at ten times the volume, for analytics across all endpoints; one more system at ours.
[pause: 1.0]

[slide: v-362]
[pause: 1.0]
C: Each endpoint is pinned to a dated public version; fan-out renders the internal event into it from a registry of every supported version. A producer's build fails if a supported version stops rendering.
[reveal: v-363]
[pause: 0.45]
C: Why A schema registry of public event versions, rendered at fan-out for each endpoint's pinned version: Producers must be free to change their internal events; merchants must not have to change their integrations when they do.
[reveal: v-364]
[pause: 0.45]
C: Rejected: Sending the internal event as it is. Every internal refactor becomes a breaking change for twenty thousand integrations.
[reveal: v-365]
[pause: 0.45]
C: One public payload forever. It freezes the product; fields that should be renamed or split never can be.
[pause: 1.0]

[slide: v-366]
[pause: 1.0]
C: The stack on one slide, as I would leave it on the whiteboard.
C: Outbox relay: Outbox + Go poller.
C: Not Dual write; Debezium.
C: One commit, one fact.
[reveal: v-367]
[pause: 0.45]
C: Event log: Kafka, by loan.
C: Not SQS; RabbitMQ.
C: Replay, many readers.
[reveal: v-368]
[pause: 0.45]
C: Fan-out: Go consumer group.
C: Not Topic per endpoint.
C: Loan order to endpoint rows.
[reveal: v-369]
[pause: 0.45]
C: Delivery store: PostgreSQL by endpoint.
C: Not Retry topics; SQS.
C: A queue per endpoint, as rows.
[reveal: v-370]
[pause: 0.45]
C: Dispatcher: Go, caps, tier pools.
C: Not Shared pool; pool each.
C: Each spends its own budget.
[reveal: v-371]
[pause: 0.45]
C: Egress proxy: Smokescreen.
C: Not URL check; allow-list.
C: Check the IP you connect to.
[reveal: v-372]
[pause: 0.45]
C: Attempt log: PostgreSQL by day.
C: Not Elasticsearch; ClickHouse.
C: Drop a day, not rows.
[reveal: v-373]
[pause: 0.45]
C: Contract renderer: Registry, pinned versions.
C: Not Internal as is; freeze.
C: The contract is the product.
[reveal: v-374]
[pause: 0.45]
N: Naming a product is not the signal.
N: Naming the property that rules out its rival is.
N: Interviewers go one level down on whichever box you name, so name only what you can defend.
[pause: 1.0]

[slide: v-375]
[pause: 0.6]
N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.
[pause: 3.0]

[slide: v-376]
[pause: 1.0]
N: Here is where interviewers usually go.
I: The relay crashed after Kafka acknowledged but before it marked the row sent.
I: What happens?
[pause: 1.2]
N: The row is published again on restart: at-least-once.
N: Every consumer, including fan-out, de-duplicates by event ID, so the merchant still gets one delivery.
[reveal: v-377]
[pause: 0.45]
N: The trap is trying to make the relay exactly-once.
I: A merchant adds a subscription while an event for them is in flight.
I: Do they get it?
[pause: 1.2]
N: The cache is refreshed from subscription change events, so there is a short window.
N: The contract says subscriptions take effect within a minute, and the merchant can replay anything since a timestamp.
[reveal: v-378]
[pause: 0.45]
N: The trap is promising the instant.
I: Two dispatchers claim at the same moment.
I: Can both send the same delivery?
[pause: 1.2]
N: No: skip locked gives the row to one of them, and the lease marks it.
N: If that worker dies, the lease expires and another sends it again: at-least-once, which the event ID makes safe.
[reveal: v-379]
[pause: 0.45]
N: The trap is a distributed lock.
I: The partner bank's endpoint slows to nine seconds at the peak.
I: What happens to a small merchant's delivery?
[pause: 1.2]
N: Nothing: the bank's endpoint is capped and sits in its own tier pool, so it queues in its own rows while the small merchant's pool is untouched.
[reveal: v-380]
[pause: 0.45]
N: The trap is a bigger shared pool.
I: A merchant registers a name that resolves to 10.0.0.5 only after you validated it.
I: What stops the call?
[pause: 1.2]
N: The proxy resolves at send time and refuses private ranges, and it connects to the address it checked, so rebinding has no gap to use.
[reveal: v-381]
[pause: 0.45]
N: The trap is a stricter regex.
N: If you picked a box that is not on this list, good.
N: Write its probe down and answer it before you watch on.
[pause: 1.2]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-382]
[pause: 1.2]
C: Before I break it, the simpler design. At this scale it is a serious option, and saying so is part of the answer.
[pause: 1.8]

[slide: v-383]
[pause: 1.3]
C: The alternate path changes one box.
[reveal: v-384]
[pause: 0.45]
C: Our outbox, our log, fan-out and the public contract stay ours.
C: The dispatcher, marked alternate, becomes a managed webhook service: it stores, signs, retries and shows merchants their logs.
[reveal: v-385]
[pause: 0.45]
C: What it gives up, precisely: loan-level data now leaves for a vendor, and the partner bank's vendor-risk review must approve that.
C: The isolation caps and tiers are the vendor's, not ours.
C: And the cost grows with every message.
[reveal: v-386]
[pause: 0.45]
C: The crossover, from the scale line.
C: A hundred and eighty million deliveries a month, at an illustrative ten cents a thousand, is about eighteen thousand dollars a month.
C: A team of three with on-call and infrastructure costs about eighty.
C: On cost alone, building wins only past about eight hundred million deliveries a month.
[pause: 1.1]

[slide: v-387]
[pause: 0.7]
V: At a hundred and eighty million deliveries a month, I would seriously consider buying the delivery engine, and keep the outbox, the log and the contract. I'd build when the partner bank won't let loan-level data leave, or past about eight hundred million a month.
[pause: 1.0]
N: Saying that is not a weakness in a design round. It is the build-against-buy judgement the manager layer is graded on. The rest of this video designs the build, because that is where the mechanisms are.
[pause: 1.6]

[pause: 1.4]

## 6 Bridge

[slide: v-388]
[pause: 1.2]
V: It works. Where does it break first?
[pause: 1.8]

[slide: v-389]
[pause: 1.3]
C: The baseline, with seven attack points.
C: The producers: what if delivery happens inside their request.
C: The dispatcher: one slow endpoint, then a dead one.
C: Endpoint health: the recovery.
[reveal: v-390]
[pause: 0.45]
C: Fan-out: duplicates and order.
C: The egress path: hostile U-R-Ls and forged calls.
C: The renderer: a producer changing the payload.
C: And the attempt log: how we'd know.
C: I'll take them in an order where each fix creates the next question.
[pause: 1.1]

[pause: 1.4]

## 7 Challenges

[slide: v-391]
[pause: 1.2]
C: Seven challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks, the fix one level down, why it works, the push on the fix itself, and what I'd say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Why not publish after the commit?

[slide: v-392]
[pause: 1.2]
N: Challenge one. The interviewer pokes at the outbox: is it really needed, or is it ceremony?
[pause: 1.8]

[slide: v-393]
[pause: 0.6]
I: Why an outbox table? Commit the loan, then publish to Kafka. It's simpler.
[pause: 2.0]

[slide: v-394]
[pause: 1.3]
C: The naive answer: commit, then publish, and retry the publish if it fails.
[reveal: v-395]
[pause: 0.45]
C: Look at the producer, marked red.
[reveal: v-396]
[pause: 0.45]
C: It is the same flaw as calling the merchant inside the request: two systems, two commits, and nothing that makes them one.
[pause: 1.1]

[slide: v-397]
[pause: 1.0]
C: The trace.
[reveal: v-398]
[pause: 0.45]
C: The loan is committed as booked.
[reveal: v-399]
[pause: 0.45]
C: Four milliseconds later a deploy kills the process, before the publish.
[reveal: v-400]
[pause: 0.45]
C: The customer sees approved, and the till waits for the event.
[reveal: v-401]
[pause: 0.45]
C: It never comes. The merchant voids the sale, and we hold a loan with no purchase behind it.
[reveal: v-402]
[pause: 0.45]
C: Publish first instead, and when the commit fails, the till hands over goods for a loan that never existed.
[reveal: v-403]
[pause: 0.45]
C: The window is milliseconds, but at eight hundred events a second, every deploy hits it.
[pause: 1.0]

[slide: v-404]
[pause: 1.3]
C: The fix, one level down.
C: The producer inserts an outbox row in the loan's own transaction: the event I-D, the loan, its sequence number, the type and the body.
[reveal: v-405]
[pause: 0.45]
C: The relay, outlined green, reads unsent rows in I-D order, publishes each keyed by loan, and marks it sent only after the log acknowledges.
C: S-one, no event lost holds: the event exists exactly when the commit does.
[reveal: v-406]
[pause: 0.45]
C: What it does not cover: a relay that dies between the acknowledgement and the mark publishes twice.
C: That's why every consumer de-duplicates by event I-D.
C: And it's not the tool under it, a distributed transaction across the database and the log, which neither supports well and which would couple their availability.
[reveal: v-407]
[pause: 0.45]
C: Rejected: A dual write: commit, then publish.
C: A crash between the two loses the event, or sends one for a change that rolled back.
[pause: 1.1]

[slide: v-408]
[pause: 1.0]
C: The relay in pseudocode. Every two hundred milliseconds, holding its lease, read up to five hundred unsent rows in I-D order. Send each to its topic, keyed by loan, carrying the event I-D. Wait for every acknowledgement. Only then mark them sent.
C: Mark before publishing and a crash loses events. Mark after, and a crash repeats them. We choose repeats, because the I-D makes them harmless.
[pause: 1.0]

[slide: v-409]
[pause: 0.6]
I: It's the morning of the second. Four hundred and eighty thousand payment events land in ten minutes. Is the relay the bottleneck?
[pause: 2.0]

[slide: v-410]
[pause: 0.6]
C: Not at this scale, if it batches.
C: Five hundred rows a round with pipelined sends is several thousand a second for one relay.
[reveal: v-411]
[pause: 0.45]
C: The peak is eight hundred.
C: Measure it by the age of the oldest unsent row, alerting over thirty seconds, not by a count.
[reveal: v-412]
[pause: 0.45]
C: And delete sent rows after a day, because a bloated outbox slows the producer's own writes.
[reveal: v-413]
[pause: 0.45]
C: The honest limit: past several thousand a second, the lease has to be split by I-D range across relays.
C: Not needed here.
[pause: 0.8]

[slide: v-414]
[pause: 0.7]
V: If asked, I'd say: no event without its commit, and none for a rollback. The outbox row is in the same transaction, the relay publishes at least once, and consumers de-duplicate by event I-D.
[pause: 1.0]
N: The events are now safe. The next question is whether one merchant can hurt the others.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: One slow endpoint

[slide: v-415]
[pause: 1.2]
N: Challenge two, the first half of the crux. One merchant's server slows down at the worst moment.
[pause: 1.8]

[slide: v-416]
[pause: 0.6]
I: At nine on the second, one till vendor's server starts taking ten seconds to answer. What happens to the partner bank's deliveries?
[pause: 2.0]

[slide: v-417]
[pause: 1.3]
C: The naive answer: autoscale the pool.
[reveal: v-418]
[pause: 0.45]
C: Look inside the dispatcher: the limiter and the client, marked red.
[reveal: v-419]
[pause: 0.45]
C: Without a cap per endpoint, a slow endpoint takes whatever capacity you add.
[reveal: v-420]
[pause: 0.45]
C: At ten seconds a call, it will hold every socket you give it.
[pause: 1.1]

[slide: v-421]
[pause: 1.0]
C: The trace.
[reveal: v-422]
[pause: 0.45]
C: At nine, the settlement file lands: two thousand four hundred deliveries a second.
[reveal: v-423]
[pause: 0.45]
C: Five seconds later, the till vendor, with five percent of the traffic, slows to our ten-second timeout.
[reveal: v-424]
[pause: 0.45]
C: By ten past, it holds twelve hundred calls in flight. The pool has six hundred.
[reveal: v-425]
[pause: 0.45]
C: The partner bank's p ninety-nine goes from a third of a second to four minutes, and approvals at every other till wait too.
[reveal: v-426]
[pause: 0.45]
C: Autoscaling doubles the pool, and the slow endpoint simply holds all of it.
[pause: 1.0]

[slide: v-427]
[pause: 1.3]
C: The fix, inside the dispatcher, with no new container.
[reveal: v-428]
[pause: 0.45]
C: The claim query only takes rows for endpoints whose in-flight count is below their cap, ten by default.
C: The count goes up in the claim's commit and down in the result's commit, so it lives in the same database as the rows and can't drift.
[reveal: v-429]
[pause: 0.45]
C: Tier pools are bulkheads: the bank, large merchants and the long tail run on separate workers.
C: And a breaker per endpoint opens after five failures in a row.
[reveal: v-430]
[pause: 0.45]
C: L-two, healthy stays fast holds: the slow endpoint queues in its own rows, and everyone else's p ninety-nine doesn't move.
C: What it doesn't cover: a flood of events from one merchant's own activity, which fills rows, not sockets.
[reveal: v-431]
[pause: 0.45]
C: That's a fair-share limit at fan-out.
C: And it's not the tool under it: a thread pool per endpoint would be twenty thousand mostly idle pools for the same isolation.
[reveal: v-432]
[pause: 0.45]
C: Rejected: A Kafka partition, or retry topics, per endpoint.
C: Head-of-line blocking: one slow endpoint stalls everything queued behind it.
[pause: 1.1]

[slide: v-433]
[pause: 1.0]
C: Every cap comes from Little's law.
[reveal: v-434]
[pause: 0.45]
C: The till vendor, healthy: a hundred and twenty a second times a quarter of a second is thirty in flight. A cap of forty, in the large-merchant pool.
[reveal: v-435]
[pause: 0.45]
C: The same vendor, slow: it would need twelve hundred. It gets forty, and the rest wait in rows.
[reveal: v-436]
[pause: 0.45]
C: The partner bank: eight hundred a second times a fifth of a second is a hundred and sixty. A cap of two hundred, set by contract, in its own pool.
[reveal: v-437]
[pause: 0.45]
C: And the long tail, under one a second: less than one in flight. The default of ten is generous.
[pause: 1.0]

[slide: v-438]
[pause: 0.6]
I: The partner bank says your cap is throttling them. They want everything in real time.
[pause: 2.0]

[slide: v-439]
[pause: 0.6]
C: Two answers.
C: Caps are a contract, not a constant.
C: The bank's lag gets its own target, and we raise its cap when its endpoint proves it can take more.
[reveal: v-440]
[pause: 0.45]
C: Better still, for a machine consumer, batch: up to a hundred events per POST, so eight hundred a second becomes eight calls a second.
[reveal: v-441]
[pause: 0.45]
C: And if their endpoint slows when we send faster, the cap is protecting them from us.
[reveal: v-442]
[pause: 0.45]
C: The honest limit: a batch makes one failure cover a hundred events, so the answer must list results per event, and that's a contract change for them.
[pause: 0.8]

[slide: v-443]
[pause: 0.7]
V: If asked, I'd say: every endpoint spends its own budget. A cap on in-flight calls set by Little's law, pools per tier, and a breaker. A slow endpoint queues in its own rows, and nobody else's latency moves.
[pause: 1.0]
N: Slow is the easy half. The next question is an endpoint that is gone for days, and then comes back.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Down for two days, then back

[slide: v-444]
[pause: 1.2]
N: Challenge three, the second half of the crux. Recovery is where most designs knock the endpoint over again.
[pause: 1.8]

[slide: v-445]
[pause: 0.6]
I: A merchant's accounting system is down from Friday evening to Sunday evening. What happens, and what happens when it comes back?
[pause: 2.0]

[slide: v-446]
[pause: 1.3]
C: The naive answer:
[reveal: v-447]
[pause: 0.45]
C: retry every ten seconds, five times, then a dead-letter queue, and send the backlog when it's back.
[reveal: v-448]
[pause: 0.45]
C: The result writer, marked red, is where that policy lives.
[pause: 1.1]

[slide: v-449]
[pause: 1.0]
C: The trace.
[reveal: v-450]
[pause: 0.45]
C: Friday at six the accounting system goes down. It takes two percent of deliveries, one point four a second.
[reveal: v-451]
[pause: 0.45]
C: A minute later, five retries at ten seconds have already killed the first deliveries.
[reveal: v-452]
[pause: 0.45]
C: By Sunday evening, two hundred and forty thousand deliveries are waiting.
[reveal: v-453]
[pause: 0.45]
C: It comes back, and we send everything at once: seventeen hundred times its normal load. It falls over again.
[reveal: v-454]
[pause: 0.45]
C: And on Monday the merchant finds a quarter of a million dead letters, and no way to replay them.
[pause: 1.0]

[slide: v-455]
[pause: 1.3]
C: The fix, version four: a new container, endpoint health, a control loop beside the dispatcher.
C: One level down.
[reveal: v-456]
[pause: 0.45]
C: The result writer sets the next attempt to now plus a random time below a ceiling that doubles each attempt, capped at an hour.
C: That's full jitter, so a quarter of a million rows don't retry in step.
C: After seventy-two hours a delivery is dead, visibly.
[reveal: v-457]
[pause: 0.45]
C: The breaker pauses the whole endpoint after five failures, so its rows stop being claimed at all, and health probes one oldest delivery a minute.
C: On success it opens at one a second and doubles each clean minute up to the cap.
C: Over five percent errors, it halves.
[reveal: v-458]
[pause: 0.45]
C: L-three, recovery no relapse holds: recovery is earned, not dumped.
C: What it doesn't cover: an endpoint that is up but answers four hundred to everything, a bug on their side.
C: Those die per delivery after the window, and the dashboard says why.
[reveal: v-459]
[pause: 0.45]
C: And it's not a fixed retry count, which a weekend outlasts.
C: Rejected: A fixed retry count every ten seconds.
C: Synchronised retries knock a recovering endpoint over again, and a two-day outage outlasts any fixed count.
[pause: 1.1]

[slide: v-460]
[pause: 1.3]
C: On the baseline: the dispatcher, the delivery store and the attempt log are carried.
[reveal: v-461]
[pause: 0.45]
C: Endpoint health is new. It reads outcomes from the attempt log, and pauses, probes and ramps each endpoint by writing to the delivery store.
[pause: 1.1]

[slide: v-462]
[pause: 1.3]
C: The ramp as a sequence.
[reveal: v-463]
[pause: 0.45]
C: The breaker has been open since Friday; health probes once a minute.
[reveal: v-464]
[pause: 0.45]
C: The dispatcher sends one oldest delivery.
[reveal: v-465]
[pause: 0.45]
C: It answers two hundred.
[reveal: v-466]
[pause: 0.45]
C: Half-open: one a second.
[reveal: v-467]
[pause: 0.45]
C: No errors for a minute: double, up to the cap.
[reveal: v-468]
[pause: 0.45]
C: And if errors pass five percent, halve the rate. At the cap of ten in flight, the backlog drains in under two hours.
[pause: 1.1]

[slide: v-469]
[pause: 1.0]
C: The merchant's side.
[reveal: v-470]
[pause: 0.45]
C: After an hour with the breaker open, we email the endpoint's technical contact and put a banner in their dashboard.
[reveal: v-471]
[pause: 0.45]
C: After seventy-two hours, the deliveries are dead and the endpoint is disabled, with another email.
[reveal: v-472]
[pause: 0.45]
C: When they fix it, they replay since a time, at a rate they choose, oldest first per loan.
[reveal: v-473]
[pause: 0.45]
C: And a four-ten means stop: we unsubscribe at once.
[pause: 1.0]

[slide: v-474]
[pause: 0.6]
I: They replay two hundred and forty thousand events. Their till only cares about the current status of each loan. Do you send all of them?
[pause: 2.0]

[slide: v-475]
[pause: 0.6]
C: Offer both.
C: A latest-state replay collapses the backlog to the newest event per loan: two hundred and forty thousand events for about sixty thousand loans become sixty thousand calls.
[reveal: v-476]
[pause: 0.45]
C: A till wants that.
C: An accounting system needs every refund and payment, so it replays the full history, oldest first per loan.
[reveal: v-477]
[pause: 0.45]
C: The replay request names the mode.
[reveal: v-478]
[pause: 0.45]
C: The honest limit: a collapsed replay hides intermediate states, so anything that books money must take the full history.
[pause: 0.8]

[slide: v-479]
[pause: 0.7]
V: If asked, I'd say: retries spread with full jitter, capped at an hour, for seventy-two hours. A breaker pauses the endpoint, probes it, and ramps it back. The merchant is told, and replays at a rate they choose.
[pause: 1.0]
N: Replays and retries mean the same event can arrive twice, and late. That's the next question.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Twice, and out of order

[slide: v-480]
[pause: 1.2]
N: Challenge four. What the merchant sees when at-least-once meets a retry.
[pause: 1.8]

[slide: v-481]
[pause: 0.6]
I: A merchant's till shows a loan as refunded after it was paid off, and it processed one refund twice. Fix it.
[pause: 2.0]

[slide: v-482]
[pause: 1.3]
C: The naive answer: guarantee exactly-once delivery, in order.
[reveal: v-483]
[pause: 0.45]
C: The delivery writer,
[reveal: v-484]
[pause: 0.45]
C: marked red, can't keep that promise, because what breaks it happens on the other side of the network.
[pause: 1.1]

[slide: v-485]
[pause: 1.0]
C: The trace.
[reveal: v-486]
[pause: 0.45]
C: At ten, the refund event, sequence seven, is sent, and the till applies it.
[reveal: v-487]
[pause: 0.45]
C: Its answer is lost. We see a timeout.
[reveal: v-488]
[pause: 0.45]
C: A minute later, paid off, sequence eight, is delivered.
[reveal: v-489]
[pause: 0.45]
C: Then our retry of sequence seven arrives. The till applies the refund twice and shows refunded. Only the till knew the first one had worked.
[pause: 1.0]

[slide: v-490]
[pause: 1.3]
C: The fix is the contract, with no version change.
C: At-least-once, said out loud, and every call carries the event I-D.
[reveal: v-491]
[pause: 0.45]
C: The till keeps the I-Ds it has processed for seven days, longer than our seventy-two-hour window, so a retry is ignored.
C: One level down: the sequence.
[reveal: v-492]
[pause: 0.45]
C: It is the loan's version, incremented in the same transaction as the change and written into the outbox row, so it is monotonic and gap-free per loan.
C: The till applies an event only if its sequence is higher than the last one it saw.
[reveal: v-493]
[pause: 0.45]
C: Sequence seven after eight is dropped.
C: And events are thin enough that a till can always fetch the loan's current state instead.
C: What it doesn't cover: a merchant who ignores the contract.
[reveal: v-494]
[pause: 0.45]
C: That's documentation, an S-D-K, and a test tool.
C: Rejected: An exactly-once, ordered delivery promise.
C: Impossible into a system we do not control; the consumer de-duplicates by event ID and orders by sequence.
[pause: 1.1]

[slide: v-495]
[pause: 1.0]
C: What we ask every merchant to do, in pseudocode, and ship in the S-D-K. Verify the signature. If the I-D was seen, answer two hundred and stop. Otherwise, in one transaction, apply the event only if its sequence is newer than the last one for that loan, and record the I-D.
C: And answer fast. A receiver that does slow work before answering turns its own latency into our retries.
[pause: 1.0]

[slide: v-496]
[pause: 0.6]
I: Why not deliver in strict order per endpoint?
[pause: 2.0]

[slide: v-497]
[pause: 0.6]
C: We can offer it, and say what it costs.
C: Strict order means one call in flight per endpoint: at a quarter of a second, four a second at most.
[reveal: v-498]
[pause: 0.45]
C: And one failing event blocks everything behind it until it dies, which is the head-of-line problem from challenge two, chosen on purpose.
[reveal: v-499]
[pause: 0.45]
C: So the default is parallel delivery plus sequence numbers, with order restored by the receiver.
[reveal: v-500]
[pause: 0.45]
C: The honest limit: a merchant who needs order and can't store a sequence pays for it in throughput.
[pause: 0.8]

[slide: v-501]
[pause: 0.7]
V: If asked, I'd say: we deliver at least once; you make the effect once. Every event carries an I-D to de-duplicate, a per-loan sequence to order, and is thin enough to fetch current state.
[pause: 1.0]
N: The till now trusts the content. The next question is whether it can trust the sender, and whether we can trust the U-R-L.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: Hostile URLs and forged calls

[slide: v-502]
[pause: 1.2]
N: Challenge five. Self-service URLs are input that our servers will call, and a webhook that releases goods is worth forging.
[pause: 1.8]

[slide: v-503]
[pause: 0.6]
I: Someone registers one-six-nine, two-five-four, one-six-nine, two-five-four as their webhook U-R-L. Someone else POSTs a fake loan approved event to a merchant's till. Go.
[pause: 2.0]

[slide: v-504]
[pause: 1.3]
C: The naive answer:
[reveal: v-505]
[pause: 0.45]
C: validate the U-R-L at registration,
[reveal: v-506]
[pause: 0.45]
C: and send an A-P-I key in a header so the till knows it's us.
[reveal: v-507]
[pause: 0.45]
C: The H-T-T-P client and the path out, marked red, trust what they were given.
[pause: 1.1]

[slide: v-508]
[pause: 1.0]
C: The trace.
[reveal: v-509]
[pause: 0.45]
C: A name is registered that resolves to a public address. The check passes.
[reveal: v-510]
[pause: 0.45]
C: At send time the name resolves to the cloud's metadata address, and our dispatcher POSTs to it from inside our network.
[reveal: v-511]
[pause: 0.45]
C: The first bytes of the answer, a credential, appear in the attacker's own delivery log. That's server-side request forgery, through D-N-S rebinding.
[reveal: v-512]
[pause: 0.45]
C: Separately, a fraudster POSTs a loan approved event for two thousand four hundred dollars to a till, with a header copied from an old request.
[reveal: v-513]
[pause: 0.45]
C: The till releases a television for a loan that doesn't exist.
[pause: 1.0]

[slide: v-514]
[pause: 1.3]
C: The fix, version five: the egress proxy joins the baseline, and the signer changes.
C: One level down on the proxy.
[reveal: v-515]
[pause: 0.45]
C: Every call leaves through it.
C: It resolves the name itself, refuses private, loopback, link-local and metadata ranges, and connects to the exact address it checked, so a name that changes between check and use gains nothing.
C: Network policy gives dispatchers no other route out.
[reveal: v-516]
[pause: 0.45]
C: And answers are truncated and scrubbed before they reach a log.
C: On the signature: an H-MAC, SHA two-fifty-six, over the event I-D, the timestamp and the body, with a secret per endpoint from the key service.
C: The till recomputes it, compares in constant time, and rejects anything more than five minutes old.
[reveal: v-517]
[pause: 0.45]
C: A copied request fails the timestamp; a replayed one inside five minutes is caught by its I-D.
C: S-two, no private address and S-three, signed no replay hold.
C: What it doesn't cover: a leaked secret, which is rotation.
[reveal: v-518]
[pause: 0.45]
C: And it's not the tool under it: an A-P-I key in a header proves nothing about the body and can be replayed forever.
C: Rejected: Checking the URL string at registration.
C: DNS rebinding resolves a public name to a private address at send time; only the egress proxy sees the real address.
[pause: 1.1]

[slide: v-519]
[pause: 1.3]
C: On the baseline: the dispatcher and the merchant endpoint are carried.
[reveal: v-520]
[pause: 0.45]
C: The egress proxy is new, and it now sits on the only path between them.
[pause: 1.1]

[slide: v-521]
[pause: 1.3]
C: As a sequence.
[reveal: v-522]
[pause: 0.45]
C: The dispatcher gets the endpoint's secret from the key service, cached for five minutes.
[reveal: v-523]
[pause: 0.45]
C: It POSTs with the timestamp and the H-MAC over the I-D, the timestamp and the body.
[reveal: v-524]
[pause: 0.45]
C: The till rejects anything older than five minutes.
[reveal: v-525]
[pause: 0.45]
C: It compares in constant time, against the current secret and, during a rotation, the old one.
[reveal: v-526]
[pause: 0.45]
C: And it answers two hundred only after storing the event I-D.
[pause: 1.1]

[slide: v-527]
[pause: 1.0]
C: Defence in depth, in layers.
[reveal: v-528]
[pause: 0.45]
C: The egress proxy, with no other route out, stops request forgery.
[reveal: v-529]
[pause: 0.45]
C: The signature with a timestamp stops forgery and old replays.
[reveal: v-530]
[pause: 0.45]
C: The stored event I-D stops a replay inside the five minutes.
[reveal: v-531]
[pause: 0.45]
C: We tell merchants to confirm a high-value approval by fetching the loan before releasing goods. That protects a till that skipped verification.
[reveal: v-532]
[pause: 0.45]
C: And for the partner bank, mutual T-L-S, so nobody else can receive loan-level data at its U-R-L.
[pause: 1.0]

[slide: v-533]
[pause: 0.6]
I: A merchant's signing secret has been pushed to a public code repository. What now?
[pause: 2.0]

[slide: v-534]
[pause: 0.6]
C: Rotate with overlap.
C: The merchant asks for a new secret by A-P-I; for twenty-four hours we sign with both, so their till can deploy without dropping events.
[reveal: v-535]
[pause: 0.45]
C: Then revoke the old one, or at once if they choose.
[reveal: v-536]
[pause: 0.45]
C: Or remove the shared secret entirely: asymmetric signatures, where we publish a public key and there's nothing to leak on their side.
[reveal: v-537]
[pause: 0.45]
C: The honest limit: that's harder for merchants on old stacks, so we offer it and keep H-MAC as the default.
[pause: 0.8]

[slide: v-538]
[pause: 0.7]
V: If asked, I'd say: every call leaves through a proxy that checks the address it actually connects to. Every call is signed over its I-D, timestamp and body, and too old means rejected. And no merchant should ship goods on a webhook alone.
[pause: 1.0]
N: The calls are now safe. The next question is about the people who change what is inside them.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: A producer changes the payload

[slide: v-539]
[pause: 1.2]
N: Challenge six. A contract problem that is really a team problem: who owns what a merchant parses?
[pause: 1.8]

[slide: v-540]
[pause: 0.6]
I: The servicing team renames amount to amount cents, and splits status into two fields. They deploy on Tuesday. What happens on Wednesday?
[pause: 2.0]

[slide: v-541]
[pause: 1.3]
C: The naive answer: announce it in the changelog, and merchants update their parsers.
[reveal: v-542]
[pause: 0.45]
C: The matcher,
[reveal: v-543]
[pause: 0.45]
C: marked red, sends the producer's internal event as it is, so the producer's refactor is everyone's breaking change.
[pause: 1.1]

[slide: v-544]
[pause: 1.0]
C: The trace.
[reveal: v-545]
[pause: 0.45]
C: Tuesday at four, servicing deploys the rename and the split.
[reveal: v-546]
[pause: 0.45]
C: Five minutes later, three thousand integrations read amount as null, and tills show zero-dollar refunds.
[reveal: v-547]
[pause: 0.45]
C: That night, accounting imports fail at twelve hundred merchants, and the partner bank's file breaks.
[reveal: v-548]
[pause: 0.45]
C: By Wednesday morning: four hundred tickets, and two teams who are both right. Servicing owns its events. Integrations owns the merchants. Nobody owns the seam.
[pause: 1.0]

[slide: v-549]
[pause: 1.3]
C: The fix, version six: the contract renderer and its schema registry join the baseline.
C: The internal event and the public contract become two different things.
C: One level down.
[reveal: v-550]
[pause: 0.45]
C: Each endpoint is pinned to a dated version, like two thousand twenty-six, June first.
C: Fan-out's renderer maps the internal event into that version.
C: The registry holds golden examples of every supported public version, and a producer's build fails if any of them stops rendering.
[reveal: v-551]
[pause: 0.45]
C: That's a consumer-driven contract test, run in the producer's own pipeline.
C: Additive fields go into the current version.
C: A rename or a split is a new dated version, and old versions are supported for twelve months.
[reveal: v-552]
[pause: 0.45]
C: The rename on Tuesday now changes one mapping in the renderer, and no merchant notices.
C: What it doesn't cover: a change in meaning with the same field name.
C: That's review, not tooling.
[reveal: v-553]
[pause: 0.45]
C: And it's not the tool under it: freezing one payload forever, which only moves the breakage to the product roadmap.
C: Rejected: Sending the producers' internal events as they are.
C: Every internal refactor becomes a breaking change for twenty thousand merchant integrations.
[pause: 1.1]

[slide: v-554]
[pause: 1.3]
C: On the baseline: the log, fan-out and the delivery store are carried.
[reveal: v-555]
[pause: 0.45]
C: The contract renderer is new, beside fan-out. Every delivery row now holds the public version its endpoint pinned.
[pause: 1.1]

[slide: v-556]
[pause: 1.0]
C: And the seam becomes a team's job.
[reveal: v-557]
[pause: 0.45]
C: The producers own internal events and their meaning. Their contract: the golden examples must still render, and changes are additive by default.
[reveal: v-558]
[pause: 0.45]
C: Merchant integrations owns the public versions, the renderer, the documentation, the S-D-Ks and deprecation. A version is supported for twelve months, and usage is measured per endpoint.
[reveal: v-559]
[pause: 0.45]
C: The webhook platform owns delivery: relay, fan-out, dispatch, egress, health and the attempt log. Its contract is the latency, the isolation and the seventy-two hours, and it never edits a payload.
[reveal: v-560]
[pause: 0.45]
C: That's Conway's law used on purpose. The seam that broke on Wednesday is now one team's whole job.
[pause: 1.0]

[slide: v-561]
[pause: 0.6]
I: A security fix needs a breaking change within thirty days. Twelve months is not an option.
[pause: 2.0]

[slide: v-562]
[pause: 0.6]
C: Usage telemetry turns deprecation into a list.
C: We know that twelve hundred endpoints are on an old version, so it's a list to call, not a guess.
[reveal: v-563]
[pause: 0.45]
C: In the old version, the unsafe field is redacted to null rather than removed, so parsers keep working.
[reveal: v-564]
[pause: 0.45]
C: And each endpoint gets a send-test-event button per version and a migration guide with a diff.
[reveal: v-565]
[pause: 0.45]
C: The honest limit: some won't move in thirty days, and the redacted field is the price they pay instead of an outage.
[pause: 0.8]

[slide: v-566]
[pause: 0.7]
V: If asked, I'd say: the internal event is not the contract. Every endpoint pins a dated version, a renderer maps to it, producers' builds fail if a supported version stops rendering, and one team owns the public contract.
[pause: 1.0]
N: Last challenge: when a merchant says something went wrong, how would you know?
[pause: 1.6]

[pause: 1.4]

## 7.7 Challenge 7: “You never sent it”

[slide: v-567]
[pause: 1.2]
N: Challenge seven, observability. The dashboards are green and a merchant is angry.
[pause: 1.8]

[slide: v-568]
[pause: 0.6]
I: A merchant says we never sent loan funded for loan seventy-seven eighty-one. Our dashboards are green. Who is right?
[pause: 2.0]

[slide: v-569]
[pause: 1.3]
C: The naive answer:
[reveal: v-570]
[pause: 0.45]
C: platform success is ninety-nine point nine percent, so it's on their side.
[reveal: v-571]
[pause: 0.45]
C: The attempt log, marked red, has the answer, and nobody is looking at it.
[pause: 1.1]

[slide: v-572]
[pause: 1.0]
C: The trace.
[reveal: v-573]
[pause: 0.45]
C: On Friday at five, the merchant rotates their own gateway credentials.
[reveal: v-574]
[pause: 0.45]
C: From then on, every delivery to them answers four-oh-one.
[reveal: v-575]
[pause: 0.45]
C: By Monday, eight thousand deliveries are dead or retrying. Platform success reads ninety-seven percent, exactly as on every other day, because six hundred endpoints are always failing.
[reveal: v-576]
[pause: 0.45]
C: Support has no per-delivery view, and it's on your side starts a week of email.
[pause: 1.0]

[slide: v-577]
[pause: 1.3]
C: The fix splits observability in two.
C: For the merchant: every attempt for every delivery in their dashboard, with status, latency and the first bytes of the answer, and an email from endpoint health after an hour of failures.
[reveal: v-578]
[pause: 0.45]
C: The merchant would have seen four-oh-one on Friday evening.
C: For us, only what we own.
C: First-attempt p ninety-nine per tier.
[reveal: v-579]
[pause: 0.45]
C: Success to healthy endpoints, those that succeeded ninety-nine percent of the time over the last day, which is what moves when we break.
C: The age of the oldest pending delivery per tier.
C: And relay and fan-out lag.
[reveal: v-580]
[pause: 0.45]
C: None of these moves when a merchant breaks their own server, and all of them move when we do.
C: Rejected: Alerting on merchants' error rates.
C: Their outages would page us all night; alert on our lag and on success to healthy endpoints.
[pause: 1.1]

[slide: v-581]
[pause: 1.0]
C: Then read them in pairs.
[reveal: v-582]
[pause: 0.45]
C: First-attempt latency up in every tier, with fan-out lag up: it's us, fan-out or the renderer.
[reveal: v-583]
[pause: 0.45]
C: The same latency, with relay lag up: a producer's relay.
[reveal: v-584]
[pause: 0.45]
C: Failures up at one endpoint, everyone else flat: it's them. Tell them, page nobody.
[reveal: v-585]
[pause: 0.45]
C: Success to healthy endpoints down, with egress denials up: the proxy or D-N-S.
[reveal: v-586]
[pause: 0.45]
C: And the oldest pending age up in one tier, with its pool saturated: a cap or a pool size.
[reveal: v-587]
[pause: 0.45]
C: A merchant's outage must never page us, and ours must page us before any merchant notices.
[pause: 1.0]

[slide: v-588]
[pause: 0.6]
I: The merchant now says our signatures don't verify.
[pause: 2.0]

[slide: v-589]
[pause: 0.6]
C: Make the signature debuggable.
C: The attempt log keeps the timestamp, the key I-D and the signature header for every attempt.
[reveal: v-590]
[pause: 0.45]
C: The dashboard has a send-test-event button and a page that recomputes the signature from a pasted body.
[reveal: v-591]
[pause: 0.45]
C: The usual causes are three: their framework re-serialised the jason before verifying, their clock is more than five minutes off, or they still use the old secret after a rotation.
[reveal: v-592]
[pause: 0.45]
C: The honest limit: we never log the secret, so the check runs in their browser or their S-D-K.
[pause: 0.8]

[slide: v-593]
[pause: 0.7]
V: If asked, I'd say: I show the merchant every attempt and tell them when their endpoint fails. I page us only on what we own: first-attempt latency per tier, success to healthy endpoints, the oldest pending delivery, and lag.
[pause: 1.6]

[pause: 1.4]

## 8 Build cost

[slide: v-594]
[pause: 1.2]
N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round, central in a manager round.
C: The platform is six versions, and the order matters more than the size.
[pause: 1.8]

[slide: v-595]
[pause: 1.0]
C: The releases.
[reveal: v-596]
[pause: 0.45]
C: Version two, the outbox library and relay, two engineers for a quarter, built with the producing teams. The log is already there.
[reveal: v-597]
[pause: 0.45]
C: Version three, the core: fan-out, the delivery store, the dispatcher with its caps, the attempt log and the A-P-I. A team of five, two quarters. This is the riskiest work, so it goes first, with a load test of one slow endpoint before anything ships.
[reveal: v-598]
[pause: 0.45]
C: Version four, endpoint health, the same team for a quarter.
[reveal: v-599]
[pause: 0.45]
C: Version five, the egress proxy and signing, one engineer with the security team.
[reveal: v-600]
[pause: 0.45]
C: And version six, the contract, is not a project but a team: merchant integrations, two engineers, for as long as there are merchants.
[pause: 1.0]

[slide: v-601]
[pause: 1.0]
C: The contracts between the teams.
[reveal: v-602]
[pause: 0.45]
C: The outbox row and internal event: producers to the platform. Additive, and the event I-D and loan sequence are always present.
[reveal: v-603]
[pause: 0.45]
C: The public versions: integrations to merchants. Dated, twelve months of support, usage measured per endpoint.
[reveal: v-604]
[pause: 0.45]
C: The delivery objectives: the platform to integrations and merchants. First-attempt latency, isolation, seventy-two hours.
[reveal: v-605]
[pause: 0.45]
C: And the golden examples: integrations to the producers' builds. A producer's build fails if a supported version stops rendering.
[reveal: v-606]
[pause: 0.45]
C: Draw the contracts first, give each team one side, and require both sides for a change.
[pause: 1.0]

[slide: v-607]
[pause: 0.6]
C: Buy against build, as in the alternate path: at a hundred and eighty million a month, a managed delivery engine costs about eighteen thousand dollars a month, a serious option if the partner bank allows it.
C: Build past about eight hundred million, or when the data must stay with us.
[reveal: v-608]
[pause: 0.45]
C: On-call: the platform pages on its own lag and on success to healthy endpoints.
C: Merchants' failures go to them, by email, and never to our pager.
[reveal: v-609]
[pause: 0.45]
C: And the top risks: a producer that bypasses the outbox, a cap tuned too high, the proxy as a single point of failure, which runs in every zone, and a public version that nobody owns.
[pause: 0.8]

[pause: 1.4]

## 9 Recap

[slide: v-610]
[pause: 1.2]
C: The recap: the final design once more, one sentence per path, the common mistakes, and the thesis.
[pause: 1.8]

[slide: v-611]
[pause: 1.3]
C: The final design, along the path of one event.
[reveal: v-612]
[pause: 0.45]
C: One: the producer commits the change and its outbox row.
[reveal: v-613]
[pause: 0.45]
C: Two: the relay publishes it to the log.
[reveal: v-614]
[pause: 0.45]
C: Three: fan-out consumes it,
[reveal: v-615]
[pause: 0.45]
C: four: renders each endpoint's public version,
[reveal: v-616]
[pause: 0.45]
C: five: and writes one delivery row per endpoint.
[reveal: v-617]
[pause: 0.45]
C: Six: the dispatcher claims it under the endpoint's cap.
[reveal: v-618]
[pause: 0.45]
C: Seven: signs it and sends it through the egress proxy,
[reveal: v-619]
[pause: 0.45]
C: eight: to the merchant's checked address.
C: Below them, the attempt log, the A-P-I and endpoint health close the loop.
[pause: 1.1]

[slide: v-620]
[pause: 1.0]
C: Seven paths, one sentence each.
[reveal: v-621]
[pause: 0.45]
C: Emit: the outbox row is in the commit, and the relay publishes at least once.
[reveal: v-622]
[pause: 0.45]
C: Fan out: one event becomes one row per endpoint, rendered to its version.
[reveal: v-623]
[pause: 0.45]
C: Deliver: claimed under a cap, signed, through a proxy that checks the address.
[reveal: v-624]
[pause: 0.45]
C: Recover: full jitter, a breaker and a ramp; dead after seventy-two hours; replay at their rate.
[reveal: v-625]
[pause: 0.45]
C: Trust: I-D, sequence, timestamp and signature, and never ship goods on a webhook alone.
[reveal: v-626]
[pause: 0.45]
C: Evolve: dated versions, a renderer, and producers' builds that fail first.
[reveal: v-627]
[pause: 0.45]
C: Observe: the merchant sees every attempt, and we page only on what we own.
[pause: 1.0]

[slide: v-628]
[pause: 0.6]
N: The mistakes that cost points.
N: In the design: a POST inside the business request, one shared queue and pool, retries in memory, and retry topics used as a queue per endpoint.
[reveal: v-629]
[pause: 0.45]
N: In judgement: promising exactly-once or strict order, trusting a U-R-L string, an A-P-I key instead of a signature, the internal event as the public contract, and paging on merchants' errors.
[pause: 0.8]

[slide: v-630]
[pause: 0.7]
V: We promise at-least-once delivery, and give every endpoint its own failure budget. Exactly-once is the consumer's job, and the contract that makes it possible is the product.
[pause: 1.6]

[slide: v-631]
[pause: 1.0]
N: Questions you should be ready for next. Each points back to where this video answers it.
[reveal: v-632]
[pause: 0.45]
C: An endpoint down for a week: challenge three, and the seventy-two-hour rule.
[reveal: v-633]
[pause: 0.45]
C: A hostile endpoint: challenge five, and the egress proxy.
[reveal: v-634]
[pause: 0.45]
C: A payload change: challenge six, and the consumer contract.
[reveal: v-635]
[pause: 0.45]
C: Buy against build: option F, and the alternate path.
[reveal: v-636]
[pause: 0.45]
C: Proving we sent it: challenge seven, and the attempt log.
[reveal: v-637]
[pause: 0.45]
C: And ten times the volume: option D's write cost, and the shard count.
[pause: 1.0]
