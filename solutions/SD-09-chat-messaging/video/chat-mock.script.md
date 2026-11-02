# Chat and messaging mock round (video), v2

<!-- Video script for ~/.claude/skills/slide-video-kit/scripts/build_video.py. [slide: v-NN] = video/frames/v-NN.png;
     NN is the number printed on every slide. Speakers: I interviewer · C candidate · V candidate, key line (slower) ·
     N coach. [pause: s] = silence. Content follows ../../SD-09-chat-messaging.md. v2.1 2026-11-02: Staff L6/L7 bar, code and sync corrections from the reference design,
     slide-video-kit/STANDARD.md §1a and §1b, with SD-08 v3 as the model. Target ~42 min, hard limit 45.
     v1 (L6 EM, 21:38) in .v1-em-2026-10-29/. -->
<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->
<!-- labels: N=COACH -->
<!-- say: clientMsgId=client_message_I-D CDC=C-D-C ZADD=Z-add ZSET=Z-set HSET=H-set MQTT=M-Q-T-T fsync=F-sync -->

## Before you start

[slide: v-01]
N: A mock system design round at the Staff bar, level six or seven, the way FAANG and other top-tier companies run it. The prompt is chat and messaging. You'll hear the interviewer, the candidate, and me, the coach. Then five follow-ups. On a second pass, pause after each question and answer first. Every slide is numbered, top right, for feedback.

[slide: v-02]
N: Three things carry a Staff round. Depth on the crux, here: where a message lives between sent and delivered. Trade-offs with evidence: every store and transport against the alternative that loses. And a correctness stance: which mechanism gives no loss, no duplicates, one order. Slides badged A-U-X are the manager layer; in a Staff round, skip them.

[pause: 0.8]

## Requirements

[slide: v-03]
I: Let's start. Design a messaging system. One-to-one and group chats, for a billion users, with delivery and read receipts, and support for clients that go offline.

C: A few questions first. Some of the answers are numbers, and one of them is a guarantee.

[slide: v-04]
C: How many users, and how many connected at once?

I: A billion users. About a hundred million connected at any moment.

C: Then connections are a cost of their own. Message rate?

I: About a million messages a second at peak.

C: Group size?

I: Up to a thousand members.

C: And devices per user?

I: Up to five, and they all have to converge.

C: So every device needs its own position in each conversation.

[slide: v-05]
C: Now the important one. Which is worse: losing a message, or showing one twice?

I: Neither is acceptable. And every participant must see the same order.

C: Then I need a durable write before anything is acknowledged, idempotency on send, and one authority for order. Receipts?

I: Sent, delivered and read.

C: That's a second message flow, and it may be bigger than the first. History?

I: Full history, kept for years, searchable by the user.

C: And encryption?

I: Assume not end to end. But tell me what it would change.

N: "Neither is acceptable" turned two requirements into a design. Durable write, and idempotency. Listen for how often they come back.

[slide: v-06]
C: In scope: send, deliver, sync, groups, receipts, history and multiple devices. Out of scope, said aloud: media, voice and video, spam, and the push notification platform itself. End-to-end encryption I'll treat as a delta. And presence is out too. Which gateway holds a socket is routing, and must be right. "Online now" is a product feature, with far weaker needs.

## Terms, defined once

[slide: v-07]
N: Six terms the round uses constantly. A gateway: a server that holds open WebSockets and has no business logic. The conversation log: every message of one chat, in order. The sequence number: assigned by the server, per conversation, with no gaps. A cursor: one device's position, "I have everything up to number N". An ACK is not a receipt: an ACK says the server stored it, which is the first tick; a receipt says a device has it, or a person read it. And the client message I-D: a unique I-D the phone picks once, and reuses on every retry.

[pause: 1.0]

[slide: v-08]
N: The central contrast, as a picture. On the left, socket first. The server pushes to the recipient if they're online, and otherwise writes to a pending table. Two code paths. A crash after the push and before the write loses the message, or a retry shows it twice. On the right, mailbox first. The sender appends to the conversation log, and gets an ACK only after that. An online device gets an early push; an offline one asks for the difference later. Both read the same log.

