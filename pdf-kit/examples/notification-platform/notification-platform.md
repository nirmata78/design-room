Reference interview · System design · SD-12

# Notification Platform, passed.

Push, email, SMS and in-app for twenty product teams and 500 million users, run stage by stage: what to ask, what to compute, what to draw and what to say, with the theory behind each choice.

21 October 2026 · built on the SD-12 reference design · 45-minute round

**\[Five sentences that pass this round\]**

1.  **This is a governance problem, not a delivery problem.** Sending a push is one API call; the platform's value is stopping twenty teams from spamming, duplicating, waking up or overcharging 500 million users.
2.  **Twelve thousand a second is ordinary.** The numbers that shape the design are the 10× campaign peak, which we cause ourselves and therefore shape, and the SMS bill.
3.  **Intent is made durable first, in a Kafka topic per priority**; policy runs after, as ordered gates: kill switch, dedup, consent, per-user rate, quiet hours, routing.
4.  **Priorities are isolated at every layer**, from topics to consumer pools, worker lanes and reserved provider capacity, so a password reset never waits behind a 400 M campaign.
5.  **Fall back only on a definite failure, and be honest about recall:** a sent push, email or SMS can't be taken back, so prevent with canaries and halt within seconds.

![clock diagram](svg/clock.svg)

**The round on a 45-minute clock.** Requirements, numbers and API take a third. The design and the deep dives the interviewer chooses take half.

## How to use this

Each section is one stage of the round, in the order you'll run it. **Green boxes** are lines to say in the room, **purple** are the follow-ups the interviewer asks at that point, **blue** is theory, **amber** a trap, **red** a must-know. Why this design matters beyond itself: in any consumer design round, "now notify the user when…" is the requirement most likely to be added mid-round. Knowing it lets you answer in two minutes inside another question.

## Contents

- **1**Requirements stage 1
- **2**Back-of-the-envelope cost and peak
- **3**API idempotent intake, campaigns, halt
- **4**Data model and stores Kafka, Redis, Cassandra
- **5**High-level design context, containers, lifecycle
- **6**The governance gates deep dive
- **7**Priority isolation deep dive
- **8**Campaigns and the kill switch deep dive
- **9**Delivery, fallback, providers deep dive
- **10**Requirements added mid-round
- **11**Failure modes, SLOs, operations
- **12**The EM layer and the close
- **13**Rapid-fire follow-ups and self-check
- **14**One-page cheat sheet

# 1Requirements *(STAGE 1 · MIN 0–5)*

**The prompt:** *"Design the platform that sends notifications to users across push, email and SMS, used by every product team in the company."* Ask six questions; each one changes a box on the whiteboard.

| I ask                 | Interviewer answers                                                               | Why it changes the design                                         |
|-----------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------|
| Volume and peak?      | 500 M users, 1 B notifications/day, 10× peak during campaigns                     | Queue sizing. The peak is self-inflicted, so it can be **shaped** |
| Channels?             | Mobile push, email, SMS, in-app; third-party providers with their own rate limits | One adapter per provider; provider limits are a hard ceiling      |
| Latency classes?      | Transactional in seconds, marketing in minutes                                    | Priority isolation: a campaign must never delay a password reset  |
| Duplicates?           | A user must never get the same notification twice                                 | Dedup key and window; careful fallback logic                      |
| Who calls it?         | ~20 product teams                                                                 | Multi-tenancy: quotas, templates, ownership, on-call boundaries   |
| Legal? (you raise it) | Opt-out must be honoured; email and SMS consent rules vary by country             | Consent is a **blocking gate**, not a filter we "try"             |

### In scope

Intake API, campaigns, policy (consent, dedup, rate, quiet hours), routing and fallback, delivery, in-app inbox, status tracking, kill switch.

### Out of scope (say it)

Content-authoring UI, segmentation and ML targeting, A/B testing of copy, the email and SMS providers themselves.

### Priority classes

| Class                | Examples                                | Target             |
|----------------------|-----------------------------------------|--------------------|
| **P0** critical      | OTP, password reset, fraud alert        | p99 \< 5 s, always |
| **P1** transactional | order shipped, driver arriving, mention | p99 \< 60 s        |
| **P2** bulk          | marketing, digests, re-engagement       | minutes to hours   |

