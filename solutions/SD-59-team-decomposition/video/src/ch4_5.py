from dsl import *
import dsl as _d
P = "[+]"

# ───────────────────────── 4 · contracts and entities ─────────────────────────
chapter(4, "Contracts and entities", 3, "The contract first. It forces the disagreements into week one.", [
 "C: Contracts and entities. Before anyone writes code, the contract at each seam, because a contract is where two teams find out they disagree, and week one is the cheapest time to find out."])

_d.wire("""{"contract": "loan-booked",
 "version": 1,
 "loanId": "ln-5531",
 "principalCents": 120000}""", """{"contract": "loan-booked",
 "version": 2,
 "loanId": "ln-5531",
 "principalCents": 120000,
 "currency": "usd"}""", "Contract · an event", "Loan Booked, v1 and an additive v2", [
 "C: The first contract, an event. Origination emits loan booked: the loan I-D, the principal in cents, the first due date. That is version one, and it is what the two external teams build against.", "[+]",
 "C: Later we need a currency. Version two adds one optional field. Nothing is renamed, nothing is removed, so every version-one consumer keeps working. That is the additive-only policy, in one example."], lang="json")
_d.wire("""POST /v1/refunds
Idempotency-Key: mr-77

{"loanId": "ln-5531",
 "amountCents": 30000}""", """HTTP/1.1 201 Created

{"refundId": "rf-901",
 "status": "applied"}""", "Contract · a call", "A synchronous call, with its rules", [
 "C: The second kind, a synchronous call. A refund, with an idempotency key so a retry is safe, and a response that says what happened.", "[+]",
 "C: And the rules that travel with it: additive changes only, and two weeks of notice before anything is deprecated. The policy is part of the contract, not a separate document."], lang="http")

S(dia("Entities · the ownership model", "Teams, components, contracts, and who depends on whom", "erd-owner", cap="Figure 4.1 — the model the manager keeps: one owner per component"), [
 "C: The entities the manager keeps, as a model. It is small on purpose.", P,
 "C: A team has a time zone and a size.", P,
 "C: A component has exactly one owner team. That one rule is " + ps("S2") + ".", P,
 "C: A contract is provided by one component, and is either an event or a call.", P,
 "C: And a dependency says which component needs which contract, and by which week. That table is the dependency graph, and I keep it."], cls="dia")

# ───────────────────────── 5 · high-level design ─────────────────────────
chapter(5, "High-level design", 4, "Three versions, each answering the objection to the one before", [
 "C: The design, in three versions, each introduced by the objection to the one before. Every picture is a view of the same container diagram; new boxes are outlined."])

S(dia("High-level design · version 1 of 3", "The simplest thing: one team per layer", "hld-v1", vtag="V1",
      chip=chips("5 teams", "by layer", "platform alone"), cap="Figure 5.1 — C4 container view, V1"), [
 "C: Version one. The simplest split: one team per layer. Team one owns every endpoint.", P, "C: Team two owns all the business rules.", P,
 "C: Team three owns all the tables.", P, "C: Team four owns every rail adapter.", P,
 "C: And team five runs the platform. It is easy to staff, and it is where most first plans start."], cls="dia")

objection(1, "Every feature crosses every team", "obj-v1", [
 "I: Walk me through how version one breaks.", P, "C: Product asks for a partial refund.", P, "C: The A-P-I team needs a new rule from the logic team.", P,
 "C: Which needs a new column from the data team.", P, "C: Which needs a new field from the adapter team.", P,
 "C: And it ships after all four, in week three. With ten pairs of teams and a feature touching four, the latency is the sum of four queues. Nobody can ship alone."],
 cap="Figure 5.2 — the failing case of V1")

