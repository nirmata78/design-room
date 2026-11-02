---
title: "SD-09 · Chat and Messaging for a Billion Users"
subtitle: "A reference solution for a system design round at the Staff bar, explained down to every term"
author: "design-room reference solution · practise with the simulator first"
date: "2 November 2026"
documentclass: article
fontsize: 10pt
geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in
colorlinks: true
linkcolor: blue
urlcolor: blue
toc: true
toc-depth: 2
numbersections: false
---

\newpage

# How to read this document

This is the **long answer key for question `SD-09`** in
[design-room](https://github.com/nirmata78/design-room), an open-source system design interview
simulator, and the written companion to its mock-round video. It shows how a strong Staff candidate
(L6/L7) runs the round: what to say, what to draw, and **when**. A short stage-by-stage version
[lives in the repository](https://nirmata78.github.io/design-room/solutions/SD-09-chat-messaging.html).
This one adds the **why** behind every line, so you can defend each choice when the interviewer asks
*"why?"*, *"what is that?"* or *"what happens when it dies?"*.

**The document has three layers, and you'll read them differently:**

1. **Part I, the system in pictures.** Read it first. It explains what a person using the app
   experiences, what happens to one message millisecond by millisecond, and where the load lands.
   There's no interview script in it, only understanding.
2. **Part II, the round stage by stage.** This is what you do in the room. Each stage has a time
   budget, the words to say, what to draw, and boxes that explain every term.
3. **Part III, the internals.** How WebSockets, Raft, wide-column storage, Kafka and change data
   capture, Redis, and the phone push services actually work, at the depth a round reaches when you
   name a tool and the interviewer asks how it works.

**The coloured boxes:**

::: {.key title="Top-3 number"}
One of the three back-of-the-envelope numbers worth computing out loud in the round. In a real
interview you have time for two or three calculations, not ten.
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

**Practise in three passes.** (1) Read Part I and Part II once, end to end. (2) Close the document
and run the [simulator](https://github.com/nirmata78/design-room) cold:
`Read CLAUDE.md. Mock me: SD-09, Meta, staff, full round.`
(3) Debrief against the Stage 12 self-check, then reread only the sections where you fell short.
**Don't memorise numbers.** Memorise *the order of the argument* and how to rebuild each number in
twenty seconds.

**About the numbers.** The scale figures in Stage 1 are the simulator's cue sheet. Everything derived
from them is back-of-the-envelope arithmetic, and any planning assumption (sockets per host,
operations per Redis node, how often a phone reconnects) is labelled as one. They are not any
company's real figures, and this is not any company's actual design.

**The prompt as the interviewer reads it:**
*"Design a messaging system: one-to-one and group chats, for a billion users, with delivery and read
receipts and support for clients that go offline."*

::: {.key title="The one-sentence insight to land by minute 12"}
**Start from the mailbox, not the socket.** A message is **durably stored in its conversation log,
with a sequence number from the server, before anything is acknowledged**. Every device then catches
up by **cursor**: "everything after number 1,234". Pushing over a WebSocket is an optimisation that
delivers early, so online, offline and multi-device become one code path.
:::

::: why
**Why is this the insight?** Most candidates start with the connection: "Alice's socket, a server,
Bob's socket". Then they add a *pending* table for when Bob is offline, a retry for when the push
fails, a second copy for Bob's laptop. Each case is a separate path, and each path has its own way to
lose or duplicate a message. Start from the log instead and those cases disappear. There's one
question every device asks, *"what comes after my number?"*, and a device that was offline for a month
asks it the same way as one that was offline for a second. The socket only shortens the wait.
:::

\newpage

# Part I — The system in pictures

## Vocabulary you need first

Every term used later in the document, grouped by where it lives. When a word in Part II makes you
ask "what is that?", the answer is here.

**The product**

| Term | Meaning |
|-------|-----------------------------------------------------|
| **Conversation** | One chat: two people, or a group of up to 1,000. Everything in this design is partitioned by `conv_id` |
| **Device** | One installed app on one phone, laptop or tablet. A user has up to five, and they must converge |
| **One tick / sent** | The server has durably stored the message. Nothing more |
| **Two ticks / delivered** | A recipient's **app has stored** the message. It doesn't mean anyone saw it |
| **Read** | The recipient opened the conversation and the message was on screen |
| **Receipt** | The delivered or read signal that travels back to other people. A flow of its own, potentially larger than the messages |
| **Presence** | "Online now" or "last seen". A product feature with weak needs, and **a different thing from routing**, which must be right. Out of scope here (SD-13) |

**The log and its numbers**

| Term | Meaning |
|--------|----------------------------------------------------|
| **Conversation log** | Every message of one conversation, in order. The source of truth. Devices only hold caches of it |
| **Sequence number (`seq`)** | Assigned by the server, per conversation, with **no gaps**: 1, 2, 3 and so on. Its order is *the* order |
| **Cursor** | One device's position in one conversation: "I have everything up to N". Delivered and read each have one |
| **Client message ID (`clientMsgId`)** | A unique ID the phone picks once for a message, and reuses on every retry. It's what makes a retry harmless |
| **ACK** | The server's answer to `SEND`: "stored, here's your number". **An ACK is not a receipt**: it says nothing about any recipient |
| **Dedup table** | `(conv_id, client_msg_id) -> seq`, kept 14 days. Finds a retry and returns the original number |
| **Gap** | A device has N and receives N+2. Because numbers have no gaps, this proves N+1 exists and is missing |
| **Tier** | `SMALL` (up to about 32 members) or `LARGE`. Decides how receipts and offline wake-ups behave |
| **Inbox index** | Per user: *which conversations changed*, and when. Not the messages themselves. It tells sync where to look |

**Connections**

| Term | Meaning |
|---------|---------------------------------------------------|
| **WebSocket** | A long-lived, two-way connection that starts as an HTTP request. Appendix A |
| **Gateway** | A server that holds open WebSockets and has no business logic. It's sized by socket count |
| **Session registry** | In-memory map of device to gateway. Hot, small, and allowed to be slightly stale |
| **Heartbeat** | A small "still here" frame every 30 s or so. It keeps the connection and mobile network mappings alive and detects dead sockets |
| **Frame** | One message on a WebSocket: `SEND`, `ACK`, `MSG`, `DELIVERED`, `READ`, `SYNC`, `SYNC_PAGE`, `LIVE` |
| **Jitter** | A random delay before retrying, so a million clients don't retry in the same second |
| **TLS resumption** | A returning client reuses earlier session keys, skipping the expensive part of the handshake |
| **Drain** | Asking a gateway's clients to move away gradually before restarting it |
| **Thundering herd / reconnect storm** | Everyone reconnecting at once after a failure, overloading whatever they reconnect to |
| **Admission control** | Refusing or delaying work beyond capacity on purpose: here, *"sync later"* |

**The data layer**

| Term | Meaning |
|--------|----------------------------------------------------|
| **Wide-column store** | A table organised by a **partition key** (which replicas hold the row) and a **clustering key** (the sorted order inside). Appendix C |
| **Bucket** | `seq` divided by about a million, added to the partition key so a ten-year group doesn't become one unbounded partition |
| **Raft** | A consensus protocol. A leader appends to a replicated log, and an entry counts once a majority has it. Appendix B |
| **Raft group** | One leader and its followers, replicating one shard of the keyspace. We run about a thousand |
| **Term** | Raft's election counter. A leader from an old term is refused by everyone: this is **fencing** |
| **Quorum / majority** | More than half the replicas: 2 of 3 |
| **LSM tree** | The storage engine shape behind most wide-column stores: writes go to a log and memory, then sorted files. Appendix C |
| **Erasure coding** | Storing data as fragments plus parity. About 1.5× the data instead of 3× for three copies, with slower reads |

**Messaging**

| Term | Meaning |
|-------|-----------------------------------------------------|
| **Kafka-class log** | A durable, ordered, replayable log. Producers append, consumer groups read at their own pace. Appendix D |
| **Partition (of a topic)** | Order is guaranteed only inside a partition, so every event is keyed by `conv_id` |
| **CDC** (change data capture) | A connector reads the store's commit log and publishes each committed row |
| **Outbox pattern** | Writing an event to a table in the same transaction as the data, for a relay to publish. We don't need one here, and Stage 4 says why |
| **Dual write** | Writing the store, then publishing separately. A crash between the two loses the event |
| **At-least-once** | Something may arrive more than once, never zero times. The receiver must be **idempotent** |
| **Upsert** | Insert, or overwrite if present. Upserting by `(conv_id, seq)` makes a repeated message a no-op |
| **Coalescing** | Merging many updates to one key into one write |

**Phones and reliability**

| Term | Meaning |
|-----------|-------------------------------------------------|
| **APNs / FCM** | Apple's and Google's push services, the only way to wake a sleeping phone. Best-effort. Appendix F |
| **Collapse key** | Tells a push service that a newer notification replaces an older one |
| **p99** | 99% of requests are faster than this |
| **SLO / SLI** | A target we commit to, and the measurement behind it |
| **Probe device** | A synthetic client that sends and receives real messages all day to measure the system from outside |
| **E2E** (end-to-end encryption) | Only devices hold the keys. The server stores ciphertext it can't read |

\newpage

## What a person experiences

Before any architecture, here is the product from the user's side. Every box later exists to make
one of these moments true.

![One message's life on the sender's screen. Every state after SENT is a cursor comparison, not a stored record per message.](diagrams/sd09-message-states.pdf){width=62%}

**Step by step, with what the screen shows:**

1. **Alice types "See you there" and taps send.** The message appears at once with a clock icon. The
   app has written it to its own database with a fresh `clientMsgId`, so it survives the app being
   killed. It is *pending*, and it sits at the bottom of the chat without a place in the order yet.
2. **A moment later, the ACK arrives** with `seq = 1234`: about 25 ms inside our system, plus the phone's own network. One tick. The message slots into place in
   the order. If someone else's message got 1233 and arrived on Alice's screen afterwards, it now
   sorts above hers, and everyone in the chat sees the same order.
3. **Bob's phone is asleep.** A notification appears: *"Alice: See you there"*. That notification is a
   hint, not the delivery. Nothing about the message depends on it.
4. **Bob opens the app.** It connects, sends its cursor for each conversation, and receives everything
   it missed, in order. It stores the messages and tells the server: *delivered up to 1234*. Alice
   sees two ticks.
5. **Bob reads the chat.** The app sends *read up to 1234*, and in a small chat Alice sees that too.
6. **Bob's laptop opens an hour later.** Its cursor is older than the phone's. Same question, same
   code, a slightly longer answer. Bob's read state follows from the phone, so the laptop doesn't show
   the conversation as unread.

And in a group of 1,000:

7. **Nobody gets 999 delivery and read events per message.** The tick stays simple, and *"read by 412
   of 1,000"* is computed only when someone opens message info.

## The same story as one device's states

The device's side of the protocol is a small state machine. It's the clearest way to answer *"what
happens if the socket drops right here?"*: every failure sends the device back to a state that knows
what to do.

![The life of one device. There is no special offline mode: being offline only means the cursor is further behind when SYNCING starts.](diagrams/sd09-device-states.pdf){width=58%}

::: why
**Why is REGISTERED before SYNCING?** Because of a race Stage 6.7 walks through. A device registers
first, then reads. A message arriving during the read gets pushed too, and arrives twice, which is
harmless. The other order loses it. **Why does BACKOFF_SYNC keep the socket open?** The expensive part
of a reconnect has already been paid. If only sync is overloaded, new messages still arrive as pushes
while the device waits its turn.
:::

## Socket first against mailbox first

![The central contrast. On the left, two code paths and a crash window between them. On the right, one path: the sender appends to the log, and every device reads it.](diagrams/video-socket-vs-mailbox.pdf){width=100%}

![What a cursor buys. One gap-free log, three devices of one person, one question each. Offline is simply a cursor that's further behind.](diagrams/video-log-cursors.pdf){width=92%}

## One message, millisecond by millisecond

This is how the system behaves when Alice sends to Bob, who is online on a phone. The clock starts
at the gateway. The budget comes from Stage 4, and the rows after the ACK don't delay the ACK.

| Time | What happens | Who feels it |
|------|----------------------------------|--------------------|
| **0 ms** | The `SEND` frame reaches a gateway (the phone's own uplink comes on top) | One gateway thread |
| **~10 ms** | Gateway has routed it by `conv_id` to the partition leader | Message service |
| **~12 ms** | Leader checks dedup, assigns `seq = 1234`, appends one Raft entry | The conversation's partition |
| **~25 ms** | A follower confirms, so a majority has it: committed. **ACK leaves** | Alice sees one tick shortly after |
| **~50 ms** | The commit stream publishes `MessageStored` | Message log |
| **~125 ms** | A delivery worker consumes it, reads members and sessions | Registry |
| **~135 ms** | Worker hands a batch to Bob's gateway, with a 200 ms deadline | Gateway |
| **~235 ms** | Frame reaches Bob's phone over the mobile network | Bob sees the message |
| **~250 ms+** | Phone stores it and sends `DELIVERED`; the receipt service forwards the cursor | Alice sees two ticks |

## Where the load lands

The single most useful picture for the round. **Two different scaling dimensions**: the connection
tier is sized by *sockets*, whether anyone is talking or not, and the message path is sized by
*messages*. Mixing them up is the commonest sizing mistake.

![Load map at peak. Red is the only part that must be strictly correct. Every figure is derived in Stage 2, including the planning assumptions behind it.](diagrams/sd09-load-map.pdf){width=68%}

::: load
**Read the arrows.** 3.3 M heartbeats a second stop at the first box. 1 M sends become 1 M commits,
and those are the only writes that carry the guarantee. Everything downstream, pushes, inbox entries
and cursors, is rebuildable and may lag. So the system has a small strict core and a large forgiving
shell, and overload should always be shed from the shell.
:::

\newpage

# Part II — The round, stage by stage

**The clock** (a 45–60-minute round; simulator pace `realtime` or `hour`):

| Minutes | Stage | On the whiteboard |
|---------|---------------------------------|------------------|
| 0:00–0:06 | **Stage 1** Clarify requirements | Requirements list + "out of scope" box |
| 0:06–0:11 | **Stage 2** Back-of-the-envelope (two numbers, maybe three) | Three lines of arithmetic |
| 0:11–0:17 | **Stage 3** API and data model | Four frames, four tables |
| 0:17–0:27 | **Stage 4** High-level design + walk-through | Two container views |
| 0:27–0:45 | **Stage 6** Deep dives, **Stage 7** new requirements as they arrive | Changes marked on the diagram |
| 0:45–0:54 | **Stages 8–9** Failure modes, SLOs, cost | Short list |
| When asked | **Stage 10** The EM layer (auxiliary at Staff) | Team split, phasing |
| 0:54–0:56 | **Stage 11** The close | — |
| 0:56–0:60 | Your question | — |

Stage 5 (tool choices) has no slot. The interviewer can ask it at any time, and you answer inline.

**At the Staff bar you pick the deep dives** (`levels.md`). Don't wait to be asked. Say which two
you'd go into and why: the sequencer and the sync protocol, because that's where the guarantees live.

# Stage 1: Clarify requirements · 0:00–0:06

Ask **six or seven questions, not fifteen**. Each one changes the design, so say why you're asking.
The interviewer's answers below come from the simulator's cue sheet.

| I ask | Interviewer answers | Why it matters to the design |
|--------------|--------------|-------------------------------|
| Users, and how many connected at once? | 1 B users, 100 M connected | The connection tier is a cost of its own |
| Message rate? | About 1 M messages/s at peak | Log and storage sizing |
| Group size? | Up to 1,000 | Fan-out model; the receipt trap |
| Devices per user? | Up to 5, and they all converge | Every device needs its own position |
| **Which is worse: losing a message, or showing one twice?** | Neither is acceptable, and order must be the same for everyone | Durable write + idempotent send + one authority for order |
| Receipts? | Sent, delivered, read | A second message flow |
| History? | Full, for years, searchable by the user | Storage tiering, and a search index |
| Encryption? | Assume not end to end, but tell me what it would change | Server-side search against E2E is a real trade-off |
| Media? | Out of scope, text only | Removes the object store and CDN from the round |

::: why
**Why each question, in more depth.**

**Connected users.** One billion accounts tells you about storage. A hundred million *connected* tells
you about memory: those sockets exist whether anyone is talking or not. A different number gives a
different fleet.

**Group size.** With a limit of 5, copying a message into each member's inbox is fine. With 1,000 it
costs 1,000 writes per message. The answer decides the storage model.

**Devices.** If each user has one device, one "delivered" flag per user would do. With five, each
device must catch up independently, so a device, not a user, owns a cursor.

**Losing or duplicating.** It's a trick question, and asking it is the point. Guarding against loss
alone suggests retries; retries cause duplicates. Guarding against duplicates alone suggests "send
once"; that loses messages. *Neither* forces both a durable write and idempotency, which is the
spine of the design.

**Encryption.** If the answer were "yes", server-side search would disappear and the server couldn't
read bodies. You want that said before you draw a search box.
:::

**Functional (in scope):** send, deliver, sync, one-to-one and groups, sent/delivered/read receipts,
full history with user search, up to five devices converging.

**Non-functional:** delivered to online recipients in p99 < 500 ms; **zero loss once the sender sees
one tick**; a total order per conversation; history durable for years; send available 99.99%.

**Explicitly out of scope** (say it, write it in a box): media, voice and video, spam detection, the
push notification platform itself (SD-12), presence (SD-13). End-to-end encryption comes back as a
delta in Stage 7.

> "Presence is out, and I want to separate it from routing. Which gateway holds a socket is routing,
> and it has to be right. 'Online now' is a product feature, with far weaker needs. They look alike and
> they aren't the same system."

::: warn
**Don't ask about things you won't use.** "What's the tech stack?" and "which cloud?" sound thorough
and change nothing. Each question should visibly change a box on the whiteboard.
:::

\newpage

# Stage 2: Back-of-the-envelope · 0:06–0:11

## How to do estimates in an interview

You have about five minutes. **That is time for two calculations, three at most.** Pick the numbers
that **decide the design**, say each one as *number → consequence*, and round hard.

Below, the **top three** come first, in the order to compute them. The full table follows for your
understanding. You won't compute it all in the room, but you should be able to rebuild any row when
asked.

::: {.key title="Top-3 number 1 — The connection tier: 2 TB of RAM, 250–300 hosts, before a single message"}
**Arithmetic.** 100,000,000 sockets × about 20 KB each = **2 TB of memory**. At about 500,000 sockets a
host (a planning assumption, deliberately below what a tuned host can reach) that's 200 hosts; run
**250–300** for zone headroom.

**What 20 KB is.** Kernel socket buffers, the TLS session, the WebSocket read state and a little
application state. Appendix A says where it goes and how it gets smaller.

**How it changes the design.** Gateways are sized by **sockets, not requests**. A gateway host carries
about 12,000 pushes a second at 300 bytes, about 4 MB/s. That's nothing. So the fleet's limits are
memory and **blast radius**, and a host should hold no state you'd miss when it dies. That's why the
gateway has no business logic.

**Say:** *"A hundred million sockets at twenty kilobytes is two terabytes of memory just to stay
connected. At half a million a host that's two hundred hosts, and I'd run two hundred and fifty to
three hundred. Gateways are sized by sockets, and they hold nothing I'd miss."*
:::

::: {.key title="Top-3 number 2 — Storage: 20 TB a day, 20 PB a year with replicas"}
**Arithmetic.** 1,000,000 messages/s × 200 bytes = **200 MB/s**. × 100,000 seconds in a day (rounding
86,400 up) = **20 TB/day**. × 3 replicas = 60 TB/day. × 365 = **about 20 PB/year**.

**Be honest about it.** 1 M/s is the *peak*. The average is lower, so this is an upper bound, which is
the right number to plan capacity against and a slightly pessimistic one for the bill.

**How it changes the design.** One machine is out, and so is one sharded relational database without a
lot of pain. It needs a store partitioned by conversation and **tiering**: recent months on fast disks,
older years on cheap storage.

**Say:** *"Two hundred megabytes a second is twenty terabytes a day, sixty with three replicas, about
twenty petabytes a year. So a partitioned store keyed by conversation, and tiering from day one."*
:::

::: {.key title="Top-3 number 3 — The trap: one read in a big group is a million receipt deliveries"}
**Arithmetic.** A thousand members read one message. Each read receipt goes to the 999 others.
1,000 × 999 = **about a million deliveries for one message**.

**Why it's a trap.** Message traffic for that group is one write and a thousand pushes. The receipt
traffic is a thousand times that. Nobody notices, because "receipts" sound like a detail.

**How it changes the design.** Two rules. Receipts are **cursors** (`upToSeq`), so one frame covers many
messages. And **large groups never fan out receipts**: they store the cursor and count on demand.

**Say:** *"Receipts are the surprise. A thousand readers each telling nine hundred and ninety-nine
others is a million deliveries for one message, so the receipt flow is a thousand times the message
flow. In large groups I aggregate, and never fan out."*
:::

![The numbers as a picture. Top row: the connection tier, sized by sockets. Bottom row: the message path, sized by messages. The red box is the trap, found by arithmetic.](diagrams/video-load-funnel.pdf){width=92%}

## The full table, row by row

| Quantity | Arithmetic | Result | Consequence |
|---------|---------------|-----------|-------------------------|
| **1 · Sockets** | 100 M × 20 KB; ÷ 500 k a host | **2 TB; 250–300 hosts** | A dedicated, logic-free gateway tier |
| **2 · Storage** | 1 M/s × 200 B × 100,000 s × 3 | **60 TB/day; ~20 PB/year** | Wide-column store + tiering |
| **3 · Receipts** | 1,000 × 999 | **~1,000,000 per message** | Cursors; aggregate above a tier line |
| Heartbeats | 100 M ÷ 30 s | ~3.3 M/s | Stop at the gateway. Never in the message path |
| Registry refreshes | 100 M ÷ 300 s (batched) | ~330 k/s | A heartbeat isn't a registry write |
| Registry size | 100 M × ~100 B | ~10 GB | Fits in memory. Sized by operations, not bytes |
| Group fan-out | 1 message, 1,000 members | 1 log write vs 1,000 inbox writes | **Shared log + cursors** |
| Pushes | 1 M/s × ~3 online devices (assumed) | ~3 M/s | Batched by gateway, with deadlines |
| Registry lookups | 1 M/s × ~5 members (assumed) | ~5 M/s | About 50 Redis-class nodes. The load is reads, not data |
| Raft leaders | 1 M/s ÷ ~10 k/s per leader | at least 100; **run ~1,000** | No global sequencer. One authority per conversation |
| Dedup table | 1 M/s × 86,400 s × 14 days × ~50 B | ~60 TB raw, ~180 TB replicated | About 3% of hot storage. Worth a TTL, not worth a clever structure |
| Reconnects, normal | 100 M ÷ 3,600 s (assumed: hourly) | ~28 k/s | Sync is a hot path even on a good day |
| Reconnects, one zone | 33 M ÷ 600 s | ~55 k/s | The drain window is sized from sync's spare capacity |

::: why
**Why 3.3 M heartbeats don't matter, and 330 k refreshes do.** A heartbeat is a small frame answered
on the socket that received it. It costs a little CPU on the gateway and touches nothing else: about
13,000 a second per host. A *registry* refresh crosses the network to a shared store, so the gateway
batches them. One refresh every five minutes per device is 100 M ÷ 300 s = 330 k/s. If every heartbeat
wrote to the registry you'd have 3.3 M writes a second for nothing. In the room: *"Heartbeats stop at
the gateway."*
:::

::: why
**Why about 5 M registry lookups a second, for 10 GB of data?** Each message needs the sessions of its
members. Assume an average of five members per message (most chats are one-to-one, a few are large),
which is consistent with about three being online. 1 M × 5 = 5 M lookups a second. A Redis-class node
does on the order of 100,000 simple operations a second, so that's about 50 nodes for a data set that
would fit on one. **Sized by operations, not bytes.** You can cut it by batching lookups per gateway and
by caching a busy group's sessions in the worker for a second or two.
:::

::: why
**Why compute the dedup table at all?** Because *"keep every `clientMsgId` for 14 days"* sounds free. 1 M
a second for 14 days is 1.2 trillion rows. At about 50 bytes that's 60 TB, and 180 TB with replicas.
Against 5.4 PB of hot messages that's about 3%, so it's fine, and now you can say so. An estimate that
ends in "this doesn't matter" is still useful: it tells you where not to spend effort.
:::

> "Two numbers decided things. The storage number gives me a partitioned wide-column store with
> tiering. The receipt number gives me cursors and aggregation in big groups. The socket number is a
> cost line, and I'll come back to it when we talk about what happens when a gateway dies."

::: warn
**The classic estimation mistake** is computing ten numbers and drawing no conclusion from any of
them. The interviewer is scoring the *consequence* column. A number without a consequence is time
lost.
:::

\newpage

# Stage 3: API and data model · 0:11–0:17

## The API

The client talks to a gateway in **frames on a socket**. History and setup are plain REST.

```text
-> SEND  {convId, clientMsgId, body}         <- ACK {clientMsgId, seq, serverTs}
<- MSG   {convId, seq, senderId, body}       -> DELIVERED {convId, upToSeq}
-> READ  {convId, upToSeq}
-> SYNC  {cursors, lastSyncTs}               <- MSG..., SYNC_PAGE..., then LIVE

GET  /v1/conversations/{id}/messages?beforeSeq=...
POST /v1/conversations
POST /v1/conversations/{id}/members
```

**Sending, on the wire.** The ACK comes after the commit, and it carries the number.

```json
// -> SEND
{ "convId": 9001, "clientMsgId": "c-77a1...", "body": "See you there", "protocol": 4 }

// <- ACK
{ "clientMsgId": "c-77a1...", "seq": 1234, "serverTs": 1792130400123 }

// MessageStored, on the log, key = convId. The stored row itself is the event.
{ "convId": 9001, "seq": 1234, "senderId": 48213, "senderDevice": 2,
  "kind": "MSG", "tier": "SMALL", "body": "See you there",
  "serverTs": 1792130400123 }
```

**Delivering.** One cursor frame acknowledges many messages.

```json
// <- MSG
{ "convId": 9001, "seq": 1234, "senderId": 48213, "kind": "MSG",
  "body": "See you there", "serverTs": 1792130400123 }

// -> DELIVERED: the app stored it. Not that anyone has seen it.
{ "convId": 9001, "upToSeq": 1234 }

// -> READ
{ "convId": 9001, "upToSeq": 1234 }

// <- RECEIPT, small groups only
{ "convId": 9001, "userId": 7731, "state": "READ", "upToSeq": 1234 }
```

**Sync.** The device says where it is, and the server sends the difference.

```json
// -> SYNC
{ "cursors": { "9001": 1231, "4410": 88 }, "lastSyncTs": 1792127000000, "limitPerConv": 20 }

// <- MSG frames per conversation, in seq order, then:
{ "type": "SYNC_PAGE", "conv": 9001, "from": 1232, "to": 1234, "hasMore": false }

// <- LIVE: pushes carry on from here
{ "type": "LIVE", "serverTs": 1792130400500 }
```

**The API we call: the push platform, owned by another team (SD-12).**

```json
// POST /push/v1/notify  (internal RPC, X-Deadline-Ms: 100)
{ "userId": 7731, "collapseKey": "conv:9001", "title": "Alice",
  "preview": "See you there", "ttlSeconds": 86400, "priority": "HIGH" }

// 202 Accepted: { "notificationId": "n-5512", "devices": 2 }
// 429 Too Many Requests, Retry-After: 2
```

::: why
**Why is each piece there?**

- **`clientMsgId` in `SEND` and `ACK`.** The retry key. It's echoed back so the phone can match an ACK to
  a pending message even if several are in flight.
- **`protocol` in the frame.** A billion phones update slowly. Every client states its version so the
  server can keep old shapes alive (Stage 7).
- **`serverTs`, and why it isn't the order.** It's for display only ("10:04"). Sorting uses `seq`.
- **`upToSeq`, not a message ID.** One frame covers everything below it. A device that catches up on 500
  messages sends one `DELIVERED`, not 500.
- **`limitPerConv` in `SYNC`.** A phone back after a month shouldn't get a year of a busy group in one go.
- **`SYNC_PAGE.hasMore`.** It separates "nothing more" from "more than I'd send you now".
- **`LIVE`.** It tells the device the catch-up is over, so the UI can stop showing "updating".
- **The body inside `MessageStored`.** 200 bytes is cheaper than a read per delivery. At 3 M pushes a
  second, reading each body from the store would add millions of reads a second to spare the log 200
  bytes.
- **`collapseKey` and `ttlSeconds` on the push call.** A burst in one chat should show one notification,
  and a wake-up older than a day is useless.
:::

::: why
**Why a cursor, and not "give me everything since ten o'clock"?** Timestamps tie: two messages in one
millisecond, and "since" either misses one or repeats one. Replicas' clocks skew, so "since" can skip
a message written on a slower clock. A cursor says exactly where the device stopped, with no gaps, so
it can't skip anything, and it reveals a missing message. `lastSyncTs` does appear in `SYNC`, but only
to narrow *which conversations to look at* (and with an overlap margin), never as the position inside
one.
:::

::: why
**Why frames over a socket, and REST as well?** Frames carry the hot flows, where a persistent
connection pays off. History and group setup are request-response, rare, and benefit from everything
HTTP already has: caching, auth middleware, load balancers. Forcing them through the socket would
make the gateway smarter, and we want it dumb.
:::

## The data model

Start conceptual, in Chen notation: rectangles are entities, diamonds relationships, ovals attributes,
numbers cardinality.

![Conceptual model. A device tracking a position in a conversation is the key modelling choice: delivered and read sequence belong to that relationship, and to neither side alone. Message and Device are weak entities: a message has no identity without its conversation, and its partial key is seq.](diagrams/video-erd-chen.pdf){width=100%}

![The same model as physical tables. Red is the one that matters.](diagrams/video-erd.pdf){width=100%}

```sql
-- The truth. Wide-column. Rows are never rewritten except by an edit or a delete.
CREATE TABLE messages (
  conv_id       bigint,
  bucket        int,                  -- seq >> 20: about a million messages per partition
  seq           bigint,               -- clustering key: the order inside
  sender_id     bigint,
  client_msg_id uuid,
  kind          text,                 -- MSG, EDIT, DELETE; unknown kinds are skipped by old apps
  target_seq    bigint,               -- for EDIT and DELETE: which message
  body          text,
  server_ts     timestamp,
  PRIMARY KEY ((conv_id, bucket), seq)
);

-- The dedup table. Same Raft group as the message, written in the same entry. TTL 14 days.
CREATE TABLE client_msgs (
  conv_id bigint, client_msg_id uuid, seq bigint,
  PRIMARY KEY (conv_id, client_msg_id)
);

-- One row per conversation. last_seq is owned by the partition leader.
CREATE TABLE conversations (
  conv_id bigint PRIMARY KEY, kind text, tier text,     -- DIRECT|GROUP, SMALL|LARGE
  member_count int, last_seq bigint, home_region text
);

-- Membership, stored in both directions: a table can be partitioned only one way.
CREATE TABLE members_by_conv (conv_id bigint, user_id bigint, role smallint,
  join_seq bigint, left_seq bigint, PRIMARY KEY (conv_id, user_id));
CREATE TABLE convs_by_user   (user_id bigint, conv_id bigint, muted boolean,
  PRIMARY KEY (user_id, conv_id));

-- Positions. Only ever move forward: max(old, new). Written behind the hot tier.
CREATE TABLE device_cursors (user_id bigint, device_id bigint, conv_id bigint,
  delivered_seq bigint, read_seq bigint, PRIMARY KEY (user_id, device_id, conv_id));
```

::: why
**Why is each table shaped like this?**

- **`(conv_id, bucket)` as partition key.** Without a bucket, a busy ten-year group becomes one unbounded
  partition. The bucket is computed from `seq`, so finding it needs no lookup: `seq >> 20` means about
  a million messages, about 200 MB. Stage 6.8 explains how buckets fit with Raft, because there's a
  trap there.
- **`client_msgs` next to the message.** They're written in **one Raft entry**, so a message can never
  exist without its dedup row, or the reverse. That's what makes failover safe.
- **`last_seq` in `conversations`.** It's the only row with contention, and it only has one writer: the
  partition leader. Single-writer means no locks.
- **`join_seq` on membership.** A new member shouldn't see earlier history. Sync's starting point for
  them is `join_seq`, not zero.
- **Membership both ways.** Delivery asks "who's in this conversation?" and rebuilding an inbox asks
  "which conversations is this person in?". One partition key can't serve both.
- **`device_cursors` per device, not per user.** Five devices, five positions. A user's *read* state is
  the maximum across their devices.
:::

![Wide-column: three Raft groups, and in red, one partition. "Conversation 9001, everything after 1234" is one partition and one sequential read, already in order. That's sync, and that's history.](diagrams/video-wide-column.pdf){width=90%}

**The hot tier lives in memory**, around the one table that matters:

| Key | Type | Holds | Lost? |
|------------------|----------|------------------------|---------------|
| `session:{user}` | hash, TTL ~5 min | device -> gateway | Refills on heartbeats, in minutes |
| `gw:{gatewayId}` | string | address, `ACTIVE` or `DRAINING` | Gateways re-register |
| `members:{conv}` | set | user IDs (up to 1,000) | Read-through from `members_by_conv` |
| `inbox:{user}` | sorted set | conversation, scored by last change | Rebuilds from membership + `last_seq` |
| `cursor:{user}:{device}` | hash | conversation -> delivered, read | Device re-syncs, and dedups locally |

![How the hot keys point at each other. A push follows the top arrows, a sync the bottom ones.](diagrams/video-keys.pdf){width=100%}

![Where each key comes from: four writers, each driven by an event or a frame.](diagrams/video-writers.pdf){width=96%}

::: load
**Inbox index: about a terabyte, about 5 M upserts a second.** Assume 100–300 M active users with 50
recent conversations at about 100 bytes per sorted-set entry: 0.5–1.5 TB. A user away for months has
no inbox in memory; their first sync rebuilds it from `convs_by_user` and each conversation's
`last_seq`. Each message touches about five inboxes, so 5 M upserts a second before coalescing.
Coalescing helps a frenzied group enormously and a quiet one-to-one chat not at all, so the steady load
is really about that 5 M. It's write-heavy, batched by pipeline, and all of it rebuildable.
:::

**Six stores, one job each. Read the last column.**

| Store | Holds | Technology | Lose it? |
|---------|---------------------|--------------|--------------------|
| **Messages** | Every message, source of truth | Wide-column, Raft | Never: replicated |
| **Membership** | Who is in each conversation | Wide-column, both directions | Never: replicated |
| Device cursors | Delivered and read, per device | KV, write-behind to a table | A re-sync; device dedups |
| Inbox index | Which conversations changed | In-memory sorted set | Rebuild |
| Session registry | Device to gateway | In-memory, TTL | Refills on heartbeats |
| Search | Inverted index | Async from the log | Replay the log |

> "Two stores are the truth, and the rest can be thrown away. That's deliberate: most of what makes
> this fast is allowed to be lost, because it can be rebuilt from those two."

\newpage
# Stage 4: High-level design · 0:17–0:27

Draw the context first (30 seconds), then the containers, then **walk one message end to end, twice**:
once to a recipient who is offline, once to a recipient online on two devices.

::: why
**What are C4 levels?** C4 is a convention for architecture diagrams at four zoom levels.
**Level 1, Context:** our system as one box, plus the people and outside systems it talks to.
**Level 2, Containers:** the deployable pieces inside (services, databases, queues).
**Level 3, Components:** the parts inside one container. **Level 4** is code, rarely drawn. In an
interview you draw L1 in seconds, spend your time on L2, and zoom to L3 only in a deep dive.
:::

![C4 Level 1: system context. In grey, what we don't own: the push platform, and behind it Apple's and Google's push services, the only way to wake a sleeping phone. Those are other people's risks, managed with a deadline.](diagrams/video-c4-context.pdf){width=96%}

![C4 Level 2: containers on the send path. The ACK returns from the message service. Everything to the right of the store happens after it.](diagrams/video-c4-containers-send.pdf){width=100%}

![C4 Level 2: containers on the sync path. Receipts take the lower lane, at lower priority, so they can never delay messages.](diagrams/video-c4-containers-sync.pdf){width=100%}

**Every container, and why it's separate:**

| Container | Job | Why it is its own box |
|---------|----------------------|-----------------------------|
| Gateway | Holds sockets, heartbeats, frames in and out | Scales with sockets. Deploys and dies independently of logic |
| Message service | Partition leader: dedup, number, commit, ACK | The correctness core. Small, boring, heavily tested |
| Messages store | Log per conversation, membership | One of the two sources of truth |
| Message log (Kafka class) | `MessageStored`, keyed by conversation | A slow gateway must never stall a send |
| Delivery workers | Members, sessions, push, wake-up | Scales with fan-out, which is a different curve from sends |
| Session registry | Device to gateway | Hot, small, allowed to be stale |
| Sync service | What changed, then the difference | Takes the reconnect storm. Must be able to say "later" |
| Inbox consumer + index | Which conversations changed | Rebuildable, so it can lag and coalesce |
| Receipt service + cursors | Delivered and read positions | Lower priority. Larger than the message flow if left alone |
| Search | Inverted index, asynchronous | Never on the send path |
| Push platform (another team) | Wakes phones through APNs and FCM | Best-effort by nature, so it stays a hint |

## Two rules on the send path

**Rule one: commit before ACK.** A majority of replicas has the message before the sender sees a tick.
So the tick is a promise.

**Rule two: the row is the event.** Change data capture means a connector reads the store's commit log
and publishes each committed row.

::: why
**Why no transactional outbox here?** Normally you pair CDC with an outbox because a mutable table
makes a poor event: the row says what the state is, not what happened, and its shape is an internal
detail you don't want consumers depending on. So you write a dedicated event row in the same
transaction. Here, the `messages` row is **append-only and already shaped like an event**. An outbox
would store every message twice for no benefit. The log *is* the table. If an interviewer pushes:
edits and deletes are also appended rows with their own `seq` (Stage 7), so this holds for them too.
:::

## The walk-through: one message, end to end

The walk-through is where you prove the boxes work together. **In the room you say it in about two
minutes while pointing at the container diagram.** The sequence diagrams are for your understanding;
draw one only if the interviewer asks.

### Phase 1 — The commit, and the promise

![The commit in detail. The message and the dedup row travel in one Raft entry. A crash before commit means no ACK, so the app retries. A crash after commit means the retry finds the original.](diagrams/video-seq-commit.pdf){width=96%}

1. Alice's phone stores the message locally and sends `SEND {convId, clientMsgId, body}`.
2. The gateway routes by `conv_id` to the **conversation's partition leader**.
3. The leader checks for a duplicate, then takes `last_seq + 1`.
4. It appends one Raft entry containing the message and the dedup row, and waits for a majority.
5. Only then does `ACK {seq}` go back. One tick.

### Phase 2 — Bob is offline

![The whole trip with Bob offline. Bob's state played no part in Alice's ACK. Nothing is queued for Bob: the message sits at 1234, and Bob's phone will ask for it.](diagrams/video-seq-send.pdf){width=100%}

6. The commit stream publishes `MessageStored` to the log. A delivery worker consumes it.
7. It looks up Bob's session: no device online. It asks the push platform for a wake-up.
8. The inbox consumer, also reading the log, marks the conversation as changed for Bob.

### Phase 3 — What the worker branches on

![Two inputs, three branches: tier from the event, online or not from the registry. The sender's own other devices are recipients too.](diagrams/video-delivery-routing.pdf){width=100%}

9. An online device, in any tier, gets a batched push through its gateway with a 200 ms deadline.
   Offline in a small group: one notification per message. Offline in a large group: collapsed, at
   most one per conversation per minute.

### Phase 4 — The same message, Bob online on two devices

![Two pushes, each with a deadline, and each device acknowledges for itself, so each cursor moves separately. A failed push isn't retried by the worker: the log has it, and the device will get it.](diagrams/video-seq-online.pdf){width=100%}

### Phase 5 — Bob comes back

![The return. Registering comes before any read, and that order matters (Stage 6.7).](diagrams/video-seq-sync.pdf){width=96%}

10. The phone connects, resuming TLS. The gateway **registers the session first**.
11. The phone sends its cursors. The sync service asks the inbox which conversations changed, reads the
    messages after each cursor, and streams them, then `LIVE`.
12. The phone says `DELIVERED`. Alice sees two ticks.

> "Sends and deliveries are separated by a durable log. The send only has to reach a majority, so
> its latency and availability don't depend on who is online. Delivery can lag, retry or fail, and
> nothing is lost, because every device can always ask for what comes after its number."

## The code, for each path

Keep this level of detail for when you're asked "show me how". It's also the fastest way to find out
whether you really understand the design.

**The partition leader.** Dedup first, so a retry never burns a number.

```python
def on_send(frame):
    conv, key = frame.conv_id, frame.client_msg_id
    require_member(conv, frame.sender)                  # same Raft group, so a local read

    # a retry of something still being committed: attach to it, don't number it again
    if (conv, key) in in_flight:
        return in_flight[conv, key].then(lambda seq: ack(frame, seq))

    # the same clientMsgId again, already committed? return the original
    seen = client_msgs.get(conv, key)
    if seen:
        return ack(frame, seen.seq)

    # only the leader assigns; a stale leader is fenced by its term
    seq = last_seq[conv] + 1
    last_seq[conv] = seq                                # reserved now, so sends can pipeline

    # message and dedup row: one Raft entry, so both or neither
    entry = raft.propose(message(frame, seq), dedup_row(frame, seq))
    in_flight[conv, key] = entry

    # a majority has it: only now is the tick true
    return entry.then(lambda _: (in_flight.pop((conv, key)), ack(frame, seq)))
```

Each conversation is handled by one thread on its leader, so the check and the reservation can't
interleave. If the proposal fails, the leader has lost its term: it steps down and forgets its
in-memory `last_seq`, and the next leader reads it from committed state.

**The delivery worker.** Delivery is best-effort on purpose.

```python
def on_message_stored(event):
    members = cached_members(event.conv_id)
    sessions = registry.multi_get(members)
    # every device online gets a push, including the sender's others
    for gateway, devices in by_gateway(sessions, skip=event.sender_device):
        gateway.push_async(devices, event, deadline_ms=200)
    # offline users get a wake-up; large groups collapse them
    for user in offline(members, sessions):
        push_platform.notify(user, event, collapse=(event.tier == LARGE))
    # a failed push is fine: the log has it, the device will ask
    kafka.commit(event.offset)
```

**The sync service.** What changed, then the difference.

```python
def on_sync(device, frame):
    # the gateway registered this session before we got here
    if not admission.try_acquire(device):
        return device.send(RETRY_LATER, after=jittered_delay())     # the socket stays open
    changed = inbox.changed_since(device.user, frame.last_sync_ts - OVERLAP)
    for conv in newest_first(changed):
        after = frame.cursors.get(conv, member_join_seq(conv, device.user))
        page = messages.read(conv, after=after, limit=frame.limit_per_conv)
        device.send(page, has_more=page.has_more)
    device.send(LIVE)
```

**On the device.** Upsert by `seq`, check the gap, never get stuck.

```python
def on_msg(msg):
    cursor = local_cursor[msg.conv_id]
    if msg.seq <= cursor:
        return                                  # seen it before: a no-op
    local_db.upsert((msg.conv_id, msg.seq), msg)
    if msg.seq > cursor + 1:
        held[msg.conv_id].add(msg.seq)          # hold it back; fetch what is missing
        request_sync(msg.conv_id, cursor)       # coalesced: at most one in flight
        return
    # unknown kinds still advance the cursor: never get stuck
    # the next message may release others that were held back
    for m in contiguous_from(msg.conv_id, msg.seq):
        if m.kind in KNOWN_KINDS:
            apply_and_render(m)
        local_cursor[msg.conv_id] = m.seq
    send(DELIVERED, msg.conv_id, local_cursor[msg.conv_id])     # debounced in practice
```

> "At-least-once delivery, plus an idempotent device, is shown once. That's the only honest meaning
> of exactly-once here, and I'd rather say it that way."

## The latency budget

| Step | Budget |
|---------------------------|---------|
| Route and commit on a quorum | ~25 ms |
| Capture and log, to the worker | ~100 ms |
| Registry and hand-off | ~10 ms |
| Gateway to a phone, mobile network | ~100 ms |
| **Total, typically** | **~250 ms; under 500 ms at p99** |

::: why
**If the log lags, delivery slows, but sends and ACKs don't.** That's the value of the split, and also
its danger: the send-success SLO stays green while people wait. So consumer lag gets its own alert.
Say this before the interviewer asks.
:::

\newpage

# Stage 5: Why these technology choices · asked at any time

Requirement-drip and data-heavy rounds say it outright: *if you name a tool, be ready to defend it in
depth.* For each tool: why it fits here, the internals you must be able to explain, and the
alternative you rejected. Part III goes one level deeper on each.

## WebSockets for the connection

**Why here.** Both directions on one socket, at about 20 KB idle. Sending and receiving are equally
frequent, and a push must arrive unprompted.

**Internals to explain.** An HTTP/1.1 `Upgrade` turning into a framed two-way stream; ping and pong
frames; why a half-open TCP connection isn't noticed until you send on it; connection memory.

| Alternative | Verdict | Why |
|---------|-----|-------------------------------------|
| Long polling | Rejected | A hundred million clients re-polling costs more than holding sockets, and adds latency on every message |
| Server-sent events | Rejected | Server to client only, so sends need a second connection |
| MQTT | Viable | A real option, designed for phones. But brokers at this scale mean custom work anyway, and we'd still own the semantics above it |

## A Raft leader per partition for the numbers

**Why here.** The number and the message must be **one atomic log entry**. Then failover can't issue a
number twice, can't lose a number, and can't reorder.

**Internals to explain.** Leader election, quorum commit, term fencing, why the new leader's log contains
everything committed, and the no-op entry at the start of a term. Appendix B.

| Alternative | Verdict | Why |
|---------|-----|-------------------------------------|
| Redis `INCR` | Rejected | Replicates asynchronously. After a failover two messages can get one number |
| Quorum store with compare-and-set | Rejected | Paxos-class round trips on every send, with contention on the counter |
| Timestamp or Snowflake ID | Rejected for this | Sorts well and needs no coordination, but it has gaps, so a device can't tell a message is missing. It also can't give an order all participants agree was the arrival order at one authority |
| One global sequencer | Rejected | A bottleneck, for an order nobody can see across conversations |

::: why
**Why is the Snowflake rejection specific to this design?** Plenty of real chat systems use time-sortable
IDs and are fine. They rely on other means to find missing messages, such as asking the server for
ranges. The *gap-free* number is a choice that buys gap detection on the device. If the interviewer says
*"Discord-style IDs work in production"*, the right answer is *"yes, and they'd cost me that detection;
under 'never lose', I'd rather pay for a sequencer."* Hold the position with a reason and don't claim
the alternative is wrong.
:::

## A wide-column store for messages

**Why here.** Append-heavy, read by conversation in order, enormous volume. A partition is already
sorted by `seq`, so sync and history are sequential reads.

**Internals to explain.** Partition and clustering keys, LSM write path, compaction, bloom filters, and
why this workload suits it: writes are appends in key order, reads are short range scans. Appendix C.

| Alternative | Verdict | Why |
|---------|-----|-------------------------------------|
| Consensus-per-range store with a wide-column shape (the Raft-replicated family) | **Chosen** | One leader per range, sequence scans, and the number lives with the row |
| Cassandra or similar leaderless store | Viable | Wide-column and proven for chat, but with no leader, numbers need a separate sequencer, and you're back to a two-system commit |
| Sharded MySQL or PostgreSQL | Viable with pain | Mature and transactional. Resharding and 20 PB a year are the cost |
| Per-member inbox tables | Rejected | A thousand writes per message |

::: warn
**Don't say "Bigtable" and "Raft" as if they were the same thing.** Bigtable-class stores give you the
data shape and one server per tablet, but they get durability from a replicated file system rather than
a Raft group per range. Spanner, CockroachDB, TiKV and YugabyteDB run consensus per range. What this
design needs is the *property*: one authority per range, and a number committed together with its
message. Saying that shows you know the mechanism, and at Staff level the mechanism is what's scored.
:::

## A Kafka-class log for fan-out

**Why here.** Ordered per conversation, replayable, with delivery, inbox and search as independent
consumers. A new consumer costs the write path nothing.

**Internals to explain.** Partitions and keys, consumer groups, offsets, rebalances, `acks=all`, at-least-once.
Appendix D.

| Alternative | Verdict | Why |
|---------|-----|-------------------------------------|
| Leader calls delivery directly | Rejected | A slow gateway would stall sends |
| A plain work queue | Rejected | No replay and no per-key order |
| Dual write (row, then publish) | Rejected | A crash in between leaves it stored, but undelivered until someone happens to sync |

## An in-memory store for the hot tier

**Why here.** The registry, inbox and cursors are small per key, very hot, and **rebuildable**, so
losing a second of them is survivable. Appendix E.

**Rejected: the same wide-column store.** It would work, and would put millions of small mutable
writes a second on the store that holds the truth, for data we can afford to lose.

> "Each store matches one need. The Raft-replicated store is strict, which suits the numbers. The log
> is durable and replayable, which suits fan-out. The in-memory tier can lose a second, which suits
> routing. One store for everything would be too weak for the numbers, or too expensive for the
> routing."

\newpage

# Stage 6: Deep dives · 0:27–0:45

At Staff level **you choose**. Name them: *"I'd go into ordering and failover first, then the sync
protocol, because those carry the guarantees."* Expect the interviewer to pull in the lost ACK, groups
and the dead gateway, because those are the classic probes. **For each: state the risk, the mechanism
and the failure case**, in that order. Everything below is deeper than you'll say out loud. The boxes
marked "Say" are the spoken version.

## 6.1 Two people send at the same instant: who decides the order?

**The risk.** Different devices show different orders, a reply appears above the question it answers,
and the conversation stops making sense. Worse, everybody's history disagrees forever.

**The mechanism.** Not the clocks. One authority per conversation assigns numbers in arrival order.

![Clocks skew and users change them. Member Y's phone says an earlier time, but member X reached the leader first. X gets 501, Y gets 502, and every device renders 501 then 502.](diagrams/video-seq-order.pdf){width=92%}

That order is the truth for every participant on every device. Your own message shows as pending until
the ACK brings its number, then it slots into place.

::: why
**Why not a Lamport or vector clock?** They give you a causal order, and they let you detect that two
messages were concurrent, but then you still need a rule to break the tie so everyone renders the
same list. A single authority gives a total order at once, and because each conversation is small
compared with the system, you lose nothing by having one. **Does arrival order respect causality?**
Mostly, and that's a good probe. Alice's reply can only be sent after she received the message it
answers, so it always arrives at the leader later and gets a higher number. Causality within one
conversation is preserved by construction.
:::

**Why per conversation and not one sequencer for everything.**

![C4 Level 3: inside the message service. The conversation router finds the partition leader; the dedup check comes next; if it's new, the sequencer, in red, and the writer, which puts the message and dedup row into one Raft entry.](diagrams/video-c4-component-message.pdf){width=100%}

::: {.load title="Sizing the leaders: two constraints, not one"}
**Throughput.** 1 M messages/s at about 10,000 per leader is 100 leaders at minimum. Group commit is what
makes 10,000 realistic: the leader batches many entries into one disk flush and one replication round.
**The busiest group** is hundreds of messages a second, which one leader handles.

**Storage.** With 90 days hot, 1.8 PB of raw data over 1,000 groups is about 1.8 TB per group, an
ordinary size. With 100 groups, 18 TB per group makes every replacement of a failed replica a very long
copy. So storage is what pushes the count to **about 1,000**, at about 1,000 messages a second each.

**In practice** you'd run more groups than hosts, several per machine, so you can move them around.
:::

### Your leader dies, mid-write

This is the question that separates "a leader" from Staff.

![Failover. The old leader (term 5) appends 900 to follower 1 and dies before a majority confirms. No ACK reaches the phone. Follower 1 wins the election, since its log is the most complete. The phone retries with the same ID, and the dedup row is in that same entry, so the new leader returns 900.](diagrams/video-seq-failover.pdf){width=96%}

**The two branches, both safe:**

| What survived | What the new leader does | What the phone sees |
|---------------|------------------------------|---------------------|
| Entry 900 reached a follower that wins | Commits its log tail (with a no-op in its own term), so `last_seq = 900` | The retry finds the dedup row, and gets 900. One copy |
| Entry 900 reached nobody who wins | Its `last_seq = 899` | The retry is new, and takes 900. One copy |

If the old leader comes back, it's on term 5. Everyone else is on term 6, so its messages are refused,
and it learns it's no longer leader. That's **fencing**, and it means a paused leader can't assign a
stale number after waking up.

::: why
**Why is the number gap-free across a failover?** Numbers are assigned in log order, and Raft's log
matching property says a follower with entry *k* has every entry before it in the same order. So
"901 survived but 900 didn't" can't happen within one conversation. Any entry that's lost is lost
along with everything after it, and those numbers get reassigned to messages that were never
acknowledged. **Nobody ever saw those numbers**, because a number leaves the leader only in an ACK
after commit, or in an event from committed state.

**How does the new leader know `last_seq`?** It's in committed state: the `conversations` row, updated
by the same entry. The leader holds a cache in memory, loaded on first use after taking over.

**How long does a failover take?** Raft's election timeout, usually configured around a second in
production to avoid false elections, plus the first commit. **Sends to that partition stall for
seconds. That's the honest cost.** About a thousandth of conversations pause, and everything else
carries on.
:::

**Hot conversation.** One leader serves it. A thousand-member group at 100 messages a second uses about
1% of a leader. If the interviewer invents a much hotter one, move that conversation's range to its
own group. The next constraint isn't the sequencer anyway, it's delivery fan-out (worked delta 3 in Stage 7).

> "One authority per conversation. Failover can pause it, never reorder it. The number and the message
> are one Raft entry, so a new leader either has both or neither, and a stale leader is fenced by its
> term. The cost is a few seconds of stalled sends on that partition, and I'd say that out loud."

::: warn
**Weak answers to avoid.** "Sort by timestamp": clocks skew, and users change them. "Kafka gives me
ordering": it does, per partition, but then the number comes from an offset, and `SEND` can't be ACKed
with it until after publish; you've moved the sequencer into Kafka without saying so. "Use a distributed
lock": a second system whose failure modes you now own, for something a leader already gives you.
:::

\newpage

## 6.2 The lost ACK: every crash point

**The risk.** The server stored the message, but the phone went into a tunnel and never got the ACK.
If the app retries blindly, a duplicate appears on every screen. If it doesn't retry, a message
may be lost.

**The mechanism.** A retry reuses the same `clientMsgId`, and the dedup check returns the original
number.

![The lost ACK. Commit as 1234; the ACK goes out and the tunnel swallows it. The app still shows pending. When the network returns it retries with the same ID, the dedup table has it, and the ACK returns the original number.](diagrams/video-seq-lost-ack.pdf){width=96%}

**Every crash point has one outcome:**

| Crash point | State on the server | What the app does | Result |
|-------------|--------------------|-----------------|-----------|
| Before reaching the leader | Nothing stored | Retries | Stored once, as new |
| Leader appended, no majority | Maybe a log tail | Retries | Stored once, either way (6.1) |
| After commit, before ACK | Stored, dedup row present | Retries | Returns the original |
| App killed and restarted | Depends on the above | Reads pending messages from its local database, retries each with the same ID | Same as the above |
| Worker crashes after the commit | Stored | Nothing | Log replays; a device gets a second push; upsert makes it a no-op |

**The two details that make it correct:**

1. **Dedup has to come before numbering.** Otherwise a retry burns a number and leaves a gap, and every
   device would think it had lost a message.
2. **The dedup table only protects after commit.** Between the first try's proposal and its commit, a
   second try would read "not in dedup". So the leader keeps an in-flight map as well.

![Why the leader needs an in-flight map as well as the dedup table. A fast retry arrives while the first try is still being committed.](diagrams/sd09-seq-retry-inflight.pdf){width=62%}

::: why
**Why not assign the number when the entry is applied, inside the state machine?** You can, and it's
elegant: the entry says "append this", and the deterministic apply step does the dedup and takes the
next number on every replica. Then no in-flight map is needed, and a duplicate entry is harmless. The cost
is that the leader doesn't know the number until apply, and duplicates still consume log space and a
replication round. Both are correct. Pick one and know the other exists.

**How long do you keep the dedup rows?** Fourteen days. The app stops retrying after seven, then shows
*failed*, and a manual resend is a new ID. **The window always covers the retry**: the rule to state is
*retry horizon < dedup TTL*. At about 180 TB replicated, that's about 3% of hot storage.

**Why does the phone generate the ID, not the server?** The whole point is that it exists before
any network call. If the server issued it, the first request could itself be lost.
:::

> "The tick appears only after a real ACK, so a message is never shown as sent when it wasn't. And a
> retry never shows twice, because dedup comes before numbering, in the same entry as the message.
> I keep dedup rows for fourteen days and stop retrying at seven, so the window always covers the
> retry."

::: warn
**A claim that breaks under follow-up:** "exactly-once delivery". Nobody has it end to end. What you have
is **at-least-once plus idempotent receivers**, and it looks the same to the user. Say it that way.
:::

\newpage

## 6.3 Groups: copies or a shared log?

**The probe.** *"Group of a thousand. Do you copy each message into a thousand inboxes? Defend that, or
don't."*

![Shared log against per-member copies. One write, one row per edit, storage times one. Each member just has a cursor into it.](diagrams/video-groups.pdf){width=92%}

| | Per-member inbox copies | **Shared log + cursors** |
|--------|--------------------|---------------------|
| Write per message | 1,000 | **1** |
| One edit | 1,000 updates | **1 row** |
| Storage | × group size | **× 1** |
| Read | Own inbox, simple | Each changed conversation after the cursor |
| Who it suits | Very small groups, feed-style reads | **This problem** |

One-to-one chats use the same model, so there's one code path.

**The follow-up.** *"But you have an inbox index per user. Isn't that a thousand writes after all?"*
It would be. So here's the arithmetic, for a thousand-member group in a frenzy at 100 messages a second:

| Design | Writes a second | What's in them |
|--------|--------|--------------------------------|
| Copies | 100,000 | Full bodies, on the send path |
| Inbox update per message | 100,000 | Small entries, off the send path |
| **Inbox, coalesced to once a second** | **1,000** | "This conversation changed" |
| The log itself | 100 | The truth |

The inbox only says *this conversation changed*, and that fact **overwrites itself**. So the consumer
writes it at most once a second per user and conversation.

::: warn
**Coalesce on the trailing edge.** A consumer that writes the first event in each second and drops the
rest will miss the *last* message of a burst, and that conversation looks unchanged forever. Keep a
pending set, and flush it each second. For the same reason, `changed_since` reads with a small overlap,
so a write near the boundary isn't missed. Nothing is lost if it reads too much: the cursor decides
what comes back.
:::

### Membership changes

**A membership change is a log entry too**, which removes a whole class of races. It takes a `seq`, and
`join_seq` is that number.

![Adding a member. The member row and the event are one Raft entry, so join_seq is exact: everything from it onward is visible, and nothing before.](diagrams/sd09-seq-membership.pdf){width=96%}

::: why
**Why does membership need to be that careful?** Because the check for "can this person read this
message?" has to have one precise answer. *"Added at 10:04"* against a timestamped message has the
clock problem all over again. *"Added at seq 5000"* doesn't. **The removal case is the harder one:** a
cached `members:{conv}` set can stay stale for a few seconds, so a removed member can receive a few
more pushes. That's why sync and history check the table, not the cache. If the interviewer says that's
not acceptable, the membership change invalidates the cache before it's acknowledged, at the cost of
some delay on the membership call, which is rare.
:::

> "A shared log, with a cursor per member. The per-user inbox only says what changed, and it overwrites
> itself, so a frenzied thousand-member group costs a thousand small writes a second, off the send
> path, against a hundred thousand with copies."

\newpage

## 6.4 Receipts are cursors, and the tier line

**The risk.** The receipt flow quietly becomes the largest thing in the system, and delays messages.

![Receipts as cursors. The reader sends READ up to 1240. The service keeps the larger value, so a late frame can't move a cursor back. In a small group, forward the cursor. In a large group, nothing is forwarded, and message info counts on demand.](diagrams/video-seq-receipts.pdf){width=96%}

**Why thirty-two, and not a hundred?** Because the cost is squared:

| Members *n* | Per message: *n* × (*n* − 1) | Policy |
|------|--------------|-------------------------|
| 2 | 2 | Forward |
| **32** | **~1,000** | **Forward: the line, a config value** |
| 100 | ~10,000 | Aggregate |
| 1,000 | ~1,000,000 | Aggregate; "read by 412" on demand |

> "A cursor coalesces a burst of messages, but it doesn't shrink the audience. The tier does that. I'd
> start the line around thirty-two, make it a config value, and measure."

**How "read by 412 of 1,000" is computed.** Read `members:{conv}`, multi-get each member's cursors, take
the maximum `read_seq` across a member's devices, and count those at or above the message's `seq`. That's
about a thousand key reads. It happens only when someone opens message info, which is rare, and the
answer can be cached for a few seconds.

::: why
**Three more things a receipt design has to answer.**

**Multi-device read state.** Bob reads on the phone; the laptop shouldn't show unread. A `READ` cursor is
also forwarded to **the user's own other devices, in every tier**. That's at most four frames, so the
squared cost doesn't apply.

**The write rate.** About 3 M pushes a second could become 3 M `DELIVERED` frames. The device debounces
(one frame per conversation per second or two), and the receipt service writes to the hot tier, flushing
to `device_cursors` behind it. A lost cursor update is harmless, because the next one covers it:
`max(old, new)` makes the flow idempotent and order-independent.

**Unread counts.** `last_seq - read_seq` is tempting and slightly wrong, because edits and deletes take
numbers too (Stage 7), and so do your own messages. It over-counts. Most apps accept that for a badge,
or have the device compute the exact number from its local data. Say which you chose.
:::

::: warn
**The trap in the name.** `DELIVERED` means *the app stored it*. It doesn't mean anyone saw it, and the
cue sheet checks for this. A candidate who treats an ACK from the client as "displayed" has built the
wrong receipt.
:::

**Receipts travel at lower priority**, on a separate lane through the gateway and a separate service. When
something has to give, receipts lag before messages do. Nobody calls support because a tick was late.

\newpage
## 6.5 A gateway dies with half a million connections

**The first sentence to say:** the messages are safe. They were never in the gateway. **What isn't
safe is the reconnect.**

![The reconnect. Half a million sockets drop. Each device waits a random delay of up to sixty seconds. The load balancer picks the least-loaded gateway, TLS resumption saves most of the handshake, and sync is a small delta. If sync is over capacity it answers retry-after, and the device stays connected.](diagrams/video-seq-reconnect.pdf){width=96%}

**The arithmetic:**

| Event | Devices | No jitter | With jitter |
|---------|-------|-----------|----------------------|
| One gateway | 500 k | 500 k in ~2 s (250 k/s) | Over 60 s: ~8 k/s |
| One zone, a deploy gone wrong | ~33 M, a third | 33 M in ~2 s | Drained over 10 min: ~55 k/s |
| Sync reads, one zone | 55 k/s × ~10 changed conversations (assumed) | — | ~550 k reads/s |

::: load
**Why the single gateway isn't the real case.** 8 k/s is small next to the roughly 28 k/s of normal
reconnects (assuming each device reconnects about once an hour). **A zone is the real case**, at about
twice the normal rate, and each reconnect brings about ten reads. So the drain window is a calculation:
*spare sync capacity ÷ reads per reconnect = reconnects a second I can absorb*, then *33 M ÷ that =
how long the zone takes to come back*. Ten minutes is an output of that sum, not a magic number.
:::

**Five layers of defence, in the order they act:**

1. **Client jitter.** A random delay with exponential backoff, built into the app. It's the cheapest
   mitigation in the system, and **it has to be there in version one**, because you can't add it later
   to phones already out there. Have the server able to send a delay as well, so you can change it
   without shipping an app.
2. **TLS resumption.** A full handshake costs on the order of a millisecond of CPU for the signature,
   so 250 k/s would be hundreds of cores' worth of handshakes. A resumed session skips the signature.
3. **Least-loaded placement.** Sockets are long-lived, so round robin leaves the restarted host empty
   and others full. Balance on connection count, and cap per host.
4. **Cursor-based sync.** A reconnect after a short drop is a small delta, so most syncs are cheap.
5. **Admission control on sync.** If sync is over capacity, it answers `RETRY_LATER`, with jitter, and the
   device stays connected and keeps receiving live pushes. Being able to say *"later"* is what stops a
   storm from turning into an outage.

::: why
**Why does the sync request come after the socket, and not with it?** Because they fail differently. If
connecting and syncing were one step, an overloaded sync service would refuse the connection, the device
would retry the connection, and the retries would add TLS handshakes to the overload. A retry storm is
how a small failure becomes a large one. Keeping them separate lets a device hold a cheap connection
while it waits for an expensive read.

**How does a dead gateway get noticed?** The other side of a dead socket hears nothing, so devices use
the heartbeat: no pong within about two intervals means reconnect. On the server side the registry entry
just expires: until then a push to that gateway fails at once, the message stays in the log, and the
device will ask for it on reconnect. A stale registry costs a wasted call, never a message.

**Graceful drain on deploys.** The gateway marks itself `DRAINING` in `gw:{id}`, and the load balancer stops
sending it new connections. It then asks clients to move, a few at a time, over minutes. So a deploy never
causes the storm it would otherwise look like. **A pipeline should enforce this**, as Stage 8 shows.
:::

> "The messages are safe, they're in the log. The risk is half a million reconnects at once. Jitter in
> the client turns the spike into a slope, resumption cuts the handshake, cursors make each sync small,
> and admission control caps the rest. The real case is a whole zone, so I size the drain window from
> sync's spare capacity."

## 6.6 Coming back after a month

**The risk.** A year's worth of a busy group arrives over a mobile connection, the app freezes, the
battery drains, and the sync service gets a very large read for one device.

![A month offline. Newest conversation first, newest twenty messages of each: useful in a second and capped per device. The phone records a hole, and older pages arrive only when the user scrolls.](diagrams/video-seq-month.pdf){width=96%}

1. `SYNC`, with cursors a month old. If the inbox key is gone, the server rebuilds it from
   `convs_by_user` and each conversation's `last_seq`, comparing with the device's cursors.
2. The inbox lists 180 changed conversations.
3. The service reads the **newest twenty messages of each, newest conversation first**. The app is
   useful in a second, then `LIVE`.
4. The phone records a **hole**: conversation 9001, from 1,240 to 8,700.
5. When the user scrolls up, it fetches an older page through the REST history call. The hole shrinks.

::: why
**A hole bends the meaning of "cursor".** A cursor says *"I have everything up to N"*. After this sync, the
phone has 8,701 onward, and a hole. So the protocol has two values: the **live cursor** (8,720, where sync
continues from) and a **local list of holes**. Gap detection compares against the live cursor only.

**What does the `DELIVERED` receipt mean for a message in the hole?** Strictly, the app hasn't stored it. In
practice, Bob's device reports its live cursor, and Alice's month-old message goes to two ticks. Say this
is a deliberate choice: nobody is waiting on a month-old tick, and tracking per-message delivery across a
hole would cost far more than the meaning it adds. Naming a small lie you're choosing to tell is a Staff
habit. Pretending it isn't there is the alternative.
:::

## 6.7 The sync protocol: three races and a hole in the tail

This is the deep dive to choose yourself, because it's where the *"never lose"* promise is actually kept.

### Race 1: registering after reading

| Order | What happens to a message landing during the read |
|--------|-------------------------------------------------|
| Read, then register | The read has passed it, and the worker sees no session. **It's in neither. Lost until the next sync** |
| **Register, then read** | The worker pushes it, and the read may return it too. **It arrives twice, and the device upserts by `seq`** |

> "Register first. A window where a message can arrive twice is fine, because the device is idempotent. A
> window where it can arrive zero times is not."

### Race 2: a push fails while the device stays connected

![Gap-free numbers pay off. The laptop is at 1234 and receives 1236: the push of 1235 timed out. It sees the gap, holds 1236 back and syncs from 1234. The upsert makes the second copy of 1236 a no-op. Loss becomes detectable, on the device.](diagrams/video-seq-gap.pdf){width=96%}

### Race 3: live pushes during a sync

While pages are streaming, live pushes arrive too, possibly with higher numbers than the current page.
The same `on_msg` handles this: held by `seq`, and released in order. The device doesn't need to know
which source a message came from, which is exactly the point.

### The hole in the tail

Gap detection has a blind spot. **It needs a later message to reveal the missing one.** If the last message
in a conversation is the one whose push was lost, nothing follows it, and a connected laptop looks
perfectly up to date. The worker has already committed its offset. In a quiet chat, that message could stay
missing for hours.

![The tail loss. Nothing follows 1241, so there's no gap to see. A periodic head check closes it.](diagrams/sd09-seq-tail-loss.pdf){width=78%}

**The fix: a periodic head check.** Every few minutes, a connected device asks which conversations have
changed since its last check, using the same inbox call as sync. If a head is past its cursor, it syncs
that conversation.

::: load
**The cost.** 100 M devices ÷ 300 s = about 330 k inbox reads a second. That's about the same as the
registry refresh, and it can ride on the same batched timer. Almost all answers are empty, and those
never touch the message store. It's a modest price for closing the only silent-loss window in the design.
The interval is the worst-case delay for that case, so it's also a product decision.
:::

**Half-open sockets are why this matters.** A mobile network can drop a connection with no signal to
either side. The gateway's `write` succeeds into a kernel buffer, and the frame never arrives. So *"the
push succeeded"* means very little, and it's why delivery confirmation comes from the device's
`DELIVERED`, never from the socket write.

> "Three repair mechanisms, all using the same read: sync on reconnect, sync on a gap, and a periodic
> head check for the last message, which has no later message to reveal it. Push only makes it faster.
> So a lost push is a delay, not a loss."

\newpage

## 6.8 Storage: buckets, Raft and twenty petabytes a year

**The risk.** A partition that never stops growing, a table that gets more expensive every month, and a
placement mistake that quietly breaks the atomic commit.

### Buckets and Raft: the trap

The partition key is `(conv_id, bucket)`. If each bucket hashed to a different Raft group, then the row for
message 1,048,576 would go to one group, and `last_seq` would live in another. **The message and its number
would no longer be one Raft entry**, and the whole of 6.1 would quietly stop being true.

So: **`conv_id` alone chooses the Raft group, and the bucket is a sort prefix inside it.** All of a
conversation's live data is in one group. `bucket` bounds the unit of compaction and the unit of
tiering. When a bucket closes (the conversation has moved past it), it becomes immutable, and it can
leave the group for colder storage.

::: warn
**This trap isn't obvious from the diagram.** "Partition key = conv + bucket" reads like the hash input, and
in a plain Cassandra-style store it would be. Say out loud which key routes to the consensus group. Then
a question like *"what happens at the bucket boundary?"* has a one-line answer: nothing, it's the same
group, and the write path doesn't notice.
:::

### Tiering

| Tier | Age | Copies | Holds | Read cost |
|-----|-----|-------|--------------|------------|
| Hot, on fast disks | 0–90 days | 3 replicas, Raft | 5.4 PB | Milliseconds |
| Cold, on object storage | 90+ days | Erasure coded, about 1.5× | Closed buckets as compressed files | Tens to hundreds of ms |

If it all stayed hot, a year is 22 PB. Cold copies at about 1.5× the data are half the bytes of three
replicas, on media that costs less per byte. And almost nobody reads a message from three years ago,
which makes this the rare trade-off with little downside.

::: why
**Why does `seq` make tiering easy?** A closed bucket is immutable and self-contained. It's a sorted run of
rows with no further writes, which turns into one compressed file with a simple index. The read path
knows from `seq` alone which bucket to look in, and from metadata whether that bucket is hot or cold, so it
needs no per-message lookup.

**What about edits and deletes in a cold bucket?** The row update is the awkward case, and it's rare. Keep
a small overlay of edits in the hot tier and merge at read, then rewrite the file during compaction. A
*delete for everyone* must physically remove the body, so that rewrite has a deadline. Stage 7 covers this.
:::

### Search: "per user" needs a second look

The requirement is *searchable by the user*. The obvious structure is a per-user inverted index, and for
one-to-one chats it's fine. In a thousand-member group, it would write each message's terms into a
thousand indexes: **the fan-out problem we just avoided, back through the side door.**

| Design | Indexing per message | Query |
|--------|---------------|---------------------------|
| Per-user index | One write per member | One index, simple and fast |
| **Per-conversation index for groups** | One write | Query the user's conversations, filtered by `join_seq` |
| A hybrid | One-to-one chats per user, large groups per conversation | Merge two result sets |

The search consumer reads the log at the lowest priority, so it can lag by minutes without anyone noticing,
and it can be rebuilt by replaying. Keep the recent years indexed; older ones can be indexed on demand.

## 6.9 The whole system under load: how it degrades

A Staff answer states the **order in which things give way**, because that's what you'd want on a runbook.

| Priority | Flow | When overloaded | What the user sees |
|-----|-------|------------------------|----------------------|
| 1, never shed | `SEND` → commit → ACK | Stalls only if the partition has no leader | Sent, one tick |
| 2 | Live push | Deadlines drop; the device repairs by gap or head check | Slower arrival |
| 3 | Sync | `RETRY_LATER`, with jitter; smaller pages | "Updating..." for longer |
| 4 | Wake-ups | Collapsed harder, then sampled | Fewer notifications |
| 5 | Inbox index | Lags, coalesces more | Sync finds changes a little later |
| 6 | Receipts | Forwarding pauses; cursors still stored | Ticks late |
| 7 | Search indexing | Pauses | New messages not searchable yet |

::: load
**Why is that order safe?** Everything from row 2 down is derived from the log, and it can catch up from
the log. Shedding any of it loses nothing but time. The system has one thing it may never drop, the commit
behind a tick, and that's why the commit path has no dependency on anything below it. Check that claim on
the diagram: the leader doesn't call the registry, the log, or anything else before the ACK.
:::

## 6.10 Regions

**The probe.** *"A whole region goes down. What about 'zero loss'?"*

![Conversations are homed in one region. A send from elsewhere is forwarded to the home leader. Replication between regions is asynchronous, so region loss has a cost that must be stated.](diagrams/sd09-regions.pdf){width=70%}

| Option | Send latency | Region loss | Fits when |
|--------|--------|--------------------|-------------------|
| **Home region, async replicas** (default) | ~25 ms at home, +~100 ms from elsewhere | Last seconds of acknowledged messages may need reconciling | Most conversations are regional, and availability wins |
| Raft quorum across nearby regions | +10–30 ms everywhere, for nearby regions | Nothing lost | You'd pay for strict zero loss, for some conversations |
| Quorum across continents | +100 ms or more on every send | Nothing lost | Rarely worth it for chat |

> "Inside a region, zero loss is exact: three zones, quorum commit. Across regions I'm replicating
> asynchronously, so losing a whole region can lose seconds of acknowledged messages. I'm stating that,
> not hiding it. If the business needs it closed, a cross-region quorum costs that round trip on every
> send, and I'd do it per conversation, for the ones that need it."

::: why
**How does the home move?** Each conversation has a `home_region`, chosen from its first members. If everyone
moves, or a user migrates, you can move it with a brief pause: stop accepting sends, let replicas catch
up, change the leader, carry on. **What does reconciling mean after a region failover?** Messages
acknowledged in the old region and not yet replicated exist only there. When it returns, they may
conflict with numbers the new home has issued, so they're re-appended with new numbers. Their order
changes, which is why you state the risk rather than promise zero.
:::

\newpage

# Stage 7: Requirements that arrive mid-round · as given

The mid-round change measures **adaptation**, not knowledge. For every one: **say what changes, what
doesn't, and what it costs**. A silent redraw scores lower than a small, named change.

::: why
**Why does a strong candidate look lucky here?** Because the design already has one seam that absorbs most
of them. A log with a number on every entry means any new kind of event gets ordering, offline
delivery and multi-device for free. Naming that seam before the requirement arrives is what the
format is looking for.
:::

## Worked delta 1: edit and delete, for everyone, retroactively

**What doesn't change:** the log, the sequencer, cursors, sync. **What changes:** one new `kind`, and one
row update.

![The delta. An edit is another message in the log, with its own number and a target. It's one Raft entry with the update of the original row. The old app skips the unknown kind and still moves its cursor.](diagrams/sd09-seq-edit.pdf){width=100%}

Because the log is the single source of truth, an edit is an event: kind `EDIT`, naming the target, with its
own `seq`. A delete is the same. Online, offline and multi-device already work, and cursors move past it
like anything else. **Had we copied messages into inboxes, every edit would be a thousand writes.**

**The real cost is on the clients.** A billion phones update slowly.

- **Version the protocol.** The first frame carries a version, and the server keeps old shapes alive for the
  supported window.
- **Unknown is harmless.** An old app ignores an unknown kind and **still advances its cursor**. It shows the
  original text, and it doesn't get stuck.

> "That rule has to be there in version one. You can't add it later to phones already out there."

::: warn
**A delete has a promise an edit doesn't.** *Delete for everyone* has to mean the text goes away, and not
only from screens. That includes the row, the cold-tier file (a rewrite with a deadline), the search index,
and the event body on the log, which ages out with retention. An old app still shows the original, and you
can't change that on a device you don't control. Say so: this is best-effort on devices, enforced on servers.
:::

## Worked delta 2: end-to-end encryption

*"The CEO announced end-to-end encryption on stage. Product wants a date by Friday."* It's also a judgement
probe: the date comes out of the decision, not the other way round.

| Part | Effect | Detail |
|-----|-----|-------------------------------|
| **Stays** | Log, numbers, cursors | The server orders ciphertext it can't read, so the core survives |
| **Breaks** | Server-side search | It moves to the device, and to each device's local history |
| **Costs** | Group fan-out | Encrypted per device; sender keys reduce that to one ciphertext per message (Appendix G) |
| **Costs** | New-device history | A new device can't read the past unless another device hands it over |
| **Lost** | Server-side moderation | Abuse reports carry decrypted copies, sent by the reporting user |

> "I won't decide a privacy question alone, and I won't let it be decided without the costs. By Friday,
> product gets one page: the options, and a range for each. The date comes out of the decision."

## Worked delta 3: broadcast channels with a million subscribers

The design's own weak spot. Each post would be a million pushes and a million inbox updates.

**What doesn't change:** the log and the sequencer, which see one write per post and don't notice.
**What changes:** delivery. Push only to people **viewing the channel right now**. Everyone else reads on
open, by cursor, like a month-old phone. Replace per-reader cursors with an approximate counter per post.

> "Same log, different delivery. A channel is a third tier on the field the worker already branches on."

## Worked delta 4: a new client protocol

*"You need to change the message schema, without breaking a billion clients that update slowly."*

| Step | What happens |
|------|--------------------------------------|
| 1 | Add the new field as optional. Old apps ignore unknown fields, new apps tolerate its absence |
| 2 | The server stores the new shape, and renders the old shape for an old `protocol` value at the gateway |
| 3 | Watch the version distribution until the old share falls under a threshold you agreed |
| 4 | Remove the old shape, with an upgrade prompt for what's left |

The stored rows can stay as they are, because the old-shape rendering happens per connection, and the
version is known from the first frame.

\newpage

# Stage 8: Failure modes and reliability · 0:45–0:50

| Failure | Blast radius | Mitigation |
|--------|-----------|-----------------------------------------|
| Gateway host lost | 500 k reconnects | Jitter, resumption, cursor sync, admission control. Messages are in the log |
| **A deploy restarts a zone** | 33 M reconnects | Gradual drain, enforced by the pipeline; pause the rollout |
| Registry stale or lost | Pushes fail or go nowhere | The message waits in the log; the registry refills on heartbeats in minutes; devices repair by head check |
| Partition leader fails | Sends to about 1/1,000 of conversations pause for seconds | Raft failover; retries with the same `clientMsgId` |
| A follower's disk fails | One replica, for a while | Quorum carries on; re-replicate from a snapshot |
| Log consumer lag | Delayed delivery, ACKs unaffected | Alert on lag. Delivery has priority over search and inbox |
| Push platform down | No wake-ups | A hint only. Devices sync when next opened |
| Inbox index lost | Sync can't tell what changed | Rebuild from `convs_by_user` and `last_seq`; slower until then |
| Bad client release | Bursts of reconnects or retries | Server-sent backoff; a kill switch by app version |
| Region outage | Users in the region disconnected | Homed conversations fail over; seconds of acknowledged messages may need reconciling. State it |

## The incident, walked through

*"A gateway deploy restarts a whole zone at once. Delivery latency goes from half a second to forty seconds."*

| Phase | Time | Action |
|-----|-----|-----------------------------------|
| **Detect** | 0–5 min | Sync latency and auth errors page on-call. The probes show delivery latency, from outside |
| **Contain, first** | ~5 min | Pause the rollout, so it can't take the next zone. Tighten admission on sync |
| **Recover** | 5–30 min | Let devices drain back, and let sync catch up. Don't add capacity in a panic if admission is holding |
| **Learn** | Next week | Why could one deploy restart a zone? Gradual drain becomes part of every deploy, enforced by the pipeline |

> "No message is lost. The outage is latency, and the SLO tells us how bad."

::: why
**Why contain before recover?** Because a rollout that's still running makes each recovery step pointless.
The first move in almost every incident is to stop whatever is changing. **Why is the "learn" step a
pipeline change and not a checklist?** Anything that relies on a person remembering at 2 a.m. will
eventually fail. A deploy tool that refuses to restart more than a fixed share per minute can't.
:::

# Stage 9: SLOs, observability, cost · 0:50–0:54

**Measure from outside.** Probe devices talk to each other all day, on real clients, through the real path.

| SLI | How it's measured | Target |
|--------|------------------------|-------------|
| Send | ACK success and latency | 99.99%; p99 < 200 ms inside our system |
| Delivery | End-to-end latency, from synthetic conversations | p99 < 500 ms to online devices |
| Sync | Time from reconnect to `LIVE` | p99 under a few seconds |
| **Integrity** | Loss and duplicate rate on probe traffic | **Exactly zero** |

::: why
**Why probes, and not server metrics?** A server can only report what it saw. It can't tell you that a message
was committed and never reached a phone. A probe conversation knows what was sent, and checks what arrived.
That's the only direct measure of *never lose* and *never show twice*. **Why "exactly zero" and not
99.999%?** Because it's an invariant, not a latency. Any violation is a bug to find, not a budget to spend.
:::

**The dashboard:** consumer lag per consumer group · commit latency per partition · leader changes per hour ·
reconnect rate against the baseline · sync admission rejects · gap repairs and head-check repairs per
device-hour (a rising rate means pushes are failing silently) · dedup hit rate (a rising rate means ACKs are
being lost).

**Cost has two big items.**

| Item | Size | Lever |
|------|------|----------------|
| Gateway fleet | 250–300 hosts, 2 TB of RAM, sized by sockets | Lower memory per socket (Appendix A) |
| Storage | 60 TB/day replicated. 90 days hot = 5.4 PB; a year all hot would be 22 PB | Tiering, compression |

**The storage bill.** *"Finance wants message storage cost down 40% next year, with no product change."*
Slice first: messages, metadata, replicas, indexes. What's growing fastest? The biggest lever is usually
tiering: recent months on fast disks, older years on object storage. That alone can approach the target.
Then compression. Retention is a product change, so it goes back to product. Report **cost per active user
per month**, so growth doesn't hide the trend.

# Stage 10: The EM layer · auxiliary at Staff, or when asked

In a Staff round, give this a sentence at most. In an EM round (`levels.md`), it's first-class.

- **Phasing.** *Phase 1:* store then deliver, one-to-one, with cursors and client IDs. That invariant never
  changes afterwards. *Phase 2:* groups, on the same log. *Phase 3:* receipts at scale, and search.
- **Team split along the data.** **Connections** (gateways, drain). **Messaging core** (sequencer, store,
  log; owns delivery on-call). **Sync and clients**. **Search**. The contracts between them are the frame
  protocol and the `MessageStored` event, so they can work in parallel.
- **Half the team?** Ship one-to-one with cursors, dedup and a single region. **Never cut commit-before-ACK or
  the integrity probes.** Those can't be added later without breaking promises already made.

![The phases. Each builds on the invariant of the first.](diagrams/video-em-phases.pdf){width=92%}

**The on-call follow-up.** *"The messaging-core team was paged forty times last month. Two engineers have asked
to move teams."* First, talk to the two engineers, and listen. Then measure: forty pages, by alert and by hour.
Page only on symptoms users feel, and send the rest to tickets. Fix the top three causes, with twenty percent
of each sprint until pages halve.

> "Paging load is a team health metric. I track it next to the SLO, and I report both."

**At other levels.** *Director:* the E2E decision (privacy against search and moderation) is a product and
legal call. Frame the options and costs, then bring the right people in.

# Stage 11: The close · 0:54–0:56

> "**What I built:** messages are appended to a per-conversation log with a server sequence before the
> sender is acknowledged, and every device catches up by cursor. **Key trade-off:** a single authority per
> conversation, which can stall a partition for seconds on failover but can never reorder it; groups share
> one log, with receipts as cursors, aggregated above about thirty-two members. **Biggest risk:** a zone-wide
> reconnect storm, watched by the probes and capped by admission control. **Next:** tiering twenty petabytes
> a year, and the protocol-versioning plan for slow-updating phones."

::: why
**Why four sentences in this shape?** What / trade-off / risk / next is how senior people summarise decisions.
It shows you know what you built, what you gave up for it, what could still hurt, and where you'd invest.
Interviewers often write the debrief from your close.
:::

# Stage 12: Self-check after a simulator run

Score yourself honestly; the simulator's debrief uses similar dimensions.

| Signal | Weak | Strong | Exceptional (aim here) |
|-----|--------|----------|-------------------------------------|
| Framing | Starts from the socket | Store before deliver | Says **"mailbox first"** by minute 12, and designs offline as a cursor |
| Estimation | Lists numbers | Numbers lead to decisions | Finds **the receipt trap with arithmetic**; sizes gateways by sockets |
| Ordering | Timestamps | One sequencer per conversation | Number and message in **one Raft entry**; walks failover; knows the fencing |
| Idempotency | "Retry" | `clientMsgId` and a dedup table | Dedup before numbering; **in-flight retries**; retry horizon < dedup TTL |
| Groups | N one-to-one chats | Shared log + cursors | Coalesced inbox on the trailing edge; membership as log entries |
| Receipts | Per-message events | Cursors | Tier line derived from *n*(*n*−1); `DELIVERED` isn't "seen" |
| Reconnect | "They reconnect" | Backoff | Jitter, resumption, admission control; drain window from spare capacity |
| Sync | "Fetch new messages" | Cursor sync | **Register first**; gap detection; **head check for the tail** |
| Tool depth | Names tools | Justifies tools | Raft no-op and log matching; CDC without an outbox; half-open sockets |
| New requirements | Redraws | Adapts | **States the delta**, what stays untouched, and the client rule from version one |
| Operations | Server metrics | SLOs | Probe devices; integrity = exactly zero; lag as a separate alert |

**Common traps:** deliver then store; client timestamps; groups as N one-to-one chats; presence and messaging
conflated; treating a client ACK as "displayed"; a heartbeat that writes to the registry; bucket as a hash input
for the consensus group; a first-edge coalescer; relying on gap detection alone; retries with a new ID.

\newpage
# Part III — The internals, for when the interviewer digs

These appendices go one level below Stage 5, in plain words. Read them once; reread the one for whichever tool
you named in your last mock. The figures are typical orders of magnitude, not guarantees, and any real
number depends on the hardware and the configuration.

## Appendix A — WebSockets and the connection tier

**How a WebSocket starts.** As an ordinary HTTP/1.1 request with `Upgrade: websocket`. The server answers
`101 Switching Protocols`, and from then on the TCP connection carries **frames** in both directions. HTTP's
request-and-response shape is gone. Because it starts as HTTP on port 443 over TLS, it passes through
proxies and firewalls that would block a custom protocol.

**Frames.** Each has a small header (opcode, length, and for client-to-server frames a masking key). Data
frames carry text or binary; control frames include **ping**, **pong** and **close**. Masking exists to stop
confused proxies treating frames as HTTP. It's not encryption; TLS does that.

**Where 20 KB goes, and how it gets smaller.**

| Part | Typical cost | How to shrink it |
|--------|---------|----------------------------------|
| Kernel socket buffers | A few KB idle; can grow far larger | Cap them, since idle sockets carry almost nothing |
| TLS session state | A few KB to tens of KB, depending on library | A library with low per-connection memory; release buffers when idle |
| Application state | From a few KB up | Event loop rather than one thread per socket, whose stack alone costs far more |
| Compression context | Can be **tens to hundreds of KB per socket** | **Turn off per-connection compression context**, or compress payloads separately |

::: why
**Why does a planning figure of 500 k per host sit well below what's possible?** Public reports describe millions
of sockets on one tuned host. But the cost of a host's failure is proportional to what it holds: 500 k means
half a million reconnects, and 2 M would mean four times that. You choose the number from the blast radius you're
prepared to absorb, and the memory calculation only sets the floor.
:::

**Half-open connections.** TCP doesn't notice a dead peer unless it sends something. A phone that lost signal
sends no FIN, and a server's `write` succeeds into the kernel buffer long before any failure is known. So
**the heartbeat exists to surface dead sockets**, and a successful socket write never counts as delivered.

**Why phones complicate it.** Radios use power to wake up, so frequent heartbeats drain the battery. Mobile networks
drop idle NAT mappings, sometimes after only minutes. Operating systems suspend background apps and kill their
sockets. So a phone in someone's pocket is usually *not* connected, and the wake-up path (Appendix F) is normal
operation, not a failure case. The 30-second interval is a compromise, and many apps vary it.

**TLS resumption.** A full TLS 1.3 handshake includes a certificate signature, the expensive part. On reconnect, a
client presents a **session ticket** from earlier and skips the signature. It still takes one round trip, and
it's a large saving in server CPU. 0-RTT exists too, but its data can be replayed, so it doesn't suit a `SEND`.

**Load balancing long-lived connections.** A layer-4 balancer forwards TCP without reading it, and it's cheap. New
connections go to the host with the fewest, because a restarted host would otherwise stay empty for hours. The port
limit people worry about applies per (source IP, destination IP, destination port), so it's the balancer's
hops to the gateways that need several addresses, not the public side.

## Appendix B — Raft: the leader, the log and failover

**The idea.** A group of replicas (three here) agrees on one ordered log. A deterministic state machine applies
the log, so every replica ends up with the same state. Raft splits this into leader election, log replication
and safety.

**Terms.** Time is divided into numbered **terms**, each starting with an election. A replica votes at most once
per term. A message carrying an older term is refused, and its sender learns it's out of date. **That's the
fencing used in Stage 6.1.**

**Writing, step by step.**

1. A client's command reaches the **leader**, which appends it to its log.
2. The leader sends `AppendEntries` to the followers, carrying the previous entry's index and term.
3. A follower accepts only if it has that previous entry, then persists the new one and answers.
4. Once a **majority** has it (the leader counts), the entry is **committed**, and the leader applies it and
   replies. Followers learn the commit index with the next message.

**Log matching.** If two logs have the same index and term at some position, they're identical up to it. This
follows from the check in step 3. **That's why numbers can't have holes across a failover**: no one can have
entry 901 without entry 900.

**Elections.** A follower that hears nothing for a random **election timeout** becomes a candidate and asks for
votes. A voter refuses a candidate whose log is less up to date than its own (compared by last term, then
length). A majority has every committed entry, so **any winner has every committed entry**.

| Timeline | Old leader L, follower F1, follower F2 |
|-----|--------------------------------------------------|
| t1 | L (term 5) appends entry 900 and sends it to F1. F1 persists it. L crashes before seeing a majority's reply |
| t2 | F1 and F2 time out. F1's log is longer, so F2 votes for F1. F1 is leader in term 6 |
| t3 | F1 appends a **no-op** in term 6 and replicates it. When it commits, 900 commits with it |
| t4 | The phone retries with the same ID. F1 finds the dedup row, and answers 900 |
| t5 | L returns on term 5, sees term 6 in the replies, and steps down |

::: why
**Why the no-op at t3?** A subtle rule. A leader may not treat an entry from an *earlier* term as committed just because
a majority holds it. There's a known failure sequence where such an entry could still be overwritten. So it
commits an entry from **its own** term; the earlier ones commit along with it by log matching. This is also why
`last_seq` isn't trustworthy until the new leader has done this.
:::

**Reads.** A leader can't simply read its local state: it might have been replaced and not know yet. A
**lease** (followers promise not to elect anyone for a short time) or a **read index** (confirm leadership with a
majority round first) solves that. Sync can often read from a follower as long as it's caught up to the requested
`seq`, because a cursor read doesn't need the newest value.

**Throughput.** One fsync per entry would limit a leader to a few hundred or a few thousand commits a second. **Group
commit** puts many entries behind one disk flush and one replication round, and **pipelining** sends the next
batch before the last one's answered. That's what makes 10,000 a second per leader a reasonable plan.

**Snapshots.** The log can't grow forever. Replicas periodically save their state and truncate the log. A far-behind
follower gets a snapshot, then the tail. **The CDC connector needs care here**: truncation mustn't pass its
position, or events are lost.

## Appendix C — Wide-column storage and LSM trees

**The data shape.** A table keyed by `(partition key, clustering key)`. The partition key decides which replicas hold
the row, and rows in a partition are stored sorted by the clustering key. Reads within one partition are cheap;
anything across partitions isn't. So you design tables from the queries, and duplicate data for a second query:
that's why membership is stored twice.

**The LSM write path.**

1. A write goes to a commit log (here, the Raft log) and to an in-memory sorted table, the **memtable**.
2. A full memtable is flushed to an immutable sorted file on disk, an **SSTable**.
3. Background **compaction** merges SSTables, dropping overwritten values and expired data.

**Reads.** Check the memtable, then the SSTables, newest first. A **bloom filter** per file answers "definitely not here"
without touching disk. That's what makes the dedup lookup cheap: most lookups are for IDs that were never seen.

**Why this workload suits it.**

- Writes are **appends in clustering order**: `seq` only grows. The worst LSM workloads are random updates to old
  rows, and we barely have those.
- Reads are **short range scans from a known point**: "after this cursor". That's a seek and a sequential read.
- Data has an obvious age. **Time-window compaction** groups files by time, so compaction doesn't keep rewriting old
  data, and a whole expired window can be dropped at once. That suits the dedup table's TTL.

**Tombstones.** A delete in an LSM store writes a marker, and data physically disappears only at compaction. Two consequences:
a *delete for everyone* isn't physically gone until compaction runs (so give it a deadline), and a partition heavy with
tombstones reads slowly.

**A real-world parallel.** Discord has written publicly about storing messages keyed by `(channel_id, bucket)`, with a
time-based bucket and time-sortable IDs. It's the same answer to the same unbounded-partition problem. They use
Snowflake-style IDs, not gap-free numbers. Stage 5 says what that trades away.

## Appendix D — The log, consumer groups and CDC

**The log.** A topic is an append-only log split into **partitions**. Each message gets an **offset**. Messages stay for a
retention period whether or not anyone has read them. **Order is guaranteed only within a partition**, so `conv_id` is the
key: all of a conversation's events go to one partition, in order.

**Consumer groups.** Each consuming service (delivery, inbox, search) is a group with its own committed offset per
partition. They read independently, at their own pace, and a new one costs the producers nothing. After a crash a consumer
restarts from its last committed offset and may **re-read**: that's at-least-once, and the receivers here are all idempotent.

| Consumer | Why a repeat is harmless |
|-------|-----------------------------------|
| Delivery | The device upserts by `(conv_id, seq)` |
| Inbox | "This conversation changed" is true twice |
| Search | Indexing the same document ID replaces it |
| Wake-ups | A collapse key replaces the notification. The one place a repeat is even visible |

**Rebalancing.** When a consumer joins or dies, partitions are reassigned, and processing pauses on them. Newer incremental
protocols reduce the pause. It matters because the delivery SLO is under a second, so **a rebalance shows up in your
delivery latency**. Keep the group stable, and don't deploy it all at once.

**Durability.** `acks=all` with `min.insync.replicas=2` means a publish is confirmed once two replicas have it.

**Don't add partitions casually.** The key-to-partition mapping changes, so a conversation's new events can land in a
different partition from its old ones, and ordering across that moment is lost. Provision generously at the start.
The numbers still protect you here: a device orders by `seq` no matter what.

**CDC, in this design.** A connector follows each Raft group's committed entries and publishes the new rows. It remembers
its position, so it resumes after a restart. It sees only committed data, so consumers never see a message
that later disappears. It publishes at least once, so it may repeat after a failover. Dual write has neither property.

## Appendix E — Redis-class stores for the hot tier

**Single-threaded execution.** One node executes commands one at a time, so each is atomic without locks. It's fast
because everything is in memory: on the order of 100,000 simple operations a second per node, more with pipelining.

**Structures used here.**

| Key | Structure | Commands | Why this one |
|-----|--------|----------|----------------------|
| `session:{user}` | Hash | `HSET`, `HGETALL`, `EXPIRE` | One small map per user, read whole |
| `members:{conv}` | Set | `SMEMBERS`, `SADD`, `SREM` | Membership, for fan-out |
| `inbox:{user}` | Sorted set | `ZADD`, `ZRANGEBYSCORE`, `ZREMRANGEBYRANK` | Ordered by last change, and trimmed |
| `cursor:{user}:{device}` | Hash | `HSET`, `HGET` | One field per conversation. Monotonic update in a short script |

**Redis Cluster and hash tags.** The key space is split into 16,384 hash slots. If a key contains `{...}`, only that part is
hashed, so `session:{7731}` and `inbox:{7731}` land together, and one pipeline can touch both.

**A small trap with TTLs.** A TTL on the hash applies to the whole key, so while one device keeps refreshing, a dead device's
field lives on. Store a last-seen time in the value and treat old fields as offline. Worst case, a push goes
to a gateway that no longer has that socket, and it's dropped. Redis 7.4 added per-field TTLs, which is another route.

**Persistence and what can be lost.** Replication is asynchronous, so a failover can lose the last moments of writes.
`appendfsync everysec` loses up to about a second on a crash.

::: why
**Why that's acceptable here, and not for the numbers.** Lose a session entry and a push is skipped: the device repairs it.
Lose an inbox entry and a head check might miss a change until that conversation's next message or the device's next full
sync, which compares its cursors with each conversation's `last_seq`. Lose a cursor and the device re-sends it. Nothing here can lose a message, since none of it holds one. If the
*sequence number* lived in Redis, a failover could hand the same number to two messages. **Same tool, different consequence,
different decision.**
:::

**The registry's load is reads, not memory.** About 5 M lookups a second, for 10 GB, is 50 or so nodes with most of their
memory empty. Batching by gateway and caching a busy group's sessions for a second or two will cut that substantially, at the
cost of a few pushes to stale addresses.

## Appendix F — Waking a phone: APNs and FCM

**Why we can't just keep a socket open.** Mobile operating systems suspend background apps to save the battery. The only channel
that reliably reaches a sleeping phone is the one the OS itself keeps: **APNs** on Apple devices, **FCM** on Android.

**How it works.** The app gets a device token from the OS and registers it with our push platform. To wake it, the
platform sends the token and a payload to Apple or Google, who deliver it over their own connection.

**What you can rely on, and what you can't.**

| Property | Reality |
|---------|-------------------------------------------|
| Delivery | **Best-effort.** No delivery guarantee, and no reliable confirmation |
| Order | Not guaranteed |
| Offline storage | Limited. APNs keeps only the most recent notification per app for an offline device; FCM has its own limits |
| Payload | Small: about 4 KB. Fine for a preview, not for a batch of messages |
| Priority | High-priority sends can be throttled if they don't lead to something the user sees |
| Collapse | Both support replacing an earlier notification with a newer one, which is how a burst becomes one banner |

That's why a notification is **a hint to come and sync, and carries no responsibility for the message**. In the round, the
line is: *"If the push platform's down, nothing is lost: the message is still in the log."*

**Don't confuse the two "push"es.** *Push* in this design usually means a frame down an open WebSocket. *Push notification*
means APNs or FCM. Say which one you mean, because interviewers notice.

## Appendix G — End-to-end encryption in plain words

**The change in one sentence.** Only devices hold the keys, so the server stores and forwards ciphertext it can't read.

**One-to-one.** Protocols of the Signal family set up a shared secret from published keys (an initial key agreement), then
derive a new key per message (a **double ratchet**). A stolen key exposes little of the past or the future: **forward secrecy**.
Each device of each person has its own session, so a message to someone with five devices is up to five ciphertexts, plus
your own other devices.

**Groups.**

| Scheme | Send | Removing a member | Note |
|-------|-------|--------------|---------------------------|
| Pairwise | One ciphertext per member device | Nothing special | Up to thousands per message at 1,000 members |
| **Sender keys** | One ciphertext per message; the key is shared pairwise beforehand | Everyone must get a new key: O(*n*) | What makes large E2E groups affordable |
| MLS (RFC 9420) | One ciphertext | O(log *n*) tree updates | A newer standard, built for large groups |

**What it does to this design.**

- **Log, numbers, cursors, receipts:** unchanged, since they read no bodies.
- **`MessageStored`:** the body is now an opaque blob, possibly with per-device parts, so 200 bytes may grow.
- **Server-side search:** gone. Each device indexes locally.
- **Edit and delete:** still events. The edit's text is encrypted like a message.
- **Moderation:** abuse reports carry decrypted copies from the reporting user. Metadata (who, when, how often) is still visible
  to the server, which matters to how privacy claims should be worded.
- **A new device:** has no keys for the past, so history comes from another device, or an encrypted backup.

\newpage

# One-page cheat card

**The insight:** mailbox first, socket second. Store with a server sequence before anything is acknowledged. Every device catches
up by cursor. Push only delivers early.

**Numbers to compute:** (1) 100 M × 20 KB = **2 TB**; ÷ 500 k = 200, so **250–300 gateways**, sized by sockets. (2) 1 M/s × 200 B =
200 MB/s = **20 TB/day**, 60 replicated, **~20 PB/year**: wide-column, tiered. (3) 1,000 × 999 = **a million receipts per
message**: cursors, aggregated above a tier line.

**Send:** dedup (in-flight, then table) → `last_seq + 1` → one Raft entry with message + dedup row → majority → ACK. One tick is a promise.

**Order:** one Raft leader per conversation's partition; ~1,000 groups. Failover pauses, never reorders. Term fences a stale leader.
No-op commits the tail.

**Lost ACK:** same `clientMsgId` returns the original. Retry horizon 7 days < dedup TTL 14 days. Dedup before numbering.

**Deliver:** the row is the event; CDC → log keyed by conversation → worker: members, sessions, push with a 200 ms deadline; offline
gets a wake-up, a hint. A failed push isn't retried.

**Sync:** **register first**, then cursors → inbox says what changed → read after cursor → `LIVE`. Repairs: reconnect, gap, **periodic
head check for the tail**. Month offline: newest first, 20 each, holes filled on scroll.

**Groups:** shared log; inbox only says "changed", coalesced per second on the **trailing edge**. Membership changes are log entries;
`join_seq` is exact.

**Receipts:** cursors, `max(old, new)`. Forward up to ~32 members; "read by 412" on demand above. *n*(*n*−1). `DELIVERED` means stored, not seen.

**Reconnect:** jitter, resumption, least-loaded, small deltas, `RETRY_LATER`. Zone: 33 M over 10 min = 55 k/s × 10 = 550 k reads/s. Gradual drain, enforced by the pipeline.

**Storage:** `conv_id` routes to the Raft group; `bucket` (`seq >> 20`) is inside it. Hot 90 days, 5.4 PB; closed buckets go cold, erasure coded.

**Shed in order:** search, receipts, inbox, wake-ups, sync, live push. Never the commit.

**Delta:** an edit is a message with a `kind`. Unknown kinds still advance the cursor: **in version one**. E2E keeps log, numbers and cursors; loses search and moderation.

**SLOs:** probe devices; integrity exactly zero; consumer lag separately.

**Say it honestly:** partition stalls for seconds on failover; region loss can cost seconds of acknowledged messages.

**Close:** what I built · key trade-off · biggest risk · next.
