from dsl import *
import dsl
P = "[+]"
def th(): dsl.SL[-1]["cls"] = (dsl.SL[-1]["cls"] + " theory").strip()

props(S1="no-silent-break", S2="one-owner-each", L1="no-team-waits", L2="integrated-by-week-4", L3="wrong-split-seen-early")

chapter(3, "Theory", 2, "What makes a split hard, in words that outlive any org chart", [
 "C: A short theory chapter before the design. What a decomposition is and is not, the properties, the central tension, six mechanisms each with the picture that fits it, and the options, one slide each. The failures come later, as the challenges."]); th()

key("Theory · 1 of 5 · what it is", "A division of the work into <em>teams that can ship alone</em>, joined by <em>explicit contracts</em>, with <em>one owner</em> for everything shared, and a way to <em>see early</em> that the cut is wrong.", [
 "V: A decomposition is a division of the work into teams that can ship alone, joined by explicit contracts, with one owner for everything shared, and a way to see early that the cut is wrong.", "[pause: 1.0]",
 "C: Every clause does work. Ship alone: the test is delivery, not tidiness. Explicit contracts: an arrow nobody wrote down is a surprise at month five. One owner: shared means nobody's. See early: a wrong split is cheap in week four and ruinous in month five."], cls="theory")

S(plain("Theory · 1 of 5 · what it is not", "Four things it is confused with", cards(
  ("", "Not an org chart", "Who reports to whom is one input. A decomposition is also what each team owns and what it promises the others."),
  ("amb", "Not an architecture diagram", "Boxes show components. A decomposition also says which team changes them, and who must agree."),
  ("red", "Not a task list", "Assigning components to people leaves the arrows unmanaged, which is where the slips are."),
  ("", "Not microservices", "Five teams do not need twelve services. A boundary is a cost, and it is expensive to move."))), [
 "C: Four neighbours it is confused with.", P,
 "C: It is not an org chart: reporting lines are one input.", P,
 "C: It is not an architecture diagram: the boxes also need a team, and a statement of who must agree.", P,
 "C: It is not a task list: assigning components leaves the arrows unmanaged, and the arrows are where the slips are.", P,
 "C: And it is not microservices: five teams do not need twelve services, and a boundary is expensive to move."], cls="theory")

S(plain("Theory · 2 of 5 · the two properties", "State safety and liveness separately",
  '<div class="prop safe"><div class="lbl">Safety · must never happen</div><p>' + pid("S1") + ' A change on one side breaks a consumer, and nobody finds out before release.<br>' + pid("S2") + ' A component, contract or table has no owner, or two.</p></div>'
  '<div class="prop live"><div class="lbl">Liveness · must eventually happen</div><p>' + pid("L1") + ' Every team has unblocked work every week.<br>' + pid("L2") + ' An end-to-end path runs by week four and stays green.<br>' + pid("L3") + ' A wrong cut is visible by month two.</p></div>'), [
 "[+]", "C: Two safety properties, things that must never happen. " + ps("S1") + ": a change on one side breaks a consumer, and nobody finds out before release. " + ps("S2") + ": a component, a contract or a table with no owner, or with two.", "[+]",
 "C: Three liveness properties, things that must eventually happen. " + ps("L1") + ": every team has unblocked work every week. " + ps("L2") + ": an end-to-end path runs by week four and stays green. " + ps("L3") + ": a wrong cut is visible by month two.",
 "C: Every fix from here on names the tag of the property it serves."], cls="theory")

S(plain("Theory · 3 of 5 · the central tension", "Autonomy against coherence", table(["Pull toward", "What you gain", "What it costs"], [
  ["<b>More autonomy</b>", "teams ship alone; fewer meetings", "duplicated logic; contracts to keep stable; drift"],
  ["<b>More coherence</b>", "one model, one style, easy to reason about", "every change needs a meeting; teams wait"],
  ["<b>The cut decides</b>", "where autonomy is free, where coherence is paid for", "a wrong cut pays both"]], "bt sm") +
  line("Cut so that what changes together lives together, and pay for coherence only at the seams.", "a")), [
 "C: The central tension is autonomy against coherence.", P,
 "C: Toward autonomy, teams ship alone and meet less. The cost is duplication, contracts to keep stable, and drift.", P,
 "C: Toward coherence, there is one model and one style. The cost is that every change needs a meeting and teams wait.", P,
 "C: The cut decides where autonomy is free and where coherence is paid for. A wrong cut pays both.", P,
 "C: So: what changes together lives together, and coherence is paid for only at the seams."], cls="theory")

