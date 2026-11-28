# SD-59 Multi-team decomposition and API contracts: reference solution (Principal / senior EM, compact cut)

<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next
     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- names: C=Candidate V=Candidate N=Coach I=Interviewer -->
<!-- say: SLO=S-L-O SLOs=S-L-Os SLI=S-L-I API=A-P-I APIs=A-P-Is HTTP=H-T-T-P HTTPS=H-T-T-P-S ID=I-D IDs=I-Ds EM=E-M PR=P-R PRs=P-Rs CI=C-I ADR=A-D-R ADRs=A-D-Rs RFC=R-F-C OpenAPI=Open-A-P-I protobuf=proto-buff Pact=Pact SDK=S-D-K UTC=U-T-C p99=P-ninety-nine QA=Q-A -->


## 0 Cold open

[slide: v-001]
[pause: 1.2]
C: This is the question that follows a design round. You have just designed a system, and now the interviewer hands you forty engineers and says: split the work. It is asked of managers and principals because the hard part is not the boxes. It is the arrows between the teams.
[pause: 1.8]

[slide: v-002]
[pause: 0.6]
I: You're given a large system to build, say the one we just designed, and forty engineers across five teams. How do you split the work so those teams can move independently, and what do you own as the manager?
[pause: 1.5]

[slide: v-003]
[pause: 1.3]
C: Here is the hook.
C: This split looks clean: an A-P-I team on top, a logic team, a data team.
[reveal: v-004]
[pause: 0.45]
C: It is the classic wrong answer, and the picture shows why.
C: One layer on top of the next.
[reveal: v-005]
[pause: 0.45]
C: Every feature goes down the whole stack, through the same three teams.
C: A clean diagram, and a dependency web.
C: The whole answer is about avoiding this.
[pause: 1.1]

[slide: v-006]
[pause: 1.0]
N: Five axes.
[reveal: v-007]
[pause: 0.45]
N: Seams. Weak: splitting by layer. Strong: cutting by domain, and stating Conway's law in their own words.
[reveal: v-008]
[pause: 0.45]
N: Contracts. Weak: the teams will agree on an A-P-I. Strong: versioned before code, additive changes only, tests owned by the consumer.
[reveal: v-009]
[pause: 0.45]
N: Unblocking. Weak: a team waits for another. Strong: mocks against the contract, and nobody idle.
[reveal: v-010]
[pause: 0.45]
N: Integration. Weak: a phase at the end. Strong: a thin end-to-end path in the first weeks.
[reveal: v-011]
[pause: 0.45]
N: Ownership. Weak: assigning everything, reserving nothing. Strong: naming what the manager owns, and not delegating it.
[reveal: v-012]
[pause: 0.45]
C: My rule for the round: choose the architecture and the org chart together, because they will converge anyway.
[pause: 1.0]

[slide: v-013]
[pause: 0.7]
V: Cut along domain seams. Make every seam an explicit, versioned contract. Give every shared thing one owner. Integrate end to end by week four. And keep the contracts, the dependency graph and the milestones for yourself.
[pause: 1.6]

[pause: 1.4]

## 1 Requirements and scope

[slide: v-014]
[pause: 1.2]
C: The scale first, then five questions. Each answer moves the plan.
[pause: 1.8]

[slide: v-015]
[pause: 0.6]
C: The interviewer gives me the scale and I write it down first.
[reveal: v-016]
[pause: 0.45]
C: Forty engineers in five teams of eight, across three time zones.
[reveal: v-017]
[pause: 0.45]
C: Six months to the first release. Forty engineers times six months is two hundred and forty engineer-months to spend.
[reveal: v-018]
[pause: 0.45]
C: And two external teams depend on what we ship, so a contract is not only internal.
[reveal: v-019]
[pause: 0.45]
C: Every number I use later starts from one of these three, and I will say which.
[pause: 0.8]

[slide: v-020]
[pause: 0.6]
C: What am I optimising the split for?
[reveal: v-021]
[pause: 0.45]
I: Independent delivery. A team should be able to ship a feature without waiting for another.
C: Then the measure of a good split is how rarely a change needs two teams, not how tidy the boxes look.
[pause: 0.6]

[slide: v-022]
[pause: 0.6]
C: What do the teams already know?
[reveal: v-023]
[pause: 0.45]
I: Two teams know the domain. Three are new to it.
C: So risk and experience have to be matched: the hard domains to the two who know it.
[pause: 0.6]

[slide: v-024]
[pause: 0.6]
C: Can I change the team structure?
[reveal: v-025]
[pause: 0.45]
I: Yes, once, at the start.
C: Then I treat org and architecture as one decision, made once, and I do not plan to re-shuffle later.
[pause: 0.6]

[slide: v-026]
[pause: 0.6]
C: Where are the teams?
[reveal: v-027]
[pause: 0.45]
I: Three time zones. Any two overlap a couple of hours. All three never overlap.
C: So the seams that cross time zones must be the most stable contracts, and the tightly coupled pieces share a zone.
[pause: 0.6]

[slide: v-028]
[pause: 0.6]
C: Who depends on us?
[reveal: v-029]
[pause: 0.45]
I: Two external teams. One consumes loan events. One reads reconciliation breaks.
C: Those two are consumers from day one, so their contracts are the first ones I freeze.
[pause: 0.6]

[slide: v-030]
[pause: 1.0]
C: Functionally, five things.
[reveal: v-031]
[pause: 0.45]
C: One, choose seams: a team for each cluster that changes together, so a feature touches two teams or fewer on average.
[reveal: v-032]
[pause: 0.45]
C: Two, make every seam an explicit, versioned contract, agreed by week two.
[reveal: v-033]
[pause: 0.45]
C: Three, keep every team unblocked: nobody idle more than two days.
[reveal: v-034]
[pause: 0.45]
C: Four, integrate early: end to end green by week four.
[reveal: v-035]
[pause: 0.45]
C: Five, detect a wrong split by month two, and be able to re-cut it once.
[reveal: v-036]
[pause: 0.45]
C: Non-functionally: the first release in six months, contract changes announced two weeks ahead, and the seams that cross time zones are the most stable.
[pause: 1.0]

[slide: v-037]
[pause: 0.6]
C: Scope, said aloud.
[reveal: v-038]
[pause: 0.45]
C: In: team boundaries, contracts and their versioning, ownership of shared things, the dependency graph, sequencing against skills, integration, and what I own personally.
[reveal: v-039]
[pause: 0.45]
C: Out, on purpose: the system's internal design, which was the last round, and hiring, tooling procurement and individual performance. They matter, but they are not this question.
[pause: 0.8]