### Non-functional requirements

| Requirement          | Target                                 |
|----------------------|----------------------------------------|
| P0 accept → provider | **p99 \< 5 s**, even during a campaign |
| Duplicates           | none within the window (\< 1 in 10⁶)   |
| Consent              | **zero** sends without it, audited     |
| Campaign halt        | effective within seconds (p99 \< 5 s)  |
| Stale messages       | never sent after `expiresAt`           |
| Intake               | 202 means durably queued               |

**\[The insight to land by minute 10\]**

Sending a push is one API call. The platform's value is everything that stops twenty teams from spamming, duplicating, waking up or overcharging 500 million users: consent, dedup, per-user rate limits, quiet hours, priority isolation and a kill switch. A design that's only a delivery pipeline has missed the question.

**\[Say it\]**

"Before boxes: this is a platform and governance problem. Twenty teams share 500 million users' attention, so the platform has to enforce consent, dedup, rate limits and quiet hours centrally, and a campaign must never delay a password reset."

# 2Back-of-the-envelope *(STAGE 2 · MIN 5–10)*

| Quantity              | Arithmetic                                 | Result                               | Consequence                                                                       |
|-----------------------|--------------------------------------------|--------------------------------------|-----------------------------------------------------------------------------------|
| Average rate          | 1,000,000,000 ÷ 86,400                     | **~12k/s** (11,574)                  | Ordinary: Kafka handles it on a handful of brokers                                |
| Peak                  | × 10 during campaigns                      | **~120k/s**                          | The peak is campaigns, so **throttle the release** instead of provisioning for it |
| Channel mix (assumed) | push 70% · in-app 15% · email 13% · SMS 2% | 700 M · 150 M · 130 M · 20 M per day | —                                                                                 |
| SMS cost              | 20 M × ~\$0.01 (varies by country)         | **~\$200k/day, ~\$73 M/year**        | The dominant cost at 2% of volume → push first, SMS only where required           |
| Email cost            | 130 M × \$0.10 per 1,000                   | ~\$13k/day                           | Secondary; reputation (bounces, complaints) matters more than price               |
| A 400 M campaign      | 400,000,000 ÷ 50,000/s                     | 8,000 s ≈ **2.2 hours**              | Fine for marketing; leaves headroom for P0 and P1                                 |
| Dedup store           | 1 B keys/day × ~100 B, 24 h TTL            | **~100 GB** RAM                      | Redis cluster for 24 h; disk KV with TTL for longer windows                       |
| Preferences           | 500 M × ~500 B                             | ~250 GB; ~120k reads/s at peak       | KV store + local cache in policy workers                                          |
| Delivery log          | 1 B × ~3 status events × ~200 B            | ~0.6 TB/day, **~55 TB** at 90 days   | Wide-column or columnar store, not the OLTP database                              |

![cost diagram](svg/cost.svg)

**Where the money goes.** SMS is 2% of the messages and about 94% of the provider bill. That's why routing prefers push and in-app, and why every tenant should see its own SMS cost.

