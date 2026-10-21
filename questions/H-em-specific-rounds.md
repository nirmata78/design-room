# Archetype H · EM-specific rounds

**SD-55 – SD-62, plus the senior-manager & director expansion SD-89 – SD-92.** Slice with `grep -n '^### SD-56' questions/H-em-specific-rounds.md`, then Read with
`offset`. Do not read this file whole.

**Read this before running any question in this archetype.**

These are **not "design X" questions.** They test the work an engineering manager actually does:
reviewing someone else's design, sequencing a migration, defending a budget, setting an SLO, splitting
a system across teams, killing a platform, and deciding whether to build at all. An L6 EM loop very
often contains one of these in some form — sometimes disguised as a normal design round that turns
into a review after twenty minutes.

**Four of the eight invert the round: you present an artifact and they respond** (SD-55, SD-57, SD-58,
SD-61). Each of those sheets contains the artifact, ready to paste, and a **planted-defect list** which
is the answer key. Rules for running an inverted round:

1. **Paste the artifact into chat, or write it into `interview.md` §0** if it is long. Say it is a
   design/proposal/incident from *another team* — never one you are defending, so criticising it is
   socially free.
2. **Do not hint at the number of defects, and do not confirm a find.** Neutral acknowledgement only:
   *"Okay, noted. Anything else?"* — including when they name something that is *not* a defect.
3. **They are scored on prioritisation, not enumeration.** Twelve findings in random order is a worse
   answer than the three that matter, ranked, with the reason each matters. Ask *"if you could only
   raise three of these in a 30-minute review with the author, which three and in what order?"*
4. **Score the tone as well as the content.** They are playing a manager reviewing another team's work.
   *"This is wrong"* and *"help me understand the reasoning behind X"* get very different results in a
   real organisation, and Communication and Leadership-signal should reflect which one they use.
5. **Reveal the planted-defect list only at debrief**, including the defects they missed and the ones they
   raised that aren't real.

---

### SD-55 · Design review — critique and improve a given design   [T1 · INVERTED · G★ A MS]

**Read aloud:** *"Here's a design doc from another team in your org. They've asked you to review it
before they start building. Walk me through your review — what you'd raise, and what you'd raise
first."*

**Crux.** **Prioritisation and influence.** A strong reviewer finds the two or three issues that would
be expensive to fix later, distinguishes them from the ones that are cheap to change once built, and
raises them in a way that would actually get acted on. Finding a long list is not the skill; ranking it
is.

**The artifact — paste this in verbatim:**

> **Design: Customer Activity Timeline Service** *(Team Aurora, v0.3)*
>
> **Goal.** Give support agents a single timeline of everything a customer has done — orders, payments,
> support tickets, logins, emails — for the last 2 years. Agents currently open six tools.
>
> **Users.** 4,000 support agents. Expected 20 timeline views per agent per hour.
>
> **Design.**
> 1. A new `TimelineService` exposes `GET /timeline/{customerId}`.
> 2. On each request it calls the six source services in parallel (Orders, Payments, Tickets, Auth,
>    Email, Marketing), merges the results in memory, sorts by timestamp and returns the last 500
>    events.
> 3. Each source call has a 30-second timeout. If a source fails, we retry twice, then return a 500 so
>    the agent knows the data is incomplete.
> 4. Results are cached in Redis for 24 hours keyed by `customerId`, to keep source load low.
> 5. Auth: the service checks the caller has the `support-agent` role.
> 6. Deployment: 3 instances behind the existing internal load balancer. We'll add more if it's slow.
> 7. Monitoring: we'll add a dashboard with request count and error rate.
> 8. Timeline: 6 weeks, 3 engineers. Phase 2 (a search box) in Q3.
>
> **Rejected alternative.** We considered replicating source data into our own store, but that's more
> work and the data would be stale.

**Planted defects — the answer key, ranked by how expensive each is to fix later:**

| # | Defect | Why it matters | Tier |
|---|---|---|---|
| 1 | **24-hour cache on a support tool.** An agent talks to a customer who paid 10 minutes ago and sees nothing. This is a *product-correctness* failure, not a tuning issue, and it contradicts the entire purpose of the tool | Breaks the use case | **must-raise** |
| 2 | **Return 500 when one of six sources fails.** With six dependencies at even 99.9% each, the composite availability is ~99.4% — and the whole page fails when one non-essential source (Marketing) is down. Should degrade partially and label what's missing | Availability arithmetic | **must-raise** |
| 3 | **30-second timeout × 2 retries × 6 sources.** Worst case is minutes; the retries amplify load on an already-struggling source (no backoff, no budget, no circuit breaker). This is how a single slow source becomes a company-wide incident | Cascading failure | **must-raise** |
| 4 | **Authorization is role-only.** Any support agent can read *any* customer's full history — payments, emails, logins — with no per-record scoping, no need-to-know check, and no audit log of who looked at whom. For this data class that is a compliance problem | Security / compliance | **must-raise** |
| 5 | Cache invalidation is entirely absent — no mechanism to evict on a new event, so even shortening the TTL only mitigates | Correctness | should-raise |
| 6 | No pagination story; "last 500 events" is arbitrary and unexplained, and a 2-year timeline for an active customer far exceeds it | Requirements gap | should-raise |
| 7 | Monitoring is request count and error rate only — no per-source latency or error breakdown, so "the timeline is slow" is undiagnosable. No SLO, no alert, no on-call named | Operability | should-raise |
| 8 | Capacity claim unexamined: 4,000 × 20/hour ≈ 22 req/s, which is genuinely small — **so 3 instances is probably fine and this is *not* a real defect.** Worth noting whether they flag it anyway, i.e. whether they can tell a real risk from a scary-sounding one | *(distractor)* | — |
| 9 | The rejected alternative was dismissed on effort, not on the actual trade-off; the staleness objection is ironic given the 24-hour cache. A CDC-fed read model would address 1, 2 and 3 together | Judgment | nice-to-raise |
| 10 | No mention of what happens as sources evolve their schemas, or who owns the timeline when a seventh source appears | Longevity | nice-to-raise |
| 11 | Phase 2 "search box" over 2 years of merged events is a fundamentally different system, and committing to it in Q3 off this architecture is a trap | Sequencing | nice-to-raise |

