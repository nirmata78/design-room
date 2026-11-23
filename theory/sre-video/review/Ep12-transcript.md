# Episode 12 · Distributed cron and data pipelines

Reader transcript generated from `src/ch12.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 12 of 16 · Priority 1 — Distributed cron and data pipelines   `[th]`
> How to run work on a schedule when machines fail, and how pipelines stay correct when workers do too.
**COACH:** Episode twelve. Two topics about work that runs by itself. The humble cron job, and what it takes to run one reliably across a datacenter. And data processing pipelines, and how a design that works at small scale breaks at large scale. Both come down to one question: when something fails halfway through, is it safe to run again?
**SAY THIS:** The hardest question in scheduling is not when to start. It is what to do when you do not know whether you already did.
*[pause: 0.8]*


## 12.0 Why this decides interviews

### Slide 2 · The opening story — Midnight on the first of the month   `[cards · c2]`
> red Skipped :: A payroll job did not start. Someone notices on the third. It is annoying, and it is fixable: run it.
> red Doubled :: A newsletter job started twice after a failover. A million people received two emails. It is not fixable.
> > Which is worse depends on the job. The scheduler must be told, and must choose a side.
**COACH:** Two failures at midnight on the first of the month. A payroll job did not start. Someone notices on the third, it is annoying, and it is fixable: run it. A newsletter job started twice after a failover, and a million people got two emails. That one is not fixable. Which failure is worse depends on the job, and the scheduler must be told, and must choose a side.

### Slide 3 · What this episode covers — Distributed cron, and data pipelines   `[panel · note]`
> Distributed periodic scheduling with cron, and data processing pipelines. The cron half is must-read for the design-room scheduling part.
**COACH:** This episode covers distributed periodic scheduling with cron, and data processing pipelines. The cron half is must read for the scheduling part of the design-room course.


## 12.1 Cron, run at scale

### Slide 4 · Idempotency — Whether you can launch twice, and whether you can skip   `[table]`
> Job | Safe to launch twice? | Safe to skip one?
> Garbage collection every five minutes | Yes | Yes: the next run catches up
> Monthly payroll | Maybe not | No
> Newsletter to a million people | No | Sometimes
> > The default: prefer skipping to double-launching, because a skip is easier to recover from.
**COACH:** First, a table. Garbage collection every five minutes is safe to launch twice, and safe to skip, because the next run catches up. Monthly payroll may not be safe to repeat, and must not be skipped. A newsletter must not be sent twice, and skipping it is sometimes acceptable. The default, as far as the infrastructure allows, is to prefer skipping to double launching, because recovering from a skip is more tenable than recovering from a double. And owners should monitor the effect of their jobs, so that a skip is noticed.

### Slide 5 · The mechanism — The two synchronisation points of a launch   `[dia]`
*Diagram:* `svg/e12-cron-launch.svg`
**COACH:** How does a distributed cron service decide? Follow the picture. The service has one leader and several followers, and they keep their state in a consensus-backed log, as in the last episode. For every launch there are two synchronisation points. Before the launch, the leader records in the log that it is about to launch. Then it sends the launch request to the datacenter scheduler. After the launch, it records that the launch finished. Now imagine the leader dies between the two records.
**COACH:** The new leader reads the log and finds a launch that started and never finished. It does not know whether the request was sent.

### Slide 6 · One level down — What the new leader does with an unfinished launch   `[table]`
> Condition | Action
> External operations are idempotent | Repeat them. Safe
> The state of the external system can be looked up | Check whether the job was launched, then act
> Neither | Choose per job: skip or launch again
> > Look up the state if you can; make operations idempotent if you can; otherwise decide in advance, per job.
**COACH:** One level down. There are conditions. If every external operation is idempotent, the new leader repeats them, and that is safe. If the state of the external system can be looked up, the new leader checks whether the job was launched, and acts accordingly. If neither is true, the new leader must choose, per job, to skip or to launch again, and that choice is made in advance, by the job's owner. This is the general shape of every exactly-once-looking system: it is at-least-once delivery, with idempotency or a lookup to make the repeat harmless.

### Slide 7 · The line to say — Prefer skipping to double launching.   `[th]`
**SAY THIS:** Unless the owner says otherwise, prefer skipping a launch to launching twice, because a skip can be repaired and a double often cannot.
*[pause: 0.8]*

### Slide 8 · Scaling — What changes at a large scale   `[panel · key]`
> Thundering herd: thousands of jobs set for midnight hit the scheduler and its dependencies together. Let owners use jittered or hashed times.
> State is small, but must be consistent: the log holds launch records, and followers hold snapshots to recover quickly.
> Failure of the scheduler is not failure of the jobs: running jobs go on while the leader changes.
**COACH:** Now what changes at scale. Thundering herds: thousands of jobs set for midnight hit the scheduler and its dependencies together, so let owners use jittered or hashed times instead of round ones. The state is small, but it must be consistent: the log holds launch records, and followers keep snapshots so that recovery is quick. And a failure of the scheduler is not a failure of the jobs. Jobs that are running keep running while the leader changes.

### Slide 9 · The line to say — At-least-once plus idempotency looks like exactly-once. Without idempotency, choose skip or double in advance.   `[th]`
**SAY THIS:** A scheduler cannot know whether it launched. So it records its intent before the side effect and its completion after, and the job's owner decides in advance whether an unknown launch is skipped or repeated.
*[pause: 0.8]*


## 12.2 Pipelines

### Slide 10 · The load shape — Three periodic pipelines that overlap   `[dia]`
*Diagram:* `svg/e12-moire.svg`
**COACH:** Start with the simplest pipeline: a program that runs periodically, say every hour or every night, reads input, and writes output. It works at small scale. It breaks at large scale, and the failures have names. Uneven work distribution: one slow shard holds up the whole run. Monitoring problems: a pipeline that is silent looks the same as one that is idle. The thundering herd: everything starts at the top of the hour.
**COACH:** And the moiré load pattern, which is in the picture. Three pipelines, each periodic, each fine on its own. Occasionally their peaks line up, and the shared resource sees the sum. The peaks cause on-call pain, and no individual pipeline owner can see them.

### Slide 11 · The line to say — Alert on freshness, not on exit codes.   `[th]`
**SAY THIS:** A periodic pipeline hides its failures. Alert on freshness and backlog, not on whether the last run exited cleanly.
*[pause: 0.8]*

### Slide 12 · One level down — Why periodic pipelines suffer at scale   `[table]`
> Problem | Cause | A direction
> Uneven distribution | A few large shards run long, while most workers sit idle | Smaller work units, dynamic assignment
> Thundering herd | Everything scheduled at the same moments | Continuous processing, or staggered starts
> Moiré load | Independent schedules sometimes align | Shared capacity planning; jitter
> Weak monitoring | Only a finished or failed run is visible | Report progress, freshness and backlog
> > The remedy is a continuous pipeline that processes work as it arrives.
**COACH:** One level down. Uneven distribution comes from a few large shards that run long while the other workers sit idle, so use smaller work units and assign them dynamically. The thundering herd comes from everything being scheduled at the same moments, so use continuous processing, or stagger the starts. Moiré load comes from independent schedules that sometimes align, so plan the shared capacity together, and add jitter. Weak monitoring comes from seeing only a finished or failed run, so report progress, freshness and backlog. The remedy is a continuous pipeline that processes work as it arrives.

### Slide 13 · The mechanism — Leases and uniquely named output   `[dia]`
*Diagram:* `svg/e12-workflow.svg`
**COACH:** Now how a continuous pipeline stays correct. A coordinator, called the task master at Google, holds the state of every unit of work, as pointers to uniquely named data. Workers are stateless. A worker acquires a unit of work with a lease, and may only commit it while it holds a valid lease. Now imagine a worker that stalls, loses its lease, and wakes later. It is an orphan.
**COACH:** To keep it from doing damage, every output file a worker opens has a unique name. The orphan can keep writing, but it writes to its own file, and when it tries to commit, it cannot, because another worker holds the lease. This is the double correctness guarantee: unique outputs, and state controlled by leases.

### Slide 14 · The line to say — An orphan can write. It cannot commit.   `[th]`
**SAY THIS:** Give every output a unique name, and every commit a lease. An orphaned worker can write, but it cannot commit.
*[pause: 0.8]*

### Slide 15 · The alternative and the price — Batch, continuous, and durable workflow   `[table]`
> Style | Strength | Weakness
> Periodic batch | Simple, cheap to reason about | Herds, stragglers, stale results, silent failures
> Continuous pipeline | Fresh results, even load | A coordinator to run, and idempotency to design
> Durable workflow engine | Resumes after a crash by replaying an event history | Your code must be deterministic
> > The middle row is the classic form. The last row is the modern form of the same idea.
**COACH:** The alternatives. Periodic batch is simple and cheap to reason about, with herds, stragglers, stale results and silent failures. A continuous pipeline gives fresh results and an even load, and needs a coordinator, and idempotency by design. A durable workflow engine resumes after a crash by replaying an event history, at the cost that your code must be deterministic. The middle row is the classic form, and the last row is the modern form of the same idea.

### Slide 16 · The trap — A pipeline that stopped, and nobody noticed   `[panel · trap]`
> Alert on freshness: the age of the newest output, against what the consumer needs.
> Alert on backlog growth, not only on errors.
> A pipeline with a clean exit and no output is a failure. Treat empty results as suspicious.
**ASIDE:** The trap is a pipeline that stopped, and nobody noticed. Alert on freshness: the age of the newest output, against what the consumer needs. Alert on backlog growth, not only on errors. And treat a clean exit with no output as a failure. Empty results are suspicious, because it is the quietest way to fail.


## 12.3 Then and now

### Slide 17 · Since 2016 — The same ideas, in current tools   `[panel · now]`
> Scheduled jobs on a container platform have settings for what to do on overlap and on a missed start. They encode the skip or double choice. Read the defaults.
> Workflow orchestrators model pipelines as dependency graphs, with retries, backfills and alerts on lateness.
> Durable execution engines keep workflow state as an event history, so code resumes after a crash.
> Streaming engines give continuous processing with event time and checkpoints. The design-room course covers them in the logs and streams part.
**ASIDE:** What has changed? Scheduled jobs on container platforms have settings for what to do when runs overlap, and when a start is missed. They encode the skip or double choice, so read the defaults. Workflow orchestrators model pipelines as graphs of dependencies, with retries, backfills and alerts on lateness. Durable execution engines keep workflow state as an event history, so that code resumes after a crash. And streaming engines give continuous processing with event time and checkpoints, which the design-room course covers in its logs and streams part.

### Slide 18 · Then and now · the line to say — Data quality is an indicator.   `[th]`
**SAY THIS:** Treat data quality as a service level indicator: freshness, completeness and correctness, each with a target.
*[pause: 0.8]*

### Slide 19 · Then and now — The data-quality angle   `[table]`
> Dimension | What to measure | Why
> Freshness | Age of newest output versus the need | Stale data is wrong data, quietly
> Completeness | Share of expected input that arrived | A partial run looks like a run
> Correctness | Checks against invariants or a second source | Wrong output is worse than no output
> Lineage | Where each output came from | Debugging, and deletion obligations
> > These become SLIs for pipelines, as episode two described.
**COACH:** One addition. Pipelines now have data quality objectives. Freshness: the age of the newest output against the need. Completeness: the share of expected input that arrived, because a partial run looks like a run. Correctness: checks against invariants or a second source, because wrong output is worse than none. And lineage: where each output came from, for debugging and for deletion obligations. These become the service level indicators of a pipeline, as episode two described.


## 12.4 Probe drills

### Slide 20 · Interviewer probe — The scheduler dies after starting a job and before recording it. What happens?   `[probe]`
**INTERVIEWER:** The scheduler dies after starting a job and before recording it. What happens?
*A strong answer on screen:*
> - The new leader sees no record of the launch, so it launches again: possible double
> - Fix: record intent before the side effect, and completion after
> - On recovery, look up the job's state, or rely on idempotency
> - Otherwise the job's owner chose skip or repeat in advance
**CANDIDATE:** Without a record, the new leader cannot know, so it may launch again, which gives a double launch. The fix is to write the intent to the replicated log before the side effect, and the completion after. On recovery, an unfinished launch is resolved by looking up the job's state, or by relying on idempotency. And if neither is possible, the job's owner has already chosen whether to skip or repeat.

### Slide 21 · Interviewer probe — A million jobs are scheduled for midnight. What breaks, and what do you do?   `[probe]`
**INTERVIEWER:** A million jobs are scheduled for midnight. What breaks, and what do you do?
*A strong answer on screen:*
> - The scheduler, the cluster, and shared dependencies see a spike
> - Spread the load: jitter or hashed start times, and a start window
> - Rate-limit launches, with a queue and priorities
> - Make the jobs tolerate delay, and monitor lateness
**CANDIDATE:** What breaks is everything that sees the spike: the scheduler, the cluster scheduler, and the shared services the jobs call. I spread the load with jitter or hashed start times inside a window, rate-limit launches with a queue and priorities, and make the jobs tolerate a delay. And I monitor lateness, not just failure, so I can see the herd forming.

### Slide 22 · Interviewer probe — How do you make a pipeline step safe to run twice?   `[probe]`
**INTERVIEWER:** How do you make a pipeline step safe to run twice?
*A strong answer on screen:*
> - Give each unit of work a unique, deterministic ID
> - Write output to a unique name, then commit atomically
> - Use conditional writes or a deduplication table keyed by that ID
> - Commit state only while holding a valid lease
**CANDIDATE:** I give each unit of work a unique and deterministic identifier. Output goes to a uniquely named location, and is committed atomically, so a repeat cannot corrupt a previous result. Writes to shared state are conditional, or checked against a deduplication table keyed by that identifier. And a worker can only commit while it holds a valid lease, so an orphan cannot commit.


## 12.5 Where this shows up

### Slide 23 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 15 covers timers, task leasing and durable workflows, and part 10 covers logs and streams.
> - Episode 11: the replicated log underneath the cron leader
> - Episode 13: data integrity: how you know the output is right
> - Google's SRE books: the chapters on distributed cron and data pipelines
> - Also: the workbook chapter on data processing pipelines
**COACH:** Next steps. Part fifteen of the design-room course covers timers, task leasing and durable workflows, and part ten covers logs and streams. Episode eleven covered the replicated log under the cron leader, and episode thirteen is data integrity: how you know the output is right. Google's free S-R-E books cover both, and the workbook has a chapter on data processing pipelines.

