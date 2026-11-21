from dsl import *

# ───────────────────────── 4 · API and entities ─────────────────────────
chapter(4, "API and entities", 3, "The contract forces the hard semantics into the open", [
 "C: The A-P-I next, because writing the contract forces the hard semantics into the open: retries, expiry, and what the customer actually agreed to."])

S(plain("API · apply and decide", "An application is a resource, not a call  <span class=vtag>FR1 · FR2</span>",
  '<pre class="code" data-lang="http">POST /v1/applications\nIdempotency-Key: 6f1e2c90-…      <span class="cm"># the POS and the phone retry</span>\n{ <span class="st">"merchant_id"</span>: <span class="st">"m_42"</span>, <span class="st">"amount_cents"</span>: 120000,\n  <span class="st">"applicant"</span>: { <span class="st">"vault_token"</span>: <span class="st">"tok_8f2c"</span> } }\n→ 202 { <span class="st">"application_id"</span>: <span class="st">"ap_91"</span>, <span class="st">"status"</span>: <span class="st">"STARTED"</span> }\n\nGET /v1/applications/ap_91            <span class="cm"># poll, or a push to the phone</span>\n→ 200 { <span class="st">"status"</span>: <span class="st">"OFFERED"</span>, <span class="st">"offers"</span>: [ … ], <span class="st">"expires_at"</span>: … }</pre>' +
  strip(("whyb", "Writes Application", "202 at once: the decision takes seconds and the phone may drop. A token, never identity. Offers expire in 15 minutes; REFERRED carries a promise time."), cols="one")), [
 "C: Apply returns at once, two-oh-two, with an application I-D, because the decision takes seconds and the phone may drop. It carries an idempotency key, so a retry from the point of sale returns the same application instead of pulling the bureau again. And it carries a vault token, never the identity itself.",
 "C: The phone polls or receives a push. The answer is offers with an expiry, fifteen minutes, because prices and credit files go stale. Or referred, with a promise time, or declined. This serves FR-one and FR-two, and writes the application entity."])

S(plain("API · accept and the event", "What the customer agreed to, and who hears about it  <span class=vtag>FR3 · FR4</span>",
  '<pre class="code" data-lang="http">POST /v1/applications/ap_91/accept\nIdempotency-Key: 0b7d11a4-…\n{ <span class="st">"offer_id"</span>: <span class="st">"of_3"</span>, <span class="st">"disclosure_version"</span>: <span class="st">"v7"</span> }\n→ 201 { <span class="st">"loan_id"</span>: <span class="st">"ln_5531"</span> }    <span class="cm"># a second accept: the same loan</span>\n\nevent LoanBooked { event_id, loan_id, application_id, merchant_id,\n                   principal_cents, merchant_fee_cents, terms }</pre>' +
  strip(("whyb", "Writes Loan, Outbox", "The disclosure version is part of the contract. The event is at least once; every consumer de-duplicates by event_id."), cols="one")), [
 "C: Accept names the offer and the version of the disclosure the customer saw, because that version is part of the contract, and it returns the loan. A second accept, from any device, returns the same loan.",
 "C: Then the event, loan booked, with the loan, the merchant, the principal and the merchant fee. It is delivered at least once, so funding and servicing de-duplicate by event I-D. FR-three and FR-four."])

S(plain("API · the internal contract", "The decision interface between two teams",
  '<pre class="code" data-lang="json">Decide(application_id, applicant_token, merchant, amount) →\n{ <span class="st">"outcome"</span>: <span class="st">"APPROVE | REFER | DECLINE"</span>,\n  <span class="st">"offers"</span>: [ … ], <span class="st">"reasons"</span>: [<span class="st">"high utilisation"</span>, <span class="st">"short history"</span>],\n  <span class="st">"versions"</span>: { <span class="st">"model"</span>: <span class="st">"v9"</span>, <span class="st">"policy"</span>: <span class="st">"v31"</span>, <span class="st">"pricing"</span>: <span class="st">"v12"</span> },\n  <span class="st">"missing"</span>: [<span class="st">"bureau_a"</span>], <span class="st">"path"</span>: <span class="st">"second_bureau"</span>, <span class="st">"record_uri"</span>: … }</pre>' +
  strip(("whyb", "Why missing and path", "The applications team shows “pending” for a refer; operations counts how often each degraded path is taken, which proves the caps hold."), cols="one")), [
 "C: Inside, the decision interface is the contract between the applications team and the decisioning platform. Outcome, offers, ranked reasons, the three versions, and two fields people forget: which inputs were missing, and which degraded path was taken.",
 "C: Without those two, the applications team can't show pending for a refer, and nobody can prove that the caps credit risk signed actually hold."])

