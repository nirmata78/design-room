#!/usr/bin/env python3
"""Part 4 figures (diagrams/p04.md). p2-pause is reused from part 2. Run: python3 diagrams_p04.py [name …]"""
import sys
from dg import *


# ---------------------------------------------------------------- p4-chubby-session
def chubby_session():
    W, H = 1600, 760
    def X(s): return 200 + s * 19
    LM, LC, AX = 200, 420, 690
    b = []
    for y, lab in ((LM, "Master"), (LC, "Client")):
        b.append(text(40, y + 8, lab, 24, INK, "start", 700)); b.append(line(X(0), y, X(72), y, "#d0d7de", 2))
    b.append(line(X(0), AX, X(72), AX, MUTED, 2, arrow=True))
    for s in (0, 12, 24, 36, 48, 60):
        b.append(line(X(s), AX - 8, X(s), AX + 8, MUTED, 2)); b.append(text(X(s), AX + 34, f"{s} s", 21, MUTED, "middle"))
    for a in (0, 12):
        b.append(bar(X(a) + 2, LM - 22, X(12) - X(0) - 4, 44, "lease 12 s", BLUE, 21))
        b.append(line(X(a) + 6, LM + 24, X(a) + 6, LC - 26, BLUE, 2.5, arrow=True))
        b.append(bar(X(a) + 2, LC - 18, X(11) - X(0) - 4, 36, "", "#9ec5f4"))
    b.append(text(X(0) + 16, (LM + LC) / 2 + 8, "KeepAlive reply", 21, BLUE, "start", 600, True))
    b.append(text(X(5.5), LC + 46, "local lease (shorter)", 21, BLUE, "middle", 600, True))
    b.append(cross(X(24), LM, 16)); b.append(text(X(24), LM - 36, "master fails", 22, RED, "middle", 700, True))
    b.append(bar(X(24) + 20, LM - 16, X(40) - X(24) - 20, 32, "no master", GREY, 21))
    b.append(box(X(40) + 6, LM - 30, 420, 60, "new master · extends every session", GREEN, size=21))
    b.append(bar(X(23), LC - 18, X(41) - X(23), 36, "", AMBER))
    b.append(text(X(30), LC + 46, "jeopardy · cache emptied · calls wait", 21, AMBER, "middle", 700, True))
    b.append(path(f"M{X(23)},{LC - 40} L{X(23)},{LC - 60} L{X(68)},{LC - 60} L{X(68)},{LC - 40}", INK, 2.5, "8 6"))
    b.append(text(X(45.5), LC - 72, "grace period 45 s", 22, INK, "middle", 700, True))
    b.append(dot(X(41), LC, 13, GREEN))
    b.append(text(X(41) + 22, LC + 90, "safe · session saved", 22, GREEN, "start", 700, True))
    b.append(line(X(41), LC + 14, X(41) + 18, LC + 72, GREEN, 2))
    b.append(line(X(68), LC - 40, X(68), LC + 120, RED, 2.5, "4 5"))
    b.append(mtext(X(68), LC + 150, ["no master by here →", "session expired · every lock lost"], 22, RED, "end", 700, halo=True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p4-election-epoch
def election_epoch():
    s = Seq(1600, y0=20, row=58, headh=60)
    s.part("a", "Node A"); s.part("b", "Node B"); s.part("s", "Coordination store", GREY); s.part("w", "Worker", GREEN)
    s.msg("a", "s", "create /leader if absent · lease 10 s")
    s.msg("s", "a", "ok · create_revision **812**", dash=True, colour=GREEN)
    s.msg("b", "s", "create /leader if absent")
    s.msg("s", "b", "exists · watch it", dash=True, colour=MUTED)
    s.msg("a", "w", "assign task · epoch 812")
    s.note("a", "a", "paused…", "grey")
    s.msg("s", "b", "key deleted (lease expired)", dash=True, colour=MUTED)
    s.msg("b", "s", "create /leader")
    s.msg("s", "b", "ok · **901**", dash=True, colour=GREEN, num=False)
    s.msg("b", "w", "assign · epoch 901")
    s.msg("a", "w", "assign · epoch 812", hl=True)
    s.note("w", "w", "812 < 901 → refused", "red")
    body = s.body()
    return svg(1600, max(820, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p4-herd
def herd():
    W, H = 1600, 720
    b = [panel(30, 20, 750, 580, "red"), panel(820, 20, 750, 580, "green")]
    b.append(title(405, 66, "Everyone watches the lock", 26, INK, "middle"))
    b.append(title(1195, 66, "Each watches its predecessor", 26, INK, "middle"))
    b.append(box(325, 110, 160, 64, "lock", GREY, size=24))
    for i in range(8):
        x = 90 + i * 90
        b.append(line(x, 368, 405 + (i - 3.5) * 14, 178, RED, 2, arrow=True))
        b.append(dot(x, 392, 22, "#f4b7bd", RED))
    b.append(text(405, 460, "… 1,000 waiters", 22, MUTED, "middle", 600))
    b.append(text(405, 540, "one release → 1,000 wake, 1 wins, 999 retry", 23, RED, "middle", 700))
    keys = [["/q/812", "(holder)"], ["/q/813"], ["/q/814"], ["/q/815"]]
    for i, k in enumerate(keys):
        x = 850 + i * 175
        b.append(box(x, 290, 145, 84, k, BLUE if i else GREEN, size=22))
        if i:
            px = x - 175
            b.append(path(f"M{x + 40},288 C{x + 20},200 {px + 125},200 {px + 105},286", GREEN, 3, "", True))
            b.append(text(x - 15, 210, "watch", 21, GREEN, "middle", 700, True))
    b.append(text(1550, 340, "…", 30, INK, "middle", 700))
    b.append(text(1195, 540, "one release → **one** wake-up", 23, GREEN, "middle", 700))
    b.append(text(W / 2, 670, "over 1,000 releases: about 500,000 wasted attempts vs 0", 26, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p4-redlock-clock
def redlock_clock():
    W, H = 1600, 780
    def X(t): return 230 + t * 108
    ys = [180 + i * 95 for i in range(5)]
    AX = 680
    b = [rect(X(4), 110, X(10) - X(4), 530, "#fdeef0", RED, 3, 8, "10 6")]
    b.append(text((X(4) + X(10)) / 2, 96, "two clients each hold a majority", 24, RED, "middle", 800, True))
    for i, y in enumerate(ys):
        b.append(text(40, y + 8, f"Node {i + 1}", 22, INK, "start", 700)); b.append(line(X(0), y, X(12), y, "#d0d7de", 2))
    for i in (0, 1):
        b.append(bar(X(0), ys[i] - 20, X(10) - X(0), 40, "held by C1 · expiry 10 s", BLUE, 21))
    b.append(bar(X(0), ys[2] - 20, X(3) - X(0), 40, "held by C1", BLUE, 21))
    b.append(text(X(1.5), ys[2] + 46, "expired early", 21, RED, "middle", 700, True))
    lx, ly = X(3), ys[2]
    b.append(f'<polygon points="{lx + 6},{ly - 52} {lx - 14},{ly - 8} {lx + 2},{ly - 8} {lx - 8},{ly + 30} {lx + 18},{ly - 16} {lx + 2},{ly - 16} {lx + 14},{ly - 52}" fill="{RED}"/>')
    b.append(text(lx + 30, ly - 34, "clock jumps forward 8 s", 21, RED, "start", 700, True))
    for i in (2, 3, 4):
        b.append(bar(X(4), ys[i] - 20, X(12) - X(4), 40, "held by C2", AMBER, 21))
    b.append(text(X(0), ys[0] - 36, "Client 1 · t = 0", 21, BLUE, "start", 700, True))
    b.append(text(X(10.2), ys[4] + 50, "Client 2 · t = 4", 21, AMBER, "start", 700, True))
    b.append(line(X(0), AX, X(12.3), AX, MUTED, 2, arrow=True))
    for t in range(0, 13, 2):
        b.append(line(X(t), AX - 8, X(t), AX + 8, MUTED, 2)); b.append(text(X(t), AX + 32, f"{t} s", 21, MUTED, "middle"))
    b.append(text(W / 2, 750, "the same overlap happens without a jump if C1 pauses past its expiry · no token to reject the late one",
                  21, INK, "middle", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p4-stale-discovery
def stale_discovery():
    s = Seq(1600, y0=20, row=62, headh=70, boxw=380)
    s.part("c", "Client", GREY); s.part("r", "Registry"); s.part("v", ["10.0.0.7", "old: shard 7 → new: shard 12"], AMBER)
    s.msg("c", "r", "who owns shard 7?")
    s.msg("r", "c", "10.0.0.7", dash=True, colour=GREEN)
    s.note("c", "c", "cached", "blue")
    s.note("v", "v", "", "amber", lines=["server dies · address", "reused for shard 12"])
    s.note("r", "r", "updated in ~10 s", "grey")
    s.msg("c", "v", "write to shard 7", hl=True)
    s.note("v", "v", "accepted by the wrong server", "red")
    body = s.body()
    return svg(1600, max(720, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p4-registry
def registry():
    W, H = 1600, 760
    b = []
    sy = {"a": 90, "b": 330, "c": 570}
    b.append(rect(700, 150, 430, 420, "#ddeaf8", BLUE, 2.5))
    b.append(text(915, 200, "Coordination store", 26, INK, "middle", 700))
    b.append(rect(740, 240, 350, 250, "#fff", BLUEGREY, 2, 8))
    b.append(mtext(915, 290, ["/members/a", "/members/b", "/members/c", "revision 950"], 22, INK, "middle", 600, 1.5))
    for n, y in sy.items():
        b.append(box(320, y, 200, 90, f"server {n}", BLUE if n != "b" else GREEN))
        b.append(line(522, y + 30, 696, 230 + (y - 90) * 0.55, BLUE, 2.5, arrow=True))
    b.append(text(534, 96, "register under lease · renew", 21, BLUE, "start", 600, True))
    for y in (150, 440):
        b.append(box(1350, y, 210, 90, "client", GREY))
        b.append(line(1132, 300 + (y - 150) * 0.45, 1346, y + 45, BLUE, 2.5, arrow=True))
    b.append(text(1240, 352, "read at 950 ·", 21, BLUE, "middle", 600, True))
    b.append(text(1240, 380, "watch from 951", 21, BLUE, "middle", 600, True))
    b.append(path(f"M1455,532 L1455,690 L580,690 L580,400 L526,400", GREEN, 3.5, "", True))
    b.append(text(1020, 676, "request · shard 7 · epoch 901", 22, GREEN, "middle", 700, True))
    b.append(box(20, 450, 280, 140, ["is shard 7 mine", "at epoch 901?", "else refuse"], RED, size=21, sw=3.5))
    b.append(line(160, 450, 330, 422, RED, 2.5, "4 4"))
    return svg(W, H, b)


# ---------------------------------------------------------------- p4-config-push
def config_push():
    W, H = 1600, 640
    b = [box(30, 150, 180, 90, "Engineer", GREY), box(280, 140, 270, 110, ["Config source", "(reviewed)"]),
         box(620, 140, 270, 110, ["Config service", "· v42"])]
    b.append(arrow(212, 195, 276, 195, colour=INK, w=2.5)); b.append(arrow(552, 195, 616, 195, colour=INK, w=2.5))
    for r in range(3):
        for c in range(4):
            b.append(rect(1130 + c * 108, 50 + r * 102, 92, 80, "#fde7e9", RED, 2.5, 8))
            b.append(text(1176 + c * 108, 98 + r * 102, "srv", 20, RED, "middle", 600))
    b.append(arrow(892, 195, 1118, 195, colour=RED, w=5, lines=["push · seconds"], weight=800, size=22))
    b.append(text(40, 420, "for comparison", 21, MUTED, "start", 600))
    b.append(bar(40, 445, 1500, 54, "binary deploy: staged over hours", GREEN, 22))
    b.append(bar(40, 530, 190, 54, "", RED))
    b.append(text(250, 566, "config change: everywhere in a minute", 22, RED, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p4-config-flow
def config_flow():
    W, H = 1600, 820
    b = []
    stages = ["canary", "one zone", "all"]
    b.append(text(40, 60, "⑤", 30, INK, "start", 700))
    for i, s in enumerate(stages):
        x = 90 + i * 300
        b.append(box(x, 28, 240, 56, s, AMBER, size=22))
        if i < 2:
            b.append(arrow(x + 242, 56, x + 296, 56, colour=AMBER, w=3))
    b.append(text(1010, 64, "health check between each", 22, AMBER, "start", 700))
    b.append(box(40, 300, 380, 230, ["Config service", "snapshot v40", "deltas 40→41→42"], BLUE, size=24))
    b.append(arrow(110, 170, 160, 296, colour=INK, w=3))
    b.append(text(60, 160, "① new version", 22, INK, "start", 700))
    b.append(rect(1000, 180, 560, 400, "#f6f8fa", INK, 2.5))
    b.append(text(1280, 222, "Server", 26, INK, "middle", 700))
    b.append(box(1040, 260, 480, 80, "④ verify checksum", GREEN, size=22))
    b.append(box(1040, 380, 480, 120, ["⑥ fails? keep last known good", "(on disk)"], RED, size=22, sw=3.5))
    b.append(arrow(422, 340, 996, 340, colour=BLUE, w=3, lines=["② stream: delta 41→42"], weight=600, size=22))
    b.append(line(996, 450, 424, 450, MUTED, 3, "10 7", True))
    b.append(text(710, 436, "③ poll every few min: I have v41", 22, MUTED, "middle", 600, True))
    b.append(text(710, 484, "backstop", 21, AMBER, "middle", 700, True))
    b.append(line(996, 640, 300, 640, GREY, 2.5, "", False))
    b.append(line(300, 640, 300, 534, GREY, 2.5, "", True))
    b.append(text(650, 626, "report: applied v42 · hash 9c1e…", 22, MUTED, "middle", 600, True))
    return svg(W, H, b)


FIGS = {"p4-chubby-session": chubby_session, "p4-election-epoch": election_epoch, "p4-herd": herd,
        "p4-redlock-clock": redlock_clock, "p4-stale-discovery": stale_discovery, "p4-registry": registry,
        "p4-config-push": config_push, "p4-config-flow": config_flow}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
