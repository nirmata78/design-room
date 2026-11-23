from dsl import *
from stack import REJ, say_text
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
def rej(n):
    t, w = REJ(n); return rejl(t, w)
def rejsay(n):
    t, w = REJ(n); return "C: Rejected: " + say_text(t) + ". " + say_text(w[0].upper() + w[1:])
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ───────── Challenge 4 · the hot merchant, and a million accounts ─────────
subchapter("7.4", "Challenge 4: The hot merchant, and a million one-time accounts", ["N: Challenge four. One merchant takes five thousand payments a second, and all of them touch one account. Then the opposite problem."])
qs("Interviewer · challenge 4 of 6", "“One merchant receives five thousand payments a second. Where does that land?”", [
 "I: One merchant receives five thousand payments a second. Where does that land?", "[pause: 2.0]"])

S(dia(K(4, "one row"), "Five thousand writers, one lock", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Update the merchant's balance in each payment's transaction.”"),
                  ("case", "Break", "Every transaction takes the same row lock; they serialise."))), [
 P, "C: Inside one partition: the transaction, the journal, and the balance.", P,
 "C: The shared row is marked.", P, "C: The naive answer: update the merchant's balance inside each payment's transaction.", P,
 "C: Every one of those transactions takes the same row lock, so they run one after another."], cls="dia")

S(trace(K(4, "the trace"), "A queue that grows by four thousand a second", [
  ("12:00:00", "merchant m-42 at 5,000 payments/s"),
  ("12:00:00", "each holds the balance row for ~1.5 ms: " + B("≈ 670/s")),
  ("12:00:01", "queue grows by 4,330; that merchant's p99 " + B("past 2 s")),
  ("12:00:02", "its payments time out and " + B("become UNKNOWNs") + ": this feeds challenge one")],
  hedge=("Label the numbers", "The lock time is illustrative and must be measured. The ratio is the point: five thousand against hundreds.")), [
 "C: The trace.", P, "C: Five thousand a second at one merchant.", P,
 "C: Each holds the balance row for about one and a half milliseconds: the row allows about six hundred and seventy a second.", P,
 "C: The queue grows by more than four thousand a second, and the merchant's latency passes two seconds within a second.", "[+2]",
 "C: Its payments time out and become unknowns. This challenge feeds challenge one. The lock time must be measured; the ratio is the point."])

S(dia(K(4, "the fix"), "Append entries; the balance is a projection", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Insert-only entries, a projector for balances, one payout writer per merchant.")) + rej(4)), [
 P, "C: The fix, on the same view.", P, "C: The journal entries, insert only.", P, "C: A balance projection, derived.", P, "C: And a payout writer.", P,
 "C: One level down. A payment only inserts its own entries into the merchant's partition, so there is no shared row to queue on. A projector tails the journal and keeps the balance a few seconds behind, which is fine for a dashboard. Where a check needs the balance now, a payout must not exceed available funds, a payout writer, one per merchant, reads the sum of the sixteen sub-accounts and posts the payout only if it fits.", 
 "C: It covers the hot row and the payout check. A refund's limit never needed this: it is a conditional update on one payment's row, and one payment is never hot. It does not cover a merchant larger than one primary. Then I split it into several sub-ledgers, which is a decision for that day.", P,
 rejsay(4)], cls="dia")

S(dia("Design · version 4", "A balance projector joins the baseline", "base-v4", vtag="V4"), [
 P, "C: This fix changes the design, so this is version four. Version three, carried.", P,
 "C: New: a balance projector. It reads entries and writes balances back, so reads of a balance never touch the hot path."], cls="dia")

S(dia(K(4, "sequence"), "Appends in, a sum out", "seq-hot"), [
 "C: As a sequence.", P, "C: Five thousand payments a second, each inserting its own entries.", P,
 "C: The projector tails the journal.", P, "C: A balance current to entry nine hundred and ninety-one million, about two seconds behind.", P,
 "C: A payout of fifty thousand: the payout writer reads the sum of the sixteen sub-accounts.", P,
 "C: Available, one point nine million.", P, "C: It posts the payout only if fifty thousand fits.", P,
 "C: A second payout waits its turn: one writer per merchant."], cls="dia")