[pause: 1.0]

[slide: v-09]
N: What the cursor buys you. One conversation's log, with no gaps. Three devices of one person. The phone's cursor is at the end: it's up to date. The laptop is at one two three six, so it asks for one two three seven onward. The tablet's been off for days, at one two three one. Same question, same code, a longer answer. Offline is just a cursor that's further behind.

[pause: 1.0]

## The thesis

[slide: v-10]
C: So, my framing.

V: Start from the mailbox, not the socket.

[pause: 1.0]

C: A message is stored durably in its conversation log, with a sequence number from the server, before anything is acknowledged. Every device then catches up by cursor. Pushing over a WebSocket is an optimisation that delivers early.

[slide: v-11]
C: Targets. Delivery to online devices under five hundred milliseconds at p ninety-nine. Zero loss once the sender sees the first tick. A total order per conversation. And send available ninety-nine point nine nine percent.

## Back of the envelope

[slide: v-12]
C: The arithmetic, each number with its consequence. The connection tier. A hundred million sockets at about twenty kilobytes each is two terabytes of memory, just to stay connected. At half a million sockets per host, that's two hundred hosts; I'd run two hundred and fifty to three hundred, for zone headroom. Gateways are sized by sockets, not requests.

C: Heartbeats, one every thirty seconds, are three point three million a second. They stop at the gateway. The registry, which gateway holds which device, needs only a batched refresh every five minutes: three hundred and thirty thousand a second. It's about ten gigabytes, so it lives in memory.

[slide: v-13]
C: The message path. A million messages a second at two hundred bytes is two hundred megabytes a second. That's twenty terabytes a day; sixty with three replicas; about twenty petabytes a year. So, a partitioned store with tiering.

C: A group message copied into a thousand inboxes is a thousand writes; a shared log is one. At an assumed three online devices per message, that's three million socket pushes a second.

C: And the trap. A thousand members read a message. Each read receipt goes to nine hundred and ninety-nine others.

[slide: v-14]
V: That's a million receipt deliveries for one message.

[pause: 0.8]

C: The receipt flow is a thousand times larger than the message flow. So in large groups, receipts are aggregated, never fanned out.

N: The last number found a trap before the interviewer did. Every number a calculation, each tied to a decision. That's the Staff estimation bar.

## The A-P-I

[slide: v-15]
C: The client talks to a gateway in frames on the socket. Send, answered by ACK. Message, answered by delivered up to a sequence number. Read up to a sequence number. And sync, answered by the missed messages, then a live marker. History and setup are plain REST.

[slide: v-16]
C: Sending, on the wire. The request: the conversation, the client message I-D, the body, and a protocol version. The ACK returns that same client I-D, the sequence number and the server time.

C: On the right, what the system emits: a message-stored event, keyed by conversation, so one chat stays in order. Two fields matter for routing. Kind: message, edit or delete. And tier: small or large. The body rides along: two hundred bytes is cheaper than a read per delivery.

[slide: v-17]
C: Delivering. A device receives a message frame with its sequence number. It answers delivered, up to that number, and that one frame acknowledges every message below it too. Later, read, also up to a number. Small groups forward that as a receipt.

C: And the trap in the grey comment: delivered means the app stored it, not that anyone saw it.

[slide: v-18]
C: Sync. The device sends its cursors, one per conversation, when it last synced, and a limit per conversation. The server streams the messages it missed, in sequence order, with a page marker saying the range and whether there's more. Then live.

[slide: v-19]
I: Why a cursor? Why not "give me everything since ten o'clock"?

C: Because timestamps tie. Two messages in one millisecond, and "since" either misses one or repeats one. And replicas' clocks skew. The cursor says exactly where I stopped, with no gaps, so it can't skip anything.

[slide: v-20]
C: One A-P-I I depend on: the push platform, another team's. My request: the user, a collapse key so a burst shows one notification, a preview and a time to live. Plus a hundred-millisecond deadline.

C: It answers two-oh-two, and hands off to Apple and Google. Or four twenty-nine, with retry-after.

I: And if it's down?

C: Nothing's lost. A notification is only a hint to come and sync. The message is still in the log.

