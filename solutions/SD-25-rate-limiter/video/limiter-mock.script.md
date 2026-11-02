# Distributed rate limiter mock round (video)

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png.
     Speakers: I interviewer · C candidate · V candidate, key line (slower) · N coach. [pause: s] = silence.
     Content follows ../../SD-25-rate-limiter.md. Level: em (L6 / M1), per levels.md.
     The four follow-ups and their diagrams (svg/fu-*.svg) are new for this video. Target ~25 min. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: Lua=Loo-ah INCR=increment -->

## Before you start

[slide: v-01]
N: This is a mock system design round, for an engineering manager loop at level six. The prompt is a distributed rate limiter. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. After the design, four manager follow-ups. Listen once, straight through. On the second pass, pause after every question, and answer it yourself first.

[slide: v-02]
N: Know what's being weighed. At this level, operations and cost count most, then leadership. Depth once: here, how each server decides locally, and how wrong that can be. And expect the manager's curveball. A big customer who wants no limits. A bad config push. Finance wanting to bill from the limiter. A log bill.

## Requirements

[slide: v-03]
I: Design a rate limiter for our API. Every customer has a quota, and we need to enforce it across a fleet of servers.

C: Some numbers first, then the questions that set the trade-off.

[slide: v-04]
C: How much traffic, on how many servers?

I: A million requests a second, across five hundred A-P-I servers, in three regions.

C: So a shared store checked on every request would take a million operations a second, on the hot path. What's limited?

I: Per customer and per endpoint. A thousand requests a minute, say. Some customers have a hundred times that.

C: Hot keys, then. How much latency can the limiter add?

I: Under one millisecond at p ninety-nine.

C: That rules out any cross-region call, and even an in-region call is half the budget. And bursts?

I: Customers burst legitimately. A hard per-second cap would break them.

[slide: v-05]
C: Now the trade-off. How accurate must it be?

I: How accurate can you be? And what does exact cost?

C: That's the question of the round. What does a client get at the limit?

I: A four twenty-nine with Retry-After. What else should it carry?

C: Remaining quota and a reset time, on every response, so clients can pace themselves. If the limiter breaks, fail open or fail closed?

I: Your call. Defend it.

C: And are limits global, or per region?

I: Good question. Assume some are global.

[slide: v-06]
C: I'll treat this as a protection mechanism, not a billing meter. In scope: limits per customer and endpoint, policies, enforcement across the fleet, the headers, and observability of decisions. Out of scope: D-D-O-S at the network edge, billing accuracy, abuse detection, and the gateway itself. If billing needs exact counts, that's a separate asynchronous pipeline. Mixing the two would force exactness onto the hot path for no reason.

N: Separating protection from billing in the first five minutes. That one sentence will save the candidate in follow-up three.

## The thesis

[slide: v-07]
C: So, the framing.

V: The limiter's latency and availability matter more than its accuracy.

[pause: 1.0]

C: It sits on the critical path of every request. A globally exact limiter needs a shared-store round trip per request. Deciding locally from a token bucket, and reconciling asynchronously, is fast, never takes the A-P-I down, and is wrong by a small, bounded amount. I'll choose that on purpose, and tell you the size of the error.

[slide: v-08]
C: The targets. Under a millisecond added at p ninety-nine. A limiter outage must never become an A-P-I outage. Accuracy within a few percent of the configured limit. And policy changes effective within seconds.

## Back of the envelope

[slide: v-09]
C: Three numbers. The first one shapes the whole design.

V: A thousand a minute, divided by five hundred servers, is two per server per minute.

[pause: 0.8]

C: A customer whose traffic lands unevenly on three servers would be throttled at a tiny fraction of their quota. So the limit can't be divided statically.

[slide: v-10]
C: Second, the shared store. A million checks a second at half a millisecond each is feasible across twenty or forty Redis shards. But it puts a network hop and a hard dependency on every single request.

[slide: v-11]
C: Third, state and hot keys. A hundred thousand customers times twenty endpoints is two million keys, about a hundred and twenty-eight megabytes. State size isn't the problem. Hot paths are. A heavy customer can send a hundred thousand requests a second on one key, and no single shard takes that.

