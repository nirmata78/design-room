# Notification platform mock round (video)

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png.
     Speakers: I interviewer · C candidate · V candidate, key line (slower) · N coach. [pause: s] = silence.
     Content follows ../notification-platform.md (SD-12 reference interview). Level: em (L6 / M1), per levels.md.
     v2 2026-10-28: 51 lighter slides, C4 and sequence diagrams, slower voices, key lines on V. Target ~29 min. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->

## Before you start

[slide: v-01]
N: This is a mock system design round, for an engineering manager loop at level six. The prompt is a notification platform. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. After the design, there are four manager follow-ups. Listen once, straight through. On the second pass, pause after every question, and answer it yourself first.

[slide: v-02]
N: Know what's being weighed. At this level, operations and cost count most. Then leadership. You still need depth, but only once: one component, two levels down. And expect the manager's curveball. An incident, or a cost spike.

## Requirements

[slide: v-03]
I: Let's start. Design the platform that sends notifications to users, across push, email and S-M-S. Every product team in the company will use it.

C: Before I draw anything, a few questions. Each one will change a box.

[slide: v-04]
C: First, scale. How many users, how much volume, and what does the peak look like?

I: Five hundred million users. About a billion notifications a day. During marketing campaigns, the peak is ten times that.

C: And who calls this platform?

I: About twenty product teams.

C: Then here's what I take from that. The peak comes from campaigns. We cause it ourselves. So we can shape it, instead of buying capacity for it.

[slide: v-05]
C: Latency. I'd guess a password reset and a marketing email aren't held to the same bar.

I: Correct. Transactional in seconds. Marketing within minutes.

C: Then three priority classes. P-zero is critical: one-time codes, password resets, fraud alerts. Under five seconds, always. P-one is transactional: order shipped, driver arriving. Under a minute. P-two is bulk: marketing and digests. Minutes to hours. And one rule above all: a campaign must never delay a password reset.

[slide: v-06]
C: One more question, and I'll raise it myself. Legal. Opt-out has to be honoured, and consent rules vary by country. So consent is a gate. Not a filter we try our best with. Out of scope, I'll say aloud: the authoring tool, targeting, copy testing, and the providers themselves.

I: Okay.

N: Notice the shape. Every answer got one sentence on what it changes. And raising legal, unprompted, is a seniority signal.

## The thesis

[slide: v-07]
C: Before boxes, one framing point.

V: This is a governance problem. Not a delivery problem.

[pause: 1.0]

C: Sending a push is one A-P-I call. The value of this platform is everything that stops twenty teams from spamming, duplicating, waking up, or overcharging, five hundred million users.

I: Why should a platform team own that? Why not each product team?

C: Because the user's attention is shared. Each team, on its own, is reasonable. Twenty reasonable teams together send one user forty notifications a day. Somebody has to own the commons.

[slide: v-08]
C: So, five targets. P-zero, from acceptance to the provider, under five seconds, even during a campaign. Duplicates, under one in a million. Zero sends without consent. A campaign halt, within five seconds. And nothing sent after its expiry time.

## Back of the envelope

[slide: v-09]
C: Quick numbers. A billion a day is about twelve thousand a second. That's ordinary. A handful of Kafka brokers handle it. The peak is ten times that, a hundred and twenty thousand a second. But again: the peak is campaigns. If I release a four-hundred-million campaign at fifty thousand a second, it drains in about two hours. Fine for marketing. And it leaves room for P-zero.

V: Shape the peak. Don't buy it.

[pause: 0.8]

[slide: v-10]
C: The number that matters more is money. Assume two percent of volume is S-M-S. Twenty million messages a day, at about a cent each. That's two hundred thousand dollars a day. Roughly seventy-three million a year. Two percent of the messages. About ninety-four percent of the bill. So routing prefers push and in-app. And every tenant should see its own S-M-S cost.

[slide: v-11]
C: Three more numbers, each with a consequence. Dedup keys for a day: about a hundred gigabytes, so a Redis cluster. The delivery log: about fifty-five terabytes over ninety days, so a wide-column store. And about twelve thousand provider calls in flight at peak, so the workers use async clients.

I: Mm-hm. Go on.

N: Every number came with its consequence. That's the estimation an engineering manager panel remembers.

## The A-P-I

[slide: v-12]
C: One intake endpoint. Tenants call it over mutual T-L-S. The request carries the tenant, the user, a category, a template and its version, the priority, a dedup key, and an expiry time. The answer is a two-oh-two. And a two-oh-two means durably queued. Nothing more. Kafka has acknowledged it, with acks set to all. Around it, the campaign endpoints, including halt. And the inbox.

