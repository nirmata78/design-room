# Archetype K · Staff+ technical-leadership rounds

**SD-83 – SD-88.** Slice with `grep -n '^### SD-84' questions/K-staff-technical-leadership.md`, then
Read with `offset`. Do not read this file whole.

**Read this before running any question in this archetype.**

Archetype H holds the rounds an **engineering manager** faces that aren't "design X". This archetype
is its counterpart for the **IC track at Staff, Senior Staff and Principal**: technical strategy,
reviewing an API, killing a system nobody owns, deciding whether to rewrite, finding a performance
regression, and arbitrating between two teams' designs. **The skill under test is technical judgment
exercised through other people** — no reporting line, so every outcome depends on the quality of the
reasoning and the way it is communicated.

Managers meet these too (a senior EM or director loop often includes SD-83 or SD-85), but the bar
differs: **from a Staff candidate the panel expects the technical argument to be decisive on its own
merits**; from a manager it expects the organisational path to be credible. Score against the
target level in `levels.md`.

**Two of the six invert the round: you present an artifact and they respond** (SD-84, SD-87). The rules
are the same as archetype H's (see the top of `H-em-specific-rounds.md`): paste the artifact, never
confirm a find, score prioritisation over enumeration, score tone, and reveal the planted list only at
debrief.

---

### SD-83 · Technical strategy — a three-year direction for a platform   [T1 · G★ MS A]

**Read aloud:** *"You're the senior technical lead for the company's data platform: a warehouse, a
streaming system, and about forty pipelines owned by different teams. Leadership asks you for a
three-year technical direction. Walk me through how you'd build it and what it would say."*

**Crux.** **A strategy is a diagnosis plus a small number of bets, with explicit things you will not
do.** Weak answers are a wish list of technologies. Strong answers start from **the problems the
business actually has** (evidence), pick **two or three bets** with sequencing and decision points, say
**what to stop**, and describe how the direction gets adopted without authority.

**Context if asked:**

| Question | Answer |
|---|---|
| Pain today? | Pipelines break weekly; data freshness is hours; nobody trusts the numbers; costs grew 70% last year |
| Teams? | 12 teams produce data, 30 consume it; a central platform team of 8 |
| Constraints? | No headcount increase next year; a compliance deadline for data deletion in 18 months |
| Stack? | A cloud warehouse, a self-hosted streaming cluster, a home-grown orchestrator from 2018 |
| Leadership wants? | "AI-ready data" — undefined |

**Listen for:**
- **Diagnosis before prescription**: gathering evidence (incident history, cost breakdown, a survey of
  consumers, freshness by dataset) and naming the **root problem** — e.g. *no ownership or contracts
  between producers and consumers*, not "old technology".
- **A few bets, sequenced**: e.g. (1) data contracts and ownership with quality checks at the producer,
  (2) retire the home-grown orchestrator, (3) a cost model with per-team attribution — each with a
  measurable outcome and a decision point. **← The senior insight: the strategy's value is mostly in
  what it says *no* to.**
- **Translating the vague ask**: "AI-ready" turned into concrete properties (documented, fresh, governed,
  deletable) rather than accepted or dismissed.
- **The compliance deadline** used as a forcing function and sequencing anchor.
- **Adoption path without authority**: paved road, migration tooling, early adopters, deprecation
  timelines agreed with consumers, metrics that make progress visible.
- **Reversibility**: which bets are one-way doors and get more scrutiny.
- **Communicating it**: a short written doc, the audience for each layer (exec summary vs team-level
  plan), and a review cadence.

**Probe ladder:**
- *Requirements:* "Who is the customer of this strategy?" · "What would make it a failure in two years?"
- *Estimation:* "With eight platform engineers and no new headcount, how much can you actually change
  per year?" — capacity as a constraint on the number of bets.
- *Design:* "Give me the one-page version: diagnosis, bets, what we stop."
- *Deep dives:* **"Three of the twelve producer teams refuse data contracts — they say it slows them
  down. What now?"** · "Leadership wants a big-bang migration to a new vendor platform. You think it's
  wrong. How do you disagree?" · "Halfway through year one, costs keep rising. Which bet do you
  revisit?" · "How will you know the strategy is working at month six?"