**Probe ladder:**
- "What would you raise first, and how would you say it to the tech lead?"
- **"If you could only raise three things in a 30-minute review, which three?"** (the core probe)
- "Which of your findings are expensive to fix after launch, and which are cheap? Does that change
  your ordering?"
- "Their availability target isn't stated. What is it, given this design?" (drive the 99.4% arithmetic
  — if they don't compute a composite availability number, that's a real gap)
- "Is anything here actually fine that a nervous reviewer would flag?" (tests calibration — item 8)
- "They push back: 'the 24-hour cache is needed for source load.' Your response?" (the numbers say
  22 req/s doesn't need a cache at all — the strong answer challenges the premise with arithmetic)
- *EM bar:* "You think this needs a different architecture. They've committed to 6 weeks and told their
  PM. How do you handle that?" · "Would you block this, or let it ship and fix it later? What's your
  criterion?" · "What would you ask them to prototype in week one to de-risk it?"

**Weak / Strong / Exceptional.** *Weak* — lists surface issues in the order they appear in the doc,
misses the cache and the availability composition, or nitpicks style. *Strong* — finds most must-raise
items, ranks them by cost-of-late-fix, computes composite availability, and frames the feedback
collaboratively. *Exceptional* — leads with the two findings that invalidate the approach rather than
the ten that improve it, does the arithmetic that dismantles the cache justification, spots the
distractor and says it's fine, proposes the alternative architecture as a question rather than a
verdict, and has a clear position on blocking versus shipping.

**Traps.** Redesigning the system instead of reviewing it (a real EM failure mode — note it if they
rewrite rather than reviews). Being harsh, which in a real org gets the finding ignored. Missing the
authorization issue because it's one line in the doc.

---

### SD-56 · Migration — monolith to services, or datacentre to cloud   [T1 · A★ MS★ G]

**Read aloud:** *"You've inherited a ten-year-old monolith serving all of the company's customers. The
mandate is to move to services on cloud infrastructure over the next eighteen months, without a
customer-visible outage. How do you approach it?"*

**Crux.** **Sequencing and reversibility.** There is no interesting technical novelty here; the entire
signal is whether they can order the work so that value arrives early, each step is independently
revertible, and the organisation can absorb it. **A big-bang cutover, or a two-year rewrite with no
delivery in between, is a fail regardless of how well-drawn the target architecture is.**

**If they ask:**

| Question | Answer |
|---|---|
| Size? | 2M lines, 300 database tables in one shared schema, 40 engineers across 6 teams |
| Traffic? | 20k req/s, 99.95% availability today, and customers notice a 5-minute outage |
| Why migrate? | Ask them. If pushed: deploys take 4 hours and happen weekly; scaling means buying servers with 3-month lead times |
| Constraints? | The product roadmap does not stop. Half the team's capacity remains on features |
| Data? | 40 TB in one relational database, hottest tables written by 30 different code paths |
| Deadline? | 18 months is a leadership commitment, not a technical estimate. **Ask them what they do with that** |
| Team appetite? | Mixed — two teams are enthusiastic, one is openly sceptical |

**Listen for:**
- **Establishing the *why* and the success metric before the plan.** "Deploy lead time and scaling
  cost", not "we'll be on microservices". A candidate who starts drawing a target architecture without
  asking what problem the migration solves has already missed the round's point.
- **Strangler-fig incremental extraction** with a routing layer/facade in front, so traffic moves
  service by service and each move is revertible by a routing change. **← The core mechanism.**
- **Ordering by risk and value, stated as a principle**: extract something with low coupling and real
  value first to prove the pattern and build confidence; leave the hairiest shared-data domain until the
  team has learned. Not alphabetically, not "the most important thing first".
- **The data migration being the hard part**, not the code — expand/contract schema changes, dual
  writes with a reconciliation check, backfill, then read cutover, then decommission, with **a
  verification step at each stage** and the ability to stop at any stage.
- **Dual-run and shadow traffic** to compare old and new behaviour on real requests before switching.
- **Explicit rollback per step**, and the honest identification of the **one-way doors** (data
  ownership splits, deleting the old path) with a deliberate decision about when to close them.
- **Keeping the lights on**: the monolith continues to receive features during the migration, so the
  plan must survive a moving target, and the seams must be chosen to minimise ongoing double work.
- **The organisational half**: team boundaries realigned to the new services (Conway's law), a
  migration budget defended against the roadmap, the sceptical team handled, and **who owns a service
  after extraction** — a migration that produces unowned services has failed.
- **Milestones that deliver value independently**, so an 18-month programme that gets cancelled at
  month 9 still leaves the company better off. **← The senior insight, and it is the most reliable
  4-signal in this question.**
- **A stop/reassess criterion**: what evidence would make them recommend halting.

**Probe ladder:**
- *Requirements:* "What's the success metric, and who agreed it?" · "What's explicitly not moving?"
  (a strong answer leaves parts of the monolith alive forever — "migrate everything" is usually wrong)
- *Estimation:* "40 engineers, half on features, 18 months — what's the capacity in engineer-months,
  and is that enough for 300 tables?" (usually it visibly isn't, which is the interesting part)
- *Design:* "Draw the first three months." · "What's the first thing you extract, and why that?"
- *Deep dives:* **"Walk me through moving one table that 30 code paths write to."** (expand/contract,
  dual write, reconcile, cut reads, decommission — the crux probe) · "You're at month 9, 30% done, and
  leadership asks whether to stop. What do you say and what evidence do you have?" · "A dual-write
  divergence appears in production. How do you detect it, and what do you do?" · "One team refuses to
  extract their domain. What now?" · "What's your rollback if the new payments service is worse and
  you've already moved 20% of traffic?"
- *EM bar:* "How do you protect migration capacity when a big customer escalation lands?" · "What do
  you tell the VP at month 3 who asks what they got for the money?" · "How do you know the migration is
  *working* — not finished, working?" · "Which of these decisions is irreversible?"

**Curveball:** *"Six months in, the cloud costs are running 3× the datacentre and the CFO wants an
explanation."* Tests whether they anticipated unit-cost changes (lift-and-shift is usually more
expensive), whether they have cost instrumentation, and whether they can make the argument in business terms
rather than technical ones.

**Weak / Strong / Exceptional.** *Weak* — a target architecture diagram, a rewrite plan, a cutover
weekend, no data migration detail, no rollback, no organisational dimension. *Strong* — strangler
pattern with a routing facade, risk-ordered extraction, expand/contract data migration with dual writes
and reconciliation, per-step rollback, team ownership addressed, value-delivering milestones.
*Exceptional* — starts from the business metric, sequences so cancellation at any point still leaves
value, names the one-way doors explicitly, has a stop criterion, defends the capacity politically, and
anticipates the cost surprise.

**Traps.** Designing the destination in detail and the journey vaguely — redirect to sequencing.
Migrating for its own sake. Assuming the team's capacity is fully available. Treating the 18-month
commitment as a technical fact rather than something to negotiate with evidence.

---

### SD-57 · Capacity, cost & FinOps review   [T1 · INVERTED · A★ N G]

**Read aloud:** *"You've just taken over a platform team. Here's last month's infrastructure bill.
Finance wants 30% out of it by next quarter without hurting reliability. Where do you start?"*

**Crux.** **Unit economics.** The strong move is to convert an absolute bill into a **cost per unit of
business value** (per request, per customer, per hour watched), find where that unit cost is
indefensible, and act there — rather than shaving percentages off the largest line item. Also: knowing
which cuts trade against reliability and saying so out loud.

**The artifact — paste this in verbatim:**

> **Monthly infrastructure bill — Platform Team · $1.42M**
>
> | Line item | Monthly | Notes |
> |---|---|---|
> | Compute — service fleet (4,000 VMs) | $480k | Average CPU utilisation 11%. Autoscaling configured on 60% CPU, min instances = max instances |
> | Data egress | $310k | Mostly serving API responses to mobile clients. No CDN in front of the API |
> | Managed database — primary cluster | $190k | One 96-core instance + 2 read replicas. Peak CPU 22% |
> | Object storage | $145k | 8 PB. All in the standard/hot tier. 70% of objects not read in over a year |
> | Observability vendor | $120k | Billed per GB ingested. Debug logging enabled in production across all services |
> | Managed Kafka | $85k | 3 clusters. One is used only by a decommissioned service's consumer group |
> | Non-prod environments | $60k | 12 environments, running 24/7, including 4 nobody has deployed to in 3 months |
> | CI compute | $22k | 20k builds/day, no build cache |
> | Misc / untagged | $8k | Cannot attribute to a team |
>
> **Business context.** 200M requests/day. 40M monthly active users. Revenue $12M/month. The bill has
> grown 60% year-on-year while traffic grew 15%.

**Planted findings — the answer key:**

| # | Finding | Rough saving | Reliability risk | Tier |
|---|---|---|---|---|
| 1 | **11% utilisation with min=max autoscaling.** The fleet is statically sized for peak and never scales down. Right-sizing instance types plus real autoscaling is the single biggest lever | $200–300k | Low if done gradually with headroom | **must-find** |
| 2 | **No CDN in front of the API**, paying full egress for cacheable responses. Even a modest hit ratio on read-heavy endpoints moves this materially | $100k+ | Low; improves latency | **must-find** |
| 3 | **8 PB all in hot storage with 70% cold for a year.** Lifecycle tiering is nearly free to implement | $60–80k | Very low (slower first byte on cold reads) | **must-find** |
| 4 | **Debug logging in production, billed per GB.** Log-level discipline and sampling | $60–70k | **Negative if done carelessly** — cutting logs hurts incident response. Sample, don't delete | **must-find** |
| 5 | The unattached Kafka cluster and the 4 unused non-prod environments are pure waste; the other environments should be scheduled off outside working hours | $70–90k | None | should-find |
| 6 | Database at 22% peak CPU on a 96-core instance, and the read replicas may be unused — needs a downsize after checking replica traffic | $60–90k | Medium — **the one place to be careful**, since a database downsize is hard to reverse quickly under load | should-find |
| 7 | No build cache on 20k builds/day — small money, but it also buys engineer time (links to SD-32) | $10k + time | None | nice-to-find |
| 8 | **The real finding: cost grew 60% while traffic grew 15%.** Unit cost is deteriorating badly, so any one-off 30% cut will be eaten within a year. **Something structural is wrong and that's the actual problem** | — | — | **the 4-signal** |
| 9 | **$8k untagged means there is no cost attribution**, so no team sees the consequence of its choices. Tagging plus per-team showback is the mechanism that stops recurrence | — | — | **the 4-signal** |
| 10 | Cost per request is ~$0.24/1k requests and infrastructure is ~12% of revenue — **worth computing before cutting anything**, to know whether 30% is even the right target | — | — | nice-to-find |

**Probe ladder:**
- "What's your cost per request and per active user? Compute it." (the reframe that should come first)
- "Rank your actions by saving-per-unit-of-risk. Which do you do this week?"
- **"Which of these cuts would you refuse to make, and why?"** (the reliability-trade probe — the
  logging one is the trap: it looks like free money and it degrades incident response)
- "Cost grew 60% while traffic grew 15%. What does that tell you, and what do you do about *that*?"
- "You've hit 30%. What stops it coming back in twelve months?"
- *EM bar:* "How do you get twenty teams to care about their own costs?" (showback/chargeback, cost in
  the design-review checklist, a per-team budget) · "What do you tell finance about the 30% target —
  is it the right number?" · "Which of these would you *spend more* on?" (headroom, and possibly
  observability — a candidate who only cuts is missing half the judgment)