[slide: v-13]
I: You've got a dedup key in there. Isn't that just idempotency?

C: They're two different jobs. Idempotency protects the request. The same request, twice, after a timeout, gets the same id back. Dedup protects the user. Two different requests that mean the same thing. The second one is suppressed. Making the dedup key mandatory turns both into a contract, instead of a hope.

## Data model

[slide: v-14]
C: Each store is there for a reason. Kafka, one topic per priority, keyed by user: durable, ordered per user, and replayable. Redis for dedup and rate counters, the hottest path. A key-value store with a cache for preferences. Cassandra for the inbox and the delivery log. And a control plane for quotas and kill flags. One Kafka fact drives a lot of the design. It's at-least-once. So everything downstream must be idempotent.

## High-level design

[slide: v-15]
C: Let me draw it, starting with the system context. On the left, twenty product teams, and marketing operations. On the right, three kinds of paid provider: push, email, and S-M-S. At the top, the user. The notification platform sits in the middle. It's the governance layer between twenty teams and five hundred million people.

[slide: v-16]
C: Now the containers, on the send path. Read it left to right. Intake authenticates the tenant, checks its quota, and writes the intent to Kafka. Then the policy and router, which is stateless, decides whether the message may exist, and where it goes. Then channel workers deliver, behind provider adapters. Underneath: the campaign service releases into P-two at a capped rate. The control plane pushes kill flags to the policy layer in about a second. And the policy layer reads Redis and the preference store.

I: Why separate the policy layer from the channel workers? It's one more hop.

C: Because they change for different reasons, and different people own them. Policy changes when the law, or the product rules, change. Workers change when a provider changes. A new channel never touches consent logic. And it's also the team seam I'll come back to.

[slide: v-17]
C: The second container view is the way back. Providers call us with webhooks: receipts, bounces, dead tokens, and STOP replies. The feedback service writes each status, with its reason, to the delivery log. And it deletes dead tokens, so we stop paying to fail. The in-app inbox is written by the channel workers, and read through its own A-P-I. It's the only channel where we can take something back.

[slide: v-18]
C: The life of one notification. Accepted. Routed. Sent. Delivered. But suppressed is a first-class outcome, with a reason. Most of this platform's value is what it decides not to send.

[slide: v-19]
C: So, in one breath.

V: Make intent durable first. Decide centrally if it may exist. Deliver per channel.

[pause: 1.0]

N: Three layers, and a reason for the seam that's organisational, not only technical. That's manager framing, done well.

## Deep dive one: the gates

[slide: v-20]
I: Let's go deeper on the policy layer. Walk me through what happens to one message.

C: Here's the component view. A consumer per priority, then six gates, in order. Cheapest and most absolute first. One: the kill switch. A cached flag. It must beat everything. Two: dedup, in Redis. Three: consent, from the preference store. Four: a per-user rate limit, a token bucket. Five: quiet hours, in the user's time zone. Six: the router, which picks the cheapest valid channel.

[slide: v-21]
C: Each gate that says no records why. Suppressed, with the reason. Quiet hours defers to a delayed queue, and when it wakes up, it goes through every gate again, because consent or the kill switch may have changed. And P-zero is exempt from the caps, and never deferred.

[slide: v-22]
C: One detail on dedup, because it's easy to get wrong. Kafka redelivers after a crash. If worker A checks dedup and then dies, worker B gets the same message. A plain set-if-absent would block that retry, our own retry. So I store the notification id as the value. If Redis hands back my own id, it's a retry, and I proceed. If it hands back a different id, it's a real duplicate. Suppressed.

[slide: v-23]
I: The preference store is down. Do you send?

C: Marketing fails closed. No proof of consent, no send. P-zero security proceeds, because it's always allowed.

I: Okay.

N: Two levels down on one component, and a failure case answered by priority class. That's the depth bar. Don't go a third level unless you're asked.

## Deep dive two: priority isolation

[slide: v-24]
I: A user requests a password reset, while a four-hundred-million-message campaign is going out. What happens?

[slide: v-25]
C: Nothing bad. Because isolation isn't a field in the message. It's structural. P-zero has its own Kafka topic, its own consumer group, its own worker lane, and a reserved slice of provider capacity, with a second S-M-S vendor. A priority field inside one queue changes nothing. Kafka has no per-message priority. A consumer reading in order waits behind everything ahead of it.

[slide: v-26]
C: Follow the reset. Intake writes it to the P-zero topic, and answers two-oh-two. The P-zero consumer has almost no lag. Dedup passes. Consent passes, it's security. The caps don't apply. The P-zero push worker calls Apple. Meanwhile, the campaign drains through a different topic, with different consumers. The backlog is invisible to the reset.