**\[Little's law: L = λ · W\]**

Items in a system = arrival rate × time each spends there. Three uses here:

- **Provider calls in flight:** 120k/s × ~100 ms per call ≈ **12,000 concurrent requests**. So workers need async, multiplexed HTTP/2 clients (APNs is HTTP/2), not a thread per call.
- **Campaign drain:** W = L / λ = 400 M ÷ 50k/s ≈ 2.2 h, the time the backlog sits in Kafka.
- **Policy workers:** at ~2k messages/s each (a few pipelined Redis calls), peak needs ~60 workers, so P2 needs ≥ 64 partitions.

**\[Shape the peak, don't buy it\]**

A 10× peak you *cause* is a scheduling decision. Provisioning every layer, every provider contract and every SMS quota for 120k/s would be idle 23 hours a day. Releasing campaigns at a capped rate turns the spike into a 2-hour plateau that fits next to P0 and P1.

**Kafka at peak:** 120k/s × ~1 KB ≈ 120 MB/s in, ×3 replicas ≈ 360 MB/s of disk writes across the cluster: a handful of brokers.

**\[Say it\]**

"Throughput isn't the hard part: twelve thousand a second is ordinary. The two numbers that shape the design are the SMS bill, about seventy million a year at two percent of volume, and the 10× peak, which we create ourselves with campaigns, so I'll shape it rather than buy capacity for it."

# 3API *(STAGE 3 · MIN 10–15)*

| Endpoint                          | Returns         | Purpose and notes                                                                           |
|-----------------------------------|-----------------|---------------------------------------------------------------------------------------------|
| POST /v1/notifications            | 202 · 200 · 429 | Send intent from a tenant service (mTLS). Same `dedupKey` again → 200 with the original id. |
| POST /v1/campaigns                | 201             | `{segmentId, template, schedule, ratePerSec}` → campaignId.                                 |
| POST /v1/campaigns/{id}/halt      | 202             | The kill switch; effective within seconds.                                                  |
| GET /v1/notifications/{id}        | 200             | Status per channel, with suppression reasons.                                               |
| GET /v1/users/{id}/inbox?cursor=… | 200             | The in-app feed, newest first.                                                              |
| PUT /v1/users/{id}/preferences    | 200             | Category × channel opt-ins, quiet hours, time zone.                                         |

    // a tenant sends one intent
    POST /v1/notifications
    { "tenant": "auth",
      "userId": "9",            // or userIds[] ≤ 1k
      "category": "security",   // security | order |
                                // social | marketing
      "template": "reset_pw", "version": 7,
      "params": { "link": "…" },
      "priority": "P0",
      "dedupKey": "reset:9:req123",
      "channels": ["push", "email"],   // optional
      "expiresAt": "2026-10-21T19:15:00Z" }

    HTTP/1.1 202 Accepted
    { "notificationId": "n_8f3c…" }

**\[What 202 promises, exactly\]**

**"Durably queued, nothing more."** Intake returns 202 after Kafka acknowledged the write with `acks=all` and `min.insync.replicas=2`, so the intent survives a broker loss. Delivery happens later, so 200 would be a lie and a synchronous call to the provider would couple every tenant to the slowest provider.

**\[Idempotency vs dedup: two different jobs\]**

**Idempotency** protects against the *same request* arriving twice (a tenant retry after a timeout): same `dedupKey` → same `notificationId`. **Dedup** protects the *user* from two different requests that mean the same thing (a retry loop, two services reacting to one event). Making `dedupKey` mandatory turns both into a contract instead of a hope.

**\[Interviewer probes\]**

**Why does the tenant send category and priority?** Because policy depends on them, and they're validated against the tenant's allowed set: no team gets to declare its marketing P0.

**Why `expiresAt`?** So "your driver is here" is never delivered an hour late after an outage.

# 4Data model and stores *(STAGE 3 · MIN 10–15)*

| Store                                 | Key                                         | Content and why this store                                                                           |
|---------------------------------------|---------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Intent** · Kafka topic per priority | partition by userId                         | The durable request: survives worker crashes, gives per-user ordering, replayable after a bad deploy |
| **Preferences** · KV + cache          | userId                                      | Opt-in matrix (category × channel), time zone, quiet hours, locale, device tokens                    |
| **Dedup / rate** · Redis, TTL         | (userId, dedupKey); (userId, category, day) | Seen markers; counters. Sub-millisecond on the hottest path                                          |
| **Templates**                         | (tenant, template, version)                 | Localized bodies per channel; a version is immutable once used                                       |
| **Delivery log**                      | (notificationId, channel)                   | ACCEPTED … DELIVERED / FAILED / SUPPRESSED + reason; ~1 B rows/day                                   |
| **Inbox** · Cassandra                 | (userId, month)                             | In-app items and read state; the only channel where "unsend" works                                   |
| **Control plane**                     | tenant, campaignId                          | Quotas, kill flags, provider config                                                                  |

**\[Kafka in five facts\]**

- A **topic** is split into **partitions**; order is guaranteed only within one. Keying by userId keeps one user's notifications in order.
- Each **consumer group** reads every partition once, with its own offsets; partitions cap the group's parallelism.
- **Consumer lag** (latest offset − committed offset) is the backlog; for P0 it's the health signal.
- Delivery to consumers is **at-least-once**: after a crash, messages since the last commit are re-read, so everything downstream must be idempotent.
- Retention makes it **replayable**: fix a policy bug, rewind the offsets, re-run.

    -- in-app inbox, Cassandra
    CREATE TABLE inbox (
      user_id  text,
      month    text,          -- '2026-10'
      ts       timeuuid,
      notif_id text,
      title    text,  body text,
      read     boolean,
      PRIMARY KEY ((user_id, month), ts)
    ) WITH CLUSTERING ORDER BY (ts DESC)
      AND default_time_to_live = 7776000;  -- 90 d

**\[Why Cassandra for inbox and log\]**

Write-heavy, time-ordered per user, expiring by age: exactly its shape. The month in the partition key keeps partitions bounded; TTL does retention. The catch: deletes write **tombstones**, so "delete from every inbox" is expensive and should be rare.

# 5High-level design *(STAGE 4 · MIN 15–25)*

![context diagram](svg/context.svg)

**System context.** Twenty tenants on one side, three paid providers on the other. The platform is the governance layer in between.

![containers diagram](svg/containers.svg)

**Containers.** Intent is made durable and prioritized before any policy runs; delivery is per channel behind provider adapters; feedback closes the loop.

### One notification, end to end

1.  **Intake** authenticates the tenant, checks its quota, validates template, category and priority, and writes the intent to the topic for its priority. 202.
2.  **Campaigns** don't call intake per user: the campaign service expands the segment in batches and releases into P2 at a configured rate.
3.  **Policy & router** consumes and runs the gates in order: kill switch → dedup → consent → per-user rate → quiet hours → channel choice (§6).
4.  **Channel workers** render the template (locale, version) and call the provider through an adapter: rate limit, retries with jitter, circuit breaker.
5.  **Feedback ingest** takes provider webhooks (receipts, bounces, invalid tokens), updates the delivery log and the token registry; in-app items land in the inbox.

| Choice                        | Rejected, and why                                                                      |
|-------------------------------|----------------------------------------------------------------------------------------|
| Kafka, one topic per priority | One queue with a priority field: head-of-line blocking behind 400 M marketing messages |
| Redis for dedup and rate      | Database unique constraint: correct, but a write on the hottest path at 120k/s         |
| Cassandra for inbox and log   | PostgreSQL: fine per row, painful at ~1 B rows a day                                   |
| Stateless policy workers      | Rules embedded in each tenant service: the twenty-teams problem again                  |
| Async 202 at intake           | Synchronous provider call from the API: tenants inherit provider latency and outages   |

![lifecycle diagram](svg/lifecycle.svg)

**The life of one notification.** SUPPRESSED is a first-class outcome: most of the platform's value is what it decides not to send. Every state change lands in the delivery log with a reason.

**\[Say it\]**

"Three layers: a durable, prioritized intent log; a stateless policy layer that decides whether a notification may exist and where it goes; and per-channel delivery behind provider adapters. Tenants only ever talk to the first layer."

# 6Deep dive: the governance gates *(STAGE 5 · MIN 25–38)*

![gates diagram](svg/gates.svg)

**Policy & router as ordered gates.** Cheapest and most absolute checks first. The router only sees notifications that are allowed to exist.

| Gate          | Check                                                                                                | Data                     | Why in this position                                                        |
|---------------|------------------------------------------------------------------------------------------------------|--------------------------|-----------------------------------------------------------------------------|
| ① Kill switch | Campaign or tenant halted?                                                                           | local flag, pushed ≤ 1 s | Cheap, absolute, must win over everything                                   |
| ② Dedup       | `(user, dedupKey)` seen in the window (24 h transactional; campaign lifetime for marketing)?         | Redis `SET NX EX`        | Stops a tenant retry loop here, and alerts the tenant on its duplicate rate |
| ③ Consent     | Category × channel opt-in, plus country law. Security always allowed; marketing never without opt-in | preferences (cached)     | A blocking legal gate; unsubscribes apply immediately                       |
| ④ Rate limit  | Token bucket per (user, category): e.g. ≤ 3 marketing/day, ≤ 20 social/day; P0 exempt                | Redis counters           | The platform's real product: it protects users from the company             |
| ⑤ Quiet hours | Inside the user's quiet window, in their time zone?                                                  | preferences              | Defer P1/P2 to a delayed queue; P0 is never deferred                        |
| ⑥ Route       | Channel(s) by category, preference, device presence and cost                                         | token registry           | SMS only for OTP/security or where the user chose it                        |

**\[Dedup that lets retries through\]**

Naive `SET NX` blocks our *own* retry after a worker crash. Store the notificationId as the value: a different id is a duplicate, the same id is a retry.

    -- Redis 7+: set if absent, return the old value
    SET dd:{u9}:reset:9:req123 n_8f3c NX GET EX 86400
    --  nil    → first time: proceed
    --  n_8f3c → my own retry: proceed
    --  other  → duplicate: SUPPRESSED

The `{u9}` hash tag keeps a user's dedup and rate keys on one Redis node, so one script can touch both.

**\[Token bucket, the formula\]**

A bucket holds up to **B** tokens and refills at **r** per second. On each request:

    tokens = min(B, tokens + (now − last) · r)
    allow  = tokens ≥ 1;  if allow: tokens −= 1

"3 marketing a day" is B = 3, r = 3 / 86,400 s. Bursts up to B are allowed, the long-run rate is r. Keep `{tokens, last}` in a Redis hash, updated by one Lua script.

**\[Quiet hours need a delayed queue\]**

A deferred item needs a wake-up time: a Redis sorted set scored by due time (`ZRANGE … BYSCORE`, claim with `ZREM`), or a scheduler table. On wake-up it goes back through the gates, because consent or the kill switch may have changed while it slept.

**\[Interviewer probes\]**

**Why dedup before consent?** Both are cheap, but dedup is per message and stops tenant bugs early, and its rate is a signal we report back to the tenant. Consent then gates what remains. The kill switch beats both because it's free and absolute.

**The preference store is down. Do you send?** Fail closed for marketing (no consent proof, no send); P0 security proceeds because it's always allowed.

# 7Deep dive: priority isolation *(THE PROBE THAT SEPARATES)*

**The question:** *"A user requests a password reset while a 400 M-message campaign is going out. What happens?"*

![isolation diagram](svg/isolation.svg)

**Isolation at every layer, not a priority field.** Separate topics, consumer groups, worker lanes and reserved provider capacity.

![p0seq diagram](svg/p0seq.svg)

**The P0 path during a campaign.** The campaign's backlog is invisible to it: P0 has its own topic, consumer pool and worker lane.

**\[Head-of-line blocking\]**

In one FIFO queue, a message waits for everything ahead of it. A "priority field" inside that queue changes nothing for consumers reading in order, and Kafka has no per-message priority. Separate topics give each class its own line. The campaign is also rate-released, so it never floods even its own lane.

**\[Reserved provider capacity\]**

The last shared resource is the provider's rate limit. Reserve a slice (e.g. 20% of push and SMS quota) for P0, keep a second SMS aggregator for P0 failover, and alert on **P0 consumer lag \> 2 s**: that's the SLO that matters most.

**\[Say it\]**

"Isolation is structural: its own topic, its own consumers, its own worker lane and reserved provider capacity. The campaign is invisible to the reset, and I alert on P0 lag above two seconds."

# 8Deep dive: campaigns and the kill switch *(DEEP DIVE)*

**The question:** *"The campaign has a typo and 80 million have already gone."*

![halt diagram](svg/halt.svg)

**Prevention first, then a fast halt.** Canary every campaign to 0.1% and a seed list, hold, release by time-zone bucket at a capped rate. Halting stops everything not yet handed to a provider.

| Channel | Recall after sending? | What you can do                                                                                                |
|---------|-----------------------|----------------------------------------------------------------------------------------------------------------|
| Push    | No, once displayed    | If not yet displayed, a message with the same collapse id (`apns-collapse-id`, FCM `collapse_key`) replaces it |
| Email   | No                    | Nothing; a correction email is a business decision, because it doubles the noise                               |
| SMS     | No                    | Nothing; and it cost money                                                                                     |
| In-app  | **Yes**               | Delete from inboxes (Cassandra tombstones; batch it)                                                           |

**\[Fan-out mechanics\]**

The campaign service expands the segment with Spark in batches of ~10k user ids, buckets them by time zone for "local 9 a.m." sends, and releases each bucket into P2 at `ratePerSec`. Each item still passes every gate, so consent, caps and quiet hours apply to campaigns too.

**\[Interviewer probes\]**

**How fast is the halt?** Flag set → pushed to policy workers within ~1 s; channel workers re-check just before the provider call. SLO: effective p99 \< 5 s.

**Who can press it?** The tenant that owns the campaign, without paging the platform team.

# 9Deep dive: delivery, fallback and providers *(DEEP DIVE)*

**The question:** *"Push fails, you fall back to email, and the push actually arrived."*

![fallback diagram](svg/fallback.svg)

**Fallback causes duplicates when "failure" is ambiguous.** Push receipts are weak, so "no receipt yet" is not a failure. Every fallback carries the same dedupKey, and the inbox shows one item.

![retry diagram](svg/retry.svg)

**Every provider adapter:** a token bucket matching the contract limit, retries with exponential backoff and full jitter on 5xx and timeouts, and a circuit breaker.

**\[Why full jitter\]**

Plain exponential backoff keeps clients synchronized: after an outage they all retry at 0.2 s, 0.4 s, 0.8 s… and hit the recovering provider in waves. A random wait in \[0, base·2ⁿ\] spreads them evenly. Retries are safe because the provider call carries an idempotency key or collapse id.

**\[Push tokens\]**

A device token identifies one app install. APNs answers **410 Unregistered** (or 400 BadDeviceToken), FCM **UNREGISTERED**, when it's dead: remove it from the registry so we stop paying to fail. A user typically has 1–3 tokens; send to each active one.

**\[Email deliverability is its own discipline\]**

- Authenticate: **SPF, DKIM, DMARC**; separate sending domains or IPs for transactional and marketing, so a campaign's reputation can't sink password resets.
- Since 2024, Gmail and Yahoo require bulk senders to keep spam complaints **under 0.3%** (aim for 0.1%) and support **one-click unsubscribe** (RFC 8058).
- Hard bounce → suppress the address for good; soft bounce → retry, then suppress.

**\[SMS realities\]**

Price varies by country by an order of magnitude; carriers require **STOP** handling and sender registration (e.g. US 10DLC); keep two aggregators for failover. Route OTP to push or in-app when the app is installed and active.

**\[Provider outage, and stale messages\]**

When a breaker opens, P2 simply waits in Kafka (it's durable) and P0 switches to the secondary provider. But when the backlog drains, check `expiresAt`: a "your driver is here" an hour late is worse than none.

# 10Requirements added mid-round *(ANY TIME)*

| New requirement                                | Change                                                                                                            | What stays untouched                         |
|------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| "Batch social notifications into one per hour" | An aggregation stage before routing: buffer per (user, category) in a keyed window, then emit one rendered digest | Gates, workers, providers                    |
| "Send at the user's local 9 a.m."              | Campaign scheduler buckets recipients by time zone and releases per bucket                                        | Policy (quiet hours already uses time zones) |
| "WhatsApp as a new channel"                    | One new adapter and worker; template variants per channel                                                         | Intake API, policy, the tenant contract      |
| "Tenants want delivery and open analytics"     | Delivery log → columnar store (ClickHouse/BigQuery) → per-tenant dashboards                                       | Hot path                                     |
| "Regulator: prove we honoured an opt-out"      | Immutable audit of preference changes + suppression reason per notification                                       | Already logged as SUPPRESSED (no consent)    |

**\[Say it\]**

"That's a new stage or a new adapter; the intake contract and the gates don't change. That's the point of separating intent, policy and delivery."

# 11Failure modes, SLOs and operations *(MIN 38–44)*

| Failure                          | Blast radius                         | Mitigation                                                                      |
|----------------------------------|--------------------------------------|---------------------------------------------------------------------------------|
| Redis dedup node failover        | Possible duplicates for ~1 s of keys | Stated, bounded risk; push collapse ids; second-level dedup in the inbox        |
| Preference store down            | Can't verify consent                 | Fail closed for marketing; P0 security proceeds (always allowed)                |
| A tenant floods the API          | Its own quota                        | Per-tenant quotas at intake, 429 on overflow; other tenants unaffected          |
| Bad template version             | Every message using it               | Versions immutable and pinned; canary send; rollback = pin the previous version |
| Provider outage                  | One channel                          | Breaker + secondary provider for P0; P1/P2 buffered in Kafka with `expiresAt`   |
| Policy bug suppresses everything | All notifications                    | Alert on suppression-rate anomaly per category; fix, then **replay from Kafka** |

### SLOs

|                         |               |
|-------------------------|---------------|
| P0 accept → provider    | p99 \< 5 s    |
| P1 accept → provider    | p99 \< 60 s   |
| Duplicate rate          | \< 1 in 10⁶   |
| Sends without consent   | zero, audited |
| Campaign halt effective | p99 \< 5 s    |

**\[Operations\]**

**Per-tenant dashboards:** volume vs quota, suppression reasons, delivery and open rates, cost. Show each team its own SMS bill; that changes behaviour faster than any policy. **On-call boundary:** the platform team owns pipeline, providers and gates; tenants own content and volume. Runbooks for provider failover and campaign halt.

# 12The EM layer and the close *(MIN 44–45)*

| Topic           | What to say                                                                                                                                                                      |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MVP             | Intake + Kafka + push and email workers + dedup + consent + P0/P2 isolation + kill switch                                                                                        |
| Then            | Quiet hours, per-user rate limits, campaign service, SMS with two providers, digests, analytics                                                                                  |
| Tenant contract | Required dedupKey; category and priority validated against the tenant's allowed set; quotas per channel; template review for marketing; deprecation policy for template versions |
| Team split      | Platform core (intake, queues, policy) · Channels (adapters, providers, deliverability) · Campaigns & tooling · Developer-experience owner for the twenty tenants                |
| Cost governance | SMS budget per tenant with alerts; route OTP to push or in-app where the app is active                                                                                           |

**\[The close, nearly verbatim\]**

"What I built: a durable, prioritized intent pipeline with a policy layer (consent, dedup, per-user rate limits, quiet hours) in front of per-channel delivery with provider adapters. Key trade-off: I isolate priorities structurally and shape campaign peaks instead of provisioning for them. Biggest risk: a bad campaign or a duplicate storm, contained by the kill switch, canary sends and dedup, with an honest limit: sent messages can't be recalled. Next: digests and per-tenant cost dashboards, because SMS is the bill."

# 13Rapid-fire follow-ups and self-check *(DRILL)*

Exactly-once delivery?

Not end to end: providers and networks don't offer it. At-least-once from Kafka plus idempotent dedup gives "effectively once" for the user, with a stated ~1 s risk on Redis failover.

Why partition by userId?

Per-user ordering (a "shipped" never overtakes "ordered"), and one user's dedup and rate checks stay on one worker at a time.

A celebrity posts; 50 M followers get a social notification.

It's a campaign in disguise: route it through the campaign path, rate-released in P2, with per-user social caps applying.

How do online users get in-app items instantly?

Write to the inbox, then push a small event over the user's WebSocket/SSE connection if one is open; otherwise they see it on next open.

How do you test a template change?

New immutable version, render tests per locale and channel, canary to the seed list, then pin. Rollback is pinning the old version.

Why not let each team call providers directly?

Twenty teams means twenty dedup bugs, no global caps, no shared consent and twenty SMS bills nobody sees. Governance needs one choke point.

What's your most important alert?

P0 consumer lag above 2 seconds. Then suppression-rate anomalies, because a policy bug fails silently.

How long do you keep the dedup window?

24 hours for transactional (~100 GB in Redis); the campaign's lifetime for marketing, in a disk-based KV with TTL if it's longer.

Multi-region?

Intake and policy per region; preferences replicated; a user's notifications processed in their home region so dedup and rate counters stay local.

How do you cut the SMS bill?

Push or in-app first for OTP when the app is active, per-tenant SMS budgets and dashboards, and cheaper routes per country.

| Signal         | Weak                     | Strong                   | Exceptional (aim here)                                                         |
|----------------|--------------------------|--------------------------|--------------------------------------------------------------------------------|
| Framing        | "Call the push provider" | Intent vs delivery split | Governance is the product; twenty tenants named                                |
| Estimation     | Average QPS only         | Peak and storage         | SMS cost as the dominant line; peak shaped, not bought                         |
| Priorities     | Priority field           | Separate queues          | Isolation at every layer + reserved provider capacity                          |
| Dedup          | None                     | Dedup key                | Window stated; required by contract; tenant retry loop stopped by the platform |
| Consent / rate | Afterthought             | Gates exist              | Ordered gates; fail closed for marketing; P0 exemptions                        |
| Fallback       | Always fall back         | Fallback exists          | Only on definite failure; same dedup key                                       |
| Kill switch    | None                     | Halt API                 | Propagation time, canary sends, honest "can't recall"                          |
| EM layer       | None                     | SLOs                     | Tenant contract, on-call boundary, per-tenant cost visibility                  |

**\[Common traps\]**

Synchronous calls to providers from the API · one queue for all priorities · fallback on "no receipt" · trusting tenants to dedup · ignoring time zones · forgetting `expiresAt`, so stale notifications go out after an outage.

# 14One-page cheat sheet

### Numbers (1 B/day, 500 M users)

|                          |                                          |
|--------------------------|------------------------------------------|
| Average                  | ~12k/s                                   |
| Campaign peak            | ~120k/s (10×)                            |
| Mix                      | push 70 · in-app 15 · email 13 · SMS 2 % |
| SMS                      | 20 M × \$0.01 ≈ \$200k/day               |
| SMS per year             | ~\$73 M, ~94% of the bill                |
| Email                    | ~\$13k/day                               |
| 400 M campaign           | at 50k/s ≈ 2.2 h                         |
| Dedup (24 h)             | ~100 GB Redis                            |
| Preferences              | ~250 GB, 120k reads/s                    |
| Delivery log             | 0.6 TB/day, 55 TB / 90 d                 |
| Provider calls in flight | 120k/s × 0.1 s = 12k                     |

### SLOs

|            |             |
|------------|-------------|
| P0         | p99 \< 5 s  |
| P1         | p99 \< 60 s |
| Duplicates | \< 1 in 10⁶ |
| Halt       | p99 \< 5 s  |
| No consent | zero sends  |

### The gates, in order

|     |                                        |
|-----|----------------------------------------|
| 1   | Kill switch: cached flag, ≤ 1 s        |
| 2   | Dedup: SET NX GET EX, own retries pass |
| 3   | Consent: category × channel + law      |
| 4   | Rate: token bucket, P0 exempt          |
| 5   | Quiet hours: defer P1/P2, never P0     |
| 6   | Route: cheapest valid channel          |

### Isolation, layer by layer

|           |                                     |
|-----------|-------------------------------------|
| Topic     | notif.p0 / p1 / p2                  |
| Consumers | own group per priority              |
| Workers   | own lane per priority               |
| Providers | 20% reserved for P0, 2nd SMS vendor |
| Alert     | P0 lag \> 2 s                       |

### API

|                     |                        |
|---------------------|------------------------|
| POST /notifications | 202, dedupKey required |
| POST /campaigns     | ratePerSec             |
| POST …/{id}/halt    | kill switch            |
| GET …/inbox         | in-app feed            |

### Rules to say out loud

|            |                                    |
|------------|------------------------------------|
| 202        | = durably queued, nothing more     |
| Fallback   | only on definite failure, same key |
| Recall     | impossible except in-app           |
| Campaigns  | canary 0.1% → hold → rate-release  |
| Stale      | drop after expiresAt               |
| Prefs down | closed for marketing, P0 goes      |
| Policy bug | fix, replay from Kafka             |

### Provider adapter

|         |                                 |
|---------|---------------------------------|
| Rate    | token bucket = contract limit   |
| Retry   | backoff + full jitter, 5xx only |
| Breaker | closed → open → half-open       |
| Tokens  | 410 / UNREGISTERED → delete     |

### The one-liner

*"Make intent durable and prioritized, decide centrally whether each message may exist, deliver per channel behind adapters, and shape the peaks we create ourselves."*
