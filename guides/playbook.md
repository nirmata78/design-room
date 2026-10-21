# The System Design Interview — Process, Behavior & Tactics

*A non-technical playbook for senior-engineer and Engineering Manager loops · Google · Meta · Amazon · Microsoft · Netflix*

## How to use this playbook

The [question bank](../Question-Bank.md) and the cue sheets teach you *what to design*. This one teaches you **how to behave in the room** so the design actually lands: how the round is structured, what the interviewer is really grading, how to manage the clock and the whiteboard, how to collaborate under pressure, how to recover when you stumble, and the specific nuances at **Google and Meta**. It is deliberately non-technical — read it once end-to-end, then re-skim the panels and the §9 phrasebook the morning of each interview, and pair it with at least three timed, spoken mock rounds.

A blunt truth worth internalizing first: most candidates who fail a system design round do **not** fail because they lacked a piece of technical knowledge. They fail because they didn't scope the problem, didn't manage the clock, went quiet, over-built, or got defensive when challenged. Those are all *behaviors*, and they are all trainable. This playbook is the training.

> **💡 THE ONE IDEA · A system design interview is a simulation of working with you**
>
> The interviewer is not collecting a perfect architecture — they have seen the "right" answer dozens of times and don't need yours. They are imagining **what it's like to be in a design review with you for the next five years.** Do you bring structure to an ambiguous problem? Do you make assumptions explicit instead of silently guessing? Do you reason about trade-offs and cost, or just name technologies? Do you listen and adapt, or steamroll? Are you calm and curious when probed, or brittle? Every behavioral choice you make is evidence for that single question. Optimize for *being a great design partner*, not for being right — and you will usually also end up being right.

## 1 · The shape of the round

A system design interview is **45–60 minutes**, typically structured as: a one-line problem statement, a long open middle where *you* drive, and an interviewer who probes with "what if…" pressure-tests to find the edges of your understanding. The most important and most counter-intuitive expectation is that **you lead**. The interviewer is a collaborator and a steering wheel, not a quizmaster who will feed you the next question. Waiting to be asked, or treating it like an oral exam, is the single most common way capable people underperform.

| Phase | Share of time | What you're doing |
|---|---|---|
| Requirements & scope | ~15 % | Clarify functional + non-functional; cut scope out loud |
| Estimation | ~10–15 % | Back-of-envelope numbers that *drive* the design |
| High-level design | ~25 % | One clean diagram; walk the end-to-end happy path |
| Deep dives | ~30 % | Go deep where the interviewer steers; show trade-offs |
| Wrap-up / failure & scale | ~10 % | Bottlenecks, SLAs, cost; summarize and state next steps |

The **medium** varies and you should confirm it with your recruiter in advance: an in-person whiteboard, a shared virtual whiteboard (Excalidraw, Miro), or a collaborative doc / coding tool (CoderPad, Google Docs). Each rewards slightly different habits — a physical whiteboard rewards economical drawing and planned use of space; a virtual canvas lets you move boxes around but tempts you into fiddling; a doc rewards crisp bulleted structure over diagrams. Practice in whatever medium you'll actually use.

> **ℹ️ FORMAT NOTES · What differs by company**
>
> **Google** (L6/L7 EM): often a first-principles design with a strong push on **scalability, the data structures behind your boxes, and rigorous trade-off justification**; expect repeated probing on *why*, not just *what*. **Meta** (E6/E7 EM): fast-paced and **product-/scale-driven** ("design X for a billion users"); the interviewer drives hard and expects you to make **decisive choices** and keep momentum. At both the system-design round is one part of a **full EM loop** (see §10) that also tests people-leadership and your track record.

## 2 · What the interviewer is actually scoring

Behind the friendly conversation is a rubric, and the interviewer is taking notes against specific signals. They usually grade variations of the following — and for each, it helps to know what a *weak* versus a *strong* version looks like, because the gap between them is where your score is decided.