[slide: v-27]
V: Isolation is structural. Own topic, own consumers, own lane, reserved capacity.

[pause: 1.0]

C: And the alert I care about most is P-zero consumer lag, above two seconds.

N: This is the probe that separates candidates. Weak: a priority field. Strong: separate queues. Exceptional: layer by layer, all the way to the provider's rate limit.

## Deep dive three: campaigns

[slide: v-28]
I: The campaign has a typo. Eighty million have already gone. What now?

C: The honest answer first. Sent push, email and S-M-S can't be recalled.

[slide: v-29]
C: So the design is prevention. Every campaign canaries to a tenth of a percent, and an internal seed list. Then it holds, while someone checks the rendering and the complaints. Only then does it release, by time-zone bucket, at a capped rate. And every message still passes every gate.

[slide: v-30]
C: Then a fast halt. The owning tenant presses it, without paging the platform team. The kill flag reaches every policy worker within a second. Queued messages become suppressed. And channel workers check the flag again, just before each send. The target: effective within five seconds.

[slide: v-31]
C: And for what's already gone: push that hasn't been shown can be replaced, with the same collapse id. In-app items can be deleted. A correction email is a business decision. It doubles the noise.

N: Saying "can't be recalled," before you're asked, is credibility.

## Deep dive four: delivery

[slide: v-32]
I: Push fails, you fall back to email, and the push actually arrived. Now the user has both.

C: That happens when failure is ambiguous.

[slide: v-33]
C: So I fall back only on a definite failure. Apple says the token is unregistered. Or the user has no app. Then the feedback service deletes the token, and the router sends email, with the same dedup key. But no receipt after thirty seconds is not a failure. Push receipts are weak. So we wait. The one exception is chosen up front: fraud alerts may go to two channels at once. That's a send-both decision, not a fallback.

[slide: v-34]
C: Every provider adapter has the same three parts. A rate limit that matches the contract. Retries with backoff and full jitter, so clients don't hit a recovering provider in waves. And a circuit breaker. When it opens, P-two simply waits in Kafka, and P-zero switches vendor. After an outage, drop anything past its expiry. "Your driver is here," an hour late, is worse than nothing.

## A requirement added mid-round

[slide: v-35]
I: Product now wants social notifications batched. One an hour, per user.

C: That's a new stage, before routing. A one-hour window per user and category, then one digest. The gates, the workers and the providers don't change. Same shape for WhatsApp, which is one new adapter. Or analytics, which reads the delivery log. That's why intent, policy and delivery are separate.

## Operations

[slide: v-36]
I: How does this fail, and how do you run it?

C: Five failures, with their blast radius. A Redis failover: maybe a second of duplicate risk. Stated, and softened by collapse ids. Preferences down: closed for marketing. A tenant floods intake: it hits its own quota, and nobody else notices. A provider outage: the breaker, and a second vendor for P-zero. And the dangerous one. A policy bug that suppresses everything. It fails silently. Nobody pages you for messages that never went out. So I alert on suppression-rate anomalies, fix it, and replay from Kafka.

[slide: v-37]
C: The S-L-Os follow the targets. And the one alert above all: P-zero consumer lag, above two seconds. The on-call boundary is written down. The platform team owns the pipeline, the providers and the gates. Tenants own their content and their volume.

N: For a manager, this stage is weighted heaviest. The silent failure is the one that impresses.

## The manager layer

[slide: v-38]
I: If you were running this, how would you build it?

C: M-V-P first. Intake, Kafka, push and email, dedup, consent, P-zero isolation, and the kill switch. Those are the things whose absence loses trust. Then quiet hours, caps, campaigns, S-M-S with two vendors, and analytics.

[slide: v-39]
C: Three teams, along the seams of the design. Platform core owns intake, the queues and the gates. Channels owns adapters, providers and deliverability. And campaigns and developer experience owns the relationship with the twenty tenant teams.

[slide: v-40]
C: And a tenant contract, written down. The dedup key is mandatory. The category fixes the priority, so no team declares its marketing P-zero. Quotas per channel. And each team sees its own S-M-S bill. That changes behaviour faster than any policy.

[slide: v-41]
C: To close.

V: I isolate priorities structurally, and I shape the peaks we create, instead of buying capacity for them.

[pause: 0.8]

C: The biggest risk is a bad campaign, or a duplicate storm, contained by the kill switch, canaries and dedup. With an honest limit: sent messages can't be recalled. Next: digests, and per-tenant cost, because S-M-S is the bill.

I: Thanks. A few more questions, on the management side.

