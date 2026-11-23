---
title: "SD-94 · A Distributed Denylist System"
subtitle: "A reference solution for a system design round at the Staff bar: versioned lists, a local check, a bound on staleness, and the release discipline that keeps one wrong rule from becoming an outage"
author: "design-room reference solution · practise with the simulator first"
date: "12 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: gblueink
urlcolor: gblueink
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-94`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its reference-solution video. It shows how a strong Staff
candidate (L6/L7) runs the round: what to say, what to draw, and **when**. It adds the **why** behind
every line, so you can defend each choice when the interviewer asks *"why?"*, *"what is that?"* or
*"what happens when it breaks?"*.

**The document has three layers, and you will read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what a denylist is, what a node
   experiences, what one ban does from the moment it is typed to the moment it is enforced, and where
   the load lands. There is no interview script in it, only understanding.
2. **Part II, the round, stage by stage.** This is what you do in the room. Each stage has the words to
   say, what to draw, and boxes that explain every term. The seven **challenges** of the video are
   Stage 6, and each one goes further here than the video can.
3. **Part III, the internals.** How versioned distribution, Bloom filters, prefix tries, staged
   rollout and the stale policy actually work, at the depth a round reaches when you name a mechanism
   and the interviewer asks how it works.

**The coloured boxes:**

::: {.key title="Top-3 number"}
One of the back-of-the-envelope numbers worth computing out loud in the round. In a real interview you
have time for two or three calculations, not ten.
:::

::: why
Explains a term or a decision in plain words. This is for you, not for the interviewer.
:::

> Words you can say in the room, nearly verbatim.

::: warn
A trap: something weak candidates do, or a claim that breaks under a follow-up question.
:::

::: load
What this part of the system sees at peak, with numbers.
:::

**Practise in three passes.** (1) Read Part I and Part II once, end to end. (2) Close the document and
run the [simulator](https://github.com/nirmata78/design-room) cold:
`Read CLAUDE.md. Mock me: SD-94, Google, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Do not memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and any planning assumption (the burst rate, how many
bytes a change takes, the poll interval, how long a canary bakes, one hit rate) is labelled as one:
*given*, *illustrative*, *initial target* or *derived*. None of them is a measurement. They are not any
company's real figures, and this is not any company's actual design. Costs are in engineer-months, not
money, because a loaded salary depends on a market.

**The prompt as the interviewer reads it:**
*"Design a distributed system that stops requests from banned sources, such as IP addresses, from being
served on every one of our servers."*

::: {.key title="The one-sentence insight to land by minute 12"}
**The check must be *local* and the list cannot be.** So the design is the distance between them: a
*version* every node can verify, a stated *bound* on how stale a node may be, and the discipline of a
*release*, because the pipe that delivers a ban in ten seconds delivers a mistake in ten seconds.
:::

::: why
**Why is this the insight?** Most candidates draw a table of banned addresses, a cache and a lookup,
and stop. The lookup is the easy part: a sorted array or a hash set, in memory, in under a microsecond.
What makes the question hard is everything around it. A hundred thousand servers must all learn about a
change quickly, in order, without trusting arrival order, and without a mistake in the list becoming a
global outage. There are also two ways to be wrong: a ban that is missing, and a block that should not
exist. The question tests whether you see both, and whether you say the staleness bound and the failure
policy out loud.
:::

\newpage

# Part I: The system in pictures

## Vocabulary you need first

The terms below appear throughout. They are grouped by *where they live*, because that is how you
should draw them.

**On the policy side (what is on the list, and why)**

| Term | Plain meaning |
|---|---|
| **List** | A named set of rules, such as the abuse list or a legal list. Each list has an owner and a signed staleness bound. |
| **Rule** | One entry: a key (an address or a range), an action (deny, challenge or log only), a reason, a source and an optional expiry. |
| **Key kind** | What the key is: a single address, a range written as a C-I-D-R block, later a user id. A field, so a new kind does not change the pipeline. |
| **Allowlist range** | A range that must never be blocked: the company's own addresses, key partners, health checks. It wins over any deny. |
| **Change set** | One published batch of rule changes, validated and approved as a unit. |

**In the pipeline (how a change becomes a version)**

| Term | Plain meaning |
|---|---|
| **Version** | A number that increases by one for every committed change set. One writer assigns it, so there is exactly one order. |
| **Snapshot** | The whole list at one version. Immutable. About 40 MB for 10 million addresses. |
| **Delta** | The changes between two versions. Immutable. Small: about 11 MB for two hours at the burst rate. |
| **Checksum chain** | Each version's checksum covers its own content and the checksum before it, so a node can verify before it applies. |
| **Manifest** | The small answer to "what is current?": the current version, where the delta window starts, references to the artifacts, a checksum, and the kill flag. About 100 bytes. |
| **Origin, relay** | The origin stores the artifacts. Relays (regional, then zone) cache them and fan them out. |

**On a node (the part that decides)**

| Term | Plain meaning |
|---|---|
| **Agent** | A library inside each serving process. It holds the list, applies updates and answers `Check` in process. |
| **Structure** | A sorted array or hash set for single keys, a prefix trie for ranges, held in memory. |
| **Atomic swap** | Build the new structure beside the old one, verify, then replace one pointer. |
| **Last known good** | The most recent verified list, on disk, so a restart with no network still enforces. |
| **Stale** | A node whose list is older than its bound. Stale is **not** open: it keeps enforcing what it has. |

**In operations (how you know)**

| Term | Plain meaning |
|---|---|
| **Version skew** | The share of nodes not on the current version. The propagation SLI is its complement. |
| **Gate** | An automatic check between rollout stages, usually the block rate per node against its own baseline. |
| **Kill flag** | A field in the manifest that tells every node to stop applying newer versions. It rides the lightest possible channel. |
| **Probe** | A synthetic banned key, published on a schedule, with a request sent through the real path to see it denied. |
| **Decision log** | A sample of verdicts, each with its rule and its list version, so an auditor can answer "why was X served on day D". |

::: why
**Why this grouping?** A denylist has two speeds. The check is microseconds and local. The list moves
over a slow, partly broken path. Keeping "policy", "pipeline", "node" and "operations" apart is what lets
you say, for each failure, which part owns it, and who gets paged.
:::

## What a node experiences

Walk through the life of one serving node, with no jargon, in order.

1. **Start.** The node boots and loads its last known good list from disk. If it has no copy and no
   network, it cannot serve a list, so it stays out of rotation until it bootstraps.
2. **Bootstrap.** It asks the manifest, learns the current version, and takes a snapshot. It verifies,
   builds the structure, and starts answering `Check`.
3. **Steady state.** Every ten seconds, with a little jitter, it asks the manifest. Almost always the
   answer is "you are current". That is the whole exchange.
4. **A change arrives.** A push says a new version exists, or the next poll shows it. The node fetches
   the delta, verifies the chain, builds a new structure beside the old one, swaps one pointer, writes
   the result to disk and reports the version it now runs.
5. **A request arrives.** The agent normalises the address, checks the allowlist first, then the exact
   key, then the longest-prefix range. The verdict carries the rule and the version. A sample goes to the
   decision log, off the hot path.
6. **Trouble.** The relay is unreachable. The node keeps enforcing its list and its age grows. Past the
   bound for that list, its action fires: alert, or ask the balancer to drain it.
7. **A bad update.** The block rate on the node jumps right after a swap. Its local circuit breaker
   reverts to the previous version, reports, and pages.

::: {.say}
The node never waits for the network to answer a request. It asks for updates on its own schedule, and
when it cannot get them it keeps doing the last correct thing it knew.
:::

![The life of one list version. A version is built, staged, rolled out, and either becomes current or is halted. A rollback is never an undo: it publishes the old content as a new, higher version.](diagrams/sd94-version-states.pdf){width=78%}

## The same story as a version's states

The figure above is the life of one version. Three details to keep in mind:

- **Compiled** is not **published**. A version exists in the origin before any node is allowed to see it.
  The rollout stage decides who may fetch it.
- **Halted** is a state, not a delete. A halted version stays in the history, and the audit still shows
  that it existed.
- **Rolled back** produces a *new* version. If the version number could move backwards, a node that
  already applied the bad one would ignore the fix.

## Why one pipe carries both a ban and a mistake

The hook of the whole question is a typo. An operator means a small range and types a wide one.

![The same pipe delivers a ban and a mistake in the same 18 seconds. Top: no gates, every node serves the mistake and 8 percent of requests are denied until someone acts. Bottom: a canary sees it first, the gate trips, and a rollback lands as a new version.](diagrams/video-badpush.pdf){width=94%}

Nothing failed. The compiler did what it was told, the relays carried it, the nodes applied it. The
pipeline that is built to land an urgent ban fast lands a mistake just as fast. This is why a
denylist gets the same discipline as a binary: validation, an allowlist that always wins, a staged
rollout gated on a number, a kill flag, and a rollback that is a new version.

![Freshness against blast radius. The same slider carries an urgent ban, a routine push, and an ungated push. The owner picks the position, per push.](diagrams/video-tension.pdf){width=92%}

## One ban, second by second

A single address ban, published at time zero, with push and a ten-second poll. All times are
**initial targets**, not measurements.

| Time (s) | Where | What happens |
|---|---|---|
| 0.0 | Policy tool | Operator publishes `203.0.113.0/28`, deny, ticket 7712 |
| 0.2 | Ingest | Normalised, size limit and allowlist checked, no approval needed |
| 0.5 | Rule store | One transaction: rules written, version 8,361,004 taken, audit written |
| 3.0 | Compiler | Snapshot and delta built, checksum chained to 8,361,003 |
| 5.0 | Origin, regional relays | Artifacts fan out to 20 regions |
| 7.0 | Zone relays | Cached for 500 nodes each |
| 8.0 | Push | Nodes learn that 8,361,004 exists |
| 8.2 | Node | Manifest asked with `have = 8,361,003`; the delta comes back |
| 8.6 | Node | Chain verified, new structure built beside the old |
| 9.0 | Node | One pointer swapped; version reported on the next poll |

About nine seconds with push. With no push, the node waits for its next poll, up to ten seconds more:
**eighteen seconds worst case against a thirty-second target**.