S(dia("Data · conceptual", "One application, many calls, one decision, at most one loan", "erd-chen"), [
 "C: The conceptual model, in one breath. An applicant, known only by a token, submits applications. Each application makes paid vendor calls. Each is decided once. A decision holds offers. An application books at most one loan. And a loan is paid out by funding transfers."], cls="dia")

S(dia("Data · physical", "The constraints carry the correctness", "erd-physical"), [
 "C: The physical tables. The application row is the state machine, with a version for the optimistic lock and a token instead of identity. The decision row is written once, never updated, with the versions and a link to the full record. The loan has a unique constraint on the application: that one constraint makes a double tap harmless.",
 "C: The outbox commits with the loan. Every vendor call is a row with its cost, because the bureau bill is the largest line. And the vault is a separate store that only two components can read."], cls="dia")

S(plain("Data · stores", "Which stores, and can we lose them?", table(["Store", "Holds", "Lose it?"], [
  ["Application database", "applications, decisions, offers, loans, outbox, vendor calls", "No: synchronous standby in another zone"],
  ["Decision records", "the full record, encrypted, one key each", "No: retention lock for seven years"],
  ["Vault", "identity, encrypted per field", "No: the only copy; replicated across zones"],
  ["Event log", "LoanBooked, decisions", "Rebuildable from the outbox table"],
  ["Report store", "recent bureau reports for reuse", "Yes: a miss costs a dollar, not correctness"]], "bt sm")), [
 "C: Five stores, and whether we can lose them. The application database, no: a synchronous standby in another zone. Decision records, no: a retention lock for seven years. The vault, no: it is the only copy. The event log can be rebuilt from the outbox. And the report store can be lost: a miss costs a dollar, not correctness."])

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the one before", [
 "C: The design in three versions. Before each new one, I'll say the objection it answers."])

S(dia("Design · V1", "The simplest thing that works", "base-v1", vtag="V1"), [
 "C: Version one, so we have something to break. The phone and the point of sale call an A-P-I edge, which calls one application service. It calls the identity vendor, then the bureau, in turn, scores, and writes the application and the loan to one database.",
 "C: Three objections. The latencies add up, so the bureau's slow tail alone breaks three seconds. A dropped phone retried on another device can book twice. And nothing records why we decided."], cls="dia")

S(dia("Design · V2", "One deadline, one state machine, one atomic step", "base-v2", vtag="V2"), [
 "C: Version two answers latency and correctness. A decision orchestrator, outlined blue, calls all vendors at once under one deadline, with a breaker per vendor. The application becomes a state machine in the database. Booking is one transaction that also writes an outbox row, and a relay publishes it to an event log. And scoring becomes a versioned policy engine: model, policy, pricing.",
 "C: What it leaves: what we do when the bureau is missing at the deadline, identity data in every row and log, no record that survives a model change, and nobody paying the merchant."], cls="dia")

S(dia("Design · V3", "Regulated, explainable, owned", "base-v3", vtag="V3"), [
 "C: Version three. The identity vault, top left, tokenises at apply, and only the vendor adapters inside the orchestrator detokenise. Decision records go to encrypted object storage, written once. The missing-data policy table lives in the policy engine, versioned with the credit policy. And funding consumes loan booked from the log, then hands the loan to servicing.",
 "C: The objection it answers: this must be regulated, explainable and owned. What it leaves are the details, and those are the challenges."], cls="dia")

S(dia("Flow · FR1 apply", "Identity is a token before anything else sees it", "flow-fr1", trs=tr(("fr", "FR1"), ("ent", "Application"))), [
 "C: FR-one, apply, by the numbers. One, the phone posts the application with an idempotency key. Two, the A-P-I edge tokenises identity in the vault. Three, the application service creates the row. Four, the row commits, status started. Five and six, the answer goes back: two-oh-two with the application I-D. From step two on, nothing but the vault sees the identity."], cls="dia")

S(dia("Flow · FR2 decide", "Everything at once, one deadline, one record", "flow-fr2", trs=tr(("fr", "FR2"), ("ent", "Decision"), ("ent", "Offer"))), [
 "C: FR-two, decide. One, the application service asks the orchestrator. Two, the vendor adapters detokenise in the vault, only for the calls that need it. Three, identity, fraud and bureau go out at once. Four, the answers come back, or the deadline passes and the miss is recorded.",
 "C: Five, the policy engine computes features, runs the model, the policy rules and pricing. Six, the decision record is written once. Seven, the decision goes back and the row becomes offered, referred or declined. Eight, the offers reach the phone."], cls="dia")

