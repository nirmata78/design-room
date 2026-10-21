# 8 · Reliability & operations — SLOs, overload, observability, cost

The wrap-up of every round asks the same questions: *what breaks first, how would you know, and what
does it cost?* For manager levels this is where most of the score lives; for Staff it is where
"designs for failure proactively" is demonstrated. This page is the vocabulary and the mechanisms.

---

## SLIs, SLOs and error budgets

- **SLI** (indicator) — a measured ratio of good events to valid events, from the user's point of view:
  *"proportion of feed loads served successfully in under 200 ms"*.
- **SLO** (objective) — the target for the SLI over a window: *"99.9% over 28 days"*.
- **Error budget** — `1 − SLO`: the allowed unreliability (99.9% → ~40 minutes per 28 days). When the
  budget is burning, slow down risky change; when it's healthy, ship faster.
- **SLA** — a contractual promise with penalties; set looser than the SLO.

**Choose SLIs per user journey**, few of them, measured as close to the user as possible:

| Kind | Example SLI |
|---|---|
| Availability | successful responses ÷ valid requests |
| Latency | requests faster than X ms ÷ requests (a threshold, not an average) |
| Freshness | items visible within N seconds of being written ÷ items written |
| Correctness | records reconciled without break ÷ records |
| Delivery | messages delivered to at least one device within N s ÷ messages sent |

{: .say }
> "I'd publish two SLOs: message delivery within two seconds for 99.9% of messages to online
> recipients, measured end to end with synthetic probes, and API availability 99.95%. The alert is
> on error-budget burn rate, not on single blips."

**Alert on burn rate** (e.g. budget consumed 14× faster than sustainable over 1 h *and* 5 min) — it
pages for real incidents and ignores noise. Alerts must be **actionable** and few; an exhausted
on-call is a reliability risk in itself.

## Overload: protecting a system from its own traffic

| Mechanism | What it does | Where |
|---|---|---|
| **Rate limiting** | caps a client's request rate | API edge, per tenant |
| **Load shedding** | rejects low-priority work when saturated, early and cheaply | every tier, by priority class |
| **Admission control / queues** | lets work in at the rate the system can serve | in front of scarce resources (GPUs, seats) |
| **Backpressure** | slows producers when consumers lag | streams, internal RPC |
| **Circuit breaker** | stops calling a failing dependency; fails fast; probes for recovery | client side of every dependency |
| **Bulkheads** | separate pools/threads/capacity per dependency or tenant | so one slow dependency can't exhaust everything |
| **Timeouts + deadlines** | bound waiting; propagate the remaining deadline downstream | every remote call |
| **Graceful degradation** | serve a reduced but useful response | e.g. unranked feed, cached results, no recommendations |

{: .key }
> **Retries multiply load during outages.** Three retries at each of three layers is 27× load on the
> bottom service. Retry at one layer, with budgets and jitter.

### Fail open or fail closed?

Decide per component, out loud: a **rate limiter** usually fails **open** (it must not become an
outage); a **fraud check** on a large payout may fail **closed**; an **authorisation** check fails
**closed**. The rule: *which failure is cheaper — letting bad traffic through, or blocking good traffic?*

## Redundancy and blast radius

- **No single point of failure**: N+1 or N+2 capacity per zone; survive the loss of a zone without
  manual action.
- **Cells**: partition the fleet into independent copies serving subsets of users, so a bad deploy or
  poison request hurts one cell, not everyone.
- **Multi-region**: active-passive (simpler, failover takes minutes, standby capacity costs money) or
  active-active (instant, but data replication and conflict questions — see
  [Replication](04-replication-and-consistency.md)). **Test failover regularly**, or assume it doesn't work.
- **Static stability**: the system keeps working in its current state if the control plane is down.

## Change is the main cause of incidents

- **Progressive delivery**: canary → small percentage → region by region, with automatic halt on SLI
  regression — for **code and configuration alike**.
- **Feature flags and kill switches** to disable a feature without a deploy.
- **Backward-compatible schema and API changes** (expand → migrate → contract).
- **Rollback must not depend on the thing that broke.**

## Observability

- **Metrics** — RED for services (Rate, Errors, Duration), USE for resources (Utilisation, Saturation,
  Errors); percentiles, not averages.
- **Logs** — structured, sampled, with request/trace IDs; mind PII and retention.
- **Traces** — distributed tracing across services to find where latency hides.
- **Per-decision audit** where users will ask "why?" — *why was I rate-limited, why was my payment
  declined, why did I not get the notification.*
- **Synthetic probes** that exercise the real user journey end to end.

## Cost — the line items to name

| Usually the biggest line | In |
|---|---|
| Compute for the hot path | APIs, gateways, ranking |
| Memory | caches, connection tiers |
| Storage × replication × retention | logs, message history, ledgers |
| **Egress** | media delivery, cross-region replication |
| Third-party per-unit fees | SMS, card networks, LLM tokens, GPUs |

{: .say }
> "The biggest cost line here is the cache tier — about 60 TB of RAM. The cheapest lever is not
> fanning out to inactive users, which cuts timeline writes by roughly half."

## Running it: on-call and incidents

Runbooks for the top alerts; clear ownership per component; **blameless postmortems** that fix the
*class* of failure (missing timeout, global config push) rather than the instance; error-budget
policy that the product side has agreed to.

---

## Traps

{: .warn }
> **"99.999% availability"** with no idea what it costs or how it's measured. Five nines is ~5 minutes
> a year; most systems need 99.9–99.95% and should say so.

{: .warn }
> **Monitoring CPU instead of the user journey.** Users don't feel CPU; they feel failed and slow
> requests.