- **Problem framing.** *Weak:* starts drawing within a minute. *Strong:* spends the opening minutes turning a vague prompt into an explicit, bounded set of functional and non-functional requirements, and states what is out of scope.
- **Structured thinking.** *Weak:* a stream-of-consciousness tour of technologies. *Strong:* a visible method the interviewer can follow — requirements → estimate → contracts → diagram → deep dive.
- **Estimation.** *Weak:* "it'll be a lot of traffic." *Strong:* a couple of back-of-envelope numbers that *change a decision* ("3M events/sec means a single ingest node can't cope, so…").
- **Technical depth.** *Weak:* names a component but can't go deeper. *Strong:* can descend two levels when probed (how the log partitions, how the cache invalidates, how a failure is detected).
- **Trade-off reasoning.** *Weak:* picks a technology with no justification. *Strong:* names two or three viable options, states the axis (latency vs cost vs complexity), and justifies the choice *for this problem*.
- **Communication.** *Weak:* mumbles, draws a tangle, goes silent. *Strong:* narrates continuously, draws few well-labeled boxes, checks for understanding.
- **Handling ambiguity & pushback.** *Weak:* defends a wrong choice or freezes. *Strong:* treats a challenge as a gift, adapts visibly, stays calm.

The *same* answer is scored differently by level — the axis is almost always **scope and ambiguity**, not raw knowledge:

| Dimension | L5 / E5 (senior) | L6 / E6 (staff · EM) | L7 / E7 (senior staff · sr. EM) |
|---|---|---|---|
| Problem scope | a well-specified component | the whole system + its operations | business / org trade-offs, multi-team |
| Ambiguity | needs the problem framed for them | frames a vague, large problem | reframes the problem and the goal |
| Trade-offs | knows the options | justifies the choice for this case | weighs cost, org, and time-horizon |
| Failure / ops | mentions it when asked | designs for it proactively | sets the reliability & cost strategy |