S(dia("Flow · FR3 accept and book", "One transaction while the customer watches", "flow-fr3", trs=tr(("fr", "FR3"), ("ent", "Loan"), ("ent", "Outbox"))), [
 "C: FR-three, accept and book. One, the phone posts accept with the offer, the disclosure version and a key. Two, the edge passes it on. Three, one transaction: the status moves to booked at a version, the loan is inserted under its unique constraint, and the outbox row is inserted. Four and five, two-oh-one with the loan I-D."], cls="dia")

S(dia("Flow · FR4 fund and hand off", "After the customer has left the counter", "flow-fr4", trs=tr(("fr", "FR4"), ("ent", "FundingTransfer"))), [
 "C: FR-four, fund and hand off. One, the booking transaction wrote the outbox row. Two, the relay publishes loan booked to the event log. Three, funding adds the loan to tonight's batch for the merchant, and servicing opens the repayment schedule. None of it is in the customer's wait."], cls="dia")

S(dia("C4 · context", "Who is at the counter, and who is slow", "c4-context"), [
 "C: The context view. On the left, the customer at the counter and the merchant. In the middle, us: apply, decide, book, fund. On the right, the credit vendors, slow and paid; the partner bank, the lender of record, which pays merchants; and servicing, which takes the loan after booking."], cls="dia")

S(dia("C4 · containers", "Every container exists for one reason", "c4-containers"), [
 "C: The containers. The A-P-I edge: merchant authentication and idempotency keys. The application service owns the state machine and booking, and has no vendor code in it. The orchestrator owns time: deadlines, breakers and rate limits. The policy engine is a pure function of inputs and versions, so it can replay.",
 "C: The vault is the regulated part, kept small. The database holds correctness in its constraints. The event log decouples the counter from funding, servicing and notices. Funding is the only container that moves money. And decision records sit in object storage with a retention lock."], cls="dia")

S(dia("Sequence · apply and decide", "Submit, then everything at once", "seq-decide"), [
 "C: Apply and decide as a sequence. The phone posts; it gets two-oh-two, started. The application service asks the orchestrator to decide with a deadline two seconds out. Identity, fraud and bureau go out at once and come back at four tenths, three and a half tenths and six tenths of a second. Features, model version nine, policy thirty-one, pricing twelve: approve, three offers, reasons. The record is written once, and offers are pushed to the phone."], cls="dia")

S(dia("Sequence · accept and book", "One commit, then at-least-once publishing", "seq-book"), [
 "C: Accept and book. The accept arrives with the offer and the disclosure version. Begin. Update the application where it is still offered and at version seven. Insert the loan, insert the outbox row, commit. One row changed, committed, two-oh-one. Later, the relay polls unpublished outbox rows, publishes loan booked, and only then marks them published. At least once, by design."], cls="dia")

S(plain("Design · one application in time", "Where the 1.3 seconds of a usual case go", table(["t (ms)", "What happens", "Where"], [
  ["0", "submit; idempotency key checked", "API edge"],
  ["150 – 200", "identity tokenised; row STARTED committed", "vault, database"],
  ["200", "three vendor calls at once; deadline set at 2,200", "orchestrator"],
  ["550 · 600 · 820", "fraud, identity, bureau A answer", "adapters"],
  ["820", "all required answers in: no need to wait for the deadline", "orchestrator"],
  ["1,070 – 1,120", "model, policy, pricing; record written; row OFFERED", "policy engine, storage"],
  ["1,320", "offers on the phone", "push"]], "bt sm")), [
 "C: One usual application in time. Submit at zero. By two hundred milliseconds the identity is a token and the row is committed. The three vendor calls go out together, and the deadline is set for two point two seconds. Fraud answers at five fifty, identity at six hundred, the bureau at eight twenty.",
 "C: At that moment every required answer is in, so the orchestrator moves on without waiting for the deadline. The deadline is a ceiling, not a wait. Model, policy and pricing finish around eleven hundred, the record is written, and the offers are on the phone at about one point three seconds. The slow case is the one the challenges are about."])

key("The line to remember", "The core is small and boring on purpose: <em>one database, one atomic step</em>. The design lives at the slow edges.", [
 "V: The core is small and boring on purpose: one database, one atomic step. The design lives at the slow edges.", "[pause: 0.8]",
 "N: Every box had a reason before it was drawn."])