[slide: v-040]
[pause: 1.3]
C: The C4 context. Here is the programme and everyone it touches.
[reveal: v-041]
[pause: 0.45]
C: You: the manager, who owns the contracts, the dependency graph and the milestones.
[reveal: v-042]
[pause: 0.45]
C: The platform itself: five teams, forty engineers, six months.
[reveal: v-043]
[pause: 0.45]
C: The origination team, an external consumer. It receives a loan booked event. An event, not a call.
[reveal: v-044]
[pause: 0.45]
C: The finance operations team reads reconciliation breaks, with a synchronous H-T-T-P-S call.
[reveal: v-045]
[pause: 0.45]
C: And the card and bank rails, external A-P-Is we call. Notice the three kinds of boundary: events, calls, and the outside world.
[pause: 1.1]

[slide: v-046]
[pause: 0.7]
V: The core is four decisions. Where the seams go. What crosses them. Who owns what is shared. And when it first works end to end.
[pause: 1.6]

[pause: 1.4]

## 2 Estimates

[slide: v-047]
[pause: 1.2]
C: Estimates. I start every one from the scale line, and say which number I used. They are all illustrative until measured.
[pause: 1.8]

[slide: v-048]
[pause: 1.0]
C: The budget.
C: From the scale line: forty engineers times six months is two hundred and forty engineer-months.
[reveal: v-049]
[pause: 0.45]
C: Overhead takes about a quarter: on-call, meetings, leave, and onboarding for the three teams who are new.
[reveal: v-050]
[pause: 0.45]
C: That is sixty, an illustrative figure.
C: Spendable: about a hundred and eighty.
[reveal: v-051]
[pause: 0.45]
C: Per team, thirty-six engineer-months.
[reveal: v-052]
[pause: 0.45]
C: What it changes: a team of eight has about four and a half productive engineers over the half year.
C: A team that waits for another team for even a month has spent a seventh of its budget.
[pause: 1.0]

[slide: v-053]
[pause: 1.0]
C: The coordination cost, from the same scale line: five teams.
C: Five teams have ten possible pairs.
[reveal: v-054]
[pause: 0.45]
C: I design so only four or five of them ever have to agree.
C: Every extra arrow is a standing meeting.
[reveal: v-055]
[pause: 0.45]
C: One cross-team change costs about a week of waiting.
C: A request, a queue, a review.
[reveal: v-056]
[pause: 0.45]
C: That is illustrative, and I would measure it.
C: So a feature that touches four teams has three to four weeks of latency, before anyone writes code.
[reveal: v-057]
[pause: 0.45]
C: And in three time zones with two hours of overlap per pair, a question costs a day.
[reveal: v-058]
[pause: 0.45]
C: The number to minimise is the number of arrows, not the number of boxes.
[pause: 1.0]

[slide: v-059]
[pause: 1.0]
C: One more number.
C: If integration happens at month five, the first mismatch is found with one month left, and it costs re-work across teams.
[reveal: v-060]
[pause: 0.45]
C: With an end-to-end skeleton at week four, the same mismatch costs a day inside two teams.
[reveal: v-061]
[pause: 0.45]
C: That ratio, about ten to one, is illustrative, but the direction is not in doubt.
[reveal: v-062]
[pause: 0.45]
C: That is why integration is a requirement here, not a phase.
[pause: 1.0]

[pause: 1.4]

## 3 Theory

[slide: v-063]
[pause: 1.2]
C: A short theory chapter before the design. What a decomposition is and is not, the properties, the central tension, six mechanisms each with the picture that fits it, and the options, one slide each. The failures come later, as the challenges.
[pause: 1.8]

[slide: v-064]
[pause: 0.7]
V: A decomposition is a division of the work into teams that can ship alone, joined by explicit contracts, with one owner for everything shared, and a way to see early that the cut is wrong.
[pause: 1.0]
C: Every clause does work. Ship alone: the test is delivery, not tidiness. Explicit contracts: an arrow nobody wrote down is a surprise at month five. One owner: shared means nobody's. See early: a wrong split is cheap in week four and ruinous in month five.
[pause: 1.6]

[slide: v-065]
[pause: 0.6]
C: Four neighbours it is confused with.
[reveal: v-066]
[pause: 0.45]
C: It is not an org chart: reporting lines are one input.
[reveal: v-067]
[pause: 0.45]
C: It is not an architecture diagram: the boxes also need a team, and a statement of who must agree.
[reveal: v-068]
[pause: 0.45]
C: It is not a task list: assigning components leaves the arrows unmanaged, and the arrows are where the slips are.
[reveal: v-069]
[pause: 0.45]
C: And it is not microservices: five teams do not need twelve services, and a boundary is expensive to move.
[pause: 0.8]

[slide: v-070]
[pause: 0.6]
C: Two safety properties, things that must never happen. S-one, no silent break: a change on one side breaks a consumer, and nobody finds out before release. S-two, one owner each: a component, a contract or a table with no owner, or with two.
[reveal: v-071]
[pause: 0.45]
C: Three liveness properties, things that must eventually happen. L-one, no team waits: every team has unblocked work every week. L-two, integrated by week 4: an end-to-end path runs by week four and stays green. L-three, wrong split seen early: a wrong cut is visible by month two.
C: Every fix from here on names the tag of the property it serves.
[pause: 0.8]

[slide: v-072]
[pause: 1.0]
C: The central tension is autonomy against coherence.
[reveal: v-073]
[pause: 0.45]
C: Toward autonomy, teams ship alone and meet less. The cost is duplication, contracts to keep stable, and drift.
[reveal: v-074]
[pause: 0.45]
C: Toward coherence, there is one model and one style. The cost is that every change needs a meeting and teams wait.
[reveal: v-075]
[pause: 0.45]
C: The cut decides where autonomy is free and where coherence is paid for. A wrong cut pays both.
[reveal: v-076]
[pause: 0.45]
C: So: what changes together lives together, and coherence is paid for only at the seams.
[pause: 1.0]

[slide: v-077]
[pause: 1.3]
C: Mechanism one, seams by domain, not by layer, drawn as the containers and the boundaries between them.
[reveal: v-078]
[pause: 0.45]
C: It protects L-one, no team waits.
[reveal: v-079]
[pause: 0.45]
C: Group what changes together into one team: a domain, with its logic, its data and its integrations. Conway's law says the system will copy the organisation, so I choose both at once.
[reveal: v-080]
[pause: 0.45]
C: It rules out every feature needing every team.
[reveal: v-081]
[pause: 0.45]
C: It costs some duplication across domains, and a domain model that has to be argued first.
[reveal: v-082]
[pause: 0.45]
C: Servicing core owns the ledger and the schedule: one team.
[reveal: v-083]
[pause: 0.45]
C: Collections owns dispatch and the rails.
[reveal: v-084]
[pause: 0.45]
C: Reconciliation owns files and breaks.
[reveal: v-085]
[pause: 0.45]
C: Policy and A-P-I owns quotes and terms. Three boundaries, each an event or one call: that is the whole arrow budget.
[pause: 1.1]

