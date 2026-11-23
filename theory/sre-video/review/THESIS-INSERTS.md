# Key-thesis inserts

Every line below is spoken by the **SAY THIS** voice (slower, a different voice from the narrator), which breaks up long
stretches of one voice and gives the viewer the sentence to repeat in an interview. Review these first: if a thesis is
wrong or weak, the episode is wrong or weak.


## Episode 1 · What SRE is, and the world it runs in

- **SRE course · Episode 1 of 16 · Priority 2** (slide 1): Reliability is the most important feature. A system nobody can use does not have other features.
- **The line to say** (slide 7): Cap the operations work, and the team is forced to automate. Without a consequence for exceeding the cap, you have the old model with a new job title.
- **The line to say** (slide 9): The team that carries the pager also owns the rate of change. That is the whole mechanism, because it puts the cost of unreliability and the benefit of velocity in the same room.
- **Episode 1 · the line to say** (slide 15): Site reliability engineering is what you get when you ask software engineers to design an operations function. The cost of operations is capped, so the team is forced to automate.

## Episode 2 · Risk, SLIs, SLOs and error budgets

- **SRE course · Episode 2 of 16 · Priority 1** (slide 1): One hundred percent is the wrong reliability target for almost everything.
- **The line to say** (slide 8): Choose the reliability target a user can feel and the business will pay for. Beyond that, extra nines buy nothing, and cost both money and speed of change.
- **The line to say** (slide 12): The error budget turns an argument about risk into a number agreed in advance. While there is budget, ship. When it is spent, slow down and invest in reliability.
- **The line to say** (slide 16): An indicator is a measurement. An objective is a target for it. An agreement is a contract, and it is always looser than the objective.
- **Episode 2 · the line to say** (slide 18): Do not alert on a threshold. Alert on how fast the budget is burning, over a short window and a long one together.

## Episode 3 · Toil and automation

- **SRE course · Episode 3 of 16 · Priority 2** (slide 1): Automation is a force multiplier. That is also exactly why it is dangerous.
- **The line to say** (slide 7): Toil is work tied to running a service that is manual, repetitive and automatable, and it grows in step with the service. The goal is not zero toil. The goal is a ceiling, and a plan to remove the largest source first.
- **The line to say** (slide 11): The first value of automation is consistency, and the first risk is blast radius. Decide how much any one run may touch before you write the first line.
- **Episode 3 · the line to say** (slide 14): Automation removes toil, and it also turns one mistake into a fleet-wide event. So every automation needs a limit on how much it can touch at once, and a way to stop it.

## Episode 4 · Monitoring and alerting

- **SRE course · Episode 4 of 16 · Priority 1** (slide 1): A page is the most expensive thing a system can do to a human. Spend it carefully.
- **The line to say** (slide 8): Page on what the user feels, debug with what the machine says, and keep latency as a distribution, because you cannot average a percentile.
- **The line to say** (slide 13): Time to detect is a sum of delays, and the biggest one is usually the hold time you chose on purpose, to stay quiet.
- **The line to say** (slide 16): If silence can mean broken, the alerting path needs an alarm of its own: a signal that is always firing, and a check that pages when it stops.
- **Since 2016 · the line to say** (slide 18): Every distinct label value is a new time series. Count the series before you add the label, because the monitoring system can be taken down by its own users.

## Episode 5 · Release engineering and simplicity

- **SRE course · Episode 5 of 16 · Priority 2** (slide 1): Every release is an experiment on production. The craft is making the experiment small.
- **The line to say** (slide 7): A rollback you cannot rebuild is a rollback you do not have. That is why builds are hermetic, and tools are versioned with the code.
- **The line to say** (slide 9): A safe release is small, reproducible, staged and reversible. If any one of those is missing, you are relying on luck.
- **the line to say** (slide 12): Decide the smallest regression you must catch. Then size the canary, and the bake time, so that you would actually see it.
- **The line to say** (slide 15): Boring is a feature. Every line you delete is a line that cannot fail at three in the morning.
- **Since 2016 · the line to say** (slide 18): You can only vouch for a build you can reproduce. Hermetic builds are the foundation of provenance.
- **Episode 5 · the line to say** (slide 20): A rollout is a statistics problem. Size the canary to the smallest regression you must catch, bake long enough to see it, and decide the abort rule before you start.