> **💡 EM LENS · The extra bar for managers, and how the same answer reads at different levels**
>
> For an EM loop, raw IC depth is necessary but not sufficient. They additionally look for **judgment** (you pick the *boringly correct* option and justify it, not the flashiest), **risk & operational thinking** (failure modes, on-call, SLAs, cost — what you'd actually own), **prioritization** (you scope and sequence, MVP-first), and **influence & collaboration** (you build *with* the interviewer). Leveling hinges largely on **scope and ambiguity tolerance**: a senior IC (L5/E5) designs a well-specified component cleanly; an L6/E6 imposes structure on a vague, large problem and reasons about the whole system and its operations; an L7/E7 additionally frames the business/organizational trade-offs and the multi-team, multi-quarter path. Signal the higher altitude by occasionally zooming out: *"I'd have the team de-risk this assumption with a load test before we commit the design, and I'd sequence delivery so the riskiest integration ships first."*

## 3 · The minute-by-minute run of show

Internalize a reliable script you can run on autopilot, so your working memory is free for the genuinely hard parts of the problem rather than for *what do I do next*.

1. **Restate & align (1 min).** "So we're designing X for these users, optimizing primarily for Y — is that right?" Confirm the target before you invest a single box.
2. **Announce your agenda (30 s).** "I'll clarify requirements, size it, define the key contracts, sketch the architecture, then deep-dive wherever you'd like." Structure is itself a score, and this hands the interviewer an early chance to redirect you.
3. **Requirements (5–7 min).** List functional needs, then non-functional ones (scale, latency, availability, consistency, cost, compliance). **Explicitly cut scope** — say what you're deferring and why.
4. **Estimation (5–7 min).** A few numbers — QPS, data volume, bandwidth — and, crucially, read each one back into a design implication.
5. **APIs & data model (5 min).** The core contracts and entities. This anchors everything downstream and prevents a vague middle.
6. **High-level design (10 min).** Draw the boxes, label every arrow with its protocol, and **walk one request end to end** so the interviewer sees the system breathe.
7. **Deep dives (12–15 min).** Let the interviewer steer; if they don't, pick the component you think is riskiest. Present options, choose one, justify it.
8. **Failure, scale, cost, wrap (5 min).** Bottlenecks, what breaks at 10×, the SLA/observability story, then a crisp 30-second summary and explicit next steps.

A good opening sounds like this, delivered calmly in the first two minutes: *"Before I design anything — who are the users and what are we optimizing for? … Got it. Let me write the functional requirements here and the non-functional ones here, call out what I'm treating as out of scope, then do a quick capacity estimate because I expect the numbers to drive the architecture."* That is the entire difference between looking senior and looking nervous.

> **ℹ️ EXAMPLE · What a strong first ten minutes sounds like (abbreviated)**
>
> **You:** "Quick check — we're designing the viewing-event pipeline for, say, 50M devices, optimizing for never losing an event and seconds-fresh metrics. Yes? Then feeds to partners are the output?"  **Interviewer:** "Right."  **You:** "Functional: ingest, real-time metrics, batch segments, delivery. Non-functional: ~3M events/sec peak, zero loss, 99.95% ingest, GDPR. Out of scope for now: the ACR matching itself and billing — fair?"  **Interviewer:** "Sure."  **You:** "Let me size it — 3M/s × 500 bytes ≈ 1.5 GB/s, ~43 TB/day raw. That number alone tells me a single ingest service can't cope and I can't afford to drop a burst, so I'll put a durable, partitioned log right after a stateless ingest tier. Let me draw that and walk one event through."  *— Notice: aligned, scoped, estimated, and the estimate justified the first architectural decision, all before drawing a second box.*

> **✅ BEST PRACTICE · Manage the clock visibly**
>
> Glance at the time at each phase boundary and **narrate the transition**: *"I've got the high-level architecture; with about 15 minutes left, let me deep-dive the part I think is riskiest — unless you'd prefer another area."* This demonstrates time-management (a core EM skill) and again hands the interviewer the wheel. Running out of time still stuck in requirements is the classic way strong candidates lose; budgeting the clock out loud is the cheapest insurance against it.

## 4 · Communication & whiteboard behavior

The design in your head is worth nothing the interviewer cannot follow. In this round, **communication is not a tax on the real work — it *is* the work being evaluated.**

- **Think out loud, always.** Your spoken reasoning is the primary signal. Narrate the options you consider *and* the ones you discard and why: *"I considered a read-through cache here, but the read volume doesn't justify the complexity yet, so I'll skip it and revisit if we hit a hot-key problem."*
- **Drive the structure.** You own the agenda and the pace. Move yourself to the next phase; don't wait to be prompted.
- **Diagram with discipline.** Few, well-labeled boxes; arrows that carry the protocol and, where useful, the throughput. Leave whitespace so you can extend the picture. Use a consistent visual vocabulary — a rectangle is a service, a cylinder a datastore, a different shape for a queue — and a [C4](https://c4model.com/)-style Context → Container → Component progression, which reads cleanly and is fast to draw on any surface.
- **Layer your answer.** Headline first, then detail: *"At a high level it's a durable log sitting between ingest and processing — let me now expand each side."* This lets the interviewer follow at their preferred depth.
- **Make assumptions explicit and visible.** Write them in a corner of the board and revisit them aloud whenever the interviewer changes the premise. Unstated assumptions are the most common source of a design that quietly drifts away from what was asked.

> **⚠️ PITFALL · Going silent while you think**
>
> Long silences read as "stuck" even when you're thinking productively. If you need a moment, **say what you're chewing on**: *"Let me weigh two storage options for a few seconds — I'm comparing write throughput against query flexibility."* Narrated thinking is collaborative and scoreable; silent thinking is invisible and is usually scored as a gap. The same applies to drawing: talk while you draw, never draw in wordless silence for a minute.

## 5 · Working *with* the interviewer

They are simulating a teammate, so treat the round as a collaboration, not a monologue and not an exam. The candidates who pass consistently make the interviewer think *"I'd happily review designs with this person every week."*

- **Hints are gifts.** If they nudge — "what happens when that node dies?" — they are steering you toward where the points are. Follow the thread immediately; don't defend the path you were on.
- **Disagree well.** It is fine, even good, to push back — but with reasoning and humility: *"I'd lean the other way because of cost at this scale, but I see the latency argument — what's driving your preference?"* Curiosity beats ego every time.
- **Check in at forks.** *"I can go deeper on the data model or on failure handling — which would be more useful to you?"* This shows prioritization and reads the room.
- **Receive feedback live and gracefully.** If they point out a flaw, acknowledge it, fix it, and move on: *"Good catch — that breaks my partitioning assumption; let me re-key by user instead."* Defensiveness is one of the strongest negative signals an interviewer can record; visible, ego-free self-correction is one of the strongest positives, because it is exactly what a senior engineer does in a real review.

> **✅ BEST PRACTICE · Make the interviewer feel like your tech lead, not your examiner**
>
> Invite input, integrate it visibly on the board, and credit good prompts out loud (*"that's a good point — it changes my caching choice"*). Collaboration here is not a soft nicety; for an EM it is a **core competency under direct test**, because leading technical discussions and making other engineers better is most of the job. An interviewer who feels heard and useful is an interviewer writing "strong collaborator" in their notes.

## 6 · Company-specific nuance

The universal advice above wins most of the points; these are the accents that distinguish a "good" performance from a "great" one at each company.

> **ℹ️ GOOGLE · First-principles rigor and scale**
>
> Expect a strong, repeated push on **scalability, the data structures and algorithms behind your boxes, and rigorous trade-off justification** — interviewers ask *why* until they hit bedrock. Be **CAP/PACELC-honest**, comfortable discussing replication, consistency models, and quorum/consensus at a mechanism level, and precise with capacity math. Leveling (L6/L7) turns on **scope and ambiguity**: demonstrate that you can take a deliberately under-specified, large problem and impose structure on it. Cite mechanisms and properties, not brand names — "a consensus-backed strongly-consistent store" lands better than just "I'd use Spanner."

> **ℹ️ META · Move fast, decide, scale for billions**
>
> Fast-paced and **product-/scale-driven** — "design X for a billion users." The interviewer drives hard and values **momentum and decisiveness**: make a defensible choice and move, rather than enumerating every option forever. Be ready for **massive scale** mechanics — sharding, fan-out on write vs read, multi-layer caching, hot keys, back-of-envelope at billions — and to **iterate quickly** when challenged. Impact and pragmatism are prized; show you can ship a defensible v1 and then articulate how you'd harden and scale it.

## 7 · Common failure modes & how to recover

Almost every poor outcome traces to one of the patterns below. Knowing them by name lets you catch yourself mid-round and correct — which, done visibly, actually *raises* your score rather than lowering it.

| Failure mode | Fix in the moment |
|---|---|
| **Jumping to a solution** before scoping | Stop, list requirements, cut scope, *then* design |
| **No numbers** | Pause, do one estimate, tie it to a concrete decision |
| **Rabbit-holing** one component | "Let me zoom back out to the whole system and return here if time allows" |
| **Buzzword salad** (tech with no why) | For each choice, state the axis and the trade-off |
| **Going silent** | Narrate what you're weighing right now |
| **Over-engineering** | "The simplest thing that meets the SLA is X; I'd add Y only when we hit Z" |
| **Defensive under pushback** | "Good point" → adjust on the board → continue |
| **Designing only the happy path** | Walk one failure: node dies, network partitions, queue backs up |
| **Running out of time** | Time-box; cover breadth before depth; summarize early |

The biggest single one is **scope and time mismanagement**: a candidate spends 25 minutes lovingly clarifying and estimating, draws half an architecture, and never reaches a deep dive — so the interviewer has no depth signal to score. Budget the clock (§3), and when in doubt move forward; you can always return to add detail.

> **✅ RECOVERY · One bad turn does not fail the loop**
>
> If you realize a choice was wrong, **say so and correct it** — interviewers reward self-correction because it is exactly what a strong engineer does in real reviews. If your mind blanks, return to the **method**: requirements → estimate → contracts → diagram → deep dive. The script carries you when intuition stalls, and narrating "let me step back to my framework" is itself a senior move, not an admission of weakness.

## 8 · Preparation & day-of logistics

**A four-week ramp (compress as needed).** *Weeks 1–2:* read one canonical reference end-to-end (see Further reading) so the building blocks — logs, caches, partitioning, replication, consistency, queues — are fluent, and skim 8–10 classic designs. *Week 3:* run **timed, spoken mock rounds** (45–60 min), ideally with a peer who plays a probing interviewer; practicing silently hides your single biggest weakness, which is narration. *Week 4:* drill weak spots, rehearse your past-systems stories (below), and do lighter mocks to stay warm without burning out.

**Build a reusable toolkit.** Memorize the §3 run-of-show until it's automatic. Keep a small **numbers kit**: powers of ten, "per-second × 10⁵ ≈ per-day," typical latencies (memory vs SSD vs network vs cross-region), and storage/throughput rules of thumb. Prepare **two or three systems you have actually built** to discuss in depth — EM loops almost always include a "tell me about a system you designed, the hardest trade-off, and what you'd change now" round, and a concrete, owned story outscores any textbook design.

**Day of.** Confirm the **format and medium** with your recruiter and practice in it. Have water, a quiet space, and for remote rounds a backup connection and a charged device. Open by **restating the problem and announcing your agenda** — the calmest possible first 90 seconds, and the moment you set the tone as someone who leads.

> **💡 EM LENS · The behavioral half is not optional**
>
> EM loops pair system design with **leadership/behavioral** interviews, and these often carry equal or greater weight. Prepare crisp **STAR** stories (Situation, Task, Action, Result — with real metrics) on: leading through ambiguity, a production incident you owned end-to-end, a hard technical decision and its trade-off, influencing without authority, growing or coaching an engineer, managing conflict, and balancing operational/KTLO load against product delivery — whatever the job description names or implies. Your design round and your stories should reinforce the *same* picture of judgment, ownership, and calm under pressure.

## 9 · Phrasebook & flag table

> **✅ PHRASEBOOK · Sentences that signal seniority**
>
> - *"Before I design, let me state my assumptions and cut scope."*
> - *"The numbers say ~3M events/sec, so a single service can't absorb that — which is why I'd put a durable log here."*
> - *"There are two reasonable options; the axis is latency vs cost. For this product I'd pick X because…"*
> - *"The failure mode here is Y; I'd mitigate with Z and alert on the leading indicator."*
> - *"That's a good prompt — it changes my earlier choice; let me adjust on the board."*
> - *"With about 10 minutes left, I'll prioritize the riskiest area unless you'd prefer another."*
> - *"The boring, correct answer is X; I'd only add complexity when we actually hit Z."*
> - *"Let me walk one request end to end so we can see where it could fail."*

| Green flags (do) | Red flags (avoid) |
|---|---|
| Clarify & scope first | Start drawing immediately |
| Numbers drive decisions | Hand-wave the scale |
| Name trade-offs, then pick one | List tech with no reasoning |
| Narrate continuously | Long silences |
| Invite & integrate input | Steamroll the interviewer |
| Self-correct gracefully | Get defensive under probing |
| Walk failure paths | Only design the happy path |
| Manage the clock | Run out of time mid-scope |
| Tie design to ops & cost (EM) | Ignore failure, SLA, money |

## 10 · The rest of the EM loop

The system design round is one interview among several, and a strong loop is internally consistent — the same person should show up in every room. A typical EM loop includes some combination of:

- **System / technical design** (this playbook) — can you architect and reason about trade-offs.
- **Deep dive on past work** — talk through a real system you designed and operated; expect drilling on the hardest decision and what you'd change.
- **People management** — coaching, performance management, growing engineers, handling a low performer or a conflict; bring specific, outcome-bearing stories.
- **Project / execution** — how you plan, prioritize, de-risk, and deliver under constraints; how you balance KTLO/operational load with roadmap.
- **Cross-functional collaboration & influence** — working with Product, Data Science, and partner teams; driving alignment without authority.
- **Hiring / org** (especially second-line) — how you build and structure teams, set standards, and grow other managers.

> **💡 EM LENS · Make every round tell one story**
>
> Decide, before the loop, on the **two or three leadership themes** you want every interviewer to walk away with — for a data-platform role, that might be *operational rigor*, *pragmatic technical judgment*, and *growing teams that own reliability*. Then choose stories and design choices that reinforce those themes across rounds. Interviewers compare notes in a debrief; a consistent, evidence-backed narrative is far more persuasive than seven unrelated good answers.

## 11 · Estimation toolkit (numbers worth memorizing)

You will not be graded on memorizing these, but having them ready lets you produce a defensible estimate in seconds instead of stalling — and a fast, correct estimate is one of the clearest senior signals. Round hard; orders of magnitude are the point.

**Latency ladder** (rounded; "how long does X take?"):

| Operation | Order of magnitude |
|---|---|
| L1 cache / branch | ~1 ns |
| Main-memory read | ~100 ns |
| SSD random read | ~100 µs |
| Datacenter network round trip | ~0.5 ms |
| Read 1 MB over 10 Gbps network | ~1 ms |
| Disk (HDD) seek | ~5–10 ms |
| Same-continent internet RTT | ~10–50 ms |
| Cross-region RTT (e.g. US↔EU) | ~70–150 ms |

**Throughput & capacity rules of thumb:**

- 1 day ≈ 86,400 ≈ 10⁵ s; 1 month ≈ 2.5 × 10⁶ s. So **QPS × 10⁵ ≈ per-day volume.**
- Sizes: char ≈ 1 B; UUID = 16 B; timestamp = 8 B; a small record ≈ 100 B–1 KB.
- 1 KB × 1M/s = 1 GB/s. Keep the unit chain visible so a factor-of-1000 slip is obvious.
- **Read-heavy** → add caches and read replicas; **write-heavy** → shard/partition and put a log in front.
- Columnar compression on analytics data ≈ 5–10×; assume ~6× when sizing a lake.

**Availability — what the nines cost in downtime per year:**

| SLA | Downtime / year |
|---|---|
| 99.9 % ("three nines") | ~8.8 hours |
| 99.95 % | ~4.4 hours |
| 99.99 % ("four nines") | ~53 minutes |
| 99.999 % ("five nines") | ~5 minutes |

> **✅ BEST PRACTICE · Questions worth asking before you estimate**
>
> "How many users / devices, and how active are they?" · "Read-heavy or write-heavy?" · "What's the freshness / latency SLA?" · "What's the retention — days, or years?" · "Average payload size?" Each answer pins one variable in the estimate; asking them shows you size systems from requirements rather than from thin air.

## Further reading

- **Interview craft**: [Hello Interview — System Design](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction); [System Design Primer](https://github.com/donnemartin/system-design-primer); [ByteByteGo](https://bytebytego.com/); [Grokking the System Design Interview](https://www.designgurus.io/course/grokking-the-system-design-interview).
- **EM-specific**: [Hello Interview — Engineering Manager](https://www.hellointerview.com/); levels & expectations at [levels.fyi](https://www.levels.fyi/); [The Manager's Path (Fournier)](https://www.oreilly.com/library/view/the-managers-path/9781491973882/); [Staff Engineer (Larson)](https://staffeng.com/).
- **Foundations**: Kleppmann, [*Designing Data-Intensive Applications*](https://dataintensive.net); [Google SRE Book](https://sre.google/books/); [The C4 model](https://c4model.com/).
- **Company prep**: [Google — how we hire](https://careers.google.com/how-we-hire/); [Meta engineering interview prep](https://www.metacareers.com/life/preparing-for-your-software-engineering-interview-at-meta/).
- **Behavioral**: the STAR method; rehearse stories on incidents, trade-offs, ambiguity, coaching, conflict, and the KTLO-versus-delivery balance, each with a concrete, measurable result.
