# Episode 15 · People: training, interrupts, overload and engagement

Reader transcript generated from `src/ch15.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 15 of 16 · Priority 3 — People: training, interrupts, overload and engagement   `[th · aux]`
> How to train an on-caller, protect focus, rescue an overloaded team and decide when an SRE team should take a service on.
**COACH:** Episode fifteen. This episode is about the management of a reliability organisation. Five topics: training new engineers, handling interrupts, recovering a team from operational overload, communicating and collaborating, and deciding how and when to engage with a service. For a manager, this is the territory that your technical answers will be judged against. In a Staff individual contributor round it is an optional layer, so the badge on these slides says so.
**SAY THIS:** A reliability team is a system too. It has load, failure modes and a control loop.
*[pause: 0.8]*


## 15.0 The story that starts it

### Slide 2 · The opening story — The same hire, two first months   `[cards · aux c2]`
> red Chaos :: Handed a pager and a wiki of old runbooks. Learns by reading alarms at three in the morning. Becomes cautious, then afraid.
> grn Structure :: A learning path, a small real project, shadowing before leading, drills against a safe copy. The first real page is familiar.
> > Confidence under pressure is built before the pressure.
**COACH:** The same new hire, two different first months. In the first, they are handed a pager and a wiki of old runbooks, and learn by reading alarms at three in the morning. They become cautious, then afraid. In the second, there is a learning path, a small real project, shadowing before leading, and drills against a safe copy of the system. When the first real page arrives, it is familiar. Confidence under pressure is built before the pressure.

### Slide 3 · What this episode covers — Training, interrupts, overload, collaboration and engagement   `[panel · note]`
> Accelerating engineers to on call and beyond, dealing with interrupts, embedding an engineer to recover from operational overload, communication and collaboration, and the evolving engagement model.
**COACH:** This episode covers accelerating engineers to on call, dealing with interrupts, embedding an engineer to recover from overload, communication and collaboration, and the evolving engagement model.


## 15.1 Training engineers to be on call

### Slide 4 · Five practices — How to prepare people for the pager   `[list · aux]`
> ~ Structure beats chaos, and for engineers who can reverse-engineer a system and think under pressure.
> - A hunger for failure: read and share postmortems
> - Disaster role-playing: act out a failure with a guide, in a safe setting
> - Break real things, fix real things: in a test environment, on purpose
> - Documentation as apprenticeship: new people improve the docs as they learn
> - Shadow on-call early and often
**COACH:** Five practices. A hunger for failure: read and share postmortems. Disaster role-playing: act out a failure with a guide, in a safe setting. Break real things and fix real things, in a test environment, on purpose. Documentation as apprenticeship: new people improve the docs as they learn. And shadow on call early and often. Underneath is a belief: you want engineers who can reverse-engineer a system, think statistically under pressure, and improvise when the unexpected happens.

### Slide 5 · One level down — A learning path that is cumulative   `[table · sm aux]`
> Stage | What the person does | Evidence they are ready for the next
> Orientation | Reads architecture and the service's postmortems | Can explain a request path and the top failure modes
> Targeted project | A real project that matters, sized for a newcomer | Ships it, and learns the tools on the way
> Shadowing | Sits in on pages and incidents | Narrates what they would do, and compares
> Secondary on-call | Primary is available, and is the escalation | Handles pages with little help
> Primary on-call | Fully responsible, with a safety net | Reviews their own handling
> > Targeted project work teaches more than menial work.
**COACH:** One level down, a learning path that is cumulative. Orientation: read the architecture and the postmortems, and explain a request path. A targeted project: a real project that matters, sized for a newcomer. Shadowing: sit in on pages and incidents, and narrate what you would do. Secondary on call, with the primary available as escalation. Then primary on call, with a safety net. Each stage has evidence that the person is ready for the next. Targeted project work teaches more than menial work.


## 15.2 Interrupts and focus

### Slide 6 · The line to say — Structure beats chaos.   `[th · aux]`
**SAY THIS:** Structure beats chaos: a learning path, a real project, shadowing, and only then the pager.
*[pause: 0.8]*

### Slide 7 · Operational load — Three kinds, and how to handle each   `[table · sm aux]`
> Kind | What it is | A good way to handle it
> Pages | Production alerts, with an expected response time | A rota, with the primary dedicated to them
> Tickets | Requests and issues from other people | A dedicated person per shift, and a clear queue
> Ongoing operations | Releases, maintenance, recurring tasks | Scheduled, automated where possible
> > The advice: do one thing well. A person who is interrupted cannot also hold a complex design in their head.
**COACH:** Split operational load into three kinds. Pages: production alerts, with an expected response time. Tickets: requests and issues from other people. And ongoing operations: releases, maintenance, recurring tasks. A good way to handle each: pages go to a rota with a primary dedicated to them, tickets to a dedicated person per shift, and ongoing operations are scheduled and automated where possible. The advice is to do one thing well. A person who is constantly interrupted cannot also hold a complex design in their head.

### Slide 8 · Cognitive flow — Why this is an engineering problem, not a discipline problem   `[panel · key aux]`
> Engineers are imperfect machines: each interruption costs more than the time spent on it, because the state in their head is lost.
> Design the team's structure so that interruptions have an owner. Give the person on interrupts the job, and protect everyone else.
> Make the process clear: tell people what to do, not a vague policy.
> Reduce interrupts at the source: fix the cause of recurring tickets.
**COACH:** Why is this an engineering problem, and not a discipline problem? Engineers are imperfect machines. Each interruption costs more than the time spent on it, because the state in the person's head is lost. So design the team's structure so that interruptions have an owner: give the person on interrupts that job, and protect everyone else. Make the process clear, with explicit instructions instead of vague policy. And reduce interrupts at the source, by fixing the cause of recurring tickets.


## 15.3 Rescuing an overloaded team

### Slide 9 · The line to say — Interruptions need an owner.   `[th · aux]`
**SAY THIS:** Interruptions need an owner, or they land on everyone, and nobody finishes anything hard.
*[pause: 0.8]*

### Slide 10 · Three phases — How an embedded engineer helps   `[table · sm aux]`
> Phase | What happens | Typical moves
> Learn the service | Find the largest sources of stress, and the kindling: small, flammable problems | Watch the pages and tickets, and talk to the team
> Share context | Make the situation visible | Write a postmortem for the team, and sort the fires by type
> Drive change | Make the improvements stick | Start with basics, get help clearing the kindling, explain reasoning, ask leading questions
> > The tone: help the team to see, then to act. Do not arrive as a rescuer who takes over.
**COACH:** Here is how to embed an engineer to recover an overloaded team, in three phases. Learn the service: find the largest sources of stress, and the kindling, the small, flammable problems waiting to become fires. Share context: make the situation visible, by writing a postmortem for the team, and sorting the fires by type. And drive change: start with the basics, get help clearing the kindling, explain your reasoning, and ask leading questions. The tone matters. Help the team see, then act. Do not arrive as a rescuer who takes over.

### Slide 11 · The line to say — Overload is a measurable condition with a recovery plan, not a character flaw in the team.   `[th · aux]`
**SAY THIS:** Operational overload is a condition with measurable symptoms and a recovery plan. The first step is to make it visible, and the second is to help the team change it without taking it over.
*[pause: 0.8]*


## 15.4 Working together

### Slide 12 · Collaboration — Practices that work   `[table · sm aux]`
> Practice | What it is
> Production meeting | A regular, structured review of a service, with a default agenda: upcoming changes, metrics, outages, paging events, non-paging events, and previous actions
> Team composition | A technical lead, a manager, and, for larger efforts, a project manager
> Cross-team projects | A case study of a large collaboration, with recommendations
> > Default to enabling change, and to track its properties, not to hold meetings whose purpose is to stop it.
**COACH:** Now communication. The production meeting is a regular, structured review of a service. A good default agenda: upcoming production changes, metrics, outages, paging events, non-paging events, and previous action items. Default to enabling change and tracking its properties, not to hold meetings whose purpose is to stop it. It also discusses team composition, with a technical lead, a manager and, for larger efforts, a project manager, and gives case studies of collaboration across teams.


## 15.5 When should SRE take a service on?

### Slide 13 · The engagement model — From late review to built-in reliability   `[dia · aux]`
*Diagram:* `svg/e15-engagement.svg`
**COACH:** Last, how an SRE team decides to engage with a service. The classic approach is the production readiness review: when a product is ready, a few SREs study it, find the gaps, help to fix them, and then take on production responsibility. It works, but it costs several people for months per service, and it comes late. The first evolution is early engagement: start in design, so that reliability is built in.
**COACH:** The second is frameworks and a shared platform: give every service the same instrumented, tested foundation, so that most of the review is done by construction, and SRE effort scales with the number of services without scaling with the headcount.

### Slide 14 · One level down — The phases of a production readiness review   `[table · sm aux]`
> Phase | What it does
> Engagement | Leadership picks a team, and one to three SREs are assigned
> Analysis | Study architecture, dependencies, failure modes, monitoring, capacity
> Improvements and refactoring | Fix the gaps, jointly with the developers
> Training | Teach the SRE team the service
> Onboarding | Hand over responsibility, gradually
> Continuous improvement | Keep reviewing, and keep the service within its objective
> > The PRR is a prerequisite for taking responsibility, not a formality.
**COACH:** One level down, the phases of a readiness review. Engagement: leadership picks a team, and one to three engineers are assigned. Analysis: study the architecture, dependencies, failure modes, monitoring and capacity. Improvements and refactoring: fix the gaps, jointly with the developers. Training: teach the receiving team the service. Onboarding: hand over responsibility gradually. And continuous improvement. The review is a prerequisite for taking responsibility, not a formality, and a service that fails it can stay with its developers, with the SRE team's help.

### Slide 15 · The line to say — Trade effort per service against upfront investment.   `[th · aux]`
**SAY THIS:** Each step in the engagement model trades effort per service for upfront investment and adoption. Choose per service, by criticality.
*[pause: 0.8]*

### Slide 16 · The alternative and the price — Three engagement models   `[table · sm aux]`
> Model | Cost per service | Reach | Weakness
> Late review | High: weeks to months, several engineers | Low | Finds design flaws when they are expensive to fix
> Early engagement | Medium | Medium | Needs capacity at design time
> Framework and platform | Low, after the upfront investment | High | Teams must adopt the platform
> > Each step trades effort per service against upfront investment and adoption.
**COACH:** The three models trade effort per service against upfront investment. Late review costs weeks to months and several engineers per service, has low reach, and finds design flaws when they are most expensive to fix. Early engagement costs less and reaches further, but needs capacity at design time. A framework and platform has low cost per service after the upfront investment, and high reach, but teams must adopt it. For a manager, the questions are always the same: which services deserve a person, and which should be served by the platform?


## 15.6 Then and now

### Slide 17 · Since 2016 — The same questions, new vocabulary   `[panel · now aux]`
> Platform engineering teams build paved roads: templates and tooling that make the reliable path the easy path. It is the old framework idea, generalised.
> Production readiness is a checklist in code that runs on every service, not a meeting.
> The spectrum of ownership, from "you build it, you run it" to a dedicated reliability team, is chosen per service, by criticality.
> On-call health is a tracked metric. Burnout is treated as a reliability risk.
**ASIDE:** What has changed since 2016? The same questions, in new vocabulary. Platform engineering teams build paved roads, templates and tooling that make the reliable path the easy path. It is the old framework idea, generalised. Production readiness is a checklist in code that runs on every service, instead of a meeting. The spectrum of ownership, from you build it, you run it, to a dedicated reliability team, is chosen per service, by criticality. And on-call health is a tracked metric: burnout is treated as a reliability risk.


## 15.7 Probe drills

### Slide 18 · Interviewer probe — You get one SRE for six weeks to help a team drowning in tickets. How do you use them?   `[probe]`
**INTERVIEWER:** You get one SRE for six weeks to help a team drowning in tickets. How do you use them?
*A strong answer on screen:*
> - First two weeks: learn, measure, find the top sources of load
> - Share a short document that makes the situation visible, with numbers
> - Pick two or three fixes that remove a class of tickets, and finish them
> - Leave tools and habits, not dependence
**CANDIDATE:** In the first two weeks, they learn the service and measure the load: which tickets, how many, how long. They write a short document that makes it visible, with numbers. Then we choose two or three fixes that remove a whole class of tickets, and finish them, rather than starting ten. And at the end we leave tools and habits that the team owns, so they are not dependent on the visitor.

### Slide 19 · Interviewer probe — A product team wants your team to take over on-call for their service next month. What do you ask?   `[probe]`
**INTERVIEWER:** A product team wants your team to take over on-call for their service next month. What do you ask?
*A strong answer on screen:*
> - What are its objectives, and how does it perform against them?
> - How many pages and tickets today? Actionable?
> - Are there runbooks, dashboards, and a rollback?
> - Will the developers stay involved, with shared ownership?
**CANDIDATE:** I ask for the service's objectives and how it has performed against them. How many pages and tickets it generates today, and how many are actionable. Whether there are runbooks, dashboards and a rollback. And whether the developers will stay involved. If the answers are poor, I propose a readiness review with specific improvements, and a date when we reconsider, instead of taking on the pager unprepared.

### Slide 20 · Interviewer probe — How do you know a new engineer is ready for primary on-call?   `[probe]`
**INTERVIEWER:** How do you know a new engineer is ready for primary on-call?
*A strong answer on screen:*
> - They can narrate a request path and the top failure modes
> - They have shadowed real incidents, and handled drills
> - They know how to escalate, and are comfortable doing so
> - They have handled pages as secondary with little help
**CANDIDATE:** I look for evidence, not a date. They can narrate a request path and the top failure modes. They have shadowed real incidents and handled drills. They know how to escalate, and are comfortable doing it. And they have handled pages as a secondary with little help. If any of those are missing, we spend more time at the earlier stage.


## 15.8 Where this shows up

### Slide 21 · Where this shows up — Read, watch and build next   `[list · aux]`
> ~ Design-room course part 16 has the manager layer: team seams, operational readiness, and organisational follow-up.
> - Episode 7: the incident structure these people use
> - Episode 16: lessons from other industries, and the close
> - Google's SRE books: the chapters on training, interrupts, overload, collaboration and engagement
> - Also: the workbook chapters on engagement, team lifecycles and organisational change
**COACH:** Next steps. Part sixteen of the design-room course has the manager layer: team seams, operational readiness and organisational follow-up. Episode seven covered the incident structure these people use, and episode sixteen finishes with lessons from other industries. Google's free S-R-E books cover all five, and the workbook chapters on engagement, team lifecycles and organisational change.