## Episode 6 · On-call and effective troubleshooting

- **SRE course · Episode 6 of 16 · Priority 3** (slide 1): Troubleshooting is not a talent. It is a loop, and the loop can be taught.
- **The line to say** (slide 7): A pager that people ignore protects nothing. Every page that did not need a human is a bug in the alerting, fixed the next working day.
- **The line to say** (slide 10): In an outage, restore service first, and understand second. A fix you cannot explain is a delay, not a cure.
- **The line to say** (slide 13): Stabilise first. Then form a hypothesis, test one thing at a time, and record what you learned, because a negative result is still a result.

## Episode 7 · Emergencies, incidents and postmortems

- **SRE course · Episode 7 of 16 · Priority 3** (slide 1): Incidents are inevitable. Chaos during an incident is a choice.
- **The line to say** (slide 6): Most unmanaged incidents do not fail at technology. They fail at coordination: no one in charge, no one talking, and everyone changing things.
- **The line to say** (slide 9): Declare early. It is cheaper to close a small incident than to start a big one late.
- **The line to say** (slide 11): In an incident, separate three things: who decides, who changes the system, and who talks to everyone else. Most of the damage in a bad incident comes from mixing them up.
- **The line to say** (slide 15): A postmortem is blameless, and it is only worth writing if its actions are owned, tracked, and finished.
- **The line to say** (slide 17): Keep a history you can query, so you invest in the cause that costs you most, not the one you remember best.

## Episode 8 · Testing for reliability, and software engineering in SRE

- **SRE course · Episode 8 of 16 · Priority 2** (slide 1): If you have not tried it, assume it is broken.
- **The line to say** (slide 6): Testing is the cheapest form of repair. A bug caught before release takes zero time to repair.
- **The line to say** (slide 10): Testing is how a team measures confidence. A failing test is cheap knowledge. Every path that matters, including recovery, should be exercised before the day it is needed.

## Episode 9 · Load balancing, at the edge and inside the datacenter

- **SRE course · Episode 9 of 16 · Priority 1** (slide 1): Load balancing is not about being fair. It is about keeping every machine below the point where it falls over.
- **The line to say** (slide 6): D-N-S is the simplest first layer and is never sufficient alone, because resolvers cache and the time to live limits how fast you can steer.
- **The line to say** (slide 8): Balance in layers. D-N-S steers users to a place. A virtual address steers connections to a front end. The client steers each request to a backend, with the best information available.
- **The line to say** (slide 11): When you need even load, do not leave it to chance. Design the assignment of clients to backends.
- **The line to say** (slide 14): More information gives a better spread, and costs more complexity. Choose the simplest policy that keeps the hottest machine safe.
- **Episode 9 · the line to say** (slide 16): Moving the balancer into the platform does not remove the need to budget retries, because a retry is load.

## Episode 10 · Overload and cascading failure

- **SRE course · Episode 10 of 16 · Priority 1** (slide 1): A system under overload must do less work, not more. Everything else is a detail.
- **The line to say** (slide 6): A cascading failure is a positive feedback loop. Each lost server makes the remaining servers' job harder, so they fail faster. You break it by reducing the work, not by adding machines to the loop.
- **The line to say** (slide 10): A rejected request should cost the backend almost nothing, or shedding load saves you nothing.
- **The line to say** (slide 13): Not every request deserves to survive. Label them, and drop the cheapest to lose first.
- **The line to say** (slide 16): A request that nobody is waiting for is the purest form of wasted work. Pass the deadline down, and stop when it is gone.
- **The line to say** (slide 18): Under overload, fail early and cheaply. Reject at the edge, drop the least critical work first, never retry into an overloaded place, and never spend effort on a request whose deadline has passed.

## Episode 11 · Distributed consensus for critical state