qs("Interviewer · the second-level push", "“Now the opposite. A million one-time virtual cards a day, each with its own account, none of them ever hot. Do you partition by account now?”", [
 "I: Now the opposite. A million one-time virtual cards a day, each with its own account, none of them ever hot. Do you partition by account now?", "[pause: 2.0]"])

S(plain(K(4, "the second fix, and the honest limit"), "An account is a row, not a partition", cards(
  ("grn", "Still the owner", "A million accounts is about 100 MB. They hash with their merchant, so they spread; created by upsert on first use."),
  ("grn", "Is the card an account?", "The card is an instrument; its limit is a hold in authorisation. The ledger holds who owes whom, with the card ID as a tag."),
  ("amb", "The honest limits", "Archive empty accounts. A funding account shared across merchants posts in two steps: pending, then confirm. Past one primary: a ledger database."), cols=3)), [
 "C: No. Partitioning by account would solve a problem we do not have, and bring back the one we avoided: every posting between a card and its funding account would span partitions.", P,
 "C: An account is a row, not a partition. A million accounts is about a hundred megabytes. They hash with their merchant, so they spread evenly, and each is created by an upsert on first use.", P,
 "C: And I would ask whether the card needs a ledger account at all. The card is an instrument, and its limit is a hold in authorisation. The ledger needs accounts for who owes whom, and the card I-D can be a tag on the entries.", P,
 "C: The honest limits. Empty accounts get closed and archived. A funding account shared across many merchants is the cross-partition case, and there the posting is two steps, pending and then confirm. And past what one primary can do, a purpose-built ledger database such as TigerBeetle takes the core, for debits and credits only: it batches thousands of transfers in one request on a single leader, so a hot account is not a lock."])

say_slide("“Payments only append entries into the merchant's partition, so there is no balance row to fight over. The balance is derived, and the rare checked operation, a payout, goes through one writer per merchant. The partition key is the owner, not the account, so a million cold accounts are just rows.”", [
 "V: If asked, I'd say: payments only append entries into the merchant's partition, so there is no balance row to fight over. The balance is derived, and the rare checked operation, a payout, goes through one writer per merchant. The partition key is the owner, not the account, so a million cold accounts are just rows.", "[pause: 1.0]",
 "N: The books are now fast and correct inside. What about when they disagree with the outside?"])

# ───────── Challenge 5 · 999,998 against 1,000,000 ─────────
subchapter("7.5", "Challenge 5: 999,998 against 1,000,000", ["N: Challenge five, the second half of the crux. The processor's books and ours disagree by two, and later, so does a release."])
qs("Interviewer · challenge 5 of 6", "“The processor's settlement statement says 999,998. Your books say 1,000,000. What now?”", [
 "I: The processor's settlement statement says 999,998. Your books say 1,000,000. What now?", "[pause: 2.0]"])

S(dia(K(5, "the outside truth"), "Who is right, and how would you know?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Compare the daily totals; investigate if they differ.”"),
                  ("case", "Break", "A total that differs does not say which line. A total that matches can hide two offsetting errors."))), [
 P, "C: Inside reconciliation: the file, the matcher, and the break writer.", P, "C: The matcher is marked.", P,
 "C: The naive answer: compare the daily totals, and investigate if they differ.", P,
 "C: A total that differs does not say which line is wrong, and a total that matches can hide two offsetting errors."], cls="dia")

S(plain(K(5, "the case"), "A difference of two, made of three breaks", table(["Line", "Ours", "Theirs", "Kind"], [
  ["p-9120", "captured 1,050", "not in the file", "<b>timing</b>: settles tomorrow; closes itself"],
  ["p-9377", "captured 2,400", "not in the file, 2 days on", "<b>missing at the processor</b>: a claim, with an owner"],
  ["p-9544", "captured 1,050, fee 30", "settled 1,050, fee 35", "<b>amount differs</b>: a fee break, zero count, five cents"]], "bt xs mx") +
  grade("Two missing lines and one wrong fee make a difference of two. Totals show neither the three nor which line.")), [
 "C: The case. The difference of two is made of three breaks.", P,
 "C: One line is a timing difference: captured by us, not in today's file, and it closes itself when tomorrow's file arrives.", P,
 "C: One is missing at the processor, two days on. That is a claim against them, with an owner.", "[+2]",
 "C: And one is settled by them for the same amount with a different fee: it does not change the count, but it is five cents wrong, times every payment like it."])

