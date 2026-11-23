
# Stage 7: Requirements that arrive mid-round

Interviewers often add a requirement around minute 35. Name the delta out loud: what changes, what does
not, what it costs, and which existing seam absorbs it.

**"The clearing file is six hours late, with 3 % duplicates."** Covered in Challenge 7. *Changes:* file
and record idempotency; expiry gated on the file's arrival. *Does not change:* the authorisation path.
*Costs:* a later posting time on bad days. *Seam:* the clearing matcher's per-record step.

**"Add credit cards."** *Changes:* available becomes credit limit minus posted balance minus holds; the
account state gains statement cycles, minimum payments and interest, all in the core ledger. *Does not
change:* holds, messages, the reserve, the fail table, rules, clearing. *Costs:* a second available
formula and a product team. *Seam:* the account row's available calculation in the reserve.

**"Run in a second region."** *Changes:* each account is homed in one region (its partition's primary);
the gateway in either region routes by the account's home; a regional failover moves the primaries.
*Does not change:* one account, one writer: the reserve stays a single-partition write. *Costs:* a
cross-region hop for an account homed far away, and a failover measured in tens of seconds, during which
those accounts get stand-in. *Seam:* the partition map.

::: warn
**Active-active balances across regions** are the trap here. Two regions accepting reserves for the same
account need either a cross-region consensus write on every authorisation (latency) or a reconciliation
of overdrafts afterwards (the two-swipes race, at region scale). Homing each account in one region is the
boring, correct answer.
:::

**"Product wants instant refunds to the card."** *Changes:* a refund message posts a credit; available
goes up only when it posts, not when the merchant initiates it. *Does not change:* everything else.
*Seam:* the message state machine gains a credit type.

**"Add the network's own risk score."** *Changes:* one more field on the request, one more model feature.
*Does not change:* anything structural. Mention it as what changed in recent years: networks' real-time
scores now routinely arrive with the request.

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| Model slow or down | fraud quality, inside the cap | model cut-off rate | fail table; roll back the model version |
| Feature store partition lost | burst features for some cards | counter errors | conservative limits; rebuild buckets |
| Bad rule set | approvals for whole merchant types | approval rate by merchant type | re-point to the previous version |
| Auth-store partition failover | its accounts, for seconds | reserve errors, stand-in count | quorum commit; stand-in covers the gap |
| Whole decision fleet down | every card: stand-in | synthetic test cards, stand-in count | restore; post advices; replay the night |
| Link to the processor down | every card: stand-in | stand-in count with flat p99 | the processor's problem, our runbook |
| Late or duplicated clearing file | posting time | file-arrival alarm | idempotent ingestion; expiry waits |
| Auth store and ledger disagree | some accounts' available | daily reconciliation breaks | break queue with an owner |
| Card data leak | regulatory | — | out of our scope: tokens only |

## One incident, walked through

**21:10, a model release.** The new model's feature fetches double; p99 for scoring goes to 1.8 s.

- *21:11* Model cut-off rate goes from 0.3 % to 31 %. Gateway p99 stays at 95 ms: the cut-off is doing
  its job. Degraded approvals start counting against the "model late" cells' caps.
- *21:12* The pair "cut-offs up, p99 flat" pages the risk platform on-call: the model, not us.
- *21:15* Runbook step 1, what changed: the model release at 21:09. Step 2, re-point the scorer to the
  previous model version.
- *21:17* Cut-offs back to 0.3 %. Degraded decisions in the incident: about 1,500 × 0.31 × 360 s =
  167,000, worth about \$10 million in volume, against which the cap and the rules held.
- *Next morning:* compare the degraded decisions' fraud with the model's normal rate as labels arrive;
  add a canary for model releases; review whether the cap was right.

# Stage 9: SLOs, observability, cost

**SLOs** (initial targets): authorisation p99 under 300 ms at the gateway; availability 99.99 % measured
by synthetic test cards in every region; stand-in under 0.01 % of authorisations in a month; clearing
posted by 09:00 on 99 % of days; rule change live within 5 minutes; reconciliation breaks resolved within
two business days.

**How they are measured from outside.** Synthetic test cards in every region send an authorisation and a
reversal every minute through the processor, so the measurement includes the link. Stand-in is counted
from advices, which are the network's own record of our absence. Approval rates are compared with the
same hour last week, because card traffic is strongly weekly.

**The dashboard**, top to bottom: approval rate by merchant type; stand-in count; gateway p99 and model
cut-offs; degraded decisions against each cap; "it was me" replies; unmatched holds and clearings;
reconciliation breaks.

**Cost, illustrative.**

| Line | Size | Lever |
|---|---|---|
| Processor and network fees | per transaction; the largest | negotiated, not engineered |
| Fraud losses | 8 bps of volume | the model, the rules, the fail policy |
| Declined good customers | lost revenue, never measured directly | fast proxies; step-up instead of decline |
| Decision archive | about 15 TB a year, seven years | compression, cold storage after 90 days |
| Model serving | a few machines | embed a small model; cache features |
| Authorisation fleet | small | none needed |

> A basis point of fraud is worth more than all the servers. The design's cost lever is the quality of
> the decision, not the size of the fleet.

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.**

| Phase | Scope | People and time |
|---|---|---|
| V0, buy | outsourced authorisation at the processor with uploaded rules and stand-in limits | 3 engineers, 8 weeks |
| V1 | own decision service on the core ledger | 4 engineers, 3 months |
| V2 | auth store, rules as data, model under a cut-off, clearing matcher | a team of 6–8, 2 quarters |
| V3 | features, fail table, advices, lifecycle tooling, reconciliation | two teams, 2 more quarters |

**Team seams.** *Authorisation platform:* gateway, decision service, authorisation store, latency and
availability. *Risk platform:* rules engine, features, shadow and backtest tooling. *Data science:*
models and their monitoring. *Fraud operations:* the content of rules, customer contact. *Ledger and
clearing:* holds' end of life, posting, reconciliation. The contracts between them: the decision event
schema, the rule-set format, and the fail-policy table.

**Half the team.** Keep V0 longer: the processor's rules and stand-in, with our own clearing matcher and
reconciliation. Cut the in-house model before cutting idempotency or reconciliation: a weaker fraud
score costs basis points; a double hold or a broken book costs trust.

**On-call.** The authorisation platform is 24/7 with a five-minute response; the runbook for "declines
doubled" is owned jointly with fraud operations; the fail-policy caps page before they run out.

# Stage 11: The close

> **What:** a stateless decision service with its state next to it answers inside 300 ms, places a hold
> rather than a debit, and makes every network message count once in any order.
> **Trade-off:** we keep a second copy of balances, reconciled daily with the ledger, to keep the ledger
> off the authorisation path.
> **Risk:** the fail policy is only as good as the caps risk and finance sign; the stand-in limits are
> only as good as last outage's replay.
> **Next:** sub-limits for large business accounts, a canary for model releases, and network tokens to
> shrink card-data scope further.

# Stage 12: Self-check after a simulator run

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Money | debits at authorisation | holds; available = posted − holds; clearing posts and releases | expiry gated on the file; clearing as truth; late clearing posts |
| Correctness | no idempotency | network reference; per-account reserve | message written in the hold's transaction; tombstones for early reversals |
| Deadline | "call the fraud service" | budget per step; a cut-off | fail table with caps and owners, priced |
| Stand-in | not mentioned | advices recorded | over-limit as a modelled state; replay to tune limits |
| Fraud change | rules as code | rules as data with shadow | backtest, slice, expiry; knows shadow cannot measure false positives |
| Features | from a stream | inline bursts | features logged with the decision |
| Operations | CPU and errors | approval rate by merchant type | symptom pairs and a runbook starting with changes |

**Common traps:** debiting at authorisation; one authorisation equals one clearing record; read-then-write
on the balance; ignoring retries and out-of-order reversals; "the network gives 100 ms"; waiting for the
model; "fail open under \$100" as the whole answer; velocity only from a stream; shadow mode to measure
false positives; refusing advices because they overdraw; no owner for the fail policy.