def M(n, name, kind, svg, cap, prot, how, rules, costs, say, steps_say, live=False):
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    for s in steps_say: lines += ["[+]", "C: " + s]
    mech_slide(n, 6, name, prot, how, rules, costs, lines, diagram=(kind, svg, cap), live=live)

M(1, "Seams by domain, not by layer", "c4", "m-seams", "Figure 3.1 — C4 container view: four domain teams, three boundaries",
  pid("L1") + ".", "Group what changes together into one team: a domain with its logic, data and integrations. Conway’s law: the system will copy the org, so choose both at once.",
  "Every feature needing every team; a dependency web hidden by a tidy diagram.", "Some duplication across domains, and a domain model that must be argued first.",
  ["Mechanism one, seams by domain, not by layer, drawn as the containers and the boundaries between them.", "It protects " + ps("L1") + ".",
   "Group what changes together into one team: a domain, with its logic, its data and its integrations. Conway's law says the system will copy the organisation, so I choose both at once.",
   "It rules out every feature needing every team.", "It costs some duplication across domains, and a domain model that has to be argued first."],
  ["Servicing core owns the ledger and the schedule: one team.", "Collections owns dispatch and the rails.", "Reconciliation owns files and breaks.",
   "Policy and A-P-I owns quotes and terms. Three boundaries, each an event or one call: that is the whole arrow budget."], live=True)
M(2, "Contracts first, versioned", "erd", "m-contract", "Figure 3.2 — the contract record: owner, versions, consumers, sunset",
  pid("S1") + ".", "Every seam is a contract with an owner, a schema, a compatibility policy (additive only) and a sunset date. Agreed before code starts.",
  "Two teams assuming different shapes; a rename that breaks a consumer.", "Up-front agreement work in weeks one and two, and the discipline of additive change.",
  ["Mechanism two, contracts first, versioned, drawn as the record we keep for each one.", "It protects " + ps("S1") + ".",
   "Every seam is a contract with an owner, a schema, a compatibility policy, additive changes only, and a sunset date. Agreed before code starts.",
   "It rules out two teams assuming different shapes, and a rename that breaks a consumer.", "It costs agreement work in weeks one and two, and the discipline of additive change."],
  ["The contract has one owner team and a kind: an event or an H-T-T-P-S call.", "Each version has a schema, a deprecation date and a sunset date.", "And each version lists its consumers and the test that proves they still work."])
M(3, "Consumer-driven tests and mocks", "seq", "m-cdct", "Figure 3.3 — a provider's rename is stopped by a consumer's test",
  pid("S1") + " and " + pid("L1") + ".", "Consumers register the calls they rely on. The provider’s CI runs every consumer test. A mock server from the contract lets a consumer build before the provider exists.",
  "A breaking change reaching release; a team idle for a missing API.", "A contract hub to run, and tests the consumers must write.",
  ["Mechanism three, consumer-driven tests and mocks, at the level of the build pipeline.", "It protects " + ps("S1") + " and " + ps("L1") + ".",
   "Consumers register the calls they rely on. The provider's pipeline runs every consumer's test. And a mock server generated from the contract lets a consumer build before the provider exists.",
   "It rules out a breaking change reaching release, and a team idle for a missing A-P-I.", "It costs a contract hub to run, and tests the consumers must write."],
  ["The consumer publishes the calls it relies on.", "The provider opens a pull request: rename a field.", "Its pipeline asks the hub to run every consumer's test.", "Two consumers fail.",
   "The merge is blocked, and the consumers are named.", "The teams agree an additive change: the old field stays.", "The tests pass, and nobody was surprised."], live=True)
M(4, "One owner for every shared thing", "c4", "m-owner", "Figure 3.4 — the shared ledger has one owner; others call it",
  pid("S2") + ".", "The shared schema, library or ledger belongs to exactly one team. Others use it only through its contract. Changes go through the owner.",
  "A table edited by three teams; a shared thing that is nobody’s problem.", "The owner becomes a queue unless its contract is rich enough.",
  ["Mechanism four, one owner for every shared thing, drawn around the ledger.", "It protects " + ps("S2") + ".",
   "The shared schema, library or ledger belongs to exactly one team. Everyone else reaches it only through its contract, and changes go through the owner.",
   "It rules out a table edited by three teams, and a shared thing that is nobody's problem.", "It costs a risk: the owner can become a queue, unless the contract is rich enough."],
  ["The servicing core team owns the ledger and its schema.", "Collections posts through a call, never into the table.", "And so does Reconciliation."])
