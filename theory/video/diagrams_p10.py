#!/usr/bin/env python3
"""Part 10 figures (diagrams/p10.md). Run: python3 diagrams_p10.py [name …] → svg/p10-*.svg"""
import math, sys
from dg import *


def cells(x, y, labels, w=90, h=60, fill="#ddeaf8", col=BLUE, size=22):
    out = []
    for i, l in enumerate(labels):
        out.append(rect(x + i * w, y, w, h, fill, col, 2, 3))
        out.append(text(x + i * w + w / 2, y + h / 2 + 8, l, size, INK, "middle", 700))
    return "".join(out)


# ---------------------------------------------------------------- p10-queue-log
def queue_log():
    W, H = 1600, 720
    b = [panel(20, 20, 640, 680, "grey"), panel(690, 20, 890, 680, "grey")]
    b.append(title(340, 66, "Queue", 28, INK, "middle")); b.append(title(1135, 66, "Log", 28, INK, "middle"))
    b.append(rect(60, 150, 400, 100, "#fff", INK, 2.5, 10))
    b.append(cells(90, 170, ["m5", "m6", "m7"], 110, 60))
    b.append(f'<g opacity="0.3">{cells(90 + 330, 280, ["m4"], 110, 60, "#eef1f4", GREY)}</g>')
    b.append(text(475, 375, "deleted on ack", 21, MUTED, "middle", 700))
    for k in range(3):
        y = 400 + k * 95
        b.append(box(100, y, 200, 70, "worker", GREEN, size=22))
        b.append(line(145 + k * 110, 252, 200, y - 4, GREEN, 2.5, "", True))
    b.append(text(340, 680, "each message to one worker, then gone", 21, MUTED, "middle", 600))
    x0, cw = 720, 64
    b.append(cells(x0, 330, [str(i) for i in range(13)], cw, 70, size=21))
    b.append(text(1135, 660, "offsets · all kept until retention", 21, MUTED, "middle", 600))
    for off, lab, col, y in ((9, "group: fulfilment @ 9", BLUE, 240), (4, "group: analytics @ 4", RED, 160)):
        x = x0 + off * cw + cw / 2
        b.append(line(x, y + 12, x, 324, col, 3, "", True))
        b.append(text(x, y, lab, 22, col, "middle", 800, True))
    ax = x0 + 4 * cw + cw / 2
    b.append(path(f"M{ax},{410} C{ax},{560} {x0 + 30},{560} {x0 + 30},{412}", RED, 3.5, "", True))
    b.append(text(ax - 40, 600, "rewind → replay", 24, RED, "middle", 800, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-segments
def segments():
    W, H = 1600, 700
    names = ["00000000.log", "05000000.log", "10000000.log", "15000000.log (active)"]
    b = []
    for i, n in enumerate(names):
        x = 40 + i * 380
        act = i == 3
        b.append(box(x, 150, 340, 130, [n, "~1 GB"], GREEN if act else BLUE, size=22))
        b.append(box(x, 320, 340, 90, [".index", "offset → byte position, every 4 KB"], GREY, size=20 if False else 21, weight=700))
    b.append(cross(210, 215, 60, GREY, 8))
    b.append(text(210, 470, "retention deletes whole file", 22, MUTED, "middle", 700))
    b.append(arrow(1440, 60, 1440, 146, colour=GREEN, w=4, lines=["append"], weight=800))
    b.append(path("M590,600 L590,412", RED, 4, "", True))
    b.append(text(800, 650, "read offset 5,000,040 → segment 05000000 → index → scan a few KB", 24, RED, "middle", 800))
    b.append(line(590, 318, 590, 284, RED, 4, "", True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-isr
def isr():
    W, H = 1600, 640
    x0, cw = 260, 78
    ends = [("Leader", 112), ("Follower 1", 110), ("Follower 2", 108)]
    b = []
    for k, (lab, e) in enumerate(ends):
        y = 120 + k * 120
        b.append(text(x0 - 20, y + 42, lab, 24, INK, "end", 700))
        offs = list(range(100, e + 1))
        b.append(cells(x0, y, [str(o) for o in offs], cw, 64, size=21))
    hw = x0 + 9 * cw
    b.append(line(hw, 90, hw, 500, RED, 4, "10 7"))
    b.append(text(hw, 76, "high watermark · 108", 24, RED, "middle", 800, True))
    b.append(vbracket(x0 + 13 * cw + 30, 120, 424, BLUE, True, 18))
    b.append(text(x0 + 13 * cw + 50, 280, "in-sync replicas", 22, BLUE, "start", 800))
    b.append(box(x0, 540, 260, 70, "Consumer", GREEN, size=22))
    b.append(path(f"M{x0 + 262},575 L{hw - 4},575 L{hw - 4},504", GREEN, 3.5, "", True))
    b.append(text(hw + 20, 590, "reads up to 108 only", 22, GREEN, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-group
def group():
    W, H = 1600, 640
    b = [text(40, 40, "6 partitions · 3 consumers", 22, MUTED, "start", 700)]
    for i in range(6):
        y = 60 + i * 52
        b.append(box(160, y, 140, 42, f"P{i}", BLUE, size=21))
        b.append(line(302, y + 21, 896, 92 + (i // 2) * 104, BLUE, 2.5, "", True))
    for k in range(3):
        b.append(box(900, 60 + k * 104, 200, 66, f"C{k + 1}", GREEN, size=22))
    y0 = 430
    b.append(text(40, y0 - 20, "same 6 partitions · 7 consumers", 22, MUTED, "start", 700))
    for i in range(6):
        b.append(box(40 + i * 120, y0, 100, 42, f"P{i}", BLUE, size=21))
        b.append(line(90 + i * 120, y0 + 44, 90 + i * 210, y0 + 116, BLUE, 2, "", True))
    for k in range(7):
        idle = k == 6
        b.append(box(40 + k * 210, y0 + 120, 120, 50, f"C{k + 1}", GREY if idle else GREEN, size=21))
    b.append(text(1340, y0 + 205, "idle: only 6 partitions", 22, MUTED, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-sink-txn
def sink_txn():
    s = Seq(1600, y0=20, row=62, headh=62)
    s.part("l", "Log", GREY); s.part("c", "Consumer"); s.part("d", "Ledger DB", GREEN)
    s.msg("l", "c", "batch offsets 100–109")
    s.msg("c", "d", "BEGIN", colour=RED)
    s.msg("c", "d", "insert 10 payments", colour=RED)
    s.msg("c", "d", "upsert consumer_offsets: p3 = 110", colour=RED)
    s.msg("c", "d", "COMMIT", colour=RED)
    s.note("c", "c", "", "blue", lines=["restart → read offset", "from the ledger"])
    body = s.body()
    xs, _ = s.xs()
    y1 = 20 + 62 + 50 + 62 - 20
    br = vbracket(xs["d"] + 60, y1, y1 + 62 * 3 + 40, RED, True, 16) + text(xs["d"] + 80, y1 + 125, "one transaction", 24, RED, "start", 800)
    return svg(1600, max(720, int(s.y + 20)), [body, br])


# ---------------------------------------------------------------- p10-reorder
def reorder():
    W, H = 1600, 700
    b = [panel(20, 20, 760, 660, "grey"), panel(820, 20, 760, 660, "grey")]
    b.append(title(400, 64, "retry with two in flight", 26, INK, "middle")); b.append(title(1200, 64, "partitions 4 → 8", 26, INK, "middle"))
    s = Seq(760, x0=40, y0=90, row=70, headh=58)
    s.part("p", "Producer", GREY); s.part("b", "Broker")
    s.lost("p", "b", "m1", "fails")
    s.msg("p", "b", "m2 ✓", colour=GREEN)
    s.msg("p", "b", "m1 retried ✓", colour=GREEN)
    b.append(f'<g transform="translate(20,0)">{s.body()}</g>')
    b.append(text(70, 540, "log:", 22, INK, "start", 700))
    b.append(cells(140, 505, ["m2", "m1"], 120, 60, "#fde7e9", RED))
    b.append(text(400, 620, "order lost: m2 before m1", 24, RED, "middle", 800))
    b.append(box(1080, 120, 240, 70, "key acct-7", GREY, size=24))
    b.append(box(870, 380, 300, 110, ["P3", "old messages waiting"], GREY, size=22))
    b.append(box(1250, 380, 300, 110, ["P7", "new messages read first"], RED, size=22, sw=4))
    b.append(line(1140, 192, 1030, 376, GREY, 3, "", True)); b.append(text(1040, 280, "hash mod 4 = 3", 22, MUTED, "end", 700, True))
    b.append(line(1260, 192, 1390, 376, RED, 3.5, "", True)); b.append(text(1350, 280, "hash mod 8 = 7", 22, RED, "start", 800, True))
    b.append(text(1200, 590, "after the resize, newer events can overtake older ones", 21, RED, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-poison
def poison():
    W, H = 1600, 640
    b = [box(30, 250, 280, 110, ["Message m42", "(bad payload)"], RED, size=23)]
    b.append(box(400, 260, 170, 90, "queue", GREY, size=22))
    b.append(arrow(312, 305, 396, 305, colour=INK, w=3))
    for k in range(3):
        x = 660 + k * 230
        b.append(box(x, 80, 180, 80, f"worker {k + 1}" if k else "worker", BLUE, size=22))
        b.append(cross(x + 165, 85, 20, RED, 6))
        b.append(text(x + 90, 192, "crash", 21, RED, "middle", 800))
        b.append(line(570, 290, x + 20, 162, BLUE, 2.5, "", True))
        b.append(path(f"M{x + 120},162 Q{x + 60},330 572,325", RED, 2.5, "8 6", True))
    b.append(text(860, 370, "redeliver · attempt 2, 3, 4 …", 22, RED, "middle", 700, True))
    b.append(arrow(486, 352, 486, 470, colour=GREEN, w=5, lines=["after attempt 5"], weight=800))
    b.append(box(300, 474, 420, 110, ["dead-letter topic", "owner · alert · replay tool"], GREEN, size=23, sw=4))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-lag
def lag():
    W, H = 1600, 600
    b = []
    for k, (rate, behind, col, frac) in enumerate((("at 100,000/s", "20 s behind", GREEN, 0.1),
                                                     ("at 500/s", "66 min behind", RED, 0.95))):
        cx, cy, r = 400 + k * 800, 330, 200
        b.append(f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}" fill="none" stroke="#e6e9ec" stroke-width="40"/>')
        a = math.pi * (1 - frac)
        ex, ey = cx + r * math.cos(a), cy - r * math.sin(a)
        b.append(f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {ex:.1f},{ey:.1f}" fill="none" stroke="{col}" stroke-width="40"/>')
        b.append(line(cx, cy, cx + (r - 50) * math.cos(a), cy - (r - 50) * math.sin(a), INK, 7)); b.append(dot(cx, cy, 14, INK))
        b.append(text(cx, 60, "lag: 2,000,000 messages", 24, INK, "middle", 700))
        b.append(text(cx, 410, rate, 26, INK, "middle", 700))
        b.append(text(cx, 456, f"→ {behind}", 32, col, "middle", 800))
    b.append(text(W / 2, 560, "measure lag in seconds", 30, INK, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-fanout
def fanout():
    W, H = 1600, 760
    b = [panel(20, 20, 760, 720, "grey"), panel(820, 20, 760, 720, "grey")]
    b.append(title(400, 64, "fan-out on write", 26, INK, "middle")); b.append(title(1200, 64, "fan-out on read", 26, INK, "middle"))
    b.append(box(60, 100, 240, 70, "author posts", GREY, size=22))
    b.append(box(60, 250, 240, 70, "fan-out worker", AMBER, size=22))
    b.append(arrow(180, 172, 180, 246, colour=INK, w=3))
    for i in range(8):
        x, y = 380 + (i % 4) * 95, 200 + (i // 4) * 120
        b.append(box(x, y, 80, 60, "inbox", BLUE, size=19 if False else 20, weight=600))
        b.append(line(302, 285, x - 2, y + 30, BLUE, 1.8, "", True))
    b.append(text(560, 168, "× followers", 24, BLUE, "middle", 800))
    b.append(box(380, 560, 200, 70, "reader", GREEN, size=22))
    b.append(line(480, 558, 422, 384, GREEN, 3.5, "", True))
    b.append(text(250, 610, "one read", 22, GREEN, "middle", 700))
    b.append(box(860, 100, 240, 70, "author posts", GREY, size=22))
    b.append(box(860, 250, 240, 70, "outbox", BLUE, size=22))
    b.append(arrow(980, 172, 980, 246, colour=INK, w=3))
    for i in range(8):
        x, y = 1180 + (i % 4) * 95, 200 + (i // 4) * 120
        b.append(box(x, y, 80, 60, "outbox", BLUE, size=19 if False else 20, weight=600))
    b.append(text(1360, 168, "× followed", 24, BLUE, "middle", 800))
    b.append(box(870, 560, 200, 70, "reader", GREEN, size=22))
    b.append(box(1200, 560, 200, 70, "merge", AMBER, size=22))
    for i in range(8):
        x, y = 1180 + (i % 4) * 95, 200 + (i // 4) * 120
        b.append(line(1300, 558, x + 40, y + 62, AMBER, 1.6, "", True))
    b.append(arrow(1072, 595, 1196, 595, colour=GREEN, w=3))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-watermark
def watermark():
    W, H = 1600, 760
    def X(m): return 300 + (m - 8) * 200
    b = []
    for m in (9, 10, 11, 12):
        b.append(rect(X(m) + 4, 80, 192, 80, "#ddeaf8", BLUE, 2.5, 8))
        b.append(text(X(m) + 100, 130, f"12:{m:02d}", 22, INK, "middle", 700))
    b.append(text(40, 128, "windows", 22, MUTED, "start", 700))
    lanes = [("partition 0", 13, BLUE, ""), ("partition 1", 12, BLUE, ""), ("partition 2", 9, AMBER, "idle")]
    for k, (lab, wm, col, note) in enumerate(lanes):
        y = 260 + k * 110
        b.append(text(40, y + 8, lab, 22, INK, "start", 700))
        b.append(line(X(8), y, X(14), y, "#d0d7de", 3))
        b.append(f'<polygon points="{X(wm)},{y - 22} {X(wm) - 14},{y - 44} {X(wm) + 14},{y - 44}" fill="{col}"/>')
        b.append(line(X(wm), y - 22, X(wm), y + 22, col, 4))
        b.append(text(X(wm) + 20, y + 34, f"watermark 12:{wm:02d}" + (f" · {note}" if note else ""), 21, col, "start", 800 if note else 600, True))
    b.append(line(X(9), 60, X(9), 620, RED, 7))
    b.append(mtext(X(9) + 16, 650, ["operator watermark = min = 12:09 → nothing emitted"], 23, RED, "start", 800))
    b.append(dot(X(10.4), 175, 12, AMBER))
    b.append(path(f"M{X(10.4)},40 L{X(10.4)},160", AMBER, 2.5, "4 4", True))
    b.append(text(X(10.4) + 18, 46, "late: update or side output", 21, AMBER, "start", 800, True))
    b.append(line(X(8), 700, X(14), 700, MUTED, 2, arrow=True))
    for m in range(8, 15):
        b.append(line(X(m), 692, X(m), 708, MUTED, 2)); b.append(text(X(m), 735, f"12:{m:02d}", 21, MUTED, "middle"))
    b.append(text(40, 708, "event time", 22, MUTED, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p10-checkpoint
def checkpoint():
    W, H = 1600, 720
    b = [box(40, 80, 220, 80, "source P0", GREY, size=22), box(40, 260, 220, 80, "source P1", GREY, size=22)]
    b.append(box(560, 150, 340, 120, ["operator", "(keyed state)"], BLUE, size=24))
    b.append(box(1200, 170, 240, 80, "sink", GREY, size=22))
    b.append(line(262, 120, 556, 190, INK, 3, "", True)); b.append(line(262, 300, 556, 235, INK, 3, "", True))
    b.append(line(902, 210, 1196, 210, INK, 3, "", True))
    for x, y in ((400, 152), (400, 268), (1040, 210)):
        b.append(rect(x - 6, y - 26, 12, 52, AMBER, "none", 0, 3))
        b.append(text(x + 14, y - 30, "‖ ckpt 42", 21, AMBER, "start", 800, True))
    b.append(cross(880, 165, 22, RED, 6)); b.append(text(910, 140, "crash", 22, RED, "start", 800, True))
    b.append(cyl(420, 480, 620, 140, ["durable storage", "checkpoint 42: state + offsets {P0: 1200, P1: 900}"], GREY, 21))
    b.append(path("M730,476 L730,274", RED, 3.5, "10 7", True))
    b.append(text(745, 400, "restore 42", 22, RED, "start", 800, True))
    b.append(path("M420,550 L150,550 L150,344", RED, 3.5, "10 7", True))
    b.append(text(160, 590, "rewind sources to 1200 / 900", 22, RED, "start", 800, True))
    return svg(W, H, b)


FIGS = {"p10-queue-log": queue_log, "p10-segments": segments, "p10-isr": isr, "p10-group": group,
        "p10-sink-txn": sink_txn, "p10-reorder": reorder, "p10-poison": poison, "p10-lag": lag,
        "p10-fanout": fanout, "p10-watermark": watermark, "p10-checkpoint": checkpoint}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
