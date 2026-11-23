# Episode 2 · Risk, SLIs, SLOs and error budgets

Reader transcript generated from `src/ch02.txt`. Voices: **COACH** narrates; **SAY THIS** is the slower key-line voice; **INTERVIEWER** and **CANDIDATE** play the probe drills; **ASIDE** is a fifth voice for traps, stories and the then-and-now panels. `[pause]` is silence in seconds; `[reveal]` is where the rest of the slide fades in. Each section also gets an automatic title card and a one-second pause. On-screen text is shown as quoted lines.

### Slide 1 · SRE course · Episode 2 of 16 · Priority 1 — Risk, SLIs, SLOs and error budgets   `[th]`
> Why one hundred percent is the wrong target, and how a number turns an argument into a decision.
**COACH:** Episode two. This is the idea that the rest of the course hangs from. Reliability is not a virtue to maximise. It is a budget to spend. We cover risk and service level objectives, and then the part that came later: how modern teams alert on the budget.
**SAY THIS:** One hundred percent is the wrong reliability target for almost everything.
*[pause: 0.8]*


## 2.0 Why this decides interviews

### Slide 2 · The opening story — The outage that was good for Google   `[cards · c2]`
> red The false comfort :: A global lock service was so reliable that teams stopped planning for its failure. They built hard dependencies on it, assuming it would never be down.
> grn The fix :: The service owners made sure it met but did not far exceed its objective. When a quarter went too well, they took it down on purpose, in a controlled outage.
> > Over-delivering on reliability creates dependencies you will pay for later.
**ASIDE:** A story about a lock service. The company's global lock service was so reliable that other teams stopped planning for its failure. They wrote services that could not work without it. Then, on the rare day it failed, the damage was far greater than the failure deserved. The fix is the opposite of what you would expect. The owners made sure the service met, but did not greatly exceed, its objective. When a quarter went too well, they took it down on purpose, in a controlled outage, to flush out the hidden dependencies.

### Slide 3 · What this episode covers — Risk, objectives and the budget   `[panel · note]`
> Embracing risk, and service level objectives. The design-room course treats both as read-first for the observability part and the manager layer.
**COACH:** This episode covers risk and service level objectives. In the design-room course they are marked read first, so this is the way to get them by ear. Let us begin with risk.


## 2.1 Risk is a continuum

### Slide 4 · The nines in minutes — What each target allows, over a year and a thirty-day month   `[table]`
> Target | Per year | Per 30 days | Per day
> 99% | 3.65 days | 7.2 hours | 14.4 minutes
> 99.9% | 8.76 hours | 43.2 minutes | 86 seconds
> 99.99% | 52.56 minutes | 4.32 minutes | 8.6 seconds
> 99.999% | 5.26 minutes | 26 seconds | 0.86 seconds
> > Worth remembering: 99.99 percent allows 52.56 minutes a year.
**COACH:** First, the nines in minutes. Ninety-nine percent allows about three and a half days of downtime a year. Ninety-nine point nine allows about eight and three quarter hours, or forty-three minutes in a thirty-day month. Ninety-nine point nine nine allows fifty-two and a half minutes a year, which is the figure worth memorising, and about four minutes a month. Five nines allows about five minutes a year. Notice that each extra nine is ten times less room for error, and it is much more than ten times the cost.

### Slide 5 · The definition that scales — Availability as request success, not uptime   `[tiles]`
> yield | successful requests divided by total requests
> 2.5 M | requests in the example day
> 250 | errors allowed at 99.99 percent for that day
**COACH:** Now the definition. A global service is almost never completely down, so a count of uptime minutes makes little sense. Define availability as the fraction of requests that succeed. Take their example. A service handles two and a half million requests in a day, with a target of ninety-nine point nine nine percent. That allows two hundred and fifty failed requests. That is a budget you can count.

### Slide 6 · Easy to confuse — Not every request is equal   `[panel · watch]`
> A failed sign-up and a failed background poll count the same in the formula, and they are not the same to a user.
> Weight by importance, or define separate objectives per request class, before you trust one global number.
> > One average hides the request that mattered.
**ASIDE:** One warning. In that formula a failed sign-up and a failed background poll count the same, and they are very different to a user. Weight by importance, or define separate objectives per request class. One global average hides the request that mattered.