S(dia("High-level design · version 2 of 3", "One team per domain, with its data and its rails", "hld-v2", vtag="V2",
      chip=chips("vertical seams", "events at the boundaries", "platform serves"), cap="Figure 5.3 — the same view, V2: new boxes outlined"), [
 "C: Version two. The platform team stays, running the shared infrastructure.", P,
 "C: Servicing core takes the ledger and the schedule, with its own tables.", P, "C: Collections takes dispatch and the rails, with its own adapters.", P,
 "C: Reconciliation takes files and breaks.", P, "C: Policy and A-P-I takes quotes and terms. Between them, only events and one call. That is the arrow budget."], cls="dia")

objection(2, "Correct by domain, and still two holes", "obj-v2", [
 "I: Domain seams look right. What is still missing?", P,
 "C: Two teams need a change to the same ledger table, and they need incompatible ones.", P,
 "C: With no owner rule and no contract, nobody can say which goes first.", P,
 "C: And the first end-to-end run is in month five, where everything fails to fit at once.", P,
 "C: So version three adds contracts with one owner for the shared thing, and a skeleton in week four."],
 cap="Figure 5.4 — the two holes of V2")

S(dia("High-level design · version 3 of 3", "Close the loops: contracts, owners, a skeleton", "hld-v3", vtag="V3",
      chip=chips("contract hub", "skeleton env", "one owner per shared thing"), cap="Figure 5.5 — the same view, V3: the carried baseline"), [
 "C: Version three adds two things and changes no team. First, everything the teams build, as the carried baseline: servicing core owns the ledger, collections owns dispatch and the rails, reconciliation owns files and breaks, policy and A-P-I owns quotes and terms, and platform runs the shared infrastructure. Every arrow is an event or a call, and each has a contract.", P,
 "C: Second, a contract hub. It holds the schemas, the consumer tests and the mock servers, and it is the only place a contract is edited.", P,
 "C: And a skeleton environment, where one thin path runs end to end from week four. This is the baseline. Every picture from here is a view of it."], cls="dia")

def flow(n, fr, title, svg, tags, say):
    S(dia(f"High-level design · requirement {n} · {fr}", title, svg, trs=tr(*tags)), say, cls="dia")

flow(1, "seams", "FR1: choosing the seams", "fr1", [("fr", "serves FR1"), ("api", "workshop"), ("ent", "writes component, owner"), ("nfr", "≤ 2 teams per feature")], [
 "C: Requirement one, choosing the seams. I list the nouns and who changes them together.", P, "C: The domain leads cluster what changes together.", P, "C: One team per cluster, one named owner."])
flow(2, "contracts", "FR2: making the seams explicit", "fr2", [("fr", "serves FR2"), ("api", "contract hub"), ("ent", "writes contract, version"), ("nfr", "agreed by week 2")], [
 "C: Requirement two, contracts. The provider drafts a contract with the additive-only policy.", P, "C: The consumers review it and register the calls they rely on.", P, "C: Version one is agreed in week two."])
flow(3, "unblock", "FR3: keeping every team unblocked", "fr3", [("fr", "serves FR3"), ("api", "mock server"), ("ent", "reads contract"), ("nfr", "idle ≤ 2 days")], [
 "C: Requirement three, unblocking. The consumer builds against a mock generated from the contract, in week two.", P, "C: The provider publishes examples to the same mock.", P, "C: In month four the real service replaces the mock."])
flow(4, "integrate", "FR4: integrating early", "fr4", [("fr", "serves FR4"), ("api", "skeleton env"), ("ent", "reads all contracts"), ("nfr", "green by week 4")], [
 "C: Requirement four, integration. Team A builds a thin ledger path.", P, "C: Team B builds the mock-rail path.", P, "C: And the skeleton goes green end to end by week four."])
flow(5, "detect", "FR5: detecting a wrong split", "fr5", [("fr", "serves FR5"), ("api", "split-health dashboard"), ("ent", "reads PRs, lead time"), ("nfr", "signal by month 2")], [
 "C: Requirement five, detection. The dashboard shows cross-team pull requests and lead time rising.", P, "C: I open a two-week review of the seam.", P, "C: And the teams move one seam, once."])

