# 1 · The interview method — how a strong round is run

A system-design round is graded on **how you think in front of someone**, not on the diagram you end
with. Every reference solution in this repository follows the same stage structure, because the
structure *is* most of the score: it is how the interviewer sees that you scope before you build,
decide with numbers, go deep where it matters and finish on time.

---

## The twelve stages and their clock

For a 45–60-minute round. Budgets are for a **60-minute** slot; scale by 0.75 for 45.

| # | Stage | Minutes | What you produce | What it proves |
|:-:|---|:-:|---|---|
| 1 | Clarify requirements | 0:00–0:06 | functional list, non-functional numbers, **explicit out-of-scope** | you can turn a vague prompt into a bounded problem |
| 2 | Back-of-the-envelope | 0:06–0:11 | three numbers, each tied to a decision | numbers drive your design, not decorate it |
| 3 | API and data model | 0:11–0:17 | the 3–6 calls that matter; the core entities and their keys | the middle of the design will not be vague |
| 4 | High-level design | 0:17–0:27 | 6–10 boxes, arrows with protocols, one end-to-end walk | a coherent system you can narrate |
| 5 | Technology choices | anywhere | a reason for every non-obvious component | judgment, not name-dropping |
| 6 | Deep dives | 0:27–0:45 | 2–3 components taken two levels down | depth where the problem is actually hard |
| 7 | Mid-round requirements | as given | a delta to the design, not a rebuild | adaptation under pressure |
| 8 | Failure modes | 0:45–0:50 | what breaks first, blast radius, recovery | operational maturity |
| 9 | SLOs, observability, cost | 0:50–0:54 | 2–3 SLIs, the alert, the biggest cost line | you would actually own this |
| 10 | The level layer | when asked | team seams, sequencing, build-vs-buy — or technical strategy | the altitude of your target level |
| 11 | The close | 0:55–0:57 | **four sentences** | crisp under pressure |
| 12 | Self-check | after | what you missed | the habit that makes you improve |

{: .warn }
> **The most common failure is not technical.** It is spending 25 minutes in stages 3–4, starting
> deep dives at minute 40 and never reaching stage 8. Say the time out loud at each transition:
> *"I'm at about 15 minutes — I'll move to the high-level design."* Interviewers score clock
> management even when they don't say so.

---

## Stage 1 · Clarify — the four question families

Ask in this order, and write the answers down where the interviewer can see them.

1. **Users and scale.** How many, how active, where in the world, what's the peak and is it
   predictable?
2. **The core use cases.** Which two or three flows matter? What is explicitly *not* in scope?
3. **The non-functional bar.** Latency (p99, not average), availability, durability, consistency,
   freshness — **each with a number.**
4. **The constraints.** Regulation, existing systems, team size, budget, deadline.

{: .say }
> "Before I design anything, I want to pin down four things: scale, the core flows, the
> non-functional bar, and constraints. Then I'll state what I'm leaving out so we can agree on scope."

**The out-of-scope list is a scoring item.** An empty one reads as "didn't think about it". Name
three things you are deliberately not designing, and why.

**"What matters more?" questions are the strongest clarifying questions** because they force a
trade-off the design will hinge on: *"Is it worse to show a message twice or to lose one?"* · *"Is it
worse to oversell a seat or to show a sold-out seat as available?"*

## Stage 2 · Estimate — the number must change a decision

Compute **three** numbers, not ten. Each one ends with *"…which means…"*. The method and the number
kit are in [Estimation](02-estimation.md).

{: .key }
> An estimate that is never referenced again is decoration and scores 2 at best. The shape to hit:
> *"1M requests a second against one shared counter is a million network round trips a second — that
> rules out a central store on the hot path."*

## Stage 3 · API and data model

- **Only the calls that carry the design** — usually 3–6. Include idempotency keys on anything that
  creates or moves something, and cursors on anything that lists.
- **Entities with their keys and access patterns.** The key is the design: it decides partitioning,
  ordering and what can be queried cheaply. *"Timeline rows keyed by `(user_id, score)`, partitioned
  by `user_id`"* says more than any diagram.
- Pick the store **after** the access pattern, with a sentence of reason ([Partitioning &
  storage](03-partitioning-and-storage.md)).

## Stage 4 · High-level design and the walk-through