### Slide 7 · The price of a nine — Is the next nine worth what it costs?   `[table]`
> Step | Revenue now | Value of the extra availability | Verdict
> 99.9 to 99.99 | one million dollars | one million times 0.0009 = 900 dollars | Only worth it if it costs less than 900 dollars
> > A different anchor: if users cannot tell, the target is high enough. The error rate of the internet between them and you is the floor.
**COACH:** And the price. The arithmetic is blunt. A service earns a million dollars. Improving it from ninety-nine point nine to ninety-nine point nine nine percent adds point zero nine percent of requests, worth nine hundred dollars. If that nine costs more than nine hundred dollars, do not buy it. There is a second anchor. If your errors are smaller than the background failure rate of the user's own internet connection, the user cannot tell the difference, and you have reached the floor.

### Slide 8 · The line to say — Pick the reliability a user can feel and a business will pay for, and then stop.   `[th]`
**SAY THIS:** Choose the reliability target a user can feel and the business will pay for. Beyond that, extra nines buy nothing, and cost both money and speed of change.
*[pause: 0.8]*


## 2.2 The error budget

### Slide 9 · The mechanism — A quarter of budget, spent by incidents and releases   `[dia]`
*Diagram:* `svg/e02-budget-burndown.svg`
**COACH:** Here is the mechanism that makes the number useful. The product team and the S-R-E team agree an objective, say ninety-nine point nine percent over a quarter. The error budget is what is left over: point one percent of requests. Follow the line. It starts full. A bad release takes a slice. A network incident takes another.
**COACH:** At the dashed line the budget is nearly spent, and the rule the teams agreed to in advance applies: releases slow down or stop, and the team works on reliability. When a new quarter begins, the budget refills. The number made the argument for them.

### Slide 10 · One level down — What actually happens as the budget moves   `[table]`
> Budget left | Release policy | Who decides
> Plenty | Ship at normal pace, take risks, run experiments | Product team
> Under a quarter | Smaller changes, more testing, canaries only | Both teams
> Exhausted | Freeze, except security and critical fixes. Spend time on reliability | The pre-agreed policy, not a meeting
> > The simple on-off version is called bang-bang control. Better policies slow down gradually.
**COACH:** One level down, here is what changes as the budget moves. With plenty left, the team ships at its normal pace, and may take risks. When it is low, changes get smaller and more cautious, with canaries. When it is exhausted, releases freeze except for security and critical fixes, and effort goes into reliability. The crucial word is pre-agreed. The policy is written before the incident, so nobody argues about it in the middle. This on-off rule is called bang-bang control, and gentler policies, which slow down gradually, work better.

### Slide 11 · The trap — A budget with no consequence is a decoration   `[panel · trap]`
> If exhausting the budget changes nothing, teams learn that the number is optional.
> If every exhausted budget freezes the company, teams learn to game the measurement.
> Write down who can override the freeze, and how the override is recorded.
**ASIDE:** The trap has two sides. If exhausting the budget changes nothing, then teams learn that the number is decoration. If every exhausted budget freezes the whole company, teams learn to game the measurement instead. The answer is to write down in advance who can override a freeze, and how the override is recorded. That is a management mechanism, not just a technical one.


## 2.3 SLIs, SLOs and SLAs

### Slide 12 · The line to say — The error budget turns an argument into a number.   `[th]`
**SAY THIS:** The error budget turns an argument about risk into a number agreed in advance. While there is budget, ship. When it is spent, slow down and invest in reliability.
*[pause: 0.8]*

### Slide 13 · The three terms — An indicator, an objective, an agreement   `[cards · c3]`
> grn SLI :: A measurement. For example, the fraction of requests served in under 300 milliseconds.
> amb SLO :: A target for that measurement, over a window. For example, 99.9 percent over 30 days.
> red SLA :: A contract with consequences, usually money. Always looser than the SLO.
> > SLI is the ruler. SLO is the goal. SLA is what you promised, with a penalty.
**COACH:** Now the vocabulary, and it is worth being precise. A service level indicator, S-L-I, is a measurement. For example, the fraction of requests answered in under three hundred milliseconds. A service level objective, S-L-O, is a target for that measurement over a window, say ninety-nine point nine percent over thirty days. A service level agreement, S-L-A, is a contract with consequences, usually money, and it is always looser than the objective, because you want to notice trouble long before you owe anyone a refund.

