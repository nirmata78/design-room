#!/usr/bin/env python3
"""Part 16 figures (diagrams/p16.md). Run: python3 diagrams_p16.py [name …] → svg/p16-*.svg"""
import sys
from dg import *


# ---------------------------------------------------------------- p16-migration
def migration():
    W, H = 1600, 760
    L, R = 70, 1540
    yo, yn = 300, 490            # lane centres: old, new
    b = [title(L, 44, "Online migration · one timeline over weeks")]
    xs = [L + 70 + i * 200 for i in range(7)]          # step markers
    nr = xs[6] + 40                                     # point of no return
    # lanes
    b.append(rect(L, yo - 55, nr - L, 110, "#eaf2fc", "none", 0, 12))
    b.append(text(L + 16, yo - 22, "Old system", 24, INK, "start", 700))
    b.append(rect(nr, yo - 55, R - nr, 110, "#f3f5f7", "none", 0, 12))
    b.append(text(nr + 16, yo + 8, "old path removed", 21, GREY, "start", 600))
    b.append(rect(xs[0] - 40, yn - 55, R - xs[0] + 40, 110, "#e9f6ec", "none", 0, 12))
    b.append(text(xs[0] - 24, yn + 44, "New system", 24, INK, "start", 700))
    # axis
    ya = 660
    b.append(line(L, ya, R, ya, INK, 2, arrow=True))
    b.append(text(R, ya + 34, "weeks", 21, MUTED, "end", 600))
    steps = ["expand", "capture", "backfill", "verify", "switch reads", "switch writes", "contract"]
    for i, (x, s) in enumerate(zip(xs, steps)):
        col = RED if i == 5 else INK
        b.append(f'<circle cx="{x}" cy="{ya}" r="19" fill="#fff" stroke="{col}" stroke-width="3"/>')
        b.append(text(x, ya + 8, str(i + 1), 21, col, "middle", 800))
        b.append(text(x, ya + 52, s, 21, col, "middle", 700))
        b.append(line(x, ya - 22, x, yo + 60, "#d0d7de", 1.5, "4 6"))
    # 1 expand: empty new lane
    b.append(text(xs[0] + 60, yn + 8, "empty", 21, MUTED, "start", 600))
    # 2 capture: continuous arrow old -> new
    b.append(line(xs[1], yo + 30, xs[1], yn - 30, BLUE, 3, arrow=True))
    b.append(line(xs[1] + 8, yo + 30, nr - 10, yo + 30, BLUE, 2, "2 6"))
    b.append(text(xs[1] + 12, (yo + yn) / 2 - 6, "CDC /", 21, BLUE, "start", 700, True))
    b.append(text(xs[1] + 12, (yo + yn) / 2 + 20, "dual write", 21, BLUE, "start", 700, True))
    # 3 backfill: thick arrow
    b.append(line(xs[2], yo + 30, xs[2], yn - 30, BLUE, 6, arrow=True))
    b.append(text(xs[2] + 14, (yo + yn) / 2 - 6, "history,", 21, BLUE, "start", 700, True))
    b.append(text(xs[2] + 14, (yo + yn) / 2 + 20, "throttled", 21, BLUE, "start", 700, True))
    # 4 verify: comparator box
    b.append(box(xs[3] - 85, (yo + yn) / 2 - 40, 170, 80, ["shadow reads", "diffs = 0"], AMBER, size=21))
    # 5 switch reads: client read arrows
    cy = 110
    b.append(box(xs[4] - 95, cy - 32, 190, 56, "clients", GREY, size=21))
    b.append(line(xs[4] - 40, cy + 24, xs[4] - 40, yo - 58, GREY, 2.5, "7 6", True))
    b.append(line(xs[4] + 40, cy + 24, xs[4] + 40, yn - 58, GREEN, 3.5, arrow=True))
    b.append(text(xs[4] + 52, cy + 66, "reads 1% → 100%", 21, GREEN, "start", 700, True))
    # 6 switch writes + reverse replication (highlight)
    b.append(box(xs[5] - 95, cy - 32, 190, 56, "clients", GREY, size=21))
    b.append(line(xs[5] + 40, cy + 24, xs[5] + 40, yn - 58, GREEN, 3.5, arrow=True))
    b.append(text(xs[5] + 52, cy + 66, "writes → new", 21, GREEN, "start", 700, True))
    b.append(line(xs[5] - 30, yn - 30, xs[5] - 30, yo + 30, RED, 4, arrow=True))
    b.append(text(xs[5] - 44, (yo + yn) / 2 - 6, "reverse", 22, RED, "end", 800, True))
    b.append(text(xs[5] - 44, (yo + yn) / 2 + 22, "replication", 22, RED, "end", 800, True))
    # 7 contract: point of no return
    b.append(line(nr, yo - 70, nr, ya - 24, INK, 2.5, "10 7"))
    b.append(text(nr + 10, yn - 70, "point of", 21, INK, "start", 700, True))
    b.append(text(nr + 10, yn - 44, "no return", 21, INK, "start", 700, True))
    # bracket 1..6
    b.append(bracket(xs[0] - 30, xs[5] + 30, 600, "", RED))
    b.append(text((xs[0] + xs[5]) / 2, 588, "rollback = switch back, nothing lost", 22, RED, "middle", 700, True))
    return svg(W, H, b)


FIGS = {"p16-migration": migration}

if __name__ == "__main__":
    save(FIGS, set(sys.argv[1:]) or None)