S(dia(K(5, "the fix"), "Expectations, matched line by line, every break owned", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Expected settlements by reference; matched line by line; the rest become owned breaks.")) + rej(5)), [
 P, "C: The fix, on the same view.", P, "C: The expectation builder.", P, "C: The matcher, by reference.", P, "C: And the break writer.", P,
 "C: One level down. The ledger writes what it expects to settle that day, by reference and net of fees. The raw file is stored unchanged, then joined to the expectations by reference. A match moves the payment to settled, with settlement entries. Anything else becomes a break with a type, an owner and an age.", 
 "C: It covers every line, not a total. It does not cover a processor that changes its reference format: the adapter owns that mapping.", P,
 rejsay(5)], cls="dia")

S(dia(K(5, "sequence"), "From the file to an owned break", "seq-recon"), [
 "C: As a sequence. This is requirement four, reconcile.", P, "C: The settlement file arrives, two point nine times ten to the eight lines, stored unchanged.", P,
 "C: Expectations for the day, by reference, net of fees.", P, "C: Matched line by line.", P,
 "C: Matched lines become settled, with settlement entries.", P,
 "C: A break goes to finance operations: settled by them, declined by us, ten fifty, with an owner and an age.", P,
 "C: A timing break closes itself when tomorrow's file matches."], cls="dia")

qs("Interviewer · the second-level push", "“There are forty thousand breaks this morning, not forty. And money has already gone out.”", [
 "I: There are forty thousand breaks this morning, not forty. And money has already gone out.", "[pause: 2.0]"])

S(dia(K(5, "the second fix"), "A spike in breaks is an incident, not a backlog", "ch5-fix2",
      extra=strip(("fixb", "Stop, find, reverse", "Kill switch, payout hold, reversing entries tagged with the incident; paid-out money is a receivable."))), [
 P, "C: A spike in breaks is an incident, not a backlog.", P, "C: Finance approves, and the corrector posts.", P,
 "C: Stop, find, reverse. Kill the release and hold payouts for the affected merchants. Because the journal is immutable, I can find the duplicates exactly, and post one reversing transaction each, tagged with the incident, so the audit trail shows both the error and the correction. Money already paid out is a receivable, recovered from future settlements.",
 "C: And why the idempotency key did not stop it: it guards requests, not code paths. A unique constraint on payment and type, for types that may occur once, closes this one."], cls="dia")

say_slide("“Reconciliation isn't a safety net for a buggy system; it's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a bad release is fixed by reversing entries, never by deleting history.”", [
 "V: If asked, I'd say: reconciliation isn't a safety net for a buggy system. It's a permanent component, because the processor's truth and ours diverge even when our code is right. I match line by line against expectations from the ledger, every difference becomes a break with an owner and an age, and a bad release is fixed by reversing entries, never by deleting history.", "[pause: 1.0]",
 "N: That fix creates the last question. Every part can now be right. How would you know when one of them isn't?"])

# ───────── Challenge 6 · observability ─────────
subchapter("7.6", "Challenge 6: How would you know before finance does?", ["N: Challenge six is observability, and in this question it is about money, not about servers."])
qs("Interviewer · challenge 6 of 6", "“What do you watch, and what alert fires before finance notices that something is wrong?”", [
 "I: What do you watch, and what alert fires before finance notices that something is wrong?", "[pause: 2.0]"])

S(dia(K(6, "silence"), "Who would have noticed?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Error rate and latency alerts on every service.”"),
                  ("case", "Break", "Every container healthy; fewer payments approved. Finance finds it last."))), [
 P, "C: Back to the container view, version four.", P, "C: Finance operations is marked: they find out last.", P,
 "C: The naive answer: error rate and latency alerts on every service.", P,
 "C: And they are green. Every container is healthy, and fewer payments are being approved."], cls="dia")