M(5, "An end-to-end skeleton first", "c4", "m-skel", "Figure 3.5 — a thin path through four boxes, week by week",
  pid("L2") + ".", "A walking skeleton: one thin request through every team’s component, with stubs and mocks, running in week four, then thickened.",
  "A six-month plan that learns it does not fit in month five.", "Early throw-away stubs, and teams who must agree before they feel ready.",
  ["Mechanism five, an end-to-end skeleton first, as the thinnest path through the system.", "It protects " + ps("L2") + ".",
   "One thin request through every team's component, with stubs and mocks where needed, running in week four, and then thickened every week.",
   "It rules out a six-month plan that finds out it does not fit in month five.", "It costs throw-away stubs, and teams who must agree before they feel ready."],
  ["The A-P-I stub books a loan, in week one.", "The servicing core is thin, in week two.", "Collections uses a mock rail, in week three.", "And in week four the rail sandbox answers: green end to end."])
M(6, "Leading indicators and one re-cut", "state", "m-health", "Figure 3.6 — split health: friction is visible, and the cut can move once",
  pid("L3") + ".", "Watch cross-team pull requests, lead time and meeting load weekly. Two weeks of friction triggers one review, and at most one re-cut.",
  "A wrong split discovered by a missed date.", "A weekly dashboard, and the humility to move a seam.",
  ["Mechanism six, leading indicators and one re-cut, drawn as a state machine of the split's health.", "It protects " + ps("L3") + ".",
   "I watch cross-team pull requests, lead time and meeting load every week. Two weeks of friction triggers one review, and I allow at most one re-cut.",
   "It rules out discovering a wrong split by missing a date.", "It costs a weekly dashboard, and the humility to move a seam."],
  ["Healthy is the start state.", "Friction appears when cross-team pull requests rise. A contract fix returns it to healthy.", "Two weeks without change opens a review. A false alarm returns to healthy.", "Or the seam moves, once, and the split is healthy again."], live=True)

def O(letter, name, verdict, pros, cons, pits, svg, say, pick=False):
    lines = ["C: " + say[0]]
    for s in say[1:]: lines += ["[+]", "C: " + s]
    option_slide(letter, name, verdict, pros, cons, pits, svg, lines, pick=pick)

O("A", "Split by technical layer", "Rejected · every feature needs every team", ["Specialists stay together", "Easy to staff"], ["Every feature crosses all teams"],
  ["Three to four weeks of latency per feature", "No team can ship alone"], "opt-a", [
  "Option A, the classic: an A-P-I team, a logic team, a data team.",
  "Specialists stay together.", "And it is easy to staff.", "But every feature crosses every team.",
  "The pitfall: three to four weeks of latency for a single feature.", "And no team can ship alone, which was the point.",
  "One layer on top of the next.", "Every feature goes down the stack.", "Through the same three teams."])
O("B", "Split by domain, vertical", "The pick · with a platform team where it earns its keep", ["A team can ship a feature alone", "Matches how the domain changes"], ["Some duplication", "A domain model to agree first"],
  ["A wrong domain cut is expensive to move", "A shared ledger needs one owner"], "opt-b", [
  "Option B, the pick: teams cut by domain, each owning logic, data and integrations for its domain.",
  "A team can ship a feature alone.", "It matches how the domain changes.", "It costs some duplication.", "And a domain model to agree first.",
  "The pitfall: a wrong domain cut is expensive to move.", "And the shared ledger needs exactly one owner.",
  "Servicing core, with Collections and Reconciliation beside it.", "Each boundary is an event, not a shared table."], pick=True)
O("C", "Feature teams, shared everything", "Rejected · no owners", ["Maximum flexibility", "No hand-offs by design"], ["No ownership", "Merge conflicts become the coordination"],
  ["Two teams change one table the same week", "Nobody is paged for the shared code"], "opt-c", [
  "Option C, feature teams on one codebase, with no owners.",
  "It is flexible, with no hand-offs by design.", "But nobody owns anything.", "And merge conflicts become the coordination.",
  "The pitfall: two teams change one table in the same week.", "And nobody is paged for the shared code.",
  "One codebase.", "One database that anyone edits."])