- **SRE course · Episode 11 of 16 · Priority 1** (slide 1): If two machines can both believe they are in charge, one day they will.
- **The line to say** (slide 6): Consensus means a group agrees on one ordered history, as long as a majority can talk to each other. Safety never depends on timing. Progress does.
- **The line to say** (slide 18): Paxos in one breath. Promise to ignore older proposals, and if anything may already be chosen, repeat it. Everything else is making that survive crashes, and repeating it for every slot.
- **The line to say** (slide 19): Commit latency is the round trip to the nearest majority, plus the disk write. Place the replicas with that in mind.
- **The line to say** (slide 22): Four replicas tolerate one failure, the same as three. Five tolerate two, which lets you survive a failure during maintenance.
- **The line to say** (slide 25): Use consensus for the small state that must be right, such as leaders, locks and metadata. Never put the bulk data through it.

## Episode 12 · Distributed cron and data pipelines

- **SRE course · Episode 12 of 16 · Priority 1** (slide 1): The hardest question in scheduling is not when to start. It is what to do when you do not know whether you already did.
- **The line to say** (slide 7): Unless the owner says otherwise, prefer skipping a launch to launching twice, because a skip can be repaired and a double often cannot.
- **The line to say** (slide 9): A scheduler cannot know whether it launched. So it records its intent before the side effect and its completion after, and the job's owner decides in advance whether an unknown launch is skipped or repeated.
- **The line to say** (slide 11): A periodic pipeline hides its failures. Alert on freshness and backlog, not on whether the last run exited cleanly.
- **The line to say** (slide 14): Give every output a unique name, and every commit a lease. An orphaned worker can write, but it cannot commit.
- **Then and now · the line to say** (slide 18): Treat data quality as a service level indicator: freshness, completeness and correctness, each with a target.

## Episode 13 · Data integrity, what you read is what you wrote

- **SRE course · Episode 13 of 16 · Priority 1** (slide 1): Nobody wants backups. They want restores.
- **The line to say** (slide 6): Replication protects you from a machine dying. It does not protect you from a bug, because it copies the bug everywhere, quickly. Only a tested restore protects you from that.
- **The line to say** (slide 9): Early detection is what makes the other layers usable. A restore point only helps if you notice in time.
- **The line to say** (slide 12): Restore time grows with the size of the data, so a recovery objective is an engineering problem, not a purchase.
- **The line to say** (slide 14): A check that shares its path with the thing it checks will fail with it. Validate out of band.

## Episode 14 · Reliable product launches at scale

- **SRE course · Episode 14 of 16 · Priority 2** (slide 1): A launch is a change with a deadline and an audience. That is the riskiest kind there is.
- **The line to say** (slide 6): A good launch checklist turns a risky day into a boring one. It is a list of questions that past incidents taught you to ask, kept short enough to be used.
- **The line to say** (slide 9): Headroom is arithmetic. With Z zones, and one lost, you need Z over Z minus one times the peak, not a feeling.
- **The line to say** (slide 12): Tier launches by risk, so that the checklist stays short enough to be used.

## Episode 15 · People: training, interrupts, overload and engagement

- **SRE course · Episode 15 of 16 · Priority 3** (slide 1): A reliability team is a system too. It has load, failure modes and a control loop.
- **The line to say** (slide 6): Structure beats chaos: a learning path, a real project, shadowing, and only then the pager.
- **The line to say** (slide 9): Interruptions need an owner, or they land on everyone, and nobody finishes anything hard.
- **The line to say** (slide 11): Operational overload is a condition with measurable symptoms and a recovery plan. The first step is to make it visible, and the second is to help the team change it without taking it over.
- **The line to say** (slide 15): Each step in the engagement model trades effort per service for upfront investment and adoption. Choose per service, by criticality.

## Episode 16 · Lessons from other industries, and the close

- **SRE course · Episode 16 of 16 · Priority 3** (slide 1): Reliability is not a feature you add. It is the discipline of making failure ordinary.
- **Appendix B · the line to say** (slide 6): When configuration changes look implausible, keep running on the previous version, and tell a human. A system that accepts any input will one day accept the worst one.
- **The whole course · the line to say** (slide 9): Name the failure, bound the blast radius, and rehearse the recovery. That is the whole course in one sentence.
- **Episode 16 · the last line** (slide 16): The goal of site reliability engineering is to make failure ordinary, and then make it boring. Plan for it, practise it, measure it, and learn from it.
