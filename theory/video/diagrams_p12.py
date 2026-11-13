#!/usr/bin/env python3
"""Part 12 figures (diagrams/p12.md). Run: python3 diagrams_p12.py [name …] → svg/p12-*.svg"""
import sys
from dg import *


# ---------------------------------------------------------------- p12-boundary
def boundary():
    W, H = 1600, 620
    L, R = 120, 1500
    def X(s): return L + (R - L) * s / 120
    ya = 470
    b = [line(L, ya, R, ya, INK, 2, arrow=True)]
    for s, lab in ((0, "0:00"), (30, "0:30"), (60, "1:00"), (90, "1:30"), (120, "2:00")):
        b.append(line(X(s), ya, X(s), ya + 10, INK, 2)); b.append(text(X(s), ya + 38, lab, 22, INK, "middle"))
    b.append(line(X(60), 90, X(60), ya + 14, INK, 4))
    b.append(text(X(60), ya + 76, "window boundary", 22, INK, "middle", 700))
    # fixed windows as brackets
    b.append(bracket(X(0) + 4, X(60) - 8, 120, "window 1: 100 ✓", GREEN))
    b.append(bracket(X(60) + 8, X(120) - 4, 120, "window 2: 100 ✓", GREEN))
    # bars: 100 requests in 0:59-1:00 and 1:00-1:01
    for s in (59, 60):
        b.append(f'<rect x="{X(s) + (2 if s == 60 else 0):.1f}" y="{ya - 220}" width="{X(1) - X(0) - 2:.1f}" height="220" fill="{RED}"/>')
    b.append(text(X(59) - 14, ya - 190, "100 requests", 22, RED, "end", 800, True))
    b.append(text(X(61) + 14, ya - 190, "100 requests", 22, RED, "start", 800, True))
    b.append(bracket(X(59) - 30, X(61) + 30, ya - 250, "", RED))
    b.append(text(X(60), ya - 268, "200 requests in 2 seconds · limit 100/min", 26, RED, "middle", 800, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p12-local-limit
def local_limit():
    W, H = 1600, 700
    b = [box(40, 270, 300, 120, ["customer", "limit 1,000/s"], BLUE)]
    labels = ["gw 1", "gw 2", "gw 3", "gw 4", "gw 5", "…", "gw 50"]
    for i, g in enumerate(labels):
        y = 60 + i * 80
        if g == "…":
            b.append(text(560, y + 40, "…", 30, MUTED, "middle", 700))
            continue
        b.append(box(470, y, 180, 60, [g], GREY, size=22))
        b.append(arrow(340, 330, 466, y + 30, "", BLUEGREY, 2))
    b.append(box(760, 110, 800, 150, ["each enforces 1,000/s", "→ customer can send 50,000/s"], RED, size=24))
    b.append(box(760, 300, 800, 150, ["each enforces 20/s", "→ traffic landing on 3 gateways throttled at 60/s"], AMBER, size=24))
    b.append(box(760, 520, 800, 110, ["the limit is global", "→ some state must be shared"], BLUE, size=24, sw=4))
    return svg(W, H, b)


# ---------------------------------------------------------------- p12-queue
def queue():
    W, H = 1600, 640
    b = [rect(320, 220, 820, 140, "#f6f8fa", INK, 3, 14), text(320, 205, "bounded queue · capacity 8 · full", 22, INK, "start", 700)]
    reqs = ["r3", "r4", "r5", "r6", "r8", "r9", "r10", "r11"]   # head (left) to tail (right)
    for i, r in enumerate(reqs):
        b.append(box(340 + i * 100, 240, 90, 100, [r, "dl ✓"], BLUE, size=21))
    # r7 at the head: deadline passed, dropped at dequeue
    b.append(box(40, 230, 240, 120, ["r7", "deadline passed"], RED, size=22))
    b.append(cross(255, 245, 16))
    b.append(arrow(336, 290, 284, 290, "", RED, 3))
    b.append(text(160, 400, "dropped at dequeue", 22, RED, "middle", 800))
    b.append(text(160, 428, "(never served)", 22, RED, "middle", 700))
    # server, fed from the tail under overload
    b.append(box(1300, 380, 240, 110, ["server"], GREEN, size=26))
    b.append(path("M1100,360 C1150,430 1200,435 1296,435", GREEN, 3.5, arrow=True))
    b.append(text(1200, 520, "overload: serve newest first (LIFO)", 22, GREEN, "middle", 800))
    # new arrival rejected
    b.append(box(1300, 110, 220, 80, ["r12 arrives"], GREY, size=22))
    b.append(arrow(1296, 150, 1150, 228, "", AMBER, 3))
    b.append(cross(1180, 212, 14, AMBER))
    b.append(text(1410, 230, "queue full → reject fast", 22, AMBER, "middle", 800))
    b.append(text(720, 600, "head (oldest) on the left · tail (newest) on the right", 21, MUTED, "middle", 600))
    return svg(W, H, b)


FIGS = {"p12-boundary": boundary, "p12-local-limit": local_limit, "p12-queue": queue}

if __name__ == "__main__":
    save(FIGS, set(sys.argv[1:]) or None)