**Weak / Strong / Exceptional.** *Weak* — starts at the largest line item and proposes buying cheaper
instances; treats every cut as free; no unit economics. *Strong* — computes unit cost, finds the
utilisation, egress, storage-tier and logging items, ranks by risk, and is careful about the database.
*Exceptional* — leads with the 60%-versus-15% divergence as the real problem, refuses the cut that
damages incident response, builds attribution so the saving persists, names what deserves *more*
spending, and challenges whether 30% is the right target.

**Traps.** Cutting observability to hit a number (looks great this quarter, costs a bad incident next
quarter). Downsizing the database without checking replica traffic first. Delivering a one-off saving
with no mechanism to stop regrowth.

---

### SD-58 · Reliability & SLO design for an existing system   [T1 · INVERTED · G★ A N]

**Read aloud:** *"You've taken over a service that's been up for two years with no formal SLOs. It has
1,200 alerts configured and the team is exhausted from being paged. Design the reliability programme —
what you measure, what you page on, and what changes."*

**Crux.** **An SLO is a constraint you agree with the business and then engineer against, not a number
you write on a dashboard.** The round is whether they can pick a small number of SLIs that reflect *user
experience*, set targets from business need rather than from current performance, and use the error
budget to change behaviour — plus fix the on-call load, which is a people problem with a technical
solution.

