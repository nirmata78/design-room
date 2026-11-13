#!/usr/bin/env python3
"""Part 2 figures (diagrams/p02.md). Run: python3 diagrams_p02.py [name …] → svg/p2-*.svg"""
import sys
from dg import *


# ---------------------------------------------------------------- p2-partition
def partition():
    W, H = 1600, 720
    b = [panel(40, 190, 720, 380, "blue", "majority side", at="bottom"),
         panel(840, 190, 720, 380, "amber", "minority side · healthy, but cut off", at="bottom")]
    b.append(line(800, 120, 800, 700, RED, 4, "16 10"))
    b.append(text(800, 105, "network partition", 22, RED, "middle", 700, True))
    b.append(box(80, 300, 280, 100, "Replica 1 · x = 2"))
    b.append(box(440, 300, 280, 100, "Replica 2 · x = 2"))
    b.append(box(1060, 300, 280, 100, "Replica 3 · x = 1", AMBER))
    b.append(line(360, 350, 440, 350, BLUEGREY, 3, "6 6"))
    b.append(box(110, 30, 220, 70, "Client A", GREY))
    b.append(box(1090, 30, 220, 70, "Client B", GREY))
    b.append(arrow(220, 100, 220, 298, colour=BLUE, w=3, lines=["write x = 2 ✓"], weight=600))
    b.append(arrow(1200, 100, 1200, 298, colour=RED, w=4, lines=["read x ?"], weight=700))
    b.append(box(850, 590, 340, 110, ["answer **1** →", "available, not consistent"], GREEN, "#fff", 22, 400, sw=3))
    b.append(box(1210, 590, 340, 110, ["refuse →", "consistent, not available"], RED, "#fff", 22, 400, sw=3))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-session-anomalies
def session_anomalies():
    W, H = 1600, 860
    top = Seq(W, y0=10, row=50, headh=56)
    top.part("u", "User", GREY); top.part("l", "Leader"); top.part("r", "Replica (behind)", AMBER)
    top.msg("u", "l", "post comment")
    top.msg("l", "u", "ok", colour=GREEN, dash=True)
    top.msg("l", "r", "replicate… not arrived yet", dash=True, colour=MUTED)
    top.msg("u", "r", "reload")
    top.msg("r", "u", "no comment", hl=True, dash=True)
    b = [top.body("No read-your-writes")]
    mid = top.y + 22
    b.append(line(40, mid, W - 40, mid, "#d0d7de", 2))
    bot = Seq(W, y0=mid + 12, row=50, headh=56)
    bot.part("u", "User", GREY); bot.part("a", "Replica A (current)"); bot.part("b", "Replica B (behind)", AMBER)
    bot.msg("u", "a", "refresh"); bot.msg("a", "u", "3 replies", colour=GREEN, dash=True)
    bot.msg("u", "b", "refresh"); bot.msg("b", "u", "2 replies", hl=True, dash=True)
    b.append(bot.body("No monotonic reads"))
    return svg(W, max(H, int(bot.y + 20)), b)


