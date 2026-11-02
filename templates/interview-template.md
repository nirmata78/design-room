# Interview Workspace

> **This is your whiteboard.** Write in §1–§9. Talk to the interviewer in chat.
> When a section is ready for the interviewer to look at, say so in chat — *"requirements are up"*,
> *"done"*, *"look at §4"*. They read only what the current phase covers.
>
> **§10 belongs to the interviewer. Do not write there.** They will not write anywhere else.
>
> Rough, ugly and fast beats neat and slow. Nobody scores your ASCII art. Half-sentences are fine;
> the interviewer is scoring your reasoning, and most of your reasoning happens in chat.

---

## 0 · Session Control

*The interviewer fills this in at setup. Read it; don't edit it — except to add assumptions you've
been granted mid-round.*

| | |
|---|---|
| **Session** | *certifying · practice (help: light / medium / heavy)* |
| **Question** | *(bank ID + title)* |
| **Company / level** | *(e.g. Google · `staff`)* |
| **Kind / domain** | |
| **Attempt** | *(N on this question)* |
| **Mode / format / pace / difficulty** | |
| **Started** | |
| **Budget** | *(certifying: live clock — `scripts/clock.py watch --notify` in a second terminal · practice: no clock)* |

**The prompt (verbatim):**

> *(the interviewer writes it here after reading it aloud)*

**Established facts — the interviewer's answers to your clarifying questions:**

| You asked | Answer given |
|---|---|
| | |

---

## 1 · Requirements & Scope

*Budget: ~12 min. Signal the gate when §1.1–§1.4 are populated.*

### 1.1 Functional requirements

*What the system must do. Verbs. Number them so you can refer to them later.*

1.
2.
3.

### 1.2 Non-functional requirements

*Attach a number to every line you can. A non-functional requirement without a number is a wish.*

| Property | Target | Why this number |
|---|---|---|
| Scale (users / QPS / events/s) | | |
| Latency (p50 / p99) | | |
| Availability | | |
| Consistency | | |
| Durability / retention | | |
| Cost ceiling | | |
| Compliance / residency | | |

### 1.3 Explicitly out of scope

*Do not leave this empty. Cutting scope out loud is one of the cheapest points in the round, and an
empty box here is the single most common thing the interviewer writes down as a negative.*

-
-

### 1.4 Assumptions

*Everything you're taking as true that nobody told you. Revisit these aloud whenever the interviewer
changes the premise.*

-
-

---

## 2 · Estimation

*Budget: ~9 min. Orders of magnitude, not decimals.*

| Quantity | Working | Result |
|---|---|---|
| | | |
| | | |

### 2.1 What these numbers mean for the design

**This subsection is the entire point of the phase.** A number that doesn't change a decision is
decoration. Write the implication next to each figure — *"X/s means one node can't absorb it, so…"*

-
-

*Number kit, if you need it: 1 day ≈ 10⁵ s · QPS × 10⁵ ≈ per-day volume · 1 KB × 1M/s = 1 GB/s ·
DC round trip ≈ 0.5 ms · cross-region RTT ≈ 70–150 ms · SSD read ≈ 100 µs · memory read ≈ 100 ns ·
columnar compression ≈ 6× · 99.9 % ≈ 8.8 h/yr, 99.99 % ≈ 53 min/yr. Full kit:
`guides/playbook.md` §11.*

---

## 3 · API & Data Model

*Budget: part of the ~18 min design phase. Skipping this is how a design gets a vague middle.*

### 3.1 Core API / contracts

```
POST   /...
GET    /...
```

### 3.2 Entities & keys

| Entity | Key | Fields that matter | Store |
|---|---|---|---|
| | | | |

**Partition key choice and why:**

---

## 4 · High-Level Design

*Budget: ~18 min including §3. Few boxes. Label every arrow with its protocol. Then be ready to walk
one request end to end — you will be asked, every time.*

**Drawing in Excalidraw?** Export PNG with *Embed scene* ticked into `board/` at the repo root
(`board/hld-v1.png`, then `-v2` after changes), or paste a screenshot into chat. Write the current one
here so the interviewer knows which to read — and keep §4.1 as text.

**Current diagram:** *(e.g. `board/hld-v1.png`, or "ASCII below")*

```
       ┌──────────┐
       │  client  │
       └────┬─────┘
            │ HTTPS
            ▼

```

### 4.1 End-to-end happy path

*One request or event, client to response, numbered steps. Write it — narrating it from a diagram
you haven't traced is where designs fall apart.*

1.
2.
3.

### 4.2 What's v1 and what's later

| Component | v1? | Why / trigger to add it |
|---|---|---|
| | | |

---

## 5 · Deep Dives

*Budget: ~22 min. The interviewer drives this phase and picks the targets. This is where most of
your score is decided.*

### 5.1 Deep dive: *(component)*

**The problem:**

**Options considered:**

| Option | Pros | Cons |
|---|---|---|
| | | |

**Chosen, and why for *this* problem:**

### 5.2 Deep dive: *(component)*

### 5.3 Curveball

*A new requirement or failure lands here mid-phase. What changed, what didn't, and what it cost.*

---

## 6 · Failure Modes, Reliability & Operations

*Budget: part of the ~9 min wrap. **This is the manager bar** — for an EM loop it carries as much
weight as the architecture. Don't leave it to the last two minutes.*

| What fails | Blast radius | Detection | Mitigation | Recovery |
|---|---|---|---|---|
| | | | | |

### 6.1 SLOs and alerting

| SLI | SLO | Alert on | Page or ticket? |
|---|---|---|---|
| | | | |

### 6.2 What breaks first as this grows

### 6.3 On-call reality

*What wakes someone at 3 a.m., what the runbook says, and what you'd automate first.*

---

## 7 · Cost

*Rough monthly shape, and the biggest line item. "I don't know" is a worse answer than a defensible
order of magnitude.*

| Line item | Rough driver | Rough monthly |
|---|---|---|
| | | |

**Biggest cost, and the lever that moves it:**

---

## 8 · Summary — four sentences

*You will be asked for this at the end, under time pressure. Write it here when you get there.*

1.
2.
3.
4.

**What I traded away, and what I'm least comfortable with:**

---

## 9 · Scratch

*Anything. Dead ends, arithmetic, half-thoughts. Nothing here is scored — but the interviewer may
read it, and a visible discarded option with a reason attached is a positive signal, not a negative.*

---

## 10 · Interviewer Notes — DO NOT EDIT

*Appended live by the interviewer. Timestamps come from the shell, not from guesswork.*

```
HH:MM:SS  elapsed  event
```