- *Staff bar:* "Which part of this would you personally build, and which would you delegate?" ·
  "What's the decision you most expect to be wrong about?"

**Curveball:** *"The company announces an acquisition; their data platform is a completely different
stack, and integration is expected within a year."* Tests whether the strategy has principles that
survive a new constraint, or only a technology list.

**Weak / Strong / Exceptional.** *Weak* — a technology wish list (new lakehouse, new streaming, new
orchestrator), no evidence, no sequencing. *Strong* — evidence-based diagnosis, two or three sequenced
bets with outcomes, what to stop, adoption plan, capacity-aware. *Exceptional* — makes the trade-offs
explicit and contestable, uses the compliance deadline as leverage, names the decision most likely to
be wrong and how it would be detected, and writes the strategy so teams can make local decisions
consistent with it.

**Traps.** Leading with tools. Strategy without capacity. Ignoring the people who must adopt it.

---

### SD-84 · API design review   [T1 · INVERTED · G★ MS A]

**Read aloud:** *"Another team is about to publish this API to external developers. Once it ships, we
support it for years. They've asked you for a review. What do you raise, and in what order?"*

**Crux.** **Public APIs are one-way doors.** A strong reviewer separates defects that become permanent
once external clients depend on them (resource model, identifiers, idempotency, pagination, error
contract, versioning) from those that are cheap later (naming nits, extra fields). Ranking is the skill.

**The artifact — paste this in verbatim:**

> **Payments API v1 — draft for review** *(Team Ledger, v0.9)*
>
> ```
> POST /createPayment
>   body: { "amount": 10.50, "currency": "usd", "customer": "jane@example.com",
>           "card": { "number": "...", "cvc": "...", "exp": "12/27" } }
>   200: { "id": 18273, "status": "ok" }
>   500: { "error": "something went wrong" }
>
> GET /getPayments?customer=jane@example.com
>   200: [ { ...every payment for this customer, all fields... } ]
>
> POST /refundPayment/{id}
>   body: { "amount": 10.50 }
>   200: { "status": "ok" }
>
> PUT /payment/{id}
>   body: full payment object — clients may change amount or currency until it settles
>
> Webhooks: we POST { "id": 18273, "status": "PAID" } to the client's URL when status changes.
> We retry once after 60 seconds.
>
> Auth: API key in the query string, ?key=...
> Versioning: we will add fields as needed and remove unused ones after 3 months.
> ```

**Planted defects — the answer key. Do not reveal until debrief.**

