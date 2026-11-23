
# Stage 6: Deep dives

The bridge sentence, said aloud: **"It works. Where does it break first?"** Then show the challenge map
and take the challenges in an order where each fix creates the next question.

![The challenge map: eight attack points on the same baseline.](diagrams/video-map.pdf){width=100%}

| # | Challenge | Kind | Mechanism that answers it |
|---|---|---|---|
| 6.1 | The bureau is slow | latency, crux part 1 | scatter-gather under one deadline, a breaker per vendor |
| 6.2 | The bureau is down for everyone | failure and policy, crux part 1 | a signed missing-data table with caps; refer |
| 6.3 | The phone drops | correctness, crux part 2 | a conditional update, a unique loan, the outbox |
| 6.4 | Funding fails after booking | failure recovery, crux part 2 | funding as its own state machine; UNKNOWN as a state |
| 6.5 | Explain a decision fourteen months later | correctness and regulation | an immutable decision record; nightly replay |
| 6.6 | A new model approves six percent more | trade-off | backtest, shadow, a capped challenger slice |
| 6.7 | Where identity data lives | security | a vault with tokens |
| 6.8 | How would you know it is broken? | observability | SLIs on the decision; symptom pairs |

## 6.1 The bureau is slow (latency)

**The question.** *"One bureau call in ten takes four seconds today. What does the customer at the
counter see?"*

**The naive answer.** "Wait for it, and if it's slow, send the same request to the second bureau and
take whichever answers first." Hedged requests are a good answer for an internal read-only service. They
are the wrong answer here, and the interviewer asked the question to find out whether you know why.

![The vendors break: waiting misses the promise; racing pays twice.](diagrams/video-ch1-attack.pdf){width=100%}

**The case.**

| Time | Event |
|---|---|
| 10:00:00.000 | Submit from the phone |
| 10:00:00.050 | Identity, fraud and bureau A called |
| 10:00:00.350 | Fraud answers |
| 10:00:00.400 | Identity answers |
| 10:00:01.000 | Hedge: the same pull sent to bureau B |
| 10:00:01.700 | Bureau B answers; offers shown at about 2.0 s |
| 10:00:04.100 | Bureau A answers: a second paid pull, a second inquiry on the customer's file |
| without the hedge | offers at about 4.4 s, past the 3 s promise |

Each pull costs about a dollar and may appear on the customer's credit file as an inquiry. Racing two
bureaus doubles the bill for every slow call and can hurt the very customer you are serving.

**The fix: scatter-gather under one deadline, and a breaker per vendor.**

![The orchestrator owns time: one deadline, a breaker per vendor.](diagrams/video-ch1-fix.pdf){width=100%}

All required calls go out at once. The orchestrator decides at the deadline (2.0 s from the start of the
calls) with what has arrived; if everything arrives earlier, it decides earlier. Each vendor adapter has a
circuit breaker: when a vendor's error rate or tail latency crosses a threshold over a window, the breaker
opens and the adapter stops calling that vendor for everyone, so no customer waits for a vendor that is
known to be failing. The second bureau is called **only after an error or an open breaker**, never as a
race against a slow but healthy first call.

![The gather in time: the late answer is recorded and used to finish a refer.](diagrams/video-seq-ch1-gather.pdf){width=95%}

**Why it works.** L1 (an answer within the deadline) is bounded by the deadline, not by the slowest
vendor. S4 (at most one pull per bureau per application) holds because a second bureau is asked only
when the first has failed, not when it is slow.

**"What if the fix fails?"** *"The bureau's answer arrives at 4.1 seconds, after you decided. What do you
do with it? You paid for it."*

**The second fix.** Record it: the call happened and was billed, so it is a fact in `vendor_call`. If the
application was referred because the bureau was missing, the late answer finishes it: the customer gets a
text with offers. If the application was already offered or declined, the late answer does not change what
the customer saw, because the decision record says what we knew at the time; it is kept as evidence and,
where the contract allows, in the report store for a re-application. The honest limit: a deadline means
about 3 % of applications reach the missing-data path every day, which is the next question.

> "All vendors at once, one deadline, a breaker per vendor. I never race two bureaus, because each pull
> is paid and may show on the customer's file. A late answer is recorded and used to finish a refer, never
> to change what the customer saw."

