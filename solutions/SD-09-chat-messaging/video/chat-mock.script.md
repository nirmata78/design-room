# Chat and messaging mock round (video)

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png.
     Speakers: I interviewer · C candidate · V candidate, key line (slower) · N coach. [pause: s] = silence.
     Content follows ../../SD-09-chat-messaging.md. Level: em (L6 / M1), per levels.md.
     The four follow-ups and their diagrams (svg/fu-*.svg) are new for this video. Target ~27 min. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: clientMsgId=client_message_I-D CDC=C-D-C -->

## Before you start

[slide: v-01]
N: This is a mock system design round, for an engineering manager loop at level six. The prompt is chat and messaging. You'll hear the interviewer, the candidate as they should sound, and me, between the stages. After the design, four manager follow-ups. Listen once, straight through. On the second pass, pause after every question, and answer it yourself first.

[slide: v-02]
N: Know what's being weighed. At this level, operations and cost count most, then leadership. Depth once: here, ordering and the idempotent send. And expect the manager's curveball. A privacy decision from the top. An incident. A team that's burning out. A storage bill.

## Requirements

[slide: v-03]
I: Let's start. Design a messaging system. One-to-one and group chats, for a billion users, with delivery and read receipts, and support for clients that go offline.

C: A few questions first. Some of the answers are numbers, and one of them is a guarantee.

[slide: v-04]
C: How many users, and how many connected at once?

I: A billion users. About a hundred million connected at any moment.

C: Then the connection tier is a cost of its own. Message rate?

I: About a million messages a second at peak.

C: Group size?

I: Up to a thousand members.

C: And devices per user?

I: Up to five, and they all have to converge.

C: So every device needs its own position in each conversation. A cursor per device.

[slide: v-05]
C: Now the guarantees. Which is worse: losing a message, or showing one twice?

I: Neither is acceptable. And every participant must see the same order.

C: Then I need a durable write before anything is acknowledged, idempotency on send, and a single order per conversation. Receipts?

I: Sent, delivered and read.

C: That's a second message flow, and it may be bigger than the first. History?

I: Full history, kept for years, searchable by the user.

C: And encryption?

I: Assume not end to end. But tell me what it would change.

N: "Neither is acceptable" turned two requirements into a design. Durable write, and idempotency. Listen for how often they come back.

[slide: v-06]
C: In scope: send, deliver, sync, groups, receipts, history and multiple devices. Out of scope, said aloud: media, voice and video calls, spam, and the push notification platform itself. End-to-end encryption I'll treat as a delta.

## The thesis

[slide: v-07]
C: Before boxes, the framing.

V: Start from the mailbox, not the socket.

[pause: 1.0]

C: A message is stored durably in its conversation log, with a sequence number from the server, before anything is acknowledged. Every device then catches up by cursor: everything after number twelve thirty-four. Pushing over a WebSocket is just an optimisation that delivers early.

[slide: v-08]
C: The targets. Delivery to online recipients under five hundred milliseconds at p ninety-nine. Zero loss once the sender sees the tick. A total order per conversation. And send available ninety-nine point nine nine percent.

## Back of the envelope

[slide: v-09]
C: Three numbers. First, connections. A hundred million sockets at about twenty kilobytes each is about two terabytes of memory, just to stay connected. At half a million connections per host, that's two hundred and fifty gateway hosts, plus headroom. Consequence: a dedicated gateway tier with no business logic in it. Heartbeats, about three million a second, stay there too.

[slide: v-10]
C: Second, storage. A million messages a second, two hundred bytes each, is about twenty terabytes a day, sixty replicated, and twenty petabytes a year. Consequence: a wide-column store, partitioned by conversation, with old history tiered to cheaper storage.

[slide: v-11]
C: Third, the trap. A message in a group of a thousand. Each member reads it, and each read receipt goes to nine hundred and ninety-nine others.

V: That's a million receipt deliveries for one message.

[pause: 0.8]

C: So in large groups, receipts are aggregated, never fanned out.

I: Mm-hm.

N: The third number found a trap before the interviewer did. That's the estimation bar.