[slide: v-086]
[pause: 1.3]
C: Mechanism two, contracts first, versioned, drawn as the record we keep for each one.
[reveal: v-087]
[pause: 0.45]
C: It protects S-one, no silent break.
[reveal: v-088]
[pause: 0.45]
C: Every seam is a contract with an owner, a schema, a compatibility policy, additive changes only, and a sunset date. Agreed before code starts.
[reveal: v-089]
[pause: 0.45]
C: It rules out two teams assuming different shapes, and a rename that breaks a consumer.
[reveal: v-090]
[pause: 0.45]
C: It costs agreement work in weeks one and two, and the discipline of additive change.
[reveal: v-091]
[pause: 0.45]
C: The contract has one owner team and a kind: an event or an H-T-T-P-S call.
[reveal: v-092]
[pause: 0.45]
C: Each version has a schema, a deprecation date and a sunset date.
[reveal: v-093]
[pause: 0.45]
C: And each version lists its consumers and the test that proves they still work.
[pause: 1.1]

[slide: v-094]
[pause: 1.3]
C: Mechanism three, consumer-driven tests and mocks, at the level of the build pipeline.
[reveal: v-095]
[pause: 0.45]
C: It protects S-one, no silent break and L-one, no team waits.
[reveal: v-096]
[pause: 0.45]
C: Consumers register the calls they rely on. The provider's pipeline runs every consumer's test. And a mock server generated from the contract lets a consumer build before the provider exists.
[reveal: v-097]
[pause: 0.45]
C: It rules out a breaking change reaching release, and a team idle for a missing A-P-I.
[reveal: v-098]
[pause: 0.45]
C: It costs a contract hub to run, and tests the consumers must write.
[reveal: v-099]
[pause: 0.45]
C: The consumer publishes the calls it relies on.
[reveal: v-100]
[pause: 0.45]
C: The provider opens a pull request: rename a field.
[reveal: v-101]
[pause: 0.45]
C: Its pipeline asks the hub to run every consumer's test.
[reveal: v-102]
[pause: 0.45]
C: Two consumers fail.
[reveal: v-103]
[pause: 0.45]
C: The merge is blocked, and the consumers are named.
[reveal: v-104]
[pause: 0.45]
C: The teams agree an additive change: the old field stays.
[reveal: v-105]
[pause: 0.45]
C: The tests pass, and nobody was surprised.
[pause: 1.1]

[slide: v-106]
[pause: 1.3]
C: Mechanism four, one owner for every shared thing, drawn around the ledger.
[reveal: v-107]
[pause: 0.45]
C: It protects S-two, one owner each.
[reveal: v-108]
[pause: 0.45]
C: The shared schema, library or ledger belongs to exactly one team. Everyone else reaches it only through its contract, and changes go through the owner.
[reveal: v-109]
[pause: 0.45]
C: It rules out a table edited by three teams, and a shared thing that is nobody's problem.
[reveal: v-110]
[pause: 0.45]
C: It costs a risk: the owner can become a queue, unless the contract is rich enough.
[reveal: v-111]
[pause: 0.45]
C: The servicing core team owns the ledger and its schema.
[reveal: v-112]
[pause: 0.45]
C: Collections posts through a call, never into the table.
[reveal: v-113]
[pause: 0.45]
C: And so does Reconciliation.
[pause: 1.1]

[slide: v-114]
[pause: 1.3]
C: Mechanism five, an end-to-end skeleton first, as the thinnest path through the system.
[reveal: v-115]
[pause: 0.45]
C: It protects L-two, integrated by week 4.
[reveal: v-116]
[pause: 0.45]
C: One thin request through every team's component, with stubs and mocks where needed, running in week four, and then thickened every week.
[reveal: v-117]
[pause: 0.45]
C: It rules out a six-month plan that finds out it does not fit in month five.
[reveal: v-118]
[pause: 0.45]
C: It costs throw-away stubs, and teams who must agree before they feel ready.
[reveal: v-119]
[pause: 0.45]
C: The A-P-I stub books a loan, in week one.
[reveal: v-120]
[pause: 0.45]
C: The servicing core is thin, in week two.
[reveal: v-121]
[pause: 0.45]
C: Collections uses a mock rail, in week three.
[reveal: v-122]
[pause: 0.45]
C: And in week four the rail sandbox answers: green end to end.
[pause: 1.1]

[slide: v-123]
[pause: 1.3]
C: Mechanism six, leading indicators and one re-cut, drawn as a state machine of the split's health.
[reveal: v-124]
[pause: 0.45]
C: It protects L-three, wrong split seen early.
[reveal: v-125]
[pause: 0.45]
C: I watch cross-team pull requests, lead time and meeting load every week. Two weeks of friction triggers one review, and I allow at most one re-cut.
[reveal: v-126]
[pause: 0.45]
C: It rules out discovering a wrong split by missing a date.
[reveal: v-127]
[pause: 0.45]
C: It costs a weekly dashboard, and the humility to move a seam.
[reveal: v-128]
[pause: 0.45]
C: Healthy is the start state.
[reveal: v-129]
[pause: 0.45]
C: Friction appears when cross-team pull requests rise. A contract fix returns it to healthy.
[reveal: v-130]
[pause: 0.45]
C: Two weeks without change opens a review. A false alarm returns to healthy.
[reveal: v-131]
[pause: 0.45]
C: Or the seam moves, once, and the split is healthy again.
[pause: 1.1]

[slide: v-132]
[pause: 1.3]
C: Option A, the classic: an A-P-I team, a logic team, a data team.
[reveal: v-133]
[pause: 0.45]
C: Specialists stay together.
[reveal: v-134]
[pause: 0.45]
C: And it is easy to staff.
[reveal: v-135]
[pause: 0.45]
C: But every feature crosses every team.
[reveal: v-136]
[pause: 0.45]
C: The pitfall: three to four weeks of latency for a single feature.
[reveal: v-137]
[pause: 0.45]
C: And no team can ship alone, which was the point.
[reveal: v-138]
[pause: 0.45]
C: One layer on top of the next.
[reveal: v-139]
[pause: 0.45]
C: Every feature goes down the stack.
[reveal: v-140]
[pause: 0.45]
C: Through the same three teams.
[pause: 1.1]

[slide: v-141]
[pause: 1.3]
C: Option B, the pick: teams cut by domain, each owning logic, data and integrations for its domain.
[reveal: v-142]
[pause: 0.45]
C: A team can ship a feature alone.
[reveal: v-143]
[pause: 0.45]
C: It matches how the domain changes.
[reveal: v-144]
[pause: 0.45]
C: It costs some duplication.
[reveal: v-145]
[pause: 0.45]
C: And a domain model to agree first.
[reveal: v-146]
[pause: 0.45]
C: The pitfall: a wrong domain cut is expensive to move.
[reveal: v-147]
[pause: 0.45]
C: And the shared ledger needs exactly one owner.
[reveal: v-148]
[pause: 0.45]
C: Servicing core, with Collections and Reconciliation beside it.
[reveal: v-149]
[pause: 0.45]
C: Each boundary is an event, not a shared table.
[pause: 1.1]