### Slide 14 · Choosing indicators — The right measurement depends on what the system does   `[table]`
> System type | Indicators that matter | The question behind it
> User-facing serving | Availability, latency, throughput | Could we respond, how fast, how many?
> Storage | Latency, availability, durability | Is the data there when I ask?
> Data pipelines | Throughput, end-to-end latency | How fresh is the output?
> Everything | Correctness | Was the answer right?
**COACH:** Which indicators? It depends on what the system does. User-facing serving cares about availability, latency and throughput. Storage cares about latency, availability and durability, which is the chance the data is still there. A data pipeline cares about throughput and how fresh the output is. And every system should care about correctness: was the answer right. Start from what the user does and wants, then work backwards to the measurement.

### Slide 15 · One level down — Percentiles, not averages, and where you measure   `[table]`
> Choice | Weak | Strong
> Latency statistic | Mean | A percentile over a window, and a tail percentile as well
> Request classes | One global number | Separate objectives for interactive and batch
> Where measured | Server logs | As close to the user as you can: client or load balancer
> Targets | Aim as high as possible | Start loose, tighten with evidence
**COACH:** One level down, the choices that separate weak from strong. Use percentiles, not averages, because the average hides the slow tail that users actually feel, and use more than one percentile. Define separate objectives for interactive and batch traffic, because they want different things. Measure as close to the user as you can, such as at the load balancer or in the client, because a server that never saw the request cannot count it as a failure. And start with a loose target, then tighten it from evidence.

### Slide 16 · The line to say — An indicator measures. An objective targets. An agreement binds.   `[th]`
**SAY THIS:** An indicator is a measurement. An objective is a target for it. An agreement is a contract, and it is always looser than the objective.
*[pause: 0.8]*

### Slide 17 · The alternative — Three rules for choosing objectives   `[panel · key]`
> Keep few. Every SLO is a promise you must watch.
> Keep a safety margin. An internal target tighter than the published one gives you room to react before users notice.
> Do not overachieve. If you far exceed the SLO, users build on the better behaviour and you cannot take it back.
**COACH:** There are a few rules for choosing objectives. Keep few of them, because each one is a promise somebody must watch. Keep a safety margin: an internal target tighter than the published one gives you room to react. And do not overachieve, because if you perform far better than your objective, users build on the better behaviour and you cannot take it back. That is the lock service story again.


## 2.4 Then and now

### Slide 18 · Episode 2 · the line to say — Alert on how fast the budget burns.   `[th]`
**SAY THIS:** Do not alert on a threshold. Alert on how fast the budget is burning, over a short window and a long one together.
*[pause: 0.8]*

### Slide 19 · Since 2016 — Alerting on the budget, not on the threshold   `[panel · now]`
> The practical form is: alert when the budget is burning fast, over several windows at once.
> With a ninety-nine point nine percent objective over thirty days, a burn rate of 14.4 for one hour spends two percent of the month. A rate of 6 for six hours spends five percent. A rate of 1 for three days spends ten percent.
> The first two page a human. The last opens a ticket.
**ASIDE:** Now the part that came later. Modern teams turn the budget into alerts. Instead of paging when errors exceed a threshold, page when the budget is burning fast. A burn rate of one means you would spend exactly the whole budget by the end of the window. Take a thirty-day window. A burn rate of fourteen point four sustained for one hour spends two percent of the month, and that pages someone.
**ASIDE:** A rate of six for six hours spends five percent, and that pages too. A rate of one for three days spends ten percent, and that opens a ticket instead.

### Slide 20 · Then and now — The arithmetic behind the burn-rate thresholds   `[table]`
> Window | Burn rate | Share of 30-day budget spent | Check
> 1 hour | 14.4 | 2% | 14.4 × 1 ÷ 720 = 0.02
> 6 hours | 6 | 5% | 6 × 6 ÷ 720 = 0.05
> 3 days | 1 | 10% | 1 × 72 ÷ 720 = 0.10
> > 720 is the hours in 30 days. Each alert is a share of the budget, translated into a rate.
**COACH:** Where do those numbers come from? A thirty-day window has seven hundred and twenty hours. A burn rate of fourteen point four for one hour is fourteen point four divided by seven hundred and twenty, which is two percent. Six for six hours is thirty-six over seven hundred and twenty, five percent. One for seventy-two hours is ten percent. So each alert is just a share of the budget, translated into a rate. Pick the share you are willing to lose before waking someone, and the rate follows.