## The A-P-I

[slide: v-12]
C: The client talks to a gateway over WebSocket frames. Send carries the conversation, a client message I-D, and the body. The server answers with an ACK carrying the sequence number. Incoming messages carry their sequence. The device answers delivered, up to a sequence, and later, read, up to a sequence. And sync sends the device's cursors, and gets back everything it missed, then live. History and setup are plain REST.

## Data model

[slide: v-13]
C: The message table is partitioned by conversation and ordered by sequence, with the sender, the client message I-D, the body and the server time. A sequencer owns the last sequence number of each conversation. Device cursors hold delivered and read, per user, device and conversation. An inbox index records which conversations changed for a user, so sync knows where to look. And a session registry says which gateway a device is on, with a time to live.

## High-level design

[slide: v-14]
C: The context. Users connect over sockets. When a recipient is offline, the push notification platform wakes their device, through the mobile operating systems' own push services. Support and trust have tools on the side.

[slide: v-15]
C: The send path. The sender's gateway passes the message to the message service, which finds the conversation's leader. The leader assigns the next sequence and writes the message, durably and replicated. Only then does the sender get its ACK. Change capture feeds a message log, partitioned by conversation. Delivery workers read it, look up each member's devices in the session registry, and push to online devices through their gateways, or to the push platform if they're offline.

[slide: v-16]
C: The sync side. A device coming back sends its cursors. The sync service asks the inbox index which conversations changed, and reads the messages after each cursor. Delivered and read go to a receipt service, on a lower-priority path, which advances the device cursors. Search reads the log asynchronously.

[slide: v-17]
C: As a sequence. Alice sends to Bob, who is offline. Alice's phone sends the message with its client I-D. The leader assigns a sequence and writes it. Now Alice gets the ACK: one tick, sent. Asynchronously, the delivery worker finds no device online for Bob, and asks the push platform to notify him.

[slide: v-18]
C: Bob opens the app later. It connects and sends its cursors. The sync service finds the changed conversations, streams every message after his cursor, then switches to live. Bob's phone answers delivered, and Alice sees two ticks.

[slide: v-19]
V: Online and offline are the same code path. The push only delivers early.

[pause: 0.8]

I: And if Bob is online on two devices?

C: The worker finds two gateway entries and pushes to both. Each device acknowledges on its own, and each device's cursor moves separately.

[slide: v-20]
C: Technology, briefly. Gateways are WebSocket servers holding only connections, because connection count is the scaling dimension. Messages go in a wide-column store: append-heavy, read in order, enormous. The sequencer is the partition leader per conversation. The log is partitioned by conversation, so it's ordered and replayable. And the registry is in memory with time-to-live, because it's small, hot, and tolerates staleness.

## Deep dive one: ordering

[slide: v-21]
I: Two people in a group send at the same instant. Who decides the order?

[slide: v-22]
C: Not the clocks. Client clocks skew, and users change them. Member Y's phone says ten o'clock, X's says one second later, but X's message reached the leader first. The conversation's single sequencer assigns five oh one to X and five oh two to Y, in arrival order. That order is the truth for every participant, on every device. Your own message shows as pending until the ACK brings its sequence, then slots into place.

[slide: v-23]
I: Why not one global sequencer?

C: A global order would be a bottleneck, and it's meaningless across conversations. Per conversation is what users see, and it partitions perfectly: a million messages a second, spread over hundreds of millions of conversations. Even a frantic thousand-member group is thousands of messages a second, well within one leader.

[slide: v-24]
C: Inside the message service: a router finds the conversation's partition leader. The sequencer assigns the number. A dedup check looks up the conversation and client message I-D. A new message goes to the writer, which writes durably, with the outbox, and only then builds the ACK. A message already seen skips straight to the ACK, with its original sequence.

## Deep dive two: the lost ACK

[slide: v-25]
I: The server stored the message, but the phone went into a tunnel and never got the ACK. What happens?

[slide: v-26]
C: The app still shows the message as pending, so it retries, with the same client message I-D. The server finds that I-D already stored in this conversation, and returns the original sequence. No duplicate is written, and none is shown.