## Data model

[slide: v-21]
C: The data model, conceptual, in Chen notation: rectangles are entities, diamonds relationships, ovals attributes, numbers cardinality. In the middle, a user. On the right, a conversation. A user is a member of many conversations and a conversation has many members: M to N, with join sequence on the relationship itself, so a new member doesn't see earlier history.

C: Two entities are weak: the double rectangles. A message has no identity without its conversation. Contains is the identifying relationship, the double diamond, and its partial key, the dashed underline, is the sequence number. A device is weak on its user, the same way. A user sends many messages.

C: The top rail is the key modelling choice. A device tracks a position in a conversation: M to N, with delivered and read sequence on the relationship. That's the cursor: it belongs to neither side alone.

[pause: 1.0]

[slide: v-22]
C: The same model as physical tables. Messages, in red. The partition key is the conversation I-D plus a bucket. The clustering key is the sequence number. The bucket is the sequence divided by about a million. Without it, a ten-year group becomes one unbounded partition. It's computed from the sequence, so no lookup.

C: Below it, client messages: the dedup table. Conversation and client I-D give the sequence number, with a fourteen-day time to live. Conversations hold the tier and last sequence. Device cursors hold the two positions. And membership is stored in both directions, because a table can be partitioned only one way.

[slide: v-23]
I: You keep saying wide-column. What do you mean by it, and why do you need it here?

C: A wide-column store, like Bigtable, organises a table by two keys. The partition key groups rows together. The clustering key decides the order inside: here, the sequence number.

C: On the slide, three Raft groups. Raft is a consensus protocol: a leader appends to a replicated log, and an entry counts once a majority has it. The conversation I-D alone picks the group, and its buckets stay inside, so a message and its number always commit together. In red, one partition, already sorted.

C: So "conversation nine thousand and one, everything after one two three four" is one partition, one sequential read, already in order. That's sync, and that's history.

[pause: 1.0]

[slide: v-24]
C: Now the hot tier, in memory: five keys around the one table that matters. Top left, in red, the session key: one hash per user, device to gateway, with a time to live. Its value points to the gateway key: the address, and whether that gateway is draining. Below, the members key: the user I-Ds of a conversation. Each member points back to a session key.

C: Delivery follows those arrows: members, sessions, gateways. Sync follows the bottom ones. The inbox key is a sorted set per user: which conversations changed, and when. The cursor key holds this device's positions. Both point into the messages table.

[pause: 1.0]

[slide: v-25]
C: Where each key comes from. Four writers. The gateway, on connect, sets the session; every few minutes, it refreshes a batch of expiries; on close, it deletes. It flips to draining on a deploy.

C: The membership consumer reads member-changed events and updates the set.

C: The inbox consumer, in red, reads message-stored events and adds the conversation to each member's inbox, but at most once a second. And the receipt service takes delivered and read frames, keeps the larger value, and flushes to the table behind.

[slide: v-26]
C: So, six stores, one job each. Read the last column. Messages and membership are the truth: replicated, never lost. Lose a cursor and the device re-syncs, and dedups locally. The inbox rebuilds from membership and each conversation's last sequence. The registry refills from heartbeats within minutes. Search replays the log. Two stores are the truth; the rest can be thrown away.

[pause: 0.8]

## Technology, against the alternatives

[slide: v-27]
I: Why WebSockets?

C: Both directions on one socket, at about twenty kilobytes idle. Long polling: rejected. A hundred million clients re-polling costs more than holding sockets. Server-sent events: server to client only, so sends need a second connection. M-Q-T-T is viable, but brokers at this scale mean custom work.

[slide: v-28]
I: And who hands out the numbers?

C: The Raft leader of the partition, so the number and the message are one log entry. Failover can't issue a number twice. Redis increment: rejected. It replicates asynchronously, so after a failover two messages can get one number. A quorum store with compare-and-set: Paxos round trips on every send. A timestamp or a Snowflake I-D sorts well, but it has gaps, so a device can't tell a message is missing. One global sequencer: a bottleneck, for an order nobody can see.