**The artifact — paste this in verbatim:**

> **Service: Checkout API.** 8 engineers, on-call 1-week rotation.
>
> **Current state.**
> - 1,200 alerts configured; ~40 pages/week; 85% of pages are resolved by "no action needed".
> - Alerts include: CPU > 70% on any instance, memory > 80%, disk > 75%, each of 340 endpoints having
>   its own latency alert, one alert per downstream dependency error, 6 alerts that page for the same
>   root cause, and 30 alerts nobody can explain the origin of.
> - Availability last quarter: measured as "instances passing health check" = 99.98%.
> - Customer-reported incidents last quarter: 7. Two of those had **no** corresponding alert.
> - MTTR: unknown, not measured.
> - Two engineers have asked to move teams, citing on-call.

**Planted findings — the answer key:**

| # | Finding | Tier |
|---|---|---|
| 1 | **The availability metric measures the wrong thing.** "Instances passing health check" says nothing about whether customers can check out. 99.98% healthy instances alongside 7 customer incidents proves the SLI is disconnected from the user experience. **Measure success rate and latency of the checkout request, from as close to the client as possible** | **must-find** |
| 2 | **85% false-positive rate on pages means the alerts are actively harmful** — the team is trained to ignore pages, which is why two real incidents had no alert anyone acted on. Alert fatigue is a reliability risk, not just a morale one | **must-find** |
| 3 | **Cause-based alerting instead of symptom-based.** CPU/memory/disk thresholds page on things that are not user-visible. Page on symptoms (error rate, latency, saturation of the user-facing SLI); leave causes to dashboards and tickets | **must-find** |
| 4 | **No error budget, so no mechanism connects reliability to decisions.** With an SLO and a budget, burn rate decides whether the team ships features or reliability work — turning reliability from an argument into arithmetic | **must-find** |
| 5 | Alert consolidation: 6 alerts for one root cause should be one, with dependencies suppressed; 30 unexplained alerts should be deleted (if nobody knows why it exists, it cannot be actioned) | should-find |
| 6 | **Multi-window burn-rate alerting** instead of static thresholds: page fast on a rapid burn, ticket on a slow burn. This is the mechanism that cuts page volume without losing coverage | should-find |
| 7 | MTTR unmeasured, so there is no feedback on whether anything improves. Also needs incident review discipline | should-find |
| 8 | On-call load itself needs a target (e.g. under 2 actionable pages per week) and an escalation path when exceeded — otherwise nothing forces the fix | should-find |
| 9 | 340 per-endpoint latency alerts is the wrong granularity — aggregate to a small number of user journeys | nice-to-find |
| 10 | **The SLO target must come from the business, not from last quarter's number.** Ask what checkout failure costs, and what customers tolerate. Setting 99.99% because they hit 99.98% is backwards | **the 4-signal** |
| 11 | The two attrition requests are the most urgent item on the page — a reliability programme that ignores the humans will not survive to deliver | **the 4-signal** |

**Probe ladder:**
- "How many SLIs should this service have, and what are they?" (a small number, user-journey shaped;
  if they propose twenty, probe why)
- "Where do you measure them, and why does that choice matter?" (client-side or at the edge — server
  metrics miss the failures that never reach the server)
- **"What number do you pick for the target, and how do you defend it?"** (must come from business
  tolerance and cost, not from history)
- "Walk me through what happens when the error budget is 80% consumed with two weeks left."
- "You're going to delete a thousand alerts. What if you delete one that mattered?" (a real risk — the
  good answer is to derive alerts from the SLO first, run in parallel, then remove)
- "Two of seven incidents had no alert. How does your design catch those?"
- *EM bar:* **"Two engineers want to leave over on-call. What do you do in week one?"** (a candidate who
  goes straight to technical fixes and never addresses this is missing the question) · "How do you get
  the PM to accept a reliability sprint?" (the error budget is the answer, and that's the point of
  having one) · "What do you report upward, monthly?"

**Weak / Strong / Exceptional.** *Weak* — proposes tuning alert thresholds and adding a dashboard;
keeps the health-check availability metric; no error budget. *Strong* — replaces the SLI with
user-journey success and latency, sets an SLO with an error budget, moves to symptom-based burn-rate
alerting, consolidates and deletes alerts safely, measures MTTR. *Exceptional* — derives the target
from business cost, treats alert fatigue as a reliability defect, uses the error budget as the
prioritisation mechanism with the PM, sets an explicit on-call load target, and addresses the attrition
risk first.


---

### SD-59 · Multi-team decomposition & API contracts   [T1 · G★ MS A]

**Read aloud:** *"You're given a large system to build — say the one we just designed — and forty
engineers across five teams. How do you split the work so those teams can move independently, and what
do you own as the manager?"*

**Crux.** **Cutting along seams that minimise cross-team coordination, then making the contracts at
those seams explicit and independently evolvable.** The failure mode is a decomposition that looks
clean on a diagram and creates a dependency web where nothing ships without three teams synchronising.

> **Best run immediately after a design round** on the same problem, as a follow-on — that's usually how
> it appears in a real loop. It also works standalone using any T1 question's design as the subject.

**If they ask:**

| Question | Answer |
|---|---|
| Teams? | 5 teams of 8, in 3 time zones |
| Existing skills? | Two teams know the domain, three are new to it |
| Timeline? | First release in 6 months |
| Can they change team structure? | Yes, once, at the start. **Give them this** — what they do with it is the signal |
| Is anyone dependent on them? | Yes, two external teams consume the output |

