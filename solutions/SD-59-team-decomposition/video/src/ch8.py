from dsl import *
P = "[+]"

chapter(8, "Recap and follow-ups", 6, "One picture, five paths, the mistakes, the thesis, and what to expect next", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, the four sentences, and the follow-up questions."])

S(plain("Recap · one sentence per path", "Five paths", table(["Path", "In one sentence"], [
  ["<b>Seams</b>", "domain clusters of what changes together, one team and one named owner each"],
  ["<b>Contracts</b>", "versioned before code, additive only, with a sunset date and a consumer test"],
  ["<b>Unblock</b>", "a mock from the contract in week two; the critical path named and owned"],
  ["<b>Integrate</b>", "a thin end-to-end skeleton green by week four, thickened weekly"],
  ["<b>Detect</b>", "three leading indicators, thresholds set in advance, one re-cut allowed"]], "bt")), [
 "C: One sentence per path. Seams: domain clusters of what changes together, one team and one named owner each.", P,
 "C: Contracts: versioned before code, additive only, with a sunset date and a consumer test.", P,
 "C: Unblock: a mock from the contract in week two, and the critical path named and owned.", P,
 "C: Integrate: a thin end-to-end skeleton, green by week four.", P,
 "C: Detect: three leading indicators with thresholds set in advance, and one re-cut allowed."])

S(plain("Recap · what I own", "What I do not delegate", '<div class="cards c2">'
  '<div class="cd"><h3>The contracts</h3><p>I approve every cross-team contract and its sunset. Teams own the content; I own that they exist.</p></div>'
  '<div class="cd"><h3>The dependency graph</h3><p>I keep the table of who needs what by when, and I read it every week.</p></div>'
  '<div class="cd amb"><h3>The integration milestones</h3><p>Week four skeleton, month three review, month five release candidate.</p></div>'
  '<div class="cd red"><h3>The escalation path</h3><p>The decision protocol, and the tie-break. I run the protocol, not every verdict.</p></div></div>'), [
 "C: What I do not delegate.", P, "C: The contracts. Teams own the content, and I own that they exist and have a sunset.", P,
 "C: The dependency graph. I keep it, and I read it every week.", P, "C: The integration milestones: week four, month three, month five.", P,
 "C: And the escalation path: I run the protocol, not every verdict."])

S(plain("Recap · common mistakes in this round", "What costs candidates the most", '<div class="cards c2">'
  '<div class="cd red"><h3>On the split</h3><p>Splitting by layer. Twelve services for five teams. Shared tables with no owner. Re-shuffling the teams every quarter.</p></div>'
  '<div class="cd red"><h3>On the manager’s role</h3><p>Assigning everything and owning nothing. Integration as a phase at the end. Status reports instead of leading indicators. Escalation by meeting.</p></div></div>'), [
 "C: The common mistakes. On the split: splitting by layer, twelve services for five teams, shared tables with no owner, and re-shuffling teams every quarter.", P,
 "C: On the manager's role: assigning everything and owning nothing, integration as a phase at the end, status reports in place of leading indicators, and escalation by meeting."])

S(plain("Recap · the four sentences", "If you have thirty seconds", '<div class="cards c2">'
  '<div class="cd"><h3>What</h3><p>Domain teams with one owner each, joined by versioned, additive-only contracts.</p></div>'
  '<div class="cd amb"><h3>The pace</h3><p>Mocks from the contract in week two; a skeleton green by week four.</p></div>'
  '<div class="cd red"><h3>The risk</h3><p>A wrong cut, found late. Three indicators and one re-cut are the defence.</p></div>'
  '<div class="cd grn"><h3>What I own</h3><p>The contracts, the dependency graph, the milestones, and the escalation path.</p></div></div>'), [
 "C: If I had thirty seconds. Domain teams with one owner each, joined by versioned, additive-only contracts.", P,
 "C: The pace: mocks from the contract in week two, and a skeleton green by week four.", P,
 "C: The risk is a wrong cut found late, and the defence is three indicators and one re-cut.", P,
 "C: And what I own: the contracts, the dependency graph, the milestones and the escalation path."])

followups([
 ("What if three teams are new to the domain and none can own the ledger?", "Challenge 3; the second fix on the owner queue"),
 ("When does a platform team start to pay for itself?", "Option E; the pick slide"),
 ("How do you keep the contract hub from becoming a bottleneck?", "Challenge 1, second fix; mechanism three"),
 ("How do you change the split when the product pivots?", "Mechanism six; challenge 6"),
 ("What would you cut if the date moved up by a month?", "Challenge 5, second fix"),
 ("How does this change with eight teams, or two?", "The alternate path; option E")], [
 "N: Questions you should be ready for next. Each points to where this video answers it.", P, "C: Three teams new to the domain and none able to own the ledger: challenge three and its second fix.", P,
 "C: When a platform team pays for itself: option E.", P, "C: Keeping the hub from becoming a bottleneck: challenge one, and mechanism three.", P,
 "C: A pivot: mechanism six, and challenge six.", P, "C: A date that moves up a month: challenge five.", P, "C: And eight teams, or two: the alternate path, and option E."])

key("The thesis, again", "Cut along <em>domain seams</em>, put a versioned <em>contract</em> on every one, give shared things <em>one owner</em>, integrate <em>by week four</em>, and keep the <em>contracts, graph and milestones</em> yourself.", [
 "V: Cut along domain seams. Put a versioned contract on every one. Give shared things one owner. Integrate by week four. And keep the contracts, the graph and the milestones yourself.", "[pause: 1.5]"])