O("D", "Twelve services, one per entity", "Rejected · over-decomposed", ["Small, replaceable parts"], ["Twelve contracts to version", "Network failure between everything"],
  ["Five teams own two or three each: more arrows, not fewer", "Boundaries drawn before the domain is understood"], "opt-d", [
  "Option D, twelve services, one per entity.",
  "Small, replaceable parts.", "But twelve contracts to version.", "And network failure between everything.",
  "The pitfall: five teams own two or three each, so there are more arrows, not fewer.", "And boundaries are drawn before the domain is understood.",
  "Five teams.", "Own twelve services.", "Behind twelve contracts."])
O("E", "Platform team plus stream teams", "Rejected for now · the honest next step at 100 engineers", ["Paved road for everyone", "Stream teams own a domain end to end"], ["A platform team to staff and fund", "Overhead before it pays"],
  ["Platform becomes a ticket queue", "Too early at forty engineers"], "opt-e", [
  "Option E, a platform team beside stream teams, the shape larger organisations grow into.",
  "It gives everyone a paved road.", "And stream teams own a domain end to end.", "It needs a platform team to staff and fund.", "And it is overhead before it pays.",
  "The pitfall: the platform becomes a ticket queue.", "And at forty engineers it is too early.",
  "The platform team serves the stream teams.", "Two stream teams, each owning a domain.", "Joined by a contract."])

S(plain("Theory · 5 of 5 · the options, side by side", "The matrix, as a summary", table(["Approach", "Ship alone", "Arrows", "Fails when"], [
  ("rej", ["A · by layer", "no", "every feature", "any feature is requested"]),
  ("pick", ["B · by domain, vertical", "yes", "3 to 5", "the domain cut is wrong, and found late"]),
  ("rej", ["C · feature teams, shared everything", "no owners", "implicit", "two teams edit one table"]),
  ("rej", ["D · twelve services", "yes", "12 or more", "five teams carry twelve contracts"]),
  ("rej", ["E · platform plus streams", "yes", "few", "the programme is under 100 engineers"])], "bt sm mx")), [
 "C: The five side by side, as a summary only.", P, "C: A fails when any feature is requested.", P, "V: B is the pick.", P,
 "C: C fails when two teams edit one table.", P, "C: D fails when five teams carry twelve contracts.", P,
 "C: E is the honest next step, and fails only because we are under a hundred engineers."], cls="theory")

S(plain("Theory · 5 of 5 · the pick", "B, and what it gives up", '<div class="cards c2">'
  '<div class="cd grn"><h3>What B buys</h3><p>A feature usually touches one team. Contracts sit only where change is rare. Every team has a domain it can own and be paged for.</p></div>'
  '<div class="cd red"><h3>What B gives up</h3><p>Some duplication. A domain model to agree up front. A shared ledger that needs one owner and a rich contract. A wrong cut that costs a re-cut.</p></div></div>' +
  line("Choose A only for a tiny, one-feature programme. Choose E when the programme passes a hundred engineers.", "a")), [
 "C: What B buys: a feature usually touches one team, contracts sit where change is rare, and every team has a domain it can own and be paged for.", P,
 "C: What it gives up: some duplication, a domain model to agree up front, a shared ledger that needs one owner and a rich contract, and a wrong cut that costs one re-cut.", P,
 "C: So in the room I would say: A only for a tiny programme, and E once we pass a hundred engineers. At forty, B."], cls="theory")

S(plain("Theory · what each mechanism serves", "Every mechanism names its property", table(["Mechanism", "Serves", "Where it returns"], [
  ["M1 Seams by domain", pid("L1"), "chapter 5, challenge 1"],
  ["M2 Contracts first, versioned", pid("S1"), "chapter 4, challenge 4"],
  ["M3 Consumer tests and mocks", pid("S1") + " " + pid("L1"), "challenges 1 and 2"],
  ["M4 One owner for shared things", pid("S2"), "challenge 3"],
  ["M5 End-to-end skeleton", pid("L2"), "chapter 5, challenge 5"],
  ["M6 Leading indicators, one re-cut", pid("L3"), "challenge 6"]], "bt xs") +
  grade("A mechanism with no stated property is decoration. Say which one each fix serves.")), [
 "C: The vocabulary in one table.", P, "C: Seams by domain serve " + ps("L1") + ".", P, "C: Contracts first serve " + ps("S1") + ".", P,
 "C: Consumer tests and mocks serve " + ps("S1") + " and " + ps("L1") + ".", P, "C: One owner serves " + ps("S2") + ".", P,
 "C: The skeleton serves " + ps("L2") + ".", P, "C: And leading indicators serve " + ps("L3") + ".", P,
 "N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back."], cls="theory")