[slide: v-27]
V: The tick appears only after a real ACK.

[pause: 0.8]

C: So a message is never shown as sent when it wasn't, and a retry never appears twice.

N: Ordering and the lost ACK. Those two, done properly, are the depth this round asks for.

## Deep dive three: groups and receipts

[slide: v-28]
I: How do groups work? Do you copy each message into a thousand inboxes?

C: No. Copies would be a thousand writes per message, a thousand updates for every edit, and storage times the group size. A shared conversation log is one write per message, and an edit is one row. The inbox index only records which conversations changed, so sync is: list what changed, then read each one after my cursor. And one-to-one chats use exactly the same model. One code path.

[slide: v-29]
C: Receipts are cursors, not per-message events. A read up to sequence twelve forty covers many messages at once. In a one-to-one chat or a small group, the cursor update is forwarded to the other participants. In a group of a thousand, it's only stored. When someone opens message info, the server counts on demand: read by four hundred and twelve of a thousand. Receipts travel on their own lower-priority path, so they can never delay messages.

## Deep dive four: reconnects

[slide: v-30]
I: A gateway dies with half a million connections on it.

[slide: v-31]
C: The messages are safe. They were never in the gateway, they're in the log. What isn't safe is the reconnect. Half a million devices reconnect at once: T-L-S handshakes, authentication, and sync. So clients back off with jitter. T-L-S session resumption cuts the handshake cost. Sync is cheap because it's deltas since a cursor. And the sync service has admission control. On deploys, gateways drain gradually over minutes, so we never cause this ourselves.

[slide: v-32]
I: And a phone that comes back after a month?

C: The inbox index lists the conversations that changed. The server sends the newest page of each first, so the app is useful within a second, and backfills older messages as the user scrolls. The burst is capped per device.

## A requirement added mid-round

[slide: v-33]
I: Users want to edit a message, and delete it for everyone.

[slide: v-34]
C: Because the conversation log is the single source of truth, an edit is an event appended to the conversation: edit sequence twelve thirty-four. A delete is the same. The stored row is updated too, one write. Devices apply the event when they sync. The cost is on the clients: old app versions must treat unknown events as harmless. So the protocol needs versioning. Had I copied messages into inboxes, every edit would be a thousand writes.

I: And end-to-end encryption?

C: Then the server can't read bodies. Server-side search goes away and moves to the device, and group messages are encrypted per member device, with sender keys to reduce the cost. It's a real trade-off, and I'd present it as one.

N: The delta, the cost, and what stays untouched. And encryption treated as a trade-off, not a footnote.

## Failures and operations

[slide: v-35]
C: The failures. A gateway lost: jitter, resumption, cursor sync, admission control. A stale registry: delivery to a dead gateway fails, and the message simply waits in the log until the device syncs. A partition leader fails over: sends to that conversation pause for seconds, and clients retry with the same client I-D. Log consumers lag: delivery has priority over search and indexing. A region outage: conversations are homed per region, replicated asynchronously, and I'd state the risk of a few seconds of reordering on failover.

[slide: v-36]
C: For S-L-Os, I use probe devices that talk to each other all day. Send success: the ACK arrived. Delivery: end-to-end latency to online recipients, from those synthetic conversations. And integrity: the loss and duplicate rate on probe traffic, which should be exactly zero.

[slide: v-37]
C: Cost has two big items. The gateway fleet, which I plan by connections, not requests. And storage, twenty petabytes a year. I'd tier old history to object storage, compress it, and keep only recent months on fast disks.

N: Probe conversations measuring zero loss. That's how a manager turns an invariant into a dashboard.

## The manager layer

[slide: v-38]
I: How would you build it?

C: The invariant first. Phase one: store-then-deliver, for one-to-one, with cursors and client message I-Ds. That never changes afterwards. Phase two: groups, on the same log, with membership and the inbox index. Phase three: receipts at scale, with aggregation, and search.

[slide: v-39]
C: Four teams. Connections: gateways, the registry and capacity. Messaging core: the sequencer, storage, and the invariant. They own the delivery-latency on-call. Sync and clients: the protocol and its versions. And search, off the send path.