| # | Defect | Why it matters | Severity |
|:-:|---|---|---|
| 1 | **No idempotency on `createPayment` / `refundPayment`** — a client retry after a timeout charges twice | Money correctness; impossible to retrofit without every client changing | **must-raise** |
| 2 | **`amount` as a float** | Rounding errors in money; use integer minor units + currency | **must-raise** |
| 3 | **Raw card data in the request body** | Puts every client and this service in full PCI scope; tokenisation should exist | **must-raise** |
| 4 | **Sequential integer IDs** | Enumerable (other customers' payments discoverable), leaks volume, hard to shard/merge; use opaque IDs | high |
| 5 | **`getPayments` unbounded, no pagination, filtered by email** | Breaks at scale, can't be fixed without breaking clients; email as a key is PII in URLs and not stable | high |
| 6 | **`PUT` allowing amount/currency change** | Mutating a financial record; should be cancel + create, or explicit capture/adjust operations | high |
| 7 | **Error contract**: one generic 500, no machine-readable codes | Clients can't distinguish retryable from non-retryable — leads to double-charges and stuck states | high |
| 8 | **Webhooks**: one retry, no signature, no event ID or ordering info | Lost events and spoofable notifications; clients need to verify, dedupe and re-fetch | high |
| 9 | **API key in query string** | Logged everywhere (proxies, browser history); use a header | medium |
| 10 | **Versioning policy**: removing fields after 3 months | Breaking change on a public API; needs explicit versioning and long deprecation | medium |
| 11 | **RPC-style verb URLs** (`/createPayment`) and status `"ok"` vs `"PAID"` inconsistency | Cheap now, inconsistent forever; lower priority than the above | low |

**Listen for:** they rank 1–3 at the top (money and compliance), recognise the "one-way door" framing,
propose concrete fixes (idempotency keys with stored responses, minor units, tokenised payment methods,
cursor pagination, typed error codes with retryability, signed webhooks with event IDs and redelivery,
explicit versions), and **ask about context** — who the clients are, what exists elsewhere in the
company (an existing tokenisation service?). Tone: a review that the author team would act on.

**Probes:** *"If they can only fix three things before launch, which three?"* · *"They push back: 'idempotency
keys are extra work for clients'. What do you say?"* · *"How would you have caught these earlier than
a review a week before launch?"* (API guidelines, linting, design-review stage) · *"Which of these is
cheap to fix after launch?"* · *(Staff bar)* *"This team doesn't report to you and is under deadline
pressure. How do you make sure the must-fix items actually get fixed?"*

**Weak / Strong / Exceptional.** *Weak* — naming and REST-style nits first, misses idempotency or the
float. *Strong* — finds the money/compliance defects and the permanent contract defects, ranks them,
gives concrete fixes. *Exceptional* — frames the review by reversibility, proposes a short launch-gating
list plus a follow-up list, suggests systemic prevention (API standards and a linter), and handles the
influence problem without authority.

---

### SD-85 · Deprecating a widely used internal system   [T2 · G MS A]

**Read aloud:** *"An internal configuration service from 2016 is used by 140 services across 35 teams.
It's unowned, it causes an incident every couple of months, and there's a newer replacement nobody is
migrating to. You've been asked to get rid of it. How?"*

**Crux.** **Deprecation is a migration you can't mandate.** The technical part — a compatibility layer,
dual-read, automated migration — is the smaller half. The larger half is **making the new path cheaper
than staying**, sequencing teams, and handling the long tail that never moves.

**Context if asked:** 140 consumers, ~20 of them critical-path; 6 use undocumented behaviours; the
replacement lacks 2 features some consumers need; no team has spare capacity; leadership will support a
deadline but not headcount; the old system's original authors have left.

**Listen for:** **inventory first** — who calls what, how (traffic analysis, not a survey) · **close the
feature gap** before asking anyone to move · **reduce migration cost to near zero** — client library
shim, automated codemods/PRs, a compatibility proxy that serves old API from the new backend ·
**sequencing**: easy volunteers first for proof, critical-path last with extra support, undocumented
behaviours handled explicitly · **making staying expensive** — freeze new consumers, then brownouts or
rate limits announced in advance, then a hard date · **tracking dashboard** of remaining consumers
visible to leadership · **owning the old system's reliability meanwhile** · the **long tail** —
the last 5% handled by doing it for them.

**Probes:** *"Twenty teams say 'not this quarter'. What do you do?"* · *"One consumer relies on a bug in
the old system. What now?"* · *"How do you know you've found every consumer?"* · *"When do you do the
first brownout, and what could go wrong?"* · *(Staff bar)* *"How much of this do you do yourself versus
convince others to do?"*

**Weak / Strong / Exceptional.** *Weak* — announce a deadline and send an email. *Strong* — traffic-based
inventory, feature parity first, automated migration tooling, sequencing, freeze then brownouts,
tracking. *Exceptional* — makes migration cost near zero with a compatibility layer, handles the long
tail by doing the work, and uses the incident history to build the case without blaming the past owners.

---

### SD-86 · Rewrite vs refactor   [T2 · G MS A N]

**Read aloud:** *"Your team's core service is a six-year-old monolith that everyone hates. Half the team
wants to rewrite it from scratch in a new language. You have to make the call — and defend it."*

**Crux.** **Rewrites fail by underestimating the implicit requirements the old system encodes** and by
delivering no value until they are done. A strong answer reframes the question into **incremental
replacement with value at each step** (strangler pattern), unless there is a concrete reason the old
foundation cannot carry the future — and shows how to tell the difference with evidence.

**Context if asked:** 300k lines, 40% test coverage, deploys weekly with frequent rollbacks, a key
product launch in 9 months depends on it, the language runtime is still supported, two engineers know
the scary parts, and the team believes velocity has halved in two years.

**Listen for:** **diagnose the pain** precisely (deploy safety? coupling? a specific module? performance?
hiring?) with data — change failure rate, lead time, hotspots · **the hidden requirements** argument —
years of bug fixes and edge cases nobody documented · **strangler fig**: carve out the highest-pain or
highest-change module behind an interface, route traffic gradually, verify with shadow comparison ·
**improve the pipeline first** (tests around hotspots, deploy safety) because it pays off either way ·
**the launch constraint** — a rewrite competing with a 9-month launch is a red flag · **criteria under
which a rewrite is right** (unsupported platform, fundamental model mismatch, small well-specified
system) · **the team dimension** — motivation, knowledge concentration in two people.

**Probes:** *"What evidence would change your mind towards a rewrite?"* · *"How do you verify the new
module behaves the same as the old one?"* · *"The two experts want the rewrite. What do you do?"* · *"Six
months in, the strangler is 30% done and leadership asks when it'll be finished."* · *(Staff bar)*
*"Write me the one-paragraph decision record."*

**Weak / Strong / Exceptional.** *Weak* — picks a side on taste. *Strong* — diagnoses with data,
proposes incremental replacement with shadow verification, protects the launch, states rewrite
criteria. *Exceptional* — sequences by pain × change frequency, invests first in what pays off in both
futures, and turns the decision into a reversible, reviewable record the team can disagree with.

---

### SD-87 · Performance investigation — the p99 regression   [T1 · INVERTED · G★ M A]

**Read aloud:** *"I'm going to show you what an on-call engineer sees. Talk me through your
investigation: what you look at, what you conclude, and what you'd change."*

**Crux.** **Disciplined diagnosis from evidence.** The candidate gets data, not a design prompt. The
skill is forming hypotheses, asking for the right next piece of evidence, ruling things out, and
separating the immediate mitigation from the real fix. It reveals depth faster than any design round.

**The artifact — paste this in, then answer their questions from the hidden facts below:**

> **Service:** `catalog-api` — product lookups for the storefront. ~12k req/s.
>
> **Symptom:** since Tuesday 14:10, p99 latency rose from 45 ms to 380 ms. p50 unchanged at 12 ms.
> Error rate unchanged. CPU on the API fleet unchanged at ~40%.
>
> **Recent changes:** Tuesday 14:00 — deploy of `catalog-api` v4.12 (changelog: "add product badges
> to response"; "bump HTTP client library"). Tuesday 13:30 — cache cluster resized from 12 to 16 nodes.
>
> **Dashboards available on request:** per-endpoint latency, cache hit rate, DB query latency, GC
> pauses, downstream call latency, per-instance latency, request size distribution.

**Hidden facts — reveal only when asked for the matching evidence. This is the answer key.**

| If they ask for… | They see |
|---|---|
| Per-endpoint latency | Only `GET /products/{id}` regressed; `/search` is fine |
| Cache hit rate | Dropped from 97% to 91% at 13:30, recovering slowly to 95% by Wednesday — **a red herring that partially matters** |
| DB query latency | Flat |
| GC pauses | Flat |
| Downstream call latency | A new call to `badge-service` appears at 14:10: p50 3 ms, **p99 340 ms** |
| Per-instance latency | Uniform across instances |
| Request size | Unchanged |
| `badge-service` details | Owned by another team; called **sequentially** after the product fetch; client has **no timeout configured** (new HTTP library default is 30 s); badge-service p99 is dominated by its own cold cache for long-tail products |

**The answer.** The regression is the **new sequential call to `badge-service`** without a timeout or
fallback, whose long tail lands directly on the p99. The cache resize is a **correlated distraction** —
it moved hit rate and contributed a little, but timing and the per-endpoint split point to the deploy.
**Mitigation:** feature-flag badges off or add an aggressive timeout with a badge-less fallback.
**Real fix:** call badge-service in parallel with the product fetch, set a timeout budget derived from
the endpoint SLO, treat badges as optional decoration, and ask the badge team about their long-tail
cache. **Systemic fix:** a client-library default timeout, a dependency-latency check in the deploy
canary, and p99 (not only p50) in canary analysis.

**Listen for:** asks for **per-endpoint** and **downstream** data early · notices **p50 flat / p99 up**
means a tail problem, not throughput · treats two simultaneous changes as **competing hypotheses** and
uses timing and scope to separate them · mitigates **before** root-causing fully · finds the missing
timeout and the sequential call · proposes systemic prevention, not only the local fix.

**Probes:** *"What's your first hypothesis, and what evidence would kill it?"* · *"You've found it. It's
3 a.m. What do you do right now, and what waits until morning?"* · *"Why didn't the canary catch this?"* ·
*"How do you handle the fact that the badge team owns the slow part?"* · *(Staff bar)* *"What would you
change so this class of regression can't ship again anywhere in the company?"*

**Weak / Strong / Exceptional.** *Weak* — blames the cache resize or GC without evidence, proposes
scaling up. *Strong* — isolates the endpoint and the new dependency, mitigates first, fixes with
parallelism + timeout + fallback. *Exceptional* — explains the tail-latency arithmetic of sequential
calls, separates mitigation / fix / prevention, and proposes org-wide guardrails (default timeouts, p99
in canary gates).

**Traps for the interviewer.** Don't volunteer data. If they ask for "logs", ask which logs and what
they'd look for.

---

### SD-88 · Arbitrating two teams' competing designs   [T2 · G★ MS A]

**Read aloud:** *"Two teams each wrote a design for the company's new event-notification system. Team A
proposes a central service everyone calls; Team B proposes a shared library plus each team running its
own infrastructure. Both teams are senior and dug in. You're asked to recommend one. How do you run
this, and what would you look at?"*

**Crux.** **The process is as much the answer as the decision.** A Staff engineer is valuable here
because they can make a disagreement **decidable**: agree on criteria first, separate facts from
preferences, find the actual crux (usually one or two assumptions), test it cheaply, and leave both
teams able to commit. Picking a side on taste — even the right side — is a weak answer.

**Context if asked:** 60 consuming services; Team A is a platform team with on-call capacity; Team B is
a product team that needs this in 3 months; reliability requirements vary widely between consumers;
a previous central service from Team A had a major outage last year; both designs are technically
competent.

**Listen for:** **criteria agreed up front** with both teams (reliability, time-to-adopt, operational
load, cost, blast radius, evolution) and their weights tied to company priorities · **find the crux** —
e.g. *"can a central service meet the reliability needs of the critical consumers?"* and *"who is on
call?"* — and resolve it with evidence (a load test, outage history, a spike) · **hybrid options**
(central service with a client library and local fallback; or library now, service later) considered
honestly, not as a compromise for its own sake · **separating people from positions** — acknowledging
the outage history without letting it decide · **a written decision record** with dissent noted ·
**disagree-and-commit** made explicit, and a review point.

**Probes:** *"Team A's lead says the previous outage was a one-off. Team B says it proves central
services are fragile. How do you settle that?"* · *"What's the one experiment that would decide this?"*
· *"Your recommendation goes against the more senior team. How do you deliver it?"* · *"Six months later,
the losing team's concerns come true. What now?"* · *(Staff bar)* *"When should you refuse to arbitrate
and escalate instead?"*

**Weak / Strong / Exceptional.** *Weak* — picks a design on preference, or splits the difference.
*Strong* — agreed criteria, identifies the crux, evidence-based resolution, written decision with
dissent, explicit commit. *Exceptional* — reframes the question so both teams own the criteria, designs
the cheapest decisive experiment, and builds in a review trigger that would reverse the decision if its
key assumption fails.