[slide: v-150]
[pause: 1.3]
C: Option C, feature teams on one codebase, with no owners.
[reveal: v-151]
[pause: 0.45]
C: It is flexible, with no hand-offs by design.
[reveal: v-152]
[pause: 0.45]
C: But nobody owns anything.
[reveal: v-153]
[pause: 0.45]
C: And merge conflicts become the coordination.
[reveal: v-154]
[pause: 0.45]
C: The pitfall: two teams change one table in the same week.
[reveal: v-155]
[pause: 0.45]
C: And nobody is paged for the shared code.
[reveal: v-156]
[pause: 0.45]
C: One codebase.
[reveal: v-157]
[pause: 0.45]
C: One database that anyone edits.
[pause: 1.1]

[slide: v-158]
[pause: 1.3]
C: Option D, twelve services, one per entity.
[reveal: v-159]
[pause: 0.45]
C: Small, replaceable parts.
[reveal: v-160]
[pause: 0.45]
C: But twelve contracts to version.
[reveal: v-161]
[pause: 0.45]
C: And network failure between everything.
[reveal: v-162]
[pause: 0.45]
C: The pitfall: five teams own two or three each, so there are more arrows, not fewer.
[reveal: v-163]
[pause: 0.45]
C: And boundaries are drawn before the domain is understood.
[reveal: v-164]
[pause: 0.45]
C: Five teams.
[reveal: v-165]
[pause: 0.45]
C: Own twelve services.
[reveal: v-166]
[pause: 0.45]
C: Behind twelve contracts.
[pause: 1.1]

[slide: v-167]
[pause: 1.3]
C: Option E, a platform team beside stream teams, the shape larger organisations grow into.
[reveal: v-168]
[pause: 0.45]
C: It gives everyone a paved road.
[reveal: v-169]
[pause: 0.45]
C: And stream teams own a domain end to end.
[reveal: v-170]
[pause: 0.45]
C: It needs a platform team to staff and fund.
[reveal: v-171]
[pause: 0.45]
C: And it is overhead before it pays.
[reveal: v-172]
[pause: 0.45]
C: The pitfall: the platform becomes a ticket queue.
[reveal: v-173]
[pause: 0.45]
C: And at forty engineers it is too early.
[reveal: v-174]
[pause: 0.45]
C: The platform team serves the stream teams.
[reveal: v-175]
[pause: 0.45]
C: Two stream teams, each owning a domain.
[reveal: v-176]
[pause: 0.45]
C: Joined by a contract.
[pause: 1.1]

[slide: v-177]
[pause: 1.0]
C: The five side by side, as a summary only.
[reveal: v-178]
[pause: 0.45]
C: A fails when any feature is requested.
[reveal: v-179]
[pause: 0.45]
V: B is the pick.
[reveal: v-180]
[pause: 0.45]
C: C fails when two teams edit one table.
[reveal: v-181]
[pause: 0.45]
C: D fails when five teams carry twelve contracts.
[reveal: v-182]
[pause: 0.45]
C: E is the honest next step, and fails only because we are under a hundred engineers.
[pause: 1.0]

[slide: v-183]
[pause: 0.6]
C: What B buys: a feature usually touches one team, contracts sit where change is rare, and every team has a domain it can own and be paged for.
[reveal: v-184]
[pause: 0.45]
C: What it gives up: some duplication, a domain model to agree up front, a shared ledger that needs one owner and a rich contract, and a wrong cut that costs one re-cut.
[reveal: v-185]
[pause: 0.45]
C: So in the room I would say: A only for a tiny programme, and E once we pass a hundred engineers.
C: At forty, B.
[pause: 0.8]

[slide: v-186]
[pause: 1.0]
C: The vocabulary in one table.
[reveal: v-187]
[pause: 0.45]
C: Seams by domain serve L-one, no team waits.
[reveal: v-188]
[pause: 0.45]
C: Contracts first serve S-one, no silent break.
[reveal: v-189]
[pause: 0.45]
C: Consumer tests and mocks serve S-one, no silent break and L-one, no team waits.
[reveal: v-190]
[pause: 0.45]
C: One owner serves S-two, one owner each.
[reveal: v-191]
[pause: 0.45]
C: The skeleton serves L-two, integrated by week 4.
[reveal: v-192]
[pause: 0.45]
C: And leading indicators serve L-three, wrong split seen early.
[reveal: v-193]
[pause: 0.45]
N: Good theory has a consequence for the design. Every mechanism here names the property it serves and where it comes back.
[pause: 1.0]

[pause: 1.4]

## 4 Contracts and entities

[slide: v-194]
[pause: 1.2]
C: Contracts and entities. Before anyone writes code, the contract at each seam, because a contract is where two teams find out they disagree, and week one is the cheapest time to find out.
[pause: 1.8]

[slide: v-195]
[pause: 1.0]
C: The first contract, an event.
C: Origination emits loan booked: the loan I-D, the principal in cents, the first due date.
C: That is version one, and it is what the two external teams build against.
[reveal: v-196]
[pause: 0.45]
C: Later we need a currency.
C: Version two adds one optional field.
C: Nothing is renamed, nothing is removed, so every version-one consumer keeps working.
C: That is the additive-only policy, in one example.
[pause: 1.0]

[slide: v-197]
[pause: 1.0]
C: The second kind, a synchronous call.
C: A refund, with an idempotency key so a retry is safe, and a response that says what happened.
[reveal: v-198]
[pause: 0.45]
C: And the rules that travel with it: additive changes only, and two weeks of notice before anything is deprecated.
C: The policy is part of the contract, not a separate document.
[pause: 1.0]

[slide: v-199]
[pause: 1.3]
C: The entities the manager keeps, as a model. It is small on purpose.
[reveal: v-200]
[pause: 0.45]
C: A team has a time zone and a size.
[reveal: v-201]
[pause: 0.45]
C: A component has exactly one owner team. That one rule is S-two, one owner each.
[reveal: v-202]
[pause: 0.45]
C: A contract is provided by one component, and is either an event or a call.
[reveal: v-203]
[pause: 0.45]
C: And a dependency says which component needs which contract, and by which week. That table is the dependency graph, and I keep it.
[pause: 1.1]

[pause: 1.4]

## 5 High-level design

[slide: v-204]
[pause: 1.2]
C: The design, in three versions, each introduced by the objection to the one before. Every picture is a view of the same container diagram; new boxes are outlined.
[pause: 1.8]

