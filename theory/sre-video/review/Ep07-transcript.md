# Episode 7 · Emergencies, incidents and postmortems

Reader transcript generated from `src/ch07.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 7 of 16 · Priority 3 — Emergencies, incidents and postmortems   `[th]`
> How a team behaves when it is on fire, and how it turns the fire into learning.
**COACH:** Episode seven. Four topics in one: emergency response, managing incidents, postmortem culture, and tracking outages. Together they answer a question every manager is eventually asked at three in the morning: who is in charge, what do we do first, and what do we do afterwards, so it does not happen again?
**SAY THIS:** Incidents are inevitable. Chaos during an incident is a choice.
*[pause: 0.8]*


## 7.0 The story that starts it

### Slide 2 · The opening story — How an unmanaged incident fails   `[cards · c3]`
> red Sharp focus on the technical problem :: Everyone stares at the same graph. Nobody tells the customers, or the other teams.
> red Poor communication :: Executives ask for updates by interrupting the engineers. Different people give different answers.
> red Freelancing :: Several people make changes at once, without telling each other. The system's state becomes unknowable.
> > Each of these is a coordination failure, not a technical one.
**COACH:** Start with three ways an unmanaged incident goes wrong. Sharp focus on the technical problem: everyone stares at the same graph, and nobody tells the customers or the other teams. Poor communication: executives ask for updates by interrupting the engineers, and different people give different answers. And freelancing: several people make changes at once without telling each other, so the state of the system becomes unknowable. Each of these is a coordination failure, not a technical one.

### Slide 3 · What this episode covers — Emergencies, incidents, postmortems and outage tracking   `[panel · note]`
> Emergency response, managing incidents, postmortem culture, and tracking outages. Google's books also include an example incident state document and an example postmortem.
**COACH:** This episode covers emergency response, managing incidents, postmortem culture, and tracking outages. Google publishes an example incident state document and an example postmortem, and they are worth reading as templates.


## 7.1 Emergency response

### Slide 4 · Three kinds of emergency — Three real stories   `[cards · c3]`
> amb Test-induced :: A planned test blocked access to one database out of a hundred, to flush out hidden dependencies. It found far more than expected.
> amb Change-induced :: A configuration change to abuse-protection infrastructure was pushed globally on a Friday, and triggered a crash loop in the systems it protects.
> amb Process-induced :: Two turndown requests for the same machines. The second sent nearly the whole fleet to be wiped. You met this in episode three.
> > All three were caused by our own actions, not by failing hardware.
**ASIDE:** Here are three stories, each a kind of emergency. Test-induced: a planned test blocked access to one database out of a hundred, to flush out hidden dependencies, and it found far more than anyone expected. Change-induced: a configuration change to abuse-protection infrastructure was pushed globally on a Friday, and set off a crash loop in the systems it protects. Process-induced: two turndown requests for the same machines, where a subtle bug in the automation sent nearly the whole fleet to be wiped.
**COACH:** You met that one in episode three. Notice that all three came from our own actions, not from failing hardware.

### Slide 5 · What to do when systems break — The advice in order   `[list]`
> ~ The advice is short, and it is the same in every story.
> - Do not panic. You are not alone, and the system is not going to end the world.
> - If you cannot fix it, escalate early: pull in people who can
> - Write it down: keep a log as you go
> - Afterwards, read the history: every outage you have had before
**COACH:** What to do when systems break. First, do not panic: you are not alone, and the system is rarely about to end the world. Second, if you cannot fix it, escalate early. Pull in people who can. Third, write things down as you go. And afterwards, read the history of your own outages, because the best predictor of the next failure is the last one.


## 7.2 Managing an incident

### Slide 6 · The line to say — Unmanaged incidents fail at coordination.   `[th]`
**SAY THIS:** Most unmanaged incidents do not fail at technology. They fail at coordination: no one in charge, no one talking, and everyone changing things.
*[pause: 0.8]*

### Slide 7 · The structure — Roles in a managed incident   `[dia]`
*Diagram:* `svg/e07-incident-roles.svg`
**COACH:** Now the incident command system, which comes from emergency services. The incident commander holds the high-level state and assigns the rest. By default the commander holds every role they have not delegated. The operations lead is the only role that changes the system. The communications lead is the single voice to stakeholders and customers. The planning lead tracks the longer-running work, files the bugs, arranges handoffs and orders food. This is called recursive separation of responsibilities. Counter-intuitively, clear roles give people more autonomy, because nobody has to second-guess a colleague.

### Slide 8 · One level down — What the process needs besides roles   `[table]`
> Element | What it is | Why
> Command post | A known place: a channel, a room, a call | Everyone knows where the truth is
> Live state document | A shared document: current state, hypotheses, actions, owner | Reduces repeated questions, and survives handoff
> Clear, live handoff | The outgoing commander says out loud who is now in charge | No gap, no two commanders
> Declared early | Declare it when you need a second team, users are affected, or an hour has passed | Cheaper to close a small incident than to start one late
> > The test for declaring: a second team needed, customer-visible, unsolved after an hour.
**COACH:** One level down, what the process needs besides roles. A recognised command post, whether a channel, a room or a call, so everyone knows where the truth is. A live state document, with the current state, hypotheses, actions and owners, which reduces repeated questions and survives a handoff. A clear live handoff, where the outgoing commander says out loud who is now in charge. And early declaration. The test is three questions. Do you need a second team? Is the outage visible to customers?
**COACH:** Is it still unsolved after an hour of focused work? If any is yes, declare an incident.

### Slide 9 · The line to say — Declare early.   `[th]`
**SAY THIS:** Declare early. It is cheaper to close a small incident than to start a big one late.
*[pause: 0.8]*

### Slide 10 · The alternative and the price — When a lightweight process is enough   `[table]`
> Situation | Process | Roles
> Small, one team, quickly fixed | Short note in the ticket | One person
> Several teams or customer-visible | Declared incident, command post | Commander plus ops and comms
> Long-running or severe | Full structure, handoffs, status updates on a schedule | All roles, rotating
> > Over-process wastes time. Under-process loses control. Match the structure to the size.
**COACH:** Match the process to the size. A small incident for one team that is fixed quickly needs a note in the ticket and one person. One that spans teams, or that customers can see, needs a declared incident, with a command post, a commander, and operations and communications leads. A long or severe one needs the full structure, with scheduled status updates and rotating handoffs. Over-process wastes time. Under-process loses control.

### Slide 11 · The line to say — In an incident, separate who decides, who acts, and who talks.   `[th]`
**SAY THIS:** In an incident, separate three things: who decides, who changes the system, and who talks to everyone else. Most of the damage in a bad incident comes from mixing them up.
*[pause: 0.8]*


## 7.3 Postmortems

### Slide 12 · The philosophy — What a postmortem is for   `[cards · c2]`
> grn Goals :: Document the incident, understand all contributing causes, and put effective preventive actions in place.
> amb Blameless :: Assume everyone acted in good faith with the information they had. Look at the system, not the person.
> > If people fear punishment, they hide problems, and then you learn nothing.
**COACH:** A postmortem has clear goals. Document the incident. Understand every contributing cause, not just one root. And put effective preventive actions in place. The tenet is that it is blameless. A blameless postmortem assumes everyone involved acted in good faith, with the information they had at the time. The idea comes from healthcare and aviation, where mistakes can be fatal. If people fear punishment, they hide problems, and then the organisation learns nothing.

### Slide 13 · One level down — When to write one, and what goes in it   `[table]`
> Triggers, defined in advance | Contents
> User-visible downtime beyond a threshold | Summary and impact, with numbers
> Data loss of any kind | Timeline, with times
> An on-call intervention such as a rollback | Root causes plural, and what went well
> Resolution time above a threshold | Action items with owners, priority and a tracker link
> A monitoring failure | Lessons learned: what went wrong, where we got lucky
> > Define the triggers before the incident, so no one has to argue about whether to write one.
**COACH:** One level down. Write a postmortem when a pre-agreed trigger fires: user-visible downtime beyond a threshold, any data loss, an intervention such as a rollback, a long resolution time, or a monitoring failure. Any stakeholder may also ask for one. A good document contains the impact with numbers, a timeline with times, the causes in the plural, what went well, and what went wrong. And where we got lucky. And, above all, action items, each with an owner, a priority, and a link to a tracker.

### Slide 14 · The trap — A postmortem with no follow-through   `[panel · trap]`
> A list of action items that nobody tracks is theatre.
> Review open actions on a schedule, and report the completion rate.
> Prefer a few actions that remove a class of failure over many that fix one instance.
**ASIDE:** The trap: a postmortem with no follow-through. A list of action items that nobody tracks is theatre. Review open actions on a schedule, and report the completion rate. And prefer a few actions that remove a whole class of failure over many that fix one instance. There are also cultural tools: sharing postmortems widely, reviewing them in forums, and rewarding people publicly for finding and writing up a problem well.


## 7.4 Tracking outages

### Slide 15 · The line to say — A postmortem without tracked actions is theatre.   `[th]`
**SAY THIS:** A postmortem is blameless, and it is only worth writing if its actions are owned, tracked, and finished.
*[pause: 0.8]*

### Slide 16 · Aggregation, tagging, analysis — Learn from the pattern, not only the incident   `[table]`
> Step | What it does
> Aggregate | Group related alerts into one incident, so ten alerts are one event
> Tag | Label by cause, service, type, so you can ask questions later
> Analyse | Across incidents: which cause is the top source of pages, of downtime?
> > One such tool is called the Outalator. What matters is the habit: a history you can query.
**COACH:** The last topic is learning from the pattern, not only the incident. Aggregate related alerts into a single incident, so ten alerts are one event. Tag each by cause, service and type, so you can ask questions later. And analyse across incidents: which cause is the top source of pages, and of downtime? One such tool is called the Outalator. What matters is the habit: a history you can query, so that you invest in the cause that costs you most, not the one you remember best.


## 7.5 Then and now

### Slide 17 · The line to say — Invest in the cause that costs the most.   `[th]`
**SAY THIS:** Keep a history you can query, so you invest in the cause that costs you most, not the one you remember best.
*[pause: 0.8]*

### Slide 18 · Then and now — One incident, and the numbers a manager should track   `[dia]`
*Diagram:* `svg/e07-incident-timeline.svg`
**COACH:** Here is an incident drawn as a timeline, with the numbers a manager tracks. Something starts. Some time later it is detected: that is time to detect. Some time after that, a human is engaged, and the incident is declared. Then the impact is mitigated, which is the time to mitigate that users feel. Then comes the full resolution, and later the postmortem and the actions. Most improvement comes from shortening detect and mitigate, not from perfect root causes.

### Slide 19 · Since 2016 — What the practice looks like today   `[panel · now]`
> Incident tooling is built into chat: one command opens a channel, assigns roles, keeps a timeline, and posts to a status page.
> Severity levels define who is paged and how fast. On-call training uses simulated incidents.
> The "learning from incidents" movement adds interviews and richer narratives to the blameless tradition, and asks why the decision made sense at the time.
> AI helps with timelines, summaries and drafts. Treat these as drafts; a human verifies facts and owns the conclusions.
**ASIDE:** What has changed? Incident tooling is built into chat. One command opens a channel, assigns roles, keeps a timeline and posts to a status page. Severity levels define who is paged and how fast, and training uses simulated incidents. A learning from incidents movement has added interviews and richer narratives to the blameless tradition, and asks why a decision made sense at the time. And assistants help with timelines, summaries and drafts, but a human verifies the facts and owns the conclusions.


## 7.6 Probe drills

### Slide 20 · Interviewer probe — You are the incident commander and a senior engineer starts making changes without telling anyone. What do you do?   `[probe]`
**INTERVIEWER:** You are the incident commander and a senior engineer starts making changes without telling anyone. What do you do?
*A strong answer on screen:*
> - Name it calmly: freelancing is the failure the structure exists to stop
> - Give them a role: for example, a sub-incident or the ops lead
> - Require changes to go through ops, with the log updated
**CANDIDATE:** I name it calmly and privately if I can, but quickly, because unannounced changes make the system's state unknowable. Then I give the person a role that uses their skill, for example leading a sub-incident on the component they understand, or making changes as the ops lead. Changes go through the ops role and are written in the live document. The structure is there to channel experience, not to suppress it.

### Slide 21 · Interviewer probe — The executive wants updates every five minutes. How do you handle it?   `[probe]`
**INTERVIEWER:** The executive wants updates every five minutes. How do you handle it?
*A strong answer on screen:*
> - One communications lead gives updates, on a fixed schedule
> - The commander and ops are not interrupted
> - Updates say: impact, what we know, what we are doing, next update time
**CANDIDATE:** I assign a communications lead, and agree a fixed schedule for updates, say every thirty minutes, with the time of the next one always stated. The executive reads those, and the commander and the operations lead are not interrupted. Each update gives the impact, what we know, what we are doing, and when the next update comes. People ask for constant updates when they do not trust that someone is in charge, so predictability fixes the cause.

### Slide 22 · Interviewer probe — A postmortem blames the engineer who ran the command. Respond.   `[probe]`
**INTERVIEWER:** A postmortem blames the engineer who ran the command. Respond.
*A strong answer on screen:*
> - Ask: why was it possible for one command to do that?
> - Look for the missing guardrail, review, or rate limit
> - People will not report problems if they expect blame
**CANDIDATE:** I would redirect it. The question is why a single command could cause that much damage, and where the missing guardrail, review or rate limit was. The engineer acted on the information and tools they had. If we blame the person, the next engineer hides the next near miss, and we lose the information that would have prevented it.


## 7.7 Where this shows up

### Slide 23 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 16 has the manager layer: operational readiness, kill switches, and on-call design.
> - Episode 10: cascading failure, the incident the structure was built for
> - Episode 15: training people to handle incidents
> - Google's SRE books: the chapters on emergency response, incidents and postmortems, and the example documents in the appendices
> - Also: the workbook chapters on incident response and postmortem culture
**COACH:** Next steps. Part sixteen of the design-room course has the manager layer, including operational readiness, kill switches, and on-call design. Episode ten covers cascading failure, the incident these structures were built for. Episode fifteen is about training people to handle incidents. Google's free S-R-E books include an example state document and an example postmortem, and the workbook has chapters on incident response and postmortem culture.

