# Episode 10 · Overload and cascading failure

Reader transcript generated from `src/ch10.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 10 of 16 · Priority 1 — Overload and cascading failure   `[th]`
> Why a service that loses a little capacity can lose all of it, and the controls that stop the spiral.
**COACH:** Episode ten. This is the most important operational episode in the course, and perhaps the most asked-about in design interviews. Handling overload is one half. The failure that happens when overload spreads is the other. Together they explain why systems collapse, and what to design so that yours bends instead of breaking.
**SAY THIS:** A system under overload must do less work, not more. Everything else is a detail.
*[pause: 0.8]*


## 10.0 Why this decides interviews

### Slide 2 · The opening story — Goodput collapses when load passes capacity   `[dia]`
*Diagram:* `svg/e10-goodput.svg`
**COACH:** Start with the picture the whole episode explains. The horizontal axis is the load offered to a service. The vertical axis is the useful work it completes, which engineers call goodput. Up to its capacity, the line rises with the load. Past it, a well-designed service holds steady, shedding the excess. A badly designed one does something worse: its useful work goes down as the load goes up.
**COACH:** It spends its effort on requests that will time out anyway, retries pile on, queues grow, memory is used up, and the service becomes a machine for burning processor time. That collapse is what spreads from one place to another and brings down a whole system.

### Slide 3 · What this episode covers — Handling overload, and cascading failures   `[panel · note]`
> Handling overload, and addressing cascading failures. Both are must-read for the design-room course part on rate limiting and overload, and the one on reliability patterns.
**COACH:** This episode covers handling overload, and cascading failures. In the design-room course, both are must read for the parts on rate limiting and overload, and on reliability patterns.


## 10.1 How overload turns into a cascade

### Slide 4 · The standard story — Two clusters, one fails   `[cards · c3]`
> grn Before :: Cluster A handles one thousand requests a second. Cluster B takes its share too.
> red B fails :: All the traffic goes to A. It now gets about twelve hundred requests a second, more than it can handle.
> red The spiral :: A's servers run out of resources and crash or time out. Useful work falls below a thousand. The next cluster is next.
> > A small capacity shortfall became a total loss of useful work.
**COACH:** The standard story. Cluster A handles a thousand requests a second. Cluster B shares the load. Cluster B fails, and all its traffic moves to A, which now gets about twelve hundred requests a second, more than it can handle. A's servers run out of resources, and start crashing or missing deadlines, so the rate of successful requests drops below a thousand. The work they cannot do spills to the next cluster. A small shortfall became a total loss.

### Slide 5 · One level down — How each exhausted resource turns slow into dead   `[table]`
> Resource | What happens when it runs out | Secondary effect
> CPU | Everything gets slower | More in-flight requests, more memory, more queueing
> Memory | Tasks are killed or garbage collection thrashes | Fewer tasks, so more load on the rest
> Threads | Requests wait for a thread | Health checks time out, so healthy tasks are removed
> File descriptors, connections | New connections refused | Clients retry, adding load
> > The pattern: every exhaustion makes the surviving servers' job harder. That is the positive feedback loop.
**COACH:** One level down, how each resource turns slow into dead. When the processor runs out, everything gets slower, so more requests are in flight, which uses more memory and more queueing. When memory runs out, tasks are killed, or garbage collection thrashes, so there are fewer tasks and more load on the rest. When threads run out, health checks time out, and healthy tasks are removed from the pool. When connections run out, new ones are refused, and clients retry, adding load.
**COACH:** Every exhaustion makes the surviving servers' job harder. That is a positive feedback loop, and that is what a cascade is.

### Slide 6 · The line to say — A cascade is a feedback loop in which failure makes the survivors' job harder.   `[th]`
**SAY THIS:** A cascading failure is a positive feedback loop. Each lost server makes the remaining servers' job harder, so they fail faster. You break it by reducing the work, not by adding machines to the loop.
*[pause: 0.8]*


## 10.2 Retries, the amplifier

### Slide 7 · The amplifier — Three layers, each trying three times: twenty-seven at the bottom   `[dia]`
*Diagram:* `svg/e10-retry-amp.svg`
**COACH:** The commonest amplifier is the retry. Imagine a chain: a client, a front end, a service and a database. Each of the first three retries a failed call up to three times. When the database is struggling, one user action reaches it as three attempts from the service, each caused by three attempts from the front end, each caused by three attempts from the client. Three times three times three is twenty-seven.
**COACH:** At the moment the database needs relief, it receives up to twenty-seven times the work. Every one of those retries is reasonable on its own, and together they are an attack.

### Slide 8 · The controls — Two budgets that cap the amplification   `[table]`
> Control | Rule | Effect in the worst case
> Per-request retry budget | At most three attempts per request | Stops one request from retrying forever
> Per-client retry budget | Retry only while retries are under ten percent of requests | Amplification falls from nearly 3x to about 1.1x
> Retry counter in metadata | The request carries how many times it was tried | Lower layers can refuse to retry what upper layers already retried
> > Do not retry an "overloaded" response against the same overloaded datacenter.
**COACH:** Now the controls. A per-request budget of at most three attempts. A per-client budget: a client retries only while retries are under ten percent of its requests. In the worst case, where a datacenter rejects most requests, the first rule alone allows nearly three times the load, and adding the ten percent budget brings it down to about one point one times.
**COACH:** A third control is a counter in the request metadata, so that lower layers can see that upper layers already retried, and refuse to retry again. The principle: do not retry an overloaded response against the same overloaded place.

### Slide 9 · The trap — Retrying without backoff, jitter, or a budget   `[panel · trap]`
> Backoff with random jitter spreads retries over time. Without jitter, every client retries at the same moment, and the retries arrive as a wave.
> A retry is safe only for idempotent operations. Say so in the design.
> Retry at one layer, not all of them. Say which.
**ASIDE:** And the classic trap. Retrying without backoff, jitter or a budget. Backoff with random jitter spreads the retries over time. Without jitter every client retries at the same instant, and the retries arrive as a wave. A retry is only safe for operations that can be repeated without harm, so say so in your design. And retry at one layer, not all of them, and be ready to say which.


## 10.3 Controls at the server

### Slide 10 · The line to say — A rejection should cost almost nothing.   `[th]`
**SAY THIS:** A rejected request should cost the backend almost nothing, or shedding load saves you nothing.
*[pause: 0.8]*

### Slide 11 · One level down — Why queries per second is the wrong unit   `[table]`
> Pitfall | Why | Better measure
> One request is not one unit of work | A search costs far more than a lookup, and costs change with data and release | Processor time, or other resource consumed
> A fixed limit per client | Fine until capacity moves | Limit as a share of capacity
> Per-customer limits are static | Capacity varies with load and failures | Fair shares, with the ability to borrow
> > The choice: provision by CPU consumption, since memory pressure shows up as CPU in most platforms.
**COACH:** One level down. Be warned that queries per second is the wrong unit. One request is not one unit of work: a search costs far more than a lookup, and costs change with the data and with each release. A fixed limit per client works until capacity moves. So measure work in resources, usually processor time, because in most platforms memory pressure shows up as processor time anyway. And give each customer a share of capacity, with the ability to borrow when others are idle.

### Slide 12 · Criticality — Not every request deserves to survive   `[table]`
> Class | Meaning | Under overload
> CRITICAL_PLUS | Serious user-visible impact if it fails | Served last to be dropped
> CRITICAL | The default for production requests | Dropped only after the lower classes
> SHEDDABLE_PLUS | Partial unavailability is expected. Batch default | Dropped early
> SHEDDABLE | Can be dropped at any time | Dropped first
> > The criticality travels with the request through every layer, so a backend can shed the cheapest to lose.
**COACH:** Criticality. Label each request with a class, and the class travels with the request through every layer. Critical plus is for requests whose failure has serious user-visible impact. Critical is the default for production requests. Sheddable plus is traffic where partial unavailability is expected, which is the default for batch work. And sheddable can be dropped at any time. Under overload a backend drops the lowest classes first. This is a better rule than dropping at random, because it spends the shortfall on the work that matters least.

### Slide 13 · The line to say — Drop the cheapest to lose first.   `[th]`
**SAY THIS:** Not every request deserves to survive. Label them, and drop the cheapest to lose first.
*[pause: 0.8]*

### Slide 14 · Client-side throttling — Reject locally before the backend has to   `[dia]`
*Diagram:* `svg/e10-throttle.svg`
**COACH:** There is also adaptive throttling at the client, with an elegant formula. Each client keeps two counts over a recent window: how many requests it attempted, and how many the backend accepted. While accepts are close to requests, nothing happens. When the backend starts rejecting, the client begins to reject some requests itself, before they leave the machine, with a probability that grows as the gap widens. The multiplier, called K, sets the aggressiveness.
**COACH:** Two is a common example, and a lower value, such as one point one, throttles more aggressively. The point is that a rejected request costs the client almost nothing, and the backend nothing at all.

### Slide 15 · The formula — The probability that a client rejects a request locally   `[code]`
> # requests = attempts in the recent window
> # accepts  = how many the backend accepted
> #
> # reject_probability = max(0, (requests - K * accepts) / (requests + 1))
> #
> # With K = 2: no rejection until the backend accepts less than half.
> # Lower K throttles earlier. Higher K tolerates more rejection.
**COACH:** Here it is as a line of code. The probability of rejecting a request locally is the larger of zero and the following: requests minus K times accepts, divided by requests plus one. With K equal to two, nothing is rejected locally until the backend accepts less than half of the requests. Lower K throttles earlier, and a higher K tolerates more rejection. It is cheap, it needs no coordination, and it keeps working when the backend is the thing that is failing.

### Slide 16 · The line to say — Work nobody waits for is pure waste.   `[th]`
**SAY THIS:** A request that nobody is waiting for is the purest form of wasted work. Pass the deadline down, and stop when it is gone.
*[pause: 0.8]*

### Slide 17 · Deadlines — A deadline is a budget handed down the call tree   `[dia]`
*Diagram:* `svg/e10-deadline.svg`
**COACH:** One more control: deadlines. Propagate deadlines. A deadline is set high in the stack, and every call below inherits the same absolute deadline. Take an example. Server A sets thirty seconds and spends seven before calling B. The call to B gets twenty-three seconds. B spends four, so the call to C gets nineteen. And if a server finds there is no time left, it stops, instead of doing work that nobody will wait for.
**COACH:** A request that nobody is waiting for is the purest form of wasted work, so check for time left before each stage.

### Slide 18 · The line to say — When overloaded, fail early and cheaply, and drop the least important work first.   `[th]`
**SAY THIS:** Under overload, fail early and cheaply. Reject at the edge, drop the least critical work first, never retry into an overloaded place, and never spend effort on a request whose deadline has passed.
*[pause: 0.8]*


## 10.4 If it is already happening

### Slide 19 · Immediate steps — A checklist for an active cascade   `[list]`
> ~ Stop the loop first. Understand later.
> - Increase resources, if there is headroom, but expect a delay
> - Stop health-check failures from killing tasks that are only slow
> - Drop traffic, and enter degraded modes: cheaper results
> - Eliminate batch load, and bad traffic
> - Restart servers only if it helps: a cold cache can make things worse
**COACH:** What do you do while it is happening? Here is a list. Increase resources if there is headroom, but expect a delay. Stop health checks from killing tasks that are only slow, since removing them makes the rest slower. Drop traffic and enter degraded modes, serving cheaper results. Eliminate batch load and any bad traffic. And restart servers only if it helps, because a restart brings a cold cache, which can make things worse. The pattern is the same everywhere: stop the loop first, and understand it later.

### Slide 20 · Preventing it — What a design needs before it is tested   `[panel · key]`
> Load test to failure and beyond, and watch what happens past the limit, not just where it ends.
> Slow start and warm caches: a new task should not take full load immediately.
> Always go downward in the stack: lower layers must not call back up, or loops form.
> Test the noncritical backend: what happens when something optional is down?
**COACH:** Prevention. Load test to failure and beyond, and watch what happens past the limit, not only where it ends. Give new tasks a slow start and warm caches, so a restarted task is not asked for full load immediately. Always go downward in the stack: lower layers must not call back up, or loops form. And test the noncritical backend, because a service that cannot survive the loss of something optional is an accident waiting for a trigger.


## 10.5 Then and now

### Slide 21 · Then and now — Metastable failure: the loop that outlives the trigger   `[dia]`
*Diagram:* `svg/e10-metastable.svg`
**COACH:** Since 2016, there has been a name for the worst version of this. A metastable failure is one where the original trigger is long gone, but the system stays down, because a sustaining loop keeps it there. Look at the cycle. A short spike overloads the service. Requests slow, so clients time out and retry. The retries add load. The caches go cold when tasks restart. The load stays above capacity, though the spike ended long ago.
**COACH:** The system is held in the bad state by its own reaction. There are two ways to break the loop: shed load, or stop the retries. Adding capacity alone often fails, because the retry backlog fills it at once.

### Slide 22 · Since 2016 — The controls became platform features   `[panel · now]`
> Adaptive concurrency limits learn a service's safe concurrency from latency, instead of fixed constants.
> Queue management such as bounded queues, serving the newest requests first, and dropping requests that already waited too long, is standard.
> Meshes and gateways offer retry budgets, timeouts, circuit breaking and outlier ejection as configuration.
> Cells limit the blast radius of an overload to a fraction of users.
> Verify product features against current documentation.
**ASIDE:** What else has changed? The controls became platform features. Adaptive concurrency limits learn a service's safe concurrency from latency, instead of using fixed constants. Queue management, such as bounded queues, serving the newest requests first, and dropping requests that already waited too long, is standard. Meshes and gateways offer retry budgets, timeouts, circuit breaking and outlier ejection as configuration. And cell-based designs limit the blast radius of an overload to a fraction of users. As always, check product features against current documentation.


## 10.6 Probe drills

### Slide 23 · Interviewer probe — Where exactly do retries happen in your design, and who is not allowed to retry?   `[probe]`
**INTERVIEWER:** Where exactly do retries happen in your design, and who is not allowed to retry?
*A strong answer on screen:*
> - Retries at one layer, usually the one closest to the user
> - Lower layers fail fast, so they cannot multiply the attempts
> - A budget on each client, and jittered backoff
> - Only idempotent operations retry
**CANDIDATE:** Retries happen at one layer, usually the one closest to the user, because that layer has the context to decide. Lower layers fail fast and do not retry, so attempts cannot multiply. Each client has a retry budget, for example ten percent of its requests, and uses exponential backoff with jitter. Only idempotent operations are retried, and the rest return an error to the caller, with a clear message.

### Slide 24 · Interviewer probe — A zone is lost at peak. Walk me through the next five minutes.   `[probe]`
**INTERVIEWER:** A zone is lost at peak. Walk me through the next five minutes.
*A strong answer on screen:*
> - Check headroom: could the remaining zones absorb it? That is capacity planning, done in advance
> - Traffic shifts; watch utilisation and latency in the survivors
> - If it climbs past the limit: shed the sheddable classes, enable degraded modes
> - Confirm retries are budgeted; hold off non-urgent batch work
**CANDIDATE:** The first question is headroom. If we planned for losing one zone at peak, the remaining zones can absorb it. Traffic shifts, and I watch utilisation and latency in the survivors. If they climb toward the limit, I shed the sheddable traffic classes and enable degraded modes, so the critical requests keep their latency. I check that retries are budgeted, and pause non-urgent batch work. And if we did not plan for the loss, that is the action item.

### Slide 25 · Interviewer probe — Load is back to normal and latency is not. Why?   `[probe]`
**INTERVIEWER:** Load is back to normal and latency is not. Why?
*A strong answer on screen:*
> - Think metastable: a sustaining loop still holds the system down
> - Look for retry backlog, cold caches, long queues, or a leftover limit
> - Break the loop: shed load until the queue drains, then ramp back up slowly
**CANDIDATE:** That smells metastable. The trigger has gone, but something sustains the problem: a retry backlog, cold caches, long queues, or a limit left in the wrong state. I would break the loop by shedding load until the queues drain, pausing retries, and then ramping traffic back up slowly so that caches can warm. Adding capacity alone is risky, because the backlog may swallow it at once.

### Slide 26 · Interviewer probe — Why not just add more servers when you see overload?   `[probe]`
**INTERVIEWER:** Why not just add more servers when you see overload?
*A strong answer on screen:*
> - It takes time, and the load may be growing faster
> - It does not stop retry amplification or a bad request mix
> - Cost and limits: you cannot scale forever
> - First protect what exists, then add capacity if it is justified
**CANDIDATE:** Adding servers takes time, and during that time the overload can feed on itself. It does not remove retry amplification or a bad mix of requests. There are limits and costs as well. So the order is: protect the servers you have, by shedding and throttling, and then add capacity if the demand is real. Capacity is the slowest control, so it comes after the fast ones.


## 10.7 Where this shows up

### Slide 27 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 12 is rate limiting and overload control, and part 13 is reliability patterns, built on this episode.
> - Episode 9: the balancer is where many of these controls live
> - Episode 7: the incident structure for when a cascade does happen
> - Google's SRE books: the chapters on overload and cascading failure, then the workbook chapters on overload and managing load
> - Papers: "The Tail at Scale", and the literature on metastable failures
**COACH:** Next steps. Part twelve of the design-room course is rate limiting and overload control, and part thirteen is reliability patterns, and both are built on this episode. Episode nine showed where many of these controls live, and episode seven covered the incident structure for when a cascade does happen. Google's free S-R-E books cover this in depth, and so does the paper The Tail at Scale.