I: So what do you want?

C: Local decisions, with a share of the quota that moves to where the traffic actually is.

N: Three numbers, and the first one killed the obvious design. That's the estimation bar.

## The A-P-I

[slide: v-12]
C: The decision is an in-process call: allow, for a customer, an endpoint and a cost. It returns allowed, remaining, the reset time and retry-after. Every response carries rate-limit headers: the limit, the remaining count, and seconds to reset. Retry-After only on a four twenty-nine. Policies are set through a control-plane A-P-I: rate, period, burst, a scope of global or region, and a mode of enforce or shadow.

## Data model

[slide: v-13]
C: State lives in four places. Policies, cached in every server. Local buckets, in memory: tokens, last refill and the current share. A regional coordinator, Redis per region, holding consumed counts and share grants. And a sampled decision log, which answers "why was I limited?".

## High-level design

[slide: v-14]
C: The context. Customers call the A-P-I. Support and product manage policies and exceptions. Billing and metering is beside it, as a separate exact pipeline, fed by usage events. Monitoring gets the S-L-Is and the decision log.

[slide: v-15]
C: One region, inside. The load balancer, then about a hundred and seventy A-P-I servers, each with the limiter library and its token buckets in memory. Asynchronously, each server reports usage to the regional coordinator and gets its share back. The policy service pushes changes to every server. And decisions are sampled into the log.

[slide: v-16]
C: One request. The library looks up the policy in its local cache, refills the bucket, and takes a token. That's an in-memory atomic operation, microseconds. If a token is there, the request is handled, and the response carries the headers. If the bucket is empty, four twenty-nine, with Retry-After. No network hop on the hot path.

[slide: v-17]
C: And the sync, every hundred milliseconds. Each server reports what it used for each active key. Server one used forty, server two used four. The coordinator gives each a share of the remaining budget, in proportion to its demand. Ninety percent and ten. For global keys, coordinators in different regions exchange totals every few seconds.

[slide: v-18]
I: Why not just a Redis increment per request? It's simpler.

C: It is, and at small scale I'd use it. At a million a second, it adds about half a millisecond to every call, which is half the budget. It concentrates heavy customers on single shards. And it turns a Redis incident into an A-P-I outage. Local buckets with async shares remove all three, at the price of bounded inaccuracy.

[slide: v-19]
C: Technology. The decision point is an in-process library, or a sidecar: zero hops. The algorithm is a token bucket: it allows bursts up to a cap and enforces a long-run rate, with constant state. The coordinator is Redis per region, with Lua scripts for atomic share updates. It only sees servers times keys every hundred milliseconds, not a million a second. Policies are pushed and cached, so servers keep working if the policy service is down. And the decision log is sampled into a columnar store.

[slide: v-20]
C: Inside the library: decide, which takes the token and sets headers. A policy cache. The local buckets. A share manager that runs every hundred milliseconds. A fallback for when the coordinator is down. And a decision sampler.

## Deep dive one: algorithms

[slide: v-21]
I: Which algorithm, and why not the others?

[slide: v-22]
C: A fixed window is the simplest, but it allows twice the limit at the boundary: a thousand at eleven fifty-nine and fifty-nine seconds, and another thousand at noon. A sliding log is exact, but stores a timestamp per request, which is unusable at this scale. A sliding window counter is a cheap, weighted approximation, and a fair compromise. A token bucket expresses rate plus burst directly, with constant state. That's my choice. A leaky bucket smooths output: it's for shaping outbound traffic, not for quotas.

[slide: v-23]
C: One more thing, because it's a real production bug.

V: Check-and-decrement must be atomic.

[pause: 0.8]

C: Reading the count, comparing, and then writing races under concurrency, and lets traffic through. So it's a Lua script, an atomic counter, or a single-threaded local bucket.

## Deep dive two: how wrong can it be?

[slide: v-24]
I: So each server decides locally. How wrong can it be?

