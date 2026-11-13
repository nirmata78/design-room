#!/usr/bin/env python3
"""Part 3 figures (diagrams/p03.md). Run: python3 diagrams_p03.py [name …] → svg/p3-*.svg"""
import sys
from dg import *

TERM = {1: ("#c9d1d9", INK), 2: (BLUE, "#fff"), 3: (AMBER, "#fff"), 4: (GREEN, "#fff")}


# ---------------------------------------------------------------- p3-smr
def smr():
    W, H = 1600, 720
    b = [box(30, 60, 180, 80, "Client", GREY), box(30, 280, 180, 80, "Client", GREY)]
    b.append(box(340, 120, 740, 110, "Consensus module", BLUE, size=24))
    b.append(line(210, 100, 336, 160, BLUE, 3, arrow=True)); b.append(text(232, 92, "command", 21, BLUE, "start", 600, True))
    b.append(line(210, 320, 336, 200, BLUE, 3, arrow=True)); b.append(text(232, 352, "command", 21, BLUE, "start", 600, True))
    cells = ["1 · set x=1", "2 · set y=2", "3 · del x", "4 · set x=7", "5 · …"]
    cx0, cw, cy = 340, 148, 400
    b.append(text(cx0, cy - 72, "Replicated log", 24, INK, "start", 700))
    for i, c in enumerate(cells):
        com = i < 4
        b.append(rect(cx0 + i * cw, cy, cw, 70, "#ddeaf8" if com else "#f6f8fa", BLUE if com else GREY, 2.5, 4,
                      "" if com else "6 5"))
        b.append(text(cx0 + i * cw + cw / 2, cy + 43, c, 21, INK, "middle", 600))
    b.append(bracket(cx0 + 6, cx0 + 4 * cw - 6, cy - 14, "committed", GREEN))
    b.append(line(710, 232, 710, 300, BLUE, 2.5, "6 5", True))
    for k, ry in enumerate((90, 330, 570)):
        b.append(box(1250, ry, 320, 110, [f"Replica {k + 1} · state machine", "x = 7, y = 2"], GREEN))
        b.append(arrow(cx0 + 5 * cw + 6, cy + 35, 1244, ry + 55, colour=GREEN, w=2.5))
    b.append(text(1166, 255, "apply in order", 21, GREEN, "middle", 700, True))
    b.append(text(1166, 568, "apply in order", 21, GREEN, "middle", 700, True))
    b.append(text(1166, 420, "apply in order", 21, GREEN, "middle", 700, True))
    b.append(text(700, 640, "same log + deterministic apply = same state", 26, INK, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p3-election
def election():
    W, H = 1600, 780
    Y = {f"S{i}": 170 + (i - 1) * 120 for i in range(1, 6)}
    b = [panel(110, 40, 400, 660, "grey", "term 1"), panel(960, 40, 610, 660, "green", "term 2")]
    for n, y in Y.items():
        b.append(text(40, y + 8, n, 24, INK, "start", 700))
        b.append(line(120, y, 1560, y, "#d0d7de", 2))
    # term 1: S1 leads
    b.append(bar(120, Y["S1"] - 14, 400, 28, "", BLUE))
    b.append(text(140, Y["S1"] - 26, "leader", 21, BLUE, "start", 700, True))
    for i, n in enumerate(("S2", "S3", "S4", "S5")):
        b.append(line(170 + 40 * i, Y["S1"] + 16, 200 + 40 * i, Y[n] - 6, BLUE, 2, "", True))
    b.append(text(330, Y["S2"] - 50, "heartbeat", 21, BLUE, "start", 600, True))
    X0 = 530
    b.append(cross(X0, Y["S1"], 16))
    b.append(text(X0 + 26, Y["S1"] + 8, "S1 fails", 22, RED, "start", 700, True))
    lens = {"S2": 300, "S3": 150, "S4": 240, "S5": 200}
    for n, L in lens.items():
        b.append(bar(X0, Y[n] - 9, L, 18, "", AMBER if n != "S3" else RED))
    b.append(bracket(X0, X0 + 300, Y["S5"] + 30, "", AMBER, up=False))
    b.append(text(X0, Y["S5"] + 76, "random timeouts, 150–300 ms", 21, AMBER, "start", 700))
    b.append(text(X0 + 140, Y["S3"] - 22, "S3: term → 2, votes for itself", 21, RED, "end", 700, True))
    # campaign
    xs = X0 + 170
    for n in ("S2", "S4", "S5"):
        b.append(line(xs, Y["S3"] + (10 if Y[n] > Y["S3"] else -10), xs + 70, Y[n] + (-10 if Y[n] > Y["S3"] else 10), RED, 2.5, "", True))
    b.append(text(xs + 30, Y["S2"] - 30, "RequestVote (term 2)", 21, RED, "start", 700, True))
    for n in ("S2", "S4"):
        b.append(line(xs + 140, Y[n], xs + 210, Y["S3"] + (-12 if Y[n] < Y["S3"] else 12), GREEN, 2.5, "", True))
    b.append(text(xs + 150, Y["S4"] + 48, "vote granted", 21, GREEN, "start", 700, True))
    # term 2
    b.append(bar(980, Y["S3"] - 14, 580, 28, "", GREEN))
    b.append(text(990, Y["S3"] - 26, "leader · 3 votes of 5", 22, GREEN, "start", 700, True))
    for i, n in enumerate(("S2", "S4", "S5")):
        x = 1130 + 70 * i
        b.append(line(x, Y["S3"] + (-16 if Y[n] < Y["S3"] else 16), x + 30, Y[n] + (8 if Y[n] < Y["S3"] else -8), GREEN, 2, "", True))
    b.append(text(1290, Y["S4"] - 30, "heartbeat", 21, GREEN, "start", 600, True))
    b.append(box(1330, Y["S5"] + 30, 220, 56, "timers reset", AMBER, size=21))
    return svg(W, H, b)


# ---------------------------------------------------------------- p3-append
def append():
    s = Seq(1600, y0=20, row=58, headh=60, boxw=270)
    s.part("c", "Client", GREY); s.part("l", "S3 (leader, term 2)"); s.part("a", "S2"); s.part("b", "S4"); s.part("d", "S5")
    s.msg("c", "l", "set x = 7")
    s.msg("l", "l", "", lines=["append at index 5, term 2", "· fsync"])
    s.fan("l", ["a", "b", "d"], "AppendEntries · prev = (index 4, term 1) · entry 5")
    s.msg("a", "a", "", lines=["has (4, 1)? yes", "· append · fsync"])
    s.msg("a", "l", "ok", colour=GREEN, dash=True)
    s.msg("b", "l", "ok", colour=GREEN, dash=True)
    s.msg("l", "l", "", hl=True, lines=["on 3 of 5 → committed", "· apply"])
    s.msg("l", "c", "ok", colour=GREEN, dash=True)
    s.msg("d", "l", "ok (late)", colour=GREY, dash=True)
    s.fan("l", ["a", "b", "d"], "next message carries commit index 5", colour=GREY)
    body = s.body()
    return svg(1600, max(760, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p3-figure8
def figure8():
    W, H = 1600, 760
    panels = [
        ("(a) term 2 · S1 leads", {1: [1, 2], 2: [1, 2], 3: [1], 4: [1], 5: [1]}, 1, [], INK),
        ("(b) S1 crashes · S5 wins term 3", {1: [1, 2], 2: [1, 2], 3: [1], 4: [1], 5: [1, 3]}, 5,
         ["votes from S3, S4, S5"], MUTED),
        ("(c) S5 crashes · S1 wins term 4", {1: [1, 2, 4], 2: [1, 2], 3: [1, 2], 4: [1], 5: [1, 3]}, 1,
         ["term-2 entry is on 3 of 5 ·", "**NOT committed** · S5 could", "still win and overwrite it"], RED),
        ("(d) safe", {1: [1, 2, 4], 2: [1, 2, 4], 3: [1, 2, 4], 4: [1], 5: [1, 3]}, 1,
         ["a term-4 entry is on a", "majority · S5 can no longer", "win · both entries committed"], GREEN),
    ]
    b = []
    for k, (ttl, logs, leader, cap, ccol) in enumerate(panels):
        px = 20 + k * 395
        b.append(rect(px, 20, 380, 650, "#f6f8fa", "#d0d7de", 2, 14))
        tl = ttl.replace(" · ", " ·\n").split("\n")
        b.append(mtext(px + 190, 58, tl, 22, INK, "middle", 700))
        gx, gy, cw, ch = px + 110, 150, 72, 54
        for c in range(3):
            b.append(text(gx + c * (cw + 8) + cw / 2, gy - 12, str(c + 1), 21, MUTED, "middle", 600))
        for r in range(1, 6):
            y = gy + (r - 1) * (ch + 10)
            b.append(text(px + 40, y + ch / 2 + 8, f"S{r}", 22, INK, "start", 700))
            for c in range(3):
                x = gx + c * (cw + 8)
                if c < len(logs[r]):
                    f, t = TERM[logs[r][c]]
                    b.append(rect(x, y, cw, ch, f, "none", 0, 6))
                    b.append(text(x + cw / 2, y + ch / 2 + 8, str(logs[r][c]), 22, t, "middle", 700))
                else:
                    b.append(rect(x, y, cw, ch, "#fff", "#d0d7de", 1.5, 6, "4 4"))
            if r == leader:
                b.append(rect(px + 26, y - 6, 340, ch + 12, "none", INK, 4, 8))
        b.append(mtext(px + 190, 500, cap, 21, ccol, "middle", 700 if ccol != MUTED else 600))
    lx = 420
    b.append(text(lx - 20, 722, "cell = term of the entry:", 21, MUTED, "end", 600))
    for t in (1, 2, 3, 4):
        f, tc = TERM[t]
        b.append(rect(lx + (t - 1) * 190, 696, 44, 36, f, "none", 0, 6))
        b.append(text(lx + (t - 1) * 190 + 54, 722, f"term {t}", 21, INK, "start", 600))
    b.append(rect(lx + 770, 694, 56, 40, "none", INK, 4, 8))
    b.append(text(lx + 836, 722, "current leader", 21, INK, "start", 600))
    return svg(W, H, b)


# ---------------------------------------------------------------- p3-readindex
def readindex():
    s = Seq(1600, y0=20, row=60, headh=60)
    s.part("c", "Client", GREY); s.part("l", "Leader"); s.part("a", "Follower A"); s.part("b", "Follower B")
    s.msg("c", "l", "read x")
    s.msg("l", "l", "note commit index = 41")
    s.fan("l", ["a", "b"], "heartbeat (term 7)")
    s.msg("a", "l", "ack", hl=True, dash=True)
    s.note("l", "a", "self + A = majority of 3 → still the leader", "red")
    s.msg("l", "l", "wait until applied ≥ 41")
    s.msg("l", "c", "x = 7", colour=GREEN, dash=True)
    s.note("c", "b", "no log entry, no disk write, one round trip", "green")
    body = s.body()
    return svg(1600, max(700, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p3-paxos-duel
def paxos_duel():
    s = Seq(1600, y0=20, row=62, headh=60)
    s.part("p1", "Proposer 1", BLUEGREY); s.part("a", "Acceptor A"); s.part("b", "Acceptor B"); s.part("c", "Acceptor C")
    s.part("p2", "Proposer 2", AMBER)
    acc = ["a", "b", "c"]
    s.fan("p1", acc, "prepare(1)")
    s.gather(acc, "p1", "promise(1), nothing accepted", colour=MUTED, dash=True)
    s.fan("p2", acc, "prepare(2)", colour=AMBER)
    s.gather(acc, "p2", "promise(2), nothing accepted", colour=MUTED, dash=True)
    s.fan("p1", acc, "accept(1, X)")
    s.gather(acc, "p1", "rejected: promised 2", hl=True, dash=True)
    s.fan("p2", acc, "accept(2, Y)", colour=AMBER)
    s.gather(acc, "p2", "accepted", colour=GREEN, dash=True)
    s.note("p1", "p2", "Y is chosen · P1 retries with ballot 3 and must adopt Y", "amber")
    body = s.body()
    return svg(1600, max(780, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p3-placement
def placement():
    W, H = 1600, 720
    b = [rect(60, 50, 600, 260, "#f3f5f7", GREY, 2.5, 16), rect(940, 50, 600, 260, "#f3f5f7", GREY, 2.5, 16),
         rect(500, 430, 600, 250, "#f3f5f7", GREY, 2.5, 16)]
    b.append(text(80, 88, "Region 1", 24, INK, "start", 700))
    b.append(text(960, 88, "Region 2", 24, INK, "start", 700))
    b.append(text(520, 468, "Region 3", 24, INK, "start", 700))
    # region links
    b.append(line(660, 270, 940, 270, GREY, 3)); b.append(text(800, 300, "30 ms", 22, MUTED, "middle", 700, True))
    b.append(line(330, 310, 560, 430, GREY, 3)); b.append(text(410, 400, "80 ms", 22, MUTED, "end", 700, True))
    b.append(line(1240, 310, 1040, 430, GREY, 3)); b.append(text(1170, 400, "70 ms", 22, MUTED, "start", 700, True))
    def voter(x, y, lab="", col=BLUE):
        o = f'<circle cx="{x}" cy="{y}" r="38" fill="{FILL[col]}" stroke="{col}" stroke-width="3"/>'
        o += text(x, y + 8, "voter", 20, INK, "middle", 600)
        if lab:
            o += text(x, y - 50, lab, 22, col, "middle", 800, True)
        return o
    LX, LY = 200, 170
    b.append(arrow(LX + 40, LY + 14, 452, 228, colour=GREEN, w=3.5))
    b.append(text(542, 250, "≈ 1 ms", 22, GREEN, "start", 700, True))
    b.append(arrow(LX + 40, LY, 1072, LY, colour=GREEN, w=5))
    b.append(text(800, LY - 14, "30 ms", 24, GREEN, "middle", 800, True))
    b.append(line(LX + 20, LY + 34, 772, 532, GREY, 2.5, "10 7", True))
    b.append(text(700, 400, "80 ms · not needed for commit", 21, MUTED, "start", 600, True))
    b.append(voter(LX, LY, "leader", BLUE)); b.append(voter(490, 240)); b.append(voter(1110, LY)); b.append(voter(1380, 240))
    b.append(voter(800, 570, "", GREY))
    b.append(rect(1150, 450, 410, 200, "#fff8e6", AMBER, 2.5))
    b.append(mtext(1355, 500, ["majority = 3 of 5 =", "leader + local + nearest", "remote → **commit ≈ 30 ms**"], 22, INK, "middle", 600))
    return svg(W, H, b)


FIGS = {"p3-smr": smr, "p3-election": election, "p3-append": append, "p3-figure8": figure8,
        "p3-readindex": readindex, "p3-paxos-duel": paxos_duel, "p3-placement": placement}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