subchapter("5.1", "Components and technologies", ["C: Now one level down: the tools that carry the contracts. Not a product tour: for each, how it works, why this one, and what an interviewer will name instead."])

S(tech("Tools · contract format", "Schemas in one registry, checked for compatibility", ("OpenAPI and protobuf in the contract hub", "One reviewed repository; a compatibility check in CI rejects a breaking change before merge."),
  "Each contract is a schema file with an owner. The pipeline compares a change to the last released version and fails on a removed field, a changed type or a new required field.",
  [("A wiki page per contract", "nothing checks it; it drifts the first week"), ("Shared source code between teams", "couples release dates and languages")],
  cite="theory/video/src: schema evolution and compatibility"), [
 "C: The contract format. One reviewed repository, with an open A-P-I description for calls and a protocol buffer schema for events.", P,
 "C: What it is built from: each contract is a schema file with an owner, and the pipeline compares every change to the last released version.", P,
 "C: It fails on a removed field, a changed type, or a new required field.", P, "C: A wiki page per contract is the thing an interviewer names. It fails because nothing checks it, and it drifts in the first week.", P,
 "C: Sharing source code between teams couples their release dates and languages."])

S(tech("Tools · consumer-driven tests", "The consumer writes the test the provider must pass", ("Consumer contract tests run in the provider’s CI", "A consumer records the exact calls it makes; the provider’s build replays them."),
  "A consumer registers its expected requests and responses in the hub. The provider's pull request runs them all, and a failure names the consumer. A mock server serves the same file.",
  [("End-to-end tests only", "slow, flaky, and they find the break after merge"), ("A manual compatibility review", "does not scale to ten pairs")],
  cite="theory/video/src: testing at service boundaries"), [
 "C: Consumer-driven tests. The consumer writes the test, and the provider has to pass it.", P,
 "C: How it works: a consumer records the exact calls it makes, the provider's build replays them, and a failure names the consumer.", P,
 "C: The same file serves the mock server, so one artefact does two jobs.", P, "C: End-to-end tests alone are what an interviewer names. They are slow and flaky, and they find the break after the merge.", P,
 "C: A manual compatibility review does not scale to ten pairs of teams."])

S(tech("Tools · decisions and health", "A short decision record, and a dashboard of three numbers", ("A one-page decision record, and a weekly dashboard", "Every cross-team decision is written in a page, with a clock; three numbers show split health."),
  "A decision record has a proposal, the options, a deadline of two days for objections, and a named decider. The dashboard shows cross-team pull requests, lead time, and meeting hours per engineer.",
  [("Escalation by meeting", "two hours per dispute, and no record"), ("Status reports", "all green until the date is missed")],
  cite="theory/video/src: observability for the organisation"), [
 "C: Decisions and health. A one-page decision record, and a dashboard of three numbers.", P,
 "C: How it works: a proposal, the options, two days for objections, and a named decider. The dashboard shows cross-team pull requests, lead time, and meeting hours per engineer.", P,
 "C: Escalation by meeting is the alternative, at two hours per dispute and with no record.", P, "C: And status reports are all green until the date is missed."])

subchapter("5.2", "When you don't need all this", ["C: Before I break it, the simpler design, and the number at which the full one becomes necessary."])
S(dia("Alternate path", "One team, a modular monolith, for the first stretch", "alt", cap="Figure 5.6 — ALTERNATE: one team of eight, modules with interfaces in code", ), [
 "C: This is the alternate path. It is not the baseline.", P,
 "C: One team of eight builds a modular monolith, with module boundaries as interfaces in code.", P,
 "C: Those module contracts are the same contracts, only cheaper to change, and not yet owned by different teams.", P,
 "C: What it gives up: nothing ships in parallel, so it caps at about a dozen engineers. Split when headcount passes twelve, or when three modules are hot at once. Below that, I would ship this."], cls="dia alt")