**Listen for:**
- **Seams chosen by coupling, not by technical layer.** Splitting into "frontend team, API team,
  database team" is the classic wrong answer — every feature then needs all three. Cutting by domain
  or vertical capability means a team can ship a feature alone. **← The senior insight, and it should
  come with Conway's law stated in their own words: the architecture and the org chart will converge, so
  choose both together.**
- **Contracts defined and versioned before implementation starts**, with a compatibility policy
  (additive changes only, deprecation windows) and consumer-driven contract testing so a team can
  change without breaking consumers.
- **The critical path and the dependency graph made explicit** — which team blocks which, and the
  deliberate use of **mocks/stubs against an agreed contract so a downstream team is never idle.**
- **Ownership of shared components**: the thing everyone needs (a shared schema, a common library, the
  ledger) either gets a clear owner or becomes a coordination tax. Naming that risk is a strong signal.
- **Sequencing against skills**: the two experienced teams take the riskiest domains, the three new
  teams start on well-bounded pieces with a clear contract.
- **Time-zone reality**: put the tightly-coupled pieces in one time zone; the cross-zone seams must be
  the most stable contracts.
- **What the manager owns personally**: the contracts, the dependency graph, the integration milestones,
  and the escalation path when two teams disagree. **A candidate who assigns all the work and reserves
  nothing for themselves has not understood the question.**
- **Integration risk handled early** — an end-to-end skeleton in the first weeks rather than an
  integration phase at the end, because integration-last is how six-month programmes slip.
- **Not over-decomposing**: five teams do not require twelve services, and premature service
  boundaries are expensive to move.

**Probe ladder:**
- *Requirements:* "What are you optimising the split for?" (independent delivery, usually) · "What would
  make you use fewer teams?"
- *Estimation:* "5 teams × 6 months. What's your engineer-month budget and what does that buy?"
- *Design:* "Draw the team-to-component map, and mark every arrow where two teams must agree."
- *Deep dives:* **"Which team is on the critical path, and what do the other four do while they
  work?"** · "Team C needs Team B's API in month two, and B won't have it until month four. What do you
  do?" · "Who owns the shared data model, and what happens when two teams need incompatible changes to
  it?" · "Two teams disagree on a contract and both escalate to you. Walk me through the conversation."
  · "Six months in, one team is 2 months behind. What do you change?"
- *EM bar:* "What do you personally own that you would not delegate?" · "How do you know in month two
  that the decomposition is wrong?" (integration friction, cross-team PRs, meeting load — leading
  indicators) · "How would you get this wrong?" (a genuinely revealing question — a strong answer names
  its own failure mode)

**Curveball:** *"You lose one team entirely to a reorg at month three."* Tests whether the
decomposition degrades gracefully or whether losing a team orphans a component, and whether they
re-plans by cutting scope rather than by spreading everyone thinner.

**Weak / Strong / Exceptional.** *Weak* — splits by technical layer, assigns components, no contract
policy, integration at the end, nothing reserved for themselves. *Strong* — domain/vertical seams with
Conway's law reasoning, contracts versioned up front with mocks to unblock, explicit dependency graph,
shared-component ownership named, integration skeleton early. *Exceptional* — chooses org and
architecture together as one decision, matches risk to team experience, designs cross-time-zone seams
to be the most stable, names their own non-delegable responsibilities, defines leading indicators that
the split is wrong, and resists over-decomposition.

---

### SD-60 · Platform consolidation / tech-debt strategy   [T2 · MS A G]

**Read aloud:** *"Your org has four internal platforms doing roughly the same job, each with a team and
its own users. You've been asked to consolidate. How?"*

**Crux.** **Migration incentive, not technical merit.** Choosing the surviving platform is the easy
part; getting dozens of unwilling teams to move is the whole job, and it is done by making the new path
cheaper for *them*, not by mandate. A candidate whose answer is "announce a deprecation date" has not
done this before.

**Numbers if asked:** 4 platforms, 60 consumer teams distributed unevenly (one platform has 5 users,
another has 30), each platform has 3–8 engineers, all four have committed roadmaps, two have vocal
internal champions, the consolidation is expected to free ~15 engineers.

**Listen for:** **evaluation criteria set before picking a winner** — adoption, capability coverage,
operational maturity, migration cost for consumers — and the acknowledgement that the technically-best
platform may lose to the one with 30 users because **migration cost dominates** · the possibility that
the answer is **a new fifth thing** and why that is usually a trap (now five platforms) · **making
migration nearly free**: compatibility shims, automated code migration, running both during transition,
a migration team that does the work *for* consumers rather than filing tickets against them ·
**per-consumer migration tracking** with a real owner and a burn-down · **deprecation with teeth but
with a path**: freeze new adoption immediately (cheap and high value), then remove capacity, then a
date · **the people dimension** — the losing platform's team is being told their work is ending, and
retention/redeployment is the hardest part of this problem and the thing an EM must address explicitly
· **what "done" means**, including deleting the old platform, since a consolidation that leaves all four
running has increased cost · **keeping the surviving platform's roadmap moving** so consumers don't
regress.

**Probes:** *"How do you choose, and what if the best platform has the fewest users?"* · *"Thirty teams
have no incentive to migrate. What actually makes them?"* · *"A senior engineer who built platform C
argues publicly that consolidating is a mistake. What do you do?"* · *"When is it right to keep two?"*
(a good answer exists — genuinely different requirements) · *(EM bar)* *"What do you tell the teams
being disbanded, and when?"*

**Weak / Strong / Exceptional.** *Weak* — pick the best one technically, announce a deprecation date,
expect teams to migrate. *Strong* — explicit criteria weighted by migration cost, freeze-then-migrate
sequencing, shims and automation, tracked burn-down, honest handling of the affected teams.
*Exceptional* — treats consumer migration cost as the dominant term, invests in doing the migration for
people, defines done as deleting the old systems, handles the champion politically and the displaced
engineers humanely, and can name the case for keeping two.

---

### SD-61 · Incident → design fix   [T2 · INVERTED · A★ G N]

