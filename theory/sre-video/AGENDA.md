# SRE course · agenda

*Site Reliability Engineering, then and now.* Sixteen narrated episodes that retell the Google SRE book chapter by chapter, add what
changed since 2016, and end every episode with interview probes. Built to `plans/00-shared-rules-and-sources.md` and
`plans/02-concepts-and-building-blocks-course.md` (the SRE book is its "must read" source for the observability, overload, reliability,
scheduling and manager-layer parts, so this course is the way to take those chapters by ear before the course parts that assume them).

**Size now:** 16 episodes · about **2 h 55 min** estimated (0.43 s a word plus pauses) · 24,300 spoken words · 395 slides ·
33 new diagrams · 79 key-thesis inserts · 50 probe drills. **Nothing has been rendered to video or audio.** The estimate is the
builder's; the real length is known only after synthesis.

## 1 · Build order, by what the plans need first

| Priority | Why | Episodes |
|---|---|---|
| **1** | Chapters that plan 02 §2.3 lists as **must read** (SRE book ch. 3, 4, 6, 19, 20, 21, 22, 23, 24, 26) | 2 · 4 · 9 · 10 · 11 · 12 · 13 |
| **2** | "Read when a part needs more" (ch. 2, 17, 25, 27), plus release engineering, which part 16 leans on | 1 · 3 · 5 · 8 · 14 |
| **3** | Manager layer and the close. Marked **AUX** on screen where it is the EM layer (ep. 15), optional in a Staff round | 6 · 7 · 15 · 16 |

Render and review Priority 1 first. Episode 10 (overload and cascading failure) is the one to look at before any other.

## 2 · Episodes

Runtimes are estimates. Slides are the builder's count (a probe drill is two slides). *Thesis* is the number of slower-voice key lines.

| Ep | Title | Book chapters | Priority | Slides | Words | Est. min | Thesis | Probes | Diagrams |
|---|---|---|---|---|---|---|---|---|---|
| 1 | What SRE is, and the world it runs in | Preface, 1, 2 | 2 | 22 | 1,275 | 9 | 4 | 3 | 2 |
| 2 | Risk, SLIs, SLOs and error budgets | 3, 4, App. A | **1** | 28 | 1,740 | 12 | 5 | 3 | 1 |
| 3 | Toil and automation | 5, 7 | 2 | 21 | 1,288 | 9 | 4 | 3 | 2 |
| 4 | Monitoring and alerting | 6, 10 | **1** | 28 | 1,667 | 12 | 5 | 3 | 2 |
| 5 | Release engineering and simplicity | 8, 9 | 2 | 27 | 1,492 | 11 | 7 | 3 | 1 |
| 6 | On-call and effective troubleshooting | 11, 12 | 3 | 23 | 1,350 | 10 | 4 | 3 | 1 |
| 7 | Emergencies, incidents and postmortems | 13, 14, 15, 16, App. C, D | 3 | 26 | 1,527 | 11 | 6 | 3 | 2 |
| 8 | Testing for reliability, and software engineering in SRE | 17, 18 | 2 | 22 | 1,319 | 10 | 3 | 3 | 2 |
| 9 | Load balancing, at the edge and inside the datacenter | 19, 20 | **1** | 25 | 1,586 | 11 | 6 | 3 | 3 |
| 10 | Overload and cascading failure | 21, 22 | **1** | 31 | 2,043 | 15 | 6 | 4 | 5 |
| 11 | Distributed consensus for critical state | 23 | **1** | 28 | 1,811 | 13 | 5 | 4 | 3 |
| 12 | Distributed cron and data pipelines | 24, 25 | **1** | 26 | 1,612 | 12 | 6 | 3 | 3 |
| 13 | Data integrity: what you read is what you wrote | 26 | **1** | 24 | 1,502 | 11 | 5 | 3 | 2 |
| 14 | Reliable product launches at scale | 27, App. E | 2 | 21 | 1,290 | 9 | 4 | 3 | 1 |
| 15 | People: training, interrupts, overload and engagement | 28, 29, 30, 31, 32, App. F | 3 · AUX | 24 | 1,474 | 11 | 5 | 3 | 1 |
| 16 | Lessons from other industries, and the close | 33, 34, App. B | 3 | 19 | 1,325 | 10 | 4 | 3 | 2 |
| | **Total** | | | | **24,301** | **≈175** | **79** | **50** | **33** |

### What the viewer can do afterwards

| Ep | After the episode you can… |
|---|---|
| 1 | Say what SRE is in two sentences, give the three numbers behind the operations cap, and name the role each Google-internal system plays and its open analogue |
| 2 | Compute what a target allows in minutes, set an error budget policy, and derive a burn-rate alert from a budget share |
| 3 | Judge a task against the six properties of toil, place automation on the five-step ladder, and list five guardrails that bound its blast radius |
| 4 | Choose symptom-based pages, say what the four golden signals are, compute detection time as a sum, and answer "p99 across ten thousand hosts" |
| 5 | Describe a staged, reversible rollout, size a canary to the smallest regression you must catch, and explain hermetic builds |
| 6 | Run a hypothesis-driven troubleshooting loop, and say what makes an on-call rota sustainable, with numbers |
| 7 | Staff an incident (commander, operations, communications, planning), write a blameless postmortem with owned actions, and say when to declare |
| 8 | Explain what tests measure, why recovery paths must be exercised, and what intent-based capacity planning buys |
| 9 | Draw the four layers of load balancing, explain why random subsets are uneven (63 to 121 percent), and describe a lame-duck drain |
| 10 | Draw goodput collapse, compute retry amplification (27 against 1.1), use the client-side throttle formula, and break a metastable loop |
| 11 | Explain why failover needs consensus, size and place a replica group, and replace a replica in the right order |
| 12 | Explain skip-or-double for scheduled work, and make a pipeline step safe to run twice with leases and unique outputs |
| 13 | Explain why replication is not a backup, name the three layers of defence, and compute restore time against an objective |
| 14 | Use the nine-area launch checklist, compute headroom as Z over Z minus one, and tier launches by risk |
| 15 | Plan an on-call learning path, protect focus, rescue an overloaded team in three phases, and pick an engagement model |
| 16 | Give the one-sentence version of each topic, and translate the book's ideas to a model-serving system |

