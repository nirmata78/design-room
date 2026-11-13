#!/usr/bin/env python3
"""Part 15 figures (diagrams/p15.md). Run: python3 diagrams_p15.py [name …] → svg/p15-*.svg"""
import math, sys
from dg import *


def seqfig(s, h, t=""):
    body = s.body(t)
    return svg(1600, max(h, int(s.y + 30)), [body])


# ---------------------------------------------------------------- p15-planes
def planes():
    W, H = 1600, 760
    b = []
    b.append(panel(40, 40, 1520, 250, "blue", "Control plane · hundreds of changes/s · may be down for minutes", 22))
    b.append(box(110, 120, 260, 110, ["API", "writes desired state"], BLUE))
    b.append(cyl(520, 105, 340, 140, ["Consistent store", "(desired state)"], BLUE))
    b.append(box(1010, 120, 300, 110, ["controllers", "decide, reconcile"], BLUE))
    b.append(arrow(370, 175, 520, 175, "", BLUE))
    b.append(arrow(860, 175, 1010, 175, "", BLUE))
    b.append(panel(40, 400, 1520, 300, "green", "Data plane · millions of requests/s · local state", 22, "bottom"))
    names = [("proxy", 130), ("proxy", 430), ("server", 730), ("server", 1030), ("storage node", 1330)]
    for n, x in names:
        b.append(box(x - 110, 450, 220, 90, [n], GREEN))
        b.append(rect(x - 100, 556, 200, 44, "#fff", GREY, 2, 6))
        b.append(text(x, 585, "last known good", 21, MUTED, "middle", 600))
    for x in (300, 800, 1300):
        b.append(arrow(x, 290, x, 445, "", BLUE, 2.5, "9 7"))
    b.append(text(820, 360, "versioned state, pushed (one-way, asynchronous)", 22, BLUE, "start", 700, True))
    # user requests enter and leave the bottom band only
    b.append(line(60, 640, 1540, 640, RED, 3.5, arrow=True))
    b.append(text(800, 628, "user requests: served entirely in the data plane", 22, RED, "middle", 800, True))
    b.append(text(800, 738, "nothing on the request path calls the control plane", 24, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p15-edge
def edge():
    W, H = 1600, 620
    L, R = 260, 1520
    def X(t): return L + (R - L) * t / 14
    b = [line(L, 560, R + 30, 560, INK, 2, arrow=True), text(R + 30, 530, "time", 21, MUTED, "end", 600)]
    for t in range(0, 15, 2):
        b.append(line(X(t), 560, X(t), 568, INK, 2)); b.append(text(X(t), 594, f"t = {t}", 21, INK, "middle"))
    lanes = {"Replicas": 120, "Events": 300, "Controller": 450}
    for name, y in lanes.items():
        b.append(text(40, y + 8, name, 24, INK, "start", 700))
        b.append(line(L, y, R, y, "#d0d7de", 1.5, "4 6"))
    for i, y in enumerate((90, 125, 160)):
        end = X(5) if i == 2 else X(14)
        b.append(bar(X(0), y - 14, end - X(0), 28, f"replica {i + 1}", BLUE, 20))
    b.append(cross(X(5) + 18, 160, 14))
    b.append(text(X(14), 215, "2 replicas for ever", 22, RED, "end", 800))
    b.append(dot(X(5), 300, 11, AMBER))
    b.append(text(X(5) + 18, 290, "event: \"replica died\"", 22, AMBER, "start", 700, True))
    b.append(hatchbar(X(4), 430, X(8) - X(4), 40, "hatch"))
    b.append(text((X(4) + X(8)) / 2, 420, "restarting", 21, MUTED, "middle", 700))
    b.append(line(X(5), 312, X(5), 428, RED, 3, "8 6", True))
    b.append(cross(X(5), 452, 14))
    b.append(text(X(5) - 20, 395, "event lost", 22, RED, "end", 800, True))
    b.append(bar(X(8), 430, X(14) - X(8), 40, "waiting for events…", GREY, 21))
    return svg(W, H, b)


# ---------------------------------------------------------------- p15-preempt
def preempt():
    W, H = 1600, 700
    b = [title(40, 46, "A full node, and a high-priority task that must run")]
    # node before
    b.append(rect(60, 100, 560, 420, "#f3f5f7", INK, 2.5, 14))
    b.append(text(80, 136, "node 17 · before", 22, INK, "start", 700))
    tasks = [("batch b1", AMBER, 160), ("batch b2", AMBER, 250), ("prod p3", BLUE, 340), ("prod p4", BLUE, 430)]
    for n, c, y in tasks:
        b.append(box(90, y, 500, 74, [n], c))
    b.append(text(340, 548, "full", 22, MUTED, "middle", 700))
    b.append(box(720, 110, 360, 110, ["prod p9", "high priority · team within quota"], RED, size=21))
    b.append(arrow(900, 220, 900, 300, "", RED))
    b.append(box(700, 300, 400, 120, ["b1, b2: SIGTERM", "30 s grace · checkpoint", "then removed"], AMBER, size=21))
    b.append(arrow(1100, 360, 1170, 360, "", INK))
    # node after
    b.append(rect(1180, 100, 380, 420, "#f3f5f7", INK, 2.5, 14))
    b.append(text(1200, 136, "node 17 · after", 22, INK, "start", 700))
    b.append(box(1205, 160, 330, 164, ["prod p9"], RED, sw=4))
    b.append(box(1205, 340, 330, 74, ["prod p3"], BLUE))
    b.append(box(1205, 430, 330, 74, ["prod p4"], BLUE))
    b.append(box(700, 560, 400, 90, ["queue", "b1, b2 requeued → run elsewhere"], GREY, size=21))
    b.append(arrow(800, 420, 800, 556, "", AMBER, 2.5, "9 7"))
    return svg(W, H, b)


# ---------------------------------------------------------------- p15-partition
def partition():
    W, H = 1600, 720
    b = []
    b.append(box(40, 200, 280, 140, ["Control plane", "heartbeats every 10 s"], BLUE))
    zones = [("zone a", 420), ("zone b", 800), ("zone c", 1220)]
    for z, x in zones:
        b.append(rect(x, 80, 340, 400, "#f3f5f7", INK, 2, 14))
        b.append(text(x + 18, 116, z, 24, INK, "start", 700))
        for r in range(10):
            for c in range(20):
                b.append(dot(x + 28 + c * 15, 150 + r * 24, 5, GREEN))
        b.append(text(x + 170, 440, "200 nodes · healthy, serving" if z == "zone c" else "nodes, reachable", 21,
                      GREEN if z == "zone c" else MUTED, "middle", 700))
    b.append(arrow(320, 270, 416, 270, "", BLUE))
    pts = [(1180, 70), (1200, 150), (1165, 230), (1200, 310), (1165, 390), (1195, 470)]
    b.append(poly(pts, RED, 5))
    b.append(text(1180, 520, "partition: control plane ⇸ zone c", 22, RED, "middle", 800))
    b.append(box(420, 570, 1140, 120, ["200 nodes silent at once → stop evicting: it is the network, not 200 failures",
                                        "nodes keep running their tasks"], RED, size=22))
    return svg(W, H, b)


# ---------------------------------------------------------------- p15-timers
def timers():
    W, H = 1600, 780
    b = []
    b.append(text(40, 50, "timer store", 24, INK, "start", 700))
    rows = ["(bucket 00:00, shard 0)", "(bucket 00:00, shard 1)", "…", "(bucket 00:00, shard 15)",
            "(bucket 00:01, shard 0)", "…"]
    for i, r in enumerate(rows):
        hl = i < 4
        b.append(rect(40, 80 + i * 70, 400, 56, FILL[BLUE] if hl else "#fff", BLUE if hl else GREY, 2, 6))
        b.append(text(240, 116 + i * 70, r, 21, INK, "middle", 600))
    b.append(text(40, 540, "keyed by due-time bucket + shard", 21, MUTED, "start", 600))
    # shards
    b.append(text(560, 50, "16 scheduler shards", 24, INK, "start", 700))
    for i in range(16):
        r, c = divmod(i, 4)
        b.append(box(560 + c * 100, 80 + r * 90, 84, 70, [f"s{i}"], GREEN, size=21))
    b.append(arrow(440, 110, 556, 115, "", BLUE))
    b.append(text(752, 460, "range read at 23:59", 22, BLUE, "middle", 700))
    b.append(text(752, 488, "(one small range per shard)", 21, MUTED, "middle"))
    # wheel
    cx, cy, r = 1280, 330, 220
    b.append(text(cx, 60, "one shard's timing wheel", 24, INK, "middle", 700))
    for k in range(60):
        a = -math.pi / 2 + 2 * math.pi * k / 60
        x1, y1 = cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a)
        x2, y2 = cx + r * math.cos(a), cy + r * math.sin(a)
        b.append(line(x1, y1, x2, y2, "#aab3bd", 2))
        if k in (3, 4, 9, 17, 18, 31, 44, 52):
            b.append(dot(cx + (r + 16) * math.cos(a), cy + (r + 16) * math.sin(a), 7, BLUE))
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    a = -math.pi / 2 + 2 * math.pi * 3 / 60
    b.append(line(cx, cy, cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a), RED, 5, arrow=True))
    b.append(text(cx, cy + 40, "60 slots, 1 per second", 21, INK, "middle", 600))
    b.append(text(cx, cy + 68, "pointer advances 1 slot/s", 21, RED, "middle", 700))
    b.append(dot(1150, 585, 7, BLUE)); b.append(text(1166, 592, "a timer in its slot", 21, BLUE, "start", 600))
    b.append(box(1120, 610, 320, 100, ["heap", "next due across slots"], AMBER, size=21))
    b.append(arrow(950, 250, 1048, 300, "", GREEN))
    b.append(text(1000, 248, "load", 21, GREEN, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p15-launch-gap
def launch_gap():
    s = Seq(1600, y0=20, size=22, row=60)
    s.part("l1", "Leader 1"); s.part("w", "Worker"); s.part("st", "Store"); s.part("l2", "Leader 2")
    s.note("l1", "l1", "decide: run billing for the 12th", "blue")
    s.msg("l1", "w", "start billing")
    s.note("w", "w", "billing runs", "grey")
    s.note("l1", "l1", "✕ crash before recording", "red")
    s.msg("l2", "st", "read: no launch recorded")
    s.msg("l2", "w", "start billing", hl=True)
    s.note("w", "l2", "everyone billed twice", "red")
    return seqfig(s, 700)


# ---------------------------------------------------------------- p15-lease
def lease():
    s = Seq(1600, y0=20, size=21, row=56)
    s.part("l", "Leader"); s.part("st", ["Store", "(consensus)"]); s.part("q", "Queue"); s.part("w", "Worker"); s.part("d", "Downstream")
    s.msg("l", "st", "", num=False, lines=["① launch record:", "billing/12 · attempt 1 · starting"])
    s.msg("l", "q", "task", num=False)
    s.msg("w", "q", "② lease task · 60 s", num=False)
    s.msg("w", "q", "heartbeat (renew)", dash=True, num=False)
    s.msg("w", "d", "effect · attempt 1", num=False)
    s.msg("w", "st", "③ result · attempt 1 · done", colour=GREEN, num=False)
    s.note("q", "d", "④ lease expires → attempt 2 queued · downstream refuses attempt 1 (fencing)", "red")
    return seqfig(s, 820)


# ---------------------------------------------------------------- p15-workflow
def workflow():
    W, H = 1600, 760
    b = []
    b.append(text(60, 60, "workflow code", 24, INK, "start", 700))
    code = ["charge()", "sleep(2 days)", "ship()", "email()"]
    for i, c in enumerate(code):
        b.append(rect(60, 90 + i * 90, 420, 70, "#f6f8fa", GREY, 2, 8))
        b.append(text(84, 135 + i * 90, c, 24, INK, "start", 600))
    b.append(text(1080, 60, "event history", 24, INK, "start", 700))
    hist = ["1  charge → ok (ch_81)", "2  timer started (2 days)"]
    for i, h in enumerate(hist):
        b.append(box(1080, 90 + i * 90, 460, 70, [h], BLUE, size=22, weight=500))
    b.append(cross(780, 160, 20))
    b.append(text(780, 216, "worker crash", 22, RED, "middle", 800))
    b.append(box(620, 470, 340, 90, ["worker 2", "replay from start"], GREEN))
    b.append(arrow(620, 500, 486, 140, "", GREEN))
    b.append(text(540, 330, "found in history,", 22, GREEN, "end", 700, True))
    b.append(text(540, 358, "not re-run", 22, GREEN, "end", 700, True))
    b.append(arrow(960, 500, 1076, 230, "", RED, 3.5))
    b.append(text(1040, 420, "resume timer", 24, RED, "start", 800, True))
    b.append(arrow(1076, 145, 486, 145, "", BLUE, 2, "8 6"))
    b.append(text(780, 128, "recorded result returned", 21, BLUE, "middle", 600, True))
    return svg(W, H, b)


FIGS = {"p15-planes": planes, "p15-edge": edge, "p15-preempt": preempt, "p15-partition": partition,
        "p15-timers": timers, "p15-launch-gap": launch_gap, "p15-lease": lease, "p15-workflow": workflow}

if __name__ == "__main__":
    save(FIGS, set(sys.argv[1:]) or None)
