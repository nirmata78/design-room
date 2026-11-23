# Episode 6 · On-call and effective troubleshooting

Reader transcript generated from `src/ch06.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 6 of 16 · Priority 3 — On-call and effective troubleshooting   `[th]`
> A sustainable pager, and a method for finding the fault when it rings.
**COACH:** Episode six. Two topics about people at the sharp end of a system. Being on call, and how to make it sustainable. And troubleshooting, a method that works when your intuition is tired. We finish with what tooling now changes, and what it does not.
**SAY THIS:** Troubleshooting is not a talent. It is a loop, and the loop can be taught.
*[pause: 0.8]*


## 6.0 The story that starts it

### Slide 2 · The opening story — Two engineers, the same alert, the same four hours   `[cards · c2]`
> red Guessing :: Restarts the service, then the cache, then rolls back last week's release. Changes three things, so nothing can be learned from the result.
> grn Hypothesis :: "Errors started at 14:02, only in one region, right after a configuration push." Tests that one idea, and learns something either way.
> > A fix you cannot explain is a delay, not a cure.
**COACH:** Two engineers get the same alert and spend four hours. The first guesses. Restart the service, then the cache, then roll back last week's release. Three changes at once, so nothing can be learned from the outcome. The second forms a hypothesis from the evidence: errors started at two in the afternoon, only in one region, right after a configuration push. She tests that one idea, and learns something whatever the answer. A fix you cannot explain is a delay, not a cure.

### Slide 3 · What this episode covers — Being on call, and troubleshooting   `[panel · note]`
> Being on call, and effective troubleshooting. Google's workbook chapter on on-call adds a lot of practical detail.
**COACH:** This episode covers being on call, and effective troubleshooting. There is a long treatment of on-call with numbers, and I will point you to it at the end.


## 6.1 Being on call

### Slide 4 · Balance in quantity — The numbers that make a rota sustainable   `[table]`
> Rule | Number | What follows
> On-call share of time | at most 25% | Plus up to 25% other operational work, leaving at least half for engineering
> Events per shift | at most 2 per 8 to 12 hours | Enough time to fix, clean up and write the postmortem
> Single-site team | at least 8 engineers | Primary and secondary, week-long shifts
> Two-site team | at least 6 per site | Follow the sun, so nobody works nights
> > If the numbers are not met, the load is operational overload.
**COACH:** Here are numbers for a sustainable rota. On call takes at most a quarter of an engineer's time, with up to a quarter more for other operational work, leaving at least half for engineering. A shift should see at most two events in eight to twelve hours, which leaves enough time to fix the problem, clean up, and write a postmortem. A single-site team needs at least eight engineers, and a two-site team at least six per site, so that nobody works nights. If you cannot meet those numbers, call it operational overload.

### Slide 5 · Balance in quality — Four ways to keep the pager humane   `[panel · key]`
> Follow the sun where you can: night shifts damage health, and there is evidence for it.
> Compensate out-of-hours work: time in lieu or pay, with a cap that doubles as a limit on how much on-call there can be.
> Feeling safe: a stressed engineer makes fast, intuitive, worse decisions. Give them runbooks, a clear escalation path, and permission to ask for help.
> Watch underload too: an engineer who is paged once a year loses the skill. Run drills.
**COACH:** Quantity is not enough. Quality matters. Follow the sun where you can, because night shifts damage health. Compensate out-of-hours work, in time or in money, and note that the cap on compensation doubles as a limit on how much on call there can be. Make people feel safe: a stressed engineer makes fast, intuitive and worse decisions, so give them runbooks, a clear path to escalate, and permission to ask for help. And watch underload. An engineer who is paged once a year loses the skill, so run drills.

### Slide 6 · The trap — Alerts that nobody acts on   `[panel · trap]`
> If the on-call engineer ignores half the pages, the pager does not protect the service. It trains people to ignore the pager.
> Every page that does not need a human is a bug in the alerting. Fix it the next working day.
> Measure: pages per shift, share that were actionable, time to acknowledge.
**ASIDE:** The trap is alerts that nobody acts on. If the engineer ignores half the pages, the pager is no longer protecting the service, it is training people to ignore it. Every page that does not need a human is a bug in the alerting, and it gets fixed the next working day. And measure it: pages per shift, the share that were actionable, and the time to acknowledge.


## 6.2 A method for troubleshooting

### Slide 7 · The line to say — A pager nobody acts on protects nothing.   `[th]`
**SAY THIS:** A pager that people ignore protects nothing. Every page that did not need a human is a bug in the alerting, fixed the next working day.
*[pause: 0.8]*

### Slide 8 · The loop — Hypothesise, test, learn, and repeat   `[dia]`
*Diagram:* `svg/e06-troubleshoot-loop.svg`
**COACH:** Treat troubleshooting as the scientific method. You start with a problem report. You triage: how bad is it, and can you reduce the harm right now? You examine the system, with its metrics, logs and traces. You form a hypothesis about the cause, and you test it, either by comparing what you see with what the hypothesis predicts, or by making a controlled change. If the test fails, you have learned something, and you go round again.
**COACH:** If it succeeds, you treat the cause and then you cure it, which means making sure it cannot happen the same way again.

### Slide 9 · Triage first — In an outage, restore service before you find the cause   `[table]`
> Move | Why
> Stop the bleeding: roll back, shift traffic, shed load | Users first, understanding second
> Preserve evidence: logs, snapshots, the failing instance | You will need them later
> Reduce the problem to a smaller one | Simpler to examine
> Ask: what changed, and what touched it last? | Most outages follow a change
> > The first priority is to stabilise, not to find the root cause.
**COACH:** Triage comes first. In an outage, restore service before you find the cause. Stop the bleeding by rolling back, shifting traffic or shedding load. Preserve evidence as you go, because you will need the logs and the failing instance later. Reduce the problem to a smaller one that is easier to examine. And always ask what changed, and what last touched the system, because most outages follow a change.

### Slide 10 · The line to say — In an outage, restore first. Understand second.   `[th]`
**SAY THIS:** In an outage, restore service first, and understand second. A fix you cannot explain is a delay, not a cure.
*[pause: 0.8]*

### Slide 11 · One level down — Three questions that narrow the search   `[table]`
> Question | Answers | Example
> What is it doing? | The symptom | Errors, not latency; only on writes
> Why is it doing that? | The mechanism | The connection pool is exhausted
> Where is the resource going? | The location | Which cluster, which version, which dependency
> > Split the system in half and test each half. Divide and conquer beats staring at a graph.
**COACH:** One level down. Three questions narrow the search. What is the system doing: errors, not latency, only on writes. Why is it doing that: the mechanism, such as an exhausted connection pool. And where is the resource going: which cluster, which version, which dependency. When the picture is unclear, divide and conquer. Split the system in half, test each half, and repeat. That beats staring at a graph.

### Slide 12 · Easy to confuse — Correlation and causation, in the middle of the night   `[panel · watch]`
> Two graphs that move together may share a third cause, or one may be an effect of the other.
> Look for the direction: what happened first?
> Treat every candidate cause as a hypothesis with a test: if this is the cause, what else must be true?
**ASIDE:** One pitfall. Two graphs that move together may share a third cause, or one may be an effect of the other. At three in the morning, correlation looks like an answer. Look for the direction: what happened first? And treat every candidate cause as a hypothesis with a test. If this is the cause, what else must be true? Then go and look for that.

### Slide 13 · The line to say — Form a hypothesis, test one thing, and write down what you learned.   `[th]`
**SAY THIS:** Stabilise first. Then form a hypothesis, test one thing at a time, and record what you learned, because a negative result is still a result.
*[pause: 0.8]*


## 6.3 Negative results and making it easier

### Slide 14 · Negative results are magic — Why ruling something out is progress   `[panel · key]`
> A negative result is solid knowledge: this is not the cause, and it is not the cause of the next outage either.
> Write it down. The next person will not repeat the test.
> Publish findings in a shared place, so the knowledge outlives the shift.
**COACH:** There is a line worth remembering: negative results are magic. A test that rules something out is solid knowledge. It also protects the next engineer from repeating it. So write down what you ruled out and where, and publish it somewhere the whole team can find, so the knowledge outlives the shift.

### Slide 15 · Making troubleshooting easier, with additions — Design for the person who will debug it   `[list]`
> ~ Most of the speed of diagnosis is decided before the incident.
> - Build in observability: metrics, logs, traces from the start
> - Give every component a well-understood interface and a way to test it alone
> - Make the recent change history one query away
> - Keep runbooks current, and link them from the alert
> - Practise: wheel-of-misfortune style drills with a real playbook
**COACH:** Most of the speed of diagnosis is decided before the incident. Build in observability, with metrics, logs and traces from the start. Give every component a well-understood interface and a way to test it alone. Make recent change history one query away. Keep runbooks current and link them from the alert. And practise, with drills that use a real playbook, so that the loop is a habit when it matters.


## 6.4 Then and now

### Slide 16 · Since 2016 — The evidence is easier to reach, the method is the same   `[panel · now]`
> Distributed tracing makes "where is the time going" a click, and exemplars link a metric to a trace.
> Change correlation: tooling shows the deploys, flag flips and configuration pushes near the start of an incident.
> AI-assisted triage summarises alerts, proposes hypotheses and drafts timelines. Treat its output as a hypothesis to test, not a conclusion.
> On-call health is now measured and reviewed: pages per shift, night interrupts, load per person.
**ASIDE:** What has changed since 2016? The evidence is easier to reach, and the method is the same. Distributed tracing makes the question of where the time is going a single click. Tooling shows the deploys, flag flips and configuration pushes near the start of an incident. Assistants summarise alerts, propose hypotheses and draft timelines, but treat their output as a hypothesis to test, not as a conclusion. And on-call health is now measured and reviewed: pages per shift, night interruptions and load per person.


## 6.5 Probe drills

### Slide 17 · Interviewer probe — You are on call. Latency doubled ten minutes ago. Walk me through the first five minutes.   `[probe]`
**INTERVIEWER:** You are on call. Latency doubled ten minutes ago. Walk me through the first five minutes.
*A strong answer on screen:*
> - Acknowledge, and check impact: how many users, which requests
> - Ask what changed: deploys, flags, config, traffic
> - If a change lines up, roll it back before you fully understand it
> - Open an incident if the impact is large, and share what you know
**CANDIDATE:** I acknowledge the page and check the impact: how many users, which requests, whether the error budget is burning. Then I ask what changed in the last half hour: deploys, flags, configuration, traffic shape. If one lines up with the start, I roll it back before I fully understand it, because restoring service comes first. If the impact is large, I open an incident and write down what I know, so others can join.

### Slide 18 · Interviewer probe — You rolled back and it did not help. What next?   `[probe]`
**INTERVIEWER:** You rolled back and it did not help. What next?
*A strong answer on screen:*
> - The rollback is a negative result: it was not that change
> - Check dependencies and shared resources, not only your own code
> - Split the path: which hop adds the time?
> - Escalate: bring in the dependency owners early
**CANDIDATE:** Then I have learned something: the change was not the cause. I look wider, at dependencies and shared resources, because the fault may be outside my own code. I split the request path and ask which hop adds the time, using traces if I have them. And I bring in the owners of the suspect dependency early, because waiting to be sure costs more than a false alarm.

### Slide 19 · Interviewer probe — Your on-call team gets six pages a shift. What do you do?   `[probe]`
**INTERVIEWER:** Your on-call team gets six pages a shift. What do you do?
*A strong answer on screen:*
> - Quantify: which alerts, how many are actionable
> - Fix or delete the noisy alerts first
> - Tune thresholds toward symptoms and budget burn
> - Plan the engineering work that removes recurring causes
> - If it stays high, shift load back to the developers
**CANDIDATE:** I start by counting. Which alerts fire most, and how many needed a human. Noisy alerts are fixed or deleted first, because they are the cheapest win. I move the paging rules toward symptoms and budget burn. Then I plan the engineering that removes the recurring causes. And if the load stays above the limit, I use the escalation: shift some of the load back to the developers.


## 6.6 Where this shows up

### Slide 20 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 13 and part 14 use these skills: the wrap-up of every design round asks "how would you know?".
> - Episode 7: when a page becomes an incident, and what happens after
> - Episode 4: the signals you reach for first
> - Google's SRE books: the chapters on on-call and troubleshooting, then the workbook on-call chapter
> - Exercise: take your last real incident and redraw the loop, with the hypotheses you tested
**COACH:** Next steps. The wrap-up of every design round asks how you would know something broke, and parts thirteen and fourteen of the design-room course build on these skills. Episode seven covers what happens when a page becomes an incident. Episode four covered the signals you reach for first. Google's free S-R-E books cover both, and here is an exercise: take your last real incident and redraw the loop, with the hypotheses you actually tested.