[slide: v-29]
C: For the messages themselves, wide-column, with consensus per range: one leader per range, and sequence scans. Cassandra is viable, but it's leaderless, so numbers need a separate sequencer. Sharded MySQL or PostgreSQL: resharding and twenty petabytes a year are the cost. Per-member inbox tables are rejected: a thousand writes per message.

[slide: v-30]
C: For transport, a Kafka-class log keyed by conversation: ordered per chat, replayable, with delivery, inbox and search as separate consumers. The leader calling delivery directly: rejected, because a slow gateway would stall sends. A plain queue: no replay and no per-key order. A dual write, row then publish: a crash in between leaves it stored, but undelivered until someone syncs.

## The send path

[slide: v-31]
C: Now the architecture, one level at a time. C4 level one, the system context. Our system is the red box in the middle. It stores every message in order and delivers to every device.

C: Users, top left: a billion, a hundred million connected on WebSockets. Support and trust, bottom left, with tools for abuse reports and recovery. On the right, in grey, what we don't own: the push platform, and behind it Apple's and Google's push services, the only way to wake a sleeping phone.

C: Those are other people's risks. I manage them with a deadline.

[pause: 1.0]

[slide: v-32]
C: Level two, the containers on the send path. The sender's device talks to a gateway, which holds connections and nothing else. The gateway passes the frame to the message service, in red, which is the partition leader. It assigns the sequence number and commits to the messages store. Only then does the ACK go back.

C: From the store, change data capture feeds the message log, keyed by conversation. Delivery workers consume it. They look up each member's devices in the session registry. Online devices get a push through their gateway. Offline ones go to the push platform.

I: What does C-D-C mean on that arrow? In other designs I'd expect an outbox as well.

[slide: v-33]
C: Two rules here. First, commit before ACK. A majority of replicas has the message before the sender sees a tick. So the tick is a promise.

C: Second, change data capture means a connector reads the store's commit log and publishes each new row. Normally you'd pair that with a transactional outbox, because a mutable table makes a poor event. But this row is append-only and already shaped like an event. So here, the log is the table.

[slide: v-34]
C: As a sequence. One: Alice's phone sends the frame. Two: the gateway routes by conversation. Three, highlighted: the leader checks for a duplicate, then takes last sequence plus one. Four and five: it appends to Raft, the message and the dedup row in one entry, on both followers. Follower one answers, so a majority has it: committed. Now the ACK goes back: one tick, sent. Six, asynchronously: the commit stream publishes message-stored.

C: The green note is the guarantee. A crash before commit: no ACK, so the app retries. A crash after commit: the retry finds the original.

[pause: 1.0]

[slide: v-35]
C: Now the whole trip, with Bob offline. One: Alice sends. The ACK comes straight back: one tick, sequence one two three four. Bob's state played no part in it. Two: message-stored goes onto the log. Three: a delivery worker consumes it. Four: it looks up Bob's session. No device is online. Five: it asks the push platform to notify. Six: Bob's phone gets a notification.

C: Nothing is queued for Bob. The message sits at one two three four, and Bob's phone will ask for it.

I: What does the worker branch on?

[slide: v-36]
C: Two things, one from the event and one from the registry. The leader stamps tier into message-stored, from the conversations table. Small is up to about thirty-two members; I'll derive that line shortly. The registry says which devices are online.

C: So, three branches. An online device, in any tier, gets a batched push through its gateway, with a two-hundred-millisecond deadline. Offline in a small group: one notification per message. Offline in a large group: collapsed, at most one per conversation per minute. The sender's own other devices are recipients too.

[slide: v-37]
C: The same message with Bob online on two devices. One: the worker reads Bob's session. It gets phone on gateway seven, laptop on gateway forty. Two and three, highlighted: two pushes, each with a deadline. Four and five: each gateway writes the frame down its socket. Six and seven: each device acknowledges for itself, and each cursor moves separately.

C: A failed push isn't retried by the worker. The log has it, and the device will come and get it.

[pause: 0.8]

[slide: v-38]
C: The leader in code, part one. First, the dedup check. Same client message I-D again? Return the original sequence. It has to come first, because otherwise a retry burns a number and leaves a gap, and every device would think it had lost a message. A retry can also beat the first attempt's commit, so the leader checks what's in flight, and attaches to that entry.

