
# Stage 7: Requirements that arrive mid-round

In a "drip" round the interviewer adds requirements while you design. Three likely ones, with the delta stated
the way the interviewer wants to hear it: what changes, what doesn't, what it costs, and which seam absorbs it.

**"Add a hardship programme: customers can pause payments for up to three months."** *Changes:* a new schedule
version with the paused months removed and the remaining instalments moved or re-amortised, per a new terms
rule; due items for the paused months are cancelled. *Doesn't change:* the ledger, the rails, the resolver.
*Costs:* a policy rule owned by risk and legal, and a reporting flag, because paused loans are reported
differently. *Seam:* schedule versions, which were built for refunds.

**"Add instant payments for payoffs: the customer pays from their bank account and it settles in seconds."**
*Changes:* a third rail with its own budget in the dispatcher and its own adapter; payoff quotes no longer need
to be conditional for that rail. *Doesn't change:* returns for bank debits, reconciliation. *Costs:* one adapter,
a reconciliation source. *Seam:* the dispatcher's rail abstraction.

**"Charge interest on some products."** *Changes:* accrual by calculation from the balance and rate, posted at
events and month-end; the waterfall's "interest due" bucket starts to matter; payoff quotes add interest to the
day. *Doesn't change:* everything else. *Costs:* the accrual calculation, its tests, and its month-end job.
*Seam:* policy versions and the waterfall.

> "That's a new schedule version from a new terms rule. The ledger and the rails don't move."

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| Card processor down | card collections stop | UNKNOWN up, breaker opens | rail switch, resolve unknowns, suppress fees, resume slowly (6.7) |
| Debit file rejected or partly rejected | a day of bank collections | acknowledgement missing or acknowledged/sent below baseline at 11:00 | fix and resend before 14:00 (6.8) |
| Return file late or not ingested | returns not posted; customers wrongly shown as paid | file arrival check; clearing balance not emptying | replay from the raw store |
| Ledger primary lost | all postings stop | database health | fail over to the synchronous standby; minutes |
| A bad policy version | misallocation across many loans | shadow diff; per-loan invariant | roll back the version; reversing transactions for affected postings |
| A bug posts duplicate lines | balances wrong | nightly sum check; unique key violations spike | stop posting; reverse the duplicates, tagged with the incident |
| Worker crash mid-batch | some due rows claimed, not sent | sweeper | rows return to DUE |

**One incident walked through: the bad policy version.** On Nov 12 a new allocation version applies fees after
interest for one state. Every transaction balances, so the sum check is silent. The shadow diff would have
caught it before release; if it was skipped, the nightly per-loan invariant (remaining schedule = outstanding
principal) fails for 30,000 loans the next morning. Response: the version is rolled back (old loans return to
the previous version from the next posting), a correction job posts one reversing and one re-posting transaction
per affected payment, each tagged with the incident ID and the policy version, and customers who were charged a
fee they should not have been are refunded. The audit trail shows the error and the correction; nothing is
edited.

# Stage 9: SLOs, observability, cost

**SLIs, measured from outside where possible:**

| SLI | Target (initial) | How measured |
|---|---|---|
| Debit file acknowledged | by 11:00 every business day | the bank's acknowledgement file |
| Acknowledged / sent | at least 99.9 % | the acknowledgement file against our file |
| UNKNOWN resolved | 99 % within 1 hour | intent state timestamps |
| Collections attempted on due date | 100 % before the cut-off | due items against attempts |
| Breaks older than 3 days | 0 by value above a threshold | reconciliation |
| Ledger sum and projection checks | 0 failures | nightly job |

**The dashboard**, top to bottom: today's funnel per rail; UNKNOWN by age; returns by reason code against
baseline; breaks by age and amount; clearing balance (money in flight) against expectation; customer payable
by age.

**Cost.** Infrastructure is small: one relational database of a few hundred gigabytes with a standby, a few
services, file storage. The real costs are processor fees (a percentage or a fixed fee per card charge, set by
contract) and bank fees per debit, returns, and people: a reconciliation function and on-call. The engineering
levers: move customers from card to bank debit where they agree (cheaper per collection), reduce
self-inflicted declines (the rail budget), and reduce returns (collect after payday, verify accounts at
origination).

# Stage 10: The EM layer (auxiliary at Staff)

**Phasing.** V1 (4 engineers, 2 quarters): ledger with projections, schedules, the state machine, the card rail,
the resolver. V2 (6 engineers, 2 quarters): the bank-file rail, returns, policy as data, refunds and payoff. V3
(two teams, 2 quarters, plus finance operations): three-way reconciliation, the finance console, runbooks,
due-date spreading. All illustrative. For a small book with standard products, buying a servicing platform is
the honest V0.

**One-way doors.** The chart of accounts and the ledger schema (seven years of lines and every auditor depend on
them); terms versioning (contracts cite it, and old loans keep old rules forever); the idempotency key format
shared with the processor.

**Team seams.**

| Team | Owns | Contract with the others |
|---|---|---|
| Ledger | accounts, posting interface, invariants, close | nobody else writes lines |
| Collections and payments | scheduler, rails, resolver, returns | intents and the key format |
| Servicing product | refunds, payoff, hardship | schedule versions |
| Finance operations | reconciliation tools, breaks | break types and ageing |
| Risk and legal | retry rules, fees, allocation | policy versions they approve |
| Compliance | debit authorisations, fee caps | rules by state |

**With half the team:** keep the ledger, the state machine with UNKNOWN and RETURNED, and reconciliation; cut
due-date spreading, the console (use queries and a spreadsheet for breaks), and the second rail's automation.
Never cut the resolver or the return handling: they are where money is lost.

**On-call.** One rotation for collections and payments, with the rail switch and the runbook in 6.7; finance
operations owns breaks during business hours; the ledger team is paged only by the invariant checks.

# Stage 11: The close

Four sentences, in the order *what · trade-off · risk · next*:

> "Money lives in a double-entry ledger with immutable lines, and each payment is a state machine with unknown
> and returned, with keys at three layers. I traded a broker and a midnight batch for the database as the queue
> and a budget per rail planned back from the bank's cut-off. The risk is the rare paths, returns and unknowns,
> so I test them with real files. Next is three-way reconciliation every day, with an owner for every break."

# Stage 12: Self-check after a simulator run

| Area | Weak | Strong | Exceptional |
|---|---|---|---|
| Framing | charges everyone on the due date | asks rails, limits, returns, refunds, audit | sets the order of what must never happen and uses it later |
| Ledger | balance column | double entry, reversals | projection in the same commit, provable, nightly invariant |
| Collections | cron at midnight, retry on error | keys, UNKNOWN, rate limit per rail | three layers of keys; day plan from the cut-off; spread due dates |
| Returns | settled = paid | RETURNED with a reversal | re-presentment rules as policy; exposure by age |
| Adjustments | subtract from the balance | schedule versions, waterfall | in-flight items in payoff quotes; customer payable with a deadline |
| Reconciliation | not mentioned | match with the bank | three-way, by reference, typed and owned breaks; never by totals |
| Operations | API uptime | file acknowledgement, UNKNOWN age | symptom pairs; "our outage is not your late fee"; shadow-tested policy |

**Common traps:** "thundering herd" and a broker for 42 a second; treating SETTLED as final; editing ledger lines;
a new key on every retry; reconciling by totals; late fees for our own outages; nobody owning the policy.