[slide: v-205]
[pause: 1.3]
C: Version one.
[reveal: v-206]
[pause: 0.45]
C: The simplest split: one team per layer.
[reveal: v-207]
[pause: 0.45]
C: Team one owns every endpoint.
C: Team two owns all the business rules.
[reveal: v-208]
[pause: 0.45]
C: Team three owns all the tables.
C: Team four owns every rail adapter.
[reveal: v-209]
[pause: 0.45]
C: And team five runs the platform.
C: It is easy to staff, and it is where most first plans start.
[pause: 1.1]

[slide: v-210]
[pause: 1.3]
I: Walk me through how version one breaks.
[reveal: v-211]
[pause: 0.45]
C: Product asks for a partial refund.
[reveal: v-212]
[pause: 0.45]
C: The A-P-I team needs a new rule from the logic team.
[reveal: v-213]
[pause: 0.45]
C: Which needs a new column from the data team.
[reveal: v-214]
[pause: 0.45]
C: Which needs a new field from the adapter team.
[reveal: v-215]
[pause: 0.45]
C: And it ships after all four, in week three. With ten pairs of teams and a feature touching four, the latency is the sum of four queues. Nobody can ship alone.
[pause: 1.1]

[slide: v-216]
[pause: 1.3]
C: Version two.
[reveal: v-217]
[pause: 0.45]
C: The platform team stays, running the shared infrastructure.
[reveal: v-218]
[pause: 0.45]
C: Servicing core takes the ledger and the schedule, with its own tables.
C: Collections takes dispatch and the rails, with its own adapters.
[reveal: v-219]
[pause: 0.45]
C: Reconciliation takes files and breaks.
C: Policy and A-P-I takes quotes and terms.
[reveal: v-220]
[pause: 0.45]
C: Between them, only events and one call.
C: That is the arrow budget.
[pause: 1.1]

[slide: v-221]
[pause: 1.3]
I: Domain seams look right. What is still missing?
[reveal: v-222]
[pause: 0.45]
C: Two teams need a change to the same ledger table, and they need incompatible ones.
[reveal: v-223]
[pause: 0.45]
C: With no owner rule and no contract, nobody can say which goes first.
[reveal: v-224]
[pause: 0.45]
C: And the first end-to-end run is in month five, where everything fails to fit at once.
[reveal: v-225]
[pause: 0.45]
C: So version three adds contracts with one owner for the shared thing, and a skeleton in week four.
[pause: 1.1]

[slide: v-226]
[pause: 1.3]
C: Version three adds two things and changes no team.
C: First, everything the teams build, as the carried baseline: servicing core owns the ledger, collections owns dispatch and the rails, reconciliation owns files and breaks, policy and A-P-I owns quotes and terms, and platform runs the shared infrastructure.
[reveal: v-227]
[pause: 0.45]
C: Every arrow is an event or a call, and each has a contract.
C: Second, a contract hub.
C: It holds the schemas, the consumer tests and the mock servers, and it is the only place a contract is edited.
[reveal: v-228]
[pause: 0.45]
C: And a skeleton environment, where one thin path runs end to end from week four.
C: This is the baseline.
C: Every picture from here is a view of it.
[pause: 1.1]

[slide: v-229]
[pause: 1.3]
C: Requirement one, choosing the seams.
[reveal: v-230]
[pause: 0.45]
C: I list the nouns and who changes them together.
[reveal: v-231]
[pause: 0.45]
C: The domain leads cluster what changes together.
C: One team per cluster, one named owner.
[pause: 1.1]

[slide: v-232]
[pause: 1.3]
C: Requirement two, contracts.
[reveal: v-233]
[pause: 0.45]
C: The provider drafts a contract with the additive-only policy.
[reveal: v-234]
[pause: 0.45]
C: The consumers review it and register the calls they rely on.
C: Version one is agreed in week two.
[pause: 1.1]

[slide: v-235]
[pause: 1.3]
C: Requirement three, unblocking.
[reveal: v-236]
[pause: 0.45]
C: The consumer builds against a mock generated from the contract, in week two.
[reveal: v-237]
[pause: 0.45]
C: The provider publishes examples to the same mock.
C: In month four the real service replaces the mock.
[pause: 1.1]

[slide: v-238]
[pause: 1.3]
C: Requirement four, integration.
[reveal: v-239]
[pause: 0.45]
C: Team A builds a thin ledger path.
[reveal: v-240]
[pause: 0.45]
C: Team B builds the mock-rail path.
C: And the skeleton goes green end to end by week four.
[pause: 1.1]

[slide: v-241]
[pause: 1.3]
C: Requirement five, detection.
[reveal: v-242]
[pause: 0.45]
C: The dashboard shows cross-team pull requests and lead time rising.
[reveal: v-243]
[pause: 0.45]
C: I open a two-week review of the seam.
C: And the teams move one seam, once.
[pause: 1.1]

[pause: 1.4]

## 5.1 Components and technologies

[slide: v-244]
[pause: 1.2]
C: Now one level down: the tools that carry the contracts. Not a product tour: for each, how it works, why this one, and what an interviewer will name instead.
[pause: 1.8]

[slide: v-245]
[pause: 1.0]
C: The contract format. One reviewed repository, with an open A-P-I description for calls and a protocol buffer schema for events.
[reveal: v-246]
[pause: 0.45]
C: What it is built from: each contract is a schema file with an owner, and the pipeline compares every change to the last released version.
[reveal: v-247]
[pause: 0.45]
C: It fails on a removed field, a changed type, or a new required field.
[reveal: v-248]
[pause: 0.45]
C: A wiki page per contract is the thing an interviewer names. It fails because nothing checks it, and it drifts in the first week.
[reveal: v-249]
[pause: 0.45]
C: Sharing source code between teams couples their release dates and languages.
[pause: 1.0]

[slide: v-250]
[pause: 1.0]
C: Consumer-driven tests. The consumer writes the test, and the provider has to pass it.
[reveal: v-251]
[pause: 0.45]
C: How it works: a consumer records the exact calls it makes, the provider's build replays them, and a failure names the consumer.
[reveal: v-252]
[pause: 0.45]
C: The same file serves the mock server, so one artefact does two jobs.
[reveal: v-253]
[pause: 0.45]
C: End-to-end tests alone are what an interviewer names. They are slow and flaky, and they find the break after the merge.
[reveal: v-254]
[pause: 0.45]
C: A manual compatibility review does not scale to ten pairs of teams.
[pause: 1.0]

[slide: v-255]
[pause: 1.0]
C: Decisions and health.
C: A one-page decision record, and a dashboard of three numbers.
C: How it works: a proposal, the options, two days for objections, and a named decider.
[reveal: v-256]
[pause: 0.45]
C: The dashboard shows cross-team pull requests, lead time, and meeting hours per engineer.
[reveal: v-257]
[pause: 0.45]
C: Escalation by meeting is the alternative, at two hours per dispute and with no record.
[reveal: v-258]
[pause: 0.45]
C: And status reports are all green until the date is missed.
[pause: 1.0]