C: Then, the number: last sequence plus one. A stale leader is fenced off by its term. Then one Raft commit, with the message and the dedup row together. Both or neither. Only then, the ACK.

[pause: 0.8]

[slide: v-39]
C: Part two, the delivery worker. Read the members from cache, and all their sessions in one multi-get. Every online device gets a push, grouped by gateway, skipping only the device that sent it. With a deadline, so one slow gateway can't stall a partition.

C: Offline users get a wake-up, collapsed in large groups. Then commit the offset. A failed push doesn't block that. Durability already happened; delivery is best-effort on purpose.

N: The send path: containers, rules, sequence, routing, code. Now the sync path the same way.

[pause: 0.8]

## The sync path

[slide: v-40]
C: Level two, the sync path. A device comes back and talks to a gateway. Sync frames go to the sync service, in red. It asks the inbox index which conversations changed, then reads messages after each cursor. On the lower lane, delivered and read frames go to the receipt service, which advances the device cursors. At lower priority, so receipts can never delay messages.

[pause: 1.0]

[slide: v-41]
C: Bob comes back. One: the phone connects, resuming T-L-S. Two, highlighted, and the order matters: the gateway registers the session, before any read. Three: the phone sends its cursors. Four: the sync service asks which conversations changed. Five: it reads messages after each cursor, and streams them, then live. Six: the phone says delivered. And Alice sees two ticks.

I: Why does registering have to come first?

C: Because of the race. Read first and register after, and a message landing between the two is in neither. Registered first, it may arrive twice, which is fine, because the device upserts by sequence number.

[slide: v-42]
I: And if a push just fails, while the device stays connected?

C: Then gap-free numbers pay off. One: the laptop's at one two three four, and receives one two three six; the push of one two three five timed out. Two: it sees the gap, and holds one two three six back. Three: it syncs from one two three four. Four: the service reads. It gets both. Five: the upsert makes the second copy of one two three six a no-op. Six: delivered, up to one two three six.

C: Loss becomes detectable, on the device. But the last message in a chat has nothing after it to reveal a gap. So every few minutes a connected device also asks what changed, and syncs if a head number has moved.

[slide: v-43]
C: The sync service in code. The gateway registered this session before we got here. Ask the inbox what changed since the last sync. Then, newest conversation first, take the cursor, or for a brand new member, the join sequence. Read a page after it, and send it with a has-more flag.

C: The admission control is one check: if this device has used its burst, tell it to come back later. Last, send live.

[slide: v-44]
C: On the device, three decisions. Anything at or below the cursor is a repeat, so it's a no-op. If the number jumps past the cursor plus one, hold it and sync. And the kind check: unknown kinds still advance the cursor, so an old app never gets stuck.

V: At-least-once delivery, plus an idempotent device, is shown once.

[pause: 0.8]

[slide: v-45]
C: The latency budget. About twenty-five milliseconds to route and commit on a quorum. About a hundred for capture and the log. Ten for the registry and the hand-off. A hundred for the last hop to a phone. About two hundred and fifty typically; under five hundred at p ninety-nine.

I: And if the log lags?

C: Delivery slows, but sends and ACKs don't. So I alert on consumer lag separately.

## Deep dive one: ordering

[slide: v-46]
I: Two people in a group send at the same instant. What order does everyone see, and who decided?

[pause: 1.5]

[slide: v-47]
C: Not the clocks. Clocks skew, and users change them. One: member X's phone says ten o'clock and one second. Two: member Y's says ten o'clock exactly, because it's skewed. But X reached the leader first. Three: X gets five oh one. Four: Y gets five oh two. Five: every device renders five oh one, then five oh two.

C: That order is the truth for every participant on every device. Your own message shows as pending until the ACK brings its number, then it slots into place.

[slide: v-48]
I: Why per conversation? Why not one sequencer for everything?

C: A global order is a bottleneck nobody can see. A million messages a second, at about ten thousand per leader, is a hundred leaders at minimum. I'd run around a thousand partitions, at about a thousand a second each. The busiest group is hundreds of messages a second, which one leader handles. And group commit batches the disk writes.