# ---------------------------------------------------------------- p2-lin-vs-ser
def lin_vs_ser():
    W, H = 1600, 780
    def X(t): return 260 + t * 130
    b = [title(40, 50, "Linearizable · single operations, real-time order")]
    for t in range(0, 7):
        b.append(text(X(t), 330, f"t = {t}", 21, MUTED, "middle"))
        b.append(line(X(t), 300, X(t), 308, MUTED, 2))
    b.append(line(X(0), 300, X(6.3), 300, MUTED, 2, arrow=True))
    b.append(text(40, 135, "Client A", 22, INK, "start", 600)); b.append(line(X(0), 128, X(6.3), 128, "#d0d7de", 2))
    b.append(text(40, 235, "Client B", 22, INK, "start", 600)); b.append(line(X(0), 228, X(6.3), 228, "#d0d7de", 2))
    b.append(bar(X(1), 104, X(3) - X(1), 48, "write x = 2", BLUE, 22))
    b.append(bar(X(4), 204, X(5) - X(4), 48, "read x", BLUE, 22))
    b.append(text(X(5) + 18, 236, "must return 2", 22, GREEN, "start", 700))
    b.append(line(X(3), 80, X(3), 290, MUTED, 2.5, "3 6"))
    b.append(text(X(3) + 10, 88, "write completed", 21, MUTED, "start", 600, True))
    b.append(line(40, 375, W - 40, 375, "#d0d7de", 2))
    o = 400
    b.append(title(40, o + 50, "Serializable · whole transactions, some serial order"))
    b.append(text(40, o + 135, "T1", 22, INK, "start", 600)); b.append(line(X(0), o + 128, X(6.3), o + 128, "#d0d7de", 2))
    b.append(text(40, o + 235, "T2", 22, INK, "start", 600)); b.append(line(X(0), o + 228, X(6.3), o + 228, "#d0d7de", 2))
    b.append(bar(X(1), o + 104, X(4) - X(1), 48, "read A, write B", BLUE, 22))
    b.append(bar(X(2), o + 204, X(5) - X(2), 48, "read B, write A", BLUEGREY, 22))
    for t in range(0, 7):
        b.append(text(X(t), o + 330, f"t = {t}", 21, MUTED, "middle"))
        b.append(line(X(t), o + 300, X(t), o + 308, MUTED, 2))
    b.append(line(X(0), o + 300, X(6.3), o + 300, MUTED, 2, arrow=True))
    b.append(rect(1140, o + 90, 420, 180, "#fff8e6", AMBER, 2.5))
    b.append(mtext(1350, o + 135, ["result must equal", "**T1 then T2** or **T2 then T1**", "either is allowed ·",
                                   "real time is not consulted"], 22, INK, "middle", 400, 1.3))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-stale-quorum
def stale_quorum():
    W, H = 1600, 760
    def X(t): return 200 + t * 125
    b = [title(40, 46, "N = 3, W = 2, R = 2")]
    ly = {"R1": 230, "R2": 340, "R3": 450}
    b.append(text(40, 128, "Writer", 22, MUTED, "start", 600))
    b.append(dot(X(1), 120, 10, INK)); b.append(text(X(1), 98, "write x = 2", 22, INK, "middle", 600))
    for name, y in ly.items():
        b.append(text(40, y + 8, name, 24, INK, "start", 700))
        arrive = 2 if name == "R1" else 8
        b.append(line(X(0), y, X(arrive), y, GREY, 10))
        b.append(line(X(arrive), y, X(10), y, BLUE, 10))
        b.append(text(X(0) + 8, y - 16, "x = 1", 21, MUTED, "start", 600))
        b.append(text(X(arrive) + 8, y + 34, "x = 2", 21, BLUE, "start", 700))
    b.append(arrow(X(1), 130, X(2), ly["R1"] - 10, colour=BLUE, w=3))
    b.append(line(X(1), 130, X(8), ly["R2"] - 10, MUTED, 2.5, "9 7", True))
    b.append(line(X(1), 130, X(8), ly["R3"] - 10, MUTED, 2.5, "9 7", True))
    b.append(text(X(6.3), 318, "still in flight", 21, MUTED, "middle", 600, True))
    # readers
    b.append(vbracket(X(3), ly["R1"] - 22, ly["R2"] + 22, INK, True, 16))
    b.append(vbracket(X(5), ly["R2"] - 22, ly["R3"] + 22, RED, True, 16))
    b.append(line(X(3), ly["R2"] + 22, X(3), 575, MUTED, 2, "3 5"))
    b.append(line(X(5), ly["R3"] + 22, X(5), 575, RED, 2, "3 5"))
    for t in range(0, 11):
        b.append(line(X(t), 510, X(t), 518, MUTED, 2)); b.append(text(X(t), 542, f"{t}", 21, MUTED, "middle"))
    b.append(line(X(0), 510, X(10.3), 510, MUTED, 2, arrow=True)); b.append(text(X(10.3) + 10, 518, "t", 21, MUTED))
    b.append(box(60, 578, 640, 80, ["Reader A · t = 3: sees 2 and 1 → returns **2**"], BLUE, "#fff", 22, 400))
    b.append(box(730, 578, 790, 80, ["Reader B · t = 5: sees 1 and 1 → returns **1**"], RED, "#fff", 22, 400, sw=3.5))
    b.append(text(W / 2, 715, "B read after A and saw an older value.", 24, RED, "middle", 700))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-lww-skew
