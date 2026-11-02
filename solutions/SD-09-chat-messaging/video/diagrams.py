#!/usr/bin/env python3
"""C4, sequence and follow-up diagrams for the SD-09 chat video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-09-chat-messaging.md; the follow-up diagrams (fu-*) are new for this video."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa"

def seq(size=22, row=50):
    return sq.Seq(1500, size=size, row=row, head=66)

def row_of(name, items, note=None, tone=(BLUE, BLUE_BG), arrows=False, focus=None, h=560):
    d = c4.Diagram(1600, h)
    n = len(items); w = (1520 - (n - 1) * 40) // n
    for i, (h_, t, desc) in enumerate(items):
        d.node(f"n{i}", 40 + i * (w + 40), 70, w, 240, "focus" if i == focus else "container", h_, t, desc,
               size=25 if n > 3 else 27)
    if arrows:
        for i in range(n - 1):
            d.edge(f"n{i}", f"n{i+1}", "", src="r", dst="l", dashed=False)
    if note:
        d.note(40, 370, 1520, note, size=21, colour=tone[0], bg=tone[1])
    d.save(OUT / f"{name}.svg")

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.node("u", 40, 60, 330, 160, "person", "Users · 1 B", "Person", "100 M connected at once; up to 5 devices each")
d.node("chat", 620, 250, 380, 220, "focus", "Messaging system", "Software System",
       "Stores every message in order, delivers to every device, never loses or duplicates")
d.node("push", 1240, 60, 320, 160, "ext", "Push notifications", "External System", "wakes offline devices (SD-12)")
d.node("os", 1240, 480, 320, 160, "ext", "Mobile OS push services", "External System", "the platforms' own gateways")
d.node("ops", 40, 500, 330, 150, "person", "Support and trust", "Person", "abuse reports, account recovery")
d.edge("u", "chat", "Send, sync, receipts", "WebSocket", src="r:0.5", dst="l:0.25", at=(480, 150), width=200)
d.edge("chat", "push", "Offline recipient", "", src="r:0.2", dst="l:0.5", at=(1120, 150), width=170)
d.edge("push", "os", "Notify", "", src="b:0.5", dst="t:0.5", at=(1400, 350), width=80)
d.edge("ops", "chat", "Tools", "", src="r:0.5", dst="l:0.8", at=(480, 560), width=70)
d.legend(40, 735, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: send and deliver ─────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(250, 20, 1330, 780, "Messaging system")
d.node("a", 20, 80, 200, 130, "person", "Sender device", "Person")
d.node("gw1", 300, 70, 240, 150, "container", "Gateway", "WebSocket", "connections only")
d.node("ms", 640, 70, 300, 150, "focus", "Message service", "Container", "conversation leader assigns seq")
d.node("db", 640, 320, 300, 150, "db", "Messages", "wide-column", "partition conv_id, cluster seq")
d.node("log", 1040, 320, 280, 150, "queue", "Message log", "by conv_id", "delivery, push, search")
d.node("dlv", 1040, 70, 280, 150, "container", "Delivery workers", "Container", "find members' devices")
d.node("reg", 1380, 70, 180, 150, "db", "Session registry", "KV + TTL")
d.node("gw2", 1040, 580, 280, 150, "container", "Gateway", "WebSocket")
d.node("b", 640, 580, 300, 150, "person", "Recipient devices", "Person")
d.node("push", 1380, 580, 180, 150, "ext", "Push", "SD-12")
d.edge("a", "gw1", "SEND", "", src="r:0.5", dst="l:0.5", at=(260, 130), width=70)
d.edge("gw1", "ms", "", src="r:0.5", dst="l:0.5")
d.edge("ms", "db", "append, then ACK", "", src="b:0.5", dst="t:0.5", at=(790, 270), width=160)
d.edge("db", "log", "CDC", "", src="r:0.5", dst="l:0.5", at=(990, 380), width=50)
d.edge("log", "dlv", "consume", "", src="t:0.5", dst="b:0.5", at=(1180, 270), width=90)
d.edge("dlv", "reg", "", src="r:0.5", dst="l:0.5")
d.edge("dlv", "gw2", "online", "", src="r:0.8", dst="r:0.3", via=[(1350, 190), (1350, 625)], at=(1350, 480), width=70)
d.edge("gw2", "b", "MSG", "", src="l:0.5", dst="r:0.5", at=(990, 640), width=60)
d.edge("dlv", "push", "offline", "", src="r:0.95", dst="t:0.5", via=[(1470, 212)], at=(1470, 400), width=80)
d.save(OUT / "c4-containers-send.svg")

# ── C4 level 2: sync and receipts ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.boundary(250, 20, 1330, 740, "Messaging system")
d.node("dev", 20, 280, 200, 150, "person", "Device", "Person", "back online")
d.node("gw", 300, 270, 240, 170, "container", "Gateway", "WebSocket")
d.node("sync", 640, 70, 300, 150, "focus", "Sync service", "Container", "deltas after each cursor")
d.node("rc", 640, 480, 300, 150, "container", "Receipt service", "Container", "lower priority path")
d.node("inbox", 1040, 40, 300, 130, "db", "Inbox index", "by user", "which conversations changed")
d.node("db", 1040, 220, 300, 130, "db", "Messages", "by conv_id")
d.node("cur", 1040, 480, 300, 150, "db", "Device cursors", "", "delivered_seq, read_seq")
d.node("srch", 1380, 220, 180, 130, "container", "Search", "async")
d.edge("dev", "gw", "SYNC", "", src="r:0.5", dst="l:0.5", at=(260, 340), width=70)
d.edge("gw", "sync", "", src="r:0.2", dst="l:0.5", via=[(590, 304), (590, 145)])
d.edge("gw", "rc", "DELIVERED, READ", "", src="r:0.8", dst="l:0.5", via=[(590, 406), (590, 555)], at=(590, 480), width=170)
d.edge("sync", "inbox", "changed?", "", src="r:0.3", dst="l:0.5", at=(990, 100), width=90)
d.edge("sync", "db", "after seq N", "", src="r:0.7", dst="l:0.5", at=(990, 260), width=110)
d.edge("rc", "cur", "advance", "", src="r:0.5", dst="l:0.5", at=(990, 540), width=80)
d.edge("db", "srch", "", src="r:0.5", dst="l:0.5")
d.save(OUT / "c4-containers-sync.svg")

# ── C4 level 3: inside the message service ───────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.boundary(240, 20, 960, 720, "Message service", "Container")
d.node("gw", 20, 80, 190, 140, "container", "Gateway", "")
d.node("rt", 300, 70, 380, 150, "component", "Conversation router", "Component", "finds the conv_id's partition leader")
d.node("sq", 760, 70, 380, 150, "focus", "Sequencer", "partition leader", "seq = last_seq + 1, in arrival order")
d.node("dd", 760, 300, 380, 150, "component", "Dedup check", "Component", "unique (conv_id, clientMsgId)")
d.node("wr", 760, 520, 380, 140, "component", "Writer", "Component", "replicated write + outbox, then ACK")
d.node("ack", 300, 520, 380, 140, "component", "ACK builder", "Component", "returns seq and server time")
d.node("db", 1320, 520, 250, 140, "db", "Messages", "")
d.edge("gw", "rt", "SEND", "", src="r:0.5", dst="l:0.5", at=(255, 125), width=70)
d.edge("rt", "sq", "", src="r:0.5", dst="l:0.5")
d.edge("sq", "dd", "", src="b:0.5", dst="t:0.5")
d.edge("dd", "wr", "new", "", src="b:0.5", dst="t:0.5", at=(950, 485), width=60)
d.edge("dd", "ack", "seen: original seq", "", src="l:0.5", dst="t:0.5", via=[(490, 375)], at=(600, 360), width=190)
d.edge("wr", "db", "", src="r:0.5", dst="l:0.5")
d.edge("wr", "ack", "", src="l:0.5", dst="r:0.5")
d.save(OUT / "c4-component-message.svg")

# ── Sequence: Alice sends to Bob, who is offline ─────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Alice's phone", "person"), ("gw", "Gateway", "container"), ("ms", "Message service", "focus"),
                    ("db", "Messages", "db"), ("dlv", "Delivery worker", "container"), ("push", "Push", "ext"),
                    ("b", "Bob's phone", "person")]:
    s.part(pid, lab, k)
s.msg("a", "gw", "SEND {convId, clientMsgId, body}")
s.msg("gw", "ms", "route to the conversation leader")
s.msg("ms", "db", "seq = last + 1; durable, replicated write", hl=True)
s.ret("ms", "a", "ACK {seq}: one tick, sent", hl=True)
s.msg("db", "dlv", "via the log", "async")
s.msg("dlv", "dlv", "registry: no device online")
s.msg("dlv", "push", "notify: new message from Alice")
s.msg("push", "b", "notification", "async")
s.save(OUT / "seq-send.svg")

# ── Sequence: Bob comes back and syncs ───────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("b", "Bob's phone", "person"), ("gw", "Gateway", "container"), ("sy", "Sync service", "focus"),
                    ("ix", "Inbox index", "db"), ("db", "Messages", "db"), ("a", "Alice", "person")]:
    s.part(pid, lab, k)
s.msg("b", "gw", "connect")
s.msg("b", "sy", "SYNC {convId: lastSeq, …}", hl=True)
s.msg("sy", "ix", "which conversations changed?")
s.msg("sy", "db", "messages after each cursor")
s.ret("sy", "b", "MSG … then LIVE")
s.msg("b", "sy", "DELIVERED {upToSeq}")
s.ret("sy", "a", "two ticks: delivered", hl=True)
s.note("b", "db", "Online and offline are one code path: the push only delivers early.", "green")
s.save(OUT / "seq-sync.svg")

# ── Sequence: the lost ACK ───────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Sender phone", "person"), ("gw", "Gateway", "container"), ("ms", "Message service", "focus"),
                    ("db", "Messages", "db")]:
    s.part(pid, lab, k)
s.msg("a", "gw", "SEND clientMsgId=c-77")
s.msg("gw", "ms", "")
s.msg("ms", "db", "store as seq 1,234")
s.ret("ms", "gw", "ACK seq 1,234")
s.note("gw", "a", "Tunnel: the ACK never arrives. The app still shows pending.", "red")
s.msg("a", "gw", "retry: same clientMsgId=c-77", hl=True)
s.msg("gw", "ms", "")
s.msg("ms", "db", "unique (conv, c-77) exists")
s.ret("ms", "a", "ACK seq 1,234: the original, no duplicate", hl=True)
s.save(OUT / "seq-lost-ack.svg")

# ── Sequence: two members send at once ───────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("x", "Member X", "person"), ("y", "Member Y", "person"), ("sq", "Conversation leader", "focus"),
                    ("db", "Messages", "db"), ("all", "Every device", "person")]:
    s.part(pid, lab, k)
s.msg("x", "sq", "SEND, client clock 10:00:01")
s.msg("y", "sq", "SEND, client clock 10:00:00 (skewed)")
s.msg("sq", "db", "X arrived first: seq 501", hl=True)
s.msg("sq", "db", "Y: seq 502", hl=True)
s.msg("db", "all", "everyone renders 501, then 502", "async")
s.note("x", "all", "Client timestamps are ignored for order. One sequencer per conversation is the truth.", "amber")
s.save(OUT / "seq-order.svg")

# ── Groups: copies vs shared log ─────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 600)
d.node("cp", 40, 60, 700, 300, "ext", "Per-member inbox copies", "rejected",
       "1,000 writes per message · edit means 1,000 updates · storage × group size", size=28)
d.node("sl", 860, 60, 700, 300, "focus", "Shared log + cursors", "chosen",
       "1 write per message · edit is one row · storage × 1 · inbox index says what changed", size=28)
d.note(40, 420, 1520, "The same model for 1:1 chats: one code path for every conversation size.", size=22,
       colour=GREEN, bg=GREEN_BG)
d.save(OUT / "groups.svg")

# ── Sequence: receipts as cursors ────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("r", "Reader device", "person"), ("rc", "Receipt service", "focus"), ("cur", "Device cursors", "db"),
                    ("s", "Sender devices", "person"), ("info", "Message info view", "container")]:
    s.part(pid, lab, k)
s.msg("r", "rc", "READ {convId, upToSeq: 1,240}: covers many messages")
s.msg("rc", "cur", "advance read_seq")
s.frame("alt", "1:1 or small group")
s.msg("rc", "s", "forward the cursor", "async")
s.end()
s.frame("alt", "group of 1,000")
s.msg("info", "cur", "count readers on demand", hl=True)
s.ret("cur", "info", "read by 412 of 1,000")
s.end()
s.save(OUT / "seq-receipts.svg")

# ── Sequence: a gateway dies ─────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("d", "500 k devices", "person"), ("gw", "Gateway (dead)", "ext"), ("lb", "Load balancer", "container"),
                    ("sy", "Sync service", "focus"), ("ng", "Other gateways", "container")]:
    s.part(pid, lab, k)
s.msg("gw", "gw", "crash: 500 k sockets drop")
s.msg("d", "lb", "reconnect after jittered backoff", hl=True)
s.msg("lb", "ng", "spread over minutes, TLS resumption")
s.msg("d", "sy", "SYNC: deltas since seq N (cheap)")
s.msg("sy", "sy", "admission control on sync", hl=True)
s.note("d", "sy", "Messages were never in the gateway. They are in the log.", "green")
s.save(OUT / "seq-reconnect.svg")

# ── Mid-round: edit and delete as events ─────────────────────────────────────────────────────────
row_of("midround-edit", [("Append an event", "to the conversation", "EDIT seq 1,234 · DELETE seq 1,240"),
                         ("Update the row", "the source of truth", "one write, not 1,000"),
                         ("Devices apply it", "on sync", "old clients ignore unknown events safely")],
       note="Version the protocol: an unknown event type must be harmless on a phone that hasn't updated.",
       arrows=True, focus=0)

# ── EM: phasing ──────────────────────────────────────────────────────────────────────────────────
row_of("em-phases", [("Store, then deliver", "phase 1", "1:1 with cursors and clientMsgId"),
                     ("Groups", "phase 2", "the same log, membership, inbox index"),
                     ("Receipts at scale", "phase 3", "aggregation for big groups; search")],
       note="Correctness first: the invariant (stored before acknowledged) ships in phase 1 and never changes.",
       tone=(GREEN, GREEN_BG), arrows=True, focus=0)

# ── Follow-up 1: end-to-end encryption ───────────────────────────────────────────────────────────
row_of("fu-e2e", [("What breaks", "server-side search", "search moves to the device"),
                  ("What costs", "group fan-out", "encrypt per device; sender keys reduce it"),
                  ("What's lost", "server moderation", "reports carry decrypted copies by consent"),
                  ("Who decides", "product, legal, policy", "engineering prices the options")],
       note="Bring a one-page options paper with costs and timelines. Don't decide a privacy question alone.",
       focus=3)

# ── Follow-up 2: the reconnect storm after a deploy ──────────────────────────────────────────────
row_of("fu-incident", [("Detect", "0–5 min", "sync latency and auth errors page on-call"),
                       ("Contain", "5–20 min", "pause the rollout; tighten admission"),
                       ("Recover", "20–60 min", "drain gradually; let sync catch up"),
                       ("Learn", "next week", "drain is part of every deploy; game day")],
       note="No message is lost: they are in the log. The outage is latency, so the SLO tells you how bad.",
       tone=(RED, RED_BG), arrows=True, focus=1)

# ── Follow-up 3: the on-call is burning ──────────────────────────────────────────────────────────
row_of("fu-oncall", [("Measure", "pages by cause", "40 pages: which alerts, which hours"),
                     ("Cut noise", "symptoms only", "page on delivery-latency SLO, not on CPU"),
                     ("Fix the top 3", "a reserved budget", "20% of each sprint until pages halve"),
                     ("Protect people", "rotation and rest", "time off after a bad night; review monthly")],
       note="Paging load is a team health metric. Track it next to the SLO, and report both upward.",
       focus=2)

# ── Follow-up 4: storage cost ────────────────────────────────────────────────────────────────────
row_of("fu-cost", [("Slice first", "what grows?", "messages, metadata, replicas, indexes"),
                   ("Tier history", "hot months, cold years", "recent on fast disks, old on object storage"),
                   ("Compress", "by conversation", "older partitions compress well"),
                   ("Retention", "a product question", "media and deleted data first")],
       note="Report cost per active user per month. The tiering lever alone can approach the target.",
       tone=(GREEN, GREEN_BG), focus=1)
print("diagrams →", OUT)
