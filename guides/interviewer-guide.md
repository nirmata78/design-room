# Running a System Design Mock — An Interviewer's Guide

*How to frame, probe, and score a FAANG-style design round · with 3 ready-to-run problems + a grading sheet*

## How to use this guide

Thank you for running this mock — a realistic dry run is one of the highest-leverage things that can be done before the real loop. This guide makes it easy **even if system design is not your area.** You do not need to know the "right" answer; your job is to hold the frame, keep time, ask a handful of well-chosen follow-ups, and write down what you observe. Everything you need to do that is here.

Read this once end-to-end (about fifteen minutes). Then pick **one** of the three problems in §6, run the 45–55 minute session using the run-of-show in §5, and fill in the one-page grading sheet on the last page. Reserve the final ten minutes for a debrief (§8) — that feedback is where most of the value lands, and it is the one way a mock differs from the real thing.

> **💡 THE ONE IDEA · You are simulating a future colleague, not grading a quiz**
>
> A system design round is not a test with a single correct diagram. The interviewer is forming one judgment: *what would it be like to be in a design review with this person for the next five years?* Do they bring structure to a vague problem, make assumptions explicit, reason about trade-offs and cost, listen and adapt, and stay calm when challenged? Score the **behaviors and the reasoning**, not whether they named the exact technology you had in mind. Your most useful instinct as the interviewer is to keep gently asking *"why?"* and *"what happens if…?"* — the quality of the answers to those two questions is almost the whole signal.

## 1 · Your job in the room

Hold four roles at once, in this priority order:

- **Timekeeper.** The single most common failure is running out of time with the design half-finished. Keep the clock visibly and steer transitions (§5). This is the highest-value thing you do.
- **Frame-holder.** Give the prompt, then let the candidate drive. Resist the urge to teach, to fill silences, or to lead them to the answer. A few seconds of silence is theirs to fill.
- **Prober.** Every few minutes, push on one decision with a follow-up from the problem's cue sheet in §6. You are looking for the *edge* of their understanding — keep asking "why" until they reach it, then move on. Reaching an edge is normal and good, not a failure.
- **Note-taker.** Jot concrete quotes and moments as they happen, against the grading dimensions in §7. Memory fades fast; the sheet is far more useful if filled live.

> **⚠️ COMMON MOCK-INTERVIEWER MISTAKES · Avoid these**
>
> **Teaching mid-round** ("well, actually you'd use a queue here") — it contaminates the signal; save it for the debrief. **Over-helping** — rescuing them the moment they pause robs you of seeing how they recover. **Under-driving** — sitting silent for 45 minutes; you should be probing every few minutes. **Leading questions** that hand over the answer ("don't you think you need a cache?") instead of neutral ones ("what happens to your database under that read load?"). **Letting a rabbit hole run** — if they spend 15 minutes on one corner, redirect. **Grading only the diagram** — the reasoning and communication matter as much as the boxes.

## 2 · The shape of a FAANG-style round

A real round is **45–60 minutes**: a one-line prompt, a long open middle where the *candidate* drives, and an interviewer who probes with "what if…" pressure-tests. The defining expectation — and the thing weaker candidates miss — is that **the candidate leads.** You are a collaborator and a steering wheel, not a quizmaster feeding the next question. If they wait to be asked or treat it like an oral exam, that itself is a (negative) signal worth noting.

| Phase | Target time (of ~50 min) | What good looks like |
|---|---|---|
| Requirements & scope | ~8 min | Turns the vague prompt into explicit functional + non-functional needs; says what's out of scope |
| Estimation | ~6 min | A few back-of-envelope numbers that *change a decision* |
| High-level design | ~12 min | One clean diagram; walks the end-to-end happy path |
| Deep dives | ~15 min | Goes two levels deep where you steer; names trade-offs |
| Wrap-up: failure, scale, cost | ~6 min | Bottlenecks, what breaks first, SLAs, cost; crisp summary |