[slide: v-49]
C: C4 level three, inside the message service. The gateway passes a send frame to the conversation router, which finds the partition leader. The dedup check comes next. If it's seen, it goes straight to the ACK builder with the original number. If it's new, it goes to the sequencer, in red, then to the writer, which puts the message and dedup row into one Raft entry and waits for a quorum. Then the ACK builder returns the number and server time.

[pause: 1.0]

[slide: v-50]
I: Your leader dies, mid-write. What happens to the order?

C: As a sequence. One: the phone sends. Two: the old leader, term five, appends sequence nine hundred to follower one. Then it dies, before a majority confirms. No ACK reaches the phone.

C: Three: follower one wins the election, since its log is the most complete. Now term six. Four: it commits its log tail, and last sequence is nine hundred. Five: the phone, having heard nothing, retries, with the same I-D. The dedup row is in that same entry, so the new leader finds it and returns nine hundred. No second copy.

C: And the other branch: if nine hundred hadn't survived, the retry would simply take nine hundred. If the old leader comes back, its stale term is refused.

[pause: 1.0]

[slide: v-51]
V: One authority per conversation. Failover can pause it, never reorder it.

[pause: 0.8]

C: Sends to that partition stall for seconds. That's the honest cost.

N: Anyone can say "a leader". Staff says what happens when it dies.

## Deep dive two: the lost ACK

[slide: v-52]
I: The server stored the message, but the phone went into a tunnel and never got the ACK. What happens?

[pause: 1.5]

[slide: v-53]
C: As a sequence. One: send, with client I-D c seventy-seven. Two: route. Three: commit as one thousand two hundred and thirty-four. Then the ACK goes out, and the tunnel swallows it. The app still shows pending.

C: Four, highlighted: when the network returns, it retries, with the same I-D. Five: route. Six: the dedup table has that I-D. And the ACK returns the original number. No duplicate is written, and none is shown.

[slide: v-54]
C: Every crash point has one outcome. Before reaching the leader: nothing is stored, so the retry stores it new. Before a majority: maybe a log tail survives, and either way it's stored once. After commit, before the ACK: the retry returns the original. The app killed and restarted: the message is in its local database, with its client I-D, so the same.

I: How long do you keep those dedup rows?

C: Fourteen days. And the app stops retrying after seven, then shows failed, and a manual resend is a new I-D. The window always covers the retry.

[slide: v-55]
V: The tick appears only after a real ACK.

[pause: 0.8]

C: So a message is never shown as sent when it wasn't, and a retry never shows twice.

## Deep dive three: groups and receipts

[slide: v-56]
I: Group of a thousand. Do you copy each message into a thousand inboxes? Defend that, or don't.

[pause: 1.5]

[slide: v-57]
C: I don't. Copies would be a thousand writes per message, a thousand updates per edit, and storage multiplied by the group size. A shared log is one write, one row per edit, and storage times one. Each member just has a cursor into it. One-to-one chats use the same model.

[slide: v-58]
I: But you have an inbox index per user. Isn't that a thousand writes after all?

C: It would be, so here's the arithmetic. A thousand-member group in a frenzy, a hundred messages a second. Copies: a hundred thousand writes a second, with bodies. An inbox update per message: also a hundred thousand, though small. But the inbox only says this conversation changed, and that fact overwrites itself. So the consumer coalesces to once a second: a thousand writes a second, off the send path. The log itself takes a hundred.

[slide: v-59]
C: Receipts are cursors, not per-message events. One: a reader sends read, up to twelve hundred and forty. Two: the receipt service keeps the larger value, so a late frame can't move a cursor back.

C: Then the two frames on the slide. Small group: three, forward the cursor to the sender's devices, asynchronously. Large group: nothing is forwarded. Four, highlighted: when someone opens message info, it counts on demand. Read by four hundred and twelve of a thousand.

[slide: v-60]
I: Why thirty-two? Why not a hundred?

