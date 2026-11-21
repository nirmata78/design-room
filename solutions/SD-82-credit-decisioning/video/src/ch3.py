from dsl import *
import dsl

def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

chapter(3, "Theory", 2, "What makes this problem hard, in words that outlive any product name", [
 "C: A short theory chapter before the design, so the design can lean on it. What this system is and is not, its properties, the central tension, six mechanisms, an options matrix, and the failure catalogue."]); th()

key("Theory · 1 of 6 · what it is", "A system that gathers identity, fraud and credit data from <em>paid vendors</em> under <em>one deadline</em>, returns an <em>explainable</em> decision with priced offers, and books <em>exactly one loan</em> when the customer accepts an offer <em>they were shown</em>.", [
 "V: A credit decisioning system gathers data from paid vendors under one deadline, returns an explainable decision with priced offers, and books exactly one loan when the customer accepts an offer they were shown.", "[pause: 1.0]",
 "C: Every clause is load-bearing. Paid vendors: every call costs money and may be recorded, so we never race them. One deadline: the customer is at a counter. Explainable: a decline carries reasons about the applicant, and they replay years later. Exactly one loan: one atomic step. And an offer they were shown: the disclosure version is part of the contract."], cls="theory")

S(plain("Theory · 1 of 6 · what it is not", "Four things it is confused with", '<div class="cards c2">'
  '<div class="cd"><h3>Not a scoring model</h3><p>The model is one input. Policy decides, and pricing prices. Each is versioned on its own.</p></div>'
  '<div class="cd amb"><h3>Not a payment</h3><p>No money moves at accept. Funding the merchant happens later, asynchronously.</p></div>'
  '<div class="cd red"><h3>Not a saga</h3><p>Only one step must be atomic. A credit pull cannot be compensated: it happened.</p></div>'
  '<div class="cd"><h3>Not an underwriting queue</h3><p>Refer means minutes, by text. A human queue of days is another product.</p></div></div>'), [
 "C: Four neighbours it gets confused with. It is not a scoring model: the model is one input, the policy rules decide, and pricing prices, each with its own version. It is not a payment: no money moves when the customer accepts. The merchant is funded later.",
 "C: It is not a saga: only one step has to be atomic, and a credit pull cannot be compensated, because it happened. And it is not an underwriting queue: refer means we finish in minutes, by text."], cls="theory")

S(plain("Theory · 2 of 6 · the properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p><b>S1</b> A loan booked twice, or without acceptance of the exact offer and disclosure shown.<br><b>S2</b> A decline or a price without reasons about the applicant that can be reproduced.<br><b>S3</b> Raw identity data outside the vault boundary.<br><b>S4</b> More than one pull per bureau per application.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p><b>L1</b> Every application gets an answer (offer, refer, decline) within the deadline.<br><b>L2</b> Every booked loan is funded and handed to servicing, with one effect.<br><b>L3</b> Every referred application is finished within ten minutes.</p></div>'), [
 "C: The properties, stated separately. Safety, what must never happen. S-one: a loan booked twice, or without acceptance of the exact offer shown. S-two: a decline or a price without reasons about the applicant that we can reproduce. S-three: raw identity outside the vault. S-four: more than one pull per bureau per application.",
 "C: Liveness, what must eventually happen. L-one: every application gets an answer within the deadline. L-two: every booked loan is funded and handed to servicing, with one effect. L-three: every referred application is finished within ten minutes. Every fix from here names the property it serves."], cls="theory")

S(dia("Theory · 3 of 6 · the central tension", "Time against evidence against money", "tension"), [
 "C: The central tension. Identity answers in four tenths of a second, fraud in about the same, the bureau usually in six tenths. One time in ten the bureau takes four seconds. The deadline line is at two seconds, and the sale is lost at ten.",
 "C: Waiting longer adds evidence and loses sales. Deciding early keeps the sale and adds risk. Asking a second bureau adds evidence, another dollar and another inquiry. Every choice from here is a point in that triangle, and the important ones belong to credit risk, not to a timeout setting."], cls="dia theory")

def mech(n, name, protects, how, rules, costs, say, live=True):
    S(plain(f"Theory · 4 of 6 · mechanism {n} of 6", name,
        f'<div class="prop {"live" if live else "safe"}"><div class="lbl">Property it protects</div><p>{protects}</p></div>'
        f'<div class="prop"><div class="lbl">How it works</div><p>{how}</p></div>'
        f'<div class="prop safe"><div class="lbl">Failure it rules out</div><p>{rules}</p></div>'
        f'<div class="prop" style="border-left-color:#d18f1c"><div class="lbl" style="color:#a86a12">What it costs</div><p>{costs}</p></div>'), say, cls="theory")

mech(1, "Scatter-gather under one deadline, a breaker per vendor", "L1 and S4.", "All vendor calls at once; decide at the deadline with what has arrived. A breaker per vendor stops calls to a vendor failing for everyone.",
     "One slow vendor setting the customer's wait; customers waiting on a dead vendor.", "Decisions with data missing, which mechanism 2 must decide.", [
 "C: Mechanism one, scatter-gather under one deadline, with a circuit breaker per vendor. It protects L-one and S-four. All vendor calls go out at once, and we decide at the deadline with what has arrived. A breaker stops calls to a vendor that is failing for everyone. It rules out one slow vendor setting the customer's wait. It costs decisions with data missing, which mechanism two has to decide."])