def lww_skew():
    W, H = 1600, 720
    def X(ms): return 400 + ms * 5.6
    b = [text(40, 108, "true time", 22, MUTED, "start", 600)]
    b.append(line(X(0) - 20, 100, X(108), 100, MUTED, 2, arrow=True))
    for ms in (0, 50, 100):
        b.append(line(X(ms), 92, X(ms), 108, MUTED, 2)); b.append(text(X(ms), 76, f"{ms} ms", 22, MUTED, "middle"))
        b.append(line(X(ms), 110, X(ms), 560, "#d0d7de", 1.5, "4 6"))
    for y, lab in ((260, "Node A · clock 100 ms fast"), (450, "Node B · clock correct")):
        b.append(text(40, y + 8, lab, 22, INK, "start", 700))
        b.append(line(X(0) - 20, y, X(105), y, "#c7ced6", 3))
    b.append(dot(X(0), 260, 13, BLUE)); b.append(text(X(0) - 10, 318, "write x = 1 · stamped **100**", 22, INK, "start", 400, True))
    b.append(dot(X(50), 450, 13, RED)); b.append(text(X(50) - 10, 508, "write x = 2 · stamped **50**", 22, INK, "start", 400, True))
    b.append(text(X(50) - 10, 540, "(this write happened later)", 21, MUTED, "start", 400, True))
    b.append(rect(1060, 250, 500, 240, "#fff8e6", AMBER, 2.5))
    b.append(mtext(1310, 310, ["last writer wins:", "100 > 50 → keep **x = 1**"], 24, INK, "middle", 600))
    b.append(mtext(1310, 410, ["the later write is discarded", "· no error"], 22, RED, "middle", 700))
    b.append(arrow(X(0) + 20, 262, 1052, 330, colour=GREY, w=2, dash="6 6"))
    b.append(arrow(X(50) + 20, 448, 1052, 420, colour=GREY, w=2, dash="6 6"))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-version-vector
def version_vector():
    W, H = 1600, 720
    b = [box(480, 30, 640, 90, ["key k · value v0 · vector (1, 0)"], GREY, size=24)]
    b.append(text(800, 155, "entries: (replica A, replica B)", 21, MUTED, "middle", 400, True))
    b.append(box(80, 270, 600, 120, ["Replica A", "client 1 writes v1 · vector **(2, 0)**"]))
    b.append(box(920, 270, 600, 120, ["Replica B", "client 2 writes v2 · vector **(1, 1)**"]))
    b.append(arrow(640, 122, 420, 266, colour=BLUE, w=3))
    b.append(arrow(960, 122, 1180, 266, colour=BLUE, w=3))
    b.append(arrow(380, 392, 620, 516, colour=MUTED, w=3))
    b.append(arrow(1220, 392, 980, 516, colour=MUTED, w=3))
    b.append(box(260, 520, 1080, 150, ["(2, 0) vs (1, 1): each ahead in one position →",
                                       "**concurrent** · keep both · merged vector (2, 1)"], RED, size=24, weight=400, sw=3.5))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-commit-wait
def commit_wait():
    W, H = 1600, 700
    S = 700
    b = [text(500, 70, "clock answers: [earliest, latest] · true time is somewhere inside", 22, BLUE, "middle", 600)]
    b.append(rect(300, 95, 400, 60, "#ddeaf8", BLUE, 2.5, 6))
    b.append(text(300, 182, "earliest", 21, MUTED, "middle")); b.append(text(700, 182, "latest", 21, MUTED, "middle"))
    b.append(dot(500, 125, 8, BLUE))
    b.append(hatchbar(S, 225, 250, 64, "hatchamber", AMBER))
    b.append(text(S + 125, 265, "commit wait", 22, INK, "middle", 700, True))
    b.append(text(S + 125, 318, "locks held", 21, AMBER, "middle", 700, True))
    b.append(rect(S + 50, 350, 400, 60, "#ddeaf8", BLUE, 2.5, 6))
    b.append(dot(S + 250, 380, 8, BLUE))
    b.append(text(S + 470, 388, "a later reading", 21, BLUE, "start", 600))
    b.append(line(S + 50, 340, S + 50, 420, RED, 6))
    b.append(line(S, 80, S, 560, RED, 3, "10 6"))
    b.append(mtext(S + 60, 450, ["earliest > s →", "**report commit**"], 22, RED, "start", 700, halo=True))
    b.append(line(S + 250, 412, S + 250, 560, MUTED, 2, "3 5"))
    b.append(bar(S + 300, 510, 1540 - (S + 300), 50, "", GREEN))
    b.append(mtext(S + 300 + (1540 - S - 300) / 2, 543, ["any later transaction gets a timestamp > s"], 21, "#fff", "middle", 600))
    b.append(line(80, 600, 1520, 600, INK, 2.5, arrow=True))
    b.append(text(1520, 640, "true time", 22, MUTED, "end", 600))
    b.append(text(S, 640, "commit timestamp s = latest", 22, RED, "middle", 700, True))
    return svg(W, H, b)


