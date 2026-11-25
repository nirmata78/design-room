from dsl import *
P = "[+]"

# ───────────────────────── 0 · cold open ─────────────────────────
chapter(0, "Cold open", -1, "Forty engineers, five teams, six months", [
 "C: This is the question that follows a design round. You have just designed a system, and now the interviewer hands you forty engineers and says: split the work. It is asked of managers and principals because the hard part is not the boxes. It is the arrows between the teams."])

qs("Interviewer · the prompt", "“You’re given a large system to build, say the one we just designed, and forty engineers across five teams. How do you split the work so those teams can move independently, and what do you own as the manager?”", [
 "I: You're given a large system to build, say the one we just designed, and forty engineers across five teams. How do you split the work so those teams can move independently, and what do you own as the manager?", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "A diagram that is clean, and a plan that is not", "opt-a",
      chip=chips("clean on a diagram", "every feature needs every team")), [
 "C: Here is the hook. This split looks clean: an A-P-I team on top, a logic team, a data team. It is the classic wrong answer, and the picture shows why.", P,
 "C: One layer on top of the next.", P, "C: Every feature goes down the whole stack, through the same three teams. A clean diagram, and a dependency web. The whole answer is about avoiding this."], cls="dia")

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Seams</b>", "Splits by technical layer; assigns components", "Cuts by domain; says Conway’s law in their own words; chooses org and architecture together"],
  ["<b>Contracts</b>", "“The teams will agree on an API”", "Contracts versioned before code; additive-only policy; consumer-driven tests"],
  ["<b>Unblocking</b>", "A team waits for the one it depends on", "Mocks against the contract; critical path named; nobody idle"],
  ["<b>Integration</b>", "An integration phase at the end", "A thin end-to-end skeleton in the first weeks"],
  ["<b>Ownership</b>", "Assigns all the work, keeps nothing", "Names what the manager owns: contracts, graph, milestones, escalation"]], "bt xs sig") +
  grade("A candidate who reserves nothing for themselves has not understood the question.")), [
 "N: Five axes.", P,
 "N: Seams. Weak: splitting by layer. Strong: cutting by domain, and stating Conway's law in their own words.", P,
 "N: Contracts. Weak: the teams will agree on an A-P-I. Strong: versioned before code, additive changes only, tests owned by the consumer.", P,
 "N: Unblocking. Weak: a team waits for another. Strong: mocks against the contract, and nobody idle.", P,
 "N: Integration. Weak: a phase at the end. Strong: a thin end-to-end path in the first weeks.", P,
 "N: Ownership. Weak: assigning everything, reserving nothing. Strong: naming what the manager owns, and not delegating it.", P,
 "C: My rule for the round: choose the architecture and the org chart together, because they will converge anyway."])

key("The thesis", "Cut along <em>domain seams</em>, make every seam an explicit, versioned <em>contract</em>, give every shared thing <em>one owner</em>, integrate <em>end to end by week four</em>, and keep the contracts, the graph and the milestones <em>for yourself</em>.", [
 "V: Cut along domain seams. Make every seam an explicit, versioned contract. Give every shared thing one owner. Integrate end to end by week four. And keep the contracts, the dependency graph and the milestones for yourself.", "[pause: 1.0]"])