mech(2, "A missing-data policy table, signed and capped", "S2 and L1.", "A versioned table in the policy: second bureau, decide small and known under a cap, refer, or decline with a real reason. A counter and a dashboard per row.",
     "“Approve with partial data” as a code default; declines for “our vendor was slow”.", "A refer path to run; an exposure counter; an owner in credit risk who signs it.", [
 "C: Mechanism two, a missing-data policy table. It protects S-two and L-one. A versioned table inside the credit policy: ask the second bureau, decide small and known customers under a cap, refer, or decline with a real reason. Each row has a counter and a dashboard. It rules out approve with partial data as a code default, and declines whose real reason is our own outage. It costs a refer path, an exposure counter, and an owner in credit risk who signs it."], live=False)
mech(3, "The application as a state machine", "S1 and L1.", "One committed row per transition, with an optimistic version; idempotency keys on create and accept.",
     "Two workers moving one application; progress lost when a phone drops.", "A committed write per transition: at 50 a second, nothing.", [
 "C: Mechanism three, the application as a state machine in the database. It protects S-one and L-one. Every transition is one committed row, with a version number used as an optimistic lock, and idempotency keys on create and accept. It rules out two workers moving one application, and lost progress when a phone drops. It costs a write per transition, which at fifty a second is nothing."], live=False)
mech(4, "One local transaction: book, unique loan, outbox", "S1 and L2.", "Move the status at a version, insert the loan under UNIQUE(application_id), insert an outbox row, commit. A relay publishes the row.",
     "Two loans for one application; a loan nobody hears about.", "A relay to run; consumers that de-duplicate by event ID.", [
 "C: Mechanism four, one local transaction for booking. It protects S-one and L-two. Move the status at a version, insert the loan under a unique constraint on the application, insert an outbox row, and commit. A relay then publishes the row. It rules out two loans for one application, and a loan that funding never hears about. It costs a relay, and consumers that de-duplicate."], live=False)
mech(5, "An immutable decision record", "S2.", "Written once: frozen inputs (the report by reference, the feature vector, missing calls), every version, the outputs and ranked reasons. Old models stay loadable.",
     "Unexplainable declines; a re-run that contradicts the notice we sent.", "8.4 TB over seven years; a model registry kept for as long as the records.", [
 "C: Mechanism five, an immutable decision record. It protects S-two. Written once: the frozen inputs, including the report by reference, the feature vector and which calls were missing; every version; and the outputs with ranked reasons. Old models stay loadable. It rules out declines nobody can explain, and a re-run that contradicts the notice we sent. It costs eight terabytes over seven years and a model registry kept just as long."], live=False)
mech(6, "An identity vault with tokens", "S3.", "Identity is tokenised at apply. Only the vault and the vendor adapters see real values; every detokenise is logged with a purpose.",
     "Identity in rows, logs, exports and training sets.", "A small, critical service; a hop at apply and at each vendor call; key management.", [
 "C: Mechanism six, an identity vault. It protects S-three. Identity is tokenised at apply, and only the vault and the vendor adapters, which must send real values, ever see them. Every detokenise is logged with its purpose. It rules out identity spreading into rows, logs, exports and training sets. It costs a small, critical service and a hop at each vendor call."], live=False)

S(plain("Theory · 5 of 6 · the options", "Six ways to run an application", table(["Approach", "3 s p95", "One pull per bureau", "Survives a drop", "Explainable", "Fails when"], [
  ("rej", ["A · Sequential calls in the request", "no", "yes", "no", "partly", "the bureau's tail alone is seconds"]),
  ("rej", ["B · Parallel, hedged: race two bureaus", "yes", "<b>no</b>", "no", "partly", "every race is two paid pulls"]),
  ("rej", ["C · A saga, a compensation per step", "yes", "yes", "yes", "partly", "a pull cannot be undone"]),
  ("", ["D · A durable workflow engine", "yes", "yes", "yes", "yes", "not a failure: another system to run"]),
  ("pick", ["<b>E · State machine + one deadline + policy table + atomic book</b>", "yes", "yes", "yes", "yes", "steps grow to days"]),
  ("rej", ["F · A manual underwriting queue", "no", "yes", "yes", "yes", "ten seconds is a lost sale"])], "bt sm")), [
 "C: The options matrix. A, sequential calls in the request: the bureau's tail alone breaks three seconds. B, parallel with hedging, racing two bureaus: fast, but every race is two paid pulls and two inquiries. C, a saga with a compensation for every step: a credit pull cannot be undone, so the compensations do nothing but add code. F, a manual queue: ten seconds is already a lost sale.",
 "C: D, a durable workflow engine, is the honest equal: it works, and I'd choose it when steps last hours or days, like document upload or manual review. I pick E: a database state machine, one deadline, the policy table, and an atomic booking with an outbox. What it gives up: the timers, retries and relay that a workflow engine would give us for free."], cls="theory")

S(plain("Theory · 6 of 6 · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "Kind"], [
  ["1", "The bureau is slow", "latency · crux"], ["2", "The bureau is down for everyone", "failure, policy · crux"],
  ["3", "The phone drops; two taps", "correctness · crux"], ["4", "Funding fails after booking", "failure recovery · crux"],
  ["5", "A decision nobody can explain", "correctness, regulation"], ["6", "A new model approves more", "trade-off"],
  ["7", "Identity data spreading", "security"], ["8", "A silent approval drop", "observability"]], "bt sm") +
  line("Out of scope, named: merchant fraud, a merchant ringing up fake sales. Merchant risk owns it.", "")), [
 "C: The failure catalogue, which becomes the challenge list. The bureau slow, then down for everyone. The phone drops, then funding fails after booking. A decision nobody can explain. A new model that approves more. Identity data spreading. And a silent approval drop.",
 "C: One more I'll name and leave: merchant fraud, a merchant ringing up fake sales. That's a merchant-risk system, and it plugs in at onboarding and at funding."], cls="theory")