# ---------------------------------------------------------------- p2-lost-reply
def lost_reply():
    s = Seq(1600, y0=20, row=54, headh=58)
    s.part("c", "Client", GREY); s.part("s", "Payment service"); s.part("n", "Card network", GREY)
    s.msg("c", "s", "POST /pay 20"); s.msg("s", "n", "charge 20"); s.msg("n", "s", "ok", colour=GREEN, dash=True)
    s.lost("s", "c", "200 OK", "reply lost")
    s.note("c", "c", "", lines=["timeout · lost request", "or lost reply?"])
    s.msg("c", "s", "POST /pay 20 (retry)"); s.msg("s", "n", "charge 20", hl=True)
    s.note("c", "n", "charged twice", "red")
    body = s.body()
    return svg(1600, max(700, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p2-dedup
def dedup():
    s = Seq(1600, y0=20, row=56, headh=58)
    s.part("c", "Client", GREY); s.part("s", "Service"); s.part("d", "Database")
    s.msg("c", "s", "POST /pay · Idempotency-Key: k1")
    s.msg("s", "d", "", lines=["BEGIN · insert key k1 · apply charge", "store response · COMMIT"])
    s.note("s", "d", "one transaction", "blue")
    s.lost("s", "c", "200 OK", "lost")
    s.msg("c", "s", "", lines=["POST /pay · Idempotency-Key:", "k1 (retry)"])
    s.msg("s", "d", "insert key k1 → already exists", hl=True)
    s.msg("d", "s", "stored response", dash=True, colour=MUTED)
    s.msg("s", "c", "200 OK · the original response", colour=GREEN, dash=True)
    body = s.body()
    return svg(1600, max(760, int(s.y + 20)), [body])


# ---------------------------------------------------------------- p2-pause / p2-fencing
def lease_timeline(fenced):
    W, H = 1600, 760
    def X(s): return 260 + s * 64
    LA, LL, LB, LS, AX = 150, 300, 430, 580, 680
    b = []
    for y, lab in ((LA, "Client A"), (LL, "Lock service"), (LB, "Client B"), (LS, "Storage")):
        b.append(text(40, y + 8, lab, 22, INK, "start", 700))
        b.append(line(X(0), y, X(20), y, "#d0d7de", 2))
    b.append(line(X(0), AX, X(20), AX, MUTED, 2, arrow=True))
    for s in (0, 10, 15):
        b.append(line(X(s), AX - 8, X(s), AX + 8, MUTED, 2)); b.append(text(X(s), AX + 36, f"{s} s", 22, MUTED, "middle"))
    # Client A
    b.append(bar(X(0), LA - 20, X(10) - X(0), 40, "", BLUE))
    b.append(text(X(0), LA - 32, "holds lease", 21, BLUE, "start", 700))
    b.append(f'<g opacity="0.85">{hatchbar(X(2), LA - 28, X(15) - X(2), 56)}</g>')
    b.append(text((X(2) + X(15)) / 2, LA - 40, "paused · GC or VM migration", 21, MUTED, "middle", 700, True))
    b.append(dot(X(15), LA, 12, RED))
    b.append(mtext(X(15) - 18, LA + 62, ["wakes · still believes it holds the lock · **writes**"], 21, RED, "end", 600, halo=True))
    # Lock service
    b.append(dot(X(0), LL, 11, BLUE)); b.append(dot(X(10), LL, 11, BLUE))
    b.append(text(X(0), LL + 40, "grant to A · token **33**" if fenced else "grant to A · lease 10 s", 21, INK, "start", 400, True))
    b.append(mtext(X(10) + 14, LL + 40, ["lease expired ·", "grant to B · token **34**" if fenced else "grant to B"], 21, INK, "start", 400, halo=True))
    # Client B
    b.append(bar(X(10), LB - 20, X(20) - X(10), 40, "holds lease · writing", BLUE, 21))
    # writes
    b.append(line(X(11), LB + 22, X(11), LS - 26, GREEN if fenced else BLUE, 3.5, arrow=True))
    b.append(line(X(15), LA + 14, X(15), LS - 26, RED, 4.5, arrow=not fenced))
    if fenced:
        b.append(cross(X(15), LS - 32, 15))
        b.append(mtext(X(11) - 14, LB + 66, ["write, token 34", "→ accepted"], 21, GREEN, "end", 700, halo=True))
        b.append(mtext(X(15) + 22, LB + 66, ["write, token 33 →", "**rejected**: 33 < 34"], 21, RED, "start", 600, halo=True))
        b.append(box(X(0.5), LS - 26, 330, 52, ["highest token seen · 33"], GREY, size=21, weight=600))
        b.append(box(X(15) + 28, LS - 26, 300, 52, ["highest token seen · 34"], GREEN, size=21, weight=600))
        b.append(arrow(X(0.5) + 336, LS, X(11) - 8, LS, colour=GREY, w=2))
    else:
        b.append(text(X(11) - 14, LB + 80, "write", 21, BLUE, "end", 700, True))
        b.append(text(X(15) + 16, LB + 80, "write", 21, RED, "start", 700, True))
        b.append(dot(X(11), LS, 10, BLUE)); b.append(dot(X(15), LS, 12, RED))
        b.append(text(X(15) + 24, LS + 44, "two writers", 24, RED, "start", 800, True))
    return svg(W, H, b)


def pause(): return lease_timeline(False)
def fencing(): return lease_timeline(True)


# ---------------------------------------------------------------- p2-gossip
def gossip():
    W, H = 1600, 620
    rounds = [[], [((0, 0), (1, 2))], [((0, 0), (2, 0)), ((1, 2), (0, 3))],
              [((0, 0), (0, 1)), ((1, 2), (2, 3)), ((2, 0), (3, 1)), ((0, 3), (1, 3))]]
    informed = {(0, 0)}
    b = []
    for r in range(4):
        px = 30 + r * 390
        b.append(rect(px, 30, 370, 470, "#f6f8fa", "#d0d7de", 2, 14))
        b.append(text(px + 185, 75, f"round {r}", 26, INK, "middle", 700))
        new = {d for _, d in rounds[r]}
        def P(rc): return px + 70 + rc[1] * 77, 140 + rc[0] * 92
        for s, d in rounds[r]:
            (x1, y1), (x2, y2) = P(s), P(d)
            L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            ux, uy = (x2 - x1) / L, (y2 - y1) / L
            b.append(line(x1 + ux * 22, y1 + uy * 22, x2 - ux * 24, y2 - uy * 24, BLUE, 2.5, arrow=True))
        informed |= new
        for i in range(4):
            for j in range(4):
                x, y = P((i, j))
                on = (i, j) in informed
                b.append(dot(x, y, 18, BLUE if on else "#d8dee4"))
        b.append(text(px + 185, 480, f"{len(informed)} informed", 22, BLUE, "middle", 600))
    b.append(text(W / 2, 568, "1 → 2 → 4 → 8 … · 1,000 nodes in about 10 rounds, stragglers a few more", 24, INK, "middle", 600))
    return svg(W, H, b)


FIGS = {"p2-partition": partition, "p2-session-anomalies": session_anomalies, "p2-lin-vs-ser": lin_vs_ser,
        "p2-stale-quorum": stale_quorum, "p2-lww-skew": lww_skew, "p2-version-vector": version_vector,
        "p2-commit-wait": commit_wait, "p2-lost-reply": lost_reply, "p2-dedup": dedup, "p2-pause": pause,
        "p2-fencing": fencing, "p2-gossip": gossip}

if __name__ == "__main__":
    save(FIGS, sys.argv[1:])
