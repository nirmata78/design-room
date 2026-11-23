# Episode 14 · Reliable product launches at scale

Reader transcript generated from `src/ch14.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 14 of 16 · Priority 2 — Reliable product launches at scale   `[th]`
> A hard date, a huge audience, and a checklist that turns a risky day into a rehearsed one.
**COACH:** Episode fourteen. This episode is about launches, the moments when a service meets the largest and least predictable load it will ever see. It is about judgement: which questions to ask before a launch, which techniques make it gradual, and how to be useful without becoming the department of no.
**SAY THIS:** A launch is a change with a deadline and an audience. That is the riskiest kind there is.
*[pause: 0.8]*


## 14.0 The story that starts it

### Slide 2 · The opening story — A service meets Santa   `[dia]`
*Diagram:* `svg/e14-santa.svg`
**COACH:** Start on Christmas Eve, two thousand eleven. A satellite imagery service normally serves up to several thousand images a second. That night it received twenty-five times its normal peak, upward of a million requests a second. The cause: Santa was coming. Google had worked with a national air defence organisation on a website that tracked Santa's progress around the world, with a virtual fly-over built on satellite imagery.
**COACH:** Here is why this was a hard launch: a hard deadline, because nobody could ask Santa to come a week later, huge publicity, an audience of millions, and a very steep ramp-up, since everyone would be watching at once. Everything about it was predictable except how many.

### Slide 3 · What this episode covers — Reliable product launches at scale   `[panel · note]`
> Reliable product launches at scale. It is on the design-room reading list as optional, but its checklist is the best template for the operational readiness part of any design answer.
**COACH:** This episode covers reliable product launches at scale. In the design-room reading plan it is optional, but its checklist is the best template for the operational readiness part of any design answer.


## 14.1 A role and a checklist

### Slide 4 · The launch coordination role — What the dedicated team does   `[list]`
> ~ Google's answer to launch risk was a specialist role.
> - Audits services before they launch
> - Curates the launch checklist and the recipes for common problems
> - Drives the launch: keeps momentum, removes blockers
> - Signs off launches judged safe, and educates the developers
> - Gives developers the documentation to integrate with shared services
**COACH:** Google's answer to launch risk was a specialist role. A small team of launch coordination engineers audit services before they launch, and curate a checklist of questions and recipes for common problems. They drive the launch, by keeping momentum and removing blockers. They sign off launches judged safe, and they educate the developers, with documentation for integrating with shared services. The role is part consultant, part gatekeeper, and part teacher.

### Slide 5 · The checklist — The nine areas, and a question for each   `[table · sm]`
> Area | A representative question
> Architecture, dependencies, integration | Is there a single point of failure, or a hidden hard dependency? Does it work with shared infrastructure as expected?
> Capacity planning | What is the forecast, and has it been load tested?
> Failure modes | What happens when each dependency fails or slows?
> Client behaviour | Can the clients cause a retry storm, and can they be updated?
> Processes and automation | Is there a rollback, a runbook, an owner on call?
> Development process and external dependencies | How are changes tested and reviewed? What if a third party is slow, or down?
> Rollout planning | Is it gradual, and what are the stop conditions?
> > A sample question for each area.
**COACH:** The checklist has nine areas, and the table gives one representative question for each. Architecture and dependencies: is there a single point of failure, or a hidden hard dependency? Integration: does it work with shared infrastructure the way that infrastructure expects? Capacity: what is the forecast, and has it been load tested? Failure modes: what happens when each dependency fails or slows? Client behaviour: can clients cause a retry storm, and can they be updated?
**COACH:** Processes: is there a rollback, a runbook, an owner on call? Development process, external dependencies, and rollout planning complete it. These are sample questions for each area.

### Slide 6 · The line to say — A launch checklist exists to make a risky day boring.   `[th]`
**SAY THIS:** A good launch checklist turns a risky day into a boring one. It is a list of questions that past incidents taught you to ask, kept short enough to be used.
*[pause: 0.8]*


## 14.2 Capacity for the day that matters

### Slide 7 · One level down — Headroom is arithmetic, not optimism   `[table · sm]`
> Zones | Capacity needed in total, to survive losing one zone at peak | Spare capacity
> 2 | 200% of peak | 100%
> 3 | 150% of peak | 50%
> 4 | 133% of peak | 33%
> 5 | 125% of peak | 25%
> > Formula: with Z equal zones, losing one leaves Z minus 1, so each must carry peak ÷ (Z minus 1), and the total is Z ÷ (Z minus 1) times peak.
**COACH:** One level down: headroom is arithmetic, not optimism. Suppose you must survive losing a zone at peak. With two zones, each must be able to carry the whole peak, so you need two hundred percent of peak in total. With three zones, the remaining two must carry it, so each carries half the peak, and the total is a hundred and fifty percent. With four zones, a hundred and thirty-three percent. With five, a hundred and twenty-five.
**COACH:** The formula is Z over Z minus one, times the peak. More zones make resilience cheaper, up to a point, which is one reason large systems spread widely.

### Slide 8 · Capacity · The launch version — What to add on top of the steady-state forecast   `[table · sm]`
> Factor | Why | Example treatment
> Launch spike | Interest peaks on day one | Plan for a multiple of normal peak, from the product forecast
> Dependencies | A shared service may not have your headroom | Tell its owners the forecast and the date
> Warm-up | Caches and connection pools start cold | Pre-warm, and ramp gradually
> Quota and limits | You can hit a cap you did not know about | Check the platform limits before the date
> > The Santa story: the imagery service met 25 times its normal peak.
**COACH:** And the launch version of capacity planning. Add the launch spike, because interest peaks on the first day, and plan from the product forecast. Account for dependencies: a shared service may not have your headroom, so tell its owners the forecast and the date. Warm up caches and connection pools, which start cold, and ramp gradually. And check quotas and limits before the date, because you can hit a cap you never knew about. The Santa story shows what a service meets when launch interest arrives: twenty-five times its normal peak.


## 14.3 Techniques for a gradual launch

### Slide 9 · The line to say — Headroom is arithmetic.   `[th]`
**SAY THIS:** Headroom is arithmetic. With Z zones, and one lost, you need Z over Z minus one times the peak, not a feeling.
*[pause: 0.8]*

### Slide 10 · Selected techniques — Four techniques   `[table · sm]`
> Technique | What it does | Watch for
> Gradual, staged rollout | Exposes the change to a few percent, then more, by region or by user | Interacts with caches, and with users who see two versions
> Feature-flag framework | Turns code on per user or per percentage, without a deploy | Flag debt; untested combinations
> Dealing with abusive clients | Detects, limits and isolates clients that misbehave | Legitimate heavy users caught by the limit
> Overload behaviour and load tests | Finds the breaking point and shows what happens beyond it | Test in a safe environment, and keep within committed limits
> > Very few launches at Google are push-button, all-at-once.
**COACH:** There are four techniques. Gradual, staged rollouts expose the change to a few percent, then more, by region or by user, and you watch for interactions with caches and with users who see two versions. Feature flag frameworks turn code on per user or percentage without a deploy, and the risks are flag debt and untested combinations. Dealing with abusive clients means detecting, limiting and isolating those that misbehave. And overload tests find the breaking point and show what happens beyond it. Very few launches at Google are of the push-button kind.

### Slide 11 · The trap — Gatekeeping every launch the same way   `[panel · trap]`
> Treating a copy change and a global product launch alike either wastes the reviewers' time or under-protects the big one.
> Tier launches by risk: small, internal, reversible ones take a light path. Large or irreversible ones get the full review.
> Keep driving convergence and simplification of the checklist, so it stays used.
**ASIDE:** The trap is gatekeeping every launch the same way. Treating a copy change and a global product launch alike either wastes reviewers' time or under-protects the big one. Tier launches by risk: small, internal, reversible changes take a light path, and large or irreversible ones get a full review. Keep driving convergence and simplification, so the checklist stays short enough to be used. A checklist nobody reads has no effect.


## 14.4 Then and now

### Slide 12 · The line to say — Tier launches by risk.   `[th]`
**SAY THIS:** Tier launches by risk, so that the checklist stays short enough to be used.
*[pause: 0.8]*

### Slide 13 · Since 2016 — The checklist became code   `[panel · now]`
> Production readiness is increasingly checked by automation: does the service have an objective, an alert, a rollback, a runbook, a dashboard?
> Feature flags and experiment platforms are standard, with kill switches for every risky new path.
> Waiting rooms and admission control let a service survive a demand spike you cannot capacity-plan for, by queueing or limiting entry.
> Game days rehearse the launch, including the failure of a dependency, before the real date.
**ASIDE:** What has changed since 2016? The checklist became code. Production readiness is increasingly checked by automation: does the service have an objective, an alert, a rollback, a runbook, a dashboard? Feature flags and experiment platforms are standard, with kill switches for every risky new path. Waiting rooms and admission control let a service survive a demand spike you cannot plan for, by queueing or limiting entry. And game days rehearse the launch, including the failure of a dependency, before the real date.

### Slide 14 · Then and now — A launch-day plan on one page   `[table · sm]`
> Time | What | Owner
> Weeks before | Forecast, load test, dependency owners informed | Service team
> Days before | Pre-warm, check quotas, rehearse rollback and the kill switch | Service team and SRE
> Launch | Staged ramp with stop conditions on the dashboard | Launch commander
> After | Review: forecast versus actual, new questions for the checklist | Everyone
> > The last row feeds the checklist: every launch should leave it a little better.
**COACH:** And here is a launch plan on one page. Weeks before: forecast, load test, and tell the dependency owners. Days before: pre-warm, check quotas, and rehearse the rollback and the kill switch. At launch: a staged ramp, with stop conditions on a dashboard, and one launch commander. Afterwards: compare forecast with actual, and add what you learned to the checklist. Every launch should leave the checklist a little better.


## 14.5 Probe drills

### Slide 15 · Interviewer probe — Product wants to launch to everyone on day one. What do you say?   `[probe]`
**INTERVIEWER:** Product wants to launch to everyone on day one. What do you say?
*A strong answer on screen:*
> - Ask what the hard constraint is: a date, a press event, an exclusivity
> - Offer a staged path that meets it: internal, then a small share, then wider, within the same day if needed
> - Prepare a kill switch and a waiting room as the safety net
> - Quantify the risk in error budget and users
**CANDIDATE:** First I find out what the hard constraint really is: a date, a press event, an exclusivity. Then I offer a staged path that still meets it, which can be internal, then a small share, then wider, even within the same day. I make sure there is a kill switch and a waiting room as the safety net. And I put the risk in numbers: how many users, how much error budget, so the decision is the business's, made with eyes open.

### Slide 16 · Interviewer probe — You have a hard launch date and an unknown demand. How do you plan capacity?   `[probe]`
**INTERVIEWER:** You have a hard launch date and an unknown demand. How do you plan capacity?
*A strong answer on screen:*
> - Take a range from product: low, expected, and high
> - Provision for expected plus headroom, with the ability to scale quickly
> - Load test to the high case, and learn the breaking point
> - Plan graceful degradation and admission control for beyond the high case
**CANDIDATE:** I get a range from the product team: a low, an expected, and a high case. I provision for the expected case plus headroom, with a way to scale fast. I load test up to the high case, so I know the breaking point. And for demand beyond the high case I plan graceful degradation and admission control, so that the failure is a slower or smaller service, not a dead one.

### Slide 17 · Interviewer probe — What are the first three questions in a launch review?   `[probe]`
**INTERVIEWER:** What are the first three questions in a launch review?
*A strong answer on screen:*
> - What depends on this, and what does it depend on?
> - What happens when it fails: each dependency, each region?
> - How do we roll back, and how do we know it is going wrong?
**CANDIDATE:** First, what depends on this, and what does it depend on, because hidden dependencies cause most surprises. Second, what happens when it fails: each dependency, each region. And third, how do we roll back, and how do we know it is going wrong, which means the signals and the stop conditions. Those three cover architecture, failure modes and rollout in one pass.


## 14.6 Where this shows up

### Slide 18 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 16 has operational readiness and rollout; part 13 has headroom and static stability.
> - Episode 5: the staged rollout that this episode relies on
> - Episode 10: overload, the failure launches provoke
> - Google's SRE books: the launch chapter and its launch coordination checklist
> - Also: the workbook chapter on non-abstract large system design
**COACH:** Next steps. Part sixteen of the design-room course has operational readiness and rollout, and part thirteen has headroom and static stability. Episode five covered the staged rollout this episode relies on, and episode ten covered overload, the failure launches provoke. Google's free S-R-E books include the launch coordination checklist, and the workbook has a chapter on non-abstract large system design.