C: Because the cost is squared. Each of n members tells n minus one others. Two members: two deliveries. Thirty-two: about a thousand. A hundred: about ten thousand. A thousand: about a million. I'd start the line around thirty-two, make it a config value, and measure.

C: A cursor coalesces a burst of messages. But it doesn't shrink the audience. The tier does that.

## Deep dive four: reconnects

[slide: v-61]
I: A gateway dies with half a million connections on it. What happens?

[pause: 1.5]

[slide: v-62]
C: The messages are safe. They were never in the gateway. What isn't safe is the reconnect. One: half a million sockets drop. Two, highlighted: each device waits a random delay of up to sixty seconds. That's jitter, in the client. Three: it reconnects. Four: the load balancer picks the least-loaded gateway, with T-L-S resumption saving most of the handshake. Five: sync, as small deltas.

C: And the alt frame: if sync is over capacity, it answers retry-after. The device stays connected, and comes back later.

[slide: v-63]
C: The arithmetic. One gateway: half a million in two seconds, without jitter. Over sixty seconds, about eight thousand a second. One whole zone is the real case: a third of everyone, thirty-three million. Drained over ten minutes, that's fifty-five thousand a second. And each one syncs maybe ten changed conversations, which I'm assuming: five hundred and fifty thousand reads a second on the message store.

C: That's what admission control protects. And on a deploy, gateways drain slowly, so we never cause this ourselves.

[slide: v-64]
I: And a phone that comes back after a month?

C: As a sequence. One: sync, with cursors a month old. Two: the inbox lists a hundred and eighty changed conversations. Three, highlighted: the service reads the newest twenty messages of each, newest conversation first. Useful in a second, capped per device, then live.

C: Four: the phone records a hole: conversation nine thousand and one, from twelve hundred and forty to eighty-seven hundred. Five: when the user scrolls, it fetches an older page. The hole shrinks.

## A requirement added mid-round

[slide: v-65]
I: New requirement. Users want to edit a message, and delete it for everyone, retroactively.

[pause: 1.5]

[slide: v-66]
C: Because the log is the single source of truth, an edit is another message in the log. Kind edit, naming the target, with its own sequence number. A delete is the same. And I update the original row: one write.

C: Then devices apply it. And see what's free: it has a number, so online, offline and multi-device already work. Cursors move past it like anything else. Had I copied messages into inboxes, every edit would be a thousand writes.

[slide: v-67]
C: The real cost is on the clients. A billion phones update slowly. So, version the protocol: the first frame carries a version, and the server keeps old shapes alive for the supported window.

C: And the rule from the device code: an old app ignores an unknown kind, and still advances its cursor. That has to be there in version one.

N: The delta, the cost, and what stays untouched.

## Failures and operations

[slide: v-68]
C: Failures. A gateway lost: jitter, resumption, cursor sync, admission control. A stale registry: the push fails, and the message waits in the log. Leader failover: seconds of pause, and retries with the same I-D. Log consumers lagging: delivery has priority over search and inbox. A region outage: conversations are homed per region, replicated asynchronously, and I'd state the risk: seconds of acknowledged messages could need reconciling on failover.

[slide: v-69]
C: For S-L-Os, I use probe devices that talk to each other all day. Send: ACK success and latency. Delivery: end-to-end latency, from those synthetic conversations. And integrity: the loss and duplicate rate on probe traffic, which should be exactly zero.

[slide: v-70]
C: Cost has two big items. The gateway fleet, two hundred and fifty to three hundred hosts, sized by sockets. And storage: sixty terabytes a day. Ninety days on fast disks is five point four petabytes; a year, if it all stayed there, is twenty-two. Cold copies with erasure coding are about one and a half times the data, not three. Half the bytes, on cheaper media.

## The EM layer, auxiliary

[slide: v-71]
N: The next two slides are the manager layer. In a Staff round, give them a sentence at most.

C: The invariant first. Phase one: store then deliver, one-to-one, with cursors and client I-Ds. That never changes afterwards. Phase two: groups, on the same log. Phase three: receipts at scale, and search.

[slide: v-72]
C: Four teams, along the data. Connections. Messaging core, which owns delivery on-call. Sync and clients. And search. The contracts: the frame protocol, and the message-stored event.