**Read aloud:** *"Here's the timeline of an incident that happened last week on a system you now own.
Take me through your read of it — what went wrong, and what you'd change."*

**The artifact — paste this in verbatim:**

> **Incident 4471 — Checkout unavailable, 47 minutes**
>
> - **14:02** A config change is deployed to the Pricing service, raising a cache TTL from 60 s to
>   3600 s. Change was reviewed by one engineer, deployed to all regions at once.
> - **14:03** Pricing latency drops (cache hit ratio up). No alerts.
> - **14:19** A promotion campaign starts. New prices are written to the Pricing database.
> - **14:20** Checkout begins returning stale prices. No alerts — prices are "valid", just old.
> - **14:26** Customer support receives the first complaints about wrong prices at checkout.
> - **14:31** Support escalates to engineering via a Slack channel. No one is on call for Pricing;
>   the rotation was for Checkout only.
> - **14:38** An engineer notices and starts investigating Checkout, not Pricing.
> - **14:49** The engineer finds the Pricing deploy in the deploy log and asks the deploying engineer,
>   who is at lunch.
> - **14:58** The config change is reverted. Caches still hold stale entries.
> - **15:04** Someone manually flushes the Pricing cache. Prices correct.
> - **15:15** Incident closed. ~4,100 orders placed at incorrect prices; ~$180k in
>   under-charges honoured.
> - **Follow-up action recorded:** *"Add an alert for cache TTL config changes."*

**Planted findings — the answer key:**