These are *targets to steer toward*, not a script to enforce rigidly — but if a phase is running long, it is your job to move things along.

## 3 · Calibrate before you judge: the 1–4 scale

Use a simple four-point scale on every dimension. Anchoring on it before the session keeps your scoring honest.

| Score | Meaning | Rough feel |
|---|---|---|
| **1** | Below bar | Missed the point, needed leading, or couldn't go deeper when asked |
| **2** | Approaching | Right instincts but gaps, vague, or needed nudging to get there |
| **3** | At bar (hire) | Solid, self-directed, justified choices, handled probing |
| **4** | Above bar | Crisp, anticipated issues, taught *you* something, strong trade-offs |

Most strong candidates land on a mix of 3s with a couple of 2s and 4s. A wall of 4s usually means you didn't probe hard enough; a wall of 2s usually means the problem was mis-scoped or the prompt was unclear.

## 4 · What and how to ask — the follow-up engine

The follow-up is your main instrument. Good ones are **neutral, open, and aimed at a decision the candidate already made.** You are not introducing new requirements to trip them up (mostly); you are asking them to defend or deepen a choice. A reliable ladder:

1. **"Why that choice?"** — surfaces whether a named technology is reasoning or name-dropping. Ask it about almost every major box.
2. **"What are the alternatives, and what did you trade away?"** — separates people who know one tool from people who know the design space.
3. **"What happens when this fails / doubles / 10×s?"** — the single richest probe. Pick a component and remove it, overload it, or break the network to it.
4. **"How would you know it's broken in production?"** — monitoring, alerting, SLAs. This is where senior and managerial candidates pull ahead.
5. **"What would you cut if you had half the time / half the budget?"** — tests prioritization and cost judgment.

> **✅ HOW TO PUSH WITHOUT LEAKING · The calibrated-hint ladder**
>
> When the candidate is genuinely stuck, help in graduated steps, and **note the level of help you had to give** — it is part of the score. (a) *Re-ask the requirement:* "Remember we need results within a minute — does this path meet that?" (b) *Narrow the area:* "Let's focus on the write path." (c) *Name the tension, not the answer:* "There's a tension between freshness and cost here — how do you think about it?" (d) *Offer a choice:* "Would you batch these or process them one at a time?" Only drop to (d) if they're truly blocked. A candidate who needs only (a)-level nudges is scoring well; one who needs (d) to move at all is not.

> **ℹ️ HANDLING THE TWO HARD MOMENTS · Silence and rabbit holes**
>
> **Silence:** count to five before intervening. Thinking time is theirs, and rescuing too early hides their recovery skill. If it persists, ask "what are you weighing right now?" — it both unblocks them and reveals their thought process. **Rabbit holes:** if they've spent more than ~5 minutes polishing one corner while the overall design is incomplete, redirect explicitly: "This is good detail — let's make sure we have the whole picture first and come back if there's time." Managing breadth-vs-depth is the candidate's job, but you protect the clock.

## 5 · The run of show (your script)

You can run the whole session from this list. Times assume a 50-minute round.

1. **Frame it (1 min).** "We'll spend about 50 minutes. I'll give you a problem; please drive — think out loud, ask me anything, and treat me as a teammate. I'll jump in now and then. Ready?" Then read the prompt from §6 **once**, slowly, and let them start.
2. **Requirements (let them run ~8 min).** Expect questions back at you — answer briefly and decisively (the §6 sheets tell you what to say). If they start drawing immediately without scoping, note it and let them; don't correct.
3. **Estimation (~6 min).** If they skip it entirely, prompt once: "Roughly what scale are we dealing with?" Note whether the numbers actually influence the design or are just decoration.
4. **High-level design (~12 min).** Let them sketch the end-to-end path. Ask them to "walk me through one request/event from start to finish." Don't critique the diagram yet.
5. **Deep dives (~15 min).** *Now* you drive. Pick two or three probes from the problem's cue sheet and go two levels deep. This is the heart of the signal.
6. **Wrap-up (~6 min).** "What breaks first as this grows? How would you know? What did you trade off?" Then: "If you had to summarize the design in four sentences, go." A crisp summary under time pressure is a strong closing signal.
7. **Stop on time.** Then switch hats for the debrief (§8).