::: warn
**"Set a three-second timeout on the bureau."** A timeout per call is not a deadline per decision. With
three vendors each on a three-second timeout in sequence, the wait is nine seconds; in parallel, each
still allows three seconds and leaves nothing for the model and the push. Derive one deadline from the
promise.
:::

## 6.2 The bureau is down for everyone (failure and policy)

**The question.** *"Bureau A is down for everyone for twenty minutes on a Saturday. What happens at the
counter?"*

**The naive answers.** "Approve with whatever data we have" or "decline until it's back." Both are
engineering decisions about credit risk, made in a catch block.

![The vendors and the policy break together: both extremes are expensive.](diagrams/video-ch2-attack.pdf){width=100%}

**The case.** From 11:00 to 11:20 on Saturday, at about 8 applications a second: 8 × 1,200 s $\approx$ 9,600
applications. Approve all of them without a credit file and we offer about 9,600 × $1,200 $\approx$ $11.5M of
credit nobody scored. Decline all of them and we lose about 9,600 × 60 % × 70 % $\approx$ 4,000 loans, and we owe
9,600 decline notices whose only true reason is "our vendor was down", which is not a reason about the
applicant.

**The fix: a missing-data policy table, signed by credit risk.**

![The policy engine holds a signed table for missing data.](diagrams/video-ch2-fix.pdf){width=100%}

![Four answers, in order, each with its own cap.](diagrams/video-policy.pdf){width=100%}

1. **The second bureau**, after the breaker on the first has opened. Not a race: the first is known to be
   failing.
2. **Decide without a bureau** only for returning customers in good standing (for example, three or more
   on-time payments on a previous loan), for at most $500, under a daily exposure cap of $250,000
   (illustrative): at most 500 such loans a day.
3. **Refer.** "We'll finish in about two minutes by text." The merchant's screen says *pending*, not
   *declined*. The application waits in a refer queue and is finished when a bureau answers.
4. **Decline**, only with a reason about the applicant, which needs data we have.

Each row is a versioned setting in the policy, with a counter per row and a dashboard, signed by credit
risk and approved by the partner bank as part of the credit policy. Engineering builds the mechanism;
credit risk owns the numbers.

![A referred application finished by text when a bureau answers.](diagrams/video-seq-ch2-refer.pdf){width=95%}

**Why it works.** S2 holds: nobody is declined for our outage. L1 holds: everybody gets an answer (an
offer, a refer, a reasoned decline) within the deadline. And the exposure is bounded by arithmetic: the
daily cap is the worst case, whatever happens to the vendor.

**"What if the fix fails?"** *"Bureau B's contract allows five calls a second. You're sending eight."*

**The second fix.** A token bucket per vendor at the contract rate: five tokens a second for bureau B.
Calls beyond it are not sent; those applications go to refer. The refer queue is drained oldest first when
tokens free up or when bureau A's breaker half-opens and a probe succeeds, inside the ten-minute promise.
The exposure cap for row 2 is split per merchant, so one busy merchant cannot spend the whole day's cap in
an hour. In twenty minutes at three a second over the limit, about 3,600 applications are referred. The
honest limit: some referred customers walk away; measure the refer completion rate and the lost sales per
minute of outage, and give those numbers to credit risk when they set the caps.

> "Every timeout is a credit decision with an owner. Credit risk signs a table: second bureau, small known
> customers under a daily cap, refer, or decline with a real reason. Engineering makes it a setting with a
> counter, a cap and a dashboard."

::: why
**Why "refer" is the senior insight.** A declined applicant must be told the principal reasons for the
decline. If the only reason is that a vendor did not answer, the decline is both wrong for the customer and
hard to defend. *Refer* turns a bad decision into a delayed one. It costs a queue and a text message.
:::

## 6.3 The phone drops (correctness)

**The question.** *"The customer taps accept, the phone loses signal, and they tap again on the
merchant's tablet. How many loans?"*

**The naive answers.** "Check whether a loan exists, and create one if it doesn't." Or: "an orchestrated
saga with a compensating action for each step."

![The application service and the database break: two workers, one application.](diagrams/video-ch3-attack.pdf){width=100%}

**The case.**