| # | Finding | Tier |
|---|---|---|
| 1 | **The recorded follow-up is the wrong fix** — narrow, specific to this trigger, and would not have caught this incident sooner (the TTL change wasn't the failure; the *undetectable staleness* was). This is the central test of the round: **can they tell a symptom fix from a systemic one?** | **must-find** |
| 2 | **No alert on data correctness.** 18 minutes of wrong prices with every system reporting healthy. The missing SLI is price freshness/correctness, not infrastructure health | **must-find** |
| 3 | **No on-call for Pricing.** Detection depended on customer complaints and escalation went through Slack. Ownership gap, not a technical gap | **must-find** |
| 4 | **A config change deployed to all regions at once** with single review — no staged rollout, no bake, no automatic revert (links to SD-35) | **must-find** |
| 5 | **Revert didn't fix it** — reverting the TTL left stale entries in the cache. Rollback wasn't sufficient for recovery, which is a design defect: a config revert must have a defined path back to a correct state | should-find |
| 6 | 24 minutes from first customer complaint to correct diagnosis, spent looking at the wrong service — no correlation between the deploy log and the symptom, and no dependency-aware view | should-find |
| 7 | Detection time (18 min) and diagnosis time (23 min) both dwarf the fix time (6 min), so **investment should go to detection and diagnosis, not to prevention of this specific change** | should-find |
| 8 | "Engineer at lunch" is a single-point-of-knowledge dependency, and blaming it is a people-fix for a process problem | nice-to-find |
| 9 | $180k and 4,100 customers gives the business weight to justify the real fixes — a strong candidate uses the number when arguing for investment | nice-to-find |
| 10 | **A blameless framing** — the reviewer, the deployer and the engineer at lunch all behaved reasonably inside a system that permitted this. If they criticise individuals, that is a genuine negative signal for an EM | **the 4-signal** |

**Probes:** *"What's the single change that would have most reduced the impact?"* (detection — an alert
on price freshness) · **"The recorded follow-up is 'alert on TTL config changes'. What do you think of
it?"** (the core probe) · *"Break the 47 minutes into detect, diagnose, fix. Where do you invest?"* ·
*"Whose fault was this?"* (a deliberate trap — the right answer refuses the framing and points at the
system) · *(EM bar)* *"You have capacity for two follow-up actions, not ten. Which two, and how do you
tell the team the other eight aren't happening?"*

**Weak / Strong / Exceptional.** *Weak* — accepts the recorded follow-up, adds more alerts on the
specific trigger, attributes the delay to the engineer at lunch. *Strong* — identifies the missing
correctness SLI, the ownership gap, and the unstaged config rollout; splits the timeline into
detect/diagnose/fix and prioritises accordingly. *Exceptional* — rejects the recorded follow-up with
reasoning, notices that revert didn't restore correctness, uses the financial impact to fund the real
fixes, ruthlessly prioritises two actions, and keeps the analysis blameless throughout.

---

### SD-62 · Build vs buy   [T2 · MS A G]

**Read aloud:** *"Your team needs [a workflow engine / an observability stack / a feature-flag system].
Do you build it or buy it? Walk me through the decision."*

**Crux.** **Total cost of ownership over years versus differentiation**, plus the exit cost nobody
computes. The signal is a structured, quantified decision — not a preference. **A candidate who always
builds is expensive; one who always buys has no view on what makes the company distinctive.**

**Context if asked:** the vendor costs $400k/year growing with usage; building is estimated at 3
engineers for 6 months; the capability is needed in 4 months; it is not the company's product; ~20
internal teams would use it; the vendor is a startup; and there is an open-source option requiring
self-hosting.

**Listen for:** **is this differentiating?** — build what makes you distinctive, buy what everyone
needs; and the honesty that most infrastructure is not differentiating · **TCO over 3 years, not the
build estimate**: the 3×6 build estimate is the *first* version, and ongoing cost is typically 30–50%
of a maintainer's time forever, plus on-call, plus the features you'll be asked for — **the ongoing
cost is the term candidates systematically omit and the best thing to probe** · **the third option** —
open-source self-hosted — as its own TCO calculation, often the right answer and often
under-considered · **time to value** against the 4-month need, and that buy-now-build-later is a valid
sequence · **exit cost / lock-in**: what it takes to leave, and whether the abstraction boundary makes
that cheaper (an adapter layer as insurance, with the caveat that a leaky abstraction over a rich
product is its own cost) · **vendor risk** — a startup vendor may be acquired or die, so what's the
contingency · **the team dimension**: do they *want* to build it, will it grow them, and is it a
retention factor or a distraction · **data gravity and compliance** as constraints that can decide it
outright · a decision **framed as reversible or not**, with a review date.

**Probes:** *"What's the 3-year TCO of each option? Show me the arithmetic."* · *"Your build estimate is
3 engineers for 6 months. What's the annual cost after it ships?"* · *"What would make you change this
decision in 12 months, and what would you have to have done now to make changing cheap?"* · *"The
vendor is a startup and gets acquired next year. What's your plan?"* · *(EM bar)* *"Your best engineer
wants to build it and will be disappointed if you buy. How do you handle that?"*

**Weak / Strong / Exceptional.** *Weak* — a preference stated with anecdote; build estimate treated as
total cost; no exit consideration. *Strong* — differentiation test, 3-year TCO including maintenance
and on-call, open-source considered as a third option, time-to-value against the deadline, lock-in and
vendor risk addressed. *Exceptional* — quantifies ongoing cost as the dominant term, sequences
buy-now-build-later where that fits, prices the exit and buys cheap insurance at the boundary, decides
with a review date, and handles the team's motivation openly.

---

## Senior-manager & director expansion — SD-89 – SD-92

*Added for `senior-em` and `director` loops. At these levels the "system design" round is often a
**technical-strategy conversation**: the interviewer wants to see how you allocate a scarce budget of
people, money and risk across several systems — and whether your architecture opinions survive contact
with an org chart. **Box-level depth is not the point; decisions, sequencing and the org shape are.**
Score Leadership signal and Ops/cost at High weight (`levels.md` §2).*

---

### SD-89 · Engineering org & architecture for a new product line   [T1 · G MS A]

**Read aloud:** *"The company is launching a new product line — a B2B version of our consumer product.
You'll lead its engineering: you have budget for about 40 engineers over 18 months. Design the
architecture and the organisation that builds it."*

**Crux.** **Conway's law, used deliberately.** The architecture and the team topology are one decision:
what to **reuse from the consumer platform** (and the coupling that creates), what to **build new**,
and how to **shape teams so their boundaries match the system's seams**. Sequencing hiring against an
18-month plan, and keeping the consumer product safe, are the risk dimensions.

**If they ask:**

| Question | Answer |
|---|---|
| Product? | Same core experience plus SSO, admin console, audit logs, data residency (EU), SLAs, invoicing |
| Existing platform? | Consumer product built by 120 engineers; shared identity, billing and storage services |
| Timeline? | A design-partner beta in 6 months, general availability in 15 |
| People? | 8 engineers transfer in now; 32 to hire; 2 experienced managers available |
| Constraints? | The consumer org is protective of its platform and on-call; enterprise customers demand 99.95% |

**Listen for:**
- **Reuse vs fork decided per capability**: reuse the core product surfaces and shared services, build
  enterprise-specific capabilities (tenancy, admin, audit, residency) — with an explicit **contract**
  with the consumer platform teams, not ad-hoc requests.
- **Multi-tenancy model** chosen deliberately (shared with tenant isolation vs cells per region for
  residency), and its consequences for the consumer stack.
- **Team topology**: stream-aligned teams per enterprise capability, maybe a small enablement or
  platform-liaison team, cognitive load per team, and **teams staffed before the work that needs them
  — sequenced hiring**.
- **Phased plan**: thin beta with design partners (manual where possible) → harden for GA; what is
  deliberately manual or deferred in the beta.
- **Risk to the consumer product**: changes to shared services go through the owners; reliability
  isolation so enterprise SLAs don't impose on consumer on-call without agreement.
- **Metrics**: beta adoption, time-to-onboard a tenant, SLA attainment, cost per tenant.
- **Leadership**: two managers placed where the risk is; hiring bar and onboarding plan; how decisions
  are made across the two orgs.

**Probe ladder:**
- *Requirements:* "What has to be true at beta versus GA?" · "What's out of scope for the first 6 months?"
- *Estimation:* "40 engineers, 32 not hired yet — how many are actually productive at month 6?" (hiring
  lag and ramp-up: maybe 15–18 effective) **— does that change the beta scope?**
- *Design:* the architecture on one page and the team map beside it.
- *Deep dives:* **"The consumer identity team says SSO isn't on their roadmap for a year. What now?"** ·
  "A design partner needs EU data residency for beta. What does that do to your architecture and your
  plan?" · "Hiring is 40% behind at month 5. What do you cut?" · "Who is on call for a shared service
  outage that only hurts enterprise customers?"
- *Director bar:* "How do you report progress to the exec team — what three numbers?" · "What would make
  you recommend not doing GA in 15 months?"

**Curveball:** *"The CEO asks you to also support a large customer's on-premise deployment for the GA
deal."* Tests whether they price that as a strategy change (a second deployment model) rather than a
feature, and push back with the cost.

**Weak / Strong / Exceptional.** *Weak* — an architecture diagram with no org, or an org chart with no
architecture; hire 40 and start. *Strong* — per-capability reuse/build with contracts, a tenancy model,
teams aligned to seams, sequenced hiring against a phased plan, consumer-risk isolation. *Exceptional* —
designs teams and system boundaries as one decision, uses effective capacity (not headcount) to scope
the beta, negotiates the platform dependency as an agreement with incentives, and names the conditions
under which they'd change the plan.

**Traps.** Assuming hires are productive on arrival. Forking the consumer platform wholesale. Treating
shared-service teams as vendors who must comply.

---

### SD-90 · The reliability program after a major outage   [T2 · A★ G N]

**Read aloud:** *"Last month the company had a nine-hour outage that made the news. The CEO asks you to
lead a reliability program across eight engineering teams. What do you do in the first 90 days, and
what does the program look like after that?"*

**Crux.** **Turning one dramatic incident into systemic improvement without a year of freeze and
theatre.** The program must stabilise now, fix the specific failure, find the **class** of failures,
and create **lasting mechanisms** — SLOs, error budgets, review practices — while keeping product
delivery alive and keeping trust with an anxious exec team.

**Context if asked:** the outage was a configuration change propagated globally that took down
authentication, and recovery was slow because the rollback path depended on the failed system; 8
teams; no SLOs today; incident reviews are inconsistent; the board wants a monthly update; product
leadership fears a feature freeze.

**Listen for:** **first weeks**: finish the incident review blamelessly and fix the specific chain
(staged config rollout, rollback independent of the failed dependency) · **find the class**: audit
other global-blast-radius changes and circular recovery dependencies across all 8 teams · **mechanisms**:
SLOs on critical user journeys, error budgets with an agreed policy, progressive delivery for code
*and* config, game days for recovery paths · **governance**: a small reliability review, not a central
approval bottleneck · **balancing delivery**: a time-boxed percentage of capacity or error-budget-driven
trade-offs instead of a blanket freeze · **reporting**: leading indicators (change failure rate, MTTR,
budget burn, % of changes staged) rather than "number of incidents" · **people**: on-call health and
not making engineers fear deploying.

**Probes:** *"The CEO wants a full freeze until it's fixed. What do you say?"* · *"What will you report
at the first board update?"* · *"Two of eight teams say reliability isn't their problem — they've had no
incidents."* · *"How will you know in six months whether this worked?"* · *(Director bar)* *"What's the
budget for this, and what are you not doing because of it?"*

**Weak / Strong / Exceptional.** *Weak* — freeze, add approvals, count incidents. *Strong* — fix the
chain, find the class, SLOs and error budgets, staged config, recovery drills, capacity allocation,
leading indicators. *Exceptional* — targets blast radius and recovery independence as the systemic
themes, designs governance that scales without a bottleneck, and manages executive trust with honest
leading metrics.

---

### SD-91 · Annual planning — roadmap, headcount and platform investment   [T2 · G MS A]

**Read aloud:** *"You run engineering for a product area: five teams, about 45 engineers. Product has
asked for 14 major initiatives next year; you have capacity for maybe six. You also believe the
platform underneath needs serious investment. Walk me through how you build the plan."*

**Crux.** **Capacity is the constraint, and the platform investment is the argument you must win in
business terms.** A strong answer builds a **real capacity model** (KTLO, on-call, attrition, hiring
lag), forces **explicit trade-offs** with product rather than accepting all 14, and justifies platform
work by **the delivery and risk outcomes it buys**, not engineering preference.

**Context if asked:** 45 engineers, ~30% of capacity goes to keeping the lights on and on-call; platform
debt is slowing every feature (lead time doubled in two years); 6 open reqs approved; attrition ~12%;
product's 14 initiatives have rough sizes; leadership wants a revenue-linked story.

**Listen for:** **capacity model**: 45 × (1 − KTLO 30%) minus attrition and hiring ramp → roughly 25–28
engineer-years of new work · **sizing the asks** at coarse granularity with uncertainty ranges ·
**prioritisation with product** by outcome, cost and risk, with explicit "not this year" decisions
written down · **platform investment framed as a business case**: lead time, incident cost, the
features it unblocks, and a staged investment with checkpoints rather than "20% for platform" ·
**protected allocation** for KTLO and reliability · **contingency** buffer · **communicating the
plan**: what each stakeholder gets, quarterly re-planning, and the signals that trigger a change.

**Probes:** *"Product says all 14 are must-haves. What happens next?"* · *"Show me the arithmetic for
your capacity."* · *"Your CFO asks what the platform investment returns. Answer in one minute."* · *"Two
months in, two senior engineers leave. What changes?"* · *(Director bar)* *"How do you avoid this being
negotiated team by team in a way that loses the platform investment?"*

**Weak / Strong / Exceptional.** *Weak* — accepts 14, or allocates a flat percentage to "tech debt" with
no case. *Strong* — capacity model with KTLO and hiring lag, prioritised trade-offs agreed with product,
platform work justified by outcomes, contingency, quarterly re-plan. *Exceptional* — makes the
not-doing list a shared artifact owned with product, ties platform investment to measurable delivery
improvements with staged checkpoints, and plans for attrition explicitly.

---

### SD-92 · Cloud, vendor and multi-region strategy   [T2 · A MS G N]

**Read aloud:** *"Your company runs on one cloud provider in one region. Leadership is asking three
things at once: cut infrastructure cost by 25%, survive a full regional outage, and reduce dependence on
the provider. You lead the infrastructure organisation. What's your recommendation?"*

**Crux.** **The three asks conflict**, and the job is to make that visible and choose. Multi-region
raises cost; multi-cloud raises cost and complexity far more; cost cuts compete with redundancy. A strong
answer **separates the asks, quantifies each**, and recommends a sequence — usually **cost discipline
first, multi-region for the critical tier, and portability only where lock-in risk is real.**

**Context if asked:** $30M/year infrastructure spend; ~35% of compute idle or over-provisioned; a regional
outage last year cost ~$4M in revenue; a few critical services, many internal ones; heavy use of the
provider's proprietary managed services; a renewal negotiation in 9 months.

**Listen for:** **cost first**: rightsizing, commitments/reservations, storage tiers, killing idle
resources, per-team attribution — often the 25% is mostly here · **tier services by criticality** and
apply multi-region (active-passive or active-active) **only to the critical tier**, with honest data
replication and failover testing · **multi-cloud scepticism**: lowest-common-denominator cost, the
real risk being addressed (pricing power? outage? regulation?), and cheaper hedges — portable data
formats, containerisation where cheap, exit plan documented, **using the renewal as negotiation
leverage** · **quantify**: cost of downtime vs cost of redundancy · **sequencing over 12–24 months**
with milestones · **organisational ownership**: FinOps practice, team-level budgets.

**Probes:** *"Multi-region will raise spend. How do you also cut 25%?"* · *"The CTO wants active-active
multi-cloud. What do you say?"* · *"What's your failover test cadence, and what happens the first time?"*
· *"How do you use the renewal?"* · *(Director bar)* *"Which of the three asks do you push back on, and
how do you say it to the exec team?"*

**Weak / Strong / Exceptional.** *Weak* — "go multi-cloud" or "go multi-region everywhere" without
numbers. *Strong* — separates and quantifies the asks, cost programme first, tiered multi-region,
targeted portability, failover testing, sequenced roadmap. *Exceptional* — exposes the conflict
explicitly with numbers, recommends what not to do (blanket multi-cloud), uses commercial leverage as
part of the architecture strategy, and makes cost ownership a team-level habit.