## 6 · Three problems you can run

Pick **one** per session. Each is self-contained: a prompt to read aloud, the answers to give if they ask, what a good design contains (in plain English — you don't need to know more than this), the probes to push on, and how to tell weak from strong. They escalate slightly in openness: Problem A is the most guided, C the most bounded and classic.

> **ℹ️ ABOUT THESE PROBLEMS**
>
> All three are aligned to a **data-delivery / streaming** flavor that matches the target role, but they are standard FAANG-style prompts and need no special domain knowledge from you to facilitate. "Good design contains" lists are *checklists of things to listen for*, not a required ordering — a strong candidate will arrive at most of them in their own sequence.

### Problem A — Real-time audience metrics

**Read aloud:** *"Design a system that ingests viewing events from tens of millions of internet-connected TVs and shows internal dashboards how many unique households are watching each program — updated to within about a minute."*

**If they ask (give these):** ~50 million devices; each sends an event every few seconds while on; "unique households" should be approximate is fine (within ~1–2%); dashboards refresh ~once a minute; data must also be kept for later exact historical analysis; one region is fine to start.

**A good design contains (listen for):** a thin ingest/collector tier behind a load balancer; a **durable event log / queue** (so spikes and consumer slowness don't lose data); a **stream processor** computing rolling counts; an **approximate unique-count technique** (they may say "HyperLogLog" or "a probabilistic counter" — the key insight is that exact distinct-counting at this scale is too expensive); a fast **read store / cache** the dashboards hit; and **separately**, writing raw events to cheap storage (a "data lake") for later exact/historical queries. Recognizing that real-time-approximate and batch-exact are *two different paths* off the same event stream is the senior insight here.

**Probes (pick 2–3):** *Why a log/queue instead of writing straight to a database?* · *Events arrive late or out of order — how do you count them correctly?* (look for "windowing" / "watermarks") · *Why approximate counting — what would exact cost?* · *A consumer crashes for 10 minutes — do you lose data or double-count?* (look for replay + idempotency) · *How do dashboards stay fast under many concurrent viewers?* · *(EM bar)* *How would you know in production that counts are wrong? What's the SLA and the cost?*

**Weak / Strong / Exceptional:** *Weak* — writes events straight to one database and queries `COUNT DISTINCT` live; no buffering; ignores late data. *Strong* — durable log + stream processor + approximate counting + a separate batch path; handles replay and late events. *Exceptional* — quantifies the load to justify each choice, discusses cost of the lake vs the serving store, names how they'd detect drift and what the on-call story is, and scopes an MVP first.

### Problem B — Partner data-feed delivery

**Read aloud:** *"Design a service that delivers large custom datasets to external business partners — some on a fixed schedule (e.g., every morning) and some on demand — and guarantees each partner gets correct, fresh, access-controlled data."*

**If they ask (give these):** hundreds of partners; datasets range from megabytes to tens of gigabytes; freshness expectation is "yesterday's data by 6 a.m."; partners pull via an API and also want bulk file drops; data is sensitive, so access control and auditability matter; occasional re-delivery of corrected data must be supported.

**A good design contains (listen for):** a clear split between **generating** a dataset (a scheduled/orchestrated job that produces a versioned, immutable output) and **delivering** it (an API plus bulk file access such as signed download links or a managed file-transfer drop); **versioning / immutability** so a partner can re-fetch exactly what they got; **access control + audit logging** per partner; a **scheduler/orchestrator** for the recurring jobs with retries and alerting on failure; **idempotent** delivery so a retry doesn't corrupt or duplicate; and handling **large files** without streaming them through an app server (pre-signed links / direct object storage). Bonus: a manifest/checksum so partners can verify completeness.

**Probes (pick 2–3):** *A nightly job fails at 3 a.m. — what happens, and how does the partner and your team find out?* · *A partner says yesterday's file was wrong — how do you re-deliver without breaking others?* (versioning) · *How do you serve a 30 GB file without melting your servers?* · *How do you stop Partner X from seeing Partner Y's data, and prove it later?* (authz + audit) · *On-demand and scheduled hit the same data — how do you avoid generating it twice?* · *(EM bar)* *What's your SLA for the morning deadline, and what do you do the morning it's about to be missed?*

**Weak / Strong / Exceptional:** *Weak* — one endpoint that builds and streams the dataset on every request; no versioning; no failure handling. *Strong* — separates generation from delivery, versions outputs, uses object storage + signed links for big files, has a scheduler with retries and per-partner access control. *Exceptional* — designs the "missed deadline" runbook, discusses correctness/checksums, reasons about cost of storing many versions, and treats auditability and consent/compliance as first-class.

### Problem C — Trending content in real time (Top-K)

**Read aloud:** *"Design a system that shows the current top 10 trending shows across the country in near real time, based on a high-volume stream of 'someone started watching X' events."*

**If they ask (give these):** millions of view-start events per minute; "trending" can be a simple count over a recent sliding window (say, the last 10 minutes); top 10 nationally, refreshed every few seconds; approximate ranking is acceptable; read traffic for the leaderboard is very high (it's shown to many users/dashboards).

**A good design contains (listen for):** ingest into a **durable stream**; counting over a **sliding time window**; an awareness that keeping an exact count for *every* show is feasible but finding top-K cheaply benefits from a **heap / "top-K" structure**, and that at extreme cardinality an **approximate frequency technique** (they may say "count-min sketch") controls memory; **pre-computing** the leaderboard and serving it from a **cache** rather than recomputing per read (because reads vastly outnumber writes); and handling the window "rolling forward" so old events age out. The core senior insight: *the read path and write path have wildly different volumes, so you precompute on write and serve a cached result on read.*

**Probes (pick 2–3):** *Reads are far more frequent than writes — how does that shape the design?* (precompute + cache) · *How do counts "expire" as the window slides?* · *Memory blows up if you track every title — what do you do?* (approximate counting / only track heavy hitters) · *Two app servers each have partial counts — how do you get one global top 10?* (aggregation) · *How fresh is the leaderboard, really, and is that okay?* · *(EM bar)* *How would you test that the ranking is correct, and detect if it silently goes stale?*

**Weak / Strong / Exceptional:** *Weak* — recomputes a global sort over all events on every page view. *Strong* — durable stream, windowed counting, precomputed leaderboard served from cache, sensible aggregation of partial counts. *Exceptional* — reasons explicitly about read/write asymmetry and memory, chooses approximate vs exact deliberately with justification, and addresses staleness detection and freshness SLA.

## 7 · What to score

Grade these nine dimensions on the 1–4 scale (§3). The sheet on the last page mirrors them.

- **Requirements & scoping** — turned a vague prompt into explicit functional + non-functional needs; stated what's out of scope.
- **Estimation** — produced a few numbers that *changed a decision*, not decoration.
- **High-level design** — a clean, end-to-end happy path you could follow.
- **Technical depth** — went two levels deep when probed, instead of stalling at the first layer.
- **Trade-off reasoning** — named alternatives and justified the choice *for this problem*.
- **Operations, reliability & cost** — failure modes, monitoring, SLAs, cost — *the manager bar.*
- **Communication & collaboration** — narrated clearly, drew few well-labeled boxes, built *with* you.
- **Handling ambiguity & pushback** — treated challenges as gifts, adapted calmly, didn't get defensive.
- **Leadership signal (EM)** — prioritized MVP-first, sequenced the risky work, zoomed out to team/business impact.

> **💡 THE EM BAR · What pushes a Senior-EM candidate from "good" to "strong"**
>
> For an Engineering Manager loop, raw technical depth is necessary but not sufficient. The differentiators are **judgment** (picks the boringly correct option and *says why*, not the flashiest), **operational ownership** (talks naturally about failure, on-call, SLAs, and cost — the things they'd actually own), **prioritization** (scopes an MVP and sequences the riskiest work first), and **influence** (designs *with* you, invites and absorbs your input). Leveling turns mostly on **scope and comfort with ambiguity**: a senior IC designs a well-specified piece cleanly; a strong EM imposes structure on a large vague problem, reasons about the whole system *and how it's run*, and naturally frames the multi-team, multi-quarter path. If they spontaneously say things like *"I'd have the team de-risk this with a load test before committing,"* that's the altitude you're listening for.

## 8 · The debrief (the most valuable ten minutes)

This is what a mock has that the real interview doesn't — use it well. Stop on time, drop the interviewer persona, and run a tight feedback loop:

1. **Ask first (2 min).** "How do you think that went? What would you change?" Self-assessment accuracy is itself a strong signal — and it primes them to hear feedback.
2. **Give the headline (1 min).** Lead with the one thing that most affected the outcome — usually scoping, time management, or depth — not a laundry list.
3. **Two strengths, two improvements (4 min).** Be specific and quote moments: "When I asked why a queue, you immediately gave the spike-buffering reason — that landed well," or "You spent eight minutes on the database schema and never got to failure handling." Concrete beats abstract.
4. **One drill (1 min).** Hand them a single thing to practice next: a tighter opening, a habit of reading every estimate back into a decision, or finishing the breadth before any depth.
5. **Share the sheet.** The filled grading sheet is a gift — give it to them.

> **✅ GREEN FLAGS / RED FLAGS · A quick gut check**
>
> **Green:** scopes before drawing · states assumptions out loud · numbers drive decisions · draws few, well-labeled boxes · says "let me start simple and evolve it" · treats your probe as a gift and adapts · talks about how it fails and what it costs · summarizes crisply at the end. **Red:** starts drawing in the first 60 seconds · name-drops technologies without justifying them · goes silent for long stretches · over-builds for imaginary scale · gets defensive when challenged · disappears down one rabbit hole · runs out of time with the design half-done · can't go a second level deep on anything.

## Grading sheet — System Design Mock

*Candidate:* _______________     *Date:* ____________     *Problem:* A / B / C

*Scale:* **1** below bar · **2** approaching · **3** at bar (hire) · **4** above bar

| # | Dimension | 1 | 2 | 3 | 4 | Notes / quotes |
|---|---|:-:|:-:|:-:|:-:|---|
| 1 | Requirements & scoping | ☐ | ☐ | ☐ | ☐ | |
| 2 | Estimation (drives decisions) | ☐ | ☐ | ☐ | ☐ | |
| 3 | High-level design | ☐ | ☐ | ☐ | ☐ | |
| 4 | Technical depth (deep dive) | ☐ | ☐ | ☐ | ☐ | |
| 5 | Trade-off reasoning | ☐ | ☐ | ☐ | ☐ | |
| 6 | Operations / reliability / cost | ☐ | ☐ | ☐ | ☐ | |
| 7 | Communication & collaboration | ☐ | ☐ | ☐ | ☐ | |
| 8 | Handling ambiguity & pushback | ☐ | ☐ | ☐ | ☐ | |
| 9 | Leadership signal (EM) | ☐ | ☐ | ☐ | ☐ | |

**How much help did they need?**  ☐ none · ☐ light nudges · ☐ frequent steering · ☐ led throughout

**Time management:**  ☐ finished cleanly · ☐ rushed the end · ☐ ran out of time

**Top 2 strengths (with a quote):**

________________________________________________

________________________________________________

**Top 2 things to improve:**

________________________________________________

________________________________________________

**One drill for next time:** ____________________________________

**Overall:**  ☐ strong hire · ☐ hire · ☐ mixed / lean no · ☐ no hire     **Apparent level:**  ☐ senior IC · ☐ EM bar · ☐ senior EM