| Time | Event |
|---|---|
| 14:31:07.200 | Phone posts accept, idempotency key k1 |
| 14:31:07.900 | The response is lost in the shop's dead zone |
| 14:31:08.050 | Tablet posts accept, key k2 (another device, another key) |
| 14:31:08.060 | Worker 1 reads ap_91: OFFERED, version 7; no loan |
| 14:31:08.070 | Worker 2 reads ap_91: OFFERED, version 7; no loan |
| 14:31:08.090 | Both insert a loan: **two loans**, two funding transfers of $1,200 tonight, the customer billed twice |

Idempotency keys alone do not save this case: the two requests came from two devices with two keys.
Check-then-insert does not save it either: both checks ran before either insert.

**The fix: one local transaction.**

![The database decides: a conditional update, a unique loan, the outbox row in the same commit.](diagrams/video-ch3-fix.pdf){width=100%}

```sql
BEGIN;
UPDATE application SET status = 'BOOKED', version = 8
 WHERE id = 'ap_91' AND status = 'OFFERED' AND version = 7;
-- 0 rows: someone else booked (or the offer expired): ROLLBACK and return the existing loan
INSERT INTO loan (id, application_id, offer_id, disclosure_v, terms)
VALUES ('ln_5531', 'ap_91', 'of_3', 'v7', '{"months": 6, "apr_bps": 1490}');
INSERT INTO outbox (event_id, type, payload)
VALUES ('ev_77', 'LoanBooked', '{"loan_id": "ln_5531", "application_id": "ap_91"}');
COMMIT;
```

The conditional update lets exactly one writer through: the second worker's update matches zero rows,
because the first changed the status and the version. The unique constraint on `loan.application_id` is
a second wall, in case a code path forgets the update. The outbox row commits with the loan, so "the loan
exists" and "the world will hear about it" are one fact. The second device's request reads the
application, finds it BOOKED, and returns `ln_5531`.

**Why it works.** S1 is enforced by the database, the one place that sees both writers. No distributed
coordination, no lock held across a network call.

**Why not a saga.** The table below is worth drawing in the round.

| Step | Can it be undone? | So |
|---|---|---|
| Identity check, credit pull | No: it happened, it was paid, it may be on the customer's file | Record it; never "compensate" |
| Offer | Expires by itself | A lifetime, no action |
| Accept → book | Must be atomic | One local transaction with the outbox |
| Fund the merchant | Yes, by a reversal or a return | Asynchronous, retried, reconciled (6.4) |

A saga is a fine tool when several steps each change state that can be undone. Here only one step after
booking can be undone, and everything before booking is either a fact or expires.

**"What if the fix fails?"** *"The commit succeeded, but the relay crashed before publishing. Or it
published twice."*

**The second fix.** The relay is at least once by design: it reads unpublished outbox rows, publishes,
and only then marks them published. A crash between the two publishes the event again on restart. So
every consumer de-duplicates by `event_id`, and funding uses the loan ID as its idempotency key at the bank,
so even a duplicate that slips through cannot pay twice. The honest limit: this is at least once plus
idempotent consumers, not "exactly once".

> "Only one step is atomic: accept to book. A conditional update at a version, a unique constraint on the
> application, and the outbox row in the same commit. A second tap finds the loan and shows it. The event
> is at least once, and every consumer de-duplicates."

## 6.4 Funding fails after booking (failure recovery)

**The question.** *"The loan is booked. The transfer to the merchant is rejected, or the bank times out.
What do you undo?"*

**The naive answer.** "Roll back the saga: cancel the loan, reverse the credit check, delete the
application."

![Funding breaks after the customer has left.](diagrams/video-ch4-attack.pdf){width=100%}

**The case.** At 14:31 loan `ln_5531` is booked. At 18:00 the daily funding batch sends $1,164 (the
$1,200 less a 3 % merchant fee) to the merchant. At 18:02 the bank returns *account closed*. At 18:03 a
second merchant's transfer, for another loan, times out with no answer at all. Re-sending both "to be
safe" would pay the second merchant twice if its first attempt actually went through.

**The fix: funding as its own state machine, with UNKNOWN as a state.**

![Funding owns its states; reconciliation closes the gaps.](diagrams/video-ch4-fix.pdf){width=100%}