[pause: 1.4]

## 5.2 When you don't need all this

[slide: v-259]
[pause: 1.2]
C: Before I break it, the simpler design, and the number at which the full one becomes necessary.
[pause: 1.8]

[slide: v-260]
[pause: 1.3]
C: This is the alternate path. It is not the baseline.
[reveal: v-261]
[pause: 0.45]
C: One team of eight builds a modular monolith, with module boundaries as interfaces in code.
[reveal: v-262]
[pause: 0.45]
C: Those module contracts are the same contracts, only cheaper to change, and not yet owned by different teams.
[reveal: v-263]
[pause: 0.45]
C: What it gives up: nothing ships in parallel, so it caps at about a dozen engineers. Split when headcount passes twelve, or when three modules are hot at once. Below that, I would ship this.
[pause: 1.1]

[pause: 1.4]

## 6 Bridge

[slide: v-264]
[pause: 1.2]
C: It works on paper. Where does it break first? Six places, ordered so each fix creates the next question: the critical path, a late dependency, a shared table, a contract dispute, a lost team, and finally how I would know any of it was going wrong.
[pause: 1.8]

[pause: 1.4]

## 7 Challenges

[slide: v-265]
[pause: 1.2]
C: Six challenges. For each: the question, the naive answer, the break on the component view, the fix one level down, and what I would say in the room.
[pause: 1.8]

[pause: 1.4]

## 7.1 Challenge 1: Which team is on the critical path?

[slide: v-266]
[pause: 1.2]
N: Challenge one. Four teams need the ledger, and one team builds it. Roughly four minutes.
[pause: 1.8]

[slide: v-267]
[pause: 0.6]
I: Which team is on the critical path, and what do the other four do while they work?
[pause: 2.0]

[slide: v-268]
[pause: 0.6]
C: The first answer most people give: start everyone in parallel and let the teams sort it out.
[reveal: v-269]
[pause: 0.45]
C: It sounds like autonomy, and it is the default when nobody names the path.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-270]
[pause: 1.3]
C: The break.
[reveal: v-271]
[pause: 0.45]
C: Servicing core builds the ledger for months one to four.
C: Collections waits for the ledger A-P-I.
[reveal: v-272]
[pause: 0.45]
C: So does reconciliation.
C: And so does policy.
[reveal: v-273]
[pause: 0.45]
C: The ledger is the critical path, and three of five teams are queued behind it.
C: With thirty-six engineer-months each, a month of waiting is a seventh of the budget.
[pause: 1.1]

[slide: v-274]
[pause: 1.3]
C: The fix, one level down.
[reveal: v-275]
[pause: 0.45]
C: Servicing core publishes the ledger contract, version one, in week two, with the schema and examples.
[reveal: v-276]
[pause: 0.45]
C: The contract hub generates a mock server from it.
[reveal: v-277]
[pause: 0.45]
C: Collections builds against the mock.
[reveal: v-278]
[pause: 0.45]
C: So does reconciliation.
C: Fix: contract and mock in week two.
[reveal: v-279]
[pause: 0.45]
C: This serves L-one, no team waits.
C: Why it works: the consumers depend on the contract, not on the code, and the contract is stable enough to be built against from week two.
[reveal: v-280]
[pause: 0.45]
C: Rejected: adding engineers to the ledger team.
C: An interviewer will name it.
C: It adds communication paths to a narrow interface, and the interface was the bottleneck.
[pause: 1.1]

[slide: v-281]
[pause: 0.6]
I: What if the mock drifts from the real service?
[pause: 2.0]

[slide: v-282]
[pause: 0.6]
C: The mock is generated from the same contract file the provider's tests use, and the consumers' tests run against the real service nightly from month three.
[reveal: v-283]
[pause: 0.45]
C: A nightly job and a provider fix time of two days; a drift is a failing test, not a surprise.
[pause: 0.8]

[slide: v-284]
[pause: 0.7]
V: The critical path is the ledger. I would publish its contract and a mock in week two, so the other four build in parallel, and I would own that date personally.
[pause: 1.6]

[pause: 1.4]

## 7.2 Challenge 2: A dependency arrives two months late

[slide: v-285]
[pause: 1.2]
N: Challenge two. Team C needs team B's API in month two, and team B will not have it until month four. Roughly four minutes.
[pause: 1.8]

[slide: v-286]
[pause: 0.6]
I: Team C needs Team B's API in month two, and B won't have it until month four. What do you do?
[pause: 2.0]

[slide: v-287]
[pause: 0.6]
C: The first answer most people give: move team C's work to month four and let them wait.
[reveal: v-288]
[pause: 0.45]
C: It is honest about the dependency, and it spends two months of a team's budget.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-289]
[pause: 1.3]
C: The break.
[reveal: v-290]
[pause: 0.45]
C: Team C asks for the A-P-I in month two.
[reveal: v-291]
[pause: 0.45]
C: Team B says not before month four.
[reveal: v-292]
[pause: 0.45]
C: Team C is idle, or guesses the shape.
C: In month four it integrates.
[reveal: v-293]
[pause: 0.45]
C: And the shape was different.
C: Two months spent, and re-work on top.
[pause: 1.1]

[slide: v-294]
[pause: 1.3]
C: The fix.
[reveal: v-295]
[pause: 0.45]
C: Team C builds against the contract, version one.
[reveal: v-296]
[pause: 0.45]
C: It registers the exact calls it makes in the hub.
[reveal: v-297]
[pause: 0.45]
C: And team B's pipeline runs those calls against its real service, from the first day it exists.
C: Fix: consumer-driven tests plus a mock.
[reveal: v-298]
[pause: 0.45]
C: This serves S-one, no silent break and L-one, no team waits.
C: Why it works: if B's real shape diverges, B's build fails and names C in week five, not in month four.
[reveal: v-299]
[pause: 0.45]
C: Rejected: re-sequencing so C simply starts later.
C: It spends two months of a thirty-six engineer-month budget on waiting.
[pause: 1.1]

[slide: v-300]
[pause: 0.6]
I: What if the real shape has to change after C started?
[pause: 2.0]

[slide: v-301]
[pause: 0.6]
C: An additive version two with both live; C migrates by the sunset date, announced two weeks ahead.
[reveal: v-302]
[pause: 0.45]
C: Two versions to support for a few weeks, and a sunset date the manager enforces.
[pause: 0.8]

[slide: v-303]
[pause: 0.7]
V: I would not let team C wait. They build against the contract in week two, and their calls run in B's pipeline from the day B's service exists, so a mismatch shows up as a failing build.
[pause: 1.6]

[pause: 1.4]

## 7.3 Challenge 3: Two teams, one table, incompatible changes

[slide: v-304]
[pause: 1.2]
N: Challenge three. Two teams need incompatible changes to the same ledger table. Roughly four minutes.
[pause: 1.8]