N: Four parts. What, trade-off, risk, next. Rehearse it until it's nearly word for word.

## Follow-up 1: the V-P who wants P-zero

[slide: v-42]
I: Three months in. The growth team's vice-president says the Black Friday promotion is business-critical. They want it sent as P-zero, and the caps lifted for the week. They've already gone to your director. What do you do?

[slide: v-43]
C: First, I separate what they need from what they asked for. They need a lot of volume, landing on a fixed date. That, I can give them. The campaign path can book release capacity for that week, by time zone, canaried first. P-zero, no. If marketing rides the P-zero lane, password resets wait behind it. That's a security problem, not a preference.

C: The caps are the real conversation.

V: The caps protect the user. And the user is shared by twenty teams.

[pause: 0.8]

C: So, no global bypass. Instead, an exception path. A written request, a named owner, data on user impact, time-boxed, and reviewed afterwards. The decision belongs to whoever owns the overall user experience. Not to the platform team, and not to whoever escalates loudest. And I'd see my director first, with that one-page proposal. No surprises upward.

N: Needs versus asks. A yes to the real need. A no, with a reason the other side can repeat. And a named decision owner.

## Follow-up 2: the duplicate storm

[slide: v-44]
I: Two weeks after a tenant migrates, users get the same push four times. Your dedup is in place. Walk me through the first hour, and the week after.

[slide: v-45]
C: Detection should come from us, not from support. That tenant's volume, against its baseline. Then I declare an incident, with roles. An incident lead, someone on communications, and the tenant's on-call paged in.

V: Contain first. Explain second.

[pause: 0.8]

C: The fastest safe lever is to throttle that one tenant, back to its baseline. The other nineteen are untouched. Then the cause. If dedup works and users still get four copies, the keys differ. The tenant's retry loop makes a new dedup key on every attempt.

I: So it's their bug. Why is it your problem?

C: Because the platform exists to make tenant bugs harmless to users. So the week after, a blameless review, with the tenant in the room. A second dedup layer, on a hash of the content. Automatic throttling on volume spikes. And a check in the client library for random-looking keys. Each one with an owner, and a date.

N: Throttle one tenant, not the platform. And never blame the tenant in the review.

## Follow-up 3: staffing and migration

[slide: v-46]
I: Suppose this doesn't exist yet. All twenty teams call providers directly. You have twelve engineers, and a year. How do you sequence it?

[slide: v-47]
C: Three teams of four, matching the seams. The first quarter is the M-V-P, with three pilot tenants. I choose them for risk. One with P-zero traffic, like authentication. One that runs campaigns. And one with S-M-S. The second quarter brings caps, quiet hours, S-M-S with two vendors, and the campaign service. Target: half of all traffic. The second half of the year migrates the other seventeen, and ends by revoking direct provider keys. Without that date, a migration never ends.

I: And if teams don't want to move?

C: Migration costs a team real work. So I treat it as a product. I make leaving cheaper than staying. A client library that's smaller than their current provider code. Dashboards they don't have today. And their own S-M-S bill, which most teams have never seen. The mandate exists, but I want most teams to move before they're forced to.

N: Seams that match the architecture. Pilots chosen for risk. A date for every quarter. That's the delivery signal.

## Follow-up 4: the cost spike

[slide: v-48]
I: Last one. Finance says the S-M-S bill doubled last month. Nobody launched anything new. What do you do?

[slide: v-49]
V: I slice before I guess.

[pause: 0.6]

C: By tenant first. Then by category. Say it's one-time codes at sign-up, and nothing else moved. Then by country and number prefix. If a few premium-rate ranges exploded, while the share of codes actually verified fell, that's S-M-S pumping. Bots request codes to numbers where a fraudster shares the fees.

C: Today, I block or cap those prefixes, rate-limit codes per phone and device, and add a daily budget breaker per tenant. But the breaker caps by country and category. Never globally. Capping S-M-S across the board breaks password resets, which is worse than the bill. This quarter: codes by push when the app is active, an alert on sent versus verified codes, and a monthly cost review with finance.

N: The order is the answer. Slice, contain without breaking P-zero, then close the loop with finance.

## Debrief

[slide: v-50]
N: Here's where the round lands. Strong candidates separate intent from delivery. Exceptional ones say governance is the product. Strong ones use separate queues. Exceptional ones isolate every layer, down to the provider. And at the manager layer: a tenant contract, and migration treated as a product. At this level, the follow-ups count as much as the design.

[slide: v-51]
N: Five checks, before the real round. The governance sentence, before the first box. Every number, followed by its consequence. Isolation, layer by layer. Every hard answer names an owner. And in an incident: contain first, explain second. Good luck.