[slide: v-40]
C: To close.

V: Store first, with a sequence. Deliver second.

[pause: 0.8]

C: Messages are appended to a per-conversation log with a server sequence before the sender is acknowledged, and every device catches up by cursor. That gives one order, no loss, and no duplicates, and offline and multi-device become the same path. Groups share one log, and receipts are cursors, aggregated in big groups. Next, I'd harden reconnect storms, and tier twenty petabytes a year of history.

I: Thanks. Some questions on the management side.

## Follow-up 1: encryption by Friday

[slide: v-41]
I: The C-E-O announced end-to-end encryption on stage. Product wants a date by Friday.

[slide: v-42]
C: I wouldn't give a date on Friday. I'd give a one-page options paper. What breaks: server-side search, which moves to the device. What it costs: group messages encrypted per device, which sender keys reduce. What we lose: server-side moderation, so abuse reports would carry decrypted copies, sent by the reporting user. And who decides: product, legal and policy. Engineering prices the options and the timelines.

V: I won't decide a privacy question alone, and I won't let it be decided without the costs.

[pause: 0.8]

C: By Friday, product gets that paper and a range for each option, with the risks named. The date comes out of the decision.

N: Whose decision, what you bring, and when. That's leadership without overreach.

## Follow-up 2: the deploy

[slide: v-43]
I: A gateway deploy restarts a whole zone at once. Delivery latency goes from half a second to forty seconds.

[slide: v-44]
C: Detect: sync latency and authentication errors page on-call in minutes. Contain, first: pause the rollout, so it can't take the next zone, and tighten admission on sync. Then recover: let devices drain back gradually, and let sync catch up.

V: No message is lost. The outage is latency, and the S-L-O tells us how bad.

[pause: 0.8]

C: The week after, a blameless review. Why could one deploy restart a zone? Gradual drain becomes part of every deploy, enforced by the pipeline. And a game day, before the next one.

N: Stop the rollout before you fix the storm. Then make the safe path the default.

## Follow-up 3: the on-call

[slide: v-45]
I: The messaging-core team was paged forty times last month. Two engineers have asked to move teams.

[slide: v-46]
C: That's a people problem and a systems problem at once. First I'd talk to the two engineers, and listen. Then measure: forty pages, by alert and by hour. Most pages are usually noise: C-P-U, disk, a flaky dependency. I'd page only on symptoms users feel, the delivery-latency S-L-O, and route the rest to tickets. Then fix the top three causes, with a reserved twenty percent of each sprint until pages halve.

C: And protect people: time off after a bad night, and a monthly review of the rotation.

V: Paging load is a team health metric. I track it next to the S-L-O, and I report both.

[pause: 0.8]

N: Listen first, then measure, then budget the fix. And the answer kept the people in it.

## Follow-up 4: the storage bill

[slide: v-47]
I: Last one. Finance wants message storage cost down forty percent next year, with no product change.

[slide: v-48]
C: I slice first: messages, metadata, replicas, indexes. Which one grows fastest? The biggest lever is usually tiering. Recent months on fast disks, older years on object storage, read rarely and slowly. That alone can approach the target. Then compression by conversation, because old partitions compress well. Retention is a lever too, but it is a product change, so it goes back to product, not into my plan.

C: And I'd report cost per active user per month, so growth doesn't hide the trend.

N: The diagnosis order is the answer. And note: none of these touches the invariant.

## Debrief

[slide: v-49]
N: Here's where the round lands. Strong candidates use WebSockets and a database. Exceptional ones say mailbox first, socket second. Strong ones use timestamps. Exceptional ones use one sequencer per conversation. Strong ones mention retries. Exceptional ones walk the lost ACK with the client message I-D. And on groups, exceptional ones find the receipt trap with a number.

[slide: v-50]
N: Five checks, before the real round. Store before deliver, said out loud. A server sequence per conversation, not timestamps. The client message I-D, and the lost ACK. Per-device cursors, and the offline walk. And the receipt trap, found with a number. Good luck.