## The close

[slide: v-73]
C: To close.

V: Store first, with a sequence. Deliver second.

[pause: 0.8]

C: Messages are appended to a per-conversation log with a server sequence before the sender is acknowledged, and every device catches up by cursor. That gives one order, no loss and no duplicates, and offline and multi-device become the same path. Groups share one log, and receipts are cursors, aggregated in big groups. Next: reconnect storms, and tiering twenty petabytes a year.

I: Thanks. A few follow-ups.

## Follow-up 1: encryption by Friday

[slide: v-74]
I: The C-E-O announced end-to-end encryption on stage. Product wants a date by Friday.

[pause: 1.5]

[slide: v-75]
C: Start with what stays: the log, the sequence numbers, and cursors. The server orders ciphertext it can't read, so the core survives. What breaks: server-side search, which moves to the device. What costs: group messages are encrypted per device, and sender keys reduce that. What's lost: server-side moderation, so abuse reports carry decrypted copies, sent by the reporting user.

V: I won't decide a privacy question alone, and I won't let it be decided without the costs.

[pause: 0.8]

C: So by Friday, product gets one page: the options and a range for each. The date comes out of the decision.

## Follow-up 2: the deploy

[slide: v-76]
I: A gateway deploy restarts a whole zone at once. Delivery latency goes from half a second to forty seconds.

[pause: 1.5]

[slide: v-77]
C: Detect: sync latency and auth errors page on-call. Contain, first: pause the rollout, so it can't take the next zone, and tighten admission. Recover: let devices drain back, and let sync catch up. Learn: why could one deploy restart a zone? Gradual drain becomes part of every deploy, enforced by the pipeline.

V: No message is lost. The outage is latency, and the S-L-O tells us how bad.

[pause: 0.8]

## Follow-up 3: the broadcast channel

[slide: v-78]
I: Product wants broadcast channels, with a million subscribers each. Same system?

[pause: 1.5]

[slide: v-79]
C: The design's own weak spot. Each post would be a million pushes and a million inbox updates. So: keep the log and the sequencer, which see one write per post and don't notice. Change delivery: push only to people viewing the channel right now. Everyone else reads on open, by cursor, like a month-old phone. And drop per-reader cursors for an approximate counter per post.

V: Same log, different delivery.

[pause: 0.8]

N: A channel is a third tier on the field the worker already branches on.

## Follow-up 4: the storage bill

[slide: v-80]
I: Finance wants message storage cost down forty percent next year, with no product change.

[pause: 1.5]

[slide: v-81]
C: I slice first: messages, metadata, replicas, indexes. What grows fastest? The biggest lever is usually tiering: recent months on fast disks, older years on object storage. That alone can approach the target. Then compression. Retention is a product change, so it goes back to product. And I'd report cost per active user per month, so growth doesn't hide the trend.

## Follow-up 5: the on-call, auxiliary

[slide: v-82]
I: The messaging-core team was paged forty times last month. Two engineers have asked to move teams.

[pause: 1.5]

[slide: v-83]
C: First I'd talk to the two engineers, and listen. Then measure: forty pages, by alert and by hour. Page only on symptoms users feel, and send the rest to tickets. Fix the top three causes, with twenty percent of each sprint until pages halve.

V: Paging load is a team health metric. I track it next to the S-L-O, and I report both.

[pause: 0.8]

## Debrief

[slide: v-84]
N: Where it lands. Senior says WebSockets and a database; Staff says mailbox first, by minute twelve. Senior says a sequence number; Staff says a Raft leader per partition, and what failover does. Senior says retries are idempotent; Staff walks every crash point, with a dedup window that covers the retry. Senior says a shared log; Staff finds the receipt trap, n times n minus one, and the coalesced inbox. And on sync: register first, gaps detected, and protocol versions.

[slide: v-85]
N: Six checks before the real round. Store before deliver, said out loud. A server sequence per conversation, and who owns it on failover. The client message I-D, and the lost ACK walked through. Per-device cursors; register first; gap detection. The receipt trap, found with a number. And the manager layer only when the loop asks for it. Good luck.