### Slide 21 · Since 2016 — What else changed in ten years   `[panel · now]`
> Objectives are now written down as code and reviewed like code. Open specifications and tooling exist for this.
> Teams measure freshness and correctness for data and machine-learning pipelines, not only availability.
> More teams agree an objective with each dependency owner instead of assuming one.
> Verify product claims against current documentation before you rely on them.
**ASIDE:** What else has changed? Objectives are now written as code, reviewed like code, and fed straight into dashboards and alerts. Teams measure freshness and correctness for data and machine-learning pipelines, not just availability. And more teams agree an objective with each dependency owner, instead of assuming one. As always, check product claims against current documentation.


## 2.5 Probe drills

### Slide 22 · Interviewer probe — Your service has a ninety-nine point nine percent objective. A dependency has ninety-nine point nine. What can you promise?   `[probe]`
**INTERVIEWER:** Your service has a ninety-nine point nine percent objective. A dependency has ninety-nine point nine. What can you promise?
*A strong answer on screen:*
> - Hard dependencies in series: multiply: 0.999 × 0.999 ≈ 99.8 percent at best
> - Your own failures come on top of that
> - So decouple: degrade gracefully, cache, retry, or make the dependency optional
**CANDIDATE:** If my service needs the dependency for every request, the two multiply. Point nine nine nine times point nine nine nine is about ninety-nine point eight percent, and that is before my own failures. So I cannot honestly promise ninety-nine point nine. I either make the dependency soft, with caching or degraded results, so that its failure does not become mine, or I negotiate a tighter objective with its owner.

### Slide 23 · Interviewer probe — The budget is spent in week two. Product says the launch cannot slip. What do you do?   `[probe]`
**INTERVIEWER:** The budget is spent in week two. Product says the launch cannot slip. What do you do?
*A strong answer on screen:*
> - Apply the pre-agreed policy, not a new negotiation
> - Ask what is cheap to reduce: scope, rollout speed, blast radius of the launch
> - Escalate the risk decision to the person who owns both, with numbers
**CANDIDATE:** I do not reopen the policy in the middle of the argument. I apply what we agreed in advance. Then I ask what is cheap to reduce: the launch scope, the rollout speed, or the blast radius, for example a smaller initial audience. If the business still wants the launch, that is a risk decision for the executive who owns both the product and the reliability, and I bring them the numbers, including how much budget remains.

### Slide 24 · Interviewer probe — Why would you sometimes take your own service down on purpose?   `[probe]`
**INTERVIEWER:** Why would you sometimes take your own service down on purpose?
*A strong answer on screen:*
> - Over-delivery creates hidden hard dependencies
> - A controlled outage shows users what the SLO really means
> - It is a test of the failure path, with an owner and a time window
**CANDIDATE:** Because if a service is much more reliable than its objective, users build on that, and the first real outage is a surprise. A controlled outage, with an owner, a time window and a rollback, keeps the real behaviour close to the published one and tests the failure path. It is the same reason we run drills.


## 2.6 Where this shows up

### Slide 25 · Where this shows up — Read, watch and build next   `[list]`
> ~ Design-room course part 14 teaches S-L-I, S-L-O and error budget as read-first. Part 16 uses the budget as a contract.
> - Episode 4: turn the SLO into alerts, dashboards and a page
> - Episode 5: the budget as the brake on releases
> - Google's SRE books: the chapters on risk and objectives, then the workbook chapters on objectives and alerting
> - Appendices: an example SLO document and an error budget policy to adapt
**COACH:** To place this in your own study. The design-room course teaches the S-L-I, S-L-O and error budget as read-first material in part fourteen, and uses the budget as a contract in part sixteen. Next in this series, episode four turns the objective into alerts and dashboards, and episode five uses the budget as the brake on releases. Google's free S-R-E books cover this in depth, and their workbook appendices are good templates for your own documents.

