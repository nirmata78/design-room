#!/usr/bin/env python3
"""C4, data, sequence and follow-up diagrams for the SD-09 chat video (v2, Staff bar) → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg,erdsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-09-chat-messaging.md; the follow-up diagrams (fu-*) are new for this video. v1 in .v1-em-2026-10-29/."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq
from erdsvg import ERD, Chen

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

# ── Terms: socket first against mailbox first ────────────────────────────────────────────────────
d = c4.Diagram(1600, 700)
d.text(40, 40, "Socket first: deliver, then store", size=26, colour=RED, bold=True)
d.text(840, 40, "Mailbox first: store, then deliver", size=26, colour="#1168bd", bold=True)
d.node("s1", 40, 90, 220, 130, "person", "Sender", "", "", size=21)
d.node("s2", 340, 90, 220, 130, "container", "Server", "", "", size=21)
d.node("s3", 40, 330, 220, 130, "person", "Recipient online", "", "", size=20)
d.node("s4", 500, 330, 260, 130, "db", "Pending table", "if offline", "", size=20)
d.edge("s1", "s2", "", src="r:0.5", dst="l:0.5", dashed=False)
d.edge("s2", "s3", "push", "", src="b:0.3", dst="r:0.5", via=[(406, 395)], at=(330, 380), width=60)
d.edge("s2", "s4", "else store", "", src="b:0.75", dst="t:0.4", at=(560, 280), width=100)
d.node("m1", 840, 90, 220, 130, "person", "Sender", "", "", size=21)
d.node("m2", 1300, 90, 260, 130, "focus", "Conversation log", "stored, numbered", "", size=20)
d.node("m3", 840, 330, 220, 130, "person", "Device online", "", "", size=20)
d.node("m4", 1300, 330, 260, 130, "person", "Device offline", "", "", size=20)
d.edge("m1", "m2", "append, then ACK", "", src="r:0.5", dst="l:0.5", at=(1180, 140), width=190)
d.edge("m2", "m3", "push: early", "", src="b:0.2", dst="r:0.5", via=[(1352, 290), (1120, 290), (1120, 395)], at=(1200, 275), width=110)
d.edge("m2", "m4", "sync by cursor", "", src="b:0.65", dst="t:0.65", at=(1490, 280), width=150)
d.note(40, 530, 720, "Two code paths. A crash after the push and before the write loses the message; a retry shows it twice.",
       size=21, colour=RED, bg=RED_BG)
d.note(840, 530, 720, "One code path. Every device reads the same log after its own cursor. The socket only delivers early.",
       size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "socket-vs-mailbox.svg")

# ── Terms: the log and three device cursors ──────────────────────────────────────────────────────
d = ERD(1600, 620, size=22)
d.text(40, 50, "One conversation's log: numbers assigned by the server, with no gaps", size=24, colour="#1f2328", bold=True)
X0, W = 60, 142
for i, n in enumerate(range(1230, 1240)):
    x = X0 + i * (W + 6); col = "#c8341f" if n == 1239 else "#1168bd"
    d.raw(f'<rect x="{x}" y="90" width="{W}" height="90" rx="8" fill="#ffffff" stroke="{col}" stroke-width="2.4"/>')
    d.text(x + W / 2, 145, f"{n}", size=26, colour=col, bold=True, anchor="middle", mono=True)
for lab, n, y, col, say in [("Phone", 1239, 300, "#2d8a4e", "cursor 1239: up to date"),
                            ("Laptop", 1236, 390, "#a86a12", "cursor 1236: asks for 1237 onward"),
                            ("Tablet", 1231, 480, "#c8341f", "cursor 1231: offline; asks for 1232 onward")]:
    x = X0 + (n - 1230) * (W + 6) + W / 2
    d.raw(f'<line x1="{x:.0f}" y1="182" x2="{x:.0f}" y2="{y - 34}" stroke="{col}" stroke-width="2.6" stroke-dasharray="6 5"/>')
    d.raw(f'<circle cx="{x:.0f}" cy="{y - 28}" r="8" fill="{col}"/>')
    tx = x - 16 if n > 1234 else x + 16
    d.text(tx, y - 18, f"{lab}, {say}", size=23, colour=col, bold=True, anchor="end" if n > 1234 else "start")
d.note(40, 530, 1520, "A cursor is one number per device, per conversation: \"I have everything up to here.\" Offline is simply a cursor that is further behind.",
       size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "log-cursors.svg")

# ── Conceptual ERD, Chen notation ────────────────────────────────────────────────────────────────
d = Chen(1600, 860, size=22)
d.entity("dv", 190, 280, "DEVICE", weak=True, w=210)
d.entity("u", 740, 280, "USER", w=200)
d.entity("c", 1340, 280, "CONVERSATION", w=280)
d.entity("m", 1340, 720, "MESSAGE", weak=True, w=220)
d.rel("ow", 460, 280, "OWNS", identifying=True, w=170)
d.rel("mb", 1040, 280, "MEMBER OF", w=220)
d.rel("ct", 1340, 500, "CONTAINS", identifying=True, w=220)
d.rel("sd", 1000, 720, "SENDS", w=170)
d.rel("tr", 760, 70, "TRACKS POSITION IN", w=320, h=80)
d.link("u", "ow", "1", card_at=0.5)
d.link("ow", "dv", "N", total=True, card_at=0.5)
d.link("u", "mb", "M", card_at=0.5)
d.link("mb", "c", "N", card_at=0.5)
d.link("c", "ct", "1", card_at=0.5)
d.link("ct", "m", "N", total=True, card_at=0.5)
d.link("u", "sd", "1", src="b:0.5", via=[(740, 720)], card_at=0.3)
d.link("sd", "m", "N", total=True, card_at=0.5)
d.link("dv", "tr", "M", src="t:0.5", via=[(190, 70)], card_at=0.5)
d.link("tr", "c", "N", dst="t:0.5", via=[(1340, 70)], card_at=0.5)
d.attr("did", 80, 450, "device_id", of="dv", partial=True)
d.attr("dpl", 300, 450, "protocol_ver", of="dv")
d.attr("uid", 610, 450, "user_id", of="u", key=True)
d.attr("uhn", 860, 450, "handle", of="u")
d.attr("cid", 1520, 130, "conv_id", of="c", key=True)
d.attr("clq", 1520, 410, "last_seq", of="c", derived=True)
d.attr("cmt", 1120, 440, "member_count", of="c", derived=True)
d.attr("mrl", 1040, 150, "join_seq", of="mb")
d.attr("mq", 1180, 830, "seq", of="m", partial=True)
d.attr("mcl", 1510, 610, "client_msg_id", of="m")
d.attr("mbd", 1520, 720, "body", of="m")
d.attr("mts", 1450, 825, "server_ts", of="m")
d.attr("trd", 480, 165, "delivered_seq", of="tr")
d.attr("trr", 1040, 45, "read_seq", of="tr")
d.legend(20, 610, size=17, gap=26)
d.save(OUT / "erd-chen.svg")

# ── Physical tables ──────────────────────────────────────────────────────────────────────────────
d = ERD(1600, 820, size=22)
d.entity("m", 20, 20, 520, "messages", [("conv_id", "bigint", "PK"), ("bucket", "int (seq ÷ 2²⁰)", "PK"), ("seq", "bigint, cluster", "PK"),
         ("sender_id", "bigint", ""), ("client_msg_id", "uuid", ""), ("kind", "MSG | EDIT | DELETE", ""),
         ("body", "text", ""), ("server_ts", "timestamp", "")], kind="focus", caption="wide-column; never rewritten but for edits")
d.entity("cl", 20, 490, 520, "client_msgs", [("conv_id", "bigint", "PK"), ("client_msg_id", "uuid", "PK"), ("seq", "bigint", "")],
         caption="the dedup table · TTL 14 days · same partition")
d.entity("c", 600, 20, 480, "conversations", [("conv_id", "bigint", "PK"), ("kind", "DIRECT | GROUP", ""), ("tier", "SMALL | LARGE", ""),
         ("member_count", "int", ""), ("last_seq", "bigint", ""), ("home_region", "text", "")], caption="last_seq owned by the partition leader")
d.entity("cu", 600, 400, 480, "device_cursors", [("user_id", "bigint", "PK"), ("device_id", "bigint", "PK"), ("conv_id", "bigint", "PK"),
         ("delivered_seq", "bigint", ""), ("read_seq", "bigint", "")], caption="only ever moves forward: max(old, new)")
d.entity("mc", 1140, 20, 440, "members_by_conv", [("conv_id", "bigint", "PK"), ("user_id", "bigint", "PK"), ("role", "smallint", ""),
         ("join_seq", "bigint", "")], caption="who gets each message")
d.entity("mu", 1140, 340, 440, "convs_by_user", [("user_id", "bigint", "PK"), ("conv_id", "bigint", "PK"), ("muted", "bool", "")],
         caption="rebuilds an inbox")
d.rel("m", "c", "N", "1", src="r:0.5", dst="l:0.5")
d.rel("c", "mc", "1", "N", src="r:0.5", dst="l:0.5")
d.rel("cl", "m", "1", "1", src="t:0.2", dst="b:0.2", label="→ seq")
d.note(600, 690, 980, "conv_id + bucket caps a partition: a group's ten-year history spans many buckets, and the bucket is "
       "computed from seq, so no lookup is needed.", size=20)
d.save(OUT / "erd.svg")

# ── Wide-column: a partition per conversation ────────────────────────────────────────────────────
d = ERD(1600, 820, size=22)
d.text(40, 44, "messages · conv_id picks the Raft group · bucket splits it inside · clustering key = seq: the order",
       size=22, colour="#1f2328", bold=True, mono=False)
nodes = [("Raft group 7", [("9001, b0", True), ("4410, b3", False)]), ("Raft group 8", [("31, b0", False), ("7770, b1", False)]),
         ("Raft group 9", [("5120, b2", False), ("66, b0", False)])]
for i, (nm, parts) in enumerate(nodes):
    x = 40 + i * 520
    d.raw(f'<rect x="{x}" y="80" width="480" height="560" rx="12" fill="#f6f8fa" stroke="#8c959f" stroke-width="1.6"/>')
    d.text(x + 20, 116, nm + " · one leader, 2 followers", size=20, colour="#57606a", bold=True)
    for j, (aid, hot) in enumerate(parts):
        y = 140 + j * 245; col = "#c8341f" if hot else "#1168bd"
        d.raw(f'<rect x="{x + 20}" y="{y}" width="440" height="225" rx="8" fill="#ffffff" stroke="{col}" stroke-width="{3 if hot else 1.4}"/>')
        d.raw(f'<rect x="{x + 20}" y="{y}" width="440" height="40" rx="8" fill="{col}"/>')
        d.text(x + 36, y + 28, f"partition: {aid}", size=19, colour="#ffffff", bold=True, mono=True)
        first = 1235 if hot else 40 + 37 * i + 211 * j
        for k, r in enumerate([f"{first} → Hi, on my way", f"{first + 1} → See you there", f"{first + 2} → ok!", "…in seq order"]):
            d.text(x + 40, y + 74 + k * 40, r, size=19, colour="#1f2328" if k < 3 else "#8c959f", mono=True)
d.note(40, 660, 1520, "Query: conversation 9001, everything after 1234 = one partition, one sequential read, already in order. "
       "That is sync and history. Fan-out never rewrites it, and a bucket caps its size.", size=20, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "wide-column.svg")

# ── Hot key space: how the keys reference each other ─────────────────────────────────────────────
d = ERD(1600, 760, size=22)
d.entity("se", 20, 20, 500, "session:{user}   HASH", [("field", "deviceId", ""), ("value", "gatewayId", ""), ("TTL", "~5 min, refreshed", "")],
         kind="focus", caption="which gateway holds each device")
d.entity("gw", 1080, 20, 500, "gw:{gatewayId}   STRING", [("value", "host:port", ""), ("state", "ACTIVE | DRAINING", "")],
         kind="redis", caption="where to send a push")
d.entity("mb", 20, 300, 500, "members:{conv}   SET", [("member", "userId", ""), ("size", "≤ 1,000", "")], kind="redis",
         caption="read-through from members_by_conv")
d.entity("in", 20, 540, 500, "inbox:{user}   ZSET", [("member", "convId", ""), ("score", "last changed, ms", "")], kind="redis",
         caption="which conversations changed for this user")
d.entity("cu", 1080, 540, 500, "cursor:{user}:{device}   HASH", [("field", "convId", ""), ("value", "delivered, read", "")],
         kind="redis", caption="write-behind to device_cursors")
d.entity("ms", 660, 320, 340, "messages", [("key", "conv, bucket, seq", "")], kind="table", caption="the truth, on disk")
d.rel("se", "gw", "N", "1", src="r:0.4", dst="l:0.4", label="value → gw:{id}", at=(800, 86))
d.rel("mb", "se", "1", "1", src="t:0.5", dst="b:0.5", label="member → session:{user}")
d.rel("in", "ms", "N", "1", src="r:0.5", dst="b:0.3", via=[(762, 620)], label="read after cursor", at=(640, 606))
d.rel("cu", "ms", "N", "1", src="l:0.5", dst="b:0.7", via=[(898, 620)], label="position in", at=(990, 606))
d.note(560, 180, 480, "A push follows the top arrows; a sync follows the bottom ones.", size=19, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "keys.svg")

# ── Where each key comes from ────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
W = [("gt", 30, 230, "Gateway", "on connect, heartbeat, close", "batches refreshes every few minutes"),
     ("mc", 300, 100, "Membership consumer", "MemberChanged events", ""),
     ("ic", 430, 120, "Inbox consumer", "MessageStored events", "coalesces per second"),
     ("rc", 590, 150, "Receipt service", "DELIVERED and READ frames", "keeps the larger value")]
for nid, y, h, t, ty, ds in W:
    d.node(nid, 40, y, 440, h, "focus" if nid == "ic" else "container", t, ty, ds, size=21)
K = [("k1", 30, "session:{user}"), ("k2", 160, "gw:{gatewayId}"), ("k3", 300, "members:{conv}"),
     ("k4", 430, "inbox:{user}"), ("k5", 610, "cursor:{user}:{device}")]
for nid, y, t in K:
    d.node(nid, 1100, y, 460, 100, "db", t, "in-memory KV", "", size=21)
for a_, b_, lab, ya, yk in [("gt", "k1", "HSET on connect · EXPIRE batched · HDEL on close", 0.25, 30),
                            ("gt", "k2", "SET on boot · DRAINING on deploy", 0.75, 160),
                            ("mc", "k3", "SADD / SREM; read-through on a miss", 0.5, 300),
                            ("ic", "k4", "ZADD conv, now · once a second", 0.5, 430),
                            ("rc", "k5", "HSET max(old, new) · flush to the table", 0.5, 610)]:
    d.edge(a_, b_, lab, "", src=f"r:{ya}", dst="l:0.5", at=(790, yk + 36), width=500)
d.save(OUT / "writers.svg")

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.node("u", 40, 60, 330, 160, "person", "Users · 1 B", "Person", "100 M connected at once; up to 5 devices each")
d.node("chat", 620, 250, 380, 220, "focus", "Messaging system", "Software System",
       "Stores every message in order, delivers to every device, never loses or duplicates")
d.node("push", 1240, 60, 320, 160, "ext", "Push notification platform", "External System", "another team's (SD-12)")
d.node("os", 1240, 480, 320, 160, "ext", "Apple and Google push", "External System", "wakes a sleeping phone")
d.node("ops", 40, 500, 330, 150, "person", "Support and trust", "Person", "abuse reports, account recovery")
d.edge("u", "chat", "Send, sync, receipts", "WebSocket", src="r:0.5", dst="l:0.25", at=(480, 150), width=200)
d.edge("chat", "push", "Recipient offline", "RPC, 100 ms", src="r:0.2", dst="l:0.5", at=(1120, 150), width=170)
d.edge("push", "os", "Notify", "", src="b:0.5", dst="t:0.5", at=(1400, 350), width=80)
d.edge("ops", "chat", "Tools", "", src="r:0.5", dst="l:0.8", at=(480, 560), width=70)
d.legend(40, 735, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: send and deliver ─────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(250, 20, 1330, 780, "Messaging system")
d.node("a", 20, 80, 200, 130, "person", "Sender device", "Person")
d.node("gw1", 300, 70, 240, 150, "container", "Gateway", "WebSocket", "connections only")
d.node("ms", 640, 70, 300, 150, "focus", "Message service", "Container", "partition leader assigns seq")
d.node("db", 640, 320, 300, 150, "db", "Messages", "wide-column, Raft", "partition conv_id, cluster seq")
d.node("log", 1040, 320, 280, 150, "queue", "Message log", "key = conv_id", "delivery, inbox, search")
d.node("dlv", 1040, 70, 280, 150, "container", "Delivery workers", "Container", "find members' devices")
d.node("reg", 1380, 70, 180, 120, "db", "Session registry", "KV + TTL")
d.node("gw2", 1040, 580, 280, 150, "container", "Gateway", "WebSocket")
d.node("b", 640, 580, 300, 150, "person", "Recipient devices", "Person")
d.node("push", 1380, 580, 180, 150, "ext", "Push platform", "SD-12")
d.edge("a", "gw1", "SEND", "", src="r:0.5", dst="l:0.5", at=(260, 130), width=70)
d.edge("gw1", "ms", "", src="r:0.5", dst="l:0.5")
d.edge("ms", "db", "commit, then ACK", "", src="b:0.5", dst="t:0.5", at=(790, 270), width=160)
d.edge("db", "log", "CDC", "", src="r:0.5", dst="l:0.5", at=(990, 380), width=50)
d.edge("log", "dlv", "consume", "", src="t:0.5", dst="b:0.5", at=(1180, 270), width=90)
d.edge("dlv", "reg", "", src="r:0.4", dst="l:0.5")
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
d.node("srch", 1380, 220, 180, 130, "container", "Search", "async, from the log")
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
d.node("dd", 760, 70, 380, 150, "component", "Dedup check", "Component", "unique (conv_id, clientMsgId), first")
d.node("sq", 760, 300, 380, 150, "focus", "Sequencer", "partition leader", "seq = last_seq + 1, in arrival order")
d.node("wr", 760, 520, 380, 140, "component", "Writer", "Component", "message + dedup row: one Raft entry")
d.node("ack", 300, 520, 380, 140, "component", "ACK builder", "Component", "returns seq and server time")
d.node("db", 1320, 520, 250, 140, "db", "Messages", "3 replicas")
d.edge("gw", "rt", "SEND", "", src="r:0.5", dst="l:0.5", at=(255, 125), width=70)
d.edge("rt", "dd", "", src="r:0.5", dst="l:0.5")
d.edge("dd", "sq", "new", "", src="b:0.5", dst="t:0.5", at=(950, 260), width=60)
d.edge("sq", "wr", "", src="b:0.5", dst="t:0.5")
d.edge("dd", "ack", "seen: original seq", "", src="b:0.15", dst="t:0.7", via=[(817, 262), (566, 262)], at=(690, 245), width=190)
d.edge("wr", "db", "quorum", "", src="r:0.5", dst="l:0.5", at=(1230, 575), width=80)
d.edge("wr", "ack", "", src="l:0.5", dst="r:0.5")
d.save(OUT / "c4-component-message.svg")

# ── Sequence: commit before ACK ──────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Alice's phone", "person"), ("gw", "Gateway", "container"), ("ld", "Partition leader", "focus"),
                    ("f1", "Follower 1", "db"), ("f2", "Follower 2", "db"), ("cdc", "CDC → message log", "queue")]:
    s.part(pid, lab, k)
s.msg("a", "gw", "SEND {convId, clientMsgId, body}")
s.msg("gw", "ld", "route by conv_id")
s.msg("ld", "ld", "dedup, then seq = last_seq + 1", hl=True)
s.msg("ld", "f1", "Raft append: message + dedup row")
s.msg("ld", "f2", "Raft append: same entry")
s.ret("f1", "ld", "ok: a majority has it, committed")
s.ret("ld", "a", "ACK {seq}: one tick, sent", hl=True)
s.msg("ld", "cdc", "commit stream: MessageStored, key = convId", "async")
s.note("a", "cdc", "Crash before commit: no ACK, the app retries. Crash after commit: the retry finds the original.", "green")
s.save(OUT / "seq-commit.svg")

# ── Sequence: Alice sends to Bob, who is offline ─────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Alice's phone", "person"), ("ms", "Message service", "focus"), ("log", "Message log", "queue"),
                    ("dlv", "Delivery worker", "container"), ("reg", "Session registry", "db"), ("push", "Push platform", "ext"),
                    ("b", "Bob's phone", "person")]:
    s.part(pid, lab, k)
s.msg("a", "ms", "SEND")
s.ret("ms", "a", "ACK {seq: 1234}: one tick", hl=True)
s.msg("ms", "log", "MessageStored via CDC", "async")
s.msg("log", "dlv", "consume, partition by conv_id")
s.msg("dlv", "reg", "session:{bob}?")
s.ret("reg", "dlv", "no device online", hl=True)
s.msg("dlv", "push", "notify: new message from Alice")
s.msg("push", "b", "notification, no body needed", "async")
s.note("ms", "reg", "Nothing is waiting in a queue for Bob. The message is at seq 1234 in the log, and Bob's phone will ask for it.", "green")
s.save(OUT / "seq-send.svg")

# ── Delivery routing on kind and tier ────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.node("lg", 40, 300, 280, 150, "queue", "Message log", "key = convId", "", size=21)
d.node("wk", 420, 285, 320, 180, "focus", "Delivery worker", "Container", "reads tier and kind from the event", size=21)
d.node("n", 860, 40, 340, 160, "container", "Online device", "any tier", "batch per gateway, 200 ms deadline", size=21)
d.node("m", 860, 295, 340, 160, "container", "Offline, SMALL", "up to ~32 members", "one notification per message", size=21)
d.node("c", 860, 550, 340, 160, "container", "Offline, LARGE", "over ~32 members", "collapsed: one per conversation per minute", size=21)
d.node("gw", 1320, 40, 250, 160, "container", "Gateway", "WebSocket", "MSG frame", size=21)
d.node("pp", 1320, 420, 250, 160, "ext", "Push platform", "SD-12", "", size=21)
d.edge("lg", "wk", "consume", "", src="r:0.5", dst="l:0.5", at=(370, 360), width=90)
d.edge("wk", "n", "", "", src="t:0.5", dst="l:0.5", via=[(580, 120)])
d.edge("wk", "m", "", "", src="r:0.5", dst="l:0.5")
d.edge("wk", "c", "", "", src="b:0.5", dst="l:0.5", via=[(580, 630)])
d.edge("n", "gw", "push", "", src="r:0.5", dst="l:0.5", at=(1260, 105), width=70)
d.edge("m", "pp", "", "", src="r:0.5", dst="l:0.3")
d.edge("c", "pp", "", "", src="r:0.5", dst="l:0.75")
d.note(40, 560, 520, "The leader stamps tier into MessageStored from conversations.tier. kind is MSG, EDIT or DELETE: all three travel "
       "the same path, and the sender's own other devices are recipients too.", size=19, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "delivery-routing.svg")

# ── Sequence: Bob online on two devices ──────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("dlv", "Delivery worker", "focus"), ("reg", "Session registry", "db"), ("g1", "Gateway 7", "container"),
                    ("g2", "Gateway 40", "container"), ("p", "Bob's phone", "person"), ("l", "Bob's laptop", "person"),
                    ("rc", "Receipt service", "container")]:
    s.part(pid, lab, k)
s.msg("dlv", "reg", "session:{bob}")
s.ret("reg", "dlv", "phone → gateway 7; laptop → gateway 40")
s.msg("dlv", "g1", "push MSG seq 1234, deadline 200 ms", hl=True)
s.msg("dlv", "g2", "push MSG seq 1234, deadline 200 ms", hl=True)
s.msg("g1", "p", "MSG 1234")
s.msg("g2", "l", "MSG 1234")
s.msg("p", "rc", "DELIVERED upTo 1234 (phone's cursor)")
s.msg("l", "rc", "DELIVERED upTo 1234 (laptop's cursor)")
s.note("dlv", "rc", "A failed push is not retried by the worker: the log has it, and the device's next sync or gap check fetches it.", "amber")
s.save(OUT / "seq-online.svg")

# ── Sequence: Bob comes back and syncs ───────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("b", "Bob's phone", "person"), ("gw", "Gateway", "container"), ("reg", "Session registry", "db"),
                    ("sy", "Sync service", "focus"), ("ix", "Inbox index", "db"), ("db", "Messages", "db"), ("a", "Alice", "person")]:
    s.part(pid, lab, k)
s.msg("b", "gw", "connect, resume TLS")
s.msg("gw", "reg", "register session, before any read", hl=True)
s.msg("b", "sy", "SYNC {cursors, lastSyncTs}")
s.msg("sy", "ix", "conversations changed since?")
s.msg("sy", "db", "messages after each cursor")
s.ret("sy", "b", "MSG … then LIVE")
s.msg("b", "sy", "DELIVERED {upToSeq}")
s.ret("sy", "a", "two ticks: delivered", hl=True)
s.note("b", "db", "Registered first, read second: a message arriving mid-sync is pushed too, and the device upserts by seq.", "green")
s.save(OUT / "seq-sync.svg")

# ── Sequence: gap detection ──────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("gw", "Gateway", "container"), ("d", "Laptop (cursor 1234)", "focus"), ("sy", "Sync service", "container"),
                    ("db", "Messages", "db")]:
    s.part(pid, lab, k)
s.msg("gw", "d", "MSG 1236 (the push of 1235 timed out)")
s.msg("d", "d", "1235 is missing: hold 1236, don't render it yet", hl=True)
s.msg("d", "sy", "SYNC {conv: 1234}")
s.msg("sy", "db", "read after 1234")
s.ret("sy", "d", "MSG 1235, MSG 1236")
s.msg("d", "d", "upsert by (conv, seq): 1236 again is a no-op", hl=True)
s.msg("d", "sy", "DELIVERED upTo 1236")
s.note("gw", "db", "Gap-free numbers make loss detectable on the device. The last message has no later one to reveal it, so a periodic head check covers that.", "green")
s.save(OUT / "seq-gap.svg")

# ── Sequence: two members send at once ───────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("x", "Member X", "person"), ("y", "Member Y", "person"), ("sq", "Partition leader", "focus"),
                    ("db", "Messages", "db"), ("all", "Every device", "person")]:
    s.part(pid, lab, k)
s.msg("x", "sq", "SEND, client clock 10:00:01")
s.msg("y", "sq", "SEND, client clock 10:00:00 (skewed)")
s.msg("sq", "db", "X arrived first: seq 501", hl=True)
s.msg("sq", "db", "Y: seq 502", hl=True)
s.msg("db", "all", "everyone renders 501, then 502", "async")
s.note("x", "all", "Client timestamps are ignored for order. One authority per conversation is the truth.", "amber")
s.save(OUT / "seq-order.svg")

# ── Sequence: leader failover without reordering ─────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Sender phone", "person"), ("ld", "Old leader, term 5", "ext"), ("nl", "Follower 1 → new leader, term 6", "focus"),
                    ("f2", "Follower 2", "db")]:
    s.part(pid, lab, k)
s.msg("a", "ld", "SEND c-77")
s.msg("ld", "nl", "append seq 900, term 5")
s.note("ld", "f2", "The leader dies before it has a majority. No ACK reaches the phone.", "red")
s.msg("nl", "f2", "wins the election: its log is the most complete", hl=True)
s.msg("nl", "nl", "commit its log tail; last_seq = 900", hl=True)
s.msg("a", "nl", "retry: same c-77, seconds later")
s.ret("nl", "a", "dedup finds seq 900: ACK, no second copy")
s.note("a", "f2", "Had 900 not survived, the retry would take 900. Term 5 can't write: a stale term is fenced. Order and numbers hold.", "green")
s.save(OUT / "seq-failover.svg")

# ── Sequence: the lost ACK ───────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Sender phone", "person"), ("gw", "Gateway", "container"), ("ms", "Partition leader", "focus"),
                    ("db", "Messages + client_msgs", "db")]:
    s.part(pid, lab, k)
s.msg("a", "gw", "SEND clientMsgId=c-77")
s.msg("gw", "ms", "route")
s.msg("ms", "db", "commit as seq 1,234")
s.ret("ms", "gw", "ACK seq 1,234")
s.note("gw", "a", "Tunnel: the ACK never arrives. The app still shows pending.", "red")
s.msg("a", "gw", "retry: same clientMsgId=c-77", hl=True)
s.msg("gw", "ms", "route")
s.msg("ms", "db", "client_msgs (conv, c-77) exists")
s.ret("ms", "a", "ACK seq 1,234: the original, no duplicate", hl=True)
s.save(OUT / "seq-lost-ack.svg")

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
s.msg("rc", "cur", "read_seq = max(old, 1,240)")
s.frame("alt", "SMALL: up to ~32 members")
s.msg("rc", "s", "forward the cursor", "async")
s.end()
s.frame("alt", "LARGE: up to 1,000 members")
s.msg("info", "cur", "count readers on demand", hl=True)
s.ret("cur", "info", "read by 412 of 1,000")
s.end()
s.save(OUT / "seq-receipts.svg")

# ── Sequence: a gateway dies ─────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("d", "500 k devices", "person"), ("gw", "Gateway (dead)", "ext"), ("lb", "Load balancer", "container"),
                    ("ng", "Other gateways", "container"), ("sy", "Sync service", "focus")]:
    s.part(pid, lab, k)
s.msg("gw", "gw", "crash: 500 k sockets drop")
s.msg("d", "d", "wait a random delay, up to 60 s: jitter", hl=True)
s.msg("d", "lb", "reconnect")
s.msg("lb", "ng", "least connections; TLS resumption")
s.msg("d", "sy", "SYNC: deltas since each cursor")
s.frame("alt", "sync over capacity")
s.ret("sy", "d", "retry-after: stay connected, come back later", hl=True)
s.end()
s.note("d", "sy", "Messages were never in the gateway. They are in the log.", "green")
s.save(OUT / "seq-reconnect.svg")

# ── Sequence: a month offline ────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("p", "Phone, a month stale", "person"), ("sy", "Sync service", "focus"), ("ix", "Inbox index", "db"),
                    ("db", "Messages", "db")]:
    s.part(pid, lab, k)
s.msg("p", "sy", "SYNC {cursors, lastSyncTs: 30 days ago}")
s.msg("sy", "ix", "changed since: 180 conversations")
s.msg("sy", "db", "newest 20 messages of each, newest conversation first", hl=True)
s.ret("sy", "p", "MSG pages, capped per device · then LIVE")
s.msg("p", "p", "record a hole: conv 9001, seq 1,240 to 8,700", hl=True)
s.msg("p", "sy", "user scrolls: GET messages beforeSeq=8,701")
s.ret("sy", "p", "older page: the hole shrinks")
s.save(OUT / "seq-month.svg")

# ── Mid-round: edit and delete as events ─────────────────────────────────────────────────────────
row_of("midround-edit", [("Append an event", "to the conversation", "kind EDIT or DELETE; it gets its own seq"),
                         ("Update the row", "the source of truth", "one write, not 1,000"),
                         ("Devices apply it", "on sync or push", "the cursor moves past it like any message")],
       note="The event has a seq, so no new path is needed: online, offline and multi-device all get it for free.",
       arrows=True, focus=0)

# ── EM: phasing ──────────────────────────────────────────────────────────────────────────────────
row_of("em-phases", [("Store, then deliver", "phase 1", "1:1 with cursors and clientMsgId"),
                     ("Groups", "phase 2", "the same log, membership, inbox index"),
                     ("Receipts at scale", "phase 3", "aggregation for big groups; search")],
       note="Correctness first: the invariant (stored before acknowledged) ships in phase 1 and never changes.",
       tone=(GREEN, GREEN_BG), arrows=True, focus=0)

# ── Follow-up 1: end-to-end encryption ───────────────────────────────────────────────────────────
row_of("fu-e2e", [("What stays", "log, seq, cursors", "the server orders ciphertext it cannot read"),
                  ("What breaks", "server-side search", "search moves to the device"),
                  ("What costs", "group fan-out", "encrypt per device; sender keys reduce it"),
                  ("What's lost", "server moderation", "reports carry decrypted copies, by consent")],
       note="Product, legal and policy decide. Engineering brings one page: the options, their costs and timelines.",
       focus=0)

# ── Follow-up 2: the reconnect storm after a deploy ──────────────────────────────────────────────
row_of("fu-incident", [("Detect", "0–5 min", "sync latency and auth errors page on-call"),
                       ("Contain", "5–20 min", "pause the rollout; tighten admission"),
                       ("Recover", "20–60 min", "drain gradually; let sync catch up"),
                       ("Learn", "next week", "drain is part of every deploy; game day")],
       note="No message is lost: they are in the log. The outage is latency, so the SLO tells you how bad.",
       tone=(RED, RED_BG), arrows=True, focus=1)

# ── Follow-up 3: a broadcast channel with a million subscribers ──────────────────────────────────
row_of("fu-channel", [("What breaks", "1 M × each post", "a million pushes and inbox upserts, per message"),
                      ("Keep", "the log and seq", "one write per post; the sequencer doesn't notice"),
                      ("Change", "push only to viewers", "the rest read on open, by cursor"),
                      ("Drop", "per-reader cursors", "a counter, approximate, per post")],
       note="Same log, different delivery. A channel is a third tier on the field the worker already branches on.",
       focus=2)

# ── Follow-up 4: storage cost ────────────────────────────────────────────────────────────────────
row_of("fu-cost", [("Slice first", "what grows?", "messages, metadata, replicas, indexes"),
                   ("Tier history", "hot months, cold years", "recent on fast disks, old on object storage"),
                   ("Compress", "by conversation", "older partitions compress well"),
                   ("Retention", "a product question", "so not in my plan: no product change")],
       note="Report cost per active user per month. The tiering lever alone can approach the target.",
       tone=(GREEN, GREEN_BG), focus=1)

# ── Follow-up 5: the on-call is burning ──────────────────────────────────────────────────────────
row_of("fu-oncall", [("Measure", "pages by cause", "40 pages: which alerts, which hours"),
                     ("Cut noise", "symptoms only", "page on delivery-latency SLO, not on CPU"),
                     ("Fix the top 3", "a reserved budget", "20% of each sprint until pages halve"),
                     ("Protect people", "rotation and rest", "time off after a bad night; review monthly")],
       note="Paging load is a team health metric. Track it next to the SLO, and report both upward.",
       focus=2)
print("diagrams →", OUT)