S(trace(K(6, "the trace"), "Seven hours of quiet losses", [
  ("02:00", "a change at one processor: " + B("6 points more declines") + " for one country"),
  ("02:00 →", "API errors 0 %, latency normal, every dashboard green"),
  ("05:00", "merchants' conversion drops; nobody pages"),
  ("09:00", B("finance sees fewer settlements") + " than expected"),
  ("09:30", "the first merchant ticket")],
  hedge=("What the dashboards saw", "Nothing. Declines are a valid answer from the processor, so no service was unhealthy.")), [
 "C: The trace.", P, "C: At two a.m. a change at one processor adds six points of declines for one country.", P,
 "C: API errors zero percent, latency normal, every dashboard green.", P,
 "C: At five, merchants' conversion drops, and nobody is paged.", P,
 "C: At nine, finance sees fewer settlements than expected.", "[+2]",
 "C: And at nine thirty the first merchant ticket. Declines are a valid answer from the processor, so no service was unhealthy."])

S(dia(K(6, "the fix"), "Watch the money and the truth", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Approval rate by segment · UNKNOWN age · slot lag · unmatched by age · zero-sum · a probe.")) + rej(6)), [
 P, "C: The fix changes no box. It adds checks on the boxes we have.", P, "C: At the A-P-I: a synthetic payment, a test card, every minute per processor.", P,
 "C: In the database: debits minus credits equal zero, checked continuously, and it pages the moment it is not.", P, "C: In reconciliation: unmatched amount by age.", P,
 "C: One level down. Approval rate per processor and country against its baseline. The count and age of unknown outcomes. Slot lag and outbox age. Unmatched amount by age. And the ledger sum. It covers a silent decline, a stuck unknown, a stalled relay and a growing break. It does not cover a slow drift.", P,
 rejsay(6)], cls="dia")

S(dia(K(6, "sequence"), "The probe, end to end", "seq-probe"), [
 "C: As a sequence.", P, "C: A synthetic payment, a test card, every minute per processor.", P,
 "C: Through the same A-P-I and the same reference.", P, "C: Captured in four hundred and ten milliseconds.", P,
 "C: Success and latency, per processor, go to monitoring.", P,
 "C: Where approval rate per processor and country is compared with its baseline: minus six points. That alert fires at two oh five, not nine.", P,
 "C: And the ledger sum, checked continuously."], cls="dia")

S(plain(K(6, "reading the signals"), "Symptoms in pairs: what each one means", table(["Symptom", "Paired with", "Means"], [
  ["Approval rate down, one processor", "API errors flat", "a processor change; fail over new payments"],
  ["Approval rate down everywhere", "fraud declines up", "our fraud service, not a processor"],
  ["UNKNOWN count up", "inquiry success flat", "the processor is slow, inquiry works"],
  ["Outbox age up", "slot lag in bytes up", "the relay has stalled"],
  ["Unmatched amount up", "one reference prefix", "a format change in one adapter"]], "bt xs mx")), [
 "C: One more habit: read symptoms in pairs. A number alone is not a diagnosis.", P,
 "C: Approval down at one processor with errors flat: a processor change.", P,
 "C: Approval down everywhere with fraud declines up: our fraud service.", P,
 "C: Unknowns up with the inquiry still succeeding: the processor is slow, and the machinery works.", P,
 "C: Outbox age and slot lag both up: the relay has stalled.", P,
 "C: And unmatched amount up for one reference prefix: a format change in one adapter."])

qs("Interviewer · the second-level push", "“The approval rate drops slowly: half a point a week.”", [
 "I: The approval rate drops slowly: half a point a week.", "[pause: 1.5]"])

S(plain(K(6, "the second fix"), "A slow drift needs a slow comparison", cards(
  ("grn", "Compare like with like", "Week over week by processor, country and card type; the decline-code mix, not the total."),
  ("grn", "Alert on the slope", "A drift of 0.2 points a week for three weeks pages a person, not a pager."), cols=2)), [
 P, "C: A slow drift hides under any threshold. So compare like with like: week over week by processor, country and card type, and look at the mix of decline codes, not only the total.", P,
 "C: And alert on the slope. A drift of two tenths of a point a week for three weeks goes to a person, not to a pager."])

say_slide("“I watch the money, not the servers: approval rate per processor and country against baseline, the count and age of unknown outcomes, outbox and slot lag, unmatched amount by age, and a continuous check that the ledger sums to zero, which pages immediately. A synthetic payment per processor tells me before a merchant does.”", [
 "V: If asked, I'd say: I watch the money, not the servers. Approval rate per processor and country against baseline, the count and age of unknown outcomes, outbox and slot lag, unmatched amount by age, and a continuous check that the ledger sums to zero, which pages immediately. A synthetic payment per processor tells me before a merchant does.", "[pause: 1.0]"])

