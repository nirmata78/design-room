# Episode 5 · Release engineering and simplicity

Reader transcript generated from `src/ch05.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 5 of 16 · Priority 2 — Release engineering and simplicity   `[th]`
> Hermetic builds, rollouts that fail small, and the case for boring software.
**COACH:** Episode five. Most outages follow a change. So the safest reliability investment is often not a new redundant system but a better way of shipping. We cover release engineering, and simplicity. Then we add the statistics of a canary.
**SAY THIS:** Every release is an experiment on production. The craft is making the experiment small.
*[pause: 0.8]*


## 5.0 The story that starts it

### Slide 2 · The opening story — The same bug, two rollouts   `[cards · c2]`
> red All at once :: A bad configuration reaches every region in one push. The dashboards turn red everywhere. The rollback takes forty minutes because the old binary must be rebuilt.
> grn In waves :: The same bug reaches one percent of traffic. A health gate trips in six minutes. The push stops by itself. One in a hundred users saw it.
> > The bug is the same. The blast radius is the engineering.
**COACH:** An illustration, with made-up numbers. Two teams ship the same bug. The first pushes to every region at once. Everything goes red together, and the rollback takes forty minutes because the old binary has to be rebuilt. The second ships in waves. The bug reaches one percent of traffic, a health gate trips in six minutes, and the push stops by itself. One user in a hundred saw it. The bug is identical. What differs is the blast radius, and the blast radius is the engineering.

### Slide 3 · What this episode covers — Release engineering, simplicity and canaries   `[panel · note]`
> Release engineering and simplicity, with the statistics of canarying from Google's workbook.
**COACH:** This episode covers release engineering and simplicity, and adds the statistics of canarying.


## 5.1 The principles of release engineering

### Slide 4 · Four principles — What a release system must provide   `[cards · c4]`
> grn Self-service :: Teams release without a gatekeeper, within rules the tooling enforces.
> grn High velocity :: Frequent, small releases, so each is easy to reason about.
> grn Hermetic builds :: Same revision in, same artefact out, on any machine.
> amb Enforced policy :: Who may release what, and what must pass first, is checked by the system.
**COACH:** A release system rests on four principles. Self-service: teams release without a gatekeeper, within rules the tooling enforces. High velocity: frequent, small releases, so that each one is easy to reason about. Hermetic builds: the same revision gives the same artefact on any machine. And enforced policy: who may release what, and what must pass first, is checked by the system and not by good intentions.

### Slide 5 · One level down — What hermetic means, and why it saves you at three in the morning   `[table]`
> Property | Meaning | Why it matters
> Pinned inputs | Compiler and libraries come from known versions, not from whatever the build machine has | Two builds of one revision are identical
> Self-contained | The build does not call external services | A third-party outage cannot stop a release
> Versioned tools | The build tooling is itself tied to the revision | A cherry-pick rebuilds with the old compiler, not today's
> > A rollback you cannot rebuild is a rollback you do not have.
**COACH:** One level down, what hermetic means. Inputs are pinned: the compiler and the libraries come from known versions, not from whatever the build machine has. The build is self-contained: it does not call external services, so somebody else's outage cannot stop your release. And the tools are versioned with the revision. That last point is subtle. When you cherry-pick a fix onto an old release, the build uses the compiler of that release, not today's. The takeaway: a rollback you cannot rebuild is a rollback you do not have.

### Slide 6 · The pipeline — From a commit to a fleet, with the gates between   `[dia]`
*Diagram:* `svg/e05-pipeline.svg`
**COACH:** Here is the shape of the pipeline. A commit builds, and tests run. The artefact is packaged with its version and checksum, and stored. Then the rollout begins. First a canary, a small slice of production. If its health gate passes after a bake period, the next wave begins, then the next, until the whole fleet runs the new version. At every stage there is a path back to the last known good version, and the rollback is a normal pipeline operation, not an emergency one. Tools differ, but the stages are the part to remember.

### Slide 7 · The line to say — A rollback you cannot rebuild is a rollback you do not have.   `[th]`
**SAY THIS:** A rollback you cannot rebuild is a rollback you do not have. That is why builds are hermetic, and tools are versioned with the code.
*[pause: 0.8]*

### Slide 8 · Configuration — Several ways to ship configuration, and the one rule   `[panel · key]`
> There are several models: files on the mainline branch, files packaged with the binary, separate configuration packages, and configuration read from an external store. All of them live in version control with strict review.
> Whichever you choose, treat configuration as code: versioned, reviewed, tested and rolled out in waves.
> Many large outages are a configuration change that skipped the pipeline.
**COACH:** Configuration needs the same care, and the point is blunt. There are several models: configuration files on the mainline branch, packaged with the binary, in separate configuration packages, or read from an external store. All of them live in version control with strict review. Whichever you choose, treat it as code: versioned, reviewed, tested and rolled out in waves. A large share of big outages are a configuration change that skipped the pipeline.

### Slide 9 · The line to say — A release is safe when it is small, reproducible, staged, and reversible.   `[th]`
**SAY THIS:** A safe release is small, reproducible, staged and reversible. If any one of those is missing, you are relying on luck.
*[pause: 0.8]*


## 5.2 A rollout is a statistics problem

### Slide 10 · Canarying · Why size and time matter — The same regression, three canary sizes   `[table]`
> Canary share | Requests in 10 minutes | Expected errors, old vs new | Evidence
> 1 percent | 6,000 | 6 against 12 | 1.4 standard deviations: easily noise
> 5 percent | 30,000 | 30 against 60 | 3.2: a real signal
> 25 percent | 150,000 | 150 against 300 | 7.1: unmistakable
> > Assumes 1,000 requests a second, a baseline error rate of 0.1 percent, and a regression to 0.2 percent. These are illustrative numbers.
**COACH:** Here is the statistics. A rollout is a statistics problem. Suppose a service takes a thousand requests a second, with a baseline error rate of point one percent, and a bad release doubles it. A one percent canary sees six thousand requests in ten minutes: six errors against twelve. That is about one and a half standard deviations, which is easily noise. A five percent canary sees thirty against sixty, over three standard deviations, a real signal. At twenty-five percent it is unmistakable. The numbers are illustrative, but the lesson is general.

### Slide 11 · Canarying · The levers — Three levers, and what each one trades   `[table]`
> Lever | Turn it up | Cost
> Canary size | Detects smaller regressions | More users exposed to a bad build
> Bake time | Catches slow leaks and rare paths | Slower releases
> Number of signals | Catches more kinds of failure | More false positives, more tuning
> > Pick the smallest regression you must catch, then size the canary and the bake to see it.
**COACH:** There are three levers. Canary size: bigger detects smaller regressions, but exposes more users to a bad build. Bake time: longer catches slow leaks and rare code paths, but slows every release. And the number of signals: more of them catch more kinds of failure, but bring more false positives and more tuning. So start from the smallest regression you must catch, then size the canary and the bake time to see it.

### Slide 12 · the line to say — Size the canary to the smallest regression you must catch.   `[th]`
**SAY THIS:** Decide the smallest regression you must catch. Then size the canary, and the bake time, so that you would actually see it.
*[pause: 0.8]*

### Slide 13 · The trap — A canary that cannot fail   `[panel · trap]`
> Compare the canary to a control from the same time, not to last week. Traffic changes by the hour.
> Compare like with like: same region, same request mix.
> If the canary gets no traffic of the type that breaks, it passes and proves nothing.
> Decide what automatic abort looks like before the rollout starts.
**ASIDE:** The classic trap is a canary that cannot fail. Compare the canary with a control from the same time, not with last week, because traffic changes by the hour. Compare like with like, the same region and the same mix of requests. If the canary never receives the kind of request that breaks, it passes and proves nothing. And decide before the rollout begins what automatic abort looks like, so that nobody has to argue about it during one.


## 5.3 Simplicity

### Slide 14 · The argument — Why boring is a feature   `[cards · c2]`
> grn Boring code :: Predictable, readable, easy to reason about at three in the morning.
> red Bloat :: Every added feature is more code to test, more paths to fail, and more to understand during an incident.
> > The proposal: measure the negative lines of code you deleted, and be proud of it.
**COACH:** Simplicity is an argument that sounds like a joke and is not. Boring is a feature. Predictable, readable code is easy to reason about at three in the morning. And every feature added is more code to test, more paths to fail, and more to understand in an incident. The proposal is to be proud of the negative lines of code you contributed, and to delete dead code routinely, instead of leaving it commented out.

### Slide 15 · The line to say — Boring is a feature.   `[th]`
**SAY THIS:** Boring is a feature. Every line you delete is a line that cannot fail at three in the morning.
*[pause: 0.8]*

### Slide 16 · What simplicity looks like in practice — Four habits   `[table]`
> Habit | What it prevents
> Minimal APIs | Fewer things to misuse, fewer things to keep compatible
> Modularity | A change in one place does not need a change in five
> Small, frequent releases | Large changes hide bugs; small changes make them obvious
> Delete dead code | Bit rot, and untested paths that wake up in production
> > An API with fewer functions is easier to test, to understand, and to keep stable.
**COACH:** Four habits. Minimal interfaces: fewer things to misuse and keep compatible. Modularity: a change in one place does not demand a change in five. Small, frequent releases, because large changes hide bugs and small changes make them obvious. And deleting dead code, which prevents bit rot and untested paths that wake up in production. An interface with fewer functions is easier to test, easier to understand, and easier to keep stable.


## 5.4 Then and now

### Slide 17 · Since 2016 — Progressive delivery became a discipline   `[panel · now]`
> Rollouts now go by cells or rings: a small internal ring, then a region or a slice of users, then wider, each with automated health checks and automatic rollback.
> Feature flags separate deploying code from turning it on. That makes rollback instant, and also adds the risk of flag debt and untested combinations.
> Declarative delivery from version control, often called GitOps, makes the deployed state auditable.
**ASIDE:** What has changed since 2016? Progressive delivery became a discipline. Rollouts go by cells or rings: a small internal ring first, then a region or a slice of users, then wider, each with automated health checks and automatic rollback. Feature flags separate deploying code from turning it on, which makes rollback instant, but adds risks of its own: flag debt, and combinations nobody tested. And delivery from version control, often called GitOps, makes the deployed state auditable.

### Slide 18 · Since 2016 · the line to say — You can only vouch for a build you can reproduce.   `[th]`
**SAY THIS:** You can only vouch for a build you can reproduce. Hermetic builds are the foundation of provenance.
*[pause: 0.8]*

### Slide 19 · Since 2016 — The supply chain is now part of release engineering   `[panel · now]`
> Teams record a software bill of materials and sign build provenance, so an artefact can be traced to its source and its build.
> Dependency updates are automated and gated, not ad hoc.
> Hermetic builds became the basis for this: you can only attest to a build you can reproduce.
> Verify the names of current standards against their documentation before quoting them.
**ASIDE:** A second change. The software supply chain became part of release engineering. Teams record a bill of materials and sign provenance, so an artefact can be traced back to its source and its build. Dependency updates are automated and gated. And hermetic builds turned out to be the foundation for this, because you can only vouch for a build you can reproduce. As ever, check the current names of standards against their documentation before quoting them.

### Slide 20 · Episode 5 · the line to say — Make the blast radius small, and the rollback boring.   `[th]`
**SAY THIS:** A rollout is a statistics problem. Size the canary to the smallest regression you must catch, bake long enough to see it, and decide the abort rule before you start.
*[pause: 0.8]*


## 5.5 Probe drills

### Slide 21 · Interviewer probe — A bad push blocks a continent. Stop it.   `[probe]`
**INTERVIEWER:** A bad push blocks a continent. Stop it.
*A strong answer on screen:*
> - Stop the rollout first: halt the waves, freeze the pipeline
> - Roll back to the last known good, using the normal path
> - Then confirm recovery with the same signals that alerted
> - Later: why the canary did not catch it
**CANDIDATE:** First I stop the bleeding by halting the rollout, so the problem cannot spread further. Then I roll back to the last known good version using the normal pipeline path, not a special one, and I confirm recovery with the same signals that raised the alert. Afterwards, in the review, the key question is why the canary and the health gates did not catch it, and what that tells us about the signals we used.

### Slide 22 · Interviewer probe — How would you roll back after two days of writes in the new version?   `[probe]`
**INTERVIEWER:** How would you roll back after two days of writes in the new version?
*A strong answer on screen:*
> - Depends on whether the data format changed
> - If it did not: ordinary rollback
> - If it did: only works if the old code can read the new data
> - Otherwise: forward fix, or a reverse migration prepared in advance
**CANDIDATE:** It depends whether the data format changed. If not, an ordinary rollback works. If it did, the old code has to be able to read what the new code wrote, which is why a schema or protocol change is released in two steps: first release code that can read the new format, then, later, release code that writes it. Without that, the only options are a forward fix, or a reverse migration that you prepared and rehearsed in advance.

### Slide 23 · Interviewer probe — A team says canarying slows them down. Respond.   `[probe]`
**INTERVIEWER:** A team says canarying slows them down. Respond.
*A strong answer on screen:*
> - Show the cost of the incidents the canary would have caught
> - Make the canary automatic so it takes no human time
> - Offer a fast path for low-risk changes with a smaller bake
**CANDIDATE:** I would show them the cost of the incidents a canary would have caught, in hours and in error budget. Then I would make the canary automatic, so it costs no human time. And I would offer a fast path for genuinely low-risk changes, with a smaller bake time, rather than an exemption. The goal is to make the safe path the easy path.


## 5.6 Where this shows up

### Slide 24 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 16 teaches rollout, bake time and health gates, online migration, and the two-release rule.
> - Episode 8: testing, the layer before a canary
> - Episode 14: launches at scale, a rollout with a business around it
> - Google's SRE books: the chapters on release engineering and simplicity, then the workbook chapters on configuration and canarying
> - Also: Software Engineering at Google, on small changes and review
**COACH:** Next steps. Part sixteen of the design-room course teaches rollout, bake time and health gates, online migration and the two-release rule. Episode eight covers testing, the layer before a canary, and episode fourteen covers launches, which are rollouts with a business wrapped around them. Google's free S-R-E books go deeper on all of it.