## 3 · Coverage of the book

Everything in the book is either taught, referenced, or deliberately left out. The left-out list is the honest part.

| Book part | Chapters | Taught in |
|---|---|---|
| Front matter | Foreword, Preface | Episode 1 (the argument; no separate episode) |
| I Introduction | 1, 2 | 1 |
| II Principles | 3, 4 · 5 · 6 · 7 · 8 · 9 | 2 · 3 · 4 · 3 · 5 · 5 |
| III Practices | 10 · 11 · 12 · 13, 14, 15, 16 · 17 · 18 · 19, 20 · 21, 22 · 23 · 24, 25 · 26 · 27 | 4 · 6 · 6 · 7 · 8 · 8 · 9 · 10 · 11 · 12 · 13 · 14 |
| IV Management | 28, 29, 30, 31, 32 | 15 |
| V Conclusions | 33, 34 | 16 |
| Appendices | A availability table · B best practices · C incident state doc · D example postmortem · E launch checklist · F production meeting minutes | 2 · 16 · 7 (pointed to) · 7 (pointed to) · 14 (pointed to) · 15 (pointed to) |

**Condensed or left out, on purpose**

- Ch. 2: hardware detail beyond the vocabulary. Ch. 7: the second case study and the long history. Ch. 18: the Auxon case study is told in outline only.
- Consensus: the operator's view, plus a working tour of **Paxos** (roles, two phases, the three rules, a worked example, Multi-Paxos, Raft compared). Plan 02 part 3 goes deeper.
- Ch. 25: the book's own workflow system is described by its two correctness mechanisms (leases, unique outputs), not its full design.
- Ch. 26: the long tape-restore narratives are summarised in two sentences each. Ch. 31: the two collaboration case studies are not told.
- Ch. 34 (the conclusion) is a few lines inside episode 16. The bibliography is not used.
- The Workbook is used only where it completes a book chapter (burn-rate alerting, canary statistics). See §6 for the episodes it would justify.

## 4 · Shape of every episode

1. **Title slide** with the thesis, spoken by the coach, then a **key line** in the slower voice.
2. **The story**: a failure or contrast that makes the stakes concrete.
3. **Assumed reading**: which book chapters this retells, and where the design-room course picks the topic up.
4. **Sections**, each built as: *mechanism* (a diagram or a table) → *one level down* → *the alternative and the price* → *the trap* → **the line to say** (slower voice).
5. **Then and now**: what changed since the book, marked with its own panel colour.
6. **Probe drills**: three or four interviewer questions, a strong answer on screen, and the candidate answer spoken (two more voices).
7. **Where this shows up**: design-room course parts, the next episodes, the chapters and papers to read.

**Voice variety.** Four voices alternate: the coach (narration), the key-line voice (slower, 79 lines), the interviewer and the candidate
(the drills). No stretch of narrator-only speech runs longer than about three minutes (checked by script). Section-end thesis lines are
the places a viewer can pause and say the sentence aloud.

## 5 · Alignment with the plans

| Plan 02 part | Supported by episode | How |
|---|---|---|
| 3 Consensus · 4 Coordination services | 11 | The operator's view; assumes the algorithms part |
| 5 Replication · 7 Storage engines | 13 | Replication is not recovery; restore time |
| 10 Logs, queues, streams | 12 | Pipelines, leases, idempotency |
| 11 Networking, the edge | 9 | Four layers of load balancing; Maglev |
| 12 Rate limiting and overload control | 10 | The chapter 21 retelling, with the formulas |
| 13 Reliability patterns | 10, 13, 14 | Retries, cascades, metastable failure, headroom, restore |
| 14 Observability and time-series storage | 2, 4 | SLI, SLO, error budget, golden signals, burn rate, detection time |
| 15 Scheduling and control planes | 1, 3, 12 | Borg vocabulary, reconciliation, cron launch records |
| 16 Operating and evolving systems, the manager layer | 3, 5, 7, 8, 14, 15 | Rollout, kill switches, testing, readiness, on-call, engagement (AUX) |

Wording follows the course where they overlap (lease, fencing token, goodput, burn rate). The reverse direction is not done yet:
none of the course sources cite this series. Whether to add "see SRE episode N" to the course's *Read next* slides is a decision for you.

## 6 · Possible additions (not built)

| Candidate | Why | Source |
|---|---|---|
| Implementing SLOs, in depth | The workbook's worked example, SLI specification vs implementation, stakeholder agreement | Workbook ch. 2–3 |
| Alerting on SLOs | The six strategies compared, with the precision/recall/detection-time numbers | Workbook ch. 5 |
| A worked design in Google's style | Plan 02 says to read workbook ch. 12 twice | Workbook ch. 12 |
| Canarying, configuration, overload recovery | Part 16 is read-first on ch. 16 | Workbook ch. 14, 15, 16, 17 |
| SRE for AI systems, longer | Episode 16 has only a short section | New, outside the books |