[slide: v-25]
C: Each server holds a share of each active key's budget, recomputed every interval, about a hundred milliseconds, from reported demand. Within one interval, a server can only overspend its own share. So the total overshoot is bounded by one interval's worth of demand shift. For a thousand a minute, that's a few tokens. For the heaviest customer at a hundred thousand a second, one to two percent. And uneven load balancing stops mattering, because shares follow traffic, not node count. That's exactly what killed the static split.

[slide: v-26]
V: I'm accepting up to a couple of percent over the limit, in exchange for no hop on the hot path.

[pause: 0.8]

C: If a customer has a contractual hard cap, say a paid tier, I switch that one policy to synchronous mode, and pay the hop for them only.

N: The error was given a size, and an escape hatch with a cost. That's the depth this round asks for.

[slide: v-27]
I: And a key the server has never seen?

C: Most customers are cold most of the time. On the first request for a key, the server asks the coordinator once, in-region, about half a millisecond, then caches the share. Later requests are local. The extra latency is bounded, and only on first use.

[slide: v-28]
I: The hot key?

C: The customer sending a hundred thousand requests a second is spread across every server, each with a local share. So the hot key is aggregated locally, by the same mechanism. The coordinator sees five hundred reports every hundred milliseconds, not a hundred thousand a second. A shared-store design would need sub-counters, summed on read.

## Deep dive three: the coordinator fails

[slide: v-29]
I: The coordinator is down. Fail open, or fail closed?

[slide: v-30]
C: Fail open, locally. Servers keep enforcing with their last known shares, decaying slowly toward a conservative default. So the A-P-I keeps working, and abusive customers are still roughly contained. On-call is alerted, but it's a degradation, not an outage.

[slide: v-31]
V: Fail-closed by default would make the limiter a single point of failure for the whole A-P-I.

[pause: 0.8]

C: If one endpoint should fail closed, say an expensive export, I'd make that a policy for that endpoint, and say why it's different.

## Deep dive four: regions

[slide: v-32]
C: Three regions, each with its own coordinator. The default scope is region: each region enforces its part of the limit independently, exact per region, with no cross-region traffic.

[slide: v-33]
C: Global scope has coordinators exchange consumption every few seconds and rebalance regional budgets. The overshoot is one sync interval of cross-region demand shift, and I'd state that. An exact global limit would need a cross-region round trip, about a hundred milliseconds, per decision. That breaks the one-millisecond budget. That's the honest answer.

## A requirement added mid-round

[slide: v-34]
I: A customer needs ten times the burst, for the first thirty seconds of each hour.

[slide: v-35]
C: The token bucket expresses that as a scheduled policy: ten times the burst, from the top of the hour for thirty seconds, pushed by the policy service and effective in seconds. Then I'd push back on the operational cost. Special cases for individual customers accumulate. I'd offer it as a product tier, burst credits, with an owner and an expiry date, rather than a hand-edited exception.

N: Yes to the customer, no to the snowflake. That's a manager answer to a feature request.

## Failures and operations

[slide: v-36]
C: The failures. Coordinator down: last shares, decaying, and an alert. Policy service down: cached policies keep working. A bad policy, with a limit of zero: that's the dangerous one, so new policies go through shadow mode and canary, with instant rollback. Clock skew: buckets use local monotonic clocks. And a server restart: start with a small share, converge in one interval.

[slide: v-37]
C: The policy rollout, as a sequence. An operator creates a policy in shadow mode. It's pushed everywhere, and would-be rejections are counted, but nothing is blocked. The decision log answers: how many four twenty-nines would this cause? Then enforce, on canary servers first, then everyone. And rollback takes seconds.

[slide: v-38]
C: The S-L-Os. Decision latency, under a millisecond at p ninety-nine. But the one customers feel is the false-limit rate: four twenty-nines issued to customers who were below their limit over the window, measured from the decision log. And "why was I limited?": policy version, node and bucket state, so support can answer a complaint in minutes. I'd design that in from day one.

N: The false-limit S-L-I is the operations signal. It measures the limiter's error from the customer's side.

## The manager layer

[slide: v-39]
I: How would you build it?

C: Week one: in-process token buckets on every server, with a conservative static share, shadow mode on, and the decision log. Week four: the coordinator, with demand-weighted shares and fail-open. Global scope later, only for policies that need it. The decision log and the false-limit S-L-I ship in week one, because the first real problem is always a customer asking why they were throttled.

