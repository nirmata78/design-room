# Episode 4 · Monitoring and alerting

Reader transcript generated from `src/ch04.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 4 of 16 · Priority 1 — Monitoring and alerting   `[th]`
> What to measure, when to wake a human, and how a time-series system turns numbers into pages.
**COACH:** Episode four. Monitoring is the bottom layer of everything else in this course. If you cannot see, you cannot defend an objective, run an incident or tell a good release from a bad one. We cover the principles of monitoring, and how a time-series system produces alerts. Then we bring both up to date.
**SAY THIS:** A page is the most expensive thing a system can do to a human. Spend it carefully.
*[pause: 0.8]*


## 4.0 Why monitoring decides interviews

### Slide 2 · The opening story — Two pagers on the same night   `[cards · c2]`
> red Cause-based paging :: Forty alerts fire: high CPU on a host, a full disk on a log node, a slow query. Nobody can tell whether a customer is affected.
> grn Symptom-based paging :: One page: "checkout errors are at four percent". The dashboards then explain why.
> > Alert on what the user feels. Debug with what the machine says.
**COACH:** Two on-call engineers, the same night. The first has cause-based paging. Forty alerts fire: high processor use on a host, a full disk on a log node, a slow query. Nobody can tell whether a customer is affected. The second has symptom-based paging. One page arrives: checkout errors are at four percent. The dashboards then explain why. That is the argument for the second approach.

### Slide 3 · What this episode covers — Monitoring principles, and alerting from time series   `[panel · note]`
> Monitoring distributed systems, and practical alerting from time-series data. In the design-room course they are read-first for part fourteen.
**COACH:** This episode covers monitoring distributed systems, and practical alerting from time-series data. In the design-room course, both are read first material for the observability part.


## 4.1 Principles

### Slide 4 · Four words — The vocabulary to use   `[table]`
> Term | Meaning | Example
> White-box monitoring | Metrics exposed by the system's own internals | Request counters, queue depth
> Black-box monitoring | Testing the system from outside, as a user would | A probe that loads the home page
> Symptom | What the user sees going wrong | Slow checkout, errors
> Cause | Why it is happening | A saturated database connection pool
> > Black-box finds the symptom now. White-box finds the cause and the problem that is coming.
**COACH:** First, four words. White-box monitoring uses metrics exposed by the system's own internals, such as request counters and queue depth. Black-box monitoring tests the system from outside, as a user would, for example a probe that loads the home page. A symptom is what the user sees going wrong. A cause is why. The pairing to remember is that black-box finds the symptom that is happening now. White-box finds the cause, and also the problem that is coming.

### Slide 5 · The four golden signals — If you can only measure four things   `[cards · c4]`
> grn Latency :: Time to serve a request. Separate the latency of failures from the latency of successes.
> grn Traffic :: How much demand. Requests per second, or bytes, or sessions.
> red Errors :: The rate of failed requests: explicit, implicit and by policy.
> amb Saturation :: How full the most constrained resource is. Predict, not just report.
**COACH:** The four golden signals. Latency: how long requests take, and keep the latency of failed requests apart from the latency of successful ones, because a fast failure can make the average look healthy. Traffic: how much demand. Errors: the rate of failed requests, whether explicit like a server error, implicit like a wrong answer with a success code, or by policy, like a response that was too slow to count. And saturation: how full the most constrained resource is. Saturation is the one that predicts trouble, instead of reporting it.

### Slide 6 · One level down — Why the mean lies, with four numbers   `[table]`
> Requests | Latency | Share
> Fast | 100 ms | 99 in 100
> Slow | 1,000 ms | 1 in 100
> Mean | 109 ms | Looks fine
> 99.5th percentile | 1,000 ms | One request in a hundred takes a full second
> > The advice: bucket latencies and watch the distribution, not the average.
**COACH:** One level down, with numbers. Suppose ninety-nine of every hundred requests take a hundred milliseconds, and one takes a full second. The mean is a hundred and nine milliseconds, and looks fine on a dashboard. But one user in a hundred waits ten times longer, and anyone who makes many requests will hit one. So record latency in buckets, spread roughly exponentially, and reading percentiles from the distribution, not the average.

### Slide 7 · The trap — Do not average percentiles   `[panel · trap]`
> You cannot combine the ninety-ninth percentile of two hosts by taking the mean of the two numbers.
> Aggregate the histograms, then read the percentile from the combined histogram.
> Ten thousand hosts, one fast and one slow: the average of their percentiles describes no real user.
**ASIDE:** And a trap that interviewers love. You cannot combine the ninety-ninth percentile of two hosts by averaging the two numbers. The result describes no real user. Merge the histograms first, then read the percentile from the combined distribution. If someone asks for the ninety-ninth percentile across ten thousand hosts, that is the answer they want: send histograms, merge them, and compute at the end.

### Slide 8 · The line to say — Page on symptoms. Debug with causes. Never average a percentile.   `[th]`
**SAY THIS:** Page on what the user feels, debug with what the machine says, and keep latency as a distribution, because you cannot average a percentile.
*[pause: 0.8]*


## 4.2 When to page a human

### Slide 9 · A page must be — Four tests before a rule is allowed to wake someone   `[list]`
> ~ Paging is expensive, so every page must pass these.
> - Urgent: it cannot wait until morning
> - Important: users or the objective are really affected
> - Actionable: a human can do something useful right now
> - Real: it is not a false alarm
**COACH:** When may a rule page a human? There are four tests. It must be urgent, because it cannot wait until morning. It must be important, because users or the objective really are affected. It must be actionable, because a human can do something useful right now. And it must be real, not a false alarm. If an alert fails any of these, make it a ticket or a dashboard, or delete it.

### Slide 10 · The alternative and the price — Pages, tickets and logs   `[table]`
> Channel | Use for | Cost of a false alarm
> Page | Active, user-visible harm, or budget burning fast | A human is woken, and alert fatigue grows
> Ticket | Needs a human, but not tonight | A little wasted time
> Dashboard or log | Context for a human who is already looking | Almost none
> > The pattern: spend the page budget on symptoms, and let causes live on dashboards.
**COACH:** The price of each channel. A page is for active, user-visible harm, or a budget burning fast. A false alarm wakes a human and builds alert fatigue. A ticket is for work that needs a human but not tonight, and a false alarm wastes a little time. A dashboard or log is context for someone already looking, and costs almost nothing. The pattern is to spend the page budget on symptoms, and let causes live on dashboards.


## 4.3 How a time-series system alerts

### Slide 11 · The mechanism — From a counter in a process to a page on a phone   `[dia]`
*Diagram:* `svg/e04-alert-path.svg`
**COACH:** Now the machinery. The shape is the same in every modern monitoring system. The service exposes counters on a plain text page. A collector scrapes them on an interval, say every fifteen seconds, and stores each as a time series. A rule engine evaluates expressions over those series on its own interval, for example the ratio of errors to requests over five minutes. If the expression stays true for a hold time, an alert fires.
**COACH:** An alert manager groups, de-duplicates and routes it, and finally a page reaches a phone. Every arrow adds delay, and that sum is your time to detect.

### Slide 12 · One level down — Detection time is a sum, and you choose which term to cut   `[table]`
> Stage | Example | Seconds
> Scrape interval | every 15 s | up to 15
> Rule evaluation interval | every 15 s | up to 15
> Hold time before firing | 2 minutes | 120
> Grouping and notification | 30 s | 30
> Worst-case detection | | 180
> > Cutting the hold time costs false alarms. Cutting the scrape interval costs storage and load.
**COACH:** One level down. Detection time is a sum. A fifteen second scrape, a fifteen second evaluation, a two minute hold time and thirty seconds for grouping and notification add up to about three minutes in the worst case. You choose which term to cut. Shortening the hold time costs you false alarms. Shortening the scrape interval costs storage and load. And notice that the biggest term is the one you set on purpose, to stay quiet.

### Slide 13 · The line to say — Detection time is a sum of delays.   `[th]`
**SAY THIS:** Time to detect is a sum of delays, and the biggest one is usually the hold time you chose on purpose, to stay quiet.
*[pause: 0.8]*

### Slide 14 · The idea in code — An error ratio rule, written in the style used today   `[code]`
> # Share of requests that failed, over five minutes, per service
> sum by (service) (rate(http_requests_total{code=~"5.."}[5m]))
> /
> sum by (service) (rate(http_requests_total[5m]))
> # Alert if it stays above the objective's error rate for two minutes
> alert: HighErrorRatio
> expr:  error_ratio > 0.01
> for:   2m
**COACH:** Here is the idea in the style used today, a query language of the Prometheus family. The first expression divides the rate of failing requests by the rate of all requests, per service, over five minutes. The second rule says: fire if that ratio stays above one percent for two minutes. It is illustrative, the syntax of your own system will differ. The point is that an alert is just a query over time series with a duration attached.

### Slide 15 · Aggregation — Monitoring that follows the shape of the service   `[dia]`
*Diagram:* `svg/e04-hierarchy.svg`
**COACH:** Now how to scale it. A small collector near each group of tasks scrapes them. A cluster level collector aggregates those. A global one aggregates the cluster ones, and each level discards detail it no longer needs. Alert rules live at the level where the decision is meaningful. This is why a global error ratio does not need every raw sample from every task, and it is the same idea as the roll-ups and retention tiers in any modern metrics system.

### Slide 16 · The line to say — Silence must be able to raise an alarm.   `[th]`
**SAY THIS:** If silence can mean broken, the alerting path needs an alarm of its own: a signal that is always firing, and a check that pages when it stops.
*[pause: 0.8]*

### Slide 17 · The trap — Who monitors the monitor?   `[panel · trap]`
> If the alerting path runs on the same cluster it watches, a bad day for the cluster is a silent day for the alerts.
> Keep the alert path independent, and add a dead-man's switch: a rule that is always firing, and a separate check that pages when it stops.
**ASIDE:** One more trap. If the alerting path runs on the same cluster it watches, a bad day for that cluster is a silent day for the alerts. Keep the path independent. And add a dead-man's switch: a rule that is always firing, with a separate check that pages when the signal stops arriving. Silence must be able to raise an alarm.


## 4.4 Then and now

### Slide 18 · Since 2016 · the line to say — Count the series before you add the label.   `[th]`
**SAY THIS:** Every distinct label value is a new time series. Count the series before you add the label, because the monitoring system can be taken down by its own users.
*[pause: 0.8]*

### Slide 19 · Since 2016 — The open ecosystem caught up   `[panel · now]`
> Metrics: a pull-based, label-oriented model with a query language is now the common default. Traces and logs share one vendor-neutral instrumentation standard.
> Metrics can carry exemplars: a pointer from a latency bucket to a sample trace, so you go from the graph to one slow request.
> Cardinality is the new hazard. Every label value makes a new series. A user ID as a label is the classic outage of the monitoring system itself.
**ASIDE:** What has changed since 2016? The open ecosystem caught up. A pull-based, label-oriented metrics model with a query language is now the common default, and traces and logs share a vendor-neutral way to instrument. Metrics can carry exemplars, a pointer from a latency bucket to a sample trace, so you can jump from a graph to one slow request. And a new hazard became famous: cardinality. Every distinct label value creates a new series, and putting a user identifier in a label is the classic way to take down your own monitoring.

### Slide 20 · Then and now — Two checklists that grew out of the golden signals   `[table]`
> Method | For | The three questions
> RED | Services | Rate, Errors, Duration
> USE | Resources | Utilisation, Saturation, Errors
> Golden signals | Both | Latency, traffic, errors, saturation
> > RED, from Tom Wilkie, and USE, from Brendan Gregg, are practitioner shorthands. RED is for services, USE is for resources.
**COACH:** Two community checklists grew out of the golden signals. R-E-D, for services: rate, errors, and duration. And U-S-E, for resources like disks and processors: utilisation, saturation, and errors. They are the same ideas in different packaging. In an interview, use whichever one you can say without thinking, and tie it back to the objective, because that is what makes a metric matter.

### Slide 21 · Since 2016 — Alert on the budget, and use the machines for triage   `[panel · now]`
> Instead of fixed thresholds, many teams alert on error budget burn rate across several windows, as episode two showed.
> Tools now cluster related alerts, correlate them with recent changes and deploys, and propose likely causes. They draft a timeline, but a human owns the call.
> Continuous profiling is becoming a fourth signal beside metrics, traces and logs. The open standard for it is still in alpha.
**ASIDE:** A second change. Many teams now alert on the error budget burn rate across several windows, as episode two showed, instead of fixed thresholds. And tooling helps with triage. It clusters related alerts, correlates them with recent deploys, and proposes likely causes. It can draft a timeline. But a human owns the call, and the first minutes of an incident still depend on a good page and a good dashboard. Continuous profiling is also becoming a fourth signal, for cost and latency work, though the open standard for it is still young.


## 4.5 Probe drills

### Slide 22 · Interviewer probe — What is the ninety-ninth percentile latency across ten thousand hosts?   `[probe]`
**INTERVIEWER:** What is the ninety-ninth percentile latency across ten thousand hosts?
*A strong answer on screen:*
> - Not the average of ten thousand percentiles
> - Each host sends a histogram; merge the histograms; read the percentile from the merged one
> - Accuracy depends on the bucket boundaries, so choose them for the range that matters
**CANDIDATE:** Not the mean of ten thousand percentiles, which describes no real request. Each host exports a histogram with agreed bucket boundaries. A collector sums the counts per bucket across hosts, and I read the percentile from the merged histogram. The accuracy depends on how the buckets are laid out, so I choose boundaries around the latency range that matters for the objective.

### Slide 23 · Interviewer probe — Cut detection time from two minutes to fifteen seconds. What does it cost?   `[probe]`
**INTERVIEWER:** Cut detection time from two minutes to fifteen seconds. What does it cost?
*A strong answer on screen:*
> - Shorter hold time: more false alarms from noise
> - Shorter scrape and evaluation intervals: more storage and compute
> - Mitigate: alert on burn rate over a short and a long window together
> - Ask: what is the harm of a two minute delay, and what does a false page cost?
**CANDIDATE:** Each term costs something. A shorter hold time lets noise through, so more false pages. A shorter scrape and evaluation interval costs storage and compute. I can soften the false alarms by requiring a short window and a longer one to agree, which is the multi-window burn rate idea. But first I would ask what a two minute delay actually costs in user harm, because if it is small, the faster alert is spending a human's sleep for nothing.

### Slide 24 · Interviewer probe — Who monitors the monitor?   `[probe]`
**INTERVIEWER:** Who monitors the monitor?
*A strong answer on screen:*
> - An independent path, ideally on a different failure domain
> - A dead-man's switch: an always-firing alert, and a check for its absence
> - External black-box probes that do not depend on internal metrics
**CANDIDATE:** A separate path, running in a different failure domain from the thing it watches. A dead-man's switch: an alert that always fires, with a second system that pages when it stops arriving. And external black-box probes, which see what a user sees, and do not rely on internal metrics at all.


## 4.6 Where this shows up

### Slide 25 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 14 covers time-series storage, cardinality, histograms and the detection-time formula, in depth.
> - Episode 2: the objective that these alerts defend
> - Episode 6: using these signals to troubleshoot
> - Google's SRE books: the chapters on monitoring and alerting, then the workbook chapters on alerting and on-call
> - Papers: the Monarch paper for a global in-memory time-series system
**COACH:** Next steps. Part fourteen of the design-room course goes deep on time-series storage, cardinality, histograms and the detection time formula. Episode two covered the objective these alerts defend, and episode six uses these signals to troubleshoot. Google's free S-R-E books go deeper, and the Monarch paper if you want to see a global time-series system.