![The propagation budget as one bar: compile 3, origin to regional 2, regional to zone 2, poll wait up to 10, verify and apply 1. Eighteen used, twelve spare.](diagrams/video-budget.pdf){width=95%}

## Where the load lands

![Load map. The request path (right) never touches the network. The distribution path (left to middle) carries about 1.5 KB a second of deltas and 10,000 manifest polls a second across the fleet. Every figure is derived in Stage 2.](diagrams/sd94-load-map.pdf){width=90%}

::: load
**The request path.** A million requests a second across a hundred thousand nodes: ten a second per
node, each answered from memory in under ten microseconds, with no network call.
:::

::: load
**The distribution path.** Deltas at the burst rate are about 1.5 KB a second. The polls are the
largest figure on the page: ten thousand manifest polls a second across the fleet, about a hundred
bytes each, one megabyte a second in total, and fifty a second on each zone relay.
:::

::: why
**Where must it be strictly correct?** Two places: the version order in the rule store, and the node's
apply step. Everything between them (relays, caches, pushes) may be late, duplicated or out of order,
because the node verifies and merges by version. A candidate who protects the middle with exactly-once
machinery has paid for the wrong guarantee.
:::

\newpage
# Part II: The round, stage by stage

**The clock** (a 75-minute round at the simulator's `typing-adjusted` pace; spoken rounds run about 50 minutes):

| Minutes | Stage | On the whiteboard |
|---|---|---|
| 0:00 to 0:12 | **Stage 1** Clarify requirements | Requirements list and an "out of scope" box |
| 0:12 to 0:21 | **Stage 2** Back-of-the-envelope (three numbers, maybe four) | Four lines of arithmetic |
| 0:21 to 0:33 | **Stage 3** API and data model | Five calls, one apply function |
| 0:33 to 0:51 | **Stage 4** High-level design in three versions, with the walk-through | One baseline, redrawn three times |
| 0:51 to 1:13 | **Stage 6** Deep dives, with **Stage 7** requirements as they arrive | Marks on the baseline |
| Last 10 minutes | **Stages 8 and 9** Failure, SLOs, cost | Short list |
| When asked | **Stage 10** The EM layer (auxiliary at Staff) | Releases, people, months |

Stage 5 (technology) has no slot. The interviewer can ask it at any time, and you answer inline.

**At the Staff bar you pick the deep dives.** Do not wait to be asked. Say which two you would go into and
why: *the bad push and the stale node, because that is where the guarantees live.*

# Stage 1: Clarify requirements

Ask **six questions, not fifteen**. Each one changes the design, so say why you are asking. The answers
below come from the simulator's cue sheet.

| # | You ask | The interviewer answers | What it changes |
|---|---|---|---|
| 1 | Who owns the list, and who calls the check? | A policy team (security, legal) owns the content. The platform team owns the mechanism. The check runs on every serving node, on the request path: about 100,000 nodes in 20 regions. | Two owners, so the contract between them must be a number. The check is on a hot path, so it is local. |
| 2 | What is banned? | Addresses first: single IPv4 and IPv6 addresses and ranges. A second key type, a user id, will come. | Ranges need longest-prefix matching. The key kind is a field. |
| 3 | How big, how fast does it change? | 10 million entries today, perhaps 100 million. About 5 changes a second, 50 in a burst. 1 million requests a second at peak. | Read everywhere, write rarely: the shape of the design. |
| 4 | How fast must a ban take effect? | Within 30 seconds for 99.9 percent of nodes. Removals the same. | Rules out a once-a-minute timer; allows a ten-second poll. About 100 nodes may be late. |
| 5 | What if a node cannot get updates? | "That is yours to propose. I will decide who signs it." | The second half of the question: the staleness policy, challenge 4. |
| 6 | Where does the list come from? | An internal tool; one list mirrored from an external authority that publishes a bulk file. A variant has only a slow lookup API. | Two sources, two speeds. The bulk file joins the same pipeline. |

::: why
**Why ask question 5 out loud?** Because failing open and failing closed are both bad for a denylist,
and the choice is not an engineering one. The policy owner decides how much risk a late ban is worth.
Candidates who invent a default silently lose the point; candidates who ask who signs it have found the
owner.
:::

::: why
**Why "an address is not a person"?** Many users share one address behind a carrier-grade translator. One
wrong range blocks thousands of legitimate people. It is the reason for the allowlist, for treating a
removal as carefully as an addition, and for an action that can be *challenge* instead of *deny*.
:::

**Functional requirements** (each gets a numbered flow in Stage 4):

- **FR1 Publish** a change: add or remove a key or range, with a reason, a source and an optional expiry;
  validated and audited.
- **FR2 Distribute** every change to every node within the bound; a node that was offline catches up on its
  own.
- **FR3 Enforce**: a verdict for every request, inside the request path, in microseconds.
- **FR4 Inspect and explain**: which version each node runs and how old; why was key X denied or served
  on day D.
- **FR5 Roll back and stop**: halt a rollout, kill a list, revert; an emergency fast path; audited.

**Non-functional requirements** (all initial targets, not measurements):

- Check p99 under 10 microseconds, in process, with **no network call** on the request path.
- 99.9 percent of nodes on a new version within 30 seconds of publish; the other 0.1 percent are listed
  with their age, not silent.
- A node keeps enforcing its last known list through any outage of the distribution plane.
- Staleness is bounded and signed: each list has a maximum age and an action when it is exceeded.
- Every decision carries the list version. An auditor can reconstruct a verdict.
- A bad push is caught by the pipeline, not by customers.

**Polling semantics, stated once.** Every ten seconds a node asks the **manifest** (about 100 bytes). If it
is current, that is the whole exchange. If it is behind and inside the delta window, it fetches
**deltas**. It fetches a **full snapshot only to bootstrap**, after falling outside the window, or when
verification fails. It never downloads the list on a routine poll.

::: warn
**The misreading to avoid.** "Pull every ten seconds" can be heard as "download the file every ten
seconds". With a 40 MB snapshot and 100,000 nodes that is 400 GB a second. Say the manifest, the
delta and the snapshot rule aloud the first time you say "poll".
:::

**Scope.** *In:* addresses and ranges (both families), a second key type as an extension, an allowlist,
internal and mirrored sources, staged rollout, audit, an operator console. *Out, and say so:* detecting
abuse (a different question, SD-43), rate limiting (SD-25), absorbing a volumetric attack (upstream
scrubbing), content rules inside requests (a web firewall), an appeals product (an owner and a workflow,
named and not drawn).

> "The core is four things: a versioned list, a distribution path that can be verified, a local check,
> and a release discipline."

# Stage 2: Back-of-the-envelope

## How to do estimates in an interview

Four lines of arithmetic, each ending in a decision. State the input, do the multiplication, say what
it means, and say what it changes. **Label every number**: given, illustrative, derived or initial
target. In 90 seconds you can say the first three below, and mention the fourth.

::: {.key title="Number 1 · Why the check is local"}
**Arithmetic.** 1,000,000 requests a second over 100,000 nodes is 10 a second per node. A remote check
adds about 1 ms to every request and puts 1 M lookups a second on one service. Availability multiplies:
99.99 percent times 99.99 percent is about 99.98 percent.

**What it means.** The reason to stay local is latency and independence, not throughput.

**Changes the design.** The check has no network call.

**Say.** "A million requests over a hundred thousand nodes is ten a second per node, so CPU is not the
argument. The argument is that a remote check puts the list service in every request's availability."
:::

::: {.key title="Number 2 · Does the list fit"}
**Arithmetic.** 10 M IPv4 addresses at 4 bytes is **40 MB** as a sorted array (a hash set is about 120
MB). 2 M ranges in a prefix trie at about 40 bytes is **80 MB**. 100 M IPv6 prefixes at 17 bytes is
**1.7 GB**, against a budget of 512 MB; a filter at 10 bits an entry is **125 MB**.

**What it means.** Ten million fits easily on every node. A hundred million does not.

**Changes the design.** Exact and local now; a filter in front with an exact tier behind it for the
large case (challenge 5).

**Say.** "Forty megabytes of sorted array, so no filter at ten million. At a hundred million IPv6, one
point seven gigabytes is over my budget, so a filter in front and an exact tier behind."
:::

::: {.key title="Number 3 · Deltas and the window"}
**Arithmetic.** 50 changes a second at about 30 bytes is **1.5 KB a second**. Two hours offline: 7,200 s
times 50 times 30 B is about **11 MB**, against a 40 MB snapshot. Break-even: 40 MB divided by 30 B is
1.33 M changes, about **7.4 hours** at the burst rate. Keep **24 hours** of deltas: 86,400 times 50 times
30 B is about 130 MB.

**What it means.** A node that was offline takes small deltas, not a whole list.

**Changes the design.** A delta window of 24 hours; beyond it, a snapshot.

**Say.** "Deltas are tiny, so catching up is cheap. I keep a day of them, and a node older than that takes
a snapshot."
:::

## The full table, row by row

| Number | Arithmetic | Label | Decision it drives |
|---|---|---|---|
| Rate per node | 1 M / s ÷ 100,000 nodes = 10 / s | given | The check is not a CPU problem |
| A remote check | ~1 ms on every request; 1 M lookups / s; 99.98 % availability | illustrative | Rules out a lookup per request |
| One lookup | log2(10 M) is about 24 comparisons, 0.3 to 1 us | illustrative, **to be measured** | The check fits 10 us with room to spare |
| Exact IPv4 | 10 M × 4 B = 40 MB; hash set about 120 MB | derived | The whole list fits on every node |
| Ranges | 2 M × ~40 B = 80 MB trie | illustrative | Longest-prefix match is a different structure |
| 100 M IPv6 | 100 M × 17 B = 1.7 GB exact; filter 125 MB | derived | Challenge 5 |
| Change volume | 50 / s × 30 B = 1.5 KB / s; two hours = 11 MB | illustrative | Deltas win over snapshots |
| Window | break-even 7.4 h; keep 24 h = 130 MB | illustrative | Retention of the delta log |
| Fan-out | 100,000 × 40 MB = 4 TB direct; through 20 + 200 relays the origin serves 800 MB | derived | The tree is not optional |
| Poll load | 100,000 ÷ 10 s = 10,000 manifest polls / s; ~1 MB / s; 50 / s per zone relay | derived | A 10 s poll is cheap enough to be the backstop |
| Propagation | compile 3 + origin to regional 2 + regional to zone 2 + poll wait up to 10 + apply 1 = 18 s, spare 12 | initial target | Pull alone meets 30 s; a 60 s poll would not (68 s) |
| Swap memory | 2 × 40 MB = 80 MB briefly | derived | Atomic swap, not in-place edits |
| External API | 20,000 first-seen / s against 100 calls / s = 200x over; 8.6 M lookups a day against ~50 M addresses = 17 % | illustrative | Cannot be the path; challenge 6 |
| Blast radius | all nodes within ~18 s; 8 % blocked is visible in one 10 s window on 5,000 nodes; staged push about 10 min | illustrative | Gates; speed is a setting |
| SLO as a budget | 0.1 % of 100,000 = 100 nodes may be late | initial target | The SLI is the share on the current version |

::: why
**Why show the pull-only number?** A pull-only design with a ten-second poll already meets thirty
seconds (18 s worst case). Push adds margin (9 s) but is not required. That is an EM-grade point: the
first release can be the simpler one. A sixty-second poll would not meet the target at all, which is why
the poll interval is the number to defend.
:::

::: warn
**Do not over-claim the lookup time.** "Under a microsecond" is an illustrative figure for a binary
search with cache misses. Say you would measure it. The decision (do not optimise the lookup) holds
anywhere between 100 ns and 5 microseconds.
:::

# Stage 3: API and data

## The API

Every call carries a tag: which requirement it serves, and which entity it reads or writes.

![Conceptual model in Chen notation. A key has at most one live state per list, and the version of its last change decides it. That is what makes merging safe.](diagrams/video-erd-chen.pdf){width=96%}

**PublishChange** (FR1, writes ChangeSet and Rule)

```
PublishChange {
  list: "abuse",
  ops: [{ op: "add", key: "203.0.113.0/28", kind: "range", action: "deny",
          reason: "ticket 7712", source: "policy-tool", expiresAt: "2026-12-01" }],
  idempotencyKey: "c4f9..."
}
-> { changeSetId: "cs-90113", version: 8361004, stage: 0 }
```

::: why
**Field by field.** `op` is add or remove. `kind` says whether the key is an address or a range, so the
compiler picks the right structure. `action` is deny, challenge or log-only, so a rule can be introduced in
shadow mode. `source` lets the precedence rules decide between a manual entry and a feed. `expiresAt` is
turned into a remove by the compiler, not left for nodes to evaluate against their own clocks. The
`idempotencyKey` makes a retried publish return the same version, never a second one.
:::

**Manifest, delta, snapshot** (FR2, reads Version)

```
GET /manifest?list=abuse&have=8361000
-> { current: 8361004, minDelta: 8274600, deltaRef: "d/8361000-8361004",
     snapshotRef: "s/8361004", checksum: "9ab3...", killed: false }
GET /delta?list=abuse&from=8361000       (immutable, content-addressed)
GET /snapshot/8361004                    (immutable, content-addressed)
```

**Check** (FR3, in process, not a network API)

```
verdict = agent.check(sourceAddress)
-> { verdict: DENY | ALLOW | CHALLENGE, ruleId: 4411, version: 8361004 }
order: normalise -> allowlist -> exact key -> longest-prefix range -> default ALLOW
```

**ReportApplied and Explain** (FR4)

```
ReportApplied { node: "z7-0412", list: "abuse", version: 8361004, ageMs: 1800 }
Explain { key: "203.0.113.9", at: "2026-11-03T14:05Z" }
-> { verdict: DENY, ruleId: 4411, version: 8360990, source: "policy-tool" }
```

**Rollout, Halt, Rollback, KillSwitch** (FR5)

```
Rollout { version: 8361004, stage: 1 }      Halt { version: 8361004, reason: "gate" }
Rollback { to: 8360990 }  -> publishes that content as version 8361005
KillSwitch { list: "abuse", on: true }      (a field in the manifest)
```

::: warn
**A rollback that reuses a version number would be ignored.** A node that already applied 8,361,004 will
not apply "8,360,990 again". Versions only go forward. A rollback is a new version whose content is an
older one.
:::

**What the kill flag does, precisely.** The video says "kill flag". The precise meaning, which the first
draft glosses over: a node that sees `killed: true` **stops applying versions newer than the one it
runs** and reports `killed`. It does not delete its list. The flag stops a bad push from spreading; the
rollback is what repairs nodes that already applied it. If you need to *remove* the bad version from
already-updated nodes quickly, publish the rollback and let the normal path carry it.

## The data model

![Physical model. A removed key stays as a tombstone for the delta window. The version number is assigned in the same transaction as the rules. On the node, two copies exist during a swap.](diagrams/video-erd-physical.pdf){width=96%}

```sql
CREATE TABLE rule (
  list_id text, key_bytes bytea, kind text, action text,
  added_version bigint, removed_version bigint NULL,
  reason text, source text, expires_at timestamptz NULL,
  PRIMARY KEY (list_id, key_bytes));
CREATE TABLE version (
  list_id text, n bigint, checksum bytea, prev_checksum bytea,
  snapshot_ref text, delta_ref text, stage text, created_at timestamptz,
  PRIMARY KEY (list_id, n));
```

::: why
**Tombstones.** A removed key keeps its row, with `removed_version`, for the delta window (24 hours).
Without it, a late delta that still says "add" could resurrect a ban the operator removed. A node older
than the window takes a snapshot, which has no tombstones, so nothing is resurrected.
:::

**Stores, and whether you can lose them.**

| Store | Holds | If lost |
|---|---|---|
| Rule store | rules, versions, audit | **Must not be lost or rewound**: version numbers would be reused and nodes would ignore them. After a rebuild, start with a higher epoch |
| Origin and relays | snapshots, deltas, manifests | Regenerated from the rule store; relays refill from the origin |
| Node memory | the live structure | Rebuilt from disk, then from a snapshot |
| Node disk | last known good | A node with none and no network cannot serve a list: keep it out of rotation until it bootstraps |

### One race the first draft glosses over: version order against commit order

"One transaction assigns the next version" sounds safe and is not, if two change sets commit
concurrently. Transaction A takes version 101, transaction B takes 102, B commits first, and the
compiler reads the table: it sees 102 and not 101. If it publishes 102 and 101 commits a moment
later, nodes that applied 102 will treat 101 as old and **skip it**. A ban is lost.

The fix is cheap, because publishes are rare (50 a second at the burst rate). Serialise the version
assignment: a per-list counter row, updated inside the transaction (`UPDATE list_counter SET n = n + 1
RETURNING n`), takes a row lock, so transactions on one list commit in version order. The compiler also
**publishes only contiguous committed versions**, and a gap is an alarm, not something to step over.

### The apply step, and the digest the chain needs

```
apply(change c):
  cur = state[c.key]                    // last version that touched this key
  if c.version <= cur.version: return   // late or duplicate: no-op
  state[c.key] = { c.version, c.op, c.action }
```

The video says each checksum "covers its content and the one before". That proves the artifacts form a
sequence. It does not by itself prove the node's **resulting list** is right, because a node applies
a *combined* delta (`d/8361000-8361004`), and it only holds the checksum of its own current version.
The robust form carries two things in the manifest: the chained checksum of the artifact, and a **state
digest** of the list at the target version (an order-independent set hash, such as the XOR or sum of
hashes of the entries, which can be updated incrementally). After applying, the node recomputes the digest
and compares. A mismatch discards the result and falls back to the snapshot.

# Stage 4: High-level design

Draw the baseline once, then redraw it three times. Each version is introduced by the objection to the one
before.

## Version 1: the simplest thing that works

![V1. A policy tool writes one list file to object storage. Each node downloads it every minute, builds a set, swaps it in and checks locally.](diagrams/video-base-v1.pdf){width=92%}

For a short list that rarely changes this might be enough. **The objection:** every minute a hundred
thousand nodes pull 40 MB each (4 TB from one place); a node can read a file while it is still being
written and load half a list without knowing; a bad file reaches every node; and there is no version, so
"what was in force at two o'clock?" has no answer.

## Version 2: versions, a rule store, and a relay tree

![V2. A rule store assigns versions. A compiler writes immutable snapshots and deltas with chained checksums to the origin. A relay tree carries them. Nodes poll the manifest every ten seconds; a push says a version exists; the delta comes back.](diagrams/video-base-v2.pdf){width=92%}

Now a node can say what it holds, verify what it gets, catch up by deltas, and never download the list
on a routine poll. **The objection:** one bad version reaches every node in eighteen seconds, nothing
checks the content, and a node that cannot update does something nobody chose.

**The three arrows between a relay and a node.** *Poll* (every ten seconds): the node asks the manifest
with its version; it always works. *Push* (optional): the relay says "version N exists" and carries no
data; the node then runs the same manifest step at once. *Delta* (when behind): the small, immutable file.
Push shortens the wait; poll guarantees arrival; the node's logic is the same for both.

## Version 3: safe enforcement

![V3. A controller reads every node's applied version and age and gates each stage of a rollout. On the node: an atomic swap, last known good on disk, and a staleness bound with an action.](diagrams/video-base-v3.pdf){width=92%}

The controller (dashed purple arrow back from the nodes) reads applied versions and ages, and gates a
rollout through the origin. Ingest now validates against an allowlist and size limits. **What V3 leaves
open** is the list of challenges: a node two hours behind, changes out of order, a plausible but wrong
rule, no control plane, a list that does not fit, a slow authority, and a silent failure.

## The numbered flows, one per functional requirement

**FR1 Publish.** (1) The operator sends `PublishChange`. (2) Ingest normalises every key into a canonical
form, so the same range always looks the same. (3) Validate: size limits, a cap on how much address space
one change may cover, and the allowlist. (4) Above a threshold, a second person approves. (5) One
transaction writes the rules and takes the next version. (6) An audit event is written. The compiler picks
it up from there.

![FR1, publish. Normalise, validate, approve, then one transaction assigns the next version.](diagrams/video-flow-fr1.pdf){width=90%}

**FR2 Distribute.** (1) The origin fans artifacts out through the relay tree. (2) A push says a new
version exists. (3) The node polls the manifest with its version. (4) The delta comes back. The node
verifies, builds beside, swaps, writes to disk and reports. A node that never hears the push takes the
same steps at its next poll, and so does a node that was offline.

![FR2, distribute. A poll asks the manifest only. Deltas when behind inside the window; a snapshot only to bootstrap.](diagrams/video-flow-fr2.pdf){width=90%}

**FR3 Enforce.** (1) A request arrives with a source address. (2) The agent normalises it and checks the
allowlist, then the exact key, then the longest-prefix range. No network call. (3) The verdict returns with
the rule and the version; a sample goes to the log off the hot path.

![FR3, enforce. Allowlist first, then exact, then longest prefix. The verdict carries the rule version.](diagrams/video-flow-fr3.pdf){width=90%}

**FR4 Inspect and explain.** (1) Every poll carries the version applied and its age. (2) The controller
computes version skew and the list of late nodes. (3) Metrics turn it into the propagation SLI per
region. For audit, `Explain` joins a sampled decision to the rule history by version.

![FR4, inspect and explain. Each node reports version and age; decisions are sampled with their version.](diagrams/video-flow-fr4.pdf){width=90%}

**FR5 Roll back and stop.** (1) An operator or a gate halts the stage, so regions not yet reached never
receive the bad version. (2) The controller tells the origin. A rollback publishes the old content as a
new, higher version. The kill flag is the lighter lever, a field in the manifest read on the next poll.

![FR5, roll back and stop. Halt the stage, flip the kill flag, or publish the old content as a higher version.](diagrams/video-flow-fr5.pdf){width=90%}

## The C4 views and the sequences

![C4 level 1. Policy owns the content; platform owns the pipe; the propagation target is the contract between them.](diagrams/video-c4-context.pdf){width=92%}

![C4 level 2. Inside each serving process, an enforcement agent holds the structure, applies updates and answers Check in process.](diagrams/video-c4-containers.pdf){width=96%}

**Why each container is separate.** The *policy tool* changes at human speed and needs approval. *Ingest
and the rule store* are the one place that must be strictly correct (one order). The *compiler and origin*
turn rows into immutable files. The *relay tree* exists to bound the origin's load and cache files. The
*control plane* owns rollout and fleet state; it must not be on the request path. The *agent* is a library,
not a service, so the check has no network between it and the request.

![Publish as a sequence.](diagrams/video-seq-publish.pdf){width=92%}

![Distribute and apply as a sequence.](diagrams/video-seq-distribute.pdf){width=92%}

![Enforce as a sequence.](diagrams/video-seq-enforce.pdf){width=92%}

![Rollback as a sequence.](diagrams/video-seq-rollback.pdf){width=92%}

**What correct serving code looks like.**

```
agent = DenyAgent.start(lists = ["abuse", "legal"])     // loads last known good from disk
v = agent.check(request.sourceAddress)                  // in process
switch v.verdict { DENY: return refuse(403, v.ruleId)
                   CHALLENGE: return challenge()
                   ALLOW: return next() }
log.sample(v)                                           // carries the list version
health = { listAge: agent.ageMs(), ok: agent.ageMs() < bound }   // the balancer reads this
```

**Layered rules.** A global list and a regional list, each with its own versions. A node reads the global
one and its own region's list; precedence is fixed (allow beats deny, a more specific range beats a wider
one). Same compiler, relays and gates; only the artifact name and audience differ.

\newpage
# Stage 5: Why these choices

The interviewer can ask for a technology at any time. Mechanism first, product second, and say what rules
each alternative out.

## A versioned snapshot-and-delta pipeline for the list

**Why here.** The list is read everywhere and written rarely, and it must be verifiable. A versioned,
immutable artifact is the only form every tier can cache forever and every node can verify before it
applies.

**What to be ready to explain.** (1) *Why immutable and content-addressed:* a relay can cache without
revalidating, 500 nodes cost one origin fetch, and a corrupt copy is detectable by its name. (2) *Why a
chain and a digest:* the chain proves the artifacts form a sequence; the digest proves the result. (3)
*Why per-key versions:* arrival order is not intent order, and a merge keyed by version is idempotent and
order-independent.

**Alternatives.** A full file on a timer (4 TB; no integrity). A push-only stream (a missed message is
never repaired). A central lookup per request (adds the list service to every request's availability).
Each fails exactly where the table in Stage 3 says.

## The rule store

**Why here.** One place that must be strictly correct: it assigns the version order. A relational store
with transactions is enough: 50 changes a second is tiny. The risk is not throughput; it is the
commit-order race in Stage 3, solved with a per-list counter row.

**Alternatives.** A replicated log as the primary store (more machinery than 50 writes a second needs). An
eventually consistent store (cannot give one order).

## Object storage behind caching relays for the artifacts

**Why here.** Immutable files with content-addressed names are exactly what object storage and an HTTP
cache do well. The manifest is the only mutable object, about 100 bytes, short-cached.

**Internals to explain.** A relay serves the manifest with a short lifetime (a second or two), and the
immutable artifacts with a long one. A stale manifest from a relay cache is harmless to correctness (a node
never applies a version lower than the one it runs) but is exactly how challenge 7's "ban that did not
land" happens, so manifest age is a metric.

**Alternatives.** A pub/sub system as the only path (no catch-up). A configuration-distribution fabric the
company already runs (adopt it for transport, build the compiler, gates and audit; see Stage 10).

## An in-memory sorted array and a prefix trie on the node

**Why here.** Binary search over a sorted array is about 24 comparisons for 10 M keys. A radix (prefix)
trie answers "which is the longest matching range" in a handful of steps. Both are compact and
cache-friendly, and both can be built beside the live copy and swapped.

**Internals to explain.** For IPv4 a range is `address / length`; the trie descends bit by bit and
remembers the last node that carried a rule. For IPv6 the same, up to 128 levels, compressed (a
path-compressed radix trie), so the depth is the number of branching points, not 128. Overlapping ranges
resolve by the longest prefix; an exception inside a range is **expanded by the compiler into explicit
entries**, so the node needs no special case.

**Alternatives.** A hash set (fast for single keys, cannot answer "is this address inside a range"). A
database index (a network call).

## A Bloom filter, only as a front tier

**Why here.** A compact membership test that never gives a false negative. At 10 bits per entry it has
about a 1 percent false-positive rate; 100 M entries is 125 MB.

**Internals to explain.** `k` hash functions set `k` bits per entry; a query that finds any of them
unset is *definitely not listed*; all set means *maybe*. The false-positive rate falls as bits per entry
rise (about 1 percent at 10 bits and 7 hash functions). **It cannot say "listed"**, so a hit must be
confirmed by an exact check. Used alone it blocks about 1 percent of clean traffic.

**Alternatives.** An exact local set (fits at 10 M, not at 100 M IPv6). A cuckoo or quotient filter (can
delete entries; still one-sided). A shared cache (a network call per request).

## Technologies, one level down

Every container with the technology it runs on, how it is built, the alternatives rejected and why, and the question an interviewer asks about it. Generated from `stack.json`.

<!-- stack:sections -->

## Rule store: PostgreSQL with a counter row

*How it is built.* Each change is a transaction that locks the list's counter row, increments it and stamps the change with the new version. Because the row lock is taken before the commit, version order equals commit order. Every change is also appended to an audit table, with who, why and the approval. Per-key versions let a merge be idempotent and independent of arrival order.

*Why PostgreSQL, one primary, a synchronous standby, a counter row per list:* The only part that must give one total order. Fifty changes a second is tiny for it; the risk is the commit-order race, not throughput.

*Rejected:*

- **A replicated log as the primary store**: More machinery than fifty writes a second needs, and the order is still decided by one leader.
- **An eventually consistent store**: It cannot give one order, which is the one thing this store is for.

*Course:* theory/04 (replication and consistency).

*Drill.* "Two operators publish at the same moment. How is the order of their changes decided?" Both transactions lock the list's counter row, so one waits. The version number is taken under the lock, so version order is commit order. The trap is stamping the version before the commit.

## Compiler: snapshots, deltas, a digest chain

*How it is built.* On each new version the compiler writes a delta from the previous one, content-addressed by its hash. Every hundredth version it writes a full snapshot. A tiny manifest names the latest version, its digest and the previous digest, so the artifacts form a chain. A node that is behind by less than the delta window applies deltas, and otherwise fetches a snapshot. Snapshots are compact and sorted, so a node can load them without rebuilding.

*Why A Go job: a snapshot every N versions, a delta per version, a manifest, a digest chain:* Every tier can cache an immutable artifact for ever, and every node can verify it before it applies it.

*Rejected:*

- **A full file on a timer**: Four terabytes a push, and no integrity check.
- **Per-request lookups only**: The list service joins every request's availability.

*Course:* theory/06 (messaging and streams).

*Drill.* "A node was offline for a day. How does it catch up, and how does it know the result is right?" It reads the manifest, sees it is behind by more than the delta window, fetches the latest snapshot, then applies deltas. The digest chain proves the artifacts form a sequence and the digest proves the result.

## Origin and relay tree: object storage and HTTP caches

*How it is built.* Artifacts sit in object storage with names that include their hash. Regional relays, then zone relays, cache them with a very long lifetime. The manifest is the one mutable object, about a hundred bytes, cached for a second or two. Nodes poll the manifest and also accept a push hint, so a change lands in seconds. Manifest age at the node is a metric: a stale manifest is harmless to correctness and exactly how a ban fails to land.

*Why Object storage as origin; regional, then zone, HTTP caching relays:* Immutable, content-addressed files are exactly what object storage and an HTTP cache do well. Five hundred nodes cost one origin fetch.

*Rejected:*

- **Pub-sub as the only path**: A missed message is never repaired, and there is no catch-up.
- **A configuration fabric we already run**: Adopt it for transport, and keep our compiler, gates and audit.

*Course:* theory/05 (caching).

## Enforcement agent: a library with a local set

*How it is built.* The agent loads the artifact into a new in-memory set, verifies the digest, then swaps one pointer. Check reads the current pointer and never blocks on a swap. A compact filter answers about ninety-nine percent of requests with a definite not listed. A maybe goes to the exact lookup tier through a small cache. If the control plane is unreachable the node keeps its last good set, and a bound says how stale it may become.

*Why Library in the server, a compact local filter with an exact tier behind it:* The check is on every request, so it cannot wait for a network call. The local copy answers, and it is swapped atomically, never edited in place.

*Rejected:*

- **A network lookup per request**: The list service becomes part of every request's availability.
- **Editing the set in place**: A reader can see a half-applied update.

*Course:* theory/08 (reliability and operations).

*Drill.* "The agent applies a corrupt artifact. What does the serving process see?" Nothing: the digest check fails before the swap, the node keeps the last good set and reports the failure. The trap is verifying after applying.

## Control plane: stages, gates and a kill flag

*How it is built.* A new version is staged to one percent of nodes, then ten, then everyone, with a gate between stages that watches the rejection rate and the error rate. A kill flag halts the rollout and holds every node at its current version. Fleet state, meaning which node runs which version, lives in etcd. A node never depends on the control plane to enforce; it depends on it only to move.

*Why Go service, etcd for fleet state, staged rollout by percentage:* A bad list is everywhere in seconds unless something can stop it. A staged rollout with a gate buys the minutes a person needs.

*Rejected:*

- **Fan out to the whole fleet at once**: One mistyped line is a global outage in twenty seconds.
- **Gate by a human approval only**: The gate is a minutes-long human step; automated metrics catch the first ten seconds.

*Course:* theory/08 (reliability and operations).

*Drill.* "An operator types slash eight instead of slash twenty-eight. What limits the damage?" The one percent stage: the gate sees the rejection rate jump and halts the rollout before the next stage. The kill flag freezes the rest. The trap is relying on the reviewer.

## Policy tool: review and explain

*How it is built.* Changes are drafted, diffed against the live list, and approved by a second person when they match more than a threshold. The explain view answers why a key was or was not blocked: which rule, which version, who added it and why. Every action lands in the audit table. A dry run shows the matched count before anything publishes.

*Why Web app and Go API, two-person approval, an explain view:* People change the list under pressure. The tool makes a risky change need a second person and makes any verdict explainable afterwards.

*Rejected:*

- **Direct database edits**: No diff, no second person, no audit trail.
- **A spreadsheet upload**: No validation of a typed range, and no explanation afterwards.

*Course:* theory/08 (reliability and operations).

<!-- /stack:sections -->

## The stack on one page

<!-- stack:summary -->

| Container | Choice | Rejected | The deciding reason |
|---|---|---|---|
| Rule store | PostgreSQL, counter row | Log as store; eventual store | One total order |
| Compiler | Snapshots, deltas, digest chain | Full file; lookups only | Immutable and verifiable |
| Origin and relays | Object storage; HTTP relays | Pub-sub only | Cache for ever; one origin fetch |
| Enforcement agent | Library; filter; atomic swap | Per-request lookup; in-place edit | Local, verified, atomic |
| Control plane | Staged rollout, gates, kill flag | Fan out at once; human gate | Minutes to stop a bad list |
| Policy tool | Web app, approval, explain | Database edits; spreadsheets | Second person; explain a verdict |

Each fix in Stage 6 rejects one tool by name:

| Deep dive | Rejected | Because |
|---|---|---|
| 6.1 | A push-only stream | a missed message is never repaired; polling the manifest catches up. |
| 6.2 | Applying changes in arrival order | arrival order is not intent order; per-key versions make the merge idempotent. |
| 6.3 | Fanning out to the whole fleet at once | one mistyped line is global in seconds; stages and a gate bound it. |
| 6.4 | Making the control plane a dependency of enforcement | its outage would stop enforcement; nodes keep the last good set within a bound. |
| 6.5 | The full list in every node's memory | it does not fit; a filter in front and an exact tier behind do. |
| 6.6 | Calling a slow external source on every request | its latency becomes ours; prefer a bulk list, else a bounded cache and a budget. |
| 6.7 | Alerting on server health only | the fleet can be green while a ban never lands; probe from change to enforcement. |

<!-- /stack:summary -->

# Stage 6: Deep dives

The challenge order: **each fix creates the next question.** Correctness: 2 and 3. Failure recovery: 1
and 4. Scale: 5 and 6. Observability: 7. The crux (the stale policy and the bad push) gets two: 3 and 4.

**Every deep dive below has five parts:** the risk, the mechanism, a failure case with numbers, what to
say, and the weak answers.

## 6.1 The node that was offline (failure recovery)

**The question.** "A node was offline for two hours. How does it catch up? How do you know all 100,000
nodes run version N?"

**The risk.** A node is behind, or what it received is truncated or corrupt, and there is no way to tell.

**The naive answer.** "On reconnect it downloads the whole list again, and we check each node's file."

**The failure case.**

```
02:00  node z7-0412 applies version 8,000,000, then loses its uplink
04:00  the list is at 8,360,000: 360,000 changes missed, about 11 MB of deltas
04:01  50 nodes in the zone reconnect together: 50 x 40 MB = 2 GB from one relay
04:01  a power cut mid-download leaves a truncated file the node would load
```

![The attack and the fix. Nothing says what the node should fetch or whether it is whole; the manifest answers the first, the chained checksum and digest the second.](diagrams/video-ch1-fix.pdf){width=90%}

**The mechanism.** The node sends `have = V`. The manifest says: inside the window, take the delta; outside
it, take the snapshot. Every artifact is verified (chain, then state digest) **before anything is applied**,
and the apply is the atomic swap.

![Reconnect, manifest, delta, verify, swap, with a failed checksum falling back to a snapshot.](diagrams/video-seq-ch1-catchup.pdf){width=92%}

```
m = manifest(have = v)
if m.current == v:           return                      // current: nothing to do
if v >= m.minDelta:          art = delta(v)              // inside the window: small
else:                        art = snapshot(m.current)   // outside, or bootstrap
if !verify(art):             discard(); art = snapshot(m.current)
if !verify(art):             keepLastGood(); report(apply_failed)
```

**Why it works.** *Convergence* (every node can reach the present, by a small delta if recent and by a
snapshot if not) and *integrity* (it never serves a state it has not verified). The fleet answer to "is
everyone on N" is the reported applied version.

**The second-level push.** "The delta window is 24 hours and the node was down for three days. Or the
checksum fails again on the snapshot." *Beyond the window* the manifest points to the snapshot, whatever
the node's age; the zone relay's cache makes 50 nodes cost one origin fetch. *A checksum that keeps
failing* means a corrupt artifact at the origin: the node keeps its last known good, reports
`apply_failed`, and the control plane halts that version.

::: why
**What the first draft glosses over: a node that restarts with an old copy on disk.** A node down for
three days boots from a three-day-old file. If it starts serving at once it is "stale at birth": it
enforces an old list and does not know it. Treat the disk copy's age as the node's age (store a
timestamp with the version file), report it from the first poll, and keep the node *not ready* until the
first successful manifest check or until the disk copy is inside the bound for that list. This is the
same policy as Stage 6.4, applied at boot.
:::

::: warn
**Weak answers.** "Re-download the whole file" (4 TB). "Checksum the file" (no chain, no digest, no
fallback). "Poll more often" (does not fix catch-up or integrity). No answer to "how do you know the fleet
is on N".
:::

::: say
"Every version has a number and a checksum chained to the one before. A node says what it has, and the
manifest says whether a small delta or a full snapshot gets it to the present. It verifies before it
applies and swaps atomically, so it never serves a half-built list. And I know the fleet is converged
because every node reports the version it runs."
:::

## 6.2 Order, duplicates and overlap (correctness)

**The question.** "An add and a remove for the same key arrive in the wrong order. Or the same delta
arrives twice. And an operator adds a /16 and allows a /26 inside it."

**The risk.** The node treats arrival order as intent order.

**The failure case.**

```
v100  add 203.0.113.9 (a mistake)
v101  remove 203.0.113.9 (the correction)
node  receives v101 then v100 by two paths; applies in arrival order: final state banned
v90   deny 198.51.0.0/16      v97  allow 198.51.100.64/26 (a partner): verdict for 198.51.100.70?
```

**The mechanism.** One total order (the rule store's counter), and a version on every key. A change applies
only if its version is higher than the key's last. Replays and reordering become no-ops. **Ranges resolve by
longest prefix; allow beats deny at equal specificity; an allowlist range matches first and always wins;
and two sources disagree by written precedence** (an unexpired manual entry beats a feed).

![Late and duplicate changes are ignored. Version 100 arrives after 101 and is not higher; the duplicate 101 is a no-op.](diagrams/video-seq-ch2-merge.pdf){width=82%}

| Situation | Rule | Why |
|---|---|---|
| A key matches an exact entry and a range | the exact entry decides | more specific |
| Two ranges match | the longest prefix decides | more specific |
| Allow and deny at equal specificity | allow wins | a wrong block is worse than a missed ban for a protected range |
| An allowlist range matches | allow, always, checked first | independent of review |
| Two sources disagree | an unexpired manual entry beats a feed | no silent overrides |

**Why it works.** *Convergence to the intended state.* The result depends on the set of changes, not on
their order or count: an idempotent, commutative merge.

**The second-level push.** "Tombstones grow forever. What if the version counter is lost or reset after a
restore?" Tombstones are kept only for the delta window; a node older than the window takes a snapshot
without them. The counter lives in the rule store's transaction log and a restore that would rewind it is
refused; after a rebuild, start with a higher **epoch**. **Expiry is a command, not a clock:** a ban with
`expiresAt` becomes an explicit remove, issued by the compiler at that time with its own version, so every
node sees the same history and none depends on its own wall clock.

::: why
**What the first draft glosses over: a remove that is not in the window.** If a removal's tombstone has
been dropped and a node older than the window takes a snapshot, it correctly has no entry. But a node
*inside* the window must still see the removal as a delta. The rule: a tombstone is dropped only after
**every node is known to be past that version** (the control plane's minimum applied version) *and* the
window has elapsed. Dropping it on age alone can resurrect a ban for a node that was offline exactly that
long.
:::

::: warn
**Weak answers.** "Apply in order" (the network does not promise it). "Use timestamps" (clocks disagree).
"Exactly-once delivery" (the wrong guarantee; idempotent merge is cheaper and stronger).
:::

::: say
"I do not trust arrival order. One writer assigns versions, and each key remembers the version of its last
change, so a late or duplicate message is ignored. Ranges resolve by longest prefix, and an exception
beats a deny. The merge is idempotent, so the same history gives the same list in any order."
:::

## 6.3 The bad push (the crux, part one)

**The question.** "Someone publishes a range that covers a large part of Europe. How fast does it break,
and how do you stop it?"

**The risk.** The pipe carries a mistake as fast as it carries a ban.

**The failure case.** 14:00:00 an operator adds a /8 instead of a /28. 14:00:03 compiled. 14:00:12 at the
relays. **14:00:21 all 100,000 nodes serve it.** 14:00:30 eight percent of requests are denied. 14:00:40
the on-call is paged, and the fix is a new version that takes another 18 seconds.

**The mechanism: treat the list like code.**

1. **Validate at ingest.** Shape and size limits, a cap on how much address space one change may cover (the
   review shows "this change covers 16 M addresses"), and an **allowlist** checked at compile time **and
   again at enforcement**, so it works even if a bad version gets through.
2. **Two-person approval** above a threshold.
3. **Staged rollout**: 5 percent (one region), 25 percent, 100 percent, with a five-minute bake each,
   **gated on block rate per node against its own baseline**. A rise of more than a few points freezes the
   stage and alerts.
4. **A kill flag** in the manifest, honoured within one poll.
5. **Rollback is a new, higher version.**
6. **Shadow mode.** The action is part of the rule: log-only, challenge or deny. A new or widened rule ships
   as log-only first; nodes record "would have denied" with the rule id; the owner promotes it after reading
   the counts, and the promotion is itself a version.

| Signal | Baseline | Trip | Action |
|---|---|---|---|
| Block rate per node, 10 s window | 0.5 % | more than +3 points on the canary | freeze the stage, alert |
| Block rate by region | per region | a region doubles | halt and page |
| Apply failures | about 0 | any checksum failure on a stage | halt that version |
| Urgent ban | none | fast path: one region, 60 s bake | logged as an exception, reviewed after |

![Staged rollout: the same mistake with a canary. Only 5,000 nodes see it; the gate trips within one metrics window.](diagrams/video-ch3-fix.pdf){width=90%}

**The second-level push.** "The rule is legitimate-looking and wrong: a real customer's range. Block rate
does not move. Or the kill switch rides the same pipe that is broken." *Nodes protect themselves:* if a
node's block rate jumps by a multiple of its baseline for N seconds right after an update, it reverts to
the previous version on its own, reports, and pages. *The kill flag is a separate, tiny channel* (one field
in the manifest), not a new snapshot. **The honest limit:** a precise, plausible, wrong rule cannot be found
by statistics. It is found by the allowlist for protected ranges, by review of high-impact changes, by the
audit trail and a fast removal path. Policy, not mechanism, owns that risk.

::: why
**What the first draft glosses over: the block-rate gate has a blind spot at small canaries.** A rule that
blocks 0.01 percent of traffic cannot be seen on a 5 percent canary of 5,000 nodes inside a ten-second
window (the signal is smaller than the noise). The gate catches *large* mistakes. Small ones need the other
defences: shadow mode (counts per rule, over a longer window), review of the effect, and the allowlist.
State what the gate can and cannot see.
:::

::: warn
**Weak answers.** "Review it first" (a human saw one line). "Fix it quickly" (18 seconds, plus a human).
"Roll back the file" (a version reused is ignored). "Fail closed" (see 6.4).
:::

::: say
"The same pipe that delivers a ban in ten seconds delivers a mistake in ten seconds, so a push gets the same
discipline as a binary: validation, an allowlist that always wins, a canary gated on block rate, a kill flag
on its own channel, and a rollback that is just a new version. Nodes also protect themselves: if the block
rate jumps right after an update, they revert on their own."
:::

## 6.4 Stale, partitioned, or no control plane (the crux, part two)

**The question.** "A node cannot reach any relay for three hours. Or the whole distribution plane is down.
What does the node do, and who decided?"

**The risk.** Both defaults are an outage, in opposite directions.

**The failure case.** A node applies its last update at 09:00 and loses all relays. By 12:00 it has missed
about 54,000 changes (3 h times 3,600 times 5 a second), including one ban the policy team called urgent.
*Fail closed* refuses 108,000 legitimate requests from this node alone (10 a second for 10,800 s), and if
the whole plane is down **every node fails closed together: a global outage caused by the system built to
protect you.** *Fail open* serves everything, including the ban it never heard about.

**The mechanism.** First, **stale is not open**: a node keeps enforcing its last list. Only the newest bans
are missing. Then a **bound and an action**, signed by the owner, per list:

| List class | Bound | Action past the bound | Owner |
|---|---|---|---|
| Abuse bans | 15 min | alert, keep serving | security |
| General list | 60 min | drain the node, capped | platform, agreed with policy |
| Legal list with a hard deadline | per the legal term | drain the node; escalate to legal | legal |
| A node with no list on disk | none | stay out of rotation until it bootstraps | platform |

![Stale is not open. A node keeps enforcing its last list through every stage; only the newest bans are missing.](diagrams/video-stale.pdf){width=92%}

![Past the bound, drained, recovered. The node keeps enforcing its last list while it is out of rotation.](diagrams/video-seq-ch4-drain.pdf){width=82%}

**The second-level push.** "Every node passes the bound at once because the control plane is down. You just
drained the fleet." A **drain budget**: automatic draining never removes more than a fixed share of the
fleet (say 5 percent per region); past it, nodes keep serving and the page goes to a human. The cost is
stated: while the plane is down beyond the bound, some nodes serve a stale list, and the owner of the list
accepts that, in writing, as the price of not causing a global outage. **The honest limit:** nothing makes
a partitioned node learn a ban it cannot hear. The cures are a plane that is not a single point of failure
and a bound short enough to matter.

::: why
**What the first draft glosses over: drain flapping.** A node that crosses the bound, is drained, recovers,
and re-enters can oscillate if its age sits near the bound. Use hysteresis (re-enter only when the age is
well inside the bound, for example half of it) and count a flap as an alert. Also: the drain budget must be
**per region and global**, or a regional plane outage drains one region completely.
:::

::: warn
**Weak answers.** "Fail closed" / "fail open" as a one-word answer. No owner. No cap on draining. Treating
the disk copy as if it were fresh.
:::

::: say
"Stale is not open: a node keeps enforcing what it has. For each list, the owner signs a maximum age and an
action: alert and keep serving, or pull the node out of rotation. Automatic draining has a cap, so a
control-plane outage cannot become a fleet outage. The risk of a late ban is a named decision, not an
accident."
:::

## 6.5 The list does not fit (scale)

**The question.** "A hundred million IPv6 prefixes. Why not one shared cache lookup per request? And a
Bloom filter says maybe. Then what?"

**The risk.** The exact set no longer fits in memory, and the obvious shortcuts break differently: a shared
lookup adds a dependency; a filter alone blocks real users.

**The failure case.** The exact set is 100 M times 17 B, **1.7 GB**, against 512 MB. A shared lookup at
1 M a second is a hard dependency and 1 ms on every call. A filter used alone, at 1 percent false
positives, blocks **10,000 real users a second**.

![A filter in front: not listed is certain; maybe needs a check.](diagrams/video-bloom.pdf){width=92%}

**The mechanism.** A local filter (125 MB) answers "not listed" for about 99 percent of traffic with no
network call. A *maybe* goes to a **sharded exact lookup tier**, whose answer is cached on the node with a
lifetime bounded by the staleness bound. Keep the hottest, most-matched ranges exact and local. The right
enforcement point depends on where the key first becomes known: an address at the edge, a user id after
authentication, an email after login.

![Maybe, lookup, cache.](diagrams/video-seq-ch5-lookup.pdf){width=82%}

**The second-level push.** "During an attack nearly every request is a true hit, so every request goes to
the lookup tier." Cache positive verdicts (repeated hits from one source cost one lookup); **coalesce**
concurrent lookups for one key; shard the tier by prefix and size it for the hit rate it will see; and cap
lookups **per node**: past the cap a node uses cached verdicts and, for an unknown key, its stated policy,
so the tier cannot be flooded by the attack it exists to stop. **The honest limit:** a very large list
costs a tier on the request path for hits; we pay for it only for keys likely to be banned.

::: why
**What the first draft glosses over: the filter must be rebuilt, not just updated.** A Bloom filter
cannot delete. A removal adds nothing to the filter, so over time it carries entries that are no longer
listed and its false-positive rate drifts upward (harmless to correctness, because a maybe is confirmed,
but it costs lookups). Rebuild the filter from each snapshot, or use a filter that supports deletion.
Also, a filter built from the *set at version N* must be swapped together with the exact tier's view, or a
key can be "not listed" locally and "listed" remotely for a moment.
:::

::: warn
**Weak answers.** "A bigger cache." "Redis for every request." A Bloom filter as a verdict. Never saying
the false-positive rate. Stretching one structure over every key type.
:::

::: say
"A shared lookup per request puts the list service in everyone's availability, and a millisecond on every
call. When the set does not fit, I keep a filter locally, which can say definitely not listed, and confirm
a maybe with an exact tier, because a false positive blocks a real user. I cache the verdicts, coalesce
lookups, and cap the load per node, so an attack does not take down the confirmation tier."
:::

## 6.6 A slow external source (overload; the source variant)

**The question.** "The authority gives you only a lookup API: one second a call, a hundred calls a second.
It is down for two days. And a new ban covers a /16 you already cached verdicts for."

**The risk.** The authority cannot keep up, and a per-address cache outlives a wider ban.

**The failure case.** 20,000 first-seen addresses a second against 100 calls a second: **200 times over**.
At 100 a second a day buys 8.6 M lookups against about 50 M distinct addresses: **17 percent coverage**.
`192.0.2.7` is cached as allowed for 24 hours; an hour later the authority bans `192.0.0.0/16`, and the
address is served from cache for 23 more hours.

![A slow lookup API cannot sit on the request path and cannot cover everything.](diagrams/video-authority.pdf){width=92%}

**The mechanism.** (1) If any bulk list or feed exists, **mirror it** and use the same pipeline; the API only
verifies. (2) With only a lookup: a **range-keyed verdict cache**, so a wider ban supersedes address
verdicts by version; a lifetime no longer than the allowed staleness or the legal grace period; single-flight
lookups; a token bucket of 100 a second spent on the highest-volume addresses first; and a **stated policy
for a first-seen address** (serve and verify, or hold briefly), chosen by the owner. (3) A circuit breaker
with an explicit, fleet-wide rule for an outage.

![One lookup, one range rule.](diagrams/video-seq-ch6-authority.pdf){width=82%}

**The second-level push.** "The API is down for two days and your cache lifetime is one day." A **grace
period**: serve expired verdicts for a stated number of days, flag every decision made on expired data in
the log, and alert; the legal owner decides how many days. The exposure is first-seen addresses during the
outage. **The honest limit:** with only a slow lookup, full coverage is not possible. Say so, and ask for a
feed.

::: why
**What the first draft glosses over: negative caching and the allow-first-then-verify trap.** "Serve and
verify" means a banned first-seen address is served until its verification returns. For a legal list that is
a violation per request, not per address. If the policy is *hold briefly*, the hold has a cost: latency on
every first-seen address. State which one the owner chose and why, with the exposure as a number: first-seen
rate times the verification delay.
:::

::: warn
**Weak answers.** "Call the API on each request." "Cache for a day" with no word on a wider ban. Silent
default on an outage. Promising full coverage.
:::

::: say
"I never call a slow authority on the request path. If there is a bulk list, I mirror it. If there is only
a lookup, I cache verdicts for no longer than the allowed staleness, coalesce lookups, spend the rate budget
on the highest-volume addresses, and write down what happens on a first-seen address and on an outage. Full
coverage is not possible, so I say how much we have, and I ask for a better feed."
:::

## 6.7 How would you know it is broken? (observability)

**The question.** "A ban was published an hour ago and one region is still serving the banned source. The
dashboard is green. How would you have known?"

**The risk.** The dashboard watches the machines. The promise is somewhere else.

**The failure case.** Relay health 100 percent, origin latency 40 ms: green. Region `ap-2` has 4 percent of
nodes on 8,360,990 and the rest on 8,361,004: the push to one zone fails quietly and polls hit a stale relay
cache. Block rate is 0.2 percent in `ap-2` against 0.5 percent elsewhere.

**The mechanism: measure the promise.**

| SLI | Target (initial) | Why |
|---|---|---|
| Version skew: nodes on the current version within 30 s | 99.9 percent or more per region | the propagation SLO, directly |
| Propagation lag | p99.9 under 30 s | per publish, end to end |
| List age per node against its bound | none past its bound | the stale policy, watched |
| Apply failures, checksum mismatches | about 0 | a corrupt artifact or a bad relay |
| Block rate against baseline, per version | within a few points | the gate and the bad-rule alarm |
| Lookup-tier hit rate | within capacity | the filter and the attack |

**Symptom pairs: two metrics, one conclusion.** Skew up and one zone's relay cache age up: a stale relay
cache. Block rate down in one region and that region's version behind: **a ban that did not land**. Block
rate up and a new version just applied: a bad rule (the gate, not the relay). Apply failures up and checksum
mismatches up: a corrupt artifact at the origin. Lookup-tier load up and hit rate up: an attack, or a filter
that is too small.

**The probe.** A synthetic banned key is published every five minutes and a request from it is sent through
the real path in each region; a region that still allows it after 30 seconds pages, with the node's applied
version attached.

![The probe, end to end.](diagrams/video-seq-ch7-probe.pdf){width=82%}

**The second-level push.** "The probe passes and a real ban is still missing. Or the block rate is flat
because traffic bypasses the enforcement point." Skew is measured **per node, from reports**, not only from
probes. **Coverage is a metric:** the share of traffic that passes through an enforcement point, and a
counter of requests that skipped the check. **The honest limit:** we can detect a late ban after the fact and
alarm on its precursors; we cannot observe an absence of risk.

::: why
**What the first draft glosses over: the probe's own key changes the baseline.** A synthetic banned key is
a real rule: it adds to the version count and the delta size, and it must be removed (with a tombstone) after
each run. Use one fixed reserved range from a block that real traffic never uses, and have the probe
*update* it (add, then remove) rather than create new keys, so the list does not grow.
:::

::: warn
**Weak answers.** "CPU and error rate of the relays." One metric per page. No probe. No coverage. A green
dashboard offered as proof that a ban landed.
:::

::: say
"I alert on the promise: the share of nodes on the current version within thirty seconds, per region, plus
a synthetic banned key sent through the real path. I read metrics in pairs so each page names a cause, and
every decision logs the rule version so an auditor gets an answer. A green relay dashboard says nothing
about whether a ban landed."
:::

## 6.8 How the whole system degrades, in priority order

| What fails | What still works | What stops | Who is told |
|---|---|---|---|
| The policy tool or ingest | every node keeps enforcing the current list | new changes cannot be published | policy, platform |
| The rule store | enforcement; relays serve existing artifacts | no new versions | platform |
| The compiler or origin | nodes keep their list; relays serve cached artifacts | new versions stall | platform |
| A relay tier | nodes poll another relay or the origin; the delta window covers the gap | propagation slows | platform |
| The whole distribution plane | every node enforces its last list | the newest bans are missing | the signed stale policy fires |
| A bad version in flight | the canary and the gate | later stages halt | the on-call, automatically |
| The lookup tier (large lists) | local filter "not listed" for most traffic | confirmations; per-node budget and policy apply | platform |
| The authority | the mirror or the cache with a grace period | coverage of first-seen addresses | legal, policy |

::: why
**The priority order.** The request path comes first: it never depends on the network, so nothing above
can stop enforcement. Then the integrity of what nodes apply. Then freshness. Freshness is what degrades
first, and it degrades by a bounded, signed amount.
:::

\newpage
# Stage 7: Requirements that arrive mid-round

At Staff you say the delta out loud: *what changes, what does not, and what it costs.*

**1. "Add a second key type: a user id."**

- *What does not change:* the rule store, compiler, relays, gates, audit, the version order and the merge.
  The key kind was a field from the start.
- *What changes:* the enforcement point (after authentication, in the application layer, the same agent
  library) and the structure (a hash set, or a filter plus lookup at very large sizes). A user ban may need a
  shorter staleness bound; the owner signs it.
- *Cost:* a second agent integration point and its own gates. No new pipeline.

**2. "Ban by country or network owner, not just address."** The key is no longer an address; it is the
result of a lookup in a geo or network-owner database, which is itself a **versioned dataset with the same
distribution problem**. Distribute that database through the same pipeline, resolve the address to its
country or network at the agent, and match a country rule against the result. *Cost:* a second dataset, and
a new error source (the database is wrong for a range, so the allowlist matters more).

**3. "Per-customer lists."** A list per tenant, each with its own owner and bound. *What changes:* the node
holds the global list plus its tenant lists, so memory grows with the number of tenants a node serves;
precedence is fixed (allow beats deny, specific beats wide). *Cost:* memory per node, and a rollout stage
per tenant class. For very many small lists, hold them in a hash map keyed by tenant and share the
structures that are identical.

**4. "A ban must take effect in 5 seconds, not 30."** Push becomes mandatory, the poll interval drops, and
the stage bake for an urgent ban shrinks, which moves the position on the freshness slider. *What it costs:*
a larger push fleet, less time for a gate to see a mistake, and so a **stricter allowlist and shadow-first
policy** for urgent bans. The honest answer: five seconds and a safe canary are in tension; the owner picks
the point, and the pipeline makes the choice explicit.

**5. "Bans that expire."** Already designed in: the compiler turns an expiry into an explicit remove with its
own version, so no node depends on its clock. *Cost:* a scheduled compile at each expiry time, and a
tombstone for the window.

# Stage 8: Failures and reliability

| Failure | Blast radius | Detection | Response |
|---|---|---|---|
| A node is offline or behind | that node's missing bans | skew, list age | catch up by deltas; stale policy past the bound |
| A corrupt artifact | every node that fetches it | checksum and digest mismatch, apply failures | nodes keep last good; halt the version |
| A bad rule | up to the fleet, gated by stage | block-rate gate, shadow counts, local breaker | halt, rollback as a new version, kill flag |
| A stale relay cache | one zone | skew paired with cache age | purge; poll another tier |
| Out-of-order or duplicate delivery | none (merge is idempotent) | none needed | n/a |
| The rule store is rebuilt | version reuse risk | counter check | higher epoch; refuse a rewind |
| The control plane is down | no rollouts, no gates, nothing drained past the cap | controller health | nodes keep enforcing; a human proceeds by hand |
| The authority is down | first-seen coverage | adapter health, expired-decision flag | grace period, policy |
| An operator error in the console | as a bad rule | approval, audit | two-person approval, audit, rollback |

**One incident walked through.** A change adds a /16 that includes a partner's range. The allowlist
was not updated. The canary stage (5 percent, one region) shows block rate 0.5 percent to 1.4 percent
within one window: the gate freezes the stage and alerts. The on-call reads the shadow counts (the rule was
shipped as log-only first, so no user was affected), finds the partner range, adds it to the allowlist and
re-publishes. Timeline: 14:00 publish, 14:02 gate trips, 14:09 corrected version published, 14:11 canary
passes, 14:21 rollout complete. **No customer saw a block.** The retrospective question is not "who
reviewed it" but "why was the partner range not in the allowlist", and the answer becomes a check at ingest.

# Stage 9: SLOs, observability, cost

**SLIs** (all initial targets):

| SLI | Target | Measured from |
|---|---|---|
| Version skew within 30 s | 99.9 percent per region | node reports |
| Propagation lag, p99.9 | under 30 s | publish time to the last applied report |
| Nodes past their staleness bound | none | list age per node |
| Apply failures and digest mismatches | about 0 | node reports |
| Block rate against baseline | within a few points | decision samples |
| Check latency | p99 under 10 us | agent timer |

**The error budget as a constraint.** The 99.9 percent target allows 100 late nodes of 100,000. A region
with more than 0.1 percent late nodes for longer than a window is an incident, not a trend. Convert it
once into a rule: *any region whose skew falls below target for ten minutes pages the platform.*

**The dashboard.** Four panels: skew and lag per region; list age distribution with the bound drawn; block
rate against baseline per version; and the probe's last result per region. Everything else is a drill-down.

**Cost.** The expensive items are people, then relay bandwidth (small: 800 MB per snapshot to the origin's
tier, 1 MB a second for polls), then memory on nodes (40 to 200 MB per node, already paid for by the
fleet). Levers: a longer poll interval for low-risk lists (a minute for a list where thirty seconds is not
needed), compressed deltas, sharing identical structures across tenant lists, and turning push off where
the poll meets the target.

# Stage 10: The EM layer (auxiliary at Staff)

**Marked AUX.** At the Staff bar this layer is optional; in a manager loop it is the main event.

**Phasing.** R0 prototype (one list, snapshot, ten-second manifest poll, atomic swap): 1 to 2 engineer-months.
R1 production (versions, deltas, relays, checksums, validation, allowlist, staged rollout and gates, kill
flag, reports, decision log, console, audit): 18 to 24 engineer-months, four engineers for five to six
months. R2 platform (push streams, layered rules, filter plus lookup tier, an external adapter, per-key-type
enforcement): 50 to 90.

| Role | FTE | Owns |
|---|---|---|
| Tech lead | 1.0 | the version and ordering model, the merge, design reviews |
| Senior backend | 1.0 | rule store, compiler, relays, rollout |
| Backend | 1.0 | agent library, console, first list's migration |
| SRE | 1.0 | controller, SLIs, probes, runbooks |
| Manager and policy liaison | 0.3 and 0.2 | roadmap, adoption, the contract with policy |

**Total cost of ownership, illustrative:** 22 engineer-months to build R1, then about 1.5 people for five
years (90): **about 112 engineer-months, or 9 engineer-years**. People dominate.

| Option | Pilot | Five years, engineer-months (illustrative) | When it wins |
|---|---|---|---|
| Don't: the edge provider's managed IP sets | about 2 weeks | about 15 | the limits fit; check first, every time |
| Adopt a configuration-distribution fabric for transport | about 8 weeks | about 70 | one is already run |
| Hybrid: build compiler, gates, audit; buy the transport | about 3 months | about 85 | the R1 pick if a transport exists |
| Build it all | about 5 months, 4 people | about 112 | beyond managed limits, custom keys, layers |

**Team seams.** Policy owns *what*; platform owns *how*; the propagation target is the contract. **Never cut:**
versions with checksums, staged rollout with a gate, the allowlist, a kill flag, last known good on disk, the
version in the decision log. **Cut first:** push streams, regional layers, the second key type, the lookup tier,
the console. **Top risks:** a bad rule; owner ambiguity; the control plane as a single point; no adopter;
scope creep into a general configuration platform.

**The question before saying yes:** "What does a wrong block cost, who decides, and how fast must a ban
land?"

**With half the team.** Build R0 plus gates and the allowlist; drop push and layers; use the provider's
feature for transport if it fits. The release discipline is phase one, not phase three.

# Stage 11: The close

> **What:** a local check, a versioned list distributed through a verified, resumable pipeline, a signed bound
> on staleness, and a release discipline. **Trade-off:** I gave up instant effect for a bounded, measured
> delay, and I pay memory on every node and a pipeline to run. **Risk:** the wrong block, so gates, an
> allowlist that always wins, shadow mode and a rollback that is a new version. **Next:** the large-list tier
> and push, once the target needs them.

# Stage 12: Self-check after a simulator run

| Dimension | Weak | Strong | Exceptional |
|---|---|---|---|
| Requirements | A table of addresses and a cache | Asks who owns the failure policy and how fast a ban must land | Separates missing ban from wrong block before drawing |
| Estimates | None, or not tied to a decision | 40 MB, 4 TB against 800 MB, 10,000 polls a second, 18 s against 30 s | The SLO as a budget of 100 late nodes |
| Design | A lookup per request | Local check, versions, deltas, relays, push with pull | Knows what a poll fetches and why |
| Depth | "Push the list" | Per-key version, tombstones, checksum chain | Commit-order race, state digest, drain flapping |
| Trade-offs | Names a product | Options with the failure that rules each out; checks F first | Says what D gives up |
| Operations | CPU and error rate | Skew, probes, symptom pairs | Coverage, shadow mode, the gate's blind spot |
| Leadership | Not discussed | Two owners and a contract; phases | Build/adopt/don't with people and months |

**Common traps in this round.**

- A lookup per request on the path.
- "Eventually consistent" with no number.
- No versions or checksums; trusting arrival order.
- A full download per node per change; "poll" without saying what it fetches.
- Failing closed fleet-wide, or open without saying so; never asking who owns the failure policy.
- A Bloom filter used as a verdict.
- One big push with no canary and no allowlist; a rollback that reuses a version number.
- A green relay dashboard as proof that a ban landed.

\newpage

# Part III: The internals

## Appendix A: Versioned distribution, in plain words

Every configuration-distribution protocol that scales solves the same four problems: *what do you hold*
(a version), *what is new* (a delta), *is it whole* (a checksum), and *did you accept it* (an acknowledge
or a reject). The pieces in this design map onto them directly.

- **A version** is a strictly increasing number assigned by one writer. It is the only thing a node needs
  to say about itself.
- **A delta** is the difference between two versions. If it is immutable and content-addressed, any cache
  can store it without asking again.
- **A checksum chain** makes each version's checksum cover its content and the previous checksum. A **state
  digest** (an order-independent set hash) covers the result, and works for a delta that spans several
  versions.
- **An acknowledge or reject per node** is the applied-version report. It lets the controller see which
  nodes accepted a stage, and a rejection (apply failed) halts it.
- **Resumption.** A node that was offline says what it has; the server answers with the shortest path to the
  present (deltas, or a snapshot). This is what makes the protocol robust: no message is precious.

Public systems that use the same shape include local-list update protocols for safe-browsing style
checks (a local list, incremental updates, a checksum to detect divergence), and the discovery protocols of
service proxies (versioned resources, acknowledge or reject). Name the idea; do not claim a product's
internals.

## Appendix B: Prefix tries and longest-prefix match

A range is `address / prefix length`. A **binary trie** stores the address bit by bit; each node may carry a
rule. To match an address, walk the bits and remember the **deepest node that carried a rule**: that is the
longest matching prefix. A **path-compressed (radix) trie** collapses chains of single-child nodes, so the
depth is the number of branching points, not the number of bits. For IPv4 that is a handful of steps; for
IPv6 the same idea works up to 128 bits.

Two practical points. (1) The trie and the exact array are separate structures, and the check order is
fixed (allowlist, exact, longest prefix). (2) An **exception inside a range** (deny a /16, allow a /26
within it) is expanded by the compiler into explicit prefixes (the /16 minus the /26 becomes a set of
smaller denies), so the node never needs a "but not this" branch. The cost is more entries; the benefit is a
node that is trivial to test.

## Appendix C: Bloom filters, the arithmetic

For `n` entries and `m` bits with `k` hash functions, the false-positive probability is about
`(1 - e^(-kn/m))^k`. The best `k` is about `(m/n) * ln 2`. At **10 bits per entry**, `k` is about 7 and the
false-positive rate is about **1 percent**. At 100 M entries that is **125 MB**. A Bloom filter has **no
false negatives** and cannot delete, so rebuild it from each snapshot (or use a variant that supports
deletion). In this design it is a front tier only, always followed by an exact check on a maybe.

## Appendix D: Staged rollout and gates

A staged rollout has three parts: a **ladder** (5, 25, 100 percent), a **bake** at each rung, and a **gate**
between rungs. The gate must be a **number**, evaluated by a machine, on a metric that moves when the
thing you are protecting is harmed. For a denylist that metric is the block rate per node against that
node's own baseline. Be able to say what the gate **cannot** see (a rule that blocks a very small share of
traffic) and what covers that gap (shadow mode, review of the effect, the allowlist, the audit trail).
An urgent ban uses a shorter ladder and bake, and is logged as an exception.

## Appendix E: Tombstones, epochs and never reusing a number

A **tombstone** records a removal so a late "add" cannot resurrect the key. It must live at least as long
as any node might still be behind, and be dropped only when every node is known to be past that version. An
**epoch** is a higher-order part of the version used after a rebuild of the rule store, so every new
version exceeds every old one, even if the counter was lost. The rule is the same one a fencing token
teaches: **a number that orders things must never go backwards, and must never be reused.**

## Appendix F: Testing a versioned distribution pipeline

- **A convergence harness.** Generate a random history of changes. Apply it to a model, and to many nodes
  with injected faults: reordering, duplication, truncation, a node offline for a random time, a relay
  serving a stale manifest. Assert that every node ends with the same list as the model.
- **A replay test for the merge.** Apply the same history in a hundred random orders; assert the same state.
- **Gate drills.** Publish a deliberately bad rule to a staging fleet; assert that the gate freezes the
  stage within one window and that the rollback lands as a new version.
- **A game day.** Practise the incident in Stage 8 on a real (small) region.
- **A restart test.** Kill a node mid-update; assert it comes back serving a verified list.

\newpage

# One-page cheat card

**Thesis.** The check is local; the list is not. Version it, bound its staleness, and release it like code.

**Order of the round.** Clarify (owner, kinds, size, bound, stale policy, source) · numbers (10/s per node,
40 MB, 4 TB against 800 MB, 10,000 polls, 18 s) · API (publish, manifest, check, report, rollout) · V1, V2,
V3 · seven challenges · cost.

**The four numbers.** 40 MB (10 M IPv4) · 125 MB filter at 100 M · 18 s of 30 s · 100 late nodes of 100,000.

**Seven fixes.** (1) manifest, window, snapshot, chained checksum and digest. (2) one order, version per key,
precedence. (3) validate, allowlist, canary gate, kill flag, local breaker, shadow. (4) a signed bound and
action; drain with a cap. (5) filter, exact tier, cache, per-node cap. (6) mirror, range cache, budget,
grace. (7) skew, probe, symptom pairs, coverage.

**One sentence per property.** Safety S1 (no served ban within the bound), S2 (no wrong block). Liveness L1
(every node applies every version), L2 (99.9 percent within 30 s), L3 (a stuck node is detected and handled).

**Say first.** "Stale is not open." "A poll asks the manifest; it does not download the list." "A rollback is a
new version." "An address is not a person."

**Close.** The check is local because it must be fast and independent. The list cannot be, so I gave it
versions, a bound, and the discipline of a release. A ban lands quickly and a mistake does not.