[slide: v-305]
[pause: 0.6]
I: Who owns the shared data model, and what happens when two teams need incompatible changes to it?
[pause: 2.0]

[slide: v-306]
[pause: 0.6]
C: The first answer most people give: let them negotiate directly and merge whichever lands first.
[reveal: v-307]
[pause: 0.45]
C: It assumes goodwill is a mechanism.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-308]
[pause: 1.3]
C: The break.
[reveal: v-309]
[pause: 0.45]
C: Team B wants to rename a column.
[reveal: v-310]
[pause: 0.45]
C: Team C wants to change its type.
C: One table, two changes, the owner in the middle.
[reveal: v-311]
[pause: 0.45]
C: Which goes first?
C: With no rule, whoever shouts, and one team is broken in production.
[pause: 1.1]

[slide: v-312]
[pause: 1.3]
C: The fix.
[reveal: v-313]
[pause: 0.45]
C: Servicing core owns the ledger and its schema.
[reveal: v-314]
[pause: 0.45]
C: That is S-two, one owner each.
C: Collections reads a versioned view, not the table.
[reveal: v-315]
[pause: 0.45]
C: Reconciliation reads the same view.
C: The owner changes the table in three steps: expand with the new column, migrate readers to the new view, then contract the old one.
[reveal: v-316]
[pause: 0.45]
C: Why it works: an incompatible need becomes two compatible versions, in sequence, decided by one owner.
[reveal: v-317]
[pause: 0.45]
C: Rejected: a shared schema anyone may alter.
C: An interviewer will name it.
C: It has no owner, and the first long migration locks every team.
[pause: 1.1]

[slide: v-318]
[pause: 0.6]
I: What if the owner becomes a bottleneck?
[pause: 2.0]

[slide: v-319]
[pause: 0.6]
C: The owner publishes a richer view so most needs need no change, reviews requests in two days, and hands a slice to a second team through its own contract if the queue passes five.
[reveal: v-320]
[pause: 0.45]
C: Review time to staff, and a view layer to maintain.
[pause: 0.8]

[slide: v-321]
[pause: 0.7]
V: Shared data gets exactly one owner. Everyone else reads versioned views. The owner changes a table by expanding, migrating, then contracting, so two incompatible needs become two compatible versions in order.
[pause: 1.6]

[pause: 1.4]

## 7.4 Challenge 4: Two teams disagree on a contract

[slide: v-322]
[pause: 1.2]
N: Challenge four. Two teams disagree on a field, and both escalate to you. Roughly four minutes.
[pause: 1.8]

[slide: v-323]
[pause: 0.6]
I: Two teams disagree on a contract and both escalate to you. Walk me through the conversation.
[pause: 2.0]

[slide: v-324]
[pause: 0.6]
C: The first answer most people give: get both in a room and decide on the spot.
[reveal: v-325]
[pause: 0.45]
C: It feels decisive, and it makes the manager the bottleneck.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-326]
[pause: 1.3]
C: The break.
[reveal: v-327]
[pause: 0.45]
C: Team B wants a field required.
[reveal: v-328]
[pause: 0.45]
C: Team D wants it optional.
[reveal: v-329]
[pause: 0.45]
C: Team B escalates.
C: Team D escalates.
[reveal: v-330]
[pause: 0.45]
C: And I spend two hours in a meeting.
C: Next month there is another dispute, and the same meeting.
[pause: 1.1]

[slide: v-331]
[pause: 1.3]
C: The fix.
[reveal: v-332]
[pause: 0.45]
C: The provider writes a one-page decision record: the proposal and the options.
[reveal: v-333]
[pause: 0.45]
C: The consumer has two days to object.
[reveal: v-334]
[pause: 0.45]
C: The provider proposes an additive change: the old field stays.
[reveal: v-335]
[pause: 0.45]
C: If they still disagree after five days, it comes to me.
[reveal: v-336]
[pause: 0.45]
C: And my rule is that the provider decides, and the consumer's cost is recorded.
C: Fix: a decision protocol.
[reveal: v-337]
[pause: 0.45]
C: This serves S-one, no silent break.
C: Why it works: most disputes dissolve in the written options; the rest have a clock and a decider, so I run a protocol, not a verdict.
[reveal: v-338]
[pause: 0.45]
C: Rejected: a meeting with both teams.
C: An interviewer will name it.
C: It costs two hours a dispute, leaves no record, and the loser relitigates it.
[pause: 1.1]

[slide: v-339]
[pause: 0.6]
I: What if the losing team is still unhappy?
[pause: 2.0]

[slide: v-340]
[pause: 0.6]
C: The record names a revisit trigger, a number such as rejected calls in a month, rather than an argument.
[reveal: v-341]
[pause: 0.45]
C: I look at the number at the month-three review; it takes discipline to let the data overrule the person who decided.
[pause: 0.8]

[slide: v-342]
[pause: 0.7]
V: When two teams escalate, I run a protocol: a written proposal, two days to object, the provider decides, the consumer's cost is on record, and a number that reopens it. I am not the bottleneck.
[pause: 1.6]

[pause: 1.4]

## 7.5 Challenge 5: You lose a team at month three

[slide: v-343]
[pause: 1.2]
N: Challenge five, the curveball. A reorg takes a whole team at month three. Roughly four minutes.
[pause: 1.8]

[slide: v-344]
[pause: 0.6]
I: You lose one team entirely to a reorg at month three. What happens?
[pause: 2.0]

[slide: v-345]
[pause: 0.6]
C: The first answer most people give: spread its work across the other four teams.
[reveal: v-346]
[pause: 0.45]
C: It looks fair, and it spreads everyone thinner.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-347]
[pause: 1.3]
C: The break.
[reveal: v-348]
[pause: 0.45]
C: The reorg takes team C at month three.
[reveal: v-349]
[pause: 0.45]
C: Reconciliation and files are orphaned.
C: The plan spreads everyone thinner.
[reveal: v-350]
[pause: 0.45]
C: And now it is five teams of work for four teams.
C: Every team gains an arrow and loses focus.
[pause: 1.1]

[slide: v-351]
[pause: 1.3]
C: The fix.
[reveal: v-352]
[pause: 0.45]
C: Servicing core continues unchanged.
[reveal: v-353]
[pause: 0.45]
C: Collections continues unchanged.
[reveal: v-354]
[pause: 0.45]
C: Reconciliation is paused to the second release.
[reveal: v-355]
[pause: 0.45]
C: Its contract stays frozen, so nobody built on it is affected.
C: Fix: cut scope, not spread thin.
[reveal: v-356]
[pause: 0.45]
C: This serves S-two, one owner each and L-one, no team waits.
C: Why it works: the decomposition has one owner per component, so losing a team orphans one component, and a frozen contract makes that safe.
[reveal: v-357]
[pause: 0.45]
C: Rejected: spreading the work across four teams.
C: It adds four new arrows, and cuts every team's focus.
[pause: 1.1]

