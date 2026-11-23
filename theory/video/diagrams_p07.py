#!/usr/bin/env python3
"""Part 7 figures (diagrams/p07.md). Run: python3 diagrams_p07.py [name …] → svg/p7-*.svg"""
import math, sys
from dg import *


def bolt(x, y, s=1.0, col=RED):
    pts = [(6, -52), (-14, -8), (2, -8), (-8, 30), (18, -16), (2, -16), (14, -52)]
    return '<polygon points="' + " ".join(f"{x + px * s:.1f},{y + py * s:.1f}" for px, py in pts) + f'" fill="{col}"/>'


# ---------------------------------------------------------------- p7-write-path
def write_path():
    W, H = 1600, 820
    ys = [40, 230, 420, 610]
    labs = [["Application"], ["write() →", "page cache (kernel memory)"], ["device write cache (volatile)"], ["persistent media"]]
    cols = [GREY, AMBER, AMBER, GREEN]
    b = []
    for y, l, c in zip(ys, labs, cols):
        b.append(box(300, y, 600, 110, l, c, size=24))
    b.append(arrow(600, 152, 600, 226, colour=INK, w=3.5))
    b.append(mtext(620, 186, ["1  write() returns here · **not durable**"], 22, RED, "start", 600, halo=True))
    b.append(arrow(600, 342, 600, 416, colour=INK, w=3.5))
    b.append(text(620, 386, "2  kernel flush · maybe 30 s later", 22, INK, "start", 600, True))
    b.append(arrow(600, 532, 600, 606, colour=GREEN, w=5))
    b.append(text(620, 576, "3  fsync / FUA · durable", 24, GREEN, "start", 800, True))
    b.append(vbracket(1020, 230, 530, RED, True, 18))
    b.append(line(1120, 380, 1030, 380, RED, 3, "", True))
    b.append(bolt(1170, 400, 1.6))
    b.append(text(1220, 360, "power loss", 26, RED, "start", 800))
    b.append(text(1220, 400, "everything here is lost", 24, RED, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-btree
def btree():
    W, H = 1600, 780
    b = []
    root = (570, 40); ints = [220, 570, 920]; leaves = [130, 310, 480, 660, 830, 1010]
    def pg(cx, y, w, col, lab="8 KB page", fill=None, sw=2.5):
        return box(cx - w / 2, y, w, 64, lab, col, fill=fill, size=21, sw=sw)
    for i, x in enumerate(ints):
        b.append(line(root[0], 104, x, 220, RED if i == 1 else GREY, 4 if i == 1 else 2))
    for j, x in enumerate(leaves):
        b.append(line(ints[j // 2], 284, x, 400, RED if j == 3 else GREY, 4 if j == 3 else 2))
    b.append(pg(root[0], 40, 220, RED, "root · 8 KB page"))
    for i, x in enumerate(ints):
        b.append(pg(x, 220, 200, RED if i == 1 else BLUE))
    for j, x in enumerate(leaves):
        b.append(pg(x, 400, 160, AMBER if j == 3 else BLUE, fill="#fff4d6" if j == 3 else None, sw=4 if j == 3 else 2.5))
    b.append(text(700, 172, "① find leaf · load into buffer pool", 22, RED, "start", 700, True))
    b.append(text(660, 500, "③ dirty in memory", 22, AMBER, "middle", 800, True))
    b.append(cyl(560, 640, 200, 110, "disk", GREY))
    b.append(path("M660,512 L660,636", MUTED, 3, "10 7", True))
    b.append(text(680, 590, "④ checkpoint writes it back later", 22, MUTED, "start", 700, True))
    # WAL
    b.append(text(1200, 120, "② WAL", 26, INK, "start", 800))
    for k in range(5):
        y = 150 + k * 72
        new = k == 4
        b.append(rect(1200, y, 360, 62, "#ddeaf8" if not new else "#dff3e4", BLUE if not new else GREEN, 2.5 if not new else 4, 4))
        b.append(text(1380, y + 39, "page 4711: insert k" if new else "earlier record", 21, INK if new else MUTED, "middle", 700 if new else 400))
    b.append(text(1380, 550, "fsync at commit", 24, GREEN, "middle", 800))
    b.append(line(1380, 518, 1380, 528, GREEN, 2))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-skiplist
def skiplist():
    W, H = 1600, 620
    vals = [10, 25, 31, 40, 52, 61, 70, 84, 92]
    lanes = {4: [10, 92], 3: [10, 52, 92], 2: [10, 31, 52, 70, 92], 1: vals}
    LY = {4: 90, 3: 200, 2: 310, 1: 420}
    def X(v): return 300 + vals.index(v) * 140
    b = [rect(60, 60, 130, 420, "#eef1f4", GREY, 2.5, 8), text(125, 520, "head", 22, MUTED, "middle", 700)]
    for L, vs in lanes.items():
        y = LY[L]
        b.append(text(40, y + 38, f"L{L}", 21, MUTED, "end", 700))
        prev = 190
        for v in vs:
            b.append(line(prev, y + 30, X(v) - 48, y + 30, GREY, 2, "", True))
            prev = X(v) + 45
        for v in vs:
            b.append(box(X(v) - 45, y, 90, 60, str(v), BLUE, size=24))
    R = RED
    b.append(line(190, LY[4] + 22, X(10) - 48, LY[4] + 22, R, 5, "", True))
    b.append(line(X(10) + 45, LY[4] + 10, X(92) - 48, LY[4] + 10, R, 3, "6 6", True))
    b.append(text((X(10) + X(92)) / 2, LY[4] - 4, "92 too big", 22, R, "middle", 700, True))
    b.append(line(X(10), LY[4] + 62, X(10), LY[3] - 4, R, 5, "", True))
    b.append(line(X(10) + 45, LY[3] + 22, X(52) - 48, LY[3] + 22, R, 5, "", True))
    b.append(line(X(52), LY[3] + 62, X(52), LY[2] - 4, R, 5, "", True))
    b.append(line(X(52) + 45, LY[2] + 22, X(70) - 48, LY[2] + 22, R, 5, "", True))
    b.append(rect(X(70) - 52, LY[2] - 7, 104, 74, "none", GREEN, 5, 12))
    b.append(text(X(70), LY[2] - 20, "found 70", 24, GREEN, "middle", 800, True))
    b.append(text(W / 2, 590, "about log n steps · heights random at insert", 26, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-random-writes
def random_writes():
    W, H = 1600, 640
    b = [arrow(40, 300, 376, 300, colour=BLUE, w=5, lines=["100,000 random writes/s"], weight=700, size=24)]
    b.append(box(380, 200, 380, 200, ["B-tree,", "10× larger than memory"], BLUE, size=24))
    b.append(line(762, 260, 1126, 230, RED, 4, "", True))
    b.append(text(944, 222, "100,000 random page reads/s", 21, RED, "middle", 700, True))
    b.append(line(762, 350, 1126, 380, RED, 4, "", True))
    b.append(mtext(944, 412, ["random 16 KB page writes", "for ~100 B changes"], 21, RED, "middle", 700, halo=True))
    cx, cy, r = 1330, 330, 170
    b.append(f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}" fill="none" stroke="#e6e9ec" stroke-width="34"/>')
    b.append(f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}" fill="none" stroke="{RED}" stroke-width="34"/>')
    b.append(line(cx, cy, cx + r - 40, cy, INK, 7)); b.append(dot(cx, cy, 14, INK))
    b.append(text(cx, cy - 60, "100%", 40, RED, "middle", 800))
    b.append(text(cx, cy + 60, "disk", 26, INK, "middle", 700))
    b.append(text(cx, 520, "disk saturates first", 30, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-lsm-write
def lsm_write():
    W, H = 1600, 820
    b = [box(40, 170, 200, 90, "Write", GREY, size=26)]
    b.append(box(420, 40, 420, 100, ["① WAL", "(append + fsync)"], BLUE, size=23))
    b.append(box(420, 210, 420, 100, ["② Memtable", "(skip list, RAM)"], GREEN, size=23))
    b.append(line(242, 200, 416, 100, INK, 3, "", True)); b.append(line(242, 230, 416, 260, INK, 3, "", True))
    b.append(arrow(630, 312, 630, 396, colour=INK, w=3.5))
    b.append(text(650, 362, "③ Memtable full (64 MB) → flush", 22, INK, "start", 700, True))
    b.append(text(790, 445, "L0: 4 overlapping SSTables", 22, INK, "start", 700))
    for k in range(4):
        b.append(rect(440 + k * 70, 400 + (k % 2) * 16, 200, 56, "#ddeaf8", BLUE, 2.5, 4))
    widths = [("L1 (10× L0)", 560), ("L2 (10×)", 860), ("L3 …", 1120)]
    for i, (lab, w) in enumerate(widths):
        y = 520 + i * 100
        b.append(bar(420, y, w, 56, "", BLUEGREY))
        for k in range(1, int(w / 140)):
            b.append(line(420 + k * 140, y, 420 + k * 140, y + 56, "#fff", 3))
        b.append(text(400, y + 37, lab, 22, INK, "end", 700))
        b.append(line(380 - 40 + 70, y - 52, 380 - 40 + 70, y - 4, AMBER, 3.5, "", True))
    b.append(text(452, 505, "④ compaction", 22, AMBER, "start", 800, True))
    b.append(text(1000, 557, "immutable files · never modified in place", 22, MUTED, "start", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-lsm-read
def lsm_read():
    W, H = 1600, 860
    rows = [("memtable", 1, None), ("immutable memtable", 1, None), ("L0 (newest first)", 4, "all"),
            ("L1", 5, 1), ("L2", 5, 3), ("L3", 5, 2), ("L4", 5, 0), ("L5", 5, 4)]
    b = [line(90, 50, 90, 770, INK, 3, "", True), text(70, 410, "search order", 21, MUTED, "middle", 700,
         extra=' transform="rotate(-90 70 410)"')]
    hit = 5
    for i, (lab, n, hl) in enumerate(rows):
        y = 40 + i * 90
        after = i > hit
        b.append(text(120, y + 42, lab, 22, GREY if after else INK, "start", 700))
        for k in range(n):
            x = 360 + k * 96
            on = hl == "all" or hl == k or (hl is None)
            c = (RED if i == hit else BLUE) if (on and not after) else GREY
            f = ("#fde7e9" if i == hit else "#ddeaf8") if (on and not after) else "#f3f5f7"
            b.append(rect(x, y + 8, 84 if n > 1 else 400, 50, f, c, 3 if (on and not after) else 1.5, 4))
        if i >= 2 and not after:
            fx = 860
            b.append(f'<polygon points="{fx},{y + 14} {fx + 30},{y + 14} {fx + 19},{y + 34} {fx + 19},{y + 50} {fx + 11},{y + 44} {fx + 11},{y + 34}" fill="{RED if i == hit else GREY}"/>')
            if i == hit:
                b.append(text(fx + 44, y + 42, "Bloom: maybe → sparse index → 1 block", 22, RED, "start", 800))
            else:
                b.append(text(fx + 44, y + 42, "Bloom filter: no → skip" + (" (×4)" if n == 4 else ""), 21, MUTED, "start", 600))
        if after:
            b.append(text(860, y + 42, "not read", 21, GREY, "start", 600))
    y = 40 + hit * 90
    b.append(box(1060, y + 100, 200, 70, "block cache", AMBER, size=22))
    b.append(cyl(1340, y + 90, 180, 96, "disk", RED))
    b.append(line(1160, y + 58, 1160, y + 96, RED, 3, "", True))
    b.append(line(1262, y + 135, 1336, y + 135, RED, 3, "", True))
    b.append(text(1300, y + 210, "the one real read", 22, RED, "middle", 800))
    b.append(text(W / 2, 830, "stop at the first match", 28, INK, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-bloom
def bloom():
    W, H = 1600, 620
    x0, cw, Y = 140, 55, 280
    ones = {3, 11, 19, 5, 22}
    def CX(i): return x0 + i * cw + cw / 2
    b = []
    for i in range(24):
        on = i in ones
        b.append(rect(x0 + i * cw, Y, cw, 62, "#ddeaf8" if on else "#fff", BLUE if on else GREY, 2, 0))
        b.append(text(CX(i), Y + 42, "1" if on else "0", 26, BLUE if on else MUTED, "middle", 800 if on else 400))
        b.append(text(CX(i), Y + 92, str(i), 19 if False else 21, MUTED, "middle"))
    def key(lab, kx, ky, cells, col, up):
        o = [box(kx - 70, ky, 140, 56, f'"{lab}"', col, size=24)]
        sy = ky + 58 if not up else ky - 2
        ty = Y - 4 if not up else Y + 104
        for c in cells:
            o.append(line(kx, sy, CX(c), ty, col, 2.5, "", True))
        return o
    b += key("cat", 420, 60, [3, 11, 19], BLUE, False)
    b += key("dog", 1150, 60, [5, 11, 22], BLUE, False)
    b.append(text(420, 46, "h1, h2, h3 → 3, 11, 19", 21, BLUE, "middle", 600))
    b.append(text(1150, 46, "h1, h2, h3 → 5, 11, 22", 21, BLUE, "middle", 600))
    b += key("emu", 500, 470, [3, 11, 22], AMBER, True)
    b += key("fox", 1150, 470, [3, 8, 19], GREEN, True)
    b.append(rect(x0 + 8 * cw, Y, cw, 62, "none", GREEN, 5, 0))
    b.append(text(500, 560, "3, 11, 22 all 1 → maybe (false positive)", 23, AMBER, "middle", 800))
    b.append(text(1150, 560, "cell 8 is 0 → definitely not", 23, GREEN, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-mvcc
def mvcc():
    W, H = 1600, 640
    def X(t): return 160 + t * 34
    Y = 220
    b = [text(40, Y + 42, "key x", 24, INK, "start", 700)]
    for t, v in ((10, "v1"), (20, "v2"), (30, "v3")):
        b.append(rect(X(t) + 3, Y, X(t + 10) - X(t) - 6, 64, FILL[BLUE if v != "v1" else GREY], BLUE if v != "v1" else GREY, 2.5))
        b.append(text(X(t) + 22, Y + 42, v, 26, INK, "start", 800))
    for t, tgt, lab in ((25, 25, "sees v2"), (35, 35, "sees v3")):
        b.append(line(X(t), 90, X(t), 440, AMBER, 3, "9 6"))
        b.append(text(X(t), 78, f"reader @ {t}", 22, AMBER, "middle", 700))
        b.append(dot(X(t), Y + 32, 10, AMBER))
        b.append(text(X(t) + 14, Y - 14, lab, 22, AMBER, "start", 700, True))
    b.append(bracket(X(10) + 6, X(20) - 6, Y + 86, "", GREY, up=False))
    b.append(mtext((X(10) + X(20)) / 2, Y + 134, ["collectable once no", "snapshot ≤ 20 remains"], 22, RED, "middle", 700))
    AX = 520
    b.append(line(X(0), AX, X(41), AX, MUTED, 2, arrow=True))
    for t in range(0, 41, 10):
        b.append(line(X(t), AX - 8, X(t), AX + 8, MUTED, 2)); b.append(text(X(t), AX + 34, str(t), 21, MUTED, "middle"))
    b.append(text(X(41), AX + 66, "timestamp", 22, MUTED, "end", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-blob-layout
def blob_layout():
    W, H = 1600, 760
    b = [rect(40, 100, 560, 340, "#ddeaf8", BLUE, 2.5)]
    b.append(mtext(320, 150, ["Metadata service", "(consistent, partitioned)"], 24, INK, "middle", 700))
    b.append(rect(70, 250, 500, 150, "#fff", BLUEGREY, 2, 8))
    b.append(mtext(320, 300, ["photos/a.jpg → size, checksum,", "chunks [c1, c2, c3]"], 22, INK, "middle", 600))
    place = {0: ["c1"], 1: ["c2"], 2: ["c3"], 3: ["c3"], 4: ["c1"], 5: ["c2"]}
    for k in range(6):
        x = 900 + (k % 3) * 230; y = 80 + (k // 3) * 220
        b.append(rect(x, y, 200, 170, "#f6f8fa", GREY, 2.5))
        b.append(text(x + 100, y + 34, "chunk server", 21, MUTED, "middle", 700))
        for j, c in enumerate(place[k]):
            b.append(box(x + 55, y + 60, 90, 80, c, AMBER, size=24))
    b.append(box(560, 600, 240, 90, "Client", GREY, size=24))
    b.append(line(802, 620, 1060, 484, BLUE, 3.5, "", True))
    b.append(text(990, 575, "① write chunks", 22, BLUE, "start", 700, True))
    b.append(line(640, 598, 450, 444, RED, 5, "", True))
    b.append(mtext(300, 520, ["② commit row", "(makes object visible)"], 23, RED, "middle", 800, halo=True))
    b.append(box(1250, 600, 240, 90, "Reader", GREY, size=24))
    b.append(line(1370, 598, 1370, 484, GREEN, 3, "9 7", True))
    b.append(mtext(1390, 552, ["lookup, then fetch", "chunks in parallel"], 21, GREEN, "start", 700, halo=True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-rs63
def rs63():
    W, H = 1600, 700
    x0, fw = 125, 150
    labs = [f"d{i}" for i in range(1, 7)] + [f"p{i}" for i in range(1, 4)]
    b = [text(x0, 60, "one stripe", 22, MUTED, "start", 700)]
    for i, l in enumerate(labs):
        x = x0 + i * fw
        c = BLUE if l[0] == "d" else AMBER
        b.append(bar(x + 4, 80, fw - 8, 70, l, c, 26))
        b.append(line(x + fw / 2, 154, x + fw / 2, 356, c, 2.5, "", True))
        b.append(box(x + 8, 360, fw - 16, 110, f"rack {i + 1}", GREY, size=22))
        if i in (1, 4, 7):
            b.append(cross(x + fw / 2, 415, 38, RED, 8))
    b.append(mtext(W / 2, 560, ["any 6 of 9 rebuild the stripe · 1.5× space ·", "repair of one fragment reads 6"], 28, RED, "middle", 800))
    return svg(W, H, b)


# ---------------------------------------------------------------- p7-orphans
def orphans():
    W, H = 1600, 680
    lc, rc, r, cy = 650, 1010, 270, 360
    b = [f'<defs><clipPath id="lcirc"><circle cx="{lc}" cy="{cy}" r="{r}"/></clipPath></defs>']
    b.append(f'<g clip-path="url(#lcirc)"><rect x="0" y="0" width="{W}" height="{cy}" fill="#fde7e9"/>'
             f'<rect x="0" y="{cy}" width="{W}" height="{H}" fill="#fff4d6"/></g>')
    b.append(f'<circle cx="{rc}" cy="{cy}" r="{r}" fill="#f3f5f7"/>')
    b.append(f'<g clip-path="url(#lcirc)"><circle cx="{rc}" cy="{cy}" r="{r}" fill="#ddeaf8"/></g>')
    b.append(f'<line x1="{lc - r}" y1="{cy}" x2="{rc - r}" y2="{cy}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 6"/>')
    b.append(f'<circle cx="{lc}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="3"/>')
    b.append(f'<circle cx="{rc}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="3"/>')
    b.append(text(lc - 80, 70, "chunks on servers", 24, INK, "middle", 700))
    b.append(text(rc + 80, 70, "chunks referenced by metadata", 24, INK, "middle", 700))
    b.append(text((lc + rc) / 2, cy + 10, "live", 30, BLUE, "middle", 800))
    b.append(text(530, 170, "orphans", 26, INK, "middle", 800))
    b.append(mtext(540, 250, ["older than", "3 days → delete"], 22, RED, "middle", 800))
    b.append(mtext(540, 420, ["younger → keep", "(upload may", "be in flight)"], 22, AMBER, "middle", 800))
    b.append(box(20, 200, 330, 64, "client died before commit", GREY, size=21, weight=600))
    b.append(box(20, 460, 330, 64, "object deleted", GREY, size=21, weight=600))
    b.append(line(352, 232, 420, 260, MUTED, 2.5, "", True)); b.append(line(352, 492, 420, 450, MUTED, 2.5, "", True))
    b.append(text(52, 180, "causes", 21, MUTED, "start", 700))
    return svg(W, H, b)


FIGS = {"p7-write-path": write_path, "p7-btree": btree, "p7-skiplist": skiplist, "p7-random-writes": random_writes,
        "p7-lsm-write": lsm_write, "p7-lsm-read": lsm_read, "p7-bloom": bloom, "p7-mvcc": mvcc,
        "p7-blob-layout": blob_layout, "p7-rs63": rs63, "p7-orphans": orphans}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