# ───────────────────────── 8 · recap ─────────────────────────
chapter(8, "Recap", 6, "The final design, and what to say", [
 "C: The recap. One picture, one sentence per path, the mistakes that cost most, and the thesis."])

S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four, the final design. The same picture as version one, with the mechanism labels from the theory chapter.", P,
 "C: The A-P-I: the key, inserted first.", P, "C: The payment service: the state machine, with unknown.", P,
 "C: The ledger database: the journal and the outbox, partitioned by merchant.", P, "C: The adapter: our reference on every call.", P,
 "C: The relay: change capture, in commit order.", P, "C: The inquiry job, which ends every unknown.", P,
 "C: Reconciliation, with owned breaks.", P,
 "C: And the balance projector, derived and never incremented."], cls="dia")

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Pay</b>", "key first, attempt committed, call by reference, one transaction for state, entries and event"],
  ["<b>Adjust</b>", "a new transaction, dated now, with the limit in one conditional update"],
  ["<b>Notify</b>", "an outbox row, read from the log, published at least once, de-duplicated by event ID"],
  ["<b>Reconcile</b>", "expectations from the ledger, matched by reference, every break owned"],
  ["<b>Explain</b>", "a sum over immutable entries, in one partition"]], "bt")), [
 "C: One sentence per path.", P,
 "C: Pay: key first, attempt committed, call by reference, one transaction for state, entries and event.", P,
 "C: Adjust: a new transaction, dated now, with the limit in one conditional update.", P,
 "C: Notify: an outbox row, read from the log, published at least once, de-duplicated by event I-D.", P,
 "C: Reconcile: expectations from the ledger, matched by reference, every break owned.", P,
 "C: Explain: a sum over immutable entries, in one partition."])

S(plain("Recap · common mistakes in this round", "What costs candidates the most", cards(
  ("red", "On correctness", "“A distributed transaction with the bank.” A balance column as the truth. A timeout treated as a failure. Floats. Keys checked, not inserted. Partitioning by account."),
  ("red", "On operations", "Events published outside the transaction. History edited. Reconciliation by totals. No owner for breaks. Dashboards with no money on them."), cols=2)), [
 "N: The common mistakes.", P,
 "N: On correctness: a distributed transaction with the bank, a balance column as the truth, a timeout treated as a failure, floats, keys that are checked instead of inserted, and partitioning by account.", P,
 "N: On operations: events published outside the transaction, history edited, reconciliation by totals, no owner for breaks, and dashboards with no money on them."])

S(plain("Recap · the four sentences", "If you have thirty seconds", cards(
  ("", "What", "A state machine per payment, an idempotent API, an immutable double-entry journal partitioned by merchant, reconciliation."),
  ("amb", "The trade", "Pending answers and a reconciliation team, in exchange for never guessing."),
  ("red", "The risk", "The unknown path runs rarely; test it daily. And the replication slot."),
  ("grn", "Next", "A gateway first if you are small; harden inquiry per processor; make breaks an owned, aged workflow."), cols=2)), [
 P, "C: What it is: a state machine per payment, an idempotent A-P-I, an immutable double-entry journal partitioned by merchant, and reconciliation.", P,
 "C: The trade: pending answers and a reconciliation team, in exchange for never guessing.", P,
 "C: The risk: the unknown path runs rarely, so I'd test it every day, and I'd watch the replication slot.", P,
 "C: Next: a gateway first, if the company is small; harden the inquiry per processor; and make breaks an owned, aged workflow."])

key("The close", "I can't get exactly-once across the boundary, so I get <em>one effect per intent</em>, a state for <em>not knowing</em>, and books I can <em>explain</em> and <em>reconcile</em>.", [
 "V: I can't get exactly-once across the boundary, so I get one effect per intent: a key inserted first, a reference on every call, a state for not knowing, and an inquiry that ends it. Every movement is a balanced, immutable entry, so any balance is a sum I can explain. And because the outside world's books will disagree with mine anyway, reconciliation is part of the design, with owners.", "[pause: 1.5]",
 "C: Thanks for watching. The written design, with every number, the technology comparisons and the internals of each tool, is linked below."])