| State | Meaning | Next |
|---|---|---|
| PENDING | In tonight's batch | SENT |
| SENT | The bank acknowledged the instruction | SETTLED, RETURNED |
| UNKNOWN | We asked and got no answer | query the bank by our key; never resend |
| RETURNED | The bank rejected or returned it | merchant operations fixes the account; a new attempt |
| SETTLED | Money arrived | done; reconciled |

Every transfer carries our idempotency key (the loan ID and the attempt number), so the bank can tell us
whether it already has the instruction. A timeout becomes **UNKNOWN**, and the only allowed action on
UNKNOWN is to ask, not to send. A *returned* transfer goes to merchant operations, who fix the account,
and a new attempt is sent with a new attempt number. The loan itself is cancelled only if the goods were
not delivered, and that is a business decision with the merchant, not a rollback.

![The unknown transfer, resolved by the next day's file rather than by a resend.](diagrams/video-seq-ch4-fund.pdf){width=95%}

**Why it works.** L2 (every booked loan eventually funded, with one effect): the loan ID is the
idempotency key end to end, and UNKNOWN keeps "maybe paid" from becoming "paid twice".

**"What if the fix fails?"** *"The bank's status API says 'not found' for the timed-out transfer, and the
file tomorrow shows it paid."*

**The second fix.** "Not found" in the first minutes after a timeout does not mean "not sent": many
bank interfaces index instructions asynchronously. So no resend happens before the reconciliation window
closes. Daily reconciliation compares three things: our funding records, the bank's settlement file, and
the loans booked. Every difference is a *break* with an owner and an age; breaks older than two days page
someone. The honest limit: some outcomes are only known the next day, so the merchant's portal says *in
progress*, not a guess.

> "The credit pull and the booking aren't compensated: they happened. The one step with a real undo is
> funding, so it's its own state machine after booking, with UNKNOWN as a state: query, never resend.
> Reconciliation against the bank file closes the gap."

## 6.5 Explain a decision fourteen months later (correctness and regulation)

**The question.** *"A regulator asks why a customer was declined fourteen months ago. Reproduce it."*

**The naive answer.** "Re-run the model on the customer's data."

![The policy engine only knows today.](diagrams/video-ch5-attack.pdf){width=100%}

**The case.** In January 2026, application `ap_204` was declined by model v9 under policy v31, with
reasons *high utilisation* and *short history*, and the customer was sent a notice saying so. In March
2027 someone re-runs today's model v14 on today's bureau file, and it approves. Now we hold a notice that
says one thing and a replay that says another, and neither tells the regulator what actually happened.

**The fix: an immutable decision record.**

![The record is written once by the orchestrator.](diagrams/video-ch5-fix.pdf){width=100%}

![What a decision record holds.](diagrams/video-record.pdf){width=100%}

Every decision writes, once, a record of three parts. **Inputs, frozen**: the bureau report stored
encrypted and referenced, the identity and fraud results, our internal history *as of that moment*, the
feature vector actually used, and which calls were missing. **Versions**: model, policy (including the
missing-data table), pricing, disclosure, and the orchestrator build. **Outputs**: the outcome, the offers,
the ranked reasons, the degraded path taken, the timings and the deadline. Old model artefacts stay
loadable in a registry. A replay job runs every night on a sample of records: it loads the versions,
re-scores the frozen features and alarms on any difference.

![The replay: load the record, load the old versions, re-score, compare.](diagrams/video-seq-ch5-replay.pdf){width=95%}

**Why it works.** S2: the same inputs and the same versions give the same answer. And the nightly replay
proves it continuously, instead of on the day the regulator asks.

**"What if the fix fails?"** *"The customer asks us to delete their data. The record holds their bureau
report."*

**The second fix.** Retention duties for credit records generally take precedence for their period, and
that call belongs to compliance, not engineering. Within the period, the record holds tokens rather than
identity and an encrypted report under a key per record; access is restricted to the purposes the rules
allow. At the end of the retention period the record's key is destroyed (crypto-shredding), which makes
every copy unreadable, backups included, without hunting for them. The honest limit: a deletion request
inside the retention period is answered by restricting use, and the customer is told so.

> "I never re-run today's model to explain yesterday. Every decision freezes its inputs, the versions of
> model, policy and pricing, and the ranked reasons. A nightly replay proves records still reproduce, and
> retention ends by destroying the record's key."

::: why
**Why "reasons" are ranked and stored, not computed later.** Reason codes come from the model and the
policy together: the features that pushed the score down most, mapped to plain language, plus any policy
rule that fired. Computing them later from a different model version gives different reasons. Store what
you told the customer.
:::

## 6.6 A new model approves six percent more (trade-off)

**The question.** *"Data science has a new model. It approves six percent more people at the same
predicted loss. Roll it out."*

**The naive answers.** "Shadow mode for a week; it looks good; switch it on." Or "a fifty-fifty A/B test."

![The policy engine is where the risk of a new model lands.](diagrams/video-ch6-attack.pdf){width=100%}

**The case.** Six percent of two million is 120,000 more approvals a month; at 70 % take-up, about 84,000
more loans, about $100M a month of new exposure. The first payments of those loans fall due in two to four
weeks; losses only show at 90 to 120 days. A week of shadow mode shows the approval rate. It shows nothing
about whether the newly approved people repay. A fifty-fifty test puts $50M a month at risk to learn it.

**The fix: champion and challenger, in steps that each see what the one before cannot.**

![A challenger beside the champion, deciding only a capped slice.](diagrams/video-ch6-fix.pdf){width=100%}

![From backtest to a policy change.](diagrams/video-rollout.pdf){width=100%}

1. **Backtest** on labelled history: approval and loss on past loans the old model approved.
2. **Shadow**: both models score every application; only the champion acts. Compare approval rates and
   reason codes by segment and by protected group.
3. **Challenger slice**: the challenger decides 5 % of traffic under its own exposure cap. The extra
   approvals in the slice are about 5 % of 120,000 = 6,000 a month, about 4,200 loans, about $5M a month,
   signed by credit risk and the partner bank.
4. **Early signals** at 30 to 45 days: the first payment missed, compared between champion and challenger
   approvals of similar people.
5. **Widen** only through a policy version change, with a kill switch per version.

**Why it works.** S2 is kept: each record says which model decided. And the exposure of learning is
bounded by the slice cap, not by optimism.

**"What if the fix fails?"** *"Shadow looked great. Why isn't that enough?"*

**The second fix.** Shadow cannot see outcomes for the people only the challenger would approve: the
champion declined them, so they never got a loan and have no repayment label. Only a slice where the
challenger actually decides produces labels for them. Fairness checks run on shadow (who would be
approved) and on the slice (who repays). The honest limit: a slice is real money at risk; the cap is the
price of learning, and credit risk owns that price.

> "Shadow tells you who the new model would approve, not whether they repay. So: backtest, shadow, then a
> capped slice where the challenger decides, early signals at thirty days, fairness by group, and every
> step a policy change with a kill switch."

## 6.7 Where identity data lives (security)

**The question.** *"The analytics team wants application data to train the next model. What do they
get?"*

**The naive answers.** "A copy of the database; we encrypt it at rest." Or "we drop the name column."

![Identity spread through rows, logs and exports.](diagrams/video-ch7-attack.pdf){width=100%}

**The case.** In V2 the application table holds a social security number, a date of birth and an address.
A debug log line in the bureau adapter prints the full request. The support tool shows the full number to
every agent. The training extract drops names but keeps date of birth and postcode, which together
re-identify most people. One leaked extract leaks two million identities a month. Encryption at rest
protects a stolen disk; it does nothing for a query, a log line or an export.

**The fix: an identity vault with tokens.**

![Only the vault and the vendor adapters see real values.](diagrams/video-ch7-fix.pdf){width=100%}

![The boundary, drawn small on purpose.](diagrams/video-vault.pdf){width=95%}

Identity is tokenised at apply. Only two things sit inside the boundary: the vault itself and the vendor
adapters, which must send the real values to the bureau and the identity vendor. Every detokenise is
logged with its caller and purpose. Rows, logs, decision records, support tools and the event log carry
tokens or masked values. Training gets derived features (utilisation, history length, income band), not
identity. Adapter logs are scrubbed at the source.

Know the rulebook, because the interviewer may test it: **card numbers** fall under the card industry's
security standard; a **social security number** falls under privacy and lending law. Quoting the card
standard for identity data is a common slip.

**Why it works.** S3 by construction: a leak anywhere outside the boundary leaks tokens.

**"What if the fix fails?"** *"The vault is down."*

**The second fix.** The vault is a tier-0 dependency, so it is kept small, with no business logic,
replicated across zones, with its own 99.95 % objective and its own on-call. If it is down, apply cannot
tokenise and the adapters cannot detokenise; applications are referred and the merchant sees *pending*.
Nothing raw is ever cached outside the vault "to help". The honest limit: the vault being small is what
makes it reliable; resist every feature request that would grow it.

> "They get tokens and derived features, never identity. Only the vault and the vendor adapters see real
> values, every access is logged, and a leak anywhere else leaks tokens. And I'd name the right rulebook:
> identity data is privacy and lending law, not the card standard."

## 6.8 How would you know it is broken? (observability)

**The question.** *"Your dashboards are green. How would you know decisions are going wrong?"*

**The naive answer.** "Error rate, latency and CPU."

![The change that broke decisions raised no error.](diagrams/video-ch8-attack.pdf){width=100%}

**The case.** At 18:00 on Friday a pricing-table change maps one bureau field wrongly. No errors; latency
is fine; CPU is flat. The approval rate across all merchants drops from 62 % to 41 %. At about two
applications a second in the evening that is 7,200 an hour and about 1,500 wrongly declined each hour,
each with a notice. It is found at 09:00 on Saturday when merchants start calling: fifteen hours, about
22,000 customers if the evening rate held (illustrative).

**The fix: SLIs on the promise and on the decision, read in pairs.**

![What to watch: the decision, the fallbacks, the money.](diagrams/video-ch8-fix.pdf){width=100%}

| SLI | Why it pages |
|---|---|
| Offers on screen within 3 s, p95 | The promise at the counter |
| Approval rate per merchant per hour, against its own baseline | A sudden drop is almost never the customers |
| Fallback rate per policy row, against its cap | Credit risk said "capped": prove it |
| Loans booked and not funded after one hour (batch-aware) | Money owed to a merchant |
| Vendor errors, latency and spend per hour | The largest cost line and the deadline's enemy |
| The mix of decline reasons | A new dominant reason is a change, not a population |

| When you see | Together with | It means |
|---|---|---|
| Approval down | Vendor errors flat, a deploy at the same time | Our change |
| Refer rate up | A breaker open | An outage being handled as designed |
| Offer latency up | Breakers closed | A vendor slow but under the breaker's threshold |
| Booked up | Funded flat | Funding stuck |
| One decline reason jumps | Feature distribution shifted for one bureau | A vendor changed a field |

Policy and pricing changes ship as canaries: a small slice first, with the approval-rate alarm armed.

**"What if the fix fails?"** *"Approval drops at one merchant only."*

**The second fix.** Per-merchant baselines by hour of the week. A drop at one merchant is usually an
integration bug (amounts sent in dollars instead of cents) or a fraud ring testing stolen identities, and
it goes to merchant operations or fraud, not credit. The honest limit: small merchants have noisy
baselines; alarm on totals over a window, not on one hour.

> "I watch the decision, not the servers: offers in three seconds, approval rate per merchant per hour
> against its baseline, fallback rate against the cap, and loans booked but not funded. Two metrics
> together tell me whether it's us, a vendor or one merchant."

## 6.9 How the whole system degrades, in priority order

| What fails | What still works | What the customer sees |
|---|---|---|
| One bureau slow | Everything; the deadline decides | Offers, rarely a refer |
| One bureau down | Second bureau, small known customers, refer | Offers or *we'll text you* |
| Both bureaus down | Small known customers under the cap, refer | Mostly *we'll text you* |
| Identity vendor down | Returning customers already verified; refer | *We'll text you* |
| Policy engine down | Nothing decides; apply still records | *Pending*; refer queue fills |
| Vault down | Nothing new starts; booked loans continue | *Pending* |
| Database primary lost | Failover to the standby in seconds; in-flight requests retry by key | A short pause |
| Event log down | Booking continues; the outbox holds events | Nothing; funding later |
| Funding down | Loans booked; merchants paid in the next batch | Nothing at the counter |