# ───────────────────────── 1 · requirements ─────────────────────────
chapter(1, "Requirements and scope", 0, "The scale first, then five questions", [
 "C: The scale first, then five questions. Each answer moves the plan."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>40 · 5 · 3</b><span>engineers · teams · time zones</span></div>'
  '<div class="tile"><b>6 months</b><span>to the first release: 240 engineer-months</span></div>'
  '<div class="tile red"><b>2</b><span>external teams consume the output</span></div></div>' +
  line("Every number later starts from one of these, and I will say which.", "a")), [
 "C: The interviewer gives me the scale and I write it down first.", P,
 "C: Forty engineers in five teams of eight, across three time zones.", P,
 "C: Six months to the first release. Forty engineers times six months is two hundred and forty engineer-months to spend.", P,
 "C: And two external teams depend on what we ship, so a contract is not only internal.", P,
 "C: Every number I use later starts from one of these three, and I will say which."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "What are we optimising the split for?", "Independent delivery. Teams should ship a feature without waiting for another team.",
     "What am I optimising the split for?", "Independent delivery. A team should be able to ship a feature without waiting for another.",
     "Then the measure of a good split is how rarely a change needs two teams, not how tidy the boxes look.")
clar(2, "What do the teams already know?", "Two teams know the domain; three are new to it.",
     "What do the teams already know?", "Two teams know the domain. Three are new to it.",
     "So risk and experience have to be matched: the hard domains to the two who know it.")
clar(3, "Can I change the team structure?", "Yes, once, at the start.",
     "Can I change the team structure?", "Yes, once, at the start.",
     "Then I treat org and architecture as one decision, made once, and I do not plan to re-shuffle later.")
clar(4, "Where are the teams?", "Three time zones. Pairs overlap two hours a day; all three never do.",
     "Where are the teams?", "Three time zones. Any two overlap a couple of hours. All three never overlap.",
     "So the seams that cross time zones must be the most stable contracts, and the tightly coupled pieces share a zone.")
clar(5, "Who depends on us?", "Two external teams: one consumes loan events, one reads reconciliation breaks.",
     "Who depends on us?", "Two external teams. One consumes loan events. One reads reconciliation breaks.",
     "Those two are consumers from day one, so their contracts are the first ones I freeze.")

S(plain("Requirements · what the split must achieve", "Five things, and the numbers on them", table(["#", "Requirement", "Number"], [
  ["<b>FR1</b>", "Choose seams: a team for each cluster that changes together", "a feature touches ≤ 2 teams, on average"],
  ["<b>FR2</b>", "Make every seam an explicit, versioned contract", "contracts agreed by week 2"],
  ["<b>FR3</b>", "Keep every team unblocked", "no team idle more than 2 days"],
  ["<b>FR4</b>", "Integrate early and continuously", "end to end green by week 4"],
  ["<b>FR5</b>", "Detect a wrong split and re-cut once", "signal by month 2"]], "bt sm") +
  line("Non-functional: first release in 6 months; contract changes announced 2 weeks ahead; cross-zone seams are the most stable.", "a")), [
 "C: Functionally, five things.", P, "C: One, choose seams: a team for each cluster that changes together, so a feature touches two teams or fewer on average.", P,
 "C: Two, make every seam an explicit, versioned contract, agreed by week two.", P, "C: Three, keep every team unblocked: nobody idle more than two days.", P,
 "C: Four, integrate early: end to end green by week four.", P, "C: Five, detect a wrong split by month two, and be able to re-cut it once.", P,
 "C: Non-functionally: the first release in six months, contract changes announced two weeks ahead, and the seams that cross time zones are the most stable."])

S(plain("Requirements · scope", "In, and out on purpose", '<div class="cards c2">'
  '<div class="cd grn"><h3>In scope</h3><p>Team boundaries · contracts and their versioning · ownership of shared things · the dependency graph · sequencing against skills · integration · what I own.</p></div>'
  '<div class="cd red"><h3>Out, on purpose</h3><p>The system’s internal design (SD-95 did that) · hiring and promotions · tooling procurement · individual performance.</p></div></div>'), [
 "C: Scope, said aloud.", P,
 "C: In: team boundaries, contracts and their versioning, ownership of shared things, the dependency graph, sequencing against skills, integration, and what I own personally.", P,
 "C: Out, on purpose: the system's internal design, which was the last round, and hiring, tooling procurement and individual performance. They matter, but they are not this question."])

S(dia("Requirements · C4 level 1", "The programme in its context", "ctx", cap="Figure 1.1 — the platform, the manager, and the two external consumers"), [
 "C: The C4 context. Here is the programme and everyone it touches.", P,
 "C: You: the manager, who owns the contracts, the dependency graph and the milestones.", P,
 "C: The platform itself: five teams, forty engineers, six months.", P,
 "C: The origination team, an external consumer. It receives a loan booked event. An event, not a call.", P,
 "C: The finance operations team reads reconciliation breaks, with a synchronous H-T-T-P-S call.", P,
 "C: And the card and bank rails, external A-P-Is we call. Notice the three kinds of boundary: events, calls, and the outside world."], cls="dia")

key("The core is", "Four decisions: <em>where the seams go</em>, <em>what crosses them</em>, <em>who owns what is shared</em>, and <em>when it first works end to end</em>.", [
 "V: The core is four decisions. Where the seams go. What crosses them. Who owns what is shared. And when it first works end to end.", "[pause: 1.0]"])

# ───────────────────────── 2 · estimates ─────────────────────────
chapter(2, "Estimates", 1, "Every number is arithmetic, and every number changes something", [
 "C: Estimates. I start every one from the scale line, and say which number I used. They are all illustrative until measured."])

S(plain("Estimates · the budget", "240 engineer-months, and what is actually spendable", table(["Step", "Arithmetic", "Result"], [
  ["From the scale line", "40 engineers × 6 months", "<b>240</b> engineer-months"],
  ["Overhead: on-call, meetings, leave, onboarding", "about 25 % of 240", "−60"],
  ["Spendable", "240 − 60", "<b>about 180</b>"],
  ["Per team", "180 ÷ 5", "<b>36</b> engineer-months"]], "bt sm") +
  line("Illustrative. Consequence: a team has about 4.5 working engineers for 8 months. Nobody can wait one.", "a")), [
 "C: The budget. From the scale line: forty engineers times six months is two hundred and forty engineer-months.", P,
 "C: Overhead takes about a quarter: on-call, meetings, leave, and onboarding for the three teams who are new. That is sixty, an illustrative figure.", P,
 "C: Spendable: about a hundred and eighty.", P,
 "C: Per team, thirty-six engineer-months.", P,
 "C: What it changes: a team of eight has about four and a half productive engineers over the half year. A team that waits for another team for even a month has spent a seventh of its budget."])

S(plain("Estimates · the coordination cost", "Pairs of teams, and what each arrow costs", table(["Quantity", "Arithmetic", "Consequence"], [
  ["Team pairs", "5 × 4 ÷ 2 = <b>10</b>", "ten possible relationships to manage"],
  ["Pairs that must agree", "design for <b>4 to 5</b>", "each arrow is a standing meeting"],
  ["One cross-team change", "≈ <b>1 week</b> of waiting", "illustrative: a request, a queue, a review"],
  ["A feature touching 4 teams", "4 hand-offs × 1 week", "<b>3 to 4 weeks</b> of latency"],
  ["Time zones", "3 zones, 2 h overlap", "a question costs a day"]], "bt xs") +
  line("From the scale line: five teams and three zones. The number to minimise is arrows, not boxes.", "a")), [
 "C: The coordination cost, from the same scale line: five teams.", P,
 "C: Five teams have ten possible pairs.", P,
 "C: I design so only four or five of them ever have to agree. Every extra arrow is a standing meeting.", P,
 "C: One cross-team change costs about a week of waiting. A request, a queue, a review. That is illustrative, and I would measure it.", P,
 "C: So a feature that touches four teams has three to four weeks of latency, before anyone writes code.", P,
 "C: And in three time zones with two hours of overlap per pair, a question costs a day. The number to minimise is the number of arrows, not the number of boxes."])

S(plain("Estimates · the integration budget", "When integration goes last, the slip lands last", table(["Plan", "When the first mismatch is found", "Cost to fix"], [
  ["Integrate at month 5", "month 5", "<b>re-work across teams</b>, 1 month left"],
  ["Skeleton at week 4", "week 4", "a day inside two teams"],
  ["Ratio", "months of drift compared with weeks", "<b>about 10× cheaper</b>, illustrative"]], "bt sm") +
  line("A six-month programme slips at the end. The only defence is to find the mismatch in the first month.", "a")), [
 "C: One more number. If integration happens at month five, the first mismatch is found with one month left, and it costs re-work across teams.", P,
 "C: With an end-to-end skeleton at week four, the same mismatch costs a day inside two teams.", P,
 "C: That ratio, about ten to one, is illustrative, but the direction is not in doubt. That is why integration is a requirement here, not a phase."])
