# Episode 9 · Load balancing, at the edge and inside the datacenter

Reader transcript generated from `src/ch09.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 9 of 16 · Priority 1 — Load balancing, at the edge and inside the datacenter   `[th]`
> DNS, virtual addresses, subsets, lame ducks and the quiet failure of round robin.
**COACH:** Episode nine. Load balancing comes in two layers. First, how a user's request finds a datacenter and a front end. Then, how a service inside a datacenter spreads work among its backends. The first is mostly about the network. The second is mostly about queues, health and statistics, and it hides some of the best interview questions in the field.
**SAY THIS:** Load balancing is not about being fair. It is about keeping every machine below the point where it falls over.
*[pause: 0.8]*


## 9.0 Why this decides interviews

### Slide 2 · The opening story — Equal requests, unequal load   `[cards · c2]`
> red Plain round robin :: Every client sends one request to each backend in turn. Fair on paper. In practice the busiest backend uses up to twice the processor time of the quietest.
> grn Informed balancing :: The client avoids tasks that are slow or full, and sends more to tasks that report spare capacity. The spread narrows, and you can run the fleet hotter.
> > Unevenness is wasted money, and the hottest machine decides when you fall over.
**COACH:** Here is the surprise to begin with. A client sends one request to each backend in turn. That is round robin, and it is fair on paper. But in practice it can leave the busiest backend using up to twice the processor time of the quietest. Informed balancing, where the client avoids slow or full tasks and favours the ones with spare capacity, narrows the spread. Unevenness is wasted money, because the hottest machine decides when you fall over, and you must keep the average low enough to protect it.

### Slide 3 · What this episode covers — Load balancing at the front end, and in the datacenter   `[panel · note]`
> Load balancing at the front end, and load balancing in the datacenter. Both are must-read for the design-room networking and overload parts.
**COACH:** This episode covers load balancing at the front end, and load balancing in the datacenter. Both are on the must read list for the networking and overload parts of the design-room course.


## 9.1 At the edge

### Slide 4 · The layers — Four steps from a name to a task   `[dia]`
*Diagram:* `svg/e09-lb-layers.svg`
**COACH:** Follow a request through the layers. A user's device looks up a name. D-N-S returns an address chosen to be near the user and to avoid a datacenter that is full or down. That is the first layer. The address is a virtual address, shared by many machines, and a network load balancer there picks a front end. That is the second. The front end terminates the connection, and sends the request to a service.
**COACH:** Inside the datacenter, a client of that service picks one backend from its subset. That is the third and fourth. Each layer makes a decision with different information, at a different speed.

### Slide 5 · One level down — What DNS can and cannot do   `[table]`
> Strength | Weakness
> Works before the connection starts, and needs no special client | Resolvers cache: you cannot flush them, so the TTL limits how fast you can steer
> Can return different answers by location and by load | The resolver is the middleman: it hides the user's real location
> Simple and universal | Answers are not tied to the health of a specific machine
> > The verdict: the simplest, most effective first step, and never sufficient alone.
**COACH:** One level down, what D-N-S can and cannot do. Its strength is that it works before the connection starts, with no special client, and it can return different answers by location and by load. Its weakness is caching. Resolvers hold on to answers, you cannot flush them, and so the time to live limits how fast you can steer traffic. The resolver is also a middleman, which hides the user's real location. And answers are not tied to the health of a specific machine.
**COACH:** The verdict is that D-N-S is the simplest and most effective first layer, and never sufficient alone.

### Slide 6 · The line to say — DNS first, never alone.   `[th]`
**SAY THIS:** D-N-S is the simplest first layer and is never sufficient alone, because resolvers cache and the time to live limits how fast you can steer.
*[pause: 0.8]*

### Slide 7 · Virtual addresses — The second layer, and its hard problem   `[table]`
> Concern | Approach
> Spreading connections across front ends | Hash on connection fields, or track connections
> Keeping a connection on one machine when the pool changes | Consistent hashing: a stable mapping when machines come and go
> Sending packets on | Encapsulate the packet, so the front end sees the original address
> > The pattern: simple connection tracking normally, consistent hashing as the fallback under pressure.
**COACH:** The second layer is the virtual address. It is shared by many machines, so the user sees one address, and the operator can add machines or run maintenance invisibly. Its hard problem is keeping one connection on one machine while the pool changes. Google uses consistent hashing for that, which gives a mapping that stays mostly stable when machines come and go, and it forwards the packet encapsulated, so the front end still sees the original address. The pattern is simple connection tracking normally, and consistent hashing as the fallback when the system is under pressure.

### Slide 8 · The line to say — Spread by name first, by address second, and by request last.   `[th]`
**SAY THIS:** Balance in layers. D-N-S steers users to a place. A virtual address steers connections to a front end. The client steers each request to a backend, with the best information available.
*[pause: 0.8]*


## 9.2 Inside the datacenter

### Slide 9 · The failure of random subsets — Three hundred clients, three hundred backends   `[dia]`
*Diagram:* `svg/e09-subset-load.svg`
**COACH:** Now a lovely piece of arithmetic. Each client keeps long-lived connections to a subset of the backends, because connecting to all of them wastes memory and effort. The naive way to choose a subset is for each client to shuffle the list of backends and take some. Take three hundred clients and three hundred backends, each client taking thirty percent, which is ninety backends.
**COACH:** The result: the least loaded backend has sixty-three percent of the average load, and the most loaded has a hundred and twenty-one percent. A random subset spreads the load unevenly, even with a generous subset size.

### Slide 10 · One level down — Choosing a subset on purpose   `[table]`
> Method | How | Result
> Random | Each client shuffles, picks | Uneven: 63 to 121 percent of the average, in the example
> Deterministic | Clients are assigned slices of a shared, shuffled order | Every backend gets about the same number of connections
> Whatever the method | Must keep churn low when tasks restart | Reconnection storms are expensive
> > The algorithm shuffles the backend list in rounds, and gives each client a fixed slice.
**COACH:** One level down. The fix is deterministic subsetting. Instead of each client shuffling alone, clients are numbered, and the list of backends is shuffled in rounds with a seed shared by the clients in a round. Each client is then assigned a fixed slice. Every backend receives about the same number of connections. And the method must keep churn low when tasks restart, because reconnection storms are expensive. The lesson is general: when you need even load, do not leave it to chance. Design the assignment.

### Slide 11 · The line to say — Design the assignment. Do not leave it to chance.   `[th]`
**SAY THIS:** When you need even load, do not leave it to chance. Design the assignment of clients to backends.
*[pause: 0.8]*

### Slide 12 · The lame duck — Draining a task without dropping a request   `[dia]`
*Diagram:* `svg/e09-lame-duck.svg`
**COACH:** Now a health problem. A task that is shutting down for an upgrade should not drop its requests. There is a state for this, called lame duck. The task tells its clients: I am still working, but do not send me new requests. Clients move new work to other tasks, while the lame duck finishes what it has and then stops. Compare that to the simple approach, flow control, where a client stops sending to a backend that has too many unfinished requests.
**COACH:** A limit of about a hundred active requests is a reasonable default. Flow control reacts to trouble. The lame duck state avoids it.

### Slide 13 · The alternative and the price — Four policies, ordered by how much they know   `[table]`
> Policy | What it uses | Weakness
> Round robin | Nothing | Up to 2x spread in processor use
> Least-loaded | The client's own count of active requests | Blind to other clients' load
> Weighted round robin | Backend-reported load or capacity | Needs reporting and tuning
> Latency or error aware | Recent response times and failures | Can oscillate if it reacts too fast
> > The trajectory: from simple, to least-loaded, to weighted.
**COACH:** The policies, ordered by how much they know. Round robin knows nothing, and the spread can reach two to one. Least-loaded uses the client's own count of active requests, but is blind to other clients' load. Weighted round robin uses what the backends report, such as their load or capacity, which needs reporting and tuning. And latency or error aware policies use recent response times, and can oscillate if they react too fast. More information gives a better spread, and costs more complexity.

### Slide 14 · The line to say — More information, better spread, more complexity.   `[th]`
**SAY THIS:** More information gives a better spread, and costs more complexity. Choose the simplest policy that keeps the hottest machine safe.
*[pause: 0.8]*

### Slide 15 · The trap — Herding: everyone goes to the same quiet machine   `[panel · trap]`
> If every client picks the least loaded backend using stale data, they all pick the same one, and it becomes the most loaded.
> Add randomness, or compare just two random candidates and take the better one.
> Use fresh signals, and dampen the reaction.
**ASIDE:** The trap is herding. If every client picks the least loaded backend using stale data, they all pick the same one, and it instantly becomes the most loaded. The fixes are randomness, or comparing just two random candidates and taking the better of the two, a technique known as the power of two choices. And use fresh signals, and dampen the reaction.


## 9.3 Then and now

### Slide 16 · Episode 9 · the line to say — Moving the balancer into the platform does not remove the need to budget retries.   `[th]`
**SAY THIS:** Moving the balancer into the platform does not remove the need to budget retries, because a retry is load.
*[pause: 0.8]*

### Slide 17 · Since 2016 — The balancer moved into the platform   `[panel · now]`
> Proxies and meshes now make per-request, layer-seven balancing a platform feature: retries, timeouts, outlier ejection and health checks, configured centrally.
> Client-side balancing remains common for RPC, but the policy is updated from a control plane that distributes endpoint lists.
> Anycast and global load balancers route users to the nearest healthy region at the network level.
> Overload awareness has moved into balancers: concurrency limits and load shedding, which the next episode covers.
**ASIDE:** What has changed since 2016? The balancer moved into the platform. Proxies and service meshes make per-request balancing a platform feature, with retries, timeouts, outlier ejection and health checks configured centrally. Client-side balancing remains common for remote procedure calls, but the policy and the list of endpoints come from a control plane. Anycast and global load balancers route users to the nearest healthy region at the network level. And balancers have become overload aware, with concurrency limits and load shedding, which is the subject of the next episode.

### Slide 18 · Then and now — Where each idea lives today   `[table]`
> Original idea | Modern form | Check
> Datacenter-wide RPC balancing | Sidecar or proxy, with centrally pushed config | Retries and timeouts must be budgeted, or they amplify load
> Lame duck | Readiness failing before shutdown, a connection drain period | Drain time must exceed the longest in-flight request
> Subsetting | Endpoint subsetting in the mesh and client libraries | Test churn during rolling updates
> Consistent hashing at the VIP | Network load balancers built on the same idea | Maglev paper describes one design
> > Source for the last row: the Maglev paper (NSDI 2016).
**COACH:** To make it concrete, here is where each idea lives today. Datacenter-wide balancing of remote calls is a sidecar or proxy with centrally pushed configuration, but retries and timeouts must be budgeted, or they amplify load. The lame duck state is a readiness check that fails before shutdown, with a connection drain period that has to exceed the longest in-flight request. Subsetting is in the mesh and in client libraries, and you should test churn during rolling updates.
**COACH:** And consistent hashing at the virtual address lives on in network load balancers, one design of which is described in the Maglev paper.


## 9.4 Probe drills

### Slide 19 · Interviewer probe — Why not just use round robin everywhere?   `[probe]`
**INTERVIEWER:** Why not just use round robin everywhere?
*A strong answer on screen:*
> - It ignores cost variation, machine differences, and uneven client rates
> - Measured spreads reach up to 2x between the quietest and busiest task
> - Use more information: backend-reported load, or latency, and avoid herding
**CANDIDATE:** Because it ignores everything that varies: the cost of each request, the differences between machines, and the fact that clients send at different rates. Measured spreads reach up to two to one in processor use between the quietest and the busiest task. I would use more information, such as backend-reported load or recent latency, and guard against herding with randomness, like comparing two candidates.

### Slide 20 · Interviewer probe — A deploy is rolling out and users see a burst of errors on each restart. Why, and how do you fix it?   `[probe]`
**INTERVIEWER:** A deploy is rolling out and users see a burst of errors on each restart. Why, and how do you fix it?
*A strong answer on screen:*
> - Tasks die with requests in flight, and clients keep sending to them
> - Add a lame duck, or a readiness failure, then drain, then stop
> - Drain time must exceed the longest in-flight request
> - Clients should retry idempotent requests on another backend
**CANDIDATE:** The tasks are being killed with requests still in flight, and the clients do not know they are going away. The fix is a graceful shutdown: signal that the task is leaving, which is the lame duck state or a failing readiness check, wait for new traffic to stop, drain the in-flight requests, and only then stop. The drain time must be longer than the longest request. And clients should retry idempotent requests on another backend.

### Slide 21 · Interviewer probe — The load balancer is a single point of failure. How do you design around it?   `[probe]`
**INTERVIEWER:** The load balancer is a single point of failure. How do you design around it?
*A strong answer on screen:*
> - Many instances behind one virtual address, with health checks
> - Stateless where possible, with connection tracking or consistent hashing
> - Failures drain automatically; the pool is sized to survive losing one or two
> - Multiple layers and regions, so one layer's failure is not total
**CANDIDATE:** By not having one. Many load balancer instances sit behind one virtual address, with health checks, so a failed instance is removed automatically. I keep them as stateless as possible, with connection tracking or consistent hashing so a pool change does not break existing connections. I size the pool to survive losing a couple of instances at peak. And I use more than one layer and more than one region, so a failure of any one layer is not total.


## 9.5 Where this shows up

### Slide 22 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 11 covers networking and the edge in depth, and part 12 builds on overload.
> - Episode 10: when the balancer meets overload, and retries turn a dip into an outage
> - Episode 11: the consensus service that decides who is leader
> - Google's SRE books: the chapters on load balancing
> - Papers: Maglev; "The Tail at Scale"
**COACH:** Next steps. Part eleven of the design-room course covers networking and the edge, and part twelve builds on overload. Episode ten shows what happens when the balancer meets overload, and retries turn a dip into an outage. Google's free S-R-E books cover both, and the Maglev paper and The Tail at Scale are the best companions.