Draw few boxes, label every arrow with what crosses it (sync HTTP/gRPC, async event, stream), then
**walk one request end to end without being asked.** That walk is the single best signal in the
round; the interviewer will ask for it if you don't offer.

{: .say }
> "Let me walk one request through: the client calls the gateway, which authenticates and checks the
> limit; the write goes to the service, which commits to the database and the outbox in one
> transaction; the relay publishes the event; the consumers…"

Start **simple and correct** — the v1 that works at today's scale — and name the evolution: *"This is
v1. The first thing that breaks at 10× is X, and here's where I'd split it."*

## Stage 5 · Technology choices — mechanism over brand

Every non-obvious component needs a reason expressed as a **mechanism and a trade-off**:

| Weak | Strong |
|---|---|
| "I'd use Kafka." | "I need a durable, partitioned, replayable log so consumers can fall behind and catch up; ordering only matters per user, so I partition by user ID." |
| "Cassandra because it scales." | "Writes dominate and access is always by partition key with a time-ordered range — a wide-column LSM store fits; I give up cross-partition transactions, which I don't need here." |
| "Redis for caching." | "An in-memory store for a hot, rebuildable working set; if it's lost we fall back to the database at reduced capacity, so it doesn't need to be durable." |

Be prepared to go one level down on anything you name: how it partitions, replicates, fails.

## Stage 6 · Deep dives — where the score is decided

Pick **the crux** (the one decision the problem is really about) before the interviewer does, and go
down the probe ladder yourself:

1. **Why this choice?** 2. **What are the alternatives and what did I trade away?** 3. **What happens
when it fails, doubles, or 10×s?** 4. **How would I know it's broken?** 5. **What would I cut with half
the time?**

Reaching the edge of what you know is fine — say so and reason from first principles: *"I don't know
the exact internals, but it has to be true that…"* is a strong move; bluffing is a weak one.

## Stage 7 · When the requirements change mid-round

A new requirement or failure is a test of **adaptation**. The strong pattern:

1. Restate it in one line. 2. Say **which parts of the design it touches** and which it doesn't.
3. Change those parts specifically. 4. **Say what it costs.**

Rebuilding everything, or ignoring it, both score low.

## Stages 8–9 · Failure, SLOs, cost — the operational bar

For each major component: *what happens when it's slow, down, or wrong?* Then publish 2–3 SLIs (see
[Reliability & operations](08-reliability-and-operations.md)), the alert that fires before customers
notice, and the biggest line on the bill. At EM level and above this is not optional — it is the
part you would own.

## Stage 10 · The level layer

What the panel listens for changes with level ([`levels.md`](../levels.md)):

{: .level }
> **Senior** — clean design, two levels deep on one component. **Staff** — you pick the risky
> component, go three levels deep with mechanisms, and name the decisions that need an RFC.
> **Principal** — the multi-year shape and what the org should not build. **EM** — operations, cost,
> team seams, an MVP and its sequencing. **Senior EM** — several systems, migration order, risk.
> **Director** — investment, org design, build-vs-buy; boxes are secondary.

## Stage 11 · The close — four sentences

1. **What it is**: *"A hybrid fan-out feed: push for normal accounts, pull for celebrities."*
2. **The hard part and how it's handled**: *"The celebrity write amplification is avoided by merging
   their posts at read time."*
3. **What I traded away**: *"Feeds are eventually consistent — seconds of staleness."*
4. **What I'd do next**: *"Load-test the threshold and add per-region timeline caches."*

## Stage 12 · Self-check after every practice run

- Did I state out-of-scope items and the non-functional numbers?
- Did at least one estimate change a decision?
- Did I walk one request end to end unprompted?
- Did I reach failure modes, SLOs and cost before the clock ran out?
- Did I say the four-sentence close?
- Which probe did I struggle with, and which [theory page](README.md) covers it?

---

## Talking patterns that score

| Situation | Say |
|---|---|
| Two valid options | *"Both work. I'm choosing X because of Y in our requirements; if Z were true I'd pick the other."* |
| You don't know | *"I haven't operated that, so let me reason from what must be true…"* |
| Challenged on a correct choice | Hold it, with reasoning: *"I'd keep it, because…; what would change my mind is…"* |
| Challenged on a wrong choice | *"You're right — that breaks when…; here's the fix."* Adapting fast scores higher than defending. |
| Running long | *"I could go deeper here, but I want to cover failure modes — shall I come back to this?"* |