[slide: v-40]
C: Ownership. The platform team owns the library, the coordinator, the false-limit S-L-I, and on-call. Policy governance owns exceptions, each with an owner and an expiry. And support owns the "why was I limited?" tool and its runbook.

[slide: v-41]
C: To close.

V: It fails open on its own dependencies, so it can never take the A-P-I down.

[pause: 0.8]

C: It's an in-process token-bucket limiter whose per-server share follows real demand, synced with a regional coordinator every hundred milliseconds. Exact limits with no hot-path hop are resolved by accepting an overshoot of a percent or two, with a synchronous mode for hard caps. Next, the decision log and the false-limit S-L-I.

I: Thanks. Some questions on the management side.

## Follow-up 1: no limits for the big customer

[slide: v-42]
I: Sales just signed our biggest customer. They want them exempt from rate limits. Entirely.

[slide: v-43]
C: First I'd find the real need. Is it a launch day? A nightly batch job? Or do they simply need a bigger tier? Usually the answer is a higher limit, not no limit. An unlimited customer can take down the A-P-I for every other customer, including themselves. So the protection stays. Whatever we agree gets an owner and an expiry date, and it's reviewed.

V: I won't just refuse. I'll price the risk, and offer what they actually need.

[pause: 0.8]

C: If sales still wants no limit, the risk is written down, and the decision goes to whoever owns platform reliability. Not decided in a hallway.

N: Find the need behind the request, keep the protection, and escalate with the risk written down.

## Follow-up 2: the bad push

[slide: v-44]
I: Someone pushed a policy with a limit of zero for a popular endpoint. Eight minutes of four twenty-nines, for everyone.

[slide: v-45]
C: Minute one: the four twenty-nine rate spikes, and the false-limit S-L-I fires. Minute three: roll back to the previous policy version, with one command. Minute ten: the status page, a support script, and a note to the customers who were affected. The week after: a blameless review. The question isn't who pushed it. It's why the system let one push reach everyone.

V: Config is code. It ships through shadow mode and canary, like code.

[pause: 0.8]

N: Roll back first, fix the process, not the person. And the fix makes the safe path mandatory.

## Follow-up 3: billing from the limiter

[slide: v-46]
I: Finance wants to bill customers from the limiter's counts. It already counts every request, right?

[slide: v-47]
C: It counts approximately, and on purpose. The limiter protects the platform, and a couple of percent of error is fine for that. Billing needs exact counts, and a couple of percent of error there is a customer dispute. So billing should be a separate, exact, asynchronous pipeline: usage events, deduplicated, from the same event stream. One source, two consumers, two guarantees. Mixing them would force exactness onto the hot path for no reason.

C: And I'd name the owners: the platform team for protection, and the billing team for the meter.

N: The scope sentence from minute five paid off here. Different jobs, different guarantees, different owners.

## Follow-up 4: the log bill

[slide: v-48]
I: Last one. The decision log now costs more than the rest of the limiter put together.

[slide: v-49]
C: Slice first: is it allowed decisions, rejections, or retention? The lever is usually sampling allows. Log one percent of allowed decisions, and keep every rejection, because rejections are what customers ask about. Then tier retention: seven days hot, then cold, with aggregates kept longer. What I won't cut is the ability to explain a single four twenty-nine, because that's what support uses.

N: Cut the cost without cutting the capability. That's the manager's cost answer.

## Debrief

[slide: v-50]
N: Here's where the round lands. Strong candidates reach for a Redis increment. Exceptional ones say "availability over accuracy" early. Strong ones give the request rate. Exceptional ones divide a thousand by five hundred, and kill the static split. Strong ones name the token bucket. Exceptional ones compare five algorithms, and make check-and-decrement atomic. And on accuracy, exceptional ones give the error a size.

[slide: v-51]
N: Five checks, before the real round. A thousand divided by five hundred, and the static split is dead. Algorithms compared, the boundary burst named. Atomic check-and-decrement. Fail open, and why. And the error sized, with "why was I limited?" designed in. Good luck.