[slide: v-358]
[pause: 0.6]
I: What if the date cannot move?
[pause: 2.0]

[slide: v-359]
[pause: 0.6]
C: Release one ships with manual break review in a sheet, an explicit risk product accepts in writing.
[reveal: v-360]
[pause: 0.45]
C: Operations carry the manual work until release two, and the cost is stated, not hidden.
[pause: 0.8]

[slide: v-361]
[pause: 0.7]
V: If I lose a team, I pause its component, freeze its contract and cut scope. I do not spread the work across four teams. The decomposition was built so a lost team orphans exactly one thing.
[pause: 1.6]

[pause: 1.4]

## 7.6 Challenge 6: How would you know the split is wrong?

[slide: v-362]
[pause: 1.2]
N: Challenge six, observability. How would you know, in month two, that the split is wrong? Roughly four minutes.
[pause: 1.8]

[slide: v-363]
[pause: 0.6]
I: How do you know in month two that the decomposition is wrong, and how would you get this wrong?
[pause: 2.0]

[slide: v-364]
[pause: 0.6]
C: The first answer most people give: watch the status reports.
[reveal: v-365]
[pause: 0.45]
C: Everyone looks at them, and they are green until the date is missed.
C: Here is where it breaks.
[pause: 0.8]

[slide: v-366]
[pause: 1.3]
C: The break.
[reveal: v-367]
[pause: 0.45]
C: The dashboard says all green.
C: In month two, nothing is integrated, and nobody has noticed.
[reveal: v-368]
[pause: 0.45]
C: In month five, a two-month slip.
C: Status reports measure what teams say, not what the split costs.
[pause: 1.1]

[slide: v-369]
[pause: 1.3]
C: The fix.
[reveal: v-370]
[pause: 0.45]
C: Cross-team pull requests per week: when more than a quarter of pull requests need two teams, the seams are wrong.
[reveal: v-371]
[pause: 0.45]
C: Lead time from idea to merged: if it doubles, a hand-off is hiding.
[reveal: v-372]
[pause: 0.45]
C: Meeting hours per engineer: if it passes six a week, the arrows are being managed by talking.
C: Together they give one split-health signal.
[reveal: v-373]
[pause: 0.45]
C: Fix: leading indicators with thresholds.
[reveal: v-374]
[pause: 0.45]
C: This serves L-three, wrong split seen early.
C: Why it works: they measure the cost of the cut, not a promise about it, and they move in weeks, before a date is missed.
[reveal: v-375]
[pause: 0.45]
C: Rejected: status reports and colour codes.
C: An interviewer will name them.
C: They stay green until the date is missed.
[pause: 1.1]

[slide: v-376]
[pause: 0.6]
I: How would you get this wrong yourself?
[pause: 2.0]

[slide: v-377]
[pause: 0.6]
C: I designed the cut, so I will want it to be right.
C: The thresholds are set now, a peer manager reads the dashboard with me, and one re-cut is allowed, once.
[reveal: v-378]
[pause: 0.45]
C: A peer's time every month, and the humility to move a seam I drew.
[pause: 0.8]

[slide: v-379]
[pause: 0.7]
V: In month two I would look at three numbers: cross-team pull requests, lead time and meeting hours, against thresholds set in advance. And I would name my own failure mode: I will want my cut to be right, so a peer reads the numbers with me.
[pause: 1.6]

[pause: 1.4]

## 8 Recap and follow-ups

[slide: v-380]
[pause: 1.2]
C: To close: one picture, one sentence per path, the mistakes to avoid, the four sentences, and the follow-up questions.
[pause: 1.8]

[slide: v-381]
[pause: 1.0]
C: One sentence per path.
C: Seams: domain clusters of what changes together, one team and one named owner each.
[reveal: v-382]
[pause: 0.45]
C: Contracts: versioned before code, additive only, with a sunset date and a consumer test.
[reveal: v-383]
[pause: 0.45]
C: Unblock: a mock from the contract in week two, and the critical path named and owned.
[reveal: v-384]
[pause: 0.45]
C: Integrate: a thin end-to-end skeleton, green by week four.
[reveal: v-385]
[pause: 0.45]
C: Detect: three leading indicators with thresholds set in advance, and one re-cut allowed.
[pause: 1.0]

[slide: v-386]
[pause: 0.6]
C: What I do not delegate.
[reveal: v-387]
[pause: 0.45]
C: The contracts. Teams own the content, and I own that they exist and have a sunset.
[reveal: v-388]
[pause: 0.45]
C: The dependency graph. I keep it, and I read it every week.
[reveal: v-389]
[pause: 0.45]
C: The integration milestones: week four, month three, month five.
[reveal: v-390]
[pause: 0.45]
C: And the escalation path: I run the protocol, not every verdict.
[pause: 0.8]

[slide: v-391]
[pause: 0.6]
C: The common mistakes.
C: On the split: splitting by layer, twelve services for five teams, shared tables with no owner, and re-shuffling teams every quarter.
[reveal: v-392]
[pause: 0.45]
C: On the manager's role: assigning everything and owning nothing, integration as a phase at the end, status reports in place of leading indicators, and escalation by meeting.
[pause: 0.8]

[slide: v-393]
[pause: 0.6]
C: If I had thirty seconds.
C: Domain teams with one owner each, joined by versioned, additive-only contracts.
[reveal: v-394]
[pause: 0.45]
C: The pace: mocks from the contract in week two, and a skeleton green by week four.
[reveal: v-395]
[pause: 0.45]
C: The risk is a wrong cut found late, and the defence is three indicators and one re-cut.
[reveal: v-396]
[pause: 0.45]
C: And what I own: the contracts, the dependency graph, the milestones and the escalation path.
[pause: 0.8]

[slide: v-397]
[pause: 1.0]
N: Questions you should be ready for next. Each points to where this video answers it.
[reveal: v-398]
[pause: 0.45]
C: Three teams new to the domain and none able to own the ledger: challenge three and its second fix.
[reveal: v-399]
[pause: 0.45]
C: When a platform team pays for itself: option E.
[reveal: v-400]
[pause: 0.45]
C: Keeping the hub from becoming a bottleneck: challenge one, and mechanism three.
[reveal: v-401]
[pause: 0.45]
C: A pivot: mechanism six, and challenge six.
[reveal: v-402]
[pause: 0.45]
C: A date that moves up a month: challenge five.
[reveal: v-403]
[pause: 0.45]
C: And eight teams, or two: the alternate path, and option E.
[pause: 1.0]

[slide: v-404]
[pause: 0.7]
V: Cut along domain seams. Put a versioned contract on every one. Give shared things one owner. Integrate by week four. And keep the contracts, the graph and the milestones yourself.
[pause: 1.6]
